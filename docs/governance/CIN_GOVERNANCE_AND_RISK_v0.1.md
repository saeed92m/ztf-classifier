# CIN Governance, Privacy, Security and Risk v0.1

**Status:** Proposed governance specification; no participant recruitment or public release is authorized by this document.  
**Canonical source:** ZTF-CIN-ARCH-001 v1.0.0  
**Tracking:** [Issue #251](https://github.com/saeed92m/ztf-classifier/issues/251)

## 1. Scientific authority

Keep machine predictions, raw human contributions, quality-assessed contributions, aggregates, expert annotations, independent reference evidence and ground truth distinct. Consensus is not ground truth. Expert review is a separate evidence class. A novelty score prioritizes investigation; it does not establish discovery.

Human annotations must not enter the protected v0.2.0 benchmark. They must not trigger automatic production retraining. Any model experiment requires a separate versioned dataset, leakage-safe splits, an approved experiment and independent evaluation.

## 2. Participation transparency

Before collection, explain the purpose of each task, data presented, data collected, intended uses, public/private status, retention, deletion process, attribution, privacy choices and limits of scientific interpretation. Participation must be voluntary and consent must be recorded where required.

## 3. Purpose limitation and telemetry

Collect only data needed for task operation, quality evaluation, security and audit. Potential fields include task completion/abandonment, optional confidence, task/presentation version and repeated attempts. Do not collect unrelated browsing behavior, device fingerprints, unnecessary location or sensitive personal data.

## 4. Pseudonymization and retention

Use pseudonymous contributor references in scientific contribution records. Keep identity/account data separate from annotation content where feasible. Define retention periods, access roles, deletion/request handling and legal holds before recruitment. Preserve the minimum audit evidence required to explain dataset releases and quality decisions without retaining unnecessary personal data.

## 5. Security controls

Before deployment, assess authentication, authorization, role separation, input validation, rate limiting, abuse/spam controls, idempotency, audit logging, secret management, database access, data isolation, secure transport, dependency security, backup and restore, incident response and deletion enforcement.

## 6. Licensing and attribution

Review licenses and terms for source observations, images/cutouts, derived assets, annotations and released datasets. Do not assume public astronomy data permit unrestricted redistribution of every derivative. Document contributor license/consent, attribution options, dataset license and publication policy. Do not promise authorship or professional credentials as a participation reward.

## 7. Risk register

| Risk | Mitigation / evidence required |
|---|---|
| Low participation | Reduce friction; evaluate recruitment channels without relaxing quality requirements |
| Low annotation quality | Independently validated controls, repeated assignments and expert review |
| Human bias | Blind presentation and independent assignments |
| Selection bias | Random audits, representative samples and stream-specific analysis |
| Incorrect consensus | Preserve response distributions, disagreement and uncertainty |
| Model anchoring | Hide predictions from ordinary participants where practical |
| Benchmark leakage | Separate stores/manifests and object-level leakage tests |
| Privacy concerns | Purpose limitation, consent, pseudonymization and retention controls |
| Spam/automated responses | Rate limits, anomaly monitoring and review controls |
| Infrastructure cost | Modular deployment and staged scaling |
| Scientific overclaiming | Predeclared metrics, expert review and publication governance |
| Provenance loss | Immutable raw records, manifests and hashes |

## 8. Failure conditions

CIN must not be called scientifically successful if users mainly repeat model predictions, consensus is treated as truth, uncertainty is hidden, provenance is lost, only unusual candidates are sampled, or model improvement is claimed without independent evaluation.

## 9. Dataset governance

Every research dataset release must be immutable and versioned. Its manifest must include source and task versions, selection and QC policies, included/excluded records and reasons, consensus method, expert-review references, checksums, licenses, privacy/retention policy, software revision and environment. Corrections create a new release.

## 10. Release and deployment gates

Do not recruit participants or publish a public CIN release until privacy, consent, retention, licensing, security, incident response, backup/restore and scientific acceptance criteria have been reviewed. A technical MVP is not proof of scientific effectiveness.
