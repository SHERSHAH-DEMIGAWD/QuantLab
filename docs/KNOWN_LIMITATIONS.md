# Known limitations

This is the consolidated release summary. Detailed financial/transport rules
remain in their contracts; this document does not supersede them.

- **Limited real-history evidence:** private Alpha Vantage public samples supplied
  100 daily bars each for IBM/MSFT, 2026-06-11..2026-11-02. Existing import,
  three strategies, costs, audit, robustness, SQLite retention and reproduction
  passed; [actual evidence](REAL_MARKET_VALIDATION.md). This does not verify
  longer histories, other securities, source accuracy against another vendor,
  or an underlying exchange feed. MSFT's provider split query was unavailable;
  its issuer history supplied separate interval evidence. No product provider
  adapter/live quote, profitability, prediction, liquidity or bias-free claim.
  Private observations are excluded from Git; the six opt-in cases skip without
  the retained snapshot. Public sample availability can change.
- **Conservative eligibility:** consistent unadjusted OHLC, raw volume and
  supported none-reported split evidence are required. Missing evidence stays
  unknown and blocks execution. Import validity does not prove eligibility,
  rights or source truth. No corporate actions/dividends, symbol changes or
  delisting proceeds are modeled. Returns exclude dividends.
- **Sessions/liquidity:** exchange coverage is unverified, even when declared
  complete; real-file coverage needs acknowledgment. Next observed open is a
  proxy for the next tradable session. Daily volume does not establish opening
  liquidity. No spread/depth/partial-fill or settlement-market realism claim.
- **Small research model:** one instrument, daily USD bars, long-only integer
  shares, no leverage, three built-ins. Explicit Decimal/cash/share limits apply.
  Final holdings remain open; no forced sale or hypothetical exit fee.
- **Statistics/selection:** 252 sessions and 365.25 days are conventions.
  Undefined/numerically unavailable metrics retain reasons; short annualization
  is extrapolation. Statistical calculations cross a documented float boundary.
  One held-out period does not establish generalization; retuning from its
  outcomes contaminates it. Unequal subperiod returns are not a quality rank.
- **Audit scope:** PASS applies only to stated evidence. Survivorship, all
  look-ahead absence, source/event truth, significance and overfitting are not
  certified. Statistical formulas have reference tests but are not independently
  re-audited by every integrity report. There is no trust score.
- **Reproduction:** original submitted CSV/effective metadata/request are retained;
  hashes identify inputs, not truth or licensing. Referenced evidence files are
  not embedded. Current economic equality and implementation equality differ.
  Source hashes do not archive/restore original code or its full environment.
  Checksums do not resist deliberate database rewriting. Preserve the database
  and original records yourself; there is no backup/encryption/migration service.
- **Local application:** single-user loopback only; no authentication, public
  deployment or live trading. Requests run synchronously with body/configuration/
  aggregate-bar limits; these are not wall-time or total-browser-memory bounds.
  Exact textual money differs from approximate canvas coordinates. No formal
  accessibility audit, concurrency/load test or cross-platform certification.
- **Environment:** verified on Windows 11, CPython 3.15.0, Node 24.15.0 and
  installed Edge. Python 3.12 is declared by packaging but was not tested; other
  browser/OS combinations are unverified. Frontend dependencies are locked;
  Python direct dependencies are pinned, while transitive resolution can change.
  The verified inventory is retained with release evidence.
- **Reliability:** historical Phase 8 SQLite 503/browser ENOSPC was not reproduced
  or explained. Later successful runs do not establish a permanent fix. Source,
  temp files, SQLite and browser writes share the same finite disk. Sandbox
  process/temp-directory restrictions required approved external execution;
  they were not worked around in application code.
- **Ownership/release:** implementation and validation are AI-assisted. Owner
  explanation/recreation are pending, not inferred from passing tests. This is
  a local demonstration deliverable, with no committed/tagged/published release.
  Benchmarks describe this machine/workload, not production scalability.

Evidence and reliability investigation: [RELEASE_VALIDATION.md](RELEASE_VALIDATION.md).
Measured results: [BENCHMARKS.md](BENCHMARKS.md). Learning/claim boundaries:
[RESUME_AND_INTERVIEW.md](RESUME_AND_INTERVIEW.md).
