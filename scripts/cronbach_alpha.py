#!/usr/bin/env python3
"""Coeficiente alfa de Cronbach por versión (estudiante/docente) y para SUS.

Alfa de Cronbach: medida de consistencia interna de un cuestionario.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path


def cronbach_alpha(items_scores: list[list[float]]) -> float:
    """Calcula alfa de Cronbach para una matriz de ítems x participantes.

    items_scores: lista de listas, cada sublista son las puntuaciones de un ítem
    para todos los participantes.
    """
    if not items_scores or not items_scores[0]:
        raise ValueError("Se requiere al menos un ítem y un participante.")
    n_items = len(items_scores)
    n_participants = len(items_scores[0])
    if n_items < 2:
        raise ValueError("Se requieren al menos 2 ítems.")
    if any(len(row) != n_participants for row in items_scores):
        raise ValueError("Todos los ítems deben tener el mismo número de participantes.")

    item_variances = []
    for item in items_scores:
        mean = sum(item) / n_participants
        var = sum((x - mean) ** 2 for x in item) / n_participants
        item_variances.append(var)

    total_scores = [sum(items_scores[i][p] for i in range(n_items))
                    for p in range(n_participants)]
    total_mean = sum(total_scores) / n_participants
    total_variance = sum((x - total_mean) ** 2 for x in total_scores) / n_participants

    if total_variance == 0:
        return 0.0

    alpha = (n_items / (n_items - 1)) * (
        1 - sum(item_variances) / total_variance
    )
    return round(alpha, 4)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calcula alfa de Cronbach por rol y para SUS.")
    parser.add_argument("input_csv", type=Path,
                        help="CSV con sus_respuestas (participant_id, rol, q1..q10).")
    parser.add_argument("--output", type=Path,
                        default=Path("cronbach_alpha.json"),
                        help="Archivo de salida JSON.")
    parser.add_argument("--sus", action="store_true",
                        help="Aplica reverse scoring de ítems pares (SUS estándar).")
    args = parser.parse_args()

    by_role = defaultdict(lambda: defaultdict(list))
    all_items = defaultdict(list)
    participants = []
    with args.input_csv.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            pid = row["participant_id"].strip()
            role = row["rol"].strip()
            participants.append((pid, role))
            for i in range(1, 11):
                val = float(row[f"q{i}"])
                if args.sus and i % 2 == 0:
                    val = 6.0 - val
                by_role[role][i].append(val)
                all_items[i].append(val)

    results = {}
    for role, items in sorted(by_role.items()):
        item_lists = [items[i] for i in sorted(items)]
        results[role] = {
            "n_participants": len(items[1]),
            "n_items": 10,
            "cronbach_alpha": cronbach_alpha(item_lists),
        }

    all_item_lists = [all_items[i] for i in sorted(all_items)]
    results["overall"] = {
        "n_participants": len(participants),
        "n_items": 10,
        "cronbach_alpha": cronbach_alpha(all_item_lists),
    }

    output = {
        "cronbach_alpha_by_role": results,
        "interpretation": "Alfa >= 0.70 indica consistencia interna aceptable.",
    }
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(f"Alfa de Cronbach guardado en {args.output}.")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
