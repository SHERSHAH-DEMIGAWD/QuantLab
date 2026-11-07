# Session 08 - Phase 8

Dates: 2026-11-02 to 2026-11-03 (Asia/Calcutta).

## A. Session overview

**Objective:** a working local research application over the verified backend.
**Status: COMPLETE.** The user explicitly authorized Phase 8 only. Read the
governing documents, Phase 7 report/API contract, actual request/result models,
fixtures and tests; verified the 428-test baseline before implementation.
Actual backend JSON guided the UI, not invented endpoints or financial fields.
No Phase 9 implementation, provider or deployment was started.

Development/verification are AI-assisted. Independent owner explanation and
recreation remain learning work, not an accomplishment inferred from these files.

## B. What was implemented

Paths are relative to repository root.

| Source | Actual responsibility |
| --- | --- |
| `frontend/src/App.tsx`, `main.tsx`, `styles.css` | Four-area shell, selected dataset preference, real connection state, navigation, render fallback, responsive local design |
| `frontend/src/api/schemas.ts`, `client.ts` | Actual JSON runtime schemas/derived TypeScript types, typed fetch, structured errors, raw metadata submission and existing reproduction endpoint |
| `frontend/src/pages/Datasets.tsx` | CSV/metadata upload, explicit synthetic example, retained list/selection, diagnostics and full provenance |
| `frontend/src/pages/Research.tsx` | Conditional strategy controls and backtest/parameter/cost/subperiod/train-test forms, loading/failed/saved states |
| `frontend/src/pages/SavedResearch.tsx` | Bounded history/filtering, open by ID, retained configuration/result and fresh reproduction |
| `frontend/src/components/ResultView.tsx` | Actual metrics, comparisons, training/test scope, trades/fills/orders/equity observations and assumptions |
| `frontend/src/components/EquityChart.tsx`, `Audit.tsx`, `ReproductionView.tsx`, `Common.tsx` | Canvas equity, four audit statuses/evidence, distinct reproduction outcomes, bounded tables and reusable states |
| `frontend/src/lib/format.ts`, `research.ts`, `upload.ts`, `useRemote.ts` | Exact money/session formatting, obvious input checks/request construction, strict byte handling and stale-read protection |
| `frontend/src/test/` | Focused tests with captured real API dataset/backtest/grid/train-test JSON; controlled error/async cases |
| `frontend/e2e/`, `playwright.config.ts` | Real browser workflows, isolated local processes/database, restart verification and responsive checks |
| `frontend/package.json`, `package-lock.json`, `tsconfig.json`, `vite.config.ts`, `index.html` | Exact frontend setup, strict checking/build, loopback proxy and test commands |
| `frontend/public/examples/` | Nine explicitly invented observations and metadata; input data only |

Updated README, D11, roadmap, status and ignore/EOL rules; added
[dashboard contract](../DASHBOARD_CONTRACT.md) and this report. All 41 backend
package source hashes match the captured API implementation manifest. No
backend source, API contract, financial model, dependency or prior test changed.

## C. Why this functionality exists

The backend already computes and retains research. The dashboard makes that
workflow accessible: choose actual retained inputs, state assumptions, execute,
inspect records/unknowns, then reopen and reproduce. It adds presentation and
coordination rather than another portfolio calculator or arbitrary trust score.

## D. Integration with the existing codebase

CSV bytes/metadata -> existing import API -> selected retained dataset ->
validated UI request -> existing experiment endpoint -> actual saved result ->
runtime shape validation -> charts/tables/audit. Saved reopening uses GET;
reproduction uses the existing empty-body POST and displays server equality
flags/limitations. No frontend calculation decides the training winner.

Vite proxies same-origin `/api` to the local backend. No new CORS policy or
endpoint was required. React state holds form/view data and only the selected
dataset ID is a browser preference; SQLite remains the research store.

## E. Technical concepts to study

- **TypeScript/runtime contracts:** `z.infer` types aid development; Zod still
  checks actual untrusted JSON after TypeScript is erased.
- **React state/effects/refs:** forms hold editable values; event handlers submit
  writes; effects load external resources; refs lock writes and invalidate stale
  reads without inventing a global state framework.
- **Boundaries:** UI validation catches obvious mistakes; backend eligibility,
  timing, accounting, selection and workload checks stay authoritative.
- **Formatting versus calculation:** string grouping/decimal expansion preserves
  money text; chart doubles are coordinates, not authoritative accounting.
- **Testing layers:** controlled component/client tests differ from real browser
  uploads, canvas rendering, HTTP computation and database process restarts.

Independently recreate **`money`** and **`useRemote`** after studying their tests.
Explain `buildRequest`, `StrategyControls`, `ResultView`, `api.execute` and the
reproduction view. Copying AI-assisted implementation is not recreation.

## F. Financial and quantitative concepts to study

Show price-only return/dividend exclusion, open positions, actual costs and
observed dates with each run. The same number can mean money, return fraction,
drawdown or ratio; units matter. Undefined win rates/Sharpe require their reason,
not a zero. Short-sample annualized return is extrapolation, not evidence.

