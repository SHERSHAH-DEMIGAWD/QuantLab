# Execution and strategy API

Implemented independent Python library; no HTTP, persistence, provider, or
frontend. Financial policy lives in D04-D06 and their dated amendments in
[DECISIONS.md](DECISIONS.md). All examples below use invented observations.

```python
from decimal import Decimal
from quantlab.data import load_dataset
from quantlab.execution import ExecutionSettings, SimulationError, simulate_buy_and_hold

dataset = load_dataset(
    "backend/tests/fixtures/synthetic_daily.csv",
    "backend/tests/fixtures/synthetic_daily.metadata.json",
)
result = simulate_buy_and_hold(dataset, Decimal("1000.00"))
print(result.final_cash, result.final_shares, result.final_equity)
print(result.orders, result.fills, result.warnings)
```

Use `Decimal` inputs, including cost settings; float/int/string cash
requests fail. Invalid requests raise `SimulationError` (a `ValueError`) before
execution returns any result. Individual execution rejections are successful
simulation outcomes recorded in `orders`, with no fill or portfolio mutation.
Use the Phase 1 importer: dataclass construction or numeric checks cannot
authenticate input hashes or establish source truth.

## Phase 3 strategy selection

```python
from quantlab.execution import simulate
from quantlab.strategies import BuyAndHold, SMACrossover, TimeSeriesMomentum

result = simulate(dataset, Decimal("1000.00"), SMACrossover(fast_window=2, slow_window=3))
result = simulate(dataset, Decimal("1000.00"), TimeSeriesMomentum(lookback=2, threshold=Decimal("0.1")))
result = simulate(dataset, Decimal("1000.00"), BuyAndHold())
```

`simulate(dataset, initial_capital, strategy=None, settings=None)` uses
buy-and-hold by default. `simulate_buy_and_hold` is a compatibility wrapper
through the same engine. Results retain the immutable strategy configuration.
Invalid configuration construction raises `StrategyError` (a `ValueError`);
unsupported strategy arguments to `simulate` raise `SimulationError`.

| Configuration | Parameters and close decision |
| --- | --- |
| `BuyAndHold()` | LONG while flat, HOLD while invested; preserves fresh intents after rejected buys |
| `SMACrossover(fast_window, slow_window)` | Positive integer windows, excluding bool, fast < slow. HOLD until slow closes; LONG if fast average > slow average, FLAT if below, HOLD if equal. Target state, including initial bullish entry, not a crossing-event detector |
| `TimeSeriesMomentum(lookback, threshold=Decimal("0"))` | Positive integer lookback excluding bool; finite Decimal threshold. HOLD until L+1 closes; LONG if close[T]/close[T-L]-1 > threshold, otherwise FLAT, including equality |

Each run creates a fresh rule implementing
`on_close(session: date, close: Decimal, shares: int) -> Target`. Only the
completed current close and current position are supplied; rolling queues
contain previously supplied closes. Rules receive no future data or mutable
cash/order state. `create_rule` accepts only the three built-in configurations;
its returned stateful rule is consumed in chronological order once per session.
The simulator always constructs its own fresh rule; it accepts no callback.

SMA compares integer-microunit rolling sums by cross multiplication. Momentum
compares exact ratios to the Decimal threshold; it does not round a quotient
into a false threshold equality. These exact signal calculations do not change
precision-28 Decimal cash accounting. By default warm-up begins inside the
selected window. Engine 1.3.0 also accepts an explicitly separated prior
indicator-only interval, described below and used by
[train/test experiments](EXPERIMENT_CONTRACT.md).
LONG while long and FLAT while flat create no orders. HOLD leaves the current
position unchanged. No target can execute at the same close that generated it.

## Settings and validation

| Setting | Behavior |
| --- | --- |
| `start_date`, `end_date` | Optional inclusive `datetime.date` bounds; absent dates need not be sessions. At least two observed bars must remain. Start flat inside the window; no pre-window position or fill. Result dates are actual first/last evaluated sessions |
| `warmup_start_date`, `warmup_end_date` | Optional paired inclusive dates, ordered strictly before an explicit `start_date`; require at least one observed warm-up bar. Feed only indicator state, with flat shares and discarded targets. No warm-up decisions, orders, pending intents, fills or valuations. Defaults None |
| `commission_per_fill_usd` | Default `Decimal("0.00")`; finite nonnegative Decimal within runtime cash bound, up to six meaningful fractional places; rounded to cents per fill |
| `slippage_bps` | Default `Decimal("0")`; finite Decimal 0 <= b < 10000, up to six meaningful fractional places; adverse to buys and sells |
| `acknowledge_unverified_coverage` | Boolean, default false; must be true for `local_file`, even with declared complete coverage |
| `sell_after_session` | Buy-and-hold only; optional exact observed evaluation date; single diagnostic FLAT decision at its close, then HOLD forever. Rejected exit stays rejected. Combining it with SMA/momentum fails |

