import { useState, type ReactNode } from 'react';
import { ApiError } from '../api/client';
import { metricText } from '../lib/format';
import type { Metric } from '../api/schemas';

export function PageIntro({ eyebrow, title, children }: { eyebrow: string; title: string; children: ReactNode }) {
  return <header className="page-intro"><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p className="lede">{children}</p></header>;
}
export function Loading({ children = 'Loading…' }: { children?: ReactNode }) {
  return <div className="loading" role="status"><span className="spinner" aria-hidden="true" />{children}</div>;
}
export function Empty({ title, children, action }: { title: string; children: ReactNode; action?: ReactNode }) {
  return <div className="empty"><span className="empty-mark" aria-hidden="true">↗</span><h3>{title}</h3><p>{children}</p>{action}</div>;
}
export function ErrorPanel({ error }: { error: unknown }) {
  if (!error) return null;
  const message = error instanceof Error ? error.message : 'The operation could not be completed. Please try again.';
  const details = error instanceof ApiError ? error.details : null;
  const issues: Record<string, unknown>[] = Array.isArray(details) ? details : details && typeof details === 'object' && 'issues' in details
    && Array.isArray(details.issues) ? details.issues : [];
  return <div className="error-panel" role="alert"><strong>{message}</strong>
    {error instanceof ApiError && <p className="error-code">{error.code}{error.status ? ` · HTTP ${error.status}` : ''}</p>}
    {issues.length > 0 && <ul>{issues.slice(0, 100).map((item, index) => <li key={index}>
      {Array.isArray(item.location) && <code>{item.location.join('.')} — </code>}
      {item.field != null && <code>{String(item.field)}{item.row != null ? `, row ${item.row}` : ''} — </code>}
      {String(item.message || item.code || 'Invalid value')}
    </li>)}</ul>}
  </div>;
}
export function MetricValue({ metric, unit = 'ratio' }: { metric: Metric; unit?: 'percent' | 'ratio' | 'money' }) {
  return <span className="metric-value"><span>{metricText(metric, unit)}</span>
    {metric.value === null && <small className="metric-reason">{metric.reason}</small>}</span>;
}
export function Pager({ offset, count, onChange }: { offset: number; count: number; onChange: (next: number) => void }) {
  return <div className="pager"><small>{count ? `${offset + 1}–${offset + count} loaded` : 'No records on this page'}</small><div>
    <button className="button subtle small" disabled={offset === 0} onClick={() => onChange(Math.max(0, offset - 50))}>Previous page</button>
    <button className="button subtle small" disabled={count < 50} onClick={() => onChange(offset + 50)}>Next page</button>
  </div></div>;
}
export type Column<T> = { label: string; render: (item: T, index: number) => ReactNode };
export function DataTable<T>({ rows, columns, caption, pageSize = 25 }: { rows: T[]; columns: Column<T>[]; caption: string; pageSize?: number }) {
  const [page, setPage] = useState(0);
  const current = Math.min(page, Math.max(0, Math.ceil(rows.length / pageSize) - 1));
  if (!rows.length) return <p className="inline-empty">No {caption.toLowerCase()} in this run.</p>;
  return <><div className="table-scroll"><table><caption>{caption}</caption><thead><tr>{columns.map(c => <th key={c.label} scope="col">{c.label}</th>)}</tr></thead>
    <tbody>{rows.slice(current * pageSize, (current + 1) * pageSize).map((row, index) => <tr key={current * pageSize + index}>
      {columns.map(c => <td key={c.label}>{c.render(row, current * pageSize + index)}</td>)}
    </tr>)}</tbody></table></div>
    {rows.length > pageSize && <div className="pager"><small>{current * pageSize + 1}–{Math.min((current + 1) * pageSize, rows.length)} of {rows.length}</small><div>
      <button className="button subtle small" onClick={() => setPage(current - 1)} disabled={current === 0} aria-label={`Previous ${caption} rows`}>Previous rows</button>
      <button className="button subtle small" onClick={() => setPage(current + 1)} disabled={(current + 1) * pageSize >= rows.length} aria-label={`Next ${caption} rows`}>Next rows</button>
    </div></div>}</>;
}
