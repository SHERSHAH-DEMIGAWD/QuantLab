"""Thin synchronous routes over the application coordinator and SQLite store."""

from dataclasses import asdict
from decimal import DecimalException
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Path as ApiPath, Query
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from quantlab.application import service
from quantlab.application.requests import DatasetImport, ExperimentRequest
from quantlab.data import DataValidationError
from quantlab.persistence import NotFound, RecordError, Store, StorageError

from .boundary import LocalBoundary, error_response
from .models import DatasetRecord, ErrorResponse, ExperimentRecord, ImportResponse, Listing, ReproductionResponse

DatasetPath = Annotated[str, ApiPath(pattern=r"^[0-9a-f]{64}$")]
ExperimentPath = Annotated[str, ApiPath(pattern=r"^[0-9a-f]{32}$")]
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0, le=1_000_000)]


def create_app(database_path: str | Path = "data/quantlab.sqlite3") -> FastAPI:
    store = Store(database_path)
    store.initialize()
    app = FastAPI(title="QuantLab local research API", version="1.0.0",
                  description="Single-user localhost backend. Existing financial contracts and audit limits apply.",
                  responses={code: {"model": ErrorResponse} for code in (400, 404, 409, 413, 415, 422, 503)})
    app.state.store = store
    app.add_middleware(LocalBoundary)

    @app.exception_handler(RequestValidationError)
    async def request_error(request, exc):
        details = [{"location": list(item["loc"]), "code": item["type"], "message": item["msg"]} for item in exc.errors()[:100]]
        return error_response(422, "invalid_request", "Request validation failed.", details)

    @app.exception_handler(DataValidationError)
    async def data_error(request, exc):
        return error_response(422, "invalid_dataset", "Dataset validation failed.",
                              {"issues": [asdict(issue) for issue in exc.issues], "error_count": exc.error_count, "truncated": exc.truncated})

    @app.exception_handler(NotFound)
    async def missing(request, exc):
        return error_response(404, "not_found", str(exc))

    @app.exception_handler(RecordError)
    async def retained_error(request, exc):
        return error_response(409, "retained_evidence_unavailable", str(exc))

    @app.exception_handler(StorageError)
    async def storage_error(request, exc):
        return error_response(503, "storage_unavailable", "Database operation unavailable; no successful write is reported.")

    @app.exception_handler(service.InputTooLarge)
    async def large_input(request, exc):
        return error_response(413, "input_too_large", str(exc))

    @app.exception_handler(ValueError)
    async def domain_error(request, exc):
        message = str(exc)
        if "Cannot fingerprint local source" in message:
            return error_response(503, "source_unavailable", "Local implementation fingerprint is unavailable.")
        return error_response(422, "computation_rejected", message)

    @app.exception_handler(DecimalException)
    async def numeric_error(request, exc):
        return error_response(422, "numeric_range", "Request exceeds supported financial arithmetic.")

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return error_response(exc.status_code, "http_error", "The requested route or method is unavailable.")

    @app.exception_handler(Exception)
    async def unexpected_error(request, exc):
        return error_response(500, "internal_error", "Unexpected backend failure; no completed experiment is reported.")

    @app.get("/api/v1/health", tags=["service"])
    def health():
        return {"status": "ok", "api_version": "1.0.0", "schema_version": store.health()}

    @app.post("/api/v1/datasets", response_model=ImportResponse, status_code=201, tags=["datasets"],
              responses={200: {"model": ImportResponse, "description": "Identical retained dataset; original timestamp preserved."}})
    def import_dataset(body: DatasetImport):
        record, created = service.import_dataset(store, body.csv_text, body.metadata)
        return JSONResponse({**record, "duplicate": not created}, status_code=201 if created else 200)

    @app.get("/api/v1/datasets", response_model=Listing, tags=["datasets"])
    def datasets(limit: Limit = 50, offset: Offset = 0):
        return {"items": store.list_datasets(limit, offset), "limit": limit, "offset": offset}

    @app.get("/api/v1/datasets/{dataset_id}", response_model=DatasetRecord, tags=["datasets"])
    def dataset(dataset_id: DatasetPath):
        return store.get_dataset(dataset_id)

    @app.post("/api/v1/experiments", response_model=ExperimentRecord, status_code=201, tags=["experiments"])
    def execute_experiment(body: ExperimentRequest):
        return service.execute(store, body)

    @app.get("/api/v1/experiments", response_model=Listing, tags=["experiments"])
    def experiments(limit: Limit = 50, offset: Offset = 0,
                    dataset_id: Annotated[str | None, Query(pattern=r"^[0-9a-f]{64}$")] = None):
        return {"items": store.list_experiments(limit, offset, dataset_id), "limit": limit, "offset": offset}

    @app.get("/api/v1/experiments/{experiment_id}", response_model=ExperimentRecord, tags=["experiments"])
    def experiment(experiment_id: ExperimentPath):
        return store.get_experiment(experiment_id)

    @app.post("/api/v1/experiments/{experiment_id}/reproduce", response_model=ReproductionResponse, tags=["experiments"])
    def reproduce(experiment_id: ExperimentPath):
        return service.reproduce(store, experiment_id)

    return app
