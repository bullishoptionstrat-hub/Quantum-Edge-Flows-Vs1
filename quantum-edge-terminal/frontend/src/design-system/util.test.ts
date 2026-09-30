import { describe, expect, it } from 'vitest';
import { decimalsFor, formatPoints, formatPrice, formatR, formatUsd, stateMeta, type AnyState } from './util';

describe('formatting', () => {
  it('prints prices in points at tick precision, never with $', () => {
    expect(decimalsFor(0.25)).toBe(2);
    expect(decimalsFor(0.1)).toBe(1);
    expect(decimalsFor(0.005)).toBe(3);
    expect(decimalsFor(1)).toBe(0);
    expect(formatPrice(5230, 0.25)).toBe('5230.00');
    expect(formatPrice(2345.1, 0.1)).toBe('2345.1');
    expect(formatPrice(-1.5, 0.25)).toBe('−1.50');
  });

  it('signs point distances, money and R multiples with a true minus', () => {
    expect(formatPoints(50, 0.25)).toBe('+50.00');
    expect(formatPoints(-20, 0.25)).toBe('−20.00');
    expect(formatPoints(0, 0.25)).toBe('0.00');
    expect(formatUsd(1017.5)).toBe('$1,017.50');
    expect(formatUsd(1000, true)).toBe('$1,000');
    expect(formatUsd(-12.5)).toBe('−$12.50');
    expect(formatR(2.4398)).toBe('2.44R');
    expect(formatR(-0.5)).toBe('−0.50R');
  });
});

describe('state vocabulary', () => {
  it("maps the backend's ACTIVE status and shows unknown codes verbatim", () => {
    expect(stateMeta('ACTIVE')).toEqual({ label: 'ACTIVE', tone: 'accent', icon: 'activity' });
    expect(stateMeta('BLOCKED').tone).toBe('danger');
    expect(stateMeta('ARCHIVED' as AnyState)).toEqual({ label: 'ARCHIVED', tone: 'neutral' });
  });
});
