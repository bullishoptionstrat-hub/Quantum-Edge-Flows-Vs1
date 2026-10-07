import pytest
from hypothesis import given, strategies as st

from qe.core.clock import ClockWentBackwards, ReplayClock
from qe.core.events import BarClosed, InvalidEvent
from qe.core.mode import Capability, CapabilityDenied, Mode, ModeRefused, require, resolve_mode
from qe.core.serialization import sha256_hex

S = 1_000_000_000


def bar(**over):
    kw = dict(provider="test", instrument_root="ES", contract_id="ESZ6", timeframe_s=60,
              bar_start_ns=0, event_time_ns=60 * S, receive_time_ns=60 * S + 5, available_at_ns=60 * S + 5,
              open=24000, high=24004, low=23998, close=24002, volume=10)
    kw.update(over)
    return BarClosed(**kw)


@pytest.mark.parametrize("over", [
    dict(high=24001),                      # high below close
    dict(low=24001),                       # low above open
    dict(receive_time_ns=59 * S, available_at_ns=59 * S),  # available before the bar closed: lookahead
    dict(available_at_ns=60 * S),          # available before it was received
    dict(event_time_ns=61 * S),            # close time does not match start + timeframe
    dict(open=24000.0),                    # float price
    dict(contract_id=""),
])
def test_invalid_bars_rejected(over):
    with pytest.raises(InvalidEvent):
        bar(**over)


def test_usable_only_once_available():
    b = bar()
    assert not b.usable_at(60 * S)
    assert b.usable_at(60 * S + 5)


@given(st.integers(0, 10_000), st.integers(0, 10_000), st.integers(0, 10_000), st.integers(0, 10_000))
def test_any_consistent_ohlc_accepted_and_hash_stable(a, b_, c, d):
    o, cl = a, b_
    hi, lo = max(o, cl) + c, min(o, cl) - d
    x = bar(open=o, close=cl, high=hi, low=lo)
    assert sha256_hex(x) == sha256_hex(bar(open=o, close=cl, high=hi, low=lo))


def test_replay_clock_only_moves_forward():
    c = ReplayClock(10)
    c.advance_to(10)
    c.advance_to(20)
    assert c.now_ns() == 20
    with pytest.raises(ClockWentBackwards):
        c.advance_to(19)


def test_live_mode_cannot_be_entered():
    with pytest.raises(ModeRefused):
        resolve_mode("LIVE")
    assert resolve_mode("REPLAY") is Mode.REPLAY


def test_no_mode_grants_live_orders_and_replay_cannot_touch_brokers():
    for m in Mode:
        with pytest.raises(CapabilityDenied):
            require(m, Capability.LIVE_ORDERS)
    for cap in (Capability.PAPER_ORDERS, Capability.LIVE_MARKET_DATA):
        with pytest.raises(CapabilityDenied):
            require(Mode.REPLAY, cap)
