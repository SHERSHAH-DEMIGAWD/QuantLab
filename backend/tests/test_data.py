"""Deterministic, offline acceptance and independent identity references."""

from dataclasses import FrozenInstanceError
from datetime import date, timedelta
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path

import pytest

from quantlab.data import (
    MAX_CSV_BYTES, MAX_DIAGNOSTICS, DataValidationError, load_dataset,
)
from quantlab.data.loader import validate_ohlc

FIXTURES = Path(__file__).parent / "fixtures"
HEADER = "date,open,high,low,close,volume\n"
ROW = "2024-01-05,10.10,12.00,9.50,11.25,100\n"
REQUIRED_METADATA = {
    "contract_version": 1, "symbol": "SYNTH", "exchange": "SYNTHETIC_US",
    "currency": "USD", "frequency": "1d", "session_timezone": "America/New_York",
    "source_kind": "synthetic", "source_name": "Invented fixture",
    "adjustment_basis": "unadjusted",
}
OPTIONAL_FIELDS = (
    "source_reference", "usage_note", "ohlc_basis_consistent", "volume_basis",
    "split_status", "split_evidence", "session_coverage",
)


@pytest.fixture
def files(tmp_path):
    def write(csv=HEADER + ROW, metadata=None):
        csv_path = tmp_path / "input.csv"
        metadata_path = tmp_path / "input.metadata.json"
        csv_path.write_bytes(csv.encode("utf-8") if isinstance(csv, str) else csv)
        metadata_path.write_text(
            json.dumps(REQUIRED_METADATA if metadata is None else metadata),
            encoding="utf-8",
        )
        return csv_path, metadata_path
    return write


def reject(paths, code, *, field=None, row=None):
    with pytest.raises(DataValidationError) as caught:
        load_dataset(*paths)
    error = caught.value
    matches = [issue for issue in error.issues if issue.code == code]
    assert matches, error.issues
    if field is not None:
        assert any(issue.field == field for issue in matches)
    if row is not None:
        assert any(issue.row == row for issue in matches)
    assert not hasattr(error, "dataset")
    return error


def test_synthetic_example_and_handwritten_records():
    result = load_dataset(
        FIXTURES / "synthetic_daily.csv",
        FIXTURES / "synthetic_daily.metadata.json",
    )
    assert [bar.date for bar in result.bars] == [date(2024, 1, d) for d in (5, 8, 9)]
    first = result.bars[0]
    assert (first.open, first.high, first.low, first.close, first.volume) == (
        Decimal("100.10"), Decimal("103.00"), Decimal("99.50"), Decimal("102.25"), 1000,
    )
    assert first.source_row == 2
    assert result.report.row_count == 3
    assert result.report.first_date == date(2024, 1, 5)
    assert result.report.last_date == date(2024, 1, 9)
    assert result.report.zero_volume_rows == 1
    assert result.metadata.source_kind == "synthetic"
    assert any("invented" in warning for warning in result.report.warnings)
    assert not result.report.normalization.rows_reordered
    with pytest.raises(FrozenInstanceError):
        first.volume = 5


def test_unordered_rows_preserve_source_locations(files):
    later = "2024-01-08,20,20,20,20,200\n"
    result = load_dataset(*files(HEADER + later + ROW))
    assert [bar.date for bar in result.bars] == [date(2024, 1, 5), date(2024, 1, 8)]
    assert [bar.source_row for bar in result.bars] == [3, 2]
    assert result.report.normalization.rows_reordered


def test_duplicate_dates_even_identical_and_invalid_rows(files):
    error = reject(files(HEADER + ROW + ROW), "duplicate_date", row=3, field="date")
    assert "row 2" in error.issues[0].message
    reject(files(HEADER + ROW.replace("10.10", "bad") + ROW), "duplicate_date", row=3)


@pytest.mark.parametrize("header,code", [
    ("date,open,high,low,close,close\n", "duplicate_header"),
    ("date,open,high,low,close, close \n", "duplicate_header"),
    ("date,open,high,low,close\n", "invalid_header"),
    ("date,open,high,low,close,volume,extra\n", "invalid_header"),
    ("date,high,open,low,close,volume\n", "invalid_header"),
    ("Date,open,high,low,close,volume\n", "invalid_header"),
])
def test_exact_headers(files, header, code):
    reject(files(header + ROW), code, row=1)


@pytest.mark.parametrize("bad_date", [
    "2024-02-30", "2023-02-29", "2024-13-01", "2024-00-01", "0000-01-01",
    "2024-1-05", "20240105", "2024-01-05T00:00:00", "", "２０２４-01-05",
])
def test_invalid_dates(files, bad_date):
    reject(files(HEADER + ROW.replace("2024-01-05", bad_date)), "invalid_date", field="date", row=2)


