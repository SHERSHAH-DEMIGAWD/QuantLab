# Phase 5 integrity audit API

Implemented deterministic rules, with no trust score. Policy is recorded in
[D09](DECISIONS.md#d09---phase-5-evidence-backed-integrity-audit); financial
conventions remain D04-D07. PASS applies only to the named check and evidence.
WARNING can describe a model/data concern without identifying an engine defect.
NOT_ASSESSED is never PASS. There is no overall assertion of financial safety.

```python
from decimal import Decimal
from pathlib import Path
from quantlab.data import load_dataset
from quantlab.execution import ExecutionSettings, simulate
from quantlab.audit import audit_simulation

path = Path("backend/tests/fixtures/synthetic_daily.csv")
dataset = load_dataset(path, "backend/tests/fixtures/synthetic_daily.metadata.json")
settings = ExecutionSettings(commission_per_fill_usd=Decimal("2"), slippage_bps=Decimal("100"))
result = simulate(dataset, Decimal("1000"), settings=settings)
audit = audit_simulation(
    result, dataset=dataset, source_bytes=path.read_bytes(),
    source_metadata=dataset.metadata, expected_settings=settings, rerun=True,
)
for finding in audit.findings:
    print(finding.rule_id, finding.status, finding.explanation, finding.evidence)
```

The fixture is invented; no historical-market conclusion follows from it.
`audit_simulation(result)` also works without supporting data and produces
NOT_ASSESSED for checks needing missing evidence. For an analytics report,
pass `performance.simulation`; statistical metric formulas and benchmark
differences are outside this version's independent audit coverage.

## Request and result

`audit_simulation(result, *, dataset=None, source_bytes=None,
source_metadata=None, expected_settings=None, rerun=False)` returns an immutable
`AuditReport(audit_version="1.1.0", dataset_id, findings)`.

Each `Finding` contains rule ID/title, status, severity (`ERROR`, `WARNING`, or
None), scoped explanation, evidence tuple, and optional suggested action.
`Evidence` contains a field/reference path, observed and expected text, plus
order ID, fill index and session where relevant. The report's dataset ID
identifies the affected result input. Ordering and text are deterministic.

Use existing typed records; malformed request/container types raise `AuditError`
(ValueError), not a fake successful report. Financial tampering is reported
through findings. Inputs are not modified. No files/network are accessed by
the audit function; callers supply retained data and exact source bytes.

## Supported rules and evidence

| Rule IDs | Supported conclusion / evidence requirement |
| --- | --- |
| `TIMING.CAUSALITY` | Recorded decisions/orders/fills are ordered, execution follows decision and declared eligibility; final expiry occurs at final close. Trace evidence only, not all-look-ahead proof |
| `TIMING.NEXT_SESSION` | Eligibility/outcomes/valuation/decision sequence match selected supplied source sessions, not calendar-day increments; needs usable source bars |
| `TIMING.WARMUP` | Paired prior requested bounds, actual source bounds/count, no pre-evaluation decisions/orders/fills/valuations; usable source needed for observed history. Independent ledger checks fresh flat cash |
| `ORDERS.LIFECYCLE` | Unique order IDs, matching decisions and budgets/full positions, terminal statuses, one fill per filled order, none on rejected/expired orders, positive integer quantities and matching fill fields |
| `ACCOUNTING.BALANCES` | Nonnegative cents cash/integer holdings, mark/equity/unrealized P&L, final-record agreement |
| `ACCOUNTING.LEDGER` | Independent full-fill cash/share/basis/realized-P&L fold from initial flat state matches each close and decision; no signal/order generation |
| `COSTS.CONFIGURATION`, `COSTS.FILL_MATH` | Retained supported Decimal settings and independent D05-D06 slipped-price/notional/fee/net-cash equations; fill arithmetic supports engines 1.2.0 and 1.3.0 |
| `COSTS.REQUEST_MATCH` | Complete result settings equal separately retained original request settings; otherwise NOT_ASSESSED |
| `COSTS.UNFILLED` | No rejected/expired fill associations and reconciled cash ledger. If unexplained cash changes prevent attribution, NOT_ASSESSED rather than inventing a cause |
| `DATA.RECORDED_IDENTITY`, `DATA.INPUT_MATCH` | Hash syntax/canonical internal relationships and optional retained Dataset identity/metadata/count/endpoints; neither proves original bytes |
| `DATA.SOURCE_SHA256` | Supplied exact CSV hash equals recorded source hash; works even without original metadata |
| `DATA.ORIGINAL_IDENTITY` | All D03 fingerprints match supplied exact bytes and separately supplied effective Metadata; both required |
| `DATA.ORIGINAL_ROWS` | Strict original CSV parsing and normalized row equality with retained Dataset, including source-row references; invalid rows fail; missing comparison data is NOT_ASSESSED |
| `DATA.SOURCE_SEQUENCE`, `DATA.PRICE_REFERENCES` | Valid supplied OHLC/date/volume structure; actual source opens, marks, and nonzero fill volume match records |
| `DATA.ELIGIBILITY` | D04 declarations and real-data coverage acknowledgment satisfy the existing policy. Unknown/present splits do not pass eligibility |
| `DATA.PROVENANCE`, `DATA.LIMITATIONS` | WARNING: visible assertions/unknowns, retained warnings, unverified coverage/actions, excluded dividends and unsupported opening liquidity |
| `REPRODUCIBILITY.REPLAY` | Opt-in current-engine 1.3.0 exact replay of all SimulationResult fields, including warm-up metadata; retained Dataset/configuration required. Historical versions are NOT_ASSESSED; no nondeterministic fields exist to exclude |
| `REPRODUCIBILITY.SOURCE_SNAPSHOT` | NOT_ASSESSED: original executable/source snapshot is not supplied/restored |

Original bytes are parsed with the existing Phase 1 strict parser (10 MiB CSV
limit). Effective metadata uses the established canonical fingerprint contract;
copying fields from a result is not independent retention of an original source.
Prefer separately retained importer outputs. Supplied inputs themselves remain
assertions; SHA-256 does not authenticate a market-data provider.

The [experiment layer](EXPERIMENT_CONTRACT.md) records a local package source
manifest but does not restore executable snapshots or supply original CSV
bytes to the auditor. Its runs retain all audit findings, use the shared
Dataset and original request settings, and disable optional replay to avoid
unbudgeted simulation. Identity/restoration limits remain explicit.

Ten `LIMITS.*` findings are always NOT_ASSESSED: every form of look-ahead,
survivorship, historical index membership, data snooping/strategy selection,
overfitting, historical corporate-action truth, authoritative session coverage,
opening liquidity, significance, and all unmodeled economic events. No strategy
profits, lack of bias, or statistical reliability are certified.

For N source/session records, O orders and F fills, normal auditing is
O(N+O+F) time and space plus findings, using date/ID dictionaries. Optional B
source bytes add O(B) hashing/parsing and O(N log N) sorting for Phase 1's
permitted unordered CSV input. Optional replay adds one existing engine run and
one linear result comparison. No repeated simulation loop, cache, concurrency,
provider, API, database or frontend was added. No runtime benchmark was run.
