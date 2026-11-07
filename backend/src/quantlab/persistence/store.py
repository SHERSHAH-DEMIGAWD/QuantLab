"""Two immutable record tables, explicit transactions and retained-input checks."""

from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from uuid import uuid4

from quantlab.data import DataValidationError, load_dataset_bytes

from .codec import digest, dumps, loads, to_wire

SCHEMA_VERSION = 1
SCHEMA = (
    """CREATE TABLE datasets (
        dataset_id TEXT PRIMARY KEY NOT NULL, source_csv BLOB NOT NULL,
        metadata_json TEXT NOT NULL, source_sha256 TEXT NOT NULL, metadata_sha256 TEXT NOT NULL,
        first_date TEXT NOT NULL, last_date TEXT NOT NULL, row_count INTEGER NOT NULL CHECK(row_count > 0),
        report_json TEXT NOT NULL, created_at TEXT NOT NULL)""",
    """CREATE TABLE experiments (
        experiment_id TEXT PRIMARY KEY NOT NULL,
        dataset_id TEXT NOT NULL REFERENCES datasets(dataset_id) ON DELETE RESTRICT,
        mode TEXT NOT NULL CHECK(mode IN ('backtest','grid','train_test')),
        request_json TEXT NOT NULL, request_sha256 TEXT NOT NULL,
        result_json TEXT NOT NULL, result_sha256 TEXT NOT NULL,
        implementation_json TEXT NOT NULL, created_at TEXT NOT NULL)""",
    "CREATE INDEX experiments_dataset_created ON experiments(dataset_id, created_at, experiment_id)",
    "CREATE INDEX experiments_created ON experiments(created_at, experiment_id)",
)
DATASET_COLUMNS = {"dataset_id", "source_csv", "metadata_json", "source_sha256", "metadata_sha256", "first_date", "last_date", "row_count", "report_json", "created_at"}
EXPERIMENT_COLUMNS = {"experiment_id", "dataset_id", "mode", "request_json", "request_sha256", "result_json", "result_sha256", "implementation_json", "created_at"}


class StorageError(RuntimeError):
    """Database operation unavailable; internal paths/SQL are not public errors."""


class SchemaError(StorageError):
    """Unsupported or malformed database schema."""


class NotFound(LookupError):
    """Unknown resource identifier."""


