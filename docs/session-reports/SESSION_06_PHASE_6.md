# Session 06 - Phase 6

Date: 2026-11-02 (Asia/Calcutta); continued the authorized Session 06 work.

## A. Session overview

**Objective:** bounded robustness experiments with honest chronological testing.
**Status: COMPLETE.** The user's Session 06 instruction explicitly authorized
Phase 6 and a small indicator/evaluation separation change. Read the governing
documents, Phase 3-5 reports, data contracts and existing interfaces/tests;
verified the 347-test baseline before implementation. The continuation finished
verification and documentation. No Phase 7 work was started.

Implementation and verification are AI-assisted. Independent owner study and
recreation remain work to do, not an accomplishment inferred from this code.

## B. What was implemented

Paths below are relative to the repository root.

| Added/modified source | Responsibility |
| --- | --- |
| `backend/src/quantlab/experiments/models.py` | Immutable periods, costs, workloads, runs, comparisons, source manifest and training selection/results |
| `backend/src/quantlab/experiments/grids.py` | `sma_grid`, `momentum_grid`, existing-config validation, canonical order and 100-config limit |
| `backend/src/quantlab/experiments/runner.py` | `_plan`, `run_experiment`, `_select_training`, `run_train_test`; atomic execution, reference deltas and workload reservation |
| `backend/src/quantlab/experiments/reproducibility.py` | `source_snapshot`: exact local package `.py` hashes and manifest hash, Python version |
| `backend/src/quantlab/experiments/__init__.py` | Public experiment API/version 1.0.0 |
| `backend/src/quantlab/execution/engine.py`, `models.py`, `__init__.py` | Engine 1.3.0, paired prior warm-up bounds, observed history metadata, public preflight counts; existing financial loop reused |
| `backend/src/quantlab/audit/trace.py`, `auditor.py`, `accounting.py` | Audit 1.1.0 warm-up evidence, current replay and unchanged 1.2/1.3 cost-math support |
| `backend/tests/test_experiments.py` | 31 grid, budget, comparison, warm-up, selection, leakage and failure cases |

Added [experiment contract](../EXPERIMENT_CONTRACT.md) and this report; amended
D08/D09 and updated status, roadmap, execution/audit/analytics contracts and
README. No existing test cases, strategies, metrics, data fixtures, dependency
or package configuration changed. No HTTP/database/frontend/provider exists.

## C. Why this functionality exists

A single backtest hides sensitivity to parameters, costs and dates. Structured
repeated runs expose those choices while retaining their accounting, warnings
and audit evidence. A frozen training choice can be evaluated honestly on later
data, including disappointing performance, without selecting a test winner.

## D. Integration with the existing codebase

Validated shared Dataset + built-in configurations + periods/costs -> preflight
all work -> existing `simulate` -> existing `analyze_simulation` -> existing
`audit_simulation` without replay -> immutable comparison/result records.
Comparisons link run IDs; each reference report/trace is stored once. The
coordinator has no persistence or delivery dependency and never mutates input.

The sole engine extension feeds explicitly prior closes to fresh indicator
state before creating the flat portfolio. Discard those targets; retain no
warm-up decisions, orders, fills or valuations. Next-open trading then uses the
unchanged loop. Default calls still start indicator history inside the selected
window. Engine/audit version and new metadata/finding fields change explicitly.

## E. Technical concepts to study

- Cartesian products with atomic validation; canonical keys versus input order.
- Preflight planning and resource reservation before expensive side effects.
- Immutable records and ID references that avoid duplicated simulation traces.
- Separating indicator state, pending intents and portfolio/valuation state.
- SHA-256 content manifests versus Git labels, archives and executable replay.
- Deterministic selection, undefined metrics and isolated Decimal arithmetic.

Independently recreate **`_select_training`** and **`_plan`** after reading their
tests. Be able to explain `run_train_test`, the warm-up loop in `simulate`, and
`check_warmup`; copying AI-assisted code is not independent recreation.

## F. Financial and quantitative concepts to study

Training selects among tried parameters and therefore can overfit. Testing
measures the frozen choice on later, nonoverlapping observations. Repeatedly
redesigning a grid after seeing test results contaminates that test; one held-out
period is not proof of generalization, significance or future profit.

