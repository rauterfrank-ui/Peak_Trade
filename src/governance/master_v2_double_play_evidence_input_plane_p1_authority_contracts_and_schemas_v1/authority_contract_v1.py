"""Executable authority boundary contracts for Component A and Component B (P1)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.constants_v1 import (
    A_AUTHORITY,
    A_RUNTIME_IMPLEMENTATION_AUTHORIZED,
    A_TRADING_AUTHORITY,
    B_AUTHORITY,
    B_DP_STATE_MUTATION_AUTHORITY,
    B_MAY_BIND_TYPED_L6_EVIDENCE,
    B_MAY_COLLAPSE_HETEROGENEOUS_EVIDENCE_TO_PROPOSED_D_T,
    B_MAY_COMPUTE_FINAL_D_T,
    B_MAY_SELECT_D_T_FORMULA,
    B_RUNTIME_IMPLEMENTATION_AUTHORIZED,
    B_TRADING_AUTHORITY,
    DIRECT_MI_LEARNING_OPTIMIZATION_META_LEARNING_RESEARCH_TO_L6,
    DIRECT_PRODUCER_TO_B,
    DIRECT_PRODUCER_TO_DP,
    FINAL_D_T_FORMULA_SELECTED,
    IMPLEMENTS_COMPONENT_A_RUNTIME,
    IMPLEMENTS_COMPONENT_B_RUNTIME,
    L6_INTERPRETATION_AUTHORITY,
    L6_SELECTED_DIRECTION,
    NO_D_T_FORMULA_SELECTION_IN_P1,
    O_002_RATIFIED,
    OWNER_DECISION_CONFIG,
    PRODUCTIVE_L6_BINDING_AUTHORIZED,
    PROPOSED_D_T_MUST_NOT_BECOME_A_B_INFORMATION_CARRIER,
    WORKPACKAGE_ID,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    ContractValidationResultV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.reason_codes_v1 import (
    AuthorityInvariantFailureCodeV1,
)

_RUNTIME_AB_MODULE_MARKERS: tuple[str, ...] = (
    "master_v2_evidence_adjudicator",
    "master_v2_double_play_input_creator",
    "master_v2_double_play_input_binder",
    "run_component_a_runtime_v1",
    "run_component_b_runtime_v1",
)

_P1_CONTRACT_PACKAGE_MARKER = (
    "master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1"
)
_P2_BOUNDED_A_RUNTIME_PACKAGE_MARKER = (
    "master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1"
)


def _fail(*codes: str) -> ContractValidationResultV1:
    return ContractValidationResultV1(ok=False, failure_codes=tuple(dict.fromkeys(codes)))


def _ok() -> ContractValidationResultV1:
    return ContractValidationResultV1(ok=True, failure_codes=())


def validate_component_a_authority_contract_v1() -> ContractValidationResultV1:
    failures: list[str] = []
    if A_AUTHORITY != "BOUNDED_EVIDENCE_ADJUDICATION_ONLY":
        failures.append(AuthorityInvariantFailureCodeV1.OWNER_DECISION_DRIFT.value)
    if A_TRADING_AUTHORITY != "NONE":
        failures.append(AuthorityInvariantFailureCodeV1.OWNER_DECISION_DRIFT.value)
    if A_RUNTIME_IMPLEMENTATION_AUTHORIZED or IMPLEMENTS_COMPONENT_A_RUNTIME:
        failures.append(AuthorityInvariantFailureCodeV1.RUNTIME_A_IMPLEMENTATION_FORBIDDEN.value)
    if failures:
        return _fail(*failures)
    return _ok()


def validate_component_b_authority_contract_v1() -> ContractValidationResultV1:
    failures: list[str] = []
    if B_AUTHORITY != "BOUNDED_DP_INPUT_CREATION_AND_BINDING_ONLY":
        failures.append(AuthorityInvariantFailureCodeV1.OWNER_DECISION_DRIFT.value)
    if B_TRADING_AUTHORITY != "NONE" or B_DP_STATE_MUTATION_AUTHORITY != "NONE":
        failures.append(AuthorityInvariantFailureCodeV1.OWNER_DECISION_DRIFT.value)
    if not B_MAY_BIND_TYPED_L6_EVIDENCE:
        failures.append(AuthorityInvariantFailureCodeV1.OWNER_DECISION_DRIFT.value)
    if B_MAY_COMPUTE_FINAL_D_T or B_MAY_SELECT_D_T_FORMULA:
        failures.append(AuthorityInvariantFailureCodeV1.OWNER_DECISION_DRIFT.value)
    if B_MAY_COLLAPSE_HETEROGENEOUS_EVIDENCE_TO_PROPOSED_D_T:
        failures.append(AuthorityInvariantFailureCodeV1.OWNER_DECISION_DRIFT.value)
    if PROPOSED_D_T_MUST_NOT_BECOME_A_B_INFORMATION_CARRIER is not True:
        failures.append(AuthorityInvariantFailureCodeV1.OWNER_DECISION_DRIFT.value)
    if DIRECT_PRODUCER_TO_B or DIRECT_PRODUCER_TO_DP:
        failures.append(AuthorityInvariantFailureCodeV1.OWNER_DECISION_DRIFT.value)
    if DIRECT_MI_LEARNING_OPTIMIZATION_META_LEARNING_RESEARCH_TO_L6:
        failures.append(AuthorityInvariantFailureCodeV1.OWNER_DECISION_DRIFT.value)
    if FINAL_D_T_FORMULA_SELECTED or not NO_D_T_FORMULA_SELECTION_IN_P1:
        failures.append(AuthorityInvariantFailureCodeV1.OWNER_DECISION_DRIFT.value)
    if L6_INTERPRETATION_AUTHORITY != "L6_ONLY":
        failures.append(AuthorityInvariantFailureCodeV1.OWNER_DECISION_DRIFT.value)
    if L6_SELECTED_DIRECTION != "OPTION_B_TYPED_L6_EVIDENCE_SEAM":
        failures.append(AuthorityInvariantFailureCodeV1.OWNER_DECISION_DRIFT.value)
    if B_RUNTIME_IMPLEMENTATION_AUTHORIZED or IMPLEMENTS_COMPONENT_B_RUNTIME:
        failures.append(AuthorityInvariantFailureCodeV1.RUNTIME_B_IMPLEMENTATION_FORBIDDEN.value)
    if PRODUCTIVE_L6_BINDING_AUTHORIZED:
        failures.append(AuthorityInvariantFailureCodeV1.PRODUCTIVE_BINDING_FORBIDDEN.value)
    if failures:
        return _fail(*failures)
    return _ok()


def validate_p1_owner_decision_config_v1(
    repo_root: Path | None = None,
) -> ContractValidationResultV1:
    root = repo_root or Path(__file__).resolve().parents[3]
    path = root / OWNER_DECISION_CONFIG
    if not path.is_file():
        return _fail(AuthorityInvariantFailureCodeV1.OWNER_DECISION_DRIFT.value)
    payload: Mapping[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "workpackage_id": WORKPACKAGE_ID,
        "o_002_ratified": True,
        "l6_selected_direction": "OPTION_B_TYPED_L6_EVIDENCE_SEAM",
        "final_d_t_formula_selected": False,
    }
    for key, expected in required.items():
        if payload.get(key) != expected:
            return _fail(AuthorityInvariantFailureCodeV1.OWNER_DECISION_DRIFT.value)
    if not O_002_RATIFIED:
        return _fail(AuthorityInvariantFailureCodeV1.OWNER_DECISION_DRIFT.value)
    return _ok()


def scan_runtime_ab_implementation_v1(
    repo_root: Path | None = None,
) -> tuple[bool, tuple[str, ...]]:
    root = repo_root or Path(__file__).resolve().parents[3]
    hits: list[str] = []
    src = root / "src"
    if not src.is_dir():
        return False, ()
    for py in src.rglob("*.py"):
        rel = py.relative_to(root).as_posix()
        if _P1_CONTRACT_PACKAGE_MARKER in rel:
            continue
        if _P2_BOUNDED_A_RUNTIME_PACKAGE_MARKER in rel:
            continue
        if "p0_evidence_seam_census" in py.name:
            continue
        try:
            text = py.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for marker in _RUNTIME_AB_MODULE_MARKERS:
            if marker in text:
                hits.append(f"{rel}:{marker}")
    return (len(hits) > 0, tuple(sorted(set(hits))))
