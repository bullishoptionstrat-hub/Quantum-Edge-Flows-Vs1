// Shared formatting and vocabulary. Prices are instrument points — never prefixed with "$".
// Money (risk, fees, P&L) is always USD with a "$". Negative numbers use U+2212 MINUS SIGN.
import type { IconName } from './icons';

export type Side = 'long' | 'short';
export type Tone = 'neutral' | 'accent' | 'bull' | 'bear' | 'ok' | 'danger' | 'warning';

/** Analytical decision states — the gate engine's verdict for a setup. */
export type DecisionState = 'NEUTRAL' | 'WAIT_FOR_TRIGGER' | 'BLOCKED' | 'NO_TRADE' | 'APPROVED_TRADE';
/** Storage / execution lifecycle of a signal record. Distinct from DecisionState; BLOCKED means the same in both. */
export type SignalStatus =
  | 'RECEIVED' | 'PENDING' | 'ACTIVE' | 'VALIDATING' | 'VALIDATED' | 'BLOCKED' | 'EXPIRED'
  | 'APPROVAL_REQUIRED' | 'APPROVED' | 'EXECUTED' | 'CLOSED' | 'ERROR';
export type AnyState = DecisionState | SignalStatus;

export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(' ');
}

const MINUS = '−';

/** Decimal places implied by a tick size: 0.25 → 2, 0.1 → 1, 0.005 → 3, 0.01 → 2. */
export function decimalsFor(tickSize: number): number {
  const s = String(tickSize);
  const i = s.indexOf('.');
  return i < 0 ? 0 : s.length - i - 1;
}

/** A price in instrument points at the tick's precision. No currency sign. */
export function formatPrice(value: number, tickSize = 0.01): string {
  const s = Math.abs(value).toFixed(decimalsFor(tickSize));
  return value < 0 ? MINUS + s : s;
}

/** A signed point distance, e.g. "+50.00" / "−20.00". */
export function formatPoints(value: number, tickSize = 0.01): string {
  const s = Math.abs(value).toFixed(decimalsFor(tickSize));
  return (value > 0 ? '+' : value < 0 ? MINUS : '') + s;
}

const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2 });
const usd0 = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 });

/** USD money, e.g. "$1,012.50"; whole: true drops cents. */
export function formatUsd(value: number, whole = false): string {
  const s = (whole ? usd0 : usd).format(Math.abs(value));
  return value < 0 ? MINUS + s : s;
}

/** An R multiple, e.g. "2.50R". */
export function formatR(r: number): string {
  return (r < 0 ? MINUS : '') + Math.abs(r).toFixed(2) + 'R';
}

export interface StateMeta { label: string; tone: Tone; icon?: IconName }

const STATE_META: Record<AnyState, StateMeta> = {
  NEUTRAL: { label: 'NEUTRAL', tone: 'neutral', icon: 'minus' },
  WAIT_FOR_TRIGGER: { label: 'WAIT_FOR_TRIGGER', tone: 'warning', icon: 'hourglass' },
  BLOCKED: { label: 'BLOCKED', tone: 'danger', icon: 'ban' },
  NO_TRADE: { label: 'NO_TRADE', tone: 'neutral', icon: 'x' },
  APPROVED_TRADE: { label: 'APPROVED_TRADE', tone: 'ok', icon: 'check' },
  RECEIVED: { label: 'RECEIVED', tone: 'accent', icon: 'activity' },
  PENDING: { label: 'PENDING', tone: 'neutral', icon: 'clock' },
  ACTIVE: { label: 'ACTIVE', tone: 'accent', icon: 'activity' },
  VALIDATING: { label: 'VALIDATING', tone: 'accent', icon: 'hourglass' },
  VALIDATED: { label: 'VALIDATED', tone: 'ok', icon: 'check' },
  EXPIRED: { label: 'EXPIRED', tone: 'neutral', icon: 'clock' },
  APPROVAL_REQUIRED: { label: 'APPROVAL_REQUIRED', tone: 'warning', icon: 'alert-triangle' },
  APPROVED: { label: 'APPROVED', tone: 'ok', icon: 'check' },
  EXECUTED: { label: 'EXECUTED', tone: 'ok', icon: 'check' },
  CLOSED: { label: 'CLOSED', tone: 'neutral', icon: 'minus' },
  ERROR: { label: 'ERROR', tone: 'danger', icon: 'alert-circle' },
};

export function stateMeta(state: AnyState): StateMeta {
  return STATE_META[state] ?? { label: state, tone: 'neutral' };
}
