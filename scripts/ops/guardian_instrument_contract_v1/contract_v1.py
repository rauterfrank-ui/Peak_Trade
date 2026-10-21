"""Thirty instrument contracts. AUTHORITY=NONE.

Contracts are derived from the parent-slot registry. Missing domain evidence
stays missing. Optimization scope does not by itself bind or calibrate an instrument.
"""

from __future__ import annotations

from typing import Any

from scripts.ops.guardian_parent_slot_loader_v1.load_v1 import load_parent_slots_v1
from scripts.ops.pin_scope_binding_v1.constants_v1 import SCOPE_FIELDS

DISPLAY_NAMES = {
    "PARENT_MASTER_V2": "Master V2",
    "PARENT_EXECUTION": "Execution",
    "PARENT_SELF_LEARNING": "Self-Learning",
    "PARENT_OPTIMIZATION": "Optimization",
    "PARENT_MARKET_INTELLIGENCE": "Market Intelligence",
    "PARENT_SELECTION": "Selection",
    "PARENT_MARKET_OBSERVATION": "Market Observation",
    "PARENT_CAPITAL": "Capital",
    "PARENT_SAFETY": "Safety",
    "PARENT_ORCHESTRATION": "Orchestration",
}
INSTRUMENT_SPECS = (
    ("ghv_id", "DOMAIN_GHV", "GHV", "scoped_ghv_crosswalk_adapter_v1.run_scoped_ghv_v1"),
    (
        "causal_graph_id",
        "DOMAIN_CURRENT_CAUSAL_GRAPH",
        "CURRENT Causal Graph",
        "scoped_causal_graph_adapter_v1.run_scoped_causal_graph_v1",
    ),
    ("ghosv_id", "DOMAIN_GHOSV", "GHOSV", "generic_ghosv_kernel_v1.run_generic_ghosv_v1"),
)
_BOUNDARIES = {
    "PARENT_MASTER_V2": (
        "Master V2 including Double Play. Membership, nodes, and edges are not evidenced here."
    ),
    "PARENT_EXECUTION": (
        "Execution boundary. The existing Execution observer stays outside this registry."
    ),
    "PARENT_SELF_LEARNING": "Self-Learning boundary. Domain membership is not evidenced here.",
    "PARENT_OPTIMIZATION": (
        "Provisional Option-2 scope. Membership is not ratified and four findings stay open."
    ),
    "PARENT_MARKET_INTELLIGENCE": (
        "Market Intelligence boundary. Domain membership is not evidenced here."
    ),
    "PARENT_SELECTION": "Selection boundary. Domain membership is not evidenced here.",
    "PARENT_MARKET_OBSERVATION": (
        "Market Observation boundary. Domain membership is not evidenced here."
    ),
    "PARENT_CAPITAL": "Capital boundary. Domain membership is not evidenced here.",
    "PARENT_SAFETY": "Safety boundary. Domain membership is not evidenced here.",
    "PARENT_ORCHESTRATION": (
        "Orchestration and Full-Core boundary. Full-Core is not an Orchestration member."
    ),
}


def build_instrument_registry_v1() -> dict[str, Any]:
    """Return thirty disabled instrument contracts, or a rejection when the slots fail."""
    loaded = load_parent_slots_v1()
    if loaded["status"] != "ACCEPTED":
        return {
            "status": "REJECTED",
            "authority": "NONE",
            "instrument_count": 0,
            "instruments": [],
            "reasons": list(loaded["reasons"]),
        }
    instruments: list[dict[str, Any]] = []
    reasons: list[str] = []
    for slot in loaded["slots"]:
        parent_id = str(slot["parent_id"])
        display = DISPLAY_NAMES.get(parent_id)
        if display is None:
            reasons.append(f"display_name_missing:{parent_id}")
            continue
        evidence_status = (
            "PROVISIONAL_SCOPE_PRESENT" if parent_id == "PARENT_OPTIMIZATION" else "MISSING"
        )
        for key, instrument_type, suffix, adapter in INSTRUMENT_SPECS:
            instrument_id = str(slot[key])
            instruments.append(
                {
                    "instrument_id": instrument_id,
                    "instrument_type": instrument_type,
                    "parent_id": parent_id,
                    "display_name": f"{display} {suffix}",
                    "adapter": adapter,
                    "domain_boundary": _BOUNDARIES[parent_id],
                    "scope": {field: list(slot["scope"][field]) for field in SCOPE_FIELDS},
                    "evidence_status": evidence_status,
                    "provenance_requirements": _provenance_requirements(evidence_status),
                    "coverage": _coverage(evidence_status),
                    "authority": "NONE",
                    "trading_authority": "NONE",
                    "safety_authority": "NONE",
                    "execution_authority": "NONE",
                    "post_authority": "NONE",
                    "activation": "DISABLED",
                    "guardian_ratified": False,
                    "membership_ratified": False,
                    "technical_state": "TECHNICALLY_PREPARED",
                    "domain_bound": False,
                    "domain_calibrated": False,
                    "current_validated": False,
                    "operationally_ready": False,
                }
            )
    ids = [item["instrument_id"] for item in instruments]
    if len(ids) != 30 or len(set(ids)) != 30:
        reasons.append("instrument_identity_not_unique")
    if reasons:
        return {
            "status": "REJECTED",
            "authority": "NONE",
            "instrument_count": 0,
            "instruments": [],
            "reasons": reasons,
        }
    return {
        "status": "ACCEPTED",
        "authority": "NONE",
        "instrument_count": 30,
        "instruments": instruments,
        "reasons": [],
    }


def _provenance_requirements(evidence_status: str) -> dict[str, Any]:
    return {
        "domain_evidence_required": True,
        "domain_evidence_present": evidence_status == "PROVISIONAL_SCOPE_PRESENT",
        "census_currency_when_embedded_pin_differs": "HISTORICAL",
        "graph_currency_until_current_graph_exists": "ABSENT",
        "current_validated": False,
    }


def _coverage(evidence_status: str) -> dict[str, Any]:
    reason = (
        "provisional_unknown_reachability"
        if evidence_status == "PROVISIONAL_SCOPE_PRESENT"
        else "missing_domain_evidence"
    )
    return {
        "coverage_gap": True,
        "coverage_proof": False,
        "reachability": "UNKNOWN"
        if evidence_status == "PROVISIONAL_SCOPE_PRESENT"
        else "NOT_EVIDENCED",
        "current_validated": False,
        "reason": reason,
    }
