"""Typed experiment plans/results; simulation traces are stored once per run."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from quantlab.analytics import Metric, PerformanceReport
from quantlab.audit import AuditReport
from quantlab.strategies import StrategyConfig


class ExperimentError(ValueError):
    """Atomic request/run failure; no partially successful result is returned."""


@dataclass(frozen=True)
class EvaluationPeriod:
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if type(self.start_date) is not date or type(self.end_date) is not date or self.start_date > self.end_date:
            raise ExperimentError("EvaluationPeriod requires ordered date bounds.")


@dataclass(frozen=True)
class CostScenario:
    commission_per_fill_usd: Decimal = Decimal("0.00")
    slippage_bps: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        for value in (self.commission_per_fill_usd, self.slippage_bps):
            if not isinstance(value, Decimal) or not value.is_finite():
                raise ExperimentError("Cost scenarios require finite Decimal settings; engine validates their supported ranges.")


@dataclass(frozen=True)
class Workload:
    run_count: int
    evaluated_bars: int
    warmup_bars: int = 0

    @property
    def total_bars(self) -> int:
        return self.evaluated_bars + self.warmup_bars


@dataclass(frozen=True)
class Reproducibility:
    source_snapshot_sha256: str
    source_files: tuple[tuple[str, str], ...]
    python_version: str
    explanation: str


@dataclass(frozen=True)
class ExperimentRun:
    run_id: str
    phase: Literal["evaluation", "training", "test"]
    role: Literal["candidate", "benchmark"]
    requested_period: EvaluationPeriod
    performance: PerformanceReport
    audit: AuditReport


@dataclass(frozen=True)
class RunComparison:
    kind: Literal["benchmark", "cost_reference"]
    run_id: str
    reference_run_id: str
    final_equity_difference: Decimal
    cumulative_return_difference: Metric
    maximum_drawdown_difference: Metric


@dataclass(frozen=True)
class ExperimentResult:
    experiment_type: str
    experiment_version: str
    dataset_id: str
    configurations: tuple[StrategyConfig, ...]
    periods: tuple[EvaluationPeriod, ...]
    costs: tuple[CostScenario, ...]
    runs: tuple[ExperimentRun, ...]
    comparisons: tuple[RunComparison, ...]
    workload: Workload
    reproducibility: Reproducibility
    assumptions: tuple[str, ...]


@dataclass(frozen=True)
class TrainingSelection:
    selected_configuration: StrategyConfig
    selected_training_run_id: str
    ranked_training_run_ids: tuple[str, ...]
    criterion: str = "cumulative_return"
    tie_break: str = "canonical strategy/parameter order among equal reported metric values"


@dataclass(frozen=True)
class TrainTestResult:
    training: ExperimentResult
    selection: TrainingSelection
    requested_test_period: EvaluationPeriod
    test_runs: tuple[ExperimentRun, ...]
    selected_test_run_id: str
    benchmark_test_run_id: str | None
    test_comparison: RunComparison | None
    planned_workload: Workload
    actual_workload: Workload
    assumptions: tuple[str, ...]
