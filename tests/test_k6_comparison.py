import pytest

from scripts.compare_k6_summaries import compare_summaries


def summary(p95, errors=0.0, acceptance_failures=0.0):
    return {"metrics": {
        "http_req_duration{phase:measurement}": {"values": {"p(95)": p95}},
        "http_req_failed{phase:measurement}": {"values": {"rate": errors}},
        "acceptance_failures{phase:measurement}": {"values": {"rate": acceptance_failures}},
    }}


def test_k6_comparison_passes_within_latency_error_and_degradation_limits():
    result = compare_summaries(summary(500), summary(580, 0.005, 0.0))

    assert result["degradation_pct"] == 16.0
    assert result["passed"] is True


@pytest.mark.parametrize(
    "target",
    [summary(801), summary(600, 0.01), summary(650, 0.0, 0.01)],
)
def test_k6_comparison_fails_when_any_acceptance_limit_is_exceeded(target):
    assert compare_summaries(summary(500), target)["passed"] is False


def test_k6_comparison_rejects_missing_metrics_and_zero_baseline():
    with pytest.raises(ValueError, match="mayor que cero"):
        compare_summaries(summary(0), summary(100))
    with pytest.raises(ValueError, match="No se encontró"):
        compare_summaries({"metrics": {}}, summary(100))
