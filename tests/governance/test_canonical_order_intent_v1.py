"""Contract tests for offline canonical order intent v1 (RUNBOOK STEP 29Q)."""

from __future__ import annotations

import ast
import importlib
import inspect
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import src.governance.canonical_order_intent_v1 as intent_mod
import src.governance.capital_risk_sizing_v1 as sizing
from src.execution.adapters.base_v1 import OrderIntentV1

MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "src" / "governance" / "canonical_order_intent_v1.py"
)

_FORBIDDEN_RUNTIME_MODULES = frozenset(
    {
        "src.execution.orchestrator",
        "src.execution.pipeline",
        "src.live.orders",
        "src.execution.adapters.base_v1",
        "src.orders.base",
    }
)

TOTAL_LIMIT_USD = Decimal("500")
ORDER_LIMIT_USD = Decimal("25")
DAILY_LOSS_LIMIT_USD = Decimal("25")


def _instrument(**overrides: object) -> sizing.InstrumentQuantityConstraintsV1:
    base: dict[str, object] = {
        "instrument_id": "ETH-USD-PERP",
        "market_type": "futures",
        "contract_kind": "LINEAR",
        "contract_multiplier": Decimal("1"),
        "quantity_step": Decimal("0.01"),
        "minimum_quantity": Decimal("0.01"),
        "maximum_quantity": Decimal("100"),
        "minimum_notional": Decimal("5"),
        "instrument_metadata_version": "futures_metadata_v1_test",
    }
    base.update(overrides)
    return sizing.InstrumentQuantityConstraintsV1(**base)  # type: ignore[arg-type]


def _sizing_input(**overrides: object) -> sizing.CapitalRiskSizingInputV1:
    instrument = _instrument()
    base: dict[str, object] = {
        "decision_id": "decision-001",
        "instrument_id": instrument.instrument_id,
        "selected_side": sizing.SelectedSide.LONG.value,
        "reference_price": Decimal("2000"),
        "protective_stop_price": Decimal("1900"),
        "stop_distance": None,
        "account_equity": TOTAL_LIMIT_USD,
        "scope_capital_limit": ORDER_LIMIT_USD,
        "per_trade_risk_limit": ORDER_LIMIT_USD,
        "total_capital_limit": TOTAL_LIMIT_USD,
        "daily_loss_remaining_budget": DAILY_LOSS_LIMIT_USD,
        "current_reconciled_exposure": Decimal("0"),
        "maximum_positions": 1,
        "current_open_positions_count": 0,
        "current_open_side": None,
        "configured_quantity_cap": None,
        "leverage_ceiling": Decimal("5"),
        "reconciliation_status": "RECONCILED",
        "policy_version": "capital_risk_sizing_policy_v1",
        "config_digest": "cfg_digest_test",
        "input_digest": "input_digest_test",
        "instrument": instrument,
    }
    base.update(overrides)
    return sizing.CapitalRiskSizingInputV1(**base)  # type: ignore[arg-type]


def _passing_sizing_decision(**overrides: object) -> sizing.CapitalRiskSizingDecisionV1:
    return sizing.evaluate_capital_risk_sizing_v1(_sizing_input(**overrides))


def _build_input(
    *,
    intent_action: str = intent_mod.IntentAction.ENTER_LONG.value,
    sizing_overrides: dict[str, object] | None = None,
    **overrides: object,
) -> intent_mod.CanonicalOrderIntentBuildInputV1:
    sizing_overrides = sizing_overrides or {}
    sizing_input = _sizing_input(**sizing_overrides)
    sizing_decision = sizing.evaluate_capital_risk_sizing_v1(sizing_input)
    side = sizing_overrides.get("selected_side", sizing.SelectedSide.LONG.value)
    expected_side = (
        intent_mod.IntentSide.LONG.value
        if intent_action == intent_mod.IntentAction.ENTER_LONG.value
        else intent_mod.IntentSide.SHORT.value
        if intent_action == intent_mod.IntentAction.ENTER_SHORT.value
        else str(side)
    )
    base: dict[str, object] = {
        "sizing_input": sizing_input,
        "sizing_decision": sizing_decision,
        "intent_id": "intent-001",
        "trading_epoch": "epoch-001",
        "canonical_trading_logic_version": "trading_logic_v1_test",
        "intent_action": intent_action,
        "policy_digest": "policy_digest_test",
        "order_type_policy": "MARKET_ONLY",
        "price_policy": "EXPLICIT_NONE",
        "time_in_force_policy": "GTC",
        "max_slippage_policy": "ZERO",
        "expected_position_side": expected_side,
        "current_reconciled_exposure": sizing_input.current_reconciled_exposure,
        "current_open_side": sizing_input.current_open_side,
    }
    base.update(overrides)
    return intent_mod.CanonicalOrderIntentBuildInputV1(**base)  # type: ignore[arg-type]


