# Session 09 - Phase 9

Date: 2026-11-03 (Asia/Calcutta).

## A. Session overview

**COMPLETE: Path B, validated offline fallback.** Session 09 explicitly
authorized this alternative if permitted provider access could not be verified.
Read governing documents, Phase 8 report, data/API contracts and implementation
of ingestion, D04/coverage preflight, SQLite, service, frontend and existing tests.
Established all reported baselines before implementation. Phase 10 not started.

Work and verification are AI-assisted. Owner learning/recreation remain pending;
this report does not attribute independent authorship or real-market research.

## B. What was implemented

- `frontend/src/components/OfflineGuide.tsx`: expandable preparation, source/
  event-evidence, eligibility, error and retained-research guidance; real downloads.
- `frontend/src/pages/Datasets.tsx`: uses the guide inside the existing import
  form. Import/execution behavior and selected-data views remain unchanged.
- `frontend/public/examples/local_file.metadata.template.json`: valid current
  metadata shape with conservative unknowns; explicitly incapable of granting
  eligibility. Existing nine-session invented CSV/metadata remain the demo.
- `backend/tests/test_offline_workflow.py`: 16 cases exercise shipped assets,
  unsupported declarations, atomic rejection, identity, restart and reexecution.
- `frontend/e2e/dashboard.spec.ts`: third genuine browser case downloads/uploads
  the template and verifies blocked unknown/adjusted input with retained form
  values and no stale result, plus mobile guide layout.
- [Provider review](../MARKET_DATA_REVIEW.md),
  [offline guide](../OFFLINE_DATA_GUIDE.md), README, D12, roadmap, status and
  data/dashboard cross-references document the working outcome.

No production Python, API, database schema, financial rule, dependency/lockfile,
strategy, external adapter or provider control changed. All 41 backend source
hashes still match the actual API fixture manifest captured in Phase 8.

## C. Why this functionality exists

Users need concrete CSV/JSON preparation and evidence instructions, not just an
upload button. Unknown-by-default metadata prevents a template from asserting
unsupported adjustment/split facts. The established application already imports,
computes and retains research; this phase makes that offline path demonstrable
and explains when valid data must remain blocked from simulation.

## D. Integration with the existing codebase

Download guide/template -> existing CSV/JSON form -> existing Phase 1 importer ->
Phase 7 SQLite -> existing execution eligibility/experiments -> actual results/
audit -> saved retrieval -> fresh reproduction. No alternate validator, source
mapping, financial calculation or eligibility flag is added in React.
Original submitted CSV bytes/effective metadata remain retained. External terms
or evidence referenced in text are not copied into SQLite; retain them privately.

## E. Technical concepts to study

Study local static-asset delivery/downloads, file encoding versus parsed values,
strict JSON enums/booleans, HTTP Host boundaries, and integration-test layering.
`OfflineGuide` uses native accessible disclosure/links and existing styles;
no new asynchronous state or framework. Existing upload/client/service/store
functions remain the data path. Tests distinguish GET retrieval from computation
by observing `_compute` only during POST reproduction.

Independently recreate **`validateUpload`** and **`fingerprints`**, then explain
the new guide, policy-test matrix, `service.import_dataset` and `service.reproduce`.
Do not copy the AI-assisted implementation and call that independent recreation.

## F. Financial and quantitative concepts to study

Import validity is distinct from evidence-backed execution eligibility.
Consistent unadjusted OHLC, raw volume, explicit interval split evidence and
none-reported splits remain required; missing/failed event checks stay unknown.
Coverage acknowledgment does not verify sessions or bypass D04. Mixing raw OHLC
with adjusted close changes financial meaning. Price returns exclude dividends.

All observations used here are invented. Independent demo reference: $1,000
buys 100 shares at the second observed $10 open; final $8 close gives **$800,
-20%, 100 open shares**. No forced exit. The earlier held-out example still
reports -54% with fresh test cash and frozen training-selected parameters.
No real security, licensed history, source truth or real no-split claim was tested.

## G. Engineering decisions and tradeoffs

D12 selects Path B. [The provider review](../MARKET_DATA_REVIEW.md) is the primary
home for current official Alpha Vantage endpoint, quota and terms evidence.
Required environment keys were absent (presence only checked, values not read).
No account/entitlement or real permitted import was available. Daily full history
and adjusted endpoint access have documented premium limits; split endpoint
availability/complete evidence was not live-verified. It was not labeled paid-only
by assumption. Alpaca was not pursued without a clearly more feasible path.

No market API, demo market response or provider mock was used as live evidence.
No subscription, credential solicitation, scraping or market-data redistribution.
Keep the fallback small and reuse actual importer/core/persistence. Unknowns
remain visible even when that prevents a simulation. No visual redesign or
extra infrastructure was needed. Provider integration stays unavailable/deferred.

## H. Testing and verification

