from pathlib import Path

import pytest

from scripts.rebuild_v0_2_model_reconstruction import validate_output_dir


def test_output_directory_must_be_inside_project_root(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    outside = tmp_path / "outside" / "run"

    with pytest.raises(ValueError, match="inside the project root"):
        validate_output_dir(root, outside)


def test_output_directory_cannot_be_project_root(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()

    with pytest.raises(ValueError, match="inside the project root"):
        validate_output_dir(root, root)


def test_output_directory_cannot_replace_frozen_production_path(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    root.mkdir()
    legacy = root / "runs" / "model_baseline_v0.2_production" / "artifact"

    with pytest.raises(ValueError, match="frozen production path"):
        validate_output_dir(root, legacy)


def test_output_directory_must_not_already_exist(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    output = root / "runs" / "new-reconstruction"
    output.mkdir(parents=True)

    with pytest.raises(FileExistsError, match="already exists"):
        validate_output_dir(root, output)
