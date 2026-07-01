"""Contract tests for offline intent compatibility firewall v1 (RUNBOOK STEP 29O)."""

from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import fields, replace
from pathlib import Path

import pytest

import src.governance.intent_compatibility_firewall_v1 as firewall

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "governance"
    / "intent_compatibility_firewall_v1.py"
)

_FORBIDDEN_RUNTIME_ACTIONS = frozenset(
    {
        "submit",
        "execute",
        "place_order",
        "cancel_order",
        "send_order",
        "transform_to_order",
        "calculate_quantity",
        "size_position",
        "grant_permission",
        "issue_authority",
        "runtime_start",
    }
)


def _canonical_target(**overrides: object) -> firewall.IntentTypeDescriptorV1:
    base = dict(
        firewall.INTENT_TYPE_DESCRIPTOR_REGISTRY_V1["CANONICAL_ORDER_INTENT_IDENTITY"].__dict__
    )
    base.update(overrides)
    descriptor = firewall.IntentTypeDescriptorV1(**base)
    return firewall.with_computed_descriptor_digest(descriptor)


def _source(**overrides: object) -> firewall.IntentTypeDescriptorV1:
    base = dict(_canonical_target().__dict__)
    base.update(
        {
            "intent_type_id": "ORCHESTRATOR_ORDER_INTENT",
            "owner_module": "src.execution.orchestrator",
            "producer_domain": "execution.orchestrator",
            "consumer_domain": "execution.pipeline",
            "persistence_lifecycle": "ephemeral_in_memory",
            "side_semantics": "none",
            "reduce_only_semantics": "absent",
            "runtime_effect": False,
            "order_effect": False,
            "adapter_submission_effect": False,
        }
    )
    base.update(overrides)
    descriptor = firewall.IntentTypeDescriptorV1(**base)
    return firewall.with_computed_descriptor_digest(descriptor)


def _edge(**overrides: object) -> firewall.IntentConversionEdgeV1:
    base: dict[str, object] = {
        "source_intent_type_id": "ORCHESTRATOR_ORDER_INTENT",
        "target_intent_type_id": "CANONICAL_ORDER_INTENT_IDENTITY",
        "conversion_kind": "EXPLICIT_ADAPTER",
        "explicit_adapter_id": "offline.intent_compatibility_firewall_v1",
        "explicit_policy_id": "",
        "preserves_quantity_semantics": True,
        "preserves_side_semantics": True,
        "preserves_reduce_only_semantics": True,
        "preserves_instrument_binding": True,
        "preserves_venue_binding": True,
        "preserves_account_binding": True,
        "preserves_identity_binding": True,
        "preserves_authority_binding": True,
        "semantic_digest": "",
    }
    base.update(overrides)
    edge = firewall.IntentConversionEdgeV1(**base)  # type: ignore[arg-type]
    return firewall.with_computed_conversion_edge_digest(edge)


def _evaluate(
    source: firewall.IntentTypeDescriptorV1 | None = None,
    target: firewall.IntentTypeDescriptorV1 | None = None,
    edge: firewall.IntentConversionEdgeV1 | None = None,
) -> firewall.IntentCompatibilityResultV1:
    return firewall.evaluate_intent_compatibility_v1(
        source=source or _source(),
        target=target or _canonical_target(),
        edge=edge or _edge(),
    )


def test_01_pure_function_and_deterministic_results() -> None:
    first = _evaluate()
    second = _evaluate()
    assert first == second
    assert first.verdict == second.verdict
    assert first.reason_codes == second.reason_codes


def test_02_stable_digests_for_identical_inputs() -> None:
    source = _source()
    target = _canonical_target()
    edge = _edge()
    first = firewall.evaluate_intent_compatibility_v1(source, target, edge)
    second = firewall.evaluate_intent_compatibility_v1(source, target, edge)
    assert first.source_descriptor_digest == second.source_descriptor_digest
    assert first.target_descriptor_digest == second.target_descriptor_digest
    assert first.conversion_edge_digest == second.conversion_edge_digest


