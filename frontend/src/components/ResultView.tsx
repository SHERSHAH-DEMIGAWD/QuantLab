import { useState } from 'react';
import { isTrainTest, type Experiment, type Run } from '../api/schemas';
import { money, sessionLabel, shortId, strategyName, timestamp } from '../lib/format';
import { Audit } from './Audit';
import { DataTable, MetricValue } from './Common';
import { EquityChart } from './EquityChart';
import { ReproductionView } from './ReproductionView';

function RunDetail({ run }: { run: Run }) {
  const { simulation: sim, equity, trades } = run.performance;
  return <div className="run-detail">
    <div className="run-context"><div><span className={`scope-tag ${run.phase}`}>{run.phase === 'test' ? 'OUT-OF-SAMPLE TEST' : run.phase.toUpperCase()}</span>
      <h2>{strategyName(sim.strategy)}</h2><p>{sessionLabel(sim.start_date)} — {sessionLabel(sim.end_date)} · {sim.valuations.length} observed sessions</p></div>
      <div className="cost-summary"><span>Commission <b>{money(sim.settings.commission_per_fill_usd)} / fill</b></span>
        <span>Slippage <b>{sim.settings.slippage_bps} bps</b></span><span>Reference role <b>{run.role}</b></span></div></div>
    <div className="return-notice">Price return only · Dividends excluded · Integer shares · Long only · No forced final sale</div>
    <div className="metric-grid">
      <div className="metric-card"><small>Initial equity · USD</small><strong>{money(sim.initial_capital)}</strong><span>Fresh starting capital</span></div>
      <div className="metric-card accent"><small>Final equity · USD</small><strong>{money(sim.final_equity)}</strong><span>{sim.final_shares ? `${sim.final_shares.toLocaleString('en-US')} shares remain open` : 'Portfolio ends flat'}</span></div>
      <div className="metric-card"><small>Cumulative return</small><strong><MetricValue metric={equity.cumulative_return} unit="percent" /></strong><span>Over this evaluation window</span></div>
      <div className="metric-card"><small>Maximum drawdown</small><strong><MetricValue metric={equity.maximum_drawdown} unit="percent" /></strong><span>Nonnegative peak-to-trough loss</span></div>
    </div>
    <section className="panel"><EquityChart values={sim.valuations} /><div className="secondary-metrics">
      <div><small>Annualized return</small><strong><MetricValue metric={equity.annualized_return} unit="percent" /></strong>
        {equity.annualization_extrapolated && <span className="extrapolation">Short-window extrapolation</span>}</div>
      <div><small>Annualized volatility</small><strong><MetricValue metric={equity.annualized_volatility} unit="percent" /></strong></div>
      <div><small>Sharpe ratio</small><strong><MetricValue metric={equity.sharpe_ratio} /></strong></div>
      <div><small>Annual risk-free rate</small><strong><MetricValue metric={{ value: equity.annual_risk_free_rate, reason: null }} unit="percent" /></strong></div>
    </div></section>
    <section className="panel"><div className="panel-heading"><div><p className="eyebrow">Completed trades & retained exposure</p><h2>Positions and trades</h2></div>
      <span className="neutral-badge">{trades.closed_trade_count} closed</span></div>
      <div className="trade-stats"><div><small>Winning / losing / break-even</small><strong>{trades.winning_trades} / {trades.losing_trades} / {trades.break_even_trades}</strong></div>
        <div><small>Win rate</small><strong><MetricValue metric={trades.win_rate} unit="percent" /></strong></div>
        <div><small>Mean closed-trade net P&L</small><strong><MetricValue metric={trades.mean_net_pnl} unit="money" /></strong></div>
        <div><small>Final cash</small><strong>{money(sim.final_cash)}</strong></div></div>
      <div className="position-note"><strong>{trades.open_position ? `Open position · ${trades.open_position.quantity.toLocaleString('en-US')} shares` : 'No open position'}</strong>
        <span>Realized P&L {money(sim.realized_pnl)} · Unrealized P&L {money(sim.unrealized_pnl)}</span>
        {trades.open_position && <small>Entry {trades.open_position.entry_session} · Entry debit {money(trades.open_position.entry_debit)} · Mark {money(trades.open_position.market_value)}. No hypothetical exit fee is deducted.</small>}</div>
      <DataTable rows={trades.closed_trades} caption="Closed trades" columns={[
        { label: 'Entry session', render: t => t.entry_session }, { label: 'Exit session', render: t => t.exit_session },
        { label: 'Shares', render: t => t.quantity.toLocaleString('en-US') }, { label: 'Entry debit · USD', render: t => money(t.entry_debit) },
        { label: 'Exit credit · USD', render: t => money(t.exit_credit) }, { label: 'Net P&L · USD', render: t => money(t.net_pnl) },
      ]} />
      <details className="data-detail" open><summary>Execution outcomes · {sim.orders.length} orders / {sim.fills.length} fills</summary>
        <DataTable rows={sim.orders} caption="Order outcomes" columns={[
          { label: 'Order', render: o => `#${o.order_id} ${o.side}` }, { label: 'Decision', render: o => o.decision_session },
          { label: 'Eligible open', render: o => o.eligible_session || 'No later session' },
          { label: 'Outcome', render: o => <><span className={`order-status ${o.status.toLowerCase()}`}>{o.status}</span><small>{o.reason}</small></> },
          { label: 'Outcome session', render: o => o.outcome_session || '—' },
          { label: 'Effective price · USD', render: o => o.effective_price === null ? '—' : money(o.effective_price) },
        ]} />
        <DataTable rows={sim.fills} caption="Executed fills" columns={[
          { label: 'Session', render: f => f.session }, { label: 'Side', render: f => f.side }, { label: 'Shares', render: f => f.quantity.toLocaleString('en-US') },
          { label: 'Base open · USD', render: f => money(f.base_open) }, { label: 'Effective · USD', render: f => money(f.effective_price) },
          { label: 'Notional · USD', render: f => money(f.notional) }, { label: 'Fee · USD', render: f => money(f.fee) },
          { label: 'Cash change · USD', render: f => money(f.cash_change) },
        ]} />
      </details>
    </section>
    <section className="panel"><details className="data-detail"><summary>Equity observations · exact stored values</summary>
      <p className="muted">Exchange-session dates are displayed as stored. Monetary values retain all meaningful decimal digits.</p>
      <DataTable rows={sim.valuations} caption="Equity observations" pageSize={50} columns={[
        { label: 'Session', render: v => v.session }, { label: 'Cash · USD', render: v => money(v.cash) }, { label: 'Shares', render: v => v.shares.toLocaleString('en-US') },
        { label: 'Close · USD', render: v => money(v.close) }, { label: 'Holdings · USD', render: v => money(v.market_value) },
        { label: 'Equity · USD', render: v => money(v.equity) }, { label: 'Entry basis · USD', render: v => money(v.cost_basis) },
        { label: 'Realized P&L · USD', render: v => money(v.realized_pnl) }, { label: 'Unrealized P&L · USD', render: v => money(v.unrealized_pnl) },
      ]} />
    </details></section>
    <Audit findings={run.audit.findings} />
    <section className="panel"><details><summary>Assumptions, warnings and provenance</summary>
      <p><b>{sim.metadata.symbol}</b> · {sim.metadata.source_name} · {sim.metadata.source_kind} · {sim.metadata.adjustment_basis}</p>
      <p>Coverage: {sim.metadata.session_coverage} (declaration) · Splits: {sim.metadata.split_status} · Time zone: {sim.metadata.session_timezone}</p>
      <p>Requested window: {run.requested_period.start_date} — {run.requested_period.end_date}. Indicator-only warm-up: {sim.warmup_bars} bars{sim.warmup_start && ` (${sim.warmup_start} — ${sim.warmup_end})`}.</p>
      <h3>Warnings</h3><ul>{[...sim.warnings, ...equity.warnings].map((text, i) => <li key={i}>{text}</li>)}</ul>
      <h3>Execution and metric assumptions</h3><ul>{[...sim.assumptions, ...equity.assumptions].map((text, i) => <li key={i}>{text}</li>)}</ul>
      <p className="hash-line">Dataset <code>{sim.dataset_id}</code></p><p className="hash-line">Source SHA-256 <code>{sim.source_sha256}</code></p>
      <p className="hash-line">Metadata SHA-256 <code>{sim.metadata_sha256}</code></p>
    </details></section>
  </div>;
}

