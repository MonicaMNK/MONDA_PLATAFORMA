from pathlib import Path

from scripts.evaluate_rag_gemini_live import CALIBRATION_PATH, build_parser

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CALIBRATION = ROOT / "data" / "rag_calibration_gemini_abstencion_20261101.json"


def test_default_calibration_points_to_current_artifact():
    """El evaluador usa por defecto el artefacto de calibración actual."""
    assert CALIBRATION_PATH == EXPECTED_CALIBRATION
    assert CALIBRATION_PATH.exists()


def test_parser_default_calibration_is_current_artifact():
    """El argumento --calibration tiene como default el artefacto actual."""
    parser = build_parser()
    args = parser.parse_args([])
    assert args.calibration == EXPECTED_CALIBRATION


def test_parser_respects_explicit_calibration():
    """Pasar --calibration con otro archivo se respeta en lugar del default."""
    parser = build_parser()
    alternate = ROOT / "data" / "rag_calibration_gemini_20261101.json"
    args = parser.parse_args(["--calibration", str(alternate)])
    assert args.calibration == alternate
    assert args.calibration != EXPECTED_CALIBRATION


def test_parser_loads_alternate_calibration_artifact():
    """El parser acepta y carga un artefacto de calibración alternativo existente."""
    parser = build_parser()
    alternate = ROOT / "data" / "rag_calibration_gemini_20261101.json"
    args = parser.parse_args(["--calibration", str(alternate)])
    import json
    calibration = json.loads(args.calibration.read_bytes())
    assert calibration.get("status") == "complete"
