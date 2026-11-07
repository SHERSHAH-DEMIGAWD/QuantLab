"""Immutable configurations for the three approved built-in decision rules."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

Target = Literal["LONG", "FLAT", "HOLD"]


class StrategyError(ValueError):
    """Invalid built-in strategy configuration or decision input."""


def _positive_integer(value: int, field: str) -> None:
    if type(value) is not int or value <= 0:
        raise StrategyError(f"{field} must be a positive integer (not bool).")


@dataclass(frozen=True)
class BuyAndHold:
    """Fresh LONG while flat, HOLD after entry; no strategy parameters."""


@dataclass(frozen=True)
class SMACrossover:
    """D08 target state, including initial bullish entry; not crossing events."""

    fast_window: int
    slow_window: int

    def __post_init__(self) -> None:
        _positive_integer(self.fast_window, "fast_window")
        _positive_integer(self.slow_window, "slow_window")
        if self.fast_window >= self.slow_window:
            raise StrategyError("fast_window must be less than slow_window.")


@dataclass(frozen=True)
class TimeSeriesMomentum:
    lookback: int
    threshold: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        _positive_integer(self.lookback, "lookback")
        if not isinstance(self.threshold, Decimal) or not self.threshold.is_finite():
            raise StrategyError("threshold must be a finite Decimal.")


StrategyConfig = BuyAndHold | SMACrossover | TimeSeriesMomentum
