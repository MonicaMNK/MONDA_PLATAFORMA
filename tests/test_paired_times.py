import pytest

from scripts.analyze_paired_times import analyze_pairs, hodges_lehmann, rank_biserial


def test_hodges_lehmann_and_rank_biserial_signs_are_explicit():
    differences = [4.0, 6.0, 8.0]
    assert hodges_lehmann(differences) == 6.0
    assert rank_biserial(differences) == 1.0
    assert rank_biserial([-4.0, -6.0, -8.0]) == -1.0


def test_paired_time_summary_has_reproducible_bootstrap_interval():
    rows = [
        {"participant_id": "P01", "manual_seconds": "20", "monda_seconds": "10"},
        {"participant_id": "P02", "manual_seconds": "18", "monda_seconds": "12"},
        {"participant_id": "P03", "manual_seconds": "30", "monda_seconds": "20"},
    ]
    first = analyze_pairs(rows, bootstrap_samples=1000, seed=7)
    second = analyze_pairs(rows, bootstrap_samples=1000, seed=7)

    assert first == second
    assert first["hodges_lehmann_seconds"] == 9.0
    assert first["hodges_lehmann_bootstrap_ci_95_seconds"][0] <= 9.0
    assert first["hodges_lehmann_bootstrap_ci_95_seconds"][1] >= 9.0
    assert first["wilcoxon_rank_biserial_correlation"] == 1.0


def test_paired_time_summary_requires_unique_pseudonymous_ids_and_valid_durations():
    repeated = [
        {"participant_id": "P01", "manual_seconds": "1", "monda_seconds": "2"},
        {"participant_id": "P01", "manual_seconds": "3", "monda_seconds": "2"},
    ]
    with pytest.raises(ValueError, match="una sola vez"):
        analyze_pairs(repeated, bootstrap_samples=1000)

    invalid = [
        {"participant_id": "P01", "manual_seconds": "-1", "monda_seconds": "2"},
        {"participant_id": "P02", "manual_seconds": "3", "monda_seconds": "2"},
    ]
    with pytest.raises(ValueError, match="no negativos"):
        analyze_pairs(invalid, bootstrap_samples=1000)
