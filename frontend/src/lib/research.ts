import type { Cost, Dataset, ExperimentRequest, Period, StrategyInput } from '../api/schemas';

export type StrategyKind = 'buy_and_hold' | 'sma' | 'momentum';
export type Study = 'parameters' | 'costs' | 'subperiods' | 'train_test';
export type FormValues = {
  strategy: StrategyKind; capital: string; fast: string; slow: string; lookback: string; threshold: string;
  fastGrid: string; slowGrid: string; lookbackGrid: string; thresholdGrid: string;
  commission: string; slippage: string; riskFree: string; start: string; end: string;
  acknowledge: boolean; benchmark: boolean; warmup: boolean;
  trainStart: string; trainEnd: string; testStart: string; testEnd: string;
};
export function defaults(dataset: Dataset): FormValues {
  return { strategy: 'buy_and_hold', capital: '1000.00', fast: '2', slow: '5', lookback: '2', threshold: '0',
    fastGrid: '1,2', slowGrid: '3,4', lookbackGrid: '1,2', thresholdGrid: '0', commission: '0.00', slippage: '0', riskFree: '0',
    start: dataset.validation.first_date, end: dataset.validation.last_date, acknowledge: false, benchmark: true, warmup: true,
    trainStart: dataset.validation.first_date, trainEnd: '', testStart: '', testEnd: dataset.validation.last_date };
}
function decimal(value: string, label: string): string {
  if (value.length > 128 || !/^-?\d+(?:\.\d+)?$/.test(value) || !Number.isFinite(Number(value))) throw new Error(`${label} must be a finite plain decimal string, without exponent notation.`);
  return value;
}
function positiveInteger(value: string, label: string): number {
  if (!/^\d+$/.test(value) || !Number.isSafeInteger(Number(value)) || Number(value) <= 0) throw new Error(`${label} must be a positive, safely represented integer.`);
  return Number(value);
}
function list(value: string, label: string): string[] {
  const entries = value.split(',').map(x => x.trim());
  if (!entries.length || entries.some(x => !x)) throw new Error(`${label} needs a comma-separated list without empty entries.`);
  if (new Set(entries).size !== entries.length) throw new Error(`${label} contains duplicate entries.`);
  return entries;
}
function configuration(values: FormValues, fast = values.fast, slow = values.slow, lookback = values.lookback, threshold = values.threshold): StrategyInput {
  if (values.strategy === 'buy_and_hold') return { kind: 'buy_and_hold' };
  if (values.strategy === 'sma') {
    const f = positiveInteger(fast, 'Fast window'), s = positiveInteger(slow, 'Slow window');
    if (f >= s) throw new Error('Every SMA combination must have fast window < slow window. No pair will be skipped.');
    return { kind: 'sma', fast_window: f, slow_window: s };
  }
  return { kind: 'momentum', lookback: positiveInteger(lookback, 'Momentum lookback'), threshold: decimal(threshold, 'Momentum threshold') };
}
export function configurations(values: FormValues, grid: boolean): StrategyInput[] {
  if (!grid || values.strategy === 'buy_and_hold') return [configuration(values)];
  const first = list(values.strategy === 'sma' ? values.fastGrid : values.lookbackGrid, 'First parameter axis');
  const second = list(values.strategy === 'sma' ? values.slowGrid : values.thresholdGrid, 'Second parameter axis');
  if (first.length * second.length + (values.benchmark ? 1 : 0) > 100) throw new Error('The grid exceeds 100 configurations including the buy-and-hold reference. Reduce an axis.');
  return first.flatMap(a => second.map(b => values.strategy === 'sma' ? configuration(values, a, b) : configuration(values, undefined, undefined, a, b)));
}
export function validatePeriod(period: Period, label: string): Period {
  for (const day of [period.start_date, period.end_date]) {
    const parsed = new Date(day + 'T00:00:00Z');
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day) || !Number.isFinite(parsed.valueOf()) || parsed.toISOString().slice(0, 10) !== day) throw new Error(`${label} requires valid ISO start and end dates.`);
  }
  if (period.start_date > period.end_date) throw new Error(`${label} start must be on or before its end.`);
  return period;
}
export function validateCost(cost: Cost): Cost {
  const commission = decimal(cost.commission_per_fill_usd, 'Commission'), slippage = decimal(cost.slippage_bps, 'Slippage');
  if (Number(commission) < 0 || Number(slippage) < 0 || Number(slippage) >= 10000) throw new Error('Commission must be nonnegative and slippage must be 0 ≤ bps < 10,000.');
  return cost;
}
export function buildRequest(dataset: Dataset, values: FormValues, study?: Study, costs: Cost[] = [], periods: Period[] = []): ExperimentRequest {
  const capital = decimal(values.capital, 'Starting capital');
  if (Number(capital) <= 0) throw new Error('Starting capital must be positive.');
  const riskFree = decimal(values.riskFree, 'Annual risk-free rate');
  if (Number(riskFree) <= -1) throw new Error('Annual risk-free rate must be greater than -1.');
  const configs = configurations(values, study === 'parameters' || study === 'train_test');
  const request: ExperimentRequest = { dataset_id: dataset.dataset_id, mode: study === 'train_test' ? 'train_test' : study ? 'grid' : 'backtest',
    initial_capital: capital, configurations: configs, settings: { ...validateCost({ commission_per_fill_usd: study === 'costs' ? '0.00' : values.commission,
      slippage_bps: study === 'costs' ? '0' : values.slippage }), acknowledge_unverified_coverage: values.acknowledge },
    include_benchmark: values.benchmark, annual_risk_free_rate: riskFree };
  if (study === 'train_test') {
    request.training_period = validatePeriod({ start_date: values.trainStart, end_date: values.trainEnd }, 'Training window');
    request.test_period = validatePeriod({ start_date: values.testStart, end_date: values.testEnd }, 'Test window');
    if (request.training_period.end_date >= request.test_period.start_date) throw new Error('Training must end strictly before the test window starts.');
    request.warmup = values.warmup;
  } else if (study === 'subperiods') {
    if (periods.length < 2) throw new Error('Add at least two explicit subperiods for this comparison.');
    request.periods = periods.map((period, index) => validatePeriod(period, `Subperiod ${index + 1}`));
  } else {
    request.periods = [validatePeriod({ start_date: values.start, end_date: values.end }, 'Evaluation window')];
    if (study === 'costs') {
      if (costs.length < 2) throw new Error('Add at least two cost scenarios. The first is the reference.');
      request.costs = costs.map(validateCost);
    }
  }
  return request;
}
