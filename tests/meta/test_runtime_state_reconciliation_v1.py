"""Contract tests for runtime_state_reconciliation_v1."""

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
    "tests.meta.runtime_state_reconciliation_v1_fixtures",
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from src.meta.learning_loop.runtime_state_reconciliation_v1 import (
    ARTIFACT_REL,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    RECONCILIATION_CONTRACT_VERSION,
    RUNTIME_STATE_RECONCILIATION_AUTHORITY_INVARIANTS,
    ReconciliationLevelResult,
    ReconciliationSnapshotComponent,
    RuntimeStateReconciliationInputs,
    build_runtime_state_reconciliation_v1,
    default_runtime_reconciliation_request,
    produce_runtime_state_reconciliation_v1,
    reverify_runtime_state_reconciliation_v1,
    verify_trading_logic_semantic_diff_evidence_bundle,
)
from tests.meta.runtime_state_reconciliation_v1_fixtures import (
    produce_runtime_state_reconciliation_fixture,
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
    "opening_order_allowed",
    "increasing_order_allowed",
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.runtime_state_reconciliation_v1.is_under_tmp",
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


def _durable_output(tmp_path: Path, name: str = "reconciliation_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _fixture_context(fixture):
    semantic_diff = verify_trading_logic_semantic_diff_evidence_bundle(
        fixture.trading_logic_semantic_diff_evidence_bundle_dir
    )
    request = default_runtime_reconciliation_request(semantic_diff=semantic_diff)
    return semantic_diff, request


def _build(fixture, request=None):
    semantic_diff, default_request = _fixture_context(fixture)
    return build_runtime_state_reconciliation_v1(
        semantic_diff=semantic_diff,
        request=default_request if request is None else request,
    )


def _assert_non_execution(payload: dict) -> None:
    for flag in _NON_EXEC_FLAGS:
        assert payload[flag] is False, flag


def test_contract_constants() -> None:
    assert CONTRACT_NAME == "runtime_state_reconciliation_v1"
    assert CONTRACT_VERSION == "v1"
    assert ARTIFACT_REL == "runtime_state_reconciliation_v1.json"
    assert RECONCILIATION_CONTRACT_VERSION == "runtime_state_reconciliation_contract_v1"


def test_happy_path(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_runtime_state_reconciliation_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.runtime_state_reconciliation_bundle_dir / ARTIFACT_REL)
    assert payload["contract_status"] == "RUNTIME_STATE_RECONCILIATION_VALID"
    assert payload["runtime_state_reconciliation_contract_complete"] is True
    assert payload["futures_only"] is True
    assert payload["reconciliation_state"] == "CLEAN"
    assert payload["r4_reconciliation_pass"] is True
    assert payload["zero_unreconciled_exposure"] is True
    assert len(payload["snapshot_components"]) == 6
    assert len(payload["reconciliation_levels"]) == 4
    _assert_non_execution(payload)


def test_snapshot_divergence(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_runtime_state_reconciliation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    semantic_diff, request = _fixture_context(fixture)
    tampered_components = []
    for component in request.snapshot_components:
        if component.component_name == "venue_orders":
            tampered_components.append(
                ReconciliationSnapshotComponent(
                    component_name=component.component_name,
                    local_digest=component.local_digest,
                    venue_digest="aa" * 32,
                    divergence_detected=True,
                )
            )
        else:
            tampered_components.append(component)
    tampered = replace(
        request,
        declared_reconciliation_state="UNCLEAN",
        snapshot_components=tuple(tampered_components),
    )
    contract = build_runtime_state_reconciliation_v1(
        semantic_diff=semantic_diff,
        request=tampered,
    )
    assert contract["contract_status"] == "RUNTIME_STATE_RECONCILIATION_SNAPSHOT_DIVERGENCE"


def test_reconciliation_state_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_runtime_state_reconciliation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    semantic_diff, request = _fixture_context(fixture)
    tampered = replace(request, declared_reconciliation_state="UNCLEAN")
    contract = build_runtime_state_reconciliation_v1(
        semantic_diff=semantic_diff,
        request=tampered,
    )
    assert contract["contract_status"] == "RUNTIME_STATE_RECONCILIATION_STATE_MISMATCH"


def test_missing_snapshot_component(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_runtime_state_reconciliation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    semantic_diff, request = _fixture_context(fixture)
    reduced = tuple(
        component
        for component in request.snapshot_components
        if component.component_name != "venue_margin"
    )
    tampered = replace(request, snapshot_components=reduced)
    contract = build_runtime_state_reconciliation_v1(
        semantic_diff=semantic_diff,
        request=tampered,
    )
    assert contract["contract_status"] == "RUNTIME_STATE_RECONCILIATION_MISSING_BINDINGS"


def test_missing_reconciliation_level(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_runtime_state_reconciliation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    semantic_diff, request = _fixture_context(fixture)
    reduced = tuple(
        level
        for level in request.reconciliation_levels
        if level.level_name != "r4_recovery_reconciliation"
    )
    tampered = replace(request, reconciliation_levels=reduced)
    contract = build_runtime_state_reconciliation_v1(
        semantic_diff=semantic_diff,
        request=tampered,
    )
    assert contract["contract_status"] == "RUNTIME_STATE_RECONCILIATION_MISSING_BINDINGS"


def test_divergence_flag_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_runtime_state_reconciliation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    semantic_diff, request = _fixture_context(fixture)
    tampered_components = []
    for component in request.snapshot_components:
        if component.component_name == "venue_fills":
            tampered_components.append(
                replace(component, divergence_detected=not component.divergence_detected)
            )
        else:
            tampered_components.append(component)
    tampered = replace(request, snapshot_components=tuple(tampered_components))
    contract = build_runtime_state_reconciliation_v1(
        semantic_diff=semantic_diff,
        request=tampered,
    )
    assert contract["contract_status"] == "RUNTIME_STATE_RECONCILIATION_LEVEL_MISMATCH"


def test_spot_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_runtime_state_reconciliation_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        instrument_type="SPOT",
    )
    semantic_diff, request = _fixture_context(fixture)
    tampered = replace(request, instrument_type="SPOT")
    contract = build_runtime_state_reconciliation_v1(
        semantic_diff=semantic_diff,
        request=tampered,
    )
    assert (
        contract["contract_status"] == "RUNTIME_STATE_RECONCILIATION_FUTURES_MARKET_TYPE_CONFLICT"
    )


def test_synthetic_spot_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_runtime_state_reconciliation_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        instrument_type="SYNTHETIC_SPOT",
    )
    semantic_diff, request = _fixture_context(fixture)
    tampered = replace(request, instrument_type="SYNTHETIC_SPOT")
    contract = build_runtime_state_reconciliation_v1(
        semantic_diff=semantic_diff,
        request=tampered,
    )
    assert (
        contract["contract_status"] == "RUNTIME_STATE_RECONCILIATION_FUTURES_MARKET_TYPE_CONFLICT"
    )


def test_unknown_market_type_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_runtime_state_reconciliation_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        instrument_type="UNKNOWN_MARKET",
    )
    semantic_diff, request = _fixture_context(fixture)
    tampered = replace(request, instrument_type="UNKNOWN_MARKET")
    contract = build_runtime_state_reconciliation_v1(
        semantic_diff=semantic_diff,
        request=tampered,
    )
    assert (
        contract["contract_status"] == "RUNTIME_STATE_RECONCILIATION_FUTURES_MARKET_TYPE_CONFLICT"
    )


def test_missing_market_type_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_runtime_state_reconciliation_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        instrument_type="",
    )
    semantic_diff, request = _fixture_context(fixture)
    tampered = replace(request, instrument_type="")
    contract = build_runtime_state_reconciliation_v1(
        semantic_diff=semantic_diff,
        request=tampered,
    )
    assert (
        contract["contract_status"] == "RUNTIME_STATE_RECONCILIATION_FUTURES_MARKET_TYPE_CONFLICT"
    )


def test_contract_version_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_runtime_state_reconciliation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    semantic_diff, request = _fixture_context(fixture)
    tampered = replace(request, reconciliation_contract_version="legacy")
    contract = build_runtime_state_reconciliation_v1(
        semantic_diff=semantic_diff,
        request=tampered,
    )
    assert contract["contract_status"] == "RUNTIME_STATE_RECONCILIATION_MISSING_BINDINGS"


def test_serialization_version_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_runtime_state_reconciliation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    semantic_diff, request = _fixture_context(fixture)
    tampered = replace(request, deterministic_serialization_version="legacy")
    contract = build_runtime_state_reconciliation_v1(
        semantic_diff=semantic_diff,
        request=tampered,
    )
    assert contract["contract_status"] == "RUNTIME_STATE_RECONCILIATION_MISSING_BINDINGS"


def test_r4_level_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_runtime_state_reconciliation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    semantic_diff, request = _fixture_context(fixture)
    tampered_levels = []
    for level in request.reconciliation_levels:
        if level.level_name == "r4_recovery_reconciliation":
            tampered_levels.append(
                ReconciliationLevelResult(level_name=level.level_name, level_pass=False)
            )
        else:
            tampered_levels.append(level)
    tampered = replace(request, reconciliation_levels=tuple(tampered_levels))
    contract = build_runtime_state_reconciliation_v1(
        semantic_diff=semantic_diff,
        request=tampered,
    )
    assert contract["contract_status"] == "RUNTIME_STATE_RECONCILIATION_INVALID"


def test_no_asset_specific_market_type_special_handling(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_runtime_state_reconciliation_fixture(
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
    fixture = produce_runtime_state_reconciliation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    semantic_diff, request = _fixture_context(fixture)
    inputs = RuntimeStateReconciliationInputs(
        trading_logic_semantic_diff_evidence_bundle_dir=(
            fixture.trading_logic_semantic_diff_evidence_bundle_dir
        ),
        reconciliation_request=request,
    )
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    produce_runtime_state_reconciliation_v1(inputs=inputs, output_dir=out_a)
    produce_runtime_state_reconciliation_v1(inputs=inputs, output_dir=out_b)
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_field_order_does_not_change_semantics(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_runtime_state_reconciliation_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        )
    )
    reordered = {key: contract[key] for key in reversed(list(contract.keys()))}
    assert deterministic_json_dumps(contract) == deterministic_json_dumps(reordered)


def test_manifest_and_self_verification(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_runtime_state_reconciliation_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.runtime_state_reconciliation_bundle_dir
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    reverify_runtime_state_reconciliation_v1(output_dir=out)


def test_authority_invariants(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_runtime_state_reconciliation_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.runtime_state_reconciliation_bundle_dir / ARTIFACT_REL)
    assert (
        payload["runtime_state_reconciliation_authority_invariants"]
        == RUNTIME_STATE_RECONCILIATION_AUTHORITY_INVARIANTS
    )
    _assert_non_execution(payload)


def test_stable_digest_tamper_on_reverify(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_runtime_state_reconciliation_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.runtime_state_reconciliation_bundle_dir
    artifact_path = out / ARTIFACT_REL
    artifact_path.write_text(
        artifact_path.read_text().replace("RECONCILIATION_VALID", "TAMPERED"),
        encoding="utf-8",
    )
    with pytest.raises(Exception):
        reverify_runtime_state_reconciliation_v1(output_dir=out)


def test_step17_regression_still_passes(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_runtime_state_reconciliation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    payload = read_manifest(
        fixture.trading_logic_semantic_diff_evidence_bundle_dir
        / "trading_logic_semantic_diff_evidence_v1.json"
    )
    assert payload["contract_status"] == "TRADING_LOGIC_SEMANTIC_DIFF_EVIDENCE_VALID"


def test_step16_regression_still_passes(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_runtime_state_reconciliation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    payload = read_manifest(
        fixture.trading_logic_semantic_diff_evidence_bundle_dir.parent
        / "baseline_durable"
        / "baseline_trading_core_decision_attestation"
        / "trading_core_decision_attestation_v1.json"
    )
    assert payload["contract_status"] == "TRADING_CORE_DECISION_ATTESTATION_VALID"


def test_all_required_snapshot_components_present(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_runtime_state_reconciliation_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        )
    )
    component_names = {item["component_name"] for item in contract["snapshot_components"]}
    for field in (
        "local_intent_ledger",
        "submission_ledger",
        "venue_orders",
        "venue_fills",
        "venue_positions",
        "venue_margin",
    ):
        assert field in component_names


def test_all_required_reconciliation_levels_present(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_runtime_state_reconciliation_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        )
    )
    level_names = {item["level_name"] for item in contract["reconciliation_levels"]}
    for field in (
        "r1_event_reconciliation",
        "r2_periodic_snapshot",
        "r3_pre_trade_reconciliation",
        "r4_recovery_reconciliation",
    ):
        assert field in level_names


def test_missing_component_digest_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_runtime_state_reconciliation_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    semantic_diff, request = _fixture_context(fixture)
    tampered_components = []
    for component in request.snapshot_components:
        if component.component_name == "venue_positions":
            tampered_components.append(
                ReconciliationSnapshotComponent(
                    component_name=component.component_name,
                    local_digest="",
                    venue_digest=component.venue_digest,
                    divergence_detected=True,
                )
            )
        else:
            tampered_components.append(component)
    tampered = replace(request, snapshot_components=tuple(tampered_components))
    contract = build_runtime_state_reconciliation_v1(
        semantic_diff=semantic_diff,
        request=tampered,
    )
    assert contract["contract_status"] == "RUNTIME_STATE_RECONCILIATION_MISSING_BINDINGS"
