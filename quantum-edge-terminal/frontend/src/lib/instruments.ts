// Price precision for display only (decimal places follow the tick). Position sizing must use a verified
// contract spec — tick size AND tick value — never this table.
const DISPLAY_TICK: Readonly<Record<string, number>> = {
  ES: 0.25,
  MES: 0.25,
  NQ: 0.25,
  MNQ: 0.25,
  GC: 0.1,
  MGC: 0.1,
  SI: 0.005,
  SPY: 0.01,
  QQQ: 0.01,
};

export function displayTickSize(symbol: string): number {
  return DISPLAY_TICK[symbol.toUpperCase()] ?? 0.01;
}
