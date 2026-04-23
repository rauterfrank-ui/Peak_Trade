# src/trading/master_v2/decision_packet_roundtrip_v1.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from .decision_packet_snapshot_v1 import (
    decision_packet_from_snapshot_v1,
    decision_packet_to_snapshot_v1,
)
from .decision_packet_v1 import (
    MasterV2DecisionPacketV1,
    validate_master_v2_decision_packet_v1,
)

DECISION_PACKET_ROUNDTRIP_LAYER_VERSION = "v1"


@dataclass
class MasterV2DecisionPacketRoundtripResultV1:
    layer_version: str
    ok: bool
    reason_codes: Tuple[str, ...] = ()
    snapshot: Dict[str, Any] = field(default_factory=dict)


def roundtrip_master_v2_decision_packet_v1(
    p: MasterV2DecisionPacketV1, *, require_valid: bool = True
) -> MasterV2DecisionPacketRoundtripResultV1:
    v = validate_master_v2_decision_packet_v1(p)
    if require_valid and not v.ok:
        return MasterV2DecisionPacketRoundtripResultV1(
            layer_version=DECISION_PACKET_ROUNDTRIP_LAYER_VERSION,
            ok=False,
            reason_codes=tuple([*v.reason_codes, "ROUNDTRIP_SKIPPED_INVALID"]),
        )
    snap = decision_packet_to_snapshot_v1(p, require_consistent_packet=require_valid)
    p2 = decision_packet_from_snapshot_v1(snap)
    if p2 != p:
        return MasterV2DecisionPacketRoundtripResultV1(
            layer_version=DECISION_PACKET_ROUNDTRIP_LAYER_VERSION,
            ok=False,
            reason_codes=("ROUNDTRIP_PACKET_MISMATCH",),
            snapshot=snap,
        )
    return MasterV2DecisionPacketRoundtripResultV1(
        layer_version=DECISION_PACKET_ROUNDTRIP_LAYER_VERSION, ok=True, snapshot=snap
    )
