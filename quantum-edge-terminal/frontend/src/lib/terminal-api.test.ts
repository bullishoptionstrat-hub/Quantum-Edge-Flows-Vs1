import { describe, expect, it } from 'vitest';
import { parseAlerts, parseCandles, parseSignals, toEpochMs, toNumber } from './terminal-api';

describe('toNumber', () => {
  it('reads numbers and the numeric strings node-postgres returns for DECIMAL and BIGINT', () => {
    expect(toNumber('5230.25000000')).toBe(5230.25);
    expect(toNumber(42)).toBe(42);
    expect(toNumber('')).toBeUndefined();
    expect(toNumber(null)).toBeUndefined();
    expect(toNumber('n/a')).toBeUndefined();
  });
});

describe('toEpochMs', () => {
  it('reads epoch seconds, epoch milliseconds and ISO dates', () => {
    expect(toEpochMs(1_758_720_000)).toBe(1_758_720_000_000);
    expect(toEpochMs('1758720000000')).toBe(1_758_720_000_000);
    expect(toEpochMs('2026-09-25T13:42:00.000Z')).toBe(Date.UTC(2026, 8, 25, 13, 42));
    expect(toEpochMs('not a date')).toBeUndefined();
  });
});

describe('parseSignals', () => {
  it('maps BUY and SELL to long and short and parses string decimals', () => {
    const out = parseSignals({
      data: [
        { id: 7, signal_type: 'BUY', symbol: 'ES', entry_price: '5230.00000000', stop_loss: '5210.00000000', take_profit: '5280.00000000', status: 'ACTIVE', created_at: '2026-09-25T13:42:00.000Z' },
        { id: 8, signal_type: 'SELL', symbol: 'NQ', entry_price: '18460', stop_loss: null, take_profit: null, status: 'PENDING' },
      ],
    });
    expect(out?.skipped).toBe(0);
    expect(out?.signals[0]).toEqual({ id: '7', symbol: 'ES', side: 'long', entry: 5230, stop: 5210, target: 5280, status: 'ACTIVE', createdAt: Date.UTC(2026, 8, 25, 13, 42) });
    expect(out?.signals[1]).toMatchObject({ side: 'short', stop: undefined, target: undefined, status: 'PENDING' });
  });

  it('counts rows it cannot render instead of dropping them silently', () => {
    const out = parseSignals({ data: [{ id: 1, signal_type: 'HEDGE', symbol: 'ES', entry_price: '1' }, { id: 2, signal_type: 'BUY', symbol: 'ES' }] });
    expect(out).toEqual({ signals: [], skipped: 2 });
  });

  it('keeps string and numeric ids and falls back when the id is missing or not a scalar', () => {
    const row = { signal_type: 'BUY', symbol: 'ES', entry_price: '1' };
    const ids = parseSignals({ data: [{ ...row, id: 'a1b2' }, { ...row, id: 42 }, { ...row }, { ...row, id: { raw: 1 } }] })?.signals.map((s) => s.id);
    expect(ids).toEqual(['a1b2', '42', 'ES-2', 'ES-3']);
  });

  it('keeps an unrecognized status code verbatim', () => {
    expect(parseSignals({ data: [{ id: 3, signal_type: 'BUY', symbol: 'GC', entry_price: '2345.1', status: 'archived' }] })?.signals[0].status).toBe('ARCHIVED');
  });

  it('rejects an error payload rather than reading it as an empty list', () => {
    expect(parseSignals({ error: 'Failed to fetch signals' })).toBeNull();
    expect(parseSignals(null)).toBeNull();
  });
});

describe('parseAlerts', () => {
  it('maps severity, category, time and read state', () => {
    const out = parseAlerts({
      data: [
        { id: 1, alert_type: 'trade', severity: 'CRITICAL', message: 'Stop hit', sent_at: '2026-09-25T14:05:00.000Z', read_at: null },
        { id: 2, alert_type: 'MACRO', severity: 'low', message: 'CPI at 08:30', sent_at: '2026-09-25T12:00:00.000Z', read_at: '2026-09-25T12:01:00.000Z' },
      ],
    });
    expect(out).toEqual([
      { id: '1', severity: 'critical', type: 'TRADE', message: 'Stop hit', sentAt: Date.UTC(2026, 8, 25, 14, 5), unread: true },
      { id: '2', severity: 'low', type: 'MACRO', message: 'CPI at 08:30', sentAt: Date.UTC(2026, 8, 25, 12, 0), unread: false },
    ]);
  });

  it('surfaces an unrecognized severity as high', () => {
    expect(parseAlerts({ data: [{ id: 3, severity: 'SEVERE', message: 'x' }] })?.[0].severity).toBe('high');
  });
});

describe('parseCandles', () => {
  it('sorts the newest-first endpoint oldest-first and drops unusable rows', () => {
    const out = parseCandles({
      data: [
        { timestamp: '1758722400000', close: '5231.25' },
        { timestamp: '1758718800000', close: '5226.50' },
        { timestamp: null, close: '1' },
        { timestamp: '1758715200000', close: 'n/a' },
      ],
    });
    expect(out).toEqual([
      { time: 1758718800000, close: 5226.5 },
      { time: 1758722400000, close: 5231.25 },
    ]);
  });
});
