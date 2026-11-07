import { Component, useEffect, useRef, useState, type ReactNode } from 'react';
import { api } from './api/client';
import type { Dataset, Experiment } from './api/schemas';
import { useRemote } from './lib/useRemote';
import { ErrorPanel, Loading } from './components/Common';
import { Datasets } from './pages/Datasets';
import { Research } from './pages/Research';
import { SavedResearch } from './pages/SavedResearch';

type Page = 'datasets' | 'backtest' | 'experiments' | 'saved';
const pages: { id: Page; label: string; path: string }[] = [
  { id: 'datasets', label: 'Datasets', path: 'M4 5h16v14H4z M4 10h16 M9 5v14' },
  { id: 'backtest', label: 'Backtest', path: 'M4 19V5 M4 19h16 M7 14l4-4 4 2 5-7' },
  { id: 'experiments', label: 'Experiments', path: 'M9 3h6 M10 3v6l-6 10h16L14 9V3 M8 14h8' },
  { id: 'saved', label: 'Saved Research', path: 'M6 3h12v18l-6-4-6 4z' },
];
function route(): Page { const key = location.hash.slice(1); return pages.some(p => p.id === key) ? key as Page : 'datasets'; }
function persistedId(): string | null { try { return localStorage.getItem('quantlab.selectedDataset'); } catch { return null; } }

class RenderBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() { return this.state.failed ? <div className="panel" role="alert"><h1>This view could not be displayed</h1><p>Reload the dashboard and check that the backend and frontend versions match. Saved research remains on the backend.</p>
    <button className="button primary" onClick={() => location.reload()}>Reload dashboard</button></div> : this.props.children; }
}

export default function App() {
  const [page, setPage] = useState<Page>(route), [dataset, setDataset] = useState<Dataset | null>(null);
  const [restoreError, setRestoreError] = useState<unknown>(null), [restoring, setRestoring] = useState(!!persistedId());
  const [initialSaved, setInitialSaved] = useState<Experiment | null>(null), [healthRevision, setHealthRevision] = useState(0);
  const health = useRemote(signal => api.health(signal), [healthRevision]);
  const restore = useRef<AbortController | null>(null);
  useEffect(() => { const change = () => { const key = location.hash.slice(1); if (pages.some(p => p.id === key)) { setPage(key as Page); window.scrollTo({ top: 0 }); } }; window.addEventListener('hashchange', change); return () => window.removeEventListener('hashchange', change); }, []);
  useEffect(() => {
    const id = persistedId(); if (!id) return;
    const controller = new AbortController(); restore.current = controller;
    api.dataset(id, controller.signal).then(value => { if (!controller.signal.aborted) setDataset(value); })
      .catch(error => { if (!controller.signal.aborted) setRestoreError(error); })
      .finally(() => { if (!controller.signal.aborted) setRestoring(false); });
    return () => controller.abort();
  }, []);
  function navigate(next: Page) { location.hash = next; setPage(next); window.scrollTo({ top: 0 }); }
  function select(value: Dataset) { restore.current?.abort(); setDataset(value); setRestoreError(null); setRestoring(false);
    try { localStorage.setItem('quantlab.selectedDataset', value.dataset_id); } catch { /* Preference only; retained research is server-side. */ } }
  function openSaved(value: Experiment) { setInitialSaved(value); navigate('saved'); }
  return <div className="app-shell"><a className="skip-link" href="#main-content">Skip to content</a>
    <aside className="sidebar"><a className="brand" href="#datasets"><span className="brand-mark" aria-hidden="true">Q<span>·</span></span><span>QuantLab<small>RESEARCH WORKSPACE</small></span></a>
      <p className="nav-label">WORKSPACE</p><nav aria-label="Primary navigation">{pages.map(item => <a key={item.id} href={`#${item.id}`} aria-current={page === item.id ? 'page' : undefined}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={item.path} /></svg>{item.label}<span aria-hidden="true">↗</span>
      </a>)}</nav>
      <div className="sidebar-context"><span className="sidebar-dot" />LOCAL RESEARCH<p>One instrument.<br />Daily observations.<br />Evidence kept in view.</p></div>
      <div className="sidebar-footer"><span>PRICE RETURN ONLY</span><p>Dividends excluded.<br />Research is not a forecast.</p></div>
    </aside>
    <div className="workspace"><header className="topbar"><span className="breadcrumb">WORKSPACE <span>/</span> {pages.find(p => p.id === page)?.label}</span>
      <button className={`connection ${health.state === 'ready' ? 'connected' : ''}`} onClick={() => setHealthRevision(n => n + 1)} title="Check backend connection" disabled={health.state === 'loading'}>
        <span className="connection-dot" />{health.state === 'loading' ? 'Checking backend…' : health.state === 'ready' ? 'Backend connected' : 'Backend unavailable'}</button></header>
      <main id="main-content"><RenderBoundary>{!!restoreError && <div className="restore-error"><p>Choose a retained dataset again if the previous selection is unavailable.</p><ErrorPanel error={restoreError} /></div>}
        {restoring ? <Loading>Restoring selected dataset…</Loading> : page === 'datasets' ? <Datasets selected={dataset} onSelect={select} goBacktest={() => navigate('backtest')} />
          : page === 'saved' ? <SavedResearch key={initialSaved?.experiment_id || 'history'} dataset={dataset} initial={initialSaved} goBacktest={() => navigate('backtest')} />
            : <Research key={page} dataset={dataset} experiments={page === 'experiments'} goDatasets={() => navigate('datasets')} openSaved={openSaved} />}
      </RenderBoundary></main><footer className="workspace-footer"><span>QuantLab / Local research</span><span>Unverified market declarations and unassessed risks remain visible.</span></footer>
    </div>
  </div>;
}
