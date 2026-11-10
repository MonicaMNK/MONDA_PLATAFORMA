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
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def mean_std(values: list[float]) -> dict[str, float]:
    n = len(values)
    if n == 0:
        return {"n": 0, "mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0,
                "median": 0.0}
    m = statistics.mean(values)
    s = statistics.stdev(values) if n > 1 else 0.0
    sv = sorted(values)
    med = sv[n // 2] if n % 2 else (sv[n // 2 - 1] + sv[n // 2]) / 2
    return {
        "n": n,
        "mean": round(m, 2),
        "std": round(s, 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "median": round(med, 2),
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

    return {
        "n_participants": len(rows),
        "manual": mean_std(manual),
        "monda": mean_std(monda),
        "difference": mean_std(diffs),
        "speedup_factor": round(statistics.mean(manual) / statistics.mean(monda), 2),
        "errors_manual_total": total_errors_manual,
        "errors_monda_total": total_errors_monda,
        "all_complete": all_complete,
        "by_role": role_stats,
        "source": path.name,
    }


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
            "mean": round(statistics.mean(slist), 2),
            "median": round(statistics.median(slist), 2),
            "min": round(min(slist), 2),
            "max": round(max(slist), 2),
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
    }
    (out / "pi14_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Reporte PI14 guardado en {out / 'pi14_report.json'}.")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
