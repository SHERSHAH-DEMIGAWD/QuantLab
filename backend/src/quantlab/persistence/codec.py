"""Lossless financial JSON and a deliberately scoped economic comparison."""

from dataclasses import fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from hashlib import sha256
import json
from math import isfinite


def to_wire(value):
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: to_wire(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return to_wire(value.value)
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Nonfinite Decimal cannot be serialized.")
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise ValueError("JSON object keys must be strings.")
        return {key: to_wire(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [to_wire(item) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is float and isfinite(value):
        return value
    raise ValueError("Unsupported JSON value.")


def dumps(value) -> str:
    return json.dumps(value, default=to_wire, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def loads(text: str | bytes):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key.")
            result[key] = value
        return result
    def reject_constant(value):
        raise ValueError("Nonstandard JSON constant.")
    def finite_float(value):
        number = float(value)
        if not isfinite(number):
            raise ValueError("Nonfinite JSON number.")
        return number
    return json.loads(text, object_pairs_hook=unique, parse_constant=reject_constant, parse_float=finite_float)


def digest(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


# These remain saved/visible; they are not economic result equality claims.
ECONOMIC_EXCLUSIONS = frozenset({
    "reproducibility", "experiment_version", "engine_version", "audit",
    "assumptions", "warnings",
})


def economic_projection(value):
    if isinstance(value, dict):
        return {key: economic_projection(item) for key, item in value.items() if key not in ECONOMIC_EXCLUSIONS}
    if isinstance(value, list):
        return [economic_projection(item) for item in value]
    return value


def difference_paths(saved, current, limit: int = 20) -> tuple[str, ...]:
    """Bounded diagnostic paths, not a duplicate of either large result."""
    paths = []
    def visit(left, right, path):
        if len(paths) >= limit:
            return
        if type(left) is not type(right):
            paths.append(path)
        elif isinstance(left, dict):
            for key in sorted(left.keys() | right.keys()):
                if key not in left or key not in right:
                    if len(paths) < limit:
                        paths.append(f"{path}.{key}")
                else:
                    visit(left[key], right[key], f"{path}.{key}")
        elif isinstance(left, list):
            if len(left) != len(right):
                paths.append(path + ".length")
            for index, (a, b) in enumerate(zip(left, right)):
                visit(a, b, f"{path}[{index}]")
        elif left != right:
            paths.append(path)
    visit(saved, current, "result")
    return tuple(paths)