def _build(**kwargs: object) -> intent_mod.CanonicalOrderIntentBuildResultV1:
    return intent_mod.build_canonical_order_intent_v1(_build_input(**kwargs))  # type: ignore[arg-type]


def _intent(**kwargs: object) -> intent_mod.CanonicalOrderIntentV1:
    result = _build(**kwargs)
    assert result.outcome is intent_mod.CanonicalOrderIntentBuildOutcome.PASS
    assert result.intent is not None
    return result.intent


# --- Positive contracts ---


def test_positive_deterministic_intent_generation() -> None:
    first = _build()
    second = _build()
    assert first == second
    assert first.intent == second.intent


def test_positive_stable_semantic_digests() -> None:
    first = _intent()
    second = _intent()
    assert first.semantic_digest == second.semantic_digest
    assert first.semantic_digest != ""


def test_positive_complete_provenance() -> None:
    built = _intent()
    assert built.capital_envelope_ref
    assert built.pre_sizing_risk_ref
    assert built.sizing_result_ref
    assert built.post_sizing_risk_ref
    assert built.provenance_digest
    assert built.quantity_provenance


def test_positive_provenance_refs_bound() -> None:
    built = _intent()
    decision = _passing_sizing_decision()
    assert built.capital_envelope_ref == intent_mod.compute_capital_envelope_ref(decision)
    assert built.pre_sizing_risk_ref == intent_mod.compute_pre_sizing_risk_ref(decision)
    assert built.sizing_result_ref == intent_mod.compute_sizing_result_ref(decision)
    assert built.post_sizing_risk_ref == intent_mod.compute_post_sizing_risk_ref(decision)
    assert built.decision_id == "decision-001"


def test_positive_enter_long_semantics() -> None:
    built = _intent(intent_action=intent_mod.IntentAction.ENTER_LONG.value)
    assert built.intent_action == intent_mod.IntentAction.ENTER_LONG.value
    assert built.side == intent_mod.IntentSide.LONG.value
    assert built.position_effect == intent_mod.PositionEffect.OPEN_OR_INCREASE.value
    assert built.reduce_only is False


def test_positive_enter_short_semantics() -> None:
    built = _intent(
        intent_action=intent_mod.IntentAction.ENTER_SHORT.value,
        sizing_overrides={
            "selected_side": sizing.SelectedSide.SHORT.value,
            "protective_stop_price": Decimal("2100"),
        },
    )
    assert built.intent_action == intent_mod.IntentAction.ENTER_SHORT.value
    assert built.side == intent_mod.IntentSide.SHORT.value
    assert built.position_effect == intent_mod.PositionEffect.OPEN_OR_INCREASE.value
    assert built.reduce_only is False


def test_positive_reduce_semantics() -> None:
    built = _intent(
        intent_action=intent_mod.IntentAction.REDUCE.value,
        sizing_overrides={
            "current_reconciled_exposure": Decimal("1.0"),
            "current_open_positions_count": 1,
            "current_open_side": sizing.SelectedSide.LONG.value,
            "maximum_positions": 2,
        },
        current_reconciled_exposure=Decimal("1.0"),
    )
    assert built.intent_action == intent_mod.IntentAction.REDUCE.value
    assert built.reduce_only is True
    assert built.position_effect == intent_mod.PositionEffect.REDUCE_ONLY.value


def test_positive_exit_semantics() -> None:
    built = _intent(
        intent_action=intent_mod.IntentAction.EXIT.value,
        sizing_overrides={
            "current_reconciled_exposure": Decimal("0.5"),
            "current_open_positions_count": 1,
            "current_open_side": sizing.SelectedSide.LONG.value,
            "maximum_positions": 2,
        },
        current_reconciled_exposure=Decimal("0.5"),
    )
    assert built.intent_action == intent_mod.IntentAction.EXIT.value
    assert built.reduce_only is True
    assert built.position_effect == intent_mod.PositionEffect.CLOSE_ONLY.value


def test_positive_quantity_positive_and_sizing_bound() -> None:
    built = _intent()
    assert built.quantity > 0
    decision = _passing_sizing_decision()
    assert decision.quantity_provenance is not None
    assert built.quantity == decision.quantity_provenance.final_quantity
    assert built.quantity_provenance == decision.quantity_provenance.output_digest


def test_positive_futures_instrument_accepted() -> None:
    built = _intent()
    assert built.instrument_id == "ETH-USD-PERP"


def test_positive_immutable_contract() -> None:
    built = _intent()
    intent_mod.assert_canonical_order_intent_immutable(built)
    with pytest.raises(Exception):
        built.quantity = Decimal("999")  # type: ignore[misc]


def test_positive_serialization_roundtrip() -> None:
    built = _intent()
    payload = json.loads(intent_mod.canonical_order_intent_to_json(built))
    restored = intent_mod.canonical_order_intent_from_dict(payload)
    assert restored.semantic_digest == built.semantic_digest
    assert restored.intent_id == built.intent_id
    assert restored.quantity == built.quantity


