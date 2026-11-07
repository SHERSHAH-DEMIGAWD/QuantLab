"""Small atomic parameter grids; invalid pairs are never silently skipped."""

from collections.abc import Sequence
from dataclasses import asdict
from decimal import Decimal

from quantlab.strategies import BuyAndHold, SMACrossover, StrategyConfig, TimeSeriesMomentum

from .models import ExperimentError

MAX_CONFIGURATIONS = 100
MAX_AGGREGATE_BARS = 1_000_000


def configuration_key(config: StrategyConfig) -> tuple:
    if type(config) is BuyAndHold:
        return ("buy_and_hold",)
    if type(config) is SMACrossover:
        return ("sma", config.fast_window, config.slow_window)
    if type(config) is TimeSeriesMomentum:
        return ("momentum", config.lookback, config.threshold)
    raise ExperimentError("Only the three existing built-in strategy configurations are supported.")


def validate_configurations(configurations: Sequence[StrategyConfig]) -> tuple[StrategyConfig, ...]:
    if not isinstance(configurations, Sequence) or not 1 <= len(configurations) <= MAX_CONFIGURATIONS:
        raise ExperimentError("Request requires 1..100 strategy configurations.")
    checked = []
    for i, config in enumerate(configurations):
        configuration_key(config)
        try:
            type(config)(**asdict(config))  # Reuse existing validation, including bool/finite checks.
        except ValueError as exc:
            raise ExperimentError(f"Configuration {i}: {exc}") from exc
        checked.append(config)
    if len(set(checked)) != len(checked):
        raise ExperimentError("Duplicate strategy configurations are not permitted.")
    return tuple(sorted(checked, key=configuration_key))


def _grid_size(first: Sequence, second: Sequence) -> None:
    if not isinstance(first, Sequence) or not isinstance(second, Sequence) or not first or not second:
        raise ExperimentError("Grid axes must be nonempty sequences.")
    if len(first) * len(second) > MAX_CONFIGURATIONS:
        raise ExperimentError("Parameter grid exceeds 100 configurations.")


def sma_grid(fast_windows: Sequence[int], slow_windows: Sequence[int]) -> tuple[SMACrossover, ...]:
    _grid_size(fast_windows, slow_windows)
    try:
        return validate_configurations(tuple(SMACrossover(fast, slow) for fast in fast_windows for slow in slow_windows))
    except ValueError as exc:
        raise ExperimentError(f"Invalid SMA grid; entire request rejected: {exc}") from exc


def momentum_grid(lookbacks: Sequence[int], thresholds: Sequence[Decimal] = (Decimal("0"),)) -> tuple[TimeSeriesMomentum, ...]:
    _grid_size(lookbacks, thresholds)
    try:
        return validate_configurations(tuple(TimeSeriesMomentum(lookback, threshold) for lookback in lookbacks for threshold in thresholds))
    except ValueError as exc:
        raise ExperimentError(f"Invalid momentum grid; entire request rejected: {exc}") from exc
