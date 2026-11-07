"""Bounded synchronous orchestration using the existing engine, analytics and auditor."""

from collections.abc import Sequence
from dataclasses import dataclass, replace
from decimal import Decimal, DecimalException, localcontext

from quantlab.analytics import Metric, analyze_simulation
from quantlab.analytics.equity import finite_metric, validate_risk_free_rate
from quantlab.audit import audit_simulation
from quantlab.data import Dataset
from quantlab.execution import ExecutionSettings, simulate, validate_simulation_request
from quantlab.execution.engine import ARITHMETIC
from quantlab.strategies import BuyAndHold, StrategyConfig

from .grids import MAX_AGGREGATE_BARS, MAX_CONFIGURATIONS, configuration_key, validate_configurations
from .models import (
    CostScenario, EvaluationPeriod, ExperimentError, ExperimentResult, ExperimentRun,
    Reproducibility, RunComparison, TrainingSelection, TrainTestResult, Workload,
)
from .reproducibility import source_snapshot

EXPERIMENT_VERSION = "1.0.0"
ASSUMPTIONS = (
    "Existing next-open, Decimal, integer, long-only, price-return/corporate-action conventions apply; no forced final sale.",
    "Invalid configurations or any execution/analysis/audit failure abort the request; no partial result is returned.",
    "At most 100 unique strategy configurations including buy-and-hold references; at most 1,000,000 evaluated plus warm-up bars across all runs.",
    "Runs are synchronous. Each planned reference executes once and is referenced by ID; there is no result cache or unbudgeted audit replay.",
    "Costs can change affordable quantity and trade paths; monotonic performance with increasing costs is not assumed.",
    "Different-length subperiod returns are labeled by their own windows and are not a common quality ranking.",
    "Audit warnings and NOT_ASSESSED risks remain; experiments do not prove generalization, significance or future profitability.",
)


@dataclass(frozen=True)
class _Job:
    run_id: str
    configuration: StrategyConfig
    settings: ExecutionSettings
    period: EvaluationPeriod
    period_index: int
    cost_index: int
    phase: str
    role: str


def _bounded(workload: Workload) -> Workload:
    if workload.total_bars > MAX_AGGREGATE_BARS:
        raise ExperimentError(f"Aggregate workload {workload.total_bars} exceeds 1,000,000 bars, including references and warm-up.")
    return workload


def _sum_workload(left: Workload, right: Workload) -> Workload:
    return Workload(left.run_count + right.run_count, left.evaluated_bars + right.evaluated_bars, left.warmup_bars + right.warmup_bars)


def _base_settings(settings: ExecutionSettings | None, explicit_periods: bool) -> ExecutionSettings:
    settings = ExecutionSettings() if settings is None else settings
    if not isinstance(settings, ExecutionSettings):
        raise ExperimentError("settings must be ExecutionSettings.")
    if settings.sell_after_session is not None or settings.warmup_start_date is not None or settings.warmup_end_date is not None:
        raise ExperimentError("Experiments reject diagnostic exits and reserve warm-up settings for the controlled train/test workflow.")
    if explicit_periods and (settings.start_date is not None or settings.end_date is not None):
        raise ExperimentError("Use explicit experiment periods or settings date bounds, not both.")
    return settings


def _periods(dataset: Dataset, settings: ExecutionSettings, periods: Sequence[EvaluationPeriod] | None) -> tuple[EvaluationPeriod, ...]:
    if not isinstance(dataset, Dataset) or not dataset.bars:
        raise ExperimentError("A nonempty validated Dataset is required.")
    if periods is None:
        periods = (EvaluationPeriod(settings.start_date or dataset.report.first_date, settings.end_date or dataset.report.last_date),)
    if not isinstance(periods, Sequence) or not periods or not all(type(period) is EvaluationPeriod for period in periods):
        raise ExperimentError("periods must be a nonempty sequence of EvaluationPeriod values.")
    if len(set(periods)) != len(periods):
        raise ExperimentError("Duplicate evaluation periods are not permitted.")
    return tuple(periods)


def _costs(settings: ExecutionSettings, costs: Sequence[CostScenario] | None) -> tuple[CostScenario, ...]:
    if costs is None:
        costs = (CostScenario(settings.commission_per_fill_usd, settings.slippage_bps),)
    elif settings.commission_per_fill_usd != 0 or settings.slippage_bps != 0:
        raise ExperimentError("Supply cost scenarios or nonzero base costs, not both.")
    if not isinstance(costs, Sequence) or not costs or not all(type(cost) is CostScenario for cost in costs):
        raise ExperimentError("costs must be a nonempty sequence of CostScenario values.")
    if len(set(costs)) != len(costs):
        raise ExperimentError("Duplicate cost scenarios are not permitted.")
    return tuple(costs)


