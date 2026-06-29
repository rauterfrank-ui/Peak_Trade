"""Contract tests for secure_handoff_envelope_v1."""

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
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.authority_lease_and_revocation_v1 import (
    ARTIFACT_REL as AUTHORITY_LEASE_ARTIFACT_REL,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from src.meta.learning_loop.handoff_trust_policy_v1 import (
    ARTIFACT_REL as HANDOFF_ARTIFACT_REL,
    CONSUMER_CONTRACT_ID,
)
from src.meta.learning_loop.secure_handoff_envelope_v1 import (
    ARTIFACT_REL,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    CREATION_CONTRACT_VERSION,
    DEFAULT_PRODUCER_IDENTITY_REF,
    DETERMINISTIC_RULE_SET_VERSION,
    ENVELOPE_SCHEMA_VERSION,
    EVIDENCE_LEVEL,
    MANIFEST_FILENAME,
    PRODUCER_VERSION,
    SECURE_HANDOFF_ENVELOPE_AUTHORITY_INVARIANTS,
    SELF_VERIFICATION_REL,
    SecureHandoffEnvelopeError,
    SecureHandoffEnvelopeInputs,
    SecureHandoffEnvelopeRequest,
    build_secure_handoff_envelope_v1,
    default_envelope_request,
    produce_secure_handoff_envelope_v1,
    reverify_secure_handoff_envelope_v1,
    serialize_secure_handoff_envelope_v1,
    verify_authority_lease_bundle,
)
from tests.meta.authority_lease_and_revocation_v1_fixtures import produce_authority_lease_fixture
from tests.meta.secure_handoff_envelope_v1_fixtures import produce_secure_handoff_envelope_fixture


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
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


def _durable_output(tmp_path: Path, name: str = "envelope_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _default_request(lease) -> SecureHandoffEnvelopeRequest:
    return default_envelope_request(lease=lease)


def test_contract_constants() -> None:
    assert CONTRACT_NAME == "secure_handoff_envelope_v1"
    assert CONTRACT_VERSION == "v1"
    assert ARTIFACT_REL == "secure_handoff_envelope_v1.json"
    assert ENVELOPE_SCHEMA_VERSION == "secure_handoff_envelope_schema_v1"
    assert CREATION_CONTRACT_VERSION == "secure_handoff_envelope_creation_v1"
    assert EVIDENCE_LEVEL == "LEVEL_3"
    assert DETERMINISTIC_RULE_SET_VERSION == "secure_handoff_envelope_rules_v1"


def test_happy_path_envelope_valid(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_secure_handoff_envelope_fixture(tmp_path, ssot_durable_output_dir)
    assert fixture.secure_handoff_envelope_bundle_dir is not None
    payload = read_manifest(fixture.secure_handoff_envelope_bundle_dir / ARTIFACT_REL)
    assert payload["envelope_status"] == "ENVELOPE_VALID_FOR_OFFLINE_HANDOFF"
    assert payload["secure_handoff_envelope_complete"] is True
    assert payload["authority_lease_and_revocation_bound"] is True
    assert payload["handoff_trust_policy_bound"] is True
    assert payload["versioned_artifact_bound"] is True
    assert payload["cross_domain_lineage_bound"] is True
    assert payload["deny_by_default"] is True
    assert payload["envelope_immutable"] is True


def test_required_non_authorizing_flags(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_secure_handoff_envelope_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.secure_handoff_envelope_bundle_dir / ARTIFACT_REL)
    assert payload["handoff_executed"] is False
    assert payload["consumer_invoked"] is False
    assert payload["consumer_mutated"] is False
    assert payload["files_transferred"] is False
    assert payload["authority_granted"] is False
    assert payload["authority_activated"] is False
    assert payload["lease_activated"] is False
    assert payload["revocation_executed"] is False
    assert payload["killswitch_executed"] is False
    assert payload["promotion_authorized"] is False
    assert payload["configpatch_created"] is False
    assert payload["runtime_authorized"] is False
    assert payload["live_authorized"] is False
    assert payload["orders_allowed"] is False
    assert payload["scheduler_runtime_allowed"] is False
    assert payload["signature_created"] is False
    assert payload["private_key_used"] is False
    assert payload["credentials_accessed"] is False
    assert payload["network_side_effect_created"] is False
    assert (
        payload["secure_handoff_envelope_authority_invariants"]
        == SECURE_HANDOFF_ENVELOPE_AUTHORITY_INVARIANTS
    )


def test_determinism(tmp_path, ssot_durable_output_dir) -> None:
    lease_fixture = produce_secure_handoff_envelope_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_authority_lease_bundle(lease_fixture.authority_lease_bundle_dir)
    request = _default_request(verified)
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    inputs = SecureHandoffEnvelopeInputs(
        authority_lease_bundle_dir=lease_fixture.authority_lease_bundle_dir,
        envelope_request=request,
    )
    produce_secure_handoff_envelope_v1(inputs=inputs, output_dir=out_a)
    produce_secure_handoff_envelope_v1(inputs=inputs, output_dir=out_b)
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_envelope_id_stability(tmp_path, ssot_durable_output_dir) -> None:
    lease_fixture = produce_secure_handoff_envelope_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_authority_lease_bundle(lease_fixture.authority_lease_bundle_dir)
    request = _default_request(verified)
    out_a = _durable_output(tmp_path, "id_a")
    out_b = _durable_output(tmp_path, "id_b")
    inputs = SecureHandoffEnvelopeInputs(
        authority_lease_bundle_dir=lease_fixture.authority_lease_bundle_dir,
        envelope_request=request,
    )
    result_a = produce_secure_handoff_envelope_v1(inputs=inputs, output_dir=out_a)
    result_b = produce_secure_handoff_envelope_v1(inputs=inputs, output_dir=out_b)
    assert result_a.envelope_id == result_b.envelope_id
    assert result_a.payload_digest == result_b.payload_digest


def test_self_verification_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_secure_handoff_envelope_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.secure_handoff_envelope_bundle_dir
    assert out is not None
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    self_payload = read_manifest(out / SELF_VERIFICATION_REL)
    assert self_payload["overall_status"] == "PASS"
    reverify_secure_handoff_envelope_v1(output_dir=out)


def test_missing_authority_lease_bundle(tmp_path) -> None:
    with pytest.raises(SecureHandoffEnvelopeError):
        verify_authority_lease_bundle(tmp_path / "missing")


def test_invalid_authority_lease_manifest(tmp_path, ssot_durable_output_dir) -> None:
    lease = produce_authority_lease_fixture(tmp_path, ssot_durable_output_dir)
    bundle_dir = lease.authority_lease_bundle_dir
    (bundle_dir / MANIFEST_FILENAME).write_text("invalid", encoding="utf-8")
    with pytest.raises(SecureHandoffEnvelopeError):
        verify_authority_lease_bundle(bundle_dir)


def test_authority_lease_digest_mismatch_on_reverify(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_secure_handoff_envelope_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.secure_handoff_envelope_bundle_dir
    artifact = read_manifest(out / ARTIFACT_REL)
    artifact["authority_lease_and_revocation_digest"] = "0" * 64
    (out / ARTIFACT_REL).write_text(deterministic_json_dumps(artifact), encoding="utf-8")
    with pytest.raises(SecureHandoffEnvelopeError):
        reverify_secure_handoff_envelope_v1(output_dir=out)


def test_handoff_digest_mismatch_on_reverify(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_secure_handoff_envelope_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.secure_handoff_envelope_bundle_dir
    artifact = read_manifest(out / ARTIFACT_REL)
    artifact["handoff_trust_policy_digest"] = "0" * 64
    (out / ARTIFACT_REL).write_text(deterministic_json_dumps(artifact), encoding="utf-8")
    with pytest.raises(SecureHandoffEnvelopeError):
        reverify_secure_handoff_envelope_v1(output_dir=out)


def test_empty_allowlist_invalid(tmp_path, ssot_durable_output_dir) -> None:
    lease = produce_secure_handoff_envelope_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_authority_lease_bundle(lease.authority_lease_bundle_dir)
    request = replace(_default_request(verified), allowed_offline_capabilities=())
    envelope = build_secure_handoff_envelope_v1(lease=verified, request=request)
    assert envelope["envelope_status"] == "ENVELOPE_INVALID"


def test_wildcard_capability_rejected(tmp_path, ssot_durable_output_dir) -> None:
    lease = produce_secure_handoff_envelope_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_authority_lease_bundle(lease.authority_lease_bundle_dir)
    request = replace(_default_request(verified), allowed_offline_capabilities=("CAN_*",))
    with pytest.raises(SecureHandoffEnvelopeError):
        build_secure_handoff_envelope_v1(lease=verified, request=request)


def test_forbidden_capability_in_allowlist_rejected(tmp_path, ssot_durable_output_dir) -> None:
    lease = produce_secure_handoff_envelope_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_authority_lease_bundle(lease.authority_lease_bundle_dir)
    request = replace(
        _default_request(verified), allowed_offline_capabilities=("CAN_EXECUTE_HANDOFF",)
    )
    with pytest.raises(SecureHandoffEnvelopeError):
        build_secure_handoff_envelope_v1(lease=verified, request=request)


def test_capability_allow_deny_conflict(tmp_path, ssot_durable_output_dir) -> None:
    lease = produce_secure_handoff_envelope_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_authority_lease_bundle(lease.authority_lease_bundle_dir)
    cap = "CAN_DESCRIBE_OFFLINE_HANDOFF_ENVELOPE"
    request = replace(
        _default_request(verified),
        allowed_offline_capabilities=(cap,),
        denied_capabilities=(cap,),
    )
    envelope = build_secure_handoff_envelope_v1(lease=verified, request=request)
    assert envelope["envelope_status"] == "ENVELOPE_INVALID"


def test_consumer_identity_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    lease = produce_secure_handoff_envelope_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_authority_lease_bundle(lease.authority_lease_bundle_dir)
    request = replace(
        _default_request(verified),
        intended_consumer_identity_ref="unknown_consumer_v99",
    )
    envelope = build_secure_handoff_envelope_v1(lease=verified, request=request)
    assert envelope["envelope_status"] == "ENVELOPE_INVALID"


def test_expired_envelope(tmp_path, ssot_durable_output_dir) -> None:
    lease = produce_secure_handoff_envelope_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        evaluation_time="2026-07-01T00:00:00+00:00",
    )
    verified = verify_authority_lease_bundle(lease.authority_lease_bundle_dir)
    request = replace(_default_request(verified), evaluation_time="2026-07-01T00:00:00+00:00")
    envelope = build_secure_handoff_envelope_v1(lease=verified, request=request)
    assert envelope["envelope_status"] == "ENVELOPE_EXPIRED"


def test_revoked_envelope(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_secure_handoff_envelope_fixture(
        tmp_path,
        ssot_durable_output_dir,
        revocation_state="REVOKED",
        envelope_name="revoked_envelope",
    )
    payload = read_manifest(fixture.secure_handoff_envelope_bundle_dir / ARTIFACT_REL)
    assert payload["envelope_status"] == "ENVELOPE_REVOKED"


def test_unknown_revocation_abstains(tmp_path, ssot_durable_output_dir) -> None:
    lease = produce_authority_lease_fixture(
        tmp_path,
        ssot_durable_output_dir,
        revocation_state="UNKNOWN",
        lease_name="unknown_revocation_lease",
    )
    verified = verify_authority_lease_bundle(lease.authority_lease_bundle_dir)
    envelope = build_secure_handoff_envelope_v1(lease=verified, request=_default_request(verified))
    assert envelope["envelope_status"] == "ABSTAIN"


def test_handoff_not_allow_invalidates(tmp_path, ssot_durable_output_dir) -> None:
    lease = produce_authority_lease_fixture(tmp_path, ssot_durable_output_dir)
    handoff_dir = lease.handoff_trust_policy_bundle_dir
    artifact_path = handoff_dir / HANDOFF_ARTIFACT_REL
    payload = read_manifest(artifact_path)
    payload["trust_result"] = "DENY_HANDOFF"
    artifact_path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    with pytest.raises(SecureHandoffEnvelopeError):
        verify_authority_lease_bundle(lease.authority_lease_bundle_dir)


def test_handoff_executed_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_secure_handoff_envelope_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.secure_handoff_envelope_bundle_dir / ARTIFACT_REL)
    payload["handoff_executed"] = True
    with pytest.raises(SecureHandoffEnvelopeError):
        serialize_secure_handoff_envelope_v1(payload)


def test_authority_activated_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_secure_handoff_envelope_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.secure_handoff_envelope_bundle_dir / ARTIFACT_REL)
    payload["authority_activated"] = True
    with pytest.raises(SecureHandoffEnvelopeError):
        serialize_secure_handoff_envelope_v1(payload)


def test_consumer_invoked_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_secure_handoff_envelope_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.secure_handoff_envelope_bundle_dir / ARTIFACT_REL)
    payload["consumer_invoked"] = True
    with pytest.raises(SecureHandoffEnvelopeError):
        serialize_secure_handoff_envelope_v1(payload)


def test_manifest_self_hashing_not_allowed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_secure_handoff_envelope_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.secure_handoff_envelope_bundle_dir
    manifest_path = out / MANIFEST_FILENAME
    content = manifest_path.read_text(encoding="utf-8")
    assert "MANIFEST.sha256" not in content.splitlines()[0]


def test_content_change_after_manifest_invalidates_reverify(
    tmp_path, ssot_durable_output_dir
) -> None:
    fixture = produce_secure_handoff_envelope_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.secure_handoff_envelope_bundle_dir
    artifact_path = out / ARTIFACT_REL
    payload = read_manifest(artifact_path)
    payload["producer_identity_ref"] = "tampered_producer"
    artifact_path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    with pytest.raises(SecureHandoffEnvelopeError):
        reverify_secure_handoff_envelope_v1(output_dir=out)


def test_binding_fields_present(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_secure_handoff_envelope_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.secure_handoff_envelope_bundle_dir / ARTIFACT_REL)
    assert payload["payload_ref"]
    assert payload["payload_digest"]
    assert payload["authority_lease_and_revocation_ref"] == AUTHORITY_LEASE_ARTIFACT_REL
    assert payload["handoff_trust_policy_ref"] == HANDOFF_ARTIFACT_REL
    assert payload["producer_identity_ref"] == DEFAULT_PRODUCER_IDENTITY_REF
    assert payload["intended_consumer_identity_ref"] == CONSUMER_CONTRACT_ID
    assert payload["replay_protection_metadata"]["idempotency_key"] == payload["envelope_id"]
    assert payload["validity_metadata"]["valid_from"]
    assert payload["cross_domain_lineage"]


def test_changed_input_changes_envelope_id(tmp_path, ssot_durable_output_dir) -> None:
    lease = produce_secure_handoff_envelope_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_authority_lease_bundle(lease.authority_lease_bundle_dir)
    request_a = _default_request(verified)
    request_b = replace(
        request_a,
        allowed_offline_capabilities=tuple(
            capability
            for capability in request_a.allowed_offline_capabilities
            if capability != "CAN_BIND_VERSIONED_ARTIFACT_REF"
        ),
    )
    envelope_a = build_secure_handoff_envelope_v1(lease=verified, request=request_a)
    envelope_b = build_secure_handoff_envelope_v1(lease=verified, request=request_b)
    assert envelope_a["envelope_id"] != envelope_b["envelope_id"]


def test_producer_consumer_refs(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_secure_handoff_envelope_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.secure_handoff_envelope_bundle_dir / ARTIFACT_REL)
    assert payload["producer_version"] == PRODUCER_VERSION
    assert payload["producer_identity_version"] == PRODUCER_VERSION
