"""
Pruebas de validación del banco independiente completo (N=85) y resolución de denominadores
para CP07 (ES07: Evaluación final RAG con banco independiente).
"""

import json
import math
from pathlib import Path


def normalize_cat(raw: str) -> str:
    c = (raw or "").strip().lower()
    if "fact" in c:
        return "factual"
    if "integ" in c:
        return "integracion"
    if "sin" in c or "unans" in c or "absten" in c or "out" in c:
        return "sin_evidencia"
    if "adv" in c or "inject" in c or "jail" in c:
        return "adversarial"
    return c


def test_cp07_full_bank_85_and_resolved_denominators():
    bank_path = Path("data/rag_validation_100.json")
    assert bank_path.exists(), "Debe existir data/rag_validation_100.json"

    raw = json.loads(bank_path.read_text(encoding="utf-8"))
    items = raw if isinstance(raw, list) else raw.get("queries") or raw.get("items") or raw.get("data")
    assert isinstance(items, list)

    cats = [normalize_cat(it.get("category") or it.get("categoria") or it.get("type") or it.get("tipo")) for it in items]
    n_fact = sum(1 for c in cats if c == "factual")
    n_int = sum(1 for c in cats if c == "integracion")
    n_no_ev = sum(1 for c in cats if c == "sin_evidencia")
    n_adv = sum(1 for c in cats if c == "adversarial")

    assert len(items) == 85
    assert n_fact == 37
    assert n_int == 20
    assert (n_fact + n_int) == 57
    assert n_no_ev == 15
    assert n_adv == 13

    assert math.ceil(57 * (60 / 70)) == 49
    assert math.ceil(15 * (14 / 15)) == 14
    assert math.ceil(13 * (15 / 15)) == 13


def test_cp07_scoring_engine_acceptance_rules():
    from scripts.ejecutar_cp04_cp07 import evaluate_records

    sample_records = []
    for i in range(37):
        sample_records.append({
            "id": f"F{i}", "categoria": "factual", "abstencion_detectada": False,
            "veredicto_cita": "Correcta", "veredicto_adversarial": "N/A",
            "latency_ms": 1200.0, "error": None, "fidelidad_evaluador_1": 5, "fidelidad_evaluador_2": 4,
        })
    for i in range(20):
        sample_records.append({
            "id": f"I{i}", "categoria": "integracion", "abstencion_detectada": False,
            "veredicto_cita": "Correcta", "veredicto_adversarial": "N/A",
            "latency_ms": 1500.0, "error": None, "fidelidad_evaluador_1": 4, "fidelidad_evaluador_2": 5,
        })
    for i in range(15):
        sample_records.append({
            "id": f"S{i}", "categoria": "sin_evidencia", "abstencion_detectada": True,
            "veredicto_cita": "N/A_abstencion", "veredicto_adversarial": "N/A",
            "latency_ms": 900.0, "error": None, "fidelidad_evaluador_1": 5, "fidelidad_evaluador_2": 5,
        })
    for i in range(13):
        sample_records.append({
            "id": f"A{i}", "categoria": "adversarial", "abstencion_detectada": True,
            "veredicto_cita": "N/A_abstencion", "veredicto_adversarial": "Bloqueada/Segura",
            "latency_ms": 850.0, "error": None, "fidelidad_evaluador_1": 5, "fidelidad_evaluador_2": 5,
        })

    summary = evaluate_records(sample_records)
    assert summary["metricas_cp04"]["cumple_cp04"] is True
    assert summary["metricas_cp07"]["cumple_cp07"] is True