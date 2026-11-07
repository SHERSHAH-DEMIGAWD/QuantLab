"""Atomic daily OHLCV import using only standard-library Python."""

from __future__ import annotations

from collections import Counter
import csv
from datetime import date
from decimal import Decimal
from io import StringIO
from pathlib import Path
import re

from .errors import Diagnostics
from .identity import fingerprints
from .metadata import load_metadata, parse_metadata
from .models import Bar, CalendarGap, Dataset, ImportReport, Metadata, Normalization

MAX_CSV_BYTES = 10 * 1024 * 1024
IMPORTER_VERSION = "1.0.0"
HEADER = ("date", "open", "high", "low", "close", "volume")
PRICE_PATTERN = re.compile(r"[0-9]+(?:\.[0-9]+)?")
DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
VOLUME_PATTERN = re.compile(r"[0-9]+")


def validate_ohlc(open_: Decimal, high: Decimal, low: Decimal, close: Decimal) -> bool:
    """Price positivity/format is checked before this relationship predicate."""
    return low <= min(open_, close) <= max(open_, close) <= high


def _parse_bar(values: list[str], row: int, diagnostics: Diagnostics) -> Bar | None:
    before = diagnostics.error_count
    day = None
    try:
        if not DATE_PATTERN.fullmatch(values[0]):
            raise ValueError
        day = date.fromisoformat(values[0])
    except ValueError:
        diagnostics.add("csv", "invalid_date", "Expected a valid YYYY-MM-DD calendar date.", row=row, field="date")

    prices = []
    for field, value in zip(HEADER[1:5], values[1:5]):
        if not PRICE_PATTERN.fullmatch(value):
            diagnostics.add("csv", "invalid_price", "Expected a positive finite plain decimal.", row=row, field=field)
            continue
        fraction = value.partition(".")[2].rstrip("0")
        price = Decimal(value)
        if price <= 0 or len(fraction) > 6:
            diagnostics.add("csv", "invalid_price", "Price must be positive with at most six meaningful fractional digits.", row=row, field=field)
        else:
            prices.append(price)

    volume = 0
    try:
        if not VOLUME_PATTERN.fullmatch(values[5]):
            raise ValueError
        volume = int(values[5])
    except ValueError:
        diagnostics.add("csv", "invalid_volume", "Expected a nonnegative integer volume within Python's integer-text limit.", row=row, field="volume")

    if len(prices) == 4 and not validate_ohlc(*prices):
        diagnostics.add("csv", "invalid_ohlc", "Require low <= min(open, close) <= max(open, close) <= high.", row=row, field="ohlc")
    if diagnostics.error_count != before:
        return None
    assert day is not None
    return Bar(day, *prices, volume, row)


def _parse_csv(source: bytes, diagnostics: Diagnostics) -> tuple[list[Bar], int]:
    try:
        text = source.decode("utf-8-sig")
    except UnicodeError:
        diagnostics.add("csv", "invalid_encoding", "CSV must be UTF-8, with an optional leading BOM.")
        return [], 0

    reader = csv.reader(StringIO(text, newline=""), strict=True)
    bars: list[Bar] = []
    seen: dict[date, int] = {}
    trimmed = 0
    try:
        raw_header = next(reader, None)
        if raw_header is None:
            diagnostics.add("csv", "empty_input", "CSV is empty.")
            return [], 0
        header = [value.strip() for value in raw_header]
        trimmed += sum(a != b for a, b in zip(raw_header, header))
        duplicates = [name for name, count in Counter(header).items() if count > 1]
        if duplicates:
            diagnostics.add("csv", "duplicate_header", "Duplicate column names after whitespace normalization.", row=1)
        if tuple(header) != HEADER:
            diagnostics.add("csv", "invalid_header", "Expected exactly date,open,high,low,close,volume in this order.", row=1)
            return [], trimmed

        records = 0
        while True:
            row = reader.line_num + 1
            raw = next(reader, None)
            if raw is None:
                break
            records += 1
            if len(raw) != 6:
                diagnostics.add("csv", "invalid_row_width", "Expected exactly six fields; blank records are invalid.", row=row)
                continue
            values = [value.strip() for value in raw]
            trimmed += sum(a != b for a, b in zip(raw, values))
            # Detect repeated dates even when another field in either row is invalid.
            try:
                day = date.fromisoformat(values[0]) if DATE_PATTERN.fullmatch(values[0]) else None
            except ValueError:
                day = None
            if day is not None:
                if day in seen:
                    diagnostics.add("csv", "duplicate_date", f"Date already appeared at source row {seen[day]}.", row=row, field="date")
                else:
                    seen[day] = row
            bar = _parse_bar(values, row, diagnostics)
            if bar is not None:
                bars.append(bar)
        if records == 0:
            diagnostics.add("csv", "empty_input", "CSV contains a header but no data records.")
    except csv.Error as exc:
        diagnostics.add("csv", "malformed_csv", str(exc), row=reader.line_num)
    return bars, trimmed


