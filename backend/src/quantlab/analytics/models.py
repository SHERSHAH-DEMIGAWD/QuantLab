"""Immutable analytics outputs; unavailable values always have explicit reasons."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from math import isfinite

from quantlab.execution import SimulationResult


class AnalyticsError(ValueError):
    """Invalid equity, trade history, or analytics request."""


@dataclass(frozen=True)
class Metric:
    value: float | Decimal | None
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.value is None:
            if not self.reason:
                raise AnalyticsError("An unavailable metric requires a reason.")
        elif self.reason is not None or not (
            self.value.is_finite() if isinstance(self.value, Decimal) else isfinite(self.value)
        ):
            raise AnalyticsError("A defined metric must be finite, without an unavailable reason.")


@dataclass(frozen=True)
class DailyReturn:
    session: date
    metric: Metric


@dataclass(frozen=True)
class EquityMetrics:
    daily_returns: tuple[DailyReturn, ...]
    cumulative_return: Metric
    annualized_return: Metric
    maximum_drawdown: Metric
    annualized_volatility: Metric
    sharpe_ratio: Metric
    annual_risk_free_rate: Decimal
    annualization_extrapolated: bool
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ClosedTrade:
    entry_order_id: int
    exit_order_id: int
    entry_session: date
    exit_session: date
    quantity: int
    entry_debit: Decimal
    exit_credit: Decimal
    net_pnl: Decimal


@dataclass(frozen=True)
class OpenPosition:
    entry_order_id: int
    entry_session: date
    quantity: int
    entry_debit: Decimal
    last_close: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal


@dataclass(frozen=True)
class TradeStatistics:
    closed_trades: tuple[ClosedTrade, ...]
    closed_trade_count: int
    winning_trades: int
    losing_trades: int
    break_even_trades: int
    win_rate: Metric
    mean_net_pnl: Metric
    open_position: OpenPosition | None


@dataclass(frozen=True)
class PerformanceReport:
    simulation: SimulationResult
    equity: EquityMetrics
    trades: TradeStatistics


@dataclass(frozen=True)
class BenchmarkComparison:
    strategy: PerformanceReport
    benchmark: PerformanceReport
    cumulative_return_difference: Metric
    annualized_return_difference: Metric
    assumptions: tuple[str, ...]
