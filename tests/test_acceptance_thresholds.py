from scripts.validation_thresholds import REQUIREMENTS


def test_rnf01_and_oe2_thresholds_are_centralized_in_machine_readable_source():
    assert REQUIREMENTS["RNF-01"]["transactional_api_p95_ms"] == 800
    assert REQUIREMENTS["RNF-01"]["max_http_error_rate"] == 0.01
    assert REQUIREMENTS["RNF-01"]["max_degradation_percent"] == 20
    assert REQUIREMENTS["OE2"]["final_query_count"] == 100
    assert sum(REQUIREMENTS["OE2"]["category_counts"].values()) == 100
    assert REQUIREMENTS["RNF-06"]["sus_minimum"] == 68
    assert REQUIREMENTS["RNF-08"]["minimum_aiken_v"] == 0.8