export function ResultView({ record, onOpenSaved, showReproduction = false }: { record: Experiment; onOpenSaved?: (record: Experiment) => void; showReproduction?: boolean }) {
  const result = record.result, split = isTrainTest(result);
  const runs = split ? [...result.training.runs, ...result.test_runs] : result.runs;
  const initial = split ? result.selected_test_run_id : (runs.find(r => r.role === 'candidate') || runs[0]).run_id;
  const [selected, setSelected] = useState(initial);
  const active = runs.find(r => r.run_id === selected) || runs.find(r => r.run_id === initial) || runs[0];
  const comparisons = split ? [...result.training.comparisons, ...(result.test_comparison ? [result.test_comparison] : [])] : result.comparisons;
  const work = split ? result.actual_workload : result.workload;
  return <section className="results" aria-label="Saved research result"><header className="result-header"><div><p className="eyebrow">Saved automatically</p>
    <h2>Research result <span className="id-inline">{shortId(record.experiment_id)}</span></h2><p>{timestamp(record.created_at)} · {record.mode.replaceAll('_', ' ')}</p></div>
    {onOpenSaved && <button className="button secondary" onClick={() => onOpenSaved(record)}>Open in Saved Research ↗</button>}</header>
    {split && <div className="selection-panel"><span className="scope-tag training">SELECTED ON TRAINING ONLY</span><h2>Frozen choice: {strategyName(result.selection.selected_configuration)}</h2>
      <p>Criterion: {result.selection.criterion}. Test window {result.requested_test_period.start_date} — {result.requested_test_period.end_date}.</p>
      <p>Fresh test cash, zero carried holdings and no training P&L. A single held-out period does not establish generalization.</p>
      <details><summary>Training ranking and tie rule</summary><p>{result.selection.tie_break}</p><ol>{result.selection.ranked_training_run_ids.map(id => {
        const run = runs.find(r => r.run_id === id)!;
        return <li key={id}>{id} · {strategyName(run.performance.simulation.strategy)} · <MetricValue metric={run.performance.equity.cumulative_return} unit="percent" /></li>;
      })}</ol></details></div>}
    {(record.mode !== 'backtest' || runs.length > 1) && <section className="panel"><div className="panel-heading"><div><p className="eyebrow">Conditions, not predictions</p><h2>Run comparison</h2></div>
      <span className="neutral-badge">{work.run_count} runs · {(work.evaluated_bars + work.warmup_bars).toLocaleString('en-US')} charged bars</span></div>
      <p className="muted">Returns cover the stated windows. Unequal durations are not equivalent measures of strategy quality. Test rows are not ranked.</p>
      <DataTable rows={runs} caption="Experiment runs" columns={[
        { label: 'Run / scope', render: r => <><b>{r.run_id}</b><small>{r.phase} · {r.role}</small></> },
        { label: 'Configuration', render: r => strategyName(r.performance.simulation.strategy) },
        { label: 'Observed window', render: r => <>{r.performance.simulation.start_date}<small>to {r.performance.simulation.end_date} · {r.performance.simulation.valuations.length} sessions</small></> },
        { label: 'Costs', render: r => <>{money(r.performance.simulation.settings.commission_per_fill_usd)}<small>{r.performance.simulation.settings.slippage_bps} bps</small></> },
        { label: 'Final equity · USD', render: r => money(r.performance.simulation.final_equity) },
        { label: 'Return', render: r => <MetricValue metric={r.performance.equity.cumulative_return} unit="percent" /> },
        { label: 'Max. drawdown', render: r => <MetricValue metric={r.performance.equity.maximum_drawdown} unit="percent" /> },
        { label: 'Details', render: r => <button className="text-button" onClick={() => setSelected(r.run_id)} aria-label={`Inspect ${r.run_id}`}>Inspect ↗</button> },
      ]} />
      <details className="data-detail"><summary>Stored baseline differences</summary><p className="muted">Candidate minus the named reference, at matching dates. Positive Δ drawdown means greater drawdown.</p>
        <DataTable rows={comparisons} caption="Baseline differences" columns={[
          { label: 'Comparison', render: c => c.kind.replaceAll('_', ' ') }, { label: 'Candidate', render: c => c.run_id },
          { label: 'Reference', render: c => c.reference_run_id }, { label: 'Δ equity · USD', render: c => money(c.final_equity_difference) },
          { label: 'Δ return', render: c => <MetricValue metric={c.cumulative_return_difference} unit="percent" /> },
          { label: 'Δ drawdown', render: c => <MetricValue metric={c.maximum_drawdown_difference} unit="percent" /> },
        ]} /></details>
    </section>}
    <div className="inspect-selector"><label>Inspect result run<select aria-label="Inspect result run" value={active.run_id} onChange={e => setSelected(e.target.value)}>
      {runs.map(r => <option key={r.run_id} value={r.run_id}>{r.run_id} · {r.phase} · {strategyName(r.performance.simulation.strategy)} · {r.role}</option>)}
    </select></label></div>
    <RunDetail key={active.run_id} run={active} />
    <section className="panel"><details><summary>Saved configuration and experiment assumptions</summary><pre>{JSON.stringify(record.request, null, 2)}</pre>
      <ul>{result.assumptions.map(text => <li key={text}>{text}</li>)}</ul><p className="hash-line">Saved result SHA-256 <code>{record.result_sha256}</code></p>
      <p className="hash-line">Implementation source manifest <code>{record.implementation.source.source_snapshot_sha256}</code></p>
    </details></section>
    {showReproduction && <ReproductionView key={record.experiment_id} experimentId={record.experiment_id} />}
  </section>;
}
