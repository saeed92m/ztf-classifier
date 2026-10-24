# Product Alignment Audit — 2026-10-24

**Type:** point-in-time audit. **Scope:** alignment of code, documentation,
packaging, CI and external systems with the product vision.

**Vision under test:** ZTF Classifier must be an independent, installable,
maintainable scientific product usable on **Windows, macOS and Ubuntu**, with
scientific validity, reproducibility, security and execution independence
preserved. It must permit an *optional, future* connection to Company-Platform
without depending on it.

**Baseline commit:** `0a8e4c6` on `arena/d3039cf3-ztf-classifier`.

Every claim below is either **Verified** (with a command or CI job named) or
**Unverified** (with the reason). No item is asserted without evidence.

---

## 1. Sources examined

| Source | Access | Result |
|---|---|---|
| `saeed92m/ztf-classifier` (GitHub API, git, gh) | Full read/write | Examined |
| Notion workspace (`ZTF Classifier — Project Knowledge Base` tree) | Full read | Examined: 9 pages retrieved |
| Supabase account (`eu-central-1`, `ap-south-1`) | Full read | 2 projects, **neither belongs to this product** |
| `saeed92m/Company-Platform` | **HTTP 403** | **Blocked — not examined** |
| GitHub Actions history, runs, artifacts | Read | Examined |
| Package build (`python -m build`) | Via CI | Examined |

**Company-Platform blocker (explicit):** both
`gh api repos/saeed92m/Company-Platform` and
`git ls-remote https://github.com/saeed92m/Company-Platform` return
`403 Resource not accessible by integration`. The automation identity lacks
read access to that repository. Per repository rule 7, **no claim is made about
its contents, structure, versioning, documentation, licence or release cycle.**
Nothing in this audit asserts that the two projects are integrated, because that
cannot be verified.

---

## 2. Findings and what was done

### 2.1 Cross-platform support was declared but not real — **fixed the measurement**

**Before.** `pyproject.toml` declared
`Operating System :: POSIX :: Linux` only, and **all eight CI jobs ran on
`ubuntu-latest`**. There was no macOS or Windows job anywhere in the repository.
`docs/INSTALLATION.md` said *"A Linux/WSL environment is recommended for
scientific workflows."*

**Root cause (verified).** `requirements.lock` is a Linux/x86-64 freeze. It pins:

- `nvidia-nccl-cu12==2.32.3` — CUDA, Linux/x86-64 only, pulled by `xgboost`
- `jeepney==0.9.0` — Linux D-Bus
- `SecretStorage==3.5.0` — Linux secret storage

`pip install -r requirements.lock` therefore **cannot succeed on macOS or
Windows**. The hermetic install path was never portable; only the unpinned
`pip install -e .` path is.

**After.** Added a `cross-platform` CI job with a real matrix —
`ubuntu-latest`, `macos-latest`, `windows-latest` — that installs from
`pyproject.toml` (the portable path) and runs the full test suite plus the CLI
smoke test on each OS. It is wired into the `CI Gate`, so a broken platform
fails CI rather than going unnoticed.

**Honest status.** This makes the platform claim *measurable*; it does not by
itself prove that all three platforms pass. That evidence is the CI run listed
in §4.

### 2.2 Documentation had no single source of truth — **fixed**

**Before.** 14 files named `docs/HANDBOOK_UPDATED_v*.md`, 4 roadmap files, and 4
unreferenced artefacts in the repository root. Concrete defects found:

| File | Internal title | Defect |
|---|---|---|
| `HANDBOOK_UPDATED_v1.3.md` | v1.4 | filename ≠ version |
| `HANDBOOK_UPDATED_v2.2.md` | v2.3 | filename ≠ version |
| `HANDBOOK_UPDATED_v2.4.md` | v2.3 | filename ≠ version, stale content reissued as a new number |
| `roadmap/CUMULATIVE_LEARNING_ROADMAP_v2.2.md` | v2.4 | filename ≠ version |
| `README.md:421` | — | calls the 87-line v2.8 an amendment a "canonical continuity handbook"; the last full handbook is v2.6 (471 lines) |

**After.**

- `docs/README.md` created as the **authority map**: one canonical document per
  topic, explicit supersession, and the handbook defects recorded rather than
  hidden.
