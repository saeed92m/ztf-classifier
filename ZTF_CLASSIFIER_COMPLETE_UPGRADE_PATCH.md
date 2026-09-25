# ZTF Classifier — Complete Upgrade Patch Specification

## هدف

این سند specification کامل برای ارتقای repository زیر است:

https://github.com/saeed92m/ztf-classifier

هدف، ارتقای پروژه از وضعیت فعلی `v0.3.0` به یک نسخه‌ی hardened و reproducible است، بدون شکستن:

- scientific baseline `v0.2.0`;
- dataset contract `benchmark_v0.2`;
- frozen 42-feature schema;
- model version `baseline_v0.2`;
- artifact schemaهای قبلی؛
- CLI output schemaهای قبلی؛
- backward compatibility با artifact schema `1.0` و `1.1`;
- تست‌های فعلی؛
- رفتار فعلی inference، مگر در مواردی که این سند صراحتاً اصلاح آن را خواسته است.

---

# قوانین قطعی اجرای کار

## 1. قبل از تغییر

قبل از هر modification:

1. branch جدید بساز:
   ```text
   chore/complete-upgrade-v0.4
   ```

2. وضعیت اولیه را ثبت کن:
   ```bash
   git status
   python --version
   python -m pip check
   python -m ruff check src tests
   python -m pytest -q
   ```

3. در صورت وجود خطاهای اولیه، آن‌ها را در فایل زیر ثبت کن:
   ```text
   reports/upgrade/baseline_test_status.md
   ```

4. قبل از تغییر، این موارد را backup/record کن:
   - version فعلی package؛
   - artifact schema؛
   - CLI schema؛
   - model version؛
   - feature schema hash؛
   - خروجی تست‌های فعلی؛
   - تعداد testها؛
   - وضعیت CI.

## 2. ممنوعیت تغییر علمی بدون درخواست

این موارد نباید در این patch تغییر کنند:

- ترتیب 42 feature فعلی؛
- نام featureهای frozen v0.2؛
- کلاس‌های مدل؛
- mapping کلاس‌ها؛
- مدل `baseline_v0.2`؛
- hyperparameterهای frozen baseline؛
- splitهای immutable scientific baseline؛
- labels موجود؛
- منطق تولید گزارش‌های v0.2؛
- خروجی artifactهای موجود.

اگر اصلاحی برای نسخه‌ی جدید لازم است، آن را با version جدید انجام بده و baseline قبلی را immutable نگه دار.

## 3. ممنوعیت جعل نسخه

هیچ نسخه‌ای برای dependencyها را حدس نزن یا بدون بررسی تعیین نکن.

نسخه‌ها باید از یکی از این روش‌ها تولید شوند:

- environment فعلی و آزمایش‌شده؛
- `pip freeze` از environment سالم؛
- `uv lock`;
- `pip-compile`;
- مستندات رسمی package؛
- اجرای واقعی تست‌ها.

اگر dependencyای با Python 3.11 سازگار نیست، آن را به‌صورت مستند اصلاح کن.

## 4. هیچ تغییر ناقصی تحویل نده

در پایان فقط زمانی کار را complete اعلام کن که تمام موارد زیر اجرا و موفق شده باشند:

```bash
python -m ruff check src tests
python -m ruff format --check src tests
python -m pytest -q
python -m build
python -m pip install --force-reinstall dist/*.whl
python -m pip check
python -c "import ztf_classifier; print(ztf_classifier.__file__)"
```

اگر ابزاری مانند `mypy` یا `pip-audit` اضافه شد، آن‌ها نیز باید اجرا شوند.

---

# بخش اول — نسخه‌بندی و release policy

## نسخه‌ها

نسخه‌های زیر را شفاف و جدا نگه دار:

