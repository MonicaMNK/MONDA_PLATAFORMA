from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DATA_DIR = ROOT / "data"
PDF_DIR = DATA_DIR / "demo_materials"
FIXTURE_PATH = DATA_DIR / "rag_calibration_100.json"
OUTPUT_PATH = DATA_DIR / "rag_calibration_gemini_20261101.json"
PARTIAL_PATH = DATA_DIR / "rag_calibration_gemini_20261101.partial.json"
TEMP_CACHE_PATH = Path.home() / "AppData" / "Local" / "Temp" / \
    "monda_calibration_rebuild_docs.json"
COURSE_DIRS = {"Biología": "biologia",
               "Historia": "historia", "Literatura": "literatura"}
DIMENSIONS = 768
BATCH_SIZE = 10
FOLDS = 5
FOLD_SEED = 20261101
K_CANDIDATES = (1, 2, 3, 4, 5, 6, 8)
THRESHOLD_CANDIDATES = tuple(sorted(set(
    round(value / 100, 2) for value in range(20, 81, 2)
) | {0.69}))
MARGIN_CANDIDATES = (0.0, 0.02, 0.05, 0.10, 0.15)

# Política de calibración del informe:
#   - Cobertura de consultas respondibles (answer_coverage) >= 0.70 es
#     restricción dura: no puede bajar del 70 %.
#   - Dentro de esa restricción se maximiza la abstención correcta de los
#     20 controles (meta del informe: 50 %; se alcanza lo máximo factible con
#     los vectores ya calculados, sin re-vectorizar las 100 consultas).
MIN_COVERAGE_REQUIRED = 0.70
TARGET_ABSTENTION = 0.50
# Regla de decisión de "evidencia suficiente":
#   "top1"  = histórico: acepta si el mejor cosíneo >= umbral (y cumple el
#     margen mínimo si se indica).
#   "meantopk" = nuevo: acepta si el promedio de los cosíneos top-k >= umbral.
#     Es más selectivo con los controles/distractores y permite subir la
#     abstención sin castigar tanto la cobertura de respondibles.
EVIDENCE_RULE = "meantopk"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_inputs() -> tuple[dict, list[dict], dict[str, str], str]:
    fixture_bytes = FIXTURE_PATH.read_bytes()
    fixture = json.loads(fixture_bytes)
    queries = fixture["queries"]
    if len(queries) != 100 or sum(query["answerable"] for query in queries) != 80:
        raise ValueError(
            "El fixture debe contener 80 consultas respondibles y 20 controles.")

    fragments = []
    pdf_hashes = {}
    for course, slug in COURSE_DIRS.items():
        for path in sorted((PDF_DIR / slug).glob("*.pdf")):
            data = path.read_bytes()
            pdf_hashes[f"{slug}/{path.name}"] = sha256(data)
            reader = PdfReader(str(path))
            text = "\n\n".join(page.extract_text()
                               or "" for page in reader.pages)
            tokens = re.findall(r"\S+", text)
            ordinal = 0
            for start in range(0, len(tokens), 462):
                piece = " ".join(tokens[start: start + 512]).strip()
                if len(piece) >= 20:
                    ordinal += 1
                    fragments.append({
                        "course": course,
                        "course_slug": slug,
                        "filename": path.name,
                        "ordinal": ordinal,
                        "text_sha256": sha256(piece.encode("utf-8")),
                        "text": piece,
                    })
                if start + 512 >= len(tokens):
                    break

    if len(fragments) != 118 or len(pdf_hashes) != 9:
        raise ValueError(
            f"Corpus inesperado: {len(fragments)} fragmentos, {len(pdf_hashes)} PDFs.")
    return fixture, fragments, pdf_hashes, sha256(fixture_bytes)


