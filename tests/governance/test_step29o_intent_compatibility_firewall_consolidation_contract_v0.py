"""STEP 29O contract-level intent compatibility firewall consolidation tests."""

from __future__ import annotations

import json

import pytest

import src.governance.intent_compatibility_firewall_v1 as firewall


def _fully_bound_bindings(**overrides: bool) -> firewall.ContractBindingSnapshotV1:
    base = {
        "quantity_bound": True,
        "quantity_provenance_bound": True,
        "order_type_bound": True,
        "reduce_only_bound": True,
        "venue_bound": True,
        "account_bound": True,
        "instrument_bound": True,
        "risk_provenance_bound": True,
        "policy_digest_bound": True,
        "config_digest_bound": True,
        "implementation_digest_bound": True,
        "permission_bound": True,
        "authority_bound": True,
        "fencing_token_bound": True,
        "futures_only": True,
        "bitcoin_direction": False,
        "spot_market": False,
        "synthetic_spot_market": False,
        "legacy_alias": False,
        "duck_typed_order_fields": False,
    }
    base.update(overrides)
    return firewall.ContractBindingSnapshotV1(**base)


def _evaluate(
    source_type: str,
    source_version: str = "v1",
    bindings: firewall.ContractBindingSnapshotV1 | None = None,
    **kwargs: object,
) -> firewall.IntentCompatibilityAssessmentV1:
    return firewall.evaluate_contract_compatibility_v1(
        source_contract_type=source_type,
        source_contract_version=source_version,
        bindings=bindings or firewall.ContractBindingSnapshotV1(),
        **kwargs,  # type: ignore[arg-type]
    )


def test_canonical_trading_decision_not_adapter_compatible() -> None:
    result = _evaluate("canonical_trading_decision_evidence_v1")
    assert (
        result.compatibility_status
        is firewall.ContractCompatibilityStatusV1.TRANSFORMATION_REQUIRED
    )
    assert result.adapter_compatible is False
    assert firewall.REASON_CANONICAL_DECISION_NOT_ORDER_INTENT in result.reason_codes


def test_decision_dict_with_order_like_fields_still_incompatible() -> None:
    result = _evaluate(
        "canonical_trading_decision_evidence_v1",
        bindings=firewall.ContractBindingSnapshotV1(
            duck_typed_order_fields=True,
            quantity_bound=True,
            order_type_bound=True,
        ),
    )
    assert result.adapter_compatible is False
    assert firewall.REASON_DUCK_TYPING_FIELD_MATCH_INSUFFICIENT in result.reason_codes


def test_risk_result_not_adapter_compatible() -> None:
    for contract in ("pre_sizing_risk_result_v1", "post_sizing_risk_result_v1"):
        result = _evaluate(contract)
        assert result.adapter_compatible is False
        assert firewall.REASON_RISK_OUTPUT_NOT_ADAPTER_COMPATIBLE in result.reason_codes


def test_sizing_result_not_adapter_compatible() -> None:
    for contract in ("canonical_sizing_result_v1", "capital_risk_sizing_decision_v1"):
        result = _evaluate(contract)
        assert result.adapter_compatible is False
        assert firewall.REASON_SIZING_OUTPUT_NOT_ADAPTER_COMPATIBLE in result.reason_codes


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("quantity_bound", firewall.REASON_MISSING_QUANTITY_BINDING),
        ("quantity_provenance_bound", firewall.REASON_MISSING_QUANTITY_PROVENANCE_BINDING),
        ("order_type_bound", firewall.REASON_MISSING_ORDER_TYPE_BINDING),
        ("reduce_only_bound", firewall.REASON_MISSING_REDUCE_ONLY_BINDING),
        ("venue_bound", firewall.REASON_MISSING_VENUE_BINDING),
        ("account_bound", firewall.REASON_MISSING_ACCOUNT_BINDING),
        ("instrument_bound", firewall.REASON_MISSING_INSTRUMENT_BINDING),
        ("policy_digest_bound", firewall.REASON_MISSING_POLICY_DIGEST_BINDING),
        ("config_digest_bound", firewall.REASON_MISSING_CONFIG_DIGEST_BINDING),
        ("implementation_digest_bound", firewall.REASON_MISSING_IMPLEMENTATION_DIGEST_BINDING),
        ("permission_bound", firewall.REASON_MISSING_PERMISSION_BINDING),
        ("authority_bound", firewall.REASON_MISSING_AUTHORITY_LEASE_BINDING),
        ("fencing_token_bound", firewall.REASON_MISSING_FENCING_TOKEN_BINDING),
    ],
)
def test_missing_binding_blocks(field: str, reason: str) -> None:
    overrides = {field: False}
    bindings = _fully_bound_bindings(**overrides)
    result = _evaluate(
        "boundary_fully_bound_canonical_order_intent_with_permission_v1",
        bindings=bindings,
    )
    assert result.adapter_compatible is False
    assert reason in result.reason_codes


