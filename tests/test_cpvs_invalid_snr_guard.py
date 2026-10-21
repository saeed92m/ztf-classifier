from pathlib import Path

from ztf_classifier.validation.derivation import derive_730k


def test_invalid_magnitude_errors_do_not_qualify_as_snr_detections(tmp_path: Path):
    parent = tmp_path / "parent.tsv"
    parent.write_text("SourceID\n1\n2\n", encoding="utf-8")

    g = tmp_path / "g.tsv"
    g.write_text(
        "SourceID\te_gmag\tgmag\tg_flag\n"
        "1\t\t15.0\t0\n"
        "2\t0.1\t15.0\t0\n",
        encoding="utf-8",
    )
    r = tmp_path / "r.tsv"
    r.write_text(
        "SourceID\te_rmag\trmag\tr_flag\n"
        "1\tnan\t15.0\t0\n"
        "2\t0.1\t15.0\t0\n",
        encoding="utf-8",
    )
    output = tmp_path / "selected.tsv"

    result = derive_730k(
        parent,
        g,
        r,
        output,
        expected_parent_rows=2,
        expected_selected_rows=1,
    )

    assert result.selected_rows == 1
    assert output.read_text(encoding="utf-8").splitlines() == ["SourceID", "2"]
