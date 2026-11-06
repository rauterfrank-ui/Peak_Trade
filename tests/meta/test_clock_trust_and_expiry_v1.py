"""Contract tests for clock_trust_and_expiry_v1."""

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
    "tests.meta.clock_trust_and_expiry_v1_fixtures",
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from src.meta.learning_loop.clock_trust_and_expiry_v1 import (
    ARTIFACT_REL,
    CLOCK_CONTRACT_VERSION,
    CLOCK_TRUST_AND_EXPIRY_AUTHORITY_INVARIANTS,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    EXPIRY_CONTRACT_VERSION,
    MANIFEST_FILENAME,
    SELF_VERIFICATION_REL,
    ClockTrustAndExpiryError,
    ClockTrustAndExpiryInputs,
    ClockTrustAndExpiryRequest,
    build_clock_trust_and_expiry_v1,
    default_clock_trust_request,
    produce_clock_trust_and_expiry_v1,
    reverify_clock_trust_and_expiry_v1,
    serialize_clock_trust_and_expiry_v1,
    verify_authority_lease_bundle,
    verify_clock_trust_and_expiry_inputs,
    verify_handoff_atomic_claim_consume_bundle,
    verify_secure_handoff_envelope_bundle_for_clock_trust,
)
from tests.meta.clock_trust_and_expiry_v1_fixtures import produce_clock_trust_and_expiry_fixture


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.clock_trust_and_expiry_v1.is_under_tmp",
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


