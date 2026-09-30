'use client';

import * as React from 'react';
import { Icon } from './controls';
import { Badge, Direction } from './status';
import { LevelKey } from './charts';
import { computeTicket, type TicketTarget } from './ticket-math';
import { cx, formatPoints, formatPrice, formatR, formatUsd, type AnyState, type Side } from './util';

export type TradeTarget = TicketTarget;

export type SmtStatus = 'confirmed' | 'absent' | 'mixed' | 'stale' | 'opposing';

export interface TradeTicketProps {
  symbol: string;
  /** Exact contract, e.g. "ESZ6" — never just the root. */
  contract?: string;
  side: Side;
  state: AnyState;
  model?: string;
  session?: string;
  /** Preformatted time with its zone, e.g. "2026-09-25 09:42:05 ET". */
  timestamp?: string;
  entry: number;
  stop: number;
  /** Nearest first: TP1, TP2, TP3. */
  targets: TradeTarget[];
  /** From a verified contract spec — ES 0.25, MES 0.25, GC 0.10, SI 0.005. */
  tickSize: number;
  /** USD per tick per contract from the same spec — ES $12.50, MES $1.25, NQ $5.00, MNQ $0.50. */
  tickValue: number;
  /** Estimated round-trip commissions + slippage per contract, USD. Included in risk and in net R. */
  costsPerContract?: number;
  /** Dollars this idea may lose (the stricter of personal and firm limits). Contracts = floor(budget ÷ risk per contract). */
  riskBudget?: number;
  /** Minimum net R to the best target (God's Plan default 2). */
  minR?: number;
  smt?: { status: SmtStatus; pair: string };
  /** What proves the idea wrong, in one sentence. */
  invalidation?: string;
  /** When to cancel the unfilled order, in one sentence. */
  cancelIf?: string;
  className?: string;
}

const SMT_WORD: Record<SmtStatus, string> = {
  confirmed: 'SMT CONFIRMED', absent: 'SMT ABSENT', mixed: 'SMT MIXED', stale: 'SMT STALE', opposing: 'SMT OPPOSING',
};

