"""Pure equity/trade analytics and a controlled buy-and-hold comparison."""

from .benchmark import analyze_simulation, compare_with_buy_and_hold
from .equity import analyze_equity
from .models import (
    AnalyticsError, BenchmarkComparison, ClosedTrade, DailyReturn, EquityMetrics,
    Metric, OpenPosition, PerformanceReport, TradeStatistics,
)
from .trades import analyze_trades

__all__ = [
    "AnalyticsError", "BenchmarkComparison", "ClosedTrade", "DailyReturn", "EquityMetrics",
    "Metric", "OpenPosition", "PerformanceReport", "TradeStatistics", "analyze_equity",
    "analyze_simulation", "analyze_trades", "compare_with_buy_and_hold",
]
