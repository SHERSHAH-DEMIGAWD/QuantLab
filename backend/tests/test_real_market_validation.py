"""Opt-in frozen private observations; no network, credentials or bundled market data.

See docs/REAL_MARKET_VALIDATION.md. An unset directory skips these six cases;
an explicitly selected missing/changed snapshot fails rather than fetching data.
"""

from collections import Counter
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from quantlab.api import create_app
from quantlab.application import service
from quantlab.audit import audit_simulation
from quantlab.data import DataValidationError, load_dataset_bytes
from quantlab.execution import ExecutionSettings, SimulationError, simulate
from quantlab.experiments import CostScenario, run_experiment
from quantlab.strategies import BuyAndHold, SMACrossover, TimeSeriesMomentum


SNAPSHOTS = {
    "IBM": (
        "309247171fca407fc9192018b402ef325b9da3d472c856513f4de5b6d84f714c",
        "e4370c73b5c3e4124a822e5da7dd68ff034bb1c7b586a9ee818cf487b58d2a01",
        "7d4799203d49cc05b7daf757b3f3ab698938f536ec812be48c92c632809a8ed9",
        # (final equity, fills, final shares, closed trades), ordered BH, momentum, SMA.
        (("9074.95", 1, 35, 0), ("8745.50", 13, 34, 6), ("7631.86", 9, 30, 4),
         ("9064.19", 1, 35, 0), ("8630.86", 13, 34, 6), ("7531.79", 9, 29, 4)),
    ),
    "MSFT": (
        "273963944d18d68064a9d4a08c90d97110a789b08cad36046c0c49da67ce7027",
        "a726c91f361fdadbcc17b00fd2304e38e705286379305ab693fcd15bf93e1796",
        "a5b7121ab20f21f78e6acf3fbe2db9c33aba93ea8b695feeb4458fba13930d2a",
        (("12892.25", 1, 25, 0), ("11878.72", 12, 0, 6), ("11449.87", 10, 0, 5),
         ("12881.46", 1, 25, 0), ("11736.21", 12, 0, 6), ("11346.42", 10, 0, 5)),
    ),
}
CAPITAL = Decimal("10000.00")
CONFIGURATIONS = (BuyAndHold(), SMACrossover(5, 20), TimeSeriesMomentum(10))
SETTINGS = ExecutionSettings(acknowledge_unverified_coverage=True)


