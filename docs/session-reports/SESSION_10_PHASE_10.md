# Session 10 - Phase 10

Date: 2026-11-03 (Asia/Calcutta).

## A. Session overview

**COMPLETE: final engineering validation and local demonstration release.**
Explicitly authorized Phase 10 only. Read the governing contracts, status,
Session 08/09 reports and actual importer, strategy/engine, analytics/auditor,
coordinator, persistence/service/API, frontend/config/test source. Established
the reported baseline before changes. No Phase 11 or new product scope.

Implementation/verification are AI-assisted. Technical acceptance does not
establish independent owner mastery; explanation/recreation remain pending.

## B. What was implemented

- `scripts/benchmark.py`: deterministic invented 250/1,000/5,000-bar inputs,
  operation-specific warm-up, five timed samples, raw timings/identities and
  bounded disposable SQLite. No optimization or production financial change.
- `scripts/verify_repository.py`: repeatable offline source/document/lockfile,
  boundary, credential-pattern, benchmark and final-report integrity checks.
- `frontend/e2e/dashboard.spec.ts`: explicit provenance inspection and fourth
  real workflow for three fixed backtests, independently calculated costs,
  audit status/evidence and zero-volume rejection. Existing workflows retained.
- README, [architecture](../ARCHITECTURE.md), [release evidence](../RELEASE_VALIDATION.md),
  [benchmarks](../BENCHMARKS.md), [demo](../DEMO_GUIDE.md),
  [limits](../KNOWN_LIMITATIONS.md), [resume/ownership](../RESUME_AND_INTERVIEW.md),
  D13, roadmap, status and relevant guide cross-references form the final package.
- Small raw benchmark/environment JSON is intentionally retained. Added ignored
  `.release-check/` for isolated setup; environments/builds/DBs/browser artifacts
  remain excluded. No staging/commit/branch/tag/remote/deployment action.

## C. Why this functionality exists

A working application needs reproducible setup, meaningful verification,
measured engineering behavior and honest demonstration claims. This phase
supplies that evidence without adding features or manufacturing a speed metric.
The final documents give the owner a short demonstration and bounded study path.

## D. Integration with the existing codebase

All **41 production backend source hashes are unchanged**, in both main and
fresh trees. No dependency, endpoint, schema, metric, adjustment, timing, sizing,
cost or train/test convention changed. No frontend portfolio calculation added.
Release scripts call existing public/core/application functions and the Store;
they are operator tools, not new application components.

Fresh setup copied 118 source/config/test/doc files instead of relying on a
nonexistent committed checkout or overwriting current work. New CPython venv,
editable install, clean npm lockfile install, full tests, actual production
browser and development proxy checks verified integration. Test databases are
separate from any user's saved research; occupied default servers left untouched.

## E. Technical concepts to study

Study isolated environments, editable packaging, direct pins versus transitive
resolution, Git-visible source versus generated state, and runtime/browser tests.
Connect `perf_counter_ns`, operation boundaries, warm caches, GC and median/range
to `measure`; do not turn five local samples into a scalability claim.
Understand why intended strategy parameters must be explicit in a reference test.

Independently recreate **`measure`** and **`fingerprints`**. Explain the engine
event loop, independent ledger audit, training selection before testing, saved
reproduction, React runtime schemas and stale-response handling. The focused
ten-area ownership checklist identifies one/two essential locations per topic.

## F. Financial and quantitative concepts to study

The release references use invented prices. Cost-bearing buy and hold: floor
((1000-2)/10.10) = 98 shares; notional 989.80, fee 2.00, cash 8.20; final equity
8.20 + 98*8 = **792.20**. Zero-cost buy and hold ends at 800 with 100 open shares.
Explicit SMA(2,3)/momentum(2) end at 910, flat. A zero-volume rejection followed
by a fresh buy leaves 83 shares/cash 4 and final equity **668**. No forced sale.

Training-selected lookback 2 still gives -54% held-out return from fresh $1,000,
with six indicator-only warm-up bars. No training P&L enters the test. Review
units, undefined statistics, price/dividend exclusion, unknown split evidence,
unverified session/liquidity facts, audit scope and held-out contamination.
No real-market, significance, generalization or profitability claim follows.

## G. Engineering decisions and tradeoffs

D13 preserves the modular monolith and financial core. Fresh source/venv and
lockfile installation demonstrate setup without destroying work. No unnecessary
global install, package/framework, provider or infrastructure was introduced.
Benchmarks exercise existing operations with explicit included/excluded work;
no bottleneck justified optimization during this final validation scope.

The historic ENOSPC/SQLite 503 remains unresolved, not declared fixed. Scoped
review found no concrete dead abstraction, unused direct dependency or duplicate
frontend accounting requiring refactor. Credential-pattern/boundary checks do
not replace an exhaustive security audit. Final output is a local demonstration
deliverable, not a published service or independent-owner authorship claim.

## H. Testing and verification

Exact clean setup, regression/startup commands, failures, environment, financial
test map and browser cases: [RELEASE_VALIDATION.md](../RELEASE_VALIDATION.md).

| Executed verification | Actual result |
| --- | --- |
| Backend baseline | 444 passed in 22.83s |
| Frontend baseline | 45 passed in 12.64s |
| Production browser baseline | 3 passed in 21.7s; build passed |
| Fresh backend full suite | 444 passed in 23.74s, no skips |
| Fresh frontend full suite | 45 passed in 11.63s, no skips |
| Extended fresh browser suite | 4 passed in 24.2s; build passed |
| Final main-tree browser suite, explicit provenance | 4 passed in 25.3s; build passed |
| Fresh npm installation / both pip checks | 110 packages installed; no broken requirements |
| Fresh development startup/proxy/import/backtest/reproduce | PASS on 8019/5179; default ports occupied, untouched |
| Actual benchmark execution | 75 timed samples: five operations, three sizes, five repeats; assertions passed |

