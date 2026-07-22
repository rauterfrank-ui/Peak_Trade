"""Canonical research-lane post-terminal lifecycle contract v1.

Shared conceptual grammar for research-lane behavior after the active
hypothesis becomes terminal and inventories may be empty.

Definition-only. Does not migrate Entry-Eligibility or Exit-Efficiency
backlog SSOTs. No evaluation, runner, holdout, promotion, or runtime.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1=true"
CONTRACT_ID = "CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1"
CONTRACT_REL_PATH = (
    "config/research/canonical_research_lane_post_terminal_lifecycle_contract_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1.md"
)
SCHEMA_VERSION = "canonical_research_lane_post_terminal_lifecycle_contract.v1"

CANONICAL_LANE_STATES: tuple[str, ...] = (
    "OPEN_BACKLOG",
    "POST_TERMINAL_OPERATOR_DECISION_REQUIRED",
    "AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS",
    "LANE_CLOSED_NO_FURTHER_RESEARCH",
)

TOTALITY_CLASSES: frozenset[str] = frozenset(
    {
        "DETERMINISTIC_CANONICAL_NEXT",
        "DETERMINISTIC_OR_ENUMERATED_WITHIN_INVENTORY",
        "ENUMERATED_OPERATOR_DECISION",
        "TERMINAL_CLOSED_STATE",
    }
)

OPERATOR_DECISIONS: frozenset[str] = frozenset(
    {
        "DECLARE_AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS",
        "CLOSE_LANE_NO_FURTHER_RESEARCH",
        "CREATE_SUCCESSOR_HYPOTHESIS",
        "REOPEN_CLOSED_LANE_WITH_NEW_HYPOTHESIS_IDENTITY",
    }
)

IMMUTABLE_ARTIFACT_CLASSES: frozenset[str] = frozenset(
    {
        "PREREGISTRATION_ECONOMIC_CONTRACT",
        "PREREGISTRATION_DIGEST",
        "EVALUATION_EVIDENCE",
        "EVALUATION_METRICS",
        "RUN_SLOT_CLAIM",
        "RESULT_DIGEST",
        "EXECUTED_AUTHORIZATION_RATIFICATION_SNAPSHOT",
        "EXECUTED_OPERATOR_CLARIFICATION_AUTHORITY_SNAPSHOT",
    }
)

MUTABLE_ARTIFACT_CLASSES: frozenset[str] = frozenset(
    {
        "LANE_BACKLOG_STATUS",
        "LANE_NEXT_CANONICAL_STEP",
        "LANE_OPERATOR_DECISION_RECORD",
    }
)

INVALID_STATE_CODES: frozenset[str] = frozenset(
    {
        "EXECUTABLE_GO_WITH_NO_TARGET",
        "AUTO_CREATED_SUCCESSOR",
        "OPEN_LANE_EMPTY_INVENTORY_WITHOUT_WAITING_SEMANTICS",
        "CLOSED_LANE_WITH_IMPLICIT_SUCCESSOR",
        "HISTORICAL_EVALUATION_EVIDENCE_MUTATION",
        "AWAITING_WITHOUT_EXPLICIT_WAITING_DECISION",
        "CLOSED_WITHOUT_EXPLICIT_CLOSEOUT_DECISION",
    }
)


class ResearchLaneLifecycleContractError(ValueError):
    """Fail-closed error for the shared research-lane lifecycle contract."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_true(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        suffix = f": {detail}" if detail else ""
        raise ResearchLaneLifecycleContractError(f"{code}{suffix}")


def default_contract_path(repo_root: Path | None = None) -> Path:
    root = _repo_root() if repo_root is None else Path(repo_root)
    return root / CONTRACT_REL_PATH


def load_lifecycle_contract(repo_root: Path | None = None) -> dict[str, Any]:
    path = default_contract_path(repo_root)
    _assert_true(path.is_file(), "LIFECYCLE_CONTRACT_MISSING", str(path))
    payload = _load_json(path)
    _assert_true(isinstance(payload, dict), "LIFECYCLE_CONTRACT_TYPE")
    return payload


