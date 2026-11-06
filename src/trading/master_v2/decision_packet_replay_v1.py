# src/trading/master_v2/decision_packet_replay_v1.py
from __future__ import annotations

from typing import Any, Dict, Mapping, Tuple

from .decision_packet_roundtrip_v1 import roundtrip_master_v2_decision_packet_v1
from .decision_packet_snapshot_v1 import decision_packet_from_snapshot_v1
from .decision_packet_v1 import MasterV2DecisionPacketV1

DECISION_PACKET_REPLAY_LAYER_VERSION = "v1"

__all__ = [
    "DECISION_PACKET_REPLAY_LAYER_VERSION",
    "decision_packet_from_snapshot_v1",
    "decision_packet_roundtrip_v1",
]


def decision_packet_roundtrip_v1(
    p: MasterV2DecisionPacketV1,
) -> Tuple[bool, Dict[str, Any], Tuple[str, ...]]:
    r = roundtrip_master_v2_decision_packet_v1(p, require_valid=True)
    if not r.ok:
        return False, r.snapshot, r.reason_codes
    return True, r.snapshot, ()
