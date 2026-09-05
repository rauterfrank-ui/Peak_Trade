"""Overclaim guards for FULL_CORE_LIVE_PATH vs canary venue-proof."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY,
    CANARY_VENUE_PROOF_PATH_IS_FULL_CORE_E2E,
    CURRENT_LIVE_CORE_PATH_PROVEN,
    FORBIDDEN_IMPORT_TOKENS,
    FULL_CORE_RESTART_TEST_AUTHORIZED,
    FULL_CORE_SYSTEM_E2E_PROVEN,
    FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH,
    LIVE_ARMED,
    LIVE_ENABLED,
    STANDING_LIVE_AUTHORIZATION,
    WIRE_SEND_PERMITTED,
)

_PACKAGE_DIR = Path(__file__).resolve().parent


def prove_package_does_not_import_wire_surfaces_v1() -> dict[str, Any]:
    unexpected: list[str] = []
    hits: list[str] = []
    for path in sorted(_PACKAGE_DIR.glob("*.py")):
        if path.name in {"constants_v1.py", "overclaim_guards_v1.py"}:
            continue
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_IMPORT_TOKENS:
            if token in text:
                hits.append(f"{path.name}:{token}")
                if token == "construct_live_execution_port_v1" and path.name == (
                    "execution_boundary_v1.py"
                ):
                    continue
                unexpected.append(f"{path.name}:{token}")
    return {
        "ok": not unexpected,
        "hits": hits,
        "unexpected": unexpected,
        "WIRE_SEND_OCCURRED": False,
        "LIVE_ENABLED": LIVE_ENABLED,
        "LIVE_ARMED": LIVE_ARMED,
        "WIRE_SEND_PERMITTED": WIRE_SEND_PERMITTED,
        "CURRENT_LIVE_CORE_PATH_PROVEN": CURRENT_LIVE_CORE_PATH_PROVEN,
        "FULL_CORE_SYSTEM_E2E_PROVEN": FULL_CORE_SYSTEM_E2E_PROVEN,
        "FULL_CORE_RESTART_TEST_AUTHORIZED": FULL_CORE_RESTART_TEST_AUTHORIZED,
        "FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH": FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH,
        "CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY": (
            CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY
        ),
        "CANARY_VENUE_PROOF_PATH_IS_FULL_CORE_E2E": CANARY_VENUE_PROOF_PATH_IS_FULL_CORE_E2E,
        "STANDING_LIVE_AUTHORIZATION": STANDING_LIVE_AUTHORIZATION,
    }


def restart_gate_v1(*, full_core_live_path_bound: bool, offline_full_chain_proven: bool) -> bool:
    if CURRENT_LIVE_CORE_PATH_PROVEN is True:
        return False
    if FULL_CORE_SYSTEM_E2E_PROVEN is True:
        return False
    if full_core_live_path_bound is not True:
        return False
    if offline_full_chain_proven is not True:
        return False
    return FULL_CORE_RESTART_TEST_AUTHORIZED
