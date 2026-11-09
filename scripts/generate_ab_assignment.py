from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


SEQUENCES = ("A_manual_B_monda", "B_manual_A_monda")


def generate_assignments(students: int = 14, teachers: int = 2, seed: int = 20261108) -> list[dict[str, str]]:
    if students < 0 or teachers < 0 or students + teachers == 0:
        raise ValueError("Debe haber al menos un participante y ningún tamaño puede ser negativo.")
    rng = random.Random(seed)
    rows: list[dict[str, str]] = []
    for role, count, prefix in (("estudiante", students, "EST"), ("docente", teachers, "DOC")):
        sequence_labels = [SEQUENCES[index % 2] for index in range(count)]
        rng.shuffle(sequence_labels)
        for index, sequence in enumerate(sequence_labels, start=1):
            rows.append({
                "codigo": f"{prefix}-{index:02d}",
                "rol": role,
                "secuencia": sequence,
                "material_A": "manual" if sequence == SEQUENCES[0] else "monda",
                "material_B": "monda" if sequence == SEQUENCES[0] else "manual",
            })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera una asignación reproducible y contrabalanceada de tareas A/B.")
    parser.add_argument("--students", type=int, default=14)
    parser.add_argument("--teachers", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20261108)
    parser.add_argument("--output", type=Path, default=Path("ab_assignment.csv"))
    args = parser.parse_args()
    rows = generate_assignments(args.students, args.teachers, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Asignación guardada en {args.output} ({len(rows)} códigos seudónimos).")


if __name__ == "__main__":
    main()
