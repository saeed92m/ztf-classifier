from pathlib import Path

from scripts.compare_cpvs_full_batch import _row_qualified, band_batch, band_full


def test_batch_merges_object_decisions_across_boundaries(tmp_path: Path):
    path = tmp_path / "g.csv"
    path.write_text(
        "1,1.0,2.0,3.0,18.0,0.1,0\n"
        "2,1.0,2.0,3.0,18.0,0.1,0\n"
        "1,1.0,2.0,4.0,18.0,0.1,0\n"
        "3,1.0,2.0,4.0,0,0.1,0\n",
        encoding="utf-8",
    )
    parent = {"1", "2", "3"}
    full_snr, full_valid, full_rows, full_qualified = band_full(
        path, parent=parent, band="g", sigma=2.5
    )
    batch_snr, batch_valid, batch_rows, batch_qualified, batches = band_batch(
        path, parent=parent, band="g", sigma=2.5, batch_rows=2
    )
    assert (full_snr, batch_snr) == ({"1", "2", "3"}, {"1", "2", "3"})
    assert (full_valid, batch_valid) == ({"1", "2"}, {"1", "2"})
    assert (full_rows, batch_rows) == (4, 4)
    assert (full_qualified, batch_qualified) == (4, 4)
    assert batches == 2



def test_non_finite_or_invalid_snr_is_rejected_fail_closed():
    parent = {"1"}

    for error in (float("nan"), float("inf"), 0.0, -0.1):
        assert _row_qualified(
            "1", 18.0, error, parent=parent, sigma=2.5
        ) == (None, False)

    assert _row_qualified(
        "1", 18.0, 0.1, parent=parent, sigma=2.5
    ) == ("1", True)
