"""Independent experiment references, workload boundaries, and leakage regressions."""

from copy import deepcopy
from dataclasses import asdict, replace
from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN, localcontext
from hashlib import sha256
import json
from pathlib import Path

import pytest

from quantlab.analytics import Metric
from quantlab.audit import audit_simulation
from quantlab.data import load_dataset
from quantlab.execution import ExecutionSettings, SimulationError, simulate, validate_simulation_request
from quantlab.experiments import (
    MAX_AGGREGATE_BARS, MAX_CONFIGURATIONS, CostScenario, EvaluationPeriod,
    ExperimentError, momentum_grid, run_experiment, run_train_test, sma_grid,
)
from quantlab.experiments import runner
from quantlab.strategies import BuyAndHold, SMACrossover, TimeSeriesMomentum

D = Decimal
FIRST = date(2024, 1, 1)
SIDECAR = Path(__file__).parent / "fixtures" / "synthetic_daily.metadata.json"


@pytest.fixture
def market(tmp_path):
    def make(closes=("10", "12", "11", "15", "16", "20", "22", "10", "8"), opens=None):
        if opens is None:
            opens = ("10", "10", "12", "11", "15", "16", "20", "22", "10") if len(closes) == 9 else closes
        rows = ["date,open,high,low,close,volume\n"]
        for i, (open_, close) in enumerate(zip(opens, closes, strict=True)):
            rows.append(f"{FIRST + timedelta(days=i)},{open_},{max(D(open_), D(close))},{min(D(open_), D(close))},{close},100\n")
        path = tmp_path / "experiment.csv"
        path.write_text("".join(rows), encoding="utf-8")
        return load_dataset(path, SIDECAR)
    return make


def period(first, last):
    return EvaluationPeriod(FIRST + timedelta(days=first), FIRST + timedelta(days=last))


def no_execution(monkeypatch):
    calls = []
    def forbidden(*args, **kwargs):
        calls.append(args)
        raise AssertionError("Expensive execution started before complete request validation")
    monkeypatch.setattr(runner, "simulate", forbidden)
    return calls


def test_sma_and_momentum_grids_are_valid_canonical_and_deterministic(market):
    sma = sma_grid([2, 1], [4, 3])
    assert sma == (SMACrossover(1, 3), SMACrossover(1, 4), SMACrossover(2, 3), SMACrossover(2, 4))
    momentum = momentum_grid([2, 1], [D("0.1"), D("0")])
    assert momentum == (TimeSeriesMomentum(1), TimeSeriesMomentum(1, D("0.1")), TimeSeriesMomentum(2), TimeSeriesMomentum(2, D("0.1")))
    data = market()
    for configs in (sma, momentum):
        result = run_experiment(data, D("1000"), configs)
        assert result == run_experiment(data, D("1000"), tuple(reversed(configs)))
        assert result.workload.run_count == 5 and result.workload.evaluated_bars == 45
        assert len({run.run_id for run in result.runs}) == 5
        assert all(run.performance.simulation.dataset_id == data.report.dataset_id for run in result.runs)


@pytest.mark.parametrize("factory", [
    lambda: sma_grid([1, 3], [3]), lambda: sma_grid([True], [3]),
    lambda: momentum_grid([0]), lambda: momentum_grid([1], [D("NaN")]),
    lambda: momentum_grid([1], [0.1]), lambda: sma_grid([], [3]),
    lambda: momentum_grid([1], [D("0"), D("0.00")]),
])
def test_invalid_grid_is_rejected_atomically(factory):
    with pytest.raises(ExperimentError):
        factory()


def test_configuration_limit_includes_fixed_references_and_rejects_before_execution(market, monkeypatch):
    assert MAX_CONFIGURATIONS == 100 and MAX_AGGREGATE_BARS == 1_000_000
    configs = sma_grid(list(range(1, 101)), [101])
    assert len(configs) == 100
    calls = no_execution(monkeypatch)
    with pytest.raises(ExperimentError, match="100"):
        run_experiment(market(), D("1000"), configs)  # 100 plus benchmark = 101.
    with pytest.raises(ExperimentError, match="100"):
        momentum_grid(list(range(1, 102)))
    with pytest.raises(ExperimentError, match="100"):
        run_experiment(market(), D("1000"), tuple(TimeSeriesMomentum(i) for i in range(1, 102)), include_benchmark=False)
    assert calls == []


