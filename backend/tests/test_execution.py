"""Hand-calculated execution references; all observations are invented and event-free."""

from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN, localcontext
import json

import pytest

from quantlab.data import load_dataset
from quantlab.execution import (
    MAX_CAPITAL, MAX_PRICE, ExecutionSettings, Order, SimulationError,
    simulate_buy_and_hold,
)
from quantlab.execution.engine import _execute

D = Decimal
FIRST = date(2024, 1, 5)
SECOND = date(2024, 1, 8)
THIRD = date(2024, 1, 9)
FOURTH = date(2024, 1, 10)
METADATA = {
    "contract_version": 1, "symbol": "SYNTH", "exchange": "SYNTHETIC_US",
    "currency": "USD", "frequency": "1d", "session_timezone": "America/New_York",
    "source_kind": "synthetic", "source_name": "Invented execution reference",
    "adjustment_basis": "unadjusted", "ohlc_basis_consistent": True,
    "volume_basis": "raw", "split_status": "none_reported",
    "split_evidence": "Invented event-free sessions, no corporate actions",
}


@pytest.fixture
def dataset(tmp_path):
    def make(rows=None, **metadata):
        # row = (date, open, close, volume); bounds come only from these source values.
        if rows is None:
            rows = [(FIRST, "100", "100", 1000), (SECOND, "103", "105", 1000),
                    (THIRD, "104", "106", 1000)]
        text = "date,open,high,low,close,volume\n" + "".join(
            f"{day},{open_},{max(D(open_), D(close))},{min(D(open_), D(close))},{close},{volume}\n"
            for day, open_, close, volume in rows
        )
        csv = tmp_path / "bars.csv"
        sidecar = tmp_path / "metadata.json"
        csv.write_text(text, encoding="utf-8")
        sidecar.write_text(json.dumps({**METADATA, **metadata}), encoding="utf-8")
        return load_dataset(csv, sidecar)
    return make


def test_buy_hold_reference_timing_residual_and_open_final_position(dataset):
    data = dataset()
    result = simulate_buy_and_hold(data, D("1000"))
    assert result.dataset_id == data.report.dataset_id
    assert (result.start_date, result.end_date) == (FIRST, THIRD)
    assert result.initial_capital == D("1000.00")
    assert [(v.cash, v.shares, v.equity) for v in result.valuations] == [
        (D("1000.00"), 0, D("1000")),
        (D("73.00"), 9, D("1018.00")),
        (D("73.00"), 9, D("1027.00")),
    ]
    assert (result.final_cash, result.final_shares, result.final_equity) == (D("73"), 9, D("1027"))
    order, = result.orders
    fill, = result.fills
    assert (order.decision_session, order.eligible_session, order.outcome_session) == (FIRST, SECOND, SECOND)
    assert (order.status, order.target, order.budget, order.requested_shares) == ("FILLED", "LONG", D("1000"), None)
    assert (fill.order_id, fill.session, fill.quantity, fill.base_open, fill.effective_price) == (1, SECOND, 9, D("103"), D("103.000000"))
    assert (fill.notional, fill.cash_change, fill.fee) == (D("927.00"), D("-927.00"), D("0.00"))
    assert [d.target for d in result.decisions] == ["LONG", "HOLD", "HOLD"]
    assert (result.realized_pnl, result.unrealized_pnl) == (D("0"), D("27"))
    assert result.settings.commission_per_fill_usd == result.settings.slippage_bps == 0
    assert any("excluding dividends" in assumption for assumption in result.assumptions)


def test_overnight_gap_changes_execution_quantity(dataset):
    data = dataset([(FIRST, "100", "100", 100), (SECOND, "130", "140", 100)])
    result = simulate_buy_and_hold(data, D("1000"))
    assert result.decisions[0].cash == D("1000")
    assert (result.fills[0].quantity, result.final_cash, result.final_equity) == (7, D("90"), D("1070"))


def test_insufficient_capital_rejects_and_final_fresh_intent_expires(dataset):
    result = simulate_buy_and_hold(dataset(), D("1"))
    assert [(o.status, o.reason) for o in result.orders] == [
        ("REJECTED", "insufficient_capital"), ("REJECTED", "insufficient_capital"),
        ("EXPIRED", "end_of_window"),
    ]
    assert result.orders[-1].eligible_session is None
    assert result.fills == ()
    assert (result.final_cash, result.final_shares, result.final_equity) == (D("1"), 0, D("1"))


