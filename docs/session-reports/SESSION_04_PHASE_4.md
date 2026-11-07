# Session 04 - Phase 4

Date: 2026-11-01 (Asia/Calcutta).

## A. Session overview

**Objective:** commission/slippage, equity and trade analytics, controlled
buy-and-hold comparisons. **Status: COMPLETE.** Session 04 explicitly approved
D06-D07 and preserved the earlier execution/strategy contracts. Read the
required project records, Phase 2-3 reports, actual models/engine/strategies
and tests; verified the baseline before implementation. Phase 5 was not started.
This implementation/verification is AI-assisted; independent owner learning
remains work to do.

## B. What was implemented

Paths below are relative to repository root.

| File | Actual responsibility/change |
| --- | --- |
| `backend/src/quantlab/execution/costs.py` | Effective buy/sell prices and rounded flat commission |
| `backend/src/quantlab/execution/engine.py` | Cost validation, fee-aware integer sizing, affordability, fee-covering exits, net entry basis/realized P&L; version 1.2.0 |
| `backend/src/quantlab/analytics/models.py` | Immutable metrics with explicit absence reasons, equity/trade/report/comparison records |
| `backend/src/quantlab/analytics/equity.py` | `analyze_equity`: returns, annualization, drawdown, sample volatility, Sharpe and short/undefined cases |
| `backend/src/quantlab/analytics/trades.py` | `analyze_trades`: paired full trades, net P&L/counts/win rate/mean, separate open position |
| `backend/src/quantlab/analytics/benchmark.py` | `analyze_simulation`, `compare_with_buy_and_hold`; same data/configuration and defined return differences |
| `backend/src/quantlab/analytics/__init__.py` | Public analytics API |
| `backend/tests/test_analytics.py` | 43 cost/metric/trade/benchmark reference and edge cases |

Updated execution exports/docstring, two obsolete positive-cost rejection cases
in `test_execution.py` and one in `test_strategies.py` to reject invalid costs
instead. All zero-cost reference assertions remain. Added analytics API docs;
updated execution docs, dated D06-D07 amendments, roadmap, status, and README.
Phase 1 source/tests, strategies, fixtures, package configuration and dependencies
are unchanged. No parallel engine, service, or fourth strategy was added.

## C. Why this functionality exists

Gross price gains can conceal execution costs and incomplete positions.
Explicit fills and fee-inclusive cash flows explain net profitability; metric
definitions and absence reasons prevent fabricated statistics. The benchmark
compares two runs under identical assumptions rather than incompatible periods.

## D. Integration with the existing codebase

Existing importer -> same strategy/next-open engine -> `SimulationResult` ->
separate equity/trade analytics. The benchmark calls that engine twice with
identical data, dates, capital, costs and terminal treatment. Each rule still
sees only completed selected-window closes. No HTTP, persistence, frontend,
provider, audit findings, sweep, or optimization dependency enters the core.

## E. Technical concepts to study

- **Money versus statistics:** Decimal maintains fill/cash/trade accounting;
  exact equity ratios convert to float at the documented statistical boundary.
- **Composition and state:** existing orders/fills feed pure analytics; a single
  entry record pairs with the next full exit; open state remains separate.
- **Validation and explicit absence:** `Metric` rejects nonfinite values and
  unexplained absence. Invalid data fails; mathematically undefined metrics
  retain a reason instead of a fabricated zero.
- **Numerical stability:** log/expm1 annualization, exact ratio returns, sample
  deviation, fee/price/notional rounding at explicit boundaries; no display
  rounding feeds accounting or analytics.

Independently understand/recreate **`_execute`** and **`analyze_equity`** after
studying their reference tests. Do not claim this AI-assisted implementation
or copying it as independent work.

## F. Financial and quantitative concepts to study