def test_exact_aggregate_budget_boundary_and_rejection_before_execution(market, monkeypatch):
    data = market(closes=["10"] * 10001)
    configs = sma_grid(list(range(1, 101)), [101])
    jobs, workload = runner._plan(
        data, D("1000"), configs, (period(0, 9999),), (CostScenario(),),
        ExecutionSettings(), False, "evaluation", "run",
    )
    assert len(jobs) == 100 and workload.total_bars == 1_000_000
    calls = no_execution(monkeypatch)
    with pytest.raises(ExperimentError, match="Aggregate workload"):
        run_experiment(data, D("1000"), configs, include_benchmark=False)
    assert calls == []


def test_train_test_budget_includes_training_test_benchmarks_and_warmup(market, monkeypatch):
    data = market(closes=["10"] * 10002)
    configs = sma_grid(list(range(1, 100)), [100])  # 99 candidates + training benchmark.
    calls = no_execution(monkeypatch)
    # Training alone is exactly 1,000,000; selected test/reference/warm-up exceed it.
    with pytest.raises(ExperimentError, match="Aggregate workload"):
        run_train_test(data, D("1000"), configs, period(0, 9999), period(10000, 10001))
    assert calls == []


def test_cost_and_period_products_are_counted_before_execution(market, monkeypatch):
    data = market()
    # Three unique strategies x two costs x two periods x three observations = 36.
    configs = (BuyAndHold(), TimeSeriesMomentum(1), SMACrossover(1, 2))
    jobs, workload = runner._plan(data, D("1000"), configs, (period(0, 2), period(3, 5)),
                                 (CostScenario(), CostScenario(D("2"))), ExecutionSettings(), True, "evaluation", "run")
    assert len(jobs) == 12 and workload.total_bars == 36  # Buy-and-hold already present; no duplicated reference.
    monkeypatch.setattr(runner, "MAX_AGGREGATE_BARS", 35)
    calls = no_execution(monkeypatch)
    with pytest.raises(ExperimentError, match="Aggregate workload"):
        run_experiment(data, D("1000"), configs, periods=(period(0, 2), period(3, 5)), costs=(CostScenario(), CostScenario(D("2"))))
    assert calls == []


def test_cost_sensitivity_has_independent_values_and_explicit_reference(market):
    data = market(closes=["100", "100", "110"], opens=["100"] * 3)
    costs = (CostScenario(), CostScenario(D("2"), D("100")))
    result = run_experiment(data, D("1000"), (BuyAndHold(),), costs=costs)
    assert result.experiment_type == "cost_sensitivity" and result.workload.run_count == 2
    assert [(run.performance.simulation.final_cash, run.performance.simulation.final_shares, run.performance.simulation.final_equity) for run in result.runs] == [
        (D("0"), 10, D("1100")), (D("89"), 9, D("1079")),
    ]
    delta, = [comparison for comparison in result.comparisons if comparison.kind == "cost_reference"]
    assert delta.reference_run_id == result.runs[0].run_id
    assert delta.final_equity_difference == D("-21")
    assert delta.cumulative_return_difference.value == pytest.approx(-0.021)
    assert delta.maximum_drawdown_difference.value == pytest.approx(0.011)
    assert all(run.performance.simulation.final_shares > 0 for run in result.runs)


def test_higher_fees_can_leave_less_exposure_to_a_loss(market):
    result = run_experiment(market(closes=["100", "100", "50"], opens=["100"] * 3), D("1000"),
                            (BuyAndHold(),), costs=(CostScenario(), CostScenario(D("2"))))
    assert [run.performance.simulation.final_equity for run in result.runs] == [D("500"), D("548")]
    delta = next(comparison for comparison in result.comparisons if comparison.kind == "cost_reference")
    assert delta.final_equity_difference == D("48") and delta.cumulative_return_difference.value == pytest.approx(0.048)


def test_subperiods_keep_identity_capital_costs_and_labels_without_cross_window_ranking(market):
    data = market()
    windows = (period(0, 2), period(3, 8))
    result = run_experiment(data, D("1000"), (TimeSeriesMomentum(1),), periods=windows,
                            settings=ExecutionSettings(commission_per_fill_usd=D("2")))
    assert result.experiment_type == "subperiods" and result.workload.evaluated_bars == 18
    by_id = {run.run_id: run for run in result.runs}
    for run in result.runs:
        simulation = run.performance.simulation
        assert simulation.dataset_id == data.report.dataset_id and simulation.initial_capital == D("1000")
        assert simulation.settings.commission_per_fill_usd == D("2")
        assert (simulation.start_date, simulation.end_date) == (run.requested_period.start_date, run.requested_period.end_date)
    assert all(by_id[comparison.run_id].requested_period == by_id[comparison.reference_run_id].requested_period for comparison in result.comparisons)
    assert any("Different-length" in assumption for assumption in result.assumptions)


