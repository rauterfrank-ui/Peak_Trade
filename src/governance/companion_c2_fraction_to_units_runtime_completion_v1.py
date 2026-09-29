"""Governed Companion C2 runtime completion scaffold v1 (fail-closed)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final, Mapping

from src.ops.companion_shadow_live_fraction_to_units_input_binding_v1 import (
    runtime_conversion_v1,
)

DECISION_CONFIG: Final[str] = (
    "config/governance/companion_c2_fraction_to_units_runtime_completion_v1_decision_v1.json"
)
WORKPACKAGE_ID: Final[str] = "COMPANION_C2_FRACTION_TO_UNITS_RUNTIME_COMPLETION_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/COMPANION_C2_FRACTION_TO_UNITS_RUNTIME_COMPLETION_V1.md"
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


def load_decision_v1(*, repo_root: Path | None = None) -> Mapping[str, Any]:
    root = repo_root or _REPO_ROOT
    return json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))


def prove_companion_c2_runtime_completion_scaffold_v1(
    *, repo_root: Path | None = None
) -> Mapping[str, Any]:
    decision = load_decision_v1(repo_root=repo_root)
    if decision.get("workpackage_id") != WORKPACKAGE_ID:
        raise RuntimeError("WORKPACKAGE_ID_MISMATCH")
    for key, expected in (
        ("companion_runtime_conversion_enabled", False),
        ("runtime_conversion_implemented", False),
        ("shadow_session_binding_present", False),
        ("live_session_binding_present", False),
        ("next_productive_conversion_slice_authorized", False),
        ("c2_authority_added", False),
        ("external_effect_authorized", False),
        ("post_allowed", False),
        ("real_venue_post_allowed", False),
        ("signal_to_orders_mutated", False),
    ):
        if decision.get(key) is not expected:
            raise RuntimeError(f"DECISION_PIN_DRIFT:{key}")
    if runtime_conversion_v1.COMPANION_RUNTIME_CONVERSION_ENABLED is not False:
        raise RuntimeError("RUNTIME_ENABLED_PIN_DRIFT")
    if runtime_conversion_v1.NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED is not False:
        raise RuntimeError("CONVERSION_SLICE_PIN_DRIFT")
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "scaffold_proven": True,
        "runtime_conversion_implemented": False,
        "next_genuine_blocker": decision.get("next_genuine_blocker"),
    }
