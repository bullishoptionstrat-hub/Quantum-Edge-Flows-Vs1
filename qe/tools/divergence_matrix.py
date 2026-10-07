#!/usr/bin/env python3
"""Source of truth for qe/audit/GODS_PLAN_RULE_DIVERGENCE_MATRIX.csv (P1-01).

Rows = canonical concepts. Columns = every existing implementation. Each cell is
what that implementation does, with file:line. ABSENT = concept not implemented.
The GP_CANONICAL column stays PENDING_A2-00 until the God's Plan source is provided.
Paths: T/ = quantum-edge-terminal/, AI/ = T/ai-engine/src/modules/, R/ = QuantumEdge/research/.
Run: python3 qe/tools/divergence_matrix.py
"""
import csv
from pathlib import Path

COLS = [
 ("GP_CANONICAL", "gp-1.0.0 (not yet written)"),
 ("AI_MSD", "AI/market_structure_detector.py (served by ai-engine; D-044 service does not start)"),
 ("AI_MSA", "AI/market_structure_analyzer.py"),
 ("AI_FRACTAL", "AI/fractal_validator.py (4-candle 'TTrades' fractal)"),
 ("AI_FIB", "AI/fib_manipulation_validator.py + enhanced_fib_validator.py"),
 ("AI_BLEND", "AI/institutional_smart_blend_plus.py + master_multi_signal.py + algo_detection.py"),
 ("PINE_BLEND", "T/tradingview_institutional_smart_blend_plus*.pine"),
 ("PINE_UT", "T/tradingview_ut_bot_institutional.pine"),
 ("RESEARCH_FIB", "R/fib..fib9 (ETF manipulation-leg research; best-engineered code in repo)"),
 ("TV_BRIDGE", "T/tradingview_bridge_adapter.py"),
 ("EXEC_RISK", "T/execution/execution_engine + risk_engine + storage/trade_journal"),
 ("SYNTH_BT", "T/backtest_*.py (17 of 18 on synthetic prices)"),
]

