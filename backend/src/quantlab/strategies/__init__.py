"""Validated built-in configurations and a close-only typed decision interface."""

from .models import BuyAndHold, SMACrossover, StrategyConfig, StrategyError, Target, TimeSeriesMomentum
from .rules import DecisionRule, create_rule

__all__ = [
    "BuyAndHold", "SMACrossover", "TimeSeriesMomentum", "StrategyConfig",
    "StrategyError", "Target", "DecisionRule", "create_rule",
]
