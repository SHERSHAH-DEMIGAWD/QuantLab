# A 3-5 minute local technical demonstration

Use **invented observations**, not a claim about market profitability. Start
both services with the [README commands](../README.md#local-development)
before the demonstration. First-time dependency installation is outside this
3-5 minute script. Keep the same SQLite database for restart/reproduction.

| Time | Action and evidence to explain |
| --- | --- |
| 0:00-0:45 | Datasets -> **Load synthetic example** -> inspect metadata -> **Import dataset**. Show source/range/split declarations and the separate validated-import notice. Reimporting may select an identical retained dataset. |
| 0:45-1:30 | Open Backtest; buy and hold, `$1000.00`, zero commission/slippage, full interval. Run. Expected final equity `$800.00`, return `-20%`, 100 shares still open. |
| 1:30-2:15 | Inspect equity curve, exact equity observations, order decision/eligible sessions and fill. Explain why Jan 1 close produces a Jan 2 open fill and why no final sale is invented. Expand a PASS, WARNING and NOT_ASSESSED audit finding. |
| 2:15-3:15 | Experiments -> parameter grid -> SMA, fast windows `2,3`, slow windows `4,5`. Run four configurations plus reference. Discuss actual costs/windows rather than calling the best row predictive. |
| 3:15-4:00 | Open in Saved Research; inspect retained configuration and click **Reproduce saved experiment**. Economic match and implementation identity are separate. GET retrieval is not reproduction. |
| 4:00-5:00 | Show the offline guide/template or run chronological momentum training through Jan 6 and testing Jan 7-9, lookbacks `1,2`, threshold `0`. Selection freezes lookback 2; held-out return is `-54%`, with fresh `$1000` and six indicator-only warm-up bars. |

Suggested spoken explanation: this is a local, single-instrument research
simulator that makes timing, accounting and evidence inspectable. Synthetic
examples demonstrate software behavior; they establish no historical alpha or
real execution accuracy. Do not describe unassessed risks as verified safe.

## Optional checks after the short demonstration

- Fixed SMA backtest: explicitly set fast `2`, slow `3` (the UI default slow
  window is `5`), zero costs. Final equity `$910.00`, one closed trade, flat end.
- Fixed momentum: lookback `2`, threshold `0`, zero costs. Final equity `$910.00`.
- Buy and hold with commission `2.00` and slippage `100` bps: 98 shares at
  `$10.100000`, fee `$2.00`, residual cash `$8.20`, final equity `$792.20`.
- Cost sensitivity: first scenario is reference; higher fees may change integer
  exposure. Subperiods: Jan 1-3 and Jan 4-9 contain three/six observations and
  must not be interpreted as an equal-duration quality ranking.
- Note a saved ID; stop/restart both terminal processes without deleting/changing
  the SQLite file. Reopen that ID and freshly reproduce it.
- Unknown-split or adjusted metadata can import but must fail D04 execution.
  Invalid OHLC must report a useful physical-row/field error, not drop the row.

Normal valid experiments show no audit FAIL. Deliberately tampered timing/ledger
records produce FAIL in backend audit tests; component tests verify FAIL display.
The release browser check inspects the genuine empty FAIL filter. Do not inject
a fabricated failure into a valid result for a demonstration.

All workflow steps above have automated application evidence; desktop/mobile
screenshots were also visually inspected. The elapsed 3-5 minute presentation
is a suggested script, not a measured human rehearsal. Full commands/results
and verification boundaries: [RELEASE_VALIDATION.md](RELEASE_VALIDATION.md).
