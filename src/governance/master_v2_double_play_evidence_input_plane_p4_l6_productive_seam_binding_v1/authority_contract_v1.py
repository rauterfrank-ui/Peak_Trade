"""Authority and non-interference checks for P4 productive L6 seam binding."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    ContractValidationResultV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.constants_v1 import (
    A_RUNTIME_IMPLEMENTATION_AUTHORIZED,
    A_RUNTIME_REACHABLE,
    B_RUNTIME_IMPLEMENTATION_AUTHORIZED,
    B_RUNTIME_REACHABLE,
    EXTERNAL_EFFECT_AUTHORIZED,
    FINAL_D_T_FORMULA_SELECTED,
    L6_PRODUCTIVE_BINDING,
    L6_SEMANTIC_AUTHORITY,
    OWNER_DECISION_CONFIG,
    P4_PACKAGE_PATH_MARKER,
    PRODUCTIVE_ACTIVATION_AUTHORIZED,
    PRODUCTIVE_DP_SEAM_BOUND,
    PRODUCTIVE_L6_BINDING_AUTHORIZED,
    WORKPACKAGE_ID,
)

_FORBIDDEN_IMPORT_MARKERS: tuple[str, ...] = (
    "current_productive_master_v2_runtime_cycle_v1",
    "src.execution",
    "src.risk",
)

_FORBIDDEN_EMIT_MARKERS: tuple[str, ...] = (
    "ENTER_LONG",
    "ENTER_SHORT",
    "SideState",
    "canonical_order_intent",
    "execution_permit",
)

_MECHANICAL_CONSUMPTION_MODULE = "l6_mechanical_consumption_v1.py"


def _fail(*codes: str) -> ContractValidationResultV1:
    return ContractValidationResultV1(ok=False, failure_codes=tuple(dict.fromkeys(codes)))


def _ok() -> ContractValidationResultV1:
    return ContractValidationResultV1(ok=True, failure_codes=())


def validate_p4_owner_decision_config_v1(
    repo_root: Path | None = None,
) -> ContractValidationResultV1:
    root = repo_root or Path(__file__).resolve().parents[3]
    path = root / OWNER_DECISION_CONFIG
    if not path.is_file():
        return _fail("owner_decision_missing")
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "workpackage_id": WORKPACKAGE_ID,
        "p4_first_approved_seam": "L6",
        "l6_external_evidence_admissibility": "YES_BOUNDED_TYPED_ONLY",
        "a_runtime_reachable": True,
        "b_runtime_reachable": True,
        "productive_l6_binding_authorized": True,
        "l6_productive_binding": True,
        "productive_dp_seam_bound": True,
        "productive_activation_authorized": False,
        "external_effect_authorized": False,
        "final_d_t_formula_selected": False,
    }
    for key, expected in required.items():
        if payload.get(key) != expected:
            return _fail("owner_decision_drift")
    return _ok()


def validate_productive_l6_seam_authority_contract_v1() -> ContractValidationResultV1:
    failures: list[str] = []
    if not PRODUCTIVE_L6_BINDING_AUTHORIZED or not L6_PRODUCTIVE_BINDING:
        failures.append("productive_l6_gate_missing")
    if not PRODUCTIVE_DP_SEAM_BOUND:
        failures.append("productive_dp_seam_not_bound")
    if not (A_RUNTIME_REACHABLE and B_RUNTIME_REACHABLE):
        failures.append("ab_reachability_missing")
    if not (A_RUNTIME_IMPLEMENTATION_AUTHORIZED and B_RUNTIME_IMPLEMENTATION_AUTHORIZED):
        failures.append("ab_implementation_authorization_missing")
    if PRODUCTIVE_ACTIVATION_AUTHORIZED:
        failures.append("blanket_productive_activation_forbidden")
    if EXTERNAL_EFFECT_AUTHORIZED:
        failures.append("external_effect_forbidden")
    if FINAL_D_T_FORMULA_SELECTED:
        failures.append("d_t_formula_selection_forbidden")
    if L6_SEMANTIC_AUTHORITY != "UNCHANGED":
        failures.append("l6_semantic_authority_drift")
    if failures:
        return _fail(*failures)
    return _ok()


def scan_p4_package_non_interference_v1(
    repo_root: Path | None = None,
) -> tuple[bool, tuple[str, ...]]:
    root = repo_root or Path(__file__).resolve().parents[3]
    pkg = root / "src" / "governance" / P4_PACKAGE_PATH_MARKER
    hits: list[str] = []
    for py in pkg.rglob("*.py"):
        if py.name == "authority_contract_v1.py":
            continue
        text = py.read_text(encoding="utf-8", errors="replace")
        rel = py.relative_to(root).as_posix()
        for marker in _FORBIDDEN_EMIT_MARKERS:
            if marker in text:
                hits.append(f"{rel}:{marker}")
        if py.name != _MECHANICAL_CONSUMPTION_MODULE and "typed_payload_digest" in text:
            if "validate_l6" not in text and "admission" not in text:
                hits.append(f"{rel}:typed_payload_digest_interpretation_risk")
        try:
            tree = ast.parse(text, filename=rel)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    _check_import(alias.name, rel, py.name, hits)
            elif isinstance(node, ast.ImportFrom) and node.module:
                _check_import(node.module, rel, py.name, hits)
    return (len(hits) == 0, tuple(sorted(set(hits))))


def _check_import(module: str, rel: str, filename: str, hits: list[str]) -> None:
    for forbidden in _FORBIDDEN_IMPORT_MARKERS:
        if module.startswith(forbidden) or forbidden in module:
            hits.append(f"{rel}:import:{module}")
    if (
        filename != _MECHANICAL_CONSUMPTION_MODULE
        and "apply_l6_dynamic_scope_generator_v1" in module
    ):
        hits.append(f"{rel}:import:{module}")
