'use client';

import * as React from 'react';
import { Icon } from './controls';
import { Badge } from './status';
import { cx, formatPrice } from './util';

// ── PriceChart ──────────────────────────────────────────────────────────────────────────
export interface PricePoint {
  /** Axis and tooltip label for the bar, e.g. "09:45". */
  t: string;
  close: number;
}

export interface PriceLevel {
  /** entry: solid muted · stop: dashed orange · target: dotted blue (strong: dashed 2px, for TP2) · fib: dotted gray. */
  kind: 'entry' | 'stop' | 'target' | 'fib';
  price: number;
  /** Short tag, e.g. "SL", "TP1", "0.705". */
  label: string;
  strong?: boolean;
}

export interface PriceMarker {
  /** Index into data of the confirmed signal bar. */
  index: number;
  side: 'buy' | 'sell';
}

export interface PriceChartProps {
  data: PricePoint[];
  levels?: PriceLevel[];
  markers?: PriceMarker[];
  /** Accessible name and table caption, e.g. "ES 5m closes". */
  label: string;
  /** Price precision for axis, labels and tooltip. */
  tickSize?: number;
  /** Plot height in px; `chart-height` (300px) by default. */
  height?: number;
  className?: string;
}

function niceStep(raw: number): number {
  const p = Math.pow(10, Math.floor(Math.log10(raw)));
  const f = raw / p;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * p;
}

const M = { top: 12, right: 124, bottom: 28, left: 64 };

// Measure before paint in the browser; fall back to useEffect during server rendering, where layout effects warn.
const useIsoLayoutEffect = typeof window !== 'undefined' ? React.useLayoutEffect : React.useEffect;

/** A legend key drawn with the chart's own level-line styles, so tickets and cards match the plot exactly. */
export function LevelKey({ kind, strong }: { kind: PriceLevel['kind']; strong?: boolean }) {
  return (
    <svg className="qe-key" width={16} height={4} viewBox="0 0 16 4" aria-hidden="true" focusable="false">
      <g className={cx('qe-chart-level', 'is-' + kind, strong && 'is-strong')}>
        <line className="qe-chart-level-line" x1={0} x2={16} y1={2} y2={2} />
      </g>
    </svg>
  );
}