For b basis points, buy price = open*(1+b/10000), sell price =
open*(1-b/10000), rounded to six decimals. Reserve the cents-rounded fee before
floor-sizing a buy; rounded debit = rounded notional + fee. Net exit credit =
rounded sale notional - fee. A closed trade's net P&L = exit credit - entry
debit, including both fees and slipped prices. Open P&L uses final mark minus
entry debit without a hypothetical final sale fee.

D07 formulas implemented: r[t]=E[t]/E[t-1]-1; cumulative=E[end]/E[0]-1;
annual=(E[end]/E[0])^(365.25/calendar_days)-1;
maximum drawdown=max(1-E[t]/running_peak[t]), including E[0];
volatility=sample_std(r)*sqrt(252);
Sharpe=sqrt(252)*mean(r-rf_daily)/sample_std(r-rf_daily), with
rf_daily=(1+rf_annual)^(1/252)-1 and rf_annual > -1. No first zero return is
prepended. Win rate counts positive net closed trades/all closed trades,
including break-even trades in the denominator.

Price-return only, excluding dividends and other unmodeled corporate actions.
365.25 days/252 sessions are conventions; short annualization is extrapolation.
Source declarations, coverage, and opening liquidity remain unverified. These
statistics and comparisons do not establish significance or predictability.

## G. Engineering decisions and tradeoffs

- Standard library only. Separate small cost/equity/trade/benchmark modules;
  retain the verified engine, strategy rules and result schema.
- Supported cost precision is six meaningful fractional places. Fee is rounded
  separately to cents; fill price to six decimals; notional to cents. Unsupported
  precision/ranges fail rather than silently change a configuration.
- A sale whose rounded proceeds equal its fee may fill for zero net credit;
  proceeds below fee or price rounded to zero reject without a fee or mutation.
  Existing cash/share bounds keep even slipped-price products within precision 28.
- Two returns are necessary for sample volatility/Sharpe. No trades means
  absent win rate/mean. Zero variance means absent Sharpe. Preserve an undefined
  interval after zero equity; do not discard it to create a better sample.
- Numerical overflow gives absent metrics with reasons; invalid/negative
  equity is an error. Benchmarks reject diagnostic exits and report differences
  as strategy-minus-benchmark return fractions, not significance estimates.

## H. Testing and verification

