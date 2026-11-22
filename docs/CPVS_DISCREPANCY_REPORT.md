# CPVS candidate-only discrepancy report

This utility creates an object-level evidence table for candidate IDs absent from the supplied published Table 4 membership list. It is a reporting and triage capability, **not a fix to the CPVS historical selection-rule blocker**.

## Inputs

- \`--parent-metadata\`: TSV/CSV with a stable integer object ID (SourceID or Seq) and all four fields: gmag, rmag, Per-g, Per-r.
- \`--candidate-ids\` and \`--published-ids\`: TSV/CSV files with an ID column.
- \`--source-revision\`: code revision that produced the input files.

Every candidate-only ID must join to exactly one parent metadata row. Duplicate IDs, missing required columns, malformed IDs, missing parent provenance, and invalid/unmapped Table 4 name crosswalks stop report generation.

**Important Table 4 join-key requirement:** the official published Table 4 contains both a ZTF object-name column (`ZTF`) and its own numeric internal `ID`. The report builder must join by normalized ZTF object name to the parent Table 2 `ID` name and map that name to the parent's `Seq`/SourceID. Never compare Table 4's numeric `ID` directly with parent `Seq`.

For the official Table 2 parent metadata input, include both the object name and source identifier, as well as the four diagnostic fields. For example, retrieve a VizieR TSV with columns `ID,Seq,gmag,rmag,Per-g,Per-r`; an export containing only `Seq,Per,gmag,rmag,Per-g,Per-r` is insufficient for the name crosswalk unless a separate verified crosswalk is joined first. A suitable published-reference export is Table 4 columns `ZTF,ID`. Record the exact query URLs, retrieval time, raw response hashes, and source revision alongside the inputs.

## Outputs

- cpvs_candidate_only_objects.csv: all candidate-only IDs, original metadata columns, feature status/reasons, raw-light-curve and cross-match states.
- cpvs_candidate_only_objects.html: local filterable object table with links by SourceID.
- cpvs_object_detail.html: per-object evidence view; open with a SourceID fragment from the table or enter an ID.
- cpvs_discrepancy_summary.json: counts and interpretation boundaries.
- cpvs_discrepancy_report.md: human-readable summary.
- cpvs_discrepancy_manifest.json: source and output SHA-256 hashes.

Example:

\`\`\`bash
python scripts/build_cpvs_discrepancy_report.py \\
  --parent-metadata /path/to/parent_metadata.tsv \\
  --candidate-ids /path/to/candidate_ids.tsv \\
  --published-ids /path/to/published_table4_ids.tsv \\
  --source-revision "$(git rev-parse HEAD)" \\
  --output-dir /path/to/cpvs-discrepancy-report
\`\`\`

## Scientific interpretation

- Candidate-only means absent from the supplied published membership reference, not a new astrophysical discovery.
- The four-field predicate is diagnostic only; it must not silently become the production selection rule.
- Raw-light-curve and external-cross-match statuses default to NOT_ASSESSED unless explicitly supplied in input metadata.
- The publisher's historical selection semantics remain UNRESOLVED until source evidence or author clarification establishes them.
- Raw datasets must remain outside Git. Keep compact manifests/reports and workflow artifacts with hashes.
