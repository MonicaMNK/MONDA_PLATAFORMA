from __future__ import annotations

import argparse
import json
from pathlib import Path


def find_metric(summary: dict, name: str) -> dict:
    metrics = summary.get("metrics", {})
    candidates = [
        f"{name}{{phase:measurement}}",
        name,
    ]
    for candidate in candidates:
        if candidate in metrics:
            return metrics[candidate].get("values", {})
    raise ValueError(f"No se encontró la métrica k6 {name} de measurement.")


def compare_summaries(baseline: dict, target: dict, p95_limit_ms: float = 800.0,
                      error_rate_limit: float = 0.01, degradation_limit_pct: float = 20.0) -> dict:
    baseline_p95 = float(find_metric(baseline, "http_req_duration")["p(95)"])
    target_p95 = float(find_metric(target, "http_req_duration")["p(95)"])
    target_error_rate = float(find_metric(target, "http_req_failed")["rate"])
    target_acceptance_fail_rate = float(find_metric(target, "acceptance_failures")["rate"])
    if baseline_p95 <= 0:
        raise ValueError("El p95 de referencia debe ser mayor que cero.")
    degradation = ((target_p95 - baseline_p95) / baseline_p95) * 100
    checks = {
        "target_p95_within_limit": target_p95 <= p95_limit_ms,
        "target_http_error_rate_within_limit": target_error_rate < error_rate_limit,
        "target_acceptance_failure_rate_within_limit": target_acceptance_fail_rate < error_rate_limit,
        "degradation_within_limit": degradation <= degradation_limit_pct,
    }
    return {
        "baseline_p95_ms": round(baseline_p95, 2),
        "target_p95_ms": round(target_p95, 2),
        "degradation_pct": round(degradation, 2),
        "target_http_error_rate": target_error_rate,
        "target_acceptance_failure_rate": target_acceptance_fail_rate,
        "limits": {
            "p95_ms": p95_limit_ms,
            "error_rate": error_rate_limit,
            "degradation_pct": degradation_limit_pct,
        },
        "checks": checks,
        "passed": all(checks.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compara salidas k6 de baja y alta concurrencia para RNF-01.")
    parser.add_argument("baseline_25_vu", type=Path)
    parser.add_argument("target_50_vu", type=Path)
    parser.add_argument("--output", type=Path, default=Path("k6_comparison.json"))
    args = parser.parse_args()
    baseline = json.loads(args.baseline_25_vu.read_text(encoding="utf-8"))
    target = json.loads(args.target_50_vu.read_text(encoding="utf-8"))
    result = compare_summaries(baseline, target)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
