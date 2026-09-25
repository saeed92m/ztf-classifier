# Scientific Report Contract

The report layer is a read-only presentation boundary over ScientificResultStore.

## Endpoint

GET /v1/results/{result_id}/report

The endpoint:

- loads the persisted result by stable result ID;
- does not execute inference;
- renders a deterministic Markdown report;
- includes object, survey, model, result schema, prediction, probabilities, diagnostics, observation count, feature count, provenance, and reproducibility metadata;
- returns 404 scientific_result_not_found when the durable result does not exist.

The report schema is versioned independently from the scientific-result schema. A report is a derived presentation artifact and is never written back as a replacement scientific result.

## Architecture

ScientificResultStore -> ScientificReportService -> API/UI

The same service can later support PDF, HTML, notebook, or archive renderers without changing scientific persistence.
