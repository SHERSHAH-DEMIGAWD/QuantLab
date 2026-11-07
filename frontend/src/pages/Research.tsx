import { useRef, useState, type FormEvent } from 'react';
import { api } from '../api/client';
import type { Cost, Dataset, Experiment, Period } from '../api/schemas';
import { buildRequest, defaults, type FormValues, type Study } from '../lib/research';
import { shortId } from '../lib/format';
import { Empty, ErrorPanel, Loading, PageIntro } from '../components/Common';
import { ResultView } from '../components/ResultView';

export function StrategyControls({ values, update, grid }: { values: FormValues; update: <K extends keyof FormValues>(key: K, value: FormValues[K]) => void; grid: boolean }) {
  return <><label>Strategy<select aria-label="Strategy" value={values.strategy} onChange={e => update('strategy', e.target.value as FormValues['strategy'])}>
    <option value="buy_and_hold">Buy and hold</option><option value="sma">SMA crossover</option><option value="momentum">Time-series momentum</option>
  </select></label>
    {values.strategy === 'sma' && <div className="form-grid"><label>{grid ? 'Fast windows' : 'Fast window'}<input value={grid ? values.fastGrid : values.fast} onChange={e => update(grid ? 'fastGrid' : 'fast', e.target.value)} inputMode="numeric" /></label>
      <label>{grid ? 'Slow windows' : 'Slow window'}<input value={grid ? values.slowGrid : values.slow} onChange={e => update(grid ? 'slowGrid' : 'slow', e.target.value)} inputMode="numeric" /></label></div>}
    {values.strategy === 'momentum' && <div className="form-grid"><label>{grid ? 'Lookbacks' : 'Lookback'}<input value={grid ? values.lookbackGrid : values.lookback} onChange={e => update(grid ? 'lookbackGrid' : 'lookback', e.target.value)} inputMode="numeric" /></label>
      <label>{grid ? 'Thresholds' : 'Threshold'}<input value={grid ? values.thresholdGrid : values.threshold} onChange={e => update(grid ? 'thresholdGrid' : 'threshold', e.target.value)} /></label></div>}
    {grid && values.strategy !== 'buy_and_hold' && <p className="field-help">Comma-separated axes; every combination is evaluated. Invalid pairs reject the request.</p>}
    {grid && values.strategy === 'buy_and_hold' && <p className="field-help">Buy and hold has one fixed configuration and no tunable parameters.</p>}
    {values.strategy === 'momentum' && <p className="field-help">Threshold is a return fraction: 0.05 means 5%. Lookback is observed closes.</p>}
  </>;
}

export function Research({ dataset, experiments = false, goDatasets, openSaved }: { dataset: Dataset | null; experiments?: boolean; goDatasets: () => void; openSaved: (record: Experiment) => void }) {
  if (!dataset) return <><PageIntro eyebrow="Research workspace" title={experiments ? 'Experiment workbench' : 'Backtest workspace'}>Start with retained data and explicit assumptions.</PageIntro>
    <section className="panel"><Empty title="Select a dataset first" action={<button className="button primary" onClick={goDatasets}>Go to Datasets ↗</button>}>Import a supported CSV or choose a previously retained dataset. Import acceptance alone does not establish simulation eligibility.</Empty></section></>;
  return <ResearchForm key={dataset.dataset_id + String(experiments)} dataset={dataset} experiments={experiments} goDatasets={goDatasets} openSaved={openSaved} />;
}

