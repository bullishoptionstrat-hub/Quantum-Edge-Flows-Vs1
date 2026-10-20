"""Instrument registry and economic risk (directive D7, INV-20, INV-24).

Money is integer minor units (cents). R ratios are exact Fractions so the
net-R threshold comparison can never be decided by rounding (compare D-045).
Registry values live in qe/config/instruments.json with a `verified` flag;
unverified specs must not be used for real risk decisions (directive D9).
The core only parses an already-loaded mapping (no file I/O here, INV-02).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from fractions import Fraction


class Side(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class InvalidGeometry(ValueError):
    """Entry, stop and target are not ordered correctly for the side."""


@dataclass(frozen=True)
class InstrumentSpec:
    root: str
    exchange: str
    currency: str
    tick_size: Decimal
    tick_value_minor: int  # value of one tick for one contract, in minor units
    exchange_timezone: str
    verified: bool
    source: str

    @property
    def point_value_minor(self) -> Fraction:
        return Fraction(self.tick_value_minor) / Fraction(self.tick_size)


@dataclass(frozen=True)
class CostModel:
    """Per-contract friction. Slippage is in ticks and always adverse."""

    commission_round_turn_minor: int
    entry_slippage_ticks: int
    stop_slippage_ticks: int
    target_slippage_ticks: int = 0

    def __post_init__(self) -> None:
        for name in ("commission_round_turn_minor", "entry_slippage_ticks",
                     "stop_slippage_ticks", "target_slippage_ticks"):
            v = getattr(self, name)
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                raise ValueError(f"{name} must be a non-negative int, got {v!r}")


def parse_registry(raw: dict) -> dict[str, InstrumentSpec]:
    out = {}
    for row in raw["instruments"]:
        spec = InstrumentSpec(
            root=row["root"], exchange=row["exchange"], currency=row["currency"],
            tick_size=Decimal(row["tick_size"]), tick_value_minor=int(row["tick_value_minor"]),
            exchange_timezone=row["exchange_timezone"], verified=bool(row["verified"]),
            source=row["source"],
        )
        if spec.tick_size <= 0 or spec.tick_value_minor <= 0:
            raise ValueError(f"invalid spec for {spec.root}")
        if spec.root in out:
            raise ValueError(f"duplicate instrument root {spec.root}")
        out[spec.root] = spec
    return out


def check_geometry(side: Side, entry: int, stop: int, target: int | None = None) -> None:
    """INV-18: stop on the correct side of entry; target beyond entry if given."""
    if side is Side.LONG:
        ok = stop < entry and (target is None or target > entry)
    else:
        ok = stop > entry and (target is None or target < entry)
    if not ok:
        raise InvalidGeometry(f"{side.value}: entry={entry} stop={stop} target={target}")


def _cost_on_stop_path(spec: InstrumentSpec, cost: CostModel) -> int:
    return cost.commission_round_turn_minor + (cost.entry_slippage_ticks + cost.stop_slippage_ticks) * spec.tick_value_minor


def _cost_on_target_path(spec: InstrumentSpec, cost: CostModel) -> int:
    return cost.commission_round_turn_minor + (cost.entry_slippage_ticks + cost.target_slippage_ticks) * spec.tick_value_minor


def economic_risk_minor(spec: InstrumentSpec, side: Side, entry: int, stop: int,
                        contracts: int, cost: CostModel) -> int:
    """INV-24: loss if the stop is hit, including fees and adverse slippage."""
    check_geometry(side, entry, stop)
    if isinstance(contracts, bool) or not isinstance(contracts, int) or contracts < 0:
        raise ValueError(f"contracts must be a non-negative int, got {contracts!r}")
    per_contract = abs(entry - stop) * spec.tick_value_minor + _cost_on_stop_path(spec, cost)
    return per_contract * contracts


def size_contracts(spec: InstrumentSpec, side: Side, entry: int, stop: int,
                   budget_minor: int, cost: CostModel) -> int:
    """INV-20: largest contract count whose economic risk fits the budget.

    Rounds down. Returns 0 when not even one contract fits; the caller must
    treat 0 as BLOCKED_RISK. The stop is never moved to make size fit.
    """
    if budget_minor < 0:
        raise ValueError("budget must be non-negative")
    per_contract = economic_risk_minor(spec, side, entry, stop, 1, cost)
    return budget_minor // per_contract


def net_r(spec: InstrumentSpec, side: Side, entry: int, stop: int, target: int,
          cost: CostModel) -> Fraction:
    """INV-19: reward after costs divided by risk after costs, exactly.

    Contract count cancels, so this is computed per contract.
    """
    check_geometry(side, entry, stop, target)
    reward = abs(target - entry) * spec.tick_value_minor - _cost_on_target_path(spec, cost)
    risk = abs(entry - stop) * spec.tick_value_minor + _cost_on_stop_path(spec, cost)
    return Fraction(reward, risk)


def meets_min_net_r(r: Fraction, min_net_r: Fraction) -> bool:
    return r >= min_net_r
