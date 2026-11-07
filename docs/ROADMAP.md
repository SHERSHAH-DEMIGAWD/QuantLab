# Master roadmap

Updated 2026-11-07 (Asia/Calcutta). These are the original 11 core phases,
numbered 0-10. All are complete within their explicitly authorized scope;
Phase 9 used offline Path B. Session 10 completed final engineering validation
for a local technical demonstration. Session 11 completed the separately
authorized post-release real-data validation; no new phase was added.
No Phase 11 is proposed or authorized.
Session 12 subsequently completed authorized repository publication preparation
without adding a phase; [publication evidence](PUBLICATION_READINESS.md).

| Phase | Name | Status | Dependencies |
| --- | --- | --- | --- |
| 0 | Charter, specification, foundation | COMPLETE | User's master specification |
| 1 | Historical data foundation | COMPLETE | 0; Session 01 explicit authorization |
| 2 | Minimal execution engine | COMPLETE | 1; Session 02 authorization of D04-D05 |
| 3 | Strategy framework and signals | COMPLETE | 2; Session 03 authorization of D08 strategy rules |
| 4 | Costs and performance analytics | COMPLETE | 3; Session 04 authorization of D06-D07 |
| 5 | Integrity auditor | COMPLETE | 1-4; Session 05 explicit authorization |
| 6 | Robustness and experiments | COMPLETE | 3-5; Session 06 authorization of D08 boundaries |
| 7 | Persistence and REST APIs | COMPLETE | 1-6; Session 07 explicit authorization |
| 8 | Interactive research dashboard | COMPLETE | 7; Session 08 explicit authorization |
| 9 | One external data integration or validated offline fallback | COMPLETE (offline Path B) | 1, 7-8; Session 09 explicit authorization |
| 10 | Engineering validation and release | COMPLETE | 0-9; Session 10 explicit authorization |

At every phase: review applicable [decisions](DECISIONS.md), explain approach,
implement only authorized work, execute relevant checks, write a complete A-L
report, update status, and stop. Completion requires the acceptance evidence
below and a learning exercise; an app merely running is insufficient. Review
gates prevent silently treating proposed modeling choices as approved.

## Phase 0 - Charter, technical specification, and foundation

**Inputs:** supplied charter and existing directory/repository inspection.

**Outputs:** permanent scope, architecture, roadmap, acceptance criteria,
proposed structure/contracts, decision log, session protocol/report, initial
learning map, and empty source/fixture/data/frontend locations.

**Acceptance:**

- Confirm the location is safe and identify existing Git/code state.
- Preserve all committed scope and non-goals; identify material ambiguities.
- Describe logical responsibilities, data flow, technology rationale, and the
  proposed structure without application implementation or dependencies.
- Document initial CSV, identity, execution, cost, and metric assumptions;
  distinguish proposals, uncertainty, and later approval requirements.
- Create all persistent memory files and Session 00's A-L learning report.
- Check document completeness, links, skeleton, scope/status consistency, and
  whitespace. Record actual commands/results and unverified behavior.
- Mark complete only after these checks; explicitly leave Phase 1 unauthorized.

## Phase 1 - Historical data foundation

**Inputs:** Phase 0, reviewed D02-D03 contract, an explicitly selected local
Python environment, synthetic CSV/metadata cases. Session 01 authorization
approves D03 with the dated amendment: nine required metadata fields, explicit
`unknown` defaults for the remaining fields, canonical effective metadata, and
a 10 MiB CSV limit. The original Phase 0 proposals remain in the decision log.

**Outputs:** minimal package/dependency/test configuration; local CSV and
metadata loading, validation, ordering, diagnostics, provenance/identity, and
small deterministic fixtures. No database, API, simulation, or provider.

**Acceptance:**

- A valid file and metadata import to documented typed records, ascending
  dates, stable IDs, and an explicit report. Preserve input bytes for identity.
- Repeated imports agree except explicitly non-deterministic provenance fields;
  changing price bytes or relevant metadata changes the identity.