The reference starts with $1,000. Momentum lookbacks 1 and 2 finish training at
$1,222 and $1,810; lookback 2 wins at **+81%**. A separate buy-and-hold reference
ends at $2,000 but is not a candidate in this request. Testing begins with fresh
$1,000, not $1,810. The frozen strategy buys 45 shares at $22 then sells at $10,
finishing at **$460 / -54%**. Six warm-up closes contribute indicator history,
not test wealth or return observations. Test has three valuations/two returns.

Costs alter integer affordability: in the rising reference, zero costs yield
$1,100 versus $1,079 with $2 commission and 100 bps slippage, a **-$21 / -0.021**
cumulative-return difference. In a falling reference, $2 commission reduces
exposure and leaves $548 versus $500 with zero fees. This is not evidence that
fees improve trading; a monotonic return assertion would be wrong for that path.

Keep subperiod lengths visible. Price-only returns exclude dividends/actions;
final holdings remain open, with no invented sale/fee. Existing drawdown,
annualization, numeric-range and undefined-statistic conventions are preserved.

## G. Engineering decisions and tradeoffs

- D08/D09 amendments document authorization and exact policies. Use built-ins
  and existing functions rather than another engine or general optimizer.
- All-or-nothing requests: invalid/duplicate configs, windows, costs, budgets,
  runtime/analysis errors or audit FAIL return no partial success. Ordinary
  order rejections remain valid outcomes. Undefined training scores abort.
- Sort configurations canonically; preserve requested period/cost order. Rank
  only training cumulative return with stable canonical ties, including equal
  reported float values. Benchmark-only runs cannot win. No test ranking.
- Count references and warm-up against 100 configs/1,000,000 bars. Reserve
  worst-case test work before training. A buy-and-hold winner may use fewer
  actual runs; report both counts. The reservation deliberately stays conservative.
- Test warm-up uses only the training interval; exclude intervening gap bars.
  A cold option is explicit. No pre-test intent is carried into the first open.
- Record exact local package source hashes with no clean Git claim. This is
  identification, not source/input retention or restoration. Audit original
  source restoration and unsupported biases remain NOT_ASSESSED.
- No caching, concurrency, new infrastructure, strategy, indicator or dependency.

## H. Testing and verification

Actual repository-root PowerShell commands used the existing environment.
Pytest ran with approved execution outside the sandbox because of the previously
established private temporary-directory restriction; no application workaround.

```powershell
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-phase6-baseline
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-phase6-integration
& '.\.venv\Scripts\python.exe' -m pytest -q backend/tests/test_experiments.py --basetemp=.venv/pytest-phase6-experiments
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=.venv/pytest-phase6-full
& '.\.venv\Scripts\python.exe' -m pip check
& '.\.venv\Scripts\python.exe' --version
```

Baseline: **347 passed in 7.69s**. Engine/audit integration regression:
**347 passed in 7.02s**. Initial experiment suite: **29 passed in 2.70s**.
After two additional audit/reference cases, full suite: **378 passed in 12.69s**,
exit 0, including all 347 prior cases and 31 new cases. No test failures were
observed in these Phase 6 runs. `pip check`: **No broken requirements found.**
CPython 3.15.0, pytest 9.2.0; Python 3.12 remains untested. No install occurred.

Executed evidence covers all 20 requested categories:

- Valid SMA/momentum grids, invalid pairs/bool/thresholds/duplicates, deterministic
  reverse-input outputs, 100-config limit including references, exact 1,000,000
  planning boundary, over-budget rejection before simulation, cost/period products
  and combined train/test/reference/warm-up reservations.
- Hand-calculated cost/final-equity/return/drawdown deltas, explicit first-cost
  reference order and nonmonotonic fee example; same dataset/capital/cost labels,
  unequal/invalid/empty/one-observation subperiod handling and open final holdings.
- Strict chronology, training-only selection and reference exclusion, frozen
  test configuration, no training holdings/P&L, no pre-test fills/pending intent,
  excluded warm-up valuations/returns, stable ties, cold indicators and gap exclusion.
- Changed test prices leave training decisions/fills/metrics/selection unchanged;
  undefined candidate score aborts before test execution; test-tagged rankings
  cannot enter selection. Training gains/test losses match the independent example.
- Missing/bad warm-up evidence, invalid requested bounds and tampered warm-up
  counts/pre-test records yield scoped NOT_ASSESSED/FAIL findings. Valid warmed
  current-engine replay passes. Selected buy-and-hold reuses its test reference.