@pytest.fixture(params=tuple(SNAPSHOTS), scope="module")
def real_sample(request):
    directory = os.environ.get("QUANTLAB_REAL_MARKET_DIR")
    if not directory:
        pytest.skip("Private real-data snapshot unavailable: set QUANTLAB_REAL_MARKET_DIR; no live fetch.")
    root, symbol = Path(directory), request.param
    raw = (root / f"{symbol}.TIME_SERIES_DAILY.json").read_bytes()
    source = (root / f"{symbol}.csv").read_bytes()
    metadata_bytes = (root / f"{symbol}.metadata.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SNAPSHOTS[symbol][0]
    assert hashlib.sha256(source).hexdigest() == SNAPSHOTS[symbol][1]
    dataset = load_dataset_bytes(source, metadata_bytes)
    assert dataset.report.dataset_id == SNAPSHOTS[symbol][2]
    return symbol, dataset, source, metadata_bytes, json.loads(raw)


def test_real_import_preserves_all_observations_and_eligibility_gates(real_sample):
    symbol, dataset, source, metadata_bytes, raw = real_sample
    assert dataset.metadata.source_kind == "local_file"
    assert dataset.metadata.symbol == raw["Meta Data"]["2. Symbol"] == symbol
    assert len(dataset.bars) == dataset.report.row_count == 100
    assert str(dataset.bars[0].date) == "2026-06-11"
    assert str(dataset.bars[-1].date) == "2026-11-02"
    assert dataset.report.zero_volume_rows == 0
    assert dataset.report.coverage_assessment == "unverified"
    for bar in dataset.bars:
        values = raw["Time Series (Daily)"][str(bar.date)]
        assert (bar.open, bar.high, bar.low, bar.close, bar.volume) == (
            *(Decimal(values[key]) for key in ("1. open", "2. high", "3. low", "4. close")),
            int(values["5. volume"]),
        )
    with pytest.raises(SimulationError, match="explicit acknowledgment"):
        simulate(dataset, CAPITAL)
    # An unavailable split check never turns into an eligible no-event declaration.
    unknown = json.loads(metadata_bytes)
    unknown.update(split_status="unknown", split_evidence="unknown")
    blocked = load_dataset_bytes(source, json.dumps(unknown).encode())
    with pytest.raises(SimulationError, match="D04 eligibility"):
        simulate(blocked, CAPITAL, settings=SETTINGS)
    with pytest.raises(DataValidationError):
        load_dataset_bytes(source + source.splitlines(keepends=True)[1], metadata_bytes)


def _half_up(value: Fraction, scale: int) -> Fraction:
    """Positive rational rounding, independent of production Decimal/cost helpers."""
    scaled = value * scale
    return Fraction((2 * scaled.numerator + scaled.denominator) // (2 * scaled.denominator), scale)


def _check_metrics(performance, equities, dates):
    # Exact rational ratios then explicit two-pass sample variance, without analytics calls.
    returns = [float(b / a - 1) for a, b in zip(equities, equities[1:])]
    mean = math.fsum(returns) / len(returns)
    deviation = math.sqrt(math.fsum((value - mean) ** 2 for value in returns) / (len(returns) - 1))
    peak, drawdown = equities[0], Fraction(0)
    for equity in equities:
        peak = max(peak, equity)
        drawdown = max(drawdown, 1 - equity / peak)
    expected = {
        "cumulative_return": float(equities[-1] / equities[0] - 1),
        "annualized_return": float(equities[-1] / equities[0]) ** (365.25 / (dates[-1] - dates[0]).days) - 1,
        "maximum_drawdown": float(drawdown),
        "annualized_volatility": deviation * math.sqrt(252),
        "sharpe_ratio": math.sqrt(252) * mean / deviation,
    }
    for name, value in expected.items():
        assert getattr(performance.equity, name).value == pytest.approx(value, rel=1e-12, abs=1e-12)


def test_real_strategies_costs_independent_references_and_source_backed_audit(real_sample):
    symbol, dataset, source, _, _ = real_sample
    result = run_experiment(
        dataset, CAPITAL, CONFIGURATIONS, settings=SETTINGS,
        costs=(CostScenario(), CostScenario(Decimal("1.00"), Decimal("10"))),
    )
    assert len(result.runs) == 6
    closes = [Fraction(bar.close) for bar in dataset.bars]
    for run, expected in zip(result.runs, SNAPSHOTS[symbol][3], strict=True):
        p, s = run.performance, run.performance.simulation
        assert (s.final_equity, len(s.fills), s.final_shares, len(p.trades.closed_trades)) == (
            Decimal(expected[0]), *expected[1:],
        )
        equities = [Fraction(v.equity) for v in s.valuations]
        if isinstance(s.strategy, BuyAndHold):
            # Closed-form single purchase/hold reference from raw source, no event loop.
            price = _half_up(Fraction(dataset.bars[1].open) * (1 + Fraction(s.settings.slippage_bps) / 10000), 1_000_000)
            fee = _half_up(Fraction(s.settings.commission_per_fill_usd), 100)
            quantity = (Fraction(CAPITAL) - fee) // price
            cash = Fraction(CAPITAL) - _half_up(quantity * price, 100) - fee
            equities = [Fraction(CAPITAL)] + [cash + quantity * close for close in closes[1:]]
            assert Fraction(s.final_cash) == cash and s.final_shares == quantity
            assert [Fraction(v.equity) for v in s.valuations] == equities
        else:
            # Direct slice sums/ratios cross-check streaming targets; no simulated fills.
            for index, decision in enumerate(s.decisions):
                if isinstance(s.strategy, SMACrossover):
                    if index < 19:
                        target = "HOLD"
                    else:
                        fast = sum(closes[index - 4:index + 1]) / 5
                        slow = sum(closes[index - 19:index + 1]) / 20
                        target = "LONG" if fast > slow else "FLAT" if fast < slow else "HOLD"
                else:
                    target = "HOLD" if index < 10 else "LONG" if closes[index] / closes[index - 10] - 1 > 0 else "FLAT"
                assert decision.target == target
        _check_metrics(p, equities, [v.session for v in s.valuations])
        audit = audit_simulation(s, dataset=dataset, source_bytes=source,
                                 source_metadata=dataset.metadata, expected_settings=s.settings, rerun=True)
        statuses = Counter(f.status for f in audit.findings)
        assert statuses["FAIL"] == 0
        assert statuses["PASS"] > 0 and statuses["WARNING"] > 0 and statuses["NOT_ASSESSED"] > 0
        assert next(f for f in audit.findings if f.rule_id == "REPRODUCIBILITY.REPLAY").status == "PASS"


def test_real_robustness_retention_restart_and_fresh_reproduction(real_sample, tmp_path, monkeypatch):
    _, dataset, source, metadata_bytes, _ = real_sample
    database = tmp_path / "real-validation.sqlite3"
    app = create_app(database)
    configs = [
        {"kind": "sma", "fast_window": 3, "slow_window": 10},
        {"kind": "sma", "fast_window": 5, "slow_window": 20},
        {"kind": "momentum", "lookback": 5}, {"kind": "momentum", "lookback": 10},
    ]
    periods = [{"start_date": "2026-06-11", "end_date": "2026-09-04"},
               {"start_date": "2026-09-08", "end_date": "2026-11-02"}]
    common = {"dataset_id": dataset.report.dataset_id, "initial_capital": "10000.00",
              "configurations": configs, "include_benchmark": True,
              "settings": {"acknowledge_unverified_coverage": True}}
    with TestClient(app, base_url="http://localhost") as client:
        payload = {"csv_text": source.decode(), "metadata": json.loads(metadata_bytes)}
        assert client.post("/api/v1/datasets", json=payload).status_code == 201
        repeated = client.post("/api/v1/datasets", json=payload)
        assert repeated.status_code == 200 and repeated.json()["dataset_id"] == dataset.report.dataset_id
        saved = []
        for request in (
            {**common, "mode": "grid", "periods": periods,
             "costs": [{"commission_per_fill_usd": "0.00", "slippage_bps": "0"},
                       {"commission_per_fill_usd": "1.00", "slippage_bps": "10"}]},
            {**common, "mode": "train_test", "training_period": periods[0], "test_period": periods[1]},
        ):
            response = client.post("/api/v1/experiments", json=request)
            assert response.status_code == 201, response.text
            saved.append(response.json())
        assert len(saved[0]["result"]["runs"]) == 20
        held_out = saved[1]["result"]
        assert len(held_out["training"]["runs"]) == 5
        assert len(held_out["test_runs"]) == 2
        for run in held_out["test_runs"]:
            simulation = run["performance"]["simulation"]
            assert simulation["warmup_bars"] == 60
            assert len(simulation["valuations"]) == 40
            first = simulation["valuations"][0]
            assert Decimal(first["equity"]) == Decimal(first["cash"]) == CAPITAL
            assert first["shares"] == 0
            assert all(fill["session"] > "2026-09-08" for fill in simulation["fills"])
    with app.state.store.connection() as connection:
        assert connection.execute("SELECT source_csv FROM datasets").fetchone()[0] == source
    calls, compute = [], service._compute

    def observed_compute(*args):
        calls.append(True)
        return compute(*args)

    monkeypatch.setattr(service, "_compute", observed_compute)
    with TestClient(create_app(database), base_url="http://localhost") as restarted:
        for record in saved:
            identifier = record["experiment_id"]
            assert restarted.get(f"/api/v1/experiments/{identifier}").json() == record
        assert calls == []
        for record in saved:
            response = restarted.post(f'/api/v1/experiments/{record["experiment_id"]}/reproduce')
            assert response.status_code == 200
            reproduced = response.json()
            assert reproduced["economic_match"] is True and reproduced["implementation_match"] is True
        assert len(calls) == 2
