# Session 02 - Phase 2

Date: 2026-11-01 (Asia/Calcutta).

## A. Session overview

**Objective:** implement and verify the minimal daily execution engine.
**Status: COMPLETE.** The user's attached Session 02 request explicitly
authorized Phase 2, D04-D05, and the fresh-intent clarification. Read the
required project documents, actual importer/models/tests, and latest report;
ran the Phase 1 baseline before modifications. Accelerated mode kept the
implementation limited to the engine and its acceptance evidence.

This implementation and verification are AI-assisted. The owner's independent
recreation and learning remain to be done. Phase 3 was not started.

## B. What was implemented

Paths below are relative to the repository root.

| File | Implemented responsibility |
| --- | --- |
| `backend/src/quantlab/execution/engine.py` | `simulate_buy_and_hold`, `_preflight`, `_decide`, `_execute`; eligibility, bounded Decimal accounting, ordered execution/valuation/decision loop, rejection/expiry, single diagnostic exit |
| `backend/src/quantlab/execution/models.py` | Frozen settings, decisions, orders, fills, daily valuations, result; `SimulationError` |
| `backend/src/quantlab/execution/__init__.py` | Public API and supported numeric bounds |
| `backend/tests/test_execution.py` | 58 deterministic cases, independent buy/sell/rounding references, financial and timing invariants |
| `docs/EXECUTION_CONTRACT.md` | API, settings, output meanings, limitations |

Updated D04/D05 through dated amendments, roadmap, status, README, and package
description. Phase 1 source/tests/fixtures and dependencies were retained.
No general strategy interface or future-phase source was added.

## C. Why this functionality exists

Valid prices alone do not explain a portfolio's cash or share count. The engine
makes decision time, reserved budget, actual execution, and closing valuation
separate records so gaps, rounding, rejected orders, and open positions remain
explainable and deterministic.

## D. Integration with the existing codebase

`load_dataset -> Dataset -> simulate_buy_and_hold -> SimulationResult`.
Reuse Phase 1's Decimal bars, effective metadata, immutable records, identities,
warnings, and OHLC predicate. Execution adds D04 eligibility and its own safe
numeric limits; ingestion acceptance alone remains insufficient. The core
imports no HTTP, database, frontend, calendar, or provider code.

## E. Technical concepts to study

- **State and loops:** the engine owns local cash, integer shares, cost basis,
  realized P&L, and at most one pending order; open processing precedes valuation
  and the close decision.
- **Data structures:** frozen records/tuples are outputs; lists accumulate the
  trace. An order's final record replaces its pending record without mutating
  input data. Each fill links to one sequential order ID.
- **Decimal/invariants:** isolated precision 28 and ROUND_HALF_UP, exact integer
  microunit sizing, cents cash/notionals, six-decimal fills, unrounded marks;
  negative cash/holdings or wrong fill timing fail explicitly.
- **Determinism/information:** `_decide` receives only current date, current
  holdings, and the explicit diagnostic exit date. It cannot inspect future
  prices; sizing belongs to the later execution step.

After studying tests, independently recreate **`_execute`** and the central
loop in **`simulate_buy_and_hold`**. Copying this AI-assisted code is not an
independent implementation.

## F. Financial and quantitative concepts to study

A LONG decision while flat creates a cash-budget intent; a fill creates shares.
At $103, $1,000 buys 9 shares and leaves $73. A $105 close marks equity at
$1,018; no closing sale occurred. A later full exit at $110 credits $990,
leaving $1,063 cash and $63 realized P&L. Before that exit, gains are unrealized.

Next observed open may follow an overnight/calendar gap. Daily positive volume
does not prove opening liquidity. Split share-unit changes and dividends are
not modeled; results are price-return simulations excluding dividends.
Eligibility declarations and the real-data coverage acknowledgment expose
uncertainty rather than verifying the market or making brokerage guarantees.

## G. Engineering decisions and tradeoffs

- Two substantive modules plus public exports; no framework, strategy callback,
  dependency, vectorization, concurrency, or cache. Explicit bounds keep current
  single-entry arithmetic exact within precision 28; later repeat-entry logic
  must review potential growth.
- Floor sizing respects the raw reserved budget, then rechecks the rounded
  debit. Rounded cash can differ slightly from exact subcent marks; tested
  explicitly and recorded in D05.
- One configured diagnostic exit tests selling. It emits FLAT once then HOLD;
  a rejected exit is terminal. Ordinary buy-and-hold instead generates fresh
  buy IDs after rejected entries while flat, as explicitly authorized.
- Full-import split declarations govern eligibility even for subwindows;
  there is no dated event ledger from which to infer a safer interval.
- Real-data coverage always needs explicit acknowledgment. No authoritative
  calendar, corporate-action model, audit framework, or metric was added.

## H. Testing and verification

Actual commands from repository-root PowerShell, using existing CPython 3.15.0
and pytest 9.2.0:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-phase2-baseline
& '.\.venv\Scripts\python.exe' -m pytest -q -x --basetemp=.venv/pytest-phase2-diagnose
```

Sandbox baseline showed repeated setup errors and was interrupted; diagnostic
run confirmed `PermissionError: [WinError 5]` on pytest's temporary directory,
including cleanup. These are environment failures, not passing tests.
Approved execution outside that sandbox:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-phase2-baseline-verified
& '.\.venv\Scripts\python.exe' -m pytest -q backend/tests/test_execution.py --basetemp=.venv/pytest-phase2-engine
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-phase2-full
& '.\.venv\Scripts\python.exe' -m pip check
```

