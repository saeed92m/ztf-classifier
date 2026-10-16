import pytest

from ztf_classifier.validation.tess_quality import (
    DEFAULT_TESS_QUALITY_MASK,
    assess_tess_quality_flags,
)


def test_default_mask_matches_documented_bitwise_semantics():
    result = assess_tess_quality_flags([0, 1, 8, 4096])
    assert result.bitmask == DEFAULT_TESS_QUALITY_MASK == 21183
    assert result.accepted == (True, False, False, False)
    assert result.reasons == (
        None,
        "quality_mask_nonzero",
        "quality_mask_nonzero",
        "quality_mask_nonzero",
    )


def test_custom_mask_is_configurable_and_keeps_row_alignment():
    result = assess_tess_quality_flags([0, 1, 2, 3], bitmask=1)
    assert result.accepted == (True, False, True, False)
    assert result.reasons == (None, "quality_mask_nonzero", None, "quality_mask_nonzero")
    assert result.to_dict() == {
        "bitmask": 1,
        "row_count": 4,
        "accepted_count": 2,
        "rejected_count": 2,
        "rejection_reason_counts": {"quality_mask_nonzero": 2},
    }


@pytest.mark.parametrize("bitmask", [-1, True, 1.5, "3"])
def test_invalid_masks_fail_closed(bitmask):
    with pytest.raises(ValueError, match="bitmask"):
        assess_tess_quality_flags([0], bitmask=bitmask)


@pytest.mark.parametrize("quality", [-1, True, 1.5, None, "0"])
def test_invalid_quality_values_fail_closed(quality):
    with pytest.raises(ValueError, match="QUALITY value at row 0"):
        assess_tess_quality_flags([quality])