def test_invalid_or_insufficient_periods_and_invalid_costs_prevent_any_execution(market, monkeypatch):
    data = market()
    calls = no_execution(monkeypatch)
    for kwargs in (
        {"periods": (period(0, 2), period(8, 8))},
        {"periods": (period(20, 21),)},
        {"costs": (CostScenario(), CostScenario(D("-1")))},
        {"costs": (CostScenario(D("0"), D("10000")),)},
        {"periods": (period(0, 2),), "settings": ExecutionSettings(start_date=FIRST)},
        {"costs": (CostScenario(),), "settings": ExecutionSettings(slippage_bps=D("1"))},
    ):
        with pytest.raises(ExperimentError):
            run_experiment(data, D("1000"), (TimeSeriesMomentum(1),), **kwargs)
    with pytest.raises(ExperimentError):
        EvaluationPeriod(FIRST + timedelta(days=1), FIRST)
    assert calls == []


def test_indicator_only_warmup_has_no_trades_valuations_or_carried_pending_order(market):
    data = market(closes=["10", "12", "14", "16"], opens=["10", "10", "12", "14"])
    settings = ExecutionSettings(start_date=FIRST + timedelta(days=2), warmup_start_date=FIRST, warmup_end_date=FIRST + timedelta(days=1))
    assert validate_simulation_request(data, D("1000"), TimeSeriesMomentum(1), settings) == (2, 2)
    result = simulate(data, D("1000"), TimeSeriesMomentum(1), settings)
    assert (result.warmup_start, result.warmup_end, result.warmup_bars) == (FIRST, FIRST + timedelta(days=1), 2)
    assert [(v.cash, v.shares, v.equity) for v in result.valuations] == [(D("1000"), 0, D("1000")), (D("6"), 71, D("1142"))]
    assert result.orders[0].decision_session == FIRST + timedelta(days=2)
    assert result.fills[0].session == FIRST + timedelta(days=3)
    assert len(result.decisions) == 2 and len(result.fills) == 1
    audit = audit_simulation(result, dataset=data, rerun=True)
    assert not [finding for finding in audit.findings if finding.status == "FAIL"]
    tampered = audit_simulation(replace(result, warmup_bars=1), dataset=data)
    assert next(f for f in tampered.findings if f.rule_id == "TIMING.WARMUP").status == "FAIL"


@pytest.mark.parametrize("settings", [
    ExecutionSettings(warmup_start_date=FIRST),
    ExecutionSettings(start_date=FIRST, warmup_start_date=FIRST, warmup_end_date=FIRST),
    ExecutionSettings(start_date=FIRST + timedelta(days=2), warmup_start_date=FIRST - timedelta(days=3), warmup_end_date=FIRST - timedelta(days=1)),
    ExecutionSettings(start_date=FIRST + timedelta(days=2), warmup_start_date="2024-01-01", warmup_end_date=FIRST),
])
def test_invalid_warmup_boundaries_are_rejected(market, settings):
    with pytest.raises(SimulationError):
        simulate(market(), D("1000"), TimeSeriesMomentum(1), settings)


def test_warmup_audit_distinguishes_missing_bad_source_and_invalid_requested_bounds(market):
    data = market()
    settings = ExecutionSettings(start_date=FIRST + timedelta(days=6), warmup_start_date=FIRST,
                                 warmup_end_date=FIRST + timedelta(days=5))
    result = simulate(data, D("1000"), TimeSeriesMomentum(1), settings)
    missing = audit_simulation(result)
    assert next(f for f in missing.findings if f.rule_id == "TIMING.WARMUP").status == "NOT_ASSESSED"
    invalid = replace(data, bars=(replace(data.bars[0], date="invalid"), *data.bars[1:]))
    malformed_source = audit_simulation(result, dataset=invalid)
    assert next(f for f in malformed_source.findings if f.rule_id == "DATA.SOURCE_SEQUENCE").status == "FAIL"
    assert next(f for f in malformed_source.findings if f.rule_id == "TIMING.WARMUP").status == "NOT_ASSESSED"
    invalid_request = audit_simulation(replace(result, settings=replace(settings, start_date=None)), dataset=data)
    assert next(f for f in invalid_request.findings if f.rule_id == "TIMING.WARMUP").status == "FAIL"
    pretest = replace(result, decisions=(replace(result.decisions[0], session=FIRST), *result.decisions[1:]))
    assert next(f for f in audit_simulation(pretest, dataset=data).findings if f.rule_id == "TIMING.WARMUP").status == "FAIL"