- `tests/test_documentation_authority.py` created (12 tests) to make the map
  enforceable: it fails when a document under `docs/` is not declared, when a
  canonical target is missing, when the frozen handbook series grows, and when
  the known version drift changes without the map being updated.
- The four root orphans were **moved, not deleted**, into `docs/archive/`:
  `git mv`, history preserved, reversible. They had **zero** inbound references
  (verified by grep across the whole repository).

### 2.3 No declared integration boundary — **fixed**

**Before.** Zero references to Supabase or Company-Platform existed anywhere,
which is the correct *runtime* state but was nowhere *documented* as a decision.
A future contributor could have introduced a dependency without noticing.

**After.** `docs/contracts/PLATFORM_INTEGRATION_BOUNDARY_V1.md` declares a
versioned, one-directional contract (Company-Platform consumes ZTF's `/v1` API;
ZTF never calls out), the data-contract obligations, the security boundary and
the change protocol. It records that the dependency is absent today and that
Company-Platform's own contents are unverified.

### 2.4 Branch and PR volume — **documented, not actioned**

216 remote branches and 27 open PRs, dominated by one-shot `ci/heavy/*` CPVS
investigation branches. Deleting branches and closing PRs is destructive and
irreversible for this identity, so it is **not** performed. A batched cleanup
plan with an acceptance criterion (≤ 40 branches, ≤ 8 open PRs) is recorded in
`docs/REPOSITORY_HYGIENE_POLICY.md` §4, pending maintainer approval.

### 2.5 Two further defects, found only because the claim was measured — **fixed**

The new `Cross-platform` job failed on its first run. That failure was the most
useful result of the round: both causes were real product defects that no
documented claim had exposed.

**(a) The `dev` extra could not run the test suite.**
`tests/test_api.py`, `tests/test_reporting.py` and `tests/test_web_workbench.py`
construct `fastapi.testclient.TestClient`. `starlette.testclient` requires an
HTTP client at import time, and `httpx` was present in `requirements.lock` but
absent from `pyproject.toml`. Consequence: every lock-based job was green, while
the documented portable path (`pip install -e .[dev]`) **could not even collect
the suite** — `3 errors during collection`, exit code 2. Fixed by declaring
`httpx` in the `dev` extra, documented in place as test-only (no module under
`src/` imports it).

**(b) A test asserted the sandbox, not the product.**
`tests/test_model_provenance.py` compared provenance to hardcoded third-party
patch versions (`numpy==2.4.6`, `pandas==3.0.6`, …). Those literals reproduce
only under `requirements.lock`; under a portable install pandas resolves to
`3.1.0` and the test failed for a reason unrelated to the code under test. Fixed
by comparing against `importlib.metadata.version(...)` for the same six
packages, which verifies the property that actually matters — that provenance
records the versions genuinely in use — in every environment. The project's own
version (`1.0.1`) remains asserted literally as a release guard.

Both fixes are accompanied by `tests/test_dependency_declarations.py` (4 tests):
the lockfile must cover every declared runtime dependency, the `dev` extra must
declare an HTTP client, `fastapi.testclient` must import in the running
environment, and every package that provenance records must be a declared
runtime dependency.

**One further correction.** The job requested `python-version: "3.11.16"`.
The runner manifests do not publish every 3.11.x patch for every
OS/architecture, so `setup-python` failed outright on `macos-latest` (arm64) and
on Windows **before a single test ran**. The matrix now requests the minor
version `"3.11"`, which resolves to the newest available 3.11.x per platform and
is also the honest test of the declared floor `requires-python = ">=3.11,<3.12"`.

### 2.6 A POSIX-only import made the Windows claim false — **fixed**

Running the suite on macOS and Windows produced a second class of defect, one
that no Linux job could ever have found:
`src/ztf_classifier/validation/runner.py` imported `resource` at module scope.
`resource` is a Unix-only standard-library module, so the module could not be
imported on Windows at all, which makes the declared Windows support false for
every code path that touches the validation runner.

Peak memory is now reported through a small portable helper: `resource.getrusage`
on Linux and macOS (KiB and bytes respectively, as before), and
`GetProcessMemoryInfo` from psapi via `ctypes` on Windows — standard library, no
new dependency. Both describe the same OS-level quantity, so `peak_rss_mb` keeps
the same meaning; if the OS call fails the value is `0.0` rather than a
fabricated number, because that figure is reported in validation output.

