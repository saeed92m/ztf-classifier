"""Acquire immutable historical benchmark archives and emit evidence manifests.

This intentionally separates immutable published/reference snapshots from live
ALeRCE/VizieR services. Large archives are never committed to Git.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen


SOURCES = {
    "alerce_reference_frozen_20200609": {
        "url": "https://zenodo.org/records/4279623/files/files_for_lc_classifier_SanchezSaez2020.tar.gz?download=1",
        "filename": "files_for_lc_classifier_SanchezSaez2020.tar.gz",
        "md5": "f0c8c47fb530613718a3cf0c4678a3e4",
        "archive_type": "tar.gz",
        "required_members": {
            "labeled_set_lc_classifier_SanchezSaez_2020.csv",
            "features_for_lc_classifier_20200609.csv",
            "ALeRCE_lc_classifier_outputs_ZTF_unlabeled_set_20200609.csv",
        },
    },
    "ztf_periodic_730k_published": {
        "url": "https://zenodo.org/records/5764899/files/Zenodo.zip?download=1",
        "filename": "Zenodo.zip",
        "md5": "7fc6562d4208cbfa97366351984810e3",
        "archive_type": "zip",
        "required_members": set(),
    },
}


def _md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, target: Path) -> None:
    request = Request(url, headers={"User-Agent": "ztf-classifier-scientific-validation/1.0"})
    with urlopen(request, timeout=120) as response, target.open("wb") as handle:
        while chunk := response.read(1024 * 1024):
            handle.write(chunk)


def _members(path: Path, archive_type: str) -> list[str]:
    if archive_type == "zip":
        with zipfile.ZipFile(path) as archive:
            return archive.namelist()
    with tarfile.open(path, "r:gz") as archive:
        return archive.getnames()


def acquire(benchmark_id: str, output: Path) -> Path:
    source = SOURCES[benchmark_id]
    output.mkdir(parents=True, exist_ok=True)
    archive = output / source["filename"]
    if not archive.exists():
        _download(source["url"], archive)

    actual_md5 = _md5(archive)
    if actual_md5 != source["md5"]:
        raise RuntimeError(
            f"{benchmark_id}: archive MD5 mismatch: "
            f"expected {source['md5']}, got {actual_md5}"
        )

    members = _members(archive, source["archive_type"])
    basenames = {Path(member).name for member in members}
    missing = sorted(set(source["required_members"]) - basenames)
    if missing:
        raise RuntimeError(
            f"{benchmark_id}: required archive members are missing: {missing}"
        )

    manifest = {
        "benchmark_id": benchmark_id,
        "source_url": source["url"].split("?")[0],
        "archive": source["filename"],
        "md5": actual_md5,
        "sha256": _sha256(archive),
        "member_count": len(members),
        "required_members": sorted(source["required_members"]),
        "members": sorted(members),
    }
    manifest_path = output / "evidence_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark_id", choices=sorted(SOURCES))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(acquire(args.benchmark_id, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
