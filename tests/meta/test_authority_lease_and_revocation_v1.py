"""Contract tests for authority_lease_and_revocation_v1."""

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
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from src.meta.learning_loop.authority_lease_and_revocation_v1 import (
    ARTIFACT_REL,
    AUTHORITY_LEASE_AUTHORITY_INVARIANTS,
    AUTHORITY_LEVEL,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    DEFAULT_ISSUER_IDENTITY_DIGEST,
    DEFAULT_ISSUER_IDENTITY_REF,
    DETERMINISTIC_RULE_SET_VERSION,
    EVIDENCE_LEVEL,
    LEASE_SCHEMA_VERSION,
    MANIFEST_FILENAME,
    PRODUCER_VERSION,
    SELF_VERIFICATION_REL,
    AuthorityLeaseAndRevocationError,
    AuthorityLeaseInputs,
    AuthorityLeaseRequest,
    VerifiedHandoffTrustPolicyBundle,
    build_authority_lease_and_revocation_v1,
    default_lease_request,
    produce_authority_lease_and_revocation_v1,
    reverify_authority_lease_and_revocation_v1,
    serialize_authority_lease_and_revocation_v1,
    verify_authority_lease_inputs,
    verify_handoff_trust_policy_bundle,
)
from src.meta.learning_loop.handoff_trust_policy_v1 import ARTIFACT_REL as HANDOFF_ARTIFACT_REL
from tests.meta.authority_lease_and_revocation_v1_fixtures import produce_authority_lease_fixture
from tests.meta.handoff_trust_policy_v1_fixtures import produce_handoff_trust_policy_fixture


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
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


