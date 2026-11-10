from scripts.evaluate_rag_gemini_live import summarize


def test_evaluador_calcula_precision_f1_con_fuente_valida():
    """El resumen del evaluador cuenta [F1] respaldada por una fuente válida."""
    results = [
        {
            "query_id": "OE2-C1",
            "course": "Historia",
            "category": "factual",
            "answer": "El sistema nervioso se divide en dos subsistemas [F1].",
            "citations": [
                {
                    "marker": "F1",
                    "valid_source_ref": True,
                    "pdf": "El Sistema Nervioso.pdf",
                    "matches_gold_pdf": True,
                }
            ],
            "generation_attempted": True,
            "generation_error": None,
            "system_abstained": False,
            "system_answered": True,
            "retrieved_sources": [{"course": "Historia", "pdf": "El Sistema Nervioso.pdf"}],
        }
    ]
    fixture = [
        {
            "id": "OE2-C1",
            "course": "Historia",
            "category": "factual",
            "answerable": True,
            "gold_pdf": "El Sistema Nervioso.pdf",
        }
    ]
    summary = summarize(results, fixture)

    assert summary["queries_evaluated"] == 1
    assert summary["pdf_level_citation_precision"] == 1.0
    assert summary["valid_citation_reference_rate"] == 1.0


def test_evaluador_calcula_abstencion_correcta_sin_evidencia():
    """El resumen del evaluador cuenta como correcta la abstención sin evidencia."""
    results = [
        {
            "query_id": "OE2-C2",
            "category": "no_evidence",
            "answer": "No encuentro evidencia suficiente en los materiales autorizados de este curso para responder con confianza.",
            "system_abstained": True,
            "system_answered": False,
            "generation_attempted": False,
            "generation_error": None,
            "citations": [],
        }
    ]
    fixture = [
        {
            "id": "OE2-C2",
            "course": "Historia",
            "category": "no_evidence",
            "answerable": False,
            "gold_pdf": None,
        }
    ]
    summary = summarize(results, fixture)

    assert summary["controls_evaluated"] == 1
    assert summary["correct_abstention"] == 1.0
    assert summary["false_answer_count"] == 0


def test_evaluador_detecta_fuentes_cruzadas_en_caso_adversarial():
    """El resumen del evaluador detecta fuentes de otro curso; no prueba el endpoint."""
    results = [
        {
            "query_id": "OE2-C3",
            "course": "Historia",
            "category": "adversarial",
            "answer": "Respuesta inventada sin soporte.",
            "system_abstained": False,
            "system_answered": True,
            "retrieved_sources": [{"course": "Biología"}],
            "citations": [],
            "generation_attempted": True,
            "generation_error": None,
        }
    ]
    fixture = [
        {
            "id": "OE2-C3",
            "course": "Historia",
            "category": "adversarial",
            "answerable": False,
            "gold_pdf": None,
        }
    ]
    summary = summarize(results, fixture)

    assert summary["adversarial_pass_rate"] == 0.0
    assert "OE2-C3" in summary["cross_course_source_query_ids"]


def test_validador_acepta_fixture_de_cien_consultas_distintas():
    """El validador acepta 100 consultas de ejemplo con IDs y preguntas distintos."""
    from scripts.evaluate_rag_gemini_live import validate_validation_fixture

    categories = (
        ["factual"] * 40 + ["integration"] * 30
        + ["no_evidence"] * 15 + ["adversarial"] * 15
    )
    queries = []
    for index, category in enumerate(categories):
        row = {
            "id": f"V{index + 1:02d}",
            "course": "Historia",
            "question": f"Consulta final independiente número {index + 1}",
            "category": category,
            "answerable": category in {"factual", "integration"},
        }
        if row["answerable"]:
            row["gold_pdf"] = "El Tahuantinsuyo.pdf"
        queries.append(row)
    fixture = {"queries": queries}
    calibration = {"queries": [{"id": "Q01", "question": "Consulta calibrada"}]}

    validate_validation_fixture(fixture, calibration)

    assert len(fixture["queries"]) == 100
    assert len({q["id"] for q in queries}) == 100
    assert len({q["question"] for q in queries}) == 100