Baseline: **162 passed in 4.47s**; no pre-existing test failure found after the
environment issue was resolved. Initial execution suite: **57 passed in
1.62s**. After strengthening malformed-record validation and adding the
import/execution-range distinction: **220 passed in 5.76s**, comprising 162
Phase 1 and 58 Phase 2 cases. `pip check`: **No broken requirements found.**
`python --version`: **Python 3.15.0**. No packages were installed this session.

| Required coverage | Executed evidence in `test_execution.py` |
| --- | --- |
| Buy/next-open/gap/integer/residual | Hand reference 9 shares, $73 cash, $1,018 equity; $130 gap buys 7 with $90 remaining |
| Insufficient funds/zero volume/fresh intent | Terminal reasons, no rejection fill, new order ID and later eligibility, final fresh intent expires |
| Sell/invalid exit/no retry | $1,063 full-sale reference, invalid requested position yields no fill, zero-volume sell preserves holdings |
| Invariants/valuation/rounding | Nonnegative cash/integer shares, linked later fills, exact equity, half-up buy/sell cents, unrounded subcent marks, maximum supported values |
| End treatment/small samples | Open final position, final sell and buy expiry, one-row and empty-window errors |
| Determinism/no future influence | Repeated output equality, hostile ambient Decimal context, changed future opens/later bars and appended future preserve earlier decisions |
| Invalid/ineligible/configuration | Bad cash/precision/ranges/OHLC/structure/settings, adjustment/volume/split restrictions, nonzero/invalid costs, real-data coverage acknowledgment even if declared complete |

Installed-package smoke execution inside the sandbox used the existing Phase 1
synthetic fixture: dataset ID unchanged (`7ee51a72...47b0e1`), one buy fill,
three valuations, final 9 shares, $79.75 cash, $1,011.25 equity. These prices
differ from the independent reference above. No actual market data was tested.

Final inline Python document/source audit: **PASS** for 32 project files,
12 Python syntax checks, 28 local links/anchors, Git whitespace including
untracked files, UTF-8/LF/trailing whitespace, A-L/questions, phase consistency,
and preserved placeholders. The first audit incorrectly required exit 0 from
Git's no-index diff on a new file; corrected the checker to accept difference
exit 1 only with no whitespace/error diagnostics, then passed. No source defect
was found by that audit. No coverage percentage, 3.12 compatibility, or
throughput claim was made.

## I. Complexity and performance

For N imported and M selected bars, preflight O(N + M), simulation O(M), total
O(N + M) time and O(M) auxiliary/output space. Fixed numeric bounds limit
arithmetic size. Only current state enters decisions; no growing history slices
are copied. Retaining daily decisions/valuations/order outcomes costs linear
space. No benchmark was run; pytest duration is not simulator throughput.

## J. Interview preparation

Five technical questions:

1. Why separate a budgeted decision from quantity sizing at the next open?
2. How do immutable output records coexist with changing local portfolio state?
3. Why isolate Decimal context and reject unsupported precision before execution?
4. How do terminal rejection and a fresh order ID differ from automatic retry?
5. Which tests independently verify accounting, and which prove earlier decisions
   remain unchanged when future inputs change?

Three finance questions:

1. Why can an overnight gap change shares purchased without changing the earlier
   buy decision?
2. How do cash, marked equity, realized P&L, and unrealized P&L differ in the
   $103 purchase/$105 close/$110 sale example?
3. Why do no reported splits and declared complete sessions still fail to prove
   a price-return simulation represents total historical shareholder wealth?

Independent exercise: write a standalone `budgeted_buy(cash, open_price)` using
Decimal that returns whole shares and remaining cents, respecting the raw
budget, half-up notional, and nonnegative cash. Hand-test $1,000/$103,
$1/$2, and $1.01/$0.335 before comparing with `_execute`. Keep it outside
production code; do not add a strategy or claim this assisted work as your own.

## K. Current project status

Phases 0-2 COMPLETE; 3-10 NOT STARTED and unauthorized. No known in-scope
functional failure remains in executed checks. Important limits: zero costs,
single entry/diagnostic exit, numeric bounds, no real-market verification,
corporate-action/coverage/liquidity uncertainty, no performance statistics or
benchmarks, Python 3.12 untested, sandbox pytest temp-directory failure.
Files remain unstaged/uncommitted; no branch/remote change was made.

## L. Next session

Proposed Session 03 / Phase 3, **only after explicit authorization and D08
review**: minimal common strategy interface, buy-and-hold adaptation preserving
timing/fresh-intent behavior, SMA crossover, and the defined time-series
momentum rule. Review warm-up, equality, initial bullish SMA entry, threshold,
and numeric-growth bounds. Acceptance: independently tabulated signal sequences,
parameter errors, restricted history, append-future invariance, and preserved
Phase 1-2 tests. Do not begin costs, metrics, audit, API, or UI. Stop here.
