"""Contract tests for Final Research Fleet Class D scope v0."""

from __future__ import annotations

from pathlib import Path

from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
)
from src.research.final_research_fleet_class_d_versioned_bindings_and_offline_economic_evaluation_scope_v0 import (
    AUTHORITY_EFFECT,
    ECONOMIC_EVALUATION_AUTHORIZED,
    ECONOMIC_EVALUATION_EXECUTED,
    GO_TOKEN,
    HISTORICAL_BLOCKED_COMPLETION_DIGEST,
    ORDER_EFFECT,
    RATIFICATION_CLASS,
    RATIFIED_SCOPE_ID,
    RUNTIME_EFFECT,
    ValidationVerdictEnum,
    _apply_class_d_binding_policy,
    materialize_operator_ratification_record_v0,
    materialize_scope_ratification_v0,
    validate_class_d_binding_completion_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_go_token_and_ratification_constants() -> None:
    assert RATIFICATION_CLASS == "D"
    assert RATIFIED_SCOPE_ID == (
        "FINAL_RESEARCH_FLEET_VERSIONED_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_SCOPE_V0"
    )
    assert GO_TOKEN.startswith("GO_BOUNDED_FINAL_RESEARCH_FLEET_CLASS_D_")


def test_no_runtime_authority_constants() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"
    assert ORDER_EFFECT == "NONE"
    assert ECONOMIC_EVALUATION_AUTHORIZED is False
    assert ECONOMIC_EVALUATION_EXECUTED is False


def test_operator_ratification_record() -> None:
    record = materialize_operator_ratification_record_v0(repo_head_sha="abc123")
    assert record["ratification_status"] == "RATIFIED_BY_OPERATOR"
    assert record["ratification_class"] == "D"
    assert record["economic_evaluation_authorized"] is False
    assert record["runtime_rewire_admissible"] is False


def test_class_d_policy_rejects_historical_completion_digest() -> None:
    raw = {
        "schema_version": "versioned_final_fleet_bindings_offline_economic_evaluation.v0",
        "completion_id": "versioned_final_fleet_bindings_offline_economic_evaluation_v0",
        "candidates": [],
        "completion_digest": HISTORICAL_BLOCKED_COMPLETION_DIGEST,
    }
    patched = _apply_class_d_binding_policy(raw)
    assert patched["completion_digest"] != HISTORICAL_BLOCKED_COMPLETION_DIGEST


def test_scope_ratification_non_authorizing() -> None:
    binding = {
        "completion_digest": "new_digest_not_historical",
        "schema_version": "final_research_fleet_class_d_versioned_bindings_and_offline_economic_evaluation_scope.v0",
        "candidates": [
            {
                "canonical_candidate_identifier": f"{sid}/v1",
                "binding_semantic_digest": f"digest_{sid}",
                "dataset_binding": {"dataset_id": "test"},
                "period_binding": {"period_binding_id": "test"},
                "instrument_binding": {"venue_id": "okx"},
                "fee_model_binding": {"fee_bps": 10.0},
                "slippage_model_binding": {"slippage_bps": 5.0},
                "funding_model_binding": {"bind": True},
                "execution_model_binding": {"roundtrip_cost_bps": 40.0},
                "economic_policy_binding": {"policy_version": "economic_validity_policy_v1"},
            }
            for sid, _ver in FLEET_CANDIDATES
        ],
    }
    scope = materialize_scope_ratification_v0(binding_completion=binding)
    assert scope["economic_evaluation_authorized"] is False
    assert scope["evaluation_execution_performed"] is False
    assert scope["allowed_after_this_ratification"] is False
    assert scope["ratified_scope_id"] == RATIFIED_SCOPE_ID


def test_validate_class_d_binding_rejects_eval_authorized_true() -> None:
    completion = {
        "schema_version": "final_research_fleet_class_d_versioned_bindings_and_offline_economic_evaluation_scope.v0",
        "completion_id": "final_research_fleet_class_d_versioned_binding_completion_v0",
        "ratified_scope_id": RATIFIED_SCOPE_ID,
        "ratification_class": "D",
        "economic_evaluation_authorized": True,
        "candidates": [],
        "completion_digest": "abc",
    }
    verdict, reasons = validate_class_d_binding_completion_v0(completion, repo_root=REPO_ROOT)
    assert verdict is ValidationVerdictEnum.REJECTED
    assert any("ECONOMIC_EVALUATION_AUTHORIZED" in reason for reason in reasons)
