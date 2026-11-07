import { describe, expect, it, vi } from 'vitest';
import { api, ApiError } from '../api/client';
import { datasetSchema, experimentSchema, isTrainTest, reproductionSchema } from '../api/schemas';
import { money, metricText, sessionLabel } from '../lib/format';
import { decodeCsv, MAX_CSV_BYTES, readCsv, validateUpload } from '../lib/upload';
import { buildRequest, defaults } from '../lib/research';
import datasetJson from './fixtures/dataset.json';
import backtestJson from './fixtures/backtest.json';
import gridJson from './fixtures/grid.json';
import trainJson from './fixtures/train_test.json';

const dataset = datasetSchema.parse(datasetJson);

describe('actual backend response contract', () => {
  it.each([backtestJson, gridJson, trainJson])('validates captured successful API records', record => {
    expect(experimentSchema.parse(record).dataset_id).toBe(dataset.dataset_id);
  });
  it('retains the real training winner and disappointing held-out result', () => {
    const record = experimentSchema.parse(trainJson);
    const result = record.result;
    expect(isTrainTest(result)).toBe(true);
    if (!isTrainTest(result)) throw Error();
    expect(result.selection.selected_configuration).toEqual({ lookback: 2, threshold: '0' });
    const test = result.test_runs.find(r => r.run_id === result.selected_test_run_id)!;
    expect(test.performance.simulation.final_equity).toBe('460.00');
    expect(test.performance.equity.cumulative_return.value).toBe(-0.54);
  });
  it('rejects malformed records and unknown audit assessments', () => {
    const record = structuredClone(backtestJson);
    (record.result.runs[0].audit.findings[0] as { status: string }).status = 'SAFE';
    expect(experimentSchema.safeParse(record).success).toBe(false);
    expect(experimentSchema.safeParse({ result: {} }).success).toBe(false);
  });
});

describe('financial presentation without floating money conversion', () => {
  it.each([
    ['999999999999999999999.99', '$999,999,999,999,999,999,999.99'],
    ['0.00000100', '$0.000001'], ['-1.005', '-$1.005'], ['1000.00', '$1,000.00'],
    ['0E-9999', '$0.00'], ['1E+4', '$10,000.00'],
  ])('formats %s exactly', (value, expected) => expect(money(value)).toBe(expected));
  it('formats fractional metrics and preserves undefined reasons separately', () => {
    expect(metricText({ value: 0.079, reason: null }, 'percent')).toBe('7.90%');
    expect(metricText({ value: null, reason: 'no_closed_trades' }, 'percent')).toBe('Unavailable');
    expect(metricText({ value: Number.MAX_VALUE, reason: null }, 'percent')).not.toMatch(/Infinity|NaN|∞/);
  });
  it('does not shift exchange-session labels through local time', () => expect(sessionLabel('2024-01-01')).toBe('01 Jan 2024'));
});

describe('original input handling', () => {
  it('preserves original UTF-8 BOM and CRLF', () => {
    const source = '\ufeffdate,open,high,low,close,volume\r\n';
    expect(decodeCsv(new TextEncoder().encode(source).buffer)).toBe(source);
  });
  it('rejects invalid UTF-8 and oversized files before decoding', async () => {
    expect(() => decodeCsv(new Uint8Array([0xff]).buffer)).toThrow('UTF-8');
    await expect(readCsv({ size: MAX_CSV_BYTES + 1 } as File)).rejects.toThrow('10 MiB');
  });
  it.each(['', '[]', 'null', '{oops'])('rejects invalid metadata object %s', metadata => {
    expect(() => validateUpload('date,open', metadata)).toThrow();
  });
  it('does not drop duplicate metadata keys before backend validation', () => {
    const raw = '{"symbol":"A","symbol":"B"}';
    expect(validateUpload('date,open', raw)).toBe(raw);
  });
});

