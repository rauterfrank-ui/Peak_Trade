"""Contract tests for trading_logic_semantic_diff_evidence_v1."""

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
    "tests.meta.trading_logic_semantic_diff_evidence_v1_fixtures",
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from src.meta.learning_loop.trading_logic_semantic_diff_evidence_v1 import (
    ARTIFACT_REL,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    SEMANTIC_DIFF_CONTRACT_VERSION,
    TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_AUTHORITY_INVARIANTS,
    SemanticDiffLayer,
    TradingLogicSemanticDiffEvidenceInputs,
    build_trading_logic_semantic_diff_evidence_v1,
    default_semantic_diff_evidence_request,
    produce_trading_logic_semantic_diff_evidence_v1,
    reverify_trading_logic_semantic_diff_evidence_v1,
    verify_trading_core_decision_attestation_bundle,
)
from tests.meta.trading_logic_semantic_diff_evidence_v1_fixtures import (
    produce_trading_logic_semantic_diff_evidence_fixture,
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

_CHANGED_ORDER_INTENT_DIGEST = "bbccddeeff00112233445566778899aabbccddeeff00112233445566778899aa"


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.trading_logic_semantic_diff_evidence_v1.is_under_tmp",
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


def _durable_output(tmp_path: Path, name: str = "semantic_diff_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _fixture_context(fixture):
    baseline = verify_trading_core_decision_attestation_bundle(
        fixture.baseline_trading_core_decision_attestation_bundle_dir
    )
    candidate = verify_trading_core_decision_attestation_bundle(
        fixture.candidate_trading_core_decision_attestation_bundle_dir
    )
    request = default_semantic_diff_evidence_request(
        baseline=baseline,
        candidate=candidate,
        declared_change_class="A",
    )
    return baseline, candidate, request


def _build(fixture, request=None):
    baseline, candidate, default_request = _fixture_context(fixture)
    return build_trading_logic_semantic_diff_evidence_v1(
        baseline=baseline,
        candidate=candidate,
        request=default_request if request is None else request,
    )


def _assert_non_execution(payload: dict) -> None:
    for flag in _NON_EXEC_FLAGS:
        assert payload[flag] is False, flag


def test_contract_constants() -> None:
    assert CONTRACT_NAME == "trading_logic_semantic_diff_evidence_v1"
    assert CONTRACT_VERSION == "v1"
    assert ARTIFACT_REL == "trading_logic_semantic_diff_evidence_v1.json"
    assert SEMANTIC_DIFF_CONTRACT_VERSION == "trading_logic_semantic_diff_contract_v1"


def test_happy_path(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path, ssot_durable_output_dir
    )
    payload = read_manifest(fixture.trading_logic_semantic_diff_evidence_bundle_dir / ARTIFACT_REL)
    assert payload["contract_status"] == "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_VALID"
    assert payload["trading_logic_semantic_diff_evidence_contract_complete"] is True
    assert payload["futures_only"] is True
    assert payload["declared_change_class"] == "A"
    assert payload["effective_change_class"] == "A"
    assert len(payload["diff_layers"]) == 8
    _assert_non_execution(payload)


def test_underdeclared_change_class(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        candidate_order_intent_digest=_CHANGED_ORDER_INTENT_DIGEST,
    )
    baseline, candidate, request = _fixture_context(fixture)
    tampered = replace(request, declared_change_class="A")
    contract = build_trading_logic_semantic_diff_evidence_v1(
        baseline=baseline,
        candidate=candidate,
        request=tampered,
    )
    assert (
        contract["contract_status"]
        == "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_UNDERDECLARED_CHANGE_CLASS"
    )


def test_declared_change_class_c_when_minimum_c(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        candidate_order_intent_digest=_CHANGED_ORDER_INTENT_DIGEST,
    )
    baseline, candidate, _ = _fixture_context(fixture)
    request = default_semantic_diff_evidence_request(
        baseline=baseline,
        candidate=candidate,
        declared_change_class="C",
    )
    contract = build_trading_logic_semantic_diff_evidence_v1(
        baseline=baseline,
        candidate=candidate,
        request=request,
    )
    assert contract["contract_status"] == "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_VALID"
    assert contract["minimum_change_class"] == "C"


def test_missing_diff_layer(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    baseline, candidate, request = _fixture_context(fixture)
    reduced = tuple(
        layer for layer in request.diff_layers if layer.layer_name != "risk_output_diff"
    )
    tampered = replace(request, diff_layers=reduced)
    contract = build_trading_logic_semantic_diff_evidence_v1(
        baseline=baseline,
        candidate=candidate,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_MISSING_BINDINGS"


def test_layer_change_flag_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    baseline, candidate, request = _fixture_context(fixture)
    tampered_layers = []
    for layer in request.diff_layers:
        if layer.layer_name == "order_intent_diff":
            tampered_layers.append(replace(layer, change_detected=not layer.change_detected))
        else:
            tampered_layers.append(layer)
    tampered = replace(request, diff_layers=tuple(tampered_layers))
    contract = build_trading_logic_semantic_diff_evidence_v1(
        baseline=baseline,
        candidate=candidate,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_LAYER_MISMATCH"


def test_spot_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        instrument_type="SPOT",
    )
    baseline, candidate, request = _fixture_context(fixture)
    contract = build_trading_logic_semantic_diff_evidence_v1(
        baseline=baseline,
        candidate=candidate,
        request=request,
    )
    assert (
        contract["contract_status"]
        == "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_FUTURES_MARKET_TYPE_CONFLICT"
    )


def test_synthetic_spot_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        instrument_type="SYNTHETIC_SPOT",
    )
    baseline, candidate, request = _fixture_context(fixture)
    contract = build_trading_logic_semantic_diff_evidence_v1(
        baseline=baseline,
        candidate=candidate,
        request=request,
    )
    assert (
        contract["contract_status"]
        == "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_FUTURES_MARKET_TYPE_CONFLICT"
    )


def test_unknown_market_type_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        instrument_type="UNKNOWN_MARKET",
    )
    baseline, candidate, request = _fixture_context(fixture)
    contract = build_trading_logic_semantic_diff_evidence_v1(
        baseline=baseline,
        candidate=candidate,
        request=request,
    )
    assert (
        contract["contract_status"]
        == "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_FUTURES_MARKET_TYPE_CONFLICT"
    )


def test_missing_market_type_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        instrument_type="",
    )
    baseline, candidate, request = _fixture_context(fixture)
    contract = build_trading_logic_semantic_diff_evidence_v1(
        baseline=baseline,
        candidate=candidate,
        request=request,
    )
    assert (
        contract["contract_status"]
        == "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_FUTURES_MARKET_TYPE_CONFLICT"
    )


def test_contract_version_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    baseline, candidate, request = _fixture_context(fixture)
    tampered = replace(request, semantic_diff_contract_version="legacy")
    contract = build_trading_logic_semantic_diff_evidence_v1(
        baseline=baseline,
        candidate=candidate,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_MISSING_BINDINGS"


def test_serialization_version_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    baseline, candidate, request = _fixture_context(fixture)
    tampered = replace(request, deterministic_serialization_version="legacy")
    contract = build_trading_logic_semantic_diff_evidence_v1(
        baseline=baseline,
        candidate=candidate,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_MISSING_BINDINGS"


def test_missing_declared_semantic_diff_summary_digest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    baseline, candidate, request = _fixture_context(fixture)
    tampered = replace(request, declared_semantic_diff_summary_digest="")
    contract = build_trading_logic_semantic_diff_evidence_v1(
        baseline=baseline,
        candidate=candidate,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_MISSING_BINDINGS"


def test_unknown_declared_change_class(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    baseline, candidate, request = _fixture_context(fixture)
    tampered = replace(request, declared_change_class="Z")
    contract = build_trading_logic_semantic_diff_evidence_v1(
        baseline=baseline,
        candidate=candidate,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_MISSING_BINDINGS"


def test_no_asset_specific_market_type_special_handling(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_trading_logic_semantic_diff_evidence_fixture(
            tmp_path,
            ssot_durable_output_dir,
            produce_output=False,
            instrument="GENERIC-FUTURES-PERP-002",
        )
    )
    blocking_factor_ids = {item.get("factor_id") for item in contract.get("blocking_facts", [])}
    assert blocking_factor_ids <= {
        "FORBIDDEN_INSTRUMENT_TYPE",
        "INVALID_INSTRUMENT_TYPE",
        "FUTURES_ONLY_FLAG_FALSE",
        None,
    }
    assert contract["futures_only"] is True


def test_determinism(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    baseline, candidate, request = _fixture_context(fixture)
    inputs = TradingLogicSemanticDiffEvidenceInputs(
        baseline_trading_core_decision_attestation_bundle_dir=fixture.baseline_trading_core_decision_attestation_bundle_dir,
        candidate_trading_core_decision_attestation_bundle_dir=fixture.candidate_trading_core_decision_attestation_bundle_dir,
        semantic_diff_request=request,
    )
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    produce_trading_logic_semantic_diff_evidence_v1(inputs=inputs, output_dir=out_a)
    produce_trading_logic_semantic_diff_evidence_v1(inputs=inputs, output_dir=out_b)
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_field_order_does_not_change_semantics(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_trading_logic_semantic_diff_evidence_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        )
    )
    reordered = {key: contract[key] for key in reversed(list(contract.keys()))}
    assert deterministic_json_dumps(contract) == deterministic_json_dumps(reordered)


def test_manifest_and_self_verification(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path, ssot_durable_output_dir
    )
    out = fixture.trading_logic_semantic_diff_evidence_bundle_dir
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    reverify_trading_logic_semantic_diff_evidence_v1(output_dir=out)


def test_authority_invariants(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path, ssot_durable_output_dir
    )
    payload = read_manifest(fixture.trading_logic_semantic_diff_evidence_bundle_dir / ARTIFACT_REL)
    assert (
        payload["trading_logic_semantic_diff_evidence_authority_invariants"]
        == TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_AUTHORITY_INVARIANTS
    )
    _assert_non_execution(payload)


def test_stable_digest_tamper_on_reverify(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path, ssot_durable_output_dir
    )
    out = fixture.trading_logic_semantic_diff_evidence_bundle_dir
    artifact_path = out / ARTIFACT_REL
    artifact_path.write_text(
        artifact_path.read_text().replace("SEMANTIC_DIFF_VALID", "TAMPERED"),
        encoding="utf-8",
    )
    with pytest.raises(Exception):
        reverify_trading_logic_semantic_diff_evidence_v1(output_dir=out)


def test_step16_regression_still_passes(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    payload = read_manifest(
        fixture.baseline_trading_core_decision_attestation_bundle_dir
        / "trading_core_decision_attestation_v1.json"
    )
    assert payload["contract_status"] == "TRADING_CORE_DECISION_ATTESTATION_VALID"


def test_all_required_diff_layers_present(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_trading_logic_semantic_diff_evidence_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        )
    )
    layer_names = {layer["layer_name"] for layer in contract["diff_layers"]}
    for field in (
        "declared_semantic_diff",
        "structural_contract_diff",
        "configuration_domain_diff",
        "decision_trace_diff",
        "golden_replay_diff",
        "boundary_behavior_diff",
        "risk_output_diff",
        "order_intent_diff",
    ):
        assert field in layer_names


def test_missing_layer_digest_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    baseline, candidate, request = _fixture_context(fixture)
    tampered_layers = []
    for layer in request.diff_layers:
        if layer.layer_name == "golden_replay_diff":
            tampered_layers.append(
                SemanticDiffLayer(
                    layer_name=layer.layer_name,
                    baseline_digest="",
                    candidate_digest=layer.candidate_digest,
                    change_detected=False,
                )
            )
        else:
            tampered_layers.append(layer)
    tampered = replace(request, diff_layers=tuple(tampered_layers))
    contract = build_trading_logic_semantic_diff_evidence_v1(
        baseline=baseline,
        candidate=candidate,
        request=tampered,
    )
    assert contract["contract_status"] == "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_MISSING_BINDINGS"