function ResearchForm({ dataset, experiments, goDatasets, openSaved }: { dataset: Dataset; experiments: boolean; goDatasets: () => void; openSaved: (record: Experiment) => void }) {
  const [values, setValues] = useState(() => defaults(dataset)), [study, setStudy] = useState<Study>('parameters');
  const [costs, setCosts] = useState<Cost[]>([{ commission_per_fill_usd: '0.00', slippage_bps: '0' }, { commission_per_fill_usd: '2.00', slippage_bps: '100' }]);
  const [periods, setPeriods] = useState<Period[]>([{ start_date: dataset.validation.first_date, end_date: '' }, { start_date: '', end_date: dataset.validation.last_date }]);
  const [record, setRecord] = useState<Experiment | null>(null), [error, setError] = useState<unknown>(null), [busy, setBusy] = useState(false);
  const locked = useRef(false);
  function changed() { setRecord(null); setError(null); }
  function update<K extends keyof FormValues>(key: K, value: FormValues[K]) { changed(); setValues(previous => ({ ...previous, [key]: value })); }
  const grid = experiments && (study === 'parameters' || study === 'train_test');
  async function submit(event: FormEvent) {
    event.preventDefault(); if (locked.current) return;
    setRecord(null); setError(null);
    let request;
    try { request = buildRequest(dataset, values, experiments ? study : undefined, costs, periods); }
    catch (error) { setError(error); return; }
    locked.current = true; setBusy(true);
    try { setRecord(await api.execute(request)); } catch (error) { setError(error); }
    finally { locked.current = false; setBusy(false); }
  }
  return <><PageIntro eyebrow={experiments ? 'Robustness & held-out evaluation' : 'Strategy research'} title={experiments ? 'Experiment workbench' : 'Backtest workspace'}>
    {experiments ? 'Change conditions deliberately. Keep the evidence with every result.' : 'One strategy. Explicit assumptions. A complete, inspectable result.'}</PageIntro>
    <div className="research-layout"><form className="panel configuration-panel" onSubmit={submit}><fieldset disabled={busy}>
      <div className="panel-heading"><h2>Configure research</h2><span className="step-label">01</span></div>
      <div className="selected-dataset"><span>SELECTED DATASET</span><strong>{dataset.metadata.symbol} <small>{shortId(dataset.dataset_id)}</small></strong>
        <p>{dataset.validation.row_count.toLocaleString('en-US')} daily observations · {dataset.metadata.currency}</p><button type="button" className="text-button" onClick={goDatasets}>Change dataset ↗</button></div>
      {experiments && <label>Experiment type<select aria-label="Experiment type" value={study} onChange={e => { changed(); setStudy(e.target.value as Study); }}>
        <option value="parameters">Parameter grid</option><option value="costs">Cost sensitivity</option><option value="subperiods">Historical subperiods</option><option value="train_test">Chronological train / test</option>
      </select></label>}
      <StrategyControls values={values} update={update} grid={grid} />
      <label>Starting capital · USD<input value={values.capital} onChange={e => update('capital', e.target.value)} inputMode="decimal" maxLength={128} /></label>
      {experiments && study === 'train_test' ? <div className="split-inputs"><h3>Training window</h3><div className="form-grid">
        <label>Training start<input type="date" value={values.trainStart} onChange={e => update('trainStart', e.target.value)} /></label>
        <label>Training end<input type="date" value={values.trainEnd} onChange={e => update('trainEnd', e.target.value)} /></label></div>
        <h3>Out-of-sample test</h3><div className="form-grid"><label>Test start<input type="date" value={values.testStart} onChange={e => update('testStart', e.target.value)} /></label>
          <label>Test end<input type="date" value={values.testEnd} onChange={e => update('testEnd', e.target.value)} /></label></div>
        <label className="checkbox"><input type="checkbox" checked={values.warmup} onChange={e => update('warmup', e.target.checked)} />Warm indicators with training data</label>
        <p className="field-help">Selection uses training return only. Test starts flat with fresh capital; warm-up contributes no trades or P&L.</p>
      </div> : experiments && study === 'subperiods' ? <div className="scenario-list"><h3>Explicit subperiods</h3>
        {periods.map((period, index) => <div className="scenario" key={index}><div className="scenario-title"><b>Window {index + 1}</b>
          <button type="button" className="text-button" disabled={periods.length <= 2} onClick={() => { changed(); setPeriods(periods.filter((_, i) => i !== index)); }} aria-label={`Remove window ${index + 1}`}>Remove</button></div>
          <div className="form-grid"><label>Start {index + 1}<input type="date" value={period.start_date} onChange={e => { changed(); setPeriods(periods.map((p, i) => i === index ? { ...p, start_date: e.target.value } : p)); }} /></label>
            <label>End {index + 1}<input type="date" value={period.end_date} onChange={e => { changed(); setPeriods(periods.map((p, i) => i === index ? { ...p, end_date: e.target.value } : p)); }} /></label></div></div>)}
        <button type="button" className="button subtle small" disabled={periods.length >= 20} onClick={() => { changed(); setPeriods([...periods, { start_date: '', end_date: '' }]); }}>+ Add subperiod</button>
        <p className="field-help">At least two observations per window. Returns over unequal durations are not directly equivalent.</p>
      </div> : <div className="form-grid"><label>Evaluation start<input type="date" value={values.start} onChange={e => update('start', e.target.value)} /></label>
        <label>Evaluation end<input type="date" value={values.end} onChange={e => update('end', e.target.value)} /></label></div>}
      {experiments && study === 'costs' ? <div className="scenario-list"><h3>Cost scenarios</h3><p className="field-help">The first scenario is the reference. Costs can change affordable quantity and exposure.</p>
        {costs.map((cost, index) => <div className="scenario" key={index}><div className="scenario-title"><b>{index === 0 ? 'Reference cost' : `Scenario ${index + 1}`}</b>
          <button type="button" className="text-button" disabled={costs.length <= 2} onClick={() => { changed(); setCosts(costs.filter((_, i) => i !== index)); }} aria-label={`Remove cost ${index + 1}`}>Remove</button></div>
          <div className="form-grid"><label>Commission {index + 1} · USD<input value={cost.commission_per_fill_usd} onChange={e => { changed(); setCosts(costs.map((c, i) => i === index ? { ...c, commission_per_fill_usd: e.target.value } : c)); }} /></label>
            <label>Slippage {index + 1} · bps<input value={cost.slippage_bps} onChange={e => { changed(); setCosts(costs.map((c, i) => i === index ? { ...c, slippage_bps: e.target.value } : c)); }} /></label></div></div>)}
        <button type="button" className="button subtle small" disabled={costs.length >= 20} onClick={() => { changed(); setCosts([...costs, { commission_per_fill_usd: '', slippage_bps: '' }]); }}>+ Add cost scenario</button></div>
        : <div className="form-grid"><label>Commission · USD / fill<input value={values.commission} onChange={e => update('commission', e.target.value)} inputMode="decimal" /></label>
          <label>Slippage · bps<input value={values.slippage} onChange={e => update('slippage', e.target.value)} inputMode="decimal" /></label></div>}
      <label className="checkbox"><input type="checkbox" checked={values.benchmark} onChange={e => update('benchmark', e.target.checked)} />Include buy-and-hold reference</label>
      <details className="advanced"><summary>Risk-free rate & coverage</summary><label>Annual risk-free rate · fraction<input value={values.riskFree} onChange={e => update('riskFree', e.target.value)} /></label>
        <label className="checkbox"><input type="checkbox" checked={values.acknowledge} onChange={e => update('acknowledge', e.target.checked)} />Acknowledge unverified real-data coverage</label>
        <p className="field-help">Required for local-file sources. This does not verify sessions or corporate actions.</p></details>
      <p className="request-limits">Up to 100 configurations and 1,000,000 aggregate bars, including references and warm-up. The backend checks the complete workload.</p>
      <button className="button primary run-button" type="submit">{busy ? 'Executing research…' : experiments ? 'Run experiment →' : 'Run backtest →'}</button>
      <p className="field-help">Successful results are saved automatically.</p>
    </fieldset></form><div className="result-column"><ErrorPanel error={error} />
      {busy ? <section className="panel"><Loading>Executing and retaining your research. No result is shown until the request completes.</Loading></section>
        : record ? <ResultView key={record.experiment_id} record={record} onOpenSaved={openSaved} />
          : <section className="panel research-empty"><Empty title="A clear view of what happened">Choose your assumptions and run research to see the actual equity curve, trades and audit evidence.</Empty>
            <ol className="workflow-steps"><li><b>01</b><span>Configure<strong>Existing strategies, explicit dates and costs.</strong></span></li>
              <li><b>02</b><span>Run & retain<strong>The backend executes and saves the complete result.</strong></span></li>
              <li><b>03</b><span>Inspect the evidence<strong>Financial records, assumptions and unassessed risks.</strong></span></li></ol></section>}
    </div></div></>;
}