def inventory_non_empty(snapshot: Mapping[str, Any]) -> bool:
    open_count = int(snapshot.get("open_unpreregistered_count") or 0)
    prereg_count = int(snapshot.get("preregistered_count") or 0)
    open_list = snapshot.get("open_unpreregistered_candidates")
    prereg_list = snapshot.get("preregistered_hypotheses")
    if isinstance(open_list, list):
        open_count = max(open_count, len(open_list))
    if isinstance(prereg_list, list):
        prereg_count = max(prereg_count, len(prereg_list))
    return open_count > 0 or prereg_count > 0


def validate_lifecycle_contract(contract: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Validate the shared contract SSOT for self-consistency and totality."""
    payload = dict(contract) if contract is not None else load_lifecycle_contract()
    _assert_true(payload.get("contract_id") == CONTRACT_ID, "CONTRACT_ID_MISMATCH")
    _assert_true(payload.get("schema_version") == SCHEMA_VERSION, "SCHEMA_VERSION_MISMATCH")
    _assert_true(payload.get("canonical_ssot") is True, "CANONICAL_SSOT_REQUIRED")
    _assert_true(payload.get("authority_effect") == "NONE", "AUTHORITY_EFFECT_MUST_BE_NONE")
    _assert_true(payload.get("runtime_effect") == "NONE", "RUNTIME_EFFECT_MUST_BE_NONE")
    _assert_true(payload.get("evaluation_authorized") is False, "EVALUATION_MUST_BE_FALSE")
    _assert_true(payload.get("backtest_authorized") is False, "BACKTEST_MUST_BE_FALSE")
    _assert_true(payload.get("implementation_authorized") is False, "IMPLEMENTATION_MUST_BE_FALSE")
    _assert_true(
        payload.get("migration_deferred", {}).get("migrate_in_this_slice") is False,
        "MIGRATION_MUST_BE_DEFERRED",
    )

    states = payload.get("canonical_lane_states")
    _assert_true(isinstance(states, list), "STATES_MUST_BE_LIST")
    _assert_true(tuple(states) == CANONICAL_LANE_STATES, "STATES_DRIFT", str(states))

    definitions = payload.get("state_definitions") or {}
    _assert_true(set(definitions) == set(CANONICAL_LANE_STATES), "STATE_DEFINITIONS_DRIFT")

    totality = payload.get("totality_invariant") or {}
    state_classes = totality.get("state_totality_class") or {}
    _assert_true(set(state_classes) == set(CANONICAL_LANE_STATES), "TOTALITY_STATE_DRIFT")
    for state, totality_class in state_classes.items():
        _assert_true(
            totality_class in TOTALITY_CLASSES,
            "TOTALITY_CLASS_UNKNOWN",
            f"{state}={totality_class}",
        )
        defn_class = definitions[state].get("totality_class")
        _assert_true(
            defn_class == totality_class,
            "TOTALITY_CLASS_MISMATCH",
            f"{state}: {defn_class} != {totality_class}",
        )

    # Totality: every state maps to exactly one bucket family.
    closed = {s for s, c in state_classes.items() if c == "TERMINAL_CLOSED_STATE"}
    enumerated = {s for s, c in state_classes.items() if c == "ENUMERATED_OPERATOR_DECISION"}
    deterministicish = {
        s
        for s, c in state_classes.items()
        if c
        in {
            "DETERMINISTIC_CANONICAL_NEXT",
            "DETERMINISTIC_OR_ENUMERATED_WITHIN_INVENTORY",
        }
    }
    _assert_true(
        closed | enumerated | deterministicish == set(CANONICAL_LANE_STATES),
        "TOTALITY_COVERAGE_INCOMPLETE",
    )
    _assert_true(
        len(closed) + len(enumerated) + len(deterministicish) == len(CANONICAL_LANE_STATES),
        "TOTALITY_OVERLAP",
    )
    _assert_true(closed == {"LANE_CLOSED_NO_FURTHER_RESEARCH"}, "CLOSED_STATE_DRIFT")
    _assert_true("OPEN_BACKLOG" in deterministicish, "OPEN_BACKLOG_TOTALITY")
    _assert_true(
        "POST_TERMINAL_OPERATOR_DECISION_REQUIRED" in enumerated,
        "POST_TERMINAL_TOTALITY",
    )
    _assert_true(
        "AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS" in enumerated,
        "AWAITING_TOTALITY",
    )

    op = payload.get("operator_decision_contract") or {}
    _assert_true(
        op.get("go_alone_never_executable_without_concrete_target") is True,
        "GO_ALONE_CONTRACT",
    )
    _assert_true(
        op.get("create_successor_requires_explicit_hypothesis_id_and_mechanism") is True,
        "SUCCESSOR_CONTRACT",
    )
    _assert_true(
        op.get("closeout_requires_explicit_closeout_decision") is True,
        "CLOSEOUT_CONTRACT",
    )
    _assert_true(
        op.get("reopen_closed_lane_requires_new_explicit_hypothesis_identity") is True,
        "REOPEN_CONTRACT",
    )
    enumerated_decisions = set(op.get("enumerated_decisions") or [])
    _assert_true(enumerated_decisions == OPERATOR_DECISIONS, "OPERATOR_DECISIONS_DRIFT")

    imm = payload.get("immutability_policy") or {}
    _assert_true(
        set(imm.get("immutable_artifact_classes") or []) == IMMUTABLE_ARTIFACT_CLASSES,
        "IMMUTABLE_CLASSES_DRIFT",
    )
    _assert_true(
        set(imm.get("mutable_artifact_classes") or []) == MUTABLE_ARTIFACT_CLASSES,
        "MUTABLE_CLASSES_DRIFT",
    )
    _assert_true(
        imm.get("authorization_summaries_class") == "HISTORICAL_SNAPSHOT_NOT_LIVE_MIRROR",
        "AUTH_SUMMARY_CLASS",
    )
    _assert_true(
        imm.get("live_authority_and_ratification_after_execution")
        == "MUST_NOT_MUTATE_SEALED_SNAPSHOT_OBJECTS",
        "LIVE_AUTHORITY_POLICY",
    )

    invalid = payload.get("invalid_states") or []
    invalid_codes = {item.get("code") for item in invalid if isinstance(item, dict)}
    _assert_true(invalid_codes == INVALID_STATE_CODES, "INVALID_STATE_CODES_DRIFT")

    open_def = definitions["OPEN_BACKLOG"]
    _assert_true(
        open_def.get("inventory_requirement") == "NON_EMPTY_OPEN_OR_PREREGISTERED",
        "OPEN_BACKLOG_INVENTORY_RULE",
    )

    post = payload.get("post_terminal_transitions") or {}
    for result_class in ("PASS", "FAIL"):
        branch = post.get(result_class) or {}
        empty = branch.get("if_inventory_empty") or {}
        _assert_true(
            empty.get("required_operator_decision_state")
            == "POST_TERMINAL_OPERATOR_DECISION_REQUIRED",
            f"POST_TERMINAL_{result_class}_EMPTY_STATE",
        )
        _assert_true(
            empty.get("deterministic_next") is None, f"POST_TERMINAL_{result_class}_NO_AUTO"
        )
        allowed = set(empty.get("allowed_operator_decisions") or [])
        _assert_true(
            allowed
            == {
                "DECLARE_AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS",
                "CLOSE_LANE_NO_FURTHER_RESEARCH",
                "CREATE_SUCCESSOR_HYPOTHESIS",
            },
            f"POST_TERMINAL_{result_class}_DECISIONS",
        )

    runtime = payload.get("runtime_policy") or {}
    for flag in (
        "live_authorized",
        "orders_allowed",
        "runtime_activated",
        "shadow_activated",
        "testnet_activated",
        "scheduler_authorized",
        "capital_activated",
        "paper_activated",
    ):
        _assert_true(runtime.get(flag) is False, f"RUNTIME_FLAG_{flag.upper()}")

    return {
        "contract_id": CONTRACT_ID,
        "valid": True,
        "canonical_lane_states": list(CANONICAL_LANE_STATES),
        "totality_invariant_defined": True,
        "operator_decision_contract_defined": True,
        "historical_immutability_defined": True,
        "live_mirror_policy": imm.get("authorization_summaries_class"),
        "migration_deferred": True,
    }


def classify_invalid_lane_snapshot(snapshot: Mapping[str, Any]) -> list[str]:
    """Return invalid-state codes for a synthetic or live lane snapshot."""
    codes: list[str] = []
    status = snapshot.get("status")
    has_inventory = inventory_non_empty(snapshot)
    waiting_decision = bool(snapshot.get("explicit_waiting_decision"))
    closeout_decision = bool(snapshot.get("explicit_closeout_decision"))
    go_executable = bool(snapshot.get("go_executable"))
    go_target = snapshot.get("go_target")
    auto_successor = bool(snapshot.get("auto_created_successor"))
    implicit_successor = bool(snapshot.get("implicit_successor"))
    historical_mutation = bool(snapshot.get("historical_evaluation_evidence_mutated"))

    if status == "OPEN_BACKLOG" and not has_inventory:
        codes.append("OPEN_LANE_EMPTY_INVENTORY_WITHOUT_WAITING_SEMANTICS")
    if status == "AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS" and not waiting_decision:
        codes.append("AWAITING_WITHOUT_EXPLICIT_WAITING_DECISION")
    if status == "LANE_CLOSED_NO_FURTHER_RESEARCH" and not closeout_decision:
        codes.append("CLOSED_WITHOUT_EXPLICIT_CLOSEOUT_DECISION")
    if status == "LANE_CLOSED_NO_FURTHER_RESEARCH" and implicit_successor:
        codes.append("CLOSED_LANE_WITH_IMPLICIT_SUCCESSOR")
    if go_executable and not go_target:
        codes.append("EXECUTABLE_GO_WITH_NO_TARGET")
    if auto_successor:
        codes.append("AUTO_CREATED_SUCCESSOR")
    if historical_mutation:
        codes.append("HISTORICAL_EVALUATION_EVIDENCE_MUTATION")
    if status is not None and status not in CANONICAL_LANE_STATES:
        codes.append("UNKNOWN_LANE_STATUS")
    return codes


def validate_lane_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Fail-closed validation of a lane lifecycle snapshot against this contract."""
    status = snapshot.get("status")
    _assert_true(
        status in CANONICAL_LANE_STATES,
        "UNKNOWN_LANE_STATUS",
        repr(status),
    )
    invalid = classify_invalid_lane_snapshot(snapshot)
    _assert_true(not invalid, "INVALID_LANE_SNAPSHOT", ",".join(invalid))

    has_inventory = inventory_non_empty(snapshot)
    if status == "OPEN_BACKLOG":
        _assert_true(has_inventory, "OPEN_BACKLOG_REQUIRES_INVENTORY")
    if status in {
        "POST_TERMINAL_OPERATOR_DECISION_REQUIRED",
        "AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS",
        "LANE_CLOSED_NO_FURTHER_RESEARCH",
    }:
        _assert_true(not has_inventory, "EMPTY_STATE_REQUIRES_EMPTY_INVENTORY")

    if status == "AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS":
        _assert_true(
            bool(snapshot.get("explicit_waiting_decision")),
            "AWAITING_REQUIRES_WAITING_DECISION",
        )
    if status == "LANE_CLOSED_NO_FURTHER_RESEARCH":
        _assert_true(
            bool(snapshot.get("explicit_closeout_decision")),
            "CLOSED_REQUIRES_CLOSEOUT_DECISION",
        )
        _assert_true(
            not bool(snapshot.get("implicit_successor")),
            "CLOSED_FORBIDS_IMPLICIT_SUCCESSOR",
        )

    if bool(snapshot.get("go_executable")):
        target = snapshot.get("go_target")
        _assert_true(
            isinstance(target, str) and bool(target.strip()),
            "GO_REQUIRES_CONCRETE_TARGET",
        )

    if snapshot.get("transition_trigger") == "CREATE_SUCCESSOR_HYPOTHESIS":
        _assert_true(
            isinstance(snapshot.get("hypothesis_id"), str)
            and bool(str(snapshot.get("hypothesis_id")).strip()),
            "SUCCESSOR_REQUIRES_HYPOTHESIS_ID",
        )
        _assert_true(
            isinstance(snapshot.get("mechanism_definition"), str)
            and bool(str(snapshot.get("mechanism_definition")).strip()),
            "SUCCESSOR_REQUIRES_MECHANISM",
        )

    if snapshot.get("transition_trigger") == "REOPEN_CLOSED_LANE_WITH_NEW_HYPOTHESIS_IDENTITY":
        _assert_true(
            bool(snapshot.get("explicit_reopen_decision")),
            "REOPEN_REQUIRES_EXPLICIT_DECISION",
        )
        _assert_true(
            isinstance(snapshot.get("hypothesis_id"), str)
            and bool(str(snapshot.get("hypothesis_id")).strip()),
            "REOPEN_REQUIRES_NEW_HYPOTHESIS_IDENTITY",
        )

    artifact_class = snapshot.get("artifact_class")
    if artifact_class in IMMUTABLE_ARTIFACT_CLASSES:
        _assert_true(
            not bool(snapshot.get("artifact_mutated_after_seal")),
            "IMMUTABLE_ARTIFACT_MUTATION_FORBIDDEN",
            str(artifact_class),
        )

    return {
        "valid": True,
        "status": status,
        "inventory_non_empty": has_inventory,
        "totality_class": (
            load_lifecycle_contract()
            .get("totality_invariant", {})
            .get("state_totality_class", {})
            .get(status)
        ),
    }


def resolve_post_terminal_transition(
    *,
    result_class: str,
    inventory_non_empty_flag: bool,
) -> dict[str, Any]:
    """Resolve the shared PASS/FAIL post-terminal transition requirement."""
    contract = load_lifecycle_contract()
    matrix = contract.get("post_terminal_transitions") or {}
    normalized = result_class.upper()
    if normalized in {"PASS"}:
        key = "PASS"
    elif normalized in {
        "FAIL",
        "INCONCLUSIVE_INFRASTRUCTURE_FAILURE",
        "INFRASTRUCTURE_FAILURE",
    }:
        # Infrastructure failures follow the FAIL empty-inventory operator path:
        # no auto-successor / auto-close; explicit operator decision required.
        key = "FAIL"
    else:
        raise ResearchLaneLifecycleContractError(f"UNKNOWN_RESULT_CLASS: {result_class!r}")
    branch = matrix.get(key) or {}
    if inventory_non_empty_flag:
        arm = branch.get("if_inventory_non_empty") or {}
        return {
            "result_class_family": key,
            "path": "INVENTORY_NON_EMPTY",
            "next_state": "OPEN_BACKLOG",
            "deterministic_next": arm.get("deterministic_next"),
            "operator_decision_required": False,
        }
    arm = branch.get("if_inventory_empty") or {}
    return {
        "result_class_family": key,
        "path": "INVENTORY_EMPTY",
        "next_state": arm.get("required_operator_decision_state"),
        "deterministic_next": arm.get("deterministic_next"),
        "operator_decision_required": True,
        "allowed_operator_decisions": list(arm.get("allowed_operator_decisions") or []),
    }


def assert_governance_doc_bound(repo_root: Path | None = None) -> None:
    root = _repo_root() if repo_root is None else Path(repo_root)
    path = root / GOVERNANCE_REL_PATH
    _assert_true(path.is_file(), "GOVERNANCE_DOC_MISSING", str(path))
    text = path.read_text(encoding="utf-8")
    _assert_true(
        "DOCS_TOKEN_CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1" in text,
        "GOVERNANCE_DOCS_TOKEN_MISSING",
    )
    for state in CANONICAL_LANE_STATES:
        _assert_true(state in text, "GOVERNANCE_STATE_MISSING", state)
    _assert_true("TOTALITY_INVARIANT" in text, "GOVERNANCE_TOTALITY_MISSING")
    _assert_true(
        "HISTORICAL_SNAPSHOT_NOT_LIVE_MIRROR" in text,
        "GOVERNANCE_MIRROR_POLICY_MISSING",
    )
    _assert_true(
        "migrate_in_this_slice: false" in text or "Migration deferred" in text,
        "GOVERNANCE_MIGRATION_NOTE",
    )


def validate_repo_binding(repo_root: Path | None = None) -> dict[str, Any]:
    root = _repo_root() if repo_root is None else Path(repo_root)
    report = validate_lifecycle_contract(load_lifecycle_contract(root))
    assert_governance_doc_bound(root)
    report["governance_doc"] = GOVERNANCE_REL_PATH
    report["contract_path"] = CONTRACT_REL_PATH
    return report


__all__ = [
    "CANONICAL_LANE_STATES",
    "CONTRACT_ID",
    "IMMUTABLE_ARTIFACT_CLASSES",
    "INVALID_STATE_CODES",
    "MUTABLE_ARTIFACT_CLASSES",
    "OPERATOR_DECISIONS",
    "PACKAGE_MARKER",
    "ResearchLaneLifecycleContractError",
    "assert_governance_doc_bound",
    "classify_invalid_lane_snapshot",
    "inventory_non_empty",
    "load_lifecycle_contract",
    "resolve_post_terminal_transition",
    "validate_lane_snapshot",
    "validate_lifecycle_contract",
    "validate_repo_binding",
]
