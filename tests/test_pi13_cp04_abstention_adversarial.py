"""
Pruebas de validación de banco y guardrails de abstención/adversariales para CP04 (ES04).
Verifica:
  1. Composición exacta del subconjunto CP04 en data/rag_validation_100.json (15 sin_evidencia + 13 adversarial = 28).
  2. Política de abstención obligatoria ante falta de evidencia (maxScore < tau o sin fuentes).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


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
    assert n_adv == 15, f"Se esperaban 15 consultas adversariales, encontradas: {n_adv}"
    assert (n_no_ev + n_adv) == 30


def test_cp04_abstention_and_adversarial_guardrail_logic():
    from types import SimpleNamespace

    from backend.app.services.rag_service import _evidence_is_sufficient

    assert not _evidence_is_sufficient([], threshold=0.5)
    assert _evidence_is_sufficient([SimpleNamespace(score=0.7)], threshold=0.7)
    assert not _evidence_is_sufficient(
        [SimpleNamespace(score=0.7), SimpleNamespace(score=0.69)],
        threshold=0.5,
        min_margin=0.05,
    )