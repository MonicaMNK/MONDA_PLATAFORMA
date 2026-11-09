from __future__ import annotations

import argparse
import csv
import json
import math
import random
from pathlib import Path
from statistics import median


def hodges_lehmann(differences: list[float]) -> float:
    if not differences:
        raise ValueError("Se necesita al menos un par de mediciones.")
    walsh = [(left + right) / 2 for i, left in enumerate(differences)
             for right in differences[i:]]
    return median(walsh)


def rank_biserial(differences: list[float]) -> float:
    nonzero = [(abs(value), value > 0) for value in differences if value != 0]
    if not nonzero:
        return 0.0
    nonzero.sort(key=lambda item: item[0])
    positive_rank_sum = 0.0
    negative_rank_sum = 0.0
    index = 0
    while index < len(nonzero):
        end = index + 1
        while end < len(nonzero) and nonzero[end][0] == nonzero[index][0]:
            end += 1
        average_rank = ((index + 1) + end) / 2
        for _, positive in nonzero[index:end]:
            if positive:
                positive_rank_sum += average_rank
            else:
                negative_rank_sum += average_rank
        index = end
    total = positive_rank_sum + negative_rank_sum
    return (positive_rank_sum - negative_rank_sum) / total if total else 0.0


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def analyze_pairs(rows: list[dict[str, str]], bootstrap_samples: int = 10000,
                  seed: int = 20261108) -> dict:
    if bootstrap_samples < 1000:
        raise ValueError("Use al menos 1000 remuestreos bootstrap.")
    seen = set()
    differences = []
    for row in rows:
        participant = row["participant_id"].strip()
        if not participant or participant in seen:
            raise ValueError("Cada participante debe aparecer una sola vez con ID seudónimo.")
        seen.add(participant)
        try:
            manual = float(row["manual_seconds"])
            monda = float(row["monda_seconds"])
        except (TypeError, ValueError) as exc:
            raise ValueError("Los tiempos deben ser números en segundos.") from exc
        if not math.isfinite(manual) or not math.isfinite(monda) or manual < 0 or monda < 0:
            raise ValueError("Los tiempos deben ser finitos y no negativos.")
        differences.append(manual - monda)
    if len(differences) < 2:
        raise ValueError("Se requieren al menos dos pares para calcular el análisis exploratorio.")

    rng = random.Random(seed)
    bootstrap = []
    for _ in range(bootstrap_samples):
        sample = [rng.choice(differences) for _ in differences]
        bootstrap.append(hodges_lehmann(sample))
    return {
        "n_pairs": len(differences),
        "difference_definition": "manual_seconds - monda_seconds; positive means time saved with Monda",
        "hodges_lehmann_seconds": round(hodges_lehmann(differences), 4),
        "hodges_lehmann_bootstrap_ci_95_seconds": [
            round(percentile(bootstrap, 0.025), 4),
            round(percentile(bootstrap, 0.975), 4),
        ],
        "bootstrap_samples": bootstrap_samples,
        "bootstrap_seed": seed,
        "wilcoxon_rank_biserial_correlation": round(rank_biserial(differences), 4),
        "individual_differences_seconds": [round(value, 4) for value in differences],
        "interpretation_limit": "Exploratory paired analysis; report the small convenience sample and the bootstrap CI method.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume tiempos pareados manual/Monda sin incluir identificadores personales.")
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("--output", type=Path, default=Path("paired_time_summary.json"))
    parser.add_argument("--bootstrap-samples", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20261108)
    args = parser.parse_args()
    with args.input_csv.open(encoding="utf-8-sig", newline="") as stream:
        result = analyze_pairs(list(csv.DictReader(stream)), args.bootstrap_samples, args.seed)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Resumen pareado guardado en {args.output}.")


if __name__ == "__main__":
    main()
