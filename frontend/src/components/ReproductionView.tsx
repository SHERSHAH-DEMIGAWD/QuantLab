import { useRef, useState } from 'react';
import { api } from '../api/client';
import type { Reproduction } from '../api/schemas';
import { ErrorPanel, Loading } from './Common';

export function ReproductionView({ experimentId }: { experimentId: string }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState<unknown>(null), [result, setResult] = useState<Reproduction | null>(null);
  const locked = useRef(false);
  async function reproduce() {
    if (locked.current) return;
    locked.current = true; setBusy(true); setError(null); setResult(null);
    try { setResult(await api.reproduce(experimentId)); } catch (error) { setError(error); }
    finally { locked.current = false; setBusy(false); }
  }
  return <section className="panel reproduction"><div className="panel-heading"><div><p className="eyebrow">Retained inputs → fresh execution</p><h2>Reproduce this research</h2></div>
    <button className="button secondary" onClick={reproduce} disabled={busy}>{busy ? 'Reproducing…' : 'Reproduce saved experiment'}</button></div>
    <p className="muted">Rerun the saved request against retained data. Retrieval alone is not reproduction.</p>
    {busy && <Loading>Revalidating inputs and executing the saved request…</Loading>}<ErrorPanel error={error} />
    {result && <div className={`reproduction-result ${result.status}`} role="status"><h3>{result.status === 'matched' ? 'Recorded outputs match' : result.status === 'mismatch' ? 'Economic outputs differ' : 'Implementation identity changed'}</h3>
      <div className="fact-grid"><div><small>Economic outputs</small><strong>{result.economic_match ? 'Match saved outputs' : 'Differ from saved outputs'}</strong></div>
        <div><small>Recorded implementation</small><strong>{result.implementation_match ? 'Identifiers match' : 'Identifiers differ'}</strong></div></div>
      {result.difference_paths.length > 0 && <ul>{result.difference_paths.map(path => <li key={path}><code>{path}</code></li>)}</ul>}
      <details><summary>Evidence and limitations</summary><ul>{result.limitations.map(item => <li key={item}>{item}</li>)}</ul>
        <p className="hash-line">Saved economic SHA-256 <code>{result.saved_economic_sha256}</code></p>
        <p className="hash-line">Current economic SHA-256 <code>{result.current_economic_sha256}</code></p>
      </details></div>}
  </section>;
}
