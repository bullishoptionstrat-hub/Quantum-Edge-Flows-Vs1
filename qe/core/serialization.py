"""Canonical serialization and hashing (INV-01, INV-06).

canonical_bytes() produces one byte string per logical value: sorted keys,
no whitespace, UTF-8, Decimals normalized and tagged, enums by value, and
objects via their to_canonical(). Floats are rejected so no hash can depend
on binary rounding. Hash chaining gives tamper evidence without a blockchain.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from enum import Enum
from typing import Any

GENESIS = "0" * 64


def _normalize_decimal(d: Decimal) -> str:
    if not d.is_finite():
        raise ValueError(f"non-finite Decimal not allowed: {d}")
    s = format(d.normalize(), "f")
    return "0" if s in ("-0", "0") else s


def to_plain(value: Any) -> Any:
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        raise TypeError(f"floats are not allowed in canonical data: {value!r}")
    if isinstance(value, Decimal):
        return "dec:" + _normalize_decimal(value)
    if isinstance(value, Enum):
        return to_plain(value.value)
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if not isinstance(k, str):
                raise TypeError(f"canonical dict keys must be str, got {k!r}")
            out[k] = to_plain(v)
        return out
    if isinstance(value, (list, tuple)):
        return [to_plain(v) for v in value]
    if hasattr(value, "to_canonical"):
        return to_plain(value.to_canonical())
    raise TypeError(f"unsupported type for canonical serialization: {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(to_plain(value), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def chain_hash(prev_hash: str, value: Any) -> str:
    if len(prev_hash) != 64 or any(c not in "0123456789abcdef" for c in prev_hash):
        raise ValueError("prev_hash must be a 64-char lowercase hex sha256")
    return hashlib.sha256(prev_hash.encode("ascii") + canonical_bytes(value)).hexdigest()
