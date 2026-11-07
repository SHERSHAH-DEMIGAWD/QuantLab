"""Valid and deliberately tampered evidence; unsupported biases remain unassessed."""

from copy import deepcopy
from dataclasses import asdict, replace
from datetime import date
from decimal import Decimal, ROUND_DOWN, localcontext
import json
from pathlib import Path

import pytest

from quantlab.audit import AuditError, audit_simulation
from quantlab.data import load_dataset
from quantlab.execution import ExecutionSettings, simulate
from quantlab.strategies import BuyAndHold, SMACrossover, TimeSeriesMomentum

D = Decimal
FIRST, SECOND, THIRD, FOURTH = (date(2024, 1, day) for day in (5, 8, 9, 10))
SOURCE = (
    "date,open,high,low,close,volume\n"
    "2024-01-05,100,100,100,100,100\n"
    "2024-01-08,100,105,100,105,100\n"
    "2024-01-09,110,110,108,108,100\n"
    "2024-01-10,112,112,111,111,100\n"
).encode()
FIXTURE_METADATA = Path(__file__).parent / "fixtures" / "synthetic_daily.metadata.json"


@pytest.fixture
def reference(tmp_path):
    def make(source=SOURCE, strategy=BuyAndHold(), settings=None, **metadata):
        if settings is None:
            settings = ExecutionSettings(commission_per_fill_usd=D("2"), slippage_bps=D("100"), sell_after_session=SECOND)
        csv, sidecar = tmp_path / "audit.csv", tmp_path / "audit.json"
        csv.write_bytes(source)
        sidecar.write_text(json.dumps({**json.loads(FIXTURE_METADATA.read_text()), **metadata}), encoding="utf-8")
        data = load_dataset(csv, sidecar)
        return data, simulate(data, D("1000"), strategy, settings), source
    return make


def findings(result, data=None, source=None, **kwargs):
    report = audit_simulation(result, dataset=data, source_bytes=source,
                              source_metadata=data.metadata if data is not None and source is not None else None, **kwargs)
    assert len({f.rule_id for f in report.findings}) == len(report.findings)
    assert all(f.evidence and f.explanation for f in report.findings)
    return {f.rule_id: f for f in report.findings}


def test_valid_reference_passes_supported_checks_with_specific_evidence(reference):
    data, result, source = reference()
    checks = findings(result, data, source, expected_settings=result.settings, rerun=True)
    assert result.final_cash == D("1067.10")  # Independent reference from Phase 4.
    assert not [f for f in checks.values() if f.status == "FAIL"]
    for rule in ("TIMING.CAUSALITY", "TIMING.NEXT_SESSION", "ORDERS.LIFECYCLE", "ACCOUNTING.BALANCES",
                 "ACCOUNTING.LEDGER", "COSTS.CONFIGURATION", "COSTS.FILL_MATH", "COSTS.UNFILLED",
                 "COSTS.REQUEST_MATCH", "DATA.RECORDED_IDENTITY", "DATA.ORIGINAL_IDENTITY",
                 "DATA.ORIGINAL_ROWS", "DATA.SOURCE_SHA256", "DATA.PRICE_REFERENCES", "REPRODUCIBILITY.REPLAY"):
        assert checks[rule].status == "PASS", checks[rule]
    assert checks["DATA.LIMITATIONS"].status == "WARNING"
    assert checks["LIMITS.LOOKAHEAD"].status == "NOT_ASSESSED"
    assert result.orders[0].eligible_session == SECOND  # Friday -> Monday, not next calendar day.


@pytest.mark.parametrize("strategy", [BuyAndHold(), SMACrossover(2, 3), TimeSeriesMomentum(1)])
def test_valid_open_positions_and_three_strategies_avoid_false_failures(reference, strategy):
    data, result, source = reference(strategy=strategy, settings=ExecutionSettings(commission_per_fill_usd=D("0.005"), slippage_bps=D("0.005")))
    checks = findings(result, data, source, rerun=True)
    assert not [f for f in checks.values() if f.status == "FAIL"]
    assert checks["ACCOUNTING.LEDGER"].status == checks["COSTS.FILL_MATH"].status == "PASS"


