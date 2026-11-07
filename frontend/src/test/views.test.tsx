import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { expect, it, vi } from 'vitest';
import { api, ApiError } from '../api/client';
import { datasetSchema, experimentSchema, type Finding, type Reproduction } from '../api/schemas';
import { useRemote } from '../lib/useRemote';
import { MetricValue } from '../components/Common';
import { Audit } from '../components/Audit';
import { ResultView } from '../components/ResultView';
import { ReproductionView } from '../components/ReproductionView';
import { Research } from '../pages/Research';
import { Datasets } from '../pages/Datasets';
import { SavedResearch } from '../pages/SavedResearch';
import datasetJson from './fixtures/dataset.json';
import backtestJson from './fixtures/backtest.json';
import gridJson from './fixtures/grid.json';
import trainJson from './fixtures/train_test.json';

const dataset = datasetSchema.parse(datasetJson), backtest = experimentSchema.parse(backtestJson);
const noop = () => {};
const list = { items: [], limit: 50, offset: 0 };

it('shows only the selected strategy parameters', async () => {
  const user = userEvent.setup();
  render(<Research dataset={dataset} goDatasets={noop} openSaved={noop} />);
  expect(screen.queryByLabelText('Fast window')).not.toBeInTheDocument();
  await user.selectOptions(screen.getByLabelText('Strategy'), 'sma');
  expect(screen.getByLabelText('Fast window')).toBeInTheDocument();
  expect(screen.queryByLabelText('Lookback')).not.toBeInTheDocument();
  await user.selectOptions(screen.getByLabelText('Strategy'), 'momentum');
  expect(screen.getByLabelText('Lookback')).toBeInTheDocument();
  expect(screen.queryByLabelText('Slow window')).not.toBeInTheDocument();
});

it('renders unavailable metric reasons without a substitute zero', () => {
  render(<MetricValue metric={{ value: null, reason: 'zero_return_variance' }} />);
  expect(screen.getByText('Unavailable')).toBeInTheDocument();
  expect(screen.getByText('zero_return_variance')).toBeInTheDocument();
  expect(screen.queryByText('0.00')).not.toBeInTheDocument();
});

it('separates all four audit assessments and expands the corresponding evidence', async () => {
  const user = userEvent.setup();
  const findings = backtestJson.result.runs[0].audit.findings;
  const pass = findings.find(f => f.status === 'PASS') as Finding;
  const warning = findings.find(f => f.status === 'WARNING') as Finding;
  const unknown = findings.find(f => f.status === 'NOT_ASSESSED') as Finding;
  const failure: Finding = { ...pass, rule_id: 'TEST.DELIBERATE_BAD_EVIDENCE', status: 'FAIL', severity: 'ERROR', title: 'Deliberate inconsistent record', explanation: 'Handcrafted component test evidence.' };
  render(<Audit findings={[pass, warning, unknown, failure]} />);
  for (const status of ['PASS','FAIL','WARNING','NOT_ASSESSED']) expect(screen.getAllByLabelText(status).length).toBe(2);
  await user.selectOptions(screen.getByLabelText('Audit status filter'), 'NOT_ASSESSED');
  expect(screen.getByText(unknown.title)).toBeInTheDocument();
  expect(screen.queryByText(failure.title)).not.toBeInTheDocument();
  await user.click(screen.getByText(unknown.title));
  expect(screen.getAllByText(unknown.explanation)[0]).toBeVisible();
});

it('prevents repeated writes, shows loading and clears prior results after invalid edits', async () => {
  const user = userEvent.setup();
  let complete!: (record: typeof backtest) => void;
  const execute = vi.spyOn(api, 'execute').mockImplementation(() => new Promise(resolve => { complete = resolve; }));
  render(<Research dataset={dataset} goDatasets={noop} openSaved={noop} />);
  await user.click(screen.getByRole('button', { name: 'Run backtest →' }));
  expect(screen.getByRole('button', { name: 'Executing research…' })).toBeDisabled();
  expect(screen.getByText(/Executing and retaining/)).toBeInTheDocument();
  expect(execute).toHaveBeenCalledTimes(1);
  await act(async () => complete(backtest));
  expect(await screen.findByRole('region', { name: 'Saved research result' })).toBeInTheDocument();
  const capital = screen.getByLabelText('Starting capital · USD');
  await user.clear(capital); await user.type(capital, '-1');
  expect(screen.queryByRole('region', { name: 'Saved research result' })).not.toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Run backtest →' }));
  expect(screen.getByRole('alert')).toHaveTextContent('Starting capital must be positive');
  expect(capital).toHaveValue('-1'); expect(execute).toHaveBeenCalledTimes(1);
});

