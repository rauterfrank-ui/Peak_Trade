"""Contract tests for deploy_inactive_v1."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest_plugins = ["tests.meta.deploy_inactive_v1_fixtures"]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from src.meta.learning_loop.deploy_inactive_v1 import (
    DEPLOYMENT_CANDIDATE_ARTIFACT_REL,
    DEPLOY_INACTIVE_AUTHORITY_INVARIANTS,
    OBSERVED_STATE_SOURCE,
    VERIFICATION_ARTIFACT_REL,
    DeployInactiveError,
    OfflineDeclarativeProjection,
    build_deployed_inactive_verification_v1,
    build_deployment_candidate_v1,
    default_deployment_candidate_evaluation_input,
    evaluate_deployed_inactive_verification_v1,
    evaluate_deployment_candidate_v1,
    produce_deployed_inactive_verification_v1,
    produce_deployment_candidate_v1,
    reverify_deployed_inactive_verification_v1,
    reverify_deployment_candidate_v1,
    serialize_deployment_candidate_v1,
)
from tests.meta.deploy_inactive_v1_fixtures import (
    build_valid_deployment_candidate_input,
    build_valid_verification_input,
    matching_projection,
    minimal_invalid_digest,
    produce_deployment_candidate_fixture,
    produce_verification_fixture,
)

_NON_MUTATION_FLAGS = (
    "real_deployment_performed",
    "file_transfer_to_runtime_performed",
    "runtime_installation_performed",
    "runtime_registration_performed",
    "deployment_created",
    "deployment_mutated",
    "deployment_activated",
    "authority_created",
    "execution_permission_created",
    "scheduler_enabled",
    "adapter_invoked",
    "order_submitted",
    "network_side_effect_created",
    "live_authorized",
    "orders_allowed",
)

_CANDIDATE_AFFIRMATIONS = (
    "does_not_transfer_file",
    "does_not_install_runtime",
    "does_not_register_runtime",
    "does_not_create_deployment",
    "does_not_activate_deployment",
    "does_not_invoke_scheduler",
    "does_not_mutate_runtime",
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.deploy_inactive_v1.is_under_tmp",
        lambda _path: False,
    )


def _durable_output(tmp_path: Path, name: str) -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _assert_candidate_non_mutation(payload: dict) -> None:
    for flag in _NON_MUTATION_FLAGS:
        assert payload.get(flag) is False, flag
    for flag in _CANDIDATE_AFFIRMATIONS:
        assert payload.get(flag) is True, flag
    assert payload.get("offline_only") is True


def test_valid_runtime_eligible_candidate_is_deployable() -> None:
    contract = build_deployment_candidate_v1(default_deployment_candidate_evaluation_input())
    assert contract["deployment_candidate_status"] == "DEPLOYABLE"
    assert contract["decision_code"] == "DEPLOYABLE"
    _assert_candidate_non_mutation(contract)


def test_deployment_candidate_deterministic_repeat() -> None:
    request = default_deployment_candidate_evaluation_input()
    assert build_deployment_candidate_v1(request) == build_deployment_candidate_v1(request)


def test_deployment_candidate_canonical_json_stability() -> None:
    contract = build_deployment_candidate_v1(default_deployment_candidate_evaluation_input())
    assert serialize_deployment_candidate_v1(contract) == deterministic_json_dumps(contract)


def test_deployment_candidate_producer_replay_and_manifest(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "candidate_out")
    result = produce_deployment_candidate_v1(
        request=default_deployment_candidate_evaluation_input(),
        output_dir=out,
    )
    verified = reverify_deployment_candidate_v1(output_dir=out)
    ok, _msg = verify_manifest_sha256(out)
    assert ok
    assert verified["deployment_candidate_status"] == "DEPLOYABLE"
    assert result.deployment_candidate_id == verified["deployment_candidate_id"]


def test_deployable_does_not_authorize() -> None:
    contract = build_deployment_candidate_v1(default_deployment_candidate_evaluation_input())
    assert contract["deployment_candidate_status"] == "DEPLOYABLE"
    _assert_candidate_non_mutation(contract)
    assert DEPLOY_INACTIVE_AUTHORITY_INVARIANTS["deployable_does_not_allow_orders"] is True


def test_futures_market_type_accepted_for_candidate() -> None:
    contract = build_deployment_candidate_v1(
        build_valid_deployment_candidate_input(market_type="FUTURES")
    )
    assert contract["deployment_candidate_status"] == "DEPLOYABLE"
    assert contract["market_type"] == "FUTURES"


@pytest.mark.parametrize(
    ("override", "expected_code"),
    [
        ({"runtime_eligibility_ref": ""}, "MISSING_RUNTIME_ELIGIBILITY"),
        ({"runtime_eligibility_status": "INELIGIBLE"}, "RUNTIME_ELIGIBILITY_STATUS_NOT_ELIGIBLE"),
        (
            {"runtime_eligibility_digest": minimal_invalid_digest()},
            "RUNTIME_ELIGIBILITY_DIGEST_MISMATCH",
        ),
        ({"candidate_artifact_ref": ""}, "MISSING_CANDIDATE_ARTIFACT"),
        (
            {"candidate_artifact_digest": minimal_invalid_digest()},
            "CANDIDATE_ARTIFACT_DIGEST_MISMATCH",
        ),
        ({"candidate_artifact_version": "v99"}, "UNSUPPORTED_CANDIDATE_VERSION"),
        ({"promotion_decision_ref": ""}, "MISSING_PROMOTION_DECISION"),
        ({"promotion_decision_outcome": "REJECT"}, "PROMOTION_STATUS_NOT_APPROVED"),
        ({"package_ref": ""}, "MISSING_PACKAGE"),
        ({"deployment_layout_ref": ""}, "MISSING_DEPLOYMENT_LAYOUT"),
        ({"deployment_policy_digest": ""}, "MISSING_DEPLOYMENT_POLICY"),
        ({"expected_loader_contract": ""}, "MISSING_LOADER_CONTRACT"),
        ({"expected_runtime_contract": ""}, "MISSING_RUNTIME_CONTRACT"),
        ({"expected_configuration_digest": ""}, "CONFIGURATION_DIGEST_MISMATCH"),
        ({"rollback_parent_ref": ""}, "ROLLBACK_PARENT_MISSING"),
        ({"rollback_artifact_ref": ""}, "ROLLBACK_ARTIFACT_MISSING"),
        ({"artifact_integrity_status": "NOT_PROVEN"}, "ARTIFACT_INTEGRITY_NOT_PROVEN"),
        ({"loader_compatibility_status": "NOT_PROVEN"}, "LOADER_COMPATIBILITY_NOT_PROVEN"),
        (
            {"runtime_contract_compatibility_status": "NOT_PROVEN"},
            "RUNTIME_CONTRACT_COMPATIBILITY_NOT_PROVEN",
        ),
        ({"data_readiness_status": "NOT_PROVEN"}, "DATA_READINESS_NOT_PROVEN"),
        ({"budget_readiness_status": "NOT_PROVEN"}, "BUDGET_READINESS_NOT_PROVEN"),
        ({"input_refs": (), "input_digests": ()}, "MISSING_REQUIRED_INPUT"),
        ({"contract_version": "v99"}, "UNKNOWN_CONTRACT_VERSION"),
        ({"market_type": "SPOT"}, "SPOT_MARKET_TYPE_REJECTED"),
        ({"market_type": "SYNTHETIC_SPOT"}, "SYNTHETIC_SPOT_MARKET_TYPE_REJECTED"),
        ({"market_type": "OPTIONS"}, "UNKNOWN_MARKET_TYPE_REJECTED"),
        ({"market_type": ""}, "MISSING_MARKET_TYPE_REJECTED"),
        ({"real_deployment_requested": True}, "REAL_DEPLOYMENT_REQUESTED"),
        ({"file_transfer_requested": True}, "FILE_TRANSFER_REQUESTED"),
        ({"runtime_installation_requested": True}, "RUNTIME_INSTALLATION_REQUESTED"),
        ({"activation_requested": True}, "ACTIVATION_REQUESTED"),
        ({"scheduler_enable_requested": True}, "SCHEDULER_ENABLE_REQUESTED"),
        ({"order_submission_requested": True}, "ORDER_SUBMISSION_REQUESTED"),
    ],
)
def test_deployment_candidate_fail_closed(override: dict, expected_code: str) -> None:
    result = evaluate_deployment_candidate_v1(build_valid_deployment_candidate_input(**override))
    assert result.deployment_candidate_status == "NOT_DEPLOYABLE"
    assert result.decision_code == expected_code
    _assert_candidate_non_mutation(result.contract_body)


def test_deployment_candidate_manifest_tampering_rejected(tmp_path: Path) -> None:
    out = produce_deployment_candidate_fixture(tmp_path)
    artifact_path = out / DEPLOYMENT_CANDIDATE_ARTIFACT_REL
    artifact_path.write_text(artifact_path.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(DeployInactiveError):
        reverify_deployment_candidate_v1(output_dir=out)


def test_valid_offline_projection_verified() -> None:
    candidate = build_deployment_candidate_v1(default_deployment_candidate_evaluation_input())
    contract = build_deployed_inactive_verification_v1(build_valid_verification_input(candidate))
    assert contract["verification_status"] == "VERIFIED_INACTIVE_PROJECTION"
    assert contract["observed_state_source"] == OBSERVED_STATE_SOURCE
    assert contract["real_runtime_observation"] is False
    assert contract["real_deployment_confirmed"] is False
    assert contract["deployment_state"] == "INACTIVE"
    assert contract["activation_state"] == "DISABLED"
    assert contract["scheduler_state"] == "DISABLED"
    assert contract["authority_state"] == "ABSENT"
    assert contract["execution_permission_state"] == "ABSENT"
    assert contract["order_capability_state"] == "DISABLED"


def test_verification_producer_replay_and_manifest(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "verification_out")
    candidate = build_deployment_candidate_v1(default_deployment_candidate_evaluation_input())
    result = produce_deployed_inactive_verification_v1(
        request=build_valid_verification_input(candidate),
        output_dir=out,
    )
    verified = reverify_deployed_inactive_verification_v1(output_dir=out)
    ok, _msg = verify_manifest_sha256(out)
    assert ok
    assert verified["verification_status"] == "VERIFIED_INACTIVE_PROJECTION"
    assert result.verification_id == verified["verification_id"]


@pytest.mark.parametrize(
    ("override", "expected_code"),
    [
        ({"deployment_candidate_ref": ""}, "MISSING_DEPLOYMENT_CANDIDATE"),
        ({"deployment_candidate_status": "NOT_DEPLOYABLE"}, "DEPLOYMENT_CANDIDATE_NOT_DEPLOYABLE"),
        ({"real_runtime_observation_requested": True}, "REAL_RUNTIME_OBSERVATION_REQUESTED"),
    ],
)
def test_verification_fail_closed(override: dict, expected_code: str) -> None:
    candidate = build_deployment_candidate_v1(default_deployment_candidate_evaluation_input())
    result = evaluate_deployed_inactive_verification_v1(
        build_valid_verification_input(candidate, **override)
    )
    assert result.verification_status == "VERIFICATION_FAILED"
    assert result.decision_code == expected_code


def test_verification_observed_digest_mismatch() -> None:
    candidate = build_deployment_candidate_v1(default_deployment_candidate_evaluation_input())
    bad_projection = OfflineDeclarativeProjection(
        observed_artifact_digest=minimal_invalid_digest(),
        observed_configuration_digest=str(candidate["expected_configuration_digest"]),
        observed_deployment_layout_digest=str(candidate["deployment_layout_digest"]),
        observed_loader_contract_digest=str(candidate["expected_loader_contract_digest"]),
        observed_runtime_contract_digest=str(candidate["expected_runtime_contract_digest"]),
    )
    result = evaluate_deployed_inactive_verification_v1(
        build_valid_verification_input(candidate, projection=bad_projection)
    )
    assert result.decision_code == "OBSERVED_ARTIFACT_DIGEST_MISMATCH"


def test_verification_activation_present_fails() -> None:
    candidate = build_deployment_candidate_v1(default_deployment_candidate_evaluation_input())
    projection = matching_projection(candidate)
    bad = OfflineDeclarativeProjection(
        observed_artifact_digest=projection.observed_artifact_digest,
        observed_configuration_digest=projection.observed_configuration_digest,
        observed_deployment_layout_digest=projection.observed_deployment_layout_digest,
        observed_loader_contract_digest=projection.observed_loader_contract_digest,
        observed_runtime_contract_digest=projection.observed_runtime_contract_digest,
        activation_state="ENABLED",
    )
    result = evaluate_deployed_inactive_verification_v1(
        build_valid_verification_input(candidate, projection=bad)
    )
    assert result.decision_code in {"ACTIVATION_STATE_NOT_DISABLED", "ACTIVATION_PRESENT"}


def test_verification_manifest_tampering_rejected(tmp_path: Path) -> None:
    out = produce_verification_fixture(tmp_path)
    artifact_path = out / VERIFICATION_ARTIFACT_REL
    artifact_path.write_text(artifact_path.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(DeployInactiveError):
        reverify_deployed_inactive_verification_v1(output_dir=out)
