'use client';

import * as React from 'react';
import type { IconName } from './icons';
import { Icon } from './controls';
import { Badge, Direction } from './status';
import { cx, formatPrice, formatR, type AnyState, type DecisionState, type Side } from './util';

// ── Score pips (internal): a confluence score is a ranking, never a probability ────────────
function Score({ value, max }: { value: number; max: number }) {
  const v = Math.max(0, Math.min(max, Math.round(value)));
  return (
    <span className="qe-score qe-label" title="Confluence score — ranks setups; never overrides a gate">
      <span className="qe-score-word">SCORE</span>
      <span className="qe-score-pips" aria-hidden="true">
        {Array.from({ length: max }, (_, i) => <span key={i} className={cx('qe-score-pip', i < v && 'is-on')} />)}
      </span>
      <span>{v}/{max}</span>
      <span className="qe-sr-only">confluence score {v} of {max}, for ranking only</span>
    </span>
  );
}

// ── SignalCard ──────────────────────────────────────────────────────────────────────────
export interface SignalCardProps {
  symbol: string;
  side: Side;
  /** Decision or lifecycle code (drives the badge). */
  state: AnyState;
  /** Playbook / model name, e.g. "Sweep & Reclaim". */
  model?: string;
  /** Session or killzone, e.g. "NY AM". */
  session?: string;
  /** Preformatted time with its zone, e.g. "09:42 ET". */
  time?: string;
  entry: number;
  /** Omit when the signal has no stop: the card shows SL NONE in `danger` and no R. */
  stop?: number;
  /** Target prices, nearest first. The card shows TP1 and its R multiple. */
  targets?: number[];
  /** Price precision, e.g. 0.25 for ES. */
  tickSize?: number;
  /** Confluence score for ranking (shown as pips, e.g. 4/5). */
  score?: number;
  scoreMax?: number;
  /** The first blocker code when state is BLOCKED, e.g. "NO_SMT". */
  blocker?: string;
  selected?: boolean;
  /** Makes the whole card a button. */
  onSelect?: () => void;
  className?: string;
}

export function SignalCard({ symbol, side, state, model, session, time, entry, stop, targets = [], tickSize = 0.01, score, scoreMax = 5, blocker, selected, onSelect, className }: SignalCardProps) {
  const tp1 = targets[0];
  const risk = stop !== undefined ? Math.abs(entry - stop) : 0;
  const r = tp1 !== undefined && risk > 0 ? Math.abs(tp1 - entry) / risk : undefined;
  const context = [model, session, time].filter(Boolean).join(' · ');
  const body = (
    <>
      <div className="qe-signal-top">
        <span className="qe-signal-symbol qe-control-sm">{symbol}</span>
        <Direction side={side} />
        <Badge state={state} className="qe-signal-state" />
      </div>
      {context ? <div className="qe-signal-context qe-data">{context}</div> : null}
      <dl className="qe-signal-levels qe-data">
        <div><dt className="qe-key-stop">SL</dt>{stop !== undefined ? <dd>{formatPrice(stop, tickSize)}</dd> : <dd className="qe-signal-missing">NONE</dd>}</div>
        <div><dt>ENTRY</dt><dd>{formatPrice(entry, tickSize)}</dd></div>
        {tp1 !== undefined ? <div><dt className="qe-key-target">TP1</dt><dd>{formatPrice(tp1, tickSize)}</dd></div> : null}
        {r !== undefined ? <div><dt className="qe-sr-only">Reward to TP1</dt><dd className="qe-signal-r">{formatR(r)}</dd></div> : null}
      </dl>
      {score !== undefined || blocker ? (
        <div className="qe-signal-foot">
          {score !== undefined ? <Score value={score} max={scoreMax} /> : null}
          {blocker ? <span className="qe-signal-blocker qe-label">{blocker}</span> : null}
        </div>
      ) : null}
    </>
  );
  const cls = cx('qe-signal', selected && 'is-selected', onSelect && 'is-interactive', className);
  return onSelect
    ? <button type="button" aria-pressed={selected} onClick={onSelect} className={cls}>{body}</button>
    : <article className={cls}>{body}</article>;
}

// ── AlertItem ───────────────────────────────────────────────────────────────────────────
export type Severity = 'critical' | 'high' | 'medium' | 'low';

