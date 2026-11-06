"""Contract tests for trading_core_decision_attestation_v1."""

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
    "tests.meta.trading_core_decision_attestation_v1_fixtures",
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.trading_core_decision_attestation_v1 import (
    ARTIFACT_REL,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    TRADING_CORE_DECISION_ATTESTATION_AUTHORITY_INVARIANTS,
    ModuleDecisionAttestation,
    TradingCoreDecisionAttestationInputs,
    build_trading_core_decision_attestation_v1,
    compute_module_attestation_manifest_digest,
    default_trading_core_decision_attestation_request,
    produce_trading_core_decision_attestation_v1,
    reverify_trading_core_decision_attestation_v1,
    verify_canonical_order_lifecycle_bundle,
    verify_order_intent_idempotency_bundle,
    verify_trading_session_single_writer_bundle,
)
from tests.meta.trading_core_decision_attestation_v1_fixtures import (
    produce_trading_core_decision_attestation_fixture,
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
        "src.meta.learning_loop.trading_core_decision_attestation_v1.is_under_tmp",
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


def _durable_output(tmp_path: Path, name: str = "attestation_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _fixture_context(fixture):
    trading_session = verify_trading_session_single_writer_bundle(
        fixture.trading_session_single_writer_bundle_dir
    )
    lifecycle = verify_canonical_order_lifecycle_bundle(
        fixture.canonical_order_lifecycle_bundle_dir
    )
    idempotency = verify_order_intent_idempotency_bundle(
        fixture.order_intent_idempotency_bundle_dir
    )
    request = default_trading_core_decision_attestation_request(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
    )
    return trading_session, lifecycle, idempotency, request


def _build(fixture, request=None):
    trading_session, lifecycle, idempotency, default_request = _fixture_context(fixture)
    return build_trading_core_decision_attestation_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        request=default_request if request is None else request,
    )


def _assert_non_execution(payload: dict) -> None:
    for flag in _NON_EXEC_FLAGS:
        assert payload[flag] is False, flag


def test_contract_constants() -> None:
    assert CONTRACT_NAME == "trading_core_decision_attestation_v1"
    assert CONTRACT_VERSION == "v1"
    assert ARTIFACT_REL == "trading_core_decision_attestation_v1.json"


def test_happy_path(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.trading_core_decision_attestation_bundle_dir / ARTIFACT_REL)
    assert payload["contract_status"] == "TRADING_CORE_DECISION_ATTESTATION_VALID"
    assert payload["trading_core_decision_attestation_contract_complete"] is True
    assert payload["futures_only"] is True
    assert len(payload["module_attestations"]) == 8
    _assert_non_execution(payload)


def test_missing_attestation_ref(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, idempotency, request = _fixture_context(fixture)
    bindings = replace(request.attestation_bindings, master_v2_attestation_ref="")
    tampered = replace(request, attestation_bindings=bindings)
    contract = build_trading_core_decision_attestation_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_CORE_DECISION_ATTESTATION_MISSING_BINDINGS"


def test_digest_chain_broken(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, idempotency, request = _fixture_context(fixture)
    tampered_attestations = []
    for attestation in request.module_attestations:
        if attestation.module_slot == "risk":
            tampered_attestations.append(replace(attestation, input_digest="broken-chain-digest"))
        else:
            tampered_attestations.append(attestation)
    tampered = replace(request, module_attestations=tuple(tampered_attestations))
    contract = build_trading_core_decision_attestation_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_CORE_DECISION_ATTESTATION_DIGEST_CHAIN_BROKEN"


def test_session_epoch_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, idempotency, request = _fixture_context(fixture)
    tampered_attestations = [
        replace(att, trading_epoch="wrong-epoch") for att in request.module_attestations
    ]
    tampered = replace(request, module_attestations=tuple(tampered_attestations))
    contract = build_trading_core_decision_attestation_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_CORE_DECISION_ATTESTATION_SESSION_EPOCH_MISMATCH"


def test_outdated_version(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, idempotency, request = _fixture_context(fixture)
    tampered_attestations = [
        replace(att, module_contract_digest="legacy-contract-digest")
        for att in request.module_attestations
    ]
    tampered = replace(request, module_attestations=tuple(tampered_attestations))
    contract = build_trading_core_decision_attestation_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_CORE_DECISION_ATTESTATION_OUTDATED_VERSION"


def test_module_not_executed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, idempotency, request = _fixture_context(fixture)
    tampered_attestations = []
    for attestation in request.module_attestations:
        if attestation.module_slot == "sizing":
            tampered_attestations.append(
                replace(attestation, module_executed=False, output_digest="")
            )
        else:
            tampered_attestations.append(attestation)
    tampered = replace(request, module_attestations=tuple(tampered_attestations))
    contract = build_trading_core_decision_attestation_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_CORE_DECISION_ATTESTATION_MODULE_NOT_EXECUTED"


def test_parallel_ssot_detected(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, idempotency, request = _fixture_context(fixture)
    tampered = replace(request, parallel_trading_logic_ssot_detected=True)
    contract = build_trading_core_decision_attestation_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_CORE_DECISION_ATTESTATION_PARALLEL_SSOT_DETECTED"


def test_attestation_ref_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, idempotency, request = _fixture_context(fixture)
    bindings = replace(request.attestation_bindings, bull_attestation_ref="wrong-attestation-id")
    tampered = replace(request, attestation_bindings=bindings)
    contract = build_trading_core_decision_attestation_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_CORE_DECISION_ATTESTATION_MISSING_BINDINGS"


def test_spot_rejected(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False, instrument_type="SPOT"
    )
    trading_session, lifecycle, idempotency, request = _fixture_context(fixture)
    intent = replace(request.canonical_order_intent_identity, instrument_type="SPOT")
    tampered = replace(request, canonical_order_intent_identity=intent)
    contract = build_trading_core_decision_attestation_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        request=tampered,
    )
    assert (
        contract["contract_status"]
        == "TRADING_CORE_DECISION_ATTESTATION_FUTURES_MARKET_TYPE_CONFLICT"
    )


def test_synthetic_spot_rejected(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, idempotency, request = _fixture_context(fixture)
    intent = replace(request.canonical_order_intent_identity, instrument_type="SYNTHETIC_SPOT")
    tampered = replace(request, canonical_order_intent_identity=intent)
    contract = build_trading_core_decision_attestation_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        request=tampered,
    )
    assert (
        contract["contract_status"]
        == "TRADING_CORE_DECISION_ATTESTATION_FUTURES_MARKET_TYPE_CONFLICT"
    )


def test_unknown_market_type_rejected(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, idempotency, request = _fixture_context(fixture)
    intent = replace(request.canonical_order_intent_identity, instrument_type="OPTIONS")
    tampered = replace(request, canonical_order_intent_identity=intent)
    contract = build_trading_core_decision_attestation_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        request=tampered,
    )
    assert (
        contract["contract_status"]
        == "TRADING_CORE_DECISION_ATTESTATION_FUTURES_MARKET_TYPE_CONFLICT"
    )


def test_missing_market_type_rejected(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, idempotency, request = _fixture_context(fixture)
    intent = replace(request.canonical_order_intent_identity, instrument_type="")
    tampered = replace(request, canonical_order_intent_identity=intent)
    contract = build_trading_core_decision_attestation_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        request=tampered,
    )
    assert (
        contract["contract_status"]
        == "TRADING_CORE_DECISION_ATTESTATION_FUTURES_MARKET_TYPE_CONFLICT"
    )


def test_no_asset_specific_market_type_special_handling(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_trading_core_decision_attestation_fixture(
            tmp_path,
            ssot_durable_output_dir,
            produce_output=False,
            instrument="GENERIC-FUTURES-PERP-001",
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


def test_contract_version_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, idempotency, request = _fixture_context(fixture)
    tampered = replace(request, attestation_contract_version="legacy")
    contract = build_trading_core_decision_attestation_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_CORE_DECISION_ATTESTATION_MISSING_BINDINGS"


def test_serialization_version_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, idempotency, request = _fixture_context(fixture)
    tampered = replace(request, deterministic_serialization_version="legacy")
    contract = build_trading_core_decision_attestation_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_CORE_DECISION_ATTESTATION_MISSING_BINDINGS"


def test_missing_module_attestation(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, idempotency, request = _fixture_context(fixture)
    reduced = tuple(att for att in request.module_attestations if att.module_slot != "risk")
    tampered = replace(request, module_attestations=reduced)
    contract = build_trading_core_decision_attestation_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_CORE_DECISION_ATTESTATION_MISSING_BINDINGS"


def test_missing_order_intent_digest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, idempotency, request = _fixture_context(fixture)
    intent = replace(request.canonical_order_intent_identity, order_intent_digest="")
    tampered = replace(request, canonical_order_intent_identity=intent)
    contract = build_trading_core_decision_attestation_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_CORE_DECISION_ATTESTATION_MISSING_ATTESTATION"


def test_manifest_digest_tamper(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, idempotency, request = _fixture_context(fixture)
    tampered_attestations = []
    for attestation in request.module_attestations:
        if attestation.module_slot == "bear":
            tampered_attestations.append(
                replace(attestation, manifest_digest="tampered-manifest-digest")
            )
        else:
            tampered_attestations.append(attestation)
    tampered = replace(request, module_attestations=tuple(tampered_attestations))
    contract = build_trading_core_decision_attestation_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_CORE_DECISION_ATTESTATION_DIGEST_CHAIN_BROKEN"


def test_parent_attestation_ref_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, idempotency, request = _fixture_context(fixture)
    tampered_attestations = []
    for attestation in request.module_attestations:
        if attestation.module_slot == "dynamic_scope":
            tampered_attestations.append(replace(attestation, parent_attestation_refs=()))
        else:
            tampered_attestations.append(attestation)
    tampered = replace(request, module_attestations=tuple(tampered_attestations))
    contract = build_trading_core_decision_attestation_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_CORE_DECISION_ATTESTATION_DIGEST_CHAIN_BROKEN"


def test_determinism(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    trading_session, lifecycle, idempotency, request = _fixture_context(fixture)
    inputs = TradingCoreDecisionAttestationInputs(
        trading_session_single_writer_bundle_dir=fixture.trading_session_single_writer_bundle_dir,
        canonical_order_lifecycle_bundle_dir=fixture.canonical_order_lifecycle_bundle_dir,
        order_intent_idempotency_bundle_dir=fixture.order_intent_idempotency_bundle_dir,
        attestation_request=request,
    )
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    produce_trading_core_decision_attestation_v1(inputs=inputs, output_dir=out_a)
    produce_trading_core_decision_attestation_v1(inputs=inputs, output_dir=out_b)
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_manifest_and_self_verification(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.trading_core_decision_attestation_bundle_dir
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    reverify_trading_core_decision_attestation_v1(output_dir=out)


def test_authority_invariants(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.trading_core_decision_attestation_bundle_dir / ARTIFACT_REL)
    assert (
        payload["trading_core_decision_attestation_authority_invariants"]
        == TRADING_CORE_DECISION_ATTESTATION_AUTHORITY_INVARIANTS
    )
    _assert_non_execution(payload)


def test_stable_digest_tamper_on_reverify(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_core_decision_attestation_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.trading_core_decision_attestation_bundle_dir
    artifact_path = out / ARTIFACT_REL
    artifact_path.write_text(
        artifact_path.read_text().replace("ATTESTATION_CHAIN_VALID", "TAMPERED"),
        encoding="utf-8",
    )
    with pytest.raises(Exception):
        reverify_trading_core_decision_attestation_v1(output_dir=out)


def test_step15_regression_still_passes(tmp_path, ssot_durable_output_dir) -> None:
    from tests.meta.order_intent_idempotency_v1_fixtures import (
        produce_order_intent_idempotency_fixture,
    )

    fixture = produce_order_intent_idempotency_fixture(
        tmp_path,
        ssot_durable_output_dir,
        idempotency_name="step15_regression_idempotency_only",
    )
    payload = read_manifest(
        fixture.order_intent_idempotency_bundle_dir / "order_intent_idempotency_v1.json"
    )
    assert payload["contract_status"] == "ORDER_INTENT_IDEMPOTENCY_EXACT_REPLAY"


def test_module_attestation_manifest_digest_deterministic() -> None:
    attestation = ModuleDecisionAttestation(
        attestation_id="att-001",
        module_owner_ref="master_v2_owner_v1",
        module_contract_digest="contract-digest",
        implementation_digest="impl-digest",
        input_digest="input-digest",
        output_digest="output-digest",
        decision_code="MASTER_V2_DECISION_OK",
        decision_trace_digest="trace-digest",
        policy_digest="policy-digest",
        parent_attestation_refs=(),
        correlation_id="corr-001",
        session_id="session-001",
        trading_epoch="epoch-001",
        created_at="1970-01-01T00:00:00+00:00",
        manifest_digest="",
        module_slot="master_v2",
    )
    digest_a = compute_module_attestation_manifest_digest(attestation)
    digest_b = compute_module_attestation_manifest_digest(attestation)
    assert digest_a == digest_b


def test_all_required_attestation_ref_fields_present(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_trading_core_decision_attestation_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        )
    )
    bindings = contract["attestation_bindings"]
    for field in (
        "master_v2_attestation_ref",
        "bull_attestation_ref",
        "bear_attestation_ref",
        "double_play_attestation_ref",
        "dynamic_scope_attestation_ref",
        "risk_attestation_ref",
        "sizing_attestation_ref",
        "scope_capital_attestation_ref",
    ):
        assert bindings[field]
