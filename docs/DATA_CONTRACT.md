# Phase 1 importer usage and output

Implemented contract v1. Policy and its original proposals/amendments live in
[D03](DECISIONS.md#d03---local-historical-data-contract-v1). Synthetic examples
are invented observations, not stock-market history. No network access occurs
during import or tests.

For the user-facing CSV/JSON preparation and repeatable retained-research path,
see the [Phase 9 offline guide](OFFLINE_DATA_GUIDE.md). Provider integration is
unavailable/deferred; no importer or eligibility policy changed in that phase.

## Public API

After the [README setup](../README.md#local-development), from the repository
root:

```python
from quantlab.data import DataValidationError, load_dataset, load_dataset_bytes

try:
    dataset = load_dataset(
        "backend/tests/fixtures/synthetic_daily.csv",
        "backend/tests/fixtures/synthetic_daily.metadata.json",
    )
except DataValidationError as exc:
    for issue in exc.issues:
        print(issue.source, issue.row, issue.field, issue.code, issue.message)
    print(exc.error_count, exc.truncated)
else:
    print(dataset.report.dataset_id)
    print(dataset.bars[0].date, dataset.bars[0].close)
    print(dataset.report.warnings)
```

`load_dataset` either returns one immutable `Dataset` or raises
`DataValidationError`. An exception has no dataset or accepted-row result.
Constructing a dataclass directly is not a substitute for validated import.

Phase 7 also exposes `load_dataset_bytes(csv_bytes, metadata_json_bytes)` for
uploads and retained input reconstruction. It shares the exact CSV parser,
metadata validation, report builder and identity logic with local file imports;
no temporary file or alternate market-data validator. The
[backend contract](API_CONTRACT.md) defines its separate HTTP body/metadata caps
and original-byte retention policy. Existing file-import behavior is unchanged.

| Returned value | Contents |
| --- | --- |
| `Dataset.bars` | Tuple of frozen `Bar` values, strictly ascending by `date`; OHLC as exact `Decimal`, volume as `int`, original physical `source_row` starting at 1 |
| `Dataset.metadata` | Frozen `Metadata` with all effective fields, including explicit uncertainty defaults |
| `Dataset.report` | Importer version, count/range, input byte count, three hashes, normalization, calendar gaps, zero-volume count, warnings, coverage assessment |

`importer_version=1.0.0` identifies this import behavior; package version is
`0.1.0`. No timestamp or machine path participates in successful results.

## Parsing and diagnostics

- CSV is UTF-8 with an optional leading BOM. The six headers must appear in
  the exact D03 order. Standard CSV quoting and CRLF/LF records are supported.
  Blank data records, extra/missing columns, invalid encoding, and bad quoting
  fail. Source row numbers are physical starting lines, including multiline
  quoted fields. A CSV syntax error reports the parser's failure line.
- Header/value surrounding whitespace is stripped and counted. BOM removal and
  chronological reordering are reported separately. No price adjustment,
  interpolation, resampling, deduplication, or inferred bar is performed.
- Prices use ASCII digits with an optional decimal part: `10`, `10.25`, and
  `0.123456000` are allowed; `.5`, `1.`, signs, exponents, NaN, and infinity
  are rejected. Insignificant trailing fractional zeros do not count toward
  the six-digit precision limit. Decimal construction preserves all accepted
  digits without rounding or relying on the current arithmetic context.
- Volume permits zero and ASCII integer text. Python's default integer-text
  conversion safety limit (4,300 digits in the tested interpreter) applies;
  an excess produces `invalid_volume`. Python's CSV parser also limits a field
  to 131,072 characters by default; excess produces `malformed_csv`. These
  parser safeguards are not financial precision/size rules for a simulator.
  The importer does not change process-wide parser or integer settings.
- The 10 MiB total CSV limit includes BOM and line endings. Reading is bounded
  to limit + 1 byte, including for files that grow after opening. Exactly the
  limit is accepted if otherwise valid. Oversize produces `input_too_large`.
- JSON sidecars accept UTF-8/BOM and reject malformed JSON, duplicate keys,
  nonstandard NaN/infinity, non-object roots, unknown keys, invalid types,
  unsupported versions, and an explicit inconsistent-OHLC declaration.
  Every optional field defaults to `unknown`, as listed in the dated D03
  amendment. JSON `false`, string `unknown`, and a missing field have distinct
  semantics; only the latter two produce the same effective uncertainty.
- `ValidationIssue` has `source`, `code`, `message`, optional `row` and `field`.
  Metadata `field` names are top-level JSON field paths. At most 100 issues are
  retained; `error_count` counts encountered issues and `truncated` reports
  omitted diagnostics. Scanning continues through recoverable data records.
  Invalid headers, undecodable bytes, or broken CSV syntax prevent full later
  record assessment; the count is not an exhaustive inventory of every defect.
  Error limits never cause successful import. Warnings are a short summary,
  including a zero-volume count rather than one warning per row.

## Identity and retention

`source_sha256` hashes the exact bytes read before decoding/normalization.
`metadata_sha256` hashes canonical JSON of **effective validated metadata**:
all fields/defaults; sorted keys; compact separators; UTF-8 with Unicode
preserved (`ensure_ascii=False`); no NaN. Metadata formatting, key order, and
omitted versus explicitly supplied defaults do not affect it.

`dataset_id` hashes canonical JSON with exactly `contract_version`,
`metadata_sha256`, and `source_sha256`. Row order, a CSV BOM, line endings,
price text, or changed relevant metadata intentionally change identity even
if normalized prices are economically equivalent. File paths and sidecar
formatting do not. The handwritten canonical reference in `test_data.py`
checks this format independently of the production serializer.

The loader does not copy/persist original files. Keep the original CSV and
sidecar to reproduce the input; hashes alone cannot reconstruct data or prove
truth, licensing, or data completeness.

## Calendar and adjustment limits

For consecutive observed dates separated by more than one day, `CalendarGap`
stores the previous date, next date, and the number of intervening calendar
days, exclusive of endpoints. January 5 to January 8 gives two such days.
No exchange calendar is loaded, so weekend labels are neither invented nor
automatically rejected. Coverage remains `unverified` even when the source
declares `declared_complete`.

Unknown, split-adjusted, and total-return-adjusted data can be imported with
their declarations and warnings. `ohlc_basis_consistent=false` fails regardless
of basis. Numerically coherent OHLC cannot establish that adjustment labels
are truthful. Unknown split status never means no splits. Dividends, split
events, revisions, survivorship, and opening liquidity are not verified or
processed.

Phase 2 can consume the ordered Decimal bars, source row references, metadata,
identity, and report. It must separately review D04-D05 and validate its own
numeric ranges, adjustment/corporate-action eligibility, and execution rules.
There is no eligibility flag, strategy return, or trading operation in Phase 1.
