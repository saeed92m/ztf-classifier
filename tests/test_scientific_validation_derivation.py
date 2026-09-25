from pathlib import Path

import pytest

from ztf_classifier.validation.derivation import DerivationConfig, _snr_from_mag_error, derive_730k


def test_published_sigma_defaults():
    config = DerivationConfig()
    assert config.g_sigma == 2.5
    assert config.r_sigma == 3.0


def test_snr_from_magnitude_error():
    assert _snr_from_mag_error("0.4342944819") == pytest.approx(2.5, rel=1e-8)
    assert _snr_from_mag_error("0.3619120683") == pytest.approx(3.0, rel=1e-8)
    assert _snr_from_mag_error("bad") != _snr_from_mag_error("bad")


def test_derivation_fails_closed_on_parent_count(tmp_path: Path):
    parent = tmp_path / "parent.tsv"
    parent.write_text("SourceID\nA\nB\n", encoding="utf-8")
    g = tmp_path / "g.tsv"
    g.write_text("SourceID\te_gmag\nA\t0.1\nB\t0.1\n", encoding="utf-8")
    r = tmp_path / "r.tsv"
    r.write_text("SourceID\te_rmag\nA\t0.1\nB\t0.1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="parent row/object count mismatch"):
        derive_730k(parent, g, r, tmp_path / "selected.tsv")
