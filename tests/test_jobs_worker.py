from pathlib import Path

from ztf_classifier.jobs import AnalysisJobWorker, JobStore


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
        raise RuntimeError("secret internal detail")

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
