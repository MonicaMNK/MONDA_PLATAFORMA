from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def aiken_v(ratings: list[int], minimum: int = 1, maximum: int = 4) -> float:
    if not ratings or maximum <= minimum:
        raise ValueError("Se requieren calificaciones y una escala válida.")
    if any(value < minimum or value > maximum for value in ratings):
        raise ValueError("Hay calificaciones fuera de la escala declarada.")
    return sum(value - minimum for value in ratings) / (len(ratings) * (maximum - minimum))


def icc_absolute_agreement(matrix: list[list[int]]) -> float:
    """Two-way random, absolute agreement, single-measure ICC (ICC(2,1))."""
    if len(matrix) < 2 or not matrix[0] or len(matrix[0]) < 2:
        raise ValueError("ICC(2,1) requiere al menos dos ítems y dos expertos.")
    expert_count = len(matrix[0])
    if any(len(row) != expert_count for row in matrix):
        raise ValueError("La matriz de calificaciones debe estar completa y rectangular.")
    item_count = len(matrix)
    grand_mean = sum(map(sum, matrix)) / (item_count * expert_count)
    row_means = [sum(row) / expert_count for row in matrix]
    column_means = [sum(matrix[row][column] for row in range(item_count)) / item_count
                    for column in range(expert_count)]
    ms_items = expert_count * sum((mean - grand_mean) ** 2 for mean in row_means) / (item_count - 1)
    ms_experts = item_count * sum((mean - grand_mean) ** 2 for mean in column_means) / (expert_count - 1)
    residual_ss = sum(
        (matrix[row][column] - row_means[row] - column_means[column] + grand_mean) ** 2
        for row in range(item_count)
        for column in range(expert_count)
    )
    ms_error = residual_ss / ((item_count - 1) * (expert_count - 1))
    denominator = ms_items + (expert_count - 1) * ms_error + expert_count * (ms_experts - ms_error) / item_count
    if denominator == 0:
        raise ValueError("No se puede calcular ICC: no hay variación entre las calificaciones.")
    return (ms_items - ms_error) / denominator


def analyze_rows(rows: list[dict[str, str]], minimum: int = 1, maximum: int = 4) -> dict:
    ratings: dict[str, dict[str, int]] = defaultdict(dict)
    for row in rows:
        item = row["item_id"].strip()
        expert = row["expert_id"].strip()
        if not item or not expert or expert in ratings[item]:
            raise ValueError("Cada par ítem/experto debe ser único y no vacío.")
        try:
            value = int(row["rating"])
        except (TypeError, ValueError) as exc:
            raise ValueError("La columna rating debe contener enteros.") from exc
        if value < minimum or value > maximum:
            raise ValueError("Hay calificaciones fuera de la escala declarada.")
        ratings[item][expert] = value
    if not ratings:
        raise ValueError("El archivo no contiene calificaciones.")
    experts = sorted({expert for item_ratings in ratings.values() for expert in item_ratings})
    if any(set(item_ratings) != set(experts) for item_ratings in ratings.values()):
        raise ValueError("Todos los expertos deben calificar todos los ítems para ICC(2,1).")
    matrix = [[ratings[item][expert] for expert in experts] for item in sorted(ratings)]
    return {
        "items": len(matrix),
        "experts": experts,
        "scale": {"minimum": minimum, "maximum": maximum},
        "aiken_v_by_item": {
            item: round(aiken_v([ratings[item][expert] for expert in experts], minimum, maximum), 4)
            for item in sorted(ratings)
        },
        "icc_2_1_absolute_agreement": round(icc_absolute_agreement(matrix), 4),
        "icc_note": "Single-measure, two-way random-effects, absolute-agreement ICC; interpret with the pilot sample size.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Calcula V de Aiken e ICC(2,1) desde una matriz CSV completa.")
    parser.add_argument("ratings_csv", type=Path)
    parser.add_argument("--minimum", type=int, default=1)
    parser.add_argument("--maximum", type=int, default=4)
    parser.add_argument("--output", type=Path, default=Path("expert_ratings_summary.json"))
    args = parser.parse_args()
    with args.ratings_csv.open(encoding="utf-8-sig", newline="") as stream:
        result = analyze_rows(list(csv.DictReader(stream)), args.minimum, args.maximum)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Resumen guardado en {args.output}.")


if __name__ == "__main__":
    main()