it('preserves research inputs and displays an actual backend rejection', async () => {
  const user = userEvent.setup();
  vi.spyOn(api, 'execute').mockRejectedValue(new ApiError('D04 eligibility requires unadjusted OHLC.', 'computation_rejected', 422));
  render(<Research dataset={dataset} goDatasets={noop} openSaved={noop} />);
  await user.click(screen.getByRole('button', { name: 'Run backtest →' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('D04 eligibility');
  expect(screen.getByLabelText('Starting capital · USD')).toHaveValue('1000.00');
  expect(screen.queryByRole('region', { name: 'Saved research result' })).not.toBeInTheDocument();
});

it('provides loading/empty dataset states and validates missing upload inputs', async () => {
  const user = userEvent.setup(); let finish!: (value: typeof list) => void;
  vi.spyOn(api, 'datasets').mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  const imported = vi.spyOn(api, 'importDataset');
  render(<Datasets selected={null} onSelect={noop} goBacktest={noop} />);
  expect(screen.getByText('Loading retained datasets…')).toBeInTheDocument();
  await act(async () => finish(list));
  expect(screen.getByText('Your research starts here')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Import dataset →' }));
  expect(screen.getByRole('alert')).toHaveTextContent('Choose a CSV');
  expect(imported).not.toHaveBeenCalled();
});

it('renders backend upload field diagnostics and keeps the editable metadata', async () => {
  const user = userEvent.setup(); vi.spyOn(api, 'datasets').mockResolvedValue(list);
  vi.spyOn(api, 'importDataset').mockRejectedValue(new ApiError('Dataset validation failed.', 'invalid_dataset', 422,
    { issues: [{ field: 'ohlc', row: 2, message: 'Require low <= min(open, close).' }] }));
  const source = 'date,open,high,low,close,volume\n2024-01-01,10,5,9,10,100\n';
  const file = new File([source], 'bad.csv', { type: 'text/csv' });
  Object.defineProperty(file, 'arrayBuffer', { value: async () => new TextEncoder().encode(source).buffer });
  render(<Datasets selected={null} onSelect={noop} goBacktest={noop} />);
  await user.upload(screen.getByLabelText('OHLCV CSV'), file);
  await user.click(screen.getByLabelText('JSON metadata')); await user.paste('{}');
  await user.click(screen.getByRole('button', { name: 'Import dataset →' }));
  const alert = await screen.findByRole('alert'); expect(alert).toHaveTextContent('ohlc, row 2');
  expect(screen.getByLabelText('JSON metadata')).toHaveValue('{}');
});

it('shows training-only selection and defaults to the real held-out losing run', () => {
  render(<ResultView record={experimentSchema.parse(trainJson)} />);
  expect(screen.getByText('SELECTED ON TRAINING ONLY')).toBeInTheDocument();
  expect(screen.getByText('OUT-OF-SAMPLE TEST')).toBeInTheDocument();
  expect(screen.getByText('Frozen choice: Momentum 2 · 0')).toBeInTheDocument();
  expect(screen.getAllByText('-54.00%').length).toBeGreaterThan(0);
  expect(screen.getAllByText('$460.00').length).toBeGreaterThan(0);
  expect(screen.getByRole('img', { name: /Equity curve in USD/ })).toBeInTheDocument();
});

it('a delayed dataset selection cannot override a newer successful import', async () => {
  const user = userEvent.setup(), selected = vi.fn();
  vi.spyOn(api, 'datasets').mockResolvedValue({ ...list, items: [{ dataset_id: dataset.dataset_id, first_date: dataset.validation.first_date,
    last_date: dataset.validation.last_date, row_count: dataset.validation.row_count, created_at: dataset.created_at }] });
  let finish!: (value: typeof dataset) => void;
  vi.spyOn(api, 'dataset').mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  vi.spyOn(api, 'importDataset').mockResolvedValue({ ...dataset, duplicate: true });
  render(<Datasets selected={null} onSelect={selected} goBacktest={noop} />);
  await user.click(await screen.findByText(dataset.dataset_id.slice(0, 10)));
  const source = 'date,open,high,low,close,volume\n2024-01-01,10,10,10,10,100\n';
  const file = new File([source], 'synthetic.csv', { type: 'text/csv' });
  Object.defineProperty(file, 'arrayBuffer', { value: async () => new TextEncoder().encode(source).buffer });
  await user.upload(screen.getByLabelText('OHLCV CSV'), file);
  await user.click(screen.getByLabelText('JSON metadata')); await user.paste('{}');
  await user.click(screen.getByRole('button', { name: 'Import dataset →' }));
  await waitFor(() => expect(selected).toHaveBeenCalledTimes(1));
  await act(async () => finish(dataset));
  expect(selected).toHaveBeenCalledTimes(1);
});

it('presents real comparison rows with their windows and stored baseline deltas', async () => {
  const user = userEvent.setup(); render(<ResultView record={experimentSchema.parse(gridJson)} />);
  const rows = within(screen.getByRole('table', { name: 'Experiment runs' })).getAllByRole('row');
  expect(rows).toHaveLength(gridJson.result.runs.length + 1);
  expect(screen.getByText(/Unequal durations are not equivalent/)).toBeInTheDocument();
  await user.click(screen.getByText('Stored baseline differences'));
  expect(screen.getByRole('table', { name: 'Baseline differences' })).toBeVisible();
  expect(screen.getByText(/Positive Δ drawdown means greater/)).toBeInTheDocument();
});

function reproduction(status: Reproduction['status']): Reproduction {
  return { experiment_id: backtest.experiment_id, status, economic_match: status !== 'mismatch', implementation_match: status !== 'implementation_changed',
    saved_economic_sha256: 'a'.repeat(64), current_economic_sha256: 'b'.repeat(64), difference_paths: status === 'mismatch' ? ['result.runs[0].final_equity'] : [], difference_path_limit: 20,
    current_implementation: backtest.implementation, limitations: ['Current computation, not a restored executable archive.'] };
}
it.each([
  ['matched', 'Recorded outputs match'], ['mismatch', 'Economic outputs differ'], ['implementation_changed', 'Implementation identity changed'],
] as const)('presents reproduction %s honestly', async (status, title) => {
  const user = userEvent.setup(); const rerun = vi.spyOn(api, 'reproduce').mockResolvedValue(reproduction(status));
  render(<ReproductionView experimentId={backtest.experiment_id} />);
  await user.click(screen.getByRole('button', { name: 'Reproduce saved experiment' }));
  expect(await screen.findByText(title)).toBeInTheDocument(); expect(rerun).toHaveBeenCalledWith(backtest.experiment_id);
});

it('clears a prior reproduction match when a later reproduction is unavailable', async () => {
  const user = userEvent.setup(); vi.spyOn(api, 'reproduce').mockResolvedValueOnce(reproduction('matched'))
    .mockRejectedValueOnce(new ApiError('Retained inputs cannot be revalidated.', 'retained_evidence_unavailable', 409));
  render(<ReproductionView experimentId={backtest.experiment_id} />);
  await user.click(screen.getByRole('button', { name: 'Reproduce saved experiment' }));
  expect(await screen.findByText('Recorded outputs match')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Reproduce saved experiment' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Retained inputs');
  expect(screen.queryByText('Recorded outputs match')).not.toBeInTheDocument();
});

it('shows empty saved research and handles an unknown saved experiment', async () => {
  const user = userEvent.setup(); vi.spyOn(api, 'experiments').mockResolvedValue(list);
  vi.spyOn(api, 'experiment').mockRejectedValue(new ApiError('Experiment not found.', 'not_found', 404));
  render(<SavedResearch dataset={null} initial={null} goBacktest={noop} />);
  expect(await screen.findByText('No saved research on this page')).toBeInTheDocument();
  await user.type(screen.getByLabelText('Open by experiment ID'), 'b'.repeat(32));
  await user.click(screen.getByRole('button', { name: /^Open$/ }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Experiment not found');
  expect(screen.queryByRole('region', { name: 'Saved research result' })).not.toBeInTheDocument();
});

it('discards stale read responses after the selected resource changes', async () => {
  const resolvers: ((value: string) => void)[] = [];
  function Probe() { const [id, setId] = useState(0); const result = useRemote(() => new Promise<string>(resolve => resolvers.push(resolve)), [id]);
    return <><button onClick={() => setId(id + 1)}>Change</button><span>{result.data || result.state}</span></>; }
  const user = userEvent.setup(); render(<Probe />); await user.click(screen.getByText('Change'));
  await act(async () => resolvers[1]('latest'));
  await act(async () => resolvers[0]('stale'));
  await waitFor(() => expect(screen.getByText('latest')).toBeInTheDocument());
  expect(screen.queryByText('stale')).not.toBeInTheDocument();
});