Repository-root PowerShell, approved execution outside known Windows pytest
temporary-directory sandbox restrictions:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --durations=5 --basetemp=.venv/pytest-phase9-baseline
.\.venv\Scripts\python.exe -m pytest -q backend/tests/test_offline_workflow.py --durations=3 --basetemp=.venv/pytest-phase9-offline
.\.venv\Scripts\python.exe -m pytest -q backend/tests/test_offline_workflow.py --durations=3 --basetemp=.venv/pytest-phase9-offline-fixed
.\.venv\Scripts\python.exe -m pytest -q --durations=5 --basetemp=.venv/pytest-phase9-regression
```

From `frontend`: `npm test` and `npm run test:e2e`. The latter executes
`npm run build` (strict TypeScript + Vite production assets) then Playwright.
No package install/upgrade was needed.

| Actual executed check | Outcome |
| --- | --- |
| Backend baseline | 428 passed in 19.42s |
| Frontend initial sandbox attempt | Vite startup failed `spawn EPERM`; no test result claimed |
| Frontend approved baseline | 45 passed in 14.99s |
| Browser/build baseline | 2 passed in 17.0s; production build passed |
| Initial new offline suite | 16 failed in 3.29s: default TestClient `testserver` Host rejected |
| Corrected new offline suite | 16 passed in 3.39s after test clients used existing localhost contract |
| Complete backend regression | 444 passed in 23.04s; slowest 0.86s workload-cap case |
| Frontend regression | 45 passed in 9.67s |
| First extended browser run | 2 passed, 1 failed in 32.3s: new assertion used wrong existing notice text |
| Corrected complete browser suite | 3 passed in 20.5s; production build passed |

The two original genuine browser workflows still verify synthetic import,
$800 backtest, real canvas/fills/equity/audit, all four robustness modes, saved
retrieval/reproduction, stopping/restarting both processes with the same DB,
invalid OHLC row diagnostics and mobile saved research. New case verifies an
actual template download, template/unknown-split/adjusted-price imports, real
HTTP 422 D04 rejection even with coverage acknowledged, preserved capital and
no stale result. No financial mocks/intercepts; isolated SQLite/API/production
frontend, installed Edge, 1440x1000 and 390x844, Asia/Kolkata timezone.

The 16 API cases also verify no records retained after invalid OHLC/NaN/fractional
volume/inconsistent declarations, all importable unsupported basis/split variants,
explicit local-file acknowledgment even with declared-complete coverage, exact
source retention, duplicate identity/timestamp, actual recomputation after restart
and no replacement experiment from reproduction. Test-only local-file coverage
uses clearly invented observations, not manufactured real-market split evidence.

Visually inspected `frontend/test-results/offline-guide-mobile.png`; guide and
download link are readable without body overflow. Browser artifacts/test DBs
remain ignored. Native desktop browser integration was not reattempted; genuine
Playwright/installed Edge verification fulfilled the browser requirement.

No SQLite 503/ENOSPC recurred; workspace free space observed at 1.97 GiB before
and 1.73 GiB during verification. Phase 8's cause remains undiagnosed, not fixed
by inference. No speculative infrastructure, cleanup or financial workaround.
The earlier ten-minute backend delay did not recur. Both corrected failures were
test-harness/assertion errors; no production policy was weakened to pass them.

Final source/document check: PASS for 118 project files, 49 Python AST parses,
10 JSON files, 97 local Markdown links and per-file Git whitespace checks.
Confirmed UTF-8/no BOM, LF/final newlines, exact frontend manifest/lock agreement,
unchanged Python dependency declarations, 41 unchanged backend source hashes,
29 core modules without HTTP/persistence imports, empty raw/processed placeholders,
no production fixture imports, A-L/learning questions and correct phase status.
No staged files. Owned browser-test ports 8018/5178 checked stopped. Later disk
observation: 1.38 GiB free; no write failure occurred in this session.

## I. Complexity and performance

New guidance/template have fixed size and no polling, data fetch loop or portfolio
calculation. Existing import O(N log N) sorting, execution/response memory and
workload limits are unchanged. Vite observed 435.68 kB JS (137.30 kB gzip) and
27.52 kB CSS (7.06 kB gzip); this is asset-size evidence, not a runtime benchmark.
No performance improvement, browser-memory bound or accessibility certification
is claimed. Finite local storage remains an operational requirement.

## J. Interview preparation

Five technical questions:

1. Why does a metadata template use explicit unknowns instead of convenient
   defaults, and which boundary validates those fields?
2. How can byte-identical imports deduplicate while metadata whitespace/key
   order changes do not change effective identity?
3. Why did TestClient's default Host fail, and why was changing the test client
   preferable to weakening the application's Host validation?
4. How do the tests prove reproduction executes instead of merely fetching a
   saved result, and what survives a process restart?
5. What can a real browser download/upload/rejection test prove beyond mocked
   component tests, and what market facts can neither establish?

Three financial questions:

1. Why is missing split evidence different from evidence that none was reported,
   and why is a coverage checkbox insufficient to repair that gap?
2. How would mixing adjusted close with raw OHLC distort a strategy simulation,
   and why does this engine separately state dividend exclusion?
3. Why do matching reproduced outputs and audit PASS findings fail to establish
   historical source truth, market completeness or future profitability?

Independent exercise: in a separate practice file, import the invented CSV with
unknown splits, predict the import and execution outcomes, then verify both.
Explain why checking coverage acknowledgment cannot change D04 rejection. Write
one independent assertion that a failed run created no saved experiment; do not
alter production declarations merely to make it pass.

## K. Current project status

Phases 0-9 COMPLETE, with Phase 9 delivered through Path B. Provider integration
unavailable/deferred; no real permitted market import claim. No known in-scope
failure remains in executed checks. All original financial/market/audit limits,
single-user/local scope, Python/browser-platform gaps and transient Phase 8 disk
observation remain. Source stays unstaged/uncommitted with no branch/remote
changes. Owner explanation/recreation remain independent future work.

## L. Next session

Session 10 / Phase 10 **only after explicit authorization**: existing roadmap's
engineering validation/release preparation, clean setup, reproducible small
benchmarks, failure/demo evidence, architecture and learning/ownership review.
Acceptance must distinguish synthetic/offline capability from provider or actual
market performance, preserve unresolved reliability observations and report only
executed evidence. No Phase 10 implementation occurred. Stop after Phase 9.
