"""Deterministic audit findings; status is separate from severity."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

Assessment = Literal["PASS", "FAIL", "WARNING", "NOT_ASSESSED"]


class AuditError(ValueError):
    """Invalid audit request structure, rather than a detected financial defect."""


@dataclass(frozen=True)
class Evidence:
    reference: str
    observed: str
    expected: str | None = None
    order_id: int | None = None
    fill_index: int | None = None
    session: date | None = None


@dataclass(frozen=True)
class Finding:
    rule_id: str
    title: str
    status: Assessment
    severity: Literal["ERROR", "WARNING"] | None
    explanation: str
    evidence: tuple[Evidence, ...]
    suggested_action: str | None = None


@dataclass(frozen=True)
class AuditReport:
    audit_version: str
    dataset_id: str
    findings: tuple[Finding, ...]


def checked(rule: str, title: str, problems: list[Evidence], scope: str) -> Finding:
    return Finding(
        rule, title, "FAIL" if problems else "PASS", "ERROR" if problems else None,
        scope, tuple(problems) if problems else (Evidence("check_scope", scope),),
        "Investigate the cited records and regenerate the result from corrected retained inputs." if problems else None,
    )


def unavailable(rule: str, title: str, reason: str) -> Finding:
    return Finding(rule, title, "NOT_ASSESSED", None, reason, (Evidence("missing_evidence_or_capability", reason),))


def finite(value: object) -> bool:
    return isinstance(value, Decimal) and value.is_finite()


def whole(value: object, minimum: int = 0) -> bool:
    return type(value) is int and value >= minimum