export function PriceChart({ data, levels = [], markers = [], label, tickSize = 0.01, height = 300, className }: PriceChartProps) {
  const wrap = React.useRef<HTMLDivElement>(null);
  const [width, setWidth] = React.useState(640);
  const [hover, setHover] = React.useState<number | null>(null);

  useIsoLayoutEffect(() => {
    const el = wrap.current;
    let ro: ResizeObserver | null = null;
    if (el) {
      const update = () => setWidth(Math.max(320, Math.round(el.clientWidth)));
      update();
      ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(update) : null;
      ro?.observe(el);
    }
    return () => ro?.disconnect();
  }, []);

  const n = data.length;
  const plotW = width - M.left - M.right;
  const all = data.map((d) => d.close).concat(levels.map((l) => l.price));
  const lo = all.length ? Math.min(...all) : 0;
  const hi = all.length ? Math.max(...all) : 1;
  const pad = (hi - lo) * 0.08 || 1;
  const d0 = lo - pad, d1 = hi + pad;
  const x = (i: number) => M.left + (n <= 1 ? plotW / 2 : (i * plotW) / (n - 1));
  const y = (v: number) => M.top + (1 - (v - d0) / (d1 - d0)) * height;

  const step = niceStep((hi - lo || 1) / 4);
  const yTicks: number[] = [];
  for (let v = Math.ceil(d0 / step) * step; v <= d1 + 1e-9; v += step) {
    yTicks.push(v);
  }
  // At most six x labels, and never closer than one label width: 12px mono runs about 7.8px a character.
  const labelW = Math.max(1, ...data.map((d) => d.t.length)) * 7.8 + 12;
  const pxPerBar = n > 1 ? plotW / (n - 1) : plotW;
  const every = Math.max(1, Math.ceil(n / 6), Math.ceil(labelW / pxPerBar));
  const xTicks = data.map((_, i) => i).filter((i) => i % every === 0);
  const path = data.map((d, i) => (i ? 'L' : 'M') + x(i).toFixed(1) + ',' + y(d.close).toFixed(1)).join('');

  // Level tags sit in the right gutter; nudge apart so they never overlap (min 18px), then draw leaders.
  const tags = levels.map((l) => ({ ...l, ly: y(l.price), ty: y(l.price) }));
  tags.sort((a, b) => a.ly - b.ly);
  for (let i = 1; i < tags.length; i++) {
    tags[i].ty = Math.max(tags[i].ty, tags[i - 1].ty + 18);
  }
  const bottom = M.top + height - 6;
  for (let i = tags.length - 1; i >= 0; i--) {
    const limit = i === tags.length - 1 ? bottom : tags[i + 1].ty - 18;
    tags[i].ty = Math.min(tags[i].ty, limit);
  }

  const onMove = (e: React.PointerEvent<SVGRectElement>) => {
    const r = (e.currentTarget as SVGRectElement).getBoundingClientRect();
    const px = e.clientX - r.left;
    setHover(n <= 1 ? 0 : Math.max(0, Math.min(n - 1, Math.round((px / r.width) * (n - 1)))));
  };
  const onKey = (e: React.KeyboardEvent) => {
    if (!n) {
      return;
    }
    if (e.key === 'ArrowLeft') { e.preventDefault(); setHover((h) => Math.max(0, (h ?? n - 1) - 1)); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); setHover((h) => Math.min(n - 1, (h ?? n - 1) + 1)); }
    else if (e.key === 'Home') { e.preventDefault(); setHover(0); }
    else if (e.key === 'End') { e.preventDefault(); setHover(n - 1); }
    else if (e.key === 'Escape') { setHover(null); }
  };
  const h = hover !== null && data[hover] ? hover : null;
  const tipLeft = h !== null ? (x(h) > M.left + plotW * 0.7 ? x(h) - 12 : x(h) + 12) : 0;
  const tipFlip = h !== null && x(h) > M.left + plotW * 0.7;
  const last = n ? data[n - 1].close : undefined;

  return (
    <div
      ref={wrap}
      className={cx('qe-chart', className)}
      tabIndex={0}
      role="group"
      aria-label={`${label}${last !== undefined ? `, last ${formatPrice(last, tickSize)}` : ''}. Arrow keys move the crosshair.`}
      onKeyDown={onKey}
      onFocus={() => setHover((v) => v ?? (n ? n - 1 : null))}
      onBlur={() => setHover(null)}
    >
      <svg width={width} height={M.top + height + M.bottom} aria-hidden="true" className="qe-chart-svg">
        {yTicks.map((v) => (
          <g key={v}>
            <line className="qe-chart-grid" x1={M.left} x2={M.left + plotW} y1={Math.round(y(v)) + 0.5} y2={Math.round(y(v)) + 0.5} />
            <text className="qe-chart-tick qe-data" x={M.left - 8} y={y(v)} textAnchor="end" dominantBaseline="middle">{formatPrice(v, tickSize)}</text>
          </g>
        ))}
        <line className="qe-chart-axis" x1={M.left} x2={M.left + plotW} y1={M.top + height + 0.5} y2={M.top + height + 0.5} />
        {xTicks.map((i) => (
          <text key={i} className="qe-chart-tick qe-data" x={x(i)} y={M.top + height + 18} textAnchor="middle">{data[i].t}</text>
        ))}

        {tags.map((l, i) => (
          <g key={l.label + i} className={cx('qe-chart-level', 'is-' + l.kind, l.strong && 'is-strong')}>
            <line className="qe-chart-level-line" x1={M.left} x2={M.left + plotW} y1={l.ly} y2={l.ly} />
            <path className="qe-chart-leader" d={`M${M.left + plotW},${l.ly}L${M.left + plotW + 8},${l.ty}`} />
            <line className="qe-chart-level-line qe-chart-key" x1={M.left + plotW + 8} x2={M.left + plotW + 22} y1={l.ty} y2={l.ty} />
            <text className="qe-chart-level-text qe-data" x={M.left + plotW + 26} y={l.ty} dominantBaseline="middle">{l.label} {formatPrice(l.price, tickSize)}</text>
          </g>
        ))}

        <path className="qe-chart-line" d={path} />

        {markers.filter((m) => data[m.index]).map((m) => {
          const cx0 = x(m.index), cy0 = y(data[m.index].close);
          const buy = m.side === 'buy';
          const top = buy ? cy0 + 12 : cy0 - 12 - 18;
          return (
            <g key={m.side + m.index} className={cx('qe-chart-marker', buy ? 'is-buy' : 'is-sell')}>
              <path className="qe-chart-marker-fill" d={buy ? `M${cx0},${cy0 + 5}l5,7h-10z` : `M${cx0},${cy0 - 5}l5,-7h-10z`} />
              <rect className="qe-chart-marker-fill qe-chart-marker-box" x={cx0 - 19} y={top} width={38} height={18} />
              <text className="qe-chart-marker-text qe-label" x={cx0} y={top + 9} textAnchor="middle" dominantBaseline="central">{buy ? 'BUY' : 'SELL'}</text>
            </g>
          );
        })}

        {h !== null ? (
          <g className="qe-chart-hover">
            <line className="qe-chart-cross" x1={x(h)} x2={x(h)} y1={M.top} y2={M.top + height} />
            <circle className="qe-chart-dot" cx={x(h)} cy={y(data[h].close)} r={4} />
          </g>
        ) : null}

        <rect
          className="qe-chart-hit" x={M.left} y={M.top} width={Math.max(plotW, 0)} height={height}
          onPointerMove={onMove} onPointerLeave={() => setHover(null)}
        />
      </svg>

      {h !== null ? (
        <div className={cx('qe-chart-tip', 'qe-data', tipFlip && 'is-flipped')} style={{ left: tipLeft, top: M.top + 8 }} aria-hidden="true">
          <span className="qe-chart-tip-time">{data[h].t}</span>
          <span className="qe-chart-tip-value">{formatPrice(data[h].close, tickSize)}</span>
        </div>
      ) : null}
      <div className="qe-sr-only" aria-live="polite">{h !== null ? `${data[h].t}, close ${formatPrice(data[h].close, tickSize)}` : ''}</div>

      <div className="qe-sr-only">
        <table>
          <caption>{label}</caption>
          <thead><tr><th scope="col">Time</th><th scope="col">Close</th></tr></thead>
          <tbody>{data.map((d, i) => <tr key={i}><td>{d.t}</td><td>{formatPrice(d.close, tickSize)}</td></tr>)}</tbody>
        </table>
      </div>
    </div>
  );
}

