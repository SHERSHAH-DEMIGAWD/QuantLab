# Decision log and initial technical contracts

Created 2026-11-01 (Asia/Calcutta). Status meanings:

- **ESTABLISHED**: follows the user's charter or is a reversible Phase 0
  foundation choice within the current authorization.
- **PROPOSED**: a reviewable default for a later phase, not implemented or
  independently approved. Authorizing a phase does not silently resolve an
  objection to one of its financial assumptions.
- **DEFERRED**: select only when the relevant phase has concrete requirements.

Keep these initial entries. Record later changes as dated amendments naming the
superseded entry, consequences, and authorization when required. Verification
evidence belongs in the session reports; proposals are not working features.

## D01 - Scope, delivery, and session boundaries

**ESTABLISHED, 2026-11-01.** The [charter](PROJECT_CHARTER.md) governs scope.
There are 11 phases, 0-10; this session authorizes Phase 0 only. The roadmap is
a plan, not permission to implement later phases. Persist reports, stop at
phase boundaries, and require evidence plus human learning tasks for completion.

Alternative: implement the entire platform now. Rejected because it would
defeat the owner's comprehension and phase controls.

## D02 - Modular monolith and delayed dependencies

**ESTABLISHED, 2026-11-01.** Establish empty backend, fixture, frontend, and
local-data locations. Create responsibility-specific modules only when needed.
Use Python domain logic independent of HTTP, database, and React. Prefer
standard-library CSV, dates, dataclasses, Decimal, and hashing for initial work;
pytest is the first planned development dependency. Pandas/NumPy need a concrete
benefit, not just inclusion in the preferred stack.

SQLite and a small access layer arrive in Phase 7. FastAPI/Pydantic validate the
HTTP boundary then; they do not own simulation logic. React/TypeScript arrive
in Phase 8. Defer chart library, HTTP client, schema tooling, exact dependency
versions, and provider choice. No package manifests, installations, migrations,
empty service classes, or application endpoints are necessary in Phase 0.

Python 3.12 is preferred by the charter. Local inspection found only Python
3.15.0 via `py --list-paths`. Phase 1 must choose a stable interpreter, create
an isolated environment, record actual versions, and verify its dependencies
before claiming compatibility. No interpreter was installed or changed here.

Alternatives: use pandas immediately, prebuild all layers, or introduce services.
These add concepts or dependencies before demonstrating a need. A future
measured problem can justify revisiting the decision.

### D02 amendment - verified Phase 1 environment, 2026-11-01

**ESTABLISHED within Session 01 authorization.** Inspection found one executable
interpreter: CPython 3.15.0, `releaselevel=final`; no Python 3.12 executable was
available. The Python314 directory contains no interpreter. Select the existing
3.15 executable for `.venv`, retaining Python >=3.12 as the package requirement.
Only 3.15 compatibility was actually verified. pytest 9.2.0, editable package
installation, and the offline tests work there. No interpreter or machine-wide
setting was installed/changed. The standard library is the only runtime
dependency; pytest is the test dependency; setuptools builds the package.
Sandbox temporary-directory ACL failures required approved execution outside
the sandbox for setup/tests, not application permission changes. Evidence and
exact commands are in Session 01.

## D03 - Local historical-data contract v1

**PROPOSED for review before Phase 1, 2026-11-01.** Import one UTF-8 CSV
(optional BOM) plus an explicit JSON metadata sidecar. Imports stay local;
no provider request, network lookup, database, API, or backtest is involved.

### CSV and validation

| Field | Initial contract |
| --- | --- |
| Header | Exactly `date,open,high,low,close,volume`; one instrument; no adjusted-close substitution |
| `date` | Exact `YYYY-MM-DD`, valid calendar date, interpreted as the exchange session label in `America/New_York`; not midnight UTC or the user's local date |
| OHLC | Positive, finite plain decimal numbers, at most six meaningful fractional digits; no separators, NaN, infinity, or scientific notation |
| `volume` | Nonnegative integer share units; zero is allowed with a warning; fractional, missing, or negative values fail |
| Ordering | Normalize to ascending date and report whether input was reordered; no implicit resampling |
| Duplicates | Reject every duplicate date, even identical rows; identify original row numbers |
| Consistency | `low <= min(open, close) <= max(open, close) <= high` |
| Missing values | Reject missing fields or rows with blank values; never fill, interpolate, or silently drop |
| Schema | Reject duplicate/unexpected/missing columns and malformed row widths; error messages name the field and source row |
| Empty input | Reject empty/header-only files; a one-row dataset may import but cannot support a next-session simulation |

Whitespace around header and field values is stripped deterministically and
reported as normalization if present. Internal blank data records fail. Use
explicit decimal parsing rather than binary floating point for price validation.
Validation is atomic: invalid input produces no usable dataset. Diagnostics may
be capped at 100 errors, with a truncation indicator; the cap must never turn an
invalid import into a successful one. Reject invalid metadata with field paths.

### Metadata and identity

Required supplied metadata:

| Field | Meaning |
| --- | --- |
| `contract_version` | Integer `1` |
| `symbol`, `exchange` | Explicit identity/venue label; not inferred from filename |
| `currency`, `frequency`, `session_timezone` | `USD`, `1d`, `America/New_York` |
| `source_kind` | `synthetic` or `local_file` |
| `source_name`, `source_reference` | Dataset author/provider and traceable locator or description; no fabricated provenance |
| `usage_note` | Supplied permission/license information, or explicit `unknown`; this is a declaration, not legal verification |
| `adjustment_basis` | `unadjusted`, `split_adjusted`, `total_return_adjusted`, or `unknown` |
| `ohlc_basis_consistent` | `true`, `false`, or `unknown`; `false` is rejected |
| `volume_basis` | `raw`, `split_adjusted`, or `unknown`; independent of OHLC declaration |
| `split_status`, `split_evidence` | `none_reported`, `present`, or `unknown`, plus evidence or an explicit statement of uncertainty for the supplied interval |
| `session_coverage` | `declared_complete` or `unknown`; a source assertion, not an automatic completeness certificate |

