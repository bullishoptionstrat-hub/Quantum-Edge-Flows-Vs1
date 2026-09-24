"""Phase 0 reproductions of legacy defects (P0-06, P0-07).

Each test asserts the behavior the directive requires (the invariant), against
the legacy code as it exists. They are marked xfail(strict=True,
raises=AssertionError): an xfail result means the defect reproduced; an XPASS
fails the run (the defect was fixed or refuted, so the register must be
updated); any exception other than AssertionError fails the run, so a broken
harness cannot pass as a reproduced defect.

IDs match qe/audit/DEFECT_REGISTER.csv.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from . import _legacy

defect = lambda did, why: pytest.mark.xfail(strict=True, raises=AssertionError, reason=f"{did}: {why}")  # noqa: E731


def _signal(**over):
    s = {"asset": "ES", "direction": "LONG", "entry": 6000.0, "stop_loss": 5990.0,
         "take_profit_targets": [6040.0], "confidence": 0.8, "signal_type": "test"}
    s.update(over)
    return s


# --------------------------------------------------------------------------- D-001
@defect("D-001", "execution_engine.py cannot be imported: dataclass field order TypeError")
def test_d001_execution_engine_imports():
    code = ("import sys; sys.path.insert(0, 'quantum-edge-terminal');"
            "import execution.execution_engine.execution_engine")
    r = subprocess.run([sys.executable, "-c", code], cwd=_legacy.REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr.strip().splitlines()[-1]


# --------------------------------------------------------------------------- D-002 (S-01)
@defect("D-002", "risk engine reads confidence/symbol/position_size_pct/signal_id; execution emits other names")
def test_d002_risk_engine_sees_execution_fields():
    ee = _legacy.execution_engine()
    risk = _legacy.load("execution/risk_engine/risk_engine.py")
    res = ee.ExecutionEngine().create_execution(_signal(confidence=0.10), {})
    payload = res.trade.to_dict()
    # A 10%-confidence signal must fail the risk engine's 50% minimum. The risk
    # engine reads payload["confidence"], absent from the payload, and defaults to 0.5.
    out = risk.RiskEngine()._check_confidence(payload)
    assert out.level == risk.RiskLevel.FAIL, out.reason


# --------------------------------------------------------------------------- D-003 (S-02)
@defect("D-003", "signal_id never set; every signal gets id '' so distinct signals collide as duplicates")
def test_d003_distinct_signals_are_not_duplicates():
    risk = _legacy.load("execution/risk_engine/risk_engine.py")
    eng = risk.RiskEngine()
    first = eng._check_duplicate_signal({"trade_id": "a", "asset": "ES"})
    second = eng._check_duplicate_signal({"trade_id": "b", "asset": "NQ"})
    assert first.level == risk.RiskLevel.PASS
    assert second.level == risk.RiskLevel.PASS, second.reason


# --------------------------------------------------------------------------- D-004 (S-03)
@defect("D-004", "macro filter exception becomes a warning; trade stays valid (fail-open)")
def test_d004_macro_filter_exception_blocks():
    ee = _legacy.execution_engine()

    def broken_filter(trade, regime):
        raise RuntimeError("macro service down")

    res = ee.ExecutionEngine(macro_filter_func=broken_filter).create_execution(_signal(), {})
    assert res.valid is False, f"valid={res.valid} warnings={res.warnings}"


@defect("D-005", "regime classifier exception silently falls back to NEUTRAL; trade stays valid")
def test_d005_regime_classifier_exception_blocks():
    ee = _legacy.execution_engine()

    def broken_regime(features):
        raise RuntimeError("regime model unavailable")

    res = ee.ExecutionEngine(classify_regime_func=broken_regime).create_execution(_signal(), {})
    assert res.valid is False, f"valid={res.valid} warnings={res.warnings}"


# --------------------------------------------------------------------------- D-006 (S-04)
@defect("D-006", "empty target list accepted; payload created with risk_reward_ratio 0")
def test_d006_missing_target_rejected():
    ee = _legacy.execution_engine()
    res = ee.ExecutionEngine().create_execution(_signal(take_profit_targets=[]), {})
    assert res.valid is False, f"valid={res.valid} rr={res.trade.risk_reward_ratio if res.trade else None}"


@defect("D-007", "no minimum R:R: a 0.5R trade is valid")
def test_d007_sub_2r_rejected():
    ee = _legacy.execution_engine()
    res = ee.ExecutionEngine().create_execution(_signal(take_profit_targets=[6005.0]), {})
    assert res.valid is False, f"valid={res.valid} rr={res.trade.risk_reward_ratio}"


# --------------------------------------------------------------------------- D-008 (S-05)
@defect("D-008", "risk_amount is |entry-stop| in price points, labelled dollars")
def test_d008_risk_amount_is_dollars():
    ee = _legacy.execution_engine()
    res = ee.ExecutionEngine().create_execution(_signal(), {})
    # 10 ES points x $50/point x 1 contract = $500 before costs.
    assert res.trade.risk_amount >= 500, f"risk_amount={res.trade.risk_amount}"


# --------------------------------------------------------------------------- D-009 (S-06)
@defect("D-009", "confidence > 0.75 in RISK_ON increases position size by up to 20%")
def test_d009_confidence_does_not_size():
    ee = _legacy.execution_engine()
    eng = ee.ExecutionEngine(classify_regime_func=lambda f: {"regime": "RISK_ON", "score": 2, "confidence": 0.9})
    lo = eng.create_execution(_signal(confidence=0.76), {}).trade.position_size
    hi = eng.create_execution(_signal(confidence=1.0), {}).trade.position_size
    assert hi == lo, f"size at conf 0.76={lo}, at conf 1.0={hi}"


# --------------------------------------------------------------------------- D-010
@defect("D-010", "max_risk_per_trade_pct and max_drawdown_pct are declared but never enforced")
def test_d010_risk_engine_enforces_per_trade_risk():
    risk = _legacy.load("execution/risk_engine/risk_engine.py")
    payload = {"signal_id": "x", "confidence": 0.9, "macro_confidence": 0.9, "symbol": "ES",
               "position_size_pct": 1.0, "entry": 6000.0, "stop_loss": 5000.0,
               "risk_amount": 50_000.0}  # 50% of equity at risk
    account = {"cash": 100_000, "buying_power": 100_000, "equity": 100_000}
    out = risk.RiskEngine().validate(payload, account, [])
    assert out.level == risk.RiskLevel.FAIL, out.reason


@defect("D-011", "missing account equity defaults to $100,000")
def test_d011_missing_equity_blocks():
    risk = _legacy.load("execution/risk_engine/risk_engine.py")
    eng = risk.RiskEngine()
    eng.daily_pnl = -4_000.0  # 40% of a real $10k account
    out = eng._check_daily_loss_limit({})  # equity unknown
    assert out.level == risk.RiskLevel.FAIL, out.reason


# --------------------------------------------------------------------------- D-012 (S-07)
@defect("D-012", "TradingView alert becomes tradeable from confidence+confluence; R:R < 1.618 only warns")
def test_d012_tv_low_rr_not_tradeable():
    tv = _legacy.load("tradingview_bridge_adapter.py")
    v = tv.TradingViewStrategyValidator()
    sig = v.parse_pine_script_alert('{"pair":"ES","signal_type":"BUY","entry":6000,"stop_loss":5990,'
                                    '"targets":[6002,6003],"confidence":0.9,"confluence":4}')
    out = v.generate_trade_instruction(sig)
    assert out["tradeable"] is False, f"rr={sig.risk_reward:.2f} tradeable={out['tradeable']}"


@defect("D-013", "missing confluence defaults to 3, exactly the passing threshold")
def test_d013_tv_missing_confluence_not_tradeable():
    tv = _legacy.load("tradingview_bridge_adapter.py")
    v = tv.TradingViewStrategyValidator()
    sig = v.parse_pine_script_alert('{"pair":"ES","signal_type":"BUY","entry":6000,"stop_loss":5990,'
                                    '"targets":[6030,6040],"confidence":0.9}')
    assert v.generate_trade_instruction(sig)["tradeable"] is False


@defect("D-014", "TradingView source timestamp discarded; replaced by local datetime.now()")
def test_d014_tv_preserves_source_time():
    tv = _legacy.load("tradingview_bridge_adapter.py")
    v = tv.TradingViewStrategyValidator()
    sig = v.parse_pine_script_alert('{"pair":"ES","signal_type":"BUY","entry":6000,"stop_loss":5990,'
                                    '"targets":[6030,6040],"confidence":0.9,"confluence":4,'
                                    '"timestamp":"2026-01-02T14:30:00Z"}')
    assert sig.timestamp == "2026-01-02T14:30:00Z", sig.timestamp


@defect("D-015", "long alert with stop above entry is still tradeable")
def test_d015_tv_rejects_inverted_stop():
    tv = _legacy.load("tradingview_bridge_adapter.py")
    v = tv.TradingViewStrategyValidator()
    sig = v.parse_pine_script_alert('{"pair":"ES","signal_type":"BUY","entry":6000,"stop_loss":6010,'
                                    '"targets":[6030,6040],"confidence":0.9,"confluence":4}')
    assert v.generate_trade_instruction(sig)["tradeable"] is False


@defect("D-016", "webhook receiver has no authentication, timestamp window, or replay protection")
def test_d016_webhook_replay_rejected():
    tv = _legacy.load("tradingview_bridge_adapter.py")
    rx = tv.create_pine_script_webhook_handler()
    alert = ('{"pair":"ES","signal_type":"BUY","entry":6000,"stop_loss":5990,'
             '"targets":[6030,6040],"confidence":0.9,"confluence":4}')
    rx.receive_alert(alert)
    rx.receive_alert(alert)
    assert len(rx.get_pending_trades()) == 1, f"pending={len(rx.get_pending_trades())}"


# --------------------------------------------------------------------------- D-017 (S-08)
@defect("D-017", "scorecard drops missing metrics from numerator and denominator; one metric can PASS")
def test_d017_scorecard_incomplete_is_not_pass():
    sc = _legacy.load("validation/scoring_engine/institutional_scorecard.py")
    res = sc.InstitutionalScorecard().evaluate({"expectancy": 0.20})
    assert res.gate_status != sc.GateStatus.PASS, f"score={res.overall_score} gate={res.gate_status}"


@defect("D-018", "a missing hard-fail metric counts as 'not failed'")
def test_d018_scorecard_missing_hard_fail_metric():
    sc = _legacy.load("validation/scoring_engine/institutional_scorecard.py")
    card = sc.InstitutionalScorecard()
    assert card.hard_fail_conditions, "scorecard defines hard-fail conditions"
    assert card._check_hard_fail({}, card.hard_fail_conditions[0]) is True


# --------------------------------------------------------------------------- D-019..D-022 (S-09..S-12)
def _bars(rows):
    import pandas as pd
    return pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"])


@defect("D-019", "sweep = high > prev_high*0.995: a bar that never reaches the level is a 'sweep'")
def test_d019_touch_below_level_is_not_sweep():
    msd = _legacy.load("ai-engine/src/modules/market_structure_detector.py")
    lvl = 6000.0
    rows = [[5990, 5995, 5985, 5992, 1]] * 3 + [[5990, lvl, 5985, 5992, 1]] * 2 + [[5980, 5975.0, 5965, 5970, 1]]
    # last bar high 5975 is 25 points BELOW the 6000 level
    sweeps = msd.MarketStructureDetector()._detect_sweeps(_bars(rows))
    assert not any(s["level"] == lvl for s in sweeps), sweeps


@defect("D-020", "no low-side (sell-side liquidity) sweep detection")
def test_d020_low_side_sweep_detected():
    msd = _legacy.load("ai-engine/src/modules/market_structure_detector.py")
    rows = [[5990, 5995, 5980, 5992, 1]] * 4 + [[5985, 5990, 5960, 5988, 1]]
    sweeps = msd.MarketStructureDetector()._detect_sweeps(_bars(rows))
    assert any(s["type"].startswith("LOW") for s in sweeps), sweeps


@defect("D-021", "CHoCH only fires on uptrend reversals; downtrend variable unused")
def test_d021_bearish_to_bullish_choch_detected():
    msd = _legacy.load("ai-engine/src/modules/market_structure_detector.py")
    closes = [6010, 6008, 6006, 6004, 6002, 6000, 6005, 6006, 6007, 6008, 6009]
    rows = [[c, c + 1, c - 1, c, 1] for c in closes]
    assert msd.MarketStructureDetector()._detect_choch(_bars(rows)), "no CHoCH after downtrend reversal"


@defect("D-022", "FVG uses two adjacent bars, not the three-candle imbalance")
def test_d022_fvg_requires_three_candles():
    msd = _legacy.load("ai-engine/src/modules/market_structure_detector.py")
    # Two bars gap up, but the third bar trades back into the gap: under a
    # three-candle definition (low[i+1] > high[i-1]) there is no FVG.
    rows = [[6000, 6002, 5998, 6001, 1], [6004, 6006, 6003, 6005, 1], [6004, 6005, 6001, 6002, 1]]
    fvgs = msd.MarketStructureDetector()._detect_fvg(_bars(rows))
    assert fvgs == [], fvgs


# --------------------------------------------------------------------------- D-023, D-024 (S-13)
def _journal_trade(tj, entry, exit_, direction="LONG"):
    j = tj.TradeJournal()
    j.create_entry({"trade_id": "t1", "asset": "ES", "direction": direction, "timestamp": "2026-01-02T14:30:00",
                    "entry": entry, "stop_loss": entry - 10, "take_profit_targets": [entry + 40],
                    "position_size": 1, "risk_reward_ratio": 4.0})
    j.mark_entry_filled("t1", entry)
    j.close_trade_manual("t1", exit_)
    return j


@defect("D-023", "journal net_pnl == gross_pnl (commissions TODO)")
def test_d023_journal_net_below_gross():
    tj = _legacy.load("storage/trade_journal/trade_journal.py")
    j = _journal_trade(tj, 6000.0, 6010.0)
    snap = j._calculate_performance_snapshot("all", list(j.entries.values()), "", "")
    assert snap.net_pnl < snap.gross_pnl, f"gross={snap.gross_pnl} net={snap.net_pnl}"


@defect("D-024", "realized R uses abs(): a losing trade reports positive R")
def test_d024_losing_trade_has_negative_r():
    tj = _legacy.load("storage/trade_journal/trade_journal.py")
    j = _journal_trade(tj, 6000.0, 5990.0)
    e = j.entries["t1"]
    assert e.rr_realized < 0, f"outcome={e.outcome} rr_realized={e.rr_realized}"


@defect("D-025", "journal P&L is price difference x size (points), not account currency")
def test_d025_journal_pnl_in_currency():
    tj = _legacy.load("storage/trade_journal/trade_journal.py")
    j = _journal_trade(tj, 6000.0, 6010.0)
    # 10 ES points x $50/point x 1 contract = $500 gross.
    assert j.entries["t1"].pnl == 500.0, f"pnl={j.entries['t1'].pnl}"


# --------------------------------------------------------------------------- D-026
@defect("D-026", "Pine alerts emit plain text; the bridge only parses JSON, so every real alert errors")
def test_d026_pine_alert_format_is_parseable_by_bridge():
    tv = _legacy.load("tradingview_bridge_adapter.py")
    rx = tv.create_pine_script_webhook_handler()
    # Message shape copied from tradingview_ut_bot_institutional.pine:297
    msg = "UT ELITE BUY | Confluence: 5/6 | Confidence: 83% | RR: 2.1:1 | Entry: 6000.25 | SL: 5990.0 | TP: 6021.75"
    out = rx.receive_alert(msg)
    assert out["status"] == "RECEIVED", out


# --------------------------------------------------------------------------- D-027, D-028
@defect("D-027", "validation_orchestrator.py and alert_engine.py are not valid Python")
@pytest.mark.parametrize("rel", ["validation/validation_orchestrator.py", "interface/alert_engine/alert_engine.py"])
def test_d027_modules_parse(rel):
    import ast
    try:
        ast.parse((_legacy.TERMINAL / rel).read_text())
    except SyntaxError as e:
        raise AssertionError(f"{rel}:{e.lineno}: {e.msg}") from None


@defect("D-028", "observability imports OpenTelemetry symbols absent from current SDKs (jaeger exporter, ProbabilitySampler)")
def test_d028_observability_imports():
    code = "import sys; sys.path.insert(0, 'quantum-edge-terminal'); import observability.telemetry_config"
    r = subprocess.run([sys.executable, "-c", code], cwd=_legacy.REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr.strip().splitlines()[-1]


# --------------------------------------------------------------------------- D-040
@defect("D-040", "BrokerConnection.submit_order always raises TypeError (OrderStatus built without 3 required fields)")
def test_d040_broker_submit_returns_status():
    bc = _legacy.load("execution/broker_engine/broker_connection.py")
    conn = bc.BrokerConnection(bc.BrokerConfig(api_key="placeholder", secret_key="placeholder",
                                               base_url="http://127.0.0.1:9", mode=bc.BrokerMode.PAPER))
    try:
        conn.submit_order("ES", 1, "buy")
    except TypeError as e:
        raise AssertionError(f"submit_order crashed: {e}") from None


# --------------------------------------------------------------------------- D-045, D-046 (Pine R:R arithmetic)
# Pine cannot run here. These tests first assert that the formulas are still in
# the Pine source (so they fail loudly if the scripts change), then replay the
# same arithmetic in float64, which is Pine's float type.
def _pine(name):
    return (_legacy.TERMINAL / name).read_text()


@defect("D-045", "UT bot: rr == 1.618 up to rounding, so the 1.618 minimum is decided by float noise")
def test_d045_ut_rr_filter_depends_on_market():
    import random
    src = _pine("tradingview_ut_bot_institutional.pine")
    assert "buy_target_2 = buy_entry + (buy_sl_dist * FRAC_162)" in src
    assert "buy_signal = buy_filtered and buy_rr >= min_rr" in src
    rng = random.Random(7)
    outcomes = set()
    for _ in range(2000):
        e, d = rng.uniform(4000, 7000), rng.uniform(0.25, 60)
        rr = ((e + d * 1.618) - e) / d
        outcomes.add(rr >= 1.618)
    # A filter that means something should pass every one of these identical-geometry setups.
    assert outcomes == {True}, f"filter outcomes over identical geometry: {outcomes}"


@defect("D-046", "Smart Blend: rr is a constant of the level geometry (2.94), so min_rr never rejects")
def test_d046_blend_rr_is_not_constant():
    src = _pine("tradingview_institutional_smart_blend_plus_CLEAN.pine")
    assert "buy_tp2 = buy_entry + (swing_range * FRAC_162)" in src
    rrs = set()
    for hi, lo in [(6000.0, 5900.0), (6000.0, 5990.0), (18000.0, 17000.0), (2400.0, 2395.5)]:
        r = hi - lo
        e = hi - r * 0.618
        sl = e - (e - (e - r * 0.786)) * 0.7
        rrs.add(round(((e + r * 1.618) - e) / (e - sl), 6))
    assert len(rrs) > 1, f"rr is the same for every range: {rrs}"
