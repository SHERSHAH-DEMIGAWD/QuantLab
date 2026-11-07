"""Exercise shipped offline assets through the unchanged API and financial core."""

import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from quantlab.api import create_app
from quantlab.application import service


EXAMPLES = Path(__file__).resolve().parents[2] / "frontend" / "public" / "examples"
CSV = (EXAMPLES / "nine_sessions.csv").read_bytes()
METADATA = json.loads((EXAMPLES / "nine_sessions.metadata.json").read_bytes())
TEMPLATE = json.loads((EXAMPLES / "local_file.metadata.template.json").read_bytes())


def import_source(client, metadata=METADATA, text=None):
    return client.post("/api/v1/datasets", json={
        "csv_text": CSV.decode("utf-8") if text is None else text, "metadata": metadata,
    })


def run(client, dataset_id, acknowledge=True):
    return client.post("/api/v1/experiments", json={
        "dataset_id": dataset_id, "initial_capital": "1000.00",
        "configurations": [{"kind": "buy_and_hold"}], "include_benchmark": False,
        "settings": {"acknowledge_unverified_coverage": acknowledge},
    })


def test_public_synthetic_inputs_identity_retention_restart_and_fresh_reproduction(tmp_path, monkeypatch):
    database = tmp_path / "offline.sqlite3"
    app = create_app(database)
    with TestClient(app, base_url="http://localhost") as client:
        imported = import_source(client)
        assert imported.status_code == 201
        dataset = imported.json()
        repeated = import_source(client)
        assert repeated.status_code == 200
        assert repeated.json()["dataset_id"] == dataset["dataset_id"]
        assert repeated.json()["created_at"] == dataset["created_at"]
        saved = run(client, dataset["dataset_id"])
        assert saved.status_code == 201, saved.text
        record = saved.json()
        result = record["result"]["runs"][0]
        simulation = result["performance"]["simulation"]
        assert simulation["final_equity"] == "800.00"
        assert simulation["valuations"][-1]["shares"] == 100
        assert result["performance"]["equity"]["cumulative_return"]["value"] == -0.2
        assert {f["status"] for f in result["audit"]["findings"]} >= {"PASS", "WARNING", "NOT_ASSESSED"}
    with app.state.store.connection() as connection:
        assert connection.execute("SELECT source_csv FROM datasets").fetchone()[0] == CSV
    calls = []
    compute = service._compute

    def observed_compute(*args):
        calls.append(True)
        return compute(*args)

    monkeypatch.setattr(service, "_compute", observed_compute)
    with TestClient(create_app(database), base_url="http://localhost") as restarted:
        assert restarted.get(f'/api/v1/experiments/{record["experiment_id"]}').json() == record
        assert calls == []  # Retrieval did not execute research.
        reproduction = restarted.post(f'/api/v1/experiments/{record["experiment_id"]}/reproduce')
        assert reproduction.status_code == 200
        assert calls == [True]
        assert reproduction.json()["economic_match"] is True
        assert reproduction.json()["implementation_match"] is True
        assert len(restarted.get("/api/v1/experiments").json()["items"]) == 1


def test_downloadable_local_template_retains_unknowns_and_cannot_bypass_d04(tmp_path):
    assert TEMPLATE["source_kind"] == "local_file"
    for field in ("adjustment_basis", "ohlc_basis_consistent", "volume_basis", "split_status", "split_evidence"):
        assert TEMPLATE[field] == "unknown"
    with TestClient(create_app(tmp_path / "template.sqlite3"), base_url="http://localhost") as client:
        imported = import_source(client, TEMPLATE)
        assert imported.status_code == 201
        dataset = imported.json()
        assert dataset["metadata"]["split_status"] == "unknown"
        rejected = run(client, dataset["dataset_id"], acknowledge=True)
        assert rejected.status_code == 422
        assert "D04 eligibility" in rejected.json()["error"]["message"]
        assert client.get("/api/v1/experiments").json()["items"] == []


@pytest.mark.parametrize("change", [
    {"adjustment_basis": "split_adjusted"},
    {"adjustment_basis": "total_return_adjusted"},
    {"adjustment_basis": "unknown"},
    {"volume_basis": "split_adjusted"},
    {"volume_basis": "unknown"},
    {"ohlc_basis_consistent": "unknown"},
    {"split_status": "present"},
    {"split_status": "unknown"},
    {"split_evidence": "unknown"},
])
def test_importable_unsupported_declarations_remain_blocked(tmp_path, change):
    with TestClient(create_app(tmp_path / "blocked.sqlite3"), base_url="http://localhost") as client:
        imported = import_source(client, {**METADATA, **change})
        assert imported.status_code == 201
        rejected = run(client, imported.json()["dataset_id"])
        assert rejected.status_code == 422
        assert "D04 eligibility" in rejected.json()["error"]["message"]
        assert client.get("/api/v1/experiments").json()["items"] == []


def test_local_file_coverage_ack_is_required_even_for_declared_complete_invented_input(tmp_path):
    # Invented bars exercise the local-file transport policy, not real split evidence.
    metadata = {**METADATA, "source_kind": "local_file", "session_coverage": "declared_complete"}
    with TestClient(create_app(tmp_path / "coverage.sqlite3"), base_url="http://localhost") as client:
        imported = import_source(client, metadata)
        assert imported.status_code == 201
        dataset = imported.json()
        assert dataset["validation"]["coverage_assessment"] == "unverified"
        rejected = run(client, dataset["dataset_id"], acknowledge=False)
        assert rejected.status_code == 422
        assert "explicit acknowledgment" in rejected.json()["error"]["message"]
        assert run(client, dataset["dataset_id"], acknowledge=True).status_code == 201


@pytest.mark.parametrize("metadata,text,field", [
    ({**METADATA, "ohlc_basis_consistent": False}, None, "ohlc_basis_consistent"),
    (METADATA, "date,open,high,low,close,volume\n2024-01-02,10,5,9,10,100\n", "ohlc"),
    (METADATA, "date,open,high,low,close,volume\n2024-01-02,NaN,10,10,10,100\n", "open"),
    (METADATA, "date,open,high,low,close,volume\n2024-01-02,10,10,10,10,1.5\n", "volume"),
])
def test_invalid_offline_input_retains_nothing(tmp_path, metadata, text, field):
    with TestClient(create_app(tmp_path / "invalid.sqlite3"), base_url="http://localhost") as client:
        response = import_source(client, metadata, text)
        assert response.status_code == 422
        issues = response.json()["error"]["details"]["issues"]
        assert any(issue["field"] == field for issue in issues)
        assert client.get("/api/v1/datasets").json()["items"] == []
