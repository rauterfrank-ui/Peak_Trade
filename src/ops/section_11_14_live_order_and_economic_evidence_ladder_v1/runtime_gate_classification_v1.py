"""Repo-default Live-gate inspection. Does not mutate any gate."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    CANARY_SUBMIT_TRANSPORT_ACTIVATED,
    ENABLE_LIVE_TRADING,
    GENERAL_LIVE_SUBMIT_UNLOCKED,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_CANARY_MINIMUM_EXPOSURE_AUTHORIZED_DEFAULT,
    LIVE_ENABLED,
    LIVE_ORDER_AUTHORIZED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    SECTION_11_14_AUTHORIZED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.path_reachable_predicate_v1 import (
    ROLE_NOT_PART_OF_REACHABILITY,
    ROLE_REQUIRED_ONLY_FOR_LATER_LADDER_STAGE,
    ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION,
)

_GATE_SPECS: tuple[tuple[str, bool, str], ...] = (
    ("LIVE_AUTHORIZED", LIVE_AUTHORIZED, ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION),
    ("LIVE_ENABLED", LIVE_ENABLED, ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION),
    ("LIVE_ARMED", LIVE_ARMED, ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION),
    ("LIVE_ORDER_AUTHORIZED", LIVE_ORDER_AUTHORIZED, ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION),
    ("ENABLE_LIVE_TRADING", ENABLE_LIVE_TRADING, ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION),
    ("SUBMIT_UNLOCKED", SUBMIT_UNLOCKED, ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION),
    (
        "GENERAL_LIVE_SUBMIT_UNLOCKED",
        GENERAL_LIVE_SUBMIT_UNLOCKED,
        ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION,
    ),
    (
        "CANARY_AUTHORIZED",
        CANARY_AUTHORIZED,
        ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION,
    ),
    (
        "LIVE_CANARY_MINIMUM_EXPOSURE_AUTHORIZED_DEFAULT",
        LIVE_CANARY_MINIMUM_EXPOSURE_AUTHORIZED_DEFAULT,
        ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION,
    ),
    ("TESTNET_AUTHORIZED", TESTNET_AUTHORIZED, ROLE_NOT_PART_OF_REACHABILITY),
    (
        "SECTION_11_14_AUTHORIZED",
        SECTION_11_14_AUTHORIZED,
        ROLE_REQUIRED_ONLY_FOR_LATER_LADDER_STAGE,
    ),
    (
        "CANARY_SUBMIT_TRANSPORT_ACTIVATED",
        CANARY_SUBMIT_TRANSPORT_ACTIVATED,
        ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION,
    ),
)


def classify_runtime_gates_v1() -> dict[str, Any]:
    rows = []
    for name, default, role in _GATE_SPECS:
        rows.append(
            {
                "name": name,
                "repo_default": bool(default),
                "implementation_status": "IMPLEMENTED",
                "configured_default": bool(default),
                "current_runtime_proven": False,
                "current_external_proven": False,
                "observation_status": "NOT_OBSERVED_AS_RUNTIME_TRUE",
                "reachability_role": role,
                "mutated_by_this_go": False,
            }
        )
    return {
        "schema_version": "section_11_14_runtime_gate_classification.v1",
        "mutation_performed": False,
        "all_standing_live_submit_gates_false": all(
            row["repo_default"] is False
            for row in rows
            if row["reachability_role"] == ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION
        ),
        "rows": rows,
    }
