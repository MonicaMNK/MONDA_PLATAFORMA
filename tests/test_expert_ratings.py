import pytest

from scripts.analyze_expert_ratings import aiken_v, analyze_rows, icc_absolute_agreement


def test_aiken_v_reports_scale_normalized_item_validity():
    assert aiken_v([4, 4, 3], 1, 4) == pytest.approx(0.8888889)
    assert aiken_v([1, 1, 1], 1, 4) == 0


def test_expert_analysis_reports_item_v_and_absolute_agreement():
    rows = [
        {"item_id": "I1", "expert_id": "E1", "rating": "4"},
        {"item_id": "I1", "expert_id": "E2", "rating": "4"},
        {"item_id": "I1", "expert_id": "E3", "rating": "4"},
        {"item_id": "I2", "expert_id": "E1", "rating": "2"},
        {"item_id": "I2", "expert_id": "E2", "rating": "2"},
        {"item_id": "I2", "expert_id": "E3", "rating": "2"},
    ]

    result = analyze_rows(rows)

    assert result["aiken_v_by_item"] == {"I1": 1.0, "I2": 0.3333}
    assert result["icc_2_1_absolute_agreement"] == 1.0


def test_expert_analysis_rejects_incomplete_or_duplicate_ratings():
    incomplete = [
        {"item_id": "I1", "expert_id": "E1", "rating": "3"},
        {"item_id": "I1", "expert_id": "E2", "rating": "4"},
        {"item_id": "I2", "expert_id": "E1", "rating": "2"},
    ]
    with pytest.raises(ValueError, match="todos los ítems"):
        analyze_rows(incomplete)

    duplicate = [
        {"item_id": "I1", "expert_id": "E1", "rating": "3"},
        {"item_id": "I1", "expert_id": "E1", "rating": "4"},
    ]
    with pytest.raises(ValueError, match="único"):
        analyze_rows(duplicate)


def test_icc_rejects_constant_matrix():
    with pytest.raises(ValueError, match="variación"):
        icc_absolute_agreement([[3, 3], [3, 3]])
