import json
from fractions import Fraction
from pathlib import Path

import pytest
from hypothesis import assume, given, strategies as st

from qe.core.instruments import (
    CostModel, InvalidGeometry, Side, economic_risk_minor, meets_min_net_r, net_r,
    parse_registry, size_contracts,
)

REG = parse_registry(json.loads((Path(__file__).parents[2] / "config" / "instruments.json").read_text()))
ES = REG["ES"]
FREE = CostModel(0, 0, 0)
COST = CostModel(commission_round_turn_minor=450, entry_slippage_ticks=1, stop_slippage_ticks=2)


def test_registry_rows_are_unverified_until_checked():
    assert set(REG) == {"ES", "MES", "NQ", "MNQ", "GC"}
    assert all(not s.verified for s in REG.values())
    assert ES.point_value_minor == 5000  # $50/point


def test_duplicate_root_rejected():
    raw = {"instruments": [dict(root="ES", exchange="CME", currency="USD", tick_size="0.25",
                                tick_value_minor=1250, exchange_timezone="America/Chicago",
                                verified=False, source="x")] * 2}
    with pytest.raises(ValueError):
        parse_registry(raw)


def test_es_ten_points_one_contract_is_500_dollars():
    # D-008 regression: 10 points is $500 of risk, not "10".
    assert economic_risk_minor(ES, Side.LONG, 24000, 23960, 1, FREE) == 50_000


def test_costs_add_to_risk():
    # 40 ticks * 1250 + 450 commission + 3 ticks slippage * 1250
    assert economic_risk_minor(ES, Side.LONG, 24000, 23960, 1, COST) == 50_000 + 450 + 3750


@pytest.mark.parametrize("side,entry,stop,target", [
    (Side.LONG, 100, 100, 110), (Side.LONG, 100, 101, 110), (Side.LONG, 100, 90, 100),
    (Side.SHORT, 100, 99, 90), (Side.SHORT, 100, 110, 100),
])
def test_bad_geometry_rejected(side, entry, stop, target):
    with pytest.raises(InvalidGeometry):
        net_r(ES, side, entry, stop, target, FREE)


def test_net_r_is_exact_and_costs_can_break_2r():
    # Gross exactly 2R (40 ticks risk, 80 ticks reward). Costs push it below 2.
    assert net_r(ES, Side.LONG, 24000, 23960, 24080, FREE) == Fraction(2)
    assert meets_min_net_r(net_r(ES, Side.LONG, 24000, 23960, 24080, FREE), Fraction(2))
    assert not meets_min_net_r(net_r(ES, Side.LONG, 24000, 23960, 24080, COST), Fraction(2))


def test_zero_contracts_when_budget_too_small():
    # INV-20: never force one contract.
    assert size_contracts(ES, Side.LONG, 24000, 23960, 49_999, FREE) == 0
    assert size_contracts(ES, Side.LONG, 24000, 23960, 50_000, FREE) == 1


prices = st.integers(min_value=1, max_value=200_000)
costs = st.builds(CostModel, st.integers(0, 5_000), st.integers(0, 8), st.integers(0, 8), st.integers(0, 8))


@given(prices, st.integers(1, 5_000), st.integers(0, 50), costs)
def test_risk_nonnegative_and_linear_in_contracts(entry, dist, n, cost):
    one = economic_risk_minor(ES, Side.LONG, entry, entry - dist, 1, cost)
    assert one > 0
    assert economic_risk_minor(ES, Side.LONG, entry, entry - dist, n, cost) == n * one


@given(prices, st.integers(1, 5_000), st.integers(0, 10**9), costs)
def test_sizing_never_exceeds_budget(entry, dist, budget, cost):
    n = size_contracts(ES, Side.SHORT, entry, entry + dist, budget, cost)
    assert economic_risk_minor(ES, Side.SHORT, entry, entry + dist, n, cost) <= budget
    assert economic_risk_minor(ES, Side.SHORT, entry, entry + dist, n + 1, cost) > budget


@given(prices, st.integers(1, 5_000), st.integers(1, 20_000), costs)
def test_costs_never_improve_net_r(entry, risk, reward, cost):
    assume(cost != CostModel(0, 0, 0, 0))
    gross = net_r(ES, Side.LONG, entry, entry - risk, entry + reward, FREE)
    assert net_r(ES, Side.LONG, entry, entry - risk, entry + reward, cost) < gross


def test_net_r_exact_value_with_costs():
    # reward: 80 ticks * 1250 - (450 commission + 1 entry-slip tick * 1250) = 98_300
    # risk:   40 ticks * 1250 + 450 + (1 entry + 2 stop slip ticks) * 1250   = 54_200
    assert net_r(ES, Side.LONG, 24000, 23960, 24080, COST) == Fraction(98_300, 54_200)
    assert net_r(ES, Side.SHORT, 24000, 24040, 23920, COST) == Fraction(98_300, 54_200)
