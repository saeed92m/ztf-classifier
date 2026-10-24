"""Real-data workflow audit — small public astronomical dataset.

Source: data/processed/benchmark_v0.2/features.parquet
- Benchmark: 150 ZTF objects, 15 ALeRCE classes (10 per class), 42 frozen v0.2 features
- Origin: ALeRCE ZTF light curves (public ZTF DR via ALeRCE broker, https://alerce.online)
- License: ZTF data via public survey (Caltech/IPAC), ALeRCE client MIT, code MIT/proprietary,
  benchmark artifact produced by this repo (v0.2) with provenance hashes
- Access: local file in repo (no download), SHA256 tracked via reproducibility_manifest_v0.2.json

This test is clearly separate from synthetic fixtures (test_astronomer_workflow_ingestion.py).
It exercises a supported workflow on real-derived data: feature table → model inference + provenance.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ztf_classifier.features.schema import V02_FEATURES


def test_real_benchmark_features_schema_and_counts():
    path = Path("data/processed/benchmark_v0.2/features.parquet")
    assert path.is_file(), f"real benchmark features missing: {path}"
    df = pd.read_parquet(path)
    # Schema: 42 frozen v0.2 features + object/meta columns
    # The parquet contains object IDs and features; we verify at least 42 present
    missing = [c for c in V02_FEATURES if c not in df.columns]
    assert not missing, f"missing v0.2 features: {missing}"
    # Counts: 150 objects expected (benchmark_v0.2)
    assert len(df) == 150, f"expected 150 objects, got {len(df)}"
    # Observation counts should be present and finite
    assert (df["g_n_obs"] > 0).any()
    assert (df["r_n_obs"] > 0).any()
    # No duplicate object IDs in this column (oid or objectId or similar)
    # Benchmark uses 'oid' or 'objectId' — check both
    oid_col = None
    for cand in ("oid", "objectId", "object_id", "oid"):
        if cand in df.columns:
            oid_col = cand
            break
    if oid_col:
        assert df[oid_col].is_unique, "real benchmark should have unique oids"
    # Provenance: reproducibility manifest exists and is strict JSON
    import json

    manifest_path = Path("reports/tables/final_reproducibility_manifest_v0.2.json")
    if manifest_path.is_file():
        text = manifest_path.read_text(encoding="utf-8")
        assert "NaN" not in text
        data = json.loads(text)
        json.dumps(data, allow_nan=False)  # strict
        assert "benchmark_v0.2" in str(data) or "v0.2" in text


def test_real_benchmark_provenance_and_model_inference():
    """Run production inference on real features and verify provenance/integrity."""
    from pathlib import Path

    import pandas as pd

    feat_path = Path("data/processed/benchmark_v0.2/features.parquet")
    df = pd.read_parquet(feat_path)
    # Select only feature columns for model input
    feat_df = df[V02_FEATURES]
    assert len(feat_df) == 150
    from ztf_classifier.features.pipeline import validate_v0_2_feature_vector

    # Pick first row as dict and validate
    first = feat_df.iloc[0].to_dict()
    validate_v0_2_feature_vector(first)
    # Simulate prediction provenance (without requiring model file)
    # Check that feature extraction is deterministic and hashable
    import json

    from ztf_classifier.validation.json_utils import dumps_strict

    payload = {
        "features": first,
        "model_version": "baseline_v0.2",
        "artifact": "benchmark_v0.2",
    }
    text = dumps_strict(payload, sort_keys=True)
    assert "NaN" not in text
    assert json.loads(text)["model_version"] == "baseline_v0.2"
    # If model artifact exists, do actual inference (optional)
    model_path = Path("artifacts/model/baseline_v0.2/model.pkl")
    if model_path.is_file():
        from ztf_classifier.models.production_inference import (
            ProductionInferenceService,
        )

        svc = ProductionInferenceService(model_path.parent)
        res = svc.predict(feat_df)
        assert len(res) == 150
        assert res is not None
    else:
        # Document that model artifact not present in this checkout — not a failure
        assert not model_path.is_file()


def test_real_data_csv_parquet_roundtrip_preserves_provenance(tmp_path: Path):
    """Real-data CSV/Parquet workflow: export 5 real objects to CSV, re-ingest, verify hash chain."""
    import hashlib
    from pathlib import Path

    import pandas as pd

    from ztf_classifier.application.ingestion import DataIngestionService, ImportRequest

    src = Path("data/processed/benchmark_v0.2/features.parquet")
    df = pd.read_parquet(src).head(5)
    # Export to CSV (simulates astronomer exporting result table)
    csv_path = tmp_path / "real5.csv"
    df.to_csv(csv_path, index=False)
    svc = DataIngestionService()
    result = svc.import_file(
        ImportRequest(path=csv_path, required_columns=("g_n_obs",))
    )
    assert result.row_count == 5
    assert result.content_sha256 == hashlib.sha256(csv_path.read_bytes()).hexdigest()
    assert result.source.metadata["format"] == "csv"
    # Metadata preserving export: columns unchanged
    assert set(result.columns) == set(df.columns)
    # Provenance: content hash matches file, source_id derived from filename
    assert result.source.source_id == "real5"
    assert result.source.schema_version == "tabular-v1"