Actual repository-root PowerShell commands, approved outside the sandbox due
to its previously established pytest temporary-directory access limitation:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-phase4-baseline
& '.\.venv\Scripts\python.exe' -m pytest -q backend/tests/test_analytics.py --basetemp=.venv/pytest-phase4-analytics
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-phase4-full
& '.\.venv\Scripts\python.exe' -m pip check
& '.\.venv\Scripts\python.exe' --version
```

Baseline **265 passed in 6.30s**. Initial new suite **41 passed in 0.81s**;
after adding valid negative risk-free and unavailable benchmark-difference
coverage, full suite **308 passed in 6.72s**: 162 data, 58 execution, 45 strategy,
43 new Phase 4 cases. All executed test runs exited 0; no failures observed.
Legacy nonzero-cost rejection expectations changed only as explicitly approved.
All prior zero-cost financial/timing/information-boundary references pass.
`pip check`: **No broken requirements found.** Python **3.15.0**, pytest 9.2.0;
no dependency was added or installed.

Independent reference evidence in `test_analytics.py`:

- $1,000, 100 bps, $2 commission: 9 shares at $101; $909 notional, $911 debit,
  $89 cash. Sell at $108.90: $980.10 gross, $978.10 credit, $1,067.10 cash,
  **+$67.10 net closed-trade P&L**.
- [.335 price, .005 configured fee] uses half-up .01 fee: $1.01 buys 2 shares
  with .33 residual; $1.02 buys 3 with zero residual after rounding. Six-decimal
  slippage rounding, fee exhaustion, zero-volume and final expiry charge no
  rejected/expired commission; unaffordable/zero-price exits preserve holdings.
- Equity [100,110,99] gives returns [.1,-.1], cumulative -.01, drawdown .1,
  annualized sample volatility sqrt(5.04), default Sharpe zero. Other cases:
  valid positive/negative risk-free, flat/constant returns, one/two valuations,
  calendar-day annualization, zero equity, overflow and invalid inputs.
- Full-trade examples classify +3/-3/0 as one win/loss/break-even, win rate 1/3,
  mean zero. An open gain remains outside closed statistics.
- Identical-window/cost benchmark references: buy-and-hold equity $2,384.26,
  SMA $2,168.26, momentum $1,301.58; return differences -.216 and -1.08268.
  Repeated comparisons agree; unavailable annual differences retain reasons.
  Strict JSON checks reject any accidental NaN/Infinity in tested reports.

Installed-package smoke inside the sandbox succeeded: engine 1.2.0 with the
existing synthetic fixture/$2/100 bps retained 9 shares, $68.55 cash, $1,000.05
equity and no closed trade. SMA-minus-buy-and-hold cumulative difference was
-.00005 on that separate fixture. Standalone metric smoke printed returns
[.1,-.1], cumulative -.01, drawdown .1, volatility 2.244994432064365, Sharpe 0.

Final inline document/source audit **PASS**: 46 project files, 23 Python syntax
checks, 42 local links/anchors, UTF-8/LF/trailing whitespace, Git whitespace
including untracked files, A-L/questions, phase consistency, no future-phase
modules, and preserved placeholders. No source changed after the 308-test run.
No real market data or profitability claim was produced.

## I. Complexity and performance

Cost calculation adds O(1) work per attempted fill under bounded numbers.
For N valuations/F fills, analytics O(N+F) time and O(N+F) working/output space;
the separate passes remain linear. Benchmarking executes and analyzes two
bounded simulations with the same engine. No growing-prefix copies, cache,
vectorization, parallelism, or runtime benchmark. Pytest duration is not
simulation/analytics throughput. Arbitrary-size input arithmetic has operand
bit-length cost; current engine outputs use documented bounded precision.

## J. Interview preparation

Five technical questions:

1. Why reserve rounded commission before floor-sizing and then recheck the
   rounded debit?
2. Why must entry basis and realized P&L use complete cash debits/net credits?
3. Where does Decimal cross to float, and which values never cross that boundary?
4. How do explicit absent metrics differ from invalid inputs and zero metrics?
5. How does the benchmark guarantee comparable inputs without another engine?

Three finance questions:

1. How do adverse slippage and flat commission produce $67.10 net P&L in the
   reference, and why is it less than the gross price gain?
2. Why does +10% then -10% lose 1% despite mean daily return zero?
3. Why are an unclosed gain, a zero-variance Sharpe, and short annualization
   inappropriate evidence of a statistically reliable strategy?

Independent exercise: write a standalone maximum-drawdown function for positive
initial/nonnegative later Decimal equity. Include the initial peak; hand-test
[100,110,99], [100,90,80,95], and a flat curve. Explain O(N) time/O(1) state.
Complete it without copying production code, then compare outputs.

## K. Current project status

Phases 0-4 COMPLETE; 5-10 NOT STARTED and unauthorized. No known in-scope
failure remains in executed checks. Limits: simplified flat/bps costs,
three built-ins, bounded accounting, selected-window warm-up, unverified data
declarations/calendars/actions/liquidity, explicit float/short-sample limits,
Python 3.12 untested, sandbox pytest restriction. No auditor, sweep, optimizer,
database, HTTP, UI, provider, or new strategy was added. Files remain
unstaged/uncommitted; no branch/remote change was made.

## L. Next session

Proposed Session 05 / Phase 5 **only after explicit authorization**: supported
integrity checks on existing inputs, configurations, timing/accounting traces,
and reproducibility records, with findings/evidence/severity and explicit
assessment limits. Test deliberate defects and valid references. Distinguish
checkable invariants from unverified corporate actions, source revisions,
survivorship, calendar completeness and arbitrary-code look-ahead claims.
No Phase 5 module exists. This report is readiness evidence, not permission.
Stop after Phase 4.
