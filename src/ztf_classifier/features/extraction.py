"""Object-level v0.1 feature extraction."""

from pathlib import Path

import pandas as pd

from ztf_classifier.features.basic import basic_band_features
from ztf_classifier.features.cross_band import basic_cross_band_features
from ztf_classifier.features.morphology import phase_morphology_features
from ztf_classifier.features.periodicity import lomb_scargle_features
from ztf_classifier.io.alerce import alerce_to_internal_lc_robust
from ztf_classifier.preprocessing.lightcurve import prepare_band_lightcurve


def extract_features_for_object(oid, raw_lc_dir):
    detection_path = Path(raw_lc_dir) / f"{oid}_detections.parquet"
    if not detection_path.exists():
        raise FileNotFoundError(
            f"Detection cache not found: {detection_path}"
        )

    internal = alerce_to_internal_lc_robust(
        pd.read_parquet(detection_path)
    )
    g = prepare_band_lightcurve(internal, 1)
    r = prepare_band_lightcurve(internal, 2)

    features = {
        "oid": oid,
        "feature_version": "v0.1",
        "n_valid_total": len(internal),
        "n_g": len(g),
        "n_r": len(r),
        "has_g": len(g) > 0,
        "has_r": len(r) > 0,
        "has_both_bands": len(g) > 0 and len(r) > 0,
    }

    if len(g) >= 10:
        features.update(basic_band_features(g, "g"))

    if len(r) >= 10:
        features.update(basic_band_features(r, "r"))

    if len(g) >= 30:
        ls_g = lomb_scargle_features(g, "g")
        features.update(ls_g)
        features.update(
            phase_morphology_features(
                g,
                ls_g["g_ls_best_period_days"],
                "g",
            )
        )

    if len(r) >= 30:
        ls_r = lomb_scargle_features(r, "r")
        features.update(ls_r)
        features.update(
            phase_morphology_features(
                r,
                ls_r["r_ls_best_period_days"],
                "r",
            )
        )

    if len(g) > 0 and len(r) > 0:
        features.update(basic_cross_band_features(g, r))

    return features
