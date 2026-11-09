from collections import Counter

import pytest

from scripts.generate_ab_assignment import SEQUENCES, generate_assignments


def test_default_assignment_counterbalances_materials_within_roles():
    rows = generate_assignments()
    counts = Counter((row["rol"], row["secuencia"]) for row in rows)

    assert len(rows) == 16
    assert counts[("estudiante", SEQUENCES[0])] == 7
    assert counts[("estudiante", SEQUENCES[1])] == 7
    assert counts[("docente", SEQUENCES[0])] == 1
    assert counts[("docente", SEQUENCES[1])] == 1
    assert generate_assignments() == rows


def test_odd_group_sizes_remain_balanced_with_difference_at_most_one():
    rows = generate_assignments(students=5, teachers=1, seed=7)
    student_counts = Counter(row["secuencia"] for row in rows if row["rol"] == "estudiante")

    assert abs(student_counts[SEQUENCES[0]] - student_counts[SEQUENCES[1]]) <= 1


@pytest.mark.parametrize("students, teachers", [(-1, 2), (0, 0)])
def test_assignment_rejects_invalid_participant_counts(students, teachers):
    with pytest.raises(ValueError):
        generate_assignments(students, teachers)
