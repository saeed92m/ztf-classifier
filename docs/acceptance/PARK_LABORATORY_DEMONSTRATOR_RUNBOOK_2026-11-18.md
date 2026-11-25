# Park Laboratory Demonstrator — Execution Runbook

**Date:** 2026-11-18  
**Target:** A reproducible, CPU-first laboratory demonstration for the Science and Technology Park  
**Scope:** Real ZTF DR24 acquisition, raw light-curve inspection, diagnostic QC, provenance, and export  
**Status:** Execution procedure; a successful local run is required before claiming the demonstration is ready.

## 1. Demonstrator boundary

The current repository contains a DR24 Explorer in the Workbench. It can request 1–10 positive DR24 OIDs through the indexed HATS API. It displays source-native epochs, a light-curve plot, a diagnostic QC assessment, and acquisition provenance. It can export the complete raw response as JSON.

This is a real-data acquisition and inspection demonstrator. It is **not** a validated DR24 classifier.

The DR24 Explorer deliberately:
- preserves HMJD as HMJD;
- preserves native `mag`, `magerr`, `clrcoeff`, and `catflags`;
- keeps each OID as a separate record;
- does not apply an approved production quality mask;
- does not convert photometry or time values to the frozen v0.2.0 input contract;
- does not generate v0.2.0 features or run model inference;
- does not silently fall back to ALeRCE.

The QC policy is `ztf-dr24-raw-qc-diagnostic-v1` and its status is `DIAGNOSTIC_NOT_PRODUCTION_APPROVED`.

## 2. Reproducible pinned sample

Use these two OIDs for the first live run:

| DR24 OID | Filter | Expected epochs | Expected payload SHA-256 |
|---:|:---:|---:|---|
| 264114400013085 | g | 78 | `735ee15135670a1a28b03b76edfb394e9c0c193d528f3da56ebb593468baf2a0` |
| 264214400000912 | r | 123 | `a37f6fa2ee91009805b6fab3a5563b793cba9e84f6a82ec333bae507442c70ae` |

These are separate survey OIDs. Do not describe them as one confirmed astrophysical source unless an independent identity association is established.

## 3. Use an isolated checkout

Do not reset, clean, or overwrite an existing working tree. Use a separate clone for the Park demonstration:

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/saeed92m/ztf-classifier.git ztf-classifier-park-demo
cd ztf-classifier-park-demo
git rev-parse HEAD
```

The project requires Python 3.11.

```bash
python3.11 --version
python3.11 -m venv .venv-park
source .venv-park/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.lock
python -m pip install -e ".[dr24]"
```

If Python 3.11 is not available, stop and report that condition. Do not silently use Python 3.14; the project declares Python 3.11 as its supported runtime.

## 4. Run the live source-parity test

This test queries the public DR24 HATS source through the actual FastAPI endpoint. It checks the returned OIDs, epoch counts, and pinned payload hashes.

```bash
ZTF_DR24_BATCH_LIVE_TEST=1 python -m pytest -q tests/test_dr24_batch_live_api.py
```

Acceptance for this test:
- the test passes;
- both OIDs are returned;
- no requested OID is missing;
- epoch counts match 78 and 123;
- both payload hashes match the pinned values above.

A failed or skipped test is not a pass. Record the full output and stop before the live demonstration if it fails.

## 5. Start the Workbench

In the activated environment:

```bash
ztf-classifier-api
```

Open this address in a browser on the same machine:

`http://127.0.0.1:8000/workbench/`

Then:
1. Select **DR24 Explorer (raw)** in the left navigation.
2. Enter the two OIDs, separated by a comma:
   `264114400013085, 264214400000912`
3. Select **Load raw light curves**.
4. Confirm that the page displays separate g- and r-band OID panels.
5. Inspect the HMJD/magnitude plots, raw epoch table, QC diagnostic, and acquisition provenance.
6. Select **Download raw JSON + QC**.
7. Keep the exported JSON as a local evidence artifact.

Do not select **Run analysis** for these DR24 OIDs. That action uses the separate normalized observation/model path. The raw DR24 Explorer does not feed the frozen v0.2.0 classifier.

## 6. Evidence to retain

Create a dated evidence folder outside the Git repository. Retain:
- Git commit SHA;
- Python version;
- installed LSDB and s3fs versions;
- complete live-test output;
- Workbench screenshot showing the two separate OID panels;
- exported JSON response;
- SHA-256 of the exported JSON;
- UTC run time;
- any warnings, missing rows, or failures.

Example commands:

```bash
python --version
python -m pip show lsdb s3fs
sha256sum PATH_TO_EXPORTED_JSON
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

Do not commit raw survey data, exported light curves, local databases, model artifacts, credentials, or environment files to Git. Keep the compact evidence package local unless a reviewed, redacted summary is required for the submission.

## 7. What this demonstration proves

If the live test and Workbench run pass, the evidence supports only these claims:
- the application can make a bounded, indexed request to public ZTF DR24 Lightcurves HATS;
- the selected OIDs and returned epoch records can be inspected in the Workbench;
- the response preserves source-native values and per-OID provenance;
- the diagnostic QC and JSON export are available;
- the pinned sample can be checked for repeatable payload content.

## 8. What it does not prove

This run does not prove:
- physical-source identity across different OIDs;
- an approved DR24 photometry or time conversion;
- production QC or a scientifically approved epoch mask;
- compatibility with the frozen 42-feature v0.2.0 contract;
- v0.2.0 model inference on DR24;
- calibrated probabilities, conformal coverage, or scientific anomaly discovery;
- 100,000-light-curve processing or population-level performance.

These claims require separate source, identity, normalization, model-artifact, and scientific-validation evidence. They are not part of this bounded raw-data demonstration.

## 9. Park presentation wording

Use:

> «نمونه آزمایشگاهی سامانه، داده‌های واقعی منحنی نوری ZTF DR24 را از کاتالوگ عمومی HATS به‌صورت هدفمند دریافت می‌کند. کاربر می‌تواند داده خام هر شناسه، نمودار منحنی نوری، شاخص‌های کنترل کیفیت تشخیصی و اطلاعات منشأ و یکپارچگی داده را مشاهده و خروجی قابل بازبینی دریافت کند. اتصال این داده خام به مدل طبقه‌بندی، پس از تکمیل و اعتبارسنجی مستقل قرارداد زمان، نورسنجی، کیفیت داده و شناسه فیزیکی انجام می‌شود.»

Do not describe the raw QC as a validated scientific classifier, and do not present a probability or class label for these DR24 records.
