"""Declared identity, optional original-input checks, eligibility and honest limits."""

from dataclasses import asdict
from hashlib import sha256
import re

from quantlab.data import Bar, Dataset, Metadata
from quantlab.data.errors import Diagnostics
from quantlab.data.identity import canonical_json, fingerprints
from quantlab.data.loader import MAX_CSV_BYTES, _parse_csv
from quantlab.execution import ExecutionSettings, SimulationResult

from .models import Evidence, Finding, checked, unavailable


def check_identity(result: SimulationResult) -> Finding:
    problems = []
    for field in ("dataset_id", "source_sha256", "metadata_sha256"):
        value = getattr(result, field)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            problems.append(Evidence("result." + field, repr(value), "64 lowercase SHA-256 hex characters"))
    if isinstance(result.metadata, Metadata):
        expected_meta = sha256(canonical_json(asdict(result.metadata))).hexdigest()
        expected_id = sha256(canonical_json({
            "contract_version": result.metadata.contract_version,
            "metadata_sha256": result.metadata_sha256, "source_sha256": result.source_sha256,
        })).hexdigest()
        if result.metadata_sha256 != expected_meta or result.dataset_id != expected_id:
            problems.append(Evidence("result.identity", repr((result.metadata_sha256, result.dataset_id)), repr((expected_meta, expected_id))))
    else:
        problems.append(Evidence("result.metadata", repr(result.metadata), "retained effective Metadata"))
    return checked("DATA.RECORDED_IDENTITY", "Recorded identity consistency", problems,
                   "Checked retained hash syntax and canonical effective-metadata/dataset identity relationships; no original bytes or source authenticity are implied.")


def check_inputs(result: SimulationResult, dataset: Dataset | None) -> Finding:
    if dataset is None:
        return unavailable("DATA.INPUT_MATCH", "Supporting dataset matches result", "No retained Dataset supplied.")
    recorded = (result.dataset_id, result.source_sha256, result.metadata_sha256, result.metadata)
    supplied = (dataset.report.dataset_id, dataset.report.source_sha256, dataset.report.metadata_sha256, dataset.metadata)
    problems = [] if recorded == supplied else [Evidence("dataset.identity/metadata", repr(supplied), repr(recorded))]
    if (not dataset.bars or dataset.report.row_count != len(dataset.bars)
            or dataset.report.first_date != dataset.bars[0].date or dataset.report.last_date != dataset.bars[-1].date):
        problems.append(Evidence("dataset.report", repr((dataset.report.row_count, dataset.report.first_date, dataset.report.last_date)), "count/endpoints match retained bars"))
    return checked("DATA.INPUT_MATCH", "Supporting dataset matches result", problems,
                   "Compared supporting Dataset identity/metadata and report count/endpoints; this alone does not reverify its original rows.")


def original_evidence(
    result: SimulationResult, dataset: Dataset | None,
    source_bytes: bytes | None, source_metadata: Metadata | None,
) -> tuple[list[Finding], tuple[Bar, ...] | None]:
    findings = []
    if source_bytes is None:
        findings.append(unavailable("DATA.SOURCE_SHA256", "Exact source-byte hash", "Original CSV bytes were not supplied."))
    else:
        source_hash = sha256(source_bytes).hexdigest()
        findings.append(checked("DATA.SOURCE_SHA256", "Exact source-byte hash", [] if source_hash == result.source_sha256 else [Evidence("original_csv.sha256", source_hash, result.source_sha256)], "Hashed supplied exact CSV bytes independently of metadata availability; this verifies identity, not authenticity."))
    if source_bytes is None or source_metadata is None:
        findings.append(unavailable("DATA.ORIGINAL_IDENTITY", "Original input fingerprints", "Both original CSV bytes and separately supplied effective Metadata are required; a stored dataset ID is not source reverification."))
    else:
        actual = fingerprints(source_bytes, source_metadata)
        expected = (result.source_sha256, result.metadata_sha256, result.dataset_id)
        problems = [] if actual == expected and source_metadata == result.metadata else [Evidence("original_inputs.fingerprints", repr(actual), repr(expected))]
        findings.append(checked("DATA.ORIGINAL_IDENTITY", "Original input fingerprints", problems,
                                "Recomputed D03 fingerprints from supplied exact CSV bytes and effective metadata; SHA-256 establishes identity, not authenticity or rights."))
    parsed = None
    if source_bytes is None:
        findings.append(unavailable("DATA.ORIGINAL_ROWS", "Original CSV rows match retained data", "Original CSV bytes were not supplied; hashes cannot reconstruct or validate rows."))
    else:
        problems = []
        if len(source_bytes) > MAX_CSV_BYTES:
            problems.append(Evidence("source_bytes.length", str(len(source_bytes)), f"at most {MAX_CSV_BYTES} bytes"))
        else:
            diagnostics = Diagnostics()
            bars, _ = _parse_csv(source_bytes, diagnostics)
            if diagnostics.error_count:
                problems.extend(Evidence(f"source_rows[{issue.row}].{issue.field}", issue.code, issue.message) for issue in diagnostics.issues)
            else:
                parsed = tuple(sorted(bars, key=lambda bar: bar.date))
                if dataset is not None and parsed != dataset.bars:
                    problems.append(Evidence("dataset.bars", "retained bars differ from parsed originals", "exact normalized source bars including source_row"))
        if dataset is None and not problems:
            findings.append(unavailable("DATA.ORIGINAL_ROWS", "Original CSV parsing and row comparison", "Source CSV parsed successfully, but no retained Dataset was supplied for row equality. Parsed bars are available for timing/price checks."))
        else:
            findings.append(checked("DATA.ORIGINAL_ROWS", "Original CSV parsing and row comparison", problems, "Reused Phase 1 strict CSV parsing and date normalization, compared every normalized retained bar; no silent row removal or repair."))
    return findings, parsed


