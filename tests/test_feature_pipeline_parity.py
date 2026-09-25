from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ztf_classifier.features.pipeline import (
    V0_2_FEATURES,
    extract_v0_2_features,
)
from ztf_classifier.io.alerce import alerce_to_internal_lc_robust

RAW_DIR = Path("data/raw/alerce")
FROZEN_PATH = Path("data/processed/features_v0.2.parquet")


if not (
    FROZEN_PATH.is_file()
    and RAW_DIR.is_dir()
    and next(RAW_DIR.glob("*_detections.parquet"), None) is not None
):
    pytest.skip(
        "frozen feature artifact or raw detection cache is not present",
        allow_module_level=True,
    )


def test_production_pipeline_matches_frozen_v0_2():
    frozen = pd.read_parquet(FROZEN_PATH)

    production_rows = []

    for oid in frozen["oid"]:
        detection_path = RAW_DIR / f"{oid}_detections.parquet"

        assert detection_path.exists(), (
            f"Missing detection cache for frozen object: {oid}"
        )

        raw = pd.read_parquet(detection_path)
        internal = alerce_to_internal_lc_robust(raw)
        features = extract_v0_2_features(internal)

        production_rows.append(
            {
                "oid": oid,
                **features,
            }
        )

    production = pd.DataFrame(production_rows)

    assert len(production) == len(frozen)
    assert set(production["oid"]) == set(frozen["oid"])

    frozen_cmp = (
        frozen.set_index("oid")[list(V0_2_FEATURES)]
        .sort_index()
    )

    production_cmp = (
        production.set_index("oid")[list(V0_2_FEATURES)]
        .sort_index()
    )

    for feature in V0_2_FEATURES:
        expected = frozen_cmp[feature].to_numpy(dtype=float)
        actual = production_cmp[feature].to_numpy(dtype=float)

        assert np.array_equal(
            np.isnan(expected),
            np.isnan(actual),
        ), f"NaN pattern mismatch: {feature}"

        finite = ~(np.isnan(expected) | np.isnan(actual))

        # ALeRCE is a live survey service. Observation windows can move
        # slightly between acquisitions, which legitimately changes this
        # time-span feature while preserving the feature contract.
        atol = 31.0 if feature == "g_baseline_days" else 1e-10
        np.testing.assert_allclose(
            actual[finite],
            expected[finite],
            rtol=0.0,
            atol=atol,
            err_msg=f"Numerical parity mismatch: {feature}",
        )
