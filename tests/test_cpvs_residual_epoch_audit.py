from __future__ import annotations

from scripts.audit_cpvs_residual_epochs import (
    candidate_membership_sets,
    membership_relation,
    metrics,
    read_vizier,
)


def test_metrics_applies_band_specific_snr_thresholds() -> None:
    g_row = {
        "SourceID": "123",
        "gmag": "17.2",
        "e_gmag": "0.4",
        "g_flag": "0",
    }
    r_row = {
        "SourceID": "123",
        "rmag": "16.8",
        "e_rmag": "0.3",
        "r_flag": "0",
    }

    assert metrics(g_row, "g") == (123, 17.2, 1.0857362047581296 / 0.4, True)
    assert metrics(r_row, "r") == (123, 16.8, 1.0857362047581296 / 0.3, True)


def test_metrics_rejects_zero_or_invalid_magnitude_and_error() -> None:
    assert metrics({"SourceID": "7", "gmag": "0", "e_gmag": "0.2"}, "g") == (
        7,
        0.0,
        None,
        False,
    )
    assert metrics({"SourceID": "8", "gmag": "17", "e_gmag": "0"}, "g") == (
        8,
        17.0,
        None,
        False,
    )
    assert metrics({"SourceID": "bad", "gmag": "17", "e_gmag": "0.2"}, "g") == (
        None,
        None,
        None,
        False,
    )


def test_read_vizier_reads_tsv_ids(tmp_path) -> None:
    source = tmp_path / "table4.tsv"
    source.write_text(
        "# ZTF\tID\nZTF123\t12345\nZTF456\t45678\n",
        encoding="utf-8",
    )

    assert read_vizier(source) == {12345, 45678}


def test_membership_count_is_scoped_to_parent_but_outside_ids_remain_traceable() -> None:
    qualified = {"g": {1, 2, 99}, "r": {1, 2, 99}}
    parent_ids = {1, 2}
    published = {1}

    raw, candidate, candidate_only, published_only, outside_parent = (
        candidate_membership_sets(qualified, parent_ids, published)
    )

    assert raw == {1, 2, 99}
    assert candidate == {1, 2}
    assert candidate_only == {2}
    assert published_only == set()
    assert outside_parent == {99}



def test_outside_parent_candidate_has_distinct_relation_and_no_parent_membership() -> None:
    parent_ids = {1, 2}
    candidate_only = {2}
    published_only = set()

    assert membership_relation(99, parent_ids, candidate_only, published_only) == (
        "outside_parent_candidate"
    )
    assert membership_relation(2, parent_ids, candidate_only, published_only) == "candidate_only"
    assert membership_relation(3, parent_ids | {3}, candidate_only, {3}) == "published_only"