def data_declarations(result: SimulationResult, dataset: Dataset | None) -> list[Finding]:
    metadata = result.metadata
    if not isinstance(metadata, Metadata):
        eligibility = checked("DATA.ELIGIBILITY", "Declared execution eligibility", [Evidence("metadata", repr(metadata), "effective Metadata")], "A completed run requires retained D04 declarations.")
        provenance = Finding("DATA.PROVENANCE", "Source provenance declarations", "WARNING", "WARNING", "Source declarations are missing, so provenance cannot be established.", (Evidence("metadata", repr(metadata)),), "Retain the original CSV and effective validated metadata.")
    else:
        problems = []
        required = {"contract_version": 1, "currency": "USD", "frequency": "1d", "session_timezone": "America/New_York", "adjustment_basis": "unadjusted", "ohlc_basis_consistent": True, "volume_basis": "raw", "split_status": "none_reported"}
        for field, expected in required.items():
            actual = getattr(metadata, field)
            if (actual is not True if field == "ohlc_basis_consistent" else actual != expected or (field == "contract_version" and type(actual) is not int)):
                problems.append(Evidence("metadata." + field, repr(actual), repr(expected)))
        if metadata.source_kind not in ("synthetic", "local_file") or not isinstance(metadata.split_evidence, str) or not metadata.split_evidence.strip() or metadata.split_evidence.strip().lower() == "unknown":
            problems.append(Evidence("metadata.source_kind/split_evidence", repr((metadata.source_kind, metadata.split_evidence)), "supported source kind and explicit split evidence"))
        if metadata.source_kind == "local_file" and (not isinstance(result.settings, ExecutionSettings) or result.settings.acknowledge_unverified_coverage is not True):
            problems.append(Evidence("settings.acknowledge_unverified_coverage", repr(getattr(result.settings, "acknowledge_unverified_coverage", None)), "explicit True for real data"))
        eligibility = checked("DATA.ELIGIBILITY", "Declared execution eligibility", problems,
                              "Checked required D04 declarations and real-data coverage acknowledgment; no declaration is independent proof of its historical truth.")
        details = tuple(Evidence("metadata." + field, repr(getattr(metadata, field))) for field in (
            "source_kind", "source_name", "source_reference", "usage_note", "adjustment_basis", "split_status", "split_evidence", "session_coverage"))
        provenance = Finding("DATA.PROVENANCE", "Source provenance declarations", "WARNING", "WARNING", "These source/rights/adjustment/split declarations are assertions, not independently verified historical market facts; synthetic observations are invented when so labeled.", details, "Retain source evidence and investigate unknown or unreliable declarations.")
    warnings = list(result.warnings)
    if dataset is not None:
        warnings.extend(warning for warning in dataset.report.warnings if warning not in result.warnings)
    disclosure = Finding(
        "DATA.LIMITATIONS", "Financial data and model limitations", "WARNING", "WARNING",
        "Session coverage is unverified; calendar gaps do not establish missing sessions. Splits/corporate actions are not processed, dividends/total shareholder return are excluded, and opening liquidity is not established.",
        (Evidence("coverage_assessment", "unverified; no authoritative calendar supplied"),)
        + tuple(Evidence(f"retained_warnings[{i}]", str(warning)) for i, warning in enumerate(warnings)),
        "Investigate source coverage/actions/liquidity before interpreting price-return results.",
    )
    return [eligibility, provenance, disclosure]


def unsupported_findings() -> list[Finding]:
    limitations = (
        ("LOOKAHEAD", "Absence of every form of look-ahead bias", "Trace timing checks cannot prove arbitrary strategy code never accessed future information."),
        ("SURVIVORSHIP", "Survivorship bias", "No historical universe or delisting membership evidence is available."),
        ("INDEX_MEMBERSHIP", "Historical index membership bias", "No historical index constituent records are available."),
        ("SELECTION", "Data snooping and strategy-selection bias", "No complete research/selection history or selection protocol is assessed."),
        ("OVERFITTING", "Overfitting", "No robustness or out-of-sample inference is performed."),
        ("CORPORATE_ACTION_TRUTH", "Historical corporate-action declarations", "Declared none_reported splits and adjustment basis are not independently verified."),
        ("SESSION_COMPLETENESS", "Complete trading-session coverage", "No authoritative reference schedule/completeness evidence is loaded."),
        ("LIQUIDITY", "Realistic opening liquidity", "Daily OHLCV cannot establish actual opening fills, spreads or market impact."),
        ("SIGNIFICANCE", "Statistical significance", "No significance testing or independence assessment is implemented."),
        ("ECONOMIC_EVENTS", "Unmodeled economic events", "OHLCV and declarations cannot resolve all dividends, delistings, revisions or other economic events."),
    )
    return [unavailable("LIMITS." + key, title, reason) for key, title, reason in limitations]