| مفهوم | مقدار |
|---|---|
| Software version | `0.4.0` |
| Previous software version | `0.3.0` |
| Dataset version | `benchmark_v0.2` |
| Scientific baseline | `v0.2.0` |
| Model version | `baseline_v0.2` |
| Feature schema | `v0.2`, 42 features |
| Artifact schema | فعلی حفظ شود؛ schema جدید فقط با migration و backward compatibility |
| CLI schema | فعلی حفظ شود؛ تغییرات additive باشند |

اگر تغییرات فقط bug fix هستند، software version را `0.3.1` نگه دار. اگر تغییرات جدید contract یا capability اضافه می‌کنند، `0.4.0` مناسب است.

## Changelog

`CHANGELOG.md` را با بخش زیر به‌روزرسانی کن:

```markdown
## [0.4.0] - YYYY-MM-DD

### Added
- Reproducible dependency lock and environment metadata.
- Stronger CI validation.
- Artifact and feature-schema checksums.
- Explicit calibration, conformal, and OOD status reporting.
- Strict ingestion diagnostics.
- Model card and data card.
- Package build and wheel-install validation.

### Changed
- Improved production inference diagnostics.
- Improved ALeRCE input validation.
- Added release and provenance metadata.

### Compatibility
- Existing v0.2 scientific baseline remains unchanged.
- Existing artifact schemas 1.0 and 1.1 remain readable.
- Existing CLI output fields remain available.

### Fixed
- Independent handling of conformal and OOD diagnostics.
- More explicit handling of missing or incomplete diagnostics.

### Limitations
- The benchmark remains small and label quality remains dependent on ALeRCE.
- Results must not be interpreted as representative of the full ZTF population.
```

تاریخ واقعی release را جایگزین `YYYY-MM-DD` کن.

---

# بخش دوم — pyproject.toml

## هدف

`pyproject.toml` باید:

- metadata کامل داشته باشد؛
- dependencyهای production و development را تفکیک کند؛
- ابزارهای quality را مشخص کند؛
- package build را قابل‌تکرارتر کند؛
- license را با وضعیت واقعی پروژه هماهنگ کند.

## کارهای لازم

1. dependencyهای runtime را بر اساس environment آزمایش‌شده pin یا lock کن.
2. dependencyهای optional را از runtime اصلی حذف کن، مگر واقعاً در importهای production لازم باشند.
3. `lightgbm` و `shap` را فقط در صورتی dependency اصلی نگه دار که کد production واقعاً به آن‌ها نیاز داشته باشد.
4. notebook dependencyها در گروه notebook بمانند.
5. dev tooling را در گروه dev قرار بده.
6. `project.urls` اضافه کن.
7. `keywords` اضافه کن.
8. `classifiers` اضافه کن.
9. `maintainers` را در صورت مشخص بودن اضافه کن.
10. license را با قصد واقعی پروژه هماهنگ کن:
    - اگر open-source است، فایل `LICENSE` استاندارد اضافه کن.
    - اگر proprietary است، در README به‌وضوح توضیح بده که repository عمومی است اما code/data/model چه محدودیت‌هایی دارند.

## dependency lock

یکی از این روش‌ها را انتخاب کن و فقط همان را canonical اعلام کن:

- `uv.lock`
- یا `requirements.lock`
- یا `requirements.txt` تولیدشده با `pip-compile`

در README دستور نصب reproducible باید دقیقاً از همان lockfile استفاده کند.

نمونه policy:

```text
Primary development environment:
- Python 3.11.x
- Locked dependencies: uv.lock
- OS tested: Ubuntu latest in GitHub Actions
```

## ابزارهای اضافه‌شده

در صورت استفاده، این ابزارها را به dev dependency اضافه کن:

- `build`
- `pytest-cov`
- `pip-audit`
- `ruff`
- `mypy`، فقط اگر type errors قابل‌اصلاح هستند
- `pre-commit`، در صورت ایجاد config معتبر

---

# بخش سوم — CI و GitHub Actions

فایل `.github/workflows/ci.yml` را ارتقا بده.

## الزامات

CI باید این مراحل را داشته باشد:

