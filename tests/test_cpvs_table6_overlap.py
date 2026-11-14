import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.diagnose_cpvs_table6_overlap import (
    build_report,
    metadata_predicates,
    read_table6_ids,
)


class Table6OverlapTests(unittest.TestCase):
    def test_reads_ids_and_checks_archive_and_member(self):
        header = b"".join(f"# header {i}\n".encode() for i in range(20))
        rows = (
            b"ZTFJ000019.72+542513.0 10.0 20.0 0.0 20.5 0.0 0.2 0.1 0.1 10 100 -5.0\n"
            b"ZTFJ000022.75+651051.5 11.0 21.0 18.0 20.0 0.2 0.3 0.1 0.1 50 60 -6.0\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "table6.zip"
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("Table6.txt", header + rows)
            checksum = hashlib.md5(archive_path.read_bytes()).hexdigest()
            ids, metadata = read_table6_ids(
                archive_path, expected_md5=checksum, expected_rows=2
            )
        self.assertEqual(ids, {
            "ZTFJ000019.72+542513.0",
            "ZTFJ000022.75+651051.5",
        })
        self.assertEqual(metadata["record_count"], 2)
        self.assertEqual(metadata["unique_id_count"], 2)
        self.assertEqual(metadata["row_field_counts"], {12: 2})

    def test_metadata_predicates_are_derived_from_source_fields(self):
        row = {
            "SourceID": "172",
            "gmag": "nan",
            "rmag": "20.593",
            "Per-g": "nan",
            "Per-r": "0.2050052",
            "four_field_positive": "false",
        }
        result = metadata_predicates(row)
        self.assertFalse(result["both_mean_magnitudes_positive"])
        self.assertFalse(result["both_band_periods_positive"])
        self.assertFalse(result["four_field_positive"])

        row.update({
            "gmag": "19.5",
            "rmag": "20.593",
            "Per-g": "0.203",
            "Per-r": "0.2050052",
            "four_field_positive": "true",
        })
        result = metadata_predicates(row)
        self.assertTrue(result["both_mean_magnitudes_positive"])
        self.assertTrue(result["both_band_periods_positive"])
        self.assertTrue(result["four_field_positive"])

    def test_build_report_counts_overlap_without_changing_membership(self):
        residuals = [
            {
                "SourceID": "172",
                "ZTF": "ZTFJ000019.72+542513.0",
                "strata": "candidate_only",
                "candidate": "true",
                "Table4_member": "false",
                "gmag": "0",
                "rmag": "20.5",
                "Per-g": "0",
                "Per-r": "0.2",
                "four_field_positive": "false",
            },
            {
                "SourceID": "197",
                "ZTF": "ZTFJ000022.75+651051.5",
                "strata": "candidate_only",
                "candidate": "true",
                "Table4_member": "false",
                "gmag": "19.1",
                "rmag": "20.2",
                "Per-g": "0.12",
                "Per-r": "0.14",
                "four_field_positive": "true",
            },
        ]
        report, overlap = build_report(
            residuals, {"ZTFJ000019.72+542513.0"}, {"record_count": 5}
        )
        self.assertEqual(report["residuals"]["table6_overlap_count"], 1)
        self.assertEqual(report["residuals"]["table6_non_overlap_count"], 1)
        self.assertEqual(overlap[0]["SourceID"], "172")
        self.assertEqual(
            report["residuals"]["by_metadata_predicate"][
                "both_mean_magnitudes_positive"
            ]["residuals_in_group"],
            1,
        )
        self.assertEqual(
            report["residuals"]["by_metadata_predicate"][
                "four_field_positive"
            ]["residuals_in_group"],
            1,
        )
        self.assertIn("does not establish", report["interpretation_limit"])


if __name__ == "__main__":
    unittest.main()
