# Phase 6 experiment API

Version 1.0.0: synchronous in-memory orchestration of existing execution,
analytics and audit. Policy approval lives in
[D08's Phase 6 amendment](DECISIONS.md#d08-amendment---approved-phase-6-experiments-2026-11-02).
No database, API, provider, frontend, arbitrary code or new strategy is involved.
The separate [Phase 7 backend](API_CONTRACT.md) now retains requests/inputs/results
and exposes these functions through HTTP; the research runner remains independent.

```python
from decimal import Decimal
from quantlab.data import load_dataset
from quantlab.experiments import CostScenario, momentum_grid, run_experiment

dataset = load_dataset(
    "backend/tests/fixtures/synthetic_daily.csv",
    "backend/tests/fixtures/synthetic_daily.metadata.json",
)
result = run_experiment(
    dataset, Decimal("1000"), momentum_grid([1, 2]),
    costs=(CostScenario(), CostScenario(Decimal("2"), Decimal("100"))),
)
for run in result.runs:
    simulation = run.performance.simulation
    print(run.run_id, simulation.strategy, simulation.settings,
          simulation.final_equity, run.performance.equity.cumulative_return)
print(result.comparisons, result.workload, result.reproducibility)
```

The three-row fixture is invented and contains a zero-volume execution bar.
Short/cold indicators can legitimately leave a run flat; it is not adequate
for two separate two-observation training/test windows or market conclusions.

## Inputs, ordering and atomic policy

| Function/value | Contract |
| --- | --- |
| `sma_grid(fast_windows, slow_windows)` | Cartesian product of nonempty sequences; every pair must satisfy existing positive integer fast < slow rules |
| `momentum_grid(lookbacks, thresholds=(Decimal("0"),))` | Cartesian product using existing positive integer lookback and finite Decimal threshold rules |
| `EvaluationPeriod(start_date, end_date)` | Ordered inclusive `date` bounds; each evaluation needs at least two actual source observations; bounds need not be sessions |
| `CostScenario(commission_per_fill_usd=Decimal("0.00"), slippage_bps=Decimal("0"))` | Finite Decimal settings; existing engine range/precision/rounding validation during preflight |
| `run_experiment(dataset, initial_capital, configurations, *, periods=None, costs=None, settings=None, include_benchmark=True, annual_risk_free_rate=Decimal("0"))` | Cartesian periods x costs x unique configurations, plus optional fixed buy-and-hold reference |
| `run_train_test(dataset, initial_capital, configurations, training_period, test_period, *, settings=None, warmup=True, include_benchmark=True, annual_risk_free_rate=Decimal("0"))` | One training grid, frozen selection, then selected strategy and optional reference on a later fresh test portfolio; costs fixed by settings |

Only the three existing built-ins are supported. Configuration sequences are
nonempty, unique and canonically ordered: buy-and-hold, momentum by lookback
then threshold, SMA by fast then slow. Grid axes have at most 100 pairs before
construction; duplicates and invalid pairs reject the entire grid. Sets and
generators are not accepted. Period/cost sequences are nonempty and unique;
their explicit order is preserved. No invalid row/configuration is dropped.

Without explicit periods, settings bounds or the full imported date range
apply. Supplying both explicit periods and settings date bounds fails. Without
explicit cost scenarios, use settings costs; explicit scenarios with nonzero
base costs fail to avoid silently overriding assumptions. Diagnostic exits and
caller-supplied warm-up settings are rejected by experiments. Train/test owns
its warm-up interval. Existing eligibility, coverage acknowledgment, numeric
bounds and risk-free-rate validation remain in force.

Request/preflight failures raise ValueError subtypes, normally `ExperimentError`;
existing risk-free-rate validation may raise `AnalyticsError`. Runtime execution,
analysis or audit FAIL aborts with an identified run and no returned partial
result. Earlier work may have consumed CPU, but no result/data mutation or
external write occurs. Ordinary rejected/expired orders are valid engine
outcomes. WARNING and NOT_ASSESSED findings do not disappear. A source-manifest
read failure also rejects before execution.

## Workload limits

- At most **100 unique strategy configurations**, counting a requested
  buy-and-hold reference. If already a candidate, its reference shares that
  run; 100 non-reference candidates plus an added reference are rejected.
- At most **1,000,000 aggregate evaluation plus indicator warm-up bars** over
  every candidate/reference, period and cost. Counting warm-up is conservative
  relative to the original evaluated-bar proposal. No truncation or concurrency.
- Preflight every window/cost before any simulation. Train/test additionally
  reserves worst-case selected test strategy plus reference work before training.
  A buy-and-hold winner can use fewer actual runs than this reservation; report
  both planned and actual workloads. Exceeding the conservative reservation
  fails even if that eventual winner would fit.

`Workload` exposes `run_count`, `evaluated_bars`, `warmup_bars` and `total_bars`.
No audit replay is hidden in this budget. Each planned reference runs once;
comparisons refer to its ID without copying the report or using a runtime cache.

## Outputs and fair comparisons

Frozen `ExperimentResult` contains type/version, dataset ID, canonical candidate
configurations, requested periods, costs, runs, comparisons, workload, source
manifest and assumptions. Type reflects varied dimensions (`parameter_grid`,
`cost_sensitivity`, `subperiods`, `combined`, or `fixed_reference`). Each
`ExperimentRun` has a deterministic ID, phase/role, requested period, existing
`PerformanceReport` and `AuditReport`. The simulation retains actual session
bounds, capital, strategy, costs, engine version, source/metadata identity,
decisions, orders, fills, valuations, warnings and final open holdings.

Comparisons store candidate/reference IDs and candidate-minus-reference final
equity, cumulative return and maximum drawdown. Money differences use Decimal
precision 28/ROUND_HALF_UP; metric differences use existing finite statistics.
Returns are fractions. Drawdown is nonnegative in each report, so a positive
drawdown difference means greater drawdown. An unavailable component produces
`Metric(None, "component_metric_unavailable")`, never zero.

Cost deltas use the **first listed cost** for the same configuration/period.
Benchmark deltas use matching capital/costs/dates/warm-up/end treatment. A
buy-and-hold candidate's self-comparison is zero. Higher costs can change
integer affordability and exposure; monotonic return ordering is not assumed.
Subperiods may overlap and differ in length; reports identify each interval
and do not rank returns across different intervals as equivalent quality.
No sessions are invented and no final sale is forced.

## Training and held-out testing

Training end must be strictly before test start. Both windows need at least
two observed sessions; a strategy may remain cold/flat if its own history
requirement is longer. Training contains only training-window observations.
Rank candidate runs by descending **existing reported cumulative return**;
ties use canonical configuration order, including ties at reported float
precision. Benchmark-only runs cannot win. Any undefined candidate score
aborts selection with its reason. Negative scores remain valid.

`TrainingSelection` records the criterion, tie rule, ranked training run IDs,
winner configuration and winning training ID. Selection completes before a
test result exists. Execute only that frozen strategy and optional reference
in testing; expose no test-selection/reranking mechanism.

Default warm-up supplies only training-window closes to a new rule, with zero
shares and discarded targets. Any gap between windows is excluded. A fresh
test portfolio then starts with the original initial capital, zero shares and
no pending order. No warm-up decisions/fills/valuations/P&L enter test metrics.
The earliest test trade follows the first test close at a later observed open.
`warmup=False` starts indicators cold at the first test close. Both selected
strategy and test reference receive the same warm-up setting. Actual warm-up
bounds/count and requested bounds remain in each engine result.

`TrainTestResult` holds training results and source manifest, frozen selection,
requested test interval, test runs, selected/reference IDs, test benchmark
comparison, planned/actual total workloads and assumptions. No training traces
are copied into test results and no training holdings/P&L carry into them.

Training chooses among tried configurations; the later test measures that
frozen choice. Repeatedly using test outcomes to redesign a grid contaminates
that test outside this function. A single held-out interval does not establish
generalization, significance or future profitability. No walk-forward
optimization, significance test or automatic retuning is implemented.

## Reproducibility and limits

Once per request, hash exact local package `.py` bytes into sorted package-relative
path/SHA-256 pairs, then hash their canonical JSON manifest. Record Python version.
No clean Git revision is claimed. This excludes docs/tests/build configuration/
dependencies; it identifies available source bytes, not an archive or proof of
unchanged already-loaded code. Retain source, original market bytes, effective
metadata and complete request separately; persistence/restoration is not implemented.

Auditing uses the shared Dataset and effective request settings, without original
CSV bytes or replay. Those evidence limitations and unsupported risks remain
visible. Price-return labeling, excluded dividends/actions, unverified calendar/
source truth/coverage/opening liquidity, simplified costs and short-sample
annualization warnings all remain. No metric formula is replaced by experiments.

For R runs, N imported rows, A aggregate evaluation+warm-up bars, and S package
source bytes: expected time O(R*N + A + S), plus sorting at most 100 configs
and training scores. Engine/auditor validation rescans the shared Dataset;
the bar cap is not a wall-clock guarantee and does not bound these full scans.
Returned traces use O(A) space (warm-up itself produces no trace), with O(N)
temporary source indexes and lightweight job/bar references. Datasets are never
copied per configuration. No cache, worker or new numerical dependency was
added. No throughput benchmark ran; pytest duration is verification time only.
Evidence: [Session 06](session-reports/SESSION_06_PHASE_6.md).