def _plan(
    dataset: Dataset, capital: Decimal, configurations: tuple[StrategyConfig, ...],
    periods: tuple[EvaluationPeriod, ...], costs: tuple[CostScenario, ...],
    base: ExecutionSettings, benchmark: bool, phase: str, prefix: str,
    warmup: EvaluationPeriod | None = None,
) -> tuple[tuple[_Job, ...], Workload]:
    if type(benchmark) is not bool:
        raise ExperimentError("include_benchmark must be bool.")
    all_configs = tuple(sorted(set(configurations) | ({BuyAndHold()} if benchmark else set()), key=configuration_key))
    if len(all_configs) > MAX_CONFIGURATIONS:
        raise ExperimentError("Including the fixed benchmark exceeds 100 unique strategy configurations.")
    run_count = len(all_configs) * len(periods) * len(costs)
    _bounded(Workload(run_count, run_count * 2))  # Every valid evaluation needs at least two observations.
    jobs = []
    workload = Workload(0, 0)
    for period_index, period in enumerate(periods):
        for cost_index, cost in enumerate(costs):
            settings = replace(
                base, start_date=period.start_date, end_date=period.end_date,
                commission_per_fill_usd=cost.commission_per_fill_usd, slippage_bps=cost.slippage_bps,
                warmup_start_date=warmup.start_date if warmup else None,
                warmup_end_date=warmup.end_date if warmup else None,
            )
            try:
                # Window/cost/data checks are shared by configs already validated above.
                evaluated, warmed = validate_simulation_request(dataset, capital, all_configs[0], settings)
            except (ValueError, DecimalException) as exc:
                raise ExperimentError(f"Preflight period {period_index}, cost {cost_index}: {exc}") from exc
            workload = _bounded(_sum_workload(workload, Workload(len(all_configs), evaluated * len(all_configs), warmed * len(all_configs))))
            for config in all_configs:
                jobs.append(_Job(
                    f"{prefix}_{len(jobs)+1:03}", config, settings, period,
                    period_index, cost_index, phase,
                    "candidate" if config in configurations else "benchmark",
                ))
    return tuple(jobs), workload


def _execute_jobs(dataset: Dataset, capital: Decimal, jobs: tuple[_Job, ...], risk_free: Decimal) -> tuple[ExperimentRun, ...]:
    runs = []
    for job in jobs:
        try:
            simulation = simulate(dataset, capital, job.configuration, job.settings)
            performance = analyze_simulation(simulation, annual_risk_free_rate=risk_free)
            audit = audit_simulation(simulation, dataset=dataset, expected_settings=job.settings, rerun=False)
            failures = [finding.rule_id for finding in audit.findings if finding.status == "FAIL"]
            if failures:
                raise ExperimentError("Audit failures: " + ", ".join(failures))
        except (ValueError, DecimalException) as exc:
            raise ExperimentError(f"Run {job.run_id} failed; entire experiment has no returned partial result: {exc}") from exc
        runs.append(ExperimentRun(job.run_id, job.phase, job.role, job.period, performance, audit))
    return tuple(runs)


def _metric_difference(left: Metric, right: Metric) -> Metric:
    if left.value is None or right.value is None:
        return Metric(None, "component_metric_unavailable")
    return finite_metric(left.value - right.value)


def _comparison(run: ExperimentRun, reference: ExperimentRun, kind: str) -> RunComparison:
    return RunComparison(
        kind, run.run_id, reference.run_id,
        run.performance.simulation.final_equity - reference.performance.simulation.final_equity,
        _metric_difference(run.performance.equity.cumulative_return, reference.performance.equity.cumulative_return),
        _metric_difference(run.performance.equity.maximum_drawdown, reference.performance.equity.maximum_drawdown),
    )


def _result(
    dataset: Dataset, configs: tuple[StrategyConfig, ...], periods: tuple[EvaluationPeriod, ...],
    costs: tuple[CostScenario, ...], jobs: tuple[_Job, ...], runs: tuple[ExperimentRun, ...],
    workload: Workload, snapshot: Reproducibility, benchmark: bool,
) -> ExperimentResult:
    lookup = {(job.period_index, job.cost_index, job.configuration): run for job, run in zip(jobs, runs)}
    comparisons = []
    for job, run in zip(jobs, runs):
        if job.role != "candidate":
            continue
        if benchmark:
            comparisons.append(_comparison(run, lookup[(job.period_index, job.cost_index, BuyAndHold())], "benchmark"))
        if job.cost_index > 0:
            comparisons.append(_comparison(run, lookup[(job.period_index, 0, job.configuration)], "cost_reference"))
    dimensions = [name for name, count in (("parameter_grid", len(configs)), ("cost_sensitivity", len(costs)), ("subperiods", len(periods))) if count > 1]
    kind = dimensions[0] if len(dimensions) == 1 else "combined" if dimensions else "fixed_reference"
    return ExperimentResult(kind, EXPERIMENT_VERSION, dataset.report.dataset_id, configs, periods, costs,
                            runs, tuple(comparisons), workload, snapshot, ASSUMPTIONS)


