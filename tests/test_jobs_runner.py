from dataclasses import dataclass

from ztf_classifier.jobs import runner


@dataclass(frozen=True)
class FakeJob:
    status: str


class FakeWorker:
    def __init__(self, jobs: list[FakeJob]) -> None:
        self.jobs = jobs

    def drain(self):
        return self.jobs


def test_runner_returns_success_when_all_jobs_succeed(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "create_worker",
        lambda: FakeWorker([FakeJob("succeeded"), FakeJob("succeeded")]),
    )

    assert runner.main() == 0


def test_runner_returns_failure_when_any_job_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "create_worker",
        lambda: FakeWorker([FakeJob("succeeded"), FakeJob("failed")]),
    )

    assert runner.main() == 1
