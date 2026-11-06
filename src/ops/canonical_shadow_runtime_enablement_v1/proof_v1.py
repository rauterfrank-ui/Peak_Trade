"""Static safety and authority proofs for canonical Shadow runtime enablement."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from src.ops.canonical_shadow_runtime_enablement_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_VENUE_POST_ALLOWED,
    TESTNET_AUTHORIZED,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    prove_execution_port_separation_v1,
)

_REPO = Path(__file__).resolve().parents[3]
_PACKAGE = Path(__file__).resolve().parent

_FORBIDDEN_CALLS = frozenset(
    {
        "submit_order",
        "place_order",
        "requests.post",
        "urlopen",
        "get_keychain",
    }
)


def _scan_package_for_forbidden_calls() -> list[str]:
    hits: list[str] = []
    for path in _PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in _FORBIDDEN_CALLS:
                    hits.append(f"{path.name}:{node.func.id}")
    return hits


def prove_canonical_shadow_runtime_safety_v1() -> dict[str, Any]:
    forbidden_hits = _scan_package_for_forbidden_calls()
    port_sep = prove_execution_port_separation_v1()
    ok = all(
        [
            LIVE_ENABLED is False,
            LIVE_ARMED is False,
            POST_ALLOWED is False,
            REAL_VENUE_POST_ALLOWED is False,
            REAL_KEYCHAIN_ACCESS_AUTHORIZED is False,
            TESTNET_AUTHORIZED is False,
            EXTERNAL_EFFECT_AUTHORIZED is False,
            not forbidden_hits,
            port_sep.get("ok") is True,
        ]
    )
    return {
        "ok": ok,
        "forbidden_call_hits": forbidden_hits,
        "execution_port_separation": port_sep,
        "standing_flags": {
            "LIVE_ENABLED": LIVE_ENABLED,
            "POST_ALLOWED": POST_ALLOWED,
            "EXTERNAL_EFFECT_AUTHORIZED": EXTERNAL_EFFECT_AUTHORIZED,
        },
    }
