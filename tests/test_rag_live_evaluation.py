import pytest

from scripts.evaluate_rag_gemini_live import validate_validation_fixture


def make_fixture():
    queries = []
    for index in range(100):
        row = {
            "id": f"V{index + 1:02d}",
            "course": "Historia",
            "question": f"Consulta final nueva número {index + 1}",
            "answerable": index % 2 == 0,
        }
        if row["answerable"]:
            row["gold_pdf"] = "El Tahuantinsuyo.pdf"
        queries.append(row)
    return {"queries": queries}


def calibration_fixture():
    return {"queries": [{"id": "Q01", "question": "Consulta calibrada"}]}


def test_validation_fixture_accepts_100_independent_queries():
    validate_validation_fixture(make_fixture(), calibration_fixture())


@pytest.mark.parametrize("mutation", ["duplicate_id", "duplicate_question", "reused_calibration_id"])
def test_validation_fixture_rejects_leakage_and_duplicate_records(mutation):
    fixture = make_fixture()
    if mutation == "duplicate_id":
        fixture["queries"][1]["id"] = fixture["queries"][0]["id"]
    elif mutation == "duplicate_question":
        fixture["queries"][1]["question"] = fixture["queries"][0]["question"].upper()
    else:
        fixture["queries"][1]["id"] = "Q01"

    with pytest.raises(ValueError):
        validate_validation_fixture(fixture, calibration_fixture())


def test_validation_fixture_rejects_missing_gold_source():
    fixture = make_fixture()
    fixture["queries"][0].pop("gold_pdf")

    with pytest.raises(ValueError, match="gold_pdf"):
        validate_validation_fixture(fixture, calibration_fixture())
