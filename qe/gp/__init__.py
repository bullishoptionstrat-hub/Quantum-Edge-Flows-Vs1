"""God's Plan setup reducer and liquidity module (directive Phase 3).

Not implemented. The spec it must implement is qe/spec/GP_SPEC.md (gp-1.0.0-draft.1,
PROPOSED, not frozen). The golden fixtures in qe/spec/fixtures/ are the acceptance
test: qe/tests/spec/test_gp_golden.py runs every fixture through these two entry
points and expects NotImplementedError until Phase 3 replaces them.

Phase 3 must not start until the operator freezes the spec (A2), because each
fixture's expected outcome depends on the PROPOSED parameter values.
"""

from __future__ import annotations


def run_setup_fixture(fixture: dict) -> dict:
    """Replay one setup fixture; return {"lineages", "rejections", "liquidity_final"}."""
    raise NotImplementedError("GP setup reducer is Phase 3; spec gp-1.0.0-draft.1 is not frozen")


def run_liquidity_fixture(fixture: dict) -> dict:
    """Replay one liquidity fixture; return {"swings", "liquidity_created"}."""
    raise NotImplementedError("GP liquidity module is Phase 3; spec gp-1.0.0-draft.1 is not frozen")