- Reject empty input, duplicate dates/headers, malformed dates/numbers/rows,
  missing/invalid values, inconsistent OHLC, invalid volume, and invalid metadata
  with useful field/row diagnostics. No silent row removal or filling.
- Tests cover unordered rows, UTF-8 BOM, normalization, one row, zero volume,
  unknown adjustment metadata, mixed-basis declarations, and error truncation.
- Verify omitted versus explicit metadata defaults have the same identity;
  reject CSV inputs above 10 MiB and preserve unsupported-version rejection.
- Date gaps are reported without equating holidays/weekends to missing bars or
  claiming a validated exchange calendar. Ingestion does not imply eligibility.
- Execute pytest in the selected environment, record actual versions/command
  and observed results, and explain/recreate the OHLC validation and fingerprint
  functions. Finish the report and stop before Phase 2.

Phase 1 acceptance evidence: [Session 01](session-reports/SESSION_01_PHASE_1.md).

## Phase 2 - Minimal backtesting execution engine

Session 02 explicitly authorized Phase 2 and approved D04-D05 with the dated
fresh-intent clarification. Implemented and verified. Evidence:
[Session 02](session-reports/SESSION_02_PHASE_2.md).

**Inputs:** validated Phase 1 data and explicitly reviewed D04-D05 conventions.

**Outputs:** independent daily simulator with buy and hold, cash/position state,
budgeted intents, integer fills, orders/history, close valuation, visible zero
costs, and deterministic hand-calculated fixtures.

**Acceptance:**

- Reference examples agree on quantities, cash, valuations, and order outcomes.
- Verify insufficient capital, overnight gaps, zero-volume rejection, invalid
  eligibility, final pending order, open final position, and no forced sale.
- Every bar preserves cash/share/equity invariants; every fill follows its
  decision session. A deliberately changed future price cannot change earlier
  decisions. State and records remain deterministic.
- Nonzero costs are rejected until Phase 4; no strategy framework or analytics
  beyond accounting is silently pulled forward. Include a small handcrafted
  sell-path example to validate both sides of state transitions.

## Phase 3 - Strategy framework and trading signals

Session 03 explicitly approved D08's strategy rules and completed this phase.
Evidence: [Session 03](session-reports/SESSION_03_PHASE_3.md).

**Inputs:** verified engine and reviewed D08 signal definitions.

**Outputs:** minimal common strategy interface, SMA crossover, momentum,
parameter validation, and reference signal fixtures. Adapt buy and hold to the
same interface without changing its timing.

**Acceptance:**

- Signal sequences match independently tabulated examples, including warm-up,
  ties, initial bullish state, thresholds, and invalid parameters.
- Strategies see history only through T; signals and Phase 2 fills preserve
  existing timing and portfolio invariants.
- Document expected signal-generation complexity; tests show append-future
  invariance for earlier outputs. No arbitrary user code or extra strategies.

## Phase 4 - Transaction costs and performance analytics

Session 04 approved D06-D07 and completed this phase. Evidence:
[Session 04](session-reports/SESSION_04_PHASE_4.md).

**Inputs:** verified strategies, reviewed D06-D07 cost/metric conventions.

**Outputs:** explicit commission/slippage; equity and return series; cumulative
and annualized return, drawdown, volatility, Sharpe, closed-trade statistics;
comparable buy-and-hold results.

**Acceptance:**

- Buy/sell accounting, rounding, fee affordability, and zero-cost compatibility
  match independent hand examples; rejected/expired orders incur no fee.
- Metrics agree with reference values and definitions, including zero trades,
  open positions, short samples, zero variance, break-even trades, and undefined
  values. All costs and dividend/adjustment limitations are visible.
- Benchmark uses the same interval, capital, costs, timing, and end treatment.
  A useful baseline is not evidence of profitability or statistical significance.

## Phase 5 - Backtest integrity auditor

Session 05 completed the supported audit checks and documented unassessed
risks. Evidence: [Session 05](session-reports/SESSION_05_PHASE_5.md).
Phase 6 was subsequently authorized and completed in Session 06.

**Inputs:** Phase 1 validation reports and Phase 2-4 execution/results.