1. checkout
2. setup Python
3. نصب lockfile
4. نصب package
5. `pip check`
6. Ruff lint
7. Ruff format check
8. pytest با coverage
9. package build
10. نصب wheel تولیدشده
11. import test
12. در صورت اضافه‌شدن، `pip-audit`

## مثال ساختار

```yaml
name: CI

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read

jobs:
  test:
    name: Python 3.11 - Test, Lint, Build
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Upgrade packaging tools
        run: |
          python -m pip install --upgrade pip setuptools wheel

      - name: Install project
        run: |
          python -m pip install -e ".[dev]"
          python -m pip install build pytest-cov pip-audit

      - name: Verify dependencies
        run: python -m pip check

      - name: Ruff lint
        run: python -m ruff check src tests

      - name: Ruff format
        run: python -m ruff format --check src tests

      - name: Test suite
        run: |
          python -m pytest -q \
            --cov=ztf_classifier \
            --cov-report=term-missing \
            --cov-report=xml \
            --cov-fail-under=80

      - name: Build package
        run: python -m build

      - name: Install built wheel
        run: |
          python -m pip install --force-reinstall dist/*.whl
          python -m pip check

      - name: Verify package import
        run: |
          python -c "import ztf_classifier; print(ztf_classifier.__file__)"

      - name: Audit dependencies
        run: python -m pip_audit
```

اگر lockfile با pip سازگار نیست، نصب CI را با ابزار lockfile انجام بده. ساختار workflow نباید صرفاً ظاهری باشد؛ باید واقعاً در CI اجرا و سبز شود.

## CIهای تکمیلی پیشنهادی

به‌صورت جداگانه اضافه کن:

- `dependency-review.yml` برای pull request؛
- `codeql.yml`؛
- workflow هفتگی برای dependency drift؛
- workflow release برای tagها؛
- Dependabot config.

هیچ secret جدیدی لازم نیست.

---

# بخش چهارم — provenance و checksum

## هدف

هر artifact باید قابل‌ردگیری و قابل‌اعتبارسنجی باشد.

## metadata لازم

برای artifact مدل، این metadataها را اضافه کن:

```json
{
  "software_version": "0.4.0",
  "model_version": "baseline_v0.2",
  "dataset_version": "benchmark_v0.2",
  "feature_schema_version": "v0.2",
  "artifact_schema_version": "1.1",
  "git_commit": "...",
  "created_at_utc": "...",
  "python_version": "...",
  "platform": "...",
  "feature_schema_sha256": "...",
  "training_dataset_sha256": "...",
  "model_file_sha256": "..."
}
```

مقادیر باید در زمان build واقعاً تولید شوند، نه hard-code شوند.

## checksum utility

یک utility عمومی اضافه کن، مثلاً:

```text
src/ztf_classifier/reproducibility/checksums.py
```

این utility باید:

- SHA-256 فایل را تولید کند؛
- برای فایل‌های missing خطای مشخص بدهد؛
- binary و text را درست بخواند؛
- deterministic باشد؛
- تست unit داشته باشد.

## loader behavior

`ModelArtifactLoader` باید:

- metadata را بخواند؛
- schema version را validate کند؛
- checksum موجود را verify کند؛
- mismatch را با exception مشخص اعلام کند؛
- امکان compatibility با artifactهای قدیمی را حفظ کند؛
- برای artifactهای قدیمی که checksum ندارند، warning/status مشخص تولید کند، نه اینکه بی‌صدا رفتار کند.

هرگز artifact قدیمی را بدون دلیل overwrite یا migrate destructive نکن.

---

# بخش پنجم — مستقل‌سازی Calibration، Conformal و OOD

فایل مهم:

```text
src/ztf_classifier/models/production_inference.py
```

## رفتار لازم

Calibration، conformal و OOD باید مستقل باشند.

رفتار مطلوب:

```python
calibrated_probabilities = raw_probabilities
calibration_status = "unavailable"

if calibration is not None:
    calibrated_probabilities = TemperatureScaler().transform(
        raw_probabilities,
        calibration.temperature,
    )
    calibration_status = "available"
else:
    calibration_status = "unavailable"
```

