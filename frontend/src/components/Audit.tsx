import { useState } from 'react';
import { statuses, type Finding } from '../api/schemas';

export function StatusPill({ status }: { status: Finding['status'] }) {
  return <span className={`status-pill ${status.toLowerCase()}`} aria-label={status}>{status.replaceAll('_', ' ')}</span>;
}
export function Audit({ findings }: { findings: Finding[] }) {
  const [filter, setFilter] = useState('ALL');
  return <section className="panel audit-panel" aria-labelledby="audit-title"><div className="panel-heading"><div>
    <p className="eyebrow">Evidence & limitations</p><h2 id="audit-title">Integrity audit</h2></div>
    <label className="compact-label">Assessment<select value={filter} onChange={e => setFilter(e.target.value)} aria-label="Audit status filter">
      <option value="ALL">All findings</option>{statuses.map(status => <option key={status} value={status}>{status.replaceAll('_', ' ')}</option>)}
    </select></label></div>
    <p className="muted">Each assessment covers its stated evidence. Unassessed risks are not verified safe.</p>
    <div className="audit-counts">{statuses.map(status => <span key={status}><StatusPill status={status} /> <b>{findings.filter(f => f.status === status).length}</b></span>)}</div>
    <div className="findings">{findings.filter(f => filter === 'ALL' || f.status === filter).map(finding => <details key={finding.rule_id} className="finding">
      <summary><StatusPill status={finding.status} /><span><strong>{finding.title}</strong><code>{finding.rule_id}</code></span><span className="chevron" aria-hidden="true">⌄</span></summary>
      <div className="finding-body"><p>{finding.explanation}</p>{finding.severity && <p><strong>Severity:</strong> {finding.severity}</p>}
        <ul className="evidence-list">{finding.evidence.map((evidence, i) => <li key={i}><code>{evidence.reference}</code><p><b>Observed:</b> {evidence.observed}</p>
          {evidence.expected !== null && <p><b>Expected:</b> {evidence.expected}</p>}
          {(evidence.order_id !== null || evidence.session !== null) && <small>{evidence.order_id !== null && `Order ${evidence.order_id} `}{evidence.session}</small>}
        </li>)}</ul>{finding.suggested_action && <p className="notice">{finding.suggested_action}</p>}
      </div></details>)}</div>
    {findings.every(f => filter !== 'ALL' && f.status !== filter) && <p className="inline-empty">No findings with this assessment.</p>}
  </section>;
}