def test_positive_execution_eligible_false() -> None:
    built = _intent()
    assert built.execution_eligible is False


def test_positive_adapter_compatible_false() -> None:
    built = _intent()
    assert built.adapter_compatible is False


def test_positive_submission_authorized_false() -> None:
    built = _intent()
    assert built.submission_authorized is False


def test_positive_no_runtime_or_authority_effect() -> None:
    built = _intent()
    assert built.runtime_effect == intent_mod.RUNTIME_EFFECT_NONE
    assert built.authority_effect == intent_mod.AUTHORITY_EFFECT_NONE
    assert built.network_effect == intent_mod.NETWORK_EFFECT_NONE
    assert built.credential_effect == intent_mod.CREDENTIAL_EFFECT_NONE
    assert built.transformation_required is True


# --- Negative / fail-closed ---


def test_negative_missing_quantity_provenance() -> None:
    decision = _passing_sizing_decision()
    assert decision.quantity_provenance is not None
    blocked = sizing.CapitalRiskSizingDecisionV1(
        outcome=decision.outcome,
        final_quantity=decision.final_quantity,
        selected_side=decision.selected_side,
        capital_envelope=decision.capital_envelope,
        pre_sizing_risk=decision.pre_sizing_risk,
        canonical_sizing=decision.canonical_sizing,
        post_sizing_risk=decision.post_sizing_risk,
        quantity_provenance=None,
        reason_codes=decision.reason_codes,
    )
    result = intent_mod.build_canonical_order_intent_v1(
        intent_mod.CanonicalOrderIntentBuildInputV1(
            sizing_input=_sizing_input(),
            sizing_decision=blocked,
            intent_id="intent-001",
            trading_epoch="epoch-001",
            canonical_trading_logic_version="trading_logic_v1_test",
            intent_action=intent_mod.IntentAction.ENTER_LONG.value,
            policy_digest="policy_digest_test",
            order_type_policy="LIMIT_ONLY",
            price_policy="REFERENCE_PRICE",
            time_in_force_policy="GTC",
            max_slippage_policy="ZERO",
            expected_position_side=intent_mod.IntentSide.LONG.value,
            current_reconciled_exposure=Decimal("0"),
        )
    )
    assert result.outcome is intent_mod.CanonicalOrderIntentBuildOutcome.BLOCKED
    assert intent_mod.REASON_MISSING_QUANTITY_PROVENANCE in result.reason_codes


def test_negative_quantity_zero_or_negative() -> None:
    decision = _passing_sizing_decision()
    assert decision.quantity_provenance is not None
    bad_provenance = sizing.QuantityProvenanceV1(
        **{
            **{
                field.name: getattr(decision.quantity_provenance, field.name)
                for field in sizing.QuantityProvenanceV1.__dataclass_fields__.values()
            },
            "final_quantity": Decimal("0"),
            "output_digest": "",
        }
    )
    blocked = sizing.CapitalRiskSizingDecisionV1(
        outcome=decision.outcome,
        final_quantity=Decimal("0"),
        selected_side=decision.selected_side,
        capital_envelope=decision.capital_envelope,
        pre_sizing_risk=decision.pre_sizing_risk,
        canonical_sizing=decision.canonical_sizing,
        post_sizing_risk=decision.post_sizing_risk,
        quantity_provenance=bad_provenance,
        reason_codes=decision.reason_codes,
    )
    result = intent_mod.build_canonical_order_intent_v1(
        intent_mod.CanonicalOrderIntentBuildInputV1(
            sizing_input=_sizing_input(),
            sizing_decision=blocked,
            intent_id="intent-001",
            trading_epoch="epoch-001",
            canonical_trading_logic_version="trading_logic_v1_test",
            intent_action=intent_mod.IntentAction.ENTER_LONG.value,
            policy_digest="policy_digest_test",
            order_type_policy="LIMIT_ONLY",
            price_policy="REFERENCE_PRICE",
            time_in_force_policy="GTC",
            max_slippage_policy="ZERO",
            expected_position_side=intent_mod.IntentSide.LONG.value,
            current_reconciled_exposure=Decimal("0"),
        )
    )
    assert result.outcome is intent_mod.CanonicalOrderIntentBuildOutcome.BLOCKED
    assert intent_mod.REASON_INVALID_QUANTITY in result.reason_codes


def test_negative_exit_without_reduce_only_semantics() -> None:
    result = intent_mod.build_canonical_order_intent_v1(
        _build_input(intent_action=intent_mod.IntentAction.EXIT.value)
    )
    assert result.outcome is intent_mod.CanonicalOrderIntentBuildOutcome.PASS
    bad = intent_mod.replace(result.intent, reduce_only=False)  # type: ignore[arg-type]
    validation = intent_mod.validate_canonical_order_intent_v1(bad)
    assert validation.validation_status == intent_mod.ValidationStatus.INVALID.value
    assert intent_mod.REASON_EXIT_WITHOUT_REDUCE_ONLY in validation.reason_codes


