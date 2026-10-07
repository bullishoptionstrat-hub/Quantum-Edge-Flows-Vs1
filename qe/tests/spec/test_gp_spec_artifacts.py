"""Consistency of the gp-1.0.0-draft.1 spec artifacts (Phase 2).

These pass now. They check that the spec, parameters, reason codes, ambiguity
register, trace matrix and golden fixtures agree with each other. They also
re-derive the fixtures' hand-computed numbers with qe/core primitives, so an
arithmetic slip by the fixture author shows up before Phase 3 trusts the fixture.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, timedelta
from fractions import Fraction
from zoneinfo import ZoneInfo

import pytest

from qe.core.data_quality import FeedHealth, FeedPolicy, FeedState, step
from qe.core.instruments import CostModel, Side, net_r, parse_registry
from qe.tests.spec._fixtures import (
    FIXTURES, REPO, all_reason_codes_used, ambiguities, expand, load_fixtures, params, ratio,
    reason_codes, spec_req_ids, spec_text, trace_rows,
)

FX = {f["fixture_id"]: f for f in load_fixtures()}
P = params()
G = P["global"]
REG = parse_registry(json.loads((REPO / "qe/config/instruments.json").read_text()))
NS = 1_000_000_000


# ------------------------------------------------------------------ cross-artifact consistency

def test_requirement_ids_unique_and_traced():
    ids = spec_req_ids()
    assert len(ids) == len(set(ids)), "duplicate GP-REQ ids in GP_SPEC.md"
    assert [r["req_id"] for r in trace_rows()] == ids, "trace matrix out of sync; rerun build_fixtures.py"
    for row in trace_rows():
        assert row["status"] == ("FIXTURE_WRITTEN" if row["golden_fixtures"] else "NO_FIXTURE_YET")


def test_fixture_covers_and_ambiguities_exist():
    ids = set(spec_req_ids())
    amb = {a["amb_id"] for a in ambiguities()}
    for f in FX.values():
        assert f["covers"], f["fixture_id"]
        assert set(f["covers"]) <= ids, (f["fixture_id"], set(f["covers"]) - ids)
        assert set(f["ambiguities"]) <= amb, (f["fixture_id"], set(f["ambiguities"]) - amb)
        assert f["spec_version"] == P["spec_version"]


def test_every_reason_code_is_produced_by_a_fixture_and_none_is_invented():
    codes = set(reason_codes())
    used = set().union(*(all_reason_codes_used(f) for f in FX.values() if f["module"] == "setup"))
    assert used <= codes, used - codes
    assert codes <= used, f"reason codes with no golden fixture (directive D5): {sorted(codes - used)}"


def test_reason_codes_cite_real_requirements():
    ids = set(spec_req_ids())
    for code, meta in reason_codes().items():
        assert re.fullmatch(r"(GP|SMT|DQ)_[A-Z_]+", code), code
        for req in meta["spec"].split():
            assert req in ids, (code, req)


def _param_names() -> set[str]:
    names = set(G)
    for inst in P["per_instrument"].values():
        names |= set(inst)
    return names


def test_every_parameter_named_in_spec_exists():
    names = _param_names()
    cited = set(re.findall(r"(?<![A-Za-z])P-[A-Z0-9]+(?:-[A-Z0-9]+)*", spec_text()))
    families = {"P-COST", "P-DQ"}  # written as P-COST-* / P-DQ-* in prose
    missing = {c for c in cited if c not in names and c not in families}
    assert not missing, missing
    for fam in families:
        assert any(n.startswith(fam + "-") for n in names), fam


def test_ambiguity_register_is_well_formed():
    rows = ambiguities()
    ids = [r["amb_id"] for r in rows]
    assert ids == [f"AMB-{n:03d}" for n in range(1, len(rows) + 1)]
    names = _param_names()
    for r in rows:
        assert r["status"] in {"PROPOSED", "APPROVED", "REJECTED"}, r["amb_id"]
        for col in ("question", "candidates", "consequences", "recommendation"):
            assert r[col].strip(), (r["amb_id"], col)
        for gf in re.findall(r"GF-(?:L)?\d+", r["distinguishing_tests"]):
            if "…" not in gf:
                assert gf in FX, (r["amb_id"], gf)
        for p in [x.strip() for x in r["params"].split(",")]:
            if p in {"-", ""}:
                continue
            assert p in names or (p.endswith("*") and any(n.startswith(p[:-1]) for n in names)), (r["amb_id"], p)


def test_no_unquantified_words_in_normative_spec():
    """Directive Phase 2: 'strong', 'clean', 'obvious', 'institutional' are illegal in the spec."""
    text = spec_text().lower()
    normative = text.split("## 19. excluded")[0]
    for line in normative.splitlines():
        if "have no meaning here" in line:  # GP-REQ-102 names the words in order to ban them
            continue
        for word in ("strong", "clean", "obvious", "institutional", "significant", "major swing"):
            assert not re.search(rf"\b{word}\b", line), (word, line)


def test_manifest_matches_fixtures():
    lines = (REPO / "qe/spec/fixtures/MANIFEST.sha256").read_text().split("\n")
    listed = {}
    for ln in filter(None, lines):
        digest, name = ln.split("  ")
        listed[name] = digest
    files = {p.name: p for p in (REPO / "qe/spec/fixtures").glob("GF-*.json")}
    assert set(listed) == set(files)
    for name, p in files.items():
        assert hashlib.sha256(p.read_bytes()).hexdigest() == listed[name], f"{name} changed without a manifest update"


@pytest.mark.parametrize("fid", sorted(FX))
def test_fixture_bars_are_valid_events(fid):
    f = FX[fid]
    feeds = [("primary_bars", f["instrument"], f["contract_id"])]
    if f.get("pair"):
        feeds.append(("pair_bars", f["pair"]["instrument"], f["pair"]["contract_id"]))
    for key, root, contract in feeds:
        events = expand(f, f.get(key, []), root, contract)  # raises InvalidEvent on bad OHLC / timing
        seen = set()
        last = -1
        for b, ev in zip(f[key], events):
            if b["i"] in seen:  # redelivery, must be marked dup:<i> somewhere in the expectation
                assert f"dup:{b['i']}" in json.dumps(f["expected"]), (fid, b["i"])
                continue
            seen.add(b["i"])
            assert ev.bar_start_ns > last, (fid, key, b["i"])
            last = ev.bar_start_ns


# ------------------------------------------------------------------ independent arithmetic oracle

def _feed(f, key="primary_bars"):
    """Bars by index, first delivery only, in arrival order."""
    out, seen = [], set()
    for b in f[key]:
        if b["i"] not in seen:
            seen.add(b["i"])
            out.append(b)
    return out


def _atr(bars, i, n):
    prev = [b for b in bars if b["i"] < i][-n:]
    assert len(prev) == n
    total = Fraction(0)
    for b in prev:
        pos = bars.index(b)
        if pos == 0:
            total += b["h"] - b["l"]
        else:
            pc = bars[pos - 1]["c"]
            total += max(b["h"] - b["l"], abs(b["h"] - pc), abs(b["l"] - pc))
    return total / n


def _bar(bars, i):
    return next(b for b in bars if b["i"] == i)


def _costs(root):
    pi = P["per_instrument"][root]
    return CostModel(pi["P-COST-COMMISSION-RT-MINOR"], 0, pi["P-COST-STOP-SLIP-TICKS"], 0)


def test_gf001_numbers_follow_from_the_spec():
    f = FX["GF-001"]
    bars, ev = _feed(f), f["expected"]["lineages"][0]["evidence"]
    pi = P["per_instrument"]["ES"]
    level = next(o["level"] for o in f["liquidity"] if o["liquidity_id"] == f["expected"]["lineages"][0]["liquidity_id"])
    n = G["P-ATR-N"]

    s = ev["sweep_bar"]
    atr_s = _atr(bars, s, n)
    pen = level - _bar(bars, s)["l"]
    assert (ratio(ev["atr_sweep"]), ev["penetration_ticks"]) == (atr_s, pen)
    assert pi["P-SWEEP-MIN-PEN-TICKS"] <= pen <= ratio(G["P-SWEEP-MAX-PEN-ATR"]) * atr_s
    for i in range(s - 30, s):
        assert all(b["l"] > level for b in bars if b["i"] == i), "an earlier bar already swept the level"

    r = ev["reclaim_bar"]
    assert r - s < G["P-RECLAIM-MAX-BARS"]
    assert all(_bar(bars, j)["c"] < level + G["P-RECLAIM-MIN-TICKS"] for j in range(s, r))
    assert _bar(bars, r)["c"] >= level + G["P-RECLAIM-MIN-TICKS"]
    extreme = min(_bar(bars, j)["l"] for j in range(s, r + 1))
    assert extreme == ev["sweep_extreme"]

    d = ev["displacement_bar"]
    db = _bar(bars, d)
    rng, body = db["h"] - db["l"], db["c"] - db["o"]
    atr_d = _atr(bars, d, n)
    struct = max(b["h"] for b in bars if s - G["P-DISP-STRUCT-LOOKBACK"] <= b["i"] <= d - 1)
    m = ev["displacement"]
    assert (m["range"], m["body"], ratio(m["atr"]), m["structure_ref"]) == (rng, body, atr_d, struct)
    assert ratio(m["body_ratio"]) == Fraction(body, rng)
    assert ratio(m["close_location"]) == Fraction(db["c"] - db["l"], rng)
    assert rng >= ratio(G["P-DISP-RANGE-ATR"]) * atr_d
    assert Fraction(body, rng) >= ratio(G["P-DISP-BODY-RATIO"])
    assert Fraction(db["c"] - db["l"], rng) >= ratio(G["P-DISP-CLOSE-LOC"])
    assert db["c"] > struct
    for j in range(r, d):  # no earlier bar in the window qualified
        jb = _bar(bars, j)
        jr = jb["h"] - jb["l"]
        jstruct = max(b["h"] for b in bars if s - G["P-DISP-STRUCT-LOOKBACK"] <= b["i"] <= j - 1)
        qualifies = (jr > 0 and jr >= ratio(G["P-DISP-RANGE-ATR"]) * _atr(bars, j, n) and jb["c"] > jb["o"]
                     and Fraction(jb["c"] - jb["o"], jr) >= ratio(G["P-DISP-BODY-RATIO"])
                     and Fraction(jb["c"] - jb["l"], jr) >= ratio(G["P-DISP-CLOSE-LOC"]) and jb["c"] > jstruct)
        assert not qualifies, j

    zone = ev["zone"]
    assert (zone["bottom"], zone["top"], zone["formed_bar"]) == (_bar(bars, d - 1)["h"], _bar(bars, d + 1)["l"], d + 1)
    assert zone["top"] - zone["bottom"] >= pi["P-FVG-MIN-TICKS"]

    t = ev["retest_bar"]
    first = next(b["i"] for b in bars if b["i"] >= d + 2 and b["l"] <= zone["top"])
    assert t == first and t <= d + 1 + G["P-RETEST-MAX-BARS"]
    c = ev["confirmation_bar"]
    cands = [b["i"] for b in bars if t <= b["i"] <= t + G["P-CONF-MAX-BARS"] - 1 and b["c"] > zone["top"] and b["c"] > b["o"]]
    assert cands and cands[0] == c
    for b in bars:  # no invalidation before the decision
        if r < b["i"] <= c:
            assert b["l"] >= extreme
        if d + 2 <= b["i"] <= c:
            assert b["c"] >= zone["bottom"]

    entry = _bar(bars, c)["c"] + pi["P-ENTRY-LIMIT-OFFSET-TICKS"]
    stop = extreme - pi["P-STOP-BUFFER-TICKS"]
    fr = G["P-TARGET-FRONTRUN-TICKS"]
    tgt_liq = min((o for o in f["liquidity"] if o["side"] == "BUY_SIDE" and o["instrument_root"] == "ES"
                   and o["level"] > entry + fr), key=lambda o: o["level"])
    target = tgt_liq["level"] - fr
    assert (ev["entry_limit"], ev["stop"], ev["target"], ev["target_liquidity_id"]) == (entry, stop, target, tgt_liq["liquidity_id"])
    r_net = net_r(REG["ES"], Side.LONG, entry, stop, target, _costs("ES"))
    assert r_net == ratio(ev["net_r"]) and r_net >= ratio(G["P-MIN-NET-R"])

    pair = _feed(f, "pair_bars")
    ref = next(o["level"] for o in f["liquidity"] if o["instrument_root"] == "NQ")
    pmin = min(b["l"] for b in pair if s <= b["i"] <= r)
    margin = P["per_instrument"]["NQ"]["P-SMT-MARGIN-TICKS"]
    assert (ev["smt"]["paired_ref"], ev["smt"]["paired_extreme"]) == (ref, pmin)
    assert pmin >= ref + margin


def test_gf002_is_the_exact_mirror_of_gf001():
    a, b = FX["GF-001"], FX["GF-002"]
    for key, m in (("primary_bars", 40000), ("pair_bars", 160000)):
        for x, y in zip(a[key], b[key]):
            assert (y["o"], y["h"], y["l"], y["c"]) == (m - x["o"], m - x["l"], m - x["h"], m - x["c"])
    ea, eb = a["expected"]["lineages"][0], b["expected"]["lineages"][0]
    assert (ea["direction"], eb["direction"]) == ("LONG", "SHORT")
    assert ea["transitions"] == eb["transitions"] and ea["reason_code"] == eb["reason_code"]
    va, vb = ea["evidence"], eb["evidence"]
    for k in ("sweep_extreme", "entry_limit", "stop", "target"):
        assert vb[k] == 40000 - va[k], k
    assert (vb["zone"]["bottom"], vb["zone"]["top"]) == (40000 - va["zone"]["top"], 40000 - va["zone"]["bottom"])
    assert vb["net_r"] == va["net_r"]
    r_short = net_r(REG["ES"], Side.SHORT, vb["entry_limit"], vb["stop"], vb["target"], _costs("ES"))
    assert r_short == ratio(vb["net_r"])


def test_gf022_net_r_is_below_two_after_costs():
    ev = FX["GF-022"]["expected"]["lineages"][0]["evidence"]
    r = net_r(REG["ES"], Side.LONG, ev["entry_limit"], ev["stop"], ev["target"], _costs("ES"))
    assert r == ratio(ev["net_r"]) == Fraction(283, 142) and r < ratio(G["P-MIN-NET-R"])
    # gross R would pass: costs decide this fixture
    assert Fraction(ev["target"] - ev["entry_limit"], ev["entry_limit"] - ev["stop"]) >= 2


def test_gf005_penetration_exceeds_atr_and_gf003_gf004_do_not_sweep():
    lvl = 19980
    b5 = _feed(FX["GF-005"])
    assert lvl - _bar(b5, 15)["l"] > ratio(G["P-SWEEP-MAX-PEN-ATR"]) * _atr(b5, 15, G["P-ATR-N"])
    assert lvl - _bar(_feed(FX["GF-003"]), 15)["l"] == 0
    assert 0 < lvl - _bar(_feed(FX["GF-004"]), 15)["l"] < P["per_instrument"]["ES"]["P-SWEEP-MIN-PEN-TICKS"]


def test_gf010_candidate_fails_only_the_structure_gate():
    bars = _feed(FX["GF-010"])
    b = _bar(bars, 17)
    rng, body = b["h"] - b["l"], b["c"] - b["o"]
    struct = max(x["h"] for x in bars if 15 - G["P-DISP-STRUCT-LOOKBACK"] <= x["i"] <= 16)
    assert rng >= ratio(G["P-DISP-RANGE-ATR"]) * _atr(bars, 17, G["P-ATR-N"])
    assert Fraction(body, rng) >= ratio(G["P-DISP-BODY-RATIO"])
    assert Fraction(b["c"] - b["l"], rng) >= ratio(G["P-DISP-CLOSE-LOC"])
    assert b["c"] <= struct == 20004
    cand = FX["GF-010"]["expected"]["lineages"][0]["evidence"]["displacement_candidates"]["17"]
    assert (cand["range"], cand["body"], cand["structure_ref"]) == (rng, body, struct)


@pytest.mark.parametrize("fid,state", [("GF-016", "DENIED"), ("GF-017", "UNCLEAR")])
def test_smt_window_arithmetic(fid, state):
    f = FX[fid]
    pmin = min(b["l"] for b in _feed(f, "pair_bars") if 15 <= b["i"] <= 16)
    ref, margin = 79900, P["per_instrument"]["NQ"]["P-SMT-MARGIN-TICKS"]
    got = "DENIED" if pmin < ref else "UNCLEAR" if pmin < ref + margin else "CONFIRMED"
    assert got == state == f["expected"]["lineages"][0]["evidence"]["smt"]["state"]
    assert f["expected"]["lineages"][0]["evidence"]["smt"]["paired_extreme"] == pmin


def _local_start(f, i):
    ev = expand(f, [b for b in f["primary_bars"] if b["i"] == i][:1], f["instrument"], f["contract_id"])[0]
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ev.bar_start_ns // NS, tz=timezone.utc).astimezone(ZoneInfo(G["P-SESSION-TZ"]))


def _in_window(f, i):
    lt = _local_start(f, i).strftime("%H:%M")
    start, end = G["P-SETUP-WINDOW"]
    return start <= lt < end


def test_session_window_fixtures():
    assert _in_window(FX["GF-001"], 15) and _local_start(FX["GF-001"], 15).strftime("%H:%M") == "09:35"
    assert not _in_window(FX["GF-024"], 15)
    f35 = FX["GF-035"]
    assert _in_window(f35, 19) and not _in_window(f35, 20) and _local_start(f35, 20).strftime("%H:%M") == "15:00"


def _blackout_hits(f, i):
    ev = expand(f, [b for b in f["primary_bars"] if b["i"] == i][:1], f["instrument"], f["contract_id"])[0]
    from qe.tests.spec._fixtures import utc_ns
    w = G["P-NEWS-BLACKOUT-MIN"] * 60 * NS
    return any(ev.bar_start_ns <= utc_ns(e["time_utc"]) + w and utc_ns(e["time_utc"]) - w < ev.event_time_ns
               for e in f["news_calendar"])


def test_news_blackout_fixtures():
    assert _blackout_hits(FX["GF-025"], 15)
    f38 = FX["GF-038"]
    assert [i for i in (15, 16, 17, 18) if _blackout_hits(f38, i)] == [18]
    assert FX["GF-026"]["news_calendar"] is None and FX["GF-001"]["news_calendar"] == []


def test_roll_fixture_counts_weekday_sessions():
    session, n = date(2026, 7, 14), G["P-ROLL-BLACKOUT-SESSIONS"]
    nxt, d = [], session
    while len(nxt) < n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            nxt.append(d.isoformat())
    assert FX["GF-027"]["roll_metadata"]["ESU6"]["roll_date"] in nxt
    assert FX["GF-001"]["roll_metadata"]["ESU6"]["roll_date"] not in nxt
    assert FX["GF-028"]["roll_metadata"] == {}


def test_insufficient_history_fixture():
    bars = _feed(FX["GF-031"])
    assert len([b for b in bars if b["i"] < 15]) < G["P-ATR-N"]


def _health_after(f, key="primary_bars", until=None):
    root = f["instrument"] if key == "primary_bars" else f["pair"]["instrument"]
    contract = f["contract_id"] if key == "primary_bars" else f["pair"]["contract_id"]
    pol = FeedPolicy(root, f["time_base"]["timeframe_s"], G["P-DQ-MAX-STALENESS-S"] * NS, G["P-DQ-RECOVERY-BARS"])
    st = FeedState()
    trail = []
    for b, ev in zip(f[key], expand(f, f[key], root, contract)):
        st, verdict = step(st, ev, pol)
        trail.append((b["i"], verdict.health))
    return trail


def test_dq_fixtures_drive_the_core_gate_as_described():
    gap = dict(_health_after(FX["GF-029"]))
    assert gap[16] is FeedHealth.HEALTHY and gap[18] is FeedHealth.GAPPED
    dup = _health_after(FX["GF-033"])
    assert dup[-1][0] == 17 and dup[-1][1] is FeedHealth.UNKNOWN
    happy = _health_after(FX["GF-001"])
    assert all(h is FeedHealth.HEALTHY for i, h in happy if i >= 3)
    misaligned_pair = _health_after(FX["GF-018"], "pair_bars")
    assert all(h is FeedHealth.HEALTHY for i, h in misaligned_pair if i >= 3), "pair grid offset must not look like a DQ fault"


def test_fixture_count():
    assert len(FX) == len(list(FIXTURES.glob("GF-*.json"))) >= 40
