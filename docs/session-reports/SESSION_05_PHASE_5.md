# Session 05 - Phase 5

Date: 2026-11-01 (Asia/Calcutta).

## A. Session overview

**Objective:** implement a scoped, deterministic backtest integrity auditor.
**Status: COMPLETE.** Session 05 explicitly authorized Phase 5; read the project
contracts, reports 01-04, actual data/execution/strategy/analytics records and
tests, and ran the baseline before implementation. No Phase 6 work was started.
This implementation/verification is AI-assisted; independent owner learning
remains to be done.

## B. What was implemented

Paths are relative to repository root.

| File | Actual responsibility |
| --- | --- |
| `backend/src/quantlab/audit/models.py` | Immutable AuditReport/Finding/Evidence, distinct status/severity, typed request error |
| `backend/src/quantlab/audit/trace.py` | `check_lifecycle`, `check_causality`, `check_sessions`; actual observed-session indexing, association/status/ordering checks |
| `backend/src/quantlab/audit/accounting.py` | `check_ledger`, balances/final state, independent cost equations and source-price/mark checks |
| `backend/src/quantlab/audit/provenance.py` | Recorded/original identities, strict source-row comparison, D04 declarations, retained warnings, unsupported risks |
| `backend/src/quantlab/audit/auditor.py` | `audit_simulation`, evidence validation, independent Decimal context, optional exact replay |
| `backend/src/quantlab/audit/__init__.py` | Public API, audit version 1.0.0 |
| `backend/tests/test_audit.py` | 39 valid/tampered audit cases |

Added audit API contract and this report; updated D09, status, roadmap, README
and analytics cross-references. **All Phase 1-4 source, fixtures, test cases,
package configuration and dependencies remain unchanged.** No result-model
addition, parallel engine, provider, service, or generic trust score was needed.

## C. Why this functionality exists

An equity figure alone cannot establish correct timing, consistent records or
reliable inputs. Each finding names a checked condition and evidence, or says
why assessment is unavailable. Internal consistency, source identity, replay
and historical-market truth remain separate conclusions.

## D. Integration with the existing codebase

Existing `SimulationResult` plus optional retained Dataset/original bytes/
effective Metadata/original settings -> immutable AuditReport. An analytics
report can supply `performance.simulation`; statistical formulas/benchmark
differences are outside this independent audit scope.

Strict source parsing/fingerprinting reuse Phase 1's parser and identity
contract. Financial reconciliation does **not** call engine execution/cost
helpers. Opt-in replay calls the existing engine once; it does not create a
second simulator. No HTTP/database/UI/network or filesystem I/O is needed by
the audit function.

## E. Technical concepts to study

- **Dictionary joins:** order IDs associate fills; source dates map eligibility;
  session buckets reconcile fills without scanning all records at each close.
- **Independent reconciliation:** fold recorded buys/full sells from initial
  flat cash; verify cents debits/credits, shares, cost basis and realized P&L.
  Generate no strategy decision or new order.
- **Typed evidence:** stable rule IDs and field paths, observed/expected text,
  affected order/fill/session references; status and severity are separate.
- **Determinism/validation:** immutable reports, isolated precision-28
  ROUND_HALF_UP context, exact comparison, honest missing-evidence handling.

Independently recreate **`check_ledger`** and **`check_sessions`** after studying
their tests. Do not describe copying this AI-assisted code as independent work.

## F. Financial and quantitative concepts to study

Same-close decisions cannot justify same-session fills. Friday's next observed
session may be Monday; calendar-day increments are insufficient. Trace timing
does not prove arbitrary strategy code lacks future access.

Buy debit is rounded notional plus commission; sell credit is rounded gross
proceeds minus commission. Entry basis includes costs, realized P&L uses a full
exit, and closing equity is cash plus integer shares times unrounded close.
Unfilled orders cannot produce fills or unexplained cash charges.

Unknown/present split status still blocks eligibility. A declared event-free
window, source hash or declared complete coverage cannot establish historical
truth, full shareholder return, opening liquidity or absence of bias. Dividends
and unmodeled corporate actions remain excluded.

## G. Engineering decisions and tradeoffs

- Fixed explicit rule functions and small records; no registry/plugin/container,
  event sourcing, numerical score, new strategy or dependency.
- Dataset/source evidence is optional. Source-dependent checks are NOT_ASSESSED
  without it; a known violation remains FAIL. Coverage/model concerns are
  WARNING, and ten unsupported bias/market categories stay NOT_ASSESSED.
- Reuse Phase 1's strict `_parse_csv` helper rather than add another importer or
  refactor its public API. Original bytes obey the 10 MiB contract; invalid
  rows fail atomically. Partial source evidence supports only the checks it
  actually enables. Supplied metadata remains an assertion.
- Separately retained settings are necessary to detect hidden request changes.
  Replay uses retained recorded settings, not silent defaults, and compares
  every SimulationResult field exactly. Current schema has no nondeterministic
  field exclusions. Original executable snapshot preservation is NOT_ASSESSED.
- Source/input authenticity, all bias absence and statistical reliability are
  never inferred from a green supported rule. No Phase 1-4 defect required a fix.

## H. Testing and verification