def test_unknown_source_contract_blocks() -> None:
    result = _evaluate("unknown_contract_xyz", "v0")
    assert result.compatibility_status is firewall.ContractCompatibilityStatusV1.INCOMPATIBLE
    assert firewall.REASON_UNKNOWN_SOURCE_CONTRACT in result.reason_codes


def test_unknown_contract_version_blocks() -> None:
    result = _evaluate("canonical_trading_decision_evidence_v1", "v99")
    assert result.compatibility_status is firewall.ContractCompatibilityStatusV1.INCOMPATIBLE
    assert firewall.REASON_UNKNOWN_SOURCE_CONTRACT in result.reason_codes


def test_legacy_alias_blocks_without_transformation() -> None:
    result = _evaluate(
        "adapter_order_intent_v1",
        "legacy_alias",
        bindings=firewall.ContractBindingSnapshotV1(legacy_alias=True),
    )
    assert result.adapter_compatible is False
    assert firewall.REASON_LEGACY_ALIAS_WITHOUT_TRANSFORMATION in result.reason_codes


def test_same_field_structure_does_not_create_implicit_compatibility() -> None:
    bindings = firewall.ContractBindingSnapshotV1(
        duck_typed_order_fields=True,
        quantity_bound=True,
        order_type_bound=True,
        reduce_only_bound=True,
        venue_bound=True,
        account_bound=True,
    )
    result = _evaluate("canonical_trading_decision_evidence_v1", bindings=bindings)
    assert result.adapter_compatible is False
    assert firewall.REASON_DUCK_TYPING_FIELD_MATCH_INSUFFICIENT in result.reason_codes


def test_boundary_fixture_structural_only_no_runtime_effect() -> None:
    result = _evaluate(
        "boundary_fully_bound_canonical_order_intent_with_permission_v1",
        bindings=_fully_bound_bindings(),
    )
    assert (
        result.compatibility_status
        is firewall.ContractCompatibilityStatusV1.STRUCTURALLY_COMPATIBLE_NOT_EXECUTION_ELIGIBLE
    )
    assert result.adapter_compatible is False
    assert result.authority_effect == firewall.AUTHORITY_EFFECT_NONE
    assert result.runtime_effect == firewall.RUNTIME_EFFECT_NONE
    assert firewall.REASON_BOUNDARY_STRUCTURAL_ONLY in result.reason_codes


def test_authority_and_runtime_effect_remain_none() -> None:
    scenarios = [
        _evaluate("canonical_trading_decision_evidence_v1"),
        _evaluate("pre_sizing_risk_result_v1"),
        _evaluate(
            "boundary_fully_bound_canonical_order_intent_with_permission_v1",
            bindings=_fully_bound_bindings(),
        ),
    ]
    for result in scenarios:
        assert result.authority_effect == firewall.AUTHORITY_EFFECT_NONE
        assert result.runtime_effect == firewall.RUNTIME_EFFECT_NONE