def test_03_unknown_intent_type_blocks() -> None:
    unknown = firewall.with_computed_descriptor_digest(
        replace(_source(), intent_type_id="UNKNOWN_INTENT_TYPE_X")
    )
    result = _evaluate(source=unknown)
    assert result.verdict is firewall.IntentCompatibilityVerdictV1.BLOCKED_UNKNOWN_INTENT_TYPE
    assert result.admissible is False


def test_04_implicit_conversion_without_explicit_adapter_blocks() -> None:
    result = _evaluate(edge=_edge(conversion_kind="IMPLICIT", explicit_adapter_id=""))
    assert result.verdict is firewall.IntentCompatibilityVerdictV1.BLOCKED_IMPLICIT_CONVERSION


def test_05_missing_canonical_bindings_block() -> None:
    target = _canonical_target(canonical_identity_compatible=False, venue_binding_present=False)
    result = _evaluate(target=target)
    assert result.verdict is firewall.IntentCompatibilityVerdictV1.BLOCKED_MISSING_CANONICAL_BINDING


def test_06_missing_quantity_provenance_blocks() -> None:
    source = _source(quantity_provenance_present=False)
    target = _canonical_target()
    result = _evaluate(
        source=source,
        target=target,
        edge=_edge(
            source_intent_type_id=source.intent_type_id,
            target_intent_type_id=target.intent_type_id,
        ),
    )
    assert result.verdict is firewall.IntentCompatibilityVerdictV1.BLOCKED_QUANTITY_PROVENANCE


def test_07_decimal_to_float_semantics_loss_blocks() -> None:
    source = _source(quantity_semantics="decimal", quantity_provenance_present=True)
    target = _canonical_target(quantity_semantics="float")
    result = _evaluate(
        source=source,
        target=target,
        edge=_edge(
            source_intent_type_id=source.intent_type_id,
            target_intent_type_id=target.intent_type_id,
            preserves_quantity_semantics=True,
        ),
    )
    assert result.verdict is firewall.IntentCompatibilityVerdictV1.BLOCKED_QUANTITY_SEMANTICS


def test_08_buy_sell_vs_buy_sell_without_normalization_blocks() -> None:
    source = _source(side_semantics="BUY_SELL")
    target = _canonical_target(side_semantics="buy_sell")
    result = _evaluate(
        source=source,
        target=target,
        edge=_edge(
            source_intent_type_id=source.intent_type_id,
            target_intent_type_id=target.intent_type_id,
            preserves_side_semantics=True,
        ),
    )
    assert result.verdict is firewall.IntentCompatibilityVerdictV1.BLOCKED_SIDE_SEMANTICS


def test_09_reduce_only_semantics_loss_blocks() -> None:
    result = _evaluate(edge=_edge(preserves_reduce_only_semantics=False))
    assert result.verdict is firewall.IntentCompatibilityVerdictV1.BLOCKED_REDUCE_ONLY_SEMANTICS


def test_10_instrument_binding_loss_blocks() -> None:
    result = _evaluate(edge=_edge(preserves_instrument_binding=False))
    assert result.verdict is firewall.IntentCompatibilityVerdictV1.BLOCKED_INSTRUMENT_BINDING


def test_11_venue_binding_loss_blocks() -> None:
    result = _evaluate(edge=_edge(preserves_venue_binding=False))
    assert result.verdict is firewall.IntentCompatibilityVerdictV1.BLOCKED_VENUE_BINDING


def test_12_account_binding_loss_blocks() -> None:
    result = _evaluate(edge=_edge(preserves_account_binding=False))
    assert result.verdict is firewall.IntentCompatibilityVerdictV1.BLOCKED_ACCOUNT_BINDING


def test_13_identity_binding_loss_blocks() -> None:
    result = _evaluate(edge=_edge(preserves_identity_binding=False))
    assert result.verdict is firewall.IntentCompatibilityVerdictV1.BLOCKED_IDENTITY_BINDING


def test_14_authority_binding_loss_blocks() -> None:
    result = _evaluate(edge=_edge(preserves_authority_binding=False))
    assert result.verdict is firewall.IntentCompatibilityVerdictV1.BLOCKED_AUTHORITY_BINDING


def test_15_runtime_effect_blocks() -> None:
    source = _source(runtime_effect=True)
    result = _evaluate(
        source=source,
        edge=_edge(source_intent_type_id=source.intent_type_id),
    )
    assert result.verdict is firewall.IntentCompatibilityVerdictV1.BLOCKED_RUNTIME_EFFECT


