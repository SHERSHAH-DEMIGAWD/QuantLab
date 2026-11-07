"""Small immutable request and result records for the daily research engine."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from quantlab.data import Metadata
from quantlab.strategies import StrategyConfig, Target


class SimulationError(ValueError):
    """An invalid request, ineligible dataset, or unsupported numeric range."""


@dataclass(frozen=True)
class ExecutionSettings:
    start_date: date | None = None
    end_date: date | None = None
    commission_per_fill_usd: Decimal = Decimal("0.00")
    slippage_bps: Decimal = Decimal("0")
    acknowledge_unverified_coverage: bool = False
    # A single diagnostic exit, not a general strategy or a recurring sell rule.
    sell_after_session: date | None = None
    # Indicator-only history; no orders, positions or valuations in this interval.
    warmup_start_date: date | None = None
    warmup_end_date: date | None = None


@dataclass(frozen=True)
class Decision:
    session: date
    target: Target
    cash: Decimal
    shares: int


@dataclass(frozen=True)
class Order:
    order_id: int
    decision_session: date
    eligible_session: date | None
    target: Target
    side: Literal["BUY", "SELL"]
    budget: Decimal | None
    requested_shares: int | None
    status: Literal["PENDING", "FILLED", "REJECTED", "EXPIRED"] = "PENDING"
    outcome_session: date | None = None
    reason: str | None = None
    base_open: Decimal | None = None
    effective_price: Decimal | None = None


@dataclass(frozen=True)
class Fill:
    order_id: int
    session: date
    side: Literal["BUY", "SELL"]
    quantity: int
    base_open: Decimal
    effective_price: Decimal
    notional: Decimal
    fee: Decimal
    cash_change: Decimal


@dataclass(frozen=True)
class DailyValuation:
    session: date
    cash: Decimal
    shares: int
    close: Decimal
    market_value: Decimal
    equity: Decimal
    cost_basis: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal


@dataclass(frozen=True)
class SimulationResult:
    engine_version: str
    dataset_id: str
    source_sha256: str
    metadata_sha256: str
    metadata: Metadata
    start_date: date
    end_date: date
    initial_capital: Decimal
    settings: ExecutionSettings
    strategy: StrategyConfig
    final_cash: Decimal
    final_shares: int
    final_equity: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    valuations: tuple[DailyValuation, ...]
    decisions: tuple[Decision, ...]
    orders: tuple[Order, ...]
    fills: tuple[Fill, ...]
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]
    warmup_start: date | None = None
    warmup_end: date | None = None
    warmup_bars: int = 0
