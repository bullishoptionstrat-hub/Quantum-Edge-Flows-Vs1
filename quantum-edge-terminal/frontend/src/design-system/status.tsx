'use client';

import * as React from 'react';
import type { IconName } from './icons';
import { Icon } from './controls';
import { cx, stateMeta, type AnyState, type Tone } from './util';

// ── Badge ───────────────────────────────────────────────────────────────────────────────
export interface BadgeProps {
  /** Meaning, not decoration: ok/danger/warning are states, bull/bear are direction, accent is info or in-progress. */
  tone?: Tone;
  /** soft (tinted, default) · outline · solid (loudest; not available for neutral). */
  variant?: 'soft' | 'outline' | 'solid';
  icon?: IconName;
  /** A decision or lifecycle code; sets tone, icon and label from the shared vocabulary. */
  state?: AnyState;
  children?: React.ReactNode;
  title?: string;
  className?: string;
}

export function Badge({ tone, variant = 'soft', icon, state, children, title, className }: BadgeProps) {
  const meta = state ? stateMeta(state) : undefined;
  const t: Tone = tone ?? meta?.tone ?? 'neutral';
  const v = t === 'neutral' && variant === 'solid' ? 'outline' : variant;
  const ic = icon ?? meta?.icon;
  return (
    <span title={title} className={cx('qe-badge', 'qe-badge-' + t, 'qe-badge-' + v, 'qe-label', className)}>
      {ic ? <Icon name={ic} size="sm" /> : null}
      <span>{children ?? meta?.label}</span>
    </span>
  );
}

// ── Direction ───────────────────────────────────────────────────────────────────────────
export interface DirectionProps {
  side: 'long' | 'short' | 'buy' | 'sell' | 'flat';
  /** sm: 12px label (rows) · md: 14px (ticket headers). */
  size?: 'sm' | 'md';
  className?: string;
}

export function Direction({ side, size = 'sm', className }: DirectionProps) {
  const up = side === 'long' || side === 'buy';
  const flat = side === 'flat';
  return (
    <span className={cx('qe-direction', flat ? 'is-flat' : up ? 'is-bull' : 'is-bear', size === 'md' ? 'qe-control-sm' : 'qe-label', className)}>
      <Icon name={flat ? 'minus' : up ? 'trending-up' : 'trending-down'} size="sm" />
      <span>{side.toUpperCase()}</span>
    </span>
  );
}

// ── FeedStatus ──────────────────────────────────────────────────────────────────────────
export type FeedState = 'live' | 'delayed' | 'demo' | 'stale' | 'disconnected';

export interface FeedStatusProps {
  state: FeedState;
  /** Provider, e.g. "Databento". */
  source?: string;
  /** Preformatted age of the newest tick, e.g. "0.4s" or "42s". */
  age?: string;
  /** Extra qualifier, e.g. "15 min" for delayed data. */
  detail?: string;
  className?: string;
}

const FEED: Record<FeedState, { label: string; tone: 'ok' | 'warning' | 'danger' }> = {
  live: { label: 'LIVE', tone: 'ok' },
  delayed: { label: 'DELAYED', tone: 'warning' },
  demo: { label: 'DEMO DATA', tone: 'warning' },
  stale: { label: 'STALE', tone: 'danger' },
  disconnected: { label: 'DISCONNECTED', tone: 'danger' },
};

export function FeedStatus({ state, source, age, detail, className }: FeedStatusProps) {
  const f = FEED[state];
  const parts = [detail, source, age].filter(Boolean);
  return (
    <span role="status" className={cx('qe-feed', 'qe-feed-' + f.tone, state === 'live' && 'is-live', 'qe-control-sm', className)}>
      <span className="qe-feed-dot" aria-hidden="true" />
      <span className="qe-feed-label">{f.label}</span>
      {parts.length ? <span className="qe-feed-meta">{parts.join(' · ')}</span> : null}
    </span>
  );
}