برای conformal:

```python
conformal = None
conformal_status = "unavailable"

if self.loaded_artifact.conformal is not None:
    conformal = ProductionConformalDiagnostics.predict(
        calibrated_probabilities,
        self.loaded_artifact.conformal,
    )
    conformal_status = "available"
```

برای OOD:

```python
ood = None
ood_status = "unavailable"

if (
    self.loaded_artifact.ood is not None
    and self.loaded_artifact.ood_model is not None
):
    # calculate OOD independently
    ood_status = "available"
```

## قواعد

- نبودن OOD نباید conformal را خاموش کند.
- نبودن conformal نباید OOD را خاموش کند.
- نبودن calibration باید به‌صورت explicit گزارش شود.
- اگر probabilities خام هستند، status باید `uncalibrated` یا مقدار معادل واضح باشد.
- هیچ warning مهمی نباید silently حذف شود.

## output fields

به `PredictionResult` یا builder، بدون حذف فیلدهای قبلی، این metadataها را اضافه کن:

```text
calibration_status
conformal_status
ood_status
warnings
artifact_schema_version
artifact_hash
feature_schema_hash
software_version
model_version
```

نام دقیق فیلدها را با conventions موجود پروژه هماهنگ کن.

---

# بخش ششم — سخت‌گیری ingestion و ALeRCE

فایل اصلی:

```text
src/ztf_classifier/io/alerce.py
```

## validationهای لازم

قبل از خروجی internal dataframe بررسی کن:

### MJD

- numeric باشد؛
- finite باشد؛
- مقدار منفی یا غیرمنطقی reject شود؛
- تعداد invalidها گزارش شود.

### fid

- numeric یا قابل تبدیل باشد؛
- فقط bandهای پشتیبانی‌شده پذیرفته شوند؛
- unknown bandها با error یا diagnostic مشخص مدیریت شوند.

### photometry

- `mag` finite باشد؛
- `magerr` finite و بزرگ‌تر از صفر باشد؛
- fallback از corrected به raw شمارش شود؛
- اگر raw نیز نامعتبر است، row حذف یا reject شود طبق policy مشخص.

### coordinates

- `ra` بین 0 و 360 باشد؛
- `dec` بین -90 و 90 باشد؛
- invalid coordinates در report مشخص شوند.

### duplicates

policy روشن داشته باش:

- حذف exact duplicate؛
- یا نگهداری با diagnostic؛
- duplicate detection با کلید مناسب انجام شود؛
- ترتیب زمانی deterministic بماند.

### booleans

رفتار فعلی strict boolean parsing حفظ شود و تست‌های جدید برای مقادیر زیر اضافه شود:

```text
true, false, 1, 0, yes, no, y, n, t, f, empty, unknown
```

مقدار `unknown` باید error بدهد.

## diagnostics

یک ساختار immutable یا dictionary استاندارد اضافه کن:

```python
{
    "rows_input": ..., 
    "rows_output": ..., 
    "rows_dropped": ..., 
    "invalid_mjd": ..., 
    "invalid_fid": ..., 
    "invalid_mag": ..., 
    "invalid_magerr": ..., 
    "invalid_coordinates": ..., 
    "duplicate_rows": ..., 
    "corrected_photometry_count": ..., 
    "raw_fallback_count": ...,
}
```

اگر تغییر API فعلی breaking است، API فعلی را حفظ کن و diagnostics را از طریق تابع یا result جدید ارائه بده.

---

# بخش هفتم — feature leakage و provenance

## هدف

باید ثابت شود که featureهای temporal از آینده استفاده نمی‌کنند.

## metadata برای هر feature

برای frozen feature schema، تا حد ممکن این ستون‌ها را به manifest اضافه کن:

```text
feature
feature_order
feature_group
source_columns
minimum_observations
uses_future_observations
cutoff_compatible
missing_behavior
units
```

