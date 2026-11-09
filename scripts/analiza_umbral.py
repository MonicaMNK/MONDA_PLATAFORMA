from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data" / "rag_calibration_gemini_20261101.json"


def cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    ln = math.sqrt(sum(v * v for v in left))
    rn = math.sqrt(sum(v * v for v in right))
    return dot / (ln * rn) if ln and rn else -1.0


def load_ranked():
    artifact = json.loads(ART.read_text(encoding="utf-8"))
    queries = artifact["queries"]
    fragments = artifact["fragments"]
    doc_vectors = artifact["document_vectors"]
    query_vectors = artifact["query_vectors"]
    ranked = []
    for query, qv in zip(queries, query_vectors):
        rows = []
        for fragment, dv in zip(fragments, doc_vectors):
            if fragment["course"] == query["course"]:
                rows.append(
                    (cosine(qv, dv), fragment["filename"], fragment["ordinal"]))
        ranked.append(sorted(rows, reverse=True))
    return artifact, queries, ranked


def decide(rule, param, cos):
    if rule == "top1":
        t = param
        return bool(cos and cos[0][0] >= t)
    if rule == "count":
        t, m = param
        return sum(1 for c, _, _ in cos if c >= t) >= m
    if rule == "meantopk":
        k, t = param
        if not cos:
            return False
        return sum(c for c, _, _ in cos[:k]) / min(k, len(cos)) >= t
    raise ValueError(rule)


def metrics(rule, param, queries, ranked):
    n_ans = sum(1 for q in queries if q["answerable"])
    n_ctl = len(queries) - n_ans
    covered = abst = 0
    details = []
    for i, query in enumerate(queries):
        accepted = decide(rule, param, ranked[i])
        is_ans = query["answerable"]
        if is_ans and accepted:
            covered += 1
        if not is_ans and not accepted:
            abst += 1
        details.append((query["id"], is_ans, accepted,
                        ranked[i][0][0] if ranked[i] else None))
    return covered / n_ans, abst / n_ctl, details


def main():
    artifact, queries, ranked = load_ranked()
    print("Candidatos con coverage >= 0.70 y abstention >= 0.50:\n")

    resultados = []
    # Regla top1 (la actual)
    for t in [round(x / 100, 2) for x in range(56, 81, 2)]:
        cov, ab, _ = metrics("top1", t, queries, ranked)
        resultados.append(("top1", t, cov, ab))

    # Regla count: al menos m fragmentos con cosine >= t
    for t in [round(x / 100, 2) for x in range(56, 81, 2)]:
        for m in (2, 3):
            cov, ab, _ = metrics("count", (t, m), queries, ranked)
            resultados.append((f"count m={m}", t, cov, ab))

    # Regla mean(top-k) >= t
    for k in (2, 3, 4, 5, 6, 8):
        for t in [round(x / 100, 2) for x in range(56, 81, 2)]:
            cov, ab, _ = metrics("meantopk", (k, t), queries, ranked)
            resultados.append((f"mean top{k}", t, cov, ab))

    validos = [r for r in resultados if r[2] >= 0.70 and r[3] >= 0.50]
    validos.sort(key=lambda r: (r[3], r[2]), reverse=True)
    print(
        f"Reglas que cumplen cobertura>=70% y abstencion>=50%: {len(validos)}\n")
    for rule, t, cov, ab in validos[:15]:
        n_ctl = sum(1 for q in queries if not q["answerable"])
        n_ans = sum(1 for q in queries if q["answerable"])
        print(f"  {rule:14s} param={t:<5} coverage={cov:.3f} "
              f"({round(cov*n_ans)}/80)  abstention={ab:.3f} "
              f"({round(ab*n_ctl)}/20)")

    if not validos:
        print("  (ninguna regla alcanza ambos umbrales con los vectores actuales)")


if __name__ == "__main__":
    main()