// ── PanelState ──────────────────────────────────────────────────────────────────────────
export interface PanelStateProps {
  /** loading · empty (fetched, nothing there) · error (fetch failed — never shown as empty) · stale (data too old to act on). */
  kind: 'loading' | 'empty' | 'error' | 'stale';
  /** One short line in the terminal voice, e.g. "No active signals". */
  title: string;
  /** Optional sentence of detail. */
  children?: React.ReactNode;
  /** Optional action, usually a small Button ("Retry"). */
  action?: React.ReactNode;
  className?: string;
}

const PANEL_ICON: Record<PanelStateProps['kind'], IconName | undefined> = {
  loading: undefined, empty: undefined, error: 'alert-circle', stale: 'clock',
};

export function PanelState({ kind, title, children, action, className }: PanelStateProps) {
  const ic = PANEL_ICON[kind];
  return (
    <div role={kind === 'error' ? 'alert' : 'status'} aria-busy={kind === 'loading' || undefined} className={cx('qe-state', 'qe-state-' + kind, className)}>
      <div className="qe-state-title qe-control-sm">
        {ic ? <Icon name={ic} size="sm" /> : null}
        <span>{title}</span>
      </div>
      {children ? <p className="qe-state-detail qe-body-sm">{children}</p> : null}
      {action ? <div className="qe-state-action">{action}</div> : null}
    </div>
  );
}

// ── TerminalHeader ──────────────────────────────────────────────────────────────────────
export interface TerminalHeaderProps {
  /** The wordmark text; rendered uppercase. */
  product?: string;
  /** Execution environment, always visible: paper · live (real capital) · demo (sample data). */
  mode?: 'paper' | 'live' | 'demo';
  /** Right-hand slot: FeedStatus, IconButtons. */
  children?: React.ReactNode;
  className?: string;
}

const MODE: Record<NonNullable<TerminalHeaderProps['mode']>, { label: string; tone: Tone }> = {
  paper: { label: 'PAPER', tone: 'accent' },
  live: { label: 'LIVE', tone: 'danger' },
  demo: { label: 'DEMO', tone: 'warning' },
};

export function TerminalHeader({ product = 'Quantum Edge Terminal', mode, children, className }: TerminalHeaderProps) {
  return (
    <header className={cx('qe-header', className)}>
      <div className="qe-header-brand">
        <Icon name="trending-up" size="lg" className="qe-header-mark" />
        <h1 className="qe-header-wordmark qe-wordmark">{product}</h1>
        {mode ? <Badge tone={MODE[mode].tone} variant={mode === 'live' ? 'solid' : 'soft'}>{MODE[mode].label}</Badge> : null}
      </div>
      {children ? <div className="qe-header-actions">{children}</div> : null}
    </header>
  );
}

// ── Panel ───────────────────────────────────────────────────────────────────────────────
export interface PanelProps {
  /** Short noun phrase; rendered uppercase in `accent`. */
  title: string;
  /** Status beside the title, e.g. a compact FeedStatus or "5s refresh". */
  meta?: React.ReactNode;
  /** Right-aligned controls, e.g. IconButtons. */
  actions?: React.ReactNode;
  /** Caps the body at `list-max` (384px) and scrolls it; the region becomes keyboard-focusable. */
  scroll?: boolean;
  children?: React.ReactNode;
  className?: string;
}

export function Panel({ title, meta, actions, scroll, children, className }: PanelProps) {
  const id = React.useId();
  return (
    <section aria-labelledby={id} className={cx('qe-panel', className)}>
      <div className="qe-panel-head">
        <h2 id={id} className="qe-panel-heading qe-panel-title">{title}</h2>
        {meta ? <div className="qe-panel-meta">{meta}</div> : null}
        {actions ? <div className="qe-panel-actions">{actions}</div> : null}
      </div>
      <div className={cx('qe-panel-body', scroll && 'is-scroll')} tabIndex={scroll ? 0 : undefined} aria-labelledby={scroll ? id : undefined} role={scroll ? 'region' : undefined}>
        {children}
      </div>
    </section>
  );
}
