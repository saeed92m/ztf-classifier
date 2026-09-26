"""Probe external validation sources and record immutable retrieval metadata.

The probe validates source reachability and captures content hashes/metadata.
It does not convert live responses into benchmark truth.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from ztf_classifier.validation.sources import SOURCES


PROBES = {
    "star_embed_ztf_40k": "https://huggingface.co/api/datasets/StarEmbed/ZTF_40k",
    "ztf_periodic_781k": "https://zenodo.org/api/records/3886372",
    "ztf_dr24_source_subset": "https://irsa.ipac.caltech.edu/data/ZTF/docs/releases/dr24/",
    "alerce_reference": "https://tap.alerce.online/tap/capabilities",
}


def fetch(url: str, timeout: int = 30) -> tuple[int, bytes, str]:
    request = Request(url, headers={"User-Agent": "ztf-classifier-scientific-validation/1"})
    with urlopen(request, timeout=timeout) as response:
        payload = response.read()
        content_type = response.headers.get("Content-Type", "")
        return response.status, payload, content_type


def run(output: str | Path, fetcher=fetch) -> dict[str, object]:
    retrieved_at = datetime.now(timezone.utc).isoformat()
    results: list[dict[str, object]] = []

    for source in SOURCES:
        url = PROBES.get(source.source_id)
        if url is None:
            results.append(
                {
                    "source_id": source.source_id,
                    "status": "DERIVED",
                    "version": source.version,
                    "note": "No independent endpoint; derived deterministically from the pinned parent source.",
                }
            )
            continue

        try:
            status, payload, content_type = fetcher(url)
            results.append(
                {
                    "source_id": source.source_id,
                    "status": "REACHABLE" if status == 200 else "HTTP_ERROR",
                    "http_status": status,
                    "content_type": content_type,
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "probe_url": url,
                    "version": source.version,
                }
            )
        except (OSError, URLError, ValueError, RuntimeError) as exc:  # pragma: no cover - network-dependent
            results.append(
                {
                    "source_id": source.source_id,
                    "status": "UNREACHABLE",
                    "probe_url": url,
                    "version": source.version,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    report = {
        "retrieved_at": retrieved_at,
        "scientific_interpretation": (
            "Reachability and response hashes are provenance evidence only; "
            "they do not constitute benchmark validation or ground truth."
        ),
        "sources": results,
    }
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "reports/scientific_validation/source_probe.json"
    result = run(target)
    print(f"source_probe={target}")
    print(f"sources={len(result['sources'])}")
