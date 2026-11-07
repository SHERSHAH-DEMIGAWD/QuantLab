# Session 00 - Phase 0

Date: 2026-11-01 (Asia/Calcutta).

## A. Session overview

- **Session:** 00.
- **Phase:** 0 - project charter, technical specification, and foundation.
- **Objective:** initialize a safe, bounded, explainable project and prepare a
  small first implementation phase without implementing business functionality.
- **Completion status:** COMPLETE; foundation acceptance criteria met.
- **Actual progress:** inspected the supplied request and existing repository;
  wrote project memory, contracts/proposals, acceptance criteria, guidance, and
  an empty directory skeleton. No Phase 1 code was started.

## B. What was implemented

Only documentation and repository foundation were introduced:

| Files | Actual responsibility |
| --- | --- |
| `README.md` | Entry point, present capabilities, structure, environment limits |
| `AGENTS.md` | Future-session authorization, scope, evidence, and reporting rules |
| `.cursor/rules/quantlab-workflow.mdc` | Always-applied pointer to the same project guidance |
| `.gitignore`, `.gitattributes` | Keep local data/secrets/output out of Git; consistent text endings |
| `docs/PROJECT_CHARTER.md` | Permanent scope, architecture, standards, and report format |
| `docs/ROADMAP.md` | Original phases 0-10, dependencies, outputs, and acceptance evidence |
| `docs/DECISIONS.md` | Established choices, proposed data/execution/metric contracts, approval gates |
| `docs/PROJECT_STATUS.md` | Actual implementation state, limitations, authorization, next task |
| This report | Work evidence, learning map, and independent exercises |
| `.gitkeep` in `backend/src/quantlab/`, `backend/tests/fixtures/`, `frontend/`, `data/raw/`, `data/processed/` | Preserve empty directories without application scaffolding |

There are no application functions, classes, implemented modules, dependencies,
datasets, financial calculations, APIs, or UI components. This is AI-assisted
foundation work, not evidence that the owner independently built a platform.

## C. Why this functionality exists

The project needs a durable boundary between research intentions and verified
functionality. Explicit phase authorization and persistent records prevent code
growth from outrunning the owner's understanding. Precise input and execution
proposals make later tests possible and expose choices that could otherwise
silently distort results. The empty skeleton prepares locations without
creating abstractions the next phase does not need.

## D. Integration with the existing codebase

Before this session, the folder contained only an initialized `.git` directory:
no commits, tracked files, remote, source code, or unrelated project. Existing
Git state was retained; no initial commit, branch change, or remote was created.

The new documents link to one another, with one primary home for scope,
phase acceptance, contracts, current state, and chronological evidence. Agent
guidance makes the required reading and stop rule discoverable in later chats.
The planned flow is local input -> validated identified data -> strategy and
daily execution -> analytics/audit -> experiments -> persistence/API -> UI.
This flow is a design, not executed application behavior.

## E. Technical concepts to study

This is the initial learning map; later phases teach their own implementation
details instead of generating a full textbook now.

| Concept | Connection to this session | Learning check |
| --- | --- | --- |
| Module boundaries | Charter separates core research from HTTP/SQLite/React | Explain why a simulator should run in a unit test without a web server |
| Data contracts and invariants | D03 gives field rules; D05 gives cash/share/timing rules | Turn one OHLC rule into a good input and a failing input |
| Deterministic identity | D03 distinguishes exact source bytes and semantic metadata | Explain why two different CSV line endings can produce different IDs |
| Git working tree versus history | The repository exists but has no commit | Explain why `git log -1` failed and why untracked files are not committed |
| Dependency/environment isolation | D02 defers packages and records the actual interpreter | Explain why having Python installed does not prove pytest/pandas compatibility |
| Acceptance versus execution evidence | Roadmap criteria and report H have different jobs | Distinguish a proposed test from an observed successful test |

No production function can be recreated yet. In Phase 1, the owner should be
able to recreate the price-consistency validator and source SHA-256 calculation
after studying the actual implementation. Their eventual names are not fixed.

## F. Financial and quantitative concepts to study

