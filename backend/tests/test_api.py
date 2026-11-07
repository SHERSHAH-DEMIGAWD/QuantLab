"""Real HTTP -> retained CSV -> research engine -> SQLite -> reproduction tests."""

from dataclasses import asdict
from datetime import date, timedelta
from decimal import Decimal
import json
from pathlib import Path
import sqlite3

import pytest
from fastapi.testclient import TestClient

from quantlab.api import create_app
from quantlab.api import boundary
from quantlab.application import service
from quantlab.data import load_dataset, load_dataset_bytes
from quantlab.experiments import runner
from quantlab.persistence import SchemaError, Store, StorageError
from quantlab.persistence.codec import digest, dumps, loads, to_wire

D = Decimal
FIXTURES = Path(__file__).parent / "fixtures"
METADATA = json.loads((FIXTURES / "synthetic_daily.metadata.json").read_text())


def csv_text(closes=(10, 12, 11, 15, 16, 20, 22, 10, 8), opens=(10, 10, 12, 11, 15, 16, 20, 22, 10)):
    rows = ["date,open,high,low,close,volume\n"]
    for index, (open_, close) in enumerate(zip(opens, closes, strict=True)):
        rows.append(f"{date(2024,1,1)+timedelta(days=index)},{open_},{max(D(open_),D(close))},{min(D(open_),D(close))},{close},100\n")
    return "".join(rows)


@pytest.fixture
def backend(tmp_path):
    path = tmp_path / "research.sqlite3"
    app = create_app(path)
    with TestClient(app, base_url="http://localhost", raise_server_exceptions=False) as client:
        yield client, app.state.store, path


def upload(client, text=None, metadata=None):
    return client.post("/api/v1/datasets", json={"csv_text": csv_text() if text is None else text,
                                               "metadata": METADATA if metadata is None else metadata})


def request(dataset_id, **changes):
    return {"dataset_id": dataset_id, "initial_capital": "1000", "configurations": [{"kind": "buy_and_hold"}], **changes}


def save(client, **changes):
    data = upload(client).json()
    response = client.post("/api/v1/experiments", json=request(data["dataset_id"], **changes))
    assert response.status_code == 201, response.text
    return response.json()


