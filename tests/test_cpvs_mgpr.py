from __future__ import annotations

import importlib.util
import unittest

import numpy as np

from scripts.diagnose_cpvs_mgpr import fit_one_gp, prepare_training_data


class CPVSMGPRPreparationTests(unittest.TestCase):
    def test_standardizes_each_band_and_repeats_three_cycles(self):
        g = [
            {"phase": 0.1, "magnitude": 10.0, "mag_error": 0.1},
            {"phase": 0.5, "magnitude": 12.0, "mag_error": 0.2},
            {"phase": 0.9, "magnitude": 14.0, "mag_error": 0.1},
        ]
        r = [
            {"phase": 0.2, "magnitude": 20.0, "mag_error": 0.2},
            {"phase": 0.6, "magnitude": 22.0, "mag_error": 0.2},
            {"phase": 0.8, "magnitude": 24.0, "mag_error": 0.2},
        ]
        x, y, yerr, scaling = prepare_training_data(g, r)
        self.assertEqual(x.shape, (18, 2))
        self.assertEqual(y.shape, (18,))
        self.assertEqual(yerr.shape, (18,))
        self.assertEqual(scaling["g"]["valid_observations"], 3)
        self.assertAlmostEqual(float(np.mean(y[:9])), 0.0, places=12)
        self.assertAlmostEqual(float(np.mean(y[9:])), 0.0, places=12)
        self.assertTrue(np.allclose(x[:3, 0], [0.1, 0.5, 0.9]))
        self.assertTrue(np.allclose(x[3:6, 0], [1.1, 1.5, 1.9]))
        self.assertTrue(np.allclose(x[6:9, 0], [2.1, 2.5, 2.9]))
        self.assertTrue(np.all(x[:9, 1] == 0.0))
        self.assertTrue(np.all(x[9:, 1] == 1.0))


    @unittest.skipUnless(importlib.util.find_spec("george"), "george is installed only in the bounded MGPR workflow")
    def test_george_fit_returns_finite_likelihood_and_conditioning(self):
        phases = np.linspace(0.0, 1.0, 12, endpoint=False)
        x = np.vstack((
            np.column_stack((np.concatenate([phases, phases + 1, phases + 2]), np.zeros(36))),
            np.column_stack((np.concatenate([phases, phases + 1, phases + 2]), np.ones(36))),
        ))
        y = np.concatenate((
            np.tile(np.sin(2 * np.pi * phases), 3),
            np.tile(0.7 * np.sin(2 * np.pi * phases + 0.2), 3),
        ))
        yerr = np.full(len(y), 0.05)
        _, result = fit_one_gp(x, y, yerr)
        self.assertTrue(np.isfinite(result["negative_log_likelihood"]))
        self.assertGreater(result["white_noise_variance"], 0)
        self.assertIsNotNone(result["covariance_condition_number_2norm"])
        self.assertEqual(len(result["optimizer_starts"]), 2)

    def test_rejects_zero_variance_band(self):
        g = [
            {"phase": 0.1, "magnitude": 10.0, "mag_error": 0.1},
            {"phase": 0.5, "magnitude": 10.0, "mag_error": 0.2},
            {"phase": 0.9, "magnitude": 10.0, "mag_error": 0.1},
        ]
        r = [
            {"phase": 0.2, "magnitude": 20.0, "mag_error": 0.2},
            {"phase": 0.6, "magnitude": 22.0, "mag_error": 0.2},
            {"phase": 0.8, "magnitude": 24.0, "mag_error": 0.2},
        ]
        with self.assertRaisesRegex(ValueError, "standard deviation"):
            prepare_training_data(g, r)


if __name__ == "__main__":
    unittest.main()