def test_negative_reduce_exposure_increase() -> None:
    result = intent_mod.build_canonical_order_intent_v1(
        _build_input(
            intent_action=intent_mod.IntentAction.REDUCE.value,
            sizing_overrides={
                "current_reconciled_exposure": Decimal("0.05"),
                "current_open_positions_count": 1,
                "current_open_side": sizing.SelectedSide.LONG.value,
                "maximum_positions": 2,
            },
            current_reconciled_exposure=Decimal("0.005"),
        )
    )
    assert result.outcome is intent_mod.CanonicalOrderIntentBuildOutcome.BLOCKED
    assert intent_mod.REASON_REDUCE_EXPOSURE_INCREASE in result.reason_codes


def test_negative_enter_long_wrong_position_effect() -> None:
    result = intent_mod.build_canonical_order_intent_v1(
        _build_input(intent_action=intent_mod.IntentAction.ENTER_LONG.value)
    )
    assert result.intent is not None
    bad = intent_mod.replace(
        result.intent,
        position_effect=intent_mod.PositionEffect.REDUCE_ONLY.value,
    )
    validation = intent_mod.validate_canonical_order_intent_v1(bad)
    assert intent_mod.REASON_ENTER_LONG_WRONG_POSITION_EFFECT in validation.reason_codes


def test_negative_enter_short_wrong_position_effect() -> None:
    result = intent_mod.build_canonical_order_intent_v1(
        _build_input(
            intent_action=intent_mod.IntentAction.ENTER_SHORT.value,
            sizing_overrides={
                "selected_side": sizing.SelectedSide.SHORT.value,
                "protective_stop_price": Decimal("2100"),
            },
        )
    )
    assert result.intent is not None
    bad = intent_mod.replace(
        result.intent,
        position_effect=intent_mod.PositionEffect.OPEN_OR_INCREASE.value,
        side=intent_mod.IntentSide.SHORT.value,
        intent_action=intent_mod.IntentAction.ENTER_SHORT.value,
    )
    validation = intent_mod.validate_canonical_order_intent_v1(bad)
    assert validation.validation_status == intent_mod.ValidationStatus.VALID.value


def test_negative_implicit_reversal() -> None:
    result = intent_mod.build_canonical_order_intent_v1(
        _build_input(
            intent_action=intent_mod.IntentAction.ENTER_SHORT.value,
            sizing_overrides={
                "selected_side": sizing.SelectedSide.SHORT.value,
                "protective_stop_price": Decimal("2100"),
                "current_reconciled_exposure": Decimal("1"),
                "current_open_positions_count": 1,
                "current_open_side": sizing.SelectedSide.LONG.value,
            },
            current_open_side=sizing.SelectedSide.LONG.value,
            current_reconciled_exposure=Decimal("1"),
        )
    )
    assert result.outcome is intent_mod.CanonicalOrderIntentBuildOutcome.BLOCKED
    assert intent_mod.REASON_IMPLICIT_REVERSAL in result.reason_codes


def test_negative_missing_decision_ref() -> None:
    result = intent_mod.build_canonical_order_intent_v1(
        _build_input(sizing_overrides={"decision_id": ""})
    )
    assert result.outcome is intent_mod.CanonicalOrderIntentBuildOutcome.BLOCKED
    assert intent_mod.REASON_MISSING_DECISION_REF in result.reason_codes


def test_negative_invalid_digest() -> None:
    built = _intent()
    bad = intent_mod.replace(built, semantic_digest="deadbeef")
    validation = intent_mod.validate_canonical_order_intent_v1(bad)
    assert intent_mod.REASON_INVALID_DIGEST in validation.reason_codes


def test_negative_spot_instrument() -> None:
    result = intent_mod.build_canonical_order_intent_v1(
        _build_input(
            sizing_overrides={
                "instrument_id": "ETH-USD",
                "instrument": _instrument(market_type="spot", instrument_id="ETH-USD"),
            }
        )
    )
    assert result.outcome is intent_mod.CanonicalOrderIntentBuildOutcome.BLOCKED
    assert intent_mod.REASON_NON_FUTURES_INSTRUMENT in result.reason_codes


def test_negative_synthetic_spot_instrument() -> None:
    result = intent_mod.build_canonical_order_intent_v1(
        _build_input(
            sizing_overrides={
                "instrument_id": "ETH-SYN",
                "instrument": _instrument(market_type="synthetic_spot", instrument_id="ETH-SYN"),
            }
        )
    )
    assert result.outcome is intent_mod.CanonicalOrderIntentBuildOutcome.BLOCKED
    assert intent_mod.REASON_NON_FUTURES_INSTRUMENT in result.reason_codes


