import { describe, expect, it } from 'vitest';
import { computeTicket } from './ticket-math';

const es = { tickSize: 0.25, tickValue: 12.5 };

describe('computeTicket', () => {
  it('sizes the ES sample in whole contracts after costs', () => {
    const t = computeTicket({ side: 'long', entry: 5230, stop: 5210, targets: [{ price: 5280 }, { price: 5300 }], ...es, costsPerContract: 17.5, riskBudget: 1500 });
    expect(t.geometryError).toBeNull();
    expect(t.stopPts).toBe(20);
    expect(t.stopTicks).toBe(80);
    expect(t.riskPerContract).toBe(1017.5);
    expect(t.contracts).toBe(1);
    expect(t.rows.map((r) => r.gross)).toEqual([2.5, 3.5]);
    expect(t.rows[0].net).toBeCloseTo(2482.5 / 1017.5, 10);
    expect(t.underMin).toBe(false);
  });

  it('never rounds size up', () => {
    expect(computeTicket({ side: 'long', entry: 5230, stop: 5210, targets: [], ...es, costsPerContract: 17.5, riskBudget: 1017.49 }).contracts).toBe(0);
    expect(computeTicket({ side: 'long', entry: 5230, stop: 5210, targets: [], ...es, costsPerContract: 17.5, riskBudget: 2035 }).contracts).toBe(2);
  });

  it('does not lose a unit to float error on an exact multiple (0.3 / 0.1)', () => {
    const t = computeTicket({ side: 'long', entry: 100.1, stop: 100, targets: [], tickSize: 0.01, tickValue: 0.01, riskBudget: 0.3 });
    expect(t.stopTicks).toBe(10);
    expect(t.contracts).toBe(3);
  });

  it('returns 0 contracts and flags a best target under 2R for the NQ short', () => {
    const t = computeTicket({ side: 'short', entry: 18460, stop: 18490, targets: [{ price: 18410 }], tickSize: 0.25, tickValue: 5, costsPerContract: 7, riskBudget: 500 });
    expect(t.riskPerContract).toBe(607);
    expect(t.contracts).toBe(0);
    expect(t.rows[0].net).toBeCloseTo(993 / 607, 10);
    expect(t.underMin).toBe(true);
  });

  it('reports a stop on the wrong side of entry', () => {
    expect(computeTicket({ side: 'long', entry: 5230, stop: 5240, targets: [{ price: 5280 }], ...es }).geometryError).toBe('Stop must be below entry for a LONG.');
    expect(computeTicket({ side: 'short', entry: 5230, stop: 5220, targets: [], ...es }).geometryError).toBe('Stop must be above entry for a SHORT.');
  });

  it('gives a target on the wrong side a negative R', () => {
    const t = computeTicket({ side: 'long', entry: 5230, stop: 5210, targets: [{ price: 5220 }], ...es });
    expect(t.geometryError).toBe('Every target must be above entry for a LONG.');
    expect(t.rows[0].dist).toBe(-10);
    expect(t.rows[0].gross).toBe(-0.5);
    expect(t.rows[0].net).toBeLessThan(0);
    expect(t.underMin).toBe(false); // the geometry error is the reported problem
  });

  it('detects prices off the tick grid', () => {
    expect(computeTicket({ side: 'long', entry: 5230.1, stop: 5210, targets: [], ...es }).offTick).toBe(true);
    expect(computeTicket({ side: 'long', entry: 29.125, stop: 29.05, targets: [], tickSize: 0.005, tickValue: 25 }).offTick).toBe(false);
  });
});
