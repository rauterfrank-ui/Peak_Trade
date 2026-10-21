"""Load ten disabled parent slots. Rejects activation, authority, and ratification."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.optimization_guardian_scope_v1.scope_v1 import build_optimization_scope_v1
from scripts.ops.pin_scope_binding_v1.constants_v1 import SCOPE_FIELDS

_REPO_ROOT = Path(__file__).resolve().parents[3]
_REGISTRY = _REPO_ROOT / "config/governance/guardian_parent_slot_registry_v1.json"
_PARENT_IDS = (
    "PARENT_MASTER_V2",
    "PARENT_EXECUTION",
    "PARENT_SELF_LEARNING",
    "PARENT_OPTIMIZATION",
    "PARENT_MARKET_INTELLIGENCE",
    "PARENT_SELECTION",
    "PARENT_MARKET_OBSERVATION",
    "PARENT_CAPITAL",
    "PARENT_SAFETY",
    "PARENT_ORCHESTRATION",
)
_FORBIDDEN_IMPORTS = (
    "ghosv_bounded_context_v1",
    "execution_guardian_binding_verifier_v1",
    "ghosv_master_v2_bounded_context_v1",
    "double_play_ghosv_observation_adapter_v1",
)


def load_parent_slots_v1(registry_path: Path | None = None) -> dict[str, Any]:
    path = _REGISTRY if registry_path is None else registry_path
    document = json.loads(path.read_text(encoding="utf-8"))
    reasons = _reasons(document)
    slots = list(document.get("slots") or [])
    return {
        "status": "ACCEPTED" if not reasons else "REJECTED",
        "authority": "NONE",
        "activation": "DISABLED",
        "guardian_ratified": False,
        "gcc_role": (document.get("gcc") or {}).get("role"),
        "parent_count": len(slots) if not reasons else 0,
        "slots": slots if not reasons else [],
        "reasons": reasons,
        "runtime_connection": False,
    }


def _reasons(document: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    gcc = document.get("gcc")
    if not isinstance(gcc, Mapping) or gcc.get("role") != "COORDINATION_ONLY":
        reasons.append("gcc_not_coordination_only")
    if gcc.get("guardian") if isinstance(gcc, Mapping) else True:
        reasons.append("gcc_is_guardian")
    slots = document.get("slots")
    if not isinstance(slots, list) or len(slots) != 10:
        reasons.append("parent_count")
        return reasons
    ids = [slot.get("parent_id") for slot in slots if isinstance(slot, Mapping)]
    if ids != list(_PARENT_IDS):
        reasons.append("parent_ids")
    expected_optimization = build_optimization_scope_v1()
    for slot in slots:
        if not isinstance(slot, Mapping):
            reasons.append("slot_not_object")
            continue
        parent_id = str(slot.get("parent_id") or "")
        if slot.get("activation") != "DISABLED":
            reasons.append(f"activation:{parent_id}")
        if slot.get("authority") != "NONE":
            reasons.append(f"authority:{parent_id}")
        if slot.get("guardian_ratified") is not False:
            reasons.append(f"ratified:{parent_id}")
        if slot.get("runtime_connection") is not False:
            reasons.append(f"runtime:{parent_id}")
        for key in ("ghv_id", "causal_graph_id", "ghosv_id"):
            if not isinstance(slot.get(key), str) or not str(slot.get(key)).startswith(parent_id):
                reasons.append(f"instrument:{parent_id}:{key}")
        scope = slot.get("scope")
        if not isinstance(scope, Mapping):
            reasons.append(f"scope:{parent_id}")
            continue
        if parent_id == "PARENT_OPTIMIZATION":
            if slot.get("membership_ratified") is not False:
                reasons.append("optimization_membership_ratified")
            if slot.get("calibration_status") != "PROVISIONAL_BOUND":
                reasons.append("optimization_calibration_status")
            for field in SCOPE_FIELDS:
                if list(scope.get(field) or []) != expected_optimization[field]:
                    reasons.append(f"optimization_scope:{field}")
            continue
        if slot.get("calibration_status") != "UNCALIBRATED":
            reasons.append(f"calibrated:{parent_id}")
        if slot.get("membership_ratified") is not False:
            reasons.append(f"membership:{parent_id}")
        for field in SCOPE_FIELDS:
            if list(scope.get(field) or []):
                reasons.append(f"membership_present:{parent_id}:{field}")
    source_imports = [
        line
        for line in Path(__file__).read_text(encoding="utf-8").splitlines()
        if line.startswith("import ") or line.startswith("from ")
    ]
    for banned in _FORBIDDEN_IMPORTS:
        if any(banned in line for line in source_imports):
            reasons.append(f"forbidden_import:{banned}")
    return reasons
