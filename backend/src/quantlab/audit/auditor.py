"""Compose explicit rules; optional replay delegates to the existing simulator."""

from dataclasses import fields
from datetime import date
from decimal import Context, DecimalException, ROUND_HALF_UP, localcontext

from quantlab.data import Bar, Dataset, ImportReport, Metadata
from quantlab.execution import (
    DailyValuation, Decision, ExecutionSettings, Fill, Order, SimulationResult, simulate,
)
from quantlab.strategies import BuyAndHold, SMACrossover, TimeSeriesMomentum

from .accounting import (
    check_balances, check_cost_configuration, check_fill_costs, check_ledger, check_source_prices,
)
from .models import AuditError, AuditReport, Evidence, Finding, checked, finite, unavailable, whole
from .provenance import check_identity, check_inputs, data_declarations, original_evidence, unsupported_findings
from .trace import check_causality, check_lifecycle, check_sessions, check_warmup

AUDIT_VERSION = "1.1.0"


def _reference_bars(result: SimulationResult, source: tuple[Bar, ...] | None) -> tuple[Finding, tuple[Bar, ...] | None]:
    if source is None:
        return unavailable("DATA.SOURCE_SEQUENCE", "Usable source session sequence", "Neither original parsed CSV bars nor a retained Dataset is available."), None
    problems = []
    previous = None
    for i, bar in enumerate(source):
        if type(bar.date) is not date or (previous is not None and bar.date <= previous):
            problems.append(Evidence(f"source.bars[{i}].date", repr(bar.date), "strictly increasing unique dates"))
        else:
            previous = bar.date
        if (not all(finite(n) and n > 0 for n in (bar.open, bar.high, bar.low, bar.close))
                or not whole(bar.volume)
                or not bar.low <= min(bar.open, bar.close) <= max(bar.open, bar.close) <= bar.high):
            problems.append(Evidence(f"source.bars[{i}]", repr(bar), "positive consistent OHLC and nonnegative integer volume"))
    settings = result.settings
    if not isinstance(settings, ExecutionSettings) or any(type(value) is not date for value in (settings.start_date, settings.end_date) if value is not None):
        problems.append(Evidence("settings.evaluation_dates", repr(settings), "retained optional date bounds"))
    if problems:
        return checked("DATA.SOURCE_SEQUENCE", "Usable source session sequence", problems, "Invalid source structure/configuration prevents observed-session reference checks."), None
    selected = tuple(bar for bar in source if (settings.start_date is None or bar.date >= settings.start_date) and (settings.end_date is None or bar.date <= settings.end_date))
    finding = checked("DATA.SOURCE_SEQUENCE", "Usable source session sequence", [], f"Checked {len(source)} supplied bars; selected {len(selected)} by recorded settings. This does not establish exchange-session completeness.")
    return finding, selected


def _replay(result: SimulationResult, dataset: Dataset | None, rerun: bool) -> Finding:
    rule, title = "REPRODUCIBILITY.REPLAY", "Exact current-engine replay"
    if not rerun:
        return unavailable(rule, title, "Replay was not requested; identity/hash checks alone do not establish simulation reproducibility.")
    if dataset is None or not isinstance(result.settings, ExecutionSettings) or type(result.strategy) not in (BuyAndHold, SMACrossover, TimeSeriesMomentum):
        return unavailable(rule, title, "A retained Dataset and complete supported strategy/execution configuration are required; missing configuration is never replaced by defaults.")
    if result.engine_version != "1.3.0":
        return unavailable(rule, title, "Only current engine 1.3.0 exact replay is supported; historical executable/source snapshots are not retained or reconstructed.")
    try:
        repeated = simulate(dataset, result.initial_capital, result.strategy, result.settings)
    except (ValueError, DecimalException) as exc:
        return checked(rule, title, [Evidence("engine.replay", str(exc), "successful run using supplied inputs and recorded configuration")], "The existing engine could not repeat the recorded request.")
    problems = []
    for field in fields(SimulationResult):
        actual, expected = getattr(result, field.name), getattr(repeated, field.name)
        if actual == expected:
            continue
        if isinstance(actual, tuple) and isinstance(expected, tuple):
            mismatch = next((i for i, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1]), None)
            if mismatch is not None:
                problems.append(Evidence(f"result.{field.name}[{mismatch}]", repr(actual[mismatch]), repr(expected[mismatch])))
            else:
                problems.append(Evidence("result." + field.name + ".length", str(len(actual)), str(len(expected))))
        else:
            problems.append(Evidence("result." + field.name, repr(actual), repr(expected)))
    return checked(rule, title, problems, "Reused the existing engine once and compared every SimulationResult dataclass field exactly, including identities/settings/strategy/events/accounting/assumptions/warnings. No fields are excluded: the current schema has no nondeterministic provenance fields. This proves agreement with current code and supplied data, not historical source truth or a preserved original code snapshot.")


