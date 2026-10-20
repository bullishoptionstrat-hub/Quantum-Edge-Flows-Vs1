# Lookahead Threat Model (P0-09)

For each way future information could leak into a decision: where it could happen in this repository, what was checked, and the verdict.

| # | Threat | Where it could occur | What was checked | Verdict |
|---|---|---|---|---|
| L1 | Swing pivot used before its right-side confirmation bars exist | `QuantumEdge/research/fib*/detector.py` | `fib`, `fib2`, `fib3` detectors: `discovery_bar = completion_bar + pivot_n` (fib2/detector.py:238,355; fib3/detector.py:224,378). Simulation starts at `discovery_bar` (fib4/execution.py:100) | **Controlled** in sampled families. fib5–fib9 were not line-audited |
| L2 | Documentation disagrees with code about the discovery bar | `fib2/model.py:115` says `anchor_bar + pivot_n`, but the code uses `completion_bar + pivot_n` | Read both | Doc bug only (code is the safer one). Phase 2 fixtures should pin this |
| L3 | Entry filled at the signal bar's close or extreme after a close-confirmed signal | Research backtesters | `fib/backtester.py:94-97` enters at the **next bar's open** | **Controlled** in `fib` |
| L4 | Same-bar stop and target, favorable outcome chosen | Research backtesters | `fib/backtester.py:165-194` checks the stop first, then the target | **Controlled (conservative)** |
| L5 | Gap through the stop filled at the stop price | Research backtesters | `exit_price = stop` even when the open is beyond it | **Optimistic** (D-031) |
| L6 | Exit-dependent MFE/MAE | Research analysis | Excursions are tracked only until exit | **Censored** (D-032) |
| L7 | Adjusted prices used as executable levels | yfinance `auto_adjust=True` → LEAN zips (`generate_lean_data.py`) | Every research level is on adjusted history | **Present.** Levels are not tradeable prices historically |
| L8 | Higher-timeframe bar used before it closes | Pine `request.security` | Not used in any of the 3 Pine scripts | Not applicable |
| L9 | Realtime alert fires intrabar and repaints | Pine `alert()` with no `freq` argument (defaults to once per bar) | Static read only | **Plausible** (D-039). Needs checking in TradingView |
| L10 | Detector uses the current, still-forming bar | `ai-engine` `market_structure_detector.py` | Runs over whatever candles the caller posts. It has no notion of a closed bar or `available_at` | **Uncontrolled by design.** Replace it (Phase 3) |
| L11 | Synthetic data generated with knowledge of the strategy | 17 terminal backtests | Prices come from `random.gauss` with a drift term; one backtest draws outcomes directly | Not lookahead, but **not evidence** (D-030) |
| L12 | Wall clock inside decision logic | 147 lines across both subtrees (`static_flags.csv`, `wall_clock`) | Replay can't reproduce decisions that read the wall clock | **Present** in legacy code. INV-02 forbids it in `qe/core` |

## Required for Phase 3/4 (canonical core)

- Every derived object carries `formed_at` and `available_at`. The reducer asserts `available_at <= decision_time`, with a property test.
- Golden fixtures for pivot confirmation (L1), next-bar entry (L3), same-bar ambiguity (L4), and gap-through stops (L5).
- Point-in-time raw prices for executable levels. Adjusted series only for labeled analytics (L7).