def test_zero_volume_rejection_and_fresh_buy_intent(dataset):
    data = dataset([(FIRST, "100", "100", 100), (SECOND, "103", "105", 0),
                    (THIRD, "110", "112", 100)])
    result = simulate_buy_and_hold(data, D("1000"))
    rejected, bought = result.orders
    assert (rejected.order_id, rejected.status, rejected.reason, rejected.outcome_session) == (1, "REJECTED", "zero_volume", SECOND)
    assert (bought.order_id, bought.decision_session, bought.eligible_session, bought.status) == (2, SECOND, THIRD, "FILLED")
    fill, = result.fills
    assert (fill.order_id, fill.quantity, fill.notional) == (2, 9, D("990"))
    assert (result.final_cash, result.final_equity) == (D("10"), D("1018"))
    assert result.valuations[1].shares == 0


def test_sell_reference_immediate_proceeds_realized_and_unrealized(dataset):
    data = dataset([(FIRST, "100", "100", 100), (SECOND, "103", "105", 100),
                    (THIRD, "110", "109", 100), (FOURTH, "50", "50", 100)])
    result = simulate_buy_and_hold(data, D("1000"), ExecutionSettings(sell_after_session=SECOND))
    assert [(f.side, f.session, f.quantity, f.notional) for f in result.fills] == [
        ("BUY", SECOND, 9, D("927")), ("SELL", THIRD, 9, D("990")),
    ]
    assert result.orders[1].requested_shares == 9
    assert (result.orders[1].decision_session, result.orders[1].eligible_session) == (SECOND, THIRD)
    assert (result.valuations[1].cost_basis, result.valuations[1].unrealized_pnl) == (D("927"), D("18"))
    assert (result.final_cash, result.final_shares, result.final_equity) == (D("1063"), 0, D("1063"))
    assert (result.realized_pnl, result.unrealized_pnl) == (D("63"), D("0"))
    assert result.valuations[2].cost_basis == 0
    assert any("Diagnostic" in warning for warning in result.warnings)


def test_zero_volume_sell_is_rejected_without_later_retry(dataset):
    data = dataset([(FIRST, "100", "100", 100), (SECOND, "103", "105", 100),
                    (THIRD, "110", "109", 0), (FOURTH, "120", "121", 100)])
    result = simulate_buy_and_hold(data, D("1000"), ExecutionSettings(sell_after_session=SECOND))
    assert len(result.orders) == 2 and len(result.fills) == 1
    assert (result.orders[1].status, result.orders[1].reason) == ("REJECTED", "zero_volume")
    assert (result.final_cash, result.final_shares, result.final_equity) == (D("73"), 9, D("1162"))


def test_invalid_sell_position_rejected_without_fill(dataset):
    # Test the execution boundary directly; the public decision rule cannot oversell.
    order = Order(1, FIRST, SECOND, "FLAT", "SELL", None, 10)
    with localcontext() as context:
        context.prec = 28
        outcome, fill = _execute(order, dataset().bars[1], D("73"), 9)
    assert (outcome.status, outcome.reason, fill) == ("REJECTED", "invalid_sell_position", None)
    assert order.status == "PENDING"  # Immutable input; state updates require a fill.


def test_final_sell_intent_expires_without_forced_liquidation(dataset):
    result = simulate_buy_and_hold(dataset(), D("1000"), ExecutionSettings(sell_after_session=THIRD))
    assert (result.orders[-1].side, result.orders[-1].status, result.orders[-1].reason) == ("SELL", "EXPIRED", "end_of_window")
    assert len(result.fills) == 1 and result.final_shares == 9


def test_exit_while_flat_has_no_sell_order(dataset):
    result = simulate_buy_and_hold(dataset(), D("1000"), ExecutionSettings(sell_after_session=FIRST))
    assert result.orders == result.fills == ()
    assert result.final_cash == result.final_equity == D("1000")


def test_round_half_up_notional_and_unrounded_marks(dataset):
    data = dataset([(FIRST, "0.333333", "0.333333", 1),
                    (SECOND, "0.335", "0.336667", 1), (THIRD, "0.345", "0.345", 1)])
    result = simulate_buy_and_hold(data, D("1.01"), ExecutionSettings(sell_after_session=SECOND))
    # 3 * .335 = 1.005 -> 1.01 debit; 3 * .336667 = 1.010001 exact mark.
    assert (result.fills[0].quantity, result.fills[0].notional, result.valuations[1].cash) == (3, D("1.01"), D("0.00"))
    assert result.valuations[1].equity == D("1.010001")
    # 3 * .345 = 1.035 -> 1.04 credit; realized profit is .03.
    assert (result.final_cash, result.realized_pnl) == (D("1.04"), D("0.03"))