def test_leap_date(files):
    assert load_dataset(*files(HEADER + ROW.replace("2024-01-05", "2024-02-29"))).bars[0].date == date(2024, 2, 29)


@pytest.mark.parametrize("price", [
    "", "abc", "0", "-1", "NaN", "Infinity", "1e1", "+10", ".10", "10.",
    "1_0", "10.0000001", "１０", "1 0",
])
@pytest.mark.parametrize("field_index", [1, 2, 3, 4])
def test_missing_and_malformed_prices(files, price, field_index):
    values = ROW.rstrip("\n").split(",")
    values[field_index] = price
    reject(files(HEADER + ",".join(values)), "invalid_price", row=2, field=HEADER.strip().split(",")[field_index])


@pytest.mark.parametrize("prices", [
    "10,11,10.50,10.75", "10,10.50,9,11", "10,8,9,10", "10,11,12,10",
])
def test_inconsistent_ohlc(files, prices):
    reject(files(HEADER + f"2024-01-05,{prices},1\n"), "invalid_ohlc", field="ohlc")


def test_equal_and_six_meaningful_decimal_prices(files):
    value = "0.1234560000"
    result = load_dataset(*files(HEADER + f"2024-01-05,{value},{value},{value},{value},0\n"))
    assert result.bars[0].open == Decimal("0.123456")
    assert result.report.zero_volume_rows == 1
    assert any("zero volume" in warning for warning in result.report.warnings)


def test_decimal_parsing_does_not_round_with_ambient_context(files):
    with localcontext() as context:
        context.prec = 2
        result = load_dataset(*files())
    assert result.bars[0].close == Decimal("11.25")


@pytest.mark.parametrize("volume", ["-1", "1.5", "1e3", "", "NaN", "+1", "１"])
def test_invalid_volume(files, volume):
    reject(files(HEADER + ROW.replace(",100\n", f",{volume}\n")), "invalid_volume", field="volume")


@pytest.mark.parametrize("csv,code", [
    ("", "empty_input"), (HEADER, "empty_input"),
    (HEADER + "\n", "invalid_row_width"),
    (HEADER + ROW + "\n", "invalid_row_width"),
    (HEADER + "2024-01-05,10,11,9,10\n", "invalid_row_width"),
    (HEADER + ROW.rstrip("\n") + ",extra\n", "invalid_row_width"),
    (HEADER + '2024-01-05,"10,12,9,11,100\n', "malformed_csv"),
    (HEADER + '2024-01-05,"10"junk,12,9,11,100\n', "malformed_csv"),
    (b"\xff\xfe", "invalid_encoding"),
])
def test_malformed_records_and_encoding(files, csv, code):
    reject(files(csv), code)


def test_bom_and_whitespace_normalization(files):
    original = load_dataset(*files())
    padded = "\ufeff date , open , high , low , close , volume \r\n2024-01-05, 10.10 ,12.00,9.50,11.25,100\r\n"
    normalized = load_dataset(*files(padded))
    assert original.bars == normalized.bars
    assert normalized.report.normalization.csv_bom_removed
    assert normalized.report.normalization.whitespace_fields_trimmed == 7
    assert original.report.dataset_id != normalized.report.dataset_id


@pytest.mark.parametrize("missing", list(REQUIRED_METADATA))
def test_missing_metadata_fields(files, missing):
    metadata = dict(REQUIRED_METADATA)
    del metadata[missing]
    reject(files(metadata=metadata), "missing_metadata_field", field=missing)


@pytest.mark.parametrize("field,value,code", [
    ("contract_version", 2, "unsupported_contract_version"),
    ("contract_version", True, "unsupported_contract_version"),
    ("contract_version", 1.0, "unsupported_contract_version"),
    ("contract_version", "1", "unsupported_contract_version"),
    ("symbol", " ", "invalid_metadata_value"),
    ("source_name", 42, "invalid_metadata_value"),
    ("exchange", None, "invalid_metadata_value"),
    ("currency", "EUR", "invalid_metadata_value"),
    ("frequency", "1h", "invalid_metadata_value"),
    ("session_timezone", "UTC", "invalid_metadata_value"),
    ("source_kind", "provider", "invalid_metadata_value"),
    ("adjustment_basis", "mixed", "invalid_metadata_value"),
    ("volume_basis", "total_return_adjusted", "invalid_metadata_value"),
    ("split_status", False, "invalid_metadata_value"),
    ("session_coverage", True, "invalid_metadata_value"),
    ("source_reference", None, "invalid_metadata_value"),
    ("usage_note", "", "invalid_metadata_value"),
    ("split_evidence", [], "invalid_metadata_value"),
    ("ohlc_basis_consistent", "true", "invalid_metadata_value"),
    ("ohlc_basis_consistent", 1, "invalid_metadata_value"),
    ("ohlc_basis_consistent", False, "inconsistent_adjustment"),
    ("misspelled_setting", "unknown", "unknown_metadata_field"),
])
def test_invalid_metadata(files, field, value, code):
    reject(files(metadata={**REQUIRED_METADATA, field: value}), code, field=field)


