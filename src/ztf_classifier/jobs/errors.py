"""Errors for expected analysis-job execution failures."""

from __future__ import annotations


class AnalysisJobExecutionError(RuntimeError):
    """Expected execution failure safe to expose as a stable job error."""


__all__ = ["AnalysisJobExecutionError"]
