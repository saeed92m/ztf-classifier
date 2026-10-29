"""Regression tests for immutable frozen-reference archive contracts."""

from __future__ import annotations

import zipfile
from pathlib import Path

from scripts.acquire_frozen_reference_evidence import SOURCES, _members


def test_cpvs_reference_requires_all_published_archive_members() -> None:
    source = SOURCES["ztf_periodic_730k_published"]
    assert source["required_members"] == {
        "1st_layer.csv",
        "2nd_layer.csv",
        "SIMBAD_ZTF_crossmatch.csv",
    }


def test_archive_member_listing_preserves_nested_member_names(tmp_path: Path) -> None:
    archive_path = tmp_path / "Zenodo.zip"
    expected = {
        "1st_layer.csv",
        "2nd_layer.csv",
        "SIMBAD_ZTF_crossmatch.csv",
    }
    with zipfile.ZipFile(archive_path, "w") as archive:
        for name in sorted(expected):
            archive.writestr(name, "placeholder\n")

    assert set(_members(archive_path, "zip")) == expected


def test_cpvs_archive_contract_rejects_missing_expected_member(tmp_path: Path) -> None:
    source = SOURCES["ztf_periodic_730k_published"]
    archive_path = tmp_path / "incomplete.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("1st_layer.csv", "placeholder\n")

    actual_basenames = {Path(name).name for name in _members(archive_path, "zip")}
    missing = set(source["required_members"]) - actual_basenames

    assert missing == {"2nd_layer.csv", "SIMBAD_ZTF_crossmatch.csv"}
