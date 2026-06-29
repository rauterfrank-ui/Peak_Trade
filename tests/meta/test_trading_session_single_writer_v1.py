"""Contract tests for trading_session_single_writer_v1."""

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
    "tests.meta.trading_session_single_writer_v1_fixtures",
]

from src.meta.learning_loop.clock_trust_and_expiry_v1 import (
    ClockTrustAndExpiryInputs,
    ClockTrustAndExpiryRequest,
    default_clock_trust_request,
    produce_clock_trust_and_expiry_v1,
    verify_clock_trust_and_expiry_inputs,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
)
from src.meta.learning_loop.trading_session_single_writer_v1 import (
    ARTIFACT_REL,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    MANIFEST_FILENAME,
    SELF_VERIFICATION_REL,
    SESSION_CONTRACT_VERSION,
    TRADING_SESSION_SINGLE_WRITER_AUTHORITY_INVARIANTS,
    WRITER_CONTRACT_VERSION,
    TradingSessionIdentity,
    TradingSessionSingleWriterError,
    TradingSessionSingleWriterInputs,
    build_trading_session_single_writer_v1,
    default_trading_session_single_writer_request,
    produce_trading_session_single_writer_v1,
    reverify_trading_session_single_writer_v1,
    verify_clock_trust_and_expiry_bundle,
    verify_trading_session_single_writer_inputs,
)
from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from tests.meta.clock_trust_and_expiry_v1_fixtures import produce_clock_trust_and_expiry_fixture
from tests.meta.trading_session_single_writer_v1_fixtures import (
    produce_trading_session_single_writer_fixture,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.trading_session_single_writer_v1.is_under_tmp",
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


def _durable_output(tmp_path: Path, name: str = "single_writer_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _fixture_inputs(fixture):
    clock_trust = verify_clock_trust_and_expiry_bundle(fixture.clock_trust_and_expiry_bundle_dir)
    request = default_trading_session_single_writer_request(clock_trust=clock_trust)
    return clock_trust, request


def test_contract_constants() -> None:
    assert CONTRACT_NAME == "trading_session_single_writer_v1"
    assert CONTRACT_VERSION == "v1"
    assert ARTIFACT_REL == "trading_session_single_writer_v1.json"
    assert SESSION_CONTRACT_VERSION == "trading_session_contract_v1"
    assert WRITER_CONTRACT_VERSION == "writer_fencing_contract_v1"


def test_happy_path_contract_valid(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_session_single_writer_fixture(tmp_path, ssot_durable_output_dir)
    assert fixture.trading_session_single_writer_bundle_dir is not None
    payload = read_manifest(fixture.trading_session_single_writer_bundle_dir / ARTIFACT_REL)
    assert (
        payload["contract_status"] == "TRADING_SESSION_SINGLE_WRITER_VALID_FOR_OFFLINE_EVALUATION"
    )
    assert payload["single_writer_status"] == "VALID"
    assert payload["trading_session_single_writer_contract_complete"] is True
    assert payload["single_writer_invariant_bound"] is True
    assert payload["writer_identity_bound"] is True
    assert payload["writer_generation_bound"] is True
    assert payload["session_identity_bound"] is True
    assert payload["clock_trust_and_expiry_bound"] is True
    assert payload["secure_handoff_envelope_bound"] is True
    assert payload["handoff_atomic_claim_consume_bound"] is True
    assert payload["authority_lease_and_revocation_bound"] is True


def test_required_non_authorizing_flags(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_session_single_writer_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.trading_session_single_writer_bundle_dir / ARTIFACT_REL)
    assert payload["trading_session_started"] is False
    assert payload["writer_registered"] is False
    assert payload["writer_activated"] is False
    assert payload["writer_lock_acquired"] is False
    assert payload["fencing_token_issued"] is False
    assert payload["state_mutated"] is False
    assert payload["runtime_authorized"] is False
    assert payload["live_authorized"] is False
    assert payload["orders_allowed"] is False
    assert (
        payload["trading_session_single_writer_authority_invariants"]
        == TRADING_SESSION_SINGLE_WRITER_AUTHORITY_INVARIANTS
    )


def test_determinism(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_session_single_writer_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    clock_trust, request = _fixture_inputs(fixture)
    inputs = TradingSessionSingleWriterInputs(
        clock_trust_and_expiry_bundle_dir=fixture.clock_trust_and_expiry_bundle_dir,
        trading_session_request=request,
    )
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    produce_trading_session_single_writer_v1(inputs=inputs, output_dir=out_a)
    produce_trading_session_single_writer_v1(inputs=inputs, output_dir=out_b)
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_self_verification_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_session_single_writer_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.trading_session_single_writer_bundle_dir
    assert out is not None
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    self_payload = read_manifest(out / SELF_VERIFICATION_REL)
    assert self_payload["overall_status"] == "PASS"
    reverify_trading_session_single_writer_v1(output_dir=out)


def test_manifest_verify_rc_zero(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_session_single_writer_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.trading_session_single_writer_bundle_dir
    assert out is not None
    rc = 0 if verify_manifest_sha256(out)[0] else 1
    assert rc == 0


def test_idempotent_same_writer(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_session_single_writer_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    clock_trust, request = _fixture_inputs(fixture)
    idempotent_request = replace(
        request,
        prior_writer_identity=request.writer_identity,
        prior_writer_generation=request.writer_generation,
    )
    contract = build_trading_session_single_writer_v1(
        clock_trust=clock_trust,
        request=idempotent_request,
    )
    assert contract["contract_status"] == "TRADING_SESSION_SINGLE_WRITER_IDEMPOTENT"
    assert contract["single_writer_status"] == "IDEMPOTENT"


def test_second_writer_conflict(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_session_single_writer_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    clock_trust, request = _fixture_inputs(fixture)
    conflict_request = replace(request, prior_writer_identity="writer-secondary-002")
    contract = build_trading_session_single_writer_v1(
        clock_trust=clock_trust,
        request=conflict_request,
    )
    assert contract["contract_status"] == "TRADING_SESSION_SINGLE_WRITER_COMPETING_WRITER"
    assert contract["single_writer_status"] == "CONFLICT"


def test_stale_generation(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_session_single_writer_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    clock_trust, request = _fixture_inputs(fixture)
    stale_request = replace(
        request,
        prior_writer_identity=request.writer_identity,
        prior_writer_generation=3,
        writer_generation=2,
    )
    contract = build_trading_session_single_writer_v1(
        clock_trust=clock_trust,
        request=stale_request,
    )
    assert contract["contract_status"] == "TRADING_SESSION_SINGLE_WRITER_STALE_GENERATION"


def test_stale_revision(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_session_single_writer_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    clock_trust, request = _fixture_inputs(fixture)
    stale_request = replace(request, observed_writer_revision=99, expected_writer_revision=1)
    contract = build_trading_session_single_writer_v1(
        clock_trust=clock_trust,
        request=stale_request,
    )
    assert contract["contract_status"] == "TRADING_SESSION_SINGLE_WRITER_STALE_REVISION"


def test_replay_detection(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_session_single_writer_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    clock_trust, request = _fixture_inputs(fixture)
    session_digest = compute_content_sha256(
        {
            "identity_domain": SESSION_CONTRACT_VERSION,
            "venue": request.trading_session_identity.venue,
            "account": request.trading_session_identity.account,
            "instrument": request.trading_session_identity.instrument,
            "trading_epoch": request.trading_session_identity.trading_epoch,
            "deterministic_rule_set_version": "trading_session_single_writer_rules_v1",
        }
    )
    writer_digest = compute_content_sha256(
        {
            "identity_domain": WRITER_CONTRACT_VERSION,
            "writer_identity": request.writer_identity,
            "writer_generation": request.writer_generation,
            "executor_epoch": request.executor_epoch,
            "deterministic_rule_set_version": "trading_session_single_writer_rules_v1",
        }
    )
    evidence_digest = compute_content_sha256(
        {
            "session_identity_digest": session_digest,
            "writer_identity_digest": writer_digest,
            "clock_trust_digest": clock_trust.artifact_digest,
            "expected_writer_revision": request.expected_writer_revision,
            "deterministic_rule_set_version": "trading_session_single_writer_rules_v1",
        }
    )
    replay_request = replace(request, prior_single_writer_evidence_digest=evidence_digest)
    contract = build_trading_session_single_writer_v1(
        clock_trust=clock_trust,
        request=replay_request,
    )
    assert contract["contract_status"] == "TRADING_SESSION_SINGLE_WRITER_REPLAY_REJECTED"


def test_revoked_via_upstream(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_session_single_writer_fixture(
        tmp_path,
        ssot_durable_output_dir,
        revocation_state="REVOKED",
        clock_trust_name="revoked_clock_trust",
        single_writer_name="revoked_single_writer",
    )
    payload = read_manifest(fixture.trading_session_single_writer_bundle_dir / ARTIFACT_REL)
    assert payload["contract_status"] == "TRADING_SESSION_SINGLE_WRITER_REVOKED"


def test_expired_clock_trust(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_session_single_writer_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        evaluation_time="2026-07-01T00:00:00+00:00",
    )
    clock_trust, request = _fixture_inputs(fixture)
    contract = build_trading_session_single_writer_v1(
        clock_trust=clock_trust,
        request=request,
    )
    assert contract["contract_status"] == "TRADING_SESSION_SINGLE_WRITER_EXPIRED"


def test_untrusted_clock(tmp_path, ssot_durable_output_dir) -> None:
    clock_fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
    )
    envelope, _, authority_lease = verify_clock_trust_and_expiry_inputs(
        ClockTrustAndExpiryInputs(
            secure_handoff_envelope_bundle_dir=clock_fixture.secure_handoff_envelope_bundle_dir,
            handoff_atomic_claim_consume_bundle_dir=clock_fixture.handoff_atomic_claim_consume_bundle_dir,
            authority_lease_and_revocation_bundle_dir=clock_fixture.authority_lease_bundle_dir,
            clock_trust_request=ClockTrustAndExpiryRequest(
                evaluation_time="1970-01-01T00:00:00+00:00",
                evaluation_time_source="OFFLINE_DETERMINISTIC_EVIDENCE",
                evaluation_time_source_identity="placeholder",
                evaluation_time_provenance={"placeholder": True},
            ),
        )
    )
    untrusted_request = replace(
        default_clock_trust_request(
            envelope=envelope,
            authority_lease=authority_lease,
            maximum_clock_skew_seconds=3600,
            maximum_evidence_age_seconds=86400,
        ),
        evaluation_time_source="WALL_CLOCK",
    )
    untrusted_clock_dir = ssot_durable_output_dir / "untrusted_clock_trust"
    produce_clock_trust_and_expiry_v1(
        inputs=ClockTrustAndExpiryInputs(
            secure_handoff_envelope_bundle_dir=clock_fixture.secure_handoff_envelope_bundle_dir,
            handoff_atomic_claim_consume_bundle_dir=clock_fixture.handoff_atomic_claim_consume_bundle_dir,
            authority_lease_and_revocation_bundle_dir=clock_fixture.authority_lease_bundle_dir,
            clock_trust_request=untrusted_request,
        ),
        output_dir=untrusted_clock_dir,
    )
    clock_trust = verify_clock_trust_and_expiry_bundle(untrusted_clock_dir)
    request = default_trading_session_single_writer_request(clock_trust=clock_trust)
    contract = build_trading_session_single_writer_v1(
        clock_trust=clock_trust,
        request=request,
    )
    assert contract["contract_status"] == "TRADING_SESSION_SINGLE_WRITER_UNTRUSTED_CLOCK"


def test_identity_tamper(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_session_single_writer_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False, use_candidate_lineage=True
    )
    clock_trust, request = _fixture_inputs(fixture)
    tampered_lineage = dict(request.session_ownership_lineage)
    field = next(iter(tampered_lineage))
    tampered_lineage[field] = f"tampered-{tampered_lineage[field]}"
    tamper_request = replace(request, session_ownership_lineage=tampered_lineage)
    contract = build_trading_session_single_writer_v1(
        clock_trust=clock_trust,
        request=tamper_request,
    )
    assert contract["contract_status"] == "TRADING_SESSION_SINGLE_WRITER_BROKEN_LINEAGE"


def test_missing_session_identity(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_session_single_writer_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    clock_trust, request = _fixture_inputs(fixture)
    bad_request = replace(
        request,
        trading_session_identity=TradingSessionIdentity(
            venue="",
            account=request.trading_session_identity.account,
            instrument=request.trading_session_identity.instrument,
            trading_epoch=request.trading_session_identity.trading_epoch,
        ),
    )
    contract = build_trading_session_single_writer_v1(
        clock_trust=clock_trust,
        request=bad_request,
    )
    assert contract["contract_status"] == "TRADING_SESSION_SINGLE_WRITER_MISSING_IDENTITY"


def test_manifest_tamper(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_session_single_writer_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.trading_session_single_writer_bundle_dir
    (out / MANIFEST_FILENAME).write_text("invalid", encoding="utf-8")
    with pytest.raises(TradingSessionSingleWriterError):
        reverify_trading_session_single_writer_v1(output_dir=out)


def test_digest_tamper_on_reverify(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_session_single_writer_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.trading_session_single_writer_bundle_dir
    artifact = read_manifest(out / ARTIFACT_REL)
    artifact["clock_trust_digest"] = "0" * 64
    (out / ARTIFACT_REL).write_text(deterministic_json_dumps(artifact), encoding="utf-8")
    with pytest.raises(TradingSessionSingleWriterError):
        reverify_trading_session_single_writer_v1(output_dir=out)


def test_missing_clock_trust_bundle(tmp_path) -> None:
    with pytest.raises(TradingSessionSingleWriterError):
        verify_clock_trust_and_expiry_bundle(tmp_path / "missing")


def test_verify_inputs(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_session_single_writer_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    verified = verify_trading_session_single_writer_inputs(
        TradingSessionSingleWriterInputs(
            clock_trust_and_expiry_bundle_dir=fixture.clock_trust_and_expiry_bundle_dir,
            trading_session_request=default_trading_session_single_writer_request(
                clock_trust=verify_clock_trust_and_expiry_bundle(
                    fixture.clock_trust_and_expiry_bundle_dir
                )
            ),
        )
    )
    assert verified.contract_name == "clock_trust_and_expiry_v1"
