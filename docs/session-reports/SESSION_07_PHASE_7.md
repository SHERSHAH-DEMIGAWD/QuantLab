# Session 07 - Phase 7

Date: 2026-11-02 (Asia/Calcutta).

## A. Session overview

**Objective:** retain local research and expose the verified core through REST.
**Status: COMPLETE.** Session 07 explicitly authorized SQLite/FastAPI/Pydantic,
original-input retention and actual reproduction. Read the charter, roadmap,
status, decisions, data contract, Session 05/06 reports and actual core models;
verified the 378-test baseline before changes. No Phase 8 work was started.
Development and verification are AI-assisted; independent ownership remains
learning work to do.

## B. What was implemented

Paths are relative to repository root.

| Source files | Actual responsibility |
| --- | --- |
| `backend/src/quantlab/persistence/store.py` | `Store.initialize`, `transaction`, dataset retention/reconstruction, completed experiment insertion/retrieval, pagination and typed errors |
| `backend/src/quantlab/persistence/codec.py`, `__init__.py` | `to_wire`, strict JSON, SHA-256, economic projection and bounded difference paths; public store interface |
| `backend/src/quantlab/application/requests.py` | Strict Pydantic HTTP/saved-request models, built-in strategy mapping and effective arguments/defaults |
| `backend/src/quantlab/application/service.py`, `__init__.py` | Import, `execute`, `reproduce`, existing-runner delegation and recorded implementation identity |
| `backend/src/quantlab/api/app.py` | `create_app`, eight API operations, generated OpenAPI and structured error handlers |
| `backend/src/quantlab/api/boundary.py`, `models.py` | Bounded body/Host/Origin/JSON checks and response schemas |
| `backend/src/quantlab/api/__main__.py`, `__init__.py` | Loopback-only CLI and side-effect-free API import |
| `backend/src/quantlab/data/loader.py`, `metadata.py`, `__init__.py` | Shared byte importer and metadata parser, retaining existing file-import rules |
| `backend/tests/test_api.py` | Temporary SQLite/TestClient integration with real core computation, accounting, failures, restart and reproduction |
| `pyproject.toml` | Exact direct backend/test dependencies |

Added [API contract](../API_CONTRACT.md), D10 and this report; updated README,
status, roadmap and importer/experiment cross-references. No execution,
strategy, analytics, auditor or Phase 6 runner implementation changed. Existing
tests/fixtures remain unchanged. No frontend/provider/queue/auth service.

## C. Why this functionality exists

Transient returns cannot support investigation or a dashboard after restart.
The backend retains original inputs, full research histories and effective
configuration. HTTP coordinates those operations without owning financial
rules. Reproduction is a new computation, with explicit evidence and limits.

## D. Integration with the existing codebase

UTF-8 CSV text + metadata -> same Phase 1 byte/file validation -> original CSV
BLOB/effective metadata in SQLite. For execution: reimport retained bytes ->
verify identity/range/count -> Pydantic request boundary -> existing Phase 6
runner -> existing simulation/analytics/audit -> exact JSON -> transactional save.

`backtest` uses one configuration; `grid` covers parameter/cost/subperiod
comparisons; `train_test` uses the existing frozen-selection workflow. All
financial traces, metrics, open holdings, comparisons and audit findings remain.
Core functions import no HTTP, application or persistence modules. Database
and server state are created by `create_app`, not by module import.

## E. Technical concepts to study

- Primary/foreign keys, immutable identities, uniqueness and idempotent imports.
- Explicit BEGIN/COMMIT/ROLLBACK, schema versions and connection lifetime.
- Transport validation versus domain validation; discriminated strategy unions.
- Decimal/date/enum JSON encoding, null metrics, canonical checksums and BLOBs.
- Re-execution versus cached retrieval; projected equality versus source identity.
- HTTP status/error envelopes, request-body bounds and parameterized SQL.

Independently recreate **`Store.transaction`** and **`reproduce`** after studying
their tests. Also explain `reconstruct_dataset`, `to_wire`, `ExperimentRequest`
and `create_app`. Copying this AI-assisted implementation is not recreation.

## F. Financial and quantitative concepts to study

Decimal money stays exact through string JSON encoding. Dates retain session
labels; UTC creation timestamps are operational, not trading dates. Undefined
win rates/Sharpe remain null with reasons; storing zero would change their meaning.
Equity history and open positions must remain available, not just a final return.

The API cost reference preserves $1,000 capital, $2 commission and 100 bps
slippage: 9 shares at $101, $89 cash and $1,079 final equity. The train/test
reference still selects momentum lookback 2 after +81% training, then loses
54% on fresh test capital. Training history warms indicators, not test wealth.

Retaining bytes makes input reconstruction possible; it does not prove coverage,
corporate-action truth, opening liquidity or future profitability. Reproduced
price-only results still exclude dividends/actions and retain audit unknowns.

## G. Engineering decisions and tradeoffs

- Two tables: `datasets` (CSV BLOB, effective metadata, fingerprints, range/count,
  validation report, import UTC); `experiments` (UUID, dataset FK, mode, complete
  effective request/result JSON and checksums, implementation evidence, UTC).
