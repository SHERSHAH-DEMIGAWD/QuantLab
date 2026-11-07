"""Revalidate retained inputs, delegate research, then save a completed result."""

from decimal import DecimalException
from importlib.metadata import version
import sqlite3

from pydantic import ValidationError

from quantlab.audit.auditor import AUDIT_VERSION
from quantlab.data import MAX_CSV_BYTES, load_dataset_bytes
from quantlab.data.loader import IMPORTER_VERSION
from quantlab.execution.engine import ENGINE_VERSION
from quantlab.experiments import EXPERIMENT_VERSION, run_experiment, run_train_test
from quantlab.persistence import NotFound, RecordError, Store
from quantlab.persistence.codec import difference_paths, digest, dumps, economic_projection, to_wire

from .requests import ExperimentRequest, MAX_METADATA_BYTES


class InputTooLarge(ValueError):
    pass


def import_dataset(store: Store, csv_text: str, metadata: dict) -> tuple[dict, bool]:
    try:
        source, metadata_bytes = csv_text.encode("utf-8"), dumps(metadata).encode("utf-8")
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ValueError("Import requires valid UTF-8 text and standard JSON metadata.") from exc
    if len(source) > MAX_CSV_BYTES or len(metadata_bytes) > MAX_METADATA_BYTES:
        raise InputTooLarge("CSV exceeds 10 MiB or metadata exceeds 64 KiB.")
    dataset = load_dataset_bytes(source, metadata_bytes)
    return store.save_dataset(source, dataset)


def _compute(dataset, request: ExperimentRequest):
    runner = run_train_test if request.mode == "train_test" else run_experiment
    return runner(dataset, **request.arguments())


def _implementation(result) -> dict:
    snapshot = result.training.reproducibility if hasattr(result, "training") else result.reproducibility
    return {
        "payload_version": 1, "request_version": 1, "engine_version": ENGINE_VERSION,
        "importer_version": IMPORTER_VERSION, "audit_version": AUDIT_VERSION,
        "experiment_version": EXPERIMENT_VERSION, "source": to_wire(snapshot),
        "sqlite_version": sqlite3.sqlite_version,
        "dependencies": {name: version(name) for name in ("fastapi", "pydantic", "starlette", "uvicorn")},
    }


def execute(store: Store, request: ExperimentRequest) -> dict:
    dataset = store.reconstruct_dataset(request.dataset_id)
    result = _compute(dataset, request)
    return store.save_experiment(request.model_dump(mode="json"), result, _implementation(result))


def reproduce(store: Store, experiment_id: str) -> dict:
    saved = store.get_experiment(experiment_id)
    if saved["implementation"].get("payload_version") != 1:
        raise RecordError("Saved result payload version is unsupported.")
    try:
        request = ExperimentRequest.model_validate(saved["request"])
    except ValidationError as exc:
        raise RecordError("Saved request cannot be revalidated with the current contract.") from exc
    try:
        dataset = store.reconstruct_dataset(saved["dataset_id"])
    except NotFound as exc:
        raise RecordError("Retained dataset is unavailable for this saved experiment.") from exc
    try:
        current = _compute(dataset, request)  # Always executes; never returns the cached result.
    except (ValueError, DecimalException) as exc:
        raise RecordError("Saved computation is unavailable under the current implementation.") from exc
    implementation = _implementation(current)
    implementation_match = implementation == saved["implementation"]
    left, right = economic_projection(saved["result"]), economic_projection(to_wire(current))
    left_hash, right_hash = digest(dumps(left)), digest(dumps(right))
    economic_match = left_hash == right_hash
    return {
        "experiment_id": experiment_id,
        "status": "implementation_changed" if not implementation_match else "matched" if economic_match else "mismatch",
        "economic_match": economic_match, "implementation_match": implementation_match,
        "saved_economic_sha256": left_hash, "current_economic_sha256": right_hash,
        "difference_paths": list(difference_paths(left, right)), "difference_path_limit": 20,
        "current_implementation": implementation,
        "limitations": [
            "Re-executed current code using revalidated retained CSV/effective metadata and saved request; no source archive is restored.",
            "Economic comparison excludes reproducibility, experiment_version, engine_version, audit, assumptions and warnings recursively; all remain retained in saved results.",
            "UUID/creation timestamps are outside result payloads. Exact serialized economic outputs, including finite statistics and Decimal strings, are compared without tolerances.",
            "Matching outputs do not establish historical-market truth, bias absence, significance or future profitability.",
        ] + ([] if implementation_match else ["Source/version/runtime identity differs; this is not exact reproduction under the original implementation."]),
    }
