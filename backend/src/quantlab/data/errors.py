"""Bounded diagnostics; exceptions never expose a partial Dataset."""

from dataclasses import dataclass
from typing import Literal

MAX_DIAGNOSTICS = 100


@dataclass(frozen=True)
class ValidationIssue:
    source: Literal["csv", "metadata"]
    code: str
    message: str
    row: int | None = None
    field: str | None = None


class DataValidationError(ValueError):
    def __init__(self, issues: tuple[ValidationIssue, ...], error_count: int):
        self.issues = issues
        self.error_count = error_count
        self.truncated = error_count > len(issues)
        first = issues[0]
        location = f"{first.source}, row {first.row}, field {first.field}"
        super().__init__(
            f"Import rejected: {error_count} detected issue(s); "
            f"showing {len(issues)}. {location}: {first.message}"
        )


class Diagnostics:
    """Keep scanning recoverable records without retaining unbounded errors."""

    def __init__(self) -> None:
        self.issues: list[ValidationIssue] = []
        self.error_count = 0

    def add(
        self, source: Literal["csv", "metadata"], code: str, message: str,
        *, row: int | None = None, field: str | None = None,
    ) -> None:
        self.error_count += 1
        if len(self.issues) < MAX_DIAGNOSTICS:
            self.issues.append(ValidationIssue(source, code, message, row, field))

    def raise_if_invalid(self) -> None:
        if self.error_count:
            raise DataValidationError(tuple(self.issues), self.error_count)
