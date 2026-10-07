"""Fixture author's tool for gp-1.0.0-draft.1 golden fixtures (directive E2, B4.1).

Every expected value below was derived by hand from qe/spec/GP_SPEC.md, not from
any implementation (none exists). Running this script rewrites qe/spec/fixtures/
GF-*.json, MANIFEST.sha256 and qe/spec/GP_REQUIREMENTS_TRACE.csv deterministically.
Implementers must never edit the fixtures to make a reducer pass (directive B4);
the manifest test detects edits.

    python qe/spec/fixtures/build_fixtures.py

Fixture conventions (also in README.md):
- Prices are integer ticks. A bar is {"i", "o", "h", "l", "c"} plus optional
  "contract_id", "delay_s" (available_at - event_time), "start_offset_s".
- Bar i starts at time_base.bar0_start_utc + i * timeframe_s (+ start_offset_s).
- Bars are listed in arrival order. A bar index listed twice is a duplicate
  delivery; the second one is referred to as "dup:<i>".
- Transitions are [state, at] where at is a bar index, "dup:<i>" or "tick:<k>".
- Setup fixtures take liquidity objects as given inputs; deriving liquidity is
  the liquidity module's job (GF-L* fixtures). Expected lists are exhaustive:
  no other lineage or rejection may be produced. "evidence" is a subset check.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = HERE.parent
SPEC_VERSION = "gp-1.0.0-draft.1"
TF = 300

# ---------------------------------------------------------------- base scenario (ES LONG)
WARM = [{"i": i, "o": 20000, "h": 20004, "l": 19996, "c": 20000} for i in range(15)]
BASE = WARM + [
    {"i": 15, "o": 19998, "h": 19999, "l": 19976, "c": 19978},  # sweep of 19980 by 4 ticks
    {"i": 16, "o": 19978, "h": 19984, "l": 19977, "c": 19983},  # reclaim: close >= 19981
    {"i": 17, "o": 19983, "h": 20010, "l": 19982, "c": 20008},  # displacement
    {"i": 18, "o": 20008, "h": 20014, "l": 19990, "c": 20012},  # FVG: zone [19984, 19990]
    {"i": 19, "o": 20012, "h": 20016, "l": 20000, "c": 20004},
    {"i": 20, "o": 20004, "h": 20006, "l": 19994, "c": 19996},
    {"i": 21, "o": 19996, "h": 19998, "l": 19987, "c": 19992},  # retest: low <= 19990
    {"i": 22, "o": 19992, "h": 20002, "l": 19990, "c": 20000},  # confirmation
]
PAIR_WARM = [{"i": i, "o": 80000, "h": 80016, "l": 79984, "c": 80000} for i in range(15)]
PAIR = PAIR_WARM + [
    {"i": 15, "o": 79996, "h": 79998, "l": 79910, "c": 79920},  # holds above 79900 (+2 ticks margin)
    {"i": 16, "o": 79920, "h": 79940, "l": 79915, "c": 79936},
    {"i": 17, "o": 79936, "h": 80040, "l": 79932, "c": 80030},
    {"i": 18, "o": 80030, "h": 80050, "l": 79990, "c": 80046},
    {"i": 19, "o": 80046, "h": 80060, "l": 80010, "c": 80020},
    {"i": 20, "o": 80020, "h": 80026, "l": 79990, "c": 79996},
    {"i": 21, "o": 79996, "h": 80000, "l": 79960, "c": 79980},
    {"i": 22, "o": 79980, "h": 80010, "l": 79970, "c": 80004},
    {"i": 23, "o": 80004, "h": 80010, "l": 79990, "c": 80000},
]
PRIOR_CLOSE = "2026-07-13T20:00:01Z"  # available_at of the prior RTH session's last bar
L_ID, H_ID, NQ_L_ID = "ES:PRIOR_RTH_LOW:2026-07-13", "ES:PRIOR_RTH_HIGH:2026-07-13", "NQ:PRIOR_RTH_LOW:2026-07-13"
LIQ_L = {"liquidity_id": L_ID, "instrument_root": "ES", "type": "PRIOR_RTH_LOW", "side": "SELL_SIDE",
         "level": 19980, "session_date": "2026-07-13", "available_at_utc": PRIOR_CLOSE}
LIQ_H = {"liquidity_id": H_ID, "instrument_root": "ES", "type": "PRIOR_RTH_HIGH", "side": "BUY_SIDE",
         "level": 20090, "session_date": "2026-07-13", "available_at_utc": PRIOR_CLOSE}
LIQ_NQ_L = {"liquidity_id": NQ_L_ID, "instrument_root": "NQ", "type": "PRIOR_RTH_LOW", "side": "SELL_SIDE",
            "level": 79900, "session_date": "2026-07-13", "available_at_utc": PRIOR_CLOSE}

BAR0_DEFAULT = "2026-07-14T12:20:00Z"  # 08:20 ET; bar 15 starts 09:35 ET


def ns(utc: str) -> int:
    dt = datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp()) * 1_000_000_000


def bar_start_ns(bar0: str, i: int) -> int:
    return ns(bar0) + i * TF * 1_000_000_000


def upto(bars, last):
    return [copy.deepcopy(b) for b in bars if b["i"] <= last]


def replace(bars, *new):
    by = {b["i"]: b for b in new}
    return [copy.deepcopy(by.get(b["i"], b)) for b in bars]


def bar(i, o, h, low, c, **kw):
    d = {"i": i, "o": o, "h": h, "l": low, "c": c}
    d.update(kw)
    return d


HAPPY_TRANSITIONS = [["SWEPT", 15], ["RECLAIMED", 16], ["DISPLACED", 17], ["RETESTED", 21],
                     ["CONFIRMED", 22], ["SMT_CONFIRMED", 22], ["STRATEGY_AUTHORIZED", 22]]
HAPPY_EVIDENCE = {
    "sweep_bar": 15, "penetration_ticks": 4, "atr_sweep": "8/1", "sweep_extreme": 19976,
    "reclaim_bar": 16, "displacement_bar": 17,
    "displacement": {"range": 28, "body": 25, "atr": "127/14", "body_ratio": "25/28",
                     "close_location": "13/14", "structure_ref": 20004},
    "zone": {"bottom": 19984, "top": 19990, "formed_bar": 18},
    "retest_bar": 21, "confirmation_bar": 22,
    "smt": {"state": "CONFIRMED", "paired_ref": 79900, "paired_extreme": 79910},
    "entry_limit": 20001, "stop": 19974, "target": 20089, "target_liquidity_id": H_ID,
    # risk = 27*1250 + 500 + 1*1250 = 35500; reward = 88*1250 - 500 = 109500
    "net_r": "219/71",
}


def setup_fixture(fid, title, covers, amb, *, primary=None, pair=None, liquidity=None,
                  instrument="ES", contract="ESU6", pair_instrument="NQ", pair_contract="NQU6",
                  bar0=BAR0_DEFAULT, news=None, news_missing=False, roll=None, store=None,
                  store_missing=False, ticks=None, expected):
    return {
        "fixture_id": fid, "module": "setup", "title": title, "spec_version": SPEC_VERSION,
        "covers": covers, "ambiguities": amb,
        "instrument": instrument, "contract_id": contract,
        "pair": None if pair_instrument is None else {"instrument": pair_instrument, "contract_id": pair_contract},
        "time_base": {"bar0_start_utc": bar0, "timeframe_s": TF, "default_delay_s": 1},
        "primary_bars": BASE if primary is None else primary,
        "pair_bars": ([] if pair_instrument is None else (PAIR if pair is None else pair)),
        "liquidity": [LIQ_L, LIQ_H, LIQ_NQ_L] if liquidity is None else liquidity,
        "news_calendar": None if news_missing else ([] if news is None else news),
        "roll_metadata": {contract: {"roll_date": "2026-09-10"}} if roll is None else roll,
        "lineage_store": None if store_missing else ([] if store is None else store),
        "clock_ticks": ticks or [],
        "expected": expected,
    }


def exp(lineages=(), rejections=(), liquidity_final=None):
    return {"lineages": list(lineages), "rejections": list(rejections),
            "liquidity_final": liquidity_final or {L_ID: "CONSUMED", H_ID: "ACTIVE"}}


def lin(transitions, final_state, reason, evidence=None, direction="LONG", liquidity_id=L_ID):
    return {"direction": direction, "liquidity_id": liquidity_id, "transitions": transitions,
            "final_state": final_state, "reason_code": reason, "evidence": evidence or {}}


def rej(i, reason, liquidity_id=L_ID):
    return {"bar": i, "liquidity_id": liquidity_id, "reason_code": reason}


def blocked_at_22(reason, evidence=None, smt_ok=True):
    t = HAPPY_TRANSITIONS[:5] + ([["SMT_CONFIRMED", 22]] if smt_ok else []) + [["BLOCKED", 22]]
    return lin(t, "BLOCKED", reason, evidence)


FULL_COVERS = ["GP-REQ-001", "GP-REQ-002", "GP-REQ-003", "GP-REQ-004", "GP-REQ-006", "GP-REQ-007",
               "GP-REQ-020", "GP-REQ-021", "GP-REQ-050", "GP-REQ-052", "GP-REQ-060", "GP-REQ-061",
               "GP-REQ-062", "GP-REQ-065", "GP-REQ-070", "GP-REQ-071", "GP-REQ-072", "GP-REQ-080",
               "GP-REQ-090", "GP-REQ-100", "GP-REQ-120", "GP-REQ-121", "GP-REQ-122", "GP-REQ-123",
               "GP-REQ-124", "GP-REQ-125", "GP-REQ-130", "GP-REQ-131", "GP-REQ-140", "GP-REQ-141",
               "GP-REQ-142", "GP-REQ-143", "GP-REQ-145", "GP-REQ-150", "GP-REQ-151"]


# ---------------------------------------------------------------- mirror (GP-REQ-005)
M_ES, M_NQ = 40000, 160000


def mirror_bars(bars, m):
    out = []
    for b in bars:
        nb = dict(b)
        nb.update(o=m - b["o"], h=m - b["l"], l=m - b["h"], c=m - b["c"])
        out.append(nb)
    return out


def mirror_liq(liq, m):
    swap = {"PRIOR_RTH_LOW": "PRIOR_RTH_HIGH", "PRIOR_RTH_HIGH": "PRIOR_RTH_LOW"}
    t = swap[liq["type"]]
    return dict(liq, type=t, side="BUY_SIDE" if liq["side"] == "SELL_SIDE" else "SELL_SIDE",
                level=m - liq["level"], liquidity_id=f'{liq["instrument_root"]}:{t}:{liq["session_date"]}')


def build_setup():
    fx = []
    fx.append(setup_fixture("GF-001", "LONG happy path: sweep, reclaim, displacement, FVG, retest, confirmation, SMT, net R >= 2",
        FULL_COVERS, ["AMB-001", "AMB-007", "AMB-015", "AMB-018", "AMB-020", "AMB-022", "AMB-025", "AMB-027", "AMB-028", "AMB-029"],
        expected=exp([lin(HAPPY_TRANSITIONS, "STRATEGY_AUTHORIZED", "GP_AUTHORIZED", HAPPY_EVIDENCE)])))

    ml = mirror_liq(LIQ_L, M_ES)
    mh = mirror_liq(LIQ_H, M_ES)
    mnq = mirror_liq(LIQ_NQ_L, M_NQ)
    mev = copy.deepcopy(HAPPY_EVIDENCE)
    mev.update(sweep_extreme=M_ES - 19976, entry_limit=M_ES - 20001, stop=M_ES - 19974, target=M_ES - 20089,
               target_liquidity_id=mh["liquidity_id"])
    mev["displacement"]["structure_ref"] = M_ES - 20004
    mev["zone"] = {"bottom": M_ES - 19990, "top": M_ES - 19984, "formed_bar": 18}
    mev["smt"] = {"state": "CONFIRMED", "paired_ref": M_NQ - 79900, "paired_extreme": M_NQ - 79910}
    fx.append(setup_fixture("GF-002", "SHORT mirror of GF-001 (prices p -> 40000 - p, NQ p -> 160000 - p)",
        ["GP-REQ-005"] + FULL_COVERS, ["AMB-001"],
        primary=mirror_bars(BASE, M_ES), pair=mirror_bars(PAIR, M_NQ), liquidity=[ml, mh, mnq],
        expected={"lineages": [lin(HAPPY_TRANSITIONS, "STRATEGY_AUTHORIZED", "GP_AUTHORIZED", mev,
                                   direction="SHORT", liquidity_id=ml["liquidity_id"])],
                  "rejections": [], "liquidity_final": {ml["liquidity_id"]: "CONSUMED", mh["liquidity_id"]: "ACTIVE"}}))

    after_touch = bar(16, 19982, 19990, 19981, 19988)
    fx.append(setup_fixture("GF-003", "A touch is not a sweep: low equals the level", ["GP-REQ-050"], ["AMB-009"],
        primary=upto(BASE, 14) + [bar(15, 19998, 19999, 19980, 19982), after_touch],
        expected=exp(liquidity_final={L_ID: "ACTIVE", H_ID: "ACTIVE"})))
    fx.append(setup_fixture("GF-004", "1-tick penetration is below the 2-tick minimum: no sweep", ["GP-REQ-051"], ["AMB-009"],
        primary=upto(BASE, 14) + [bar(15, 19998, 19999, 19979, 19982), after_touch],
        expected=exp(liquidity_final={L_ID: "ACTIVE", H_ID: "ACTIVE"})))
    fx.append(setup_fixture("GF-005", "Penetration 9 ticks > 1.0 x ATR(8): breakdown, not a sweep", ["GP-REQ-052", "GP-REQ-021"], ["AMB-010"],
        primary=upto(BASE, 14) + [bar(15, 19998, 19999, 19971, 19975), bar(16, 19975, 19985, 19973, 19984)],
        expected=exp(rejections=[rej(15, "GP_INVALID_SWEEP_TOO_DEEP")])))
    fx.append(setup_fixture("GF-006", "Reclaim window (3 bars) expires; failed bullish reclaim creates no SHORT lineage; consumed level cannot be re-swept",
        ["GP-REQ-062", "GP-REQ-063", "GP-REQ-064", "GP-REQ-133"], ["AMB-012", "AMB-014"],
        primary=upto(BASE, 15) + [bar(16, 19978, 19982, 19977, 19980), bar(17, 19980, 19980, 19975, 19979),
                                  bar(18, 19979, 19981, 19972, 19974)],
        expected=exp([lin([["SWEPT", 15], ["EXPIRED", 17]], "EXPIRED", "GP_EXPIRED_RECLAIM_WINDOW")])))
    fx.append(setup_fixture("GF-007", "Two consecutive closes below the level: accepted beyond", ["GP-REQ-060", "GP-REQ-062"], ["AMB-014"],
        primary=upto(BASE, 15) + [bar(16, 19978, 19979, 19973, 19975)],
        expected=exp([lin([["SWEPT", 15], ["INVALIDATED", 16]], "INVALIDATED", "GP_INVALID_ACCEPTED_BEYOND")])))
    fx.append(setup_fixture("GF-008", "Sweep bar reclaims on its own close (non-terminal at fixture end)", ["GP-REQ-061"], ["AMB-013"],
        primary=upto(BASE, 14) + [bar(15, 19998, 19999, 19976, 19985), bar(16, 19985, 19988, 19983, 19986)],
        expected=exp([lin([["SWEPT", 15], ["RECLAIMED", 15]], "RECLAIMED", None)])))
    quiet = [bar(17, 19983, 19988, 19980, 19986), bar(18, 19986, 19990, 19982, 19984), bar(19, 19984, 19989, 19981, 19987),
             bar(20, 19987, 19991, 19983, 19985), bar(21, 19985, 19990, 19981, 19988), bar(22, 19988, 19992, 19984, 19990)]
    fx.append(setup_fixture("GF-009", "No displacement within reclaim bar + 6 bars", ["GP-REQ-072", "GP-REQ-073"], ["AMB-015", "AMB-017"],
        primary=upto(BASE, 16) + quiet,
        expected=exp([lin([["SWEPT", 15], ["RECLAIMED", 16], ["EXPIRED", 22]], "EXPIRED", "GP_EXPIRED_DISPLACEMENT_WINDOW")])))
    fx.append(setup_fixture("GF-010", "Candidate passes range/body/close-location but fails the structure break (close 20002 <= 20004)",
        ["GP-REQ-071", "GP-REQ-073"], ["AMB-015", "AMB-016"],
        primary=upto(BASE, 16) + [bar(17, 19983, 20003, 19982, 20002), bar(18, 20002, 20004, 19996, 19998),
                                  bar(19, 19998, 20000, 19992, 19995), bar(20, 19995, 19999, 19990, 19996),
                                  bar(21, 19996, 19998, 19991, 19993), bar(22, 19993, 19997, 19989, 19994)],
        expected=exp([lin([["SWEPT", 15], ["RECLAIMED", 16], ["EXPIRED", 22]], "EXPIRED", "GP_EXPIRED_DISPLACEMENT_WINDOW",
                          {"displacement_candidates": {"17": {"failed_gates": ["STRUCTURE_BREAK"], "range": 21, "body": 19,
                                                              "structure_ref": 20004}}})])))
    fx.append(setup_fixture("GF-011", "Displacement leaves no FVG (low(18) = high(16)): no zone", ["GP-REQ-080", "GP-REQ-081"], ["AMB-018", "AMB-019"],
        primary=upto(BASE, 17) + [bar(18, 20008, 20014, 19984, 20012)],
        expected=exp([lin([["SWEPT", 15], ["RECLAIMED", 16], ["DISPLACED", 17], ["EXPIRED", 18]], "EXPIRED", "GP_EXPIRED_NO_ZONE")])))
    fx.append(setup_fixture("GF-012", "No retest of the zone on bars 19..30", ["GP-REQ-090", "GP-REQ-091"], ["AMB-020"],
        primary=upto(BASE, 18) + [bar(i, 20012, 20018, 20004, 20012) for i in range(19, 31)],
        expected=exp([lin([["SWEPT", 15], ["RECLAIMED", 16], ["DISPLACED", 17], ["EXPIRED", 30]], "EXPIRED", "GP_EXPIRED_RETEST_WINDOW")])))
    fx.append(setup_fixture("GF-013", "Bar touching the zone closes below its bottom: mitigated before it can count as a retest", ["GP-REQ-113", "GP-REQ-006"], ["AMB-021"],
        primary=upto(BASE, 20) + [bar(21, 19996, 19998, 19980, 19982)],
        expected=exp([lin([["SWEPT", 15], ["RECLAIMED", 16], ["DISPLACED", 17], ["INVALIDATED", 21]], "INVALIDATED", "GP_INVALID_ZONE_MITIGATED")])))
    fx.append(setup_fixture("GF-014", "Low below the frozen sweep extreme after reclaim", ["GP-REQ-112", "GP-REQ-065"], [],
        primary=upto(BASE, 16) + [bar(17, 19983, 19985, 19975, 19978)],
        expected=exp([lin([["SWEPT", 15], ["RECLAIMED", 16], ["INVALIDATED", 17]], "INVALIDATED", "GP_INVALID_SWEEP_EXTREME_BREACHED")])))
    fx.append(setup_fixture("GF-015", "No bullish close above the zone top within 3 bars of the retest", ["GP-REQ-101", "GP-REQ-102"], ["AMB-022"],
        primary=upto(BASE, 21) + [bar(22, 19992, 19994, 19988, 19991), bar(23, 19991, 19993, 19986, 19989)],
        expected=exp([lin([["SWEPT", 15], ["RECLAIMED", 16], ["DISPLACED", 17], ["RETESTED", 21], ["EXPIRED", 23]],
                          "EXPIRED", "GP_EXPIRED_CONFIRMATION_WINDOW")])))

    smt_cov = ["GP-REQ-123", "GP-REQ-124"]
    fx.append(setup_fixture("GF-016", "SMT DENIED: NQ also breaks its reference (79895 < 79900)", smt_cov, ["AMB-026"],
        pair=replace(PAIR, bar(15, 79996, 79998, 79895, 79920)),
        expected=exp([blocked_at_22("SMT_BLOCK_DENIED", {"smt": {"state": "DENIED", "paired_ref": 79900, "paired_extreme": 79895}}, smt_ok=False)])))
    fx.append(setup_fixture("GF-017", "SMT UNCLEAR: NQ holds by 1 tick, margin is 2", smt_cov, ["AMB-026"],
        pair=replace(PAIR, bar(15, 79996, 79998, 79901, 79920)),
        expected=exp([blocked_at_22("SMT_BLOCK_UNCLEAR", {"smt": {"state": "UNCLEAR", "paired_ref": 79900, "paired_extreme": 79901}}, smt_ok=False)])))
    fx.append(setup_fixture("GF-018", "SMT MISALIGNED: NQ bars on a grid offset by 60 s", smt_cov, ["AMB-026"],
        pair=[dict(b, start_offset_s=60) for b in PAIR],
        expected=exp([blocked_at_22("SMT_BLOCK_MISALIGNED", smt_ok=False)])))
    fx.append(setup_fixture("GF-019", "SMT STALE: NQ bar 22 available 120 s after close, wait limit 30 s", smt_cov + ["GP-REQ-121"], ["AMB-026"],
        pair=replace(PAIR, dict(PAIR[22], delay_s=120)),
        expected=exp([blocked_at_22("SMT_BLOCK_STALE", smt_ok=False)])))
    fx.append(setup_fixture("GF-020", "SMT UNAVAILABLE: no paired PRIOR_RTH_LOW reference", smt_cov + ["GP-REQ-122"], ["AMB-024"],
        liquidity=[LIQ_L, LIQ_H],
        expected=exp([blocked_at_22("SMT_BLOCK_UNAVAILABLE", smt_ok=False)])))
    gc_l = dict(LIQ_L, liquidity_id="GC:PRIOR_RTH_LOW:2026-07-13", instrument_root="GC")
    gc_h = dict(LIQ_H, liquidity_id="GC:PRIOR_RTH_HIGH:2026-07-13", instrument_root="GC")
    fx.append(setup_fixture("GF-021", "GC is not an authorized instrument (no specified SMT pair)", ["GP-REQ-010", "GP-REQ-120"], ["AMB-023"],
        instrument="GC", contract="GCQ6", pair_instrument=None, liquidity=[gc_l, gc_h],
        expected={"lineages": [], "rejections": [rej(15, "GP_BLOCK_INSTRUMENT_NOT_AUTHORIZED", gc_l["liquidity_id"])],
                  "liquidity_final": {gc_l["liquidity_id"]: "CONSUMED", gc_h["liquidity_id"]: "ACTIVE"}}))
    near_h = dict(LIQ_H, level=20059)
    fx.append(setup_fixture("GF-022", "Nearest target 20058 gives net R 283/142 < 2 after costs (gross 57/27 would pass)", ["GP-REQ-143", "GP-REQ-144", "GP-REQ-142"], ["AMB-028", "AMB-030"],
        liquidity=[LIQ_L, near_h, LIQ_NQ_L],
        # reward = 57*1250 - 500 = 70750; risk = 35500; 70750/35500 = 283/142
        expected=exp([blocked_at_22("GP_BLOCK_R_BELOW_MIN", {"entry_limit": 20001, "stop": 19974, "target": 20058, "net_r": "283/142"})])))
    fx.append(setup_fixture("GF-023", "No buy-side liquidity above entry: no target", ["GP-REQ-142"], ["AMB-028"],
        liquidity=[LIQ_L, LIQ_NQ_L],
        expected={"lineages": [blocked_at_22("GP_BLOCK_NO_TARGET")], "rejections": [], "liquidity_final": {L_ID: "CONSUMED"}}))
    fx.append(setup_fixture("GF-024", "Sweep bar starts 15:00 ET, outside the 09:35-15:00 setup window", ["GP-REQ-010", "GP-REQ-011", "GP-REQ-012"], ["AMB-002"],
        bar0="2026-07-14T17:45:00Z",
        expected=exp(rejections=[rej(15, "GP_WAIT_OUTSIDE_SETUP_WINDOW")])))
    fx.append(setup_fixture("GF-025", "Sweep bar inside a +/-10 min news blackout (event 09:40 ET)", ["GP-REQ-010"], ["AMB-004"],
        news=[{"name": "FIXTURE_EVENT", "time_utc": "2026-07-14T13:40:00Z"}],
        expected=exp(rejections=[rej(15, "GP_BLOCK_NEWS_BLACKOUT")])))
    fx.append(setup_fixture("GF-026", "News calendar missing (not empty): every setup is blocked", ["GP-REQ-014", "GP-REQ-010"], ["AMB-004"],
        news_missing=True, expected=exp(rejections=[rej(15, "GP_BLOCK_NEWS_CALENDAR_MISSING")])))
    fx.append(setup_fixture("GF-027", "Roll date is the next session (within 2): blocked", ["GP-REQ-013"], ["AMB-005", "AMB-031"],
        roll={"ESU6": {"roll_date": "2026-07-15"}}, expected=exp(rejections=[rej(15, "GP_BLOCK_ROLL_WINDOW")])))
    fx.append(setup_fixture("GF-028", "Roll metadata missing for the contract", ["GP-REQ-010"], ["AMB-005"],
        roll={}, expected=exp(rejections=[rej(15, "GP_BLOCK_ROLL_METADATA_MISSING")])))
    fx.append(setup_fixture("GF-029", "Primary bar 17 missing: feed GAPPED at bar 18, lineage blocked for good", ["GP-REQ-111"], ["AMB-033"],
        primary=upto(BASE, 16) + [b for b in BASE if b["i"] >= 18],
        expected=exp([lin([["SWEPT", 15], ["RECLAIMED", 16], ["BLOCKED", 18]], "BLOCKED", "DQ_BLOCK_PRIMARY_GAPPED")])))
    fx.append(setup_fixture("GF-030", "Bar 17 arrives for a different contract (ESZ6)", ["GP-REQ-110"], [],
        primary=replace(upto(BASE, 17), dict(BASE[17], contract_id="ESZ6")),
        expected=exp([lin([["SWEPT", 15], ["RECLAIMED", 16], ["INVALIDATED", 17]], "INVALIDATED", "GP_INVALID_CONTRACT_CHANGED")])))
    fx.append(setup_fixture("GF-031", "Only 10 bars precede the sweep; ATR(14) undefined", ["GP-REQ-010", "GP-REQ-021"], ["AMB-010"],
        primary=[b for b in BASE if b["i"] >= 5], pair=[b for b in PAIR if b["i"] >= 5],
        expected=exp(rejections=[rej(15, "GP_WAIT_INSUFFICIENT_HISTORY")])))
    fx.append(setup_fixture("GF-032", "No bar for 601 s after bar 18 (staleness limit 600 s)", ["GP-REQ-111"], ["AMB-033"],
        primary=upto(BASE, 18), pair=upto(PAIR, 18), ticks=[{"k": 0, "after_bar": 18, "now_offset_s": 601}],
        expected=exp([lin([["SWEPT", 15], ["RECLAIMED", 16], ["DISPLACED", 17], ["BLOCKED", "tick:0"]], "BLOCKED", "DQ_BLOCK_PRIMARY_STALE")])))
    fx.append(setup_fixture("GF-033", "Bar 17 redelivered with a different close: feed UNKNOWN", ["GP-REQ-111"], ["AMB-033"],
        primary=upto(BASE, 17) + [bar(17, 19983, 20010, 19982, 20007, delay_s=5)],
        expected=exp([lin([["SWEPT", 15], ["RECLAIMED", 16], ["DISPLACED", 17], ["BLOCKED", "dup:17"]], "BLOCKED", "DQ_BLOCK_PRIMARY_UNKNOWN")])))
    identity = {"spec_version": SPEC_VERSION, "instrument_root": "ES", "contract_id": "ESU6", "direction": "LONG",
                "setup_family": "GP_REVERSAL", "liquidity_id": L_ID, "sweep_bar_start_ns": bar_start_ns(BAR0_DEFAULT, 15),
                "session_id": "ES:RTH:2026-07-14"}
    fx.append(setup_fixture("GF-034", "Lineage already attempted (e.g. before a restart): one attempt only", ["GP-REQ-130", "GP-REQ-131"], ["AMB-032"],
        store=[{"identity": identity, "attempt_count": 1}],
        expected=exp([blocked_at_22("GP_BLOCK_ONE_ATTEMPT_USED")])))
    fx.append(setup_fixture("GF-035", "Setup still open when bar 20 starts at 15:00 ET: expired at session end", ["GP-REQ-016"], ["AMB-037"],
        bar0="2026-07-14T17:20:00Z", primary=upto(BASE, 20), pair=upto(PAIR, 20),
        expected=exp([lin([["SWEPT", 15], ["RECLAIMED", 16], ["DISPLACED", 17], ["EXPIRED", 20]], "EXPIRED", "GP_EXPIRED_SESSION_END")])))
    late_l = dict(LIQ_L, available_at_utc="2026-07-14T13:40:01Z")  # bar 15 close + 1 s
    fx.append(setup_fixture("GF-036", "Liquidity object not yet available when bar 15 starts: bar 15 cannot sweep it", ["GP-REQ-003"], ["AMB-007"],
        primary=upto(BASE, 15) + [bar(16, 19982, 19986, 19981, 19985)], liquidity=[late_l, LIQ_H, LIQ_NQ_L],
        expected=exp(liquidity_final={L_ID: "ACTIVE", H_ID: "ACTIVE"})))
    fx.append(setup_fixture("GF-037", "Lineage store unavailable: fail closed", ["GP-REQ-132"], ["AMB-032"],
        store_missing=True, expected=exp([blocked_at_22("GP_BLOCK_LINEAGE_STORE_UNAVAILABLE")])))
    fx.append(setup_fixture("GF-038", "News blackout (event 10:00 ET) begins at bar 18 while the lineage is open", ["GP-REQ-015"], ["AMB-004"],
        news=[{"name": "FIXTURE_EVENT", "time_utc": "2026-07-14T14:00:00Z"}],
        expected=exp([lin([["SWEPT", 15], ["RECLAIMED", 16], ["DISPLACED", 17], ["BLOCKED", 18]], "BLOCKED", "GP_BLOCK_NEWS_BLACKOUT")])))
    on_id = "ES:OVERNIGHT_LOW:2026-07-14"
    on_l = {"liquidity_id": on_id, "instrument_root": "ES", "type": "OVERNIGHT_LOW", "side": "SELL_SIDE",
            "level": 19982, "session_date": "2026-07-14", "available_at_utc": "2026-07-14T13:30:01Z"}
    fx.append(setup_fixture("GF-039", "One bar sweeps PRIOR_RTH_LOW and OVERNIGHT_LOW: one lineage, keyed to PRIOR_RTH_LOW", ["GP-REQ-053"], ["AMB-011"],
        liquidity=[LIQ_L, on_l, LIQ_H, LIQ_NQ_L],
        expected={"lineages": [lin(HAPPY_TRANSITIONS, "STRATEGY_AUTHORIZED", "GP_AUTHORIZED", HAPPY_EVIDENCE)], "rejections": [],
                  "liquidity_final": {L_ID: "CONSUMED", on_id: "CONSUMED", H_ID: "ACTIVE"}}))
    return fx


def build_liquidity():
    bar0 = "2026-07-14T13:30:00Z"  # 09:30 ET, so the swing forms in the regular session
    common = {"module": "liquidity", "spec_version": SPEC_VERSION, "instrument": "ES", "contract_id": "ESU6",
              "time_base": {"bar0_start_utc": bar0, "timeframe_s": TF, "default_delay_s": 1}}
    sid = f"ES:SWING_K_LOW:{bar_start_ns(bar0, 10)}"
    expected = {"swings": [{"type": "SWING_LOW", "pivot_bar": 10, "level": 19990, "available_bar": 13}],
                "liquidity_created": [{"liquidity_id": sid, "type": "SWING_K_LOW", "side": "SELL_SIDE", "level": 19990, "available_bar": 13}]}
    l01 = dict(common, fixture_id="GF-L01", title="Swing low k=3: available at the close of the 3rd confirming bar",
               covers=["GP-REQ-030", "GP-REQ-031", "GP-REQ-041"], ambiguities=["AMB-006"],
               primary_bars=replace(WARM, bar(10, 20000, 20004, 19990, 20000)), expected=expected)
    l02 = dict(common, fixture_id="GF-L02", title="Equal lows on bars 10 and 11: the earliest is the pivot",
               covers=["GP-REQ-030"], ambiguities=["AMB-006"],
               primary_bars=replace(WARM, bar(10, 20000, 20004, 19990, 20000), bar(11, 20000, 20004, 19990, 20000)),
               expected=expected)
    return [l01, l02]


def dump(obj) -> bytes:
    return (json.dumps(obj, indent=1, sort_keys=True) + "\n").encode()


def main() -> None:
    fixtures = build_setup() + build_liquidity()
    for old in HERE.glob("GF-*.json"):
        old.unlink()
    manifest = []
    for f in fixtures:
        data = dump(f)
        (HERE / f"{f['fixture_id']}.json").write_bytes(data)
        manifest.append(f"{hashlib.sha256(data).hexdigest()}  {f['fixture_id']}.json")
    (HERE / "MANIFEST.sha256").write_text("\n".join(manifest) + "\n")

    spec_text = (SPEC / "GP_SPEC.md").read_text()
    reqs = []
    for m in re.finditer(r"\*\*(GP-REQ-\d{3})\*\*\s*(.*)", spec_text):
        summary = re.sub(r"[`*]", "", m.group(2)).strip()
        reqs.append((m.group(1), summary[:140]))
    cover = {}
    for f in fixtures:
        for r in f["covers"]:
            cover.setdefault(r, []).append(f["fixture_id"])
    with open(SPEC / "GP_REQUIREMENTS_TRACE.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["req_id", "summary", "golden_fixtures", "implementation", "status"])
        for rid, summary in reqs:
            fxs = " ".join(cover.get(rid, []))
            w.writerow([rid, summary, fxs, "NOT IMPLEMENTED (Phase 3)",
                        "FIXTURE_WRITTEN" if fxs else "NO_FIXTURE_YET"])
    print(f"{len(fixtures)} fixtures, {len(reqs)} requirements")


if __name__ == "__main__":
    main()
