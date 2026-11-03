# CPVS candidate-only discrepancy report

This utility creates an object-level evidence table for candidate IDs absent from the supplied published Table 4 membership list. It is a reporting and triage capability, **not a fix to the CPVS historical selection-rule blocker**.

## Inputs

- `--parent-metadata`: TSV/CSV with a stable integer object ID (SourceID or Seq) and all four fields: gmag, rmag, Per-g, Per-r.
- `--candidate-ids` and `--published-ids`: TSV/CSV files with an ID column.
- `--source-revision`: code revision that produced the input files.

Every candidate-only ID must join to exactly one parent metadata row. Duplicate IDs, missing required columns, malformed IDs, missing parent provenance, and invalid/unmapped Table 4 name crosswalks stop report generation.

## Outputs

- cpvs_candidate_only_objects.csv: all candidate-only IDs, original metadata columns, feature status/reasons, raw-light-curve and cross-match states.
- cpvs_candidate_only_objects.html: local filterable object table with links by SourceID.
- cpvs_object_detail.html: per-object evidence view; open with a SourceID fragment from the table or enter an ID.
- cpvs_discrepancy_summary.json: counts and interpretation boundaries.
- cpvs_discrepancy_report.md: human-readable summary.
- cpvs_discrepancy_manifest.json: source and output SHA-256 hashes.

Example:

```bash
python scripts/build_cpvs_discrepancy_report.py \
  --parent-metadata /path/to/parent_metadata.tsv \
  --candidate-ids /path/to/candidate_ids.tsv \
  --published-ids /path/to/published_table4_ids.tsv \
  --source-revision "$(git rev-parse HEAD)" \
  --output-dir /path/to/cpvs-discrepancy-report
```

## Independent retained-artifact recheck — 2026-10-28

A separate local verification re-read the full retained candidate, published, and parent ID lists and parsed the complete 781,602-row parent metadata TSV, rather than trusting the precomputed JSON summaries.

| Check | Independently observed result |
|---|---:|
| Parent IDs / unique IDs | 781,602 / 781,602 |
| Candidate IDs / unique IDs | 741,786 / 741,786 |
| Published IDs / unique IDs | 730,184 / 730,184 |
| Candidate ∩ published | 730,184 |
| Candidate-only | 11,602 |
| Published-only | 0 |
| Candidate IDs absent from parent metadata | 0 |
| Candidates passing all four nonzero finite metadata checks | 730,184 |
| Four-field diagnostic vs published set | 0 false positives / 0 false negatives |

Verified SHA-256:
- Full parent metadata TSV: `3675b1274f73fcb15d47e7a780f194ef8fa335cd248c6ff53ea4f01559c86591`.
- Canonical candidate ID list: `699ff34bcf8dd4b5043eed48384973cb5109fd86ca260f831a502097370238df`.

The retained candidate-only epoch-provenance JSONL was also streamed independently: 1,571,640 records parsed without malformed JSON, covering all 11,602 candidate-only SourceIDs. Every one of those IDs has at least one currently qualifying raw row in both g and r. The provenance bundle contains 10 additional diagnostic IDs outside the candidate-only set (including two known non-finite-SNR regression cases); these were not counted as candidate-only objects.

**Scope limitation:** these checks independently validate retained full object-ID sets, parent metadata, and the supplied candidate-only epoch-provenance records. They do **not** independently reproduce the complete candidate set from the original g/r archives: those raw archive payloads are not included in the retained compact evidence. A fresh heavy workflow run must verify the official Zenodo archive MD5s, parse the complete raw files, derive candidates from source rows, and compare the result to independent Table 4 membership.

## Scientific interpretation

- Candidate-only means absent from the supplied published membership reference, not a new astrophysical discovery.
- The four-field predicate is diagnostic only; it must not silently become the production selection rule.
- Raw-light-curve and external-cross-match statuses default to NOT_ASSESSED unless explicitly supplied in input metadata.
- The publisher's historical selection semantics remain UNRESOLVED until source evidence or author clarification establishes them.
- Raw datasets must remain outside Git. Keep compact manifests/reports and workflow artifacts with hashes.
