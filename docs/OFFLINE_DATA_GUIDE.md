# Using historical files offline

Phase 9 selected **Path B**. Provider import is unavailable/deferred; see the
[provider review](MARKET_DATA_REVIEW.md). No market-data account is needed for
this working workflow. The shipped observations are invented, not U.S. market
history. Session 11 separately verified private IBM/MSFT historical samples
through this workflow; see [real validation](REAL_MARKET_VALIDATION.md).

## 1. Acquire and retain your source

Use a lawful export you are permitted to analyze locally. Confirm the instrument
is a U.S.-listed stock/ETF, daily USD observations, and understand the vendor's
OHLC/volume conventions before declaring them. Keep the original export,
documentation/terms, retrieval date, selected interval and event evidence in
your private records. Do not commit provider-owned data without explicit
redistribution permission. Hashes establish input identity, not rights or truth.

Export the required columns deliberately; record any manual conversion and keep
the original vendor file separately. Do not round prices, turn fractional volume
into integers, fill missing sessions, blend adjusted close with raw OHLC, or drop
invalid rows to manufacture acceptance. An unsupported source remains
unsupported. Browser import retains the submitted UTF-8 CSV bytes and effective
metadata in SQLite; it does not archive the vendor's original pre-conversion
format, terms or linked evidence files. Keep those yourself.

## 2. Prepare CSV and metadata

CSV: UTF-8, optional BOM, LF or CRLF. Header, in this exact order:

```csv
date,open,high,low,close,volume
```

Dates are `YYYY-MM-DD` exchange-session labels in `America/New_York`, not UTC
timestamps. One row per date; duplicate/blank/malformed records fail. OHLC must
be positive plain decimal text, with at most six significant fractional digits
and `low <= min(open,close) <= max(open,close) <= high`. Volume must be a
nonnegative integer. No extra columns, currency symbols, thousands separators,
exponents, NaN or Infinity. Maximum CSV size: 10 MiB; metadata UI: 64 KiB.
Sorting and limited text normalization are reported; no missing bars are inferred.
Full parser/identity semantics: [data contract](DATA_CONTRACT.md).

Download the [local-file metadata template](../frontend/public/examples/local_file.metadata.template.json)
from the in-app **Offline import guide & templates**, or copy it from the repo.
It is valid metadata syntax with conservative unknowns, **not an eligible
historical-data example**. Replace `REPLACE_ME` identity/source placeholders;
do not label real observations `synthetic` to bypass coverage acknowledgment.

| Metadata field | What to supply |
| --- | --- |
| `contract_version`, `currency`, `frequency`, `session_timezone` | Keep `1`, `USD`, `1d`, `America/New_York` only when they describe the file |
| `symbol`, `exchange` | Actual instrument/listing identity; names are declarations, not automatically checked against a security master |
| `source_kind`, `source_name` | `local_file` for historical files; actual source/export name |
| `source_reference` | Original file/reference, retrieved UTC date, export interval, relevant documentation and retained evidence references; never credentials |
| `usage_note` | Actual permitted local use and restrictions; unknown permission is not a grant |
| `adjustment_basis` | `unadjusted`, `split_adjusted`, `total_return_adjusted` or `unknown`, according to the source documentation |
| `ohlc_basis_consistent` | Boolean `true` only with supporting source semantics; otherwise string `unknown`; boolean `false` fails import |
| `volume_basis` | `raw`, `split_adjusted` or `unknown`; do not infer it from price labels |
| `split_status`, `split_evidence` | `none_reported` only with a documented successful event check covering the imported interval and explicit evidence; `present` for reported events; otherwise `unknown` |
| `session_coverage` | `declared_complete` only as a supported declaration; otherwise `unknown`; backend coverage stays unverified |

Use only these existing fields. There is no new `retrieved_at`, event list,
calendar certificate or licensing schema. Put references into the existing text
fields. JSON booleans differ from strings; duplicate/unknown keys fail. Omitted
optional declarations become unknown. The complete eligible invented metadata
example is [nine_sessions.metadata.json](../frontend/public/examples/nine_sessions.metadata.json).
Its no-event evidence describes invented data and must never be reused for a
real security. The private Session 11 interval declarations have separate
documented issuer/provider evidence; the downloadable template stays unknown.

## 3. Separate import acceptance from execution