def run_experiment(
    dataset: Dataset, initial_capital: Decimal, configurations: Sequence[StrategyConfig], *,
    periods: Sequence[EvaluationPeriod] | None = None, costs: Sequence[CostScenario] | None = None,
    settings: ExecutionSettings | None = None, include_benchmark: bool = True,
    annual_risk_free_rate: Decimal = Decimal("0"),
) -> ExperimentResult:
    """Atomic Cartesian experiment; cost deltas use the explicitly listed first cost."""
    with localcontext(ARITHMETIC):
        validate_risk_free_rate(annual_risk_free_rate)
        configs = validate_configurations(configurations)
        base = _base_settings(settings, periods is not None)
        windows, scenarios = _periods(dataset, base, periods), _costs(base, costs)
        jobs, workload = _plan(dataset, initial_capital, configs, windows, scenarios, base, include_benchmark, "evaluation", "run")
        snapshot = source_snapshot()
        runs = _execute_jobs(dataset, initial_capital, jobs, annual_risk_free_rate)
        return _result(dataset, configs, windows, scenarios, jobs, runs, workload, snapshot, include_benchmark)


def _select_training(runs: tuple[ExperimentRun, ...]) -> TrainingSelection:
    candidates = [run for run in runs if run.role == "candidate"]
    if not candidates or any(run.phase != "training" for run in candidates):
        raise ExperimentError("Selection accepts training candidate runs only, never test rankings.")
    for run in candidates:
        metric = run.performance.equity.cumulative_return
        if metric.value is None:
            raise ExperimentError(f"Undefined training selection metric at {run.run_id}: {metric.reason}; no zero substitution or selection is permitted.")
    ranking = sorted(candidates, key=lambda run: (-run.performance.equity.cumulative_return.value,
                                                 configuration_key(run.performance.simulation.strategy)))
    winner = ranking[0]
    return TrainingSelection(winner.performance.simulation.strategy, winner.run_id, tuple(run.run_id for run in ranking))


def run_train_test(
    dataset: Dataset, initial_capital: Decimal, configurations: Sequence[StrategyConfig],
    training_period: EvaluationPeriod, test_period: EvaluationPeriod, *,
    settings: ExecutionSettings | None = None, warmup: bool = True,
    include_benchmark: bool = True, annual_risk_free_rate: Decimal = Decimal("0"),
) -> TrainTestResult:
    """Freeze training-only selection before executing a fresh, flat test portfolio."""
    if type(training_period) is not EvaluationPeriod or type(test_period) is not EvaluationPeriod or training_period.end_date >= test_period.start_date:
        raise ExperimentError("Training must be strictly earlier than a nonoverlapping test period.")
    if type(warmup) is not bool:
        raise ExperimentError("warmup must be bool.")
    with localcontext(ARITHMETIC):
        validate_risk_free_rate(annual_risk_free_rate)
        configs = validate_configurations(configurations)
        base = _base_settings(settings, True)
        costs = _costs(base, None)
        history = training_period if warmup else None
        train_jobs, train_work = _plan(dataset, initial_capital, configs, (training_period,), costs, base, include_benchmark, "training", "train")
        # Reserve worst-case selected strategy + reference before any training run.
        representative = next((config for config in configs if type(config) is not BuyAndHold), configs[0])
        _, reserved_test = _plan(dataset, initial_capital, (representative,), (test_period,), costs, base, include_benchmark, "test", "test", history)
        planned = _bounded(_sum_workload(train_work, reserved_test))
        snapshot = source_snapshot()
        train_runs = _execute_jobs(dataset, initial_capital, train_jobs, annual_risk_free_rate)
        training = _result(dataset, configs, (training_period,), costs, train_jobs, train_runs, train_work, snapshot, include_benchmark)
        selection = _select_training(train_runs)  # No test report exists at selection time.
        test_jobs, test_work = _plan(dataset, initial_capital, (selection.selected_configuration,), (test_period,), costs, base, include_benchmark, "test", "test", history)
        actual = _bounded(_sum_workload(train_work, test_work))
        test_runs = _execute_jobs(dataset, initial_capital, test_jobs, annual_risk_free_rate)
        selected = next(run for run in test_runs if run.role == "candidate")
        reference = next((run for run in test_runs if type(run.performance.simulation.strategy) is BuyAndHold), None) if include_benchmark else None
        assumptions = ASSUMPTIONS + (
            "Training ranks only candidate cumulative-return metrics, with deterministic canonical ties; undefined scores abort selection.",
            "Selected parameters are frozen before test execution; test performance never reselects or ranks configurations.",
            "Test starts flat with fresh capital and no pending order; optional indicator-only warm-up uses training-window bars only, excluding any gap bars.",
            "A single held-out period is not independent proof of generalization, significance or future profitability.",
        )
        return TrainTestResult(
            training, selection, test_period, test_runs, selected.run_id,
            reference.run_id if reference else None,
            _comparison(selected, reference, "benchmark") if reference else None,
            planned, actual, assumptions,
        )
