"""Strict JSON sidecar validation, including explicit defaults for uncertainty."""

from dataclasses import fields
import json
from pathlib import Path

from .errors import Diagnostics
from .models import Metadata

REQUIRED = (
    "contract_version", "symbol", "exchange", "currency", "frequency",
    "session_timezone", "source_kind", "source_name", "adjustment_basis",
)
ENUMS = {
    "currency": ("USD",),
    "frequency": ("1d",),
    "session_timezone": ("America/New_York",),
    "source_kind": ("synthetic", "local_file"),
    "adjustment_basis": (
        "unadjusted", "split_adjusted", "total_return_adjusted", "unknown",
    ),
    "volume_basis": ("raw", "split_adjusted", "unknown"),
    "split_status": ("none_reported", "present", "unknown"),
    "session_coverage": ("declared_complete", "unknown"),
}


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate metadata key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"Non-standard JSON constant: {value}")


def load_metadata(path: Path, diagnostics: Diagnostics) -> Metadata | None:
    try:
        source = path.read_bytes()
    except OSError as exc:
        diagnostics.add("metadata", "metadata_read_error", str(exc))
        return None
    return parse_metadata(source, diagnostics)


def parse_metadata(source: bytes, diagnostics: Diagnostics) -> Metadata | None:
    """Validate retained/uploaded JSON using the same rules as local sidecars."""
    before = diagnostics.error_count
    try:
        supplied = json.loads(
            source.decode("utf-8-sig"),
            object_pairs_hook=_unique_object, parse_constant=_reject_constant,
        )
    except (ValueError, UnicodeError, RecursionError) as exc:
        diagnostics.add("metadata", "invalid_json", str(exc))
        return None
    if not isinstance(supplied, dict):
        diagnostics.add("metadata", "invalid_metadata", "Expected a JSON object.", field="$")
        return None

    field_names = tuple(item.name for item in fields(Metadata))
    allowed = set(field_names)
    for key in sorted(supplied.keys() - allowed):
        diagnostics.add("metadata", "unknown_metadata_field", "Unknown field.", field=key)
    for key in REQUIRED:
        if key not in supplied:
            diagnostics.add("metadata", "missing_metadata_field", "Required field missing.", field=key)

    effective = {
        key: supplied.get(key, "unknown") for key in field_names
        if key in supplied or key not in REQUIRED
    }
    for key, value in effective.items():
        if key == "contract_version":
            if type(value) is not int or value != 1:
                diagnostics.add("metadata", "unsupported_contract_version", "Expected integer contract_version 1.", field=key)
        elif key == "ohlc_basis_consistent":
            if value is False:
                diagnostics.add("metadata", "inconsistent_adjustment", "Inconsistent OHLC adjustment declaration is rejected.", field=key)
            elif value is not True and value != "unknown":
                diagnostics.add("metadata", "invalid_metadata_value", "Expected true, false, or the string unknown.", field=key)
        elif not isinstance(value, str) or not value.strip():
            diagnostics.add("metadata", "invalid_metadata_value", "Expected a nonblank string.", field=key)
        elif key in ENUMS and value not in ENUMS[key]:
            diagnostics.add("metadata", "invalid_metadata_value", "Unsupported field value.", field=key)
        else:
            try:
                value.encode("utf-8")
            except UnicodeError:
                diagnostics.add("metadata", "invalid_metadata_value", "Invalid Unicode text.", field=key)

    if diagnostics.error_count != before:
        return None
    return Metadata(**effective)
