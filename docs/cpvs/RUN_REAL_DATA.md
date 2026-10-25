# Running the CPVS reconstruction on the real catalogues

Executable runbook for Ubuntu/WSL and Windows. Everything here was checked against
the committed files, not against a remembered state of the worktree.

**Gate status: UNRESOLVED.** This runbook produces evidence. It does not, and
cannot, close the scientific gate by itself.

---

## 0. Exact revision

| Item | Value |
|---|---|
| Repository | `https://github.com/saeed92m/ztf-classifier` |
| Branch | `arena/5d244d9d-ztf-classifier` |
| **Commit** | **`4d3d902088ae2ce0dfe5e526f44feb2840e1f151`** (short `4d3d902`) |
| Parent chain | `4d3d902` → `89c6847` → `a04ce3b` → `21faaf5` → `c7066a5` → `c630701` → `d88e54a` (`main`) |
| `main` | untouched at `d88e54a2eb70d5e4531bc950341ef3136c29a5e2` |

`a04ce3b` is an ancestor, not the tip. `4d3d902` is the **code** commit for this
runbook: it contains `a04ce3b` plus the layout resolution, the full-ID traceability
fix, and the checksum-before-analysis fix.

Later commits on the branch do touch code — `scripts/diagnose_cpvs_selection.py`
and `scripts/audit_cpvs_membership.py` were repaired after `4d3d902` (see
`docs/CPVS_RESOLUTION_STATUS_2026-10-25.md`). They are **not** the three files this
runbook executes, so the reconstruction path below is unaffected.

**The file digests are the authoritative check, not the commit name.** The three
digests in the table are unchanged from `4d3d902` through the current tip, and were
re-verified against the working tree. If your digests match, you are running the
audited reconstruction code regardless of which commit you checked out.

The two repaired scripts have their own digests, for anyone auditing the diagnostic
rather than the reconstruction:

| File | SHA-256 |
|---|---|
| `scripts/diagnose_cpvs_selection.py` | `9b6c80f4f8f7e5adcb22e51cd9e8a5fafbf91824e18da56f34df03c364f03b5d` |
| `scripts/audit_cpvs_membership.py` | `29cb09c8ef7aee01f0c1cee6c9f2130a2ddde3c847f6d0563ab9073e2d854562` |

### Verify you have exactly this code

File digests at `4d3d902` (SHA-256 of the committed blob):

| File | SHA-256 | Bytes |
|---|---|---|
| `scripts/reconstruct_cpvs_from_photometry.py` | `5a2fc1ca9ef29506ebf1fa0bbb200c7adf91adad741e226526dd0d96743757f4` | 24,772 |
| `configs/cpvs/cpvs_input_acquisition.json` | `a6234721010453d52d70f8d77cd2d2ec6305a4517eba1181faec264830b47795` | 15,904 |
| `tests/test_cpvs_documented_rule.py` | `d487e63d176c6b3af665ee694b8e2469ef7c8b9bb99c07fc61b6bb5868f7fcf0` | 27,439 |

```bash
git clone https://github.com/saeed92m/ztf-classifier.git
cd ztf-classifier
git checkout 4d3d902088ae2ce0dfe5e526f44feb2840e1f151
git rev-parse HEAD   # must print 4d3d902088ae2ce0dfe5e526f44feb2840e1f151
sha256sum scripts/reconstruct_cpvs_from_photometry.py \
          configs/cpvs/cpvs_input_acquisition.json
```

Windows PowerShell:

```powershell
git clone https://github.com/saeed92m/ztf-classifier.git
cd ztf-classifier
git checkout 4d3d902088ae2ce0dfe5e526f44feb2840e1f151
git rev-parse HEAD
Get-FileHash scripts\reconstruct_cpvs_from_photometry.py -Algorithm SHA256
Get-FileHash configs\cpvs\cpvs_input_acquisition.json  -Algorithm SHA256
```

If the digests differ, stop. You are not running the audited code.

**No dependencies.** The script imports only `argparse`, `dataclasses`,
`hashlib`, `json`, `pathlib`, `sys`, plus `__future__`. Any Python ≥ 3.10 runs it
with no install step and no virtualenv.