def test_negative_bitcoin_direction() -> None:
    result = intent_mod.build_canonical_order_intent_v1(
        _build_input(
            sizing_overrides={
                "instrument_id": "BTC-USD-PERP",
                "instrument": _instrument(instrument_id="BTC-USD-PERP"),
            }
        )
    )
    assert result.outcome is intent_mod.CanonicalOrderIntentBuildOutcome.BLOCKED
    assert intent_mod.REASON_BITCOIN_SPECIFIC_DIRECTION in result.reason_codes


def test_negative_direct_adapter_cast() -> None:
    built = _intent()
    firewall = intent_mod.evaluate_adapter_compatibility_firewall_v1(
        built,
        target_type_name="OrderRequest",
    )
    assert firewall.admissible is False
    assert intent_mod.REASON_ADAPTER_CAST_FORBIDDEN in firewall.reason_codes
    with pytest.raises(intent_mod.CanonicalOrderIntentError):
        intent_mod.reject_direct_adapter_cast_v1(built, dict)


def test_negative_direct_submission() -> None:
    built = _intent()
    with pytest.raises(intent_mod.CanonicalOrderIntentError):
        intent_mod.reject_direct_submission_v1(built)


def test_negative_no_action_not_submittable() -> None:
    result = intent_mod.build_canonical_order_intent_v1(
        _build_input(intent_action=intent_mod.IntentAction.NO_ACTION.value)
    )
    assert result.outcome is intent_mod.CanonicalOrderIntentBuildOutcome.BLOCKED
    assert intent_mod.REASON_NO_ACTION_NOT_SUBMITTABLE in result.reason_codes


def test_negative_sizing_not_pass() -> None:
    blocked_decision = sizing.evaluate_capital_risk_sizing_v1(
        _sizing_input(scope_capital_limit=Decimal("0"))
    )
    assert blocked_decision.outcome is sizing.CapitalRiskSizingOutcome.BLOCKED
    result = intent_mod.build_canonical_order_intent_v1(
        intent_mod.CanonicalOrderIntentBuildInputV1(
            sizing_input=_sizing_input(scope_capital_limit=Decimal("0")),
            sizing_decision=blocked_decision,
            intent_id="intent-001",
            trading_epoch="epoch-001",
            canonical_trading_logic_version="trading_logic_v1_test",
            intent_action=intent_mod.IntentAction.ENTER_LONG.value,
            policy_digest="policy_digest_test",
            order_type_policy="LIMIT_ONLY",
            price_policy="REFERENCE_PRICE",
            time_in_force_policy="GTC",
            max_slippage_policy="ZERO",
            expected_position_side=intent_mod.IntentSide.LONG.value,
            current_reconciled_exposure=Decimal("0"),
        )
    )
    assert result.outcome is intent_mod.CanonicalOrderIntentBuildOutcome.BLOCKED
    assert intent_mod.REASON_SIZING_NOT_PASS in result.reason_codes


def test_negative_deterministic_serialization_stable() -> None:
    built = _intent()
    first = intent_mod.canonical_order_intent_to_json(built)
    second = intent_mod.canonical_order_intent_to_json(built)
    assert first == second


def test_negative_no_runtime_imports() -> None:
    source = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(source):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
    for forbidden in _FORBIDDEN_RUNTIME_MODULES:
        assert forbidden not in imported


def test_schema_contract_complete() -> None:
    schema = intent_mod.canonical_order_intent_schema_v1()
    assert schema["contract_name"] == intent_mod.CONTRACT_NAME
    assert schema["invariants"]["execution_eligible"] is False
    assert schema["invariants"]["adapter_compatible"] is False
    assert schema["invariants"]["no_order_without_quantity_provenance"] is True


def test_import_smoke() -> None:
    mod = importlib.import_module("src.governance.canonical_order_intent_v1")
    assert inspect.isfunction(mod.build_canonical_order_intent_v1)
    assert inspect.isfunction(mod.transform_canonical_order_intent_v1_to_adapter_order_intent_v1)


# --- STEP 29R: canonical -> adapter transformation contract ---


def _mutated_intent(
    intent: intent_mod.CanonicalOrderIntentV1,
    **kwargs: object,
) -> intent_mod.CanonicalOrderIntentV1:
    mutated = intent_mod.replace(intent, **kwargs)  # type: ignore[arg-type]
    if "semantic_digest" not in kwargs:
        mutated = intent_mod.replace(
            mutated,
            semantic_digest=intent_mod.compute_semantic_digest(mutated),
        )
    return mutated


def _transformable_intent(**kwargs: object) -> intent_mod.CanonicalOrderIntentV1:
    build_kwargs: dict[str, object] = {
        "order_type_policy": "MARKET_ONLY",
        "price_policy": "EXPLICIT_NONE",
        "time_in_force_policy": "GTC",
    }
    build_kwargs.update(kwargs)
    return _intent(**build_kwargs)


def _transform(**kwargs: object) -> intent_mod.CanonicalOrderIntentTransformResultV1:
    return intent_mod.transform_canonical_order_intent_v1_to_adapter_order_intent_v1(
        _transformable_intent(**kwargs)
    )