def test_selected_buy_and_hold_reuses_test_reference_and_explicit_cost_order(market):
    data = market(closes=["10", "12", "14", "16", "18", "20", "22", "24", "26"])
    result = run_train_test(data, D("1000"), (BuyAndHold(), TimeSeriesMomentum(1)), period(0, 5), period(6, 8))
    assert result.selection.selected_configuration == BuyAndHold()
    assert len(result.test_runs) == 1 and result.selected_test_run_id == result.benchmark_test_run_id
    assert result.planned_workload.run_count == result.actual_workload.run_count + 1
    assert result.test_comparison.final_equity_difference == 0
    costs = (CostScenario(D("2")), CostScenario())
    sensitivity = run_experiment(data, D("1000"), (BuyAndHold(),), costs=costs)
    assert sensitivity.costs == costs
    delta = next(c for c in sensitivity.comparisons if c.kind == "cost_reference")
    assert delta.reference_run_id == sensitivity.runs[0].run_id
    assert sensitivity.runs[0].performance.simulation.settings.commission_per_fill_usd == D("2")


def test_training_selects_on_training_only_and_test_honestly_loses(market):
    data = market()
    result = run_train_test(data, D("1000"), momentum_grid([1, 2]), period(0, 5), period(6, 8))
    candidates = {run.performance.simulation.strategy.lookback: run for run in result.training.runs if run.role == "candidate"}
    assert candidates[1].performance.simulation.final_equity == D("1222")
    assert candidates[2].performance.simulation.final_equity == D("1810")
    assert result.selection.selected_configuration == TimeSeriesMomentum(2)
    assert candidates[2].performance.equity.cumulative_return.value == 0.81
    selected = next(run for run in result.test_runs if run.run_id == result.selected_test_run_id)
    test = selected.performance.simulation
    assert test.strategy == result.selection.selected_configuration
    assert test.valuations[0].cash == test.valuations[0].equity == D("1000") and test.valuations[0].shares == 0
    assert test.warmup_bars == 6 and len(test.valuations) == len(test.decisions) == 3
    assert [(fill.side, fill.session, fill.quantity) for fill in test.fills] == [
        ("BUY", FIRST + timedelta(days=7), 45), ("SELL", FIRST + timedelta(days=8), 45),
    ]
    assert (test.final_cash, test.final_shares, test.final_equity, test.realized_pnl) == (D("460"), 0, D("460"), D("-540"))
    assert selected.performance.equity.cumulative_return.value == -0.54
    assert [point.metric.value for point in selected.performance.equity.daily_returns] == [-0.54, 0.0]
    assert result.planned_workload == result.actual_workload
    assert (result.actual_workload.run_count, result.actual_workload.evaluated_bars, result.actual_workload.warmup_bars) == (5, 24, 12)
    assert result.actual_workload.total_bars == 36


def test_changing_future_test_prices_never_changes_training_selection(market):
    configs = momentum_grid([1, 2])
    original = run_train_test(market(), D("1000"), configs, period(0, 5), period(6, 8))
    changed_data = market(closes=["10", "12", "11", "15", "16", "20", "30", "40", "50"], opens=["10", "10", "12", "11", "15", "16", "20", "30", "40"])
    changed = run_train_test(changed_data, D("1000"), configs, period(0, 5), period(6, 8))
    assert original.selection == changed.selection
    for before, after in zip(original.training.runs, changed.training.runs):
        assert before.performance.equity == after.performance.equity
        assert before.performance.simulation.decisions == after.performance.simulation.decisions
        assert before.performance.simulation.fills == after.performance.simulation.fills
    assert original.test_runs != changed.test_runs


