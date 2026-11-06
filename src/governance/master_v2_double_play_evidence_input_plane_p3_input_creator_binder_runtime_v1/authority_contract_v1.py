"""Non-interference and authority boundary checks for P3 Component B runtime."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    ContractValidationResultV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.constants_v1 import (
    A_RUNTIME_REACHABLE,
    B_AUTHORITY,
    B_DP_STATE_MUTATION_AUTHORITY,
    B_RUNTIME_IMPLEMENTATION_AUTHORIZED,
    B_RUNTIME_REACHABLE,
    B_TRADING_AUTHORITY,
    EXTERNAL_EFFECT_AUTHORIZED,
    IMPLEMENTS_COMPONENT_B_RUNTIME,
    OWNER_DECISION_CONFIG,
    P3_PACKAGE_PATH_MARKER,
    PRODUCTIVE_ACTIVATION_AUTHORIZED,
    PRODUCTIVE_L6_BINDING_AUTHORIZED,
    WORKPACKAGE_ID,
)

_FORBIDDEN_IMPORT_MARKERS: tuple[str, ...] = (
    "trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.runtime",
    "current_productive_master_v2_runtime_cycle_v1",
    "apply_l6",
    "src.execution",
    "src.risk",
)

_FORBIDDEN_EMIT_MARKERS: tuple[str, ...] = (
    "ENTER_LONG",
    "ENTER_SHORT",
    "SideState",
    "canonical_order_intent",
    "execution_permit",
    "proposed_d_t",
)


def _fail(*codes: str) -> ContractValidationResultV1:
    return ContractValidationResultV1(ok=False, failure_codes=tuple(dict.fromkeys(codes)))


def _ok() -> ContractValidationResultV1:
    return ContractValidationResultV1(ok=True, failure_codes=())


def validate_p3_owner_decision_config_v1(
    repo_root: Path | None = None,
) -> ContractValidationResultV1:
    root = repo_root or Path(__file__).resolve().parents[3]
    path = root / OWNER_DECISION_CONFIG
    if not path.is_file():
        return _fail("owner_decision_missing")
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "workpackage_id": WORKPACKAGE_ID,
        "b_runtime_implemented": True,
        "b_runtime_implementation_authorized": False,
        "b_runtime_reachable": False,
        "a_runtime_reachable": False,
        "productive_activation_authorized": False,
        "productive_l6_binding_authorized": False,
    }
    for key, expected in required.items():
        if payload.get(key) != expected:
            return _fail("owner_decision_drift")
    return _ok()


def validate_component_b_runtime_authority_contract_v1() -> ContractValidationResultV1:
    failures: list[str] = []
    if B_AUTHORITY != "BOUNDED_DP_INPUT_CREATION_AND_BINDING_ONLY":
        failures.append("b_authority_drift")
    if B_TRADING_AUTHORITY != "NONE" or B_DP_STATE_MUTATION_AUTHORITY != "NONE":
        failures.append("b_trading_or_dp_authority_forbidden")
    if not IMPLEMENTS_COMPONENT_B_RUNTIME:
        failures.append("b_runtime_not_implemented")
    if B_RUNTIME_IMPLEMENTATION_AUTHORIZED or B_RUNTIME_REACHABLE:
        failures.append("productive_b_gate_forbidden")
    if A_RUNTIME_REACHABLE:
        failures.append("productive_a_reachability_forbidden")
    if PRODUCTIVE_ACTIVATION_AUTHORIZED or PRODUCTIVE_L6_BINDING_AUTHORIZED:
        failures.append("productive_binding_forbidden")
    if EXTERNAL_EFFECT_AUTHORIZED:
        failures.append("external_effect_forbidden")
    if failures:
        return _fail(*failures)
    return _ok()


def scan_component_b_package_non_interference_v1(
    repo_root: Path | None = None,
) -> tuple[bool, tuple[str, ...]]:
    root = repo_root or Path(__file__).resolve().parents[3]
    pkg = root / "src" / "governance" / P3_PACKAGE_PATH_MARKER
    hits: list[str] = []
    for py in pkg.rglob("*.py"):
        if py.name == "authority_contract_v1.py":
            continue
        text = py.read_text(encoding="utf-8", errors="replace")
        rel = py.relative_to(root).as_posix()
        for marker in _FORBIDDEN_EMIT_MARKERS:
            if marker in text:
                hits.append(f"{rel}:{marker}")
        try:
            tree = ast.parse(text, filename=rel)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    _check_import(alias.name, rel, hits)
            elif isinstance(node, ast.ImportFrom) and node.module:
                _check_import(node.module, rel, hits)
    return (len(hits) == 0, tuple(sorted(set(hits))))


def _check_import(module: str, rel: str, hits: list[str]) -> None:
    for forbidden in _FORBIDDEN_IMPORT_MARKERS:
        if module.startswith(forbidden) or forbidden in module:
            hits.append(f"{rel}:import:{module}")
