# Phase 8 local research dashboard

The React/TypeScript dashboard consumes the unchanged
[Phase 7 API](API_CONTRACT.md). Financial calculations, eligibility, workload
preflight, saved records and reproduction remain authoritative on the backend.
UI choices are recorded in [D11](DECISIONS.md#d11---phase-8-local-research-dashboard).

## Start locally

Prerequisites: the existing Python environment/package and Node 24+. Verified
here: CPython 3.15.0, Node 24.15.0, npm 11.12.1, Windows and Edge 156.

Terminal 1, repository root:

```powershell
& '.\.venv\Scripts\python.exe' -m quantlab.api
```

Terminal 2, repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open [the local dashboard](http://127.0.0.1:5173/) while both processes run.
The API defaults to 127.0.0.1:8000 and ignored `data/quantlab.sqlite3`.
Stop each foreground process with Ctrl+C. The frontend stores only the selected
dataset ID as a browser preference; research is retained in SQLite.

For a different local API port, set `QUANTLAB_API_TARGET` before launching Vite:

```powershell
$env:QUANTLAB_API_TARGET='http://127.0.0.1:8008'
npm run dev
```

`VITE_API_BASE` configures the browser API prefix (default `/api/v1`). The
recommended setup keeps same-origin `/api` requests and changes Vite's target,
not backend CORS. An absolute cross-origin API URL still requires that server's
own compatible CORS policy; this phase adds no CORS access. Vite and its
production preview bind to loopback. No public hosting/deployment is configured.

`npm run build` performs strict TypeScript checking and creates `frontend/dist`.
`npm run preview` serves that production build at 127.0.0.1:4173 with the same
local proxy. Runtime dependencies are React/ReactDOM 19.3.1, uPlot 1.6.32 and
Zod 4.6.7. Vite 8.3.5, TypeScript 7.0.2, Vitest 5.0.5 and Playwright 1.64.1
are development/test tools. Exact direct/transitive choices are in the manifest
and lockfile; no component library, state framework or router dependency.

## Four research areas

| Area | Implemented workflow |
| --- | --- |
| Datasets | Upload CSV and upload/edit JSON metadata, load explicitly invented example inputs, inspect field/row errors, paginate retained datasets, select and inspect provenance/validation |
| Backtest | Conditional buy-and-hold/SMA/momentum controls, capital/dates/costs/risk-free rate/coverage acknowledgment/reference, execute and retain actual results |
| Experiments | Parameter grids, cost sensitivity, explicit subperiods and chronological train/test using the real existing endpoint |
| Saved Research | Paginate/filter completed records, open by ID, inspect complete configuration/results and request a fresh reproduction |

Import acceptance is labeled separately from simulation eligibility. Source,
adjustment basis, declared/unverified coverage, split status/evidence and usage
information remain inspectable. The synthetic nine-session input contains no
historical market observations; it supplies inputs, never precomputed UI results.

Phase 9 adds **Offline import guide & templates** within Datasets: local-file
metadata with conservative unknowns, downloadable invented inputs, preparation,
eligibility and saved/reproduction guidance. It uses the same import form and
backend without a provider option. Detailed steps/evidence requirements belong
in [OFFLINE_DATA_GUIDE.md](OFFLINE_DATA_GUIDE.md); provider access is explicitly
unavailable/deferred. No financial or API behavior changed.

SMA and momentum grid axes use comma-separated lists. Invalid pairs reject the
entire request, not a filtered grid. Cost sensitivity uses the first listed
scenario as reference; subperiod rows retain their own dates and durations.
The UI permits at most 20 explicit cost scenarios or subperiods per form.
The existing 100-config/1,000,000-bar limits still count references/warm-up and
are checked by the backend. Integer controls reject unsafe JavaScript integer
representations; decimal strings use the existing plain-notation/length rules.

Training/test controls explicitly separate the intervals and optional training
indicator history. The saved training selection/ranking/tie rule is shown as
recorded. Test detail defaults to the selected held-out run, with its own label,
fresh initial capital and no training holdings/P&L. Test rows are not ranked.

## Result presentation

- Equity curve, initial/final equity, cumulative/annualized return, drawdown,
  volatility, Sharpe and annual risk-free rate are taken from returned records.
  Short-sample annualization is marked as extrapolation.
- Closed-trade statistics, open holdings, realized/unrealized P&L, execution
  outcomes, fills and exact equity observations are inspectable. No final sale
  or hypothetical fee is invented. Returned baseline differences are displayed,
  not recalculated. Positive delta drawdown means greater drawdown.
- Monetary text formats original Decimal strings by string operations, retaining
  all meaningful fractional digits. It does not convert money to float or feed
  display values back into portfolio calculations. Existing float statistics
  have percentage/ratio formatting. Undefined values say Unavailable and retain
  the backend reason, rather than showing zero or NaN/Infinity.
- uPlot uses numeric coordinates for the canvas only. Chart positions/tick
  labels are approximate; the hover readout and observation table use original
  Decimal/session values. All actual valuation points are supplied; no market
  rows, missing sessions, returns or portfolio metrics are synthesized.
- Session labels remain stored ISO dates. UTC timestamps identify operational
  creation times. Chart timestamp coordinates use UTC explicitly and do not
  shift session labels through the user's local timezone.
- PASS, FAIL, WARNING and NOT_ASSESSED have distinct labels/styles, expandable
  explanations, severity and evidence. Counts are finding counts, not a trust
  score. Unsupported risks never become verified safe. Price-only/dividend
  exclusion is visible alongside each run; further assumptions remain expandable.

Large tables render 25 rows at a time (50 for equity observations); API lists
use 50-record pages. Comparison order is the backend order. One selected run
drives the detail chart; the UI does not generate test-performance rankings.

## State and errors

Read requests abort/discard stale responses; delayed dataset selection cannot
override a newer import or navigation. New execution/reproduction attempts clear
previous result/status, prevent double submission, and retain useful editable
inputs on errors. Dataset file decoding is also guarded against stale reads.
Successful executions are saved automatically by the API; opening a saved
record is presented separately from reproduction.

CSV decoding is fatal on invalid UTF-8 and preserves original BOM/CRLF. Metadata
syntax/object checks are preliminary: its original JSON is submitted without
reserializing/dropping duplicate keys, so the backend can reject them. UI caps:
10 MiB CSV and 64 KiB raw metadata. Backend body/precision/eligibility checks may
still reject a request, including JSON overhead exceeding its body cap.

Zod schemas model actual JSON responses and derive TypeScript result types.
Unexpected success/error shapes, nonfinite values and unsupported assessments
produce readable contract errors. HTTP diagnostics retain useful field/row
messages; network failures explain the local backend/proxy requirement. No
stack trace or untrusted HTML is rendered. A render boundary provides a reload
path for unexpected view failures without inventing a research result.

Reproduction uses the existing empty-body POST. It separately displays economic
equality and recorded implementation equality, mismatch paths and server-provided
limitations. A changed implementation remains a limitation even when outputs
match. A 409/unavailable result clears any earlier successful reproduction state.
No cached retrieval or frontend comparison is labeled reproduction.

## Verification and limits

From `frontend`:

```powershell
npm test
npm run build
npm run test:e2e
```

The browser command builds first, then runs real Edge workflows on Windows
(override `PLAYWRIGHT_CHANNEL` for another installed supported channel). It
owns loopback backend 8018 and production-preview 5178, uses an isolated ignored
SQLite file, uploads synthetic inputs through the UI and stops owned processes.
`QUANTLAB_PYTHON` can select an explicit interpreter; the default is the project
venv. Other operating systems/browser channels were not verified. A Playwright
browser installation is needed on platforms without a supported installed one.

Focused tests use captured real API shapes and controlled failures; browser
tests use the actual backend with no mocked financial computation. Actual
evidence, failures/corrections and screenshots: [release validation](RELEASE_VALIDATION.md).

No throughput benchmark or production accessibility audit was performed.
Response parsing/rendering remains O(P) in payload size; chart preparation is
O(N) in actual valuation count, with numeric canvas data and bounded table DOM.
Very large allowed payloads still consume browser memory. The backend remains
local/single-user, unauthenticated and price-return-only, with the existing
market-data, audit and statistical limitations. An observed transient disk-full
failure affected SQLite/trace writes; successful reruns do not establish its
external cause or remove the need for available local disk space.

Implementation references: [React effect guidance](https://react.dev/learn/you-might-not-need-an-effect),
[Vite local development](https://vite.dev/guide/), and [Vitest](https://vitest.dev/guide/).
Phase 9 completed the validated offline fallback; Phase 10 verified the final
local demonstration release. No further phase or provider integration is authorized.
