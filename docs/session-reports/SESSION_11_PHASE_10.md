# Session 11 - Post-release Phase 10 validation

Date: 2026-11-03 (Asia/Calcutta). No Phase 11 is introduced.

## A. Session overview

**COMPLETE: explicitly authorized post-release real-market validation.** Read
the charter, roadmap, status, decisions and Session 10, then inspected data/
execution/cost/analytics/audit/experiment/persistence contracts, source, existing
offline assets and completed test coverage. Used the existing offline workflow
with two genuine Alpha Vantage public samples and documented split evidence.
No financial policy, architecture or application capability was changed.
Implementation and verification are AI-assisted; owner mastery is unverified.

## B. What was implemented

- `backend/tests/test_real_market_validation.py`: three tests parameterized over
  two private frozen samples, six cases. Import/source equality and eligibility
  failures; three-strategy/cost regressions with independent references and
  source-backed replay audit; robustness/API/SQLite/reopening/fresh reproduction.
- [REAL_MARKET_VALIDATION.md](../REAL_MARKET_VALIDATION.md): primary home for
  access/rights, instrument/feed/adjustment/coverage, raw/CSV/metadata identities,
  split checks, actual numerical/failed results, commands and limitations.
- README, limitations, status, roadmap, provider review/offline guide and D14
  updated to distinguish this success from earlier synthetic-only evidence.
- Private raw JSON, CSV, metadata, issuer HTML/receipts, preparation script,
  results and two SQLite copies retained under already ignored `.release-check/`.
  No provider data added to distributable fixtures. No production source change.

## C. Why this functionality exists

Synthetic reference tests establish controlled behavior but cannot exercise
real vendor observations or their provenance/corporate-action uncertainty.
This session supplies bounded genuine-input evidence while preserving strict
eligibility and lawful private retention. It does not extend the research model.

## D. Integration with the existing codebase

Raw fields are explicitly mapped without numeric transformation to the six-column
contract; `load_dataset_bytes` remains the sole importer. `run_experiment`,
`audit_simulation` and API/service/Store call the existing execution engine.
No second financial engine, schema, endpoint, SDK or runtime dependency added.
The 41 production backend file hashes and frontend source remain unchanged.
Private tests skip only when their directory environment variable is unset;
an explicitly supplied unavailable/changed snapshot fails.

## E. Technical concepts to study

Study source bytes versus normalized records, deterministic fingerprints,
public sample access versus account entitlement, HTTP 200 error envelopes,
environment-only credential discovery, opt-in fixtures and data licensing.
Connect rational rounding/reference formulas to Decimal cash and float metrics;
distinguish recomputation from cached retrieval. Recreate **`_half_up`** and
**`_check_metrics`** independently before comparing with the generated test code.

## F. Financial and quantitative concepts to study

Two 100-bar U.S. common-stock samples cover 2026-06-11..2026-11-02. Unadjusted
OHLC/raw volume, price return excluding dividends, no split processing, integer
budgeted next-open fills, no forced liquidation. IBM's source events were outside
the window; MSFT's failed provider split query remained unknown and its issuer
history supplied separate evidence. The automated auditor still does not certify
corporate-action truth or session completeness.

At $10,000, zero-cost buy and hold leaves 35 IBM shares/$237.10 cash and final
equity $9,074.95; MSFT leaves 25 shares/$214.25 cash and $12,892.25. Independent
single-purchase formulas agree. Strategies/costs/held-out comparisons have the
same assumptions. Short annualization is extrapolation, not statistical evidence.

## G. Engineering decisions and tradeoffs

D14 records the narrow authorized continuation. No personal provider credentials
were present in checked names, but published public demo access supplied two
usable daily samples. Prefer that permitted bounded path over new provider
infrastructure. Alpaca's longer-history alternative requires unavailable
authentication; no feed/entitlement test was invented.

Keep observations/evidence/database private because redistribution permission
was not established. This means the six cases need the retained local snapshot;
source checkout alone cannot reproduce them. Pinned raw/CSV/dataset hashes prevent
unreviewed moving samples from silently changing expectations. Issuer histories
support declarations without weakening D04 or upgrading automated audit scope.

## H. Testing and verification

Exact commands, identities, results, negative cases and scope:
[real validation](../REAL_MARKET_VALIDATION.md).