- Runtime failure returns no partial result; input Dataset remains unchanged;
  source-manifest hash independently agrees, caller Decimal context cannot alter
  outputs, strict JSON conversion emits no NaN/Infinity, unsupported overfitting
  stays NOT_ASSESSED. All Phase 1-5 regressions pass.

Installed-package offline smoke **PASS** using the existing synthetic fixture:
six runs, 18 evaluated bars, no warm-up or audit FAIL; reverse grid input gives
equal results and strict JSON conversion succeeds. Experiment/engine/audit
versions: 1.0.0 / 1.3.0 / 1.1.0. Source manifest covers 30 package files; hash
`12038e328acb759eaf73643c7e8a06a6f722c6ac3270d2ea8e0785913e3f67fc`.
Overfitting remains NOT_ASSESSED. No real market data was used.

Final inline document/source verification **PASS**: 63 project files, 36 Python
AST syntax checks, 58 local links/anchors, UTF-8/LF/final newlines/trailing
whitespace and Git whitespace including untracked files. A-L/questions, all
11 phase statuses, absent Phase 7 modules and empty placeholders passed. The
first checker treated Git's default LF-to-CRLF conversion warnings on two root
files as failures; reran with command-local `core.autocrlf=false` and
`core.eol=lf`, without changing files or Git settings. No source changed after
the final 378-test run.

## I. Complexity and performance

For R runs, N imported bars, A charged evaluation+warm-up bars and S source
bytes: O(R*N + A + S) expected time, plus bounded configuration/training sorting.
Preflight, simulation and audit rescan the shared Dataset; this is explicit,
not hidden by the aggregate bar budget. The cap is not a wall-time bound.
Reports use O(A) trace space, with O(N) temporary source indexes and lightweight
jobs/bar references; no Dataset copy per configuration. Warm-up creates no output
trace. Existing fixed-numeric-size qualifications apply to strategy arithmetic.
No throughput benchmark, optimization claim, cache or worker was introduced.
Pytest duration measures verification only.

## J. Interview preparation

Five technical questions:

1. How does preflight count Cartesian products, shared references and worst-case
   test work before running any strategy?
2. Why must indicator state be distinct from cash, positions, pending orders
   and valuation history when testing a warmed strategy?
3. How do canonical ties and undefined-score rejection keep selection reproducible?
4. What do immutable run-ID references save, and why is this different from caching?
5. What can a source manifest establish, and which original bytes/environment
   details are still needed to reproduce a run?

Three financial/quantitative questions:

1. Why can a training winner lose out-of-sample, and how does repeated inspection
   contaminate a supposedly held-out test?
2. How can higher fees leave greater final equity on a particular losing path
   without making fees economically beneficial in general?
3. Why must unequal subperiod lengths, open holdings, excluded dividends and
   short-sample annualization remain visible in strategy comparisons?

Independent exercise: write a standalone workload estimator taking candidate
count, reference inclusion, evaluation lengths and warm-up length. Hand-check
exact/over-budget cases and a shared buy-and-hold reference. Reject an entire
request rather than truncating. Explain the conservative test reservation;
write the solution before consulting `_plan` and keep practice separate.

## K. Current project status

Phases 0-6 COMPLETE; 7-10 NOT STARTED and unauthorized. No known in-scope failure
remains in executed checks. Core financial rules and unsupported audit limits
remain. Statistical significance/generalization, authoritative market truth,
original source/input archive restoration and Python 3.12 compatibility are
unverified/unimplemented. Full-source scans can dominate tiny-window runs on
large inputs; no measured performance claim exists. Files remain unstaged and
uncommitted with no branch/remote changes. Independent owner learning is pending.

## L. Next session

Proposed Session 07 / Phase 7 **only after explicit authorization**: SQLite
persistence and REST APIs wrapping the verified core. Review source/input byte
retention versus fingerprints, serialization of Decimal/date/undefined metrics,
schema versioning, transaction rollback and error boundaries. Acceptance:
save/retrieve reproducible experiments with explicit retained-evidence limits;
test initialization, validation, unknown IDs and failed writes; preserve core
independence and regressions. No Phase 7 implementation is authorized or present.
Stop after Phase 6.
