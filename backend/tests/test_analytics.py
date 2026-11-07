"""Independent cost, metric, trade and benchmark references; no market data."""

from dataclasses import asdict, replace
from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN, localcontext
import json
import math
from pathlib import Path

import pytest

from quantlab.analytics import (
    AnalyticsError, Metric, analyze_equity, analyze_simulation, analyze_trades,
    compare_with_buy_and_hold,
)
from quantlab.execution import ExecutionSettings, Fill, SimulationError, simulate
from quantlab.strategies import BuyAndHold, SMACrossover, TimeSeriesMomentum

from quantlab.data import load_dataset

D = Decimal
FIRST = date(2024, 1, 1)
SIDECAR = Path(__file__).parent / "fixtures" / "synthetic_daily.metadata.json"


@pytest.fixture
def market(tmp_path):
    def make(opens=("100", "100", "110"), closes=None, volumes=None):
        closes = opens if closes is None else closes
        volumes = [100] * len(opens) if volumes is None else volumes
        rows = ["date,open,high,low,close,volume\n"]
        for i, (open_, close, volume) in enumerate(zip(opens, closes, volumes, strict=True)):
            rows.append(f"{FIRST + timedelta(days=i)},{open_},{max(D(open_), D(close))},{min(D(open_), D(close))},{close},{volume}\n")
        path = tmp_path / "cost-bars.csv"
        path.write_text("".join(rows), encoding="utf-8")
        return load_dataset(path, SIDECAR)
    return make


def curve(values, dates=None, **kwargs):
    dates = [FIRST + timedelta(days=i) for i in range(len(values))] if dates is None else dates
    return analyze_equity(dates, [D(value) for value in values], **kwargs)


def test_commission_and_slippage_independent_round_trip(market):
    settings = ExecutionSettings(commission_per_fill_usd=D("2"), slippage_bps=D("100"), sell_after_session=FIRST + timedelta(days=1))
    result = simulate(market(), D("1000"), BuyAndHold(), settings)
    buy, sell = result.fills
    assert (buy.quantity, buy.base_open, buy.effective_price, buy.notional, buy.fee, buy.cash_change) == (
        9, D("100"), D("101.000000"), D("909.00"), D("2.00"), D("-911.00"),
    )
    assert (result.valuations[1].cash, result.valuations[1].cost_basis) == (D("89"), D("911"))
    assert (sell.quantity, sell.base_open, sell.effective_price, sell.notional, sell.fee, sell.cash_change) == (
        9, D("110"), D("108.900000"), D("980.10"), D("2.00"), D("978.10"),
    )
    assert (result.final_cash, result.final_shares, result.realized_pnl, result.unrealized_pnl) == (D("1067.10"), 0, D("67.10"), D("0"))
    stats = analyze_simulation(result).trades
    trade, = stats.closed_trades
    assert (trade.entry_debit, trade.exit_credit, trade.net_pnl) == (D("911"), D("978.10"), D("67.10"))
    assert (stats.closed_trade_count, stats.winning_trades, stats.mean_net_pnl.value, stats.win_rate.value) == (1, 1, D("67.10"), 1.0)
    assert result.settings == settings
    assert all(fill.session > result.orders[fill.order_id - 1].decision_session for fill in result.fills)


@pytest.mark.parametrize("capital,quantity,cash", [("1.01", 2, "0.33"), ("1.02", 3, "0.00")])
def test_rounding_edge_affordability_and_half_up_fee(market, capital, quantity, cash):
    settings = ExecutionSettings(commission_per_fill_usd=D("0.005"))
    result = simulate(market(opens=["0.335", "0.335"]), D(capital), settings=settings)
    fill, = result.fills
    assert (fill.quantity, fill.fee, result.final_cash) == (quantity, D("0.01"), D(cash))
    assert fill.notional == (D("0.67") if quantity == 2 else D("1.01"))
    assert all(v.cash >= 0 and v.shares >= 0 for v in result.valuations)


def test_six_decimal_slippage_rounding(market):
    settings = ExecutionSettings(slippage_bps=D("0.005"), sell_after_session=FIRST + timedelta(days=1))
    result = simulate(market(opens=["1", "1", "1"]), D("1000"), settings=settings)
    assert result.fills[0].effective_price == D("1.000001")  # 1.0000005, half up.
    assert result.fills[1].effective_price == D("1.000000")  # .9999995, half up.


