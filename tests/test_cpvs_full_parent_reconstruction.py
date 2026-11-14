import unittest

from scripts.diagnose_cpvs_full_parent_reconstruction import cohort, confusion, pos, resolve_member_name


class FullParentReconstructionTests(unittest.TestCase):
    def test_positive_metadata_requires_finite_positive_values(self):
        self.assertTrue(pos("0.1"))
        self.assertFalse(pos("0"))
        self.assertFalse(pos("-0.1"))
        self.assertFalse(pos("nan"))
        self.assertFalse(pos(""))

    def test_cohort_partition_is_explicit(self):
        self.assertEqual(cohort(1, {1}, {2}, {3}), "table4_member")
        self.assertEqual(cohort(2, {1}, {2}, {3}), "candidate_only_residual")
        self.assertEqual(cohort(3, {1}, {2}, {3}), "four_field_only_55")
        self.assertEqual(cohort(4, {1}, {2}, {3}), "other_parent")


    def test_resolves_nested_zip_member_by_basename(self):
        import tempfile
        import zipfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "fixture.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("work/ztf2g", b"photometry")
                archive.writestr("__MACOSX/ztf2g", b"metadata")
            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(resolve_member_name(archive, "ztf2g"), "work/ztf2g")

    def test_confusion_matrix_is_object_level(self):
        result = confusion({1, 2, 3}, {2, 3, 4})
        self.assertEqual(result["TP"], 2)
        self.assertEqual(result["FP"], 1)
        self.assertEqual(result["FN"], 1)
        self.assertAlmostEqual(result["precision"], 2 / 3)
        self.assertAlmostEqual(result["recall"], 2 / 3)


if __name__ == "__main__":
    unittest.main()
