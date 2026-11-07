# Session 01 - Phase 1

Date: 2026-11-01 (Asia/Calcutta).

## A. Session overview

- **Session/phase:** 01 / 1, historical data foundation.
- **Objective:** local OHLCV/metadata ingestion, validation, and input identity.
- **Authorization:** user's Session 01 instruction, including the metadata and
  size-limit amendments. Read the five required Phase 0 documents before
  changes; amended D03/roadmap before code.
- **Status:** COMPLETE; 162 pytest cases passed, editable installation and
  dependency check succeeded, and the synthetic smoke import worked.
- **Ownership:** AI-assisted implementation and verification. Independent
  learning/recreation by the owner remains to be done and has not been assessed.

## B. What was implemented

Paths are relative to the repository root.

| Created file | Responsibility and key names |
| --- | --- |
| `pyproject.toml` | Minimal setuptools package, Python >=3.12, pytest 9.2.0 test extra/configuration; no runtime dependencies |
| `backend/src/quantlab/__init__.py` | Independent core package |
| `backend/src/quantlab/data/__init__.py` | Public API, record types, expected error, limits |
| `backend/src/quantlab/data/models.py` | Frozen `Bar`, `Metadata`, `Dataset`, `ImportReport`, `Normalization`, `CalendarGap` |
| `backend/src/quantlab/data/errors.py` | `ValidationIssue`, `DataValidationError`, bounded `Diagnostics` |
| `backend/src/quantlab/data/metadata.py` | `load_metadata`: JSON, type/enum/version validation, effective defaults |
| `backend/src/quantlab/data/identity.py` | `canonical_json`, `fingerprints`: exact-byte/effective-metadata SHA-256 |
| `backend/src/quantlab/data/loader.py` | `load_dataset`, `_parse_csv`, `_parse_bar`, `validate_ohlc`; atomic loading, ordering, gap/limitation reports |
| `backend/tests/test_data.py` | 162 parametrized offline cases, handwritten OHLC and canonical-identity references |
| `backend/tests/fixtures/synthetic_daily.csv` and `.metadata.json` | Three invented observations and explicit synthetic provenance |

Modified `.gitattributes` (TOML LF policy), `README.md`, `docs/DECISIONS.md`,
`docs/ROADMAP.md`, and `docs/PROJECT_STATUS.md`. Created
[DATA_CONTRACT.md](../DATA_CONTRACT.md) and
this report. Removed the two `.gitkeep` files in populated source/fixture
directories; retained three empty frontend/data placeholders. `.venv` and
generated caches/package metadata are ignored local artifacts. No prior
business source existed to modify.

## C. Why this functionality exists

Later execution needs validated observations rather than silently repaired
rows. One bad row rejects the entire import; a duplicate cannot create an
extra simulated session. Separate source and metadata hashes identify the
exact input and interpretation, while warnings distinguish source declarations
from verification. No market-data truth is established by passing these checks.

## D. Integration with the existing codebase

Before: documentation/placeholders. After: a Python library with flow
`local CSV + JSON -> validate -> sort -> fingerprint -> Dataset + ImportReport`.
The core has no HTTP, persistence, presentation, or provider dependency.

Phase 2 can consume ordered Decimal bars, physical source rows, effective
metadata, identity, and warnings. It must separately approve D04-D05 and check
execution eligibility/numeric ranges. No eligibility flag, trading state,
strategy return, or future-phase scaffolding was added.

## E. Technical concepts to study