## تست temporal invariance

تست جدید اضافه کن:

1. از یک light curve، cutoff مشخص بساز.
2. featureهای قبل از cutoff را استخراج کن.
3. observationهای بعد از cutoff را اضافه کن.
4. دوباره با همان cutoff featureها را استخراج کن.
5. تمام featureهای finite باید برابر باشند.
6. اختلاف فقط در tolerance عددی مجاز است.

این تست باید برای:

- basic features؛
- periodicity؛
- cross-band features؛
- missing band؛
- observationهای ناکافی

اجرا شود.

## ممنوعیت

هیچ feature جدیدی را به frozen v0.2 اضافه نکن. featureهای جدید فقط در schema جدید مثل `v0.3` یا `v0.4` اضافه شوند.

---

# بخش هشتم — تست‌های جدید

تست‌های جدید باید به‌صورت جدا و قابل‌فهم اضافه شوند.

## checksum tests

- checksum deterministic است.
- تغییر یک byte checksum را تغییر می‌دهد.
- فایل missing خطای صحیح می‌دهد.

## artifact compatibility tests

- artifact schema 1.0 load می‌شود.
- artifact schema 1.1 load می‌شود.
- artifact با checksum غلط reject می‌شود.
- artifact بدون checksum warning/status مناسب دارد.
- artifact با feature schema اشتباه reject می‌شود.

## inference diagnostic tests

سناریوهای زیر را تست کن:

1. همه diagnostics موجود هستند.
2. فقط calibration موجود است.
3. فقط conformal موجود است.
4. فقط OOD موجود است.
5. conformal موجود اما OOD موجود نیست.
6. OOD موجود اما conformal موجود نیست.
7. هیچ diagnostic اضافه‌ای موجود نیست.
8. calibration missing است و probabilities خام برمی‌گردند.
9. warnings بدون حذف سایر outputها تولید می‌شوند.

## ingestion tests

- invalid MJD
- invalid fid
- invalid magnitude
- zero/negative magerr
- invalid RA/DEC
- duplicate detections
- boolean unknown
- corrected photometry
- raw fallback
- empty dataframe
- one-row dataframe
- all-invalid dataframe

## CLI tests

- direct artifact
- registry-backed model
- artifact و registry همزمان؛ باید reject شود
- missing artifact
- invalid model version
- empty batch
- existing output file
- metadata output
- status fields
- checksum fields

## package tests

بعد از build:

```bash
python -m build
python -m pip install --force-reinstall dist/*.whl
python -c "import ztf_classifier"
ztf-classifier --help
```

---

# بخش نهم — Data Card و Model Card

## فایل‌ها

ایجاد کن:

```text
docs/DATA_CARD.md
docs/MODEL_CARD.md
```

## Data Card باید شامل این موارد باشد

- منبع داده: ZTF / ALeRCE
- dataset version
- تعداد objectها
- تعداد کلاس‌ها
- تعداد نمونه در هر کلاس
- selection strategy
- probability threshold
- fallback policy
- band coverage
- missingness
- label provenance
- weak-label limitation
- temporal range
- known selection bias
- license/data usage constraints
- reproducibility instructions

## Model Card باید شامل این موارد باشد

- model version
- model family
- feature schema
- training data
- training procedure
- cross-validation protocol
- temporal validation protocol
- calibration
- conformal prediction
- OOD detection
- metrics
- per-class results
- confidence intervals
- intended use
- out-of-scope use
- known failure modes
- domain shift risk
- label limitations
- security considerations
- artifact loading warning
- version compatibility

---

# بخش دهم — README

README را بدون حذف اطلاعات فعلی به‌روزرسانی کن.

## بخش‌های لازم

### Quick start

دستورهای واقعی و آزمایش‌شده:

```bash
git clone https://github.com/saeed92m/ztf-classifier.git
cd ztf-classifier

# install exact environment
...

# run tests
python -m pytest -q

# inspect CLI
ztf-classifier --help
```