Failures were investigated rather than hidden: first fresh pytest run had
56 passes/388 setup errors (32.20s); a one-test diagnostic confirmed WinError 3
because the command's basetemp parent was absent. Corrected it to the existing
sibling venv, then reran all tests. First extended browser run had 3 passes/1
failure (25.4s): a reference for SMA(2,3) had not overridden the actual 2/5 UI
default, correctly producing $628. Made the intended parameters explicit and
reran the complete suite. No production default/policy changed to pass tests.

Backend cases verify close-only/future-prefix isolation, next-open timing,
nonnegative cash/integer shares, rounding/costs, equity/ledger reconciliation,
undefined metrics, compatible references, no forced liquidation, training-only
selection and indicator-only warm-up. API cases verify limits, rollback,
unexpected failures, missing records, corrupted inputs and reproduction mismatch.
Valid real-browser results expose PASS/WARNING/NOT_ASSESSED and an empty FAIL
filter; tampered backend traces and UI component tests cover FAIL honestly.

Real installed Edge 156.0.4314.58, no financial mocks, isolated API/SQLite and
production frontend, desktop/mobile: uploads/provenance, all three backtests,
equity/trades/fills/rejections/costs/audit, four robustness modes, saved reopening,
both-service restarts, fresh reproduction and useful invalid-input rejection.
Desktop order-outcome and mobile saved-research screenshots were visually
inspected. No measured human demo duration or full accessibility certification.

Workspace/TEMP share C:. Free space observed from 3,202,330,624 bytes initially
to 1.01 GiB later; measured release-check tree 202.6 MiB, main dependencies
140.8 MiB, main browser artifacts 0.3 MiB. No ENOSPC/503 recurred; successful
SQLite/test/benchmark/browser writes do not explain the historical failure.
No global temp/user-data cleanup or speculative fix. Owned QA ports
8018/5178/8019/5179 checked stopped. Known sandbox restrictions used approved
external execution; no permission workaround was added to application code.

Final command `.\.venv\Scripts\python.exe scripts/verify_repository.py`: PASS.
Checked 129 project files, 51 Python AST parses, 12 JSON files, 141 local
Markdown links and per-file Git whitespace. Confirmed frontend lockfile/direct
Python declarations, 41 unchanged backend hashes, 29 core modules without
HTTP/persistence imports, 75 benchmark samples/script/source identities, excluded
generated files, no known credential-pattern match, empty data placeholders,
A-L/questions and all 11 roadmap phases complete. No staged files.

## I. Complexity and performance

Full methodology, raw samples/script/source identities and theoretical bounds:
[BENCHMARKS.md](../BENCHMARKS.md). At 5,000 bars, median import 92.446 ms, SMA
simulation 104.761 ms, five-run grid 1291.182 ms, source-backed audit 151.862 ms,
SQLite retrieval 51.416 ms. Five repeated measurements after one warm-up per
operation, Ryzen AI 9 HX 370/Windows/CPython 3.15.0, cached local workload.
No optimization, HTTP/browser/concurrency benchmark, throughput, production
capacity or improvement claim. Asset build stays 435.68 kB JS/27.52 kB CSS.

## J. Interview preparation

Five technical questions:

1. What did a fresh installation prove beyond the original passing tests, and
   why were source bytes and the installed dependency inventory recorded?
2. Why did the basetemp command fail, and how does that differ from a product
   defect or the earlier unexplained disk-resource failure?
3. How do warm-up, cached input, GC and included operation boundaries affect
   a median benchmark? What claims remain unsupported?
4. How do next-open event ordering, independent ledger checks and future-prefix
   tests provide different evidence of financial correctness?
5. How do real browser restarts and POST recomputation complement typed API,
   component tests and saved-result retrieval?

Three financial questions:

1. Why do the 98-share cost example and zero-volume rejection affect exposure,
   and why must open holdings remain distinct from closed trade statistics?
2. Why do training-only selection, indicator-only warm-up and fresh test capital
   still fail to establish generalization or eliminate selection bias?
3. Why are matching reproduction, scoped audit PASS and synthetic benchmarks
   insufficient to claim market truth, total return or real execution accuracy?

Independent exercise: before consulting `measure`, implement a tiny timing
sampler for a separate deterministic operation, excluding one warm-up and
retaining five raw durations. Manually check its median/range and explain what
is inside the timed interval. Keep practice separate; do not label generated
release tooling independent work. The broader document has ten technical/five
finance questions and five bounded exercises.

## K. Current project status

Original phases 0-10 COMPLETE, including Phase 9 offline alternative. Ready for
a local technical demonstration under documented environment and limits.
No known in-scope functional failure remains in executed checks. Synthetic-only,
single-user, corporate-action/session/liquidity/statistical/audit/reproduction
limits and historical disk observation remain explicit. No provider or public
deployment, committed/tagged release, or independent owner mastery claimed.
All work remains unstaged/uncommitted; owner study is pending.

## L. Next session

**STOP. The planned development roadmap is complete.** No Phase 11 is added or
proposed. Owner learning, independent recreation and honest contribution review
remain prerequisites for personally defending resume/interview claims. Any
future bug fix or scope change requires a new explicit task; no automatic
provider integration, new strategy, prediction or deployment work follows.
