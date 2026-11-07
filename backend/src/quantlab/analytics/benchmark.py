"""One strategy versus buy-and-hold, with identical data and execution settings."""

from decimal import Decimal
from fractions import Fraction

from quantlab.data import Dataset
from quantlab.execution import ExecutionSettings, SimulationResult, simulate
from quantlab.strategies import BuyAndHold, StrategyConfig

from .equity import analyze_equity, finite_metric, ratio_metric, validate_risk_free_rate
from .models import AnalyticsError, BenchmarkComparison, Metric, PerformanceReport
from .trades import analyze_trades


def analyze_simulation(
    simulation: SimulationResult, *, annual_risk_free_rate: Decimal = Decimal("0"),
) -> PerformanceReport:
    if not isinstance(simulation, SimulationResult) or not simulation.valuations:
        raise AnalyticsError("Expected a successful simulation with closing valuations.")
    return PerformanceReport(
        simulation=simulation,
        equity=analyze_equity(
            [value.session for value in simulation.valuations],
            [value.equity for value in simulation.valuations],
            annual_risk_free_rate=annual_risk_free_rate,
        ),
        trades=analyze_trades(simulation.fills, simulation.valuations[-1].close),
    )


def compare_with_buy_and_hold(
    dataset: Dataset, initial_capital: Decimal, strategy: StrategyConfig,
    settings: ExecutionSettings | None = None, *,
    annual_risk_free_rate: Decimal = Decimal("0"),
) -> BenchmarkComparison:
    validate_risk_free_rate(annual_risk_free_rate)
    settings = ExecutionSettings() if settings is None else settings
    if not isinstance(settings, ExecutionSettings) or settings.sell_after_session is not None:
        raise AnalyticsError("Benchmark requires ExecutionSettings without a diagnostic exit.")
    selected = analyze_simulation(simulate(dataset, initial_capital, strategy, settings), annual_risk_free_rate=annual_risk_free_rate)
    benchmark = analyze_simulation(simulate(dataset, initial_capital, BuyAndHold(), settings), annual_risk_free_rate=annual_risk_free_rate)
    difference = ratio_metric(
        (Fraction(selected.simulation.final_equity) - Fraction(benchmark.simulation.final_equity))
        / Fraction(selected.simulation.initial_capital)
    )
    left, right = selected.equity.annualized_return, benchmark.equity.annualized_return
    annual_difference = (finite_metric(left.value - right.value)
                         if left.value is not None and right.value is not None
                         else Metric(None, "component_annualized_return_unavailable"))
    return BenchmarkComparison(
        strategy=selected, benchmark=benchmark, cumulative_return_difference=difference,
        annualized_return_difference=annual_difference,
        assumptions=(
            "Same dataset, evaluation dates, initial capital, costs, execution and terminal-position conventions.",
            "Both rules see only closes inside the same selected window; intrinsic indicator warm-up may delay entry.",
            "Differences are strategy minus buy-and-hold return fractions; 0.01 is one percentage point.",
            "No statistical significance or future-performance claim; dividends remain excluded.",
        ),
    )
