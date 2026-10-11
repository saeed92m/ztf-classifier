#!/usr/bin/env python3
"""Safely probe ScrapeGraphAI credentials and optionally scrape one reference page.

The API key is read only from SGAI_API_KEY and is never printed or persisted.
The scrape call is opt-in because it may consume account credits.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = os.environ.get("SGAI_API_URL", "https://v2-api.scrapegraphai.com/api").rstrip("/")
OUT_DIR = Path("scrapegraphai-probe-output")
CPVS_REFERENCE_URL = (
    "https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJ/932/118?format=html&tex=true"
)


def request_json(path: str, *, method: str = "GET", payload: dict | None = None) -> dict:
    key = os.environ.get("SGAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "Missing GitHub Actions secret SGAI_API_KEY. Add it in "
            "Repository Settings > Secrets and variables > Actions."
        )
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/{path.lstrip('/')}",
        data=body,
        method=method,
        headers={
            "SGAI-APIKEY": key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "ztf-classifier-scrapegraphai-probe/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            raw = response.read()
            return json.loads(raw.decode("utf-8")) if raw else {}
    except urllib.error.HTTPError as exc:
        # Do not include request headers or environment values in logs.
        detail = exc.read(1500).decode("utf-8", errors="replace")
        raise RuntimeError(f"ScrapeGraphAI returned HTTP {exc.code}: {detail}") from None
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach ScrapeGraphAI API: {exc.reason}") from None


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    key = os.environ.get("SGAI_API_KEY", "").strip()
    if not key:
        print(
            "::error::Missing GitHub Actions secret SGAI_API_KEY. "
            "Add it in Settings > Secrets and variables > Actions."
        )
        return 2

    print("Checking ScrapeGraphAI credits endpoint (no scrape request yet)...")
    try:
        credits = request_json("/credits")
        # Write only non-sensitive account metadata; never save the API key.
        safe_credits = {
            k: credits.get(k)
            for k in ("remaining", "used", "plan")
            if k in credits
        }
        (OUT_DIR / "credits.json").write_text(
            json.dumps(safe_credits, indent=2) + "\n", encoding="utf-8"
        )
        print("API authentication succeeded.")
        if safe_credits:
            print("Account metadata:", json.dumps(safe_credits, ensure_ascii=False))
        else:
            print("Credits endpoint responded successfully; response fields were not recognized.")

        if os.environ.get("RUN_SCRAPE", "false").lower() not in ("1", "true", "yes"):
            print("Scrape skipped. Set workflow input run_scrape=true to run the one-page test.")
            return 0

        print("Running one-page CPVS reference scrape; this may consume credits...")
        result = request_json(
            "/scrape",
            method="POST",
            payload={
                "url": CPVS_REFERENCE_URL,
                "formats": [{"type": "markdown", "mode": "reader"}],
            },
        )
        (OUT_DIR / "scrape-response.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print("Scrape request completed. Response saved as a short-retention workflow artifact.")
        # Print only a bounded preview, never the full response.
        preview = result.get("result")
        if preview is not None:
            print("Response preview:", json.dumps(preview, ensure_ascii=False)[:1500])
        return 0
    except RuntimeError as exc:
        print(f"::error::{exc}")
        return 1
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"::error::Unexpected response format from ScrapeGraphAI: {type(exc).__name__}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