`tests/test_platform_portability.py` now enforces the rule at the cheapest
possible level: no module in `src/` may import one of
`fcntl`, `grp`, `pty`, `pwd`, `resource`, `syslog`, `termios`, `tty` at module
scope, and the runner must import with `resource` unavailable.

**Diagnosability.** Logs from a failed matrix job are served from the runner's
blob storage, which was not reachable from the tooling performing this audit.
The `Cross-platform` test step now captures pytest output and re-emits every
`FAILED`/`ERROR` line as a GitHub annotation, which is served by the API and
shown on the check. A platform failure is therefore legible to whoever is
reviewing it, not only to whoever can reach the log bucket.

### 2.7 Three platform defects the annotations exposed — **fixed**

With matrix failures readable again, the macOS and Windows runs yielded three
more concrete defects.

**(a) Provenance wrote OS-specific paths.** `str(Path)` produces backslashes on
Windows, so the same repository produced provenance strings that differed by
platform and did not match the data contract. All four recorded paths now use
`as_posix()`, consistent with `reproducibility/manifest.py`.

**(b) Peak memory was reported as `0.0` on Windows.** The `ctypes` handle type was
not declared, so the `-1` pseudo-handle from `GetCurrentProcess()` was truncated
to `0x00000000FFFFFFFF`, the query failed, and the helper returned its failure
value. That figure is written into validation output, so this was a reporting
defect and not merely a failing assertion. Fixed with explicit
`restype`/`argtypes`, plus a fallback to `kernel32.K32GetProcessMemoryInfo`.

**(c) The frozen OOF comparison was applied across platforms.**
`xgboost_baseline_v0.2_oof_predictions.parquet` was produced in one recorded
environment — `Linux-…-x86_64-with-glibc2.43`, numpy 2.4.6, pandas 3.0.6,
scikit-learn 1.9.1, xgboost 3.2.0 — which
`reproducibility_manifest_v0.2.json` states exactly. On Windows the label columns
already differ, so the comparison was testing the platform rather than the code.
The test now asserts structure, class validity, probability normalisation and
argmax consistency on every platform, and asserts value-level agreement
**when the environment matches the recorded reference**. The strict comparison is
therefore still enforced on the reference system, and it extends automatically to
any platform on which the artefact is regenerated. Cross-OS numerical identity of
the frozen artefact is not claimed. This is a scoping of a claim to its evidence,
not a relaxation of a criterion.

**macOS installation prerequisite.** `xgboost`'s macOS wheel links
`@rpath/libomp.dylib` and does not ship it; nine test modules failed to collect
until it was present. `brew install libomp` is a genuine end-user step and is now
documented as such in `docs/INSTALLATION.md` and performed by the matrix job.

---

## 3. Sources examined with **no change made** (and why)

| Source | Decision |
|---|---|
| **Supabase** | No change. The account holds `company-platform-pilot` (INACTIVE) and `company-website` (ACTIVE_HEALTHY); neither is this project. Issue #183 already records *evaluation only, adoption not authorised*. Creating a project, schema or migration would violate the "do not change something merely because the tool exists" rule. |
| **Notion** | Only an alignment page was added (see §5). The existing pages were **not** mass-edited: several near-duplicate "Latest revision pin" headings already exist, and rewriting them risks destroying provenance. The authority map now states Notion is narrative, not authoritative. |
| **Frozen scientific baseline `v0.2.0`** | Untouched, by explicit standing constraint. |
| **Release tags `v0.2.0`–`v1.0.1`** | Untouched. No new tag, no merge to `main`. |
| **`requirements.lock`** | Not regenerated. Changing a lockfile used by the release pipeline is a separate, reviewable change; the defect is documented instead. |
| **`.github/release-manifest.json`** | Not modified. It is consumed by the release workflow and editing it would affect the release path. |

---

## 4. Verification evidence

| Check | Command / job | Result |
|---|---|---|
| Documentation authority suite | `pytest tests/test_documentation_authority.py` | 12 passed |
| Dependency declaration guards | `pytest tests/test_dependency_declarations.py` | 4 passed |
| Platform import guards | `pytest tests/test_platform_portability.py` | 3 passed, 8 skipped |
| Full suite, locked environment | `python -m pytest tests/ -q` | **667 passed, 13 skipped** |
| Full suite, portable environment (`pip install -e ".[dev]"` in a clean venv) | `python -m pytest -q` | **666 passed, 14 skipped** (the extra skip is the frozen-OOF value comparison, which is scoped to the reference environment — §2.7c) |
| Lint | `ruff check src tests` | All checks passed |
| Format | `ruff format --check src tests` | 234 files already formatted |
| CLI entry point | `ztf-classifier --help` | usage printed, exit 0 |
| Root cleanliness | `git status` after `git mv` | 4 renames, 0 deletions |
| Cross-platform | CI job `Cross-platform (ubuntu-latest / macos-latest / windows-latest)` | see §6 |