The browser's invented buy-and-hold reference starts at $1,000 and ends at
**$800 / -20%**, retaining 100 open shares. The UI does not force a sale. The
training/test workflow freezes momentum lookback 2 after training and reports
**-54%** test return, **$1,000** fresh initial test cash and **six** indicator-only
warm-up bars. No training P&L enters that test. These are reference calculations,
not market claims or attractive performance manufactured for the interface.

Different-length subperiod returns are labeled, not ranked as equivalent
quality. Cost deltas come from stored comparisons; fee changes can alter
integer exposure. PASS is scoped evidence, WARNING is a concern, and
NOT_ASSESSED is an unknown rather than verified safety. One held-out period
does not establish generalization, significance or future profitability.

## G. Engineering decisions and tradeoffs

- Local React/TypeScript/Vite with small hooks/components, fetch, Zod and uPlot.
  No component framework, router package, global-state framework or extra server.
- Pinned runtime: React/ReactDOM 19.3.1, Zod 4.6.7, uPlot 1.6.32. Tooling:
  TypeScript 7.0.2, Vite 8.3.5, Vitest 5.0.5, Playwright 1.64.1 and Testing
  Library; complete choices are in the manifest/lockfile.
- Strict UTF-8 upload preserves BOM/CRLF. Metadata is checked for syntax/object
  shape but submitted raw so duplicate keys reach the backend instead of being
  silently lost during JSON reserialization. Original identity remains meaningful.
- Exact Decimal strings are used for monetary text; canvas axes are explicitly
  approximate, with original hover/table values. No metric/P&L is recomputed.
- Show one selected run in detail; keep backend ordering in comparisons and
  distinguish training selection from test measurement. Tables/API lists are
  paginated. UI cost/window forms allow up to 20 rows each; backend caps remain.
- Clear old results/status before a new execution/reproduction; disable duplicate
  writes, preserve useful failed inputs and discard stale reads, including a
  delayed dataset lookup after a newer import/navigation.
- Native desktop browser tools failed kernel initialization. Local Playwright
  with already-installed Edge provided genuine browser verification instead.
  The Sites skill used its local-only route; no registration/publishing occurred.
- Browser tests build and serve production assets. This prevents development
  hot-reload from confusing deliberate frontend/server restart verification.

## H. Testing and verification