---

## 1. What is being verified before any download

Every claim below was re-checked against the committed files and the primary CDS
ReadMes on 2026-10-25.

### 1.1 CLI, as committed

```
--table2 PATH       table2.dat      (required)
--table4 PATH       table4.dat      (required)
--ztf2g  PATH       ztf2g.dat       (required)
--ztf2r  PATH       ztf2r.dat       (required)
--output-dir PATH   created if absent (required)
--manifest PATH     acquisition manifest; checks publisher md5 (optional)
```

Exit codes: **0** report written · **1** refused or aborted (no report written).
There is no exit code that means "the science is resolved". A successful run
writes `status: "UNRESOLVED"` and `validated_on_real_data: false` by construction.

Output path: `<output-dir>/cpvs_documented_rule_report.json`.

### 1.2 Byte layout — resolved from the CDS ReadMes, all 16 spans match the code

`ztf2g.dat` / `ztf2r.dat` (Lrecl 75, 89,697,393 rows each):

| Column | CDS bytes | Format | Documented range | Used |
|---|---|---|---|---|
| `Seq` | 1-6 | I6 | `[1/781604]` | yes |
| `RAdeg` | 8-18 | E11.7 | — | no |
| `DEdeg` | 20-30 | E11.7 | `[-20.8/80.3]` | no |
| `MJD` | 32-44 | F13.7 | `[58197.15/58725.2]` | yes |
| `mag` | 46-55 | F10.7 | `[9.97/22.63]` | yes |
| `e_mag` | 57-70 | E14.7 | `[-0.005/0.4]` | yes |
| `Flag` | 72-75 | I4 | `[0/4628]` | yes |

`table2.dat` (Lrecl 228, 781,602 rows):

| Column | CDS bytes | Format | Documented range | Used |
|---|---|---|---|---|
| `ID` | 1-22 | A22 | — | yes |
| `Seq` | 24-29 | I6 | `[1/781604]` | yes |
| `Per` | 51-61 | F11.7 | `[0.03/973.5]` | no |
| `gmag` | 90-95 | F6.3 | `[11.7/22]?=0` | yes |
| `rmag` | 97-102 | F6.3 | `[11.2/21.4]?=0` | yes |
| `Per-g` | 104-116 | F13.7 | `[0.02/18340]?=0` | yes |
| `Per-r` | 118-130 | F13.7 | `[0.02/13242]?=0` | yes |
| `Ng` | 132-135 | I4 | `[0/2084]` | no |
| `Nr` | 137-140 | I4 | `[0/3300]` | no |

`table4.dat` (Lrecl 63, 730,184 rows): `ZTF` 1-22 A22, `ID` 24-29 I6
`[1/781604]`, `Class` 31-35, `RAdeg` 37-45, `DEdeg` 47-55 `[-21/81]`, `Score` 57-63.

`?=0` is CDS notation for "nullable, null encoded as 0". Those four columns are
read as `None`, never as `0.0`.

### 1.3 The former flag uncertainty, and what it changed

A previous revision recorded the flag span as unverified because the coded width
was four characters and Chen+ 2020's `catflags != 32768` needs five. The ReadMe
resolves it: the span **is** four characters, `I4`, range `[0/4628]`.

That proves the documented cut **cannot apply here** — 32768 is outside the
documented range, so it never occurs and re-applying the cut is a no-op. The
`catflags_32768` policy was therefore **deleted** rather than shipped as a policy
that can never change a result. A test pins its absence.

| Policy | Meaning |
|---|---|
| `none` | no flag cut; closest to Chan+ 2022, which states none |
| `any_nonzero` | undocumented — sensitivity check only |

**UNKNOWN, not approximated:** `INFOBITS < 33,554,432` is an image-level bitmask
absent from all four files. It cannot be reproduced.

### 1.4 No silent empty results

This is the defect that produced the historical false result: unreadable rows were
skipped, so a parse failure became an empty set, which read as "nothing
disagrees". Current behaviour, verifiable in the code and in the
`g_band_rows` / `r_band_rows` fields:

