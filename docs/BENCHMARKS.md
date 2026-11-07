# Measured engineering benchmarks

Measured 2026-11-03 (Asia/Calcutta), unchanged financial implementation. These
are software timings on invented inputs, not investment results or a speedup
claim. [Raw samples/identities](benchmark-results/phase10.json) and the
[fresh installed-version inventory](benchmark-results/environment.json) are
retained as small release evidence.

## Environment and method

- Windows 11 build 26200; AMD Ryzen AI 9 HX 370 with Radeon 890M, 12 physical
  cores / 24 logical processors; reported RAM 24,823,836,672 bytes.
- CPython 3.15.0, 64-bit MSC v.1951, SQLite 3.53.4. Fresh isolated installation
  of declared Python package/test dependencies; complete inventory linked above.
- `scripts/benchmark.py`, `time.perf_counter_ns`, enabled GC, one untimed warm-up
  **per operation and dataset**, then five timed repetitions. Result destruction
  is outside each timed interval. All raw samples, median/min/max are retained.
  No benchmark/test job ran concurrently with timing.
- No cache flushing, CPU affinity or governor control; OS/background activity
  remains possible. Cached source bytes and warm local SQLite/filesystem paths.
  This is not a cold-start, HTTP, browser or concurrent-user benchmark.
- Generator: calendar-day labels from 2000-01-01, triangular integer-cent closes
  with a 100-day cycle, prior-close opens, ten-cent high/low envelope, fixed
  volume. These are invented sessions including weekends. Inputs pass the actual
  importer and repeat byte-identically; hashes/byte sizes are retained.
- Cash `$10000.00`, commission `$0.50` per fill, slippage `5` bps. Single strategy:
  SMA(5,20). Grid: fast `[5,10]`, slow `[20,40]`, four candidates plus matching
  buy-and-hold reference, one full period/cost scenario, five runs total.

## Results

**Median milliseconds**, five samples per cell:

| Bars | Import/validate | SMA simulation | Five-run grid | Source-backed audit | SQLite retrieval |
| --- | ---: | ---: | ---: | ---: | ---: |
| 250 | 3.151 | 4.023 | 59.812 | 5.430 | 2.688 |
| 1,000 | 12.484 | 13.734 | 239.383 | 30.439 | 11.350 |
| 5,000 | 92.446 | 104.761 | 1291.182 | 151.862 | 51.416 |

Variability matters: the 5,000-bar simulation ranged 97.512-147.363 ms; the grid
1199.503-1410.431 ms. Other ranges are in the raw evidence. Three sizes and 75
samples do not establish tail latency, production capacity or an asymptotic fit.
No before/after optimization or throughput claim is made.

## Included work

| Operation | Included / excluded |
| --- | --- |
| Import/validate | Byte parser, metadata, sorting/report, identity; excludes generation and disk acquisition |
| SMA simulation | Existing preflight, streaming rule, next-open execution, full histories; excludes analytics/audit/HTTP |
| Five-run grid | Coordinator preflight, source fingerprint, five simulations, analytics, audits and comparisons; excludes SQLite/HTTP |
| Source-backed audit | Simulation, Dataset, exact source bytes, separate effective metadata, expected settings; includes original-row/identity verification, replay disabled |
| SQLite retrieval | Open/read full one-strategy saved record, checksums, JSON parsing; preparation/computation/initial INSERT/HTTP serialization excluded |

Each audit was checked for no FAIL; saved retrieval matched the untimed saved
record. Temporary benchmark databases were confined to ignored `.release-check`
and removed by their context manager after absolute-path checks.

## Reproduce

From the installed repository root:

```powershell
.\.venv\Scripts\python.exe scripts/benchmark.py --repeats 5
```

The recorded run used the fresh environment:

```powershell
.\.release-check\python\Scripts\python.exe scripts/benchmark.py --repeats 5
```

JSON records the script SHA-256 and 41-file backend source snapshot. A rerun
overwrites this small evidence file with new samples; preserve it if comparing
environments. No source optimization was introduced.

## Complexity, separately from measurements

For N rows, B input bytes and P result bytes: ingestion scans/hashes O(B) and
sorts O(N log N), retaining O(N) bars. With bounded arithmetic, streaming
simulation is O(N), with O(N) histories and bounded rolling windows. A fixed
R-run grid coordinates roughly O(RN) simulation/analysis/audit work plus source
hashing; preflight can scan the full imported Dataset even for a small window.
Source-row audit verification sorts parsed input, adding O(N log N) work for
that option. Retrieval decodes/checks O(P) data, not just a summary row. These
are code-derived bounds, not measurements beyond the sizes/configurations above.
