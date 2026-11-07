"""Immutable values returned only after an entire import passes validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True)
class Bar:
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    source_row: int


@dataclass(frozen=True)
class Metadata:
    contract_version: int
    symbol: str
    exchange: str
    currency: str
    frequency: str
    session_timezone: str
    source_kind: str
    source_name: str
    adjustment_basis: str
    source_reference: str = "unknown"
    usage_note: str = "unknown"
    ohlc_basis_consistent: bool | Literal["unknown"] = "unknown"
    volume_basis: str = "unknown"
    split_status: str = "unknown"
    split_evidence: str = "unknown"
    session_coverage: str = "unknown"


@dataclass(frozen=True)
class Normalization:
    csv_bom_removed: bool
    whitespace_fields_trimmed: int
    rows_reordered: bool


@dataclass(frozen=True)
class CalendarGap:
    previous_date: date
    next_date: date
    unobserved_calendar_days: int


@dataclass(frozen=True)
class ImportReport:
    importer_version: str
    row_count: int
    first_date: date
    last_date: date
    source_byte_count: int
    source_sha256: str
    metadata_sha256: str
    dataset_id: str
    normalization: Normalization
    calendar_gaps: tuple[CalendarGap, ...]
    zero_volume_rows: int
    warnings: tuple[str, ...]
    coverage_assessment: Literal["unverified"] = "unverified"


@dataclass(frozen=True)
class Dataset:
    bars: tuple[Bar, ...]
    metadata: Metadata
    report: ImportReport