Actual repository-root PowerShell commands, approved outside the sandbox due
to the already established pytest temporary-directory restriction:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-phase5-baseline
& '.\.venv\Scripts\python.exe' -m pytest -q backend/tests/test_audit.py --basetemp=.venv/pytest-phase5-audit
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-phase5-full
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-phase5-final
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-phase5-verified
& '.\.venv\Scripts\python.exe' -m pip check
& '.\.venv\Scripts\python.exe' --version
```

Baseline **308 passed in 6.16s**. Initial audit suite **34 passed in 1.01s**.
First combined suite **345 passed in 8.06s**. Stronger chronology checks exposed
an audit test fixture that placed two fills on the same session while expecting
trace causality PASS: **1 failed, 346 passed in 8.80s**. Corrected that fixture
to distinct later sessions, isolating wrong source eligibility without an
additional chronology contradiction. Final suite: **347 passed in 8.10s**,
exit 0, including all 308 unchanged prior cases and 39 audit cases.

`pip check`: **No broken requirements found.** Python **3.15.0**, pytest 9.2.0;
no package installation or application permission workaround. Tests verify:

- Valid $1,067.10 reference, three strategies/open positions, re-entry ($1,306
  final equity), zero terminal cash, rejected/final-expired orders avoid false
  FAIL findings. Friday-to-Monday uses actual source sequence.
- Same/earlier/wrong-eligible fills, reversed history, backdated expiry, missing
  fill, rejected-plus-filled order, duplicates, nonpositive/fractional quantity,
  negative cash/holdings, wrong equity/P&L/commission/prices/marks and hidden cash
  changes trigger the intended supported findings.
- Missing originals/configuration produce NOT_ASSESSED; unknown adjustment or
  split declarations do not pass eligibility. Declared complete coverage remains
  unverified, with real-data acknowledgment still required.
- Original byte hash/metadata mismatch and normalized row tampering fail;
  malformed originals are not silently dropped. Retained request-setting
  mismatch is distinct from internally consistent cost math.
- Repeat reports/replays are deterministic and do not mutate inputs; changed
  economic fields and even removed deterministic warning fields fail replay.
  Unsupported versions/missing inputs cannot claim replay PASS.
- A monkeypatch guard confirms independent audit reconciliation never calls
  production execution/cost helpers. Strict JSON checks find no nonfinite audit
  values; unsupported risk tests assert honest limitation messages.

Installed-package smoke inside the sandbox succeeded with audit version 1.0.0.
The existing synthetic fixture had no FAIL findings; observed-session timing,
ledger/cost math, original fingerprints and current-engine replay passed their
specific checks. Original code snapshot and survivorship stayed NOT_ASSESSED.
Adding $1 to terminal equity triggered ACCOUNTING.BALANCES and
REPRODUCIBILITY.REPLAY FAIL findings.

Final inline document/source verification **PASS**: 55 project files, 30 Python
syntax checks, 47 local links/anchors, UTF-8/LF/trailing whitespace, Git whitespace
including untracked files, A-L/questions, phase consistency, no future-phase
modules and preserved placeholders. No source changed after the final 347-test
run. No real market data or bias-detection claim beyond the explicit rules was
produced.

## I. Complexity and performance

Normal audit: O(N+O+F) time/space plus findings for N source/session records,
O orders and F fills, using date/ID dictionaries and linear passes. Optional B
original CSV bytes add O(B) hashing/parsing and O(N log N) chronological sorting
for Phase 1's permitted unordered sources. Optional replay adds one engine run,
one full-result comparison and its histories; no repeated simulation loop.
Fixed numeric bounds limit money operation size. No cache, vectorization,
concurrency or runtime benchmark was introduced; pytest time is not throughput.

## J. Interview preparation

Five technical questions:

1. How do ID/date dictionaries keep lifecycle and session checks linear?
2. How does an independent fill-ledger fold differ from another simulator?
3. Why are FAIL, WARNING and NOT_ASSESSED distinct from severity?
4. What additional evidence makes original-byte identity and original-request
   matching assessable, and what does SHA-256 fail to establish?
5. Why compare every deterministic replay field, and why is this insufficient
   to prove preservation of the original executable code?

Three financial/quantitative questions:

1. Why can correct trace timing still fail to eliminate look-ahead or selection
   bias?
2. Why must cash, marked equity, realized P&L and open-position P&L reconcile
   separately when commissions and slippage apply?
3. Why do no reported splits, complete-coverage declarations and positive daily
   volume fail to prove accurate corporate actions, complete sessions or opening
   liquidity?

Independent exercise: write a standalone order-ID/fill-ID join that identifies
missing/duplicate fill associations and fills on rejected/expired orders. Use
handwritten small expected cases and a dictionary; explain O(O+F) time/space.
Do it before consulting the production function and keep practice outside it.

## K. Current project status

Phases 0-5 COMPLETE; 6-10 NOT STARTED and unauthorized. No known in-scope failure
remains in executed checks. Supported-rule passes are narrow evidence, not a
trust score. Unsupported biases, authenticity/calendars/actions/liquidity,
significance and unmodeled events remain unknown; full statistical-metric audit
and original code-snapshot restoration are not implemented. Python 3.12 remains
untested and sandbox pytest remains restricted. Files are unstaged/uncommitted;
no branch/remote change or future-phase source was added.

## L. Next session

Proposed Session 06 / Phase 6 **only after explicit authorization and D08
review**: bounded parameter/cost/period comparisons and chronological train/test
evaluation. Review caps (proposed 100 configurations/1,000,000 aggregate bars),
pre-window indicator warm-up, frozen selection, identical benchmark windows,
data/source snapshot reproducibility and failure/resource handling. Acceptance:
deterministic bounded runs, explicit oversized-grid rejection, no test-set-driven
selection, independent comparison fixtures and preserved regressions. No sweep,
optimizer, train/test or walk-forward module exists. Stop after Phase 5.
