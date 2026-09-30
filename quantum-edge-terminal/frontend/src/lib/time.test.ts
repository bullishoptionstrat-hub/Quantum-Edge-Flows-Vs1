import { describe, expect, it } from 'vitest';
import { formatAge, formatBarLabel, formatEtTime, isStale } from './time';

describe('New York time', () => {
  it('formats in EDT and EST whatever the machine zone', () => {
    expect(formatEtTime(Date.UTC(2026, 8, 25, 13, 42))).toBe('09:42 ET'); // EDT, UTC−4
    expect(formatEtTime(Date.UTC(2026, 0, 15, 14, 30))).toBe('09:30 ET'); // EST, UTC−5
    expect(formatEtTime(Date.UTC(2026, 8, 26, 4, 0))).toBe('00:00 ET'); // midnight reads 00, not 24
  });

  it('labels bars by timeframe', () => {
    const t = Date.UTC(2026, 8, 25, 17, 0); // 13:00 ET
    expect(formatBarLabel(t, '5m')).toBe('13:00');
    expect(formatBarLabel(t, '1h')).toBe('Sep 25 13:00');
    expect(formatBarLabel(t, '4h')).toBe('Sep 25 13:00');
    expect(formatBarLabel(t, '1D')).toBe('Sep 25');
  });
});

describe('staleness', () => {
  it('flags data whose newest bar is more than two bars old', () => {
    expect(isStale(2 * 60_000, '1m')).toBe(false);
    expect(isStale(2 * 60_000 + 1, '1m')).toBe(true);
    expect(isStale(3 * 3_600_000, '1h')).toBe(true);
    expect(isStale(3 * 3_600_000, '4h')).toBe(false);
  });

  it('formats ages compactly', () => {
    expect(formatAge(42_000)).toBe('42s');
    expect(formatAge(18 * 60_000)).toBe('18m');
    expect(formatAge(3 * 3_600_000)).toBe('3h');
    expect(formatAge(50 * 3_600_000)).toBe('2d');
    expect(formatAge(-5)).toBe('0s');
  });
});
