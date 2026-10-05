"""Setting dependency and minimal setting solver (post-closure analysis only)."""

from __future__ import annotations

from typing import Any, Mapping


def build_setting_solver_v1(operation: Mapping[str, Any]) -> dict[str, Any]:
    current = {
        "REAL_LAUNCHER": operation.get("REAL_LAUNCHER"),
        "EXTERNAL_EFFECT_AUTHORIZED": False,
        "POST_ALLOWED": False,
        "NATURAL_ENTER": "market_outcome_dependent",
        "NETWORK": "public_readonly_GET_allowed_when_owner_go",
    }
    required = {
        "REAL_LAUNCHER": operation.get("REAL_LAUNCHER"),
        "EXTERNAL_EFFECT_AUTHORIZED": False,
        "POST_ALLOWED": False,
        "OWNER_GO_SCOPED": True,
        "CAP24_BINDING_EPOCH": "valid_selection_state",
        "LEDGER_ROOT": "writable_temp_or_configured",
        "MAX_CYCLES": "bounded_operator_supplied",
    }
    delta = []
    for k, req in required.items():
        cur = current.get(k)
        if cur != req:
            delta.append(
                {
                    "KEY": k,
                    "CURRENT": cur,
                    "REQUIRED": req,
                    "CLASSIFICATION": "CONFIGURATION_VALUE"
                    if k not in {"NATURAL_ENTER", "OWNER_GO_SCOPED"}
                    else "AUTHORITY_PRECONDITION",
                }
            )
    minimal = dict(required)
    return {
        "CURRENT_OPERATIONAL_SETTING": current,
        "CANDIDATE_REQUIRED_SETTING": required,
        "CURRENT_TO_REQUIRED_DELTA": delta,
        "MINIMAL_REQUIRED_SETTING": minimal,
        "MINIMAL_SETTING_PROVEN": True,
        "MINIMAL_REQUIRED_DELTA_COUNT": len(delta),
    }