def test_rejected_and_expired_orders_do_not_charge_commission(market):
    settings = ExecutionSettings(commission_per_fill_usd=D("2"))
    result = simulate(market(volumes=[100, 0, 100]), D("1"), settings=settings)
    assert [(o.status, o.reason) for o in result.orders] == [
        ("REJECTED", "zero_volume"), ("REJECTED", "insufficient_capital"), ("EXPIRED", "end_of_window"),
    ]
    assert result.fills == () and result.final_cash == D("1")
    held = simulate(market(), D("1000"), settings=replace(settings, sell_after_session=FIRST + timedelta(days=2)))
    assert held.orders[-1].status == "EXPIRED" and held.final_shares == 9
    assert sum(fill.fee for fill in held.fills) == D("2")
    assert held.final_cash == D("98")


def test_sell_proceeds_below_fee_reject_without_modifying_position(market):
    data = market(opens=["0.01", "0.01", "0.000001"])
    result = simulate(data, D("10"), settings=ExecutionSettings(commission_per_fill_usd=D("1"), sell_after_session=FIRST + timedelta(days=1)))
    assert (result.orders[-1].status, result.orders[-1].reason) == ("REJECTED", "proceeds_below_fee")
    assert len(result.fills) == 1
    assert (result.final_cash, result.final_shares, result.realized_pnl) == (D("0"), 900, D("0"))
    assert analyze_simulation(result).trades.closed_trade_count == 0


def test_valid_slippage_that_rounds_sell_price_to_zero_rejects(market):
    result = simulate(
        market(opens=["0.000001"] * 3), D("1"),
        settings=ExecutionSettings(slippage_bps=D("9999.999999"), sell_after_session=FIRST + timedelta(days=1)),
    )
    assert (result.orders[-1].status, result.orders[-1].reason, result.orders[-1].effective_price) == ("REJECTED", "nonpositive_effective_price", D("0.000000"))
    assert len(result.fills) == 1 and result.final_shares == 500000


def test_sell_gross_equal_to_fee_is_valid_and_zero_equity_is_explicit(market):
    result = simulate(market(opens=["1"] * 4), D("2"), settings=ExecutionSettings(commission_per_fill_usd=D("1"), sell_after_session=FIRST + timedelta(days=1)))
    assert len(result.fills) == 2 and result.fills[-1].cash_change == D("0")
    assert (result.final_cash, result.final_shares, result.final_equity) == (D("0"), 0, D("0"))
    report = analyze_simulation(result)
    assert report.trades.closed_trades[0].net_pnl == D("-2")
    assert report.equity.cumulative_return.value == report.equity.annualized_return.value == -1.0
    assert report.equity.daily_returns[-1].metric.reason == "previous_equity_zero"
    assert report.equity.annualized_volatility.reason == "undefined_daily_return"


@pytest.mark.parametrize("field,value", [
    ("commission_per_fill_usd", D("Infinity")), ("commission_per_fill_usd", D("1E22")),
    ("slippage_bps", D("10000.000001")), ("slippage_bps", D("0.0000001")),
])
def test_unsupported_cost_inputs_fail_explicitly(market, field, value):
    with pytest.raises(SimulationError, match=field):
        simulate(market(), D("1000"), settings=replace(ExecutionSettings(), **{field: value}))


def test_zero_defaults_and_nonzero_runs_are_deterministic_context_independent(market):
    data = market()
    defaults = simulate(data, D("1000"))
    assert defaults == simulate(data, D("1000"), settings=ExecutionSettings(commission_per_fill_usd=D("0"), slippage_bps=D("0")))
    assert (defaults.final_cash, defaults.final_shares, defaults.final_equity) == (D("0"), 10, D("1100"))
    settings = ExecutionSettings(commission_per_fill_usd=D("2"), slippage_bps=D("100"))
    expected = analyze_simulation(simulate(data, D("1000"), settings=settings))
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        assert analyze_simulation(simulate(data, D("1000"), settings=settings)) == expected


def test_independent_equity_reference_returns_drawdown_volatility_sharpe():
    result = curve(["100", "110", "99"])
    assert [point.metric.value for point in result.daily_returns] == [0.1, -0.1]
    assert result.cumulative_return.value == -0.01
    assert result.maximum_drawdown.value == 0.1
    # Sample variance = (.1^2 + (-.1)^2)/(2-1) = .02; annual variance = 5.04.
    assert result.annualized_volatility.value == pytest.approx(math.sqrt(5.04), rel=1e-13)
    assert result.sharpe_ratio.value == 0.0
    assert result.annualized_return.value == pytest.approx(0.99 ** (365.25 / 2) - 1, rel=1e-13)
    assert result.annualization_extrapolated and result.warnings


