"""D07 equity analytics; exact input ratios cross one documented float boundary."""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from fractions import Fraction
import math
from statistics import fmean, stdev

from .models import AnalyticsError, DailyReturn, EquityMetrics, Metric

ASSUMPTIONS = (
    "Return values are fractions, not percentages; input closing equity is not display-rounded.",
    "Consecutive observed closes only; no artificial first zero return or silent removal of undefined returns.",
    "Annual return uses elapsed calendar days and 365.25; sample volatility and Sharpe use 252 sessions/year.",
    "Exact equity ratios convert to float for statistics/powers; trade and cash accounting remain Decimal.",
    "Sharpe uses a constant effective annual risk-free rate converted by (1+rf)^(1/252)-1.",
    "These are price-return statistics excluding dividends; they do not establish significance or predictability.",
)


def finite_metric(value: float) -> Metric:
    return Metric(value) if math.isfinite(value) else Metric(None, "numerical_overflow")


def ratio_metric(value: Fraction) -> Metric:
    try:
        return finite_metric(float(value))
    except OverflowError:
        return Metric(None, "numerical_overflow")


def validate_risk_free_rate(rate: Decimal) -> None:
    if not isinstance(rate, Decimal) or not rate.is_finite() or rate <= -1:
        raise AnalyticsError("annual_risk_free_rate must be a finite Decimal greater than -1.")


def _annualized(final: Decimal, initial: Decimal, days: int, count: int) -> Metric:
    if count < 2 or days <= 0:
        return Metric(None, "insufficient_evaluation_period")
    if final == 0:
        return Metric(-1.0)
    ratio = Fraction(final) / Fraction(initial)
    try:
        # log1p preserves small changes; use the positive ratio for near-total losses.
        change = float(ratio - 1)
        log_ratio = math.log1p(change) if change > -1 else math.log(float(ratio))
        return finite_metric(math.expm1(log_ratio * (365.25 / days)))
    except (OverflowError, ValueError):
        return Metric(None, "numerical_range_unavailable")


def _risk_daily(rate: Decimal) -> Metric:
    converted = float(rate)
    if not math.isfinite(converted) or converted <= -1:
        return Metric(None, "risk_free_rate_not_representable")
    return finite_metric(math.expm1(math.log1p(converted) / 252))


def analyze_equity(
    dates: Sequence[date], equities: Sequence[Decimal], *,
    annual_risk_free_rate: Decimal = Decimal("0"),
) -> EquityMetrics:
    """Allow one valuation; reject invalid input, never fabricate missing statistics."""
    validate_risk_free_rate(annual_risk_free_rate)
    dates, equities = tuple(dates), tuple(equities)
    if not dates or len(dates) != len(equities):
        raise AnalyticsError("Expected matching, nonempty dates and equities.")
    previous_date = None
    for session, equity in zip(dates, equities):
        if type(session) is not date or (previous_date is not None and session <= previous_date):
            raise AnalyticsError("Valuation dates must be strictly ascending unique dates.")
        if not isinstance(equity, Decimal) or not equity.is_finite() or equity < 0:
            raise AnalyticsError("Equity must be finite nonnegative Decimal; negative equity is an accounting failure.")
        previous_date = session
    if equities[0] <= 0:
        raise AnalyticsError("Initial equity must be positive.")

    returns = []
    peak = equities[0]
    greatest_drawdown = Fraction(0)
    previous_equity = None
    for session, equity in zip(dates, equities):
        peak = max(peak, equity)
        greatest_drawdown = max(greatest_drawdown, (Fraction(peak) - Fraction(equity)) / Fraction(peak))
        if previous_equity is not None:
            metric = (ratio_metric(Fraction(equity) / Fraction(previous_equity) - 1)
                      if previous_equity > 0 else Metric(None, "previous_equity_zero"))
            returns.append(DailyReturn(session, metric))
        previous_equity = equity

    if len(returns) < 2:
        volatility = sharpe = Metric(None, "insufficient_return_observations")
    elif any(point.metric.value is None for point in returns):
        volatility = sharpe = Metric(None, "undefined_daily_return")
    else:
        values = [point.metric.value for point in returns]
        try:
            deviation = stdev(values)
            volatility = finite_metric(deviation * math.sqrt(252))
            daily_rf = _risk_daily(annual_risk_free_rate)
            if deviation == 0:
                sharpe = Metric(None, "zero_return_variance")
            elif daily_rf.value is None:
                sharpe = daily_rf
            else:
                # Subtracting a constant does not change the sample standard deviation.
                sharpe = finite_metric(math.sqrt(252) * ((fmean(values) - daily_rf.value) / deviation))
        except (OverflowError, ValueError):
            volatility = sharpe = Metric(None, "numerical_range_unavailable")

    days = (dates[-1] - dates[0]).days
    extrapolated = 0 < days < 365.25
    warnings = ("Annualized return over less than 365.25 calendar days is extrapolation.",) if extrapolated else ()
    return EquityMetrics(
        daily_returns=tuple(returns),
        cumulative_return=ratio_metric(Fraction(equities[-1]) / Fraction(equities[0]) - 1),
        annualized_return=_annualized(equities[-1], equities[0], days, len(equities)),
        maximum_drawdown=ratio_metric(greatest_drawdown),
        annualized_volatility=volatility, sharpe_ratio=sharpe,
        annual_risk_free_rate=annual_risk_free_rate, annualization_extrapolated=extrapolated,
        assumptions=ASSUMPTIONS, warnings=warnings,
    )
