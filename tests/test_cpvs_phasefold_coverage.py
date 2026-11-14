import hashlib
import shutil
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path
from unittest.mock import patch

from scripts.diagnose_cpvs_phasefold_coverage import (
    ARCHIVES,
    num,
    phase_metrics,
    positive,
    scan_archive,
)


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
        result = phase_metrics([-0.01, 0.99, 1.99])
        self.assertEqual(result["unique_phases"], 1)
        self.assertEqual(result["occupied_bins_160"], 1)
        self.assertEqual(result["max_circular_phase_gap"], 1.0)

    def test_numeric_helpers_reject_nonfinite(self):
        self.assertIsNone(num(float("nan")))
        self.assertIsNone(num(float("inf")))
        self.assertFalse(positive("0"))
        self.assertTrue(positive("1.5"))

    @unittest.skipUnless(shutil.which("unzip"), "Info-ZIP unzip is not installed")
    def test_scan_archive_streams_member_and_verifies_integrity(self):
        raw_member = b"100\\t0\\t0\\t2400001.5\\t17.0\\t0.1\\t0\\n"
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "tiny-ztf2g.zip"
            with zipfile.ZipFile(
                archive_path, "w", compression=zipfile.ZIP_DEFLATED
            ) as archive:
                archive.writestr("ztf2g", raw_member)

            with zipfile.ZipFile(archive_path) as archive:
                crc = archive.getinfo("ztf2g").CRC
            config = {
                "member": "ztf2g",
                "sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
                "threshold": 2.5,
                "mag_index": 4,
                "err_index": 5,
                "member_sha256": hashlib.sha256(raw_member).hexdigest(),
                "member_size": len(raw_member),
                "member_rows": 1,
                "member_crc32": f"{crc:08x}",
            }
            with patch.dict(ARCHIVES, {"g": config}):
                result = scan_archive(
                    archive_path, "g", {100: {"period": 1.0}}
                )

        self.assertEqual(result["rows_total"], 1)
        self.assertEqual(result["member_bytes"], len(raw_member))
        self.assertEqual(result["member_crc32"], f"{crc:08x}")
        self.assertEqual(result["objects"][100]["valid"]["n"], 1)
        self.assertEqual(result["objects"][100]["snr_qualified"]["n"], 1)
        self.assertEqual(result["objects"][100]["flag_lt_32768"]["n"], 1)


if __name__ == "__main__":
    unittest.main()
