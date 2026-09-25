"""ASGI server entry point for the ZTF Classifier API."""

from __future__ import annotations

import uvicorn


def main() -> None:
    """Run the API with Uvicorn."""
    uvicorn.run(
        "ztf_classifier.api.app:app",
        host="127.0.0.1",
        port=8000,
    )


if __name__ == "__main__":
    main()
