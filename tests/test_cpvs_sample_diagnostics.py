import pytest
from pathlib import Path

from scripts.diagnose_cpvs_sample import _band_diagnostics, select_stratified_ids


def test_cpvs_sample_is_deterministic_balanced_and_nested():
    parent = set(range(1, 101))
    published = set(range(1, 51))

    sample_a, diagnostic_a = select_stratified_ids(
        parent, published, seed=1234, sample_size=20, diagnostic_size=10
    )
    sample_b, diagnostic_b = select_stratified_ids(
        parent, published, seed=1234, sample_size=20, diagnostic_size=10
    )

    assert sample_a == sample_b
    assert diagnostic_a == diagnostic_b
    assert len(sample_a) == 20
    assert sum(source_id in published for source_id in sample_a) == 10
    assert sum(source_id not in published for source_id in sample_a) == 10
    assert len(diagnostic_a) == 10
    assert sum(source_id in published for source_id in diagnostic_a) == 5
    assert sum(source_id not in published for source_id in diagnostic_a) == 5
    assert set(diagnostic_a).issubset(sample_a)


@pytest.mark.parametrize(
    "sample_size,diagnostic_size",
    [(0, 10), (11, 10), (20, 0), (20, 21), (20, 9)],
)

def test_band_diagnostics_retains_sample_source_evidence(tmp_path: Path):
    path = tmp_path / "g.tsv"
    path.write_text(
        "SourceID\tHJD\tgmag\te_gmag\tg_flag\n"
        "1\t1.0\t15.0\t0.1\t0\n"
        "1\t2.0\t15.1\t0.5\t1\n"
        "2\t3.0\t0\t0.2\t0\n"
        "3\t4.0\t16.0\tnan\t0\n",
        encoding="utf-8",
    )

    linear, exact, sample = _band_diagnostics(
        path,
        parent_ids={1, 2, 3},
        sample_ids={1, 2, 3},
        error_column="e_gmag",
        mag_column="gmag",
        flag_column="g_flag",
        sigma=2.5,
    )

    assert linear == {1}
    assert exact == {1}
    assert sample[1]["rows"] == 2
    assert sample[1]["valid_error_rows"] == 2
    assert sample[1]["valid_nonzero_magnitude_rows"] == 2
    assert sample[1]["linear_qualifying_rows"] == 1
    assert sample[1]["exact_qualifying_rows"] == 2
    assert sample[1]["flag_zero_valid_error_rows"] == 1
    assert sample[1]["flag_nonzero_valid_error_rows"] == 1
    assert sample[1]["max_snr_linear_row"]["HJD"] == "1.0"
    assert sample[3]["valid_error_rows"] == 0
    assert sample[3]["valid_nonzero_magnitude_rows"] == 1


def test_cpvs_sample_rejects_invalid_sizes(sample_size, diagnostic_size):
    with pytest.raises(ValueError):
        select_stratified_ids(
            set(range(1, 101)),
            set(range(1, 51)),
            sample_size=sample_size,
            diagnostic_size=diagnostic_size,
        )