| Situation | Behaviour |
|---|---|
| A row's `Seq` is not an integer | `ValueError` naming file and line number — abort |
| `mag`/`e_mag` unparseable | counted in `unparsed`; row skipped |
| More than 1 % *and* ≥ 100 rows unparseable | `ValueError`: offsets do not match this file — abort |
| `e_mag <= 0` (documented negative errors exist) | counted in `nonpositive_error`; row skipped |
| Blank / comment lines | counted in `blank` |
| Duplicate `Seq` in `table2.dat` | `ValueError` |
| Published name absent from `table2.dat` | `ValueError` listing the names |
| `--manifest` md5 mismatch | `ValueError` naming the inputs — abort |
| Input has no publisher md5 | `NO_PUBLISHER_CHECKSUM` — explicitly not a pass |

Every run reports `rows`, `unparsed`, `nonpositive_error`, `blank` per band per
rule. A non-zero `unparsed` in the output is a signal to inspect, not a footnote.

---

## 2. Download the four files

### 2.1 Which representation to use — read this first

The CDS `.dat` files are **fixed-width** and match the ReadMe byte layout. The
Zenodo archives contain **CSV** text, which this parser does not read.

The publisher md5 values on Zenodo apply to **those zip archives**, not to the CDS
files. A Zenodo md5 can never validate a CDS download — they are different
representations. Downloading from CDS and reporting
`NO_PUBLISHER_CHECKSUM` is the **correct** outcome, not a failure.

Both routes to the same underlying data are given below so nothing is hidden.

### 2.2 Route A — CDS fixed-width `.dat` (recommended; the only format this parser reads)

URLs, sizes computed from the ReadMe (`(Lrecl + 1) × records`), and how each is
verified:

| File | URL | Expected bytes | Expected rows | Publisher checksum |
|---|---|---|---|---|
| `table2.dat` | `https://cdsarc.cds.unistra.fr/ftp/J/ApJS/249/18/table2.dat` | 178,986,858 (170.7 MiB) | 781,602 | none |
| `table4.dat` | `https://cdsarc.cds.unistra.fr/ftp/J/ApJ/932/118/table4.dat` | 46,731,776 (44.6 MiB) | 730,184 | none |
| `ztf2g.dat` | `https://cdsarc.cds.unistra.fr/ftp/J/ApJS/249/18/ztf2g.dat` | 6,817,001,868 (6.35 GiB) | 89,697,393 | none |
| `ztf2r.dat` | `https://cdsarc.cds.unistra.fr/ftp/J/ApJS/249/18/ztf2r.dat` | 6,817,001,868 (6.35 GiB) | 89,697,393 | none |

Byte counts are *computed* from the ReadMe, not measured by me: I could not reach
CDS from this environment (`curl` → HTTP 000). Treat them as an expectation to
test, not as ground truth. **Row count is the authoritative check** and is exact.

Sizes assume one `\n` per record and no trailing padding. If `wc -c` differs by a
few bytes but `wc -l` matches exactly, the row count is what matters.

Total ≈ 13.6 GiB. Budget disk accordingly.

### 2.3 Route B — Zenodo CSV archives (publisher md5 available, wrong format)

These md5 values are published by the publisher on the record page and are the
only checksums that are independent of us:

| File | URL | Size (reported) | md5 (publisher) |
|---|---|---|---|
| `Table2.txt.zip` | `https://zenodo.org/records/3886372/files/Table2.txt.zip?download=1` | 64.0 MB | `24dd4cf138a2687901d64b2d029cc624` |
| `ztf2g.zip` | `https://zenodo.org/records/3886372/files/ztf2g.zip?download=1` | 753.7 MB | `850fcef561dd7407fbe8e19e99100d7a` |
| `ztf2r.zip` | `https://zenodo.org/records/3886372/files/ztf2r.zip?download=1` | 881.5 MB | `daa7bc45c67579253eebe6b1c09dfbd9` |
| `Table6.txt.zip` | `https://zenodo.org/records/3886372/files/Table6.txt.zip?download=1` | 57.0 MB | `fcad26b036c8dbee29f6d868fecc9697` |

If you use Route B you get checksum-verified bytes but a **CSV** format that the
current parser rejects. That is the named fallback in §7 — it costs a converter,
not a weakening of the criterion.