### Reproducible environment

واضح بنویس:

- Python version
- OS
- package manager
- lockfile
- install command
- known unsupported environments

### Scientific baseline

صریح اعلام کن که:

- baseline immutable است؛
- نسخه جدید نتیجه‌های baseline را بازتولید یا overwrite نمی‌کند؛
- benchmark فعلی کوچک است؛
- labels ground truth مستقل نیستند؛
- نتایج نماینده کل ZTF نیستند.

### Artifact compatibility

یک جدول اضافه کن:

| Artifact schema | Loadable | Notes |
|---|---|---|
| 1.0 | Yes | Legacy compatibility |
| 1.1 | Yes | Current |
| future schema | Only after migration | Explicit compatibility required |

### Security warning

هشدار بده که artifactهای pickle/joblib فقط از منبع مورداعتماد load شوند.

### License

وضعیت code، data و model را جداگانه توضیح بده.

---

# بخش یازدهم — Dataset و artifact storage

## هدف

repository بیش از حد با binary generated files سنگین نشود.

## کار لازم

بدون حذف ناگهانی artifactهای فعلی:

1. `.gitignore` را بررسی کن.
2. مشخص کن کدام فایل‌ها source و کدام generated هستند.
3. برای dataset و artifactهای بزرگ یکی از این روش‌ها را انتخاب کن:
   - Git LFS
   - DVC
   - release assets
   - object storage
4. اگر migration انجام می‌شود، manifest و checksum را حفظ کن.
5. README را با دستور download/restore به‌روزرسانی کن.

## ممنوعیت

فایل‌های لازم برای تست را حذف نکن، مگر اینکه fixture جایگزین و تست‌شده ایجاد شود.

---

# بخش دوازدهم — quality و typing

## Ruff

Ruff را فعال نگه دار و در صورت امکان این موارد را اضافه کن:

- lint
- format
- import sorting
- unused imports
- obvious bug patterns

اصلاحات صرفاً stylistic نباید رفتار runtime را تغییر دهند.

## Typing

اگر `mypy` اضافه می‌شود:

- ابتدا فقط package اصلی را بررسی کن؛
- third-party missing stubs را مدیریت کن؛
- type ignore بی‌دلیل اضافه نکن؛
- `Any` را بی‌رویه استفاده نکن؛
- type errors را واقعاً حل کن.

## Coverage

coverage threshold را واقع‌بینانه انتخاب کن. اگر coverage فعلی کمتر از 80٪ است:

- ابتدا مقدار واقعی را اندازه بگیر؛
- threshold را پایین‌تر اما موقت تعیین نکن مگر در گزارش ثبت شود؛
- کد جدید باید coverage کامل داشته باشد؛
- generated code و notebook code را جدا کن.

---

# بخش سیزدهم — monitoring و production diagnostics

در صورت امکان، بدون افزودن dependency سنگین، این موارد را به inference/batch اضافه کن:

- تعداد rows ورودی؛
- تعداد rows معتبر؛
- زمان inference؛
- missingness summary؛
- تعداد OOD flagها؛
- تعداد prediction setهای بزرگ؛
- calibration status؛
- model version؛
- artifact hash؛
- feature schema hash.

لاگ‌ها نباید شامل secret یا داده حساس باشند.

برای external API:

- timeout اجباری؛
- retry محدود؛
- exponential backoff؛
- خطای rate limit مشخص؛
- response schema validation؛
- cache/provenance؛
- failure report.

---

# بخش چهاردهم — GitHub repository hardening

در صورت امکان این فایل‌ها را اضافه کن:

```text
.github/dependabot.yml
.github/workflows/codeql.yml
.github/workflows/dependency-review.yml
```

## تنظیمات پیشنهادی repository

- branch protection روی `main`;
- required CI checks;
- pull request review؛
- جلوگیری از push مستقیم در صورت امکان؛
- Dependabot updates؛
- CodeQL؛
- secret scanning؛
- dependency graph.

