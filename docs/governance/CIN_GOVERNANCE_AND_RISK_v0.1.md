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


## 11. Current repository privacy and security boundary (read-only findings)

Inspected against the pinned repository baseline used by the CIN integration assessment:

- The current FastAPI application has an optional shared `ZTF_API_KEY` Bearer check for `/v1/` routes. It does not establish individual participant identities, contributor roles, task-level authorization, consent or participant-specific access control.
- The existing API uses local SQLite stores for analysis jobs and scientific results. These stores are not a CIN contribution ledger and do not establish multi-user isolation, retention enforcement, deletion workflows or tested backup/restore.
- The Workbench stores appearance preferences in browser `localStorage`; the inspected preference keys cover theme and day/night settings. No CIN participant telemetry or contributor profile flow was identified in the inspected Workbench code.
- The example environment file explicitly says to keep a real API credential in deployment secret management and not in source control.
- No CIN recruitment, account, consent, contribution, moderation or public task endpoint exists in the inspected application.
- Deployment configuration, reverse-proxy protections, production secret rotation, database filesystem permissions, backup jobs and incident procedures were not established by this source inspection.

These findings describe the inspected repository modules. They are not a complete security audit or proof that every deployment is configured in the same way.

### 11.1 Minimum privacy design before participant recruitment

1. Publish a plain-language privacy notice and task-specific consent text before collecting contributions.
2. Define the controller/operator, purpose, lawful basis where applicable, participant rights, contact route and applicable jurisdiction with qualified review.
3. Store a pseudonymous contributor reference in scientific contribution records. Keep account/contact identity in a separate access-controlled system.
4. Do not collect precise location, device fingerprints, unrelated browsing history or sensitive personal data.
5. Define separate retention periods for account data, raw contributions, security logs, audit events and published research datasets.
6. Define correction, account deletion and withdrawal handling. A published dataset must have a documented policy for withdrawal requests and a record of which releases can or cannot be changed.
7. Record only the minimum consent version, timestamp and status needed to prove the relevant permission. Do not put unnecessary personal information in scientific manifests.
8. Explain attribution options and dataset licensing before participation. Do not promise authorship or scientific credit as a reward.

## 12. Initial CIN threat model

This is a proposed threat model for design and testing. It does not claim that the controls are implemented.

| Asset / boundary | Threat | Required control and verification |
|---|---|---|
| Task definitions and scientific sample manifests | Unauthorized task changes, poisoned samples or silent task-version drift | Server-controlled versioned definitions; approval for changes; pinned sample manifests; content hashes; audit tests |
| Contributor identity and assignments | Impersonation, Sybil accounts, assignment takeover or replay | Authenticated participant identity; separate pseudonymous scientific ID; short-lived assignment tokens; server-side ownership checks; replay/idempotency tests |
| Contribution ingestion | Duplicate, malformed, automated or adversarial submissions | Strict schemas and bounds; idempotency keys; rate limits and quotas; abuse monitoring; independent controls; append-only event records |
| Other participants' responses | Response leakage, collusion or model/peer anchoring | Do not expose previous responses or contributor identity to ordinary participants; blind presentation; authorization tests |
| Model predictions | Participants copy the model instead of providing independent evidence | Hide model outputs in ordinary tasks where practical; test UI/API payloads for accidental leakage |
| Scientific identity and source data | Wrong object association, false cross-match or proprietary data entering public tasks | Typed subject references; preserve source IDs; unresolved-identity state; record-level release/access checks; AOIC integration only after acceptance |
| Raw contributions and consensus | Overwriting, tampering, or loss of disagreement | Append-only raw records; corrections as linked events; deterministic consensus reconstruction; hashes and immutable dataset manifests |
| Benchmark and model boundary | Object-level leakage into frozen benchmark or automatic retraining | Explicit exclusion manifests; object-level split tests; separate research datasets; production retraining disabled by default |
| Web task interface | Cross-site scripting, malicious task text or unsafe rendered metadata | Context-aware output escaping; content security policy; strict input schemas; no dynamic code execution; security regression tests |
| API and worker capacity | Denial of service, queue exhaustion or expensive task generation | Request-size limits; bounded queues; concurrency limits; timeouts; rate limits; backpressure; load tests before public access |
| Credentials and operations | API-key exposure, unauthorized database access or untested recovery | Server-side secret storage; no secrets in browser code or logs; least privilege; rotation procedure; encrypted backups; restore drills |
| Dataset publication | Redistribution beyond source or contributor permissions | Per-source license registry; contributor license/consent records; release review; provenance and attribution; block release when rights are unresolved |

### 12.1 Security and privacy release blockers

CIN must remain private/internal until all applicable items below have evidence:

- [ ] Participant authentication and authorization model reviewed.
- [ ] Consent, privacy notice, retention and deletion policies approved.
- [ ] Pseudonymization and identity-data separation tested.
- [ ] Task and contribution ownership/isolation tests pass.
- [ ] Rate limiting, request limits, abuse handling and queue bounds tested.
- [ ] XSS/input validation and security regression tests pass.
- [ ] Secrets management and incident response documented.
- [ ] Backup and restore tested against defined recovery objectives.
- [ ] Source and contributor licensing/attribution rules approved.
- [ ] Dataset export cannot include protected benchmark records or unauthorized source data.

A green CI run, a private technical prototype or a working login screen does not satisfy these gates by itself.
