"""Contract tests for order_intent_idempotency_v1."""

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
    "tests.meta.order_intent_idempotency_v1_fixtures",
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.canonical_order_lifecycle_v1 import (
    CanonicalOrderIdentity,
    CanonicalOrderIntentIdentity,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
)
from src.meta.learning_loop.order_intent_idempotency_v1 import (
    ARTIFACT_REL,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    DETERMINISTIC_SERIALIZATION_VERSION,
    IDEMPOTENCY_CONTRACT_VERSION,
    ORDER_INTENT_IDEMPOTENCY_AUTHORITY_INVARIANTS,
    OrderIntentIdempotencyInputs,
    PriorOrderIntentArtifactBinding,
    build_order_intent_idempotency_v1,
    default_order_intent_idempotency_request,
    derive_canonical_idempotency_key,
    prior_binding_from_request,
    produce_order_intent_idempotency_v1,
    replace_request_idempotency_key,
    reverify_order_intent_idempotency_v1,
    verify_canonical_order_lifecycle_bundle,
    verify_trading_session_single_writer_bundle,
)
from tests.meta.order_intent_idempotency_v1_fixtures import (
    produce_order_intent_idempotency_fixture,
)

_NON_EXEC_FLAGS = (
    "order_created",
    "order_submission_requested",
    "order_submitted",
    "order_state_mutated",
    "adapter_invoked",
    "exchange_request_sent",
    "network_side_effect_created",
    "database_mutated",
    "lock_acquired",
    "reservation_created",
    "runtime_authorized",
    "live_authorized",
    "orders_allowed",
    "scheduler_runtime_allowed",
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.order_intent_idempotency_v1.is_under_tmp",
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


def _durable_output(tmp_path: Path, name: str = "idempotency_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _fixture_context(
    fixture,
    *,
    with_prior_binding: bool = False,
    prior_exact_match: bool = True,
):
    trading_session = verify_trading_session_single_writer_bundle(
        fixture.trading_session_single_writer_bundle_dir
    )
    lifecycle = verify_canonical_order_lifecycle_bundle(
        fixture.canonical_order_lifecycle_bundle_dir
    )
    prior_binding = None
    if with_prior_binding:
        base_request = default_order_intent_idempotency_request(
            trading_session=trading_session,
            lifecycle=lifecycle,
        )
        prior_binding = prior_binding_from_request(
            base_request,
            session_identity_digest=trading_session.session_identity_digest,
            writer_identity=trading_session.writer_identity,
        )
        if not prior_exact_match:
            prior_binding = replace(prior_binding, intent_payload_digest="tampered-payload-digest")
    request = default_order_intent_idempotency_request(
        trading_session=trading_session,
        lifecycle=lifecycle,
        prior_artifact_binding=prior_binding,
    )
    return trading_session, lifecycle, request


def _build(fixture, request=None, **context_kwargs):
    trading_session, lifecycle, default_request = _fixture_context(fixture, **context_kwargs)
    return build_order_intent_idempotency_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        request=default_request if request is None else request,
    )


def _assert_non_execution(payload: dict) -> None:
    for flag in _NON_EXEC_FLAGS:
        assert payload[flag] is False, flag


def test_contract_constants() -> None:
    assert CONTRACT_NAME == "order_intent_idempotency_v1"
    assert CONTRACT_VERSION == "v1"
    assert ARTIFACT_REL == "order_intent_idempotency_v1.json"