describe('request construction delegates financial computation', () => {
  it('builds conditional SMA/momentum requests with exact monetary strings', () => {
    const values = { ...defaults(dataset), strategy: 'sma' as const, capital: '999999999.99' };
    const request = buildRequest(dataset, values);
    expect(request.configurations).toEqual([{ kind: 'sma', fast_window: 2, slow_window: 5 }]);
    expect(request.initial_capital).toBe('999999999.99');
    expect(buildRequest(dataset, { ...values, strategy: 'momentum' }).configurations).toEqual([{ kind: 'momentum', lookback: 2, threshold: '0' }]);
  });
  it('rejects any invalid Cartesian pair and excessive configurations without truncation', () => {
    expect(() => buildRequest(dataset, { ...defaults(dataset), strategy: 'sma', fastGrid: '1,3', slowGrid: '3' }, 'parameters')).toThrow('Every SMA');
    expect(() => buildRequest(dataset, { ...defaults(dataset), strategy: 'momentum', lookbackGrid: Array.from({ length: 100 }, (_, i) => i + 1).join(',') }, 'parameters')).toThrow('100');
  });
  it('uses explicit first-cost ordering and avoids conflicting base costs', () => {
    const costs = [{ commission_per_fill_usd: '2.00', slippage_bps: '100' }, { commission_per_fill_usd: '0', slippage_bps: '0' }];
    const request = buildRequest(dataset, { ...defaults(dataset), commission: '5' }, 'costs', costs);
    expect(request.costs).toEqual(costs); expect(request.settings.commission_per_fill_usd).toBe('0.00');
  });
  it('preserves explicitly unequal subperiods and strictly separates training/test', () => {
    const periods = [{ start_date: '2024-01-01', end_date: '2024-01-03' }, { start_date: '2024-01-04', end_date: '2024-01-09' }];
    expect(buildRequest(dataset, defaults(dataset), 'subperiods', [], periods).periods).toEqual(periods);
    expect(() => buildRequest(dataset, { ...defaults(dataset), trainEnd: '2024-01-06', testStart: '2024-01-06' }, 'train_test')).toThrow('strictly before');
    const request = buildRequest(dataset, { ...defaults(dataset), trainEnd: '2024-01-06', testStart: '2024-01-07' }, 'train_test');
    expect(request.warmup).toBe(true); expect(request.mode).toBe('train_test'); expect(request.periods).toBeUndefined();
  });
});

describe('typed HTTP client', () => {
  it('validates successful JSON and carries the configured API prefix', async () => {
    const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(backtestJson), { status: 200 })); vi.stubGlobal('fetch', fetch);
    expect((await api.experiment(backtestJson.experiment_id)).experiment_id).toBe(backtestJson.experiment_id);
    expect(fetch.mock.calls[0][0]).toBe('/api/v1/experiments/' + backtestJson.experiment_id);
  });
  it('preserves actionable field-level API errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: { code: 'invalid_dataset', message: 'Dataset validation failed.', details: { issues: [{ field: 'ohlc', row: 2, message: 'Invalid OHLC.' }] } } }), { status: 422 })));
    await expect(api.importDataset('csv', '{}')).rejects.toMatchObject({ code: 'invalid_dataset', status: 422 });
  });
  it('distinguishes network and unexpected successful responses', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('private internals')));
    await expect(api.datasets()).rejects.toMatchObject({ code: 'backend_unavailable' });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}')));
    await expect(api.datasets()).rejects.toMatchObject({ code: 'unexpected_response' });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('<html>stack</html>')));
    await expect(api.datasets()).rejects.toMatchObject({ code: 'malformed_response' });
  });
  it('passes metadata duplicates as raw JSON and reproduction with no body', async () => {
    const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(datasetJson))); vi.stubGlobal('fetch', fetch);
    await api.importDataset('csv', '{"symbol":"A","symbol":"B"}');
    expect(fetch.mock.calls[0][1].body).toContain('"symbol":"A","symbol":"B"');
    fetch.mockResolvedValue(new Response('{}'));
    await expect(api.reproduce(backtestJson.experiment_id)).rejects.toBeInstanceOf(ApiError);
    expect(fetch.mock.calls[1][1]).toEqual({ method: 'POST' });
  });
  it('rejects unknown reproduction states instead of presenting a match', () => expect(reproductionSchema.safeParse({ status: 'verified_safe' }).success).toBe(false));
});
