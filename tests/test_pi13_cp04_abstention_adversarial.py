"""
Pruebas de validación de banco y guardrails de abstención/adversariales para CP04 (ES04).
Verifica:
  1. Composición exacta del subconjunto CP04 en data/rag_validation_100.json (15 sin_evidencia + 13 adversarial = 28).
  2. Política de abstención obligatoria ante falta de evidencia (maxScore < tau o sin fuentes).
"""

import json
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


def test_cp04_bank_composition_and_denominators():
    bank_path = Path("data/rag_validation_100.json")
    assert bank_path.exists(), "Debe existir data/rag_validation_100.json"

    raw = json.loads(bank_path.read_text(encoding="utf-8"))
    items = raw if isinstance(raw, list) else raw.get("queries") or raw.get("items") or raw.get("data")
    assert isinstance(items, list)

    cats = [normalize_cat(it.get("category") or it.get("categoria") or it.get("type") or it.get("tipo")) for it in items]
    n_no_ev = sum(1 for c in cats if c == "sin_evidencia")
    n_adv = sum(1 for c in cats if c == "adversarial")

    assert n_no_ev == 15, f"Se esperaban 15 consultas sin_evidencia, encontradas: {n_no_ev}"
    assert n_adv == 13, f"Se esperaban 13 consultas adversariales, encontradas: {n_adv}"
    assert (n_no_ev + n_adv) == 28


def test_cp04_abstention_and_adversarial_guardrail_logic():
    from scripts.ejecutar_cp04_cp07 import CONFIGURACION_CONGELADA, is_abstention_response

    assert CONFIGURACION_CONGELADA["similarity_threshold_tau"] == 0.42
    canonical = CONFIGURACION_CONGELADA["abstention_canonical_phrase"]

    assert is_abstention_response(canonical, evidence_sufficient=False) is True
    assert is_abstention_response("Según el documento [F1], la respuesta es X.", evidence_sufficient=True) is False