def initial_artifact(settings, fixture: dict, fragments: list[dict], pdf_hashes: dict[str, str], fixture_hash: str) -> dict:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
    except Exception:
        commit = None
    return {
        "status": "partial",
        "metadata": {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "provider": "gemini",
            "embedding_model": settings.gemini_embedding_model,
            "dimensions": DIMENSIONS,
            "external_processing_authorized": True,
            "repository_commit": commit,
            "fixture_sha256": fixture_hash,
            "source_pdf_sha256": pdf_hashes,
            "pdf_count": len(pdf_hashes),
            "query_count": len(fixture["queries"]),
            "answerable_count": 80,
            "unanswerable_control_count": 20,
            "fragment_count": len(fragments),
            "document_prefix": "title: none | text: ",
            "query_prefix": "task: question answering | query: ",
            "chunking": {"window_tokens": 512, "overlap_tokens": 50},
            "embedding_api_batch_size": BATCH_SIZE,
        },
        "queries": fixture["queries"],
        "fragments": [{key: value for key, value in item.items() if key != "text"} for item in fragments],
        "document_vectors": [],
        "query_vectors": [],
        "calibration": None,
    }


def validate_partial(artifact: dict, fixture: dict, fragments: list[dict], pdf_hashes: dict[str, str], fixture_hash: str, model: str) -> None:
    metadata = artifact.get("metadata", {})
    expected_fragments = [
        {key: value for key, value in item.items() if key != "text"} for item in fragments]
    checks = (
        metadata.get("fixture_sha256") == fixture_hash,
        metadata.get("source_pdf_sha256") == pdf_hashes,
        metadata.get("embedding_model") == model,
        artifact.get("queries") == fixture["queries"],
        artifact.get("fragments") == expected_fragments,
    )
    if not all(checks):
        raise ValueError(
            "El artefacto parcial no coincide con los PDFs, el fixture o el modelo actuales.")


def cached_fragments_match(cached: list[dict], current: list[dict]) -> bool:
    if len(cached) > len(current):
        return False
    stable_fields = ("course_slug", "filename", "ordinal", "text_sha256")
    return all(
        all(old.get(field) == new.get(field) for field in stable_fields)
        for old, new in zip(cached, current)
    )


def embed_batch(texts: list[str], prefix: str, settings) -> list[list[float]]:
    model = settings.gemini_embedding_model
    url = f"{settings.gemini_base_url.rstrip('/')}/models/{model}:batchEmbedContents"
    payload = {
        "requests": [
            {
                "model": f"models/{model}",
                "content": {"parts": [{"text": prefix + text}]},
                "output_dimensionality": DIMENSIONS,
            }
            for text in texts
        ]
    }
    response = requests.post(
        url,
        headers={"x-goog-api-key": settings.gemini_api_key},
        json=payload,
        timeout=120,
    )
    if not response.ok:
        try:
            error = response.json().get("error", {})
            detail = f"{error.get('status', 'unknown')}: {error.get('message', '')[:300]}"
        except Exception:
            detail = "respuesta de error no interpretable"
        raise RuntimeError(f"Gemini HTTP {response.status_code}; {detail}")
    vectors = [item.get("values", [])
               for item in response.json().get("embeddings", [])]
    if len(vectors) != len(texts) or any(len(vector) != DIMENSIONS for vector in vectors):
        raise ValueError(
            "Gemini devolvió un número de vectores o dimensiones inesperados.")
    return [[float(value) for value in vector] for vector in vectors]


def save_partial(artifact: dict) -> None:
    temporary_path = PARTIAL_PATH.with_suffix(".tmp")
    temporary_path.write_text(json.dumps(
        artifact, ensure_ascii=False), encoding="utf-8")
    temporary_path.replace(PARTIAL_PATH)


def cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    return dot / (left_norm * right_norm) if left_norm and right_norm else -1.0


def decide_top1(results: list[tuple], top_k: int, threshold: float,
                margin: float = 0.0) -> bool:
    """Regla histórica: hay evidencia si el mejor cosíneo supera el umbral
    y el margen sobre el segundo mejor cumple el mínimo."""
    if not results:
        return False
    score_gap = results[0][0] - results[1][0] if len(results) > 1 else 2.0
    return results[0][0] >= threshold and score_gap >= margin


def decide_mean_topk(results: list[tuple], top_k: int, threshold: float,
                     margin: float = 0.0) -> bool:
    """Nueva regla del informe: hay evidencia si el promedio de los cosíneos
    de los top-k fragmentos recuperados supera el umbral (y cumple el margen
    mínimo si se indica).

    Un distractor/control suele tener un solo fragmento con cosíneo alto,
    mientras que una consulta respondible tiene varios fragmentos relevantes;
    promediar top-k castiga más a los controles y permite subir la abstención
    correcta sin castigar tanto la cobertura de respondibles.
    """
    if not results:
        return False
    kk = min(max(top_k, 1), len(results))
    score_gap = results[0][0] - results[1][0] if len(results) > 1 else 2.0
    return (sum(score for score, _, _ in results[:kk]) / kk >= threshold
            and score_gap >= margin)


