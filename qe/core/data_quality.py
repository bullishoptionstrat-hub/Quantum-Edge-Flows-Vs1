"""Data-quality authority for closed-bar feeds (directive D8, INV-09, INV-11).

A pure step function checks each incoming bar against the feed's last known
state and returns a verdict with a closed reason code. It runs upstream of any
strategy logic. Fail-closed rules:

  - no data yet            -> UNKNOWN (not tradeable, INV-11)
  - duplicate bar          -> rejected, state unchanged (idempotent)
  - same bar, new content  -> rejected, state UNKNOWN (a correction needs its
                              own event type, INV-07; until then we trust nothing)
  - older bar              -> rejected (out of order)
  - missing bars           -> accepted, state GAPPED, unless the injected
                              session-break rule says the hole is a known closure
  - contract changed       -> accepted, state UNKNOWN (roll uncertainty)
  - silence past the limit -> STALE (checked with health_at)

Leaving GAPPED/UNKNOWN requires `recovery_bars` consecutive clean bars. Numeric
thresholds are policy (A2) and have no defaults here.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Callable

from qe.core.events import BarClosed
from qe.core.serialization import sha256_hex


class FeedHealth(Enum):
    HEALTHY = "HEALTHY"
    GAPPED = "GAPPED"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class DQReason(Enum):
    DQ_OK = "DQ_OK"
    DQ_WRONG_FEED = "DQ_WRONG_FEED"
    DQ_DUPLICATE = "DQ_DUPLICATE"
    DQ_CONFLICTING_DUPLICATE = "DQ_CONFLICTING_DUPLICATE"
    DQ_OUT_OF_ORDER = "DQ_OUT_OF_ORDER"
    DQ_GAP = "DQ_GAP"
    DQ_CONTRACT_CHANGED = "DQ_CONTRACT_CHANGED"
    DQ_RECOVERING = "DQ_RECOVERING"


# (previous bar close ns, next bar start ns) -> True if the hole is an expected closure.
SessionBreakRule = Callable[[int, int], bool]


@dataclass(frozen=True)
class FeedPolicy:
    instrument_root: str
    timeframe_s: int
    max_staleness_ns: int
    recovery_bars: int
    is_session_break: SessionBreakRule | None = None  # None: every hole is a gap (fail closed)

    def __post_init__(self) -> None:
        if self.timeframe_s <= 0 or self.max_staleness_ns <= 0 or self.recovery_bars < 1:
            raise ValueError("timeframe_s, max_staleness_ns must be > 0 and recovery_bars >= 1")


@dataclass(frozen=True)
class FeedState:
    health: FeedHealth = FeedHealth.UNKNOWN
    last_bar_start_ns: int | None = None
    last_bar_hash: str | None = None
    last_available_at_ns: int | None = None
    contract_id: str | None = None
    clean_streak: int = 0


@dataclass(frozen=True)
class Verdict:
    accepted: bool
    reason: DQReason
    health: FeedHealth

    def to_canonical(self) -> dict:
        return {"accepted": self.accepted, "reason": self.reason, "health": self.health}


def step(state: FeedState, bar: BarClosed, policy: FeedPolicy) -> tuple[FeedState, Verdict]:
    if bar.instrument_root != policy.instrument_root or bar.timeframe_s != policy.timeframe_s:
        return state, Verdict(False, DQReason.DQ_WRONG_FEED, state.health)

    bar_hash = sha256_hex(bar)
    last = state.last_bar_start_ns

    if last is not None and bar.bar_start_ns == last:
        if bar_hash == state.last_bar_hash:
            return state, Verdict(False, DQReason.DQ_DUPLICATE, state.health)
        new = replace(state, health=FeedHealth.UNKNOWN, clean_streak=0)
        return new, Verdict(False, DQReason.DQ_CONFLICTING_DUPLICATE, new.health)

    if last is not None and bar.bar_start_ns < last:
        return state, Verdict(False, DQReason.DQ_OUT_OF_ORDER, state.health)

    base = replace(state, last_bar_start_ns=bar.bar_start_ns, last_bar_hash=bar_hash,
                   last_available_at_ns=bar.available_at_ns, contract_id=bar.contract_id)

    if state.contract_id is not None and bar.contract_id != state.contract_id:
        new = replace(base, health=FeedHealth.UNKNOWN, clean_streak=0)
        return new, Verdict(True, DQReason.DQ_CONTRACT_CHANGED, new.health)

    tf_ns = policy.timeframe_s * 1_000_000_000
    if last is not None and bar.bar_start_ns != last + tf_ns:
        prev_close = last + tf_ns
        expected = policy.is_session_break is not None and policy.is_session_break(prev_close, bar.bar_start_ns)
        if not expected:
            new = replace(base, health=FeedHealth.GAPPED, clean_streak=0)
            return new, Verdict(True, DQReason.DQ_GAP, new.health)

    streak = state.clean_streak + 1
    if state.health is FeedHealth.HEALTHY or streak >= policy.recovery_bars:
        new = replace(base, health=FeedHealth.HEALTHY, clean_streak=streak)
        return new, Verdict(True, DQReason.DQ_OK, new.health)
    new = replace(base, clean_streak=streak)  # still GAPPED/UNKNOWN/STALE until recovered
    return new, Verdict(True, DQReason.DQ_RECOVERING, new.health)


def health_at(state: FeedState, now_ns: int, policy: FeedPolicy) -> FeedHealth:
    """Health as of `now_ns`; silence beyond max_staleness_ns makes a healthy feed STALE."""
    if state.last_available_at_ns is None:
        return FeedHealth.UNKNOWN
    if now_ns - state.last_available_at_ns > policy.max_staleness_ns:
        return FeedHealth.STALE
    return state.health


def tradeable(state: FeedState, now_ns: int, policy: FeedPolicy) -> bool:
    return health_at(state, now_ns, policy) is FeedHealth.HEALTHY
