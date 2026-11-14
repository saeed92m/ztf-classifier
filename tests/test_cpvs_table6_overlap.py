import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.diagnose_cpvs_table6_overlap import build_report, read_table6_ids


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
            ids, metadata = read_table6_ids(archive_path, expected_md5=checksum, expected_rows=2)
        self.assertEqual(ids, {"ZTFJ000019.72+542513.0", "ZTFJ000022.75+651051.5"})
        self.assertEqual(metadata["record_count"], 2)
        self.assertEqual(metadata["unique_id_count"], 2)
        self.assertEqual(metadata["row_field_counts"], {12: 2})

    def test_build_report_counts_overlap_without_changing_membership(self):
        residuals = [
            {
                "SourceID": "172", "ZTF": "ZTFJ000019.72+542513.0", "Type": "EW",
                "mean_magnitude_pair_positive": "false",
                "band_period_pair_positive": "false", "four_field_positive": "false",
            },
            {
                "SourceID": "197", "ZTF": "ZTFJ000022.75+651051.5", "Type": "EW",
                "mean_magnitude_pair_positive": "false",
                "band_period_pair_positive": "false", "four_field_positive": "false",
            },
        ]
        report, overlap = build_report(residuals, {"ZTFJ000019.72+542513.0"}, {"record_count": 5})
        self.assertEqual(report["residuals"]["table6_overlap_count"], 1)
        self.assertEqual(report["residuals"]["table6_non_overlap_count"], 1)
        self.assertEqual(overlap[0]["SourceID"], "172")
        self.assertIn("does not establish", report["interpretation_limit"])


if __name__ == "__main__":
    unittest.main()