def audit_simulation(
    result: SimulationResult, *, dataset: Dataset | None = None,
    source_bytes: bytes | None = None, source_metadata: Metadata | None = None,
    expected_settings: ExecutionSettings | None = None, rerun: bool = False,
) -> AuditReport:
    """Audit typed records; original bytes/metadata and replay are optional evidence.

    Financial reconciliation has its own Decimal context and formulas. Source
    CSV parsing/fingerprinting and replay reuse their established components.
    No rule claims complete bias detection, a trust score, or investment merit.
    """
    if not isinstance(result, SimulationResult) or type(rerun) is not bool:
        raise AuditError("Expected SimulationResult and boolean rerun.")
    for name, record_type in (("orders", Order), ("fills", Fill), ("valuations", DailyValuation), ("decisions", Decision)):
        records = getattr(result, name)
        if not isinstance(records, tuple) or not all(isinstance(item, record_type) for item in records):
            raise AuditError(f"{name} must contain typed {record_type.__name__} records.")
    if dataset is not None and (not isinstance(dataset, Dataset) or not isinstance(dataset.report, ImportReport)
            or not isinstance(dataset.metadata, Metadata) or not isinstance(dataset.bars, tuple)
            or not all(isinstance(bar, Bar) for bar in dataset.bars)):
        raise AuditError("dataset must be a typed Phase 1 Dataset.")
    if source_bytes is not None and not isinstance(source_bytes, bytes):
        raise AuditError("source_bytes must be exact bytes, not text.")
    if source_metadata is not None and not isinstance(source_metadata, Metadata):
        raise AuditError("source_metadata must be separately supplied effective Metadata.")
    if expected_settings is not None and not isinstance(expected_settings, ExecutionSettings):
        raise AuditError("expected_settings must be a separately retained ExecutionSettings.")
    with localcontext(Context(prec=28, rounding=ROUND_HALF_UP)):
        originals, parsed = original_evidence(result, dataset, source_bytes, source_metadata)
        source = parsed if parsed is not None else dataset.bars if dataset is not None else None
        sequence, bars = _reference_bars(result, source)
        findings = [check_identity(result), check_inputs(result, dataset), *originals, sequence,
                    check_lifecycle(result), check_causality(result), check_sessions(result, bars),
                    check_warmup(result, source if sequence.status == "PASS" else None)]
        # Tampered Decimal values outside supported arithmetic become findings,
        # rather than crashing the remaining independent checks.
        financial = []
        for rule, title, check in (
            ("ACCOUNTING.BALANCES", "Portfolio balances and terminal state", check_balances),
            ("ACCOUNTING.LEDGER", "Cash and position ledger", check_ledger),
            ("COSTS.CONFIGURATION", "Retained supported cost settings", check_cost_configuration),
        ):
            try:
                financial.append(check(result))
            except DecimalException as exc:
                financial.append(checked(rule, title, [Evidence("numeric_trace", str(exc), "supported finite precision-28 arithmetic")], "Unsupported numeric trace prevents reconciliation."))
        findings.extend(financial)
        try:
            findings.append(check_fill_costs(result, financial[-1]))
        except DecimalException as exc:
            findings.append(checked("COSTS.FILL_MATH", "Declared cost arithmetic", [Evidence("numeric_trace", str(exc), "supported precision-28 arithmetic")], "Unsupported fill arithmetic."))
        findings.append(check_source_prices(result, bars))
        request_match = (checked("COSTS.REQUEST_MATCH", "Retained settings match original request", [] if result.settings == expected_settings else [Evidence("result.settings", repr(result.settings), repr(expected_settings))], "Compared the complete result settings with separately supplied original request settings.")
                         if expected_settings is not None else unavailable("COSTS.REQUEST_MATCH", "Retained settings match original request", "Original request settings were not separately supplied; hidden settings changes cannot be assessed from a self-consistent result alone."))
        findings.append(request_match)
        filled_ids = {fill.order_id for fill in result.fills if whole(fill.order_id, 1)}
        charged = [Evidence("orders.status/fills", repr(order.status), "rejected/expired order has no fill", order.order_id) for order in result.orders if order.status in ("REJECTED", "EXPIRED") and whole(order.order_id, 1) and order.order_id in filled_ids]
        findings.append(checked("COSTS.UNFILLED", "No unfilled-order cash charges", charged, "Checked absence of fills on rejected/expired orders and a fully reconciled cash ledger.") if charged or financial[1].status == "PASS" else unavailable("COSTS.UNFILLED", "No unfilled-order cash charges", "Cash ledger did not reconcile; absence of hidden unfilled-order charges cannot be established."))
        findings.extend(data_declarations(result, dataset))
        findings.append(_replay(result, dataset, rerun))
        findings.append(unavailable("REPRODUCIBILITY.SOURCE_SNAPSHOT", "Original executable source snapshot", "No original executable/source snapshot is supplied or restored; a version label and current-engine replay do not prove preservation of historical code."))
        findings.extend(unsupported_findings())
        return AuditReport(AUDIT_VERSION, result.dataset_id, tuple(findings))