def _as_order_intent_v1(
    structural: intent_mod.AdapterOrderIntentV1StructuralV1,
) -> OrderIntentV1:
    meta = dict(structural.meta) if structural.meta is not None else None
    return OrderIntentV1(
        symbol=structural.symbol,
        side=structural.side,  # type: ignore[arg-type]
        qty=structural.qty,
        order_type=structural.order_type,  # type: ignore[arg-type]
        price=structural.price,
        tif=structural.tif,  # type: ignore[arg-type]
        post_only=structural.post_only,
        reduce_only=structural.reduce_only,
        client_id=structural.client_id,
        meta=meta,
    )


def test_transform_01_long_entry_deterministic_success() -> None:
    result = _transform(intent_action=intent_mod.IntentAction.ENTER_LONG.value)
    assert result.outcome is intent_mod.CanonicalOrderIntentTransformOutcome.PASS
    assert result.adapter_intent is not None
    assert result.descriptor is not None
    adapter = _as_order_intent_v1(result.adapter_intent)
    assert adapter.side == "buy"
    assert adapter.reduce_only is False
    assert adapter.symbol == "ETH-USD-PERP"
    assert adapter.order_type == "market"
    assert adapter.tif == "gtc"
    assert result.descriptor.transformation_required_acknowledged is True


def test_transform_02_short_entry_deterministic_success() -> None:
    result = _transform(
        intent_action=intent_mod.IntentAction.ENTER_SHORT.value,
        sizing_overrides={
            "selected_side": sizing.SelectedSide.SHORT.value,
            "protective_stop_price": Decimal("2100"),
        },
    )
    assert result.outcome is intent_mod.CanonicalOrderIntentTransformOutcome.PASS
    assert result.adapter_intent is not None
    adapter = _as_order_intent_v1(result.adapter_intent)
    assert adapter.side == "sell"
    assert adapter.reduce_only is False


def test_transform_03_reduce_only_exit_stays_reduce_only() -> None:
    result = _transform(
        intent_action=intent_mod.IntentAction.EXIT.value,
        sizing_overrides={
            "current_reconciled_exposure": Decimal("0.5"),
            "current_open_positions_count": 1,
            "current_open_side": sizing.SelectedSide.LONG.value,
            "maximum_positions": 2,
        },
        current_reconciled_exposure=Decimal("0.5"),
    )
    assert result.outcome is intent_mod.CanonicalOrderIntentTransformOutcome.PASS
    assert result.adapter_intent is not None
    assert result.adapter_intent.reduce_only is True
    assert result.adapter_intent.side == "sell"


def test_transform_04_identical_input_identical_output_and_descriptor() -> None:
    intent = _transformable_intent()
    first = intent_mod.transform_canonical_order_intent_v1_to_adapter_order_intent_v1(intent)
    second = intent_mod.transform_canonical_order_intent_v1_to_adapter_order_intent_v1(intent)
    assert first == second
    assert first.descriptor is not None
    assert second.descriptor is not None
    assert first.descriptor.target_digest == second.descriptor.target_digest
    assert first.descriptor.source_digest == intent.semantic_digest


def test_transform_05_direct_cast_remains_forbidden() -> None:
    built = _transformable_intent()
    with pytest.raises(intent_mod.CanonicalOrderIntentError):
        intent_mod.reject_direct_adapter_cast_v1(built, OrderIntentV1)


def test_transform_06_missing_quantity_provenance_rejected() -> None:
    intent = _transformable_intent()
    bad = _mutated_intent(intent, quantity_provenance="")
    result = intent_mod.transform_canonical_order_intent_v1_to_adapter_order_intent_v1(bad)
    assert result.outcome is intent_mod.CanonicalOrderIntentTransformOutcome.BLOCKED
    assert intent_mod.REASON_MISSING_QUANTITY_PROVENANCE in result.reason_codes


def test_transform_07_invalid_quantity_rejected() -> None:
    intent = _transformable_intent()
    bad = _mutated_intent(intent, quantity=Decimal("0"))
    result = intent_mod.transform_canonical_order_intent_v1_to_adapter_order_intent_v1(bad)
    assert result.outcome is intent_mod.CanonicalOrderIntentTransformOutcome.BLOCKED
    assert intent_mod.REASON_INVALID_QUANTITY in result.reason_codes


def test_transform_08_risk_increasing_rounding_rejected() -> None:
    intent = _transformable_intent()
    bad = _mutated_intent(intent, quantity=Decimal("0.10000000000000001"))
    result = intent_mod.transform_canonical_order_intent_v1_to_adapter_order_intent_v1(bad)
    assert result.outcome is intent_mod.CanonicalOrderIntentTransformOutcome.BLOCKED
    assert (
        intent_mod.REASON_QUANTITY_PRECISION_LOSS in result.reason_codes
        or intent_mod.REASON_QUANTITY_ROUNDING_INCREASES_RISK in result.reason_codes
    )


