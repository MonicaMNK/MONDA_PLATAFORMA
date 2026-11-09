import pytest

from scripts.evaluate_rag_gemini_live import validate_gold_sources, validate_validation_fixture


def make_fixture():
    categories = (["factual"] * 40 + ["integration"] * 30
                  + ["no_evidence"] * 15 + ["adversarial"] * 15)
    queries = []
    for index, category in enumerate(categories):
        row = {
            "id": f"V{index + 1:02d}",
            "course": "Historia",
            "question": f"Consulta final nueva número {index + 1}",
            "category": category,
            "answerable": category in {"factual", "integration"},
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


def test_validation_fixture_rejects_gold_pdf_from_a_different_course():
    fixture = make_fixture()
    with pytest.raises(ValueError, match="no pertenece al curso"):
        validate_gold_sources(fixture, {"Historia": {"El Imperio Inca.pdf"}})

    validate_gold_sources(fixture, {"Historia": {"El Tahuantinsuyo.pdf"}})


def test_live_summary_lists_false_answers_and_separates_categories():
    from scripts.evaluate_rag_gemini_live import summarize

    fixture = make_fixture()
    query = fixture["queries"][70]
    results = [{
        "query_id": query["id"],
        "system_abstained": False,
        "system_answered": True,
        "citations": [],
        "generation_attempted": False,
        "generation_error": None,
        "answer": "respuesta",
        "retrieved_sources": [{"course": "Historia"}],
    }]

    summary = summarize(results, fixture["queries"])

    assert summary["false_answer_count"] == 1
    assert summary["false_answer_query_ids"] == [query["id"]]
    assert summary["category_metrics"]["no_evidence"]["answered"] == 1
    assert summary["cross_course_source_query_ids"] == []
    assert summary["no_evidence_correct_abstention_rate"] == 0
    assert summary["acceptance_checks"]["correct_abstention"] is False


def test_live_summary_does_not_count_generation_error_as_coverage_or_abstention():
    from scripts.evaluate_rag_gemini_live import summarize

    fixture = make_fixture()
    query = fixture["queries"][0]
    summary = summarize([{
        "query_id": query["id"],
        "system_abstained": False,
        "system_answered": False,
        "generation_error": "synthetic timeout",
        "generation_attempted": True,
        "answer": "",
        "citations": [],
        "retrieved_sources": [],
    }], fixture["queries"])

    assert summary["answer_coverage"] == 0
    assert summary["generation_errors"] == 1
    assert summary["category_metrics"]["factual"]["generation_errors"] == 1
