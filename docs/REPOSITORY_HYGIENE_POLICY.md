# Repository and Branch Hygiene Policy

**Owner:** project maintainer. **Enforced by:** review, plus the checks noted
inline. **Last review:** 2026-10-24.

This policy exists because the repository accumulated **216 branches** and
**27 open pull requests**, mostly one-shot CI/CPVS investigation branches. That
volume hides the handful of branches that matter and makes `git branch` useless
as an overview.

## 1. Branch classes

| Class | Prefix | Lifetime | Deletion rule |
|---|---|---|---|
| Long-lived | `main` | permanent | never |
| Active work | `feat/`, `fix/`, `docs/`, `chore/` | until merged or abandoned | delete after merge |
| Arena session | `arena/<session-id>-<topic>` | while the session is active | delete when session closes |
| Investigation | `ci/heavy/*`, `science/*`, `research/*` | ≤ 30 days after last commit | delete when the finding is recorded in `docs/` |
| Snapshot | `backup/*`, `recovery/*` | permanent until superseded | delete only after the referenced state is tagged |
| Bot | `dependabot/*` | automated | delete when the PR closes |

## 2. Rules

1. **A branch is not evidence.** A scientific finding must be written to
   `docs/` or an issue. A branch that only exists to prove something is deleted
   once the finding is recorded.
2. **No branch older than 30 days without a commit** may remain in the
   `ci/`, `science/` or `research/` classes. It is either revived or deleted.
3. **One branch per purpose.** Do not create a new branch to "re-run" CI; use
   a re-run or push a fix to the existing branch.
4. **Pull requests over 30 days old** are closed with a status comment, not left
   open indefinitely. Reopening is cheap; stale open PRs are expensive.
5. **Deletion requires a recorded decision.** Merged branches: delete freely.
   Unmerged branches with commits: tag or record the SHA in the issue first.
6. **Never delete** `main`, `backup/pre-*` snapshots that a tag points at, or a
   branch referenced by an open release checklist.

## 3. Current inventory (2026-10-24)

Measured, not estimated:

| Metric | Value |
|---|---|
| Remote branches | 216 |
| Open pull requests | 27 |
| Open issues | 11 |
| Release tags | `v0.2.0`, `v0.3.0`, `v0.4.0`, `v0.5.0`, `v0.5.0-release`, `v1.0.0`, `v1.0.0.1`, `v1.0.1` |
| Published releases | 6 (`v1.0.1` latest) |

Branch prefix distribution: `fix/*` 51, `feat/*` 48, `ci/*` 42, `docs/*` 29,
`recovery/*` 7, `chore/*` 5, `science/*` 4, `release/*` 4, `feature/*` 4,
`dependabot/*` 3, `audit/*` 3, and 17 singletons.

## 4. Cleanup work that is NOT authorised here

Branch deletion, PR closure and tag deletion are **destructive and
irreversible for the automation identity**. They are deliberately not performed
by this policy. Each requires explicit maintainer approval, because a deleted
unmerged branch loses commits that may be the only copy of a scientific
finding.

Recommended batched cleanup, to be approved before execution:

1. Delete the ~42 `ci/heavy/*` branches whose runs have completed and whose
   results are recorded in issues #170/#180/#195.
2. Close (not delete) the ~20 CPVS investigation PRs (#168–#209) that are
   superseded by PR #219, with a comment pointing at #219 and #170.
3. Delete `audit/*`, `test/*`, `validation/*` one-shot branches.

Acceptance criterion for the cleanup: remote branch count ≤ 40 and open PR
count ≤ 8, with every deleted branch either merged or its SHA recorded in an
issue.

## 5. Release hygiene

- A release tag is created by `.github/workflows/release.yml` only on `main`
  after Scientific Validation succeeds. Do not hand-create release tags.
- `CHANGELOG.md` must describe the released state before the tag is created.
- A release must not silently change a scientific baseline. Baseline identity
  changes require their own decision record.
