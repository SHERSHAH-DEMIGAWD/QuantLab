# Post-release real market validation

2026-11-03 (Asia/Calcutta). **COMPLETE for the two short samples below.**
This is the explicitly authorized validation improvement after phases 0-10,
not a new development phase. All production backend/frontend source, financial
rules, dependencies and original synthetic tests are unchanged. AI-assisted
implementation/verification; no independent owner-authorship claim.

## Access, rights and source selection

Checked presence only for `ALPHAVANTAGE_API_KEY`, `ALPHA_VANTAGE_API_KEY`,
`APCA_API_KEY_ID`, `APCA_API_SECRET_KEY`, `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`,
`ALPACA_API_KEY_ID`, `ALPACA_API_SECRET_KEY` in process/User/Machine environments:
all absent. No secret was printed, requested in chat or read from a file.
Local `data/raw` and `data/processed` contained only placeholders.

Alpha Vantage's documented public `apikey=demo` request and a symbol substitution
returned usable IBM/MSFT historical samples. This is limited public sample
access, not verified personal-account access or a supported product integration.
Its daily endpoint documents raw OHLCV, compact 100 observations and premium
full history. [Official documentation](https://www.alphavantage.co/documentation/#daily).
Used for private individual noncommercial testing under the reviewed
[terms, sections 2-5](https://www.alphavantage.co/terms_of_service/).
No subscription, account registration, restricted scraping or redistribution
permission was obtained. No market-data files were staged/committed or included
in test fixtures. Private JSON, CSV, metadata, issuer HTML and SQLite remain
under the already ignored `.release-check/real-market/` directory.

Alpaca was evaluated for longer history. Its
[plan documentation](https://docs.alpaca.markets/us/docs/about-market-data-api)
describes history since 2016; its
[bars API](https://docs.alpaca.markets/us/reference/stockbars) supports raw
adjustments, explicit feeds and paginated results. Authentication is required;
no credentials or verified entitlement were available, so no Alpaca market-data
request was made. No IEX/SIP entitlement or longer history was demonstrated.

## Instruments, coverage and corporate actions

| Instrument | Listing identity | Received/used interval | Source/basis |
| --- | --- | --- | --- |
| IBM | NYSE (issuer also lists NYSE Texas) | 2026-06-11..2026-11-02, all 100 returned bars | Alpha Vantage `TIME_SERIES_DAILY`, compact public sample; raw unadjusted OHLC, raw share volume |
| MSFT | Nasdaq | 2026-06-11..2026-11-02, all 100 returned bars | Same endpoint/basis; no adjusted-close substitution |

Listing sources: [IBM issuer FAQ](https://www.ibm.com/investor/help/general-faqs),
[Microsoft issuer FAQ](https://www.microsoft.com/en-us/Investor/faq).
Listing identity is separate from the price feed: the responses do **not** name
an underlying exchange/SIP/IEX feed. No specific feed is asserted. Both response
timezones are `US/Eastern`, mapped to the contract's `America/New_York` session
labels. USD/daily declarations follow the selected U.S. common shares and endpoint.
The source offers no independent session-completeness certificate; metadata
keeps `session_coverage=unknown` and runs explicitly acknowledge that limitation.
The 144-calendar-day sample is not a long-history or market-regime study.

| Interval split check | Actual response/evidence | Declaration used |
| --- | --- | --- |
| IBM, full imported interval | Successful `SPLITS` response lists 1999-05-27 (2.0000) and 2021-11-04 (1.0460), neither inside this interval. The [issuer history](https://www.ibm.com/investor/help/ibm-stock-splits-and-ibm-stock-dividends) describes the latest stock split as May 1999. | `none_reported`, with both references and interval in `split_evidence` |
| MSFT, full imported interval | `SPLITS` returned HTTP 200 with **Information only**, requesting a personal key. That provider check remains **unknown**. The separately successful [issuer FAQ/history](https://www.microsoft.com/en-us/Investor/faq) lists nine splits and describes the latest as trading 2003-02-18. | `none_reported` based on the separately reviewed issuer history; failed provider query is explicitly disclosed |

These are documented checks supporting declarations, not an exhaustive corporate-
action certification. IBM's provider/issuer event categories and 1999 date
conventions differ; this was not reconciled, and neither reported date is near
the imported interval. Do not generalize this eligibility to IBM's 2021 event.
Dividends and other actions remain excluded. Neither an unavailable query nor
an HTTP 200 alone establishes absence of splits.

## Retained provenance and transformation

Four HTTPS requests used exactly
`https://www.alphavantage.co/query?function=FUNCTION&symbol=SYMBOL&apikey=demo`,
with FUNCTION in `TIME_SERIES_DAILY,SPLITS` and SYMBOL in `IBM,MSFT`.
The `demo` value is the provider's public example, not a user secret.

| Private original | Retrieval UTC on 2026-11-03 | Bytes | SHA-256 |
| --- | --- | --- | --- |
| `IBM.TIME_SERIES_DAILY.json` | 04:58:29.622927 | 21302 | `309247171fca407fc9192018b402ef325b9da3d472c856513f4de5b6d84f714c` |
| `MSFT.TIME_SERIES_DAILY.json` | 04:58:31.568562 | 21390 | `273963944d18d68064a9d4a08c90d97110a789b08cad36046c0c49da67ce7027` |
| `IBM.SPLITS.json` | 04:58:30.770760 | 247 | `e2c0de31a1b0c5ceab7ea037c0dd7d5292bbc502184519373777cd2f1652d2dd` |
| `MSFT.SPLITS.json` (access message) | 04:58:32.123795 | 220 | `e8ddc218d89ff77ad7e395782b4c4d28d10d328ae90c3ba597a8e7d3689b9585` |
| `IBM.issuer.html` | 05:00:55.550312 | 127816 | `ac25cf7619b330d2aa08ec2276d0379e95cf03806601fd8bcd8d4a3206ca7672` |
| `MSFT.issuer.html` | 05:00:56.791446 | 266578 | `da59f641055370c77de6bc3c05d3cecce69127a09ef87288497ec6f5f389f869` |

All six successful HTTP requests returned 200. Each retained receipt records
URL/time/status/size/hash; issuer redirects stayed on the exact requested URL.
The original vendor JSON is retained separately from the imported CSV.

Conversion, executed by the private one-off `prepare.py`, mapped the date key
and strings `1. open,2. high,3. low,4. close,5. volume` to the existing six-column
CSV contract. It sorted all dates ascending and emitted UTF-8 without BOM, LF
lines, one header. No numeric rounding, adjusted prices, resampling, filled
sessions or dropped rows. Each normalized bar was tested against every original
JSON value. The existing `load_dataset_bytes` imported both complete files:
100 rows each, zero invalid/duplicate/zero-volume rows, no further normalization.

| Identity | IBM | MSFT |
| --- | --- | --- |
| CSV bytes | 5547 | 5634 |
| CSV SHA-256 | `e4370c73b5c3e4124a822e5da7dd68ff034bb1c7b586a9ee818cf487b58d2a01` | `a726c91f361fdadbcc17b00fd2304e38e705286379305ab693fcd15bf93e1796` |
| Effective metadata SHA-256 | `9bbfebf5a5237d93e0e3df351db081ebbe96619a108c0918b7ee53286a5b73b8` | `1b4f7f48c737691b401a1fe3e12adb7a87c40bb52bbf5d2c80c70b023dfae18f` |
| Dataset ID | `7d4799203d49cc05b7daf757b3f3ab698938f536ec812be48c92c632809a8ed9` | `a5b7121ab20f21f78e6acf3fbe2db9c33aba93ea8b695feeb4458fba13930d2a` |

Metadata uses `source_kind=local_file`, the named provider/public endpoint,
original retrieval time/hash, conversion description, reviewed private-use
restriction and interval-specific split references. No synthetic identity was
used to bypass coverage acknowledgment. Hashes identify retained inputs; they
do not independently authenticate the provider, data completeness or rights.

## Executed financial results

Existing importer -> simulator -> analytics -> auditor -> experiment coordinator;
API/SQLite wrap those same functions. Initial cash **$10,000**, long-only integer
shares, decisions after close, next observed open, no leverage/final sale.
Fixed configurations chosen for validation, not optimized: buy and hold,
SMA(5,20), momentum(10, threshold 0). Risk-free rate 0. Costs below are
commission per filled order plus adverse slippage on both sides.

| Instrument / strategy | Zero-cost final equity | $1 / 10 bps final equity | Fills, zero / cost | Final shares, zero / cost |
| --- | --- | --- | --- | --- |
| IBM buy and hold | $9,074.95 | $9,064.19 | 1 / 1 | 35 / 35 |
| IBM SMA(5,20) | $7,631.86 | $7,531.79 | 9 / 9 | 30 / 29 |
| IBM momentum(10) | $8,745.50 | $8,630.86 | 13 / 13 | 34 / 34 |
| MSFT buy and hold | $12,892.25 | $12,881.46 | 1 / 1 | 25 / 25 |
| MSFT SMA(5,20) | $11,449.87 | $11,346.42 | 10 / 10 | 0 / 0 |
| MSFT momentum(10) | $11,878.72 | $11,736.21 | 12 / 12 | 0 / 0 |

These are conditional price-return accounting outputs, not profitability or
prediction evidence. Open holdings remain marked, not realized trades.

Independent reference checks in
[the six opt-in cases](../backend/tests/test_real_market_validation.py):

- Buy and hold: rational arithmetic directly from source prices, one closed-form
  purchase at the second open (2026-06-12). Floor quantity after fee/slippage,
  independent half-up rounding, residual cash and all closing equities agree
  exactly. Zero-cost residual cash: IBM $237.10, MSFT $214.25; cost case:
  $226.34/$203.46. No production sizing/cost helper is called by the reference.
- All 100 SMA/momentum targets at both costs: direct window sums/ratios agree
  exactly with the streaming rules, including warm-up. The reference generates
  no orders/fills and is not another execution engine.
- For all 12 fixed runs: rational equity ratios and independently expressed
  two-pass sample variance check cumulative/annualized return, drawdown,
  annualized volatility and Sharpe (99 return observations). Cumulative and
  drawdown differences were zero; maximum absolute differences were
  4.44e-16 annualized return, 1.11e-16 volatility and 4.44e-16 Sharpe. Tests allow
  1e-12 absolute/relative tolerance at the documented float boundary.
- SMA/momentum statistical references use the recorded equity trace; their
  terminal accounting also receives the existing independent ledger audit.
  They are not a second independently implemented trading engine. Frozen final
  equities/fill counts are regression checks, not independent market truth.

Reference assumptions match QuantLab: price return excluding dividends, residual
cash, second-open entry, actual 144 calendar days/365.25 annualization and sample
deviation/252. A close-to-close quote return, first-open purchase, fractional
shares or dividend reinvestment would be a different comparison; none was used
as an expected result. Annualization is flagged as short-window extrapolation.

All 12 fixed runs passed source-backed audit with exact CSV/effective metadata,
separately supplied settings and opt-in simulator replay: no FAIL. A representative
IBM buy-and-hold report had **19 PASS, 2 WARNING, 11 NOT_ASSESSED**. Warnings
retain provenance/model limits; unassessed rules include corporate-action truth,
session completeness, opening liquidity, all look-ahead absence, survivorship,
selection/overfitting/significance and original executable restoration. Human
source checks do not silently upgrade those automated rules.

## Robustness, persistence and reproduction

For each instrument, actual API/TestClient requests imported the same private
CSV/metadata into isolated SQLite and reimported it with the same dataset ID.
Parameter grid: SMA(3,10), SMA(5,20), momentum(5,0), momentum(10,0), plus the
matching buy-and-hold reference. Two cost cases as above and two subperiods:
2026-06-11..2026-09-04 (60 observations), 2026-09-08..2026-11-02 (40).
Each saved grid executed **20 runs / 1,000 evaluated bars**. No unequal-duration
ranking or claim that costs must monotonically lower every possible return.
Each grid's audit totals: 300 PASS, 40 WARNING, 300 NOT_ASSESSED, zero FAIL.

Separate chronological train/test requests used those four candidates with
zero costs and benchmark, selecting only on training cumulative return before
testing. Each used five training runs, two test runs, 380 evaluated bars and
120 indicator warm-up bars. Each test run started flat with fresh $10,000;
60 earlier closes warmed indicators, with no earlier fill/valuation carried in.

| Instrument | Frozen training selection | Selected test final equity / return | Matching test buy and hold |
| --- | --- | --- | --- |
| IBM | momentum(5,0) | $11,051.68 / 10.5168% | $10,834.12 / 8.3412% |
| MSFT | momentum(10,0) | $10,045.70 / 0.4570% | $10,281.00 / 2.8100% |

Each train/test result's audit totals: 105 PASS, 14 WARNING, 105 NOT_ASSESSED,
zero FAIL. A single selected interval does not establish generalization.

Four saved experiments in two databases survived closing/recreating the app
against the same files. Original CSV BLOBs were byte-identical. Retrieval made
zero coordinator calls; reproduction made one fresh call per experiment and
reported **economic_match=true, implementation_match=true** for all four.
Retained private copies: `IBM.validation.sqlite3`, `MSFT.validation.sqlite3`;
summary/hashes: `workflow-summary.json`. This was real SQLite with new app
instances/TestClient, not a browser run or an OS/server-process restart test.
No cached result was substituted for recomputation and no source archive restored.

## Precise commands, regressions and failures

PowerShell, repository root, existing `.venv` (CPython 3.15.0/pytest 9.2.0).
Acquisition was executed as inline Python with `urllib.request.urlopen(url,
timeout=25)` for the four exact URLs defined above, reading at most 2 MiB+1,
writing unmodified response bytes and SHA-256 receipts. No authentication header
or user key was used. The following is the request/retention command body:

```powershell
@'
from datetime import datetime, timezone
import hashlib, json
from pathlib import Path
import urllib.request
root = Path('.release-check/real-market')
root.mkdir(parents=True, exist_ok=True)
for symbol in ('IBM', 'MSFT'):
    for function in ('TIME_SERIES_DAILY', 'SPLITS'):
        url = f'https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey=demo'
        record = {'symbol': symbol, 'function': function, 'url': url,
                  'retrieved_utc': datetime.now(timezone.utc).isoformat()}
        with urllib.request.urlopen(url, timeout=25) as response:
            body = response.read(2 * 1024 * 1024 + 1)
            record.update(http_status=response.status, bytes=len(body),
                          sha256=hashlib.sha256(body).hexdigest())
        (root / f'{symbol}.{function}.json').write_bytes(body)
        (root / f'{symbol}.{function}.receipt.json').write_text(
            json.dumps(record, indent=2) + '\n', encoding='utf-8')
'@ | .\.venv\Scripts\python.exe -
```

Do not overwrite the retained snapshot when refreshing. Public compact responses
move over time; re-fetching later cannot promise these exact observations/hashes.
The executed conversion command was
`.\.venv\Scripts\python.exe .release-check/real-market/prepare.py`.
That private script and all original inputs are retained locally, not distributed.
Its complete transformation is the field mapping/order/encoding specified above;
reproduction uses the retained CSV/effective metadata, not another download.

Executed regression commands:

```powershell
$env:QUANTLAB_REAL_MARKET_DIR=(Resolve-Path '.release-check/real-market').Path
.\.venv\Scripts\python.exe -m pytest -q backend/tests/test_real_market_validation.py --basetemp=.release-check/pytest-real-integration -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.release-check/pytest-real-full -p no:cacheprovider
# Separately verified the absent-snapshot behavior:
$env:QUANTLAB_REAL_MARKET_DIR=$null
.\.venv\Scripts\python.exe -m pytest -q backend/tests/test_real_market_validation.py -p no:cacheprovider
# From frontend:
npm test
```

| Check | Actual result |
| --- | --- |
| Initial new integration suite | 4 passed / 2 failed in 3.72s; test wrongly compared `10000.0000` with text `10000.00` |
| Corrected full backend suite | **450 passed in 25.24s**, no skips: all 444 original + six private-data cases |
| Snapshot environment unset | **6 explicitly skipped in 1.17s**; no fake data/network fallback |
| Existing frontend regression suite | **45 passed in 15.59s** |
| Repository integrity check | PASS: 132 files, 52 Python parses, 151 local links, 41 unchanged production backend hashes; latest report/private receipts checked separately |

Corrected the new assertion to compare Decimal value, cash and zero shares;
production serialization/financial rules were unchanged. The first inline
summary command also tried to JSON-encode a ClosedTrade dataclass while printing
a count; fixed the reporting expression to `len(closed_trades)` and reran.

Environment failures were retained honestly: initial sandbox network requests
failed `URLError`; approved external execution obtained the responses above.
A sandbox full-test attempt hit temp-directory errors and was interrupted, not
counted as a completed baseline. A targeted file-fixture diagnostic confirmed
`PermissionError [WinError 5]` on pytest's private basetemp directory. Frontend
initially failed Vite startup with `spawn EPERM`. Approved external executions
then completed the full backend/frontend suites. One sandbox read of private
pytest directories produced an empty glob; a checked external extraction
required exactly two databases before recording the successful workflow summary.
No application permissions or financial behavior were weakened.

## Remaining limits and stop

Six new cases are opt-in to respect data rights. `QUANTLAB_REAL_MARKET_DIR`
must contain the exact retained private JSON/CSV/metadata; supplied missing or
changed files fail rather than skip or download. A fresh source checkout alone
cannot rerun them. Keep originals/metadata/evidence/database and current source
yourself; live documentation and provider revisions are outside reproduction.

This validates two short common-stock samples from one vendor, not ETFs, long
history, split processing, independent price accuracy, validated session coverage
or market liquidity. No product provider adapter, new strategy, feature,
deployment, infrastructure, trading profitability, predictive accuracy or
bias-free claim. Existing [limitations](KNOWN_LIMITATIONS.md) still apply.
No real-data browser or cross-platform validation ran in this session.
**Stop after this validation; further work requires a separate explicit task.**