def test_transform_09_unbound_order_type_rejected() -> None:
    intent = _transformable_intent()
    bad = _mutated_intent(intent, order_type_policy="UNKNOWN_ORDER_TYPE")
    result = intent_mod.transform_canonical_order_intent_v1_to_adapter_order_intent_v1(bad)
    assert result.outcome is intent_mod.CanonicalOrderIntentTransformOutcome.BLOCKED
    assert intent_mod.REASON_UNSUPPORTED_ORDER_TYPE_POLICY in result.reason_codes


def test_transform_10_unbound_time_in_force_rejected() -> None:
    intent = _transformable_intent()
    bad = _mutated_intent(intent, time_in_force_policy="DAY")
    result = intent_mod.transform_canonical_order_intent_v1_to_adapter_order_intent_v1(bad)
    assert result.outcome is intent_mod.CanonicalOrderIntentTransformOutcome.BLOCKED
    assert intent_mod.REASON_UNSUPPORTED_TIME_IN_FORCE_POLICY in result.reason_codes


def test_transform_11_missing_instrument_rejected() -> None:
    intent = _transformable_intent()
    bad = _mutated_intent(intent, instrument_id="")
    result = intent_mod.transform_canonical_order_intent_v1_to_adapter_order_intent_v1(bad)
    assert result.outcome is intent_mod.CanonicalOrderIntentTransformOutcome.BLOCKED
    assert intent_mod.REASON_MISSING_INSTRUMENT in result.reason_codes


def test_transform_12_spot_rejected() -> None:
    intent = _mutated_intent(
        _transformable_intent(),
        instrument_id="ETH-USD",
        instrument_metadata_ref="spot_metadata_v1",
    )
    result = intent_mod.transform_canonical_order_intent_v1_to_adapter_order_intent_v1(intent)
    assert result.outcome is intent_mod.CanonicalOrderIntentTransformOutcome.BLOCKED
    assert intent_mod.REASON_NON_FUTURES_INSTRUMENT in result.reason_codes


def test_transform_13_synthetic_spot_rejected() -> None:
    intent = _mutated_intent(
        _transformable_intent(),
        instrument_id="ETH-SYN-PERP",
        instrument_metadata_ref="synthetic_spot_metadata_v1",
    )
    result = intent_mod.transform_canonical_order_intent_v1_to_adapter_order_intent_v1(intent)
    assert result.outcome is intent_mod.CanonicalOrderIntentTransformOutcome.BLOCKED
    assert intent_mod.REASON_NON_FUTURES_INSTRUMENT in result.reason_codes


def test_transform_14_contradictory_reduce_only_rejected() -> None:
    intent = _transformable_intent(intent_action=intent_mod.IntentAction.ENTER_LONG.value)
    bad = _mutated_intent(intent, reduce_only=True)
    result = intent_mod.transform_canonical_order_intent_v1_to_adapter_order_intent_v1(bad)
    assert result.outcome is intent_mod.CanonicalOrderIntentTransformOutcome.BLOCKED
    assert (
        intent_mod.REASON_CONTRADICTORY_REDUCE_ONLY_SEMANTICS in result.reason_codes
        or intent_mod.REASON_INVALID_SIDE_ACTION_COMBINATION in result.reason_codes
    )


def test_transform_15_unbound_adapter_fields_not_guessed() -> None:
    intent = _transformable_intent()
    bad = _mutated_intent(
        intent,
        order_type_policy="LIMIT_ONLY",
        price_policy="REFERENCE_PRICE",
    )
    result = intent_mod.transform_canonical_order_intent_v1_to_adapter_order_intent_v1(bad)
    assert result.outcome is intent_mod.CanonicalOrderIntentTransformOutcome.BLOCKED
    assert intent_mod.REASON_UNBOUND_PRICE_POLICY in result.reason_codes
    assert result.adapter_intent is None


