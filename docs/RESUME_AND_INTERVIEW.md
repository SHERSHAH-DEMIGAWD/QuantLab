# Resume and interview preparation

The project is AI-assisted. Passing tests establishes software evidence, not
personal mastery. Before using any statement, revise it to describe your actual
contribution and only retain claims you can explain and independently modify.
Do not imply that you independently authored the generated implementation.

## Candidate wording after ownership review

- Developed an AI-assisted local strategy-research application with a Python
  financial core, FastAPI/SQLite persistence and a React/TypeScript dashboard,
  exposing inspectable backtests, integrity evidence and saved reproduction.
- Implemented and validated explicit next-open simulation, Decimal transaction
  accounting and bounded experiments with training-only parameter selection;
  demonstrated synthetic workflows through backend, frontend and real-browser
  tests. Replace “implemented” with your actual role if you cannot own that work.
- Measured import, simulation, bounded grids, audit and SQLite retrieval on
  deterministic 250/1,000/5,000-bar inputs using repeated local timings. Describe
  the median methodology and machine limits; claim no optimization or scale gain.

Evidence: [release checks](RELEASE_VALIDATION.md), [benchmarks](BENCHMARKS.md),
[architecture](ARCHITECTURE.md). Use exact current test counts from the release
report; do not convert a test count into a coverage percentage or market guarantee.
The synthetic suite remains in place; subsequent [limited historical validation](REAL_MARKET_VALIDATION.md)
additionally verified IBM/MSFT, 100 raw daily bars each for 2026-06-11..2026-11-02,
through existing research and persistence workflows. Private observations are
excluded from the repository; this does not demonstrate market prediction skill.

Do **not** claim profitable trading, historical alpha, live-market validation,
broker execution accuracy, complete bias elimination, certified data adjustments,
production deployment, unlimited scalability, independent authorship or a
performance improvement. No provider integration was delivered. Do not present
the invented -20%/-54% examples as market backtests.

## Minimum ownership checklist

Mark each only after explaining the code and making a small independent change.

| Area to understand | Essential locations | Owner done |
| --- | --- | --- |
| OHLCV/metadata validation and identity | `backend/src/quantlab/data/loader.py`, `identity.py` | [ ] |
| Close-only rules and indicator warm-up | `backend/src/quantlab/strategies/rules.py`, `execution/engine.py` | [ ] |
| Next-open orders, fills and state | `backend/src/quantlab/execution/engine.py`, `models.py` | [ ] |
| Decimal sizing/rounding/costs | `backend/src/quantlab/execution/costs.py`, `engine.py` | [ ] |
| Equity/trade metrics and undefined values | `backend/src/quantlab/analytics/equity.py`, `trades.py` | [ ] |
| Evidence-backed audit and unknowns | `backend/src/quantlab/audit/auditor.py`, `accounting.py` | [ ] |
| Training-only selection and test separation | `backend/src/quantlab/experiments/runner.py`, `models.py` | [ ] |
| Retained-input reproduction | `backend/src/quantlab/application/service.py`, `experiments/reproducibility.py` | [ ] |
| SQLite transactions and HTTP validation | `backend/src/quantlab/persistence/store.py`, `api/boundary.py` | [ ] |
| React request/state/result workflow | `frontend/src/pages/Research.tsx`, `api/client.ts` | [ ] |

Also explain `ResultView.tsx`, runtime schemas, `useRemote`, exact money text,
approximate chart coordinates and the browser restart tests. Essential finance:
signal versus order/fill, OHLCV versus intraday paths, adjusted versus raw prices,
dividend exclusion, cash/equity/P&L, fees/slippage, annualization/Sharpe, audit
scope, survivorship, overfitting and held-out contamination. Use actual example
numbers and the contract definitions, not slogans.

## Ten technical questions

1. A strategy sees Jan 2's close. Which open may execute its new order, and how
   do the streaming rule interface and tests prevent access to future prices?
2. How does budgeted sizing handle a gap or subcent price without negative cash,
   and why are affordability and rounded debit both checked?
3. Where does Decimal remain exact, where do statistics become floats, and why
   must the dashboard preserve original strings rather than recompute money?
4. What can an independent ledger fold detect that rerunning the same engine
   may miss? What does neither prove without original source evidence?
5. How are invalid rows, duplicate keys and unknown metadata handled, and why
   must successful import remain separate from execution eligibility?
6. How does train/test planning reserve work before selection, exclude gap
   warm-up bars and prevent training cash/positions from entering test metrics?
7. Why compute before inserting the experiment, and how do transactions,
   foreign keys and checksums address different persistence failures?
8. How do GET retrieval and POST reproduction differ, and why can economic
   outputs match when implementation identity changes?
9. Why are TypeScript types insufficient at the HTTP boundary, and how do refs,
   abort signals and state revisions address duplicate writes/stale reads?
10. How do benchmark warm-ups, repeated samples, caching, serialization and
    included grid/audit work affect interpretation of a measured median?

## Five quantitative-finance questions

1. Why can consistently raw prices still be ineligible, and why does a failed
   event request establish nothing about split absence?
2. What is the difference between price return and total shareholder return,
   and why can an open profitable position have no closed winning trade?
3. Why do short-period annualization, sample volatility and Sharpe require
   explicit conventions/unavailable states rather than attractive substitutes?
4. How can higher transaction costs reduce a loss through integer exposure,
   and why is monotonic fee sensitivity not guaranteed?
5. Why can a strong training winner, one held-out result and matching replay
   still provide no evidence of significance, survivorship coverage or future alpha?

## Five independent exercises

Do these separately after studying; they are proposed practice, not implemented
features or evidence of completed ownership.

1. Recreate `fingerprints` from its documented canonical format and compare
   against one handwritten expected input/hash, including metadata key reordering.
2. Recreate the fee/slippage calculation for a single fill with independent
   Decimal arithmetic; include one half-cent fee edge and an affordability case.
3. Write a four-valuation reference calculation for returns/drawdown, then explain
   when volatility/Sharpe are unavailable. Do not call production metric helpers.
4. Build a small separate delayed-request React selector; prove a stale response
   cannot replace a newer selection. Add one focused behavior test.
5. Add a read-only source-name display in a practice copy of the dataset list,
   explain the API payload it needs, and preserve validation/error behavior.

Before an interview, run the [demo](DEMO_GUIDE.md), explain one deliberate failure,
recreate one backend and one frontend helper, and state the unresolved limits
without claiming that AI-assisted work was independent.
