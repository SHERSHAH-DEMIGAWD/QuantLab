# Phase 7 local backend contract

API 1.0.0, SQLite schema 1, saved request/payload version 1. Scope and approved
choices: [D10](DECISIONS.md#d10---phase-7-persistence-and-http-boundary).
The backend reuses [experiments](EXPERIMENT_CONTRACT.md), execution, analytics
and audit. No financial calculation is implemented in a route.

## Run locally

From repository-root PowerShell after selecting the existing environment:

```powershell
& '.\.venv\Scripts\python.exe' -m pip install -e '.[test]'
& '.\.venv\Scripts\python.exe' -m quantlab.api
```

The command binds **127.0.0.1:8000**, with access logging disabled. It initializes
`data/quantlab.sqlite3`; `--database PATH` and `--port NUMBER` are operator CLI
options. HTTP requests cannot choose server paths. `create_app(database_path)`
also supports isolated databases without launching a server. Importing the API
module alone creates no database. Stop the foreground server with Ctrl+C.

Open [interactive OpenAPI docs](http://127.0.0.1:8000/docs) or
[OpenAPI JSON](http://127.0.0.1:8000/openapi.json) while the server runs.
These URLs are local runtime endpoints, not hosted services.

## Operations

| Method and route | Behavior |
| --- | --- |
| `GET /api/v1/health` | API/schema versions and database availability |
| `POST /api/v1/datasets` | JSON `csv_text` and `metadata` object; validate/save; 201 new, 200 identical duplicate with original timestamp |
| `GET /api/v1/datasets` | Summary list with `limit` default 50 (1-100), `offset` default 0 (0-1,000,000) |
| `GET /api/v1/datasets/{dataset_id}` | Effective metadata and complete original validation report/warnings; no CSV duplication in the response |
| `POST /api/v1/experiments` | Synchronously execute and save one successful `backtest`, `grid`, or `train_test`; 201 complete record |
| `GET /api/v1/experiments` | Summary pagination, optional exact `dataset_id` filter |
| `GET /api/v1/experiments/{experiment_id}` | Full saved request, result, implementation identity and creation metadata |
| `POST /api/v1/experiments/{experiment_id}/reproduce` | Empty body; revalidate retained inputs and saved request, rerun and compare; saves no replacement experiment |

Dataset IDs are 64 lowercase SHA-256 hex characters. Experiment IDs are stable
32-character UUID4 hex identifiers allocated per saved experiment. Repeating
an experiment creates another record; dataset imports deduplicate by exact
original bytes plus effective metadata identity. Listing order is creation
timestamp then ID. No count query or large result payload is loaded for lists.

Example client, using only standard-library Python while the server is running:

```python
import json
from pathlib import Path
from urllib.request import Request, urlopen

base = "http://127.0.0.1:8000"
def call(method, route, value=None):
    data = None if value is None else json.dumps(value).encode("utf-8")
    headers = {} if data is None else {"Content-Type": "application/json"}
    with urlopen(Request(base + route, data=data, headers=headers, method=method)) as response:
        return json.loads(response.read())

fixtures = Path("backend/tests/fixtures")
dataset = call("POST", "/api/v1/datasets", {
    "csv_text": (fixtures / "synthetic_daily.csv").read_bytes().decode("utf-8"),
    "metadata": json.loads((fixtures / "synthetic_daily.metadata.json").read_text()),
})
saved = call("POST", "/api/v1/experiments", {
    "dataset_id": dataset["dataset_id"], "initial_capital": "1000.00",
    "configurations": [{"kind": "buy_and_hold"}],
})
print(saved["result"]["runs"][0]["performance"]["simulation"]["final_equity"])
print(call("POST", f'/api/v1/experiments/{saved["experiment_id"]}/reproduce'))
```

This fixture is invented and contains a zero-volume bar. Reading bytes and
decoding UTF-8 preserves a leading BOM and CRLF inside `csv_text`; the server
stores its exact UTF-8 encoding. Invalid UTF-8 cannot be represented by this
text interface. The byte importer also validates retained raw bytes directly.

## Experiment request

Pydantic forbids unknown fields. Monetary/rate/threshold inputs are **plain
decimal strings**, optionally negative where the domain permits, at most 128
characters. No exponent notation, numeric JSON coercion, NaN or infinity.
The plain-notation bound prevents extreme threshold-ratio expansion. Existing
financial ranges/precision are validated by the existing engine/runner.

- `mode`: `backtest` (default), `grid`, or `train_test`.
- `initial_capital`: required string; `configurations`: required 1-100 objects.
  `kind="buy_and_hold"` has no parameters; `kind="sma"` requires integer
  `fast_window`, `slow_window`; `kind="momentum"` requires integer `lookback`
  and optional threshold string (default `"0"`). Booleans are not integers.
- `settings`: commission string (default `"0.00"`), slippage-bps string
  (default `"0"`), boolean `acknowledge_unverified_coverage` (default false).
- `periods`: optional nonempty list of inclusive `start_date`/`end_date` ISO
  date objects; absent means the imported range. No diagnostic exit or arbitrary
  engine warm-up fields are exposed. `costs`: optional nonempty cost-object list.
- `backtest` permits one config and at most one period/cost. `grid` permits
  existing parameter/cost/subperiod Cartesian comparisons. Phase 6 ordering,
  first-cost baseline, benchmark matching and atomic failure policies apply.
- `train_test` requires `training_period` and `test_period`, with fixed costs
  from settings; no periods/costs lists. `warmup` defaults true, training-only.
  Other modes reject training/test fields and a changed warmup option.
- `include_benchmark` defaults true; `annual_risk_free_rate` defaults `"0"`;
  `request_version` is 1. Effective defaults are saved explicitly.

Both evaluation intervals need at least two actual observations. Existing
corporate-action/coverage eligibility applies to all runs. Requests preserve
the **100 unique configurations / 1,000,000 aggregate evaluation+warm-up bars**
caps, including references and reserved test work. No truncation or queue.

## SQLite retention and serialization

| Table | Retained fields |
| --- | --- |
| `datasets` | Dataset primary key, original CSV BLOB, canonical effective metadata JSON, source/metadata SHA-256, actual dates/count, complete validation report JSON, UTC import timestamp |
| `experiments` | UUID primary key, dataset foreign key with restricted deletion, mode, complete effective request/result JSON plus their SHA-256 checksums, implementation JSON, UTC creation timestamp |

Foreign keys are enabled on every connection. `PRAGMA user_version=1` identifies
the explicit schema. Initialization is transactional/repeatable; an unknown
version, nonempty unversioned database, malformed table shape or missing dataset
relationship fails without overwriting it. Every subsequent connection checks
the version. There is no automatic migration from an unsupported schema.

Computations finish before opening the experiment INSERT transaction. Exceptions
roll back writes; no running/failed row can masquerade as completed. Identical
dataset insertion is idempotent, with a byte/metadata conflict check; no replace
or silent overwrite. Raw inputs are reimported and identity/range/count checked
before execution/reproduction. Metadata/report summaries remain retained.

Explicit JSON rules: Decimal -> exact string, date/datetime -> ISO string,
enum -> value, tuples -> arrays, finite existing statistics -> numbers,
undefined metric -> `{"value": null, "reason": "..."}`. No nonfinite numeric
value is accepted or emitted. Result checksums cover exact canonical JSON.
Full simulation/equity/order/fill/trade histories, open holdings, comparisons,
selection, warnings and audit findings are retained. Request/result payloads
are parsed once on retrieval; authoritative calculations stay in the core.

## Reproduction interpretation

Reproduction always executes current computation against revalidated retained
CSV/effective metadata and the saved effective request. No request-body override,
cached-result substitution, parameter reselection based on test outcomes or
original-record overwrite is allowed. UUID/UTC timestamps live outside result
payloads and do not participate in economic comparisons.

Economic projection recursively excludes only these named technical/evidence
fields: `reproducibility`, `experiment_version`, `engine_version`, `audit`,
`assumptions`, `warnings`. They stay saved/visible. All other result fields,
including dataset/configuration, settings, selection, valuations, decisions,
orders/fills, cash/shares/P&L, statistics and deltas, compare exactly in their
serialized representation. No float tolerance or money rounding is introduced.

The response reports economic hashes/equality, implementation equality, up to
20 differing field paths, current implementation and limitations. Status is
`matched`, `mismatch`, or `implementation_changed`; the latter takes precedence
even if economic outputs also differ. A completed negative comparison returns
200 with false equality flags. Missing/corrupt/unsupported retained evidence
returns 409 instead of a reproduction claim. Reproduction adds no saved record.

Implementation identity includes package `.py` source manifest, Python version,
importer/engine/experiment/audit/request/payload versions, SQLite version and
direct runtime dependency versions. It is conservative: unrelated package edits
can change it. It is not an executable archive, full transitive-environment
capture or proof of original loaded bytes. Source changes therefore limit any
claim of original-implementation reproduction. Fingerprints and checksums do
not authenticate upstream data or protect a database from deliberate rewriting.

## Errors, local boundaries and complexity

Errors use `{"error":{"code":"...","message":"...","details":...}}`.
400 covers ambiguous/malformed/nonstandard JSON or nonlocal Host; 403 nonlocal
write Origin; 404 unknown resources; 409 unavailable retained evidence; 413
oversize input; 415 media/encoding; 422 configuration/data/eligibility/workload;
503 database/source availability; 500 unexpected backend failures. Data errors
retain bounded field/row diagnostics; request validation omits submitted input.
Internal SQL, server paths, stack traces and uploaded data are not returned.

Bodies are streamed into bounded memory before JSON parsing: import JSON at
most 12 MiB, CSV UTF-8 bytes at most 10 MiB, canonical metadata at most 64 KiB,
other request bodies at most 64 KiB. Raw import overhead/escaping can hit the
body cap before the CSV cap. Reject compressed bodies, duplicate JSON keys,
unsupported media, malformed dates, extra fields and unsupported strategies.

This is a local single-user service without authentication, encryption, public
deployment hardening, CORS access, background jobs or backups. Host validation
and default loopback binding are not authentication. Database files require
normal operator access control/backup. Existing unverified market declarations,
price-only return labeling, audit NOT_ASSESSED risks and statistical limitations
remain; retained bytes establish repeatable inputs, not historical truth.

Dataset/experiment primary-key lookups use indexed search plus O(P) payload work;
experiment lists use creation and dataset/creation indexes with O(log E+offset+L)
row traversal for E records and L page rows. Dataset lists sort D small summary
records: O(D log D), without CSV/result decoding. JSON/hash storage is O(P) time/
space in payload bytes, with bounded transient copies; full traces can still be
large at the experiment bar cap. Revalidation adds CSV parsing/sorting; research
complexity remains in the Phase 6 contract. SQLite writes serialize; busy/errors
return 503 after the configured 5-second timeout. No throughput benchmark ran.

Implementation references: [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/),
[Pydantic strict validation](https://pydantic.dev/docs/validation/latest/concepts/strict_mode/),
[Python SQLite transactions](https://docs.python.org/3/library/sqlite3.html#transaction-control-via-the-autocommit-attribute).
Executed acceptance evidence: [Session 07](session-reports/SESSION_07_PHASE_7.md).