def _durable_output(tmp_path: Path, name: str = "clock_trust_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _fixture_inputs(fixture, *, request: ClockTrustAndExpiryRequest | None = None):
    envelope, claim_consume, authority_lease = verify_clock_trust_and_expiry_inputs(
        ClockTrustAndExpiryInputs(
            secure_handoff_envelope_bundle_dir=fixture.secure_handoff_envelope_bundle_dir,
            handoff_atomic_claim_consume_bundle_dir=fixture.handoff_atomic_claim_consume_bundle_dir,
            authority_lease_and_revocation_bundle_dir=fixture.authority_lease_bundle_dir,
            clock_trust_request=ClockTrustAndExpiryRequest(
                evaluation_time="1970-01-01T00:00:00+00:00",
                evaluation_time_source="OFFLINE_DETERMINISTIC_EVIDENCE",
                evaluation_time_source_identity="placeholder",
                evaluation_time_provenance={"placeholder": True},
            ),
        )
    )
    if request is None:
        request = default_clock_trust_request(
            envelope=envelope,
            authority_lease=authority_lease,
            maximum_clock_skew_seconds=3600,
            maximum_evidence_age_seconds=86400,
        )
    return envelope, claim_consume, authority_lease, request


def test_contract_constants() -> None:
    assert CONTRACT_NAME == "clock_trust_and_expiry_v1"
    assert CONTRACT_VERSION == "v1"
    assert ARTIFACT_REL == "clock_trust_and_expiry_v1.json"
    assert CLOCK_CONTRACT_VERSION == "clock_trust_contract_v1"
    assert EXPIRY_CONTRACT_VERSION == "expiry_contract_v1"


def test_happy_path_contract_valid(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(tmp_path, ssot_durable_output_dir)
    assert fixture.clock_trust_and_expiry_bundle_dir is not None
    payload = read_manifest(fixture.clock_trust_and_expiry_bundle_dir / ARTIFACT_REL)
    assert payload["contract_status"] == "CLOCK_TRUST_VALID_FOR_OFFLINE_TEMPORAL_EVALUATION"
    assert payload["clock_trust_status"] == "TRUSTED"
    assert payload["clock_trust_and_expiry_complete"] is True
    assert payload["secure_handoff_envelope_bound"] is True
    assert payload["handoff_atomic_claim_consume_bound"] is True
    assert payload["authority_lease_and_revocation_bound"] is True


def test_required_non_authorizing_flags(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.clock_trust_and_expiry_bundle_dir / ARTIFACT_REL)
    assert payload["system_clock_read"] is False
    assert payload["wall_clock_read"] is False
    assert payload["network_time_read"] is False
    assert payload["expiry_executed"] is False
    assert payload["claim_executed"] is False
    assert payload["consume_executed"] is False
    assert payload["state_mutated"] is False
    assert payload["consumer_invoked"] is False
    assert payload["runtime_authorized"] is False
    assert payload["live_authorized"] is False
    assert payload["orders_allowed"] is False
    assert (
        payload["clock_trust_and_expiry_authority_invariants"]
        == CLOCK_TRUST_AND_EXPIRY_AUTHORITY_INVARIANTS
    )


def test_determinism(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    envelope, claim_consume, authority_lease, request = _fixture_inputs(fixture)
    inputs = ClockTrustAndExpiryInputs(
        secure_handoff_envelope_bundle_dir=fixture.secure_handoff_envelope_bundle_dir,
        handoff_atomic_claim_consume_bundle_dir=fixture.handoff_atomic_claim_consume_bundle_dir,
        authority_lease_and_revocation_bundle_dir=fixture.authority_lease_bundle_dir,
        clock_trust_request=request,
    )
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    produce_clock_trust_and_expiry_v1(inputs=inputs, output_dir=out_a)
    produce_clock_trust_and_expiry_v1(inputs=inputs, output_dir=out_b)
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_self_verification_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.clock_trust_and_expiry_bundle_dir
    assert out is not None
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    self_payload = read_manifest(out / SELF_VERIFICATION_REL)
    assert self_payload["overall_status"] == "PASS"
    reverify_clock_trust_and_expiry_v1(output_dir=out)


def test_missing_evaluation_time(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    envelope, claim_consume, authority_lease, request = _fixture_inputs(fixture)
    bad_request = replace(request, evaluation_time="")
    contract = build_clock_trust_and_expiry_v1(
        envelope=envelope,
        claim_consume=claim_consume,
        authority_lease=authority_lease,
        request=bad_request,
    )
    assert contract["contract_status"] == "CLOCK_TRUST_INVALID"


def test_malformed_timestamp(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    envelope, claim_consume, authority_lease, request = _fixture_inputs(fixture)
    bad_request = replace(request, evaluation_time="not-a-timestamp")
    contract = build_clock_trust_and_expiry_v1(
        envelope=envelope,
        claim_consume=claim_consume,
        authority_lease=authority_lease,
        request=bad_request,
    )
    assert contract["contract_status"] == "CLOCK_TRUST_INVALID"


def test_untrusted_clock_source(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    envelope, claim_consume, authority_lease, request = _fixture_inputs(fixture)
    bad_request = replace(request, evaluation_time_source="WALL_CLOCK")
    contract = build_clock_trust_and_expiry_v1(
        envelope=envelope,
        claim_consume=claim_consume,
        authority_lease=authority_lease,
        request=bad_request,
    )
    assert contract["contract_status"] == "CLOCK_TRUST_UNTRUSTED_CLOCK_SOURCE"


def test_missing_clock_source_identity(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    envelope, claim_consume, authority_lease, request = _fixture_inputs(fixture)
    bad_request = replace(request, evaluation_time_source_identity="")
    contract = build_clock_trust_and_expiry_v1(
        envelope=envelope,
        claim_consume=claim_consume,
        authority_lease=authority_lease,
        request=bad_request,
    )
    assert contract["contract_status"] == "CLOCK_TRUST_INVALID"


def test_expired_contract(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        evaluation_time="2026-07-01T00:00:00+00:00",
    )
    envelope, claim_consume, authority_lease, request = _fixture_inputs(fixture)
    bad_request = replace(request, evaluation_time="2026-07-01T00:00:00+00:00")
    contract = build_clock_trust_and_expiry_v1(
        envelope=envelope,
        claim_consume=claim_consume,
        authority_lease=authority_lease,
        request=bad_request,
    )
    assert contract["contract_status"] == "CLOCK_TRUST_EXPIRED"
    assert contract["expiry_state"] == "EXPIRED"


def test_stale_evidence(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        evaluation_time="2026-06-29T12:00:00+00:00",
    )
    envelope, claim_consume, authority_lease, request = _fixture_inputs(fixture)
    stale_request = replace(
        request,
        evaluation_time="2026-06-30T12:00:00+00:00",
        maximum_evidence_age_seconds=3600,
    )
    contract = build_clock_trust_and_expiry_v1(
        envelope=envelope,
        claim_consume=claim_consume,
        authority_lease=authority_lease,
        request=stale_request,
    )
    assert contract["contract_status"] == "CLOCK_TRUST_STALE_EVIDENCE"
    assert contract["stale_state"] == "STALE"


def test_excessive_clock_skew(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    envelope, claim_consume, authority_lease, request = _fixture_inputs(fixture)
    skew_request = replace(
        request,
        evaluation_time="2026-06-29T18:00:00+00:00",
        maximum_clock_skew_seconds=60,
    )
    contract = build_clock_trust_and_expiry_v1(
        envelope=envelope,
        claim_consume=claim_consume,
        authority_lease=authority_lease,
        request=skew_request,
    )
    assert contract["contract_status"] == "CLOCK_TRUST_INVALID"


def test_boundary_evaluation_equals_valid_from(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        evaluation_time="2026-06-29T00:00:00+00:00",
        valid_from="2026-06-29T00:00:00+00:00",
    )
    envelope, claim_consume, authority_lease, request = _fixture_inputs(fixture)
    boundary_request = replace(request, evaluation_time="2026-06-29T00:00:00+00:00")
    contract = build_clock_trust_and_expiry_v1(
        envelope=envelope,
        claim_consume=claim_consume,
        authority_lease=authority_lease,
        request=boundary_request,
    )
    assert contract["contract_status"] == "CLOCK_TRUST_VALID_FOR_OFFLINE_TEMPORAL_EVALUATION"


def test_boundary_evaluation_equals_valid_until_expired(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    envelope, claim_consume, authority_lease, request = _fixture_inputs(fixture)
    boundary_request = replace(request, evaluation_time=authority_lease.valid_until)
    contract = build_clock_trust_and_expiry_v1(
        envelope=envelope,
        claim_consume=claim_consume,
        authority_lease=authority_lease,
        request=boundary_request,
    )
    assert contract["contract_status"] == "CLOCK_TRUST_EXPIRED"


def test_boundary_skew_exact_limit(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    envelope, claim_consume, authority_lease, request = _fixture_inputs(fixture)
    skew_request = replace(
        request,
        evaluation_time="2026-06-29T13:00:00+00:00",
        maximum_clock_skew_seconds=3600,
    )
    contract = build_clock_trust_and_expiry_v1(
        envelope=envelope,
        claim_consume=claim_consume,
        authority_lease=authority_lease,
        request=skew_request,
    )
    assert contract["contract_status"] == "CLOCK_TRUST_VALID_FOR_OFFLINE_TEMPORAL_EVALUATION"


def test_boundary_evidence_age_exact_limit(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    envelope, claim_consume, authority_lease, request = _fixture_inputs(fixture)
    age_request = replace(
        request,
        evaluation_time="2026-06-29T13:00:00+00:00",
        maximum_evidence_age_seconds=3600,
    )
    contract = build_clock_trust_and_expiry_v1(
        envelope=envelope,
        claim_consume=claim_consume,
        authority_lease=authority_lease,
        request=age_request,
    )
    assert contract["contract_status"] == "CLOCK_TRUST_VALID_FOR_OFFLINE_TEMPORAL_EVALUATION"


def test_wrong_contract_version(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    envelope, claim_consume, authority_lease, request = _fixture_inputs(fixture)
    bad_request = replace(request, clock_contract_version="clock_trust_contract_v99")
    contract = build_clock_trust_and_expiry_v1(
        envelope=envelope,
        claim_consume=claim_consume,
        authority_lease=authority_lease,
        request=bad_request,
    )
    assert contract["contract_status"] == "CLOCK_TRUST_AMBIGUOUS_ORDERING"


def test_revoked_authority(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path,
        ssot_durable_output_dir,
        revocation_state="REVOKED",
        clock_trust_name="revoked_clock_trust",
    )
    payload = read_manifest(fixture.clock_trust_and_expiry_bundle_dir / ARTIFACT_REL)
    assert payload["contract_status"] == "CLOCK_TRUST_REVOKED"


def test_replay_detection(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    envelope, claim_consume, authority_lease, request = _fixture_inputs(fixture)
    from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

    digest = compute_content_sha256(
        {
            "evaluation_time": request.evaluation_time,
            "envelope_digest": envelope.artifact_digest,
            "claim_consume_digest": claim_consume.artifact_digest,
            "authority_lease_digest": authority_lease.artifact_digest,
        }
    )
    replay_request = replace(request, prior_temporal_evidence_digest=digest)
    contract = build_clock_trust_and_expiry_v1(
        envelope=envelope,
        claim_consume=claim_consume,
        authority_lease=authority_lease,
        request=replay_request,
    )
    assert contract["contract_status"] == "CLOCK_TRUST_REPLAY_REJECTED"


def test_missing_provenance(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    envelope, claim_consume, authority_lease, request = _fixture_inputs(fixture)
    bad_request = replace(request, evaluation_time_provenance={})
    contract = build_clock_trust_and_expiry_v1(
        envelope=envelope,
        claim_consume=claim_consume,
        authority_lease=authority_lease,
        request=bad_request,
    )
    assert contract["contract_status"] == "CLOCK_TRUST_INVALID"


def test_manifest_tamper(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.clock_trust_and_expiry_bundle_dir
    (out / MANIFEST_FILENAME).write_text("invalid", encoding="utf-8")
    with pytest.raises(ClockTrustAndExpiryError):
        reverify_clock_trust_and_expiry_v1(output_dir=out)


def test_self_verification_tamper(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.clock_trust_and_expiry_bundle_dir
    (out / SELF_VERIFICATION_REL).write_text('{"overall_status":"FAIL"}', encoding="utf-8")
    with pytest.raises(ClockTrustAndExpiryError):
        reverify_clock_trust_and_expiry_v1(output_dir=out)


def test_digest_tamper_on_reverify(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.clock_trust_and_expiry_bundle_dir
    artifact = read_manifest(out / ARTIFACT_REL)
    artifact["envelope_digest"] = "0" * 64
    (out / ARTIFACT_REL).write_text(deterministic_json_dumps(artifact), encoding="utf-8")
    with pytest.raises(ClockTrustAndExpiryError):
        reverify_clock_trust_and_expiry_v1(output_dir=out)


def test_missing_envelope_bundle(tmp_path) -> None:
    with pytest.raises(ClockTrustAndExpiryError):
        verify_secure_handoff_envelope_bundle_for_clock_trust(tmp_path / "missing")


def test_missing_claim_consume_bundle(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    with pytest.raises(ClockTrustAndExpiryError):
        verify_handoff_atomic_claim_consume_bundle(tmp_path / "missing")


def test_missing_authority_lease_bundle(tmp_path, ssot_durable_output_dir) -> None:
    with pytest.raises(ClockTrustAndExpiryError):
        verify_authority_lease_bundle(tmp_path / "missing")
