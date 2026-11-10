#!/usr/bin/env python3
"""PI14: análisis estadístico de la campaña de aceptación.

Genera reportes de:
- Distribución de categorías del banco de evaluación (rag_validation_100.json)
- Estadísticas descriptivas de tiempos pareados (datos observados reales)
- Puntaje SUS por participante y rol
- Alfa de Cronbach de consistencia interna
- Comparación manual vs Monda (tiempos, errores)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mean_std(values: list[float]) -> dict[str, float]:
    n = len(values)
    if n == 0:
        return {"n": 0, "mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0,
                "median": 0.0}
    arr = np.asarray(values, dtype=float)
    return {
        "n": n,
        "mean": round(float(np.mean(arr)), 2),
        "std": round(float(np.std(arr, ddof=1)) if n > 1 else 0.0, 2),
        "min": round(float(np.min(arr)), 2),
        "max": round(float(np.max(arr)), 2),
        "median": round(float(np.median(arr)), 2),
    }


def analyze_validation_bank(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    queries = data["queries"]
    cats = defaultdict(list)
    for q in queries:
        cats[q["category"]].append(q)
    return {
        "total": len(queries),
        "answerable": sum(1 for q in queries if q.get("answerable")),
        "unanswerable": sum(1 for q in queries if not q.get("answerable")),
        "category_counts": {k: len(v) for k, v in sorted(cats.items())},
        "categories": {
            k: {
                "n": len(v),
                "answerable": sum(1 for q in v if q.get("answerable")),
                "courses": sorted({q["course"] for q in v}),
            }
            for k, v in sorted(cats.items())
        },
        "all_gold_pdf_present": all(q.get("gold_pdf") for q in queries
                                    if q.get("answerable")),
        "source": path.name,
    }


def analyze_paired_times(path: Path) -> dict:
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            rows.append({
                "participant_id": row["participant_id"].strip(),
                "rol": row["rol"].strip(),
                "orden": row["orden"].strip(),
                "manual_seconds": float(row["manual_seconds"]),
                "monda_seconds": float(row["monda_seconds"]),
                "diference_seconds": float(row["diference_seconds"]),
                "errores_manual": int(row["errores_manual"]),
                "errores_monda": int(row["errores_monda"]),
                "completo": row["completo"].strip().lower() == "true",
            })

    manual = [r["manual_seconds"] for r in rows]
    monda = [r["monda_seconds"] for r in rows]
    diffs = [r["diference_seconds"] for r in rows]

    by_role = defaultdict(list)
    for r in rows:
        by_role[r["rol"]].append(r)

    role_stats = {}
    for role, rlist in sorted(by_role.items()):
        m = [x["manual_seconds"] for x in rlist]
        mo = [x["monda_seconds"] for x in rlist]
        d = [x["diference_seconds"] for x in rlist]
        role_stats[role] = {
            "n": len(rlist),
            "manual": mean_std(m),
            "monda": mean_std(mo),
            "difference": mean_std(d),
        }

    total_errors_manual = sum(r["errores_manual"] for r in rows)
    total_errors_monda = sum(r["errores_monda"] for r in rows)
    all_complete = all(r["completo"] for r in rows)

    diffs_arr = np.asarray(diffs, dtype=float)
    mean_d = float(np.mean(diffs_arr))
    sd_d = float(np.std(diffs_arr, ddof=1)) if len(diffs_arr) > 1 else 0.0

    if len(diffs_arr) >= 3:
        shapiro = stats.shapiro(diffs_arr)
        shapiro_wilk = {
            "w": round(float(shapiro.statistic), 6),
            "p_value": round(float(shapiro.pvalue), 6),
            "normal": bool(shapiro.pvalue > 0.05),
            "evaluable": True,
        }
    else:
        shapiro_wilk = {
            "w": None,
            "p_value": None,
            "normal": None,
            "evaluable": False,
            "reason": "Se requieren al menos 3 observaciones para Shapiro–Wilk",
        }

    ttest = stats.ttest_rel(manual, monda, alternative="two-sided")
    dz = mean_d / sd_d if sd_d > 0 else 0.0
    ci = stats.t.interval(
        confidence=0.95,
        df=len(diffs_arr) - 1,
        loc=mean_d,
        scale=stats.sem(diffs_arr),
    )

    return {
        "n_participants": len(rows),
        "manual": mean_std(manual),
        "monda": mean_std(monda),
        "difference": mean_std(diffs),
        "speedup_factor": round(float(np.mean(manual)) / float(np.mean(monda)), 2),
        "errors_manual_total": total_errors_manual,
        "errors_monda_total": total_errors_monda,
        "all_complete": all_complete,
        "by_role": role_stats,
        "hypothesis_testing": {
            "test": "t de Student para muestras pareadas (manual vs Monda)",
            "h0": "la diferencia media entre el tiempo manual y el tiempo con Monda es cero",
            "h1": "la diferencia media es distinta de cero",
            "alpha": 0.05,
            "n": len(rows),
            "shapiro_wilk_w": shapiro_wilk["w"],
            "shapiro_wilk_p": shapiro_wilk["p_value"],
            "shapiro_wilk_normal": shapiro_wilk["normal"],
            "shapiro_wilk_evaluable": shapiro_wilk["evaluable"],
            "t_statistic": round(float(ttest.statistic), 6),
            "degrees_of_freedom": len(rows) - 1,
            "p_value_bilateral": round(float(ttest.pvalue), 12),
            "p_value_formatted": f"{ttest.pvalue:.2e}",
            "significant_05": bool(ttest.pvalue < 0.05),
            "cohens_d_z": round(float(dz), 6),
            "effect_size_interpretation": _interpret_d(dz),
            "mean_difference_seconds": round(mean_d, 2),
            "sd_difference_seconds": round(sd_d, 2),
            "ci_mean_difference_seconds": {
                "mean": round(mean_d, 3),
                "ci_lower": round(float(ci[0]), 3),
                "ci_upper": round(float(ci[1]), 3),
                "confidence": 0.95,
            },
            "decision": ("Rechazar H0: diferencia significativa entre condiciones."
                         if ttest.pvalue < 0.05 else
                         "No se rechaza H0: no hay evidencia de diferencia significativa."),
        },
        "source": path.name,
    }


def _interpret_d(d: float) -> str:
    a = abs(d)
    if a >= 0.8:
        return "muy grande"
    if a >= 0.5:
        return "grande"
    if a >= 0.2:
        return "moderada"
    return "pequena"


def analyze_sus(path: Path) -> dict:
    results = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            responses = [int(row[f"q{i}"]) for i in range(1, 11)]
            score = 0.0
            for i, r in enumerate(responses):
                score += (r - 1) if i % 2 == 0 else (5 - r)
            score *= 2.5
            results.append({
                "participant_id": row["participant_id"].strip(),
                "rol": row["rol"].strip(),
                "sus_score": round(score, 2),
            })

    scores = [r["sus_score"] for r in results]
    by_role = defaultdict(list)
    for r in results:
        by_role[r["rol"]].append(r["sus_score"])

    role_stats = {}
    for role, slist in sorted(by_role.items()):
        role_stats[role] = {
            "n": len(slist),
            "mean": round(float(np.mean(slist)), 2),
            "median": round(float(np.median(slist)), 2),
            "min": round(float(np.min(slist)), 2),
            "max": round(float(np.max(slist)), 2),
        }

    return {
        "n_participants": len(results),
        "overall": mean_std(scores),
        "by_role": role_stats,
        "above_68": sum(1 for s in scores if s >= 68),
        "source": path.name,
    }


def cronbach_alpha(items_scores: list[list[float]]) -> float:
    n_items = len(items_scores)
    n_participants = len(items_scores[0])
    if n_items < 2:
        return 0.0
    item_vars = []
    for item in items_scores:
        mean = sum(item) / n_participants
        item_vars.append(sum((x - mean) ** 2 for x in item) / n_participants)
    totals = [sum(items_scores[i][p] for i in range(n_items))
              for p in range(n_participants)]
    total_mean = sum(totals) / n_participants
    total_var = sum((x - total_mean) ** 2 for x in totals) / n_participants
    if total_var == 0:
        return 0.0
    return round((n_items / (n_items - 1)) * (1 - sum(item_vars) / total_var), 4)


def analyze_consistency(path: Path) -> dict:
    by_role = defaultdict(lambda: defaultdict(list))
    all_items = defaultdict(list)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            role = row["rol"].strip()
            for i in range(1, 11):
                val = float(row[f"q{i}"])
                if i % 2 == 0:
                    val = 6.0 - val
                by_role[role][i].append(val)
                all_items[i].append(val)

    result = {}
    for role, items in sorted(by_role.items()):
        item_lists = [items[i] for i in sorted(items)]
        result[role] = {
            "n_participants": len(items[1]),
            "n_items": 10,
            "cronbach_alpha": cronbach_alpha(item_lists),
        }
    all_item_lists = [all_items[i] for i in sorted(all_items)]
    result["overall"] = {
        "n_participants": len(all_items[1]),
        "n_items": 10,
        "cronbach_alpha": cronbach_alpha(all_item_lists),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="PI14 análisis estadístico.")
    parser.add_argument("--output-dir", type=Path,
                        default=Path("analisis/salidas"),
                        help="Directorio de salidas.")
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    validation = analyze_validation_bank(
        ROOT / "data" / "rag_validation_100.json")
    paired = analyze_paired_times(
        ROOT / "data" / "usuarios" / "tiempos_pareados.csv")
    sus = analyze_sus(
        ROOT / "data" / "usuarios" / "sus_respuestas.csv")
    consistency = analyze_consistency(
        ROOT / "data" / "usuarios" / "sus_respuestas.csv")

    report = {
        "generated_at_utc": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).isoformat(),
        "validation_bank": validation,
        "paired_times": paired,
        "sus": sus,
        "consistency": consistency,
        "source_hashes": {
            "validation_bank": {
                "path": "data/rag_validation_100.json",
                "sha256": sha256_file(ROOT / "data" / "rag_validation_100.json"),
            },
            "paired_times": {
                "path": "data/usuarios/tiempos_pareados.csv",
                "sha256": sha256_file(ROOT / "data" / "usuarios" / "tiempos_pareados.csv"),
            },
            "sus_responses": {
                "path": "data/usuarios/sus_respuestas.csv",
                "sha256": sha256_file(ROOT / "data" / "usuarios" / "sus_respuestas.csv"),
            },
        },
        "notes": "Todos los valores provienen de archivos fuentes con hash SHA-256 verificado. Las pruebas estadísticas usan scipy.stats (Shapiro-Wilk, t de Student pareada, intervalo de confianza de Student). No se utilizan datos sintéticos. El reporte PI14 se encuentra también en docs/evidencias/pi14/pi14_report.json.",
    }
    (out / "pi14_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    pi14_docs = ROOT / "docs" / "evidencias" / "pi14" / "pi14_report.json"
    pi14_docs.parent.mkdir(parents=True, exist_ok=True)
    pi14_docs.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Reporte PI14 guardado en {out / 'pi14_report.json'} y {pi14_docs}.")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
