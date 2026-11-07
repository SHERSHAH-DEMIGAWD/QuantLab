import { z } from 'zod';

const text = z.string();
const integer = z.number().int().nonnegative().max(Number.MAX_SAFE_INTEGER);
const day = z.string().regex(/^\d{4}-\d{2}-\d{2}$/);
const decimal = z.string().regex(/^-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?$/).refine(v => Number.isFinite(Number(v)));
const hash = z.string().regex(/^[a-f0-9]{64}$/);
const id = z.string().regex(/^[a-f0-9]{32}$/);
const period = z.object({ start_date: day, end_date: day });
const cost = z.object({ commission_per_fill_usd: decimal, slippage_bps: decimal });

export const metricSchema = z.object({ value: z.union([z.number().finite(), decimal, z.null()]), reason: text.nullable() })
  .refine(v => v.value === null ? !!v.reason : v.reason === null);
export type Metric = z.infer<typeof metricSchema>;
export const strategySchema = z.union([
  z.object({ fast_window: integer, slow_window: integer }).strict(),
  z.object({ lookback: integer, threshold: decimal }).strict(), z.object({}).strict(),
]);
export type Strategy = z.infer<typeof strategySchema>;
export type StrategyInput = { kind: 'buy_and_hold' } | { kind: 'sma'; fast_window: number; slow_window: number }
  | { kind: 'momentum'; lookback: number; threshold: string };
export type Period = z.infer<typeof period>;
export type Cost = z.infer<typeof cost>;
export type ExperimentRequest = {
  dataset_id: string; mode: 'backtest' | 'grid' | 'train_test'; initial_capital: string;
  configurations: StrategyInput[]; settings: Cost & { acknowledge_unverified_coverage: boolean };
  periods?: Period[]; costs?: Cost[]; training_period?: Period; test_period?: Period;
  include_benchmark: boolean; annual_risk_free_rate: string; warmup?: boolean;
};

export const metadataSchema = z.looseObject({
  contract_version: z.literal(1), symbol: text, exchange: text, currency: z.literal('USD'), frequency: z.literal('1d'),
  session_timezone: text, source_kind: z.enum(['synthetic', 'local_file']), source_name: text,
  adjustment_basis: text, source_reference: text, usage_note: text,
  ohlc_basis_consistent: z.union([z.boolean(), z.literal('unknown')]), volume_basis: text,
  split_status: text, split_evidence: text, session_coverage: text,
});
const validationSchema = z.looseObject({
  importer_version: text, row_count: integer, first_date: day, last_date: day, source_byte_count: integer,
  source_sha256: hash, metadata_sha256: hash, dataset_id: hash, warnings: z.array(text),
  coverage_assessment: text, zero_volume_rows: integer,
  normalization: z.object({ csv_bom_removed: z.boolean(), whitespace_fields_trimmed: integer, rows_reordered: z.boolean() }),
  calendar_gaps: z.array(z.object({ previous_date: day, next_date: day, unobserved_calendar_days: integer })),
});
export const datasetSchema = z.object({ dataset_id: hash, metadata: metadataSchema, validation: validationSchema, created_at: text });
export const importSchema = datasetSchema.extend({ duplicate: z.boolean() });
export type Dataset = z.infer<typeof datasetSchema>;
export const datasetSummarySchema = z.object({ dataset_id: hash, first_date: day, last_date: day, row_count: integer, created_at: text });
export type DatasetSummary = z.infer<typeof datasetSummarySchema>;

export const statuses = ['PASS', 'FAIL', 'WARNING', 'NOT_ASSESSED'] as const;
export const findingSchema = z.object({
  rule_id: text, title: text, status: z.enum(statuses), severity: z.enum(['ERROR', 'WARNING']).nullable(),
  explanation: text, suggested_action: text.nullable(),
  evidence: z.array(z.object({ reference: text, observed: text, expected: text.nullable(), order_id: integer.nullable(),
    fill_index: integer.nullable(), session: day.nullable() })),
});
export type Finding = z.infer<typeof findingSchema>;
const auditSchema = z.object({ audit_version: text, dataset_id: hash, findings: z.array(findingSchema) });
export const valuationSchema = z.object({ session: day, cash: decimal, shares: integer, close: decimal,
  market_value: decimal, equity: decimal, cost_basis: decimal, realized_pnl: decimal, unrealized_pnl: decimal });
export type Valuation = z.infer<typeof valuationSchema>;
const fillSchema = z.object({ order_id: integer, session: day, side: z.enum(['BUY', 'SELL']), quantity: integer,
  base_open: decimal, effective_price: decimal, notional: decimal, fee: decimal, cash_change: decimal });
const orderSchema = z.object({ order_id: integer, decision_session: day, eligible_session: day.nullable(), target: text,
  side: z.enum(['BUY', 'SELL']), budget: decimal.nullable(), requested_shares: integer.nullable(),
  status: z.enum(['PENDING', 'FILLED', 'REJECTED', 'EXPIRED']), outcome_session: day.nullable(),
  reason: text.nullable(), base_open: decimal.nullable(), effective_price: decimal.nullable() });
const settingsSchema = cost.extend({ start_date: day.nullable(), end_date: day.nullable(),
  acknowledge_unverified_coverage: z.boolean(), sell_after_session: day.nullable(),
  warmup_start_date: day.nullable(), warmup_end_date: day.nullable() });
