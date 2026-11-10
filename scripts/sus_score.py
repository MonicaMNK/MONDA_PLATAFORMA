#!/usr/bin/env python3
"""Cálculo del puntaje SUS estándar por participante y por rol.

SUS (System Usability Scale): 10 ítems, escala 1-5.
- Ítems impares: puntuación = respuesta - 1
- Ítems pares: puntuación = 5 - respuesta
- Puntaje total = suma de puntuaciones × 2.5
- Rango: 0-100
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def sus_score(responses: list[int]) -> float:
    """Calcula el puntaje SUS de 10 respuestas (escala 1-5)."""
    if len(responses) != 10:
        raise ValueError("SUS requiere exactamente 10 respuestas.")
    if any(r < 1 or r > 5 for r in responses):
        raise ValueError("Las respuestas SUS deben estar en escala 1-5.")
    score = 0.0
    for i, r in enumerate(responses):
        if i % 2 == 0:  # ítem impar (1,3,5,7,9): respuesta - 1
            score += r - 1
        else:  # ítem par (2,4,6,8,10): 5 - respuesta
            score += 5 - r
    return round(score * 2.5, 2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calcula puntaje SUS estándar por participante y rol.")
    parser.add_argument("input_csv", type=Path,
                        help="CSV con sus_respuestas (participant_id, rol, q1..q10).")
    parser.add_argument("--output", type=Path,
                        default=Path("sus_scores.json"),
                        help="Archivo de salida JSON.")
    args = parser.parse_args()

    results = []
    by_role = defaultdict(list)
    with args.input_csv.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            pid = row["participant_id"].strip()
            role = row["rol"].strip()
            responses = [int(row[f"q{i}"]) for i in range(1, 11)]
            score = sus_score(responses)
            results.append({
                "participant_id": pid,
                "rol": role,
                "sus_score": score,
            })
            by_role[role].append(score)

    role_summary = {}
    for role, scores in sorted(by_role.items()):
        n = len(scores)
        mean = sum(scores) / n
        sorted_scores = sorted(scores)
        median = sorted_scores[n // 2] if n % 2 else (
            sorted_scores[n // 2 - 1] + sorted_scores[n // 2]) / 2
        variance = sum((s - mean) ** 2 for s in scores) / n
        std = variance ** 0.5
        role_summary[role] = {
            "n": n,
            "mean": round(mean, 2),
            "median": round(median, 2),
            "std": round(std, 2),
            "min": round(min(scores), 2),
            "max": round(max(scores), 2),
            "scores": [round(s, 2) for s in scores],
        }

    all_scores = [r["sus_score"] for r in results]
    overall_mean = sum(all_scores) / len(all_scores)
    overall_min = min(all_scores)
    overall_max = max(all_scores)

    output = {
        "n_participants": len(results),
        "overall": {
            "mean": round(overall_mean, 2),
            "median": round(sorted(all_scores)[len(all_scores) // 2], 2),
            "min": round(overall_min, 2),
            "max": round(overall_max, 2),
        },
        "by_role": role_summary,
        "participants": results,
        "interpretation": "SUS >= 68 se considera aceptable (mínimo 62.5 observado en este piloto).",
    }
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(f"Puntajes SUS guardados en {args.output}.")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
