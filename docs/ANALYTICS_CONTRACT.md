# Phase 4 analytics and benchmark API

Metric definitions and approved edge cases live in
[D07](DECISIONS.md#d07---metric-definitions-and-reference-conventions).
Execution/cost usage lives in [EXECUTION_CONTRACT.md](EXECUTION_CONTRACT.md).
No HTTP, persistence, frontend, external provider, or auditor is required by
analytics. The separate [audit API](AUDIT_CONTRACT.md) can examine
`report.simulation`; it does not independently recalculate all statistics.
The [experiment coordinator](EXPERIMENT_CONTRACT.md) reuses these reports for
bounded comparisons and training selection. Indicator-only warm-up produces
no valuation rows, so it never enters these return/statistic calculations.

```python
from decimal import Decimal
from quantlab.data import load_dataset
from quantlab.execution import ExecutionSettings, simulate
from quantlab.strategies import SMACrossover
from quantlab.analytics import analyze_simulation, compare_with_buy_and_hold

dataset = load_dataset(
    "backend/tests/fixtures/synthetic_daily.csv",
    "backend/tests/fixtures/synthetic_daily.metadata.json",
)
settings = ExecutionSettings(commission_per_fill_usd=Decimal("2"), slippage_bps=Decimal("100"))
simulation = simulate(dataset, Decimal("1000"), SMACrossover(1, 2), settings)
report = analyze_simulation(simulation, annual_risk_free_rate=Decimal("0"))
print(report.equity.cumulative_return.value, report.equity.sharpe_ratio.reason)
print(report.trades.closed_trades, report.trades.open_position)
comparison = compare_with_buy_and_hold(dataset, Decimal("1000"), SMACrossover(1, 2), settings)
print(comparison.cumulative_return_difference)
```

The fixture is synthetic and has a zero-volume execution bar; example outputs
are not market evidence. Rejected orders can leave a run flat. Full simulation
warnings/settings remain available in `report.simulation`.

## Functions and records

| Function | Result |
| --- | --- |
| `analyze_equity(dates, equities, *, annual_risk_free_rate=Decimal("0"))` | `EquityMetrics`; strictly ascending date labels and matching nonempty finite Decimal equity. One valuation is allowed for explicit short-sample handling; initial equity must be positive, later values nonnegative |
| `analyze_trades(fills, last_close)` | `TradeStatistics`; chronological complete-entry/exit engine fills, positive finite Decimal final close |
| `analyze_simulation(simulation, *, annual_risk_free_rate=Decimal("0"))` | `PerformanceReport(simulation, equity, trades)`; consumes a successful engine result without recomputing execution |
| `compare_with_buy_and_hold(dataset, initial_capital, strategy, settings=None, *, annual_risk_free_rate=Decimal("0"))` | `BenchmarkComparison`; two reports plus strategy-minus-benchmark cumulative and annualized return differences. Diagnostic exit settings are rejected |

Invalid inputs raise `AnalyticsError` (ValueError). Dataclasses do not
authenticate supplied simulation history or source truth. Use validated
importer/engine outputs and the separate auditor for its documented checks.

`EquityMetrics.daily_returns` contains N-1 `DailyReturn(session, metric)`
observations; the first close adds no artificial zero. It also includes
cumulative/annualized return, nonnegative maximum drawdown, annualized sample
volatility, Sharpe, the supplied annual risk-free rate, annualization warning,
and assumptions. Return metrics/differences use fractions, not percentages.

Each `Metric` has `value` and `reason`: a finite value with no reason, or `None`
with an explanatory reason. Examples: `no_closed_trades`,
`insufficient_return_observations`, `zero_return_variance`,
`insufficient_evaluation_period`, `previous_equity_zero`, and numerical range
failures. Never drop an undefined interval to manufacture a statistical sample.
When either annualized return is unavailable, its benchmark difference is too.

`TradeStatistics` retains closed-trade records and count/win/loss/break-even
counts, win rate, mean net closed-trade P&L, and optional `OpenPosition`.
Each closed trade stores entry debit, net exit credit, quantity, linked order
IDs/sessions, and exact net P&L. Open position stores entry debit, quantity,
last close, exact mark, and unrealized P&L; it is not a completed trade.

## Numerical boundary and limits

Cash, fill fees/notionals, and individual trade P&L remain Decimal. Mean net
P&L uses Decimal precision 28 and is not display-rounded. Exact ratios of
Decimal equity convert to Python float for returns/statistics/powers; use
reasonable numerical tolerances. Overflow or an unrepresentable risk-free
rate gives an absent metric with a reason. No NaN/Infinity is emitted.
No display-rounded value feeds another calculation.

Sharpe uses effective annual risk-free Decimal > -1, default zero, converted
to the constant daily rate. It requires at least two returns and nonzero
sample deviation. Annualized volatility uses sample deviation and 252;
annualized return uses actual calendar days and 365.25. A period shorter than
365.25 days is flagged as extrapolation. These are conventions, not calendar
verification or statistical significance. Dividends and other unmodeled
corporate actions remain excluded.

For N valuations and F fills, analysis is O(N+F) time and O(N+F) output/working
space with bounded numeric inputs. Cost calculations add O(1) per attempted
fill. Benchmarking runs the same engine twice and analyzes both results;
no sweep, caching, or concurrency inside analytics. The separate experiment
layer coordinates bounded repetitions. No throughput benchmark ran.
Evidence: [Session 04](session-reports/SESSION_04_PHASE_4.md).
