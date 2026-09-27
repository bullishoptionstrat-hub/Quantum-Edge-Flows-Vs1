from dataclasses import replace

import pytest
from hypothesis import given, strategies as st

from qe.core.data_quality import DQReason, FeedHealth, FeedPolicy, FeedState, health_at, step, tradeable
from qe.core.events import BarClosed
from qe.core.serialization import sha256_hex

S = 1_000_000_000
TF = 60
POLICY = FeedPolicy(instrument_root="ES", timeframe_s=TF, max_staleness_ns=120 * S, recovery_bars=2)


def bar(i, contract="ESZ6", close=24000, root="ES", tf=TF):
    start = i * tf * S
    end = start + tf * S
    return BarClosed(provider="t", instrument_root=root, contract_id=contract, timeframe_s=tf,
                     bar_start_ns=start, event_time_ns=end, receive_time_ns=end, available_at_ns=end,
                     open=24000, high=max(24000, close) + 1, low=min(24000, close) - 1, close=close, volume=1)


def run(bars, policy=POLICY):
    s, out = FeedState(), []
    for b in bars:
        s, v = step(s, b, policy)
        out.append(v)
    return s, out


def test_no_data_is_unknown_and_not_tradeable():
    assert health_at(FeedState(), 0, POLICY) is FeedHealth.UNKNOWN
    assert not tradeable(FeedState(), 0, POLICY)


def test_recovery_needs_consecutive_clean_bars():
    s, v = run([bar(0)])
    assert v[-1].reason is DQReason.DQ_RECOVERING and not tradeable(s, bar(0).available_at_ns, POLICY)
    s, v = run([bar(0), bar(1)])
    assert v[-1].reason is DQReason.DQ_OK and tradeable(s, bar(1).available_at_ns, POLICY)


def test_duplicate_is_idempotent():
    s1, _ = run([bar(0), bar(1)])
    s2, v = run([bar(0), bar(1), bar(1)])
    assert v[-1].reason is DQReason.DQ_DUPLICATE and not v[-1].accepted
    assert s1 == s2


def test_conflicting_duplicate_blocks():
    s, v = run([bar(0), bar(1), bar(1, close=24010)])
    assert v[-1].reason is DQReason.DQ_CONFLICTING_DUPLICATE and not v[-1].accepted
    assert s.health is FeedHealth.UNKNOWN and v[-1].health is FeedHealth.UNKNOWN
    assert not tradeable(s, bar(1).available_at_ns, POLICY)


def test_out_of_order_rejected_and_state_unchanged():
    s1, _ = run([bar(0), bar(1), bar(2)])
    s2, v = run([bar(0), bar(1), bar(2), bar(1, close=23990)])
    assert v[-1].reason is DQReason.DQ_OUT_OF_ORDER and s1 == s2


def test_gap_blocks_until_recovered():
    s, v = run([bar(0), bar(1), bar(3)])
    assert v[-1].reason is DQReason.DQ_GAP and s.health is FeedHealth.GAPPED
    assert not tradeable(s, bar(3).available_at_ns, POLICY)
    s, v = run([bar(0), bar(1), bar(3), bar(4)])
    assert v[-1].reason is DQReason.DQ_RECOVERING
    s, v = run([bar(0), bar(1), bar(3), bar(4), bar(5)])
    assert v[-1].reason is DQReason.DQ_OK


def test_declared_session_break_is_not_a_gap():
    policy = replace(POLICY, is_session_break=lambda prev_close, nxt: nxt - prev_close == TF * S)
    s, v = run([bar(0), bar(1), bar(3)], policy)
    assert v[-1].reason is DQReason.DQ_OK and s.health is FeedHealth.HEALTHY


def test_contract_change_blocks():
    s, v = run([bar(0), bar(1), bar(2, contract="ESH7")])
    assert v[-1].reason is DQReason.DQ_CONTRACT_CHANGED and s.health is FeedHealth.UNKNOWN


def test_wrong_feed_rejected():
    s, v = run([bar(0, root="NQ")])
    assert v[-1].reason is DQReason.DQ_WRONG_FEED and s == FeedState()
    s, v = run([bar(0, tf=300)])
    assert v[-1].reason is DQReason.DQ_WRONG_FEED


def test_staleness_boundary():
    s, _ = run([bar(0), bar(1)])
    t = bar(1).available_at_ns
    assert health_at(s, t + 120 * S, POLICY) is FeedHealth.HEALTHY
    assert health_at(s, t + 120 * S + 1, POLICY) is FeedHealth.STALE


@pytest.mark.parametrize("kw", [dict(timeframe_s=0), dict(max_staleness_ns=0), dict(recovery_bars=0)])
def test_policy_requires_positive_thresholds(kw):
    with pytest.raises(ValueError):
        replace(POLICY, **kw)


# Property: whatever order bars arrive in (shuffled, repeated), the gate never
# accepts a bar at or before one it already accepted, and HEALTHY is only ever
# reported after `recovery_bars` consecutive contiguous bars.
@given(st.lists(st.integers(0, 12), min_size=1, max_size=40))
def test_accepted_starts_strictly_increase(idx):
    s = FeedState()
    accepted, streak = [], 0
    for i in idx:
        s, v = step(s, bar(i), POLICY)
        if v.accepted:
            assert not accepted or bar(i).bar_start_ns > accepted[-1]
            contiguous = bool(accepted) and bar(i).bar_start_ns == accepted[-1] + TF * S
            streak = streak + 1 if (contiguous or not accepted) else 1
            accepted.append(bar(i).bar_start_ns)
            if v.health is FeedHealth.HEALTHY:
                assert streak >= POLICY.recovery_bars


@given(st.lists(st.integers(0, 12), max_size=30))
def test_verdict_sequence_is_deterministic(idx):
    assert sha256_hex(run([bar(i) for i in idx])[1]) == sha256_hex(run([bar(i) for i in idx])[1])
