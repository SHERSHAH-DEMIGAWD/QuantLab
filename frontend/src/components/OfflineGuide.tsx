export function OfflineGuide() {
  return <details className="input-notes" id="offline-import-guide"><summary>Offline import guide & templates</summary>
    <p><strong>Provider import is unavailable.</strong> Use a legitimately acquired local file, or the invented example. No API key or network data service is required.</p>
    <ol>
      <li>Keep your original export, its source, retrieval date, usage terms and any split-event evidence. Do not upload or share data you lack permission to use.</li>
      <li>Supply UTF-8 CSV with this exact header: <code>date,open,high,low,close,volume</code>. One U.S. stock/ETF, USD, daily America/New_York session dates; no extra index or adjusted-close column.</li>
      <li><a href="/examples/local_file.metadata.template.json" download>Download local metadata template</a>, replace the identity/source placeholders, then upload the JSON. It deliberately starts with unknown declarations and cannot establish simulation eligibility.</li>
      <li>Import, then inspect the retained provenance, observed range and warnings below. A validated import is not permission to simulate.</li>
      <li>Open Backtest, state your dates/capital/costs, then inspect equity, fills and audit findings. Open Saved Research to retrieve or freshly reproduce the run.</li>
    </ol>
    <p>For simulation, the backend requires consistent <code>unadjusted</code> OHLC, <code>raw</code> volume, <code>none_reported</code> splits and explicit split evidence. Declare these only when supported for the imported interval. A missing, failed or incomplete event check stays <code>unknown</code>; do not copy the synthetic example's evidence into real metadata.</p>
    <p>Use <code>source_kind: local_file</code> for historical observations. The research form also requires acknowledgment of unverified real-data coverage, even when declared complete. That acknowledgment does not bypass adjustment or split restrictions. Dividends are excluded.</p>
    <p>Unknown/adjusted bases and present/unknown splits may be retained, but research is blocked. Inconsistent OHLC declarations, invalid rows and unsupported metadata fail import. Prices must be positive plain decimals with at most six significant fractional digits; volume is a nonnegative integer. No filling, interpolation or invalid-row dropping.</p>
    <p>Required metadata: contract_version, symbol, exchange, currency, frequency, session_timezone, source_kind, source_name, adjustment_basis. Optional omissions remain unknown. Check the reported field and physical CSV row for import errors; preserve useful input while correcting the source explicitly.</p>
    <p>For a reproducible practice run, use “Load synthetic example”, then import and run buy and hold with $1,000 and zero costs: final equity $800, 100 shares open, price return -20%. These are invented observations, not historical market evidence.</p>
    <p><a href="/examples/nine_sessions.csv" download>Download synthetic CSV</a> · <a href="/examples/nine_sessions.metadata.json" download>Download synthetic metadata</a>. Keep the backend SQLite file across restarts; reopening retrieves a saved result, while reproduction recomputes it from retained inputs.</p>
  </details>;
}
