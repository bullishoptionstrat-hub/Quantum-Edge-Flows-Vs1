'use client';

import * as React from 'react';
import { Button, Icon } from './controls';
import { Badge } from './status';
import { cx, formatUsd } from './util';

// ── RiskMeter ───────────────────────────────────────────────────────────────────────────
export interface RiskMeterProps {
  /** e.g. "Daily loss". */
  label?: string;
  /** Realized loss so far today, as a positive USD amount. */
  used: number;
  /** The configured daily loss cap, USD (the stricter of personal and firm limits). */
  limit: number;
  /** Stop-outs this session and the lockout count, e.g. 1 of 2. */
  stopOuts?: number;
  maxStopOuts?: number;
  /** Daily lock active: trading disabled by the backend. */
  locked?: boolean;
  /** When the lock lifts, e.g. "Trading resumes 09:30 ET tomorrow." */
  lockNote?: string;
  className?: string;
}

export function RiskMeter({ label = 'Daily loss', used, limit, stopOuts, maxStopOuts, locked, lockNote, className }: RiskMeterProps) {
  const pct = limit > 0 ? Math.min(Math.max(used / limit, 0), 1) : 1;
  const level = locked || pct >= 0.8 ? 'danger' : pct >= 0.5 ? 'warning' : 'accent';
  const left = Math.max(limit - used, 0);
  const textId = React.useId();
  return (
    <div className={cx('qe-risk', 'is-' + level, className)}>
      <div className="qe-risk-top">
        <span className="qe-risk-label qe-label" id={textId}>{label}</span>
        <span className="qe-risk-value qe-control-sm">{formatUsd(used, true)} <span className="qe-risk-of">of {formatUsd(limit, true)}</span></span>
      </div>
      <div
        className="qe-risk-track" role="meter" aria-labelledby={textId}
        aria-valuemin={0} aria-valuemax={limit} aria-valuenow={Math.min(used, limit)}
        aria-valuetext={`${formatUsd(used, true)} of ${formatUsd(limit, true)} used`}
      >
        <span className="qe-risk-fill" style={{ width: `${pct * 100}%` }} />
      </div>
      <div className="qe-risk-foot qe-data">
        <span>{Math.round(pct * 100)}% used · {formatUsd(left, true)} left</span>
        {maxStopOuts ? (
          <span className="qe-risk-stops">
            Stop-outs {stopOuts ?? 0}/{maxStopOuts}
            <span className="qe-risk-pips" aria-hidden="true">
              {Array.from({ length: maxStopOuts }, (_, i) => <span key={i} className={cx('qe-risk-pip', i < (stopOuts ?? 0) && 'is-on')} />)}
            </span>
          </span>
        ) : null}
      </div>
      {locked ? (
        <div className="qe-risk-lock" role="status">
          <Badge tone="danger" icon="lock">DAILY_LOCK_ACTIVE</Badge>
          {lockNote ? <span className="qe-body-sm">{lockNote}</span> : null}
        </div>
      ) : null}
    </div>
  );
}

// ── ApprovalBar ─────────────────────────────────────────────────────────────────────────
export interface ApprovalBarProps {
  onApprove?: () => void;
  onHold?: () => void;
  onReject?: () => void;
  /** Why approval is unavailable right now (stale data, a failed gate, a lock). Disables APPROVE only. */
  disabledReason?: string;
  /** Preformatted time left before the setup expires, e.g. "02:14". */
  expiresIn?: string;
  className?: string;
}

export function ApprovalBar({ onApprove, onHold, onReject, disabledReason, expiresIn, className }: ApprovalBarProps) {
  return (
    <div className={cx('qe-approval', className)}>
      <div className="qe-approval-actions">
        <Button variant="primary" icon="check" onClick={onApprove} disabledReason={disabledReason}>Approve</Button>
        <Button icon="pause" onClick={onHold}>Hold</Button>
        <Button icon="x" onClick={onReject}>Reject</Button>
        {expiresIn ? <span className="qe-approval-expiry qe-data"><Icon name="clock" size="sm" />Expires in {expiresIn}</span> : null}
      </div>
      {disabledReason ? (
        <p className="qe-approval-reason qe-body-sm" role="status"><Icon name="alert-triangle" size="sm" />{disabledReason}</p>
      ) : null}
      <p className="qe-approval-note qe-body-sm">Approve sends the order to pre-trade risk checks. It is not a fill.</p>
    </div>
  );
}

// ── KillSwitch ──────────────────────────────────────────────────────────────────────────
export interface KillSwitchProps {
  /** Mirrors the backend's halt state — never local UI state alone. */
  engaged: boolean;
  /** Called with the requested state. Confirm before disengaging; engaging is one press. */
  onToggle?: (next: boolean) => void;
  /** One line of consequence or audit, e.g. "Engaged 10:42 ET by A. Morhan · 3 working orders cancelled". */
  detail?: string;
  className?: string;
}

export function KillSwitch({ engaged, onToggle, detail, className }: KillSwitchProps) {
  return (
    <button
      type="button" role="switch" aria-checked={engaged}
      onClick={() => onToggle?.(!engaged)}
      className={cx('qe-kill', engaged && 'is-engaged', className)}
    >
      <Icon name={engaged ? 'shield-off' : 'power'} size="md" />
      <span className="qe-kill-text">
        <span className="qe-kill-title qe-control-sm">{engaged ? 'Trading halted' : 'Kill switch'}</span>
        <span className="qe-kill-detail qe-data">{detail ?? (engaged ? 'All order submission is stopped.' : 'Armed. Press to halt all order submission.')}</span>
      </span>
    </button>
  );
}