def test_ties_are_canonical_and_testing_without_warmup_starts_cold(market):
    data = market(closes=["10"] * 9)
    result = run_train_test(data, D("1000"), (TimeSeriesMomentum(2), TimeSeriesMomentum(1)), period(0, 5), period(6, 8))
    assert result.selection.selected_configuration == TimeSeriesMomentum(1)
    assert result == run_train_test(data, D("1000"), (TimeSeriesMomentum(1), TimeSeriesMomentum(2)), period(0, 5), period(6, 8))
    cold = run_train_test(market(), D("1000"), momentum_grid([1, 2]), period(0, 5), period(6, 8), warmup=False)
    selected = next(run for run in cold.test_runs if run.run_id == cold.selected_test_run_id)
    assert selected.performance.simulation.warmup_bars == 0
    assert selected.performance.simulation.fills == () and selected.performance.simulation.final_equity == D("1000")


def test_train_test_chronology_is_validated_before_execution(market, monkeypatch):
    calls = no_execution(monkeypatch)
    for train, test in ((period(0, 5), period(5, 8)), (period(4, 8), period(0, 3)), (period(0, 5), period(8, 8))):
        with pytest.raises(ExperimentError):
            run_train_test(market(), D("1000"), momentum_grid([1, 2]), train, test)
    assert calls == []


def test_warmup_uses_training_interval_and_excludes_intervening_gap(market):
    data = market(closes=["10", "12", "11", "1000", "13", "14"], opens=["10", "10", "12", "1000", "13", "13"])
    result = run_train_test(data, D("1000"), (TimeSeriesMomentum(1),), period(0, 2), period(4, 5), include_benchmark=False)
    test = result.test_runs[0].performance.simulation
    assert test.warmup_bars == 3 and test.warmup_end == FIRST + timedelta(days=2)
    assert test.decisions[0].target == "LONG"  # 13/11 > 1; gap's 1000 close is never supplied.
    assert test.fills[0].session == FIRST + timedelta(days=5)


def test_undefined_training_metric_aborts_before_any_test_run(market, monkeypatch):
    original_analysis, original_simulate = runner.analyze_simulation, runner.simulate
    started = []
    def unavailable(simulation, **kwargs):
        report = original_analysis(simulation, **kwargs)
        if type(simulation.strategy) is TimeSeriesMomentum:
            report = replace(report, equity=replace(report.equity, cumulative_return=Metric(None, "synthetic_unavailable")))
        return report
    def observed(*args, **kwargs):
        started.append(args[3].start_date)
        return original_simulate(*args, **kwargs)
    monkeypatch.setattr(runner, "analyze_simulation", unavailable)
    monkeypatch.setattr(runner, "simulate", observed)
    with pytest.raises(ExperimentError, match="Undefined training.*synthetic_unavailable"):
        run_train_test(market(), D("1000"), momentum_grid([1, 2]), period(0, 5), period(6, 8))
    assert started and all(start == FIRST for start in started)


def test_selection_never_accepts_test_rankings_and_runtime_failure_is_atomic(market, monkeypatch):
    completed = run_experiment(market(), D("1000"), (TimeSeriesMomentum(1),), include_benchmark=False)
    with pytest.raises(ExperimentError, match="training candidate"):
        runner._select_training((replace(completed.runs[0], phase="test"),))
    original = runner.simulate
    calls = []
    def fail_second(*args, **kwargs):
        calls.append(args)
        if len(calls) == 2:
            raise SimulationError("handcrafted execution failure")
        return original(*args, **kwargs)
    monkeypatch.setattr(runner, "simulate", fail_second)
    with pytest.raises(ExperimentError, match="Run run_002.*no returned partial result"):
        run_experiment(market(), D("1000"), momentum_grid([1, 2]))
    assert len(calls) == 2


def test_immutability_source_fingerprint_and_context_independence(market):
    data = market()
    before = deepcopy(data)
    result = run_experiment(data, D("1000"), momentum_grid([1, 2]))
    snapshot = result.reproducibility
    encoded = json.dumps(snapshot.source_files, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    assert snapshot.source_snapshot_sha256 == sha256(encoded).hexdigest()
    assert snapshot.source_files == tuple(sorted(snapshot.source_files))
    assert all(not Path(path).is_absolute() and len(digest) == 64 for path, digest in snapshot.source_files)
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        assert run_experiment(data, D("1000"), momentum_grid([1, 2])) == result
    assert data == before
    assert any(f.status == "NOT_ASSESSED" and f.rule_id == "LIMITS.OVERFITTING" for f in result.runs[0].audit.findings)
    json.dumps(asdict(result), default=str, allow_nan=False)
