"""Operating-mode firewall (directive B2).

Capabilities are allow-listed per mode in code. LIVE cannot be entered from
this codebase: it is outside the scope of QEGP-MASTER-4.0 and needs an A3
human action plus a passing live-readiness review, neither of which exists.
"""

from __future__ import annotations

from enum import Enum


class Mode(Enum):
    AUDIT = "AUDIT"
    SPECIFICATION = "SPECIFICATION"
    REPLAY = "REPLAY"
    RESEARCH = "RESEARCH"
    SHADOW = "SHADOW"
    PAPER = "PAPER"
    LIVE_ELIGIBLE = "LIVE_ELIGIBLE"
    LIVE = "LIVE"


class Capability(Enum):
    READ_SOURCE = "READ_SOURCE"
    RUN_TESTS = "RUN_TESTS"
    REPLAY_HISTORY = "REPLAY_HISTORY"
    SIMULATED_ORDERS = "SIMULATED_ORDERS"
    RESEARCH_EXPERIMENTS = "RESEARCH_EXPERIMENTS"
    LIVE_MARKET_DATA = "LIVE_MARKET_DATA"
    PAPER_ORDERS = "PAPER_ORDERS"
    LIVE_ORDERS = "LIVE_ORDERS"


_C = Capability
CAPABILITIES: dict[Mode, frozenset[Capability]] = {
    Mode.AUDIT: frozenset({_C.READ_SOURCE, _C.RUN_TESTS}),
    Mode.SPECIFICATION: frozenset({_C.READ_SOURCE, _C.RUN_TESTS}),
    Mode.REPLAY: frozenset({_C.READ_SOURCE, _C.RUN_TESTS, _C.REPLAY_HISTORY, _C.SIMULATED_ORDERS}),
    Mode.RESEARCH: frozenset({_C.READ_SOURCE, _C.RUN_TESTS, _C.REPLAY_HISTORY, _C.SIMULATED_ORDERS,
                              _C.RESEARCH_EXPERIMENTS}),
    Mode.SHADOW: frozenset({_C.READ_SOURCE, _C.RUN_TESTS, _C.LIVE_MARKET_DATA}),
    Mode.PAPER: frozenset({_C.READ_SOURCE, _C.RUN_TESTS, _C.LIVE_MARKET_DATA, _C.PAPER_ORDERS}),
    Mode.LIVE_ELIGIBLE: frozenset({_C.READ_SOURCE, _C.RUN_TESTS, _C.LIVE_MARKET_DATA, _C.PAPER_ORDERS}),
    Mode.LIVE: frozenset(),  # never granted here; see resolve_mode
}


class ModeRefused(PermissionError):
    pass


class CapabilityDenied(PermissionError):
    pass


def resolve_mode(name: str) -> Mode:
    mode = Mode(name)
    if mode is Mode.LIVE:
        raise ModeRefused("LIVE is outside QEGP-MASTER-4.0 scope and cannot be entered (A3)")
    return mode


def require(mode: Mode, capability: Capability) -> None:
    if capability not in CAPABILITIES[mode]:
        raise CapabilityDenied(f"{mode.value} does not allow {capability.value}")
