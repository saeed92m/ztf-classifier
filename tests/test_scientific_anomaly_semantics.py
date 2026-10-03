import numpy as np
import pytest

from ztf_classifier.models.scientific_anomaly import ScientificAnomalyResult


def test_scientific_anomaly_is_explicitly_independent_from_ood() -> None:
    result = ScientificAnomalyResult(
        status="available",
        score=np.array([0.25, 0.9]),
        flags=np.array([False, True]),
        method="domain-rule-v1",
        evidence_version="1.0",
    )
    assert result.sample_count == 2
    assert result.method == "domain-rule-v1"


def test_unavailable_scientific_anomaly_has_no_implicit_score() -> None:
    result = ScientificAnomalyResult(status="not_evaluated")
    assert result.sample_count == 0
    assert result.score is None
    assert result.flags is None


def test_unavailable_scientific_anomaly_cannot_hide_data() -> None:
    with pytest.raises(ValueError, match="cannot carry"):
        ScientificAnomalyResult(
            status="unavailable",
            score=np.array([0.5]),
            flags=np.array([True]),
        )