@pytest.mark.parametrize("session", [FIRST, date(2024, 1, 4)])
def test_same_or_earlier_fill_is_detected(reference, session):
    data, result, _ = reference()
    fill = replace(result.fills[0], session=session)
    order = replace(result.orders[0], outcome_session=session)
    tampered = replace(result, fills=(fill, result.fills[1]), orders=(order, result.orders[1]))
    check = findings(tampered, data)["TIMING.CAUSALITY"]
    assert check.status == "FAIL"
    assert any(e.fill_index == 0 and e.order_id == 1 for e in check.evidence)


def test_coordinated_wrong_eligibility_is_detected_by_actual_session_sequence(reference):
    data, result, _ = reference()
    order = replace(result.orders[0], eligible_session=THIRD, outcome_session=THIRD)
    fill = replace(result.fills[0], session=THIRD)
    exit_order = replace(result.orders[1], eligible_session=FOURTH, outcome_session=FOURTH)
    exit_fill = replace(result.fills[1], session=FOURTH)
    checks = findings(replace(result, orders=(order, exit_order), fills=(fill, exit_fill)), data)
    assert checks["TIMING.CAUSALITY"].status == "PASS"  # Internally later and eligible; still wrong source sequence.
    assert checks["TIMING.NEXT_SESSION"].status == "FAIL"


def test_filled_order_missing_fill(reference):
    data, result, _ = reference()
    check = findings(replace(result, fills=result.fills[1:]), data)["ORDERS.LIFECYCLE"]
    assert check.status == "FAIL" and any(e.order_id == 1 for e in check.evidence)


def test_rejected_order_cannot_also_fill_or_charge_a_fee(reference):
    data, result, _ = reference()
    order = replace(result.orders[0], status="REJECTED", reason="zero_volume")
    checks = findings(replace(result, orders=(order, result.orders[1])), data)
    assert checks["ORDERS.LIFECYCLE"].status == checks["COSTS.UNFILLED"].status == "FAIL"


def test_duplicate_fill_associations(reference):
    data, result, _ = reference()
    checks = findings(replace(result, fills=(result.fills[0],) + result.fills), data)
    assert checks["ORDERS.LIFECYCLE"].status == "FAIL"
    assert checks["ACCOUNTING.LEDGER"].status == "FAIL"


def test_reverse_fill_history_is_detected_without_source_or_replay(reference):
    _, result, _ = reference()
    checks = findings(replace(result, fills=tuple(reversed(result.fills))))
    assert checks["TIMING.CAUSALITY"].status == "FAIL"
    assert checks["REPRODUCIBILITY.REPLAY"].status == "NOT_ASSESSED"


def test_backdated_final_expiry_is_detected_without_source(reference):
    _, result, _ = reference(source=SOURCE.replace(b",100\n", b",0\n"), settings=ExecutionSettings())
    order = replace(result.orders[-1], outcome_session=FIRST)
    checks = findings(replace(result, orders=result.orders[:-1] + (order,)))
    assert checks["TIMING.CAUSALITY"].status == "FAIL"


@pytest.mark.parametrize("quantity", [0, -1, 1.5])
def test_actual_fills_require_positive_integer_quantities(reference, quantity):
    data, result, _ = reference()
    fill = replace(result.fills[0], quantity=quantity)
    assert findings(replace(result, fills=(fill, result.fills[1])), data)["ORDERS.LIFECYCLE"].status == "FAIL"


@pytest.mark.parametrize("field,value", [("cash", D("-1")), ("shares", -1), ("equity", D("9999")), ("unrealized_pnl", D("9999"))])
def test_invalid_balances_and_equity_are_detected(reference, field, value):
    data, result, _ = reference()
    valuation = replace(result.valuations[1], **{field: value})
    tampered = replace(result, valuations=(result.valuations[0], valuation) + result.valuations[2:])
    assert findings(tampered, data)["ACCOUNTING.BALANCES"].status == "FAIL"


