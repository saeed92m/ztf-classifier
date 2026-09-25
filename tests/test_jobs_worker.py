from pathlib import Path

import pytest

from ztf_classifier.jobs import AnalysisJobExecutionError, AnalysisJobWorker, JobStore


def test_worker_claims_oldest_queued_job_and_persists_result(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "jobs.sqlite3")
    first = store.create(oid="ZTF-first", survey="ztf", model_version="baseline_v0.2")
    second = store.create(oid="ZTF-second", survey="ztf", model_version="baseline_v0.2")
    seen: list[str] = []

    def execute(job):
        seen.append(job.oid)
        return {"oid": job.oid, "status": "analysis-complete"}

    result = AnalysisJobWorker(store, execute).run_once()

    assert result is not None
    assert result.status == "succeeded"
    assert result.result == {"oid": first.oid, "status": "analysis-complete"}
    assert seen == [first.oid]
    assert store.get(second.job_id).status == "queued"


def test_worker_persists_executor_failure_without_leaking_exception(
    tmp_path: Path,
) -> None:
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.create(oid="ZTF-failure", survey="ztf", model_version=None)

    def execute(_job):
        raise AnalysisJobExecutionError("secret internal detail")

    result = AnalysisJobWorker(store, execute).run_once()

    assert result is not None
    assert result.status == "failed"
    assert result.error == {
        "code": "analysis_job_failed",
        "message": "The analysis job could not be completed.",
    }
    assert "secret" not in str(result.error)


def test_worker_rejects_non_mapping_executor_result(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.create(oid="ZTF-invalid", survey="ztf", model_version=None)

    result = AnalysisJobWorker(store, lambda _job: ["not", "a", "mapping"]).run_once()

    assert result is not None
    assert result.status == "failed"
    assert result.error["code"] == "analysis_job_invalid_result"


def test_worker_drain_processes_multiple_jobs(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "jobs.sqlite3")
    for index in range(3):
        store.create(oid=f"ZTF-{index}", survey="ztf", model_version=None)

    result = AnalysisJobWorker(store, lambda job: {"oid": job.oid}).drain()

    assert [item.status for item in result] == ["succeeded", "succeeded", "succeeded"]
    assert store.claim_next() is None


def test_worker_leaves_unexpected_errors_visible(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "jobs.sqlite3")
    job = store.create(oid="ZTF-unexpected", survey="ztf", model_version=None)

    def execute(_job):
        raise ValueError("programmer error")

    import pytest

    with pytest.raises(ValueError, match="programmer error"):
        AnalysisJobWorker(store, execute).run_once()

    assert store.get(job.job_id).status == "running"


def test_expired_running_job_is_requeued(tmp_path) -> None:
    store = JobStore(tmp_path / "jobs.sqlite3")
    record = store.create(oid="ZTF17lease", survey="ztf", model_version=None)
    running = store.claim_next(lease_seconds=1)
    assert running is not None
    import sqlite3

    with sqlite3.connect(store.path) as connection:
        connection.execute(
            "UPDATE analysis_jobs SET lease_expires_at = ? WHERE job_id = ?",
            ("2000-01-01T00:00:00+00:00", record.job_id),
        )

    assert store.requeue_expired() == 1
    requeued = store.get(record.job_id)
    assert requeued.status == "queued"
    assert requeued.lease_expires_at is None


def test_claim_assigns_lease_and_transition_clears_it(tmp_path) -> None:
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.create(oid="ZTF17lease2", survey="ztf", model_version=None)

    running = store.claim_next(lease_seconds=60)
    assert running is not None
    assert running.lease_expires_at is not None

    completed = store.transition(
        running.job_id,
        status="succeeded",
        result={"ok": True},
    )
    assert completed.status == "succeeded"
    assert completed.lease_expires_at is None


def test_worker_persists_scientific_result_and_links_job(tmp_path: Path) -> None:
    from ztf_classifier.results import ScientificResultStore

    job_store = JobStore(tmp_path / "jobs.sqlite3")
    result_store = ScientificResultStore(tmp_path / "results.sqlite3")
    job = job_store.create(
        oid="ZTF-result",
        survey="ztf",
        model_version="baseline_v0.2",
    )

    worker = AnalysisJobWorker(
        job_store,
        lambda item: {
            "schema_version": "1.0",
            "oid": item.oid,
            "model_version": "baseline_v0.2",
            "prediction": {"predicted_class": "AGN"},
        },
        result_store,
    )

    completed = worker.run_once()

    assert completed is not None
    assert completed.status == "succeeded"
    assert completed.scientific_result_id is not None
    assert completed.result == {
        "result_id": completed.scientific_result_id,
        "schema_version": "1.0",
    }

    stored = result_store.get(completed.scientific_result_id)
    assert stored.job_id == job.job_id
    assert stored.payload["prediction"]["predicted_class"] == "AGN"


def test_worker_marks_result_persistence_failure_without_leaking_details(
    tmp_path: Path,
) -> None:
    from ztf_classifier.results import ScientificResultStore

    job_store = JobStore(tmp_path / "jobs.sqlite3")
    result_store = ScientificResultStore(tmp_path / "results.sqlite3")
    job_store.create(oid="ZTF-result-fail", survey="ztf", model_version=None)

    completed = AnalysisJobWorker(
        job_store,
        lambda _job: {"value": object()},
        result_store,
    ).run_once()

    assert completed is not None
    assert completed.status == "failed"
    assert completed.error["code"] == "scientific_result_persistence_failed"


def test_job_store_lists_jobs_deterministically(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "jobs.sqlite3")
    first = store.create(oid="ZTF17first", survey="ztf", model_version="baseline_v0.2")
    second = store.create(oid="ZTF17second", survey="ztf", model_version="baseline_v0.2")

    jobs = store.list(limit=10)

    assert [job.job_id for job in jobs] == [second.job_id, first.job_id]


def test_job_store_rejects_invalid_listing_status(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "jobs.sqlite3")

    with pytest.raises(ValueError, match="Unsupported job status"):
        store.list(status="invalid")
