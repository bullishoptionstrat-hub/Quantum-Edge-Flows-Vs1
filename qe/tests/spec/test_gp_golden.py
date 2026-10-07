"""Golden fixtures as the Phase 3 acceptance test (directive E2, Phase 2 exit).

Every fixture runs through qe.gp. Until Phase 3 replaces the stubs, each case is
an expected failure that must raise NotImplementedError. When the reducer exists:
- a correct result XPASSes, which fails the strict run and forces removal of the marker;
- a wrong result raises AssertionError, which is not the expected exception, so it fails.
"""

from __future__ import annotations

import copy

import pytest

from qe.gp import run_liquidity_fixture, run_setup_fixture
from qe.tests.spec._fixtures import load_fixtures, outcomes_match

FIXTURES = load_fixtures()


@pytest.mark.xfail(strict=True, raises=NotImplementedError,
                   reason="Phase 3: GP reducer not implemented; gp-1.0.0-draft.1 not frozen")
@pytest.mark.parametrize("fixture", FIXTURES, ids=[f["fixture_id"] for f in FIXTURES])
def test_golden_fixture(fixture):
    run = run_setup_fixture if fixture["module"] == "setup" else run_liquidity_fixture
    assert outcomes_match(fixture["expected"], run(fixture)) == []


def test_comparator_accepts_exact_and_rejects_deviations():
    """The comparator must be able to fail, otherwise the golden test proves nothing."""
    gf1 = next(f for f in FIXTURES if f["fixture_id"] == "GF-001")["expected"]
    assert outcomes_match(gf1, copy.deepcopy(gf1)) == []

    wrong_r = copy.deepcopy(gf1)
    wrong_r["lineages"][0]["evidence"]["net_r"] = "2/1"
    assert outcomes_match(gf1, wrong_r)

    extra = copy.deepcopy(gf1)
    extra["lineages"].append(copy.deepcopy(extra["lineages"][0]))
    assert outcomes_match(gf1, extra)

    skipped_state = copy.deepcopy(gf1)
    skipped_state["lineages"][0]["transitions"].pop(3)  # drop RETESTED
    assert outcomes_match(gf1, skipped_state)

    extra_rejection = copy.deepcopy(gf1)
    extra_rejection["rejections"] = [{"bar": 15, "liquidity_id": "x", "reason_code": "GP_BLOCK_NO_TARGET"}]
    assert outcomes_match(gf1, extra_rejection)

    # equal fractions in different spellings match; unequal ones do not
    same_value = copy.deepcopy(gf1)
    same_value["lineages"][0]["evidence"]["net_r"] = "438/142"
    assert outcomes_match(gf1, same_value) == []