A = "ABSENT"
M = {
 "liquidity": {
  "AI_MSD": A, "AI_MSA": "ORDER_CLUSTER = close where volume > 2x mean of last 20 bars (:267-291); LIQUIDATION_LEVEL enum unused",
  "AI_FRACTAL": "implicit: previous candle's low/high (:45,48)", "AI_FIB": "enhanced: 'liquidity grab' = mean wick/body ratio over 10 bars > 1.3 (enhanced_fib_validator.py:12-38)",
  "AI_BLEND": "volume-based 'institutional liquidity' score (institutional_smart_blend_plus.py)", "PINE_BLEND": A, "PINE_UT": A,
  "RESEARCH_FIB": "prior confirmed pivot high/low (pivot_n=5 daily) as the level swept (R/fib2/detector.py:204-223)",
  "TV_BRIDGE": A, "EXEC_RISK": A, "SYNTH_BT": "inherits AI modules on random-walk data"},
 "swing": {
  "AI_MSD": "3-bar fractal: bar > neighbours +-1 (:155-166); no confirmation time",
  "AI_MSA": "max/min of symmetric window n=3 AND > neighbours (:171-195); no available_at",
  "AI_FRACTAL": A, "AI_FIB": "swing high/low = max/min of last 20 bars, not a pivot (fib_manipulation_validator.py:62-71)",
  "AI_BLEND": "via AI_FRACTAL + AI_MSA", "PINE_BLEND": "highest high / lowest low of last 20 bars (pine CLEAN :73-86)",
  "PINE_UT": "highest/lowest of recent bars (:70-83)",
  "RESEARCH_FIB": "symmetric pivot, n=5 daily, strict right-side; discovery_bar = pivot + n (R/fib/detector.py:32-80; R/fib2/detector.py:238)",
  "TV_BRIDGE": A, "EXEC_RISK": A, "SYNTH_BT": "AI modules"},
 "BOS": {
  "AI_MSD": "high > max(high of previous 2 bars) (:51-80); not a swing break; constant confidence 0.85",
  "AI_MSA": A, "AI_FRACTAL": A, "AI_FIB": A, "AI_BLEND": A, "PINE_BLEND": A, "PINE_UT": A,
  "RESEARCH_FIB": "completion must be a new higher high / lower low vs prior pivots (R/fib2/detector.py:235,352)",
  "TV_BRIDGE": A, "EXEC_RISK": A, "SYNTH_BT": A},
 "CHoCH": {
  "AI_MSD": "5 rising closes then a non-rising close; bullish-side only (:83-98, D-021)",
  "AI_MSA": A, "AI_FRACTAL": A, "AI_FIB": A, "AI_BLEND": A,
  "PINE_BLEND": "EMA9/EMA21 trend-state crossover used as signal (pine CLEAN :35-44) (trend flip, not structure)",
  "PINE_UT": "UT-bot ATR trailing-stop flip", 
  "RESEARCH_FIB": "fib3/fib4 '1h_structure_shift': first 1H close above prior 1H consolidation high inside zone (R/fib7/live_spec.py:53-56)",
  "TV_BRIDGE": A, "EXEC_RISK": A, "SYNTH_BT": A},
 "sweep": {
  "AI_MSD": "high > max(prev 2 highs) * 0.995; high side only (:118-134, D-019/D-020)",
  "AI_MSA": A, "AI_FRACTAL": "C2 low < C1 low (any undercut of the previous candle) (:45,48)",
  "AI_FIB": A, "AI_BLEND": "algo_detection stop hunt: high > prior high * 0.995 with volume > 1.5x mean, close < high*0.99 (algo_detection.py:77-97)",
  "PINE_BLEND": A, "PINE_UT": A,
  "RESEARCH_FIB": "new pivot low below prior pivot low (any penetration, no minimum) (R/fib2/detector.py:207-209)",
  "TV_BRIDGE": A, "EXEC_RISK": A, "SYNTH_BT": "AI_FRACTAL on random walks"},
 "reclaim": {
  "AI_MSD": A, "AI_MSA": A, "AI_FRACTAL": "C3 close beyond C1 close (:56)", "AI_FIB": A, "AI_BLEND": "algo_detection: close < high*0.99 (1% off the high)",
  "PINE_BLEND": A, "PINE_UT": A,
  "RESEARCH_FIB": "close back above prior pivot within sweep_recovery_bars=3 (R/fib2/detector.py:110-127, model.py:41). fib6 tested '1h_reclaim_after_sweep': -0.201R, 30.6% WR, rejected (R/fib7/live_spec.py:62-65; not reproducible, D-035)",
  "TV_BRIDGE": A, "EXEC_RISK": A, "SYNTH_BT": A},
 "displacement": {
  "AI_MSD": A, "AI_MSA": A, "AI_FRACTAL": "C4 high > C3 high (:64)", "AI_FIB": "leg magnitude vs threshold (fib_manipulation_validator.py)",
  "AI_BLEND": "ATR/momentum confluence points", "PINE_BLEND": "EMA separation > 0.5 ATR (pine CLEAN :51-53)", "PINE_UT": A,
  "RESEARCH_FIB": "leg >= 3.0 ATR and >= 2% of price, 3-120 bars (R/fib2/model.py:44-48); fib4 'displacement_off' entry bar body > ATR threshold",
  "TV_BRIDGE": A, "EXEC_RISK": A, "SYNTH_BT": A},
 "FVG": {
  "AI_MSD": "adjacent bars: low[i] > high[i-1] (:100-116, D-022)",
  "AI_MSA": "c1.high < c2.low (adjacent) plus trivial c3 test (:230-265); level = midpoint; confidence 0.80",
  "AI_FRACTAL": A, "AI_FIB": A, "AI_BLEND": "uses AI_MSA",
  "PINE_BLEND": "high[1] < low[0] or high[2] < low[1] (adjacent) (pine CLEAN :93-97)", "PINE_UT": A,
  "RESEARCH_FIB": A, "TV_BRIDGE": A, "EXEC_RISK": A, "SYNTH_BT": A},
 "iFVG": {c: A for c, _ in COLS[1:]},
 "order_block": {
  "AI_MSD": "open gap vs prior close > 2 x std of 2 closes (:135-153)", "AI_MSA": A, "AI_FRACTAL": A, "AI_FIB": A, "AI_BLEND": A,
  "PINE_BLEND": A, "PINE_UT": A, "RESEARCH_FIB": A, "TV_BRIDGE": A, "EXEC_RISK": A, "SYNTH_BT": A},
 "breaker": {
  "AI_MSD": A, "AI_MSA": "3-bar gap then close back through c1 extreme (:293-326); not an ICT breaker",
  "AI_FRACTAL": A, "AI_FIB": A, "AI_BLEND": A, "PINE_BLEND": A, "PINE_UT": A, "RESEARCH_FIB": A, "TV_BRIDGE": A, "EXEC_RISK": A, "SYNTH_BT": A},
 "retest": {
  "AI_MSD": A, "AI_MSA": A, "AI_FRACTAL": A,
  "AI_FIB": "limit entry assumed filled at 0.618 of 20-bar range (fib_manipulation_validator.py:112,134)",
  "AI_BLEND": "0.618 zone", "PINE_BLEND": "0.618 of 20-bar range (entry reference only; fill is market on crossover bar)", "PINE_UT": "optional fib 0.618 entry reference (:212)",
  "RESEARCH_FIB": "zone 0.382-0.618 of leg after discovery_bar, wait <= 40 bars (R/fib2/model.py:51-52,75; R/fib4/execution.py:100-135)",
  "TV_BRIDGE": A, "EXEC_RISK": A, "SYNTH_BT": "AI modules"},
 "confirmation": {
  "AI_MSD": A, "AI_MSA": A, "AI_FRACTAL": "C3 close + C4 expansion", "AI_FIB": "enhanced: trend + liquidity-grab confluence",
  "AI_BLEND": ">= 3 confluence 'hits' (institutional_smart_blend_plus.py:195)", "PINE_BLEND": "confluence score >= 2 (input :13; f_confluence_score :108-130)",
  "PINE_UT": "confluence N/6 filters", 
  "RESEARCH_FIB": "configurable trigger: touch_rejection | close_in_zone | nextbar_confirm | midzone_only | displacement_off | 1h_* (R/fib4/model.py:56-68; R/fib7/live_spec.py:28-66)",
  "TV_BRIDGE": "confidence >= 0.70 and confluence >= 3 (D-012/D-013)", "EXEC_RISK": "signal confidence >= 0.5 (risk_engine.py:289)", "SYNTH_BT": A},
 "SMT": {c: A for c, _ in COLS[1:]},
 "entry": {
  "AI_MSD": A, "AI_MSA": A, "AI_FRACTAL": "C4 close (the last candle supplied, may be forming) (:73,78)",
  "AI_FIB": "0.618 retracement limit, fill assumed", "AI_BLEND": "from fractal / optimized fib", 
  "PINE_BLEND": "strategy.entry market on signal bar (pine CLEAN :181-184)", "PINE_UT": "strategy.entry market (:257-260)",
  "RESEARCH_FIB": "next bar open after trigger (R/fib/backtester.py:94-97; fib4 entry_price = 1H or daily open)",
  "TV_BRIDGE": "alert 'entry' field, no fill model", "EXEC_RISK": "signal['entry'] as given", "SYNTH_BT": "varies"},
 "stop": {
  "AI_MSD": A, "AI_MSA": A,
  "AI_FRACTAL": "beyond C2 extreme - 0.2*C1 range, then moved 30% toward entry ('proven +$1893' on synthetic data) (:74,85): not structural",
  "AI_FIB": "0.786 - 5% of leg (fib_manipulation_validator.py:113,135)", "AI_BLEND": "0.786", 
  "PINE_BLEND": "entry - 0.786*range, then 30% tighter (pine CLEAN :152-159)", "PINE_UT": "UT ATR trailing stop (:213,225)",
  "RESEARCH_FIB": "origin (anchor extreme - 0.25 ATR) or fib_786 (R/fib2/model.py:66-68)",
  "TV_BRIDGE": "alert stop_loss; side not validated (D-015)", "EXEC_RISK": "signal stop_loss; side validated in execution engine only", "SYNTH_BT": "varies"},
 "target": {
  "AI_MSD": A, "AI_MSA": "fib extension targets (:328-343)", "AI_FRACTAL": "entry + 1.618 x (C1 high - C2 low)",
  "AI_FIB": "1.618 extension", "AI_BLEND": "1.618", "PINE_BLEND": "entry + 1.618*range (pine CLEAN :155,160)", "PINE_UT": "entry + 1.618 x stop distance (:218,230)",
  "RESEARCH_FIB": "1.272 or 1.618 extension; optional partial at 1.272 (R/fib2/model.py:71)",
  "TV_BRIDGE": "targets[1] if >1 target else targets[0] (:138)", "EXEC_RISK": "take_profit_targets[0]; empty list allowed (D-006)", "SYNTH_BT": "varies"},
 "R_min": {
  "AI_MSD": A, "AI_MSA": A, "AI_FRACTAL": "none", "AI_FIB": "none", "AI_BLEND": "min_rr = 1.618 (institutional_smart_blend_plus.py:83,301)",
  "PINE_BLEND": "min_rr 1.618 input, but the level geometry fixes rr at 2.94 (2.06 with the 30% stop fix off) for every setup, so the filter never depends on the market (D-046)",
  "PINE_UT": "min_rr 1.618 and target = 1.618 x stop distance, so rr = 1.618 up to float rounding: pass/fail is decided by rounding noise (about 50% fail in a float64 simulation) (D-045)",
  "RESEARCH_FIB": "none (R measured post hoc)", "TV_BRIDGE": "1.618 warning only (D-012)", "EXEC_RISK": "none (D-007)", "SYNTH_BT": "varies"},
 "costs": {
  "AI_MSD": A, "AI_MSA": A, "AI_FRACTAL": A, "AI_FIB": A, "AI_BLEND": A, "PINE_BLEND": "strategy() declares none (TradingView defaults)", "PINE_UT": "none declared",
  "RESEARCH_FIB": "fib5+: slippage_pct/commission default 0, applied post hoc to R (D-033)", "TV_BRIDGE": A,
  "EXEC_RISK": "none; journal net = gross (D-023)", "SYNTH_BT": "none in 17 of 18"},
 "session": {
  "AI_MSD": A, "AI_MSA": A, "AI_FRACTAL": A, "AI_FIB": A, "AI_BLEND": A, "PINE_BLEND": A, "PINE_UT": "session.ismarket filter (:59-60)",
  "RESEARCH_FIB": "daily/1H ETF bars; no session model", "TV_BRIDGE": "comment only (:176-177)", "EXEC_RISK": A, "SYNTH_BT": A},
 "expiry": {
  "AI_MSD": A, "AI_MSA": A, "AI_FRACTAL": A, "AI_FIB": A, "AI_BLEND": A, "PINE_BLEND": "min 3 bars between signals", "PINE_UT": A,
  "RESEARCH_FIB": "zone wait <= 40 bars, trade <= 60 bars (R/fib2/model.py:75-76)", "TV_BRIDGE": A, "EXEC_RISK": A, "SYNTH_BT": A},
 "one_attempt": {
  "AI_MSD": A, "AI_MSA": A, "AI_FRACTAL": A, "AI_FIB": A, "AI_BLEND": A, "PINE_BLEND": A, "PINE_UT": A,
  "RESEARCH_FIB": "one simulated trade per detected leg; overlapping legs from the same sweep not deduplicated (not verified)",
  "TV_BRIDGE": "none; duplicate alerts both pending (D-016)", "EXEC_RISK": "5-minute duplicate window on signal_id that is always '' (D-003)", "SYNTH_BT": A},
 "timing": {
  "AI_MSD": "no closed-bar concept; operates on whatever candles are posted", "AI_MSA": "same", "AI_FRACTAL": "last 4 supplied candles, incl. possibly forming bar",
  "AI_FIB": "last 20 supplied candles", "AI_BLEND": "same", "PINE_BLEND": "alert() without freq: may fire intrabar (D-039)", "PINE_UT": "same (D-039)",
  "RESEARCH_FIB": "discovery_bar = completion + pivot_n; entry next open (controlled)", "TV_BRIDGE": "source time discarded (D-014)",
  "EXEC_RISK": "datetime.utcnow() / datetime.now() in logic", "SYNTH_BT": "synthetic index"},
 "intrabar": {
  "AI_MSD": A, "AI_MSA": A, "AI_FRACTAL": A, "AI_FIB": A, "AI_BLEND": A, "PINE_BLEND": "TradingView broker emulator", "PINE_UT": "TradingView broker emulator",
  "RESEARCH_FIB": "stop checked before target (conservative); gap-through fills at stop (optimistic, D-031)",
  "TV_BRIDGE": A, "EXEC_RISK": A, "SYNTH_BT": "not audited (synthetic data, D-030)"},
}

rows = []
for concept, cells in M.items():
    row = {"concept": concept, "GP_CANONICAL": "PENDING_A2-00"}
    for c, _ in COLS[1:]:
        row[c] = cells.get(c, A)
    impl = sum(1 for c, _ in COLS[1:] if row[c] != A)
    row["n_implementations"] = impl
    row["conflict"] = "NONE_IMPLEMENTED" if impl == 0 else ("SINGLE" if impl == 1 else "DIVERGENT")
    rows.append(row)

fields = ["concept", "n_implementations", "conflict"] + [c for c, _ in COLS]
out = Path("qe/audit/GODS_PLAN_RULE_DIVERGENCE_MATRIX.csv")
with out.open("w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)
with Path("qe/audit/DIVERGENCE_MATRIX_COLUMNS.csv").open("w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["column", "implementation"]); w.writerows(COLS)
from collections import Counter
print(len(rows), Counter(r["conflict"] for r in rows))