def test_deterministic_reason_code_order() -> None:
    first = _evaluate("canonical_trading_decision_evidence_v1")
    second = _evaluate("canonical_trading_decision_evidence_v1")
    assert first.reason_codes == second.reason_codes
    assert list(first.reason_codes) == sorted(first.reason_codes)


def test_serialization_digest_roundtrip() -> None:
    result = _evaluate("canonical_trading_decision_evidence_v1")
    digest = firewall.compute_intent_compatibility_assessment_digest(result)
    assert digest == result.assessment_digest
    payload = {
        field.name: getattr(result, field.name)
        for field in firewall.fields(firewall.IntentCompatibilityAssessmentV1)
    }
    payload["compatibility_status"] = result.compatibility_status.value
    encoded = json.dumps(payload, sort_keys=True, default=str)
    assert "canonical_trading_decision_evidence_v1" in encoded


def test_futures_only_spot_and_synthetic_spot_excluded() -> None:
    for flag in ("spot_market", "synthetic_spot_market"):
        bindings = firewall.ContractBindingSnapshotV1(
            futures_only=False,
            **{flag: True},
        )
        result = _evaluate("canonical_trading_decision_evidence_v1", bindings=bindings)
        assert firewall.REASON_NON_FUTURES_CONTRACT in result.reason_codes


def test_bitcoin_direction_excluded() -> None:
    bindings = firewall.ContractBindingSnapshotV1(bitcoin_direction=True)
    result = _evaluate("canonical_trading_decision_evidence_v1", bindings=bindings)
    assert firewall.REASON_BITCOIN_DIRECTION_FORBIDDEN in result.reason_codes


def test_negative_guard_raises_on_forbidden_adapter_compatible() -> None:
    assessment = firewall.assert_not_adapter_compatible_contract_v1(
        source_contract_type="canonical_trading_decision_evidence_v1",
        source_contract_version="v1",
    )
    assert assessment.adapter_compatible is False


def test_registry_entries_for_decision_risk_sizing_present() -> None:
    assert "CANONICAL_TRADING_DECISION_EVIDENCE_V1" in firewall.INTENT_TYPE_DESCRIPTOR_REGISTRY_V1
    assert "PRE_SIZING_RISK_RESULT_V1" in firewall.INTENT_TYPE_DESCRIPTOR_REGISTRY_V1
    assert "CANONICAL_SIZING_RESULT_V1" in firewall.INTENT_TYPE_DESCRIPTOR_REGISTRY_V1
    assert ("canonical_trading_decision_evidence_v1", "v1") in firewall.CONTRACT_TYPE_REGISTRY_V1


def test_compatibility_firewall_contract_invariants() -> None:
    contract = firewall.compatibility_firewall_contract_v1()
    invariants = contract["invariants"]
    assert invariants["canonical_trading_decision_is_not_order_intent"] is True
    assert invariants["no_implicit_adapter_compatibility"] is True
    assert invariants["authority_effect"] == firewall.AUTHORITY_EFFECT_NONE
    assert invariants["runtime_effect"] == firewall.RUNTIME_EFFECT_NONE


def test_bypass_scan_has_no_open_critical_paths() -> None:
    results = firewall.bypass_scan_results_v1()
    assert results
    for entry in results:
        assert entry["classification"] in {
            "CLOSED_IN_SCOPE",
            "ALREADY_GUARDED",
            "DEFERRED_TO_STEP29P",
            "DEFERRED_TO_STEP29Q",
            "DEFERRED_TO_STEP29R",
            "OUT_OF_SCOPE_WITH_EXPLICIT_OWNER",
        }


def test_current_real_intents_never_adapter_compatible() -> None:
    real_contracts = (
        "canonical_trading_decision_evidence_v1",
        "pre_sizing_risk_result_v1",
        "post_sizing_risk_result_v1",
        "canonical_sizing_result_v1",
        "capital_risk_sizing_decision_v1",
    )
    for contract in real_contracts:
        result = _evaluate(contract, bindings=_fully_bound_bindings())
        assert result.adapter_compatible is False