- Schema 1 uses transactional SQL and `PRAGMA user_version`; repeated setup is
  safe, unsupported/unversioned nonempty/malformed schemas fail. Every connection
  enables FKs and checks version. No ORM or migration framework.
- Finish computation/serialization before the experiment write transaction.
  Failed runs produce no completed row. Duplicate dataset imports preserve the
  original timestamp and check retained bytes/metadata rather than overwrite.
- JSON imports avoid a multipart dependency and arbitrary server paths. Preserve
  accepted UTF-8 bytes/BOM/CRLF; cap CSV 10 MiB, metadata/config 64 KiB and import
  body 12 MiB. Reject duplicate/nonfinite JSON and unknown fields. Decimal text
  is plain notation, at most 128 characters, bounding exponent expansion.
- Request version is an integer 1 explicitly; Pydantic Literal equality alone
  also accepted bool/float, so a boundary validator rejects those types.
- Reproduction revalidates inputs and saved configuration, reruns, compares exact
  economic payloads and separately compares recorded implementation identity.
  It accepts no replacement body and writes no new experiment. Operational IDs/
  timestamps and explicitly documented technical/evidence fields are excluded
  from economic equality; audit/assumption fields remain saved and visible.
- Source manifest, versions and direct dependency identifiers are evidence, not
  executable archives or complete transitive-environment capture. Changed code
  is reported even if economic values match. Checksums are not authentication.
- Local loopback CLI/Host validation, no unrestricted CORS, no public deployment
  claim, authentication system, arbitrary strategy code or background execution.

## H. Testing and verification

Actual repository-root PowerShell commands (pytest/setup approved outside the
known Windows temporary-directory sandbox restriction):

```powershell
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-phase7-baseline
& '.\.venv\Scripts\python.exe' -m pytest -q backend/tests/test_api.py --basetemp=.venv/pytest-phase7-api
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-phase7-full
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-phase7-final
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-phase7-verified
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-phase7-release
& '.\.venv\Scripts\python.exe' -m pytest -q backend/tests/test_api.py --durations=5 --basetemp=.venv/pytest-phase7-stability
& '.\.venv\Scripts\python.exe' -m pip install -e '.[test]'
& '.\.venv\Scripts\python.exe' -m pip check
& '.\.venv\Scripts\python.exe' -m quantlab.api --help
```

| Executed run | Result |
| --- | --- |
| Baseline | 378 passed in 8.93s |
| Initial API suite | 42 passed in 6.73s |
| First combined suite | 423 passed in 17.22s |
| Schema/retention extensions | 425 passed in 16.24s |
| Reproduction body guard | 426 passed in 16.72s |
| Final integer-version regression | 428 passed in 596.98s (0:09:56) |
| Focused timing/reliability repeat | 50 passed in 9.43s |

All executed pytest runs above passed; no prior test was removed or changed.
The final suite includes all 378 Phase 1-6 cases plus 50 API/persistence cases.
The final full-run delay was not reproduced in the focused repeat: its slowest
case was 1.07s, followed by the real bar-budget case at 0.73s. The delay's cause
remains undiagnosed; no throughput conclusion is drawn. Meaningful evidence:

- Fresh/repeated schema, FK enforcement, unknown/malformed/live changed versions,
  atomic failed schema creation, and INSERT-trigger failures prove rollback.
- Real CSV import/reconstruction, exact BOM/CRLF retention, stable IDs, effective
  metadata, duplicate timestamps, changed-source identity and conflict protection.
- Invalid CSV/OHLC/metadata/version diagnostics return 422 without partial rows;
  ineligible splits and unacknowledged real-data coverage still block execution.
- Real buy-and-hold/SMA/momentum plus costs/grids/subperiods/train-test through
  HTTP; independent $1,079 accounting and -54% test-loss expectations, exact
  Decimal/date encoding, equity/fill/trade history and null-with-reason metrics.
- Saved audit warnings/NOT_ASSESSED retained, no audit FAIL for references;
  restart retrieves the full unchanged record, filtering/pagination work.
- A spy wraps actual computation during reproduction, proving rerun rather than
  cached return. Matching economics/implementation, altered economics, simulated
  old implementation labels, missing/corrupt inputs/checksums/request/payload
  versions and prohibited replacement bodies yield the intended distinct results.
- Bool/float versions, invalid strategies/bool windows/dates/costs/cash and
  exponent-form thresholds fail. A real 10,001-bar/100-config request exceeds
  1,000,000; an execution guard proves rejection before simulation. Added
  benchmark/101-config caps also reject without a saved result.
- Oversize CSV/metadata, streamed body without length, duplicate keys, NaN/
  overflowing JSON numbers, bad media/compression/Host/Origin, unknown IDs,
  pagination bounds and sanitized unexpected failures are covered. No wildcard
  CORS or server-path input is exposed. OpenAPI documents all six route paths.

