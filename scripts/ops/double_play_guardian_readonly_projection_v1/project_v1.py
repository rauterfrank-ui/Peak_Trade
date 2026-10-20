"""Deterministic read-only gap projection. AUTHORITY=NONE. No tool execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.double_play_guardian_readonly_projection_v1.constants_v1 import (
    ALLOWED_CLAIMS,
    AUTHORITY,
    AUTHORITY_TRANSFER_TOKEN,
    CATALOG_GAP_IDS,
    DECISION_PATH_RELATIVE,
    DOMAIN,
    EXECUTION_AUTHORITY,
    EXPECTED_BASELINE_SHA,
    EXPECTED_BASELINE_TREE,
    FORBIDDEN_OUTPUT_KEYS,
    GHOSV_CONSTANTS_RELATIVE,
    GHOSV_CONTRACT_RELATIVE,
    HIERARCHY_TOKEN,
    INTERNAL_AREA_TOKEN,
    INTERNAL_COMPONENT,
    LOCK_TOKEN,
    SAFETY_AUTHORITY,
    SCHEMA_ID,
    SCHEMA_VERSION,
    SEPARATE_UNIVERSE_TOKEN,
    TOOL_ROLES,
    TRADING_AUTHORITY,
)
from scripts.ops.double_play_guardian_readonly_projection_v1.extract_v1 import (
    extract_constant_assignments_v1,
    path_is_inside_v1,
    read_json_object_v1,
    read_text_v1,
)

_CONSTANT_NAMES = frozenset(
    {
        "AUTHORITY",
        "CURRENT_CODE_PIN",
        "CURRENT_TREE_PIN",
        "DOMAIN",
        "NOT_TESTED_REQUIREMENTS",
    }
)
_AUTHORITY_CLAIM_FIELDS = (
    "authority",
    "trading_authority",
    "safety_authority",
    "execution_authority",
)


@dataclass(frozen=True)
class ProjectionInputsV1:
    current_sha: str
    current_tree: str
    ghosv_contract_text: str | None
    decision_path_text: str | None
    ghosv_constants: dict[str, Any] | None
    snapshot_header: dict[str, Any] | None
    ghosv_contract_source: str
    decision_path_source: str
    ghosv_constants_source: str
    snapshot_header_source: str
    claims: dict[str, Any]


def load_projection_inputs_v1(
    *,
    repository_root: Path,
    snapshot_header_path: Path,
    current_sha: str,
    current_tree: str,
    claims: Mapping[str, Any] | None = None,
) -> ProjectionInputsV1:
    root = repository_root.resolve()
    contract_path = root / GHOSV_CONTRACT_RELATIVE
    decision_path = root / DECISION_PATH_RELATIVE
    constants_path = root / GHOSV_CONSTANTS_RELATIVE
    if not path_is_inside_v1(root, contract_path):
        contract_text = None
    else:
        contract_text = read_text_v1(contract_path)
    if not path_is_inside_v1(root, decision_path):
        decision_text = None
    else:
        decision_text = read_text_v1(decision_path)
    if not path_is_inside_v1(root, constants_path):
        constants = None
    else:
        constants = extract_constant_assignments_v1(constants_path, _CONSTANT_NAMES)
    header = read_json_object_v1(snapshot_header_path)
    return ProjectionInputsV1(
        current_sha=current_sha,
        current_tree=current_tree,
        ghosv_contract_text=contract_text,
        decision_path_text=decision_text,
        ghosv_constants=constants,
        snapshot_header=header,
        ghosv_contract_source=GHOSV_CONTRACT_RELATIVE,
        decision_path_source=DECISION_PATH_RELATIVE,
        ghosv_constants_source=GHOSV_CONSTANTS_RELATIVE,
        snapshot_header_source=str(snapshot_header_path),
        claims=dict(claims or {}),
    )


def project_double_play_guardian_gap_v1(inputs: ProjectionInputsV1) -> dict[str, Any]:
    reasons: list[str] = []
    claims = inputs.claims
    unknown_claims = sorted(set(claims) - ALLOWED_CLAIMS)
    if unknown_claims:
        reasons.append("UNKNOWN_CLAIM")

    if inputs.current_sha != EXPECTED_BASELINE_SHA:
        reasons.append("BASELINE_SHA_MISMATCH")
    if inputs.current_tree != EXPECTED_BASELINE_TREE:
        reasons.append("BASELINE_TREE_MISMATCH")

    contract = inputs.ghosv_contract_text or ""
    decision = inputs.decision_path_text or ""
    constants = inputs.ghosv_constants
    header = inputs.snapshot_header

    if not contract or not decision or constants is None or header is None:
        reasons.append("MISSING_REQUIRED_EVIDENCE")

    lock_in_contract = LOCK_TOKEN in contract
    lock_in_decision = LOCK_TOKEN in decision
    if not lock_in_contract and not lock_in_decision:
        reasons.append("MISSING_OWNER_LOCK_EVIDENCE")

    hierarchy_observed = HIERARCHY_TOKEN in contract
    internal_area_observed = INTERNAL_AREA_TOKEN in decision
    separate_universe_false = SEPARATE_UNIVERSE_TOKEN in decision
    authority_transfer_false = AUTHORITY_TRANSFER_TOKEN in contract
    if not hierarchy_observed or not internal_area_observed or not separate_universe_false:
        reasons.append("MISSING_REQUIRED_EVIDENCE")
    if not authority_transfer_false:
        reasons.append("MISSING_REQUIRED_EVIDENCE")

    if claims.get("dynamic_scope_separate_universe") is True:
        reasons.append("UNAUTHORIZED_UNIVERSE_CLAIM")

    for field in _AUTHORITY_CLAIM_FIELDS:
        if field in claims and claims[field] != "NONE":
            reasons.append("UNAUTHORIZED_AUTHORITY_CLAIM")

    not_tested = _not_tested_tuple(constants)
    catalog_gap = {item: _catalog_state(item, not_tested) for item in CATALOG_GAP_IDS}
    if constants is None or any(catalog_gap[item] != "NOT_TESTED" for item in CATALOG_GAP_IDS):
        reasons.append("MISSING_REQUIRED_EVIDENCE")
    if claims.get("treat_catalog_check_as_executed") is True:
        reasons.append("CATALOG_CHECK_TREATED_AS_EXECUTED")

    code_pin = _constant_str(constants, "CURRENT_CODE_PIN")
    tree_pin = _constant_str(constants, "CURRENT_TREE_PIN")
    pin_is_current = code_pin == EXPECTED_BASELINE_SHA and tree_pin == EXPECTED_BASELINE_TREE
    if claims.get("treat_older_ghosv_pin_as_current") is True:
        reasons.append("OLDER_GHOSV_PIN_TREATED_AS_CURRENT")

    if claims.get("treat_ops_census_node_as_trading_symbol") is True:
        reasons.append("OPS_CENSUS_NODE_TREATED_AS_TRADING_SYMBOL")
    if claims.get("treat_missing_graph_symbol_as_isolation") is True:
        reasons.append("MISSING_GRAPH_SYMBOL_TREATED_AS_ISOLATION_PROOF")
    if claims.get("infer_productive_persistence_from_state_persisted") is True:
        reasons.append("PRODUCTIVE_PERSISTENCE_INFERENCE_REJECTED")

    header_head, header_tree, header_authority = _header_binding(header)
    if header is not None and header_authority not in (None, "NONE"):
        reasons.append("UNAUTHORIZED_AUTHORITY_CLAIM")
    if header is not None and header_head != EXPECTED_BASELINE_SHA:
        reasons.append("BASELINE_SHA_MISMATCH")
    if header is not None and header_tree != EXPECTED_BASELINE_TREE:
        reasons.append("BASELINE_TREE_MISMATCH")

    unique_reasons = tuple(dict.fromkeys(reasons))
    rejected = bool(unique_reasons)
    provenance = _provenance(inputs)
    tools = [_tool_row(role, provenance, code_pin, pin_is_current) for role in TOOL_ROLES]
    report: dict[str, Any] = {
        "SCHEMA_ID": SCHEMA_ID,
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "BASELINE_SHA": EXPECTED_BASELINE_SHA,
        "BASELINE_TREE": EXPECTED_BASELINE_TREE,
        "SUPPLIED_SHA": inputs.current_sha,
        "SUPPLIED_TREE": inputs.current_tree,
        "DOMAIN": DOMAIN,
        "INTERNAL_COMPONENT": INTERNAL_COMPONENT,
        "AUTHORITY": AUTHORITY,
        "TRADING_AUTHORITY": TRADING_AUTHORITY,
        "SAFETY_AUTHORITY": SAFETY_AUTHORITY,
        "EXECUTION_AUTHORITY": EXECUTION_AUTHORITY,
        "PROJECTION_STATUS": "REJECTED" if rejected else "GAP_REPORTED",
        "REJECTION_REASONS": list(unique_reasons),
        "ARCHITECTURE_OBSERVATION": {
            "CHAIN": "HUMAN OWNER > MASTER V2 > DOUBLE PLAY > DYNAMIC SCOPE",
            "DYNAMIC_SCOPE_CLASS": "INTERNAL_FUNCTIONAL_COMPONENT",
            "INDEPENDENT_DYNAMIC_SCOPE_GUARDIAN": False,
            "HIERARCHY_TOKEN_OBSERVED": hierarchy_observed,
            "DOUBLE_PLAY_SEPARATE_UNIVERSE_FALSE_OBSERVED": separate_universe_false,
            "DOUBLE_PLAY_INTERNAL_FUNCTIONAL_AREA_TRUE_OBSERVED": internal_area_observed,
            "AUTHORITY_TRANSFER_FALSE_OBSERVED": authority_transfer_false,
        },
        "OWNER_LOCK_STATUS": {
            "CATEGORY_3_FULL_OWNER_LOCK": "LEVEL_3"
            if lock_in_contract or lock_in_decision
            else "UNKNOWN",
            "OBSERVATION_CLASS": "CONTRACT_TEXT"
            if lock_in_contract or lock_in_decision
            else "MISSING",
            "PYTHON_ENFORCEMENT": "NOT_CLAIMED",
            "GATE_CREATED": False,
            "LOCK_TOKEN_IN_GHOSV_CONTRACT": lock_in_contract,
            "LOCK_TOKEN_IN_DECISION_PATH": lock_in_decision,
        },
        "GHOSV_GAP_STATUS": catalog_gap,
        "GHOSV_GAP_CLASS": "CATALOG_STATE_NOT_EXECUTED_CHECK",
        "GHOSV_CODE_PIN": code_pin,
        "GHOSV_TREE_PIN": tree_pin,
        "GHOSV_PIN_IS_CURRENT_BASELINE": False if code_pin is None else pin_is_current,
        "GHOSV_EXISTING_DOMAIN_CONSTANT": _constant_str(constants, "DOMAIN"),
        "ENTRY_EXIT_EFFECT_EVALUATED": False,
        "PRODUCTIVE_PERSISTENCE_INFERRED": False,
        "RUNTIME_ACTIVATED_IS_EXECUTION_PROOF": False,
        "OPS_CENSUS_NODE_IS_TRADING_SYMBOL": False,
        "ABSENT_GRAPH_SYMBOL_IS_ISOLATION_PROOF": False,
        "WHOLE_SYSTEM_HEADER_MATCHES_BASELINE": header_head == EXPECTED_BASELINE_SHA
        and header_tree == EXPECTED_BASELINE_TREE,
        "WHOLE_SYSTEM_HEADER_IS_DOMAIN_TOOL": False,
        "TOOL_ROLES": tools,
        "DOUBLE_PLAY_GHV_READY": False,
        "DOUBLE_PLAY_CURRENT_CAUSAL_GRAPH_READY": False,
        "DOUBLE_PLAY_GHOSV_READY": False,
        "SOURCE_PROVENANCE": provenance,
    }
    _assert_no_forbidden_keys(report)
    return report


def _tool_row(
    role: str,
    provenance: list[dict[str, str]],
    code_pin: str | None,
    pin_is_current: bool,
) -> dict[str, Any]:
    missing = [
        "NO_DOMAIN_IMPLEMENTATION",
        "NO_CURRENT_DOMAIN_BINDING",
        "DOMAIN_COVERAGE_NOT_PROVEN",
        "DYNAMIC_SCOPE_INTERNAL_CHECK_NOT_EXECUTED",
    ]
    binding = "NOT_BOUND"
    if role == "DOUBLE_PLAY_GHOSV":
        missing.extend(
            [
                "MV2-04_NOT_TESTED",
                "MV2-05_NOT_TESTED",
                "MV2-06_NOT_TESTED",
                "MV2-08_NOT_TESTED",
                "ENTRY_EXIT_EFFECT_NOT_EVALUATED",
                "PERSISTENCE_CONSTANT_IS_NOT_RUNTIME_PROOF",
            ]
        )
        if code_pin is not None and not pin_is_current:
            missing.append("GHOSV_PIN_IS_NOT_CURRENT_BASELINE")
            binding = "OLDER_PIN_NOT_CURRENT"
    if role == "DOUBLE_PLAY_CURRENT_CAUSAL_GRAPH":
        missing.extend(
            [
                "NO_DOMAIN_GRAPH",
                "FUNCTIONAL_EDGE_COVERAGE_NOT_PROVEN",
                "ABSENT_SYMBOL_IS_NOT_ISOLATION",
            ]
        )
    if role == "DOUBLE_PLAY_GHV":
        missing.append("WHOLE_SYSTEM_GHV_IS_NOT_DOMAIN_GHV")
    return {
        "TOOL_ROLE": role,
        "PROPOSED_IDENTITY": role,
        "IMPLEMENTATION_STATUS": "NO_IMPLEMENTATION_FOUND",
        "CURRENT_BINDING_STATUS": binding,
        "DOMAIN_COVERAGE_STATUS": "NOT_PROVEN",
        "DYNAMIC_SCOPE_COVERAGE_STATUS": "NOT_PROVEN",
        "EXECUTION_STATUS": "NOT_EXECUTED",
        "READINESS_STATUS": "NOT_READY",
        "AUTHORITY": "NONE",
        "MISSING_EVIDENCE": missing,
        "SOURCE_PROVENANCE": provenance,
    }


def _provenance(inputs: ProjectionInputsV1) -> list[dict[str, str]]:
    rows = [
        {"source": inputs.ghosv_contract_source, "class": "EXISTING_CONTRACT_TEXT"},
        {"source": inputs.decision_path_source, "class": "EXISTING_CONTRACT_TEXT"},
        {"source": inputs.ghosv_constants_source, "class": "EXISTING_CONSTANT_ASSIGNMENT"},
        {"source": inputs.snapshot_header_source, "class": "FROZEN_SNAPSHOT_HEADER"},
    ]
    return rows


def _not_tested_tuple(constants: dict[str, Any] | None) -> tuple[str, ...] | None:
    if constants is None:
        return None
    raw = constants.get("NOT_TESTED_REQUIREMENTS")
    if not isinstance(raw, tuple) or not all(isinstance(item, str) for item in raw):
        return None
    return raw


def _catalog_state(item: str, not_tested: tuple[str, ...] | None) -> str:
    if not_tested is None:
        return "UNKNOWN"
    if item in not_tested:
        return "NOT_TESTED"
    return "UNKNOWN"


def _constant_str(constants: dict[str, Any] | None, name: str) -> str | None:
    if constants is None:
        return None
    value = constants.get(name)
    if isinstance(value, str):
        return value
    return None


def _header_binding(header: dict[str, Any] | None) -> tuple[str | None, str | None, str | None]:
    if header is None:
        return None, None, None
    authority = header.get("authority")
    authority_text = authority if isinstance(authority, str) else None
    isolated = header.get("isolated")
    if not isinstance(isolated, dict):
        code_snapshot = header.get("code_snapshot")
        if isinstance(code_snapshot, dict):
            head = code_snapshot.get("git_head")
            return (
                head if isinstance(head, str) else None,
                None,
                authority_text,
            )
        return None, None, authority_text
    head = isolated.get("head")
    tree = isolated.get("tree")
    return (
        head if isinstance(head, str) else None,
        tree if isinstance(tree, str) else None,
        authority_text,
    )


def _assert_no_forbidden_keys(payload: object) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in FORBIDDEN_OUTPUT_KEYS:
                raise RuntimeError("FORBIDDEN_OUTPUT_KEY")
            _assert_no_forbidden_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            _assert_no_forbidden_keys(item)
