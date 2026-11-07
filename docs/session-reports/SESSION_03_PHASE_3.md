# Session 03 - Phase 3

Date: 2026-11-01 (Asia/Calcutta).

## A. Session overview

**Objective:** separate the three authorized built-in decision rules from
execution while preserving Phase 2 financial behavior. **Status: COMPLETE.**
The user's Session 03 attachment approved Phase 3 and D08 strategy semantics.
Read the required documents, Phase 1-2 reports, importer/engine/models/tests,
and verified the baseline before code changes. Phase 4 was not started.
Implementation and verification are AI-assisted; owner learning remains
independent work to do.

## B. What was implemented

Paths are relative to the repository root.

| File | Actual change |
| --- | --- |
| `backend/src/quantlab/strategies/models.py` | Immutable `BuyAndHold`, `SMACrossover`, `TimeSeriesMomentum`, validated parameters, shared Target and expected error |
| `backend/src/quantlab/strategies/rules.py` | `DecisionRule.on_close`, controlled factory, fresh rolling sums/queues, exact SMA/momentum comparisons |
| `backend/src/quantlab/strategies/__init__.py` | Public configurations and typed close-only interface |
| `backend/src/quantlab/execution/engine.py` | Existing loop becomes `simulate`; buy-and-hold compatibility wrapper; runtime arithmetic envelope for re-entry; engine version 1.1.0 |
| `backend/src/quantlab/execution/models.py`, `__init__.py` | Result retains immutable strategy configuration; shared exports |
| `backend/tests/test_strategies.py` | 45 deterministic signal and integration cases |

Updated execution API documentation, dated D05/D08 amendments, roadmap, status,
and README. Phase 1 source, all 220 existing test cases, fixtures, package
configuration, and dependencies remain unchanged. No second engine exists.

## C. Why this functionality exists

A rule selects a desired state; the engine determines whether that state needs
an order and how a later fill changes the account. Separating those steps
allows SMA and momentum to reuse verified accounting and avoids duplicate
execution paths or strategy access to future opening prices.

## D. Integration with the existing codebase

`load_dataset -> simulate(config) -> current completed close -> target ->
existing next-open order/fill/accounting -> SimulationResult`.
Only scalar current position and the current date/close reach a rule; queues
contain earlier supplied closes. No full dataset or mutable portfolio is passed.
Each call constructs its own state; configurations and returned events are
immutable. `simulate_buy_and_hold` routes through this same loop, including
fresh intents and the prior diagnostic exit.

## E. Technical concepts to study

- **Protocol and composition:** one small typed interface without inheritance
  trees or plugin callbacks; only three exact built-in configuration types.
- **Rolling state:** deques evict old closes in O(1); integer sums avoid scanning
  or copying growing history prefixes.
- **Exact comparisons:** compare SMA sums by window cross multiplication;
  compare momentum to a Decimal's integer ratio without rounding division.
  Decimal precision-28 cash accounting is unchanged.
- **Isolation and invariants:** fresh rule per run, immutable input/output,
  terminal order outcomes, runtime numeric checks before unsafe products.

Independently recreate **`_SMARule.on_close`** and **`_MomentumRule.on_close`**
after studying their tests. Do not count copying AI-assisted code as independent
work.

## F. Financial and quantitative concepts to study

SMA is a **target-state rule**: after enough closes, fast above slow means LONG,
below means FLAT, equal means HOLD. A first bullish state can enter without a
prior observed crossing. HOLD preserves the current position, including on ties.

Momentum uses one instrument's `close[T]/close[T-L]-1`, not cross-sectional
ranking. Exactly equal to threshold means FLAT. Warm-up uses selected-window
closes only. A target at T can fill only at the next observed open. LONG while
already long and FLAT while flat do not trade. Re-entry uses available cash and
new integer sizing; sale proceeds remain immediately available in this model.
Zero costs, price-return/dividend exclusion, corporate-action restrictions,
and coverage/liquidity uncertainty remain in force.

## G. Engineering decisions and tradeoffs

- Stream one completed close into a fresh stateful rule rather than handing it
  a mutable full dataset or repeatedly sliced prefixes. Pure immutable configs
  can be reused across runs; live rolling state cannot.
- Exact integer signal arithmetic avoids false equality caused by rounded SMA
  or momentum division. Threshold accepts finite Decimal, with no float
  conversion. Arithmetic cost depends on parameter/threshold bit length.
- Numeric review was required by the original D05 amendment for repeated
  entries. Preserve initial/price limits; bound runtime shares/cash, fail
  explicitly beyond the precision-28 envelope, and test extreme re-entry.
  This is new-flow range handling, not a Phase 2 financial defect or redesign.
- Keep the old diagnostic exit only with buy-and-hold; combining it with another
  rule fails rather than silently overriding that rule. No pre-window warm-up,
  user-defined code, fourth strategy, optimization framework, or dependency.

## H. Testing and verification

