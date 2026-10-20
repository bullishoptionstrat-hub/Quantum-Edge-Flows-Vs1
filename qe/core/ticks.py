"""Integer-tick price representation (INV-05).

Prices enter the core as Decimal or str and are converted to integer ticks.
Floats are rejected outright: binary floating point cannot represent most
tick grids exactly, and float equality on stops/targets is forbidden.
"""

from __future__ import annotations

from decimal import Decimal

PriceLike = Decimal | str | int


class OffTickError(ValueError):
    """Price is not an exact multiple of the instrument tick size."""


def _dec(value: PriceLike) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise TypeError(f"float/bool prices are not allowed in the core: {value!r}")
    return value if isinstance(value, Decimal) else Decimal(value)


def to_ticks(price: PriceLike, tick_size: Decimal) -> int:
    """Convert a price to integer ticks, refusing anything off the tick grid."""
    if tick_size <= 0:
        raise ValueError(f"tick_size must be positive, got {tick_size}")
    q = _dec(price) / tick_size
    if q != q.to_integral_value():
        raise OffTickError(f"price {price} is not a multiple of tick size {tick_size}")
    return int(q)


def from_ticks(ticks: int, tick_size: Decimal) -> Decimal:
    if isinstance(ticks, bool) or not isinstance(ticks, int):
        raise TypeError(f"ticks must be int, got {type(ticks).__name__}")
    return tick_size * ticks
