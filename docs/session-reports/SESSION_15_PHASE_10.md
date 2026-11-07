# Session 15 - Authorized GitHub publication

Date: 2026-11-07 (Asia/Calcutta). Source publication, not a development phase.

## A. Session overview

**COMPLETE.** The user explicitly requested publication under the supplied GitHub
account. Published the reviewed repository as public
[SHERSHAH-DEMIGAWD/QuantLab](https://github.com/SHERSHAH-DEMIGAWD/QuantLab),
default branch `main`, then verified a fresh remote clone. Prior no-push stop
conditions were superseded only by this explicit publication request. No hosted
deployment or new financial/application feature. Work remains AI-assisted.

## B. What was implemented

Created local `codex/publication`, staged the 140 reviewed files, created initial
commit `2b2b94e`, created the GitHub repository/`origin` and pushed only
`HEAD:refs/heads/main`. Used the verified GitHub account's public noreply identity.
Updated D17, status, roadmap and publication record; a follow-up documentation
commit records the executed result. No license, dependency or application change.

## C. Why this functionality exists

The previous task prepared a safe public package but intentionally stopped before
publication. The new explicit request authorized creating the remote and pushing
the reviewed source so others can clone and inspect the project.

## D. Integration with the existing codebase

No financial/core/API/frontend/test/script/package bytes changed. All 92 original
source/test/script/dependency files matched the prior hash inventory; the existing
verifier also checked all 41 backend file identities and 29 core dependency
boundaries. Generated PDF, environments, outputs, private databases and all 22
IBM/MSFT validation/evidence files remain ignored. Private internal tool refs
were neither pushed nor rewritten. No working `.git` directory was distributed.

## E. Technical concepts to study

Study staged/index content versus worktree, ordinary commits versus private tree
refs, branch/refspec/upstream/default-branch distinctions, authenticated GitHub
API/CLI operations, public commit identity and clean-clone verification. Recreate
**`inspect`** and **`tree_entries`** from the read-only publication checker in a
separate practice repository with dummy files, not live credentials.

## F. Financial and quantitative concepts to study

No new market analysis. Public observations remain the two explicitly synthetic
CSV fixtures. Private IBM/MSFT sample evidence and the six opt-in tests retain
their original limited source/period/basis/split/coverage/liquidity/statistical
scope. Public source publication grants no new permission to redistribute vendor
observations and makes no profitability or prediction claim.

## G. Engineering decisions and tradeoffs

D17 records the publication authorization and narrow boundary. Keep the original
root history as an initial ordinary commit; push a single explicit remote branch,
not all refs or a mirror. Preserve private historical tool trees locally. A
separate documentation commit records remote verification without amending or
force-pushing the published initial commit. Leave the license unselected; public
visibility is not described as a selected open-source license or deployed service.

## H. Testing and verification

Exact publication commands and prior preparation evidence:
[PUBLICATION_READINESS.md](../PUBLICATION_READINESS.md). Executed root checks
before/after staging and after the initial commit:

```powershell
git diff --cached --check
.\.venv\Scripts\python.exe scripts/check_publication.py
.\.venv\Scripts\python.exe scripts/verify_repository.py
git check-ignore .release-check/real-market/IBM.csv .release-check/real-market/MSFT.csv output/pdf/QUANTLAB_COMPLETE_HANDBOOK.pdf
```

GitHub API verified the signed-in account and absence of an existing target;
after creation verified public visibility, default `main` and initial remote tree:
140 files, no forbidden paths, not truncated. The remote clone had only ordinary
main refs, no private workspace directory and byte-identical SHA-256 for all
140 initial files. Inside that clone:

```powershell
py -3.15 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[test]'
.\.venv\Scripts\python.exe -m pip check
$env:QUANTLAB_REAL_MARKET_DIR=$null
$env:PYTHONPATH=$null
.\.venv\Scripts\python.exe -m pytest -q
# From frontend:
npm ci --offline --no-audit --no-fund
npm test
npm run build
npm run test:e2e
```

The venv command actually used the existing verified CPython interpreter with
`-m venv`; the selector above is the equivalent README command. Installation
completed before backend/browser execution. Actual fresh-clone results:

- pip consistency: **no broken requirements**.
- npm lockfile install: **110 packages**, using cached/offline packages.
- Backend: **444 passed, six expected private-data skips in 24.82s**.
- Frontend: **45 passed in 11.14s**.
- TypeScript/Vite build: **passed**.
- Actual API/SQLite/Edge workflows: **four passed in 25.4s**, including synthetic
  import, all strategies, costs/rejections, audits, robustness, saved restarts and
  fresh reproduction. No historical download or private input was used.

Initial sandbox GitHub commands failed through the blocked proxy and misleadingly
reported invalid auth; allowed network execution confirmed existing access.
Sandbox venv ensurepip failed; an approved external retry succeeded. A later
unneeded sandbox `ls-remote` also hit that proxy; authoritative remote checks used
allowed network execution. No auto-review rejection or application correction.
The final metadata-only changes were checked with repository/publication scanners
and pushed normally; no application suites were repeated for documentation alone.

Final repository checks cover 141 public files, 53 Python AST parses, 12 JSON
files, 324 local links, 41 unchanged backend hashes, 29 independent core modules,
75 retained benchmark samples and valid latest A-L/questions. Candidate and
ordinary-history scans have no findings; the previously disclosed path-bearing
documents remain only in private internal snapshot refs. Owned QA ports
8018/5178 had zero listeners after the browser suite. No private refs or observations
are present in the remotely cloned ordinary history.

## I. Complexity and performance

No financial performance change or new benchmark. Candidate/hash inspection is
linear in scanned bytes; publication-history scanning depends on reachable
ordinary commits. The remote clone/test durations are local verification results,
not application throughput or hosted-capacity claims.

## J. Interview preparation

Five technical questions:

1. Why does a single reviewed branch push exclude private internal tree refs?
2. What does matching every remote-clone file hash establish beyond local status?
3. Why is the public noreply author identity preferable to exposing a local email?
4. Why can public visibility coexist with no selected software license?
5. Why must documentation publication and deployment of an authenticated service
   remain separate claims?

Three financial questions:

1. Why do public source tests skip the six private historical-data cases?
2. Why does publishing aggregate validation evidence not permit publishing the
   underlying restricted observations or retained databases?
3. Why do successful synthetic browser workflows establish application behavior
   without proving executable liquidity or profitable trading?

Independent exercise: in a separate dummy repository, create a public text file
and ignored dummy private file, commit only the public candidate, clone one named
branch and compare hashes. Explain which refs/data were transmitted. Do not use
real credentials or restricted market observations.

## K. Current project status

Source publication COMPLETE at the linked public repository, default `main`.
Phases 0-10, limited historical validation, handbook/PDF and all financial limits
remain unchanged. Existing public application tests passed from the fresh remote
clone; six private cases skipped as designed. No license invented or service
deployment. The local generated PDF remains available privately as previously
delivered. Owner mastery remains pending independent study.

## L. Next session

**STOP after publication verification.** No additional feature, provider,
infrastructure, license selection or hosted deployment is implied. Future changes
require their own explicit task; the owner can now share the repository URL.
