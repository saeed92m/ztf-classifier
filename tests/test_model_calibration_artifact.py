"""Tests for the production calibration artifact state."""

from pathlib import Path

import pytest

from ztf_classifier.models.calibration_artifact import (
    CALIBRATION_ARTIFACT_SCHEMA_VERSION,
    CalibrationArtifact,
)

TEMPERATURE = 1.0268501887


def test_calibration_artifact_roundtrip(
    tmp_path: Path,
) -> None:
    artifact = CalibrationArtifact(
        method="temperature_scaling",
        temperature=TEMPERATURE,
    )

    path = tmp_path / "calibration.json"
    artifact.write(path)

    restored = CalibrationArtifact.read(path)

    assert restored == artifact
    assert restored.to_dict() == {
        "method": "temperature_scaling",
        "schema_version": (
            CALIBRATION_ARTIFACT_SCHEMA_VERSION
        ),
        "temperature": TEMPERATURE,
    }


def test_calibration_artifact_rejects_unsupported_method() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        CalibrationArtifact(
            method="isotonic",
            temperature=TEMPERATURE,
        )


@pytest.mark.parametrize(
    "temperature",
    [0.0, -1.0],
)
def test_calibration_artifact_rejects_invalid_temperature(
    temperature: float,
) -> None:
    with pytest.raises(ValueError, match="positive"):
        CalibrationArtifact(
            method="temperature_scaling",
            temperature=temperature,
        )


def test_calibration_artifact_rejects_invalid_schema() -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported calibration artifact schema",
    ):
        CalibrationArtifact.from_dict(
            {
                "schema_version": "999.0",
                "method": "temperature_scaling",
                "temperature": TEMPERATURE,
            }
        )


def test_calibration_artifact_rejects_existing_path(
    tmp_path: Path,
) -> None:
    path = tmp_path / "calibration.json"
    path.write_text("existing\n", encoding="utf-8")

    artifact = CalibrationArtifact(
        method="temperature_scaling",
        temperature=TEMPERATURE,
    )

    with pytest.raises(FileExistsError):
        artifact.write(path)