The two environments matter independently. The locked environment is the one the
four ubuntu CI jobs install and is the only place the pinned scientific stack is
reproduced. The portable environment is what a Windows or macOS user actually
gets from `pyproject.toml`. A test suite that passes in only one of them is not
evidence of cross-platform support.

---

## 5. Notion changes

One page created under
`ZTF Classifier — Project Knowledge Base`:
*ZTF Classifier — Product Alignment Audit — 2026-10-24*. It links the authority
map, records the Company-Platform access blocker, and states that Notion is a
narrative mirror, not the authority for code or contract facts.

No existing Notion page was deleted or overwritten.

---

## 6. Remaining work

| # | Item | Owner | Acceptance criterion |
|---|---|---|---|
| 1 | Verify `saeed92m/Company-Platform` contents and licence | Maintainer with read access | A read-only identity can list the repo; its licence, versioning and release cycle are recorded in its own repository |
| 2 | Cross-platform CI green on all three OSes | Maintainer (may need portability fixes) | `Cross-platform (*)` jobs all succeed on `main` |
| 3 | Per-platform lockfiles | Maintainer | `requirements/linux.lock`, `requirements/macos.lock`, `requirements/windows.lock`, each installing successfully in its matrix job |
| 4 | Decide the licence question | Maintainer | `pyproject.toml` `license` matches the intended distribution model; classifiers updated |
| 5 | Widen `requires-python` | Maintainer | CI matrix proves 3.12 works before the constraint is relaxed |
| 6 | Branch/PR cleanup | Maintainer approval | ≤ 40 branches, ≤ 8 open PRs, every removed branch either merged or its SHA recorded |
| 7 | Repair handbook filename/version drift | Maintainer | The three mismatches fixed and `docs/README.md` §2 updated in the same change |
| 8 | Regenerate the CPVS diagnostic artefact after PR #197 | Maintainer | New artifact hash recorded; strict JSON parse passes (issue #196) |
| 9 | Source-backed re-run after PR #219 (`Seq` parser) | Maintainer | Real Table 2 `Seq` gaps inspected; issue #170 kept open until then |

---

## 7. Subsystem progress against measurable criteria

Scored against verifiable criteria only. A subsystem is not 100% because it is
documented; it is 100% when its acceptance criterion is demonstrably met.

| Subsystem | Criteria met | Score | Basis |
|---|---|---|---|
| Scientific core (features/model/calibration) | 6/6 | **100%** | 648 tests green, frozen baseline intact, model card present |
| Scientific validation & claim discipline | 5/6 | **83%** | Claim vocabulary + fail-closed gates verified; CPVS #170 unresolved |
| Ubuntu / Linux install | 4/4 | **100%** | Hermetic lock + CI green |
| macOS / Windows install | 2/4 | **50%** | Matrix job added and wired to the gate; **green run not yet observed** |
| Packaging & release automation | 4/4 | **100%** | 6 releases, tags verified, release workflow gated on Scientific Validation |
| API & integration contracts | 3/4 | **75%** | `/v1` documented + boundary contract v1; no consumer exists yet |
| Documentation authority | 4/4 | **100%** | Authority map + 12 enforcement tests |
| Repository hygiene | 1/4 | **25%** | Policy written; **216 branches / 27 PRs not yet reduced** |
| External-system independence | 3/3 | **100%** | Zero Supabase/Company-Platform references verified |
| Company-Platform alignment | 0/2 | **0%** | **Access blocked (403); cannot verify** |
| Licence clarity | 0/2 | **0%** | `Proprietary` in `pyproject.toml`, no `LICENSE` file, GitHub reports `license: null` |

**Weighted product readiness (excluding the blocked Company-Platform axis):
≈ 78%.** The three largest deductions are repository hygiene (25%), licence
clarity (0%) and macOS/Windows (50%).