**Outputs:** supported timing, provenance, reproducibility, configuration, and
data checks with findings, evidence, severity, and assessment limitations.

**Acceptance:**

- Deliberately invalid records trigger the intended check; valid references do
  not trigger those same errors. Report precise rule coverage and unknowns.
- Check that fills are eligible, cost settings are retained, and identified
  inputs/configuration repeat. Distinguish a check of traces from proof that
  arbitrary strategy code is free from future-data access.
- Never claim that OHLCV alone detects universe survivorship, all corporate
  actions, complete session coverage, or every form of bias.

## Phase 6 - Robustness and experiment engine

Session 06 completed all four capabilities, workload preflight, indicator-only
test warm-up and training-only selection. D08/D09 dated amendments record the
boundary decisions. Evidence: [Session 06](session-reports/SESSION_06_PHASE_6.md).
Phase 7 was subsequently authorized and completed in Session 07.

**Inputs:** strategies, analytics, auditor, and reviewed D08 boundaries/caps.

**Outputs:** bounded parameter grids, cost sensitivity, historical subperiods,
chronological train/test evaluations, comparison records.

**Acceptance:**

- Repeat identical requests deterministically; reject invalid/oversized grids
  before execution; do not truncate silently.
- Freeze training-selected parameters before test evaluation. Warm-up history
  does not enter test performance; no training holdings carry into test state.
- Controlled fixtures verify comparison math and show a case where parameters
  or costs deteriorate results. Do not label test-driven selection out-of-sample.

## Phase 7 - Persistence and REST APIs

Session 07 completed the local SQLite/FastAPI backend, retained-input
revalidation, full saved results and fresh reproduction with explicit economic/
implementation comparisons. D10 records scope and serialization policy.
Evidence: [Session 07](session-reports/SESSION_07_PHASE_7.md).
Phase 8 was subsequently authorized and completed in Session 08.

**Inputs:** verified core and stable experiment/result contracts.

**Outputs:** SQLite schema, necessary versioned SQL changes, lightweight access
layer, FastAPI/Pydantic endpoints, saved metadata/configuration/experiments/
results, and reproducibility references.

**Acceptance:**

- Create, save, retrieve, and reproduce an experiment with matching economic
  outputs using retained input data, metadata, configuration, and source identity.
- Integration tests cover validation errors, unknown IDs, failed writes with
  rollback, schema initialization/version handling, and result retrieval.
- Domain functions still work without HTTP/database; metadata alone is never
  claimed sufficient when original input bytes are unavailable.

## Phase 8 - Interactive research dashboard

Session 08 completed the four local research areas, typed real-API integration,
equity/trade/audit/comparison views and saved reopening/reproduction. Genuine
production-browser workflows and backend/frontend regressions passed. D11
records UI boundaries. Evidence: [Session 08](session-reports/SESSION_08_PHASE_8.md).
Session 09 subsequently authorized and completed Phase 9's offline alternative.

**Inputs:** stable, integration-tested APIs and existing research workflow.

**Outputs:** React/TypeScript interface for dataset/strategy/parameter selection,
execution, equity/metrics, trades, warnings, and experiment comparison.

**Acceptance:**

- Complete one documented research workflow through the interface without
  manual API calls; validate loading, empty, invalid-input, and failed-run states.
- Charts/tables match stored backend results, units, dates, and costs; warnings
  remain visible and comparisons use compatible evaluation windows.
- Record actual frontend checks and a representative end-to-end verification.
  Select only the charting/development packages needed for this phase.

## Phase 9 - One permitted external financial-data integration

Session 09 completed **Path B, validated offline fallback**. Alpha Vantage was
reviewed first; no configured credentials/permitted live import were available.
Provider integration is unavailable/deferred, not implemented. The existing UI
now includes offline guidance/templates; actual imports, financial restrictions,
backtest/audit, restart persistence and fresh reproduction passed real workflows.
No backend source or policy changed. Evidence: [provider review](MARKET_DATA_REVIEW.md),
[offline guide](OFFLINE_DATA_GUIDE.md), [Session 09](session-reports/SESSION_09_PHASE_9.md).
Session 10 subsequently authorized and completed final engineering validation.

