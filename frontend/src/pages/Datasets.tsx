import { useEffect, useRef, useState, type FormEvent } from 'react';
import { OfflineGuide } from '../components/OfflineGuide';
import { api } from '../api/client';
import type { Dataset } from '../api/schemas';
import { useRemote } from '../lib/useRemote';
import { MAX_METADATA_BYTES, readCsv, validateUpload } from '../lib/upload';
import { shortId, timestamp } from '../lib/format';
import { Empty, ErrorPanel, Loading, PageIntro, Pager } from '../components/Common';

export function DatasetDetails({ dataset }: { dataset: Dataset }) {
  const m = dataset.metadata, v = dataset.validation;
  return <section className="panel dataset-details"><div className="panel-heading"><div><p className="eyebrow">Selected dataset</p><h2>{m.symbol} <span className="neutral-badge">{m.source_kind === 'synthetic' ? 'Invented input' : 'Local file'}</span></h2></div>
    <span className="neutral-badge">Validated import</span></div>
    <p className="notice">Import validation does not establish simulation eligibility. The backend checks eligibility when research runs.</p>
    <div className="fact-grid"><div><small>Observed range</small><strong>{v.first_date} — {v.last_date}</strong></div><div><small>Rows / currency</small><strong>{v.row_count.toLocaleString('en-US')} / {m.currency}</strong></div>
      <div><small>Source</small><strong>{m.source_name}</strong></div><div><small>Adjustment basis</small><strong>{m.adjustment_basis}</strong></div>
      <div><small>Coverage</small><strong>{v.coverage_assessment} · {m.session_coverage}</strong></div><div><small>Split declaration</small><strong>{m.split_status}</strong></div>
    </div>
    <details><summary>Provenance, declarations and validation</summary><dl className="metadata-list">
      {Object.entries(m).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{String(value)}</dd></div>)}
    </dl><ul>{v.warnings.map(text => <li key={text}>{text}</li>)}</ul>
      <p>Zero-volume rows: {v.zero_volume_rows}. BOM removed for parsing: {String(v.normalization.csv_bom_removed)}. Rows reordered: {String(v.normalization.rows_reordered)}. Trimmed fields: {v.normalization.whitespace_fields_trimmed}.</p>
      <p>{v.calendar_gaps.length} observed calendar gaps; these do not identify missing trading sessions.</p>
      <p>Imported {timestamp(dataset.created_at)} · Importer {v.importer_version}</p>
      <p className="hash-line">Dataset <code>{dataset.dataset_id}</code></p><p className="hash-line">Source SHA-256 <code>{v.source_sha256}</code></p><p className="hash-line">Metadata SHA-256 <code>{v.metadata_sha256}</code></p>
    </details></section>;
}

