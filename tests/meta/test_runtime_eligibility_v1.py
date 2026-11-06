"""Contract tests for runtime_eligibility_v1."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest_plugins = ["tests.meta.runtime_eligibility_v1_fixtures"]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from src.meta.learning_loop.runtime_eligibility_v1 import (
    ARTIFACT_REL,
    CONTRACT_VERSION,
    RUNTIME_ELIGIBILITY_AUTHORITY_INVARIANTS,
    RuntimeEligibilityError,
    build_runtime_eligibility_v1,
    default_runtime_eligibility_evaluation_input,
    evaluate_runtime_eligibility_v1,
    produce_runtime_eligibility_v1,
    reverify_runtime_eligibility_v1,
    serialize_runtime_eligibility_v1,
)
from tests.meta.runtime_eligibility_v1_fixtures import (
    build_valid_runtime_eligibility_input,
    minimal_invalid_digest,
    produce_runtime_eligibility_fixture,
    trading_logic_owner_refs,
)

_NON_MUTATION_FLAGS = (
    "deployment_created",
    "deployment_mutated",
    "deployment_activated",
    "runtime_activated",
    "runtime_state_mutated",
    "trading_session_created",
    "authority_created",
    "authority_activated",
    "lease_created",
    "execution_permission_created",
    "submission_authorized",
    "adapter_invoked",
    "venue_capability_discovery_executed",
    "venue_capability_refresh_executed",
    "reconciliation_executed",
    "killswitch_state_mutated",
    "order_created",
    "order_submitted",
    "network_side_effect_created",
    "exchange_request_sent",
    "live_authorized",
    "orders_allowed",
    "scheduler_runtime_allowed",
)

_NON_MUTATION_AFFIRMATIONS = (
    "does_not_deploy",
    "does_not_activate",
    "does_not_create_authority",
    "does_not_activate_authority",
    "does_not_create_execution_permission",
    "does_not_authorize_submission",
    "does_not_mutate_runtime",
    "does_not_invoke_adapter",
    "does_not_send_network_request",
    "does_not_submit_order",
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.runtime_eligibility_v1.is_under_tmp",
        lambda _path: False,
    )


def _durable_output(tmp_path: Path, name: str = "runtime_eligibility_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _assert_non_mutation(payload: dict) -> None:
    for flag in _NON_MUTATION_FLAGS:
        assert payload.get(flag) is False, flag
    for flag in _NON_MUTATION_AFFIRMATIONS:
        assert payload.get(flag) is True, flag
    assert payload.get("offline_only") is True


def test_valid_candidate_is_eligible() -> None:
    contract = build_runtime_eligibility_v1(default_runtime_eligibility_evaluation_input())
    assert contract["eligibility_status"] == "ELIGIBLE"
    assert contract["decision_code"] == "ELIGIBLE"
    _assert_non_mutation(contract)


def test_deterministic_repeat_identical_inputs() -> None:
    request = default_runtime_eligibility_evaluation_input()
    first = build_runtime_eligibility_v1(request)
    second = build_runtime_eligibility_v1(request)
    assert first == second


def test_canonical_json_and_digest_stability() -> None:
    contract = build_runtime_eligibility_v1(default_runtime_eligibility_evaluation_input())
    serialized = serialize_runtime_eligibility_v1(contract)
    reserialized = deterministic_json_dumps(contract)
    assert serialized == reserialized
    assert contract["output_digest"] == contract["integrity"]["content_sha256"]


def test_producer_validator_replay_and_manifest(tmp_path: Path) -> None:
    out = _durable_output(tmp_path)
    result = produce_runtime_eligibility_v1(
        request=default_runtime_eligibility_evaluation_input(),
        output_dir=out,
    )
    verified = reverify_runtime_eligibility_v1(output_dir=out)
    ok, _msg = verify_manifest_sha256(out)
    assert ok
    assert verified["eligibility_status"] == "ELIGIBLE"
    assert result.evidence_id == verified["evidence_id"]


def test_trading_logic_owner_binding_complete() -> None:
    contract = build_runtime_eligibility_v1(
        build_valid_runtime_eligibility_input(**trading_logic_owner_refs())
    )
    assert contract["eligibility_status"] == "ELIGIBLE"
    for key in trading_logic_owner_refs():
        assert contract[key] == trading_logic_owner_refs()[key]


def test_eligible_does_not_authorize() -> None:
    contract = build_runtime_eligibility_v1(default_runtime_eligibility_evaluation_input())
    assert contract["eligibility_status"] == "ELIGIBLE"
    _assert_non_mutation(contract)
    assert (
        RUNTIME_ELIGIBILITY_AUTHORITY_INVARIANTS["eligible_does_not_authorize_submission"] is True
    )


@pytest.mark.parametrize(
    ("override", "expected_code"),
    [
        ({"candidate_artifact_ref": ""}, "MISSING_CANDIDATE_ARTIFACT"),
        (
            {"candidate_artifact_digest": minimal_invalid_digest()},
            "CANDIDATE_ARTIFACT_DIGEST_MISMATCH",
        ),
        ({"candidate_version": "v99"}, "UNSUPPORTED_CANDIDATE_VERSION"),
        ({"promotion_decision_ref": ""}, "MISSING_PROMOTION_DECISION"),
        (
            {"promotion_decision_digest": minimal_invalid_digest()},
            "PROMOTION_DECISION_DIGEST_MISMATCH",
        ),
        ({"promotion_decision_outcome": "REJECT"}, "PROMOTION_STATUS_NOT_APPROVED"),
        (
            {"promotion_authorized_by_canonical_owner": False},
            "PROMOTION_DECISION_NOT_AUTHORIZED_BY_CANONICAL_OWNER",
        ),
        ({"completion_evidence_ref": ""}, "MISSING_COMPLETION_EVIDENCE"),
        ({"research_validity_ref": ""}, "MISSING_RESEARCH_VALIDITY"),
        ({"research_validity_status": "FAIL"}, "RESEARCH_VALIDITY_NOT_PASS"),
        ({"trading_logic_compatibility_ref": ""}, "MISSING_TRADING_LOGIC_COMPATIBILITY"),
        (
            {"trading_logic_compatibility_status": "INCOMPATIBLE"},
            "MISSING_TRADING_LOGIC_COMPATIBILITY",
        ),
        ({"master_v2_owner_ref": "invalid"}, "MASTER_V2_OWNER_INVALID"),
        (
            {"master_v2_contract_digest": minimal_invalid_digest()},
            "MASTER_V2_CONTRACT_DIGEST_MISMATCH",
        ),
        ({"double_play_owner_ref": "invalid"}, "DOUBLE_PLAY_OWNER_INVALID"),
        (
            {"double_play_contract_digest": minimal_invalid_digest()},
            "DOUBLE_PLAY_CONTRACT_DIGEST_MISMATCH",
        ),
        ({"bull_component_ref": ""}, "BULL_BEAR_COMPONENT_BINDING_INVALID"),
        (
            {"bull_bear_semantic_digest": minimal_invalid_digest()},
            "BULL_BEAR_SEMANTIC_DIGEST_MISMATCH",
        ),
        ({"dynamic_scope_owner_ref": "invalid"}, "DYNAMIC_SCOPE_OWNER_INVALID"),
        (
            {"dynamic_scope_policy_digest": minimal_invalid_digest()},
            "DYNAMIC_SCOPE_POLICY_DIGEST_MISMATCH",
        ),
        ({"risk_owner_ref": "invalid"}, "RISK_OWNER_INVALID"),
        ({"sizing_owner_ref": "invalid"}, "SIZING_OWNER_INVALID"),
        ({"scope_capital_owner_ref": "invalid"}, "SCOPE_CAPITAL_OWNER_INVALID"),
        (
            {"canonical_order_intent_contract_digest": minimal_invalid_digest()},
            "CANONICAL_ORDER_INTENT_LINEAGE_INVALID",
        ),
        ({"trading_logic_bypass_detected": True}, "TRADING_LOGIC_BYPASS_DETECTED"),
        ({"parallel_trading_logic_ssot_detected": True}, "PARALLEL_TRADING_LOGIC_SSOT_DETECTED"),
        ({"kill_switch_owner_ref": ""}, "MISSING_KILLSWITCH_CONTRACT"),
        (
            {"kill_switch_contract_digest": minimal_invalid_digest()},
            "KILLSWITCH_CONTRACT_DIGEST_MISMATCH",
        ),
        (
            {"kill_switch_writer_fencing_evidence_ref": ""},
            "MISSING_KILLSWITCH_WRITER_FENCING_EVIDENCE",
        ),
        (
            {"kill_switch_writer_fencing_decision": "BLOCK"},
            "KILLSWITCH_WRITER_FENCING_EVIDENCE_INVALID",
        ),
        (
            {"kill_switch_independent_read_paths_proven": False},
            "KILLSWITCH_INDEPENDENT_READ_PATHS_NOT_PROVEN",
        ),
        ({"pre_trade_safety_kernel_evidence_ref": ""}, "MISSING_PRE_TRADE_SAFETY_KERNEL_EVIDENCE"),
        ({"pre_trade_safety_fail_closed": False}, "PRE_TRADE_SAFETY_NOT_FAIL_CLOSED"),
        ({"adapter_submission_contract_ref": ""}, "MISSING_ADAPTER_SUBMISSION_CONTRACT"),
        (
            {"adapter_submission_contract_status": "ADAPTER_SUBMISSION_CONTRACT_INVALID"},
            "ADAPTER_SUBMISSION_CONTRACT_INVALID",
        ),
        ({"adapter_semantic_mutation_allowed": True}, "ADAPTER_SEMANTIC_MUTATION_ALLOWED"),
        ({"venue_capability_snapshot_ref": ""}, "MISSING_VENUE_CAPABILITY_SNAPSHOT"),
        ({"venue_capability_stale": True}, "VENUE_CAPABILITY_STALE"),
        ({"venue_capability_venue_scope": "OTHER-VENUE"}, "VENUE_CAPABILITY_SCOPE_MISMATCH"),
        ({"reconciliation_evidence_ref": ""}, "MISSING_RECONCILIATION_EVIDENCE"),
        (
            {"reconciliation_contract_status": "RUNTIME_STATE_RECONCILIATION_INVALID"},
            "RECONCILIATION_READINESS_NOT_PROVEN",
        ),
        (
            {"unknown_outcome_recovery_evidence_ref": ""},
            "MISSING_UNKNOWN_OUTCOME_RECOVERY_EVIDENCE",
        ),
        (
            {"unknown_outcome_recovery_fail_closed": False},
            "UNKNOWN_OUTCOME_RECOVERY_NOT_FAIL_CLOSED",
        ),
        ({"authority_contract_ref": ""}, "MISSING_AUTHORITY_CONTRACT"),
        ({"authority_contract_digest": minimal_invalid_digest()}, "AUTHORITY_CONTRACT_INVALID"),
        ({"revocation_contract_ref": ""}, "MISSING_REVOCATION_CONTRACT"),
        ({"environment": ""}, "ENVIRONMENT_BINDING_MISSING"),
        ({"venue_scope": ""}, "VENUE_SCOPE_MISSING"),
        ({"instrument_scope": ""}, "INSTRUMENT_SCOPE_MISSING"),
        ({"risk_policy_digest": ""}, "RISK_POLICY_DIGEST_MISSING"),
        ({"sizing_profile_digest": ""}, "SIZING_PROFILE_BINDING_MISSING"),
        ({"scope_capital_digest": ""}, "SCOPE_CAPITAL_BINDING_MISSING"),
        ({"rollback_parent_ref": ""}, "ROLLBACK_CAPABILITY_MISSING"),
        ({"data_readiness_status": "NOT_PROVEN"}, "DATA_READINESS_NOT_PROVEN"),
        ({"budget_readiness_status": "NOT_PROVEN"}, "BUDGET_READINESS_NOT_PROVEN"),
        ({"input_epoch": 2, "bound_input_epoch": 1}, "INPUT_EPOCH_MISMATCH"),
        ({"input_refs": (), "input_digests": ()}, "MISSING_REQUIRED_INPUT"),
        ({"contract_version": "v99"}, "UNKNOWN_CONTRACT_VERSION"),
        ({"market_type": "SPOT"}, "SPOT_MARKET_TYPE_REJECTED"),
        ({"market_type": "SYNTHETIC_SPOT"}, "SYNTHETIC_SPOT_MARKET_TYPE_REJECTED"),
        ({"market_type": "OPTIONS"}, "UNKNOWN_MARKET_TYPE_REJECTED"),
        ({"market_type": ""}, "MISSING_MARKET_TYPE_REJECTED"),
    ],
)
def test_fail_closed_negative_cases(override: dict, expected_code: str) -> None:
    result = evaluate_runtime_eligibility_v1(build_valid_runtime_eligibility_input(**override))
    assert result.eligibility_status == "INELIGIBLE"
    assert result.decision_code == expected_code
    _assert_non_mutation(result.contract_body)


def test_manifest_tampering_rejected(tmp_path: Path) -> None:
    out = produce_runtime_eligibility_fixture(tmp_path)
    artifact_path = out / ARTIFACT_REL
    artifact_path.write_text(artifact_path.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(RuntimeEligibilityError):
        reverify_runtime_eligibility_v1(output_dir=out)


def test_futures_market_type_accepted() -> None:
    contract = build_runtime_eligibility_v1(
        build_valid_runtime_eligibility_input(market_type="FUTURES")
    )
    assert contract["eligibility_status"] == "ELIGIBLE"
    assert contract["market_type"] == "FUTURES"
