// Every clock time in the terminal is New York time and says so ("09:42 ET"), whatever the viewer's zone.
const ET = 'America/New_York';
const clock = new Intl.DateTimeFormat('en-US', { timeZone: ET, hour: '2-digit', minute: '2-digit', hourCycle: 'h23' });
const day = new Intl.DateTimeFormat('en-US', { timeZone: ET, month: 'short', day: 'numeric' });

/** "09:42" in New York time. */
export function formatEtClock(ms: number): string {
  return clock.format(ms);
}

/** "09:42 ET". */
export function formatEtTime(ms: number): string {
  return `${clock.format(ms)} ET`;
}

export const TIMEFRAME_MS: Readonly<Record<string, number>> = {
  '1m': 60_000,
  '5m': 300_000,
  '15m': 900_000,
  '1h': 3_600_000,
  '4h': 14_400_000,
  '1D': 86_400_000,
};

/** Axis label for a bar: the date for daily bars, date and time for 1h and 4h bars (50 of them span days), the clock time below that. */
export function formatBarLabel(ms: number, timeframe: string): string {
  if (timeframe === '1D') {
    return day.format(ms);
  }
  if (timeframe === '4h' || timeframe === '1h') {
    return `${day.format(ms)} ${clock.format(ms)}`;
  }
  return clock.format(ms);
}

/** Data is stale once its newest bar is more than two bars of its timeframe old. */
export function isStale(ageMs: number, timeframe: string): boolean {
  return ageMs > 2 * (TIMEFRAME_MS[timeframe] ?? TIMEFRAME_MS['1h']);
}

/** Compact age: "42s", "18m", "3h", "2d". */
export function formatAge(ms: number): string {
  const s = Math.max(0, Math.round(ms / 1000));
  if (s < 60) {
    return `${s}s`;
  }
  const m = Math.floor(s / 60);
  if (m < 60) {
    return `${m}m`;
  }
  const h = Math.floor(m / 60);
  if (h < 48) {
    return `${h}h`;
  }
  return `${Math.floor(h / 24)}d`;
}