def test_cash_ledger_detects_hidden_charge_even_if_marked_equity_is_consistent(reference):
    data, result, _ = reference()
    rows = tuple(replace(v, cash=v.cash - D("1"), equity=v.equity - D("1")) for v in result.valuations)
    decisions = tuple(replace(d, cash=d.cash - D("1")) for d in result.decisions)
    tampered = replace(result, valuations=rows, decisions=decisions, final_cash=result.final_cash-D("1"), final_equity=result.final_equity-D("1"))
    checks = findings(tampered, data)
    assert checks["ACCOUNTING.BALANCES"].status == "PASS"
    assert checks["ACCOUNTING.LEDGER"].status == "FAIL"
    assert checks["COSTS.UNFILLED"].status == "NOT_ASSESSED"


def test_incorrect_fee_and_signed_cash_accounting(reference):
    data, result, _ = reference()
    fill = replace(result.fills[0], fee=D("3"))
    checks = findings(replace(result, fills=(fill, result.fills[1])), data)
    assert checks["COSTS.FILL_MATH"].status == checks["ACCOUNTING.LEDGER"].status == "FAIL"
    fill = replace(result.fills[0], cash_change=D("-910"))
    assert findings(replace(result, fills=(fill, result.fills[1])), data)["COSTS.FILL_MATH"].status == "FAIL"


def test_incorrect_execution_price_and_source_close(reference):
    data, result, _ = reference()
    fill = replace(result.fills[0], effective_price=D("102"))
    order = replace(result.orders[0], effective_price=D("102"))
    checks = findings(replace(result, fills=(fill, result.fills[1]), orders=(order, result.orders[1])), data)
    assert checks["ORDERS.LIFECYCLE"].status == "PASS"
    assert checks["COSTS.FILL_MATH"].status == "FAIL"
    fake_base = replace(result.fills[0], base_open=D("101"))
    assert findings(replace(result, fills=(fake_base, result.fills[1])), data)["DATA.PRICE_REFERENCES"].status == "FAIL"
    row = replace(result.valuations[1], close=D("106"), market_value=D("954"), equity=D("1043"), unrealized_pnl=D("43"))
    tampered = replace(result, valuations=(result.valuations[0], row) + result.valuations[2:])
    checks = findings(tampered, data)
    assert checks["ACCOUNTING.BALANCES"].status == "PASS"
    assert checks["DATA.PRICE_REFERENCES"].status == "FAIL"


def test_missing_original_provenance_is_not_fabricated(reference):
    _, result, _ = reference()
    result = replace(result, source_sha256="", metadata=replace(result.metadata, source_name="unknown", source_reference="unknown"))
    checks = findings(result)
    assert checks["DATA.RECORDED_IDENTITY"].status == "FAIL"
    assert checks["DATA.PROVENANCE"].status == "WARNING"
    for rule in ("DATA.SOURCE_SHA256", "DATA.ORIGINAL_IDENTITY", "DATA.ORIGINAL_ROWS", "DATA.INPUT_MATCH", "DATA.PRICE_REFERENCES", "TIMING.NEXT_SESSION", "REPRODUCIBILITY.REPLAY", "COSTS.REQUEST_MATCH"):
        assert checks[rule].status == "NOT_ASSESSED"


@pytest.mark.parametrize("field,value", [("adjustment_basis", "unknown"), ("split_status", "unknown"), ("split_status", "present")])
def test_unknown_or_present_declarations_never_pass_eligibility(reference, field, value):
    _, result, _ = reference()
    result = replace(result, metadata=replace(result.metadata, **{field: value}))
    checks = findings(result)
    assert checks["DATA.ELIGIBILITY"].status == "FAIL"
    assert checks["LIMITS.CORPORATE_ACTION_TRUTH"].status == "NOT_ASSESSED"


def test_declared_complete_coverage_still_unverified_and_acknowledgment_required(reference):
    data, result, _ = reference(source_kind="local_file", session_coverage="declared_complete", settings=ExecutionSettings(acknowledge_unverified_coverage=True))
    checks = findings(result, data)
    assert checks["DATA.ELIGIBILITY"].status == "PASS"
    assert checks["DATA.LIMITATIONS"].status == "WARNING"
    assert "coverage is unverified" in checks["DATA.LIMITATIONS"].explanation
    assert checks["LIMITS.SESSION_COMPLETENESS"].status == "NOT_ASSESSED"
    result = replace(result, settings=replace(result.settings, acknowledge_unverified_coverage=False))
    assert findings(result, data)["DATA.ELIGIBILITY"].status == "FAIL"


