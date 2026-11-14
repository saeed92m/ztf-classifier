import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts.diagnose_cpvs_mismatch_lineage import (
    ARCHIVES,
    angular_separation_arcsec,
    build_spatial_hash,
    cell_key,
    classify_time_scale,
    scan_archive,
)


class CPVSMismatchLineageTests(unittest.TestCase):
    def test_angular_separation_handles_ra_wrap(self):
        self.assertAlmostEqual(
            angular_separation_arcsec(359.9999, 0.0, 0.0001, 0.0),
            0.72,
            places=3,
        )

    def test_time_scale_hints(self):
        self.assertEqual(classify_time_scale(58197.15), "MJD_LIKE")
        self.assertEqual(classify_time_scale(2458197.15), "HJD_OR_JD_LIKE")
        self.assertEqual(classify_time_scale(None), "UNKNOWN")

    def test_spatial_hash_indexes_neighbor_cells(self):
        targets = {100: {"ra": 10.001, "dec": 20.001}}
        index = build_spatial_hash(targets)
        self.assertIn(100, index[cell_key(10.001, 20.001)])
        self.assertIn(100, index[cell_key(10.049, 20.049)])

    def test_scan_finds_nearby_alternate_source_id(self):
        raw = (
            b"100 10.0 0.0 2459000.5 17.0 0.1 0\\n"
            b"201 20.0001 0.0 2459000.6 17.1 0.1 64\\n"
            b"201 20.0001 0.0 2459001.6 17.2 0.1 64\\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "tiny.zip"
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("ztf2g", raw)
            with zipfile.ZipFile(archive_path) as archive:
                crc = archive.getinfo("ztf2g").CRC
            config = {
                "member": "ztf2g",
                "sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
                "member_sha256": hashlib.sha256(raw).hexdigest(),
                "member_bytes": len(raw),
                "member_rows": 3,
                "member_crc32": f"{crc:08x}",
            }
            targets = {
                100: {"ZTF": "ZTFJ_A", "ra": 10.0, "dec": 0.0},
                200: {"ZTF": "ZTFJ_B", "ra": 20.0, "dec": 0.0},
            }
            mismatches = [
                {"SourceID": "100", "raw_g": "1"},
                {"SourceID": "200", "raw_g": "0"},
            ]
            with patch.dict(ARCHIVES, {"g": config}):
                result = scan_archive(archive_path, "g", targets, mismatches)
        self.assertEqual(result["objects"][0]["raw_rows"], 1)
        self.assertEqual(result["targets_without_raw_rows"], [200])
        self.assertEqual(len(result["coordinate_aliases"]), 1)
        alias = result["coordinate_aliases"][0]
        self.assertEqual(alias["alternate_SourceID"], 201)
        self.assertEqual(alias["target_SourceID"], 200)
        self.assertEqual(alias["alternate_raw_rows"], 2)
        self.assertLess(alias["separation_arcsec"], 1.0)


if __name__ == "__main__":
    unittest.main()