def test_subcent_sizing_preserves_raw_budget_and_rounding_is_visible(dataset):
    data = dataset([(FIRST, "0.006667", "0.006667", 1), (SECOND, "0.006667", "0.006667", 1)])
    result = simulate_buy_and_hold(data, D("0.02"))
    assert (result.final_shares, result.final_cash, result.final_equity) == (2, D("0.01"), D("0.023334"))
    # Three shares would have unrounded notional .020001, exceeding the .02 intent budget.


def test_numeric_extremes_and_invariants(dataset):
    data = dataset([(FIRST, "0.000001", "0.000001", 1),
                    (SECOND, "0.000001", str(MAX_PRICE), 1),
                    (THIRD, str(MAX_PRICE), str(MAX_PRICE), 1)])
    result = simulate_buy_and_hold(data, MAX_CAPITAL, ExecutionSettings(sell_after_session=SECOND))
    assert result.fills[0].quantity == 999999999990000
    assert result.valuations[1].equity == D("999999999989000000000.010000")
    assert result.final_cash == D("999999999989000000000.01")
    with localcontext() as context:
        context.prec = 40  # Independent reference checks do not inherit ambient rounding.
        for valuation in result.valuations:
            assert valuation.cash >= 0 and type(valuation.shares) is int and valuation.shares >= 0
            assert valuation.cash.as_tuple().exponent == -2
            assert valuation.equity == valuation.cash + valuation.shares * valuation.close
        assert all(fill.session > result.orders[fill.order_id - 1].decision_session for fill in result.fills)


def test_repeat_execution_is_deterministic_and_context_independent(dataset):
    data = dataset()
    expected = simulate_buy_and_hold(data, D("1000.00"))
    assert simulate_buy_and_hold(data, D("1000.00")) == expected
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        context.Emax = 3
        context.Emin = -3
        assert simulate_buy_and_hold(data, D("1000.00")) == expected
        assert context.prec == 3 and context.rounding == ROUND_DOWN and context.Emax == 3


def test_future_prices_do_not_change_earlier_decisions(dataset):
    original = simulate_buy_and_hold(dataset(), D("1000"))
    changed_open = simulate_buy_and_hold(dataset([
        (FIRST, "100", "100", 1000), (SECOND, "200", "210", 1000),
        (THIRD, "300", "310", 1000),
    ]), D("1000"))
    assert changed_open.decisions[0] == original.decisions[0]
    assert changed_open.orders[0].budget == original.orders[0].budget
    assert changed_open.fills[0].quantity == 5
    changed_later = simulate_buy_and_hold(dataset([
        (FIRST, "100", "100", 1000), (SECOND, "103", "105", 1000),
        (THIRD, "300", "310", 1000),
    ]), D("1000"))
    assert changed_later.decisions[:2] == original.decisions[:2]
    assert changed_later.valuations[:2] == original.valuations[:2]
    assert changed_later.fills == original.fills
    appended = simulate_buy_and_hold(dataset([
        (FIRST, "100", "100", 1000), (SECOND, "103", "105", 1000),
        (THIRD, "104", "106", 1000), (FOURTH, "900", "910", 1000),
    ]), D("1000"))
    assert appended.decisions[:3] == original.decisions


@pytest.mark.parametrize("capital", [
    D("0"), D("-1"), D("NaN"), D("Infinity"), D("sNaN"),
    D("1.001"), D("1000000000"), 1000.0, 1000, "1000",
])
def test_invalid_capital_rejected(dataset, capital):
    with pytest.raises(SimulationError, match="initial_capital"):
        simulate_buy_and_hold(dataset(), capital)


@pytest.mark.parametrize("field,value", [
    ("commission_per_fill_usd", D("-1")), ("slippage_bps", D("10000")),
    ("commission_per_fill_usd", D("0.0000001")), ("slippage_bps", D("-1")),
    ("slippage_bps", D("NaN")), ("commission_per_fill_usd", 0.0),
])
def test_invalid_costs_rejected(dataset, field, value):
    with pytest.raises(SimulationError, match=field):
        simulate_buy_and_hold(dataset(), D("1000"), replace(ExecutionSettings(), **{field: value}))