def test_original_fingerprint_mismatch_and_retained_row_tampering(reference):
    data, result, source = reference()
    changed = source.replace(b"105", b"106")
    checks = findings(result, data, changed)
    assert checks["DATA.SOURCE_SHA256"].status == checks["DATA.ORIGINAL_IDENTITY"].status == "FAIL"
    assert checks["DATA.ORIGINAL_ROWS"].status == "FAIL"
    fake = replace(data, bars=(replace(data.bars[0], close=D("99"), low=D("99")),) + data.bars[1:])
    assert findings(result, fake, source)["DATA.ORIGINAL_ROWS"].status == "FAIL"


def test_partial_source_evidence_checks_only_supported_components(reference):
    _, result, source = reference()
    report = audit_simulation(result, source_bytes=source)
    checks = {f.rule_id: f for f in report.findings}
    assert checks["DATA.SOURCE_SHA256"].status == "PASS"
    assert checks["DATA.ORIGINAL_IDENTITY"].status == checks["DATA.ORIGINAL_ROWS"].status == "NOT_ASSESSED"
    assert checks["TIMING.NEXT_SESSION"].status == checks["DATA.PRICE_REFERENCES"].status == "PASS"
    changed = audit_simulation(result, source_bytes=source + b"\n")
    assert next(f for f in changed.findings if f.rule_id == "DATA.SOURCE_SHA256").status == "FAIL"


def test_invalid_original_rows_are_not_silently_dropped(reference):
    data, result, source = reference()
    checks = findings(result, data, source + b"invalid,row\n")
    assert checks["DATA.ORIGINAL_ROWS"].status == "FAIL"
    assert any("invalid_row_width" in e.observed for e in checks["DATA.ORIGINAL_ROWS"].evidence)


def test_replay_is_stable_exact_and_detects_tampered_results(reference):
    data, result, source = reference()
    saved = deepcopy((data, result))
    first = audit_simulation(result, dataset=data, source_bytes=source, source_metadata=data.metadata, rerun=True)
    assert first == audit_simulation(result, dataset=data, source_bytes=source, source_metadata=data.metadata, rerun=True)
    assert (data, result) == saved
    tampered = replace(result, final_equity=result.final_equity + D("1"))
    check = findings(tampered, data, rerun=True)["REPRODUCIBILITY.REPLAY"]
    assert check.status == "FAIL" and any(e.reference == "result.final_equity" for e in check.evidence)
    tampered = replace(result, warnings=())  # Current schema has no excluded nondeterministic fields.
    assert findings(tampered, data, rerun=True)["REPRODUCIBILITY.REPLAY"].status == "FAIL"
    json.dumps(asdict(first), default=str, allow_nan=False)


def test_replay_without_inputs_configuration_or_supported_version_is_unassessed(reference):
    data, result, _ = reference()
    assert findings(result, rerun=True)["REPRODUCIBILITY.REPLAY"].status == "NOT_ASSESSED"
    for changed in (replace(result, settings=None), replace(result, strategy=None), replace(result, engine_version="0.0.0")):
        assert findings(changed, data, rerun=True)["REPRODUCIBILITY.REPLAY"].status == "NOT_ASSESSED"


def test_original_settings_match_is_separate_from_self_consistency(reference):
    data, result, _ = reference()
    original = replace(result.settings, slippage_bps=D("50"))
    checks = findings(result, data, expected_settings=original)
    assert checks["COSTS.FILL_MATH"].status == "PASS"
    assert checks["COSTS.REQUEST_MATCH"].status == "FAIL"
    assert findings(result, data)["COSTS.REQUEST_MATCH"].status == "NOT_ASSESSED"


def test_valid_rejected_and_expired_orders_have_reconciled_zero_charges(reference):
    data, result, source = reference(source=SOURCE.replace(b",100\n", b",0\n"), settings=ExecutionSettings(commission_per_fill_usd=D("2")))
    checks = findings(result, data, source, rerun=True)
    assert not result.fills and result.orders[-1].status == "EXPIRED"
    assert checks["COSTS.UNFILLED"].status == "PASS"
    assert not [f for f in checks.values() if f.status == "FAIL"]


