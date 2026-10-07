"""Shared loaders for the gp-1.0.0-draft.1 spec artifacts (test-only helpers)."""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

import yaml

from qe.core.events import BarClosed

REPO = Path(__file__).resolve().parents[3]
SPEC = REPO / "qe/spec"
FIXTURES = SPEC / "fixtures"


def load_fixtures() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(FIXTURES.glob("GF-*.json"))]


def reason_codes() -> dict:
    return yaml.safe_load((SPEC / "REASON_CODES.yaml").read_text())["codes"]


def params() -> dict:
    return json.loads((SPEC / "params/gp-1.0.0-draft.1.json").read_text())


def spec_text() -> str:
    return (SPEC / "GP_SPEC.md").read_text()


def spec_req_ids() -> list[str]:
    return re.findall(r"\*\*(GP-REQ-\d{3})\*\*", spec_text())


def ambiguities() -> list[dict]:
    with open(SPEC / "AMBIGUITY_REGISTER.csv", newline="") as fh:
        return list(csv.DictReader(fh))


def trace_rows() -> list[dict]:
    with open(SPEC / "GP_REQUIREMENTS_TRACE.csv", newline="") as fh:
        return list(csv.DictReader(fh))


def utc_ns(s: str) -> int:
    dt = datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp()) * 1_000_000_000


def expand(fixture: dict, bars: list[dict], root: str, contract: str) -> list[BarClosed]:
    """Turn compact fixture bars into validated BarClosed events, in arrival order."""
    tb = fixture["time_base"]
    t0, tf = utc_ns(tb["bar0_start_utc"]), tb["timeframe_s"]
    out = []
    for seq, b in enumerate(bars):
        start = t0 + b["i"] * tf * 1_000_000_000 + b.get("start_offset_s", 0) * 1_000_000_000
        close = start + tf * 1_000_000_000
        avail = close + b.get("delay_s", tb["default_delay_s"]) * 1_000_000_000
        out.append(BarClosed(provider="FIXTURE", instrument_root=root, contract_id=b.get("contract_id", contract),
                             timeframe_s=tf, bar_start_ns=start, event_time_ns=close, receive_time_ns=avail,
                             available_at_ns=avail, open=b["o"], high=b["h"], low=b["l"], close=b["c"],
                             volume=1, provider_sequence=seq))
    return out


def ratio(s: str) -> Fraction:
    n, d = s.split("/")
    return Fraction(int(n), int(d))


def all_reason_codes_used(fixture: dict) -> set[str]:
    exp = fixture["expected"]
    used = {r["reason_code"] for r in exp.get("rejections", [])}
    used |= {lin["reason_code"] for lin in exp.get("lineages", []) if lin["reason_code"]}
    return used


def outcomes_match(expected: dict, actual: dict) -> list[str]:
    """Compare a reducer result to a fixture's expectation (exhaustive lists, subset evidence)."""
    problems = []

    def subset(exp, act, path):
        if isinstance(exp, dict):
            if not isinstance(act, dict):
                problems.append(f"{path}: expected mapping, got {act!r}")
                return
            for k, v in exp.items():
                if k not in act:
                    problems.append(f"{path}.{k}: missing")
                else:
                    subset(v, act[k], f"{path}.{k}")
        elif isinstance(exp, str) and re.fullmatch(r"-?\d+/\d+", exp):
            if ratio(exp) != (act if isinstance(act, Fraction) else ratio(str(act))):
                problems.append(f"{path}: expected {exp}, got {act}")
        elif exp != act:
            problems.append(f"{path}: expected {exp!r}, got {act!r}")

    for key in ("rejections", "liquidity_final", "swings", "liquidity_created"):
        if key in expected and expected[key] != actual.get(key):
            problems.append(f"{key}: expected {expected[key]!r}, got {actual.get(key)!r}")
    if "lineages" in expected:
        exp_l, act_l = expected["lineages"], actual.get("lineages", [])
        if len(exp_l) != len(act_l):
            problems.append(f"lineages: expected {len(exp_l)}, got {len(act_l)}")
        for n, (e, a) in enumerate(zip(exp_l, act_l)):
            for k in ("direction", "liquidity_id", "transitions", "final_state", "reason_code"):
                if e[k] != a.get(k):
                    problems.append(f"lineages[{n}].{k}: expected {e[k]!r}, got {a.get(k)!r}")
            subset(e["evidence"], a.get("evidence", {}), f"lineages[{n}].evidence")
    return problems
