"""Pruebas de integridad del banco de validación RAG vigente."""

import json
from pathlib import Path


def normalize_cat(raw: str) -> str:
    c = (raw or "").strip().lower()
    if "fact" in c:
        return "factual"
    if "integ" in c:
        return "integracion"
    if "sin" in c or "no_evidence" in c or "unans" in c or "absten" in c or "out" in c:
        return "sin_evidencia"
    if "adv" in c or "inject" in c or "jail" in c:
        return "adversarial"
    return c


def test_current_rag_validation_bank_composition():
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

    assert len(items) == 100
    assert n_fact == 40
    assert n_int == 30
    assert n_no_ev == 15
    assert n_adv == 15