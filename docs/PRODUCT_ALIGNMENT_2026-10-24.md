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
| Full suite | `pytest tests/` | see §6 |
| Lint | `ruff check src tests` | see §6 |
| Format | `ruff format --check src tests` | see §6 |
| Cross-platform | CI job `Cross-platform (ubuntu-latest / macos-latest / windows-latest)` | see §6 |
| Root cleanliness | `git status` after `git mv` | 4 renames, 0 deletions |

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
