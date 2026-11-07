# Project status

Updated: 2026-11-04 (Asia/Calcutta).

- **Current phase:** 10 - complete; authorized handbook PDF edition finished.
- **Status:** COMPLETE; Session 14 PDF export and layout verification completed.
- **Completed phases:** 0-10. Phase 9 used the validated offline alternative.
- **Further planned phases:** none. Stop after Phase 10; no Phase 11 authorized.
- **Readiness:** local technical demonstration; owner learning remains pending.

## Actual application

One local Python/FastAPI/SQLite application with a React/TypeScript dashboard:
Datasets, Backtest, Experiments and Saved Research. It validates/retains original
CSV/effective metadata, executes three built-ins and four robustness workflows,
shows actual equity/trades/orders/audit evidence, and reopens/reproduces saved
research across restarts. Architecture: [ARCHITECTURE.md](ARCHITECTURE.md).

Phase 9 delivered the working offline path. Session 11 used that path with
private Alpha Vantage public historical samples: IBM/MSFT, 100 daily bars each,
2026-06-11..2026-11-02, with supported interval split evidence. All three
strategies, costs, source-backed audit, bounded robustness, SQLite retention and
fresh reproduction passed. No product provider adapter or live quote was added.
Source/access/failures/commands: [real validation](REAL_MARKET_VALIDATION.md).

All 41 production backend package files remain unchanged in Phases 8-10; no
financial/API/schema/dependency correction was needed. Phase 10 added release
tools, stronger browser checks, measured evidence and final documentation.
No provider, strategy, live trading or deployment was added.

Session 11 added six opt-in private-data test cases and documentation only;
the 41 production backend files and frontend source remain unchanged.
Full backend: **450 passed in 25.24s** (444 existing + six real-data cases).
Frontend: **45 passed in 15.59s**. No browser suite was rerun in Session 11.

Session 12 prepared the public package, synthetic screenshots and read-only
publication checks; redacted owner paths and verified a disposable source-only
Git clone with fresh dependencies. Clone: **444 backend passed/six private skips**,
**45 frontend passed**, **four browser workflows/build passed**. All private
real observations remain ignored. Root still has no initial commit or remote;
no history rewrite, GitHub creation or push. License choice remains pending.
Evidence/recommended steps: [publication readiness](PUBLICATION_READINESS.md).

## Executed release evidence

Fresh source copy and isolated CPython 3.15.0 environment installed successfully;
frontend npm ci installed the lockfile; both pip consistency checks passed.
Windows 11, SQLite 3.53.4, Node 24.15.0/npm 11.12.1, Edge 156.0.4314.58.
Python 3.12 and other platforms/browsers remain untested.

- Backend baseline: **444 passed in 22.83s**; fresh full suite: **444 passed in 23.74s**.
- Frontend baseline: **45 passed in 12.64s**; fresh suite: **45 passed in 11.63s**.
- Browser baseline: 3 passed in 21.7s; extended fresh suite: 4 passed in 24.2s;
  final main-tree suite: **4 passed in 25.3s**, with successful production build.
- Real workflows include all strategies, explicit costs/rejected orders, audit,
  robustness, train/test separation, saved restart/reproduction and desktop/mobile.
- Fresh backend/Vite development startup and proxy/import/reproduction succeeded
  on alternate loopback ports; occupied default services were left untouched.
- Benchmarks: 250/1,000/5,000 invented bars, five samples per operation after a
  warm-up. Raw samples/environment/script/source identities are retained.

Commands, corrected validation-harness errors, financial/failure test map and
reliability investigation: [RELEASE_VALIDATION.md](RELEASE_VALIDATION.md).
Measured medians and limitations: [BENCHMARKS.md](BENCHMARKS.md).

## Remaining limits and ownership

No known in-scope functional failure remains in executed checks. This is local,
single-user, short real-sample evidence with price-return/corporate-action/session/
liquidity/statistical/audit limits. The historical SQLite 503/browser ENOSPC
remains unexplained; it did not recur. Source/TEMP/browser/SQLite share finite
local disk; passing reruns do not prove a permanent fix. Complete consolidated
limits: [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md). Financial contracts retain
their detailed semantics.

Owned QA ports 8018/5178/8019/5179 stopped. Environments, builds, databases and
browser artifacts are ignored; raw/processed placeholders remain empty. Small
synthetic fixtures and measured benchmark JSON are intentionally retained.
No staging/commit/branch/remote/tag/deployment changes; no committed baseline.

Implementation/verification are AI-assisted. Independent explanation/recreation
and honest resume contribution review are pending. See the focused
[ownership checklist](RESUME_AND_INTERVIEW.md) and [demo](DEMO_GUIDE.md).

## Complete project handbook

Session 13 added the [complete handbook](QUANTLAB_COMPLETE_HANDBOOK.md): 20
source-grounded chapters, worked accounting/statistical/train-test examples,
architecture diagrams, concurrency/security limits, interview answers and an
eight-week learning plan. This was documentation only; application, financial,
test, dependency and configuration bytes remain unchanged. Prior full-suite
results are labeled as recorded evidence, not new suite runs.

Source review and a focused runtime example confirmed a stale assumption string
in `analytics/benchmark.py`: the direct comparison helper honors explicit earlier
indicator warm-up but still says only selected-window closes are seen. Actual
warm-up fields/engine behavior are explained; no ledger defect was demonstrated
and no code correction was authorized in this task. Owner mastery remains pending.

The user's format follow-up was completed in Session 14: a full 72-page PDF
edition at local generated path `output/pdf/QUANTLAB_COMPLETE_HANDBOOK.pdf`,
with linked contents/bookmarks, wrapped tables and three vector diagrams.
All 1,379 source text blocks/cells checked against extracted PDF text; 72 pages
rendered for review. The Markdown source remains unchanged. Generated exports
are ignored, so public source/setup does not depend on the local PDF or tools.

Latest report: [Session 14 / handbook PDF](session-reports/SESSION_14_PHASE_10.md).

## Stop condition

The original development roadmap is complete. No next phase is proposed or
implemented. Owner study can continue independently; future changes require a
new explicit task. Stop after this requested handbook task; GitHub creation/push
requires explicit approval. No provider integration or deployment starts automatically.