def _durable_output(tmp_path: Path, name: str = "authority_lease_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _default_request(handoff: VerifiedHandoffTrustPolicyBundle) -> AuthorityLeaseRequest:
    return default_lease_request(handoff=handoff)


def test_contract_constants() -> None:
    assert CONTRACT_NAME == "authority_lease_and_revocation_v1"
    assert CONTRACT_VERSION == "v1"
    assert ARTIFACT_REL == "authority_lease_and_revocation_v1.json"
    assert LEASE_SCHEMA_VERSION == "authority_lease_schema_v1"
    assert EVIDENCE_LEVEL == "LEVEL_3"
    assert AUTHORITY_LEVEL == "NON_AUTHORITIZING"
    assert DETERMINISTIC_RULE_SET_VERSION == "authority_lease_and_revocation_rules_v1"


def test_happy_path_lease_contract_valid(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_authority_lease_fixture(tmp_path, ssot_durable_output_dir)
    assert fixture.authority_lease_bundle_dir is not None
    payload = read_manifest(fixture.authority_lease_bundle_dir / ARTIFACT_REL)
    assert payload["lease_status"] == "LEASE_CONTRACT_VALID"
    assert payload["authority_lease_and_revocation_contract_complete"] is True
    assert payload["handoff_trust_policy_bound"] is True
    assert payload["cross_domain_lineage_bound"] is True
    assert payload["deny_by_default"] is True
    assert payload["revocation_precedence"] is True


def test_required_non_authorizing_flags(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_authority_lease_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.authority_lease_bundle_dir / ARTIFACT_REL)
    assert payload["authority_granted"] is False
    assert payload["authority_activated"] is False
    assert payload["lease_activated"] is False
    assert payload["lease_renewed"] is False
    assert payload["revocation_executed"] is False
    assert payload["killswitch_executed"] is False
    assert payload["consumer_invoked"] is False
    assert payload["runtime_permission_created"] is False
    assert payload["execution_permission_created"] is False
    assert payload["arming_token_created"] is False
    assert payload["promotion_authorized"] is False
    assert payload["configpatch_created"] is False
    assert payload["runtime_authorized"] is False
    assert payload["live_authorized"] is False
    assert payload["orders_allowed"] is False
    assert payload["scheduler_runtime_allowed"] is False
    assert payload["network_side_effect_created"] is False
    assert payload["authority_lease_authority_invariants"] == AUTHORITY_LEASE_AUTHORITY_INVARIANTS


def test_determinism(tmp_path, ssot_durable_output_dir) -> None:
    handoff = produce_authority_lease_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_handoff_trust_policy_bundle(handoff.handoff_trust_policy_bundle_dir)
    request = _default_request(verified)
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    inputs = AuthorityLeaseInputs(
        handoff_trust_policy_bundle_dir=handoff.handoff_trust_policy_bundle_dir,
        lease_request=request,
    )
    produce_authority_lease_and_revocation_v1(inputs=inputs, output_dir=out_a)
    produce_authority_lease_and_revocation_v1(inputs=inputs, output_dir=out_b)
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_self_verification_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_authority_lease_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.authority_lease_bundle_dir
    assert out is not None
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    self_payload = read_manifest(out / SELF_VERIFICATION_REL)
    assert self_payload["overall_status"] == "PASS"
    reverify_authority_lease_and_revocation_v1(output_dir=out)


def test_missing_handoff_bundle(tmp_path) -> None:
    with pytest.raises(AuthorityLeaseAndRevocationError):
        verify_handoff_trust_policy_bundle(tmp_path / "missing")


def test_invalid_handoff_manifest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_handoff_trust_policy_fixture(tmp_path, ssot_durable_output_dir)
    bundle_dir = fixture.handoff_trust_policy_bundle_dir
    (bundle_dir / MANIFEST_FILENAME).write_text("invalid", encoding="utf-8")
    with pytest.raises(AuthorityLeaseAndRevocationError):
        verify_handoff_trust_policy_bundle(bundle_dir)


def test_handoff_digest_mismatch_on_reverify(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_authority_lease_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.authority_lease_bundle_dir
    artifact = read_manifest(out / ARTIFACT_REL)
    artifact["source_handoff_trust_policy_digest"] = "0" * 64
    (out / ARTIFACT_REL).write_text(deterministic_json_dumps(artifact), encoding="utf-8")
    with pytest.raises(AuthorityLeaseAndRevocationError):
        reverify_authority_lease_and_revocation_v1(output_dir=out)


def test_unknown_authority_domain_invalid(tmp_path, ssot_durable_output_dir) -> None:
    handoff = produce_authority_lease_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_handoff_trust_policy_bundle(handoff.handoff_trust_policy_bundle_dir)
    request = replace(_default_request(verified), authority_domain="UNKNOWN_DOMAIN")
    contract = build_authority_lease_and_revocation_v1(handoff=verified, request=request)
    assert contract["lease_status"] == "LEASE_CONTRACT_INVALID"


def test_empty_allowlist_invalid(tmp_path, ssot_durable_output_dir) -> None:
    handoff = produce_authority_lease_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_handoff_trust_policy_bundle(handoff.handoff_trust_policy_bundle_dir)
    request = replace(_default_request(verified), allowed_capabilities=())
    contract = build_authority_lease_and_revocation_v1(handoff=verified, request=request)
    assert contract["lease_status"] == "LEASE_CONTRACT_INVALID"


def test_wildcard_capability_rejected(tmp_path, ssot_durable_output_dir) -> None:
    handoff = produce_authority_lease_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_handoff_trust_policy_bundle(handoff.handoff_trust_policy_bundle_dir)
    request = replace(_default_request(verified), allowed_capabilities=("CAN_*",))
    with pytest.raises(AuthorityLeaseAndRevocationError):
        build_authority_lease_and_revocation_v1(handoff=verified, request=request)


def test_capability_allow_deny_conflict(tmp_path, ssot_durable_output_dir) -> None:
    handoff = produce_authority_lease_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_handoff_trust_policy_bundle(handoff.handoff_trust_policy_bundle_dir)
    cap = "CAN_DESCRIBE_OFFLINE_AUTHORITY_SCOPE"
    request = replace(
        _default_request(verified),
        allowed_capabilities=(cap,),
        denied_capabilities=(cap,),
    )
    contract = build_authority_lease_and_revocation_v1(handoff=verified, request=request)
    assert contract["lease_status"] == "LEASE_CONTRACT_INVALID"


def test_invalid_timezone_rejected(tmp_path, ssot_durable_output_dir) -> None:
    handoff = produce_authority_lease_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_handoff_trust_policy_bundle(handoff.handoff_trust_policy_bundle_dir)
    request = replace(_default_request(verified), valid_from="2026-06-29T00:00:00+01:00")
    contract = build_authority_lease_and_revocation_v1(handoff=verified, request=request)
    assert contract["lease_status"] == "LEASE_CONTRACT_INVALID"


def test_valid_until_before_valid_from(tmp_path, ssot_durable_output_dir) -> None:
    handoff = produce_authority_lease_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_handoff_trust_policy_bundle(handoff.handoff_trust_policy_bundle_dir)
    request = replace(
        _default_request(verified),
        valid_from="2026-06-30T00:00:00+00:00",
        valid_until="2026-06-29T00:00:00+00:00",
        evaluation_time="2026-06-30T00:00:00+00:00",
    )
    contract = build_authority_lease_and_revocation_v1(handoff=verified, request=request)
    factor_ids = {item["factor_id"] for item in contract["contradictions"]}
    assert "VALID_UNTIL_BEFORE_VALID_FROM" in factor_ids
    assert contract["lease_status"] in {"LEASE_CONTRACT_INVALID", "LEASE_EXPIRED"}


def test_boundary_at_valid_from_valid(tmp_path, ssot_durable_output_dir) -> None:
    handoff = produce_authority_lease_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_handoff_trust_policy_bundle(handoff.handoff_trust_policy_bundle_dir)
    request = replace(_default_request(verified), evaluation_time="2026-06-29T00:00:00+00:00")
    contract = build_authority_lease_and_revocation_v1(handoff=verified, request=request)
    assert contract["lease_status"] == "LEASE_CONTRACT_VALID"


def test_boundary_at_valid_until_expired(tmp_path, ssot_durable_output_dir) -> None:
    handoff = produce_authority_lease_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_handoff_trust_policy_bundle(handoff.handoff_trust_policy_bundle_dir)
    request = replace(_default_request(verified), evaluation_time="2026-06-30T00:00:00+00:00")
    contract = build_authority_lease_and_revocation_v1(handoff=verified, request=request)
    assert contract["lease_status"] == "LEASE_EXPIRED"


def test_expired_lease(tmp_path, ssot_durable_output_dir) -> None:
    handoff = produce_authority_lease_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_handoff_trust_policy_bundle(handoff.handoff_trust_policy_bundle_dir)
    request = replace(_default_request(verified), evaluation_time="2026-07-01T00:00:00+00:00")
    contract = build_authority_lease_and_revocation_v1(handoff=verified, request=request)
    assert contract["lease_status"] == "LEASE_EXPIRED"


def test_unknown_revocation_abstains(tmp_path, ssot_durable_output_dir) -> None:
    handoff = produce_authority_lease_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_handoff_trust_policy_bundle(handoff.handoff_trust_policy_bundle_dir)
    request = replace(_default_request(verified), revocation_state="UNKNOWN")
    contract = build_authority_lease_and_revocation_v1(handoff=verified, request=request)
    assert contract["lease_status"] == "ABSTAIN"


def test_revoked_lease_precedence(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_authority_lease_fixture(
        tmp_path,
        ssot_durable_output_dir,
        revocation_state="REVOKED",
    )
    payload = read_manifest(fixture.authority_lease_bundle_dir / ARTIFACT_REL)
    assert payload["lease_status"] == "LEASE_REVOKED"
    assert payload["revocation_precedence"] is True


def test_revocation_beats_grant_even_when_time_valid(tmp_path, ssot_durable_output_dir) -> None:
    handoff = produce_authority_lease_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_handoff_trust_policy_bundle(handoff.handoff_trust_policy_bundle_dir)
    request = replace(
        _default_request(verified),
        revocation_state="REVOKED",
        revocation_ref="offline_revocation_evidence_v1",
        revocation_digest="deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
    )
    contract = build_authority_lease_and_revocation_v1(handoff=verified, request=request)
    assert contract["lease_status"] == "LEASE_REVOKED"


def test_handoff_not_allow_invalidates(tmp_path, ssot_durable_output_dir) -> None:
    handoff = produce_handoff_trust_policy_fixture(tmp_path, ssot_durable_output_dir)
    bundle_dir = handoff.handoff_trust_policy_bundle_dir
    artifact_path = bundle_dir / HANDOFF_ARTIFACT_REL
    payload = read_manifest(artifact_path)
    payload["trust_result"] = "DENY_HANDOFF"
    artifact_path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    with pytest.raises(AuthorityLeaseAndRevocationError):
        verify_handoff_trust_policy_bundle(bundle_dir)


def test_forbidden_capability_in_allowlist_rejected(tmp_path, ssot_durable_output_dir) -> None:
    handoff = produce_authority_lease_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_handoff_trust_policy_bundle(handoff.handoff_trust_policy_bundle_dir)
    request = replace(_default_request(verified), allowed_capabilities=("CAN_GRANT_AUTHORITY",))
    with pytest.raises(AuthorityLeaseAndRevocationError):
        build_authority_lease_and_revocation_v1(handoff=verified, request=request)


def test_authority_granted_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_authority_lease_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.authority_lease_bundle_dir / ARTIFACT_REL)
    payload["authority_granted"] = True
    with pytest.raises(AuthorityLeaseAndRevocationError):
        serialize_authority_lease_and_revocation_v1(payload)


def test_lease_activated_flag_rejected_on_serialize(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_authority_lease_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.authority_lease_bundle_dir / ARTIFACT_REL)
    payload["lease_activated"] = True
    with pytest.raises(AuthorityLeaseAndRevocationError):
        serialize_authority_lease_and_revocation_v1(payload)


def test_manifest_self_hashing_not_allowed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_authority_lease_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.authority_lease_bundle_dir
    manifest_path = out / MANIFEST_FILENAME
    content = manifest_path.read_text(encoding="utf-8")
    assert "MANIFEST.sha256" not in content.splitlines()[0]


def test_content_change_after_manifest_invalidates_reverify(
    tmp_path, ssot_durable_output_dir
) -> None:
    fixture = produce_authority_lease_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.authority_lease_bundle_dir
    artifact_path = out / ARTIFACT_REL
    payload = read_manifest(artifact_path)
    payload["authority_domain"] = "SAFETY_EXECUTION_RUNTIME_CORE"
    artifact_path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    with pytest.raises(AuthorityLeaseAndRevocationError):
        reverify_authority_lease_and_revocation_v1(output_dir=out)


def test_subject_identity_mismatch_invalid(tmp_path, ssot_durable_output_dir) -> None:
    handoff = produce_authority_lease_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_handoff_trust_policy_bundle(handoff.handoff_trust_policy_bundle_dir)
    request = replace(_default_request(verified), subject_identity_digest="1" * 64)
    contract = build_authority_lease_and_revocation_v1(handoff=verified, request=request)
    assert contract["lease_status"] in {"LEASE_CONTRACT_VALID", "LEASE_CONTRACT_INVALID"}


def test_issuer_identity_required(tmp_path, ssot_durable_output_dir) -> None:
    handoff = produce_authority_lease_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_handoff_trust_policy_bundle(handoff.handoff_trust_policy_bundle_dir)
    request = replace(_default_request(verified), issuer_identity_ref="")
    contract = build_authority_lease_and_revocation_v1(handoff=verified, request=request)
    assert contract["lease_status"] == "LEASE_CONTRACT_INVALID"


def test_default_issuer_constants() -> None:
    assert DEFAULT_ISSUER_IDENTITY_REF == "peak_trade_offline_authority_lease_issuer_v1"
    assert len(DEFAULT_ISSUER_IDENTITY_DIGEST) == 64


def test_handoff_trust_policy_ref_bound(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_authority_lease_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.authority_lease_bundle_dir / ARTIFACT_REL)
    assert payload["source_handoff_trust_policy_ref"] == HANDOFF_ARTIFACT_REL
    assert payload["handoff_trust_policy_bound"] is True


def test_cross_domain_lineage_present(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_authority_lease_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.authority_lease_bundle_dir / ARTIFACT_REL)
    assert payload.get("strategy_identity_ref")
    assert payload.get("strategy_identity_digest")
    assert payload.get("cross_domain_lineage")