**Inputs:** reviewed provider terms, fields, adjustment conventions, reliability,
history, and limitations; existing import/backend/frontend workflow.

**Outputs:** one bounded adapter with normalization, provenance, local caching,
failure handling, and fallback; or a validated offline-import completion report.

**Acceptance:**

- If a provider is suitable, import one supported instrument under documented
  permitted use; verify field mapping, adjustment basis, cache identity,
  bounded requests, and failures against fixtures plus an actual permitted
  import. A cached input snapshot supports repeatability, not immutable upstream
  history. Record access date and terms limitations.
- If no provider qualifies, document evaluation evidence and execute a
  reproducible offline import-to-results workflow. No unauthorized scraping.
  Explicitly report provider integration as unavailable, not implemented.

## Phase 10 - Engineering validation and resume-ready release

Session 10 completed fresh isolated setup, full regressions, all-strategy real
browser/failure/restart workflows, financial/failure evidence review, repeated
250/1,000/5,000-bar benchmarks and concise release/demo/ownership documentation.
No financial engine, provider, dependency or architecture change was needed.
The result is a local demonstration deliverable, not a published service or
independent owner-mastery claim. Evidence: [release validation](RELEASE_VALIDATION.md),
[benchmarks](BENCHMARKS.md), [Session 10](session-reports/SESSION_10_PHASE_10.md).

**Inputs:** preceding phase evidence and a representative end-to-end workflow.

**Outputs:** regression evidence, repeatable small benchmarks, failure demos,
setup cleanup, architecture diagram update, demo, interview material, and
evidence-backed resume statements.

**Acceptance:**

- Run documented setup/workflow from a clean environment; execute relevant
  regression and failure cases and record results, known limitations, and bugs.
- Benchmark documented dataset sizes with hardware, versions, configuration,
  timing method, and repeated measurements; establish a baseline before any
  improvement claim. Do not invent coverage, speed, or finance conclusions.
- Owner can explain core data/execution/metric files, rerun checks, recreate key
  functions, and make a small change. Resume/demo claims map to actual evidence
  and honestly describe AI assistance and unresolved market-data limitations.

## Phase sizing and optional work

Post-release validation, explicitly authorized 2026-11-03: **COMPLETE**.
Two private Alpha Vantage historical samples exercised the existing offline
importer and research/persistence workflows; six opt-in cases and full relevant
regressions passed. No financial, product-provider or architectural change.
Evidence: [real validation](REAL_MARKET_VALIDATION.md),
[Session 11](session-reports/SESSION_11_PHASE_10.md). Stop after this task.

All planned implementation phases are complete. Stop; there is no automatic
next phase. Independent study remains pending. Optional ideas below are not
authorization for further development.

Post-release educational handbook, explicitly authorized: **COMPLETE**, 2026-11-04.
The [20-chapter handbook](QUANTLAB_COMPLETE_HANDBOOK.md) consolidates source-grounded
teaching, worked examples, interview defense and independent study. Documentation
only; no application/test/dependency/architecture change or additional phase.
Verification and disclosed wording gap: [Session 13](session-reports/SESSION_13_PHASE_10.md).
Stop after the handbook; owner learning is not inferred from document completion.
Session 14 completed the user's PDF-format follow-up: the full local 72-page
edition, with content/link/layout checks; no implementation phase or application
change. Evidence: [Session 14](session-reports/SESSION_14_PHASE_10.md).
Session 15 completed explicitly authorized public GitHub source publication and
fresh-clone setup/backend/frontend/browser verification. No new phase, financial
change or hosted deployment. Evidence: [Session 15](session-reports/SESSION_15_PHASE_10.md).

Target one focused session per phase. If a phase proves too large, explain why,
record named subphases and unchanged acceptance, and report partial progress.
Do not rush checks or implement multiple future phases to hit a deadline.

Optional post-MVP ideas remain only in the charter. No extensions, providers,
strategies, infrastructure, or additional committed phases have been added.