def test_reentry_and_zero_terminal_cash_avoid_false_accounting_failures(reference):
    # Same independent Phase 3 reference: 66 bought at 15, sold at 9, 54 bought at 11.
    opens = ("10", "10", "10", "15", "9", "10", "11", "12")
    closes = ("10", "12", "14", "8", "6", "20", "22", "24")
    rows = ["date,open,high,low,close,volume\n"]
    for i, (open_, close) in enumerate(zip(opens, closes)):
        rows.append(f"2024-02-{i+1:02},{open_},{max(D(open_), D(close))},{min(D(open_), D(close))},{close},100\n")
    data, result, source = reference(source="".join(rows).encode(), strategy=SMACrossover(2, 3), settings=ExecutionSettings())
    assert result.final_equity == D("1306")
    assert not [f for f in findings(result, data, source, rerun=True).values() if f.status == "FAIL"]
    source = SOURCE.replace(b"100", b"1").replace(b"105", b"1").replace(b"110", b"1").replace(b"108", b"1").replace(b"112", b"1").replace(b"111", b"1")
    data, result, source = reference(source=source, settings=ExecutionSettings(commission_per_fill_usd=D("500"), sell_after_session=SECOND))
    # Buy 500 shares at 1 plus 500 fee; sell proceeds equal the fee -> no cash left.
    assert result.final_equity == D("0")
    assert not [f for f in findings(result, data, source, rerun=True).values() if f.status == "FAIL"]


def test_independent_checks_do_not_call_production_execution_or_cost_helpers(reference, monkeypatch):
    data, result, source = reference()
    import quantlab.execution.costs as costs
    import quantlab.execution.engine as engine
    def forbidden(*args, **kwargs):
        raise AssertionError("Production execution/cost helper must not perform audit reconciliation")
    monkeypatch.setattr(costs, "effective_price", forbidden)
    monkeypatch.setattr(costs, "commission_per_fill", forbidden)
    monkeypatch.setattr(engine, "_execute", forbidden)
    checks = findings(result, data, source)
    assert checks["ACCOUNTING.LEDGER"].status == checks["COSTS.FILL_MATH"].status == "PASS"


def test_numeric_equal_values_do_not_hide_invalid_position_types(reference):
    data, result, _ = reference()
    assert findings(replace(result, final_shares=0.0), data)["ACCOUNTING.BALANCES"].status == "FAIL"
    decision = replace(result.decisions[1], shares=9.0)
    assert findings(replace(result, decisions=(result.decisions[0], decision) + result.decisions[2:]), data)["ORDERS.LIFECYCLE"].status == "FAIL"


def test_unsupported_biases_are_honest_not_assessed_not_detected(reference):
    data, result, source = reference()
    checks = findings(result, data, source)
    keys = {"LOOKAHEAD", "SURVIVORSHIP", "INDEX_MEMBERSHIP", "SELECTION", "OVERFITTING", "CORPORATE_ACTION_TRUTH", "SESSION_COMPLETENESS", "LIQUIDITY", "SIGNIFICANCE", "ECONOMIC_EVENTS"}
    assert all(checks["LIMITS." + key].status == "NOT_ASSESSED" and checks["LIMITS." + key].severity is None for key in keys)
    assert "arbitrary strategy" in checks["LIMITS.LOOKAHEAD"].explanation
    assert "No significance testing" in checks["LIMITS.SIGNIFICANCE"].explanation


def test_context_independence_invalid_numeric_trace_and_request_validation(reference):
    data, result, source = reference()
    expected = findings(result, data, source)
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        assert findings(result, data, source) == expected
    row = replace(result.valuations[1], cash=D("NaN"))
    changed = replace(result, valuations=(result.valuations[0], row) + result.valuations[2:])
    assert findings(changed, data)["ACCOUNTING.BALANCES"].status == "FAIL"
    for kwargs in ({"source_bytes": "text"}, {"rerun": "yes"}, {"dataset": "data"}):
        with pytest.raises(AuditError):
            audit_simulation(result, **kwargs)