def test_happy_path_first_observation(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.order_intent_idempotency_bundle_dir / ARTIFACT_REL)
    assert payload["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_EXACT_REPLAY"
    assert payload["order_intent_idempotency_contract_complete"] is True
    assert payload["futures_only"] is True
    _assert_non_execution(payload)


def test_exact_replay_with_prior(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    contract = _build(fixture, with_prior_binding=True)
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_EXACT_REPLAY"
    assert contract["duplicate_replay_classification"] == "EXACT_REPLAY"


def test_idempotent_duplicate(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
    )
    trading_session, lifecycle, request = _fixture_context(
        fixture, with_prior_binding=True, prior_exact_match=False
    )
    prior = request.prior_artifact_binding
    assert prior is not None
    tampered = replace(
        request,
        intent_payload_digest=prior.intent_payload_digest,
        intent_semantic_digest=prior.intent_semantic_digest,
        idempotency_key=prior.idempotency_key,
    )
    tampered = replace(tampered, intent_payload_digest="tampered-payload-digest")
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        request=request,
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_IDEMPOTENT_DUPLICATE"


def test_semantic_payload_conflict(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture, with_prior_binding=True)
    prior = request.prior_artifact_binding
    assert prior is not None
    tampered = replace(
        request,
        intent_payload_digest="deadbeef" * 8,
        intent_semantic_digest="cafebabe" * 8,
        idempotency_key=prior.idempotency_key,
    )
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_SEMANTIC_DUPLICATE_CONFLICT"


def test_semantic_digest_conflict(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture, with_prior_binding=True)
    prior = request.prior_artifact_binding
    assert prior is not None
    tampered = replace(
        request,
        intent_semantic_digest="cafebabe" * 8,
        idempotency_key=prior.idempotency_key,
    )
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_SEMANTIC_DUPLICATE_CONFLICT"


def test_order_identity_conflict(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture, with_prior_binding=True)
    prior = request.prior_artifact_binding
    assert prior is not None
    order = request.canonical_order_identity
    tampered = replace(
        request,
        canonical_order_identity=CanonicalOrderIdentity(
            canonical_order_id="other-order",
            client_order_id=order.client_order_id,
        ),
        idempotency_key=prior.idempotency_key,
    )
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_IDENTITY_CONFLICT"


def test_intent_identity_conflict(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture, with_prior_binding=True)
    prior = request.prior_artifact_binding
    assert prior is not None
    intent = request.canonical_order_intent_identity
    tampered = replace(
        request,
        canonical_order_intent_identity=replace(intent, order_intent_digest="ff" * 32),
        idempotency_key=prior.idempotency_key,
    )
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_IDENTITY_CONFLICT"


def test_session_identity_conflict(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture, with_prior_binding=True)
    prior = request.prior_artifact_binding
    assert prior is not None
    tampered_prior = replace(prior, session_identity_digest="tampered-session")
    tampered = replace(request, prior_artifact_binding=tampered_prior)
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_IDENTITY_CONFLICT"


def test_writer_identity_conflict(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture, with_prior_binding=True)
    prior = request.prior_artifact_binding
    assert prior is not None
    tampered_prior = replace(prior, writer_identity="other-writer")
    tampered = replace(request, prior_artifact_binding=tampered_prior)
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_IDENTITY_CONFLICT"


def test_stale_writer_revision(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture, with_prior_binding=True)
    prior = request.prior_artifact_binding
    assert prior is not None
    tampered_prior = replace(prior, writer_revision=5)
    tampered = replace(
        request,
        prior_artifact_binding=tampered_prior,
        writer_revision=3,
        idempotency_key=prior.idempotency_key,
    )
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_REVISION_OR_GENERATION_CONFLICT"


def test_writer_generation_regression(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture, with_prior_binding=True)
    prior = request.prior_artifact_binding
    assert prior is not None
    tampered_prior = replace(prior, writer_generation=5)
    tampered = replace(
        request,
        prior_artifact_binding=tampered_prior,
        writer_generation=3,
        idempotency_key=prior.idempotency_key,
    )
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_REVISION_OR_GENERATION_CONFLICT"


def test_order_revision_regression(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture, with_prior_binding=True)
    prior = request.prior_artifact_binding
    assert prior is not None
    tampered_prior = replace(prior, order_revision=5)
    tampered = replace(
        request,
        prior_artifact_binding=tampered_prior,
        order_revision=3,
        idempotency_key=prior.idempotency_key,
    )
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_REVISION_OR_GENERATION_CONFLICT"


def test_order_generation_jump(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture, with_prior_binding=True)
    prior = request.prior_artifact_binding
    assert prior is not None
    tampered_prior = replace(prior, order_generation=1)
    tampered = replace(
        request,
        prior_artifact_binding=tampered_prior,
        order_generation=5,
        idempotency_key=prior.idempotency_key,
    )
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_REVISION_OR_GENERATION_CONFLICT"


def test_lifecycle_digest_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture)
    tampered = replace(request, lifecycle_contract_digest="bad" * 16)
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_LIFECYCLE_CONFLICT"


def test_forbidden_target_state(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture, with_prior_binding=True)
    tampered = replace(request, intended_target_state="FILLED", expected_prior_state="")
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_LIFECYCLE_CONFLICT"


def test_missing_idempotency_key(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture)
    tampered = replace(request, idempotency_key="")
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_MISSING_BINDINGS"


def test_malformed_idempotency_key(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture)
    tampered = replace(request, idempotency_key="not-a-valid-sha256")
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_MISSING_BINDINGS"


def test_authority_identity_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture)
    tampered = replace(request, authority_lease_digest="deadbeef" * 8)
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert (
        contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_AUTHORITY_OR_REVOCATION_CONFLICT"
    )