**Validated import** means the file/metadata passed the importer. It does not
verify the vendor, usage rights, price conventions, split history or sessions.
The existing backend decides eligibility when research executes:

| Situation | Existing behavior |
| --- | --- |
| Consistent unadjusted OHLC, raw volume, none-reported splits with explicit evidence | Meets D04 declarations; other numeric/window/strategy checks still apply |
| Unknown/adjusted OHLC, unknown/split-adjusted volume, unknown/present splits, missing/unknown evidence | May import, but D04 blocks simulation |
| Explicit inconsistent OHLC, malformed rows or unsupported metadata | Import fails; no partial dataset is retained |
| `local_file`, even `declared_complete` coverage | Also requires **Risk-free rate & coverage → Acknowledge unverified real-data coverage** in the research form |

A failed, missing or incomplete splits query proves nothing about event absence.
Never set `none_reported` because an endpoint was unavailable. Acknowledgment
does not override D04, certify market sessions, or authorize unsupported prices.
Split status is a dataset-level declaration: selecting a shorter evaluation
window does not bypass a present/unknown declaration on the imported file. A
separately acquired, documented split-free interval needs its own honest metadata
and retained provenance. Dividends and other corporate actions remain unmodeled;
results are price return, not total shareholder return.

## 4. Repeatable application workflow

1. Start backend/frontend with the [README commands](../README.md#local-development).
   Open Datasets and expand **Offline import guide & templates**.
2. For a safe first run, click **Load synthetic example**, review the JSON, then
   **Import dataset**. Alternatively upload the downloadable CSV/JSON pair.
   It contains nine invented daily observations, including nonmarket session
   labels; it is not a calendar-completeness example.
3. Inspect source, adjustment/volume/split declarations, actual range/count,
   warnings and hashes. Reimporting identical bytes/effective metadata selects
   the same dataset with its original timestamp.
4. Open Backtest. Use buy and hold, starting cash `1000.00`, entire observed
   interval, commission `0.00` and slippage `0`. Run it. Independent expected
   result: buy 100 shares at the second observed open of $10; final close $8;
   final equity **$800**, price return **-20%**, **100 open shares**. No forced
   sale. Inspect actual fills/equity observations, unavailable metric reasons
   and expanded audit evidence. PASS covers only its named condition.
5. Open in Saved Research. Note the experiment ID. **Reproduce saved experiment**
   executes current code using retained inputs; cached retrieval is separate.
   Inspect economic and implementation equality individually.
6. Stop both servers, retain the same SQLite database, restart using the same
   commands/database path, reopen the ID and reproduce again. No browser storage
   holds financial results. Keep available disk space for SQLite/browser writes.
7. To see a valid-but-blocked import, upload the same invented CSV with the
   conservative local-file template (clearly label any test identity invented).
   Import succeeds, execution fails D04 even with coverage acknowledged. Do not
   edit unknown declarations solely to obtain a result.

Original CSV bytes and effective metadata determine identity. Changing CSV line
endings/BOM or declarations intentionally creates a different identity; metadata
formatting alone does not. Linked evidence files are not embedded. Retain source
records/database yourself. Reproduction neither restores archived source code
nor establishes historical truth, significance or future profitability.

## 5. Read errors without weakening the data policy

| Error or symptom | Useful action |
| --- | --- |
| CSV `field`, `row` diagnostic | Inspect that physical source line and the source specification; fix/export explicitly or reject the source, preserving the original |
| Metadata missing/unknown/invalid field | Use supported names/types/enums; keep unsupported facts unknown, not invented |
| `D04 eligibility requires...` | Review unadjusted/consistent OHLC, raw volume and interval split evidence; import success did not verify them |
| Real-data coverage acknowledgment required | Read the limitation and use the existing checkbox; it does not repair missing sessions |
| Price/range/precision or evaluation-window failure | Choose supported inputs/observed dates; do not silently round or change financial semantics |
| Backend unavailable / storage unavailable | Start the correct local services and check access/disk resources; no successful write is claimed |
| Reproduction mismatch / implementation changed / unavailable | Read distinct equality flags and limitations; preserve the original record and investigate evidence/version changes |

Phase 8 observed a transient SQLite 503 / browser ENOSPC. Its cause remains
unresolved; passing later runs do not prove a permanent fix. Actual current
verification and failures belong in [release validation](RELEASE_VALIDATION.md).