---

## 3. Ubuntu / WSL — copy-paste

```bash
set -euo pipefail

# --- 0. code -----------------------------------------------------------------
git clone https://github.com/saeed92m/ztf-classifier.git
cd ztf-classifier
git checkout 4d3d902088ae2ce0dfe5e526f44feb2840e1f151
git rev-parse HEAD
python3 --version          # need >= 3.10
nproc                      # 2+ cores is fine; run time scales ~linearly

# --- 1. download -------------------------------------------------------------
mkdir -p data/raw/cpvs && cd data/raw/cpvs

fetch() {   # check status BEFORE pulling gigabytes
  local url="$1" out="$2"
  code=$(curl -sSL -o /dev/null -w '%{http_code}' --range 0-0 "$url" || echo 000)
  echo "$url -> HTTP $code"
  [ "$code" = "200" ] || [ "$code" = "206" ] || { echo "STOP: $out not reachable"; return 1; }
  curl -L --fail --retry 3 -C - -o "$out" "$url"
}

fetch https://cdsarc.cds.unistra.fr/ftp/J/ApJS/249/18/table2.dat table2.dat
fetch https://cdsarc.cds.unistra.fr/ftp/J/ApJ/932/118/table4.dat   table4.dat
fetch https://cdsarc.cds.unistra.fr/ftp/J/ApJS/249/18/ztf2g.dat    ztf2g.dat
fetch https://cdsarc.cds.unistra.fr/ftp/J/ApJS/249/18/ztf2r.dat    ztf2r.dat
```

`-C -` resumes, so an interrupted multi-gigabyte download continues rather than
restarting.

### 3.1 Verify before analysing anything

```bash
# row counts are the authoritative check
wc -l table2.dat table4.dat ztf2g.dat ztf2r.dat
# expect:  781602   730184   89697393   89697393

# structural sanity: first record must be 75 / 228 / 63 bytes
for f in ztf2g.dat ztf2r.dat; do echo "$f: $(head -1 "$f" | wc -c) (expect 76)"; done
echo "table2.dat: $(head -1 table2.dat | wc -c) (expect 229)"
echo "table4.dat: $(head -1 table4.dat | wc -c) (expect 64)"

# documented ranges must hold; a violation means wrong or corrupt bytes.
# NOTE: every accumulator is initialised in BEGIN. An uninitialised awk variable
# prints as an empty string, which reads like "no data" rather than "zero".
awk 'BEGIN{max=-1} {v=substr($0,72,4)+0; if(v>max)max=v}
     END{printf "Flag max: %d (ReadMe max 4628) %s\n", max, (max>4628?"VIOLATION":"ok")}' ztf2g.dat
awk 'BEGIN{max=-1; min=1e9} {v=substr($0,1,6)+0; if(v>max)max=v; if(v<min)min=v}
     END{printf "Seq range: %d - %d (expect within 1..781604) %s\n", min, max, (min<1||max>781604?"VIOLATION":"ok")}' ztf2g.dat
awk 'BEGIN{max=-1} {v=substr($0,90,6)+0; if(v==0)z++; if(v>max)max=v}
     END{printf "table2 gmag: nulls=%d max=%d (ReadMe max 22) %s\n", z+0, max, (max>22?"VIOLATION":"ok")}' table2.dat
awk 'BEGIN{max=-1} {v=substr($0,24,6)+0; if(v>max)max=v}
     END{printf "table4 ID max: %d (expect <=781604) %s\n", max, (max>781604?"VIOLATION":"ok")}' table4.dat

# record your own provenance; the publisher supplies none for these files
sha256sum table2.dat table4.dat ztf2g.dat ztf2r.dat | tee SHA256SUMS.txt
```

The `awk` checks read the same byte offsets the parser uses, so a mismatch there
predicts a parser mismatch.

### 3.2 Run

```bash
cd /path/to/ztf-classifier      # repo root
python3 scripts/reconstruct_cpvs_from_photometry.py \
  --table2 data/raw/cpvs/table2.dat \
  --table4 data/raw/cpvs/table4.dat \
  --ztf2g  data/raw/cpvs/ztf2g.dat \
  --ztf2r  data/raw/cpvs/ztf2r.dat \
  --output-dir out/cpvs-documented-rule \
  --manifest configs/cpvs/cpvs_input_acquisition.json \
  2> run.stderr.log | tee run.stdout.log
echo "exit=$?"
```