DECIDE_FNS = {"top1": decide_top1, "meantopk": decide_mean_topk}


def evaluate(indices, config_for, queries, ranked, decide_fn=None) -> dict:
    if decide_fn is None:
        decide_fn = DECIDE_FNS[EVIDENCE_RULE]
    answerable_total = sum(queries[index]["answerable"] for index in indices)
    control_total = len(indices) - answerable_total
    covered = correct_abstentions = citation_hits = citation_total = false_answers = 0
    for index in indices:
        query = queries[index]
        top_k, threshold, min_margin = config_for(index)
        results = ranked[index]
        accepted = bool(decide_fn(results, top_k, threshold, min_margin))
        if query["answerable"] and accepted:
            covered += 1
        if not query["answerable"]:
            if accepted:
                false_answers += 1
            else:
                correct_abstentions += 1
        if accepted:
            selected = results[:top_k]
            citation_total += len(selected)
            if query["answerable"]:
                citation_hits += sum(filename == query["gold_pdf"]
                                     for _, filename, _ in selected)

    coverage = covered / answerable_total if answerable_total else 0.0
    abstention = correct_abstentions / control_total if control_total else 0.0
    precision = citation_hits / citation_total if citation_total else 0.0
    return {
        "answer_coverage": coverage,
        "correct_abstention": abstention,
        "citation_precision_pdf": precision,
        "false_answers": false_answers,
        "citations_emitted": citation_total,
        "correct_citations": citation_hits,
        "balanced_score_equal_weight": (coverage + abstention + precision) / 3,
    }


def _select_calibration_config(candidates: list[tuple]) -> tuple:
    """Elige la configuración de calibración siguiendo la política del informe.

    Reglas:
      1. answer_coverage (índice 3) >= MIN_COVERAGE_REQUIRED: cobertura de
         consultas respondibles no puede bajar del 70 % (restricción dura).
      2. Entre las que cumplen el piso, maximiza correct_abstention (índice 2):
         sube el % de controles correctamente abstendos (meta del informe: 50 %;
         se alcanza lo máximo factible con los vectores existentes).
      3. Desempates: mayor citation_precision_pdf (índice 1), luego k menor
         (índice 5 = -k), luego umbral menor (índice 6 = -umbral), luego
         margen menor (índice 7 = -margin).
      4. Si ninguna candidata cumple el piso de cobertura, se relaja la
         restricción y se elige por balanced_score_equal_weight (red de
         seguridad).
    """
    valid = [c for c in candidates if c[3] >= MIN_COVERAGE_REQUIRED]
    pool = valid if valid else candidates
    return max(
        pool,
        key=lambda c: (c[2], c[1], c[5], c[6], c[7]),
    )


