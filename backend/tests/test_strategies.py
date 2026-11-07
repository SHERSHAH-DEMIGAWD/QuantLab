"""Independent signal tables and integrations through the single execution engine."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN, localcontext
from pathlib import Path

import pytest

from quantlab.data import load_dataset
from quantlab.execution import ExecutionSettings, MAX_CAPITAL, MAX_PRICE, SimulationError, simulate, simulate_buy_and_hold
from quantlab.strategies import BuyAndHold, SMACrossover, StrategyError, TimeSeriesMomentum, create_rule

D = Decimal
FIRST = date(2024, 1, 1)
METADATA_PATH = Path(__file__).parent / "fixtures" / "synthetic_daily.metadata.json"
CLOSES = ["10", "12", "14", "8", "6", "20", "22", "24"]
OPENS = ["10", "10", "10", "15", "9", "10", "11", "12"]


@pytest.fixture
def market(tmp_path):
    def make(closes=CLOSES, opens=None, volumes=None):
        opens = ["10"] * len(closes) if opens is None else opens
        volumes = [100] * len(closes) if volumes is None else volumes
        path = tmp_path / "strategy-bars.csv"
        rows = ["date,open,high,low,close,volume\n"]
        for i, (open_, close, volume) in enumerate(zip(opens, closes, volumes, strict=True)):
            high, low = max(D(open_), D(close)), min(D(open_), D(close))
            rows.append(f"{FIRST + timedelta(days=i)},{open_},{high},{low},{close},{volume}\n")
        path.write_text("".join(rows), encoding="utf-8")
        return load_dataset(path, METADATA_PATH)
    return make


def signals(config, closes):
    rule = create_rule(config)
    return [rule.on_close(FIRST + timedelta(days=i), D(close), 0) for i, close in enumerate(closes)]


def test_sma_reference_averages_and_rolling_eviction():
    # At the fourth close: fast=(3+4)/2=3.5, slow=(1+2+3+4)/4=2.5.
    # At the sixth: fast=(3+2)/2=2.5, slow=(3+4+3+2)/4=3 -> FLAT.
    assert signals(SMACrossover(2, 4), ["1", "2", "3", "4", "3", "2", "1", "2", "3", "4"]) == [
        "HOLD", "HOLD", "HOLD", "LONG", "LONG", "FLAT", "FLAT", "FLAT", "LONG", "LONG",
    ]


def test_sma_equality_holds_and_initial_bullish_state_enters():
    assert signals(SMACrossover(2, 3), ["10", "10", "10", "10"]) == ["HOLD"] * 4
    assert signals(SMACrossover(2, 3), ["10", "12", "14"]) == ["HOLD", "HOLD", "LONG"]


def test_momentum_reference_lookback_and_default_zero_threshold():
    # L=2: 12/10-1=.2; 10/11-1<0; 12/12-1=0; 9/10-1=-.1.
    assert signals(TimeSeriesMomentum(2), ["10", "11", "12", "10", "12", "9"]) == [
        "HOLD", "HOLD", "LONG", "FLAT", "FLAT", "FLAT",
    ]


def test_momentum_positive_negative_and_equal_thresholds():
    # Two exact +10% observations equal k, so neither enters.
    assert signals(TimeSeriesMomentum(1, D("0.1")), ["100", "110", "121", "108.9", "120"]) == [
        "HOLD", "FLAT", "FLAT", "FLAT", "LONG",
    ]
    # Exact -10% equals negative k; -1/81 is greater than -10%.
    assert signals(TimeSeriesMomentum(1, D("-0.1")), ["100", "90", "81", "80"]) == [
        "HOLD", "FLAT", "FLAT", "LONG",
    ]


def test_exact_comparisons_do_not_round_away_small_differences():
    assert signals(TimeSeriesMomentum(1, D("0.3333333333333333333333333333")), ["3", "4"]) == ["HOLD", "LONG"]
    assert signals(TimeSeriesMomentum(1, D("0.3333333333333333333333333334")), ["3", "4"]) == ["HOLD", "FLAT"]
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        assert signals(SMACrossover(2, 3), ["999999.999999", "999999.999998", "999999.999997"]) == ["HOLD", "HOLD", "FLAT"]
        assert signals(TimeSeriesMomentum(1, D("0.1")), ["100", "110", "111"]) == ["HOLD", "FLAT", "FLAT"]


@pytest.mark.parametrize("factory", [
    lambda: SMACrossover(0, 3), lambda: SMACrossover(-1, 3),
    lambda: SMACrossover(True, 3), lambda: SMACrossover(1.0, 3),
    lambda: SMACrossover(2, 2), lambda: SMACrossover(3, 2),
    lambda: SMACrossover(1, 0), lambda: SMACrossover(1, "3"),
    lambda: TimeSeriesMomentum(0), lambda: TimeSeriesMomentum(False),
    lambda: TimeSeriesMomentum("2"), lambda: TimeSeriesMomentum(1, D("NaN")),
    lambda: TimeSeriesMomentum(1, D("Infinity")), lambda: TimeSeriesMomentum(1, D("sNaN")),
    lambda: TimeSeriesMomentum(1, 0.1), lambda: TimeSeriesMomentum(1, "0"),
])
def test_parameters_reject_invalid_values(factory):
    with pytest.raises(StrategyError):
        factory()


def test_configuration_is_immutable_and_only_builtin_rules_are_accepted(market):
    config = SMACrossover(2, 3)
    with pytest.raises(FrozenInstanceError):
        config.fast_window = 1
    with pytest.raises(SimulationError, match="configuration"):
        simulate(market(), D("1000"), strategy=lambda: "LONG")
    with pytest.raises(SimulationError, match="diagnostic"):
        simulate(market(), D("1000"), config, ExecutionSettings(sell_after_session=FIRST))


def test_sma_buy_exit_reentry_and_no_redundant_execution(market):
    data = market(opens=OPENS)
    result = simulate(data, D("1000"), SMACrossover(2, 3))
    assert [d.target for d in result.decisions] == ["HOLD", "HOLD", "LONG", "FLAT", "FLAT", "LONG", "LONG", "LONG"]
    assert [(f.side, f.session, f.quantity, f.notional) for f in result.fills] == [
        ("BUY", FIRST + timedelta(days=3), 66, D("990")),
        ("SELL", FIRST + timedelta(days=4), 66, D("594")),
        ("BUY", FIRST + timedelta(days=6), 54, D("594")),
    ]
    assert len(result.orders) == 3  # FLAT while flat / LONG while long do not trade.
    assert (result.final_cash, result.final_shares, result.final_equity) == (D("10"), 54, D("1306"))
    assert (result.realized_pnl, result.unrealized_pnl) == (D("-396"), D("702"))
    assert result.strategy == SMACrossover(2, 3)
    for fill in result.fills:
        order = result.orders[fill.order_id - 1]
        assert fill.session == order.eligible_session > order.decision_session
    for valuation in result.valuations:
        assert valuation.cash >= 0 and type(valuation.shares) is int and valuation.shares >= 0
        assert valuation.equity == valuation.cash + valuation.shares * valuation.close


def test_momentum_buy_exit_reentry_with_hand_calculated_cash(market):
    data = market(["10", "12", "12", "9", "18", "20"], opens=["10", "10", "13", "8", "10", "19"])
    result = simulate(data, D("100"), TimeSeriesMomentum(1))
    assert [d.target for d in result.decisions] == ["HOLD", "LONG", "FLAT", "FLAT", "LONG", "LONG"]
    assert [(f.side, f.quantity, f.notional) for f in result.fills] == [
        ("BUY", 7, D("91")), ("SELL", 7, D("56")), ("BUY", 3, D("57")),
    ]
    assert (result.final_cash, result.final_shares, result.final_equity) == (D("8"), 3, D("68"))
    assert (result.realized_pnl, result.unrealized_pnl) == (D("-35"), D("3"))


@pytest.mark.parametrize("config", [SMACrossover(2, 20), TimeSeriesMomentum(20)])
def test_warmup_longer_than_window_never_trades(market, config):
    result = simulate(market(), D("1000"), config)
    assert [d.target for d in result.decisions] == ["HOLD"] * 8
    assert result.orders == result.fills == ()
    assert result.final_equity == D("1000")


def test_sma_equal_averages_hold_an_existing_position(market):
    result = simulate(market(["10", "12", "14", "14", "14", "14"]), D("1000"), SMACrossover(2, 3))
    assert [d.target for d in result.decisions] == ["HOLD", "HOLD", "LONG", "LONG", "HOLD", "HOLD"]
    assert len(result.orders) == len(result.fills) == 1
    assert result.final_shares == 100


def test_final_bearish_signal_expires_without_forced_liquidation(market):
    result = simulate(market(["10", "12", "14", "8"]), D("1000"), SMACrossover(2, 3))
    assert [(o.side, o.status) for o in result.orders] == [("BUY", "FILLED"), ("SELL", "EXPIRED")]
    assert (result.final_shares, result.final_cash, result.final_equity) == (100, D("0"), D("800"))


@pytest.mark.parametrize("config", [BuyAndHold(), SMACrossover(2, 3), TimeSeriesMomentum(1)])
def test_new_long_after_zero_volume_rejection_is_a_fresh_order(market, config):
    result = simulate(market(["10", "12", "14", "15", "16"], volumes=[100, 0, 0, 0, 100]), D("1000"), config)
    assert result.orders[-1].status == "FILLED"
    assert result.orders[-1].order_id > 1
    assert all(o.status == "REJECTED" and o.reason == "zero_volume" for o in result.orders[:-1])
    assert [o.order_id for o in result.orders] == list(range(1, len(result.orders) + 1))
    assert result.fills[0].order_id == result.orders[-1].order_id
    assert len(result.fills) == 1


def test_buy_hold_wrapper_keeps_phase2_reference_and_diagnostic_behavior(market):
    data = market(["100", "105", "109"], opens=["100", "103", "110"])
    result = simulate(data, D("1000"), BuyAndHold())
    assert result == simulate_buy_and_hold(data, D("1000")) == simulate(data, D("1000"))
    assert [d.target for d in result.decisions] == ["LONG", "HOLD", "HOLD"]
    assert (result.final_cash, result.final_shares, result.valuations[1].equity) == (D("73"), 9, D("1018"))
    settings = ExecutionSettings(sell_after_session=FIRST + timedelta(days=1))
    diagnostic = simulate_buy_and_hold(data, D("1000"), settings)
    assert diagnostic == simulate(data, D("1000"), BuyAndHold(), settings)
    assert (diagnostic.final_cash, diagnostic.final_shares) == (D("1063"), 0)


@pytest.mark.parametrize("config", [BuyAndHold(), SMACrossover(2, 3), TimeSeriesMomentum(2)])
def test_determinism_dataset_event_immutability_and_run_isolation(market, config):
    data = market(opens=OPENS)
    original = deepcopy(data)
    result = simulate(data, D("1000"), config)
    previous_decisions = deepcopy(result.decisions)
    simulate(market(["50", "40", "30", "20"]), D("2000"), config)
    assert simulate(data, D("1000"), config) == result
    assert data == original and result.decisions == previous_decisions
    with pytest.raises(FrozenInstanceError):
        result.decisions[0].shares = 10


@pytest.mark.parametrize("config", [BuyAndHold(), SMACrossover(2, 3), TimeSeriesMomentum(1)])
def test_changed_future_prices_preserve_earlier_signals_and_completed_fills(market, config):
    data = market(opens=OPENS)
    original = simulate(data, D("1000"), config)
    changed = simulate(market(CLOSES[:6] + ["500", "400"], opens=OPENS[:6] + ["100", "200"]), D("1000"), config)
    cutoff = FIRST + timedelta(days=5)
    assert original.decisions[:6] == changed.decisions[:6]
    assert original.valuations[:6] == changed.valuations[:6]
    assert tuple(f for f in original.fills if f.session <= cutoff) == tuple(f for f in changed.fills if f.session <= cutoff)
    assert tuple(o for o in original.orders if o.outcome_session <= cutoff) == tuple(o for o in changed.orders if o.outcome_session <= cutoff)


@pytest.mark.parametrize("config", [SMACrossover(2, 3), TimeSeriesMomentum(1)])
@pytest.mark.parametrize("volume,status", [(100, "FILLED"), (0, "REJECTED")])
def test_appending_future_preserves_prefix_but_resolves_final_pending_order(market, config, volume, status):
    prefix = simulate(market(["3", "2", "1", "4"]), D("1000"), config)
    longer = simulate(market(["3", "2", "1", "4", "5"], volumes=[100, 100, 100, 100, volume]), D("1000"), config)
    assert prefix.decisions == longer.decisions[:4]
    assert prefix.valuations == longer.valuations[:4]
    assert prefix.fills == tuple(f for f in longer.fills if f.session <= FIRST + timedelta(days=3))
    assert prefix.orders[:-1] == longer.orders[:len(prefix.orders) - 1]
    old, resolved = prefix.orders[-1], longer.orders[len(prefix.orders) - 1]
    assert (old.order_id, old.decision_session, old.target, old.budget) == (resolved.order_id, resolved.decision_session, resolved.target, resolved.budget)
    assert old.status == "EXPIRED" and old.eligible_session is None
    assert resolved.status == status and resolved.eligible_session == FIRST + timedelta(days=4)


def test_selected_window_starts_flat_and_warmup_starts_inside_window(market):
    settings = ExecutionSettings(start_date=FIRST + timedelta(days=4))
    result = simulate(market(opens=OPENS), D("1000"), SMACrossover(2, 3), settings)
    assert [d.target for d in result.decisions] == ["HOLD", "HOLD", "LONG", "LONG"]
    assert result.valuations[0].shares == 0
    assert result.fills[0].session == FIRST + timedelta(days=7)
    assert (result.final_shares, result.final_cash, result.final_equity) == (83, D("4"), D("1996"))


def test_reentry_outside_numeric_envelope_fails_without_rounded_accounting(market):
    data = market(
        ["0.000001", "0.000002", "0.000001", "0.000002", "0.000003"],
        opens=["0.000001", "0.000001", "0.000001", str(MAX_PRICE), "0.000001"],
    )
    with pytest.raises(SimulationError, match="Share quantity.*precision-28"):
        simulate(data, MAX_CAPITAL, SMACrossover(1, 2))


def test_shared_engine_keeps_eligibility_zero_costs_and_context_isolation(market):
    data = market()
    config = SMACrossover(2, 3)
    expected = simulate(data, D("1000"), config)
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        assert simulate(data, D("1000"), config) == expected
    with pytest.raises(SimulationError, match="slippage_bps"):
        simulate(data, D("1000"), config, ExecutionSettings(slippage_bps=D("10000")))
    unknown_split = replace(data, metadata=replace(data.metadata, split_status="unknown"))
    with pytest.raises(SimulationError, match="D04"):
        simulate(unknown_split, D("1000"), config)
