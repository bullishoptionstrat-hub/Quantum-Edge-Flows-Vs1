from decimal import Decimal

import pytest
from hypothesis import given, strategies as st

from qe.core.ticks import OffTickError, from_ticks, to_ticks

Q = Decimal("0.25")


def test_known_values():
    assert to_ticks("6000.25", Q) == 24001
    assert to_ticks(Decimal("2400.1"), Decimal("0.10")) == 24001
    assert from_ticks(24001, Q) == Decimal("6000.25")


def test_off_tick_rejected():
    with pytest.raises(OffTickError):
        to_ticks("6000.30", Q)


@pytest.mark.parametrize("bad", [6000.25, True])
def test_float_and_bool_rejected(bad):
    with pytest.raises(TypeError):
        to_ticks(bad, Q)


@given(st.integers(min_value=-10**9, max_value=10**9))
def test_roundtrip(t):
    assert to_ticks(from_ticks(t, Q), Q) == t
