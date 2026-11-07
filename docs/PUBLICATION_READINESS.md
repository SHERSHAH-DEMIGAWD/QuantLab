# GitHub publication readiness

## Publication completed, 2026-11-07

**PUBLISHED with the user's explicit authorization:**
[SHERSHAH-DEMIGAWD/QuantLab](https://github.com/SHERSHAH-DEMIGAWD/QuantLab),
public visibility, default branch `main`. Initial reviewed commit: `2b2b94e`.
Local `codex/publication` tracks `origin/main`. Only that reviewed history was
pushed; no force, mirror, all-ref push or history rewrite. Commits use the
verified account's public GitHub noreply identity. No license was invented and
no application was deployed.

Immediately before committing, both review scripts passed for 140 candidates.
The committed ordinary history also passed: no private files, detected credentials
or owner paths. Remote GitHub tree inspection returned 140 files, no truncated
tree and no forbidden paths. A fresh remote clone matched every initial file's
SHA-256. All 22 private IBM/MSFT validation files remain ignored locally; only
the two invented CSV fixtures are published. Internal tool refs and generated
PDF/environments/databases are excluded. Pattern scans remain bounded evidence.

Fresh clone at local ignored `.release-check/github-publication/clone-verified-20261107`:

| Executed check | Result |
| --- | --- |
| Isolated venv / editable `.[test]` install / pip check | Succeeded; no broken requirements; no private configuration |
| Frontend lockfile install | `npm ci --offline --no-audit --no-fund`: 110 packages |
| Backend with private snapshot/PYTHONPATH unset | **444 passed, six private-data skips in 24.82s** |
| Frontend unit/component suite | **45 passed in 11.14s** |
| TypeScript/Vite production build | Passed |
| Actual API/SQLite browser workflows | **Four passed in 25.4s**, including build |
| Source/test/script/dependency baseline | 92 pre-existing files unchanged |

The sandbox's blocked proxy initially made GitHub auth appear invalid; external
network verification confirmed the existing signed-in account without requesting
secrets. Sandbox ensurepip also failed; an approved external retry completed the
fresh environment. These are verification-environment failures, not concealed
application failures. No full suites were started before dependency installation
completed. Tests used synthetic inputs and did not fetch historical observations.

Key publication commands, from the root:

```powershell
gh api user --jq '{login: .login, id: .id}'
git switch -c codex/publication
git add -- .gitattributes .gitignore .cursor AGENTS.md README.md pyproject.toml backend frontend scripts docs data/raw/.gitkeep data/processed/.gitkeep
git diff --cached --check
.\.venv\Scripts\python.exe scripts/check_publication.py
.\.venv\Scripts\python.exe scripts/verify_repository.py
git -c user.name=SHERSHAH-DEMIGAWD -c user.email=178127292+SHERSHAH-DEMIGAWD@users.noreply.github.com commit -m 'Initial QuantLab release'
gh repo create SHERSHAH-DEMIGAWD/QuantLab --public --description 'Local strategy research with deterministic daily backtesting, integrity audits, robustness experiments, FastAPI, SQLite, and React.' --source . --remote origin
git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push -u origin HEAD:refs/heads/main
git clone --single-branch --branch main https://github.com/SHERSHAH-DEMIGAWD/QuantLab.git .release-check/github-publication/clone-verified-20261107
```

Inside the fresh clone, ran the README venv/editable install and pip check, then
`python -m pytest -q` with `QUANTLAB_REAL_MARKET_DIR` and `PYTHONPATH` unset.
From its `frontend`, ran the npm install above, `npm test`, `npm run build` and
`npm run test:e2e`. A subsequent documentation-only commit records completion;
it changes no tested application, fixture, package or script. Final status and
questions: [Session 15](session-reports/SESSION_15_PHASE_10.md).

## Original preparation record, 2026-11-03

The dated findings and recommended steps below describe the earlier preparation
session, before the later explicit publication authorization and actions above.

2026-11-03 (Asia/Calcutta). **Preparation complete; suitable for a reviewed
initial commit and an explicitly approved publication. Nothing was pushed.**
This is packaging/safety review after completed phases 0-10 and limited real
historical validation, not another development phase.

## Git and privacy findings

- The working repository has **zero tracked/staged files, zero branch/tag
  commits, no remote, tags or stashes**. Its branch is still unborn `master`.
  Application/source files are currently untracked publication candidates;
  the working repository itself is not yet a cloneable project history.
- Candidate contents and intended branch/tag history passed the publication
  path/credential-pattern review. No `.env`, private database, environment,
  Node modules, generated output or restricted market observation is included.
  Only two CSVs are candidates: the explicitly invented backend fixture and
  `frontend/public/examples/nine_sessions.csv`.
- All **22 existing private real-validation files** remain present and ignored
  under `.release-check/real-market/`, including IBM/MSFT JSON/CSV, metadata,
  issuer archives, results and SQLite. None is tracked or in publication history.
- Five private tool refs point to four unique historical trees. They contain
  older versions of three documents with owner-specific absolute paths, and
  are **not publication branches**. They were inspected and left unchanged.
  Do not mirror-push, push tool refs, upload the working `.git` directory or use
  a filesystem ZIP of the whole workspace as a publication artifact.
- Credential checks inspect file names, token/private-key patterns and quoted
  credential-like assignments without printing matches. No detected credentials
  remain in candidate files or intended history. This is bounded inspection,
  not an exhaustive security certification. Recheck after staging changes.

## Changes made

- Reorganized README around features, stack/architecture, public setup/tests,
  actual historical evidence, limitations and data rights. The public suite
  still includes synthetic references; the six private historical cases are
  explicitly optional and skip without their local snapshot.
- Removed owner-specific paths from the release guide and two historical
  session reports, marking the portable/redacted forms. No financial evidence
  was rewritten. Clarified that Session 10's synthetic checks preceded the
  later IBM/MSFT validation; updated the ownership guide accordingly.
- Added two visually inspected **synthetic-only** application screenshots in
  `docs/images/`, captured by the existing browser suite in the disposable clone.
  They contain no private observations, owner paths or textual PNG metadata.
- Extended ignore rules for SQLite journals/sidecars and private-key files.
  Added read-only `scripts/check_publication.py`; updated the existing repository
  verifier to accept reviewed PNGs, check image links/latest reports and report
  staging rather than treating any staged file as an error.
- Replaced one HTTP-403 legacy SEC reference with the already documented,
  accessible issuer explanation. No application/financial source, strategy,
  financial rule, dependency, infrastructure or license was added/changed.

## Historical-data claim permitted by the evidence

Private Alpha Vantage `TIME_SERIES_DAILY` public sample responses supplied
**100 raw daily bars each for IBM and MSFT, 2026-06-11..2026-11-02**. The existing
import/simulator/analytics/audit/experiment/API/SQLite workflows were used.
IBM's provider split query succeeded with no listed event in that interval.
MSFT's provider query returned an access message and remains unknown; separate
Microsoft issuer history supported the interval declaration. The underlying
exchange feed was unspecified. No dataset redistribution permission was found.

The original real-data run passed 450 backend tests (444 existing + six private).
This does not demonstrate independent price accuracy, long histories, verified
sessions/liquidity, profitability, prediction or freedom from bias. Dividends
are excluded. Sources, provenance hashes, calculations and failures remain in
[REAL_MARKET_VALIDATION.md](REAL_MARKET_VALIDATION.md); observations stay private.

## Clean clone verification and exact commands

Because the root has no commit, copied only `git ls-files --cached --others
--exclude-standard` candidates into an ignored disposable `seed` repository,
created a local test commit with a nonpersonal test identity, then executed:

```powershell
git clone --no-local .release-check/publication/seed .release-check/publication/clone-verified
```

No root commit, branch/ref rewrite or GitHub operation occurred. The seed/clone
is disposable evidence, not the repository to publish. Inside the clone:

```powershell
py -0p
py -3.15 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[test]'
.\.venv\Scripts\python.exe -m pip check
$env:QUANTLAB_REAL_MARKET_DIR=$null
$env:PYTHONPATH=$null
.\.venv\Scripts\python.exe -m pytest -q
# From frontend:
npm ci
npm test
npm run test:e2e
```

| Executed verification | Actual result |
| --- | --- |
| Fresh Python install / pip check | Declared dependencies installed; no broken requirements |
| Clean npm lockfile install | 110 packages installed |
| Public backend suite | **444 passed, six private-data cases skipped in 18.19s** |
| Frontend suite | **45 passed in 10.50s** |
| Build and real-browser suite | **Four passed in 25.4s**; strict TypeScript/Vite build passed |
| Development startup | Fresh default SQLite created; API health/docs/OpenAPI and Vite HTML/proxy health all HTTP 200 on documented alternate ports 8019/5179 |
| Import isolation | `quantlab` resolved inside the clone's `backend/src`; private market-data directory absent |
| Screenshots | Fresh desktop/mobile captures of shipped SYNTH input; visually inspected |

Development startup used the clone's `.venv` interpreter with
`-m quantlab.api --port 8019`, and `node node_modules/vite/bin/vite.js --host
127.0.0.1 --port 5179 --strictPort` from its frontend, with
`QUANTLAB_API_TARGET=http://127.0.0.1:8019`. The latter is the executable used by
`npm run dev`. Only owned processes were stopped. An immediate stop probe was
early; the subsequent listener check confirmed all owned QA ports closed.

The first sandbox local-clone command failed (exit 128); approved external
execution succeeded. The first backend command started before pip finished and
failed collection with missing FastAPI (one error in 4.80s). Waited for successful
installation/pip check and reran the complete public suite above. No product fix
or omitted test concealed either verification-harness failure.

Final exact review commands, from the working repository:

```powershell
git status --short --branch
git ls-files --stage
git log --all --oneline --decorate -15
git rev-list --branches --tags --count
git for-each-ref --format='%(refname) %(objecttype)'
git remote
git stash list
.\.venv\Scripts\python.exe scripts/check_publication.py
.\.venv\Scripts\python.exe scripts/verify_repository.py
git check-ignore .release-check/real-market/IBM.csv .release-check/real-market/MSFT.csv
```

Repository verification includes all local Markdown/image links and anchors,
whitespace/JSON/Python syntax, dependency manifests and unchanged core hashes.
External documentation HEAD requests initially returned 200 for 16 of 17 URLs;
the legacy SEC URL returned 403 and was replaced rather than bypassed. Runtime
loopback routes were checked on the alternate ports above. Final counts/results
are recorded in [Session 12](session-reports/SESSION_12_PHASE_10.md).

## Remaining decisions and recommended publication steps

No application/package blocker remains in the executed Windows checks. Python
3.12, other platforms/browsers, installation without registry/cache access and
the six private-data cases from a public checkout remain unverified/unavailable
as documented. The Python direct pins/installed inventory do not freeze every
future transitive resolution. No LICENSE has been selected; do not describe the
repository as licensed open source until the owner makes that decision.

The root still needs a reviewed initial commit. After reviewing this report:

1. Choose the public commit identity and decide whether to supply a license;
   none has been invented by this preparation.
2. Stage the reviewed publication files with ordinary `git add` (no `-f`):
   `.gitattributes .gitignore .cursor AGENTS.md README.md pyproject.toml backend
   frontend scripts docs data/raw/.gitkeep data/processed/.gitkeep`.
3. Review `git diff --cached --name-only`, `git diff --cached --check` and rerun
   both check scripts. Verify screenshots and the two synthetic CSVs are the only
   intended data assets. Create the initial commit only after that review.
4. Only with explicit approval, create/select an empty GitHub repository and add
   its approved URL as `origin`. Push **only the reviewed branch**, e.g.
   `git push -u origin main` after intentionally naming it `main`. Do not use
   `--mirror`, `--all`, force-push or upload internal refs.
5. Clone the approved GitHub branch into a fresh directory and repeat the README
   setup/tests; confirm ignored private files remain absent.

Preparation stops here. No remote repository was created and nothing was pushed.