def count(store, table):
    assert table in ("datasets", "experiments")
    with store.connection() as connection:
        return connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def test_fresh_repeat_initialization_schema_keys_and_health(backend):
    client, store, _ = backend
    store.initialize()
    assert client.get("/api/v1/health").json() == {"status": "ok", "api_version": "1.0.0", "schema_version": 1}
    with store.connection() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
        assert {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")} == {"datasets", "experiments"}
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO experiments VALUES ('id','missing','backtest','{}','h','{}','h','{}','now')")


@pytest.mark.parametrize("setup", ["PRAGMA user_version=99", "CREATE TABLE unrelated (id TEXT)", "CREATE TABLE datasets (id TEXT); PRAGMA user_version=1"])
def test_unsupported_and_malformed_schemas_are_not_overwritten(tmp_path, setup):
    path = tmp_path / "unsupported.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.executescript(setup)
    with pytest.raises(SchemaError):
        Store(path).initialize()
    with sqlite3.connect(path) as connection:
        assert not connection.execute("SELECT 1 FROM sqlite_master WHERE name='experiments'").fetchone()


def test_file_and_byte_imports_share_exact_existing_contract():
    source = (FIXTURES / "synthetic_daily.csv").read_bytes()
    metadata = (FIXTURES / "synthetic_daily.metadata.json").read_bytes()
    assert load_dataset_bytes(source, metadata) == load_dataset(FIXTURES / "synthetic_daily.csv", FIXTURES / "synthetic_daily.metadata.json")


def test_schema_creation_is_atomic_and_live_unsupported_versions_are_blocked(tmp_path, monkeypatch):
    from quantlab.persistence import store as storage_module
    path = tmp_path / "schema_failure.sqlite3"
    original = storage_module.SCHEMA
    monkeypatch.setattr(storage_module, "SCHEMA", (original[0], "INVALID SQL"))
    with pytest.raises(StorageError):
        Store(path).initialize()
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 0
        assert not connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    monkeypatch.setattr(storage_module, "SCHEMA", original)
    store = Store(path)
    store.initialize()
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA user_version=99")
    with pytest.raises(SchemaError):
        store.list_datasets(50, 0)


def test_missing_retained_dataset_is_unavailable_and_identity_conflicts_never_overwrite(backend):
    client, store, path = backend
    saved = save(client)
    with store.transaction() as connection:
        connection.execute("UPDATE datasets SET source_csv=?", (b"conflicting bytes",))
    conflict = upload(client)
    assert conflict.status_code == 409
    with store.connection() as connection:
        assert connection.execute("SELECT source_csv FROM datasets").fetchone()[0] == b"conflicting bytes"
    # Simulate externally damaged retention; application connections always enforce FKs.
    with sqlite3.connect(path) as connection:
        connection.execute("DELETE FROM datasets")
    reproduction = client.post("/api/v1/experiments/" + saved["experiment_id"] + "/reproduce")
    assert reproduction.status_code == 409 and "unavailable" in reproduction.json()["error"]["message"]


def test_original_bom_crlf_metadata_identity_duplicates_and_retrieval(backend):
    client, store, _ = backend
    source = "\ufeff" + csv_text().replace("\n", "\r\n")
    first = upload(client, source)
    assert first.status_code == 201 and first.json()["duplicate"] is False
    value = first.json()
    again = upload(client, source)
    assert again.status_code == 200 and again.json()["duplicate"] is True
    assert again.json()["dataset_id"] == value["dataset_id"] and again.json()["created_at"] == value["created_at"]
    assert count(store, "datasets") == 1
    with store.connection() as connection:
        assert connection.execute("SELECT source_csv FROM datasets").fetchone()[0] == source.encode("utf-8")
    reconstructed = store.reconstruct_dataset(value["dataset_id"])
    assert reconstructed.report.dataset_id == value["dataset_id"]
    fetched = client.get("/api/v1/datasets/" + value["dataset_id"]).json()
    assert fetched["metadata"] == asdict(reconstructed.metadata)
    assert fetched["validation"]["normalization"]["csv_bom_removed"] is True
    assert fetched["validation"]["coverage_assessment"] == "unverified"
    assert client.get("/api/v1/datasets?limit=1&offset=0").json()["items"][0]["dataset_id"] == value["dataset_id"]
    changed = upload(client, source.replace(",100\r\n", ",101\r\n"))
    assert changed.status_code == 201 and changed.json()["dataset_id"] != value["dataset_id"]
    assert count(store, "datasets") == 2
    assert client.get("/api/v1/datasets/" + value["dataset_id"]).json() == fetched


@pytest.mark.parametrize("source,metadata,code", [
    ("", METADATA, "empty_input"),
    ("date,open,high,low,close,volume\n2024-01-01,10,5,9,10,1\n", METADATA, "invalid_ohlc"),
    (csv_text(), {**METADATA, "currency": "EUR"}, "invalid_metadata_value"),
    (csv_text(), {**METADATA, "extra": "unknown"}, "unknown_metadata_field"),
    (csv_text(), {**METADATA, "contract_version": True}, "unsupported_contract_version"),
])
def test_bad_imports_keep_field_diagnostics_and_no_partial_record(backend, source, metadata, code):
    client, store, _ = backend
    response = upload(client, source, metadata)
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "invalid_dataset"
    assert code in {issue["code"] for issue in error["details"]["issues"]}
    assert count(store, "datasets") == 0


def test_successful_cost_backtest_retains_exact_accounting_histories_and_undefined_metrics(backend):
    client, store, _ = backend
    data = upload(client, csv_text((100, 100, 110), (100, 100, 100))).json()
    response = client.post("/api/v1/experiments", json=request(data["dataset_id"], settings={"commission_per_fill_usd": "2", "slippage_bps": "100"}))
    assert response.status_code == 201, response.text
    saved = response.json()
    run, = saved["result"]["runs"]  # Candidate/reference share buy-and-hold.
    simulation = run["performance"]["simulation"]
    assert (simulation["final_cash"], simulation["final_shares"], simulation["final_equity"]) == ("89.00", 9, "1079.00")
    assert simulation["fills"][0]["effective_price"] == "101.000000"
    assert simulation["fills"][0]["fee"] == "2.00"
    assert [v["session"] for v in simulation["valuations"]] == ["2024-01-01", "2024-01-02", "2024-01-03"]
    assert simulation["valuations"][0]["equity"] == "1000.00" and simulation["valuations"][-1]["shares"] == 9
    assert run["performance"]["equity"]["cumulative_return"]["value"] == 0.079
    assert run["performance"]["trades"]["win_rate"] == {"value": None, "reason": "no_closed_trades"}
    assert run["performance"]["trades"]["open_position"]["quantity"] == 9
    assert any(f["status"] == "NOT_ASSESSED" and f["rule_id"] == "LIMITS.OVERFITTING" for f in run["audit"]["findings"])
    assert not any(f["status"] == "FAIL" for f in run["audit"]["findings"])
    assert client.get("/api/v1/experiments/" + saved["experiment_id"]).json() == saved
    assert count(store, "experiments") == 1


def test_grid_costs_periods_and_sma_are_real_saved_experiments(backend):
    client, _, _ = backend
    saved = save(client, mode="grid", configurations=[{"kind": "sma", "fast_window": 1, "slow_window": 3}, {"kind": "momentum", "lookback": 1}],
                 costs=[{}, {"commission_per_fill_usd": "2"}],
                 periods=[{"start_date": "2024-01-01", "end_date": "2024-01-03"}, {"start_date": "2024-01-04", "end_date": "2024-01-09"}])
    result = saved["result"]
    assert result["experiment_type"] == "combined" and result["workload"]["run_count"] == 12
    assert result["workload"]["evaluated_bars"] == 54
    assert {c["kind"] for c in result["comparisons"]} == {"benchmark", "cost_reference"}
    assert all(r["performance"]["simulation"]["dataset_id"] == saved["dataset_id"] for r in result["runs"])


def test_train_test_preserves_frozen_selection_fresh_cash_and_disappointing_results(backend):
    client, _, _ = backend
    saved = save(client, mode="train_test", configurations=[{"kind": "momentum", "lookback": 1}, {"kind": "momentum", "lookback": 2}],
                 training_period={"start_date": "2024-01-01", "end_date": "2024-01-06"},
                 test_period={"start_date": "2024-01-07", "end_date": "2024-01-09"})
    result = saved["result"]
    assert result["selection"]["selected_configuration"] == {"lookback": 2, "threshold": "0"}
    selected = next(run for run in result["test_runs"] if run["run_id"] == result["selected_test_run_id"])
    simulation = selected["performance"]["simulation"]
    assert simulation["warmup_bars"] == 6 and len(simulation["valuations"]) == 3
    assert simulation["valuations"][0]["cash"] == "1000.00" and simulation["valuations"][0]["shares"] == 0
    assert simulation["fills"][0]["session"] == "2024-01-08" and simulation["final_equity"] == "460.00"
    assert selected["performance"]["equity"]["cumulative_return"]["value"] == -0.54
    assert selected["performance"]["trades"]["closed_trades"][0]["net_pnl"] == "-540.00"


def test_restart_retrieval_pagination_filtering_and_real_reexecution(backend, monkeypatch):
    client, store, path = backend
    saved = save(client)
    second = save(client, configurations=[{"kind": "momentum", "lookback": 1}])
    with TestClient(create_app(path), base_url="http://localhost") as restarted:
        assert restarted.get("/api/v1/experiments/" + saved["experiment_id"]).json() == saved
        listing = restarted.get(f'/api/v1/experiments?dataset_id={saved["dataset_id"]}&limit=1&offset=1').json()
        assert [r["experiment_id"] for r in listing["items"]] == [second["experiment_id"]]
        calls = []
        original = service._compute
        def observed(*args):
            calls.append(args)
            return original(*args)
        monkeypatch.setattr(service, "_compute", observed)
        reproduction = restarted.post("/api/v1/experiments/" + saved["experiment_id"] + "/reproduce")
        assert reproduction.status_code == 200 and reproduction.json()["status"] == "matched"
        assert reproduction.json()["economic_match"] and reproduction.json()["implementation_match"]
        assert len(calls) == 1
        assert restarted.get("/api/v1/experiments/" + saved["experiment_id"]).json() == saved
    assert count(store, "experiments") == 2


def test_reproduction_detects_changed_economics_and_implementation_separately(backend):
    client, store, _ = backend
    saved = save(client)
    altered = saved["result"]
    altered["runs"][0]["performance"]["simulation"]["final_equity"] = "999.00"
    payload = dumps(altered)
    with store.transaction() as connection:
        connection.execute("UPDATE experiments SET result_json=?,result_sha256=? WHERE experiment_id=?", (payload, digest(payload), saved["experiment_id"]))
    response = client.post("/api/v1/experiments/" + saved["experiment_id"] + "/reproduce").json()
    assert response["status"] == "mismatch" and response["economic_match"] is False
    assert any(path.endswith("simulation.final_equity") for path in response["difference_paths"])
    other = save(client)
    implementation = {**other["implementation"], "engine_version": "older-simulated-version"}
    with store.transaction() as connection:
        connection.execute("UPDATE experiments SET implementation_json=? WHERE experiment_id=?", (dumps(implementation), other["experiment_id"]))
    response = client.post("/api/v1/experiments/" + other["experiment_id"] + "/reproduce").json()
    assert response["status"] == "implementation_changed" and response["economic_match"] is True
    assert response["implementation_match"] is False and "original implementation" in response["limitations"][-1]


@pytest.mark.parametrize("mutation", ["result_checksum", "request_checksum", "csv", "payload_version", "request_version", "metadata_type"])
def test_unavailable_or_corrupt_retained_inputs_fail_honestly(backend, mutation):
    client, store, _ = backend
    saved = save(client)
    with store.transaction() as connection:
        if mutation == "result_checksum":
            connection.execute("UPDATE experiments SET result_json='{}'")
        elif mutation == "request_checksum":
            connection.execute("UPDATE experiments SET request_json='{}'")
        elif mutation == "csv":
            connection.execute("UPDATE datasets SET source_csv=?", (b"invalid",))
        elif mutation == "request_version":
            changed = dumps({**saved["request"], "request_version": 99})
            connection.execute("UPDATE experiments SET request_json=?,request_sha256=?", (changed, digest(changed)))
        elif mutation == "metadata_type":
            connection.execute("UPDATE datasets SET metadata_json=?", (b"invalid",))
        else:
            changed = {**saved["implementation"], "payload_version": 99}
            connection.execute("UPDATE experiments SET implementation_json=?", (dumps(changed),))
    response = client.post("/api/v1/experiments/" + saved["experiment_id"] + "/reproduce")
    assert response.status_code == 409 and response.json()["error"]["code"] == "retained_evidence_unavailable"


@pytest.mark.parametrize("changes", [
    {"initial_capital": 1000}, {"initial_capital": "NaN"}, {"initial_capital": "-1"},
    {"request_version": True}, {"request_version": 1.0},
    {"configurations": [{"kind": "momentum", "lookback": 1, "threshold": "1e999999999"}]},
    {"configurations": [{"kind": "sma", "fast_window": True, "slow_window": 3}]},
    {"configurations": [{"kind": "sma", "fast_window": 3, "slow_window": 3}]},
    {"configurations": [{"kind": "momentum", "lookback": 0}]},
    {"configurations": [{"kind": "python", "code": "arbitrary()"}]},
    {"settings": {"slippage_bps": "10000"}}, {"settings": {"commission_per_fill_usd": "-1"}},
    {"periods": [{"start_date": "2024-02-30", "end_date": "2024-03-01"}]},
    {"periods": [{"start_date": "2024-01-09", "end_date": "2024-01-09"}]},
    {"periods": [{"start_date": "2024-02-01", "end_date": "2024-02-02"}]},
    {"csv_path": "C:/private.csv"},
])
def test_invalid_api_configuration_never_saves_completed_experiment(backend, changes):
    client, store, _ = backend
    data = upload(client).json()
    response = client.post("/api/v1/experiments", json=request(data["dataset_id"], **changes))
    assert response.status_code == 422 and count(store, "experiments") == 0
    assert "Traceback" not in response.text


def test_eligibility_still_blocks_imported_unknown_splits_and_requires_coverage_ack(backend):
    client, store, _ = backend
    for metadata in ({**METADATA, "split_status": "unknown"}, {**METADATA, "source_kind": "local_file"}):
        data = upload(client, metadata=metadata)
        assert data.status_code == 201
        response = client.post("/api/v1/experiments", json=request(data.json()["dataset_id"]))
        assert response.status_code == 422
    assert count(store, "experiments") == 0


def test_configuration_and_full_aggregate_bar_caps_apply_before_engine_execution(backend, monkeypatch):
    client, store, _ = backend
    source = csv_text([10] * 10001, [10] * 10001)
    data = upload(client, source).json()
    calls = []
    def forbidden(*args, **kwargs):
        calls.append(args)
        raise AssertionError("Engine should not start before budget rejection")
    monkeypatch.setattr(runner, "simulate", forbidden)
    configs = [{"kind": "sma", "fast_window": fast, "slow_window": 101} for fast in range(1, 101)]
    for payload in (
        request(data["dataset_id"], mode="grid", configurations=configs, include_benchmark=True),
        request(data["dataset_id"], mode="grid", configurations=configs, include_benchmark=False),
        request(data["dataset_id"], mode="grid", configurations=configs + [{"kind": "buy_and_hold"}]),
    ):
        response = client.post("/api/v1/experiments", json=payload)
        assert response.status_code == 422, response.text
    assert calls == [] and count(store, "experiments") == 0


@pytest.mark.parametrize("table", ["datasets", "experiments"])
def test_failed_writes_roll_back_and_do_not_report_success(backend, table):
    client, store, _ = backend
    data = upload(client).json() if table == "experiments" else None
    with store.connection() as connection:
        connection.execute(f"CREATE TRIGGER injected_failure AFTER INSERT ON {table} BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
    response = upload(client) if table == "datasets" else client.post("/api/v1/experiments", json=request(data["dataset_id"]))
    assert response.status_code == 503 and count(store, table) == 0
    assert "injected failure" not in response.text


def test_unknown_ids_pagination_and_unrecognized_routes_have_structured_errors(backend):
    client, _, _ = backend
    for method, url, body in (
        ("GET", "/api/v1/datasets/" + "a"*64, None),
        ("GET", "/api/v1/experiments/" + "b"*32, None),
        ("POST", "/api/v1/experiments/" + "b"*32 + "/reproduce", None),
        ("POST", "/api/v1/experiments", request("a"*64)),
    ):
        response = client.request(method, url, json=body)
        assert response.status_code == 404 and response.json()["error"]["code"] == "not_found"
    assert client.get("/api/v1/datasets?limit=101").status_code == 422
    assert client.get("/api/v1/datasets?offset=-1").status_code == 422
    assert client.get("/missing").json()["error"]["code"] == "http_error"


def test_input_limits_media_json_and_loopback_boundary(backend, monkeypatch):
    client, store, _ = backend
    assert upload(client, "a" * (10*1024*1024 + 1)).status_code == 413
    assert upload(client, metadata={**METADATA, "source_reference": "a"*65536}).status_code == 413
    assert client.post("/api/v1/experiments", content=b"{}", headers={"content-type": "text/plain"}).status_code == 415
    assert client.post("/api/v1/experiments", content=b"{}", headers={"content-type": "application/json", "content-encoding": "gzip"}).status_code == 415
    for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":1e9999}', '{broken'):
        assert client.post("/api/v1/experiments", content=raw, headers={"content-type":"application/json"}).status_code == 400
    assert client.get("/api/v1/health", headers={"host":"external.example"}).status_code == 400
    assert client.post("/api/v1/datasets", json={}, headers={"origin":"https://external.example"}).status_code == 403
    cors = client.options("/api/v1/experiments", headers={"origin":"https://external.example", "access-control-request-method":"POST"})
    assert "access-control-allow-origin" not in cors.headers
    monkeypatch.setattr(boundary, "MAX_CONFIGURATION_BYTES", 32)
    streamed = client.post("/api/v1/experiments", content=iter([b'{"x":"', b'a'*40, b'"}']), headers={"content-type":"application/json"})
    assert streamed.status_code == 413 and count(store, "experiments") == 0


def test_unexpected_backend_failures_do_not_expose_paths_or_stacktraces(backend, monkeypatch):
    client, store, _ = backend
    data = upload(client).json()
    def broken(*args):
        raise RuntimeError("private C:/secret/backend.py stack")
    monkeypatch.setattr(service, "_compute", broken)
    response = client.post("/api/v1/experiments", json=request(data["dataset_id"]))
    assert response.status_code == 500
    assert "secret" not in response.text and "Traceback" not in response.text and count(store, "experiments") == 0


def test_openapi_documents_models_discriminators_and_all_api_routes(backend):
    client, _, _ = backend
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert len(schema["paths"]) == 6
    request_schema = schema["components"]["schemas"]["ExperimentRequest"]
    assert request_schema["properties"]["configurations"]["items"]["discriminator"]["propertyName"] == "kind"
    assert request_schema["additionalProperties"] is False
    assert client.get("/docs").status_code == 200


def test_reproduction_cannot_silently_override_saved_parameters(backend):
    client, store, _ = backend
    saved = save(client)
    response = client.post("/api/v1/experiments/" + saved["experiment_id"] + "/reproduce", json={"initial_capital":"5000"})
    assert response.status_code == 422 and count(store, "experiments") == 1
    assert client.get("/api/v1/experiments/" + saved["experiment_id"]).json() == saved


def test_codec_preserves_decimal_dates_enums_and_rejects_nonfinite_values():
    from enum import Enum
    class Choice(Enum):
        YES = "yes"
    value = {"money": D("0.123456000"), "date": date(2024,1,1), "enum": Choice.YES, "metric": {"value":None,"reason":"undefined"}}
    assert loads(dumps(value)) == {"money":"0.123456000","date":"2024-01-01","enum":"yes","metric":{"value":None,"reason":"undefined"}}
    for value in (float("inf"), D("NaN")):
        with pytest.raises(ValueError):
            to_wire(value)