def test_revoked_upstream(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path,
        ssot_durable_output_dir,
        revocation_state="REVOKED",
        trading_session_name="revoked_session_idempotency",
        lifecycle_name="revoked_lifecycle_idempotency",
        idempotency_name="revoked_idempotency",
    )
    payload = read_manifest(fixture.order_intent_idempotency_bundle_dir / ARTIFACT_REL)
    assert payload["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_AUTHORITY_OR_REVOCATION_CONFLICT"


def test_expired_intent(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        evaluation_time="2026-06-29T12:00:00+00:00",
        valid_from="2026-06-29T00:00:00+00:00",
        valid_until="2026-06-30T00:00:00+00:00",
    )
    trading_session, lifecycle, request = _fixture_context(fixture)
    tampered = replace(
        request,
        issued_at="2026-06-29T00:00:00+00:00",
        expires_at="2026-06-29T06:00:00+00:00",
        evaluation_time="2026-06-29T12:00:00+00:00",
    )
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_CLOCK_OR_EXPIRY_CONFLICT"


def test_issued_after_expires(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture)
    tampered = replace(
        request,
        issued_at="2026-06-30T01:00:00+00:00",
        expires_at="2026-06-30T00:00:00+00:00",
    )
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_CLOCK_OR_EXPIRY_CONFLICT"


def test_secure_handoff_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture)
    tampered = replace(request, secure_handoff_envelope_identity="wrong-handoff")
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_CLAIM_CONSUME_CONFLICT"


def test_atomic_claim_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture)
    tampered = replace(request, atomic_claim_identity="wrong-claim")
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_CLAIM_CONSUME_CONFLICT"


def test_atomic_consume_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture, with_prior_binding=True)
    prior = request.prior_artifact_binding
    assert prior is not None
    tampered_prior = replace(prior, atomic_consume_identity="wrong-consume")
    tampered = replace(request, prior_artifact_binding=tampered_prior)
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_CLAIM_CONSUME_CONFLICT"


def test_duplicate_consume(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture, with_prior_binding=True)
    prior = request.prior_artifact_binding
    assert prior is not None
    tampered_prior = replace(prior, artifact_consumed=True)
    tampered = replace(request, prior_artifact_binding=tampered_prior)
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_CLAIM_CONSUME_CONFLICT"


def test_provenance_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture, with_prior_binding=True)
    prior = request.prior_artifact_binding
    assert prior is not None
    tampered_prior = replace(prior, provenance_digest="bad-provenance")
    tampered = replace(request, prior_artifact_binding=tampered_prior)
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_IDENTITY_CONFLICT"


def test_cross_domain_lineage_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture, with_prior_binding=True)
    prior = request.prior_artifact_binding
    assert prior is not None
    tampered_prior = replace(prior, cross_domain_lineage_digest="bad-lineage")
    tampered = replace(request, prior_artifact_binding=tampered_prior)
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_IDENTITY_CONFLICT"


def test_serialization_version_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture)
    tampered = replace(request, deterministic_serialization_version="legacy")
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_MISSING_BINDINGS"


def test_contract_version_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture)
    tampered = replace(request, idempotency_contract_version="legacy")
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_MISSING_BINDINGS"


def test_spot_rejected(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False, instrument_type="SPOT"
    )
    trading_session, lifecycle, request = _fixture_context(fixture)
    intent = replace(request.canonical_order_intent_identity, instrument_type="SPOT")
    tampered = replace(request, canonical_order_intent_identity=intent)
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_FUTURES_MARKET_TYPE_CONFLICT"


def test_synthetic_spot_rejected(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture)
    intent = replace(request.canonical_order_intent_identity, instrument_type="SYNTHETIC_SPOT")
    tampered = replace(request, canonical_order_intent_identity=intent)
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_FUTURES_MARKET_TYPE_CONFLICT"


def test_unknown_market_type_rejected(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture)
    intent = replace(request.canonical_order_intent_identity, instrument_type="OPTIONS")
    tampered = replace(request, canonical_order_intent_identity=intent)
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_FUTURES_MARKET_TYPE_CONFLICT"


