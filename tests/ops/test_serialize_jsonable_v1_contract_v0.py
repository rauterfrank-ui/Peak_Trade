"""Contract tests for `to_jsonable_v1` (v0).

No network, subprocess, or env-backed behavior. Matches public semantics of
``src.ops.common.serialize_v1``.

Results built only from primitives, Path-derived strings, and Enum values are
asserted to be ``json.dumps``-serializable. Opaque pass-through is asserted only
for identity/semantics, not JSON round-trips.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum, IntEnum
from pathlib import Path

import pytest

from src.ops.common.serialize_v1 import to_jsonable_v1


def _assert_json_dumps_round_trip(obj: object) -> None:
    out = to_jsonable_v1(obj)
    json.dumps(out, sort_keys=True)


def test_to_jsonable_v1_none_contract_v0() -> None:
    assert to_jsonable_v1(None) is None
    assert json.dumps(to_jsonable_v1({"k": None}), sort_keys=True) == '{"k": null}'


@pytest.mark.parametrize(
    "primitive",
    [0, 1, -1, 3.14, True, False, "", "hello"],
)
def test_to_jsonable_v1_primitives_stable_contract_v0(primitive: object) -> None:
    assert to_jsonable_v1(primitive) is primitive


def test_to_jsonable_v1_dict_key_stringify_nested_contract_v0() -> None:
    raw = {1: {2: "x"}, "a": [{"b": 3}]}
    out = to_jsonable_v1(raw)
    assert out == {"1": {"2": "x"}, "a": [{"b": 3}]}
    _assert_json_dumps_round_trip(raw)


def test_to_jsonable_v1_list_and_tuple_recursive_contract_v0() -> None:
    tup = ([1], ({"x": Path("logs/out.txt")},))
    out = to_jsonable_v1(tup)
    assert isinstance(out, list)
    assert out[0] == [1]
    assert out[1][0]["x"] == "logs/out.txt"
    _assert_json_dumps_round_trip(tup)


@dataclass
class Inner:
    n: int
    rel_path: Path


@dataclass(frozen=True)
class Outer:
    label: str
    inner: Inner


def test_to_jsonable_v1_dataclass_nested_contract_v0() -> None:
    oc = Outer("x", Inner(7, Path("cfg/app.toml")))
    out = to_jsonable_v1(oc)
    assert out == {"label": "x", "inner": {"n": 7, "rel_path": "cfg/app.toml"}}
    _assert_json_dumps_round_trip(oc)


class _StrEnum(Enum):
    A = "alpha"


class _IntEnumV(IntEnum):
    X = 42


@pytest.mark.parametrize(
    "member,expected",
    [(_StrEnum.A, "alpha"), (_IntEnumV.X, 42)],
)
def test_to_jsonable_v1_enum_value_branch_contract_v0(member: Enum, expected: object) -> None:
    assert to_jsonable_v1(member) == expected
    assert json.dumps(to_jsonable_v1({"e": member}), sort_keys=True) == json.dumps(
        {"e": expected}, sort_keys=True
    )


def test_to_jsonable_v1_pathlike_contract_v0() -> None:
    p = Path("docs/ops/README.md")
    assert to_jsonable_v1(p) == "docs/ops/README.md"
    _assert_json_dumps_round_trip({"p": p})


class _Opaque:
    __slots__ = ()


def test_to_jsonable_v1_unknown_object_pass_through_contract_v0() -> None:
    o = _Opaque()
    assert to_jsonable_v1(o) is o


def test_to_jsonable_v1_type_objects_not_treated_as_enum_contract_v0() -> None:
    assert to_jsonable_v1(int) is int
    assert to_jsonable_v1(str) is str