| Topic | Actual code/evidence to explain |
| --- | --- |
| CSV parsing/validation | `_parse_csv` uses strict `csv.reader` for quoting, CRLF, and multiline fields; `_parse_bar` checks exact dates/numeric text before OHLC relationships |
| Data structures | Frozen dataclasses/tuples for output; a dictionary maps dates to first source row; lists accumulate records; a header `Counter` finds duplicates |
| Decimal versus float | `Decimal("100.10")` preserves source decimals; binary float cannot exactly represent many decimal fractions. Parsing never rounds or converts to float; the low-context test proves independence from arithmetic precision |
| Deterministic normalization | Trim only surrounding whitespace and sort dates; report actions. Equal normalized values may retain different exact-byte identities |
| SHA-256/canonical metadata | `fingerprints` hashes raw CSV and all effective metadata fields/defaults, using sorted compact UTF-8 JSON without paths/times. The test's handwritten canonical JSON checks this independently |
| Error handling/pytest | `exc.issues`, `error_count`, and `truncated` preserve row/field context; the cap never admits bad input. Parametrized invalid cases require no provider |

Independently recreate **`validate_ohlc`** in `loader.py` and **`fingerprints`**
in `identity.py` after studying their tests. Do not count copying or this
AI-assisted implementation as independent work. Complexity is covered in I.

## F. Financial and quantitative concepts to study

- **OHLCV:** the first invented bar opens at 100.10, reaches high 103.00 and
  low 99.50, closes at 102.25, and declares 1,000 shares of volume. The validator
  checks the bounds, not the intraday path or opening liquidity. All-equal
  prices pass; the last zero-volume bar is retained with a warning.
- **Sessions/calendar days:** January 5 -> 8 gives two intervening calendar
  days in the report, not evidence of two missing sessions. No exchange
  schedule is loaded, and source-declared coverage remains unverified.
- **Adjustment:** raw, split-adjusted, and total-return-adjusted OHLC have
  different interpretations. Unknown basis/consistency is retained with
  warnings; explicitly inconsistent OHLC fails. Numeric bounds cannot verify
  a source's adjustment label.
- **Splits:** hypothetically, a 2-for-1 split changes 10 shares at $100 into
  20 at $50 without itself halving position value. Changing prices alone does
  not update share units. No corporate-action processing is implemented.
- **Dividends:** distributions affect shareholder wealth; a price-only series
  omits that cash. Importing a total-return adjustment label does not create a
  dividend ledger or verify a total-return backtest.
- **Data quality:** duplicate observations can distort timing, missing sessions
  can change next-open execution, and mixed adjustments can invent jumps.
  These motivate rejection/warnings; no real-market or strategy result ran.

## G. Engineering decisions and tradeoffs

- D03's dated amendment preserves Phase 0 history. Nine fields are required;
  seven optional concepts each default to string `unknown`. Explicit inconsistent
  OHLC fails. Omission and explicit default have identical metadata identity;
  unknown split status never becomes `none_reported`.
- Standard-library CSV/JSON/dates/Decimal/dataclasses/hashing meet the need.
  pytest is the direct test dependency; setuptools packages the library. No
  pandas, schema framework, calendar package, or provider was necessary.
- Read at most 10 MiB + 1 CSV byte once. Bounded in-memory parsing is simpler
  than streaming here, and hashing the same snapshot avoids a second-read
  race. Original files must still be retained externally; nothing is persisted.
- Store at most 100 diagnostics while scanning recoverable records. Broken
  syntax/header/encoding prevents exhaustive later assessment. Parser safeguards
  remain unchanged; the [contract](../DATA_CONTRACT.md) documents per-field and
  integer-text limits separately from future financial arithmetic constraints.
- Only executable CPython 3.15.0 final was found. Python314 contains no
  executable; no 3.12 executable appeared in launcher/PATH/registry/common-path
  probes. Used 3.15 in `.venv` after verifying pytest/package compatibility.
  Python >=3.12 is declared, but 3.12 is untested. No interpreter installation
  or machine-wide setting change was made.

## H. Testing and verification

Actually inspected `Get-Command` for Python/launcher/uv/pip/pytest; `py -0p`;
`python --version`; `sys.executable`, `sys.version`, `sys.version_info` and module
probes; common install paths/registry; and `python -m pip --version`. Observed
CPython 3.15.0 final, MSC v.1951 AMD64, pip 26.2.1; pytest/uv initially absent.