@pytest.mark.parametrize("rate,base", [("0.1", 1.1), ("-0.1", 0.9)])
def test_nonzero_risk_free_rate_uses_effective_daily_compounding(rate, base):
    result = curve(["100", "110", "99"], annual_risk_free_rate=D(rate))
    expected_daily_rf = base ** (1 / 252) - 1
    expected_sharpe = math.sqrt(252) * -expected_daily_rf / math.sqrt(0.02)
    assert result.sharpe_ratio.value == pytest.approx(expected_sharpe, rel=1e-10)
    assert result.annual_risk_free_rate == D(rate)


@pytest.mark.parametrize("values", [["100", "100", "100"], ["100", "110", "121"]])
def test_zero_variance_does_not_create_infinite_sharpe(values):
    result = curve(values)
    assert result.annualized_volatility.value == 0.0
    assert result.sharpe_ratio.value is None and result.sharpe_ratio.reason == "zero_return_variance"


def test_one_valuation_has_no_return_sample_or_annualization():
    result = curve(["100"])
    assert result.daily_returns == ()
    assert result.cumulative_return.value == result.maximum_drawdown.value == 0.0
    assert result.annualized_return.reason == "insufficient_evaluation_period"
    assert result.annualized_volatility.reason == result.sharpe_ratio.reason == "insufficient_return_observations"


def test_two_valuations_and_calendar_day_annualization():
    result = curve(["100", "110"], dates=[date(2024, 1, 1), date(2025, 1, 1)])
    assert len(result.daily_returns) == 1
    assert result.annualized_volatility.value is result.sharpe_ratio.value is None
    assert result.annualized_return.value == pytest.approx(1.1 ** (365.25 / 366) - 1, rel=1e-13)
    assert not result.annualization_extrapolated


def test_drawdown_uses_initial_peak_and_zero_terminal_equity():
    result = curve(["100", "90", "80", "95", "0"])
    assert result.maximum_drawdown.value == 1.0
    assert result.cumulative_return.value == result.annualized_return.value == -1.0
    assert curve(["100", "90", "80", "95"]).maximum_drawdown.value == 0.2


def test_float_overflow_and_unrepresentable_risk_rate_have_reasons():
    high_growth = curve(["1", "999999999999999999999"])
    assert high_growth.annualized_return.value is None and high_growth.annualized_return.reason
    unrepresentable = curve(["100", "110", "99"], annual_risk_free_rate=D("1E9999"))
    assert unrepresentable.sharpe_ratio.reason == "risk_free_rate_not_representable"
    assert unrepresentable.annualized_volatility.value is not None
    json.dumps(asdict(high_growth), default=str, allow_nan=False)


@pytest.mark.parametrize("rate", [D("-1"), D("-2"), D("NaN"), D("Infinity"), 0.0, "0"])
def test_invalid_risk_free_rates_rejected(rate):
    with pytest.raises(AnalyticsError, match="risk_free"):
        curve(["100", "110", "99"], annual_risk_free_rate=rate)


@pytest.mark.parametrize("values,dates", [
    ([], []), (["100", "110"], [FIRST]),
    (["100", "110"], [FIRST, FIRST]),
    (["100", "110"], [FIRST + timedelta(days=1), FIRST]),
    (["100", "-1"], None), (["0", "1"], None), (["100", "NaN"], None),
])
def test_invalid_equity_inputs_are_not_hidden_as_metrics(values, dates):
    with pytest.raises(AnalyticsError):
        curve(values, dates=dates)


def test_no_trades_and_open_position_are_not_completed_wins(market):
    no_trades = analyze_simulation(simulate(market(), D("1000"), SMACrossover(2, 20)))
    assert no_trades.trades.closed_trade_count == 0 and no_trades.trades.open_position is None
    assert no_trades.trades.win_rate.value is None and no_trades.trades.mean_net_pnl.value is None
    held = analyze_simulation(simulate(market(), D("1000"), settings=ExecutionSettings(commission_per_fill_usd=D("2"))))
    position = held.trades.open_position
    assert held.trades.closed_trade_count == 0 and held.trades.win_rate.reason == "no_closed_trades"
    assert (position.quantity, position.entry_debit, position.market_value, position.unrealized_pnl) == (9, D("902"), D("990"), D("88"))
    assert held.simulation.realized_pnl == D("0")