D04 eligibility applies to synthetic and real inputs: explicitly consistent
unadjusted OHLC, raw volume, no reported split, and explicit split evidence.
Metadata covers the full imported interval; selecting dates cannot bypass an
unknown/present split declaration. The engine preserves import warnings.
No exchange calendar or corporate-action verification exists.

`validate_simulation_request(dataset, initial_capital, strategy, settings)`
performs the same preflight without trading and returns `(evaluated_bars,
warmup_bars)`. Prices consumed in either interval obey the same numeric/OHLC
rules. No history outside the two requested intervals is fed to a rule. Test
portfolio state is created after warm-up; its first close has fresh cash and
zero shares, and its first possible fill follows that close.

Initial capital and selected OHLC must fit the supported bounds in the
[D05 amendment](DECISIONS.md#d05-amendment---approved-execution-and-fresh-intents-2026-11-01).
Input validation rejects excess precision rather than silently rounding it.
Arithmetic uses an isolated Decimal context regardless of caller settings.
Integer microunits implement floor sizing without a division-rounding error.
Repeated entries also enforce the runtime cash/share envelope in the
[D05 extension](DECISIONS.md#d05-amendment---repeated-entry-numeric-envelope-2026-11-01).
Unsupported growth fails the run explicitly, with no partially returned result.
Cost formulas, supported precision, and rounding are fixed by the
[D06 amendment](DECISIONS.md#d06-amendment---approved-phase-4-costs-2026-11-01).
Size buys after reserving the rounded fee, and recheck rounded affordability.
Rejected/expired orders have no fill and no commission. Sale proceeds must
cover the fee; an effective sell price rounded to zero rejects the order.

## Result records

Frozen dataclasses and tuples keep successful results immutable and comparable.
`engine_version=1.3.0` identifies explicit indicator-only warm-up support;
package version remains `0.1.0`.

| Record/field | Contents |
| --- | --- |
| `SimulationResult` identity/configuration | Dataset ID, source/metadata hashes, effective metadata, actual evaluation range, initial capital, requested settings, immutable strategy configuration, engine version |
| `warmup_start`, `warmup_end`, `warmup_bars` | Actual observed indicator-only history bounds/count; None, None, 0 without requested warm-up; never part of evaluation traces or metrics |
| `decisions` | One per evaluated close: session, LONG/FLAT/HOLD target, currently available cash and shares; the decision function receives no future bars or prices |
| `orders` | Sequential ID, target/side, decision and eligible session, reserved buy budget or full sell quantity, terminal status/outcome session, reason, attempted base/effective price |
| `fills` | Exactly one record per filled order, linked by order ID: actual session, quantity, base open, six-decimal slipped price, rounded notional/commission, signed net cash change; slippage configuration remains in result settings |
| `valuations` | Each close's cash, integer shares, source close, exact market value/equity, rounded entry cost basis, realized and unrealized P&L |
| Final accounting | Cash, shares, exact equity, realized P&L, unrealized P&L; open positions retained |
| `assumptions`, `warnings` | Price-return/dividend exclusion, explicit cost model, timing, rounding, corporate-action/session/liquidity limits, diagnostic-mode notice if enabled |

Orders begin pending and end FILLED, REJECTED, or EXPIRED. Rejections include
`zero_volume`, `insufficient_capital`, `nonpositive_effective_price`,
`proceeds_below_fee`, and defensive invalid-state reasons;
expired orders use `end_of_window`. A final-close order has no eligible date,
no attempted price, and no fill. Buy-and-hold may create a fresh intent at a
rejection session's close; rejected orders never become filled later.

At each session: execute the prior pending intent at the open; update cash and
holdings; record closing equity; evaluate the decision; queue a later order.
No same-close fills, partial fills, forced final sales, or liquidity claims.
Equity is cash plus shares times close, without rounding the mark. Unrealized
P&L is marked holdings minus rounded entry debit including commission; realized
P&L is net sale credit minus that debit. Open marks do not deduct hypothetical
exit costs. [Analytics](ANALYTICS_CONTRACT.md) consume these records separately.

For the independent test reference: $1,000 -> 9 shares at $103 -> $73 cash;
a $105 close gives $1,018 equity. A later full sale at $110 gives $990 proceeds,
$1,063 cash, zero shares, and $63 realized P&L. The separate README fixture
has different prices; do not expect these exact values from that fixture.

Preflight scans N imported bars; simulation processes W warm-up and M evaluation
bars in order. Time O(N + W + M), auxiliary space O(W + M) bar references and
O(M) output; no prefixes are repeatedly copied. For W+M closes, buy-and-hold
uses O(1) signal state; SMA uses O(min(W+M, slow_window)) and momentum
O(min(W+M, lookback+1)). Each does O(1)
updates per close for fixed-size numeric inputs/parameters; arbitrary-precision
integer cost grows with parameter/threshold bit length. No throughput benchmark
has been performed. Evidence: [Session 02](session-reports/SESSION_02_PHASE_2.md)
and [Session 03](session-reports/SESSION_03_PHASE_3.md); costs are verified in
[Session 04](session-reports/SESSION_04_PHASE_4.md). Warm-up regression evidence:
[Session 06](session-reports/SESSION_06_PHASE_6.md).