Actual environment setup, repository-root PowerShell (the original
owner-specific interpreter path is represented portably for publication):

```powershell
py -3.15 -m venv .venv
& '.\.venv\Scripts\python.exe' -m pip install --disable-pip-version-check --cache-dir '.venv\pip-cache' pytest
& '.\.venv\Scripts\python.exe' -m pip install --disable-pip-version-check --cache-dir '.venv\pip-cache' -e '.[test]'
```

Sandbox venv/ensurepip failed with `PermissionError` accessing freshly created
private temporary directories; redirecting process-local TEMP/TMP under
`.venv/tmp` did not fix it. Approved execution outside the sandbox succeeded.
Initial sandbox pytest was interrupted after repeated fixture setup errors;
`-x --basetemp=.venv/pytest-inspect` confirmed permission failure on its own
temporary directory and cleanup. These are environment failures, not passing
tests. No application permission workaround was added.

Actual verified commands, approved execution outside that sandbox:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-verified
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-final
& '.\.venv\Scripts\python.exe' -m pip check
& '.\.venv\Scripts\python.exe' -m pip list --format=freeze
```

First full suite: **159 passed in 5.19s**. After strengthening the exact-size
test and adding field-limit/multiline/row-order cases: **162 passed in 3.62s**,
exit 0. `pip check`: **No broken requirements found.** Editable installation:
**quantlab 0.1.0 succeeded**. Test packages: pytest 9.2.0, colorama 0.4.6,
iniconfig 2.3.1, packaging 26.3, pluggy 1.7.0, Pygments 2.21.0; pip 26.2.1.
Build dependencies were isolated.

| Acceptance | Executed tests in `backend/tests/test_data.py` |
| --- | --- |
| Valid import/normalization | Handwritten prices/dates; frozen bars; unordered rows/source lines; whitespace/BOM; single-row and zero-volume warnings |
| Invalid CSV/data | Exact/duplicate headers; duplicate dates; invalid calendar dates; every OHLC field missing/malformed/nonfinite; bad relationships; invalid volume; widths, blank records, quoting, encoding |
| Metadata/adjustments | Every required field missing; schema/type/enum/key/JSON errors; duplicate keys; unknown/adjusted basis retained; inconsistent declaration rejected; optional defaults equivalent |
| Identity | Handwritten canonical reference; repeatability; changed price/line-ending/BOM/row-order bytes and metadata; invariant sidecar formatting/defaults/file paths |
| Gaps/coverage | Exact January 5 -> 8 gap; no invented rows; consecutive/single dates; declared coverage never becomes verified |
| Limits/atomic failure | Valid exactly-10-MiB CSV; one extra byte rejected; bounded read spy; field limit; 105 issues retain 100; no partial dataset |

An inline smoke import using the installed package also succeeded inside the
sandbox: three rows, 2024-01-05 through 2024-01-09, 160 source bytes, one
zero-volume row, coverage `unverified`, and the two-day calendar gap. Actual
fixture fingerprints (LF source bytes):

```text
source_sha256   7d8a9fc87a2e586612575b9deee35991f71c77ea9c7cf2b53342bdca7507546f
metadata_sha256 ee8f1aa78ea5e38dd589c3850659b1e5b31a9799a94bd59f2dc4df2dff8d1d7d
dataset_id      7ee51a72545c52466a04b3c9ad462d14a5b24e20085d398183f42b54ca47b0e1
```

Final documentation/working-tree audit: **PASS**. An inline Python check
enumerated Git's tracked/nonignored untracked files and verified all 26 project
files for UTF-8, LF, final newlines and trailing whitespace; all 21 local links
and anchors; A-L order; 11 roadmap phases; five technical/three finance
questions; three empty placeholders; eight ignore/trackability cases; and
COMPLETE Phase 1/unauthorized Phase 2 consistency. It also applied
`git -c core.autocrlf=false diff --no-index --check -- /dev/null <file>` to
every project file, covering files that plain `git diff --check` cannot assess
before an initial commit.

The first audit exposed a Git line-ending warning for new TOML files; added
`*.toml text eol=lf` to `.gitattributes` and reran successfully. Two empty
`pytest-cache-files-*` directories left at the root by failed sandbox pytest
caused Git permission warnings. Approved cleanup checked each resolved target
against the workspace and removed those generated directories. No user input
or source file was deleted. `git status --short --untracked-files=all`,
`git diff --check`, `git rev-parse --verify HEAD`, and `git remote -v` confirmed
the files remain untracked, no committed HEAD exists (expected revision error),
and no remote is configured. No staging or commit was performed.

Unverified: Python 3.12, real market inputs, source truth/rights, authoritative
calendars/corporate actions, simulation, metrics, coverage percentage, and
performance benchmarks. No finance simulation or provider request ran.

## I. Complexity and performance

For B CSV bytes, M metadata text bytes, and N records with bounded field/integer
sizes: parsing/hashing O(B + M), expected date-dictionary work O(N), sorting
O(N log N), gaps/report O(N). Overall O(B + M + N log N) time and O(B + M + N)
space. Retained diagnostics use O(100) space. Metadata has no separate byte-size
limit. The importer retains bytes/text/records; it is not constant-memory.

No benchmark was performed. Pytest's 3.62s duration includes fixture setup and
is not import throughput/latency. No optimization or speed claim is supported.

## J. Interview preparation

Five technical questions:

1. Why use `csv.reader` instead of splitting on commas, and how are physical
   source rows tracked for multiline quoted fields?
2. How do staged validation and bounded diagnostics prevent partial imports?
3. Why parse source strings as Decimal rather than float, and why does parsing
   avoid dependence on the current arithmetic context?
4. Why can normalized-equivalent CSVs have different identities, while omitted
   and explicit metadata defaults have identical metadata hashes?
5. How does the handwritten canonical reference provide independent evidence,
   and what are the loader's time/space bounds?

Three finance questions:

1. What does the OHLC inequality establish and leave unknown about the session?
2. Why are two calendar days between January 5 and 8 not automatically two
   missing trading sessions?
3. How can an unhandled 2-for-1 split or omitted dividend distort a backtest
   even when every row passes numerical validation?

Independent exercise: without copying the loader, write `calendar_gaps(dates)`
for already-sorted unique `datetime.date` values. Return adjacent intervals
with at least one intervening calendar day. Write independent expected results
for empty input, one date, consecutive dates, and January 5/8/9. Do not fetch
calendars, infer missing sessions, or add bars. Compare with the fixture report
only after completing your version.

Files to explain: `loader.py` (atomic boundary), `metadata.py` (unknown/default
versus false), `models.py` (output), `identity.py` (canonical format),
`errors.py` (cap), and the independent references in `test_data.py`.

## K. Current project status

Phases 0-1 COMPLETE; 2-10 NOT STARTED and unauthorized. No known in-scope
functional failure remains in executed checks. Limitations: declarative
provenance, no calendar/corporate-action verification, no original-file
persistence, no 3.12 evidence, and Windows sandbox temporary-directory access.
No simulation/performance evidence exists. Files remain unstaged/uncommitted;
no branch/remote change was made.

## L. Next session

Proposed only: **Session 02, Phase 2 - minimal daily execution engine**, after
explicit authorization and D04-D05 review. Decide adjustment/corporate-action
eligibility, dividend exclusion, next-open budget conversion, rounding/safe
numeric ranges, zero-volume execution, reuse of sale proceeds, final pending
orders, and final open positions. D06 requires visible zero costs and rejects
nonzero costs until Phase 4.

Use Phase 2's roadmap acceptance: independent cash/share/fill references,
timing/information-boundary checks, and invariants. Phase 1 supplies ordered
observations, metadata, identity, and warnings; it does not settle those
financial decisions. The owner should first run tests, explain key files, and
complete the independent recreation/exercise above.

Stop after Phase 1. This next-session proposal is not implementation permission.
