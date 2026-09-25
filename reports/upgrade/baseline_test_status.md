# v0.4.0 Upgrade Baseline Status

Date: 2026-09-25
Branch: chore/complete-upgrade-v0.4
Baseline source commit: 0c615b09813e0f5a8e61a895d371789e3ab1e21f

## Verification boundary

The GitHub repository connector can inspect and modify repository state, but it does not expose the project's WSL2 working tree or an arbitrary shell session. Therefore the pre-change local commands required by the upgrade specification were NOT VERIFIED locally by this execution and are not represented as successful results.

Required commands: git status; python --version; python -m pip check; python -m ruff check src tests; python -m pytest -q — all NOT VERIFIED locally.

## Known repository baseline

- Software version: 0.3.0
- Scientific baseline: v0.2.0 (immutable)
- Dataset contract: benchmark_v0.2
- Model version: baseline_v0.2
- Frozen feature schema: v0.2 / 42 features
- Artifact schemas: 1.0 and 1.1
- Main branch at start of upgrade: 0c615b09813e0f5a8e61a895d371789e3ab1e21f
- Latest previously recorded release-gate CI result: run #90 passed on the final v0.3.0 preparation head, as documented by Handbook v1.3.

No pre-change failure is fabricated. Branch CI is the authoritative executable validation for this upgrade branch.
