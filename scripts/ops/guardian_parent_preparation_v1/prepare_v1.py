"""Prepare ten disabled parents and thirty instrument contracts. AUTHORITY=NONE.

This module does not import Execution observers, does not invent membership,
and does not call the generic adapters.
"""

from __future__ import annotations

from typing import Any

from scripts.ops.guardian_instrument_contract_v1.contract_v1 import build_instrument_registry_v1
from scripts.ops.guardian_parent_slot_loader_v1.load_v1 import load_parent_slots_v1


def prepare_parent_guardians_v1() -> dict[str, Any]:
    """Return the technical preparation for every parent slot."""
    loaded = load_parent_slots_v1()
    registry = build_instrument_registry_v1()
    if loaded["status"] != "ACCEPTED" or registry["status"] != "ACCEPTED":
        return {
            "status": "REJECTED",
            "authority": "NONE",
            "parent_count": 0,
            "instrument_count": 0,
            "parents": [],
            "reasons": list(loaded["reasons"]) + list(registry["reasons"]),
        }
    by_parent: dict[str, list[dict[str, Any]]] = {}
    for instrument in registry["instruments"]:
        by_parent.setdefault(str(instrument["parent_id"]), []).append(instrument)
    parents: list[dict[str, Any]] = []
    for slot in loaded["slots"]:
        parent_id = str(slot["parent_id"])
        instruments = by_parent.get(parent_id, [])
        parents.append(
            {
                "parent_id": parent_id,
                "label": slot["label"],
                "domain_boundary": instruments[0]["domain_boundary"] if instruments else "",
                "activation": "DISABLED",
                "authority": "NONE",
                "trading_authority": "NONE",
                "safety_authority": "NONE",
                "execution_authority": "NONE",
                "post_authority": "NONE",
                "guardian_ratified": False,
                "membership_ratified": False,
                "calibration_status": slot["calibration_status"],
                "technical_state": "TECHNICALLY_PREPARED",
                "domain_bound": False,
                "domain_calibrated": False,
                "current_validated": False,
                "operationally_ready": False,
                "instruments": instruments,
            }
        )
    return {
        "status": "ACCEPTED",
        "authority": "NONE",
        "gcc_role": "COORDINATION_ONLY",
        "trading_authority": "NONE",
        "safety_authority": "NONE",
        "post_authority": "NONE",
        "sub_guardian_count": 0,
        "parent_count": len(parents),
        "instrument_count": len(registry["instruments"]),
        "parents": parents,
        "reasons": [],
    }