const simulationSchema = z.object({
  engine_version: text, dataset_id: hash, source_sha256: hash, metadata_sha256: hash, metadata: metadataSchema,
  start_date: day, end_date: day, initial_capital: decimal, settings: settingsSchema, strategy: strategySchema,
  final_cash: decimal, final_shares: integer, final_equity: decimal, realized_pnl: decimal, unrealized_pnl: decimal,
  valuations: z.array(valuationSchema).min(2), decisions: z.array(z.object({ session: day, target: text, cash: decimal, shares: integer })),
  orders: z.array(orderSchema), fills: z.array(fillSchema), assumptions: z.array(text), warnings: z.array(text),
  warmup_start: day.nullable(), warmup_end: day.nullable(), warmup_bars: integer,
});
const equitySchema = z.object({
  daily_returns: z.array(z.object({ session: day, metric: metricSchema })), cumulative_return: metricSchema,
  annualized_return: metricSchema, maximum_drawdown: metricSchema, annualized_volatility: metricSchema,
  sharpe_ratio: metricSchema, annual_risk_free_rate: decimal, annualization_extrapolated: z.boolean(),
  assumptions: z.array(text), warnings: z.array(text),
});
const closedTrade = z.object({ entry_order_id: integer, exit_order_id: integer, entry_session: day, exit_session: day,
  quantity: integer, entry_debit: decimal, exit_credit: decimal, net_pnl: decimal });
const openPosition = z.object({ entry_order_id: integer, entry_session: day, quantity: integer, entry_debit: decimal,
  last_close: decimal, market_value: decimal, unrealized_pnl: decimal });
const tradesSchema = z.object({ closed_trades: z.array(closedTrade), closed_trade_count: integer, winning_trades: integer,
  losing_trades: integer, break_even_trades: integer, win_rate: metricSchema, mean_net_pnl: metricSchema, open_position: openPosition.nullable() });
export const runSchema = z.object({ run_id: text, phase: z.enum(['evaluation', 'training', 'test']), role: z.enum(['candidate', 'benchmark']),
  requested_period: period, performance: z.object({ simulation: simulationSchema, equity: equitySchema, trades: tradesSchema }), audit: auditSchema });
export type Run = z.infer<typeof runSchema>;
const comparison = z.object({ kind: z.enum(['benchmark', 'cost_reference']), run_id: text, reference_run_id: text,
  final_equity_difference: decimal, cumulative_return_difference: metricSchema, maximum_drawdown_difference: metricSchema });
const workload = z.object({ run_count: integer, evaluated_bars: integer, warmup_bars: integer });
const source = z.object({ source_snapshot_sha256: hash, source_files: z.array(z.tuple([text, hash])), python_version: text, explanation: text });
export const experimentResultSchema = z.object({ experiment_type: text, experiment_version: z.literal('1.0.0'), dataset_id: hash,
  configurations: z.array(strategySchema), periods: z.array(period), costs: z.array(cost), runs: z.array(runSchema).min(1),
  comparisons: z.array(comparison), workload, reproducibility: source, assumptions: z.array(text) });
export const trainTestResultSchema = z.object({ training: experimentResultSchema,
  selection: z.object({ selected_configuration: strategySchema, selected_training_run_id: text, ranked_training_run_ids: z.array(text), criterion: text, tie_break: text }),
  requested_test_period: period, test_runs: z.array(runSchema).min(1), selected_test_run_id: text,
  benchmark_test_run_id: text.nullable(), test_comparison: comparison.nullable(), planned_workload: workload, actual_workload: workload,
  assumptions: z.array(text) });
export type ExperimentResult = z.infer<typeof experimentResultSchema>;
export type TrainTestResult = z.infer<typeof trainTestResultSchema>;
export type Result = ExperimentResult | TrainTestResult;
export function isTrainTest(result: Result): result is TrainTestResult { return 'training' in result; }

const implementation = z.looseObject({ payload_version: z.literal(1), request_version: z.literal(1), engine_version: text,
  importer_version: text, audit_version: text, experiment_version: text, source, sqlite_version: text,
  dependencies: z.record(text, text) });
export const experimentSchema = z.object({ experiment_id: id, dataset_id: hash, mode: z.enum(['backtest', 'grid', 'train_test']),
  request: z.looseObject({ dataset_id: hash, mode: text, initial_capital: decimal, configurations: z.array(z.unknown()).min(1), request_version: z.literal(1) }),
  result: z.union([trainTestResultSchema, experimentResultSchema]), implementation, result_sha256: hash, created_at: text });
export type Experiment = z.infer<typeof experimentSchema>;
export const experimentSummarySchema = z.object({ experiment_id: id, dataset_id: hash, mode: z.enum(['backtest', 'grid', 'train_test']), created_at: text });
export type ExperimentSummary = z.infer<typeof experimentSummarySchema>;
export const reproductionSchema = z.object({ experiment_id: id, status: z.enum(['matched', 'mismatch', 'implementation_changed']),
  economic_match: z.boolean(), implementation_match: z.boolean(), saved_economic_sha256: hash, current_economic_sha256: hash,
  difference_paths: z.array(text).max(20), difference_path_limit: integer, current_implementation: implementation, limitations: z.array(text) });
export type Reproduction = z.infer<typeof reproductionSchema>;
export const errorSchema = z.object({ error: z.object({ code: text, message: text, details: z.unknown().optional() }) });
export const healthSchema = z.object({ status: z.literal('ok'), api_version: text, schema_version: integer });
export const datasetListSchema = z.object({ items: z.array(datasetSummarySchema), limit: integer, offset: integer });
export const experimentListSchema = z.object({ items: z.array(experimentSummarySchema), limit: integer, offset: integer });