هیچ permission اضافه‌ای به workflowها نده. اصل least privilege رعایت شود.

---

# بخش پانزدهم — Performance و resource safety

برای pipelineهای batch بررسی کن:

- کل dataset بی‌دلیل در memory چند بار کپی نشود؛
- Parquet به‌صورت columnar خوانده شود؛
- امکان batch/chunk processing وجود داشته باشد؛
- logging progress برای batchهای بزرگ وجود داشته باشد؛
- input خالی و input بسیار بزرگ رفتار مشخص داشته باشند؛
- memory error با پیام قابل‌فهم مدیریت شود.

یک تست یا benchmark سبک اضافه کن که:

- زمان inference یک object را اندازه بگیرد؛
- زمان batch کوچک را اندازه بگیرد؛
- peak memory تقریبی را بررسی کند، اگر tooling موجود است.

---

# بخش شانزدهم — Scientific evaluation improvements

این بخش نباید baseline فعلی را تغییر دهد. فقط report و evaluation جدید اضافه کن.

## گزارش‌های لازم برای benchmark جدید

- accuracy
- balanced accuracy
- macro F1
- weighted F1
- log loss
- per-class precision
- per-class recall
- per-class F1
- support
- confusion matrix
- top-k accuracy
- calibration curve
- Brier score
- ECE
- conformal coverage
- average prediction-set size
- class-wise coverage
- OOD score distribution
- temporal degradation
- performance versus observation count
- performance versus missing band

## confidence intervals

برای metricهای اصلی confidence interval اضافه کن:

- bootstrap با seed ثابت؛
- تعداد bootstrap مشخص؛
- method مستند؛
- seed و config در manifest ذخیره شود.

## baselineهای مقایسه‌ای

در صورت امکان گزارش کن:

- majority classifier
- stratified random
- logistic regression
- random forest
- XGBoost baseline فعلی

این baselineها نباید model artifact فعلی را overwrite کنند.

---

# بخش هفدهم — Acceptance Criteria

پچ فقط زمانی قابل قبول است که همه‌ی موارد زیر برقرار باشند:

## Repository

- [ ] branch upgrade ایجاد شده است.
- [ ] تغییرات atomic و قابل‌بررسی هستند.
- [ ] هیچ فایل secret اضافه نشده است.
- [ ] baseline علمی تغییر نکرده است.
- [ ] generated files مشخص شده‌اند.
- [ ] CHANGELOG به‌روزرسانی شده است.

## Packaging

- [ ] package build موفق است.
- [ ] wheel از نو نصب می‌شود.
- [ ] import package موفق است.
- [ ] dependencyها reproducible هستند.
- [ ] license و metadata روشن هستند.

## CI

- [ ] Ruff lint سبز است.
- [ ] Ruff format check سبز است.
- [ ] pytest سبز است.
- [ ] coverage threshold رعایت شده است.
- [ ] pip check سبز است.
- [ ] pip audit بررسی شده است.
- [ ] build در CI انجام می‌شود.

## Model compatibility

- [ ] artifact schema 1.0 load می‌شود.
- [ ] artifact schema 1.1 load می‌شود.
- [ ] checksum mismatch reject می‌شود.
- [ ] feature schema mismatch reject می‌شود.
- [ ] model version metadata حفظ می‌شود.
- [ ] baseline output تغییر نکرده است.

## Inference

- [ ] calibration مستقل عمل می‌کند.
- [ ] conformal مستقل عمل می‌کند.
- [ ] OOD مستقل عمل می‌کند.
- [ ] missing diagnostics explicit هستند.
- [ ] warnings حفظ می‌شوند.
- [ ] output backward-compatible است.
- [ ] artifact hash گزارش می‌شود.
- [ ] feature schema hash گزارش می‌شود.

## Ingestion