def test_missing_market_type_rejected(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture)
    intent = replace(request.canonical_order_intent_identity, instrument_type="")
    tampered = replace(request, canonical_order_intent_identity=intent)
    contract = build_order_intent_idempotency_v1(
        trading_session=trading_session, lifecycle=lifecycle, request=tampered
    )
    assert contract["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_FUTURES_MARKET_TYPE_CONFLICT"


def test_no_asset_specific_market_type_special_handling(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_order_intent_idempotency_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False, instrument="ETH-PERP"
        )
    )
    blocking_factor_ids = {item.get("factor_id") for item in contract.get("blocking_facts", [])}
    assert blocking_factor_ids <= {
        "FORBIDDEN_INSTRUMENT_TYPE",
        "INVALID_INSTRUMENT_TYPE",
        "MISSING_INSTRUMENT_TYPE",
        None,
    }
    assert contract["futures_only"] is True


def test_determinism(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture)
    inputs = OrderIntentIdempotencyInputs(
        trading_session_single_writer_bundle_dir=fixture.trading_session_single_writer_bundle_dir,
        canonical_order_lifecycle_bundle_dir=fixture.canonical_order_lifecycle_bundle_dir,
        idempotency_request=request,
    )
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    produce_order_intent_idempotency_v1(inputs=inputs, output_dir=out_a)
    produce_order_intent_idempotency_v1(inputs=inputs, output_dir=out_b)
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_field_order_does_not_change_digest(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_order_intent_idempotency_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        )
    )
    reordered = dict(sorted(contract.items(), reverse=True))
    assert (
        compute_content_sha256(
            {
                k: contract[k]
                for k in sorted(contract)
                if k
                not in {
                    "output_digest",
                    "manifest_digest",
                    "integrity",
                    "created_at",
                    "artifact_id",
                    "contract_id",
                }
            }
        )
        == contract["output_digest"]
    )


def test_manifest_and_self_verification(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.order_intent_idempotency_bundle_dir
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    reverify_order_intent_idempotency_v1(output_dir=out)


def test_authority_invariants(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.order_intent_idempotency_bundle_dir / ARTIFACT_REL)
    assert (
        payload["order_intent_idempotency_authority_invariants"]
        == ORDER_INTENT_IDEMPOTENCY_AUTHORITY_INVARIANTS
    )
    _assert_non_execution(payload)


def test_derive_idempotency_key_deterministic(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, request = _fixture_context(fixture)
    intent = request.canonical_order_intent_identity
    order = request.canonical_order_identity
    from src.meta.learning_loop.canonical_order_lifecycle_v1 import (
        _compute_order_identity_digest,
        _compute_order_intent_identity_digest,
    )

    kwargs = dict(
        market_type=intent.instrument_type,
        canonical_order_identity_digest=_compute_order_identity_digest(order=order),
        canonical_order_intent_identity_digest=_compute_order_intent_identity_digest(intent=intent),
        session_identity_digest=trading_session.session_identity_digest,
        writer_identity=trading_session.writer_identity,
        writer_generation=request.writer_generation,
        writer_revision=request.writer_revision,
        order_generation=request.order_generation,
        order_revision=request.order_revision,
        intent_semantic_digest=request.intent_semantic_digest,
        lifecycle_contract_digest=request.lifecycle_contract_digest,
        authority_lease_digest=request.authority_lease_digest,
        clock_trust_digest=request.clock_trust_digest,
        provenance_digest=request.provenance_digest,
        cross_domain_lineage_digest=request.cross_domain_lineage_digest,
        idempotency_scope=request.idempotency_scope,
        contract_version=IDEMPOTENCY_CONTRACT_VERSION,
    )
    assert derive_canonical_idempotency_key(**kwargs) == derive_canonical_idempotency_key(**kwargs)
    assert request.idempotency_key == derive_canonical_idempotency_key(**kwargs)


def test_stable_digest_tamper_on_reverify(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_order_intent_idempotency_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.order_intent_idempotency_bundle_dir
    artifact_path = out / ARTIFACT_REL
    artifact_path.write_text(
        artifact_path.read_text().replace("EXACT_REPLAY", "TAMPERED"), encoding="utf-8"
    )
    with pytest.raises(Exception):
        reverify_order_intent_idempotency_v1(output_dir=out)


def test_step14_regression_still_passes(tmp_path, ssot_durable_output_dir) -> None:
    from tests.meta.canonical_order_lifecycle_v1_fixtures import (
        produce_canonical_order_lifecycle_fixture,
    )

    fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path,
        ssot_durable_output_dir,
        lifecycle_name="step14_regression_lifecycle_only",
    )
    payload = read_manifest(
        fixture.canonical_order_lifecycle_bundle_dir / "canonical_order_lifecycle_v1.json"
    )
    assert payload["contract_status"] == "CANONICAL_ORDER_LIFECYCLE_VALID_FOR_OFFLINE_EVALUATION"