Initial HTTP smoke exposed an experiment INSERT placeholder mismatch (ten
placeholders for nine columns); fixed it before integration testing. A
`--no-build-isolation` editable refresh failed because setuptools is not installed
inside this venv; ordinary isolated `pip install -e '.[test]'` then succeeded.
No interpreter/machine setting was changed. Starlette's deprecated HTTPX fallback
was replaced with its supported HTTPX2 client; exploratory HTTPX/httpcore/certifi
packages were removed. Final `pip check`: **No broken requirements found.**

Verified CPython 3.15.0, SQLite 3.53.4, FastAPI 0.162.0, Pydantic 2.14.2,
Starlette 1.10.0, Uvicorn 0.54.0, HTTPX2 2.16.0 and pytest 9.2.0. Python 3.12
remains untested. Direct versions are pinned; build dependencies use isolation.

Actual loopback HTTP/CLI smoke **PASS**: launched `python -m quantlab.api` on
127.0.0.1 with ignored `.venv/phase7-network.sqlite3`, imported the synthetic
three-bar rising reference, saved $1,079 results, obtained OpenAPI, stopped the
process, restarted it, retrieved the exact saved record and reproduced it with
matching economics/recorded implementation. Both server processes were stopped;
no public service or real-market dataset was used. Installed-package/TestClient
smoke likewise returned 201 import/execute and 200 matched reproduction.

Final inline document/source verification **PASS**: 77 project files, 48 Python
AST syntax checks and 68 local links/anchors. All 29 financial-core modules
remain free of HTTP/application/persistence/SQLite imports. UTF-8/LF/final
newlines/trailing whitespace and Git whitespace including untracked files
passed, using command-local `core.autocrlf=false` and `core.eol=lf`. A-L/questions,
exact declared dependencies, all 11 phase statuses and empty frontend/raw/
processed placeholders passed. No source changed after the final 428-test run;
later edits completed documentation only.

## I. Complexity and performance

For payload size P, JSON conversion/hash/storage/retrieval is O(P) time/space;
complete bar-budget traces can still be large. Dataset reconstruction parses
retained bytes and sorts observations using Phase 1's established complexity.
Research remains Phase 6's O(R*N + A + S); the bar cap is not a wall-time bound.

Primary-key lookups are indexed plus payload work. Experiment indexes support
creation ordering and dataset/creation filtering; pages traverse O(log E+offset+L)
rows. Dataset lists sort D small summaries, O(D log D), without decoding BLOBs/
result histories. One connection per operation, serialized SQLite writes and
a 5-second timeout keep failure handling explicit. No cache, queue, concurrency
framework or measured throughput improvement was introduced. Test durations
measure verification only; no performance benchmark ran.

## J. Interview preparation

Five technical questions:

1. Why store original CSV BLOBs alongside effective metadata and fingerprints
   instead of trusting serialized Bar records or a source filename?
2. How do schema initialization and INSERT transactions avoid partial records,
   and why enable foreign keys on every SQLite connection?
3. Why encode Decimal as strings and undefined metrics as null plus a reason?
4. How does real reproduction differ from retrieving a saved result, and why
   compare economic outputs separately from implementation evidence?
5. Which indexes serve actual list/filter routes, and how do payload size and
   offset pagination affect their remaining costs?

Three financial/quantitative questions:

1. Why can exact reproduced results still contain corporate-action, coverage,
   survivorship or opening-liquidity uncertainty?
2. Why must open holdings, costs and excluded dividends remain visible when
   inspecting a stored return or comparing subperiods?
3. Why must a saved train/test request reproduce its training-only selection
   instead of optimizing parameters after seeing test results?

Independent exercise: in a separate practice file, create two small SQLite
tables with a foreign key and a context-managed transaction. Inject a failure
after the first INSERT and prove that neither row remains. Then serialize a
Decimal/date/null metric without precision loss and explain the boundary.
Write it before consulting production code; do not claim this AI-assisted
implementation as independent work.

## K. Current project status

Phases 0-7 COMPLETE; 8-10 NOT STARTED and unauthorized. All prior financial
contracts remain. No known in-scope functional failure remains in executed
checks. Backend is local/single-user with no authentication, encryption,
backup workflow, public deployment or frontend. Original market bytes are
retained; executable archives/full environment restoration are not. Matching
recorded identities/checksums do not establish authenticity or all bias absence.
Synchronous large results and full-Dataset validation remain bounded only as
documented; no performance claim exists. Python 3.12 remains untested. Work is
unstaged/uncommitted; no branch/remote change. Owner recreation is pending.

## L. Next session

Proposed Session 08 / Phase 8 **only after explicit authorization**: a research
dashboard consuming the verified local API. Review dataset/import/research/
retrieval/reproduction flows, Decimal/date/null formatting, complete equity/
trade displays, visible audit limits, unequal-window labels and honest mismatch/
implementation-change states. Select only necessary React/TypeScript/chart
dependencies then. Acceptance: an end-to-end UI workflow matching retained API
results and covering loading/empty/error states without changing core finance.
No Phase 8 code or dependency was added. Stop after Phase 7.