def calibrate(artifact: dict, fragments: list[dict], fixture: dict) -> dict:
    queries = fixture["queries"]
    doc_vectors = artifact["document_vectors"]
    query_vectors = artifact["query_vectors"]
    if len(doc_vectors) != len(fragments) or len(query_vectors) != len(queries):
        raise ValueError("No se puede calibrar: faltan vectores completos.")

    ranked = []
    for query, query_vector in zip(queries, query_vectors):
        rows = []
        for fragment, document_vector in zip(fragments, doc_vectors):
            if fragment["course"] == query["course"]:
                rows.append((
                    cosine(query_vector, document_vector),
                    fragment["filename"],
                    fragment["ordinal"],
                ))
        ranked.append(sorted(rows, reverse=True))

    strata = defaultdict(list)
    for index, query in enumerate(queries):
        key = (query["course"], query["answerable"],
               query["gold_pdf"] if query["answerable"] else None)
        strata[key].append(index)
    fold_of = {}
    rng = random.Random(FOLD_SEED)
    for indices in strata.values():
        rng.shuffle(indices)
        for position, index in enumerate(indices):
            fold_of[index] = position % FOLDS

    oof_config = {}
    fold_results = []
    full_indices = list(range(len(queries)))
    for fold in range(FOLDS):
        train = [index for index in full_indices if fold_of[index] != fold]
        test = [index for index in full_indices if fold_of[index] == fold]
        candidates = []
        for top_k in K_CANDIDATES:
            for threshold in THRESHOLD_CANDIDATES:
                for margin in MARGIN_CANDIDATES:
                    metrics = evaluate(train, lambda _i, k=top_k,
                                       t=threshold, m=margin: (k, t, m), queries, ranked,
                                       decide_fn=DECIDE_FNS[EVIDENCE_RULE])
                    candidates.append((
                        metrics["balanced_score_equal_weight"],
                        metrics["citation_precision_pdf"],
                        metrics["correct_abstention"],
                        metrics["answer_coverage"],
                        -top_k,
                        -threshold,
                        -margin,
                        top_k,
                        threshold,
                        margin,
                    ))
        best = _select_calibration_config(candidates)
        selected = (best[-3], best[-2], best[-1])
        for index in test:
            oof_config[index] = selected
        fold_results.append({
            "fold": fold + 1,
            "train_count": len(train),
            "test_count": len(test),
            "selected_k": selected[0],
            "selected_cosine_threshold": selected[1],
            "selected_minimum_score_margin": selected[2],
        })

    out_of_fold_metrics = evaluate(
        full_indices, lambda index: oof_config[index], queries, ranked)
    full_candidates = []
    for top_k in K_CANDIDATES:
        for threshold in THRESHOLD_CANDIDATES:
            for margin in MARGIN_CANDIDATES:
                metrics = evaluate(full_indices, lambda _i, k=top_k,
                                   t=threshold, m=margin: (k, t, m), queries, ranked,
                                   decide_fn=DECIDE_FNS[EVIDENCE_RULE])
                full_candidates.append((
                    metrics["balanced_score_equal_weight"],
                    metrics["citation_precision_pdf"],
                    metrics["correct_abstention"],
                    metrics["answer_coverage"],
                    -top_k,
                    -threshold,
                    -margin,
                    top_k,
                    threshold,
                    margin,
                    metrics,
                ))
    best_full = _select_calibration_config(full_candidates)

    predictions = []
    for index, query in enumerate(queries):
        top_k, threshold, min_margin = oof_config[index]
        results = ranked[index]
        score_gap = results[0][0] - results[1][0] if len(results) > 1 else 2.0
        accepted = bool(
            DECIDE_FNS[EVIDENCE_RULE](results, top_k, threshold, min_margin))
        predictions.append({
            "query_id": query["id"],
            "fold": fold_of[index] + 1,
            "selected_k": top_k,
            "selected_cosine_threshold": threshold,
            "selected_minimum_score_margin": min_margin,
            "top_cosine": results[0][0] if results else None,
            "top_two_score_gap": score_gap if results else None,
            "accepted": accepted,
            "gold_answerable": query["answerable"],
            "sources": [
                {"pdf": filename, "fragment_ordinal": ordinal, "cosine": score}
                for score, filename, ordinal in results[:top_k]
            ] if accepted else [],
        })

    return {
        "method": {
            "validation": "stratified_5_fold_out_of_fold",
            "fold_seed": FOLD_SEED,
            "k_candidates": list(K_CANDIDATES),
            "cosine_threshold_candidates": list(THRESHOLD_CANDIDATES),
            "minimum_score_margin_candidates": list(MARGIN_CANDIDATES),
            "selection_objective": (
                "maximize correct abstention subject to answer_coverage >= "
                f"{MIN_COVERAGE_REQUIRED:.0%}; ties broken by citation "
                "precision, then smaller k, threshold and margin"
            ),
            "coverage_floor": MIN_COVERAGE_REQUIRED,
            "target_abstention": TARGET_ABSTENTION,
            "evidence_rule": EVIDENCE_RULE,
            "scope": "course-restricted retrieval over pypdf-extracted 512-token chunks with 50-token overlap",
        },
        "folds": fold_results,
        "out_of_fold_metrics": out_of_fold_metrics,
        "full_dataset_selected_config_in_sample": {
            "k": best_full[-4],
            "cosine_threshold": best_full[-3],
            "minimum_score_margin": best_full[-2],
            "metrics_in_sample_not_generalization": best_full[-1],
        },
        "out_of_fold_predictions": predictions,
        "citation_metric_limit": "Citation precision is evaluated at PDF-source level because the fixture gold labels identify PDFs, not pages or exact supporting fragments.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calibra k y umbral coseno del RAG con Gemini y conserva evidencia reproducible.")
    parser.add_argument("--resume", action="store_true",
                        help="Reanuda desde el artefacto parcial verificado.")
    args = parser.parse_args()

    from backend.app.core.config import settings
    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY no está configurada.")
    if not settings.gemini_external_processing_authorized:
        raise SystemExit(
            "Falta GEMINI_EXTERNAL_PROCESSING_AUTHORIZED=1 para enviar los PDFs a Gemini.")

    fixture, fragments, pdf_hashes, fixture_hash = load_inputs()
    if PARTIAL_PATH.exists():
        if not args.resume:
            raise SystemExit(
                f"Existe {PARTIAL_PATH}; usa --resume para continuar o archívalo antes de iniciar otro run.")
        artifact = json.loads(PARTIAL_PATH.read_text(encoding="utf-8"))
        validate_partial(artifact, fixture, fragments, pdf_hashes,
                         fixture_hash, settings.gemini_embedding_model)
    else:
        artifact = initial_artifact(
            settings, fixture, fragments, pdf_hashes, fixture_hash)
        if args.resume and TEMP_CACHE_PATH.exists():
            temporary_cache = json.loads(
                TEMP_CACHE_PATH.read_text(encoding="utf-8"))
            cached_chunks = temporary_cache.get("chunks", [])
            if not cached_fragments_match(cached_chunks, fragments):
                raise SystemExit(
                    "La caché temporal no coincide con los fragmentos actuales; no se importó.")
            vectors = temporary_cache.get("vectors", [])
            if len(vectors) > len(cached_chunks) or any(len(vector) != DIMENSIONS for vector in vectors):
                raise SystemExit(
                    "La caché temporal tiene vectores incompletos o dimensiones incorrectas.")
            artifact["document_vectors"] = vectors
            artifact["metadata"]["imported_verified_temp_vectors"] = len(
                vectors)

    save_partial(artifact)
    document_prefix = "title: none | text: "
    query_prefix = "task: question answering | query: "
    for offset in range(len(artifact["document_vectors"]), len(fragments), BATCH_SIZE):
        group = fragments[offset: offset + BATCH_SIZE]
        vectors = embed_batch([item["text"]
                              for item in group], document_prefix, settings)
        artifact["document_vectors"].extend(vectors)
        save_partial(artifact)
        print(
            f"document_vectors={len(artifact['document_vectors'])}/{len(fragments)}", flush=True)

    for offset in range(len(artifact["query_vectors"]), len(fixture["queries"]), BATCH_SIZE):
        group = fixture["queries"][offset: offset + BATCH_SIZE]
        vectors = embed_batch([item["question"]
                              for item in group], query_prefix, settings)
        artifact["query_vectors"].extend(vectors)
        save_partial(artifact)
        print(
            f"query_vectors={len(artifact['query_vectors'])}/{len(fixture['queries'])}", flush=True)

    if len(artifact["document_vectors"]) != len(fragments) or len(artifact["query_vectors"]) != len(fixture["queries"]):
        raise SystemExit("No se completaron todos los embeddings.")
    artifact["status"] = "complete"
    artifact["metadata"]["completed_at_utc"] = datetime.now(
        timezone.utc).isoformat()
    artifact["metadata"]["document_embedding_count"] = len(fragments)
    artifact["metadata"]["query_embedding_count"] = len(fixture["queries"])
    artifact["calibration"] = calibrate(artifact, fragments, fixture)
    final_tmp = OUTPUT_PATH.with_suffix(".tmp")
    final_tmp.write_text(json.dumps(
        artifact, ensure_ascii=False), encoding="utf-8")
    final_tmp.replace(OUTPUT_PATH)
    PARTIAL_PATH.unlink(missing_ok=True)
    print(
        f"Complete calibration evidence written to {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