Record the imported date range, row count, validation issues, normalization
actions, importer version, and original source SHA-256. Reject unsupported
contract versions. Unknown metadata keys fail clearly so misspellings do not
silently become settings. Synthetic fixtures must identify their invented
prices and volumes; they are not historical market observations.

Compute `metadata_sha256` from canonical JSON of the validated supplied metadata:
UTF-8, sorted keys, compact separators, no NaN, and no import timestamp. Define
`dataset_id` as the SHA-256 of canonical JSON containing `contract_version`,
`source_sha256`, and `metadata_sha256`. Store all three values. This identifies
exact original CSV bytes and interpretation, not economically equivalent data:
different line endings or row order intentionally give a different source ID.
Do not include machine paths or import time in deterministic identity. Hashes
identify supplied inputs; they do not prove source truth or permission.

### Sessions and adjustment limitations

Report intervals between observed dates as calendar gaps with coverage
**unverified**. Do not call each absent calendar date a missing bar. Weekends,
holidays, early closes, suspended trading, and missing source records require
different interpretations. Phase 1 introduces no exchange-calendar library and
makes no automatic session-completeness claim. A future authoritative schedule
must be versioned before it can support stronger checks.

The NYSE publishes exchange holidays and early closes; this supports the need
to distinguish calendar dates from sessions, not a claim that this importer has
implemented a calendar. [NYSE hours and calendars](https://www.nyse.com/trade/hours-calendars)
(consulted 2026-11-01).

Ingest coherent adjusted data with an explicit basis and warnings, but never
combine adjusted close with unadjusted open/high/low. Mixed or mislabeled prices
cannot always be detected numerically; the source declaration remains a limit.
Unknown basis may be retained for inspection but is ineligible for simulation.

Alternative: silently clean a loosely specified CSV or auto-adjust it. Rejected:
that hides errors and introduces unsupported financial transformations.

### D03 amendment - approved Session 01 contract, 2026-11-01

**ESTABLISHED for Phase 1 by explicit user authorization.** The original D03
above is preserved as history. These amendments supersede its required metadata
list and refine import limits; the other CSV/identity rules remain in force.

- Required supplied fields: `contract_version`, `symbol`, `exchange`,
  `currency`, `frequency`, `session_timezone`, `source_kind`, `source_name`,
  `adjustment_basis`.
- Optional fields `source_reference`, `usage_note`, `ohlc_basis_consistent`,
  `volume_basis`, `split_status`, `split_evidence`, and `session_coverage` each
  default to the string `unknown`. Explicit nulls and wrong types fail.
  Consistency accepts JSON `true`, `false`, or the string `unknown`; `false`
  fails. Omitted split status never becomes `none_reported`. Declarations do
  not verify source truth, absence of splits, usage rights, or coverage.
- Canonical metadata includes all effective validated fields and defaults.
  Omitting an optional field and explicitly supplying `unknown` have identical
  metadata hashes. Unknown keys and unsupported schema versions still fail.
- Maximum CSV size is **10 MiB (10,485,760 bytes)**, including any BOM.
  Read at most the limit plus one byte; reject excess with `input_too_large`.
- Retain at most **100 diagnostics** per failed import; count further issues
  and set a truncation flag. No failing import returns a dataset. Warnings
  summarize zero-volume rows and limitations rather than issuing one per row.
- Importing adjusted/unknown data preserves its declarations and warnings.
  Phase 1 has no simulation-eligibility decision or corporate-action model;
  D04 remains a proposal for review before Phase 2. This supersedes the earlier
  D03 sentence assigning eligibility to unknown adjustment data.

Rationale: keep input validation strict while representing unavailable evidence
honestly. The output supports inspection without inventing financial assurance.
No phase beyond 1 is authorized.

## D04 - Corporate actions and simulation eligibility

**PROPOSED before Phase 2, 2026-11-01.** Begin execution with clearly synthetic,
event-free fixtures. For the initial real-data simulation model, require
unadjusted, consistently based OHLC, `volume_basis=raw`, and documented
`split_status=none_reported` for the entire selected window. A known split or
unknown split status blocks a run under this model. A declaration is evidence
provided by the user/source, not automatic verification that no split occurred.

Cash dividends, reinvestment, interest, taxes, symbol changes, and delisting
proceeds are not modeled. Label all such output as a price-return simulation
excluding dividends, never total shareholder return. An action or data issue
that invalidates the window must not be silently bypassed. Real-data runs also
require visible acknowledgment of unverified session coverage until a reliable
calendar/completeness check exists; fixtures explicitly define their sessions.

A split changes share units as well as price; treating the price change alone
as a loss is unsound. [IBM explanation of split share units](https://www.ibm.com/investor/help/ibm-stock-splits-and-ibm-stock-dividends)
(publication reference updated 2026-11-03 after the original SEC link returned
HTTP 403). No split-processing implementation is proposed here.

This conservative default restricts usable real-data windows. Alternatives are
an explicit corporate-action ledger, or a consistently adjusted-price simulator
with clearly synthetic share units. The former adds scope; the latter cannot
claim historically executable integer share accounting. Neither is silently
selected. Review this tradeoff before implementing Phase 2. Import acceptance
in Phase 1 does not imply simulation eligibility or investment suitability.

### D04 amendment - approved Phase 2 eligibility, 2026-11-01

**ESTABLISHED by the user's Session 02 authorization.** Adopt D04's conservative
price-return model. Execution requires `unadjusted`, consistency `true`, raw
volume, `none_reported` splits, and nonblank/non-`unknown` split evidence.
Synthetic reference data explicitly asserts event-free sessions. Real-data
(`local_file`) runs additionally require the boolean coverage acknowledgment,
even with `session_coverage=declared_complete`. Warnings retain uncertainty;
none of these assertions independently proves coverage or corporate actions.

Metadata describes the whole imported interval. A subwindow cannot bypass a
`present`/`unknown` split declaration; import a separately supported event-free
window instead. This conservatism avoids pretending the sidecar contains dated
events. No corporate-action ledger or calendar was added. Output explicitly
excludes dividends and all other actions listed in the original D04.

## D05 - Daily execution and portfolio state

**PROPOSED before Phase 2, 2026-11-01.** These conventions resolve initial
engine ambiguities; they must become reference tests before implementation is
marked complete.

1. Start the selected evaluation window flat with positive finite cash in USD
   cents. Require at least two eligible session bars. No external cash flows.
2. At each bar's open, process at most one order intent from the preceding
   observed session. Then mark cash plus shares at this bar's close. Only after
   that close may the strategy inspect history through this bar and emit a new
   target of `LONG`, `FLAT`, or `HOLD`. Never expose tomorrow's bar to it.
3. Buy and hold emits `LONG` at the first evaluation close and otherwise holds.
   Its first possible purchase is the second evaluation session's open. Do not
   buy at the first open using knowledge of that day's close.
4. `LONG` while flat creates a budgeted market-buy intent: reserve the currently
   available cash as a maximum budget at decision time. At the next open,
   execution determines the largest affordable nonnegative integer quantity
   using that budget and the effective fill price plus commission. This is an
   explicit next-open budget-conversion model, not a precommitted share order.
   The next open influences fill sizing, never the strategy's decision.
5. `FLAT` while long sells the entire held quantity at the next open. `LONG`
   while already long, `FLAT` while flat, and `HOLD` create no new order.
   No pyramiding, rebalancing, partial positions from targets, or simultaneous
   conflicting orders. Residual cash after integer sizing remains cash.
6. Record `PENDING -> FILLED`, `PENDING -> REJECTED` with a reason, or
   `PENDING -> EXPIRED` at the window end. Quantity zero, insufficient funds,
   or a zero-volume execution bar rejects the order without fees; no automatic
   retry. Invalid prices fail preflight/run validation rather than permit fills.
   Sell proceeds must cover fees; otherwise reject without changing the holding.
7. An order fills once in full under this idealized model. A rejected order
   needs a fresh later signal. No volume participation or spread simulation;
   positive daily volume does not prove liquidity at the opening price.
8. The next observed row is only a proxy for the next tradable session when
   coverage is unverified. Flag that limitation. Never add a synthetic bar or
   automatically jump across a known missing required session.
9. No forced liquidation at the last close. Mark any open position to that
   close, show it separately, and expire final pending intents. Report realized
   and unrealized amounts separately. No extra final sale fee is invented.

Use Decimal arithmetic from source strings with precision 28. Proposed fill
prices are rounded to six decimal places using ROUND_HALF_UP; each fill's
notional and flat fee are rounded to USD cents with the same rule before cash
updates. Cash starts and remains in cents. Recheck affordability after rounding;
reduce the computed buy quantity if needed, never allow negative cash. Marked
equity uses unrounded `cash + shares * close`; round only its display. Numeric
range checks must reject values beyond this arithmetic model's safe precision.

Record decision session, earliest eligible session, actual fill session, target,
budget/quantity, base open, effective price, fee, outcome, and reason. Each fill
links to exactly one order. Invariants: cash >= 0; integer shares >= 0;
`equity = cash + shares * close`; no fill on/before its decision session.

Hand reference, not an executed simulation: starting cash $1,000; next open
$103; zero costs; quantity 9; cash $73. At a $105 close, equity is
`73 + 9 * 105 = $1,018`. The remaining $73 cannot buy a tenth share.

Alternatives include fixed quantity chosen at T's close (can reject on an
overnight gap), fractional shares, or same-close fills. The first is defensible
but different; the latter two violate initial scope/timing. A budgeted next-open
order needs explicit explanation because it idealizes actual order submission.

### D05 amendment - approved execution and fresh intents, 2026-11-01

**ESTABLISHED by the user's Session 02 authorization; original D05 retained.**
Adopt next-observed-open execution, budgeted integer sizing, cents accounting,
six-decimal fills, precision 28/ROUND_HALF_UP, unrounded closing marks, immediate
sale proceeds, and no final liquidation. Pending final-close orders expire.

Refine original item 3 and clarify items 6-7: buy-and-hold emits `LONG` at each
observed close while still flat, including the close of a session whose open
rejected a buy. Each such signal creates a **new order ID and intent** eligible
only at the following observed open. The rejected order remains terminal; it
is never retried. Once invested, buy-and-hold emits `HOLD` without further buys.
This also permits a fresh intent after insufficient capital. Each rejection
retains its reason. Session 02 explicitly tests this refinement.

Safe bounds selected within D05's numeric-range requirement: initial capital
USD 0.01..999,999,999.99; each selected OHLC price
0.000001..999,999.999999. Extra meaningful fractional digits fail rather than
round at input. These bounds limit the single entry to fewer than 10^15 shares
and its price products to 27 significant digits; cash-plus-mark fits precision
28. They apply to this single-entry engine; future repeat-entry strategies must
review bounds before reuse. Trailing decimal zeros are accepted.

Compute quantity as exact `floor(budget / effective_price)`, using integer
microunits; recheck the rounded cash debit. The raw notional cannot exceed the
reserved budget, even when cents rounding would hide that excess. Rounding is
visible: subcent prices may create small differences between exact marks and
cent-rounded cash debits/credits. No binary float enters cash accounting.

The optional `sell_after_session` is a single diagnostic FLAT decision on an
observed close, followed by HOLD forever, including after a rejected exit. It
tests full liquidation and rejection without introducing a strategy framework;
results using it are labeled diagnostic, not a buy-and-hold benchmark.
See [execution contract](EXECUTION_CONTRACT.md) and
[Session 02 evidence](session-reports/SESSION_02_PHASE_2.md). D06's zero costs
are enforced; nonzero/invalid cost inputs fail. Phase 3 is not authorized.

### D05 amendment - repeated-entry numeric envelope, 2026-11-01

**ESTABLISHED within Session 03's authorized re-entry support.** Keep initial
capital/price bounds and all timing, sizing, rounding, and zero-cost policies.
Extend the arithmetic review from a single entry to repeated entries: reject
a run explicitly if a proposed buy exceeds 999,999,999,999,999 shares or a
portfolio exceeds USD 999,999,999,999,999,999,999.99 cash. Check quantity before
notional multiplication and balances before valuation. With the existing
six-decimal price cap, products use at most 27 significant digits and cash plus
marked holdings fits precision 28. Do not truncate shares, cap a fill, round
away excess precision, or return a partial simulation. This adds a supported
range failure for new re-entry flows; Phase 2's supported results are unchanged.
The initial-capital cap does not limit earned sale proceeds to initial capital.

## D06 - Phased cost model

**ESTABLISHED sequence; PROPOSED formulas before Phase 4, 2026-11-01.**
Phase 2 must expose and record `commission_per_fill_usd=0` and
`slippage_bps=0`. Until Phase 4, reject nonzero cost requests rather than ignore
them. Its results are explicitly zero-cost simulations.

Phase 4 proposes a finite nonnegative flat USD commission per filled order,
charged once, and adverse slippage `b` with `0 <= b < 10000` basis points:

- Buy effective price: `open * (1 + b / 10000)`.
- Sell effective price: `open * (1 - b / 10000)`.
- Buy cash debit: rounded notional plus rounded commission.
- Sell cash credit: rounded notional minus rounded commission.

Apply D05 rounding and affordability. Rejections/expiry have no commission.
Fees cannot make cash negative. Display the effective configuration in every
result, including all zeros. No claim to reproduce a particular broker's fees,
liquidity, bid/ask spread, taxes, regulatory fees, or actual opening execution.

Alternative: per-share or percentage commissions and multiple slippage models.
Defer them; one flat fee and one basis-point adjustment teach the accounting
without a general cost framework. This resolves the charter's execution-cost
requirements arriving before its dedicated Phase 4 analytics work.

### D06 amendment - approved Phase 4 costs, 2026-11-01

**ESTABLISHED by the user's Session 04 authorization.** Adopt the proposed
flat commission and adverse bps formulas, retaining zero defaults. Inputs must
be finite nonnegative Decimal, with up to six meaningful fractional places;
commission is bounded by D05's runtime cash ceiling, and bps must be below
10,000 (largest supported value 9999.999999). Reject unsupported precision.
Round effective price to six decimals, fee/notional separately to cents, all
ROUND_HALF_UP. Preserve the supplied configuration and actual rounded fill fee.

Buy quantity is `floor((reserved cash - rounded fee) / effective price)`, or
zero if fee exhausts the budget. Respect the raw budget and recheck the final
rounded debit. Charge only filled orders. Sell the entire position only when
rounded gross proceeds cover the fee; equality permits a zero net credit.
An effective sell price rounded to zero rejects with
`nonpositive_effective_price`; proceeds below fee reject with
`proceeds_below_fee`. Neither rejection changes the position or incurs a fee.
No automatic retry or final liquidation is introduced.

Entry basis includes commission; realized P&L uses net sale credit minus full
entry debit. Slippage is already included in effective prices. Costs are
simplified research assumptions, not a brokerage/liquidity model. With adverse
buy slippage, effective prices may approach twice the source-price ceiling;
15-digit shares times a 13-digit effective price fit precision 28. Keep the
existing runtime envelope. Zero-cost economic results are unchanged.

## D07 - Metric definitions and reference conventions

**PROPOSED before Phase 4, 2026-11-01.** Let `E0` be initial cash at the first
evaluation close before any eligible fill. Daily closing equity is `Et`.
Use consecutive evaluated session closes, including flat days. Returns are
`rt = Et / E(t-1) - 1` for t >= 1; there is no artificial zero return prepended
to the statistical sample. Let `n` be the number of these return intervals.

| Metric | Definition and edge cases |
| --- | --- |
| Cumulative return | `Eend / E0 - 1` for positive E0 |
| Annualized return | `(Eend / E0) ** (365.25 / d) - 1`, where d is calendar days between initial and final valuation dates; unavailable for d <= 0 or insufficient endpoints; flag windows under one year as extrapolation; zero terminal equity gives -100% |
| Drawdown | `Dt = Et / max(E0,...,Et) - 1`; maximum drawdown reported as nonnegative `-min(Dt)`; include initial equity peak |
| Annualized volatility | Sample standard deviation of daily returns (`ddof=1`) times `sqrt(252)`; unavailable for fewer than two returns; 252 is a modeling convention, not a validated calendar count |
| Sharpe ratio | `sqrt(252) * mean(rt - rf_daily) / sample_std(rt - rf_daily)`, with constant effective annual `rf=0` by default and `rf_daily=(1+rf)**(1/252)-1`; require rf > -1; unavailable for fewer than two returns or zero deviation |
| Closed trade | One full entry and its full exit, since initial scope has no scaling; net P&L equals rounded exit proceeds minus rounded entry debit, including both fees |
| Win rate | Closed trades with net P&L > 0 divided by all closed trades; break-even trades stay in denominator; unavailable when there are no closed trades |
| Other trade statistics | Closed/winning/losing/break-even counts; mean net closed-trade P&L in USD; open position reported separately; each later statistic requires its own definition |

Use `null` plus an explanatory reason for undefined metrics, never NaN,
infinity, or a fabricated zero. Stop with an explicit failure if accounting
produces impossible negative equity. Do not hide a failed run behind metrics.
Use NumPy or small numerical functions where justified; convert Decimal equity
to a documented floating representation at the statistics boundary and test
with tolerances. No metric implementation or precision claim exists yet.

Reference arithmetic, not test output: equity `[100, 110, 99]` gives cumulative
return -1%, daily returns +10% and -10%, and maximum drawdown 10%. The two daily
returns' arithmetic mean is 0%, which does not imply zero compounded loss.

The buy-and-hold comparator uses the identical dataset slice, starting cash,
first eligible decision/fill convention, costs, and end treatment. Compare on
the same evaluation interval after any pre-window warm-up. Do not compare one
strategy's test interval against another's full-history result. Price-return
and dividend limitations apply to both.

These are explicit project conventions, not a claim that one annualization or
Sharpe estimator is uniquely correct. Annualized figures and a high Sharpe do
not establish significance, forecast skill, or independence of daily returns.

### D07 amendment - approved Phase 4 analytics, 2026-11-01

**ESTABLISHED by the user's Session 04 authorization.** Implement the D07 table
above. Exact ratios of unrounded Decimal equity cross to float for statistical
metrics/powers; cash, individual trade P&L, and mean closed-trade P&L remain
Decimal (the mean uses precision 28). Public `Metric` records contain a finite
value or `None` plus a reason, never NaN/Infinity or an invented missing zero.

One valuation has cumulative return/drawdown zero but no return sample or
annualization. Two valuations provide one return, insufficient for sample
volatility/Sharpe. Zero variance gives volatility zero and undefined Sharpe.
Initial equity must be positive; later equity must be nonnegative; invalid
values, duplicate/descending dates, and empty/mismatched input fail explicitly.
An interval after zero equity has an undefined return; retain it and make
volatility/Sharpe unavailable rather than drop it. Zero final equity gives
cumulative/annualized return -100% when the annualization period is valid.

Flag `0 < elapsed days < 365.25` annualization as extrapolation. Floating range
failures produce unavailable values with reasons. Effective annual risk-free
rate is finite Decimal > -1, default zero; convert it to a constant daily rate
using D07's formula. If float conversion loses its domain or exceeds finite
range, Sharpe alone is unavailable with a reason. Subtracting the constant
does not change sample standard deviation. Do not use display-rounded inputs.

Closed trades pair one full buy and sale; include both fees and classify net
P&L >0, <0, or =0. Break-even trades remain in the win-rate denominator. With
no closed trades, win rate and mean P&L are unavailable; show open entry cost,
quantity, final mark, and unrealized P&L separately, without a hypothetical
exit fee. No open position is counted as a closed winner.

Benchmark runs use the same dataset/window/capital/costs and engine conventions.
Both receive only selected-window closes. Intrinsic indicator warm-up can delay
entry; no extra history is supplied. Reject diagnostic exits in comparisons.
Return differences mean strategy minus benchmark, in fractions (0.01 = one
percentage point); annualized difference is unavailable if either component is.
No statistical significance claim. See [analytics API](ANALYTICS_CONTRACT.md)
and [Session 04 evidence](session-reports/SESSION_04_PHASE_4.md). Phase 5 is
not authorized.

## D08 - Strategy, experiment, and reproducibility boundaries

**PROPOSED before Phases 3 and 6, 2026-11-01.** Strategies take only a history
prefix through T, current position state, and validated parameters; they return
a target, not access to the full dataset or a future fill price.

- SMA: positive integer `fast < slow`; after at least `slow` closes, target
  LONG when fast SMA > slow SMA, FLAT when below, HOLD when equal. Initial
  bullish history can enter without a prior observed crossing. State this
  initialization explicitly and test it; no signal before sufficient history.
- Momentum: positive integer lookback L, finite threshold k (default 0);
  `mT = closeT / close(T-L) - 1`. After L+1 closes, target LONG if mT > k,
  otherwise FLAT. No signal before sufficient history. This is simple
  time-series momentum, not cross-sectional stock ranking.
- Train/test: chronological nonoverlapping evaluation intervals; select
  parameters using training data only, freeze them before testing. Earlier
  bars may warm indicators in the test run, but test cash starts flat and
  test performance excludes warm-up. No training positions carry over.
- Bounded grids: propose at most 100 configurations and 1,000,000 aggregate
  evaluated bars per request, including reference runs. Validate before work;
  reject excess rather than silently truncate. Revisit only with measured need.
  No test-set-driven selection of the reported winner.
- Reproduce using original data plus metadata IDs, effective configuration,
  date slice, contract/engine versions, and source revision. A dirty or
  uncommitted source tree needs an explicit source snapshot fingerprint, not
  a misleading clean Git commit label. Import time/run ID is provenance,
  excluded from deterministic output comparisons.

Phase 7 stores these inputs and results with versioned schema changes. Keep
original data accessible or state clearly that metadata alone cannot reproduce
a run. Initial synchronous bounded execution is sufficient unless measurements
justify a separately approved change.

### D08 amendment - approved Phase 3 strategy rules, 2026-11-01

**ESTABLISHED by the user's Session 03 authorization.** Adopt D08's SMA target
state and one-instrument time-series momentum rules exactly. SMA warms up for
`slow_window` selected closes, holds on ties, and may enter at the first bullish
state without observing a prior crossing. Momentum warms up for `lookback+1`
selected closes, enters only above threshold, and is FLAT on equality.
Parameters are immutable; windows/lookback are positive integers excluding
bool, with fast < slow. Threshold is a finite Decimal, default zero.

Use a streaming `on_close(session, close, shares)` interface: each run constructs
fresh rolling state and receives only the current completed close and scalar
position. No full dataset, future open, or mutable portfolio enters a rule.
Only the three approved configuration types are accepted; no arbitrary callback
or plugin. The engine remains the sole execution/accounting loop. Original
buy-and-hold fresh-intent and diagnostic-exit behavior is preserved.

Rolling sums and exact cross multiplication compare SMA averages; integer
ratios compare momentum to its Decimal threshold without a rounded quotient.
Warm-up starts at the selected evaluation window's first bar; no pre-window
history is consumed in Phase 3. Train/test warm-up, experiments, resource caps,
and source snapshot persistence remain later-phase proposals, not implemented
by this approval. No Phase 4 work is authorized.

### D08 amendment - approved Phase 6 experiments, 2026-11-02

**ESTABLISHED by the user's Session 06 authorization and continuation.** Adopt
bounded synchronous grids, cost sensitivity, explicit subperiods, and one
chronological train/test split. Reuse the existing simulator, analytics and
auditor; no new strategy, dependency, persistence or service. This supersedes
the Phase 3 restriction on consuming explicitly requested pre-window history.

- Reject the entire request for any invalid/duplicate configuration, date or
  cost scenario, unsupported setting, oversized workload, runtime/analysis
  failure, or audit FAIL. No skipped combinations or returned partial results.
  A normal recorded order rejection remains a successful simulation outcome.
- Cap unique configurations at 100 **including** the optional buy-and-hold
  reference. Charge every evaluation and indicator warm-up bar for every
  candidate/reference run against 1,000,000 bars. Preflight all windows/costs
  and reserve worst-case selected-test plus reference work before training.
  Reuse a single run by ID when buy-and-hold is also a candidate. No cache or
  unbudgeted audit replay. The conservative test reservation may reject a
  request that would fit if buy-and-hold eventually won.
- Canonically sort configurations by strategy then numeric parameters;
  preserve explicit period/cost order. Cost differences use the first listed
  cost; benchmark differences use matching periods/costs/capital. Do not rank
  unequal-duration subperiod returns or assume monotonic cost effects.
- Select only training candidates by descending existing reported cumulative
  return; equal reported values use canonical configuration order. An undefined
  candidate score aborts selection, rather than becoming zero or disappearing.
  A benchmark-only run is ineligible to win. Freeze selection before any test
  execution; do not rank test configurations or retune on the test result.
- Require training end < test start and at least two observed sessions per
  evaluation interval. Default test indicator warm-up feeds training-window
  closes only, excluding any gap; `warmup=False` starts indicators cold.
  Discard warm-up targets. Test starts flat with fresh initial cash and no
  pending order; no warm-up decision/order/fill/valuation enters its metrics.
  The first test-close signal can fill only at a later observed test open.
- Engine 1.3.0 adds optional paired warm-up bounds and actual warm-up metadata
  to the existing loop. Defaults retain selected-window-only signal history.
  Timing, sizing, costs, eligibility, metrics and final open holdings are unchanged.
- Record a SHA-256 manifest of sorted package-relative `.py` paths and exact
  content hashes, its canonical manifest hash, and Python version. This
  identifies dirty/uncommitted local source without inventing a Git revision.
  It does not archive/restore source, configuration files, dependencies or
  market inputs, or prove the bytes loaded by a concurrently modified process.
  Retention and persistence remain separate work.

Contract: [experiments](EXPERIMENT_CONTRACT.md). Acceptance evidence:
[Session 06](session-reports/SESSION_06_PHASE_6.md). One held-out interval does
not prove generalization, significance or profitability; unsupported audit
risks stay NOT_ASSESSED. Phase 7 is not authorized.

## D09 - Phase 5 evidence-backed integrity audit

**ESTABLISHED by the user's Session 05 authorization, 2026-11-01.** Add an
independent audit package without changing Phase 1-4 records or financial
semantics. Findings have stable rule IDs, PASS/FAIL/WARNING/NOT_ASSESSED,
separate severity, specific evidence references and suggested actions where
appropriate. No trust score or aggregate assertion of financial reliability.
Missing evidence/capabilities never become PASS.

Check recorded chronology/lifecycle, source-observed next-session eligibility,
cash/position/terminal reconciliation, D05-D06 cost arithmetic, declarations,
input identity and optional replay. Reconciliation independently folds recorded
fills and applies Decimal precision 28/ROUND_HALF_UP; it calls no production
execution/cost helper and generates no strategy decisions or orders. Verify
original request settings only when separately supplied; internal consistency
cannot prove the settings were unchanged from the original request.

Optional exact CSV bytes and separately supplied effective Metadata reverify
D03 fingerprints. Reuse the strict Phase 1 CSV parser to compare normalized
rows with retained Dataset bars; do not create another importer or silently
drop invalid rows. Source dates/prices can then support timing/mark checks.
Without original inputs, state that original identity/rows are not reverified.
Hashes identify supplied data, not source authenticity, completeness or rights.
Existing D04 eligibility remains mandatory, even if assertions are unknown.

Replay is opt-in, at most one call to the existing engine using retained
Dataset/strategy/settings/capital. Support current engine 1.2.0 and compare
**every SimulationResult field exactly**, including identity, configuration,
decisions/orders/fills/valuations, terminal balances, assumptions and warnings.
Exclude nothing: this schema has no nondeterministic provenance fields.
Missing inputs/configuration or unsupported engine version produce
NOT_ASSESSED. Agreement means current-engine/supplied-input equivalence; an
original executable source snapshot is separately NOT_ASSESSED.

All-look-ahead absence, survivorship, index membership, selection/data snooping,
overfitting, corporate-action truth, authoritative session completeness,
opening liquidity, significance and all economic events remain NOT_ASSESSED.
Known model exclusions and unverified declarations carry warnings. Auditing
SimulationResult accounting does not independently revalidate every statistical
metric in PerformanceReport. See [audit contract](AUDIT_CONTRACT.md) and
[Session 05](session-reports/SESSION_05_PHASE_5.md). Phase 6 is not authorized.

### D09 amendment - warm-up evidence and current replay, 2026-11-02

**ESTABLISHED within the authorized Phase 6 engine extension.** Audit 1.1.0
adds `TIMING.WARMUP`: requested separation, actual observed bounds/count and
absence of pre-evaluation trading/valuation records. Source-dependent evidence
is NOT_ASSESSED without usable source; the independent ledger still starts
from initial flat cash. Invalid requested bounds fail. Exact opt-in replay
now supports current engine 1.3.0 and includes new warm-up fields; historical
1.2.0 exact replay is NOT_ASSESSED. Independent unchanged cost formulas support
both 1.2.0 and 1.3.0. Experiment source fingerprints do not change the auditor's
original executable-restoration NOT_ASSESSED finding. No audit score or
statistical/bias certification is introduced.

## D10 - Phase 7 persistence and HTTP boundary

**ESTABLISHED by the user's Session 07 authorization, 2026-11-02.** Use the
standard-library SQLite driver, FastAPI/Pydantic boundary and a minimal local
server. Keep existing financial layers independent of HTTP/database imports.
No provider, frontend, authentication system, queue or new financial model.

The problem is retaining inspectable, reproducible research across restarts.
Two tables retain original CSV bytes/effective metadata and complete request/
result JSON respectively. Benefits: no financial trace loss, deterministic
duplicate dataset handling and simple foreign-key relationships. Complexity:
explicit serialization, reconstruction validation and transactional schema/
record writes; no ORM or migration framework. This implements planned Phase 7
without changing the remaining roadmap or financial conventions.

Use `PRAGMA user_version` for schema versioning, primary/foreign keys and
foreign-key enforcement on every connection. Unsupported/malformed schemas
fail explicitly; insert successful experiments only after computation and
serialization finish. Never silently overwrite an identity conflict.

HTTP imports accept UTF-8 CSV text and a metadata object, preserving the CSV's
UTF-8 bytes, including BOM/line endings. No request names a server-side file.
Cap CSV at existing 10 MiB, metadata/configuration at 64 KiB, and total import
JSON at 12 MiB. Reject duplicate/nonstandard JSON and unknown request fields.
Serialize Decimal as exact strings, dates as ISO strings and undefined metrics
as null plus reason; existing finite float statistics remain JSON numbers.
API decimal input strings are plain notation, at most 128 characters; reject
exponent notation to bound threshold expansion. This is a transport resource
limit, not a change to domain financial calculations. Lists page at 1-100
records, with offset 0-1,000,000. Reproduction accepts no replacement body.

Persist operational UUID/timestamps separately from deterministic results.
Reproduction reconstructs retained inputs through the same importer, validates
the saved request, reruns the same coordinator and compares defined economic
payloads exactly. Report implementation/source/runtime changes separately;
never call cached retrieval reproduction or imply an original source archive
was restored. Exclude only documented technical/assumption/audit fields from
the economic projection; retain them in saved results for inspection.

Run locally on 127.0.0.1 by default, with bounded JSON bodies, loopback Host
validation and no unrestricted CORS. No public deployment suitability is
claimed. Runtime dependencies are FastAPI 0.162.0, Pydantic 2.14.2, Starlette
1.10.0 (direct middleware/response dependency) and Uvicorn 0.54.0; tests use
pytest 9.2.0 and HTTPX2 2.16.0. SQLite comes from Python. No optional server,
telemetry exporter or multipart extra is installed. Exact schema/routes and
evidence: [API contract](API_CONTRACT.md),
[Session 07](session-reports/SESSION_07_PHASE_7.md). Stop before Phase 8.

## D11 - Phase 8 local research dashboard

**ESTABLISHED by the user's Session 08 authorization, 2026-11-02.** Build a
local React/TypeScript/Vite frontend over the actual Phase 7 API. Four areas:
Datasets, Backtest, Experiments, Saved Research. Core calculations, stored
records and all financial/eligibility/selection policies remain authoritative.
No provider, authentication, deployment or additional financial analysis.

The problem is making retained research inspectable without manual HTTP calls.
Use focused components/hooks, fetch and runtime response schemas; no component
framework, global-state framework or new server. Zod validates real response
shapes, uPlot draws canvas equity curves, and exact Decimal strings remain the
source for textual money displays. Chart coordinates use approximate numbers;
session labels and inspectable values retain the original ISO/Decimal data.

Vite's loopback proxy forwards `/api` to the existing loopback backend; configure
the API base/target through environment variables. No CORS expansion or backend
finance change is planned. Uploaded CSV decoding is strict UTF-8 and preserves
BOM/line endings; metadata raw JSON passes to the API without silently dropping
duplicate keys. Example inputs are clearly synthetic, never example results.

Preserve all audit statuses with evidence, undefined metric reasons, open
holdings, cost/window labels, training-only selection and reproduction identity
limits. New submissions clear prior results; failures retain editable inputs.
Read operations discard stale responses; writes prevent duplicate submissions.
Tables are paginated. No frontend portfolio return or drawdown is calculated.

Use Vitest/Testing Library for focused states/formatting and Playwright against
the real API/frontend for end-to-end evidence. This is required Phase 8 browser
verification, not new production infrastructure. Desktop browser tools failed
kernel initialization; an existing local browser is the fallback. Source/check
details and actual versions belong in Session 08. Phase 9 remains unauthorized.

## D12 - Phase 9 validated offline workflow

**ESTABLISHED by the user's Session 09 authorization, 2026-11-03. Path B.**
Reviewed Alpha Vantage first against current official documentation/support/
terms. No permitted credential/account was configured, so a real provider
import and interval split evidence could not be verified. Do not implement or
advertise an unverified adapter. Provider findings/access limits have their
primary home in [MARKET_DATA_REVIEW.md](MARKET_DATA_REVIEW.md).

The problem is using lawful historical files without treating valid syntax as
market/eligibility proof. Improve the existing Datasets workflow with a concise
in-app guide, downloadable unknown-by-default local metadata, full offline
instructions and integration tests of the actual shipped inputs. Benefit:
repeatable import/backtest/audit/persistence/reproduction with honest failure
behavior. Added complexity: one static React component/template and bounded
tests; no new dependency, endpoint, schema, provider or architectural layer.

D04 declarations, real-file coverage acknowledgment, financial calculations,
original-byte identity and stored historical records remain unchanged. A missing
or failed split check stays unknown. No real-market input or real no-split
evidence was manufactured. This completes the roadmap's existing offline
alternative, not Path A. Phase 10 remains unstarted and requires explicit
authorization. [Offline guide](OFFLINE_DATA_GUIDE.md),
[Session 09](session-reports/SESSION_09_PHASE_9.md).

## D13 - Phase 10 local engineering release

**ESTABLISHED by the user's final Session 10 authorization, 2026-11-03.**
Preserve the working modular monolith and financial policies. Validate a fresh
source copy/isolated Python environment and clean frontend lockfile install,
complete regressions, real application/restart workflows and bounded repeated
benchmarks. No source optimization or new product capability was justified.

The problem is supporting a defensible local technical demonstration with
actual setup, timing, failure and financial evidence. Benefits: repeatable
release checks, explicit limits and focused ownership/interview preparation.
Complexity/dependencies: two standalone standard-library release tools, small
benchmark JSON and extended existing browser tests; no new runtime dependency,
endpoint, infrastructure or architectural component. All 41 backend package
source hashes remain unchanged. The first missing-temp-parent test command and
an assumed SMA test default were corrected in the verification harness; no
financial policy changed.

Release means local demonstration readiness, not deployment, real-market proof,
independent authorship or a committed/tagged version. Keep Phase 9's synthetic/
offline boundary and unresolved historical disk observation. Consolidated
evidence: [RELEASE_VALIDATION.md](RELEASE_VALIDATION.md),
[BENCHMARKS.md](BENCHMARKS.md), [limits](KNOWN_LIMITATIONS.md).
All original phases 0-10 are complete; stop without adding Phase 11.

## D14 - Post-release historical validation, 2026-11-03

**ESTABLISHED by the user's explicit post-release validation request.** This is
a bounded validation improvement after completed phases 0-10, not Phase 11.
The problem is synthetic-only engineering evidence. Use existing offline input,
simulator, audit, experiments and persistence with two permitted public Alpha
Vantage samples; independently review interval split evidence and cross-check
selected arithmetic/signals/statistics. Benefits: real input/regression evidence.
Complexity/dependencies: six opt-in private-snapshot cases, no new dependency,
financial policy, product adapter, architecture or roadmap phase.

Personal credentials were absent in checked environment names. Published demo
responses are limited sample access, not verified general account entitlement.
Keep provider observations and issuer-page archives/databases ignored; no
redistribution permission was established. MSFT's failed split response stays
unknown; the separate issuer history supports its interval declaration.
Preserve D03-D09 and all original synthetic tests. Scope and actual results:
[REAL_MARKET_VALIDATION.md](REAL_MARKET_VALIDATION.md). Stop after validation.

## D15 - Publication preparation, 2026-11-03

**ESTABLISHED by the user's explicit packaging/safety request.** The problem is
publishing a self-contained repository without private data/credentials or
owner-specific paths. Benefits: reviewed candidates/history, honest README,
synthetic screenshots and clean-clone setup evidence. Complexity/dependencies:
one standard-library read-only check, small updates to the existing verifier,
ignore rules and documentation; no application/financial/dependency change or
new roadmap phase. Use an ignored disposable local commit/clone because the
root has no ordinary commits. Leave private tool refs and root Git state intact.
No license invention, market-data redistribution, remote creation or push.
Findings and recommended owner actions: [publication readiness](PUBLICATION_READINESS.md).

## D16 - Complete educational handbook, 2026-11-04

**ESTABLISHED by the user's explicit documentation request.** Synthesize existing
source, tests, contracts and evidence into one standalone learning resource:
[QUANTLAB_COMPLETE_HANDBOOK.md](QUANTLAB_COMPLETE_HANDBOOK.md). Explain current
behavior separately from tested cases, recorded results, general concepts and
hypothetical improvements. Verify source symbols, links and worked numerical
examples. Preserve application/financial behavior, tests, dependencies and
architecture; no new phase, provider, infrastructure, publication or push.

Confirmed disclosure gap: the direct benchmark helper accepts/honors explicit
earlier indicator warm-up, but one returned assumption says only selected-window
closes are seen. Document actual behavior and the stale string; a future code
correction requires separate authorization. No new financial convention is chosen.

2026-11-04 format follow-up: the user requested a PDF. Generate the complete
print edition using bundled document tooling, preserve handbook content and
application dependencies, and keep generated local exports under ignored
`output/`. This adds no product feature, financial rule or development phase.

## D17 - Authorized GitHub publication, 2026-11-07

**ESTABLISHED by the user's explicit request to publish under the supplied
GitHub account.** Publish the reviewed project as public repository
[SHERSHAH-DEMIGAWD/QuantLab](https://github.com/SHERSHAH-DEMIGAWD/QuantLab).
Use an initial ordinary commit and push only its reviewed branch to remote
`main`; do not transfer private internal refs or rewrite history. The local
publication branch is `codex/publication`. Use the verified account's public
GitHub noreply identity for commits, not a private local email address.

Keep credentials, environments, databases, IBM/MSFT observations/evidence and
generated local exports excluded. Leave the license unselected rather than
inventing permissions. Verify remote contents and a fresh GitHub clone with
public setup/tests. This is source publication, not hosted deployment or a new
development phase. No financial/application/test/dependency change is authorized.

## Review gates and unresolved questions

| Gate | Review required | Consequence of leaving it unresolved |
| --- | --- | --- |
| Before Phase 1 | D03's strict six-column CSV and metadata contract; ingestion warnings versus simulation eligibility; select/verify the actual Python environment under D02 | Stay at the foundation until Phase 1 is explicitly authorized; environment compatibility must be checked during that phase |
| Before Phase 2 | D04's conservative corporate-action window restriction and dividend exclusion; D05 budgeted sizing, rounding, zero-volume policy, immediate reuse of sale proceeds, and no forced liquidation | Do not implement an engine with assumed approval; split-aware or adjusted-unit execution needs a separate explicit choice |
| Before Phase 3 | D08 warm-up, equality, first bullish SMA entry, and exact momentum definition | Do not silently choose a different strategy |
| Before Phase 4 | D06 costs and D07 metric conventions, annualization, undefined values | No unreviewed financial semantics changes |
| Before Phase 6 | D08 caps, split boundaries, warm-up, parameter selection, and source identity | No unbounded search or accidental test contamination |
| Before Phase 9 | Provider terms, fields, adjustment policy, historical coverage, reliability, cache and redistribution limits | No provider is selected; validated offline import remains acceptable |

Immediate settlement is an explicit proposed simplification: after a simulated
sale, proceeds may fund a later simulated purchase without modeling settlement
delays or real cash-account trading restrictions. Add this to Phase 2 result
assumptions if approved. This platform models research accounting, not broker
account compliance or executable trading guarantees.

The main ambiguity is not a contradiction in scope: daily OHLCV and an integer
share engine do not themselves solve corporate actions or opening liquidity.
The proposed restrictions expose those limits. No core phase has been added,
removed, or authorized by this document.
