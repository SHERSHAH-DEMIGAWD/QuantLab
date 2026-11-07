import { useEffect, useRef, useState } from 'react';
import uPlot from 'uplot';
import 'uplot/dist/uPlot.min.css';
import type { Valuation } from '../api/schemas';
import { money, sessionLabel } from '../lib/format';

export function EquityChart({ values }: { values: Valuation[] }) {
  const container = useRef<HTMLDivElement>(null), plot = useRef<uPlot | null>(null);
  const [hover, setHover] = useState<number | null>(null);
  useEffect(() => {
    const element = container.current;
    if (!element) return;
    let alive = true;
    const times = values.map(v => Date.parse(v.session + 'T00:00:00Z') / 1000);
    const options: uPlot.Options = {
      width: Math.max(100, element.clientWidth), height: 280,
      padding: [16, 12, 0, 0], legend: { show: false },
      cursor: { drag: { x: true, y: false } },
      scales: { x: { time: false } },
      series: [{}, { label: 'Equity (USD)', stroke: '#248268', width: 2, fill: 'rgba(36,130,104,0.07)', points: { show: false } }],
      axes: [
        { stroke: '#6a776e', grid: { show: false }, ticks: { show: false }, font: '11px sans-serif',
          values: (_, ticks) => ticks.map(t => { const d = new Date(t * 1000); return `${d.getUTCDate()}/${d.getUTCMonth() + 1}/${String(d.getUTCFullYear()).slice(-2)}`; }) },
        { stroke: '#6a776e', size: 75, grid: { stroke: '#e7ece6', width: 1 }, ticks: { show: false }, font: '11px sans-serif',
          values: (_, ticks) => ticks.map(v => new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 2 }).format(v)) },
      ],
      hooks: { setCursor: [chart => { if (alive) setHover(chart.cursor.idx ?? null); }] },
    };
    plot.current = new uPlot(options, [times, values.map(v => Number(v.equity))], element);
    const observer = new ResizeObserver(() => plot.current?.setSize({ width: Math.max(100, element.clientWidth), height: 280 }));
    observer.observe(element);
    return () => { alive = false; observer.disconnect(); plot.current?.destroy(); plot.current = null; };
  }, [values]);
  const point = values[hover ?? values.length - 1] || values[values.length - 1];
  return <div className="equity-chart"><div className="chart-heading"><div><h3>Equity curve</h3><p>USD · observed session closes</p></div>
    <div className="chart-readout" aria-live="polite"><strong>{money(point.equity)}</strong><small>{sessionLabel(point.session)}</small></div></div>
    <div ref={container} role="img" aria-label="Equity curve in USD; exact session values are in Equity observations" />
    <div className="chart-caption"><span>Chart coordinates are approximate. Exact stored values are available below.</span>
      <button className="text-button" onClick={() => plot.current?.setScale('x', { min: Date.parse(values[0].session + 'T00:00:00Z') / 1000,
        max: Date.parse(values[values.length - 1].session + 'T00:00:00Z') / 1000 })}>Reset chart view</button></div>
  </div>;
}
