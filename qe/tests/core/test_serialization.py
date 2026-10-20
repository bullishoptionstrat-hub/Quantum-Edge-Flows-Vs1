from decimal import Decimal
from enum import Enum

import pytest
from hypothesis import given, strategies as st

from qe.core.serialization import GENESIS, canonical_bytes, chain_hash, sha256_hex


class Color(Enum):
    RED = "red"


def test_key_order_does_not_matter():
    assert canonical_bytes({"b": 1, "a": [1, 2]}) == canonical_bytes({"a": [1, 2], "b": 1})


def test_decimal_normalization():
    assert canonical_bytes(Decimal("1.50")) == canonical_bytes(Decimal("1.5"))
    assert canonical_bytes(Decimal("100")) == canonical_bytes(Decimal("1E+2"))
    assert canonical_bytes(Decimal("-0.0")) == canonical_bytes(Decimal("0"))


@pytest.mark.parametrize("bad", [1.5, {"x": 0.1}, {1: "a"}, Decimal("NaN"), object()])
def test_rejects_non_canonical(bad):
    with pytest.raises((TypeError, ValueError)):
        canonical_bytes(bad)


def test_golden_hash_is_stable():
    # If this changes, every stored decision hash changes: bump the schema, don't edit the value.
    value = {"instrument": "ES", "entry": 24001, "px": Decimal("6000.25"), "side": Color.RED, "tags": ("a", None, True)}
    assert canonical_bytes(value) == b'{"entry":24001,"instrument":"ES","px":"dec:6000.25","side":"red","tags":["a",null,true]}'
    assert sha256_hex(value) == GOLDEN


def test_chain_hash_depends_on_order():
    a, b = {"n": 1}, {"n": 2}
    assert chain_hash(chain_hash(GENESIS, a), b) != chain_hash(chain_hash(GENESIS, b), a)
    with pytest.raises(ValueError):
        chain_hash("xyz", a)


json_like = st.recursive(
    st.none() | st.booleans() | st.integers() | st.text(),
    lambda c: st.lists(c, max_size=4) | st.dictionaries(st.text(max_size=5), c, max_size=4),
    max_leaves=12,
)


@given(json_like)
def test_hash_is_deterministic(v):
    assert sha256_hex(v) == sha256_hex(v)


GOLDEN = "e2fe93e807290a0cd659433573a33fffc4496680a011840f82974af525b63a38"
