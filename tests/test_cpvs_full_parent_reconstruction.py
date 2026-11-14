import unittest

from scripts.diagnose_cpvs_full_parent_reconstruction import confusion, pos


class FullParentReconstructionTests(unittest.TestCase):
    def test_positive_metadata_requires_finite_positive_values(self):
        self.assertTrue(pos("0.1"))
        self.assertFalse(pos("0"))
        self.assertFalse(pos("-0.1"))
        self.assertFalse(pos("nan"))
        self.assertFalse(pos(""))

    def test_confusion_matrix_is_object_level(self):
        result = confusion({1, 2, 3}, {2, 3, 4})
        self.assertEqual(result["TP"], 2)
        self.assertEqual(result["FP"], 1)
        self.assertEqual(result["FN"], 1)
        self.assertAlmostEqual(result["precision"], 2 / 3)
        self.assertAlmostEqual(result["recall"], 2 / 3)


if __name__ == "__main__":
    unittest.main()
