"""Typed, immutable market events (directive D3, INV-03, INV-07).

Only the closed-bar event exists for now. Every market event separates
event_time (when the market says it happened), receive_time (when we got it)
and available_at (earliest instant a decision may use it).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

SCHEMA_VERSION = 1


class InvalidEvent(ValueError):
    pass


def _nonneg_int(name: str, v: object) -> None:
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise InvalidEvent(f"{name} must be a non-negative int, got {v!r}")


@dataclass(frozen=True)
class BarClosed:
    provider: str
    instrument_root: str
    contract_id: str
    timeframe_s: int
    bar_start_ns: int
    event_time_ns: int  # bar close time
    receive_time_ns: int
    available_at_ns: int
    open: int  # ticks
    high: int
    low: int
    close: int
    volume: int
    provider_sequence: int | None = None
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("timeframe_s", "bar_start_ns", "event_time_ns", "receive_time_ns",
                     "available_at_ns", "volume"):
            _nonneg_int(name, getattr(self, name))
        for name in ("open", "high", "low", "close"):
            v = getattr(self, name)
            if isinstance(v, bool) or not isinstance(v, int):
                raise InvalidEvent(f"{name} must be int ticks, got {v!r}")
        if self.timeframe_s == 0:
            raise InvalidEvent("timeframe_s must be positive")
        if self.event_time_ns != self.bar_start_ns + self.timeframe_s * 1_000_000_000:
            raise InvalidEvent("event_time_ns must equal bar_start_ns + timeframe")
        if not (self.low <= min(self.open, self.close) and self.high >= max(self.open, self.close)):
            raise InvalidEvent(f"impossible OHLC o={self.open} h={self.high} l={self.low} c={self.close}")
        if self.available_at_ns < self.event_time_ns:
            raise InvalidEvent("available_at_ns precedes the bar close (lookahead)")
        if self.available_at_ns < self.receive_time_ns:
            raise InvalidEvent("available_at_ns precedes receive_time_ns")
        if not self.provider or not self.instrument_root or not self.contract_id:
            raise InvalidEvent("provider, instrument_root and contract_id are required")

    def usable_at(self, decision_time_ns: int) -> bool:
        """INV-03: a decision may use this bar only once it is available."""
        return self.available_at_ns <= decision_time_ns

    def to_canonical(self) -> dict:
        return {"type": "BarClosed", **asdict(self)}
