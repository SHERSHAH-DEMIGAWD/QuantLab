# Phase 10 release validation

2026-11-03 (Asia/Calcutta). This records Session 10's synthetic release checks.
Later [real historical validation](REAL_MARKET_VALIDATION.md) additionally
verified limited IBM/MSFT workflows; the synthetic suite remains in place.
No financial/production backend correction was needed.
All 41 package `.py` files match the retained Phase 8 source manifest in both
the main tree and the fresh source copy. No dependency/architecture change.

## Environment and clean setup

Windows 11 build 26200, CPython 3.15.0 (64-bit MSC v.1951), SQLite 3.53.4,
Node 24.15.0/npm 11.12.1, installed Edge 156.0.4314.58. Frontend runtime:
React/ReactDOM 19.3.1, uPlot 1.6.32, Zod 4.6.7; TypeScript 7.0.2, Vite 8.3.5,
Vitest 5.0.5, Playwright 1.64.1. Exact declared dependencies are in
`pyproject.toml`/frontend manifest+lock; all installed Python package versions
are in [environment.json](benchmark-results/environment.json). Python 3.12,
other operating systems/browser channels and full machine configuration were
not verified. No global software/configuration changes were made.

The repository has no committed baseline. Instead of deleting/replacing the
working tree, copied 118 Git-visible source/config/test/doc files to the new
ignored `.release-check/source` tree, excluding environments, private data,
databases, caches and builds. Created sibling `.release-check/python` from the
existing interpreter. The final browser-test additions were copied into that
tree before verification; production backend hashes stayed identical.

Actual setup commands, repository root unless noted:

```powershell
py -3.15 -m venv .release-check/python
# From .release-check/source
..\python\Scripts\python.exe -m pip install -e '.[test]'
# From .release-check/source/frontend
npm ci
# From repository root
.\.release-check\python\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pip check
```

Fresh editable package/dependency install succeeded; `npm ci` installed 110
packages and reported zero vulnerabilities at installation time. Both `pip
check` commands found no broken requirements. This is consistency evidence,
not an exhaustive security audit. Python transitive dependencies remain
resolver-selected, with the actual verified inventory retained.

## Actual regression commands and results

Baseline from repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --durations=5 --basetemp=.venv/pytest-phase10-baseline
```

Fresh source directory, corrected complete run:

```powershell
..\python\Scripts\python.exe -m pytest -q --durations=5 --basetemp=../python/pytest-phase10-clean-fixed
```

Frontend commands: `npm test`, `npm run test:e2e`; the latter always runs
`npm run build` first (strict TypeScript + Vite). For the fresh tree and final
main-tree browser run, explicitly selected the fresh backend environment:

```powershell
# From frontend; equivalent portable form of the session's absolute path
$env:QUANTLAB_PYTHON=(Resolve-Path '..\.release-check\python\Scripts\python.exe').Path
npm run test:e2e
```

| Executed run | Outcome, no skips |
| --- | --- |
| Main backend baseline | 444 passed in 22.83s |
| Main frontend baseline | 45 passed in 12.64s |
| Main production-browser baseline | 3 passed in 21.7s; build passed |
| Fresh backend first attempt | 56 passed, 388 setup errors in 32.20s |
| Isolated first setup diagnostic | 1 error in 1.51s; missing basetemp parent confirmed |
| Fresh backend corrected full suite | 444 passed in 23.74s; slowest case 0.89s |
| Fresh frontend suite | 45 passed in 11.63s |
| First extended fresh browser suite | 3 passed, 1 failed in 25.4s |
| Corrected extended fresh browser suite | 4 passed in 24.2s; build passed |
| Final main-tree browser suite with explicit provenance inspection | 4 passed in 25.3s; build passed |

The first fresh pytest command used `--basetemp=.venv/pytest-phase10-clean`
inside the source copy, whose `.venv` parent did not exist because its venv is
a sibling. WinError 3 was a validation-command error, not a test assertion or
financial defect. Corrected the path to the existing environment parent and
reran the complete suite; no tests were omitted.

The first added browser case assumed SMA slow window 3 without setting it;
the actual default is 5 and correctly returned $628. Its independent $910
reference was for SMA(2,3). Explicitly set those parameters; left UI defaults and
engine unchanged. The complete suite then passed. Neither failure was hidden
by retries or a production-policy workaround. Approved external execution was
used for known Windows sandbox process/private-temp restrictions; no app change.

## Genuine application workflow

Playwright uses the actual production frontend/API/SQLite, no financial mocks,
one worker, 1440x1000 and 390x844, Asia/Kolkata timezone. Four workflows verify:

1. Actual CSV/JSON upload, expanded provenance, separate eligibility notice,
   buy-and-hold $800 reference, real canvas, fills/exact equity, audit evidence,
   saved reopening, fresh reproduction, restart of both processes with same DB,
   reopening/reproduction again, and invalid OHLC physical-row diagnostics.
2. Four SMA parameter candidates plus reference, two actual cost scenarios,
   three/six-bar subperiods, chronological training/test selection frozen at
   momentum lookback 2, -54% held-out result, fresh $1,000/six warm-up bars,
   saved reproduction and mobile saved-result/chart layouts.
3. Genuine metadata-template download/upload; unknown-template, unknown-split
   and adjusted-price imports remain blocked by D04 even with coverage
   acknowledged; form values persist and no stale result appears; mobile guide.
4. Separate buy-and-hold/SMA(2,3)/momentum(2) backtests; independently expected
   cost-bearing $792.20 and zero-cost $910/$910 results; actual PASS/WARNING/
   NOT_ASSESSED evidence, empty valid FAIL filter, and invented zero-volume
   rejection followed by a fresh buy (final $668, 83 open shares).

Valid saved experiments contain no audit FAIL; tampered records exercise FAIL
in the backend audit suite and component tests display it. No fabricated audit
failure was injected into a valid real-browser result. Desktop order-outcome
and mobile saved-research screenshots were visually inspected. Artifacts under
ignored `frontend/test-results/` include screenshots, `e2e-evidence.json` and
`release-evidence.json`. No measured human 3-5 minute rehearsal is claimed.

Fresh development startup also succeeded: backend `-m quantlab.api --port 8019`
from the clean source tree, Vite `npm run dev -- --port 5179 --strictPort` with
`QUANTLAB_API_TARGET=http://127.0.0.1:8019`. Verified HTML, proxied health/schema
1, synthetic import, $800 backtest and fresh matching reproduction through
5179. Default 8000/5173 were occupied and left untouched. Owned test/dev ports
8018/5178/8019/5179 were checked stopped afterward.