export function TradeTicket(p: TradeTicketProps) {
  const { symbol, contract, side, state, model, session, timestamp, entry, stop, targets, tickSize, tickValue, costsPerContract = 0, riskBudget, minR = 2, smt, invalidation, cancelIf, className } = p;
  const { geometryError, offTick, stopPts, stopTicks, riskPerContract, contracts, rows, bestNet, underMin } =
    computeTicket({ side, entry, stop, targets, tickSize, tickValue, costsPerContract, riskBudget, minR });
  const context = [model, session].filter(Boolean).join(' · ');

  return (
    <article className={cx('qe-ticket', className)} aria-label={`${side} ${symbol} trade ticket`}>
      <header className="qe-ticket-head">
        <div className="qe-ticket-id">
          <span className="qe-ticket-symbol qe-control">{symbol}</span>
          {contract ? <span className="qe-ticket-contract qe-data">{contract}</span> : null}
          <Direction side={side} size="md" />
        </div>
        <Badge state={state} />
        {context ? <div className="qe-ticket-context qe-data">{context}</div> : null}
      </header>

      {geometryError ? (
        <p role="alert" className="qe-ticket-flag is-danger qe-body-sm"><Icon name="alert-circle" size="sm" />Invalid ticket: {geometryError} Sizing is withheld.</p>
      ) : null}
      {offTick ? (
        <p className="qe-ticket-flag is-warning qe-body-sm"><Icon name="alert-triangle" size="sm" />A price is off the {formatPrice(tickSize, tickSize)} tick grid. Check the contract spec before sending.</p>
      ) : null}

      <section className="qe-ticket-section" aria-label="Risk">
        <h3 className="qe-ticket-section-title qe-label">Risk</h3>
        <dl className="qe-ticket-rows">
          <div className="qe-ticket-row">
            <dt className="qe-label"><LevelKey kind="stop" />Stop / invalidation</dt>
            <dd><span className="qe-ticket-value qe-control">{formatPrice(stop, tickSize)}</span><span className="qe-ticket-sub qe-data">{formatPoints(-stopPts, tickSize)} pts · {stopTicks} ticks</span></dd>
          </div>
          <div className="qe-ticket-row">
            <dt className="qe-label">Risk / contract</dt>
            <dd><span className="qe-ticket-value qe-control">{formatUsd(riskPerContract)}</span><span className="qe-ticket-sub qe-data">{stopTicks} × {formatUsd(tickValue)}{costsPerContract ? ` + ${formatUsd(costsPerContract)} est. costs` : ''}</span></dd>
          </div>
          <div className="qe-ticket-row">
            <dt className="qe-label">Size</dt>
            <dd>
              {geometryError || contracts === undefined ? (
                <span className="qe-ticket-value qe-control is-muted">{geometryError ? 'Withheld' : 'Set a risk budget'}</span>
              ) : contracts === 0 ? (
                <>
                  <span className="qe-ticket-value qe-control is-warning">0 contracts</span>
                  <span className="qe-ticket-sub qe-data">One contract risks {formatUsd(riskPerContract)}, over the {formatUsd(riskBudget!)} budget. Pass, or use the micro contract.</span>
                </>
              ) : (
                <>
                  <span className="qe-ticket-value qe-control">{contracts} {contracts === 1 ? 'contract' : 'contracts'}</span>
                  <span className="qe-ticket-sub qe-data">floor({formatUsd(riskBudget!)} ÷ {formatUsd(riskPerContract)}) · {formatUsd(contracts * riskPerContract)} at risk</span>
                </>
              )}
            </dd>
          </div>
        </dl>
      </section>

      <section className="qe-ticket-section" aria-label="Entry">
        <h3 className="qe-ticket-section-title qe-label">Entry</h3>
        <dl className="qe-ticket-rows">
          <div className="qe-ticket-row">
            <dt className="qe-label"><LevelKey kind="entry" />Entry</dt>
            <dd><span className="qe-ticket-value qe-control">{formatPrice(entry, tickSize)}</span></dd>
          </div>
        </dl>
      </section>

      {rows.length ? (
        <section className="qe-ticket-section" aria-label="Targets">
          <h3 className="qe-ticket-section-title qe-label">Targets</h3>
          <table className="qe-ticket-targets qe-data">
            <thead><tr><th scope="col">Level</th><th scope="col">Price</th><th scope="col">Distance</th><th scope="col">Gross</th><th scope="col">Net</th></tr></thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={r.label}>
                  <th scope="row"><LevelKey kind="target" strong={i === 1} />{r.label}</th>
                  <td>{formatPrice(r.price, tickSize)}</td>
                  <td>{formatPoints(r.dist, tickSize)} pts</td>
                  <td>{formatR(r.gross)}</td>
                  <td className={cx(r.net < minR && 'is-warning')}>{formatR(r.net)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {underMin ? (
            <p className="qe-ticket-flag is-warning qe-body-sm"><Icon name="alert-triangle" size="sm" />Best target nets {formatR(bestNet)}, under the {formatR(minR)} minimum (REWARD_UNDER_2R).</p>
          ) : null}
        </section>
      ) : null}

      {smt || invalidation || cancelIf ? (
        <section className="qe-ticket-section" aria-label="Conditions">
          <h3 className="qe-ticket-section-title qe-label">Conditions</h3>
          {smt ? <Badge tone={smt.status === 'confirmed' ? 'ok' : 'danger'} icon={smt.status === 'confirmed' ? 'check' : 'ban'}>{SMT_WORD[smt.status]} · {smt.pair}</Badge> : null}
          <dl className="qe-ticket-notes">
            {invalidation ? <div><dt className="qe-label">Invalidated if</dt><dd className="qe-body-sm">{invalidation}</dd></div> : null}
            {cancelIf ? <div><dt className="qe-label">Cancel if</dt><dd className="qe-body-sm">{cancelIf}</dd></div> : null}
          </dl>
        </section>
      ) : null}

      {timestamp ? <footer className="qe-ticket-foot qe-data">{timestamp}</footer> : null}
    </article>
  );
}