@pytest.mark.parametrize("field,value", [
    ("adjustment_basis", "unknown"), ("adjustment_basis", "split_adjusted"),
    ("adjustment_basis", "total_return_adjusted"), ("ohlc_basis_consistent", "unknown"),
    ("volume_basis", "unknown"), ("volume_basis", "split_adjusted"),
    ("split_status", "present"), ("split_status", "unknown"), ("split_evidence", "unknown"),
])
def test_ineligible_imports_are_blocked(dataset, field, value):
    with pytest.raises(SimulationError, match="D04"):
        simulate_buy_and_hold(dataset(**{field: value}), D("1000"))


@pytest.mark.parametrize("coverage", ["unknown", "declared_complete"])
def test_real_data_requires_coverage_acknowledgment(dataset, coverage):
    # Still invented prices: local_file only exercises eligibility, not real market performance.
    data = dataset(source_kind="local_file", session_coverage=coverage)
    with pytest.raises(SimulationError, match="acknowledgment"):
        simulate_buy_and_hold(data, D("1000"))
    result = simulate_buy_and_hold(data, D("1000"), ExecutionSettings(acknowledge_unverified_coverage=True))
    assert result.settings.acknowledge_unverified_coverage is True
    assert any("unverified" in warning for warning in result.warnings)
    assert result.fills[0].session == SECOND  # Observed Friday -> Monday, no invented session.


def test_window_starts_flat_and_keeps_original_dataset_identity(dataset):
    data = dataset()
    result = simulate_buy_and_hold(data, D("1000"), ExecutionSettings(start_date=SECOND, end_date=THIRD))
    assert result.dataset_id == data.report.dataset_id
    assert (result.start_date, result.end_date) == (SECOND, THIRD)
    assert (result.valuations[0].shares, result.fills[0].session, result.fills[0].quantity) == (0, THIRD, 9)
    assert (result.final_cash, result.final_equity) == (D("64"), D("1018"))


def test_import_precision_and_execution_ranges_are_distinct(dataset):
    data = dataset([(FIRST, "103.000000000", "103.000000000", 1),
                    (SECOND, "103.000000000", "105.000000000", 1)])
    result = simulate_buy_and_hold(data, D("1000.00000"))
    assert result.fills[0].effective_price.as_tuple().exponent == -6
    assert result.final_cash.as_tuple().exponent == -2
    large = dataset([(FIRST, "1000000", "1000000", 1), (SECOND, "1000000", "1000000", 1)])
    with pytest.raises(SimulationError, match="supported range"):
        simulate_buy_and_hold(large, D("1000"))


def test_insufficient_sessions_and_empty_window(dataset):
    with pytest.raises(SimulationError, match="two observed"):
        simulate_buy_and_hold(dataset([(FIRST, "100", "100", 1)]), D("1000"))
    data = dataset()
    for settings in (ExecutionSettings(start_date=THIRD), ExecutionSettings(end_date=FIRST - timedelta(days=1))):
        with pytest.raises(SimulationError, match="two observed"):
            simulate_buy_and_hold(data, D("1000"), settings)


@pytest.mark.parametrize("settings", [
    ExecutionSettings(start_date=THIRD, end_date=FIRST),
    ExecutionSettings(start_date="2024-01-05"),
    ExecutionSettings(sell_after_session=date(2024, 1, 6)),
    ExecutionSettings(acknowledge_unverified_coverage="yes"),
    "invalid settings",
])
def test_invalid_settings_rejected(dataset, settings):
    with pytest.raises(SimulationError):
        simulate_buy_and_hold(dataset(), D("1000"), settings)


@pytest.mark.parametrize("field,value", [
    ("open", D("0")), ("low", D("-1")), ("close", D("NaN")),
    ("open", D("103.0000001")), ("high", D("1000000")),
    ("low", D("106")), ("volume", -1), ("volume", True),
])
def test_invalid_or_unsupported_bar_values_fail_before_execution(dataset, field, value):
    data = dataset()
    bars = (data.bars[0], replace(data.bars[1], **{field: value}), data.bars[2])
    with pytest.raises(SimulationError):
        simulate_buy_and_hold(replace(data, bars=bars), D("1000"))


def test_unordered_or_inconsistent_direct_dataset_construction_rejected(dataset):
    data = dataset()
    for changed in (replace(data, bars=(data.bars[0], data.bars[0], data.bars[2])),
                    replace(data, report=replace(data.report, row_count=4)),
                    replace(data, bars=(None, data.bars[1], data.bars[2])),
                    replace(data, metadata=None),
                    replace(data, bars=()), None):
        with pytest.raises(SimulationError):
            simulate_buy_and_hold(changed, D("1000"))
