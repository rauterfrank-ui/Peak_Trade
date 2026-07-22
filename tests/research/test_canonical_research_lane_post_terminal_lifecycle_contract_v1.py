"""Contract tests for canonical research-lane post-terminal lifecycle v1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research.canonical_research_lane_post_terminal_lifecycle_contract_v1 import (
    CANONICAL_LANE_STATES,
    CONTRACT_ID,
    IMMUTABLE_ARTIFACT_CLASSES,
    INVALID_STATE_CODES,
    OPERATOR_DECISIONS,
    ResearchLaneLifecycleContractError,
    classify_invalid_lane_snapshot,
    load_lifecycle_contract,
    resolve_post_terminal_transition,
    validate_lane_snapshot,
    validate_lifecycle_contract,
    validate_repo_binding,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPO_ROOT / "config/research/canonical_research_lane_post_terminal_lifecycle_contract_v1.json"
)
OWNER_MAP = (
    REPO_ROOT
    / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
TECH_WIRING = REPO_ROOT / "config/governance/technical_canonical_wiring_authorization_v1.json"
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1.md"
)


def test_contract_self_validation_and_repo_binding() -> None:
    report = validate_repo_binding(REPO_ROOT)
    assert report["valid"] is True
    assert report["contract_id"] == CONTRACT_ID
    assert report["totality_invariant_defined"] is True
    assert report["operator_decision_contract_defined"] is True
    assert report["historical_immutability_defined"] is True
    assert report["live_mirror_policy"] == "HISTORICAL_SNAPSHOT_NOT_LIVE_MIRROR"
    assert report["migration_deferred"] is True
    assert CONTRACT_PATH.is_file()
    assert GOVERNANCE_DOC.is_file()


def test_canonical_states_and_totality_coverage() -> None:
    contract = load_lifecycle_contract(REPO_ROOT)
    assert tuple(contract["canonical_lane_states"]) == CANONICAL_LANE_STATES
    report = validate_lifecycle_contract(contract)
    assert report["canonical_lane_states"] == list(CANONICAL_LANE_STATES)
    totality = contract["totality_invariant"]["state_totality_class"]
    assert set(totality) == set(CANONICAL_LANE_STATES)
    assert totality["LANE_CLOSED_NO_FURTHER_RESEARCH"] == "TERMINAL_CLOSED_STATE"
    assert totality["POST_TERMINAL_OPERATOR_DECISION_REQUIRED"] == ("ENUMERATED_OPERATOR_DECISION")
    assert totality["AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS"] == ("ENUMERATED_OPERATOR_DECISION")


def test_open_backlog_invalid_when_inventories_empty() -> None:
    snapshot = {
        "status": "OPEN_BACKLOG",
        "open_unpreregistered_count": 0,
        "preregistered_count": 0,
        "open_unpreregistered_candidates": [],
        "preregistered_hypotheses": [],
    }
    codes = classify_invalid_lane_snapshot(snapshot)
    assert "OPEN_LANE_EMPTY_INVENTORY_WITHOUT_WAITING_SEMANTICS" in codes
    with pytest.raises(ResearchLaneLifecycleContractError, match="INVALID_LANE_SNAPSHOT"):
        validate_lane_snapshot(snapshot)


def test_open_backlog_valid_with_candidate_inventory() -> None:
    snapshot = {
        "status": "OPEN_BACKLOG",
        "open_unpreregistered_candidates": [{"candidate_id": "C1"}],
        "preregistered_hypotheses": [],
    }
    report = validate_lane_snapshot(snapshot)
    assert report["valid"] is True
    assert report["inventory_non_empty"] is True


@pytest.mark.parametrize("result_class", ["PASS", "FAIL", "INFRASTRUCTURE_FAILURE"])
def test_post_terminal_empty_inventory_requires_operator_decision(
    result_class: str,
) -> None:
    resolved = resolve_post_terminal_transition(
        result_class=result_class,
        inventory_non_empty_flag=False,
    )
    assert resolved["operator_decision_required"] is True
    assert resolved["next_state"] == "POST_TERMINAL_OPERATOR_DECISION_REQUIRED"
    assert resolved["deterministic_next"] is None
    assert set(resolved["allowed_operator_decisions"]) == {
        "DECLARE_AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS",
        "CLOSE_LANE_NO_FURTHER_RESEARCH",
        "CREATE_SUCCESSOR_HYPOTHESIS",
    }


@pytest.mark.parametrize("result_class", ["PASS", "FAIL"])
def test_post_terminal_non_empty_inventory_stays_open_backlog(result_class: str) -> None:
    resolved = resolve_post_terminal_transition(
        result_class=result_class,
        inventory_non_empty_flag=True,
    )
    assert resolved["operator_decision_required"] is False
    assert resolved["next_state"] == "OPEN_BACKLOG"


def test_operator_decision_contract_go_and_successor_rules() -> None:
    assert "CREATE_SUCCESSOR_HYPOTHESIS" in OPERATOR_DECISIONS
    with pytest.raises(ResearchLaneLifecycleContractError, match="INVALID_LANE_SNAPSHOT"):
        validate_lane_snapshot(
            {
                "status": "POST_TERMINAL_OPERATOR_DECISION_REQUIRED",
                "open_unpreregistered_candidates": [],
                "preregistered_hypotheses": [],
                "go_executable": True,
                "go_target": None,
            }
        )
    with pytest.raises(
        ResearchLaneLifecycleContractError, match="SUCCESSOR_REQUIRES_HYPOTHESIS_ID"
    ):
        validate_lane_snapshot(
            {
                "status": "AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS",
                "explicit_waiting_decision": True,
                "open_unpreregistered_candidates": [],
                "preregistered_hypotheses": [],
                "transition_trigger": "CREATE_SUCCESSOR_HYPOTHESIS",
                "hypothesis_id": "",
                "mechanism_definition": "mech",
            }
        )
    report = validate_lane_snapshot(
        {
            "status": "AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS",
            "explicit_waiting_decision": True,
            "open_unpreregistered_candidates": [],
            "preregistered_hypotheses": [],
            "transition_trigger": "CREATE_SUCCESSOR_HYPOTHESIS",
            "hypothesis_id": "H_NEXT",
            "mechanism_definition": "explicit_mechanism_v1",
            "go_executable": True,
            "go_target": "H_NEXT",
        }
    )
    assert report["valid"] is True


def test_closeout_and_reopen_require_explicit_decisions() -> None:
    with pytest.raises(ResearchLaneLifecycleContractError, match="INVALID_LANE_SNAPSHOT"):
        validate_lane_snapshot(
            {
                "status": "LANE_CLOSED_NO_FURTHER_RESEARCH",
                "open_unpreregistered_candidates": [],
                "preregistered_hypotheses": [],
                "explicit_closeout_decision": False,
            }
        )
    closed = validate_lane_snapshot(
        {
            "status": "LANE_CLOSED_NO_FURTHER_RESEARCH",
            "open_unpreregistered_candidates": [],
            "preregistered_hypotheses": [],
            "explicit_closeout_decision": True,
        }
    )
    assert closed["valid"] is True
    reopen = validate_lane_snapshot(
        {
            "status": "OPEN_BACKLOG",
            "open_unpreregistered_candidates": [],
            "preregistered_hypotheses": [{"hypothesis_id": "H_REOPEN"}],
            "transition_trigger": "REOPEN_CLOSED_LANE_WITH_NEW_HYPOTHESIS_IDENTITY",
            "explicit_reopen_decision": True,
            "hypothesis_id": "H_REOPEN",
            "mechanism_definition": "mech_reopen",
        }
    )
    assert reopen["valid"] is True


def test_invalid_states_enumeration_and_auto_successor() -> None:
    contract = load_lifecycle_contract(REPO_ROOT)
    codes = {item["code"] for item in contract["invalid_states"]}
    assert codes == INVALID_STATE_CODES
    assert "AUTO_CREATED_SUCCESSOR" in classify_invalid_lane_snapshot(
        {
            "status": "OPEN_BACKLOG",
            "open_unpreregistered_candidates": [{"candidate_id": "x"}],
            "auto_created_successor": True,
        }
    )
    assert "CLOSED_LANE_WITH_IMPLICIT_SUCCESSOR" in classify_invalid_lane_snapshot(
        {
            "status": "LANE_CLOSED_NO_FURTHER_RESEARCH",
            "explicit_closeout_decision": True,
            "implicit_successor": True,
            "open_unpreregistered_candidates": [],
            "preregistered_hypotheses": [],
        }
    )


def test_historical_immutability_and_live_mirror_policy() -> None:
    contract = load_lifecycle_contract(REPO_ROOT)
    imm = contract["immutability_policy"]
    assert set(imm["immutable_artifact_classes"]) == IMMUTABLE_ARTIFACT_CLASSES
    assert imm["authorization_summaries_class"] == "HISTORICAL_SNAPSHOT_NOT_LIVE_MIRROR"
    assert (
        imm["live_authority_and_ratification_after_execution"]
        == "MUST_NOT_MUTATE_SEALED_SNAPSHOT_OBJECTS"
    )
    with pytest.raises(
        ResearchLaneLifecycleContractError,
        match="IMMUTABLE_ARTIFACT_MUTATION_FORBIDDEN",
    ):
        validate_lane_snapshot(
            {
                "status": "LANE_CLOSED_NO_FURTHER_RESEARCH",
                "explicit_closeout_decision": True,
                "open_unpreregistered_candidates": [],
                "preregistered_hypotheses": [],
                "artifact_class": "EVALUATION_EVIDENCE",
                "artifact_mutated_after_seal": True,
            }
        )


def test_owner_map_and_technical_wiring_registration() -> None:
    import json

    owner_map = json.loads(OWNER_MAP.read_text(encoding="utf-8"))
    surfaces = owner_map["allowed_optimization_surfaces"]
    assert CONTRACT_ID in surfaces
    prefixes = surfaces[CONTRACT_ID]["path_prefixes"]
    expected = {
        "config/research/canonical_research_lane_post_terminal_lifecycle_contract_v1.json",
        "src/research/canonical_research_lane_post_terminal_lifecycle_contract_v1.py",
        "tests/research/test_canonical_research_lane_post_terminal_lifecycle_contract_v1.py",
        "docs/governance/CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1.md",
    }
    assert expected.issubset(set(prefixes))
    assert list(surfaces) == sorted(surfaces)

    wiring = json.loads(TECH_WIRING.read_text(encoding="utf-8"))
    allowed = set(wiring["allowed_paths"])
    assert expected.issubset(allowed)


def test_migration_deferred_and_production_lanes_untouched() -> None:
    contract = load_lifecycle_contract(REPO_ROOT)
    assert contract["migration_deferred"]["migrate_in_this_slice"] is False
    entry = (
        REPO_ROOT / "config/research/canonical_open_mr_entry_eligibility_hypothesis_backlog_v1.json"
    )
    exit_eff = (
        REPO_ROOT / "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"
    )
    entry_payload = json.loads(entry.read_text(encoding="utf-8"))
    exit_payload = exit_eff.read_text(encoding="utf-8")
    assert entry_payload["status"] == "POST_TERMINAL_OPERATOR_DECISION_REQUIRED"
    assert entry_payload["lifecycle_contract_id"] == CONTRACT_ID
    assert entry_payload["lane_auto_closed"] is False
    assert contract["migration_deferred"].get("entry_eligibility_migrated") is True
    assert contract["migration_deferred"].get("exit_efficiency_migrated") is False
    assert '"status": "OPEN_BACKLOG"' in exit_payload
    assert "LANE_CLOSED_NO_FURTHER_RESEARCH" not in exit_payload
    assert "POST_TERMINAL_OPERATOR_DECISION_REQUIRED" not in exit_payload