def test_16_order_effect_blocks() -> None:
    source = _source(order_effect=True)
    result = _evaluate(
        source=source,
        edge=_edge(source_intent_type_id=source.intent_type_id),
    )
    assert result.verdict is firewall.IntentCompatibilityVerdictV1.BLOCKED_ORDER_EFFECT


def test_17_adapter_submission_effect_blocks() -> None:
    source = _source(adapter_submission_effect=True)
    result = _evaluate(
        source=source,
        edge=_edge(source_intent_type_id=source.intent_type_id),
    )
    assert result.verdict is firewall.IntentCompatibilityVerdictV1.BLOCKED_ADAPTER_SUBMISSION_EFFECT


def test_18_spot_intent_blocks() -> None:
    source = _source(producer_domain="execution.spot")
    result = _evaluate(
        source=source,
        edge=_edge(source_intent_type_id=source.intent_type_id),
    )
    assert result.verdict is firewall.IntentCompatibilityVerdictV1.BLOCKED_NON_FUTURES_INTENT


def test_19_synthetic_spot_intent_blocks() -> None:
    source = _source(producer_domain="execution.synthetic_spot")
    result = _evaluate(
        source=source,
        edge=_edge(source_intent_type_id=source.intent_type_id),
    )
    assert result.verdict is firewall.IntentCompatibilityVerdictV1.BLOCKED_NON_FUTURES_INTENT


def test_20_bitcoin_direction_semantics_block() -> None:
    source = _source(side_semantics="BITCOIN_DIRECTION")
    result = _evaluate(
        source=source,
        edge=_edge(source_intent_type_id=source.intent_type_id),
    )
    assert (
        result.verdict is firewall.IntentCompatibilityVerdictV1.BLOCKED_BITCOIN_SPECIFIC_DIRECTION
    )


def test_21_lossless_explicit_offline_edge_can_be_admissible() -> None:
    source = _canonical_target()
    target = _canonical_target()
    result = firewall.evaluate_intent_compatibility_v1(
        source=source,
        target=target,
        edge=_edge(
            source_intent_type_id="CANONICAL_ORDER_INTENT_IDENTITY",
            target_intent_type_id="CANONICAL_ORDER_INTENT_IDENTITY",
            conversion_kind="IDENTITY_NO_CONVERSION",
            explicit_adapter_id="",
            explicit_policy_id="offline.identity_no_conversion.v1",
        ),
    )
    assert result.verdict is firewall.IntentCompatibilityVerdictV1.ADMISSIBLE
    assert result.admissible is True


def test_22_admissible_does_not_imply_execution_adapter_runtime_or_authority() -> None:
    source = _canonical_target()
    target = _canonical_target()
    result = firewall.evaluate_intent_compatibility_v1(
        source=source,
        target=target,
        edge=_edge(
            source_intent_type_id="CANONICAL_ORDER_INTENT_IDENTITY",
            target_intent_type_id="CANONICAL_ORDER_INTENT_IDENTITY",
            conversion_kind="IDENTITY_NO_CONVERSION",
            explicit_adapter_id="",
            explicit_policy_id="offline.identity_no_conversion.v1",
        ),
    )
    assert isinstance(result, firewall.IntentCompatibilityResultV1)
    assert result.runtime_effect is False
    assert result.order_effect is False
    assert result.authority_effect is False
    assert result.transformation_performed is False
    assert not hasattr(result, "execution_eligible")
    assert not hasattr(result, "adapter_compatible")
    assert not hasattr(result, "runtime_eligible")
    assert not hasattr(result, "order_allowed")
    assert not hasattr(result, "authority_granted")


def test_23_reason_code_order_is_stable() -> None:
    result_a = _evaluate(edge=_edge(preserves_identity_binding=False))
    result_b = _evaluate(edge=_edge(preserves_identity_binding=False))
    assert result_a.reason_codes == result_b.reason_codes
    assert list(result_a.reason_codes) == sorted(result_a.reason_codes)