- A daily OHLCV bar summarizes a session. It does not reveal the sequence of
  intraday prices or liquidity available for an opening fill. Calendar gaps
  cannot automatically be counted as missing trading sessions.
- A close-based decision cannot buy at that same historical open. D05 proposes
  first-close decisions and earliest next-session-open fills, keeping the
  signal's information separate from the execution price used for sizing.
- Integer shares leave residual cash: the D05 hand example spends $927 for
  nine shares at $103 from $1,000, leaving $73. At a $105 close, equity is
  $1,018. This is worked arithmetic, not simulator output.
- A split changes share units; dividends change total shareholder wealth.
  D04's proposed event-free unadjusted execution and dividend exclusion avoid
  unsupported total-return claims but restrict usable real-data research.
- Compounding differs from averaging: equity 100 -> 110 -> 99 has +10% and
  -10% daily returns but a -1% cumulative return. Drawdown from 110 to 99 is
  10%. D07 records the full proposed metric conventions for later review.

No financial metric, strategy performance, bias elimination, or investment
conclusion has been implemented or verified. The calendar and split references
in D03-D04 motivate the limitations; they do not certify any supplied dataset.

## G. Engineering decisions and tradeoffs

- Chose a modular monolith and empty source locations; rejected service
  infrastructure and prebuilt class hierarchies because this phase needs none.
- Chose one decision log for contracts and review gates rather than many
  overlapping architecture/finance specifications.
- Proposed strict atomic import with diagnostics rather than hidden row
  repair. This improves auditability at the cost of more explicit input work.
- Proposed exact-byte provenance plus metadata identity; economically identical
  files may intentionally have different IDs. Hashes prove identity, not truth.
- Exposed the cost-phase sequencing issue: Phase 2 will be visibly zero-cost
  and reject nonzero settings until Phase 4 implements them.
- Left budgeted order sizing, rounding, corporate actions, immediate sale-cash
  reuse, strategy initialization, and annualization as reviewable proposals.
  None is a silently approved or implemented financial model.

Detailed alternatives and gate timing are recorded once in
[DECISIONS.md](../DECISIONS.md). No major scope expansion was made.

## H. Testing and verification

No application tests were written or run because Phase 0 contains no code.
Document and repository checks are appropriate here; no pytest, server,
database, browser workflow, or benchmark result is claimed.

Commands actually executed during initial inspection (private attachment path
redacted for publication; the attachment is not a runtime dependency):

```powershell
Get-Content -LiteralPath '<private-original-specification-attachment>' -Raw
Get-ChildItem -Force | Select-Object Mode,Name
git status --short --branch
git rev-parse --is-inside-work-tree
git log -1 --oneline
git ls-files
git remote -v
python --version
py --list-paths
node --version
git --version
```

Observed: only `.git` existed; `git status` reported no commits on `master`;
`rev-parse` returned true; tracked-file and remote listings were empty.
`git log -1 --oneline` reported that the branch has no commits. This is the
expected empty-history condition, not a failed application check. Python was
3.15.0; Node was v24.15.0; Git was 2.56.0.windows.2. No ancestor `AGENTS.md`
was found in the inspected path chain. The create-rule skill was read to set
up concise always-applied project guidance.

Final checks actually executed:

```powershell
git status --short --untracked-files=all
git diff --check
git check-ignore --no-index -v -- data/raw/_phase0_probe.csv data/processed/_phase0_probe.json .env .env.local backend/__pycache__/_phase0_probe.pyc frontend/node_modules/_phase0_probe.js
git ls-files
git remote -v
```

Inline Python checks were run using PowerShell here-strings piped to `python -`.
The document checker enumerated all non-Git files, compared the inventory to
the explicit 15-file foundation, decoded UTF-8, checked LF/final newlines and
trailing whitespace, confirmed five empty placeholders, resolved all 15 local
Markdown links/anchors, checked report headings A-L, verified the 11 numbered
roadmap entries, counted five technical plus three finance interview questions,
and checked the always-applied guidance setting. **All checks passed.**

A separate inline Python check called `git check-ignore --no-index --quiet --
<path>` for six generated/secret paths and four trackable placeholder/fixture/
example paths, asserting exit codes 0 and 1 respectively. **All ten checks
passed.** Probe names were hypothetical; no probe files were created.

