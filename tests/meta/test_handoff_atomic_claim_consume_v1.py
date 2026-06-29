"""Contract tests for handoff_atomic_claim_consume_v1."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

pytest_plugins = [
    "tests.meta.comparison_ssot_v1_fixtures",
    "tests.meta.comparison_completion_research_validity_binding_v1_fixtures",
    "tests.meta.comparison_completion_promotion_input_binding_v1_fixtures",
    "tests.meta.comparison_promotion_candidate_identity_binding_v1_fixtures",
    "tests.meta.comparison_promotion_candidate_eligibility_evidence_v1_fixtures",
    "tests.meta.comparison_promotion_candidate_model_parameter_identity_binding_v1_fixtures",
    "tests.meta.comparison_config_patch_manifest_cross_domain_lineage_binding_v1_fixtures",
    "tests.meta.comparison_promotion_candidate_input_v1_fixtures",
    "tests.meta.comparison_eligibility_promotion_policy_input_binding_v1_fixtures",
    "tests.meta.comparison_promotion_policy_input_evidence_v1_fixtures",
    "tests.meta.comparison_promotion_policy_decision_v1_fixtures",
    "tests.meta.ai_promotion_assessment_v1_fixtures",
    "tests.meta.versioned_strategy_model_parameter_artifact_v1_fixtures",
    "tests.meta.handoff_trust_policy_v1_fixtures",
    "tests.meta.authority_lease_and_revocation_v1_fixtures",
    "tests.meta.secure_handoff_envelope_v1_fixtures",
    "tests.meta.handoff_atomic_claim_consume_v1_fixtures",
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from src.meta.learning_loop.handoff_atomic_claim_consume_v1 import (
    ARTIFACT_REL,
    CLAIM_CONTRACT_VERSION,
    CONSUME_CONTRACT_VERSION,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    CREATION_CONTRACT_VERSION,
    DEFAULT_PRODUCER_IDENTITY_REF,
    DETERMINISTIC_RULE_SET_VERSION,
    EVIDENCE_LEVEL,
    HANDOFF_ATOMIC_CLAIM_CONSUME_AUTHORITY_INVARIANTS,
    MANIFEST_FILENAME,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    SELF_VERIFICATION_REL,
    ClaimStateContext,
    HandoffAtomicClaimConsumeError,
    HandoffAtomicClaimConsumeInputs,
    HandoffAtomicClaimConsumeRequest,
    build_handoff_atomic_claim_consume_v1,
    default_claim_consume_request,
    produce_handoff_atomic_claim_consume_v1,
    reverify_handoff_atomic_claim_consume_v1,
    serialize_handoff_atomic_claim_consume_v1,
    verify_secure_handoff_envelope_bundle,
)
from src.meta.learning_loop.handoff_trust_policy_v1 import CONSUMER_CONTRACT_ID
from src.meta.learning_loop.secure_handoff_envelope_v1 import (
    ARTIFACT_REL as ENVELOPE_ARTIFACT_REL,
)
from tests.meta.handoff_atomic_claim_consume_v1_fixtures import (
    produce_handoff_atomic_claim_consume_fixture,
)
from tests.meta.secure_handoff_envelope_v1_fixtures import produce_secure_handoff_envelope_fixture


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.handoff_atomic_claim_consume_v1.is_under_tmp",
        "src.meta.learning_loop.secure_handoff_envelope_v1.is_under_tmp",
        "src.meta.learning_loop.authority_lease_and_revocation_v1.is_under_tmp",
        "src.meta.learning_loop.handoff_trust_policy_v1.is_under_tmp",
        "src.meta.learning_loop.versioned_strategy_model_parameter_artifact_v1.is_under_tmp",
        "src.meta.learning_loop.ai_promotion_assessment_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_policy_decision_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_policy_input_evidence_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_eligibility_promotion_policy_input_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_candidate_input_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_config_patch_manifest_cross_domain_lineage_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_candidate_model_parameter_identity_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_candidate_eligibility_evidence_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_candidate_identity_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_completion_promotion_input_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_completion_research_validity_binding_v1.is_under_tmp",
        "src.experiments.experiment_identity_manifest_v1.is_under_tmp",
    )
    for target in targets:
        monkeypatch.setattr(target, lambda _path: False)


def _durable_output(tmp_path: Path, name: str = "claim_consume_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _default_request(envelope) -> HandoffAtomicClaimConsumeRequest:
    return default_claim_consume_request(envelope=envelope)


def test_contract_constants() -> None:
    assert CONTRACT_NAME == "handoff_atomic_claim_consume_v1"
    assert CONTRACT_VERSION == "v1"
    assert ARTIFACT_REL == "handoff_atomic_claim_consume_v1.json"
    assert CLAIM_CONTRACT_VERSION == "handoff_atomic_claim_v1"
    assert CONSUME_CONTRACT_VERSION == "handoff_atomic_consume_v1"
    assert SCHEMA_VERSION == "handoff_atomic_claim_consume_schema_v1"
    assert EVIDENCE_LEVEL == "LEVEL_3"


def test_happy_path_contract_valid(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(tmp_path, ssot_durable_output_dir)
    assert fixture.handoff_atomic_claim_consume_bundle_dir is not None
    payload = read_manifest(fixture.handoff_atomic_claim_consume_bundle_dir / ARTIFACT_REL)
    assert payload["contract_status"] == "CONTRACT_VALID_FOR_OFFLINE_ATOMIC_CLAIM_CONSUME"
    assert payload["handoff_atomic_claim_consume_complete"] is True
    assert payload["secure_handoff_envelope_bound"] is True
    assert payload["consumer_identity_bound"] is True
    assert payload["replay_protection_bound"] is True
    assert payload["atomic_transition_contract_bound"] is True


def test_required_non_authorizing_flags(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.handoff_atomic_claim_consume_bundle_dir / ARTIFACT_REL)
    assert payload["claim_executed"] is False
    assert payload["consume_executed"] is False
    assert payload["state_mutated"] is False
    assert payload["lock_acquired"] is False
    assert payload["reservation_created"] is False
    assert payload["ack_emitted"] is False
    assert payload["payload_transferred"] is False
    assert payload["files_transferred"] is False
    assert payload["consumer_invoked"] is False
    assert payload["consumer_mutated"] is False
    assert payload["authority_activated"] is False
    assert payload["lease_activated"] is False
    assert payload["revocation_executed"] is False
    assert payload["runtime_authorized"] is False
    assert payload["live_authorized"] is False
    assert payload["orders_allowed"] is False
    assert payload["scheduler_runtime_allowed"] is False
    assert (
        payload["handoff_atomic_claim_consume_authority_invariants"]
        == HANDOFF_ATOMIC_CLAIM_CONSUME_AUTHORITY_INVARIANTS
    )


def test_determinism(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_secure_handoff_envelope_bundle(fixture.secure_handoff_envelope_bundle_dir)
    request = _default_request(verified)
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    inputs = HandoffAtomicClaimConsumeInputs(
        secure_handoff_envelope_bundle_dir=fixture.secure_handoff_envelope_bundle_dir,
        claim_consume_request=request,
    )
    produce_handoff_atomic_claim_consume_v1(inputs=inputs, output_dir=out_a)
    produce_handoff_atomic_claim_consume_v1(inputs=inputs, output_dir=out_b)
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_contract_id_stability(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_secure_handoff_envelope_bundle(fixture.secure_handoff_envelope_bundle_dir)
    request = _default_request(verified)
    out_a = _durable_output(tmp_path, "id_a")
    out_b = _durable_output(tmp_path, "id_b")
    inputs = HandoffAtomicClaimConsumeInputs(
        secure_handoff_envelope_bundle_dir=fixture.secure_handoff_envelope_bundle_dir,
        claim_consume_request=request,
    )
    result_a = produce_handoff_atomic_claim_consume_v1(inputs=inputs, output_dir=out_a)
    result_b = produce_handoff_atomic_claim_consume_v1(inputs=inputs, output_dir=out_b)
    assert result_a.contract_id == result_b.contract_id
    assert result_a.claim_identity == result_b.claim_identity
    assert result_a.consume_identity == result_b.consume_identity


def test_self_verification_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.handoff_atomic_claim_consume_bundle_dir
    assert out is not None
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    self_payload = read_manifest(out / SELF_VERIFICATION_REL)
    assert self_payload["overall_status"] == "PASS"
    reverify_handoff_atomic_claim_consume_v1(output_dir=out)


def test_missing_envelope_bundle(tmp_path) -> None:
    with pytest.raises(HandoffAtomicClaimConsumeError):
        verify_secure_handoff_envelope_bundle(tmp_path / "missing")


def test_invalid_envelope_manifest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_secure_handoff_envelope_fixture(tmp_path, ssot_durable_output_dir)
    bundle_dir = fixture.secure_handoff_envelope_bundle_dir
    (bundle_dir / MANIFEST_FILENAME).write_text("invalid", encoding="utf-8")
    with pytest.raises(HandoffAtomicClaimConsumeError):
        verify_secure_handoff_envelope_bundle(bundle_dir)


def test_envelope_digest_mismatch_on_reverify(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.handoff_atomic_claim_consume_bundle_dir
    artifact = read_manifest(out / ARTIFACT_REL)
    artifact["envelope_digest"] = "0" * 64
    (out / ARTIFACT_REL).write_text(deterministic_json_dumps(artifact), encoding="utf-8")
    with pytest.raises(HandoffAtomicClaimConsumeError):
        reverify_handoff_atomic_claim_consume_v1(output_dir=out)


def test_consumer_identity_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_secure_handoff_envelope_bundle(fixture.secure_handoff_envelope_bundle_dir)
    request = replace(_default_request(verified), consumer_identity_ref="unknown_consumer_v99")
    contract = build_handoff_atomic_claim_consume_v1(envelope=verified, request=request)
    assert contract["contract_status"] == "CONTRACT_INVALID"


def test_expired_contract(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        evaluation_time="2026-07-01T00:00:00+00:00",
    )
    verified = verify_secure_handoff_envelope_bundle(fixture.secure_handoff_envelope_bundle_dir)
    request = replace(_default_request(verified), evaluation_time="2026-07-01T00:00:00+00:00")
    contract = build_handoff_atomic_claim_consume_v1(envelope=verified, request=request)
    assert contract["contract_status"] == "CONTRACT_EXPIRED"


def test_revoked_contract(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(
        tmp_path,
        ssot_durable_output_dir,
        revocation_state="REVOKED",
        claim_consume_name="revoked_claim_consume",
    )
    payload = read_manifest(fixture.handoff_atomic_claim_consume_bundle_dir / ARTIFACT_REL)
    assert payload["contract_status"] == "CONTRACT_REVOKED"


def test_duplicate_claim_replay(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_secure_handoff_envelope_bundle(fixture.secure_handoff_envelope_bundle_dir)
    request = replace(
        _default_request(verified),
        transition_evaluate="CLAIM",
        claim_state_context=ClaimStateContext(
            current_state="CLAIMED",
            current_revision=0,
            claim_identity=build_handoff_atomic_claim_consume_v1(
                envelope=verified, request=_default_request(verified)
            )["claim_identity"],
        ),
    )
    contract = build_handoff_atomic_claim_consume_v1(envelope=verified, request=request)
    assert contract["contract_status"] == "CONTRACT_REPLAY_REJECTED"


def test_duplicate_claim_conflict(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_secure_handoff_envelope_bundle(fixture.secure_handoff_envelope_bundle_dir)
    request = replace(
        _default_request(verified),
        transition_evaluate="CLAIM",
        claim_state_context=ClaimStateContext(
            current_state="CLAIMED",
            current_revision=0,
            claim_identity="0" * 64,
        ),
    )
    contract = build_handoff_atomic_claim_consume_v1(envelope=verified, request=request)
    assert contract["contract_status"] == "CONTRACT_CONFLICT"


def test_consume_without_claim(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_secure_handoff_envelope_bundle(fixture.secure_handoff_envelope_bundle_dir)
    request = replace(
        _default_request(verified),
        transition_evaluate="CONSUME",
        claim_state_context=ClaimStateContext(current_state="UNCLAIMED", current_revision=0),
    )
    contract = build_handoff_atomic_claim_consume_v1(envelope=verified, request=request)
    assert contract["contract_status"] == "CONTRACT_INVALID"


def test_consume_foreign_claim(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_secure_handoff_envelope_bundle(fixture.secure_handoff_envelope_bundle_dir)
    request = replace(
        _default_request(verified),
        transition_evaluate="CONSUME",
        claim_state_context=ClaimStateContext(
            current_state="CLAIMED",
            current_revision=0,
            claim_identity="0" * 64,
        ),
    )
    contract = build_handoff_atomic_claim_consume_v1(envelope=verified, request=request)
    assert contract["contract_status"] == "CONTRACT_INVALID"


def test_duplicate_consume_replay(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_secure_handoff_envelope_bundle(fixture.secure_handoff_envelope_bundle_dir)
    base = build_handoff_atomic_claim_consume_v1(
        envelope=verified, request=_default_request(verified)
    )
    request = replace(
        _default_request(verified),
        transition_evaluate="CONSUME",
        claim_state_context=ClaimStateContext(
            current_state="CONSUMED",
            current_revision=0,
            claim_identity=base["claim_identity"],
            consume_identity=base["consume_identity"],
        ),
    )
    contract = build_handoff_atomic_claim_consume_v1(envelope=verified, request=request)
    assert contract["contract_status"] == "CONTRACT_REPLAY_REJECTED"


def test_stale_revision(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_secure_handoff_envelope_bundle(fixture.secure_handoff_envelope_bundle_dir)
    request = replace(
        _default_request(verified),
        transition_evaluate="CLAIM",
        claim_state_context=ClaimStateContext(current_state="UNCLAIMED", current_revision=5),
    )
    contract = build_handoff_atomic_claim_consume_v1(envelope=verified, request=request)
    assert contract["contract_status"] == "CONTRACT_CONFLICT"


def test_claim_path_claimable(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_secure_handoff_envelope_bundle(fixture.secure_handoff_envelope_bundle_dir)
    request = replace(
        _default_request(verified),
        transition_evaluate="CLAIM",
        claim_state_context=ClaimStateContext(current_state="UNCLAIMED", current_revision=0),
    )
    contract = build_handoff_atomic_claim_consume_v1(envelope=verified, request=request)
    assert contract["contract_status"] == "CONTRACT_CLAIMABLE"
    assert contract["claim_transition_allowed"] is True


def test_consume_path_consumable(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_secure_handoff_envelope_bundle(fixture.secure_handoff_envelope_bundle_dir)
    base = build_handoff_atomic_claim_consume_v1(
        envelope=verified, request=_default_request(verified)
    )
    request = replace(
        _default_request(verified),
        transition_evaluate="CONSUME",
        claim_state_context=ClaimStateContext(
            current_state="CLAIMED",
            current_revision=0,
            claim_identity=base["claim_identity"],
        ),
    )
    contract = build_handoff_atomic_claim_consume_v1(envelope=verified, request=request)
    assert contract["contract_status"] == "CONTRACT_CONSUMABLE"
    assert contract["consume_transition_allowed"] is True


def test_unknown_state(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_secure_handoff_envelope_bundle(fixture.secure_handoff_envelope_bundle_dir)
    request = replace(
        _default_request(verified),
        claim_state_context=ClaimStateContext(current_state="UNKNOWN_STATE", current_revision=0),
    )
    contract = build_handoff_atomic_claim_consume_v1(envelope=verified, request=request)
    assert contract["contract_status"] == "CONTRACT_INVALID"


def test_claim_replay_content_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_secure_handoff_envelope_bundle(fixture.secure_handoff_envelope_bundle_dir)
    request = replace(
        _default_request(verified),
        transition_evaluate="CLAIM",
        claim_state_context=ClaimStateContext(
            current_state="UNCLAIMED",
            current_revision=0,
            prior_claim_content_digest="a" * 64,
        ),
        proposed_claim_content_digest="b" * 64,
    )
    contract = build_handoff_atomic_claim_consume_v1(envelope=verified, request=request)
    assert contract["contract_status"] == "CONTRACT_REPLAY_REJECTED"


def test_changed_input_changes_contract_id(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_secure_handoff_envelope_bundle(fixture.secure_handoff_envelope_bundle_dir)
    request_a = _default_request(verified)
    request_b = replace(request_a, transition_evaluate="CLAIM")
    contract_a = build_handoff_atomic_claim_consume_v1(envelope=verified, request=request_a)
    contract_b = build_handoff_atomic_claim_consume_v1(envelope=verified, request=request_b)
    assert contract_a["contract_id"] != contract_b["contract_id"]


def test_same_input_same_contract_id(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_secure_handoff_envelope_bundle(fixture.secure_handoff_envelope_bundle_dir)
    request = _default_request(verified)
    contract_a = build_handoff_atomic_claim_consume_v1(envelope=verified, request=request)
    contract_b = build_handoff_atomic_claim_consume_v1(envelope=verified, request=request)
    assert contract_a["contract_id"] == contract_b["contract_id"]


def test_claim_executed_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.handoff_atomic_claim_consume_bundle_dir / ARTIFACT_REL)
    payload["claim_executed"] = True
    with pytest.raises(HandoffAtomicClaimConsumeError):
        serialize_handoff_atomic_claim_consume_v1(payload)


def test_consume_executed_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.handoff_atomic_claim_consume_bundle_dir / ARTIFACT_REL)
    payload["consume_executed"] = True
    with pytest.raises(HandoffAtomicClaimConsumeError):
        serialize_handoff_atomic_claim_consume_v1(payload)


def test_state_mutated_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.handoff_atomic_claim_consume_bundle_dir / ARTIFACT_REL)
    payload["state_mutated"] = True
    with pytest.raises(HandoffAtomicClaimConsumeError):
        serialize_handoff_atomic_claim_consume_v1(payload)


def test_lock_acquired_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.handoff_atomic_claim_consume_bundle_dir / ARTIFACT_REL)
    payload["lock_acquired"] = True
    with pytest.raises(HandoffAtomicClaimConsumeError):
        serialize_handoff_atomic_claim_consume_v1(payload)


def test_runtime_authorized_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.handoff_atomic_claim_consume_bundle_dir / ARTIFACT_REL)
    payload["runtime_authorized"] = True
    with pytest.raises(HandoffAtomicClaimConsumeError):
        serialize_handoff_atomic_claim_consume_v1(payload)


def test_manifest_self_hashing_not_allowed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.handoff_atomic_claim_consume_bundle_dir
    manifest_path = out / MANIFEST_FILENAME
    content = manifest_path.read_text(encoding="utf-8")
    assert "MANIFEST.sha256" not in content.splitlines()[0]


def test_content_change_after_manifest_invalidates_reverify(
    tmp_path, ssot_durable_output_dir
) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.handoff_atomic_claim_consume_bundle_dir
    artifact_path = out / ARTIFACT_REL
    payload = read_manifest(artifact_path)
    payload["producer_identity_ref"] = "tampered_producer"
    artifact_path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    with pytest.raises(HandoffAtomicClaimConsumeError):
        reverify_handoff_atomic_claim_consume_v1(output_dir=out)


def test_binding_fields_present(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.handoff_atomic_claim_consume_bundle_dir / ARTIFACT_REL)
    assert payload["envelope_ref"] == ENVELOPE_ARTIFACT_REL
    assert payload["envelope_digest"]
    assert payload["claim_identity"]
    assert payload["consume_identity"]
    assert payload["producer_identity_ref"] == DEFAULT_PRODUCER_IDENTITY_REF
    assert payload["consumer_identity_ref"] == CONSUMER_CONTRACT_ID
    assert payload["allowed_transitions"]
    assert payload["forbidden_transitions"]
    assert payload["transition_preconditions"]
    assert payload["replay_protection_metadata"]["idempotency_key"]
    assert payload["retry_semantics"]["retry_without_double_effect"] is True
    assert (
        payload["crash_consistency_semantics"]["atomicity_model"] == "COMPARE_AND_SWAP_ON_REVISION"
    )
    assert payload["cross_domain_lineage"]


def test_wrong_envelope_contract_name(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_secure_handoff_envelope_fixture(tmp_path, ssot_durable_output_dir)
    bundle_dir = fixture.secure_handoff_envelope_bundle_dir
    artifact = read_manifest(bundle_dir / ENVELOPE_ARTIFACT_REL)
    artifact["contract_name"] = "wrong_contract_v99"
    (bundle_dir / ENVELOPE_ARTIFACT_REL).write_text(
        deterministic_json_dumps(artifact), encoding="utf-8"
    )
    with pytest.raises(HandoffAtomicClaimConsumeError):
        verify_secure_handoff_envelope_bundle(bundle_dir)


def test_state_machine_transitions(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_atomic_claim_consume_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.handoff_atomic_claim_consume_bundle_dir / ARTIFACT_REL)
    allowed = {(item["from_state"], item["to_state"]) for item in payload["allowed_transitions"]}
    assert ("UNCLAIMED", "CLAIMABLE") in allowed
    assert ("CLAIMABLE", "CLAIMED") in allowed
    assert ("CLAIMED", "CONSUMABLE") in allowed
    assert ("CONSUMABLE", "CONSUMED") in allowed
    forbidden = {
        (item["from_state"], item["to_state"]) for item in payload["forbidden_transitions"]
    }
    assert ("UNCLAIMED", "CONSUMED") in forbidden
    assert ("CONSUMED", "CLAIMED") in forbidden
