from __future__ import annotations

import hashlib

import pandas as pd
import pytest

from ztf_classifier.application.errors import ApplicationInputError
from ztf_classifier.application.ingestion import (
    DataIngestionService,
    ImportRequest,
)


def test_import_csv_returns_table_and_content_provenance(tmp_path):
    path = tmp_path / "detections.csv"
    path.write_text(
        "oid,mjd,mag\nZTF1,60000.1,18.2\nZTF1,60001.1,18.4\n"
    )

    result = DataIngestionService().import_file(
        ImportRequest(path=path, required_columns=("oid", "mjd"))
    )

    assert result.row_count == 2
    assert result.columns == ("oid", "mjd", "mag")
    assert result.data["oid"].tolist() == ["ZTF1", "ZTF1"]
    assert result.source.source_type == "local_csv"
    assert result.source.schema_version == "tabular-v1"
    expected_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    assert result.source.content_hash == expected_hash
    assert result.content_sha256 == result.source.content_hash
    assert result.source.metadata["row_count"] == 2


@pytest.mark.parametrize(
    ("contents", "message"),
    [
        ("oid,mjd\n", "no data rows"),
        ("oid,mjd\nZTF1,60000\n", "missing required columns"),
    ],
)
def test_import_rejects_empty_data_or_missing_columns(
    tmp_path, contents, message
):
    path = tmp_path / "input.csv"
    path.write_text(contents)
    required = ("oid", "mag") if "ZTF1" in contents else ()

    with pytest.raises(ApplicationInputError, match=message):
        DataIngestionService().import_file(
            ImportRequest(path=path, required_columns=required)
        )


def test_import_rejects_unsupported_formats_and_oversized_files(tmp_path):
    unsupported = tmp_path / "input.json"
    unsupported.write_text('{"oid":"ZTF1"}')
    with pytest.raises(ApplicationInputError, match="Unsupported file format"):
        DataIngestionService().import_file(ImportRequest(path=unsupported))

    csv_path = tmp_path / "input.csv"
    csv_path.write_text("oid\nZTF1\n")
    with pytest.raises(ApplicationInputError, match="exceeds max_bytes"):
        DataIngestionService().import_file(
            ImportRequest(path=csv_path, max_bytes=1)
        )


def test_import_does_not_mutate_source_file(tmp_path):
    path = tmp_path / "table.csv"
    original = b"oid,mjd\nZTF1,60000\n"
    path.write_bytes(original)

    result = DataIngestionService().import_file(ImportRequest(path=path))

    assert path.read_bytes() == original
    assert isinstance(result.data, pd.DataFrame)


def test_import_request_rejects_invalid_size_and_format(tmp_path):
    path = tmp_path / "table.csv"
    with pytest.raises(ApplicationInputError, match="positive integer"):
        ImportRequest(path=path, max_bytes=0)
    with pytest.raises(ApplicationInputError, match="Unsupported import format"):
        ImportRequest(path=path, format="json")