## Financial and failure evidence map

All cases below ran in both complete 444-test suites; no new financial defect
required a targeted production regression fix.

| Concern | Working reference tests/source reviewed |
| --- | --- |
| Close-only signals, next observed open, future-prefix isolation | `test_execution.py::test_future_prices_do_not_change_earlier_decisions`; `test_strategies.py::test_changed_future_prices_preserve_earlier_signals_and_completed_fills`; engine/rules loop |
| Integer sizing, nonnegative cash/shares, exact rounding | `test_execution.py::test_numeric_extremes_and_invariants`, `test_round_half_up_notional_and_unrounded_marks`; `test_analytics.py::test_rounding_edge_affordability_and_half_up_fee` |
| Fee/slippage and reconciliation | `test_analytics.py::test_commission_and_slippage_independent_round_trip`; independent `audit/accounting.py` ledger tests in `test_audit.py` |
| Rejected/expired orders, open versus closed, no forced final sale | `test_execution.py` zero-volume/terminal tests; `test_analytics.py::test_rejected_and_expired_orders_do_not_charge_commission`, `test_no_trades_and_open_position_are_not_completed_wins` |
| Metrics/undefined reasons/compatible reference | `test_analytics.py` independent equity reference, zero variance, overflow and same-cost/window benchmark tests |
| Frozen selection, no warm-up trading/carryover | `test_experiments.py::test_changing_future_test_prices_never_changes_training_selection`, `test_indicator_only_warmup_has_no_trades_valuations_or_carried_pending_order`, `test_warmup_uses_training_interval_and_excludes_intervening_gap` |
| Honest audit statuses and evidence | `test_audit.py` tampered timing/ledger/input tests, missing evidence and scoped limitations; `views.test.tsx` four-status rendering |
| Invalid inputs, limits and eligibility | `test_data.py`, `test_offline_workflow.py`, `test_api.py` CSV/body/precision/configuration/aggregate caps and unknown-split/coverage tests |
| Rollback/API failures/unknown records/mismatch | `test_api.py::test_failed_writes_roll_back_and_do_not_report_success`, `test_unexpected_backend_failures_do_not_expose_paths_or_stacktraces`, `test_unknown_ids_pagination_and_unrecognized_routes_have_structured_errors`, `test_reproduction_detects_changed_economics_and_implementation_separately` |

## Reliability and repository review

Phase 8's SQLite 503/browser ENOSPC did not recur. Initial C: free space was
3,202,330,624 bytes; later observations were 2.79/1.54/1.01 GiB. Source and TEMP
share that volume. Measured retained release-check tree 202.6 MiB, primary
node_modules 140.8 MiB, primary browser artifacts 0.3 MiB. Fresh installation,
test rollback cases, benchmark temporary SQLite creation/removal and browser
restarts/downloads all succeeded. Tests/installs preceded timing; test helpers
stop owned processes. No historic resource telemetry explains the earlier
incident, and observed disk changes are not attributed without evidence.
No global temp cleanup, user-data deletion, stress-to-disk-full test or
speculative infrastructure fix was performed. Cause remains unresolved.

Reviewed module boundaries, codec/financial ownership, declarations/imports and
frontend runtime/test package use. No obvious unused direct dependency, dead
framework or duplicated frontend portfolio calculation required removal. This
was a scoped review, not an exhaustive static/security audit. `scripts/verify_repository.py`
checks source/JSON/Python syntax, local links, whitespace, dependency-lock match,
known credential patterns, generated-file exclusions, core boundaries, unchanged
backend hashes, benchmark evidence and final report/phase status. No source
credential pattern was found. Raw/processed data placeholders remain empty.
No staging, commit, branch, remote, tag or deployment action was taken.

Benchmarks: [BENCHMARKS.md](BENCHMARKS.md). Remaining scope/ownership limits:
[KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md). Final integrity-check outcome is
recorded in [Session 10](session-reports/SESSION_10_PHASE_10.md).