Actual repository-root PowerShell commands, approved outside the sandbox due
to the already documented pytest temporary-directory access failure:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-phase3-baseline
& '.\.venv\Scripts\python.exe' -m pytest -q backend/tests/test_strategies.py --basetemp=.venv/pytest-phase3-strategies
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-phase3-full
& '.\.venv\Scripts\python.exe' -m pip check
& '.\.venv\Scripts\python.exe' --version
```

Baseline **220 passed in 5.63s**; new strategy suite **45 passed in 0.88s**;
complete suite **265 passed in 5.94s** (162 data, 58 execution, 45 strategy).
All runs exited 0; no pre-existing or new test failure was observed. Dependency
check: **No broken requirements found.** Environment: **Python 3.15.0**,
pytest 9.2.0. No package installation or permission workaround was added.

Independent references in `test_strategies.py`:

- SMA 2/4: fourth-close means 3.5 versus 2.5 -> LONG; sixth-close means
  2.5 versus 3 -> FLAT. Flat averages HOLD; first sufficient bullish state enters.
- L=2 momentum: +20% -> LONG; zero return -> FLAT. Exact +10% with k=.1 and
  -10% with k=-.1 are FLAT. A threshold just below 1/3 still permits 4/3-1,
  without rounded equality changing the signal.
- SMA 2/3 integration: buy 66 at $15, sell 66 at $9, re-enter 54 at $11;
  final cash $10, shares 54, closing equity $1,306; realized -$396,
  unrealized $702. Momentum round trip/re-entry ends with $8 cash, 3 shares,
  and $68 equity. Expected values are handwritten, not generated by the rule.
- Warm-up, parameter errors, ties with an existing position, rejected entries,
  no redundant executions, later eligible fills, final expired sell, extreme
  numeric growth, immutable records, deterministic repeats, and interleaved runs.
- Changed future prices preserve earlier decisions/valuations/completed fills.
  Appended sessions preserve the prefix while the old final EXPIRED intent
  legitimately becomes FILLED or REJECTED; tests compare those separately.
- All Phase 2 tests pass unchanged, plus explicit wrapper/reference checks and
  shared-engine eligibility, zero-cost, and Decimal-context checks.

Installed-package smoke run inside the sandbox succeeded for all three
configurations on the existing synthetic fixture. Buy-and-hold retained 9
shares, $79.75 cash, and $1,011.25 equity; SMA 1/2 and momentum L=1 each recorded
a zero-volume rejection and remained flat with $1,000. No data was discarded.

Final inline document/source audit **PASS**: 37 project files, 16 Python syntax
checks, 31 local links/anchors, UTF-8/LF/trailing whitespace, Git whitespace
including untracked files, A-L/questions, phase consistency, no future-phase
modules, and preserved empty placeholders. No source changed after the full
265-test run. No real market data, coverage percentage, Python 3.12
compatibility, or profitability evidence was produced.

## I. Complexity and performance

For M selected closes and fixed-size prices/parameters: each rule processes
O(M) total time. Buy-and-hold uses O(1) state; SMA O(min(M, slow_window));
momentum O(min(M, L+1)). Rolling updates are O(1) per session; exact integer
operation cost grows with operand bit length, including arbitrary-precision
thresholds. No O(M^2) growing-prefix copies or repeated full-window sums.
Engine preflight adds O(N) for N imported bars; result histories use O(M).
No benchmark ran; test durations do not measure signal throughput.

## J. Interview preparation

Five technical questions:

1. How does `DecisionRule` separate decisions from account mutations without
   accepting arbitrary executable strategies?
2. How do the two rolling SMA queues and sums maintain their invariants?
3. Why compare exact sums/ratios instead of rounded quotients near equality?
4. Why must configuration be immutable and rolling state be fresh for each run?
5. Why can appending a session preserve earlier decisions while changing an
   earlier run's final EXPIRED order into a fill?

Three finance questions:

1. How does a target-state SMA rule differ from a crossing-event detector, and
   what happens when its first sufficient history is bullish?
2. What does threshold equality mean for momentum versus equality of SMAs?
3. How can a correct close signal lead to a different quantity or rejected order
   at the next open without violating the information boundary?

Independent exercise: without copying the rolling implementation, write a
simple reference SMA target function using only an explicitly supplied close
prefix and fast/slow windows. Hand-tabulate warm-up, ties, and a bullish then
bearish example before comparing outputs. Explain its O(window) decision cost
versus rolling sums. Keep practice outside production code.

## K. Current project status

Phases 0-3 COMPLETE; 4-10 NOT STARTED and unauthorized. No known in-scope
functional failure remains in executed checks. Limitations: three built-ins,
zero costs, bounded accounting, selected-window warm-up, declarative data
eligibility, unverified calendars/actions/liquidity, Python 3.12 untested, and
sandbox pytest limitation. No costs/metrics/audit/experiments/API/database/UI
were added. Files remain unstaged/uncommitted; no branch or remote changed.

## L. Next session

Proposed Session 04 / Phase 4 **only after explicit authorization and D06-D07
review**: commission/slippage, equity-based returns and risk metrics, closed
trade statistics, and comparable buy-and-hold results. Review fee rounding and
affordability, annualization, undefined metrics, risk-free convention, trade
definitions, and identical evaluation/cost settings for the benchmark.
Acceptance: independent fee/metric references, meaningful edge cases, and all
existing regressions. No Phase 4 source exists. Stop after Phase 3.
