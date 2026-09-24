diff --git a/src/ztf_classifier/io/alerce.py b/src/ztf_classifier/io/alerce.py
index 9b69dd7..bb0bb70 100644
--- a/src/ztf_classifier/io/alerce.py
+++ b/src/ztf_classifier/io/alerce.py
@@ -5,6 +5,44 @@
 import numpy as np
 import pandas as pd
 
+_REQUIRED_COLUMNS = {
+    "mjd",
+    "fid",
+    "magpsf_corr",
+    "sigmapsf_corr_ext",
+    "magpsf",
+    "sigmapsf",
+    "ra",
+    "dec",
+    "dubious",
+    "corrected",
+}
+
+
+def _coerce_bool_series(
+    series: pd.Series,
+    *,
+    column_name: str,
+) -> pd.Series:
+    """Parse boolean-like ALeRCE values without silent string coercion."""
+    values = series.astype("string").str.strip().str.lower()
+    truthy = values.isin({"true", "1", "yes", "y", "t"})
+    falsy = values.isin({"false", "0", "no", "n", "f", ""})
+    unknown = ~(truthy | falsy | values.isna())
+
+    if unknown.any():
+        bad_values = values[unknown].dropna().unique()[:10]
+        raise ValueError(
+            f"Column '{column_name}' contains non-boolean values: "
+            f"{bad_values.tolist()}"
+        )
+
+    return pd.Series(
+        truthy.fillna(False).to_numpy(dtype=bool),
+        index=series.index,
+        dtype=bool,
+    )
+
 
 def alerce_to_internal_lc_robust(
     detections: pd.DataFrame,
@@ -18,6 +56,13 @@ def alerce_to_internal_lc_robust(
     Raw ALeRCE columns are never overwritten.
     """
 
+    missing = _REQUIRED_COLUMNS - set(detections.columns)
+    if missing:
+        raise ValueError(
+            "ALeRCE detections are missing required columns: "
+            f"{sorted(missing)}"
+        )
+
     lc = detections.copy()
 
     mjd = pd.to_numeric(lc["mjd"], errors="coerce")
@@ -77,8 +122,14 @@ def alerce_to_internal_lc_robust(
                 lc["dec"],
                 errors="coerce",
             ).astype(float),
-            "dubious": lc["dubious"].astype(bool),
-            "corrected": lc["corrected"].astype(bool),
+            "dubious": _coerce_bool_series(
+                lc["dubious"],
+                column_name="dubious",
+            ),
+            "corrected": _coerce_bool_series(
+                lc["corrected"],
+                column_name="corrected",
+            ),
             "source": "ALeRCE",
         }
     )
diff --git a/src/ztf_classifier/models/inference.py b/src/ztf_classifier/models/inference.py
index 6cdfb0b..34bd5ac 100644
--- a/src/ztf_classifier/models/inference.py
+++ b/src/ztf_classifier/models/inference.py
@@ -131,6 +131,11 @@ def prepare_features(
                 "Frozen v0.2 model requires exactly 42 features."
             )
 
+        if X.isnull().all(axis=1).any():
+            raise ValueError(
+                "Dataset contains rows with all model features missing."
+            )
+
         return X
 
     def _load_feature_names(
@@ -159,7 +164,20 @@ def _load_feature_names(
 
         ordered = schema.sort_values(
             "feature_order"
-        )
+        ).copy()
+
+        if ordered["feature_order"].duplicated().any():
+            raise ValueError(
+                "Frozen feature schema contains duplicate feature_order values."
+            )
+
+        expected_order = list(range(1, 43))
+        actual_order = ordered["feature_order"].tolist()
+        if actual_order != expected_order:
+            raise ValueError(
+                "Frozen feature schema must use feature_order values "
+                "1 through 42."
+            )
 
         feature_names = ordered["feature"].astype(str).tolist()
 
diff --git a/tests/test_p0_validation.py b/tests/test_p0_validation.py
new file mode 100644
index 0000000..6eebdad
--- /dev/null
+++ b/tests/test_p0_validation.py
@@ -0,0 +1,148 @@
+import numpy as np
+import pandas as pd
+import pytest
+
+from ztf_classifier.io.alerce import alerce_to_internal_lc_robust
+
+
+def _detections(**overrides: object) -> pd.DataFrame:
+    values: dict[str, object] = {
+        "mjd": [59001, 59002],
+        "fid": [1, 1],
+        "magpsf_corr": [20.0, 21.0],
+        "sigmapsf_corr_ext": [0.1, 0.2],
+        "magpsf": [20.5, 21.5],
+        "sigmapsf": [0.15, 0.25],
+        "ra": [10.0, 10.0],
+        "dec": [20.0, 20.0],
+        "dubious": [False, False],
+        "corrected": [True, True],
+    }
+    values.update(overrides)
+    return pd.DataFrame(values)
+
+
+def test_alerce_boolean_strings_are_parsed_safely() -> None:
+    result = alerce_to_internal_lc_robust(
+        _detections(
+            dubious=["False", "True"],
+            corrected=["true", "false"],
+        )
+    )
+
+    assert result["dubious"].tolist() == [False, True]
+    assert result["corrected"].tolist() == [True, False]
+
+
+def test_alerce_rejects_unknown_boolean_values() -> None:
+    with pytest.raises(ValueError, match="non-boolean values"):
+        alerce_to_internal_lc_robust(
+            _detections(dubious=["not-a-bool", "False"])
+        )
+
+
+def test_alerce_rejects_missing_required_columns() -> None:
+    detections = _detections().drop(columns=["corrected"])
+
+    with pytest.raises(ValueError, match="missing required columns"):
+        alerce_to_internal_lc_robust(detections)
+
+
+def test_alerce_preserves_nan_boolean_as_false() -> None:
+    result = alerce_to_internal_lc_robust(
+        _detections(dubious=[np.nan, "0"])
+    )
+
+    assert result["dubious"].tolist() == [False, False]
+
+
+def _feature_schema() -> pd.DataFrame:
+    return pd.DataFrame(
+        {
+            "feature_order": list(range(1, 43)),
+            "feature": [f"feature_{index}" for index in range(1, 43)],
+        }
+    )
+
+
+def _inference_engine(tmp_path):
+    from ztf_classifier.models.inference import XGBoostInferenceEngine
+
+    schema_path = tmp_path / "feature_schema.parquet"
+    _feature_schema().to_parquet(schema_path, index=False)
+    return XGBoostInferenceEngine(
+        model=object(),
+        feature_schema_path=schema_path,
+    )
+
+
+def test_inference_rejects_rows_with_all_features_missing(tmp_path) -> None:
+    engine = _inference_engine(tmp_path)
+    dataset = pd.DataFrame(
+        {
+            f"feature_{index}": [np.nan]
+            for index in range(1, 43)
+        }
+    )
+
+    with pytest.raises(
+        ValueError,
+        match="all model features missing",
+    ):
+        engine.prepare_features(dataset)
+
+
+def test_inference_rejects_duplicate_feature_order(tmp_path) -> None:
+    schema = _feature_schema()
+    schema.loc[1, "feature_order"] = schema.loc[0, "feature_order"]
+
+    schema_path = tmp_path / "duplicate_order.parquet"
+    schema.to_parquet(schema_path, index=False)
+
+    from ztf_classifier.models.inference import XGBoostInferenceEngine
+
+    engine = XGBoostInferenceEngine(
+        model=object(),
+        feature_schema_path=schema_path,
+    )
+
+    dataset = pd.DataFrame(
+        {
+            f"feature_{index}": [float(index)]
+            for index in range(1, 43)
+        }
+    )
+
+    with pytest.raises(
+        ValueError,
+        match="duplicate feature_order",
+    ):
+        engine.prepare_features(dataset)
+
+
+def test_inference_rejects_non_contract_feature_order(tmp_path) -> None:
+    schema = _feature_schema()
+    schema.loc[0, "feature_order"] = 0
+
+    schema_path = tmp_path / "invalid_order.parquet"
+    schema.to_parquet(schema_path, index=False)
+
+    from ztf_classifier.models.inference import XGBoostInferenceEngine
+
+    engine = XGBoostInferenceEngine(
+        model=object(),
+        feature_schema_path=schema_path,
+    )
+
+    dataset = pd.DataFrame(
+        {
+            f"feature_{index}": [float(index)]
+            for index in range(1, 43)
+        }
+    )
+
+    with pytest.raises(
+        ValueError,
+        match="1 through 42",
+    ):
+        engine.prepare_features(dataset)