- [ ] MJD validation وجود دارد.
- [ ] fid validation وجود دارد.
- [ ] mag/magerr validation وجود دارد.
- [ ] coordinate validation وجود دارد.
- [ ] duplicate policy مستند است.
- [ ] fallback count گزارش می‌شود.
- [ ] invalid rows diagnostic دارند.

## Scientific quality

- [ ] Data Card اضافه شده است.
- [ ] Model Card اضافه شده است.
- [ ] benchmark limitations صریح هستند.
- [ ] label provenance مستند است.
- [ ] temporal leakage test اضافه شده است.
- [ ] calibration limitations مستند شده است.
- [ ] conformal assumptions مستند شده است.
- [ ] OOD limitations مستند شده است.

---

# بخش هجدهم — گزارش نهایی مورد انتظار

در پایان یک فایل ایجاد کن:

```text
reports/upgrade/upgrade_report.md
```

این فایل باید شامل باشد:

1. خلاصه تغییرات؛
2. فهرست فایل‌های تغییرکرده؛
3. دلیل هر تغییر؛
4. dependencyهای نهایی و نسخه آن‌ها؛
5. تست‌های اجراشده؛
6. خروجی تست‌ها؛
7. coverage؛
8. build result؛
9. compatibility result؛
10. benchmark baseline comparison؛
11. known limitations؛
12. مواردی که به دلیل نبود environment یا data اجرا نشده‌اند؛
13. دستور rollback؛
14. دستور اجرای نسخه جدید؛
15. دستور بازتولید baseline قبلی.

اگر هر تستی قابل اجرا نبود، آن را به‌عنوان `NOT VERIFIED` گزارش کن و هرگز به‌عنوان موفق اعلام نکن.

---

# بخش نوزدهم — دستورهای نهایی برای اجرا

پس از تکمیل تغییرات:

```bash
git diff --stat
git diff --check

python -m ruff check src tests
python -m ruff format --check src tests
python -m pytest -q

python -m build

python -m pip install --force-reinstall dist/*.whl
python -m pip check

python -c "import ztf_classifier; print(ztf_classifier.__file__)"
ztf-classifier --help

git status
```

در صورت وجود lockfile، environment را از ابتدا در یک محیط تمیز بساز و تست کن.

## تست clean-room

در محیط جدید:

```bash
python -m venv .venv-clean
source .venv-clean/bin/activate
python -m pip install --upgrade pip
# install using the canonical lockfile
# install package
# run tests
```

روی Windows/WSL، معادل فعال‌سازی محیط را استفاده کن.

---

# بخش بیستم — Commitهای پیشنهادی

تغییرات را در commitهای کوچک و قابل‌بررسی انجام بده:

```text
chore: record baseline test and environment status
build: make dependency resolution reproducible
ci: harden lint test build and audit checks
feat: add artifact checksums and provenance metadata
fix: decouple calibration conformal and ood diagnostics
fix: strengthen alerce ingestion validation
test: add artifact compatibility and ingestion edge cases
docs: add data card and model card
docs: document reproducibility and compatibility policy
chore: add upgrade report and changelog
```

هر commit باید بعد از تغییر، تست مرتبط خود را پاس کند.

---

# نتیجه مورد انتظار

نتیجه باید یک repository باشد که:

- baseline علمی قبلی را حفظ می‌کند؛
- dependencyهای reproducible دارد؛
- package قابل build و install است؛
- CI واقعی و سخت‌گیر دارد؛
- artifactها قابل‌ردگیری و قابل‌اعتبارسنجی هستند؛
- calibration/conformal/OOD مستقل و شفاف‌اند؛
- ingestion در برابر داده خراب مقاوم‌تر است؛
- limitations علمی را پنهان نمی‌کند؛
- model card و data card دارد؛
- backward compatibility را حفظ می‌کند؛
- فقط پس از اجرای واقعی تست‌ها complete اعلام می‌شود.

هر جایی که اجرای واقعی یا داده کافی وجود ندارد، به‌جای حدس‌زدن، آن را صریحاً با وضعیت `NOT VERIFIED` گزارش کن.

