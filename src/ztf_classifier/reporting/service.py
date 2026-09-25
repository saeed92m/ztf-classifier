"""Deterministic scientific report generation over durable results."""

from __future__ import annotations

import json
from typing import Any

from ztf_classifier.results import ScientificResultRecord


class ScientificReportService:
    """Render a durable scientific result as a human-readable Markdown report."""

    REPORT_SCHEMA_VERSION = "1.0"

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )

    def render_markdown(self, record: ScientificResultRecord) -> str:
        payload = record.payload
        prediction = payload.get("prediction") or {}
        probabilities = prediction.get("probabilities") or {}
        diagnostics = payload.get("diagnostics") or {}
        observation_provenance = payload.get("observation_provenance") or {}
        feature_provenance = payload.get("feature_provenance") or {}
        model_provenance = payload.get("model_provenance") or {}
        observations = payload.get("observations") or []
        features = payload.get("features") or {}

        lines = [
            "# ZTF Scientific Analysis Report",
            "",
            f"- Report schema: {self.REPORT_SCHEMA_VERSION}",
            f"- Result ID: {record.result_id}",
            f"- Job ID: {record.job_id}",
            f"- Object: {record.oid}",
            f"- Survey: {record.survey}",
            f"- Model: {record.model_version}",
            f"- Result schema: {record.schema_version}",
            f"- Created: {record.created_at}",
            "",
            "## Analysis Summary",
            "",
            f"- Predicted class: {prediction.get('predicted_class', 'unavailable')}",
            f"- Observation count: {len(observations)}",
            f"- Feature count: {len(features)}",
            "",
            "## Probability Distribution",
            "",
        ]
        if probabilities:
            for label, value in sorted(
                probabilities.items(),
                key=lambda item: (-float(item[1]), str(item[0])),
            ):
                lines.append(f"- {label}: {float(value):.8f}")
        else:
            lines.append("- unavailable")

        lines.extend(
            [
                "",
                "## Diagnostics",
                "",
                f"- Calibration: {diagnostics.get('calibration', 'unavailable')}",
                f"- Conformal: {diagnostics.get('conformal', 'unavailable')}",
                f"- OOD: {diagnostics.get('ood', 'unavailable')}",
                "",
                "## Provenance",
                "",
                f"- Observation source: {observation_provenance.get('source', 'unavailable')}",
                f"- Feature backend: {feature_provenance.get('backend', 'unavailable')}",
                f"- Model version: {model_provenance.get('model_version', record.model_version)}",
                "",
                "## Reproducibility Record",
                "",
                "The following persisted metadata is included without recomputing inference:",
                "",
                "~~~json",
                self._json(
                    {
                        "result_id": record.result_id,
                        "job_id": record.job_id,
                        "schema_version": record.schema_version,
                        "created_at": record.created_at,
                        "feature_schema_version": payload.get("feature_schema_version"),
                        "warnings": payload.get("warnings", []),
                    }
                ),
                "~~~",
                "",
            ]
        )
        return "\n".join(lines)


__all__ = ["ScientificReportService"]