`--manifest` will print one `NO_PUBLISHER_CHECKSUM` per input for Route A. That is
expected and correct.

Run time: measured throughput is 2.1–2.5 M rows/s per band per rule on 2 cores, so
two bands × 89.7 M rows × 3 rules ≈ **4–8 minutes**, plus ~2 s to read
`table2.dat` (measured: 1.7 s, 412 MB RSS). Peak memory is under 1 GB.

### 3.3 Exit-code handling

```bash
python3 scripts/reconstruct_cpvs_from_photometry.py ... ; rc=$?
case $rc in
  0) echo "report written - now read it; it is NOT a pass" ;;
  1) echo "refused or aborted - the message on stderr names the input and why" ;;
  *) echo "unexpected exit $rc" ;;
esac
```

A `1` with text like "fixed-width offsets do not match this file" means the byte
layout is wrong: do not adjust the offsets, check the file. A `1` naming a
published name absent from `table2.dat` means the two catalogues are different
versions — that is a finding, not a glitch.

---

## 4. Windows

Two supported routes. **WSL2 is strongly preferred** — the files are 6.35 GiB each
and native Windows tooling is slower and more error-prone here.

### 4.1 WSL2 (recommended)

```powershell
wsl --install -d Ubuntu
```

Then inside Ubuntu, follow §3 verbatim. Store the data inside the Linux
filesystem (`~/cpvs`), not under `/mnt/c`, or throughput collapses.

### 4.2 Native Windows (PowerShell 7)

```powershell
git clone https://github.com/saeed92m/ztf-classifier.git
Set-Location ztf-classifier
git checkout 4d3d902088ae2ce0dfe5e526f44feb2840e1f151
git rev-parse HEAD

New-Item -ItemType Directory -Force -Path data\raw\cpvs | Out-Null
Set-Location data\raw\cpvs

$urls = @{
  'table2.dat' = 'https://cdsarc.cds.unistra.fr/ftp/J/ApJS/249/18/table2.dat'
  'table4.dat' = 'https://cdsarc.cds.unistra.fr/ftp/J/ApJ/932/118/table4.dat'
  'ztf2g.dat'  = 'https://cdsarc.cds.unistra.fr/ftp/J/ApJS/249/18/ztf2g.dat'
  'ztf2r.dat'  = 'https://cdsarc.cds.unistra.fr/ftp/J/ApJS/249/18/ztf2r.dat'
}
foreach ($f in $urls.Keys) {
  Write-Host "downloading $f"
  curl.exe -L --fail --retry 3 -C - -o $f $urls[$f]
  if ($LASTEXITCODE -ne 0) { throw "download failed: $f" }
}

# row counts: Get-Content is unusable at 90M lines, so use a fast line counter
foreach ($f in @('table2.dat','table4.dat','ztf2g.dat','ztf2r.dat')) {
  $n = (cmd /c "find /c /v """" $f") -split '\s+' | Select-Object -Last 1
  Write-Host "$f rows = $n"
}

# provenance
Get-FileHash table2.dat, table4.dat, ztf2g.dat, ztf2r.dat -Algorithm SHA256 |
  Format-Table -AutoSize | Out-File SHA256SUMS.txt
```

Expected rows: `table2.dat` 781,602 · `table4.dat` 730,184 ·
`ztf2g.dat` 89,697,393 · `ztf2r.dat` 89,697,393.

Run:

```powershell
Set-Location ..\..\..
python scripts\reconstruct_cpvs_from_photometry.py `
  --table2 data\raw\cpvs\table2.dat `
  --table4 data\raw\cpvs\table4.dat `
  --ztf2g  data\raw\cpvs\ztf2g.dat `
  --ztf2r  data\raw\cpvs\ztf2r.dat `
  --output-dir out\cpvs-documented-rule `
  --manifest configs\cpvs\cpvs_input_acquisition.json
Write-Host "exit=$LASTEXITCODE"
```

