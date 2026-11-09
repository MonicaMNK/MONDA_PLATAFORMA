import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_each_objective_maps_exactly_four_executable_reference_cases():
    traceability = json.loads((ROOT / "data/acceptance_traceability.json").read_text(encoding="utf-8"))

    for objective in ("OE1", "OE3"):
        cases = traceability["objectives"][objective]
        assert len(cases) == 4
        assert len({case["case"] for case in cases}) == 4
        for case in cases:
            test_path = ROOT / case["test_file"]
            assert test_path.is_file()
            tree = ast.parse(test_path.read_text(encoding="utf-8"))
            test_names = {node.name for node in ast.walk(tree)
                          if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
            assert case["test"] in test_names

    mapped_cases = [case["case"] for cases in traceability["objectives"].values()
                    for case in cases]
    assert all("CP11" not in case and "D07" not in case for case in mapped_cases)
