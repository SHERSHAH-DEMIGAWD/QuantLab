import type { Metric, Strategy } from '../api/schemas';

function plainDecimal(value: string): string | null {
  const match = /^(-?)(\d+)(?:\.(\d+))?(?:[eE]([+-]?\d+))?$/.exec(value);
  if (!match) return null;
  const [, sign, whole, fraction = '', exponent = '0'] = match;
  const digits = whole + fraction;
  if (/^0+$/.test(digits)) return '0';
  const shift = Number(exponent), point = whole.length + shift;
  if (!Number.isSafeInteger(shift) || Math.abs(shift) > 128) return null;
  const expanded = point <= 0 ? '0.' + '0'.repeat(-point) + digits : point >= digits.length
    ? digits + '0'.repeat(point - digits.length) : digits.slice(0, point) + '.' + digits.slice(point);
  return sign + expanded;
}
export function money(value: string): string {
  const expanded = plainDecimal(value);
  if (expanded === null) return value;
  const negative = expanded.startsWith('-'), [whole, fraction = ''] = expanded.replace(/^-/, '').split('.');
  const significant = fraction.replace(/0+$/, '').padEnd(2, '0');
  const grouped = whole.replace(/^0+(?=\d)/, '').replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  return `${negative ? '-' : ''}$${grouped}.${significant}`;
}
export function metricText(metric: Metric, unit: 'percent' | 'ratio' | 'money' = 'ratio'): string {
  if (metric.value === null) return 'Unavailable';
  if (unit === 'money') return money(String(metric.value));
  const value = Number(metric.value);
  if (!Number.isFinite(value)) return 'Unavailable';
  return new Intl.NumberFormat('en-US', { style: unit === 'percent' ? 'percent' : 'decimal', maximumFractionDigits: 2, minimumFractionDigits: 2 }).format(value);
}
export function strategyName(strategy: Strategy): string {
  if ('fast_window' in strategy) return `SMA ${strategy.fast_window} / ${strategy.slow_window}`;
  if ('lookback' in strategy) return `Momentum ${strategy.lookback} · ${strategy.threshold}`;
  return 'Buy and hold';
}
export function sessionLabel(value: string): string {
  const [year, month, day] = value.split('-');
  return `${day} ${['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][Number(month)-1]} ${year}`;
}
export function timestamp(value: string): string {
  const parsed = new Date(value);
  return Number.isFinite(parsed.valueOf()) ? parsed.toLocaleString('en-GB', { timeZone: 'UTC', dateStyle: 'medium', timeStyle: 'short' }) + ' UTC' : value;
}
export function shortId(value: string): string { return value.slice(0, 10); }
