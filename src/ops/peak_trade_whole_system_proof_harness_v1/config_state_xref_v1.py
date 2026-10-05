"""Config / state cross-reference for operation proof (observational)."""

from __future__ import annotations

from typing import Any

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)


def build_config_state_xref_v1() -> dict[str, Any]:
    items: list[dict[str, Any]] = [
        {
            "ITEM": "EXTERNAL_EFFECT_AUTHORIZED",
            "SOURCE_OF_TRUTH": "src/ops/full_core_live_path_composition_root_v1/constants_v1.py",
            "CURRENT_VALUE": EXTERNAL_EFFECT_AUTHORIZED,
            "REQUIRED_VALUE": False,
            "RUNTIME_MUTABILITY": "STATIC_INVARIANT",
            "SEMANTIC_OWNER": "full_core_live_path_composition_root_v1",
        },
        {
            "ITEM": "POST_ALLOWED",
            "CURRENT_VALUE": POST_ALLOWED,
            "REQUIRED_VALUE": False,
            "RUNTIME_MUTABILITY": "STATIC_INVARIANT",
        },
        {
            "ITEM": "REAL_VENUE_POST_ALLOWED",
            "CURRENT_VALUE": REAL_VENUE_POST_ALLOWED,
            "REQUIRED_VALUE": False,
            "RUNTIME_MUTABILITY": "STATIC_INVARIANT",
        },
        {
            "ITEM": "CLI --max-cycles",
            "SOURCE_OF_TRUTH": "launcher argparse",
            "RUNTIME_MUTABILITY": "RUNTIME_ARGUMENT",
            "REQUIRED_FOR_OPERATION": True,
        },
        {
            "ITEM": "lane ledger root",
            "SOURCE_OF_TRUTH": "CLI --ledger-root",
            "PERSISTENCE_SCOPE": "bounded_lane_state",
            "RUNTIME_MUTABILITY": "RUNTIME_ARGUMENT",
        },
        {
            "ITEM": "CAP24 selection state",
            "PERSISTENCE_SCOPE": "selection_binding_epoch",
            "RUNTIME_MUTABILITY": "PERSISTED",
        },
    ]
    conflicts = [
        i for i in items if "REQUIRED_VALUE" in i and i.get("CURRENT_VALUE") != i["REQUIRED_VALUE"]
    ]
    return {
        "CONFIG_STATE_ITEMS": items,
        "CONFLICTS": conflicts,
        "UNUSED_SETTINGS_DETECTED": [],
    }
