// Pure trade-ticket arithmetic: stop distance, dollar risk, whole-contract size and R per target.
// No React here, so the same numbers can be tested and computed on a server.
import type { Side } from './util';

export interface TicketTarget { label?: string; price: number }

export interface TicketInput {
  side: Side;
  entry: number;
  stop: number;
  /** Nearest first: TP1, TP2, TP3. */
  targets: TicketTarget[];
  /** From a verified contract spec — ES 0.25, MES 0.25, GC 0.10, SI 0.005. */
  tickSize: number;
  /** USD per tick per contract from the same spec — ES $12.50, MES $1.25, NQ $5.00, MNQ $0.50. */
  tickValue: number;
  /** Estimated round-trip commissions + slippage per contract, USD. */
  costsPerContract?: number;
  /** Dollars this idea may lose. */
  riskBudget?: number;
  /** Minimum net R to the best target; default 2. */
  minR?: number;
}

export interface TicketRow {
  label: string;
  price: number;
  /** Signed distance in points: positive when the target is on the profitable side of entry. */
  dist: number;
  gross: number;
  net: number;
}

export interface TicketMath {
  /** Why the geometry is invalid (stop or a target on the wrong side of entry), else null. Sizing must be withheld. */
  geometryError: string | null;
  /** True when entry, stop or any target is off the tick grid. */
  offTick: boolean;
  stopPts: number;
  stopTicks: number;
  /** stopTicks × tickValue + costs, USD. */
  riskPerContract: number;
  /** floor(riskBudget ÷ riskPerContract) — never rounded up; undefined without a budget. */
  contracts?: number;
  rows: TicketRow[];
  /** The best net R across targets (−Infinity with no targets). */
  bestNet: number;
  /** True when the best target nets less than minR (REWARD_UNDER_2R at the default). */
  underMin: boolean;
}

const onTick = (price: number, tick: number) => Math.abs(price / tick - Math.round(price / tick)) < 1e-6;

export function computeTicket(input: TicketInput): TicketMath {
  const { side, entry, stop, targets, tickSize, tickValue, costsPerContract = 0, riskBudget, minR = 2 } = input;
  const long = side === 'long';
  const geometryError =
    long && !(stop < entry) ? 'Stop must be below entry for a LONG.'
    : !long && !(stop > entry) ? 'Stop must be above entry for a SHORT.'
    : targets.some((t) => (long ? t.price <= entry : t.price >= entry)) ? `Every target must be ${long ? 'above' : 'below'} entry for a ${long ? 'LONG' : 'SHORT'}.`
    : null;
  const offTick = [entry, stop, ...targets.map((t) => t.price)].some((x) => !onTick(x, tickSize));

  const stopPts = Math.abs(entry - stop);
  const stopTicks = Math.round(stopPts / tickSize);
  const riskPerContract = stopTicks * tickValue + costsPerContract;
  // The epsilon keeps an exact multiple (e.g. 2035 ÷ 1017.5) from flooring to one less through float error.
  const contracts = riskBudget !== undefined && riskPerContract > 0 ? Math.floor(riskBudget / riskPerContract + 1e-9) : undefined;

  const rows = targets.map((t, i) => {
    const dist = long ? t.price - entry : entry - t.price;
    const ticks = Math.round(dist / tickSize);
    const gross = stopPts > 0 ? dist / stopPts : 0;
    const net = riskPerContract > 0 ? (ticks * tickValue - costsPerContract) / riskPerContract : 0;
    return { label: t.label ?? `TP${i + 1}`, price: t.price, dist, gross, net };
  });
  const bestNet = rows.reduce((m, r) => Math.max(m, r.net), -Infinity);
  const underMin = !geometryError && rows.length > 0 && bestNet < minR;
  return { geometryError, offTick, stopPts, stopTicks, riskPerContract, contracts, rows, bestNet, underMin };
}
