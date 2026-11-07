"""OpenAPI response envelopes; financial payload fields retain the domain contract."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class DatasetRecord(BaseModel):
    dataset_id: str
    metadata: dict[str, Any]
    validation: dict[str, Any]
    created_at: str


class ImportResponse(DatasetRecord):
    duplicate: bool


class ExperimentRecord(BaseModel):
    experiment_id: str
    dataset_id: str
    mode: Literal["backtest", "grid", "train_test"]
    request: dict[str, Any]
    result: dict[str, Any] = Field(description="Complete Phase 6 result; Decimal strings, ISO dates, null metrics plus reasons. See API_CONTRACT.md.")
    implementation: dict[str, Any]
    result_sha256: str
    created_at: str


class Listing(BaseModel):
    items: list[dict[str, Any]]
    limit: int
    offset: int


class ReproductionResponse(BaseModel):
    experiment_id: str
    status: Literal["matched", "mismatch", "implementation_changed"]
    economic_match: bool
    implementation_match: bool
    saved_economic_sha256: str
    current_economic_sha256: str
    difference_paths: list[str]
    difference_path_limit: int
    current_implementation: dict[str, Any]
    limitations: list[str]


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
