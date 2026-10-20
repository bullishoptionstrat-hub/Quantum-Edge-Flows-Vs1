"""Injected time (INV-02, INV-04).

The core never reads the wall clock. Time is integer nanoseconds since the
Unix epoch, UTC. ReplayClock only moves forward; a live clock (later, in
adapters/) must satisfy the same Clock protocol.
"""

from __future__ import annotations

from typing import Protocol


class Clock(Protocol):
    def now_ns(self) -> int: ...


class ClockWentBackwards(RuntimeError):
    pass


class ReplayClock:
    def __init__(self, start_ns: int) -> None:
        if isinstance(start_ns, bool) or not isinstance(start_ns, int) or start_ns < 0:
            raise ValueError(f"start_ns must be a non-negative int, got {start_ns!r}")
        self._now = start_ns

    def now_ns(self) -> int:
        return self._now

    def advance_to(self, t_ns: int) -> None:
        if t_ns < self._now:
            raise ClockWentBackwards(f"{t_ns} < {self._now}")
        self._now = t_ns