`find /c /v ""` omits a final line lacking a newline; if the expectation is off by
one, check `wc -l` under WSL before suspecting the file.

---

## 5. Output contract and traceability

The report is a single JSON file at
`<output-dir>/cpvs_documented_rule_report.json`.

### 5.1 Fields

| Path | Meaning |
|---|---|
| `status` | always `"UNRESOLVED"` — hardcoded, cannot be flipped by a match |
| `validated_on_real_data` | `false` — set by the author of the code, not by the run |
| `note` | states that a count match is not treated as resolution |
| `inputs.<name>.path` / `.bytes` / `.sha256` / `.md5` | per-input provenance |
| `table2_rows`, `table4_rows` | parsed row counts |
| `comparison.reference_size` | published membership size after the name join |
| `comparison.published_id_vs_name_join` | `"AGREE"` or `"DISAGREE"` |
| `comparison.reference_only_ids` | published objects the name join failed to find |
| `comparison.detection_runs[]` | one entry per rule: `label`, `rule`, `g_band_objects`, `r_band_objects`, `both_bands_objects`, `g_band_rows`, `r_band_rows` |
| `comparison.detection_runs[].g_band_rows.{rows,unparsed,nonpositive_error,blank}` | parse accounting per band |
| `comparison.routes.<label>.size` | objects the route selects |
| `comparison.routes.<label>.intersection` | agreement with the published set |
| `comparison.routes.<label>.produced_only` / `.reference_only` | counts on each side |
| `comparison.routes.<label>.produced_only_ids` | **complete** sorted ID list, never truncated |
| `comparison.routes.<label>.reference_only_ids` | **complete** sorted ID list, never truncated |
| `comparison.routes.<label>.produced_only_objects[]` | 200-row convenience sample: `seq`, `name`, `gmag`, `rmag`, `per_g`, `per_r` |
| `comparison.routes.<label>.produced_only_sample_truncated` | rows beyond the sample |
| `comparison.routes.<label>.exact_set_equality` | the only field that decides equality |

Route labels are `documented_rule[<snr_method>,<flag_policy>]`, plus
`null_exclusion`. The three rule routes actually produced are:

`documented_rule[inverse_error,none]`
`documented_rule[inverse_error,any_nonzero]`
`documented_rule[magnitude_over_error,none]`

**All four routes are always reported.** No route is ranked, selected, or
discarded on the basis of matching 730,184. A route reproducing the published
count is shown next to one that does not, with the same status.

### 5.2 Verify the IDs trace to original records

`seq` is `table2.Seq` and `produced_only_ids` are these same integers.

```bash
R=out/cpvs-documented-rule/cpvs_documented_rule_report.json

# 1. every produced-only ID must exist in table2.dat at bytes 24-29
python3 -c "
import json;d=json.load(open('$R'))
k='documented_rule[inverse_error,none]'
print('\n'.join(map(str,d['comparison']['routes'][k]['produced_only_ids'])))" > produced_only.txt
awk 'NR==FNR{want[$1]=1; next} {s=substr($0,24,6)+0; if(s in want) found[s]=1}
     END{for(s in want) if(!(s in found)) print "MISSING from table2.dat:", s}' \
    produced_only.txt table2.dat | head
# prints nothing = every ID resolves to a real parent record

# 2. every published-only ID must exist in table4.dat at bytes 24-29
python3 -c "
import json;d=json.load(open('$R'))
print('\n'.join(map(str,d['comparison']['routes']['null_exclusion']['reference_only_ids'])))" > reference_only.txt
awk 'NR==FNR{want[$1]=1; next} {s=substr($0,24,6)+0; if(s in want) found[s]=1}
     END{for(s in want) if(!(s in found)) print "MISSING from table4.dat:", s}' \
    reference_only.txt table4.dat | head

# 3. counts must agree with the reported numbers
wc -l produced_only.txt
python3 -c "
import json;d=json.load(open('$R'))
k='documented_rule[inverse_error,none]'
r=d['comparison']['routes'][k]
assert len(r['produced_only_ids'])==r['produced_only'], 'ID list and count disagree'
print('traceability counts consistent:', r['produced_only'])"

# 4. the ID route must agree with the name route
python3 -c "
import json;d=json.load(open('$R'))
print('id vs name join:', d['comparison']['published_id_vs_name_join'])"
```