class RecordError(ValueError):
    """Retained evidence is inconsistent, corrupt, or unsupported."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _object(text: str) -> dict:
    try:
        value = loads(text)
        if not isinstance(value, dict):
            raise ValueError
        return value
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise RecordError("Stored JSON record is invalid.") from exc


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    @contextmanager
    def connection(self, *, validate_version: bool = True):
        connection = None
        try:
            connection = sqlite3.connect(self.path, timeout=5, isolation_level=None)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
            if validate_version and connection.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
                raise SchemaError("Unsupported database schema.")
            yield connection
        except sqlite3.Error as exc:
            raise StorageError("Database operation unavailable.") from exc
        finally:
            if connection is not None:
                connection.close()

    @contextmanager
    def transaction(self, *, validate_version: bool = True):
        with self.connection(validate_version=validate_version) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
                connection.commit()
            except BaseException:
                connection.rollback()
                raise

    def initialize(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError("Database directory unavailable.") from exc
        with self.transaction(validate_version=False) as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            if version == 0 and not tables:
                for statement in SCHEMA:
                    connection.execute(statement)
                connection.execute("PRAGMA user_version=1")
            elif version != SCHEMA_VERSION or tables != {"datasets", "experiments"}:
                raise SchemaError("Unsupported database schema; no migration was applied.")
            for table, expected in (("datasets", DATASET_COLUMNS), ("experiments", EXPERIMENT_COLUMNS)):
                if {row[1] for row in connection.execute(f"PRAGMA table_info({table})")} != expected:
                    raise SchemaError("Database schema does not match version 1.")
            foreign_keys = connection.execute("PRAGMA foreign_key_list(experiments)").fetchall()
            if not any(row[2:5] == ("datasets", "dataset_id", "dataset_id") for row in foreign_keys):
                raise SchemaError("Required dataset relationship is missing.")

    def health(self) -> int:
        with self.connection() as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version != SCHEMA_VERSION:
                raise SchemaError("Unsupported database schema.")
            return version

    def save_dataset(self, source: bytes, dataset) -> tuple[dict, bool]:
        report = dataset.report
        metadata = dumps(asdict(dataset.metadata))
        with self.transaction() as connection:
            cursor = connection.execute(
                """INSERT INTO datasets VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(dataset_id) DO NOTHING""",
                (report.dataset_id, source, metadata, report.source_sha256, report.metadata_sha256,
                 report.first_date.isoformat(), report.last_date.isoformat(), report.row_count, dumps(report), _now()),
            )
            created = cursor.rowcount == 1
            row = connection.execute("SELECT source_csv,metadata_json FROM datasets WHERE dataset_id=?", (report.dataset_id,)).fetchone()
            if bytes(row["source_csv"]) != source or row["metadata_json"] != metadata:
                raise RecordError("Dataset identity conflict; existing evidence was not overwritten.")
        return self.get_dataset(report.dataset_id), created

    def get_dataset(self, dataset_id: str) -> dict:
        with self.connection() as connection:
            row = connection.execute("SELECT dataset_id,metadata_json,report_json,created_at FROM datasets WHERE dataset_id=?", (dataset_id,)).fetchone()
        if row is None:
            raise NotFound("Dataset not found.")
        return {"dataset_id": row["dataset_id"], "metadata": _object(row["metadata_json"]),
                "validation": _object(row["report_json"]), "created_at": row["created_at"]}

    def reconstruct_dataset(self, dataset_id: str):
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM datasets WHERE dataset_id=?", (dataset_id,)).fetchone()
        if row is None:
            raise NotFound("Dataset not found.")
        if not isinstance(row["source_csv"], bytes) or not isinstance(row["metadata_json"], str):
            raise RecordError("Retained dataset byte/text types are invalid.")
        try:
            dataset = load_dataset_bytes(bytes(row["source_csv"]), row["metadata_json"].encode("utf-8"))
        except (DataValidationError, TypeError, UnicodeError, ValueError) as exc:
            raise RecordError("Retained dataset inputs cannot be revalidated.") from exc
        report = dataset.report
        expected = (dataset_id, row["source_sha256"], row["metadata_sha256"], row["first_date"], row["last_date"], row["row_count"])
        observed = (report.dataset_id, report.source_sha256, report.metadata_sha256, report.first_date.isoformat(), report.last_date.isoformat(), report.row_count)
        if observed != expected:
            raise RecordError("Retained dataset identity/range/count mismatch.")
        return dataset

    def list_datasets(self, limit: int, offset: int) -> list[dict]:
        with self.connection() as connection:
            rows = connection.execute("SELECT dataset_id,first_date,last_date,row_count,created_at FROM datasets ORDER BY created_at,dataset_id LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        return [dict(row) for row in rows]

    def save_experiment(self, request: dict, result, implementation: dict) -> dict:
        wire_result = to_wire(result)
        request_json, result_json = dumps(request), dumps(wire_result)
        identifier, created_at = uuid4().hex, _now()
        with self.transaction() as connection:
            connection.execute("INSERT INTO experiments VALUES (?,?,?,?,?,?,?,?,?)", (
                identifier, request["dataset_id"], request["mode"], request_json, digest(request_json),
                result_json, digest(result_json), dumps(implementation), created_at,
            ))
        return {"experiment_id": identifier, "dataset_id": request["dataset_id"], "mode": request["mode"],
                "request": request, "result": wire_result, "implementation": implementation,
                "result_sha256": digest(result_json), "created_at": created_at}

    def get_experiment(self, experiment_id: str) -> dict:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM experiments WHERE experiment_id=?", (experiment_id,)).fetchone()
        if row is None:
            raise NotFound("Experiment not found.")
        if not all(isinstance(row[name], str) for name in ("request_json", "result_json", "request_sha256", "result_sha256", "implementation_json")):
            raise RecordError("Saved experiment text fields are invalid.")
        if digest(row["request_json"]) != row["request_sha256"] or digest(row["result_json"]) != row["result_sha256"]:
            raise RecordError("Saved request/result checksum mismatch.")
        request = _object(row["request_json"])
        if request.get("dataset_id") != row["dataset_id"] or request.get("mode") != row["mode"]:
            raise RecordError("Saved request identity mismatch.")
        return {"experiment_id": row["experiment_id"], "dataset_id": row["dataset_id"], "mode": row["mode"],
                "request": request, "result": _object(row["result_json"]),
                "implementation": _object(row["implementation_json"]), "result_sha256": row["result_sha256"],
                "created_at": row["created_at"]}

    def list_experiments(self, limit: int, offset: int, dataset_id: str | None = None) -> list[dict]:
        with self.connection() as connection:
            columns = "SELECT experiment_id,dataset_id,mode,created_at FROM experiments"
            if dataset_id is None:
                rows = connection.execute(columns + " ORDER BY created_at,experiment_id LIMIT ? OFFSET ?", (limit, offset)).fetchall()
            else:
                rows = connection.execute(columns + " WHERE dataset_id=? ORDER BY created_at,experiment_id LIMIT ? OFFSET ?", (dataset_id, limit, offset)).fetchall()
        return [dict(row) for row in rows]