@pytest.mark.parametrize("content", [
    "{", "[]", "null", '{"contract_version":1,"contract_version":1}',
    '{"contract_version":NaN}', '{"symbol":"\\ud800"}',
])
def test_invalid_json_and_non_objects(files, content):
    paths = files()
    paths[1].write_text(content, encoding="utf-8")
    with pytest.raises(DataValidationError):
        load_dataset(*paths)


def test_missing_files(files):
    paths = files()
    paths[1].unlink()
    reject(paths, "metadata_read_error")
    paths = files()
    paths[0].unlink()
    reject(paths, "csv_read_error")


@pytest.mark.parametrize("basis", ["unknown", "split_adjusted", "total_return_adjusted"])
def test_adjustment_information_is_preserved_without_eligibility(files, basis):
    result = load_dataset(*files(metadata={**REQUIRED_METADATA, "adjustment_basis": basis}))
    assert result.metadata.adjustment_basis == basis
    assert result.metadata.ohlc_basis_consistent == "unknown"
    assert result.metadata.split_status == "unknown"
    assert any(basis in warning for warning in result.report.warnings)
    assert not hasattr(result, "simulation_eligible")
    reject(files(metadata={**REQUIRED_METADATA, "adjustment_basis": basis, "ohlc_basis_consistent": False}), "inconsistent_adjustment")


def test_optional_defaults_have_canonical_identity(files):
    omitted = load_dataset(*files())
    explicit = load_dataset(*files(metadata={**REQUIRED_METADATA, **dict.fromkeys(OPTIONAL_FIELDS, "unknown")}))
    assert omitted == explicit
    assert all(getattr(omitted.metadata, field) == "unknown" for field in OPTIONAL_FIELDS)
    assert any("not established" in warning for warning in omitted.report.warnings)


def test_declared_complete_does_not_verify_coverage(files):
    result = load_dataset(*files(metadata={**REQUIRED_METADATA, "session_coverage": "declared_complete"}))
    assert result.metadata.session_coverage == "declared_complete"
    assert result.report.coverage_assessment == "unverified"


def test_fingerprints_against_independent_canonical_reference(files):
    source = (HEADER + ROW).encode("utf-8")
    # Handwritten, sorted, complete effective metadata; not the production serializer.
    canonical = (
        '{"adjustment_basis":"unadjusted","contract_version":1,"currency":"USD",'
        '"exchange":"SYNTHETIC_US","frequency":"1d","ohlc_basis_consistent":"unknown",'
        '"session_coverage":"unknown","session_timezone":"America/New_York",'
        '"source_kind":"synthetic","source_name":"Invented fixture",'
        '"source_reference":"unknown","split_evidence":"unknown",'
        '"split_status":"unknown","symbol":"SYNTH","usage_note":"unknown",'
        '"volume_basis":"unknown"}'
    ).encode("utf-8")
    source_hash = sha256(source).hexdigest()
    metadata_hash = sha256(canonical).hexdigest()
    expected_id_input = (
        '{"contract_version":1,"metadata_sha256":"' + metadata_hash
        + '","source_sha256":"' + source_hash + '"}'
    ).encode("utf-8")
    result = load_dataset(*files())
    assert result.report.source_sha256 == source_hash
    assert result.report.metadata_sha256 == metadata_hash
    assert result.report.dataset_id == sha256(expected_id_input).hexdigest()
    assert result.report.source_byte_count == len(source)
    assert result == load_dataset(*files())


@pytest.mark.parametrize("new_csv", [
    HEADER + ROW.replace("11.25", "11.26"),
    (HEADER + ROW).replace("\n", "\r\n"),
    "\ufeff" + HEADER + ROW,
])
def test_changed_source_bytes_change_identity(files, new_csv):
    original = load_dataset(*files())
    changed = load_dataset(*files(new_csv))
    assert original.report.source_sha256 != changed.report.source_sha256
    assert original.report.metadata_sha256 == changed.report.metadata_sha256
    assert original.report.dataset_id != changed.report.dataset_id


@pytest.mark.parametrize("field,value", [
    ("source_name", "Another invented source"), ("symbol", "OTHER"),
    ("adjustment_basis", "unknown"), ("split_status", "present"),
    ("usage_note", "Unknown permission evidence"), ("ohlc_basis_consistent", True),
])
def test_changed_metadata_changes_identity(files, field, value):
    original = load_dataset(*files())
    changed = load_dataset(*files(metadata={**REQUIRED_METADATA, field: value}))
    assert original.report.source_sha256 == changed.report.source_sha256
    assert original.report.metadata_sha256 != changed.report.metadata_sha256
    assert original.report.dataset_id != changed.report.dataset_id


