from pathlib import Path

from ztf_classifier.catalog import ScientificCatalogService
from ztf_classifier.results import ScientificResultStore


def _store(tmp_path: Path) -> ScientificResultStore:
    return ScientificResultStore(tmp_path / "results.sqlite3")


def test_catalog_query_filters_and_orders_results(tmp_path: Path) -> None:
    store = _store(tmp_path)
    for job_id, oid in [("job-1", "ZTF17a"), ("job-2", "ZTF18b"), ("job-3", "ZTF17c")]:
        store.save(
            job_id=job_id,
            oid=oid,
            survey="ztf",
            model_version="baseline_v0.2",
            payload={"prediction": {"predicted_class": "AGN"}},
        )

    page = ScientificCatalogService(store).query(
        survey="ztf",
        model_version="baseline_v0.2",
        limit=2,
    )

    assert page.total == 3
    assert len(page.items) == 2
    assert page.items[0].created_at >= page.items[1].created_at
    assert page.has_next


def test_catalog_csv_export_is_deterministic(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.save(
        job_id="job-1",
        oid="ZTF17a",
        survey="ztf",
        model_version="baseline_v0.2",
        payload={"value": 1, "label": "AGN"},
    )

    csv_text = ScientificCatalogService(store).export_csv(
        ScientificCatalogService(store).query(limit=1)
    )

    assert csv_text.splitlines()[0].startswith("result_id,job_id,oid,survey")
    assert "ZTF17a" in csv_text
    assert '"label":"AGN"' in csv_text


def test_catalog_query_rejects_invalid_limit(tmp_path: Path) -> None:
    store = _store(tmp_path)

    try:
        ScientificCatalogService(store).query(limit=1001)
    except ValueError as exc:
        assert "between 1 and 1000" in str(exc)
    else:
        raise AssertionError("invalid catalog limit was accepted")