Every discrepant object therefore has three independent handles: its `Seq`, its
ZTF name, and (for published objects) its `table4.ID`.

---

## 6. What the run will and will not settle

**Will settle, per route:** whether that exact rule, on these exact bytes,
reproduces the 730,184-member published set as a *set*, and if not, precisely
which objects differ — exhaustively, not by sample.

**Will not settle on its own:**

- Which route is correct. If the `inverse_error` route matches and
  `magnitude_over_error` does not, that is consistent with the physical reading
  and is still not a statement of what the authors did.
- The cause of the 11,602. A route reproducing the published set makes the
  documented criterion a *sufficient* reconstruction; it does not prove the
  historical pipeline used it.
- Anything about `INFOBITS`, which is unavailable here.

Interpreting the outcome:

| Observation | Reading |
|---|---|
| a documented route reproduces 730,184 as a set, and `produced_only`/`reference_only` are both 0 | the documented criterion is reconstructible from primary data — strongest available evidence, still not "the authors did X" |
| every documented route differs from 730,184 | the published set involved a further undocumented step; the question narrows and stays open |
| `null_exclusion` matches while documented rules do not | the four-field predicate is an empirical proxy, not the published rule |
| `published_id_vs_name_join` is `DISAGREE` | the join is broken — stop, this is a defect to fix before interpreting anything |
| `unparsed` is large in any band | the layout does not match the file — do not interpret |

---

## 7. If a source is inaccessible

Name the exact missing file. Each has a distinct fallback that does **not**
weaken validation:

| Missing | Consequence | Fallback |
|---|---|---|
| `table4.dat` | no reference membership, nothing to compare | Zenodo `Table6.txt.zip` is **not** a substitute (Table 6 ≠ Table 4). Blocked until CDS reachable. |
| `ztf2g.dat` or `ztf2r.dat` | documented criterion not computable at all | none — no substitute exists |
| `table2.dat` | no name↔Seq crosswalk | Zenodo `Table2.txt.zip` md5 `24dd4cf1…` — but CSV, needs a converter |
| CDS unreachable, Zenodo reachable | CSV not fixed-width | download the md5-verified zip, then write a converter that emits the exact fixed-width layout; verify by row count and by reproducing the ReadMe ranges. This adds a transformation step that must be tested, so it is the **named cost**, not a shortcut. |

Do not substitute a different catalogue version, and do not concatenate sources
from different retrieval dates into one run.

---

## 8. What not to do

- Do not tune `--manifest`, thresholds, or offsets to make a count match.
- Do not edit `730184` anywhere, or treat it as a target to hit.
- Do not conclude "solved" from `exact_set_equality: true`. It is evidence.
- Do not delete rows to reconcile. `741,786 − 730,184 ≠ 39,816`; the paths differ
  in kind, and only object identity separates them.
- Do not report a route as the published rule because it happened to match.

---

## 9. Full provenance of this runbook

| Claim | How verified |
|---|---|
| Commit and file digests | `git rev-parse`, `sha256sum` on the committed blobs |
| Byte layout, ranges, row counts, Lrecl | CDS ReadMe `J/ApJS/249/18` and `J/ApJ/932/118`, fetched 2026-10-25 |
| Publisher md5s | Zenodo record 3886372 file listing |
| "730,184 of 781,602 at 2.5σ/3σ" | Chan+ 2022 §II.1, arXiv `2112.03306v1`, verbatim |
| `catflags != 32768` | Chen+ 2020 §III, arXiv `2005.08662v2`, verbatim |
| Throughput, memory | measured in this environment on 2 M and 781,602-row fixtures |
| Stdlib-only | AST scan of the committed script |

**Not verified, and stated as such:** the CDS byte sizes are computed, not
measured — CDS was unreachable from this environment (`curl` HTTP 000, while
`api.github.com` returned 200 and `fetch_page` could read the ReadMes as text).
No file in this runbook was downloaded or parsed here. `validated_on_real_data`
remains `false` until you run it.