| Executed check | Actual result |
| --- | --- |
| Import | 100/100 rows each, raw-field equality; no discarded/rounded observations |
| Fixed runs | All three built-ins, zero and $1/10 bps costs, 12 runs total |
| Independent references | Buy-and-hold accounting and SMA/momentum targets exact; five metrics within 1e-12 tolerance |
| Source-backed audits/replay | No FAIL across the 12 fixed runs; scope limitations retained |
| Robustness | 20 grid runs per instrument, parameter/cost/two-period products; four training candidates plus reference, frozen selected held-out run |
| SQLite/reproduction | Four saved experiments across two DBs; exact retained CSV; reopened-app retrieval; four fresh economic/implementation matches |
| Corrected full backend suite | **450 passed in 25.24s**, all 444 existing tests preserved and passing |
| Absent private snapshot | Six clearly reported skips in 1.17s, no live/synthetic fallback |
| Frontend regression suite | **45 passed in 15.59s** |

Initial new suite: 4 passed/2 failed (3.72s), because the new test compared text
`10000.0000` with `10000.00`; corrected to numeric Decimal equality plus flat
cash/share assertions. No production serialization change. One inline reporting
command tried to JSON-encode ClosedTrade records as a count; fixed the reporting
expression, not financial code. All final reported results came from successful
reruns/extractions.

Sandbox network URLError, pytest private-temp WinError 5 and Vite spawn EPERM
were resolved by approved external execution. Interrupted sandbox suite is not
a passing baseline. Reading private pytest directories also required approved
external execution and an explicit two-database extraction check. No sandbox
restrictions were worked around in application code. No new browser suite,
OS-process restart, cross-platform or performance benchmark was executed.

Final `.\.venv\Scripts\python.exe scripts/verify_repository.py`: **PASS**.
132 project files/whitespace checks, 52 Python AST parses, 12 JSON files,
151 local Markdown links; 41 unchanged backend hashes, 29 independent core
modules and no staged files. Its original release checks still validate
Session 10; a separate executed check verified Session 11 is the latest report,
A-L order, five technical/three finance questions, six private receipt hashes,
two retained databases, four successful reproduction summaries and zero
Git-visible provider files. No staging/commit/tag/deployment action occurred.

## I. Complexity and performance

Existing import/simulation/analytics/audit complexity is unchanged. Direct slice
sum signal references use O(N*W) work, N=100/W<=20; this intentionally differs
from the production streaming implementation. Metrics use O(N) work/storage.
Each robustness grid evaluated 1,000 bars/20 runs; each train/test used 380
evaluation plus 120 warm-up bars/7 runs. Suite durations measure verification,
not financial-engine throughput or performance improvement. No new benchmark.

## J. Interview preparation

Five technical questions:

1. Why can HTTP 200 with an Information field never establish a successful split
   check, and what separate evidence supported MSFT's interval declaration?
2. Why retain both raw JSON and exact imported CSV, and which bytes/declarations
   change a dataset ID?
3. How does Fraction-based half-up rounding provide a reference independent of
   the production Decimal helpers without implementing a second engine?
4. Why do matching target/metric references, frozen regressions and source-backed
   ledger/replay audits provide different kinds of evidence?
5. How do reopened SQLite retrieval and observed coordinator calls demonstrate
   fresh reproduction, and what source/runtime restoration remains unproved?

Three financial questions:

1. Why does next-open integer-share buy and hold differ from a first-close quote
   return, even before considering dividends?
2. Why do interval split evidence and positive daily volume fail to establish
   exhaustive corporate-action truth, complete sessions or opening liquidity?
3. Why do two 100-bar samples and a training-selected held-out result fail to
   establish profitability, predictive accuracy, significance or absence of bias?

Independent exercise: using a separately permitted short file, manually tabulate
one budgeted next-open purchase with commission/slippage and five closing equity
values. Calculate cumulative return and maximum drawdown before using QuantLab;
explain any assumption difference. Do not copy private data into a public repo
or label this AI-assisted validation independent work.

## K. Current project status

Original phases 0-10 remain COMPLETE. Requested post-release validation COMPLETE
for the documented IBM/MSFT samples. No known in-scope failure remains in final
executed checks. Limited sample/history/source/feed, private-fixture availability,
price-return/corporate-action/session/liquidity/statistical/reproduction and
existing platform/reliability/ownership limits remain. No product provider,
live trading, deployment or profitability claim. No staged/committed baseline.

## L. Next session

**STOP after this validation.** No new phase, provider adapter, strategy,
infrastructure or deployment is proposed or authorized. Preserve the ignored
private snapshot/evidence/database for reruns. Any extension to history,
instruments, data rights or corporate-action modeling needs a separate explicit
task and its applicable evidence/decision review; owner study can continue.