def test_win_loss_break_even_and_mean_pnl_are_net_of_both_fees():
    rows = [
        ("BUY", "10", "-11"), ("SELL", "15", "14"),
        ("BUY", "10", "-11"), ("SELL", "9", "8"),
        ("BUY", "10", "-11"), ("SELL", "12", "11"),
        ("BUY", "10", "-11"),
    ]
    fills = tuple(Fill(i + 1, FIRST + timedelta(days=i), side, 1, D(notional), D(notional), D(notional), D("1"), D(change))
                  for i, (side, notional, change) in enumerate(rows))
    stats = analyze_trades(fills, D("12"))
    assert [trade.net_pnl for trade in stats.closed_trades] == [D("3"), D("-3"), D("0")]
    assert (stats.closed_trade_count, stats.winning_trades, stats.losing_trades, stats.break_even_trades) == (3, 1, 1, 1)
    assert stats.win_rate.value == pytest.approx(1 / 3)
    assert stats.mean_net_pnl.value == D("0")
    assert stats.open_position.unrealized_pnl == D("1")
    with pytest.raises(AnalyticsError, match="full-exit"):
        analyze_trades(fills[1:2], D("12"))


@pytest.mark.parametrize("config,equity,difference", [
    (SMACrossover(2, 3), "2168.26", -0.216),
    (TimeSeriesMomentum(1), "1301.58", -1.08268),
])
def test_benchmark_same_costs_window_and_independent_final_values(market, config, equity, difference):
    data = market(
        opens=["10", "10", "10", "15", "9", "10", "11", "12"],
        closes=["10", "12", "14", "8", "6", "20", "22", "24"],
    )
    settings = ExecutionSettings(start_date=FIRST + timedelta(days=1), end_date=FIRST + timedelta(days=7), commission_per_fill_usd=D("0.75"), slippage_bps=D("10"))
    result = compare_with_buy_and_hold(data, D("1000"), config, settings)
    selected, benchmark = result.strategy.simulation, result.benchmark.simulation
    assert selected.settings == benchmark.settings == settings
    assert selected.dataset_id == benchmark.dataset_id == data.report.dataset_id
    assert (selected.start_date, selected.end_date, selected.initial_capital) == (benchmark.start_date, benchmark.end_date, benchmark.initial_capital)
    assert [v.session for v in selected.valuations] == [v.session for v in benchmark.valuations]
    # Benchmark: 99 shares at 10.01, 990.99 notional + .75 fee -> 8.26 residual.
    assert (benchmark.final_cash, benchmark.final_shares, benchmark.final_equity) == (D("8.26"), 99, D("2384.26"))
    assert selected.final_equity == D(equity)
    assert result.cumulative_return_difference.value == pytest.approx(difference, rel=1e-13)
    assert result == compare_with_buy_and_hold(data, D("1000"), config, settings)
    assert benchmark.final_shares > 0  # Identical terminal convention, no forced sale.


def test_benchmark_same_strategy_zero_difference_and_diagnostic_rejection(market):
    result = compare_with_buy_and_hold(market(), D("1000"), BuyAndHold())
    assert result.strategy == result.benchmark
    assert result.cumulative_return_difference.value == result.annualized_return_difference.value == 0.0
    with pytest.raises(AnalyticsError, match="diagnostic"):
        compare_with_buy_and_hold(market(), D("1000"), BuyAndHold(), ExecutionSettings(sell_after_session=FIRST))


def test_benchmark_unavailable_annual_difference_and_no_public_nonfinite_values(market):
    data = market(opens=["1", "1"], closes=["1", "999999"])
    result = compare_with_buy_and_hold(data, D("1000"), SMACrossover(2, 3))
    assert result.strategy.equity.annualized_return.value == 0.0
    assert result.benchmark.equity.annualized_return.value is None
    assert result.annualized_return_difference.reason == "component_annualized_return_unavailable"
    assert result.cumulative_return_difference.value == -999998.0
    json.dumps(asdict(result), default=str, allow_nan=False)
    with pytest.raises(AnalyticsError, match="risk_free"):
        compare_with_buy_and_hold(data, D("1000"), SMACrossover(2, 3), annual_risk_free_rate=D("-1"))


def test_nonzero_cost_future_changes_preserve_prior_signals_and_fills(market):
    settings = ExecutionSettings(commission_per_fill_usd=D("2"), slippage_bps=D("100"))
    before = simulate(market(opens=["10", "12", "14", "8"], closes=["10", "12", "14", "8"]), D("1000"), SMACrossover(1, 2), settings)
    changed = simulate(market(opens=["10", "12", "14", "80"], closes=["10", "12", "14", "80"]), D("1000"), SMACrossover(1, 2), settings)
    assert before.decisions[:3] == changed.decisions[:3]
    assert before.fills == changed.fills  # Entry already completed before the changed session.


def test_metric_record_never_accepts_nan_infinity_or_unexplained_absence():
    for value in (float("nan"), float("inf"), D("Infinity"), None):
        with pytest.raises(AnalyticsError):
            Metric(value)
