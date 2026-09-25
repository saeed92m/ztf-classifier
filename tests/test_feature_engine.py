from __future__ import annotations

import pandas as pd
import pytest

from ztf_classifier.features.engine import ScientificFeatureEngine


def _observations() -> pd.DataFrame:
    rows = []
    for fid in (1, 2):
        for index in range(10):
            rows.append(
                {
                    "mjd": 60000.0 + index,
                    "fid": fid,
                    "mag": 19.0 + 0.01 * index + 0.2 * (fid - 1),
                    "magerr": 0.05,
                }
            )
    return pd.DataFrame(rows)


def test_native_engine_preserves_v02_contract_and_provenance() -> None:
    result = ScientificFeatureEngine().compute(
        _observations(),
        parameters={"cutoff_mjd": 60009.0},
    )

    assert result.feature_schema_version == "v0.2"
    assert len(result.values) == 42
    assert result.feature_names[0] == "g_baseline_days"
    assert result.provenance.backend == "native"
    assert result.provenance.feature_schema_version == "v0.2"
    assert result.provenance.parameters == {"cutoff_mjd": 60009.0}
    assert len(result.provenance.input_observation_sha256) == 64


def test_unknown_backend_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown feature backend"):
        ScientificFeatureEngine().compute(
            _observations(),
            backend="missing",
        )


def test_empty_observations_are_rejected() -> None:
    with pytest.raises(ValueError, match="at least one row"):
        ScientificFeatureEngine().compute(pd.DataFrame())


class _TestBackend:
    name = "test"
    software_version = "test-1.0"
    feature_schema_version = "test.v1"

    def extract(self, observations, *, parameters):
        return {"value": 1.0}


def test_feature_engine_supports_explicit_backend_registration() -> None:
    engine = ScientificFeatureEngine()
    engine.register_backend(_TestBackend())

    assert engine.list_backends() == ("native", "test")
    assert engine.backend_metadata("test") == {
        "name": "test",
        "software_version": "test-1.0",
        "feature_schema_version": "test.v1",
    }
    assert engine.all_backend_metadata()[1]["name"] == "test"


def test_feature_engine_rejects_backend_collision() -> None:
    engine = ScientificFeatureEngine()

    with pytest.raises(ValueError, match="already registered"):
        engine.register_backend(NativeV0_2Backend())


def test_feature_engine_rejects_incomplete_backend() -> None:
    class InvalidBackend:
        name = "invalid"

        def extract(self, observations, *, parameters):
            return {}

    engine = ScientificFeatureEngine()

    with pytest.raises(ValueError, match="require name"):
        engine.register_backend(InvalidBackend())
