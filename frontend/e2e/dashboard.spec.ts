import { expect, test, type Page } from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import { experimentSchema, isTrainTest, type Experiment } from '../src/api/schemas';
import { frontend, startServers, stopServers } from './servers';

test.describe.configure({ mode: 'serial' });
test.beforeAll(startServers);
test.afterAll(stopServers);
const source = path.resolve(frontend, 'public/examples/nine_sessions.csv');
const metadata = path.resolve(frontend, 'public/examples/nine_sessions.metadata.json');

async function importExample(page: Page) {
  await page.goto('/#datasets');
  await expect(page.getByRole('heading', { name: 'Dataset library' })).toBeVisible();
  await page.getByLabel('OHLCV CSV', { exact: true }).setInputFiles(source);
  await expect(page.getByRole('button', { name: 'Import dataset →', exact: true })).toBeEnabled();
  await page.getByLabel('Upload metadata JSON').setInputFiles(metadata);
  await expect(page.getByLabel('JSON metadata', { exact: true })).toHaveValue(/contract_version/);
  const response = page.waitForResponse(r => r.url().endsWith('/api/v1/datasets') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Import dataset →', exact: true }).click();
  const imported = await response; expect([200, 201]).toContain(imported.status());
  await expect(page.getByText('Validated import', { exact: true })).toBeVisible();
  await page.getByText('Provenance, declarations and validation', { exact: true }).click();
  await expect(page.locator('.metadata-list')).toContainText('Project-authored synthetic input; no historical market observations');
  await expect(page.locator('.metadata-list')).toContainText('Invented event-free example; no assertion about a real security');
  await expect(page.getByText(/Import validation does not establish simulation eligibility/)).toBeVisible();
}
async function execute(page: Page, label = 'Run experiment →'): Promise<Experiment> {
  const response = page.waitForResponse(r => r.url().endsWith('/api/v1/experiments') && r.request().method() === 'POST');
  await page.getByRole('button', { name: label, exact: true }).click();
  const completed = await response; expect(completed.status(), await completed.text()).toBe(201);
  const result = experimentSchema.parse(await completed.json());
  await expect(page.getByRole('region', { name: 'Saved research result' })).toBeVisible();
  return result;
}

test('real import → backtest → equity/trades/audit → saved/reproduce → process restarts → invalid upload', async ({ page }) => {
  const browserErrors: string[] = []; page.on('pageerror', error => browserErrors.push(error.message));
  await page.goto('/#datasets');
  await expect(page.getByText('Your research starts here')).toBeVisible();
  await importExample(page);
  await page.getByRole('button', { name: 'Open Backtest →', exact: true }).click();
  const saved = await execute(page, 'Run backtest →');
  if (isTrainTest(saved.result)) throw Error('Expected a backtest result.');
  const candidate = saved.result.runs.find(r => r.role === 'candidate')!;
  expect(candidate.performance.simulation.final_equity).toBe('800.00');
  await expect(page.getByText('$800.00', { exact: true }).first()).toBeVisible();
  await expect(page.getByRole('img', { name: /Equity curve in USD/ })).toBeVisible();
  await expect(page.getByRole('table', { name: 'Executed fills', exact: true })).toBeVisible();
  await page.getByText('Equity observations · exact stored values', { exact: true }).click();
  await expect(page.getByRole('table', { name: 'Equity observations', exact: true })).toContainText('2024-01-01');
  await page.getByLabel('Audit status filter').selectOption('NOT_ASSESSED');
  const finding = candidate.audit.findings.find(f => f.status === 'NOT_ASSESSED')!;
  await page.getByText(finding.title, { exact: true }).click();
  await expect(page.locator('.finding-body > p').filter({ hasText: finding.explanation }).first()).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 240));
  await page.screenshot({ path: path.resolve(frontend, 'test-results/dashboard-desktop.png') });
  await page.getByRole('button', { name: 'Open in Saved Research ↗', exact: true }).click();
  await page.getByRole('button', { name: 'Reproduce saved experiment', exact: true }).click();
  await expect(page.getByText('Recorded outputs match', { exact: true })).toBeVisible();
  await stopServers(); await startServers();
  await page.reload({ waitUntil: 'networkidle' });
  await page.getByRole('button', { name: `Open saved ${saved.experiment_id}`, exact: true }).click();
  await expect(page.getByText('$800.00', { exact: true }).first()).toBeVisible();
  await page.getByRole('button', { name: 'Reproduce saved experiment', exact: true }).click();
  await expect(page.getByText('Recorded outputs match', { exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Datasets', exact: true }).click();
  await page.getByLabel('OHLCV CSV', { exact: true }).setInputFiles({ name: 'invalid.csv', mimeType: 'text/csv',
    buffer: Buffer.from('date,open,high,low,close,volume\n2024-01-01,10,5,9,10,100\n') });
  await page.getByLabel('Upload metadata JSON').setInputFiles(metadata);
  await page.getByRole('button', { name: 'Import dataset →', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('ohlc, row 2');
  expect(browserErrors).toEqual([]);
});

test('all four real robustness workflows, frozen test choice and responsive saved research', async ({ page }) => {
  await importExample(page);
  await page.getByRole('link', { name: 'Experiments', exact: true }).click();
  await page.getByLabel('Strategy', { exact: true }).selectOption('sma');
  const grid = await execute(page);
  if (isTrainTest(grid.result)) throw Error();
  expect(grid.result.configurations).toHaveLength(4);
  expect(grid.result.runs).toHaveLength(5);
  await expect(page.getByRole('table', { name: 'Experiment runs', exact: true })).toBeVisible();
  await page.getByLabel('Experiment type').selectOption('costs');
  await page.getByLabel('Strategy', { exact: true }).selectOption('buy_and_hold');
  const costs = await execute(page);
  if (isTrainTest(costs.result)) throw Error();
  expect(costs.result.costs).toHaveLength(2);
  expect(costs.result.comparisons.some(c => c.kind === 'cost_reference')).toBe(true);
  await page.getByLabel('Experiment type').selectOption('subperiods');
  await page.getByLabel('End 1', { exact: true }).fill('2024-01-03');
  await page.getByLabel('Start 2', { exact: true }).fill('2024-01-04');
  const periods = await execute(page);
  if (isTrainTest(periods.result)) throw Error();
  expect(periods.result.runs.map(r => r.performance.simulation.valuations.length)).toEqual([3, 6]);
  await page.getByLabel('Experiment type').selectOption('train_test');
  await page.getByLabel('Strategy', { exact: true }).selectOption('momentum');
  await page.getByLabel('Training end', { exact: true }).fill('2024-01-06');
  await page.getByLabel('Test start', { exact: true }).fill('2024-01-07');
  const split = await execute(page);
  if (!isTrainTest(split.result)) throw Error();
  expect(split.result.selection.selected_configuration).toEqual({ lookback: 2, threshold: '0' });
  const splitResult = split.result;
  const testRun = splitResult.test_runs.find(r => r.run_id === splitResult.selected_test_run_id)!;
  expect(testRun.performance.simulation.valuations[0].cash).toBe('1000.00');
  expect(testRun.performance.equity.cumulative_return.value).toBe(-0.54);
  await expect(page.getByText('OUT-OF-SAMPLE TEST', { exact: true })).toBeVisible();
  await expect(page.getByText('-54.00%', { exact: true }).first()).toBeVisible();
  await page.getByRole('button', { name: 'Open in Saved Research ↗', exact: true }).click();
  await page.getByRole('button', { name: 'Reproduce saved experiment', exact: true }).click();
  await expect(page.getByText('Recorded outputs match', { exact: true })).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('link', { name: 'Datasets', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Dataset library' })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: path.resolve(frontend, 'test-results/dashboard-mobile.png') });
  await page.getByRole('link', { name: 'Saved Research', exact: true }).click();
  await expect(page.getByText('OUT-OF-SAMPLE TEST', { exact: true })).toBeVisible();
  await expect(page.getByRole('img', { name: /Equity curve in USD/ })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByText('Frozen choice: Momentum 2 · 0', { exact: true }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.resolve(frontend, 'test-results/dashboard-mobile-research.png') });
  await fs.writeFile(path.resolve(frontend, 'test-results/e2e-evidence.json'), JSON.stringify({
    configurations: grid.result.configurations.length, cost_scenarios: costs.result.costs.length,
    subperiod_lengths: periods.result.runs.map(r => r.performance.simulation.valuations.length),
    selected: split.result.selection.selected_configuration, test_return: testRun.performance.equity.cumulative_return,
    test_initial_cash: testRun.performance.simulation.valuations[0].cash, test_warmup_bars: testRun.performance.simulation.warmup_bars,
  }, null, 2) + '\n');
});

test('offline guide downloads a conservative template and unsupported imports stay blocked', async ({ page }) => {
  await page.goto('/#datasets');
  await page.getByText('Offline import guide & templates', { exact: true }).click();
  await expect(page.getByText('Provider import is unavailable.', { exact: true })).toBeVisible();
  const downloadReady = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Download local metadata template', exact: true }).click();
  const download = await downloadReady;
  expect(await download.failure()).toBeNull();
  const template = JSON.parse(await fs.readFile((await download.path())!, 'utf8'));
  expect(template).toMatchObject({ source_kind: 'local_file', adjustment_basis: 'unknown', volume_basis: 'unknown',
    split_status: 'unknown', split_evidence: 'unknown', ohlc_basis_consistent: 'unknown' });
  const synthetic = JSON.parse(await fs.readFile(metadata, 'utf8'));
  const cases = [template, { ...synthetic, split_status: 'unknown', split_evidence: 'unknown' },
    { ...synthetic, adjustment_basis: 'split_adjusted' }];
  for (const declarations of cases) {
    await page.getByRole('link', { name: 'Datasets', exact: true }).click();
    await page.getByLabel('OHLCV CSV', { exact: true }).setInputFiles(source);
    await page.getByLabel('Upload metadata JSON').setInputFiles({ name: 'invented-policy-test.metadata.json', mimeType: 'application/json',
      buffer: Buffer.from(JSON.stringify(declarations)) });
    const importReady = page.waitForResponse(r => r.url().endsWith('/api/v1/datasets') && r.request().method() === 'POST');
    await page.getByRole('button', { name: 'Import dataset →', exact: true }).click();
    expect([200, 201]).toContain((await importReady).status());
    await expect(page.getByText('Validated import', { exact: true })).toBeVisible();
    await expect(page.getByText(/Import validation does not establish simulation eligibility/)).toBeVisible();
    await page.getByRole('button', { name: 'Open Backtest →', exact: true }).click();
    await page.getByText('Risk-free rate & coverage', { exact: true }).click();
    await page.getByRole('checkbox', { name: 'Acknowledge unverified real-data coverage', exact: true }).check();
    const runReady = page.waitForResponse(r => r.url().endsWith('/api/v1/experiments') && r.request().method() === 'POST');
    await page.getByRole('button', { name: 'Run backtest →', exact: true }).click();
    const rejected = await runReady;
    expect(rejected.status()).toBe(422);
    expect((await rejected.json()).error.code).toBe('computation_rejected');
    await expect(page.getByRole('alert')).toContainText('D04 eligibility');
    await expect(page.getByRole('region', { name: 'Saved research result' })).toHaveCount(0);
    await expect(page.getByLabel('Starting capital · USD')).toHaveValue('1000.00');
  }
  await page.getByRole('link', { name: 'Datasets', exact: true }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByText('Offline import guide & templates', { exact: true }).click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole('link', { name: 'Download local metadata template', exact: true }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.resolve(frontend, 'test-results/offline-guide-mobile.png') });
});

test('release checks all three strategy backtests, actual costs, audit states and zero-volume rejection', async ({ page, browser }) => {
  await importExample(page);
  await page.getByRole('button', { name: 'Open Backtest →', exact: true }).click();
  const evidence: Record<string, unknown>[] = [];
  for (const strategy of ['buy_and_hold', 'sma', 'momentum']) {
    await page.getByLabel('Strategy', { exact: true }).selectOption(strategy);
    await page.getByLabel('Commission · USD / fill', { exact: true }).fill(strategy === 'buy_and_hold' ? '2.00' : '0.00');
    await page.getByLabel('Slippage · bps', { exact: true }).fill(strategy === 'buy_and_hold' ? '100' : '0');
    if (strategy === 'sma') {
      await page.getByLabel('Fast window', { exact: true }).fill('2');
      await page.getByLabel('Slow window', { exact: true }).fill('3');
    }
    if (strategy === 'momentum') await page.getByLabel('Lookback', { exact: true }).fill('2');
    const saved = await execute(page, 'Run backtest →');
    if (isTrainTest(saved.result)) throw Error('Expected a fixed backtest.');
    const run = saved.result.runs.find(r => r.role === 'candidate')!;
    const simulation = run.performance.simulation;
    expect(simulation.final_equity).toBe(strategy === 'buy_and_hold' ? '792.20' : '910.00');
    expect(simulation.final_shares).toBe(strategy === 'buy_and_hold' ? 98 : 0);
    expect(simulation.fills).toHaveLength(strategy === 'buy_and_hold' ? 1 : 2);
    if (strategy === 'buy_and_hold') {
      expect(simulation.fills[0]).toMatchObject({ quantity: 98, effective_price: '10.100000', fee: '2.00', cash_change: '-991.80' });
      expect(simulation.final_cash).toBe('8.20');
    }
    await expect(page.getByRole('img', { name: /Equity curve in USD/ })).toBeVisible();
    await expect(page.getByRole('table', { name: 'Executed fills', exact: true })).toBeVisible();
    for (const status of ['PASS', 'WARNING', 'NOT_ASSESSED']) {
      const finding = run.audit.findings.find(f => f.status === status)!;
      expect(finding).toBeDefined();
      await page.getByLabel('Audit status filter').selectOption(status);
      await page.getByText(finding.title, { exact: true }).click();
      await expect(page.locator('.finding-body > p').filter({ hasText: finding.explanation }).first()).toBeVisible();
    }
    await page.getByLabel('Audit status filter').selectOption('FAIL');
    await expect(page.getByText('No findings with this assessment.', { exact: true })).toBeVisible();
    evidence.push({ strategy, final_equity: simulation.final_equity, final_shares: simulation.final_shares,
      fills: simulation.fills.length, experiment_id: saved.experiment_id });
  }
  // Deliberately invented zero-volume bar, not a repaired or actual market export.
  const zeroVolume = (await fs.readFile(source, 'utf8')).split('\n').map(line =>
    line.startsWith('2024-01-02,') ? line.replace(/,\d+$/, ',0') : line).join('\n');
  await page.getByRole('link', { name: 'Datasets', exact: true }).click();
  await page.getByLabel('OHLCV CSV', { exact: true }).setInputFiles({ name: 'invented-zero-volume.csv', mimeType: 'text/csv', buffer: Buffer.from(zeroVolume) });
  await page.getByLabel('Upload metadata JSON').setInputFiles(metadata);
  const imported = page.waitForResponse(r => r.url().endsWith('/api/v1/datasets') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Import dataset →', exact: true }).click();
  expect((await imported).status()).toBe(201);
  await page.getByRole('button', { name: 'Open Backtest →', exact: true }).click();
  const saved = await execute(page, 'Run backtest →');
  if (isTrainTest(saved.result)) throw Error('Expected a backtest.');
  const rejected = saved.result.runs[0].performance.simulation;
  expect(rejected.orders[0]).toMatchObject({ status: 'REJECTED', reason: 'zero_volume', outcome_session: '2024-01-02' });
  expect(rejected.fills).toHaveLength(1);
  expect(rejected.final_equity).toBe('668.00');
  await expect(page.getByRole('table', { name: 'Order outcomes', exact: true })).toContainText('zero_volume');
  await page.getByRole('table', { name: 'Order outcomes', exact: true }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.resolve(frontend, 'test-results/release-order-outcomes.png') });
  await fs.writeFile(path.resolve(frontend, 'test-results/release-evidence.json'), JSON.stringify({ browser: browser.version(), backtests: evidence,
    rejected_order: rejected.orders[0], zero_volume_final_equity: rejected.final_equity }, null, 2) + '\n');
});
