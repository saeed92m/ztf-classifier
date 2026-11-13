import math
import unittest

from scripts.diagnose_cpvs_phasefold_coverage import num, phase_metrics, positive


class PhaseFoldCoverageTests(unittest.TestCase):
    def test_phase_metric_counts_wrapped_phases(self):
        result = phase_metrics([0.02, 0.24, 0.48, 0.72, 0.98])
        self.assertEqual(result["n"], 5)
        self.assertEqual(result["unique_phases"], 5)
        self.assertEqual(result["occupied_bins_160"], 5)
        self.assertAlmostEqual(result["max_circular_phase_gap"], 0.26, places=8)

    def test_phase_metric_handles_empty_input(self):
        result = phase_metrics([])
        self.assertEqual(result["n"], 0)
        self.assertIsNone(result["max_circular_phase_gap"])

    def test_phase_metric_wraps_values(self):
        result = phase_metrics([-0.01, 1.01, 2.01])
        self.assertEqual(result["unique_phases"], 1)
        self.assertEqual(result["occupied_bins_160"], 1)
        self.assertEqual(result["max_circular_phase_gap"], 1.0)

    def test_numeric_helpers_reject_nonfinite(self):
        self.assertIsNone(num(float("nan")))
        self.assertIsNone(num(float("inf")))
        self.assertFalse(positive("0"))
        self.assertTrue(positive("1.5"))


if __name__ == "__main__":
    unittest.main()