export function Datasets({ selected, onSelect, goBacktest }: { selected: Dataset | null; onSelect: (dataset: Dataset) => void; goBacktest: () => void }) {
  const [offset, setOffset] = useState(0), [refresh, setRefresh] = useState(0);
  const library = useRemote(signal => api.datasets(offset, signal), [offset, refresh]);
  const [csv, setCsv] = useState(''), [filename, setFilename] = useState(''), [metadata, setMetadata] = useState('');
  const [busy, setBusy] = useState(false), [choosing, setChoosing] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null), [selectionError, setSelectionError] = useState<unknown>(null), [notice, setNotice] = useState('');
  const locked = useRef(false), selectedRequest = useRef(0), fileRequest = useRef(0);
  useEffect(() => () => { selectedRequest.current += 1; fileRequest.current += 1; }, []);
  async function example() {
    if (locked.current) return;
    locked.current = true; setBusy(true); setError(null); setNotice('');
    try {
      const [csvResponse, metadataResponse] = await Promise.all([fetch('/examples/nine_sessions.csv'), fetch('/examples/nine_sessions.metadata.json')]);
      if (!csvResponse.ok || !metadataResponse.ok) throw new Error('Example inputs could not be loaded. Choose local CSV and metadata files instead.');
      setCsv(await csvResponse.text()); setMetadata(await metadataResponse.text()); setFilename('nine_sessions.csv · invented example');
      setNotice('Invented nine-session inputs loaded. Review the declarations, then import.');
    } catch (error) { setError(error); } finally { locked.current = false; setBusy(false); }
  }
  async function submit(event: FormEvent) {
    event.preventDefault(); if (locked.current) return;
    selectedRequest.current += 1; setChoosing(null); setSelectionError(null);
    setError(null); setNotice('');
    let raw;
    try { raw = validateUpload(csv, metadata); } catch (error) { setError(error); return; }
    locked.current = true; setBusy(true);
    try {
      const imported = await api.importDataset(csv, raw);
      onSelect(imported); setNotice(imported.duplicate ? 'Identical dataset already retained. Its original import timestamp is preserved.' : 'Dataset imported and selected. Ready for backend eligibility checks when you run research.');
      setOffset(0); setRefresh(n => n + 1);
    } catch (error) { setError(error); } finally { locked.current = false; setBusy(false); }
  }
  async function choose(id: string) {
    const request = ++selectedRequest.current; setChoosing(id); setSelectionError(null);
    try { const dataset = await api.dataset(id); if (request === selectedRequest.current) onSelect(dataset); }
    catch (error) { if (request === selectedRequest.current) setSelectionError(error); }
    finally { if (request === selectedRequest.current) setChoosing(null); }
  }
  return <><PageIntro eyebrow="Data foundation" title="Dataset library">Retain the original observations. Keep their provenance and limitations in view.</PageIntro>
    <div className="dataset-layout"><form className="panel import-panel" onSubmit={submit}><div className="panel-heading"><div><p className="eyebrow">CSV + JSON metadata</p><h2>Import observations</h2></div><span className="step-label">01</span></div>
      <fieldset disabled={busy}><label className="file-field">OHLCV CSV<input type="file" accept=".csv,text/csv" aria-label="OHLCV CSV" aria-describedby="csv-file-help" onChange={async e => {
        const file = e.target.files?.[0]; if (!file) return;
        const revision = ++fileRequest.current; locked.current = true; setBusy(true); setError(null); setNotice(''); setCsv(''); setFilename(file.name);
        try { const text = await readCsv(file); if (revision === fileRequest.current) setCsv(text); }
        catch (error) { if (revision === fileRequest.current) setError(error); }
        finally { if (revision === fileRequest.current) { locked.current = false; setBusy(false); } }
      }} /><small id="csv-file-help">{filename || 'UTF-8 · maximum 10 MiB · original bytes retained'}</small></label>
      <div className="metadata-heading"><label htmlFor="metadata-json">JSON metadata</label><label className="file-link">Upload JSON<input type="file" accept=".json,application/json" aria-label="Upload metadata JSON" onChange={async e => {
        const file = e.target.files?.[0]; if (!file) return;
        const revision = ++fileRequest.current; locked.current = true; setBusy(true); setError(null); setNotice(''); setMetadata('');
        try { if (file.size > MAX_METADATA_BYTES) throw new Error('Metadata exceeds the 64 KiB input limit.');
          const text = new TextDecoder('utf-8', { fatal: true }).decode(await file.arrayBuffer()); if (revision === fileRequest.current) setMetadata(text); }
        catch (error) { if (revision === fileRequest.current) setError(error); }
        finally { if (revision === fileRequest.current) { locked.current = false; setBusy(false); } }
      }} /></label></div>
      <textarea id="metadata-json" className="code-input" value={metadata} rows={11} spellCheck={false} onChange={e => { setMetadata(e.target.value); setError(null); setNotice(''); }} placeholder={'{\n  "contract_version": 1,\n  "symbol": "...",\n  "source_kind": "local_file",\n  ...\n}'} />
      <p className="field-help">Supply the required identity, source and adjustment declarations. Omitted optional fields become unknown; nothing is inferred from a filename.</p>
      <div className="button-row"><button className="button primary" type="submit">{busy ? 'Processing…' : 'Import dataset →'}</button><button type="button" className="button secondary" onClick={example}>Load synthetic example</button></div>
      </fieldset>{busy && <Loading>Validating or loading input…</Loading>}<ErrorPanel error={error} />
      {notice && <div className="success-note" role="status">{notice}</div>}
      <OfflineGuide />
    </form>
    <section className="panel library-panel"><div className="panel-heading"><div><p className="eyebrow">Retained on this backend</p><h2>Available datasets</h2></div>
      <button className="text-button" onClick={() => setRefresh(n => n + 1)} disabled={library.state === 'loading'}>Refresh ↻</button></div>
      {library.state === 'loading' && <Loading>Loading retained datasets…</Loading>}<ErrorPanel error={library.error} /><ErrorPanel error={selectionError} />
      {library.data && <>{library.data.items.length === 0 ? <Empty title="Your research starts here">Import your first dataset or load the clearly labeled synthetic example. Successful imports are retained by the backend.</Empty>
        : <div className="dataset-list">{library.data.items.map(row => <button className={`dataset-row ${selected?.dataset_id === row.dataset_id ? 'selected' : ''}`} key={row.dataset_id} onClick={() => choose(row.dataset_id)} disabled={choosing === row.dataset_id}>
          <span className="dataset-glyph" aria-hidden="true">▥</span><span><strong>{selected?.dataset_id === row.dataset_id ? selected.metadata.symbol : 'Dataset'} <code>{shortId(row.dataset_id)}</code></strong>
            <small>{row.first_date} — {row.last_date}</small><small>{row.row_count.toLocaleString('en-US')} observations{selected?.dataset_id === row.dataset_id ? ' · Selected' : ''}</small></span><span className="row-arrow" aria-hidden="true">{choosing === row.dataset_id ? '…' : '↗'}</span>
        </button>)}</div>}<Pager offset={offset} count={library.data.items.length} onChange={setOffset} /></>}
      <div className="library-note"><b>Validated is not verified.</b><p>Source truth, session coverage and corporate-action declarations remain explicit limitations.</p></div>
    </section></div>
    {selected && <><div className="selected-actions"><p>Selected for your next research request.</p><button className="button primary" onClick={goBacktest}>Open Backtest →</button></div><DatasetDetails dataset={selected} /></>}
  </>;
}