export interface AlertItemProps {
  severity: Severity;
  /** Alert category code from the backend: TRADE, STRUCTURE, MACRO, VOLUME. */
  type: string;
  /** One sentence, specific: what happened, where, at what level. */
  message: React.ReactNode;
  /** Preformatted time with its zone, e.g. "09:42 ET". */
  time?: string;
  unread?: boolean;
  className?: string;
}

const SEVERITY: Record<Severity, { word: string; icon: IconName }> = {
  critical: { word: 'CRITICAL', icon: 'alert-circle' },
  high: { word: 'HIGH', icon: 'alert-triangle' },
  medium: { word: 'MEDIUM', icon: 'info' },
  low: { word: 'LOW', icon: 'info' },
};

export function AlertItem({ severity, type, message, time, unread, className }: AlertItemProps) {
  const s = SEVERITY[severity];
  return (
    <article className={cx('qe-alert', 'qe-alert-' + severity, unread && 'is-unread', className)}>
      <div className="qe-alert-top qe-label">
        <Icon name={s.icon} size="sm" className="qe-alert-icon" />
        <span className="qe-alert-severity">{s.word}</span>
        <span className="qe-alert-type">[{type}]</span>
        {time ? <span className="qe-alert-time">{time}</span> : null}
        {unread ? <span className="qe-alert-unread"><span className="qe-sr-only">unread</span></span> : null}
      </div>
      <p className="qe-alert-message qe-body-sm">{message}</p>
    </article>
  );
}

// ── GateChecklist ───────────────────────────────────────────────────────────────────────
export type GateStatus = 'pass' | 'fail' | 'unavailable' | 'pending';

export interface Gate {
  id: string;
  /** What the gate checks, e.g. "Paired SMT (ES/NQ)". */
  label: string;
  status: GateStatus;
  /** The observed evidence behind the result, with levels and times. */
  evidence?: string;
  /** Blocker code shown when the gate fails or is unavailable, e.g. "NO_SMT". */
  code?: string;
}

export interface GateChecklistProps {
  gates: Gate[];
  /** The engine's verdict. A verdict of APPROVED_TRADE with any non-passing gate is flagged, never shown as clean. */
  decision?: DecisionState;
  /** Confluence score for ranking only. */
  score?: { value: number; max: number };
  /** When the gates were evaluated, e.g. "09:42:05 ET · rules v4.0.1". */
  asOf?: string;
  className?: string;
}

const GATE: Record<GateStatus, { word: string; icon: IconName }> = {
  pass: { word: 'PASS', icon: 'check' },
  fail: { word: 'FAIL', icon: 'x' },
  unavailable: { word: 'N/A', icon: 'circle-dashed' },
  pending: { word: 'PENDING', icon: 'hourglass' },
};

export function GateChecklist({ gates, decision, score, asOf, className }: GateChecklistProps) {
  const blocking = gates.filter((g) => g.status === 'fail' || g.status === 'unavailable');
  const contradiction = decision === 'APPROVED_TRADE' && gates.some((g) => g.status !== 'pass');
  return (
    <div className={cx('qe-gates', className)}>
      <ol className="qe-gates-list">
        {gates.map((g) => (
          <li key={g.id} className={cx('qe-gate', 'is-' + g.status)}>
            <span className="qe-gate-status qe-label"><Icon name={GATE[g.status].icon} size="sm" />{GATE[g.status].word}</span>
            <span className="qe-gate-label qe-control-sm">{g.label}</span>
            {g.code && g.status !== 'pass' ? <span className="qe-gate-code qe-label">{g.code}</span> : null}
            {g.evidence ? <p className="qe-gate-evidence qe-body-sm">{g.evidence}</p> : null}
          </li>
        ))}
      </ol>
      {decision || score || asOf || blocking.length ? (
        <div className="qe-gates-summary">
          {decision ? <Badge state={decision} /> : null}
          {score ? <Score value={score.value} max={score.max} /> : null}
          {blocking.length ? (
            <span className="qe-gates-blockers qe-data">Blocked by {blocking.map((g) => g.code ?? g.label).join(', ')}</span>
          ) : null}
          {asOf ? <span className="qe-gates-asof qe-data">{asOf}</span> : null}
        </div>
      ) : null}
      {contradiction ? (
        <p role="alert" className="qe-gates-contradiction qe-body-sm">
          <Icon name="alert-circle" size="sm" />
          Gate results contradict APPROVED_TRADE. Treat as BLOCKED until the engine re-evaluates.
        </p>
      ) : null}
    </div>
  );
}