`git diff --check` produced no diagnostics but does not cover these untracked
files by itself. The Python whitespace check covered every file. An additional
`git -c core.autocrlf=false diff --no-index --check -- /dev/null README.md`
probe produced no diagnostics and exit 1, indicating a nonempty file differs
from the empty input, not a whitespace failure. The final audit also applies
that command to every foundation file and checks completion/authorization
consistency. Its result is recorded in the final audit paragraph below.

The working tree contains the 15 new untracked foundation files; tracked-file
and remote listings remain empty. No files were staged or committed. Manual
review corrected the proposed eligibility text to require raw volume alongside
unadjusted OHLC and removed a redundant hardcoded current phase from persistent
agent guidance. No business implementation was introduced.

External NYSE/SEC references were consulted through web search; a recursive
external-link availability audit is not claimed. No third-party packages were
installed. **Final audit: PASS.** The recheck confirmed all 15 files, five empty
placeholders, 15 local links/anchors, A-L headings, 11 phases, eight interview
questions, all-file text/Git whitespace checks, ten ignore-policy cases, and
consistent COMPLETE/NOT STARTED/authorization states. No source, dependency
manifest, or application functionality exists; no Phase 1 work was performed.

Unverified: all application behavior, third-party compatibility, real-data
coverage/provenance, financial metrics, execution, persistence, UI, and
performance. No large financial dataset was fetched.

## I. Complexity and performance

There is no implemented algorithm or application runtime to benchmark.
Theoretical expectations for Phase 1 only: sorting N rows is O(N log N);
retaining records is O(N) space; hashing B source bytes is O(B) time and can
stream with constant auxiliary memory. These are design expectations, not
measured QuantLab results. No speed or throughput claim is made.

## J. Interview preparation

Five technical questions:

1. Why choose a modular monolith, and which dependency direction keeps the core
   independently testable?
2. How do a data contract and a portfolio invariant differ?
3. What does SHA-256 input identity establish, and what can it not establish?
4. Why can `git status` succeed while `git log` fails in this repository?
5. How would you test deterministic ingestion without network or market data?

Three finance/quantitative questions:

1. Why does a signal evaluated after T's close require a later execution price?
2. Why can an unhandled stock split corrupt an integer-share simulation?
3. Why do a +10% return and a -10% return leave a loss rather than break even?

Independent exercise: on paper, design an OHLC consistency predicate. Give
three valid rows, including all-equal prices, and three invalid rows. Separately
list malformed inputs that must fail before that predicate is evaluated. Then
write a small version locally during the authorized Phase 1 session and compare
its behavior with the actual validator/tests. No code is required in Phase 0.

Files to explain now: charter architecture/session rules; D03 data identity;
D04-D05 execution limitations; Phase 1 roadmap acceptance; status authorization;
and the README skeleton. Later learning should reference actual source files.

## K. Current project status

Phase 0 is COMPLETE; Phases 1-10 are NOT STARTED. No phase after 0 is authorized.
No application bugs can be assessed yet. Main limitations are
an unverified future Python dependency environment, proposed rather than
approved financial semantics, and unavailable automatic corporate-action,
session-coverage, and survivorship verification. No implementation debt exists
to report. Project functionality remains unimplemented.

## L. Next session

Proposed exact task: **Session 01, Phase 1 - local daily OHLCV CSV/metadata
ingestion, validation, diagnostics, fingerprints, and deterministic fixtures.**
Prerequisites are explicit Phase 1 authorization, review of D03, and selecting
and checking the actual Python environment. No provider or real dataset is
required: start with clearly labeled synthetic files.

Use [Phase 1 acceptance](../ROADMAP.md#phase-1---historical-data-foundation).
The importer must accept valid inputs consistently, reject malformed inputs
clearly without silent repairs, retain provenance, and pass its actual pytest
checks. Finish the report/status and stop before engine work.

Immediate user review: charter scope, roadmap size, D03 input contract, and the
D04-D05 tradeoffs that must be settled before Phase 2. Costs, metrics, strategy
details, experiment caps, and provider selection have explicit later gates.
Do not interpret this proposed task or Phase 0 completion as permission to begin.
