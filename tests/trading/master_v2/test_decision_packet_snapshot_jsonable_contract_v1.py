"""Contract: Decision-Packet-Snapshot v1 is JSON-round-trippable via Ops `to_jsonable_v1`.

Non-authorizing reproducibility anchor only — no readiness, gate, execution, or signoff claims.
"""

from __future__ import annotations

import json

from trading.master_v2.decision_packet_fixtures_v1 import sample_decision_packet_snapshot_v1
from trading.master_v2.decision_packet_replay_v1 import decision_packet_from_snapshot_v1
from trading.master_v2.decision_packet_snapshot_v1 import (
    DECISION_PACKET_SNAPSHOT_LAYER_VERSION,
    validate_decision_packet_snapshot_v1,
)

from src.ops.common.serialize_v1 import to_jsonable_v1


_EXPECTED_SNAPSHOT_TOP_LEVEL_KEYS = frozenset(
    {
        "snapshot_layer_version",
        "layer_version",
        "correlation_id",
        "staged",
        "universe",
        "doubleplay",
        "scope_envelope",
        "risk_cap",
        "safety",
    }
)


def _assert_json_native(obj: object, *, depth: int = 0) -> None:
    if depth > 24:
        raise AssertionError("json structure too deep for contract bound")
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert isinstance(k, str), (type(k), obj)
            _assert_json_native(v, depth=depth + 1)
        return
    if isinstance(obj, list):
        for x in obj:
            _assert_json_native(x, depth=depth + 1)
        return
    raise AssertionError(f"non-json-native type after serialization: {type(obj)!r}")


def test_decision_packet_snapshot_v1_jsonable_round_trip_stable_shape() -> None:
    snapshot = sample_decision_packet_snapshot_v1()
    assert snapshot, "fixture must produce a non-empty snapshot dict"
    assert snapshot["snapshot_layer_version"] == DECISION_PACKET_SNAPSHOT_LAYER_VERSION
    validate_decision_packet_snapshot_v1(snapshot)

    jsonable = to_jsonable_v1(snapshot)
    assert jsonable == snapshot
    _assert_json_native(jsonable)

    wire = json.dumps(jsonable, sort_keys=True)
    decoded = json.loads(wire)
    assert decoded == snapshot
    assert set(decoded.keys()) == _EXPECTED_SNAPSHOT_TOP_LEVEL_KEYS

    validate_decision_packet_snapshot_v1(decoded)
    assert decision_packet_from_snapshot_v1(snapshot) == decision_packet_from_snapshot_v1(decoded)