Repository-root backend commands, approved outside the known Windows pytest
temporary-directory sandbox restriction:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest -q --durations=5 --basetemp=.venv/pytest-phase8-baseline
& '.\.venv\Scripts\python.exe' -m pytest -q --durations=10 --basetemp=.venv/pytest-phase8-regression
```

From `frontend`, actual executed verification commands:

```powershell
npm test
npm run build
npm run test:e2e
```

| Executed check | Actual outcome |
| --- | --- |
| Backend baseline | 428 passed in 20.38s |
| Backend regression after integration | 428 passed in 20.46s; slowest case 0.89s |
| Initial frontend suite | 42 passed, 2 failed in 10.97s |
| Corrected frontend suite | 44 passed in 8.02s |
| Final frontend suite with selection-race regression | 45 passed in 9.19s |
| TypeScript + Vite production build | PASS; final browser command rebuilds before testing |
| Real production-browser workflows | 2 passed in 16.8s; extended mobile dataset/saved-result/chart verification: 2 passed in 18.8s |

The earlier ten-minute backend run did not recur. Initial frontend failures
were a query matching duplicate explanation/evidence text and an upload field's
accessible name including its helper text; corrected the query and gave the
control a stable name/description. A first compile caught an unknown ReactNode
condition, then a CSS close-parenthesis error; both corrected before browser QA.

Primary end-to-end evidence, real Edge 156.0.4314.58 at 1440x1000 with an
Asia/Kolkata browser timezone, actual API/SQLite, no mocked financial engine:

1. Start isolated backend 8018 and frontend, upload the actual synthetic CSV
   and JSON metadata, and retain/select it through the UI.
2. Execute buy and hold, verify $800 final equity independently, view the real
   canvas curve/fills/exact observations, and inspect expanded audit evidence.
3. Open saved research, reproduce it, stop/restart both backend/frontend with
   the same database, reload the browser, reopen the same ID and reproduce again.
4. Submit invalid OHLC and verify the backend's `ohlc, row 2` diagnostic.
5. Execute a four-configuration SMA grid plus reference, two cost scenarios,
   explicit three/six-observation subperiods and chronological momentum testing.
6. Verify frozen lookback 2, -54% test return, $1,000 initial test cash and six
   indicator-only warm-up bars; reopen/reproduce the train/test result.
7. Check 390x844 dataset and saved train/test/chart layouts for body overflow
   and inspect real screenshots.

The initial browser run reached restart/reproduction but Vite's reconnect
hot-reload cleared the later failure form. Switched verification to production
preview and explicit document reload. A subsequent run found real select names
including option text; explicit accessible labels fixed strategy/type/run
controls. One retry then failed with **SQLite 503 / Playwright ENOSPC**. Disk
inspection later showed space available; a disposable 1 MiB write probe passed,
extra QA preview processes were stopped, and complete workflows then passed.
No source/user data was deleted to claim a fix. The transient resource cause
remains undiagnosed; no speculative accounting or performance workaround added.

Focused tests cover exact large/subcent/exponent-zero money, percentages and
unavailable reasons, unchanged session labels, actual response schemas,
conditional strategy controls, grids/limits/dates/cost ordering, original bytes,
metadata duplicate preservation, HTTP failures/malformed responses, loading/
empty states, four audit assessments/evidence, comparison/test presentation,
reproduction match/mismatch/implementation change/unavailable states, duplicate
write prevention, preserved failed inputs and stale read/import protection.
Canvas is mocked only for jsdom tests; real browser rendering was inspected.

Dependency setup used the local Sites helper; 110 packages installed and the
installer reported zero vulnerabilities at that time. No interpreter, global
Node/npm upgrade or machine setting was installed/changed. Verified Node
24.15.0/npm 11.12.1; backend stays CPython 3.15.0/pytest 9.2.0. Other browser/OS
combinations and Python 3.12 remain untested.

Screenshots/evidence are generated under ignored `frontend/test-results/`:
`dashboard-desktop.png`, `dashboard-mobile.png`, `dashboard-mobile-research.png`
and `e2e-evidence.json`. Real screenshots were visually inspected. Browser
artifacts/temporary SQLite files are not application source or market datasets.
Preview opening in Codex was queued; no claim of successful native-panel
interaction follows. Owned verification/preview server ports were checked stopped.

Final source/document verification: PASS across 112 project files, including
48 Python AST parses, nine JSON parses, 74 local Markdown links and per-file
Git whitespace checks. Verified UTF-8/no BOM, LF/final newlines, exact frontend
manifest/lock agreement, unchanged Python dependency declarations, all 41
backend source hashes, and 29 core modules without HTTP/persistence imports.
Confirmed A-L sections, five technical/three financial questions, phase status,
empty raw/processed placeholders, no production fixture imports and no staged
files. Converted four captured JSON fixtures from CRLF to LF after proving
their parsed JSON identical; removed one extra CSS end-of-file blank line.
These final whitespace-only corrections leave tested behavior unchanged.

## I. Complexity and performance

For response size P and N valuation points, parsing/runtime validation is O(P)
time/space and chart preparation is O(N). The canvas receives actual points;
the UI does not render an SVG/DOM node per point. Visible table DOM is bounded
at 25/50 rows and list requests at 50 records; source arrays remain in memory.
Exact text formatting is linear in decimal-string length. Stale reads are
discarded; there is no polling loop or speculative financial cache.

Large allowed payloads can still consume substantial browser memory; no
throughput, rendering-speed or formal accessibility benchmark was performed.
Vite reported a 432.59 kB JS / 27.52 kB CSS build (136.21/7.06 kB gzip); these
are observed asset sizes, not a performance improvement claim. Backend complexity
and financial resource bounds are unchanged.

## J. Interview preparation

Five technical questions:

1. Why are TypeScript types insufficient to validate a fetched JSON result, and
   how do runtime schemas keep malformed data out of result components?
2. Why use string operations for Decimal money text while allowing numeric
   coordinates in a chart with exact readouts/tables?
3. How do state, refs, abort signals and request revisions solve different
   loading/double-write/stale-response problems in these actual components?
4. How does the local Vite proxy avoid adding unrestricted backend CORS, and
   which settings change the browser prefix versus the upstream target?
5. What does a mocked component test establish that a real restart/browser
   workflow does not, and why are both needed here?

Three financial questions:

1. Why must unavailable statistics, short-sample annualization and price-only
   return labeling remain visible even when an equity curve looks persuasive?
2. Why must training selection, later test evaluation and unequal-length
   subperiod comparisons remain distinct in the interface?
3. Why can a reproduced result and scoped audit PASS still leave market-data,
   corporate-action, liquidity, overfitting and profitability questions open?

Independent exercise: write a small React dataset selector against two delayed
mock requests. Show loading/error/empty states, then prove that response A
arriving after selection B cannot replace B. Preserve the selected label and
write one focused test. Do it before consulting `useRemote`; keep practice
separate and do not attribute this AI-assisted dashboard to independent work.

## K. Current project status

Phases 0-8 COMPLETE; 9-10 NOT STARTED and unauthorized. No known in-scope
functional failure remains in the executed checks. Backend/API/financial source
is unchanged. Local/single-user, no authentication/public deployment/provider,
no live trading/prices or new analytics. Existing audit/data/statistical limits
remain. Exact text and approximate canvas coordinates are explicitly separated.
Large payload/browser-memory and observed disk-resource limits remain; no
benchmark or full accessibility certification is claimed. Work remains
unstaged/uncommitted with no branch/remote changes. Owner recreation is pending.

## L. Next session

Proposed Session 09 / Phase 9 **only after explicit authorization**: evaluate
one permitted external data integration or the roadmap's validated offline
fallback. Review permitted use/terms, field and adjustment conventions, history,
coverage, reliability, bounded requests, caching identity and failure handling.
Acceptance: one documented import-to-results path with retained evidence and
honest adjustment/session/source limitations. No provider has been selected or
contacted for market data. Stop after Phase 8.