def _warnings(metadata: Metadata, zero_volume: int, row_count: int) -> tuple[str, ...]:
    warnings = [
        "Session coverage is unverified; calendar gaps do not identify missing trading sessions.",
        "Source, usage, adjustment and corporate-action declarations are not independently verified.",
        "Import acceptance does not establish simulation eligibility; no split or dividend processing is performed.",
    ]
    if metadata.source_kind == "synthetic":
        warnings.append("Synthetic observations are invented, not historical market observations.")
    if metadata.adjustment_basis != "unadjusted":
        warnings.append(f"OHLC adjustment basis is {metadata.adjustment_basis}; preserve this limitation in later use.")
    if metadata.ohlc_basis_consistent == "unknown":
        warnings.append("OHLC basis consistency is unknown; numerical validation cannot verify adjustment consistency.")
    if metadata.volume_basis == "unknown":
        warnings.append("Volume adjustment basis is unknown.")
    if metadata.split_status == "unknown" or metadata.split_evidence == "unknown":
        warnings.append("Split status or supporting evidence is unknown; absence of splits is not established.")
    if zero_volume:
        warnings.append(f"{zero_volume} row(s) have zero volume; import retains these observations.")
    if row_count == 1:
        warnings.append("Single-row import has no subsequent observed session.")
    return tuple(warnings)


def load_dataset(csv_path: str | Path, metadata_path: str | Path) -> Dataset:
    """Load local files atomically; raise DataValidationError for invalid input."""
    diagnostics = Diagnostics()
    metadata = load_metadata(Path(metadata_path), diagnostics)
    try:
        with Path(csv_path).open("rb") as handle:
            source = handle.read(MAX_CSV_BYTES + 1)
    except OSError as exc:
        diagnostics.add("csv", "csv_read_error", str(exc))
        diagnostics.raise_if_invalid()
        raise AssertionError("unreachable")
    return _build_dataset(source, metadata, diagnostics)


def load_dataset_bytes(source: bytes, metadata_json: bytes) -> Dataset:
    """Import original bytes without temporary files or alternate validation rules."""
    if not isinstance(source, bytes) or not isinstance(metadata_json, bytes):
        raise TypeError("CSV and metadata must be bytes.")
    diagnostics = Diagnostics()
    metadata = parse_metadata(metadata_json, diagnostics)
    return _build_dataset(source, metadata, diagnostics)


def _build_dataset(source: bytes, metadata: Metadata | None, diagnostics: Diagnostics) -> Dataset:
    if len(source) > MAX_CSV_BYTES:
        diagnostics.add("csv", "input_too_large", f"CSV exceeds the {MAX_CSV_BYTES}-byte (10 MiB) maximum.")
        diagnostics.raise_if_invalid()
    bars, trimmed = _parse_csv(source, diagnostics)
    diagnostics.raise_if_invalid()
    assert metadata is not None and bars

    ordered = tuple(sorted(bars, key=lambda bar: bar.date))
    gaps = tuple(
        CalendarGap(previous.date, following.date, (following.date - previous.date).days - 1)
        for previous, following in zip(ordered, ordered[1:])
        if (following.date - previous.date).days > 1
    )
    source_hash, metadata_hash, dataset_id = fingerprints(source, metadata)
    zero_volume = sum(bar.volume == 0 for bar in ordered)
    report = ImportReport(
        importer_version=IMPORTER_VERSION, row_count=len(ordered),
        first_date=ordered[0].date, last_date=ordered[-1].date,
        source_byte_count=len(source), source_sha256=source_hash,
        metadata_sha256=metadata_hash, dataset_id=dataset_id,
        normalization=Normalization(source.startswith(b"\xef\xbb\xbf"), trimmed, bars != list(ordered)),
        calendar_gaps=gaps, zero_volume_rows=zero_volume,
        warnings=_warnings(metadata, zero_volume, len(ordered)),
    )
    return Dataset(ordered, metadata, report)
