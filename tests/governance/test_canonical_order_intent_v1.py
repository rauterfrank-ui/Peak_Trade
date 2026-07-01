"""Contract tests for offline canonical order intent v1 (RUNBOOK STEP 29Q)."""

from __future__ import annotations

import ast
import importlib
import inspect
import json
from decimal import Decimal
from pathlib import Path

import pytest

import src.governance.canonical_order_intent_v1 as intent_mod
import src.governance.capital_risk_sizing_v1 as sizing

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
        "order_type_policy": "LIMIT_ONLY",
        "price_policy": "REFERENCE_PRICE",
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