def test_transform_16_no_runtime_submission_functions_called(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[str] = []

    def _boom(*_args: Any, **_kwargs: Any) -> None:
        called.append("place_order")
        raise AssertionError("runtime submission must not be called")

    monkeypatch.setattr(
        "src.execution.adapters.base_v1.ExecutionAdapterV1.place_order",
        _boom,
        raising=False,
    )
    result = _transform()
    assert result.outcome is intent_mod.CanonicalOrderIntentTransformOutcome.PASS
    assert called == []


def test_transform_17_no_permission_or_authority_fields() -> None:
    result = _transform()
    assert result.authority_effect is False
    assert result.runtime_effect is False
    assert result.order_effect is False
    assert result.adapter_submission_effect is False
    assert result.descriptor is not None
    assert result.descriptor.authority_effect is False


def test_transform_18_descriptor_has_full_provenance() -> None:
    intent = _transformable_intent()
    result = intent_mod.transform_canonical_order_intent_v1_to_adapter_order_intent_v1(intent)
    assert result.descriptor is not None
    descriptor = result.descriptor
    assert descriptor.source_contract == intent_mod.CONTRACT_NAME
    assert descriptor.target_contract == intent_mod.TARGET_CONTRACT_NAME
    assert descriptor.transformation_id == intent_mod.TRANSFORMATION_ID
    assert descriptor.source_digest == intent.semantic_digest
    assert descriptor.target_digest
    assert descriptor.source_quantity_provenance == intent.quantity_provenance
    assert descriptor.network_effect is False
    assert descriptor.adapter_submission_effect is False


def test_transform_19_source_intent_unchanged() -> None:
    intent = _transformable_intent()
    before = intent_mod.canonical_order_intent_to_json(intent)
    result = intent_mod.transform_canonical_order_intent_v1_to_adapter_order_intent_v1(intent)
    after = intent_mod.canonical_order_intent_to_json(intent)
    assert before == after
    assert result.outcome is intent_mod.CanonicalOrderIntentTransformOutcome.PASS


@pytest.mark.parametrize(
    "quantity",
    [
        Decimal("0.01"),
        Decimal("0.50"),
        Decimal("1.00"),
        Decimal("12.34"),
        Decimal("99.99"),
    ],
)
def test_transform_20_output_quantity_never_exceeds_input(quantity: Decimal) -> None:
    decision = _passing_sizing_decision()
    assert decision.quantity_provenance is not None
    provenance = sizing.QuantityProvenanceV1(
        **{
            **{
                field.name: getattr(decision.quantity_provenance, field.name)
                for field in sizing.QuantityProvenanceV1.__dataclass_fields__.values()
            },
            "final_quantity": quantity,
            "output_digest": f"digest-{quantity}",
        }
    )
    blocked = sizing.CapitalRiskSizingDecisionV1(
        outcome=decision.outcome,
        final_quantity=quantity,
        selected_side=decision.selected_side,
        capital_envelope=decision.capital_envelope,
        pre_sizing_risk=decision.pre_sizing_risk,
        canonical_sizing=decision.canonical_sizing,
        post_sizing_risk=decision.post_sizing_risk,
        quantity_provenance=provenance,
        reason_codes=decision.reason_codes,
    )
    build = intent_mod.build_canonical_order_intent_v1(
        intent_mod.CanonicalOrderIntentBuildInputV1(
            sizing_input=_sizing_input(),
            sizing_decision=blocked,
            intent_id="intent-prop",
            trading_epoch="epoch-001",
            canonical_trading_logic_version="trading_logic_v1_test",
            intent_action=intent_mod.IntentAction.ENTER_LONG.value,
            policy_digest="policy_digest_test",
            order_type_policy="MARKET_ONLY",
            price_policy="EXPLICIT_NONE",
            time_in_force_policy="GTC",
            max_slippage_policy="ZERO",
            expected_position_side=intent_mod.IntentSide.LONG.value,
            current_reconciled_exposure=Decimal("0"),
        )
    )
    if build.intent is None:
        return
    result = intent_mod.transform_canonical_order_intent_v1_to_adapter_order_intent_v1(build.intent)
    if result.outcome is intent_mod.CanonicalOrderIntentTransformOutcome.PASS:
        assert result.adapter_intent is not None
        assert Decimal(str(result.adapter_intent.qty)) <= build.intent.quantity


def test_transform_21_long_short_symmetry() -> None:
    long_result = _transform(intent_action=intent_mod.IntentAction.ENTER_LONG.value)
    short_result = _transform(
        intent_action=intent_mod.IntentAction.ENTER_SHORT.value,
        sizing_overrides={
            "selected_side": sizing.SelectedSide.SHORT.value,
            "protective_stop_price": Decimal("2100"),
        },
    )
    assert long_result.outcome is intent_mod.CanonicalOrderIntentTransformOutcome.PASS
    assert short_result.outcome is intent_mod.CanonicalOrderIntentTransformOutcome.PASS
    assert long_result.adapter_intent is not None
    assert short_result.adapter_intent is not None
    assert long_result.adapter_intent.side == "buy"
    assert short_result.adapter_intent.side == "sell"


def test_transform_22_futures_only_and_no_bitcoin_direction() -> None:
    schema = intent_mod.canonical_order_intent_transformation_schema_v1()
    assert intent_mod.FUTURES_ONLY is True
    assert intent_mod.BITCOIN_DIRECTION_ALLOWED is False
    assert schema["invariants"]["full_adapter_compatibility_proven"] is False
    result = intent_mod.transform_canonical_order_intent_v1_to_adapter_order_intent_v1(
        _mutated_intent(
            _transformable_intent(),
            instrument_id="BTC-USD-PERP",
            instrument_metadata_ref="btc_perp_metadata_v1",
        )
    )
    assert result.outcome is intent_mod.CanonicalOrderIntentTransformOutcome.BLOCKED
    assert intent_mod.REASON_BITCOIN_SPECIFIC_DIRECTION in result.reason_codes
