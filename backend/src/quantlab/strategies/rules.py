"""Streaming close-only rules. Each factory call owns fresh, bounded history."""

from collections import deque
from datetime import date
from decimal import Decimal
from typing import Protocol

from .models import BuyAndHold, SMACrossover, StrategyConfig, StrategyError, Target, TimeSeriesMomentum


class DecisionRule(Protocol):
    def on_close(self, session: date, close: Decimal, shares: int) -> Target:
        """Receive the current completed close and position, never future bars."""
        ...


def _microunits(close: Decimal) -> int:
    """Exact conversion, independent of ambient Decimal arithmetic precision."""
    if not isinstance(close, Decimal) or not close.is_finite() or close <= 0:
        raise StrategyError("close must be a positive finite Decimal.")
    numerator, denominator = close.as_integer_ratio()
    units, remainder = divmod(numerator * 1_000_000, denominator)
    if remainder:
        raise StrategyError("close supports at most six meaningful fractional places.")
    return units


class _BuyAndHoldRule:
    def __init__(self, sell_after_session: date | None) -> None:
        self.sell_after_session = sell_after_session

    def on_close(self, session: date, close: Decimal, shares: int) -> Target:
        if self.sell_after_session is not None and session >= self.sell_after_session:
            return "FLAT" if session == self.sell_after_session else "HOLD"
        return "LONG" if shares == 0 else "HOLD"


class _SMARule:
    def __init__(self, config: SMACrossover) -> None:
        self.config = config
        self.fast: deque[int] = deque()
        self.slow: deque[int] = deque()
        self.fast_sum = 0
        self.slow_sum = 0

    def on_close(self, session: date, close: Decimal, shares: int) -> Target:
        units = _microunits(close)
        self.fast.append(units)
        self.slow.append(units)
        self.fast_sum += units
        self.slow_sum += units
        if len(self.fast) > self.config.fast_window:
            self.fast_sum -= self.fast.popleft()
        if len(self.slow) > self.config.slow_window:
            self.slow_sum -= self.slow.popleft()
        if len(self.slow) < self.config.slow_window:
            return "HOLD"
        # Compare exact averages by cross multiplication; rounded quotients can invent ties.
        fast_scaled = self.fast_sum * self.config.slow_window
        slow_scaled = self.slow_sum * self.config.fast_window
        if fast_scaled > slow_scaled:
            return "LONG"
        if fast_scaled < slow_scaled:
            return "FLAT"
        return "HOLD"


class _MomentumRule:
    def __init__(self, config: TimeSeriesMomentum) -> None:
        self.config = config
        self.closes: deque[int] = deque()
        self.threshold_numerator, self.threshold_denominator = config.threshold.as_integer_ratio()

    def on_close(self, session: date, close: Decimal, shares: int) -> Target:
        units = _microunits(close)
        self.closes.append(units)
        if len(self.closes) > self.config.lookback + 1:
            self.closes.popleft()
        if len(self.closes) < self.config.lookback + 1:
            return "HOLD"
        previous = self.closes[0]
        # (close / previous - 1) > k, with positive previous and exact rational k.
        return "LONG" if (units - previous) * self.threshold_denominator > self.threshold_numerator * previous else "FLAT"


def create_rule(config: StrategyConfig, *, sell_after_session: date | None = None) -> DecisionRule:
    """Construct only approved built-ins, never an arbitrary callback or plugin."""
    if type(config) is BuyAndHold:
        return _BuyAndHoldRule(sell_after_session)
    if sell_after_session is not None:
        raise StrategyError("sell_after_session is available only for diagnostic buy-and-hold.")
    if type(config) is SMACrossover:
        return _SMARule(config)
    if type(config) is TimeSeriesMomentum:
        return _MomentumRule(config)
    raise StrategyError("Expected BuyAndHold, SMACrossover, or TimeSeriesMomentum configuration.")