def test_24_descriptor_registry_has_no_colliding_type_ids() -> None:
    ids = list(firewall.INTENT_TYPE_DESCRIPTOR_REGISTRY_V1.keys())
    assert len(ids) == len(set(ids))
    for type_id, descriptor in firewall.INTENT_TYPE_DESCRIPTOR_REGISTRY_V1.items():
        assert descriptor.intent_type_id == type_id


def test_25_canonical_identity_is_referenced_not_duplicated() -> None:
    result = _evaluate()
    assert result.canonical_identity_reference == firewall.CANONICAL_IDENTITY_REFERENCE
    assert firewall.CANONICAL_IDENTITY_SYMBOL in firewall.CANONICAL_IDENTITY_REFERENCE
    schema = firewall.intent_compatibility_firewall_schema_v1()
    assert (
        schema["referenced_owners"]["canonical_order_intent_identity"]
        == firewall.CANONICAL_IDENTITY_OWNER_MODULE
    )


def test_26_no_imports_of_runtime_live_submission_owners_with_side_effects() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_from = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    forbidden_runtime_modules = {
        "src.execution.orchestrator",
        "src.execution.pipeline",
        "src.live.orders",
        "src.execution.adapters.base_v1",
        "src.orders.base",
    }
    assert forbidden_runtime_modules.isdisjoint(imported_from)


def test_27_no_quantity_risk_or_sizing_calculation() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    for token in ("calculate_quantity", "size_position", "risk_sizing", "notional"):
        assert token not in source


def test_28_no_network_clock_or_random_dependency() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert "random" not in imported
    assert "time" not in imported
    assert "datetime" not in imported
    assert "socket" not in imported
    assert "requests" not in imported


def test_negative_contract_forbidden_runtime_action_symbols_absent() -> None:
    public_names = {
        name
        for name, obj in inspect.getmembers(firewall)
        if not name.startswith("_") and (inspect.isfunction(obj) or inspect.isclass(obj))
    }
    for forbidden in _FORBIDDEN_RUNTIME_ACTIONS:
        assert forbidden not in public_names


def test_negative_contract_all_results_remain_non_authorizing() -> None:
    scenarios = [
        _evaluate(),
        _evaluate(edge=_edge(preserves_identity_binding=False)),
        _evaluate(source=_source(producer_domain="execution.spot")),
    ]
    for result in scenarios:
        assert result.runtime_effect is False
        assert result.order_effect is False
        assert result.authority_effect is False
        assert result.transformation_performed is False


def test_schema_contract_complete() -> None:
    schema = firewall.intent_compatibility_firewall_schema_v1()
    assert schema["contract_name"] == firewall.CONTRACT_NAME
    assert firewall.IMPLICIT_INTENT_CONVERSION_ALLOWED is False
    assert schema["invariants"]["futures_only"] is True
    assert schema["invariants"]["bitcoin_direction_allowed"] is False
    required_descriptor_fields = {f.name for f in fields(firewall.IntentTypeDescriptorV1)}
    assert "intent_type_id" in required_descriptor_fields
    assert "semantic_digest" in required_descriptor_fields


def test_import_smoke() -> None:
    module = importlib.import_module("src.governance.intent_compatibility_firewall_v1")
    assert module.PACKAGE_MARKER == "INTENT_COMPATIBILITY_FIREWALL_V1=true"


def test_deterministic_double_run_of_full_test_module() -> None:
    source = _canonical_target()
    target = _canonical_target()
    edge = _edge(
        source_intent_type_id="CANONICAL_ORDER_INTENT_IDENTITY",
        target_intent_type_id="CANONICAL_ORDER_INTENT_IDENTITY",
        conversion_kind="IDENTITY_NO_CONVERSION",
        explicit_adapter_id="",
        explicit_policy_id="offline.identity_no_conversion.v1",
    )
    payloads = []
    for _ in range(2):
        result = firewall.evaluate_intent_compatibility_v1(source, target, edge)
        payloads.append(
            json.dumps(
                {
                    "verdict": result.verdict.value,
                    "reason_codes": result.reason_codes,
                    "source_descriptor_digest": result.source_descriptor_digest,
                    "target_descriptor_digest": result.target_descriptor_digest,
                    "conversion_edge_digest": result.conversion_edge_digest,
                },
                sort_keys=True,
            )
        )
    assert payloads[0] == payloads[1]