// ── StatTile ────────────────────────────────────────────────────────────────────────────
export interface StatTileProps {
  /** Sentence case, no trailing colon, e.g. "Expectancy per trade". */
  label: string;
  /** Preformatted, e.g. "+0.31R" or "−8.4%". */
  value: string;
  /** Where the number comes from. Required: a figure without its basis is not shown. */
  basis: 'backtest' | 'paper' | 'live';
  /** Sample size (trades). Required. */
  n: number;
  /** e.g. "Mar–Sep 2026, out-of-sample". */
  period?: string;
  /** Change vs a named period; `good` decides the color (a rising drawdown is bad). */
  delta?: { value: string; direction: 'up' | 'down'; good: boolean; vs?: string };
  className?: string;
}

export function StatTile({ label, value, basis, n, period, delta, className }: StatTileProps) {
  return (
    <div className={cx('qe-stat', className)}>
      <span className="qe-stat-label qe-label">{label}</span>
      <span className="qe-stat-value qe-price">{value}</span>
      {delta ? (
        <span className={cx('qe-stat-delta', 'qe-data', delta.good ? 'is-good' : 'is-bad')}>
          <Icon name={delta.direction === 'up' ? 'trending-up' : 'trending-down'} size="sm" />
          <span>{delta.value}</span>
          {delta.vs ? <span className="qe-stat-vs">{delta.vs}</span> : null}
          <span className="qe-sr-only">{delta.good ? '(better)' : '(worse)'}</span>
        </span>
      ) : null}
      <span className="qe-stat-basis">
        <Badge variant="outline">{basis.toUpperCase()}</Badge>
        <span className="qe-data">n = {n}{period ? ` · ${period}` : ''}</span>
      </span>
    </div>
  );
}
