import { useRef, useState, type FormEvent } from 'react';
import { api } from '../api/client';
import type { Dataset, Experiment } from '../api/schemas';
import { shortId, timestamp } from '../lib/format';
import { useRemote } from '../lib/useRemote';
import { Empty, ErrorPanel, Loading, PageIntro, Pager } from '../components/Common';
import { ResultView } from '../components/ResultView';

export function SavedResearch({ dataset, initial, goBacktest }: { dataset: Dataset | null; initial: Experiment | null; goBacktest: () => void }) {
  const [offset, setOffset] = useState(0), [filter, setFilter] = useState(false), [refresh, setRefresh] = useState(0);
  const list = useRemote(signal => api.experiments(offset, filter ? dataset?.dataset_id : undefined, signal), [offset, filter, dataset?.dataset_id, refresh]);
  const [record, setRecord] = useState<Experiment | null>(initial), [id, setId] = useState('');
  const [busy, setBusy] = useState(false), [error, setError] = useState<unknown>(null);
  const request = useRef(0);
  async function open(identifier: string) {
    setRecord(null); setError(null);
    if (!/^[a-f0-9]{32}$/.test(identifier)) { setError(new Error('Enter the full 32-character lowercase experiment ID.')); return; }
    const revision = ++request.current; setBusy(true);
    try { const saved = await api.experiment(identifier); if (revision === request.current) setRecord(saved); }
    catch (error) { if (revision === request.current) setError(error); }
    finally { if (revision === request.current) setBusy(false); }
  }
  function submit(event: FormEvent) { event.preventDefault(); if (!busy) void open(id.trim()); }
  return <><PageIntro eyebrow="Retained evidence" title="Saved Research">Reopen the complete record. Reproduce it with a fresh computation.</PageIntro>
    <section className="panel"><div className="panel-heading"><div><p className="eyebrow">Completed experiments</p><h2>Research history</h2></div>
      <button className="text-button" onClick={() => setRefresh(n => n + 1)} disabled={list.state === 'loading'}>Refresh ↻</button></div>
      <div className="saved-controls"><label className="checkbox"><input type="checkbox" checked={filter} disabled={!dataset} onChange={e => { setFilter(e.target.checked); setOffset(0); }} />Only selected dataset</label>
        <form className="id-form" onSubmit={submit}><label>Open by experiment ID<input value={id} onChange={e => setId(e.target.value)} maxLength={32} placeholder="Full experiment ID" /></label><button className="button secondary small" disabled={busy}>Open</button></form></div>
      {list.state === 'loading' && <Loading>Loading saved research…</Loading>}<ErrorPanel error={list.error} />
      {list.data && <>{list.data.items.length ? <div className="table-scroll"><table><caption>Saved experiments</caption><thead><tr><th>Experiment</th><th>Mode</th><th>Dataset</th><th>Created · UTC</th><th>Inspect</th></tr></thead>
        <tbody>{list.data.items.map(item => <tr key={item.experiment_id}><td><code>{shortId(item.experiment_id)}</code></td><td>{item.mode.replaceAll('_', ' ')}</td>
          <td><code>{shortId(item.dataset_id)}</code></td><td>{timestamp(item.created_at)}</td><td><button className="text-button" onClick={() => open(item.experiment_id)} disabled={busy} aria-label={`Open saved ${item.experiment_id}`}>Open ↗</button></td></tr>)}</tbody></table></div>
        : <Empty title="No saved research on this page" action={<button className="button primary" onClick={goBacktest}>Open Backtest →</button>}>Successful research requests are saved automatically. Reopen them here after restarting the application.</Empty>}
        <Pager offset={offset} count={list.data.items.length} onChange={setOffset} /></>}
    </section>
    <ErrorPanel error={error} />{busy && <section className="panel"><Loading>Opening the retained research record…</Loading></section>}
    {record && <ResultView key={record.experiment_id} record={record} showReproduction />}
  </>;
}
