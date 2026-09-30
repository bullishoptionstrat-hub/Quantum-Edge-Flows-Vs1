// Typed access to the terminal backend (backend/src/api). Payloads are validated here, not trusted:
// node-postgres returns DECIMAL and BIGINT columns as strings, and a failed request returns { error }.
import type { AnyState, Severity, Side, SignalStatus } from '@/design-system';

export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

export interface Signal {
  id: string;
  symbol: string;
  side: Side;
  entry: number;
  /** Absent when the backend stored no stop_loss. */
  stop?: number;
  target?: number;
  status: AnyState;
  createdAt?: number;
}

export interface SignalList {
  signals: Signal[];
  /** Rows dropped because their signal_type is neither BUY nor SELL, or a required field is missing. */
  skipped: number;
}

export interface Alert {
  id: string;
  severity: Severity;
  /** TRADE, STRUCTURE, MACRO or VOLUME. */
  type: string;
  message: string;
  sentAt?: number;
  unread: boolean;
}

export interface Candle {
  /** Milliseconds since the epoch. */
  time: number;
  close: number;
}

type Row = Record<string, unknown>;

function dataRows(json: unknown): Row[] | null {
  if (typeof json !== 'object' || json === null) {
    return null;
  }
  const data = (json as { data?: unknown }).data;
  if (!Array.isArray(data)) {
    return null;
  }
  return data.filter((r): r is Row => typeof r === 'object' && r !== null);
}

/** A row's id as a string (UUIDs and BIGINTs arrive as strings, SERIALs as numbers), else the fallback. */
function rowId(value: unknown, fallback: string): string {
  if (typeof value === 'string') {
    return value;
  }
  return typeof value === 'number' ? String(value) : fallback;
}

/** A finite number from a number or a numeric string, else undefined. */
export function toNumber(value: unknown): number | undefined {
  const n = typeof value === 'number' ? value : typeof value === 'string' && value.trim() !== '' ? Number(value) : NaN;
  return Number.isFinite(n) ? n : undefined;
}

/**
 * Epoch milliseconds from a number, a numeric string or an ISO date. The candles table stores a BIGINT whose
 * unit no writer documents, so values below 1e12 are read as seconds and larger ones as milliseconds.
 */
export function toEpochMs(value: unknown): number | undefined {
  const n = toNumber(value);
  if (n !== undefined) {
    return n < 1e12 ? n * 1000 : n;
  }
  if (typeof value === 'string') {
    const parsed = Date.parse(value);
    return Number.isNaN(parsed) ? undefined : parsed;
  }
  return undefined;
}

const LIFECYCLE: ReadonlySet<string> = new Set<SignalStatus>([
  'RECEIVED', 'PENDING', 'ACTIVE', 'VALIDATING', 'VALIDATED', 'BLOCKED', 'EXPIRED',
  'APPROVAL_REQUIRED', 'APPROVED', 'EXECUTED', 'CLOSED', 'ERROR',
]);

function toState(value: unknown): AnyState {
  const code = typeof value === 'string' ? value.trim().toUpperCase() : '';
  if (LIFECYCLE.has(code)) {
    return code as SignalStatus;
  }
  // An unknown code is still the backend's truth: Badge renders unrecognized codes verbatim in the neutral tone.
  return (code || 'PENDING') as AnyState;
}

export function parseSignals(json: unknown): SignalList | null {
  const rows = dataRows(json);
  if (!rows) {
    return null;
  }
  const signals: Signal[] = [];
  let skipped = 0;
  for (const r of rows) {
    const type = typeof r.signal_type === 'string' ? r.signal_type.toUpperCase() : '';
    const side: Side | undefined = type === 'BUY' ? 'long' : type === 'SELL' ? 'short' : undefined;
    const entry = toNumber(r.entry_price);
    const symbol = typeof r.symbol === 'string' ? r.symbol : '';
    if (!side || entry === undefined || !symbol) {
      skipped += 1;
      continue;
    }
    signals.push({
      id: rowId(r.id, `${symbol}-${signals.length}`),
      symbol,
      side,
      entry,
      stop: toNumber(r.stop_loss),
      target: toNumber(r.take_profit),
      status: toState(r.status),
      createdAt: toEpochMs(r.created_at),
    });
  }
  return { signals, skipped };
}

const SEVERITIES: Record<string, Severity> = { CRITICAL: 'critical', HIGH: 'high', MEDIUM: 'medium', LOW: 'low' };

export function parseAlerts(json: unknown): Alert[] | null {
  const rows = dataRows(json);
  if (!rows) {
    return null;
  }
  return rows.map((r, i) => ({
    id: rowId(r.id, String(i)),
    // An unrecognized severity is a contract mismatch; surface it as HIGH rather than bury it as LOW.
    severity: SEVERITIES[typeof r.severity === 'string' ? r.severity.toUpperCase() : ''] ?? 'high',
    type: typeof r.alert_type === 'string' && r.alert_type ? r.alert_type.toUpperCase() : 'UNKNOWN',
    message: typeof r.message === 'string' ? r.message : '',
    sentAt: toEpochMs(r.sent_at),
    unread: r.read_at === null || r.read_at === undefined,
  }));
}

/** Candles oldest first (the endpoint returns newest first); rows without a time or close are dropped. */
export function parseCandles(json: unknown): Candle[] | null {
  const rows = dataRows(json);
  if (!rows) {
    return null;
  }
  const candles: Candle[] = [];
  for (const r of rows) {
    const time = toEpochMs(r.timestamp);
    const close = toNumber(r.close);
    if (time !== undefined && close !== undefined) {
      candles.push({ time, close });
    }
  }
  candles.sort((a, b) => a.time - b.time);
  return candles;
}
