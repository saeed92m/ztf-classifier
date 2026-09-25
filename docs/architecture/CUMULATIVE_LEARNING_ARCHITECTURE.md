# Cumulative Learning & Continuous Improvement Architecture

## Purpose

ZTF Classifier evolves through a closed evidence loop rather than isolated linear stages. Every implementation cycle consumes validated prior knowledge and emits reusable knowledge, tests, measurements, and decisions.

## Canonical lifecycle

AUDIT -> RETRIEVE PREVIOUS KNOWLEDGE -> DEFINE OBJECTIVE -> DEFINE BASELINE -> PLAN -> IMPLEMENT -> TEST -> MEASURE -> VALIDATE -> FAILURE/ROOT-CAUSE ANALYSIS -> KNOWLEDGE EXTRACTION -> UPDATE KNOWLEDGE BASE -> UPDATE TESTS/RULES -> COMPARE AGAINST PREVIOUS BASELINE -> ACCEPT/REVISE -> NEXT STAGE

Knowledge Extraction is mandatory.

## Knowledge status

Allowed statuses are FACT, VERIFIED, SUPPORTED, HYPOTHESIS, ASSUMPTION, UNRESOLVED, REJECTED. Only evidence-backed knowledge may become a normative inherited rule.

## Multi-objective quality vector

Q = {Accuracy, Correctness, Speed, Efficiency, Reliability, Robustness, Coverage, Reproducibility, Scientific Validity}

The vector is contextual: not every dimension applies to every change. A trade-off is acceptable only when explicitly measured, scientifically justified, regression-checked, and recorded in the ledger. Local optimization that damages scientific validity or release integrity is not accepted.

## Stage contract

Every meaningful stage or PR must declare:
- previous knowledge consumed
- inherited baseline
- objective
- expected improvement
- measurement method and metrics
- new knowledge generated
- new risks
- regression status
- lessons learned
- knowledge carried forward

## Executable enforcement

ztf_classifier.lifecycle validates a machine-readable cycle record. Required fields and allowed knowledge statuses are contractually checked. The lifecycle contract is tested in CI, making missing cumulative evidence detectable rather than documentary only.

## Scientific coupling

Changes affecting feature generation, preprocessing, model, inference, calibration, conformal prediction, OOD, normalization, or scientific API contracts must link their cycle record to relevant scientific validation evidence. Scientific Validation remains release-blocking.

## Performance coupling

Where performance is relevant, the cycle records before/after runtime, throughput, latency, memory, CPU/GPU utilization, I/O, batch efficiency, feature-generation time, and inference time as applicable. NOT_MEASURED is explicit when a metric is not applicable or not yet available.

## Process improvement

When data exists, process metrics such as audit time, implementation time, debugging time, regression-fix time, rework count, repeated-failure count, PR cycle time, and test execution efficiency should be recorded. Process optimization must not weaken scientific or release gates.