def test_metadata_formatting_key_order_and_paths_do_not_change_identity(files, tmp_path):
    paths = files()
    original = load_dataset(*paths)
    metadata_text = json.dumps(dict(reversed(list(REQUIRED_METADATA.items()))), indent=4)
    other_meta = tmp_path / "another.json"
    other_meta.write_bytes(b"\xef\xbb\xbf" + metadata_text.encode("utf-8"))
    other_csv = tmp_path / "another.csv"
    other_csv.write_bytes(paths[0].read_bytes())
    assert original == load_dataset(other_csv, other_meta)


def test_calendar_gaps_without_session_invention(files):
    result = load_dataset(*files(HEADER + ROW + ROW.replace("2024-01-05", "2024-01-08")))
    assert len(result.bars) == 2
    gap, = result.report.calendar_gaps
    assert (gap.previous_date, gap.next_date, gap.unobserved_calendar_days) == (
        date(2024, 1, 5), date(2024, 1, 8), 2,
    )
    assert result.report.coverage_assessment == "unverified"


def test_single_row_and_consecutive_calendar_dates(files):
    result = load_dataset(*files())
    assert result.report.calendar_gaps == ()
    assert any("Single-row" in warning for warning in result.report.warnings)
    # Even a Saturday label is not rejected using an invented trading calendar.
    two = load_dataset(*files(HEADER + ROW + ROW.replace("2024-01-05", "2024-01-06")))
    assert two.report.calendar_gaps == ()


def test_exact_csv_size_boundary_and_oversize(files):
    # Exactly 10 MiB of valid CSV, with each field below csv's parser limit.
    rows = [ROW.replace("2024-01-05", str(date(2024, 1, 1) + timedelta(days=i))) for i in range(100)]
    padding, remainder = divmod(MAX_CSV_BYTES - len(HEADER + "".join(rows)), len(rows))
    padded = [
        row.replace("10.10,", "10.10" + " " * (padding + (i < remainder)) + ",")
        for i, row in enumerate(rows)
    ]
    source = (HEADER + "".join(padded)).encode("utf-8")
    assert len(source) == MAX_CSV_BYTES
    paths = files(source)
    assert load_dataset(*paths).report.row_count == 100
    paths[0].write_bytes(source + b"\n")
    reject(paths, "input_too_large")


def test_csv_parser_field_limit_has_a_diagnostic(files):
    reject(files(HEADER + ROW.replace("10.10", "1" * 131073)), "malformed_csv")


def test_multiline_quoted_field_uses_physical_source_rows(files):
    source = HEADER + '2024-01-05,"\n10.10\n",12,9,11,100\n' + ROW.replace("2024-01-05", "2024-01-06")
    result = load_dataset(*files(source))
    assert [bar.source_row for bar in result.bars] == [2, 5]
    assert result.report.normalization.whitespace_fields_trimmed == 1


def test_reordering_source_rows_changes_identity(files):
    second = ROW.replace("2024-01-05", "2024-01-08")
    original = load_dataset(*files(HEADER + ROW + second))
    reordered = load_dataset(*files(HEADER + second + ROW))
    assert [bar.date for bar in original.bars] == [bar.date for bar in reordered.bars]
    assert original.report.source_sha256 != reordered.report.source_sha256
    assert original.report.dataset_id != reordered.report.dataset_id


def test_bounded_read_does_not_read_an_entire_oversized_file(files, monkeypatch):
    paths = files()
    original_open = Path.open
    reads = []

    class OversizedInput:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, size):
            reads.append(size)
            return b"x" * size

    def opened(path, *args, **kwargs):
        return OversizedInput() if path == paths[0] else original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", opened)
    reject(paths, "input_too_large")
    assert reads == [MAX_CSV_BYTES + 1]


def test_bounded_diagnostics_and_atomic_failure(files):
    invalid = "not-a-date,10,12,9,11,1\n"
    error = reject(files(HEADER + ROW + invalid * (MAX_DIAGNOSTICS + 5)), "invalid_date")
    assert len(error.issues) == MAX_DIAGNOSTICS
    assert error.error_count == MAX_DIAGNOSTICS + 5
    assert error.truncated
    assert error.issues[0].row == 3
    assert error.issues[-1].row == MAX_DIAGNOSTICS + 2
    exact = reject(files(HEADER + invalid * MAX_DIAGNOSTICS), "invalid_date")
    assert not exact.truncated


def test_ohlc_predicate_independent_cases():
    for values, expected in [
        ((10, 12, 9, 11), True), ((10, 10, 10, 10), True),
        ((12, 12, 9, 9), True), ((10, 12, 11, 12), False),
        ((10, 11, 9, 12), False),
    ]:
        assert validate_ohlc(*(Decimal(value) for value in values)) is expected
