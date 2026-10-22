import math

import pytest

from scripts.diagnose_cpvs_selection import _exact_snr_from_mag_error


def test_exact_snr_inverts_magnitude_error_relation():
    threshold = 2.5
    magnitude_error = 2.5 * math.log10(1.0 + 1.0 / threshold)

    assert _exact_snr_from_mag_error(magnitude_error) == pytest.approx(threshold)


@pytest.mark.parametrize("error", [0.0, -0.1, float("nan"), float("inf")])
def test_exact_snr_rejects_invalid_magnitude_errors(error: float):
    assert math.isnan(_exact_snr_from_mag_error(error))
