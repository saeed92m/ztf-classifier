"""Catalog services over the canonical scientific-result repository."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from dataclasses import dataclass
from typing import Any

from ztf_classifier.results import ScientificResultRecord, ScientificResultStore


@dataclass(frozen=True)
class CatalogPage:
    """One deterministic page of persisted scientific results."""

    items: list[ScientificResultRecord]
    total: int
    limit: int
    offset: int

    @property
    def has_next(self) -> bool:
        return self.offset + len(self.items) < self.total


class ScientificCatalogService:
    """Query and export durable scientific analysis history."""

    def __init__(self, store: ScientificResultStore) -> None:
        self.store = store

    @staticmethod
    def _validate_window(
        created_after: str | None,
        created_before: str | None,
    ) -> None:
        parsed_after = None
        parsed_before = None
        try:
            if created_after is not None:
                parsed_after = datetime.fromisoformat(created_after)
            if created_before is not None:
                parsed_before = datetime.fromisoformat(created_before)
        except ValueError as exc:
            raise ValueError("created_after/created_before must be ISO-8601 timestamps") from exc
        if parsed_after is not None and parsed_before is not None and parsed_after > parsed_before:
            raise ValueError("created_after must not be later than created_before")

    def query(
        self,
        *,
        oid: str | None = None,
        survey: str | None = None,
        model_version: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> CatalogPage:
        """Return a bounded, deterministic catalog page."""
        self._validate_window(created_after, created_before)
        total = self.store.count(
            oid=oid,
            survey=survey,
            model_version=model_version,
            created_after=created_after,
            created_before=created_before,
        )
        items = self.store.query(
            oid=oid,
            survey=survey,
            model_version=model_version,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            offset=offset,
        )
        return CatalogPage(items=items, total=total, limit=limit, offset=offset)

    def export_csv(self, page: CatalogPage) -> str:
        """Serialize one catalog page with stable metadata columns."""
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "result_id",
                "job_id",
                "oid",
                "survey",
                "model_version",
                "schema_version",
                "created_at",
                "payload_json",
            ],
            lineterminator="
",
        )
        writer.writeheader()
        for record in page.items:
            writer.writerow(
                {
                    "result_id": record.result_id,
                    "job_id": record.job_id,
                    "oid": record.oid,
                    "survey": record.survey,
                    "model_version": record.model_version,
                    "schema_version": record.schema_version,
                    "created_at": record.created_at,
                    "payload_json": json.dumps(
                        record.payload,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                }
            )
        return output.getvalue()


__all__ = ["CatalogPage", "ScientificCatalogService"]
