"""Reproducible local engineering timings; invented data, no market performance claim."""

import argparse
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import platform
import sqlite3
from statistics import median
import sys
from tempfile import TemporaryDirectory
from time import perf_counter_ns

from quantlab.application.requests import ExperimentRequest
from quantlab.application.service import execute, import_dataset
from quantlab.audit import audit_simulation
from quantlab.data import load_dataset_bytes
from quantlab.execution import ExecutionSettings, simulate
from quantlab.experiments import run_experiment, sma_grid
from quantlab.experiments.reproducibility import source_snapshot
from quantlab.persistence import Store
from quantlab.strategies import SMACrossover


ROOT = Path(__file__).resolve().parents[1]
CAPITAL = Decimal("10000.00")
SETTINGS = ExecutionSettings(commission_per_fill_usd=Decimal("0.50"), slippage_bps=Decimal("5"))


def synthetic_input(count: int) -> tuple[bytes, bytes]:
    """Integer-cent triangular closes, prior close opens, invented calendar-day labels."""
    metadata = json.loads((ROOT / "frontend/public/examples/nine_sessions.metadata.json").read_bytes())
    metadata.update(symbol="BENCH_SYNTH", source_name="QuantLab deterministic benchmark observations",
                    source_reference="scripts/benchmark.py: synthetic_input; invented daily labels from 2000-01-01",
                    split_evidence="Invented event-free benchmark; no assertion about any real security")
    rows = ["date,open,high,low,close,volume\n"]
    previous = 10000

    def price(cents):
        return f"{cents // 100}.{cents % 100:02}"

    for i in range(count):
        phase = i % 100
        close = 10000 + 5 * (phase if phase <= 50 else 100 - phase)
        session = date(2000, 1, 1) + timedelta(days=i)
        values = (previous, max(previous, close) + 10, min(previous, close) - 10, close)
        rows.append(f"{session}," + ",".join(map(price, values)) + ",100000\n")
        previous = close
    return "".join(rows).encode("utf-8"), json.dumps(metadata, sort_keys=True).encode("utf-8")


def measure(operation, repeats):
    warm = operation()  # One untimed operation-specific warm-up; OS caches are not flushed.
    del warm
    samples = []
    for _ in range(repeats):
        start = perf_counter_ns()
        value = operation()
        samples.append(perf_counter_ns() - start)
        del value  # Result destruction is outside the measured interval.
    return {"samples_ns": samples, "median_ms": median(samples) / 1e6,
            "min_ms": min(samples) / 1e6, "max_ms": max(samples) / 1e6}


def cpu_name():
    if sys.platform == "win32":
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
            return winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
    return platform.processor() or "unreported"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/benchmark-results/phase10.json")
    args = parser.parse_args()
    if not 3 <= args.repeats <= 20:
        parser.error("Use 3..20 measured repetitions.")
    report = {
        "recorded_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "platform": platform.platform(), "cpu": cpu_name(), "logical_processors": os.cpu_count(),
        "sqlite": sqlite3.sqlite_version, "repeats": args.repeats, "untimed_warmups_per_operation": 1,
        "timer": "time.perf_counter_ns; GC enabled; cached local inputs; no concurrent benchmark jobs",
        "capital_usd": str(CAPITAL), "commission_per_fill_usd": "0.50", "slippage_bps": "5",
        "strategy": "SMA(5,20)", "grid": "SMA fast=[5,10], slow=[20,40], plus buy-and-hold reference (5 runs)",
        "source_snapshot_sha256": source_snapshot().source_snapshot_sha256,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "results": [],
    }
    scratch = ROOT / ".release-check"
    scratch.mkdir(exist_ok=True)
    for count in (250, 1000, 5000):
        csv, metadata = synthetic_input(count)
        assert synthetic_input(count) == (csv, metadata)
        dataset = load_dataset_bytes(csv, metadata)
        assert dataset.report.row_count == count
        simulation = simulate(dataset, CAPITAL, SMACrossover(5, 20), SETTINGS)
        grid = sma_grid([5, 10], [20, 40])
        with TemporaryDirectory(prefix="benchmark-", dir=scratch) as folder:
            assert Path(folder).resolve().is_relative_to(scratch.resolve())
            store = Store(Path(folder) / "research.sqlite3")
            store.initialize()
            imported, _ = import_dataset(store, csv.decode("utf-8"), json.loads(metadata))
            request = ExperimentRequest.model_validate({
                "dataset_id": imported["dataset_id"], "initial_capital": str(CAPITAL),
                "configurations": [{"kind": "sma", "fast_window": 5, "slow_window": 20}],
                "include_benchmark": False, "settings": {"commission_per_fill_usd": "0.50", "slippage_bps": "5"},
            })
            saved = execute(store, request)  # Preparation/write is intentionally untimed.
            operations = {
                "import_validate": lambda: load_dataset_bytes(csv, metadata),
                "sma_simulation": lambda: simulate(dataset, CAPITAL, SMACrossover(5, 20), SETTINGS),
                "grid_with_analytics_audit": lambda: run_experiment(dataset, CAPITAL, grid, settings=SETTINGS),
                "audit_with_source_no_replay": lambda: audit_simulation(simulation, dataset=dataset,
                    source_bytes=csv, source_metadata=dataset.metadata, expected_settings=SETTINGS, rerun=False),
                "sqlite_retrieval": lambda: store.get_experiment(saved["experiment_id"]),
            }
            values = {}
            for name, operation in operations.items():
                values[name] = measure(operation, args.repeats)
                print(f"{count:5} {name}: median {values[name]['median_ms']:.3f} ms", flush=True)
            assert not any(f.status == "FAIL" for f in operations["audit_with_source_no_replay"]().findings)
            assert store.get_experiment(saved["experiment_id"]) == saved
        report["results"].append({"bars": count, "csv_bytes": len(csv), "dataset_id": dataset.report.dataset_id,
                                  "source_sha256": dataset.report.source_sha256, "operations": values})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(f"Evidence written: {args.output}", flush=True)


if __name__ == "__main__":
    main()
