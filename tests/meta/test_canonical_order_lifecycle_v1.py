"""Contract tests for canonical_order_lifecycle_v1."""

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
    "tests.meta.canonical_order_lifecycle_v1_fixtures",
]

from src.meta.learning_loop.canonical_order_lifecycle_v1 import (
    ARTIFACT_REL,
    CANONICAL_ORDER_LIFECYCLE_AUTHORITY_INVARIANTS,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    DETERMINISTIC_RULE_SET_VERSION,
    LIFECYCLE_CONTRACT_VERSION,
    MANIFEST_FILENAME,
    ORDER_IDENTITY_CONTRACT_VERSION,
    ORDER_INTENT_IDENTITY_CONTRACT_VERSION,
    SELF_VERIFICATION_REL,
    CanonicalOrderIdentity,
    CanonicalOrderIntentIdentity,
    CanonicalOrderLifecycleInputs,
    build_canonical_order_lifecycle_v1,
    default_canonical_order_lifecycle_request,
    produce_canonical_order_lifecycle_v1,
    reverify_canonical_order_lifecycle_v1,
    verify_trading_session_single_writer_bundle,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from tests.meta.canonical_order_lifecycle_v1_fixtures import (
    produce_canonical_order_lifecycle_fixture,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.canonical_order_lifecycle_v1.is_under_tmp",
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


def _durable_output(tmp_path: Path, name: str = "lifecycle_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _fixture_inputs(fixture):
    trading_session = verify_trading_session_single_writer_bundle(
        fixture.trading_session_single_writer_bundle_dir
    )
    request = default_canonical_order_lifecycle_request(trading_session=trading_session)
    return trading_session, request


def test_contract_constants() -> None:
    assert CONTRACT_NAME == "canonical_order_lifecycle_v1"
    assert CONTRACT_VERSION == "v1"
    assert ARTIFACT_REL == "canonical_order_lifecycle_v1.json"
    assert LIFECYCLE_CONTRACT_VERSION == "canonical_order_lifecycle_contract_v1"


def test_happy_path_initial_bind(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.canonical_order_lifecycle_bundle_dir / ARTIFACT_REL)
    assert payload["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_VALID_FOR_OFFLINE_EVALUATION"
    assert payload["lifecycle_status"] == "VALID"
    assert payload["target_order_state"] == "INTENT_CREATED"
    assert payload["canonical_order_lifecycle_contract_complete"] is True
    assert payload["canonical_order_identity_bound"] is True
    assert payload["canonical_order_intent_bound"] is True
    assert payload["trading_session_identity_bound"] is True
    assert payload["single_writer_identity_bound"] is True
    assert payload["state_transition_contract_bound"] is True


def test_allowed_transition_validate(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, _ = _fixture_inputs(fixture)
    request = default_canonical_order_lifecycle_request(
        trading_session=trading_session,
        transition_identity="transition-validate-001",
        transition_type="VALIDATE",
        previous_order_state="INTENT_CREATED",
        expected_order_state="INTENT_CREATED",
        target_order_state="INTENT_VALIDATED",
        order_revision=2,
        idempotency_key="idempotency-validate-001",
        replay_identity="replay-validate-001",
    )
    contract = build_canonical_order_lifecycle_v1(trading_session=trading_session, request=request)
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_VALID_FOR_OFFLINE_EVALUATION"
    assert contract["target_order_state"] == "INTENT_VALIDATED"


def test_required_non_authorizing_flags(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.canonical_order_lifecycle_bundle_dir / ARTIFACT_REL)
    assert payload["order_created"] is False
    assert payload["order_submitted"] is False
    assert payload["order_state_mutated"] is False
    assert payload["adapter_invoked"] is False
    assert payload["runtime_authorized"] is False
    assert payload["live_authorized"] is False
    assert payload["orders_allowed"] is False
    assert (
        payload["canonical_order_lifecycle_authority_invariants"]
        == CANONICAL_ORDER_LIFECYCLE_AUTHORITY_INVARIANTS
    )


def test_determinism(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    inputs = CanonicalOrderLifecycleInputs(
        trading_session_single_writer_bundle_dir=fixture.trading_session_single_writer_bundle_dir,
        lifecycle_request=request,
    )
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    produce_canonical_order_lifecycle_v1(inputs=inputs, output_dir=out_a)
    produce_canonical_order_lifecycle_v1(inputs=inputs, output_dir=out_b)
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_self_verification_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.canonical_order_lifecycle_bundle_dir
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    self_payload = read_manifest(out / SELF_VERIFICATION_REL)
    assert self_payload["overall_status"] == "PASS"
    reverify_canonical_order_lifecycle_v1(output_dir=out)


def test_manifest_verify_rc_zero(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(tmp_path, ssot_durable_output_dir)
    rc = 0 if verify_manifest_sha256(fixture.canonical_order_lifecycle_bundle_dir)[0] else 1
    assert rc == 0


def test_idempotent_repeat(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    idempotent_request = replace(request, transition_type="IDEMPOTENT_REPEAT")
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=idempotent_request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_IDEMPOTENT"
    assert contract["lifecycle_status"] == "IDEMPOTENT"


def test_stale_revision(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    stale_request = replace(request, prior_order_revision=5, order_revision=3)
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=stale_request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_STALE_ORDER_REVISION"


def test_stale_generation(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    stale_request = replace(request, prior_order_generation=5, order_generation=3)
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=stale_request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_STALE_ORDER_GENERATION"


def test_forbidden_transition(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    bad_request = replace(
        request,
        previous_order_state="INTENT_CREATED",
        expected_order_state="INTENT_CREATED",
        target_order_state="FILLED",
        transition_type="FILL",
    )
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=bad_request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_FORBIDDEN_TRANSITION"


def test_terminal_state_reopen(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    bad_request = replace(
        request,
        previous_order_state="FILLED",
        expected_order_state="FILLED",
        target_order_state="CANCEL_REQUESTED",
        transition_type="CANCEL_REQUEST",
    )
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=bad_request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_TERMINAL_STATE_REOPEN"


def test_expected_state_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    bad_request = replace(
        request,
        previous_order_state="",
        expected_order_state="INTENT_VALIDATED",
        target_order_state="INTENT_CREATED",
    )
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=bad_request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_EXPECTED_STATE_MISMATCH"


def test_duplicate_submission(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    dup_request = replace(
        request,
        transition_type="SUBMISSION_START",
        prior_idempotency_key=request.idempotency_key,
        prior_transition_identity="transition-prior-001",
    )
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=dup_request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_DUPLICATE_SUBMISSION"


def test_duplicate_cancel(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    dup_request = replace(
        request,
        transition_type="CANCEL_REQUEST",
        prior_idempotency_key=request.idempotency_key,
        prior_transition_identity="transition-prior-cancel",
    )
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=dup_request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_DUPLICATE_CANCEL"


def test_duplicate_fill(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    dup_request = replace(
        request,
        transition_type="FILL",
        prior_idempotency_key=request.idempotency_key,
        prior_transition_identity="transition-prior-fill",
    )
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=dup_request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_DUPLICATE_FILL"


def test_replay_detection(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    intent = request.canonical_order_intent_identity
    order = request.canonical_order_identity
    order_intent_digest = compute_content_sha256(
        {
            "identity_domain": ORDER_INTENT_IDENTITY_CONTRACT_VERSION,
            "client_order_id": intent.client_order_id,
            "order_intent_digest": intent.order_intent_digest,
            "instrument_type": intent.instrument_type,
            "venue": intent.venue,
            "account": intent.account,
            "instrument": intent.instrument,
            "trading_epoch": intent.trading_epoch,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )
    order_identity_digest = compute_content_sha256(
        {
            "identity_domain": ORDER_IDENTITY_CONTRACT_VERSION,
            "canonical_order_id": order.canonical_order_id,
            "client_order_id": order.client_order_id,
            "venue_order_id": order.venue_order_id,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )
    evidence_digest = compute_content_sha256(
        {
            "order_intent_identity_digest": order_intent_digest,
            "canonical_order_identity_digest": order_identity_digest,
            "session_identity_digest": trading_session.session_identity_digest,
            "writer_identity_digest": trading_session.writer_identity_digest,
            "transition_identity": request.transition_identity,
            "expected_order_state": request.expected_order_state,
            "target_order_state": request.target_order_state,
            "order_revision": request.order_revision,
            "idempotency_key": request.idempotency_key,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )
    replay_request = replace(request, prior_lifecycle_evidence_digest=evidence_digest)
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=replay_request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_REPLAY_REJECTED"


def test_revoked_via_upstream(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path,
        ssot_durable_output_dir,
        revocation_state="REVOKED",
        trading_session_name="revoked_trading_session",
        lifecycle_name="revoked_lifecycle",
    )
    payload = read_manifest(fixture.canonical_order_lifecycle_bundle_dir / ARTIFACT_REL)
    assert payload["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_REVOKED"


def test_expired_upstream(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        evaluation_time="2026-07-01T00:00:00+00:00",
    )
    trading_session, request = _fixture_inputs(fixture)
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_EXPIRED"


def test_missing_order_identity(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    bad_request = replace(
        request,
        canonical_order_identity=CanonicalOrderIdentity(
            canonical_order_id="",
            client_order_id=request.canonical_order_identity.client_order_id,
        ),
    )
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=bad_request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_MISSING_ORDER_IDENTITY"


def test_missing_intent_identity(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    intent = request.canonical_order_intent_identity
    bad_request = replace(
        request,
        canonical_order_intent_identity=CanonicalOrderIntentIdentity(
            client_order_id=intent.client_order_id,
            order_intent_digest="",
            instrument_type=intent.instrument_type,
            venue=intent.venue,
            account=intent.account,
            instrument=intent.instrument,
            trading_epoch=intent.trading_epoch,
        ),
    )
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=bad_request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_MISSING_ORDER_INTENT_IDENTITY"


def test_spot_intent_rejected(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    bad_request = replace(
        request,
        canonical_order_intent_identity=replace(
            request.canonical_order_intent_identity,
            instrument_type="SPOT",
        ),
    )
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=bad_request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_FORBIDDEN_INSTRUMENT"


def test_synthetic_spot_intent_rejected(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    bad_request = replace(
        request,
        canonical_order_intent_identity=replace(
            request.canonical_order_intent_identity,
            instrument_type="SYNTHETIC_SPOT",
        ),
    )
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=bad_request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_FORBIDDEN_INSTRUMENT"


def test_unknown_market_type_rejected(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    bad_request = replace(
        request,
        canonical_order_intent_identity=replace(
            request.canonical_order_intent_identity,
            instrument_type="OPTIONS",
        ),
    )
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=bad_request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_FORBIDDEN_INSTRUMENT"


def test_missing_market_type_rejected(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    bad_request = replace(
        request,
        canonical_order_intent_identity=replace(
            request.canonical_order_intent_identity,
            instrument_type="",
        ),
    )
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=bad_request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_FORBIDDEN_INSTRUMENT"


def test_valid_futures_market_type_success(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        instrument="ETH-PERP",
        instrument_type="FUTURES",
    )
    trading_session, request = _fixture_inputs(fixture)
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_VALID_FOR_OFFLINE_EVALUATION"
    assert contract["canonical_order_intent_identity"]["instrument_type"] == "FUTURES"
    assert contract["futures_only"] is True


def test_no_asset_specific_market_type_special_handling(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=request,
    )
    blocking_factor_ids = {item.get("factor_id") for item in contract.get("blocking_facts", [])}
    market_type_factors = {
        factor_id
        for factor_id in blocking_factor_ids
        if factor_id and ("INSTRUMENT" in factor_id or "MARKET" in factor_id)
    }
    assert market_type_factors <= {
        "FORBIDDEN_INSTRUMENT_TYPE",
        "INVALID_INSTRUMENT_TYPE",
        "MISSING_INSTRUMENT_TYPE",
    }
    assert contract["futures_only"] is True
    assert contract["canonical_order_intent_identity"]["instrument_type"] == "FUTURES"


def test_lineage_tamper(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False, use_candidate_lineage=True
    )
    trading_session, request = _fixture_inputs(fixture)
    tampered_lineage = dict(request.order_lifecycle_lineage)
    field = next(iter(tampered_lineage))
    tampered_lineage[field] = f"tampered-{tampered_lineage[field]}"
    tamper_request = replace(request, order_lifecycle_lineage=tampered_lineage)
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=tamper_request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_BROKEN_LINEAGE"


def test_manifest_tamper(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.canonical_order_lifecycle_bundle_dir
    artifact_path = out / ARTIFACT_REL
    artifact_path.write_text(
        artifact_path.read_text().replace("INTENT_CREATED", "TAMPERED"),
        encoding="utf-8",
    )
    ok, _ = verify_manifest_sha256(out)
    assert ok is False


def test_digest_tamper_on_reverify(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.canonical_order_lifecycle_bundle_dir
    artifact_path = out / ARTIFACT_REL
    artifact_path.write_text(
        artifact_path.read_text().replace("INTENT_CREATED", "TAMPERED"), encoding="utf-8"
    )
    with pytest.raises(Exception):
        reverify_canonical_order_lifecycle_v1(output_dir=out)


def test_boundary_exact_revision(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    boundary_request = replace(
        request,
        transition_identity="transition-validate-boundary",
        transition_type="VALIDATE",
        previous_order_state="INTENT_CREATED",
        expected_order_state="INTENT_CREATED",
        target_order_state="INTENT_VALIDATED",
        prior_order_revision=1,
        order_revision=2,
        idempotency_key="idempotency-boundary-revision",
        replay_identity="replay-boundary-revision",
    )
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=boundary_request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_VALID_FOR_OFFLINE_EVALUATION"


def test_boundary_transition_to_terminal(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, request = _fixture_inputs(fixture)
    terminal_request = replace(
        request,
        previous_order_state="ACKNOWLEDGED",
        expected_order_state="ACKNOWLEDGED",
        target_order_state="FILLED",
        transition_type="FILL",
        order_revision=2,
    )
    contract = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=terminal_request,
    )
    assert contract["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_VALID_FOR_OFFLINE_EVALUATION"
    assert contract["terminal_state"] is True
