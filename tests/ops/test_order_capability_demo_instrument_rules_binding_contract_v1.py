"""Offline tests for order_capability_demo_instrument_rules_binding_contract_v1.

Class-4 scoped: no network, credentials, orders, or Testnet execute.
"""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_contract_v0 import DEFAULT_INSTRUMENT
from src.ops.order_capability_demo_instrument_rules_binding_contract_v1 import (
    ALLOWED_CREDENTIAL_CLASS,
    AUTHORITY_IMPACT,
    BLOCKER_MIN_SIZE_NOT_VERIFIED_OFFLINE,
    DemoInstrumentOfflineRulesBound,
    DemoInstrumentRulesBindingError,
    DemoInstrumentRulesBindingVerdictKind,
    FORBIDDEN_SERIALIZATION_KEYS,
    PACKAGE_MARKER,
    REASON_CAP_FEASIBILITY_INPUT_MISSING,
    REASON_CREDENTIAL_CLASS_REJECTED,
    REASON_DEMO_HOST_MISMATCH,
    REASON_FORBIDDEN_ENDPOINT_BATCHORDER,
    REASON_FORBIDDEN_ENDPOINT_CANCELALLORDERS,
    REASON_INFEASIBLE_UNDER_CAP_ENVELOPE,
    REASON_LIVE_HOST_REJECTED,
    REASON_MISSING_INSTRUMENT,
    REASON_OFFLINE_RULES_NOT_BOUND,
    REASON_SECRET_MATERIAL_REJECTED,
    REASON_UNSAFE_AUTHORITY_FLAGS,
    REQUIRED_DEMO_HOST,
    OrderCapabilityDemoInstrumentRulesBindingInput,
    default_order_capability_demo_instrument_rules_binding_input,
    evaluate_order_capability_demo_instrument_rules_binding,
    reject_secret_like_mapping,
    serialize_order_capability_demo_instrument_rules_binding_result,
    validate_order_capability_demo_instrument_rules_binding_result,
)

CONTRACT_MODULE = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "ops"
    / "order_capability_demo_instrument_rules_binding_contract_v1.py"
)

TEST_PACKAGE_MARKER = "ORDER_CAPABILITY_DEMO_INSTRUMENT_RULES_BINDING_CONTRACT_V1_TEST=true"
OPERATOR_GO_BINDING = (
    "GO_ORDER_CAPABILITY_DEMO_INSTRUMENT_RULES_BINDING_CONTRACT_IMPL_TESTS_ONLY_NO_RUN_V1"
)


def _complete_offline_rules(**overrides: object) -> DemoInstrumentOfflineRulesBound:
    base = {
        "min_size": Decimal("0.001"),
        "qty_step": Decimal("0.001"),
        "price_tick": Decimal("0.5"),
        "qty_precision": 3,
        "price_precision": 1,
        "min_notional": None,
        "offline_bound": True,
        "source_ref": "synthetic_offline_fixture_only_not_exchange_truth",
    }
    base.update(overrides)
    return DemoInstrumentOfflineRulesBound(**base)


def _valid_input(**overrides: object) -> OrderCapabilityDemoInstrumentRulesBindingInput:
    base = {
        "demo_host": REQUIRED_DEMO_HOST,
        "credential_class": ALLOWED_CREDENTIAL_CLASS,
        "instrument": DEFAULT_INSTRUMENT,
        "offline_rules": _complete_offline_rules(),
        "cap_max_notional_eur": Decimal("10.0"),
        "reference_price_usd": Decimal("100.0"),
        "fx_rate_usd_per_eur": Decimal("1.0"),
        "cancelallorders": False,
        "batchorder": False,
        "execute_authorized": False,
        "order_authorized": False,
        "cancel_authorized": False,
    }
    base.update(overrides)
    return OrderCapabilityDemoInstrumentRulesBindingInput(**base)


def test_package_marker_present() -> None:
    assert TEST_PACKAGE_MARKER
    assert OPERATOR_GO_BINDING
    assert PACKAGE_MARKER in CONTRACT_MODULE.read_text(encoding="utf-8")


def test_default_missing_rules_fail_closed() -> None:
    result = evaluate_order_capability_demo_instrument_rules_binding(
        default_order_capability_demo_instrument_rules_binding_input()
    )
    assert result.verdict == DemoInstrumentRulesBindingVerdictKind.FAIL_CLOSED
    assert result.min_size_verified_offline is False
    assert result.blocker_min_size_not_verified_offline is True
    assert BLOCKER_MIN_SIZE_NOT_VERIFIED_OFFLINE in result.blockers
    assert result.execute_authorized_now is False
    assert result.order_authorized_now is False
    assert result.cancel_authorized_now is False
    validate_order_capability_demo_instrument_rules_binding_result(result)


def test_demo_host_required_accepts_demo_futures() -> None:
    result = evaluate_order_capability_demo_instrument_rules_binding(
        _valid_input(demo_host="https://demo-futures.kraken.com/derivatives/api/v3")
    )
    assert REASON_DEMO_HOST_MISMATCH not in result.reason_codes
    assert result.verdict == DemoInstrumentRulesBindingVerdictKind.BINDING_SATISFIED_FOR_DRY_ONLY


@pytest.mark.parametrize(
    "host",
    [
        "futures.kraken.com",
        "live-futures.kraken.com",
        "prod.kraken.com",
        "",
    ],
)
def test_live_prod_host_rejected(host: str) -> None:
    result = evaluate_order_capability_demo_instrument_rules_binding(_valid_input(demo_host=host))
    assert result.verdict == DemoInstrumentRulesBindingVerdictKind.FAIL_CLOSED
    assert REASON_DEMO_HOST_MISMATCH in result.reason_codes or REASON_LIVE_HOST_REJECTED in result.reason_codes


def test_credential_class_kraken_futures_demo_only_accepted() -> None:
    result = evaluate_order_capability_demo_instrument_rules_binding(_valid_input())
    assert REASON_CREDENTIAL_CLASS_REJECTED not in result.reason_codes


@pytest.mark.parametrize(
    "credential_class",
    [
        "kraken_futures_live",
        "kraken_spot",
        "live",
        "production",
        "spot_only",
        "",
    ],
)
def test_credential_class_alternates_rejected(credential_class: str) -> None:
    result = evaluate_order_capability_demo_instrument_rules_binding(
        _valid_input(credential_class=credential_class)
    )
    assert result.verdict == DemoInstrumentRulesBindingVerdictKind.FAIL_CLOSED
    assert REASON_CREDENTIAL_CLASS_REJECTED in result.reason_codes


def test_required_instrument_rules_missing_blocks_operator_decision_prep() -> None:
    result = evaluate_order_capability_demo_instrument_rules_binding(
        _valid_input(offline_rules=_complete_offline_rules(qty_step=None, offline_bound=True))
    )
    assert result.operator_side_qty_price_decision_prep_allowed_next is False
    assert result.demo_instrument_rules_binding_prepared is False
    assert result.instrument_rules_offline_bound is False


def test_synthetic_complete_offline_bound_rules_binding_prepared_without_authority_lift() -> None:
    result = evaluate_order_capability_demo_instrument_rules_binding(_valid_input())
    assert result.verdict == DemoInstrumentRulesBindingVerdictKind.BINDING_SATISFIED_FOR_DRY_ONLY
    assert result.demo_instrument_rules_binding_prepared is True
    assert result.instrument_rules_offline_bound is True
    assert result.min_size_verified_offline is True
    assert result.cap_feasible is True
    assert result.operator_side_qty_price_decision_prep_allowed_next is True
    assert result.order_authorized_now is False
    assert result.cancel_authorized_now is False
    assert result.execute_authorized_now is False
    assert result.demo_mutation_execute_allowed_now is False
    validate_order_capability_demo_instrument_rules_binding_result(result)


def test_cap_infeasible_under_min_size_times_reference_price() -> None:
    result = evaluate_order_capability_demo_instrument_rules_binding(
        _valid_input(
            offline_rules=_complete_offline_rules(min_size=Decimal("0.01")),
            reference_price_usd=Decimal("100001.0"),
            cap_max_notional_eur=Decimal("10.0"),
            fx_rate_usd_per_eur=Decimal("1.08"),
        )
    )
    assert result.verdict == DemoInstrumentRulesBindingVerdictKind.INFEASIBLE_UNDER_CAP
    assert REASON_INFEASIBLE_UNDER_CAP_ENVELOPE in result.reason_codes
    assert result.cap_feasible is False
    assert result.operator_side_qty_price_decision_prep_allowed_next is False


def test_cap_infeasible_when_min_notional_exceeds_cap() -> None:
    result = evaluate_order_capability_demo_instrument_rules_binding(
        _valid_input(
            offline_rules=_complete_offline_rules(min_notional=Decimal("500.0")),
            reference_price_usd=Decimal("1.0"),
            cap_max_notional_eur=Decimal("10.0"),
            fx_rate_usd_per_eur=Decimal("1.0"),
        )
    )
    assert result.verdict == DemoInstrumentRulesBindingVerdictKind.INFEASIBLE_UNDER_CAP
    assert REASON_INFEASIBLE_UNDER_CAP_ENVELOPE in result.reason_codes


def test_no_secret_material_invariant() -> None:
    result = evaluate_order_capability_demo_instrument_rules_binding(_valid_input())
    data = serialize_order_capability_demo_instrument_rules_binding_result(result)
    assert data["value_redacted"] is True
    assert data["no_secret_material"] is True
    for key in data:
        assert key.lower() not in FORBIDDEN_SERIALIZATION_KEYS
    secret_reasons = reject_secret_like_mapping({"api_key": "redacted"})
    assert REASON_SECRET_MATERIAL_REJECTED in secret_reasons


def test_authority_impact_always_no_authority_change() -> None:
    default_result = evaluate_order_capability_demo_instrument_rules_binding(
        default_order_capability_demo_instrument_rules_binding_input()
    )
    ok_result = evaluate_order_capability_demo_instrument_rules_binding(_valid_input())
    assert default_result.authority_impact == AUTHORITY_IMPACT
    assert ok_result.authority_impact == AUTHORITY_IMPACT


def test_cancelallorders_and_batchorder_not_allowed() -> None:
    cancel_all = evaluate_order_capability_demo_instrument_rules_binding(
        _valid_input(cancelallorders=True)
    )
    batch = evaluate_order_capability_demo_instrument_rules_binding(_valid_input(batchorder=True))
    assert REASON_FORBIDDEN_ENDPOINT_CANCELALLORDERS in cancel_all.reason_codes
    assert cancel_all.cancelallorders_allowed is False
    assert REASON_FORBIDDEN_ENDPOINT_BATCHORDER in batch.reason_codes
    assert batch.batchorder_allowed is False


def test_unsafe_authority_flags_fail_closed() -> None:
    result = evaluate_order_capability_demo_instrument_rules_binding(
        _valid_input(execute_authorized=True)
    )
    assert REASON_UNSAFE_AUTHORITY_FLAGS in result.reason_codes
    assert result.execute_authorized_now is False


def test_missing_instrument_fail_closed() -> None:
    result = evaluate_order_capability_demo_instrument_rules_binding(_valid_input(instrument=""))
    assert REASON_MISSING_INSTRUMENT in result.reason_codes


def test_offline_rules_not_bound_fail_closed() -> None:
    result = evaluate_order_capability_demo_instrument_rules_binding(
        _valid_input(offline_rules=_complete_offline_rules(offline_bound=False))
    )
    assert REASON_OFFLINE_RULES_NOT_BOUND in result.reason_codes
    assert result.min_size_verified_offline is False


def test_cap_feasibility_input_missing_when_reference_price_absent() -> None:
    result = evaluate_order_capability_demo_instrument_rules_binding(
        _valid_input(reference_price_usd=None)
    )
    assert REASON_CAP_FEASIBILITY_INPUT_MISSING in result.reason_codes
    assert result.cap_feasible is False


def test_deterministic_output_same_input() -> None:
    inp = _valid_input()
    first = evaluate_order_capability_demo_instrument_rules_binding(inp)
    second = evaluate_order_capability_demo_instrument_rules_binding(inp)
    assert first == second


def test_machine_summary_shape_stable() -> None:
    result = evaluate_order_capability_demo_instrument_rules_binding(_valid_input())
    data = serialize_order_capability_demo_instrument_rules_binding_result(result)
    required_keys = {
        "schema_version",
        "contract_marker",
        "verdict",
        "reason_codes",
        "blockers",
        "violations",
        "demo_instrument_rules_binding_prepared",
        "instrument_rules_offline_bound",
        "min_size_verified_offline",
        "cap_feasible",
        "operator_side_qty_price_decision_prep_allowed_next",
        "demo_mutation_execute_allowed_now",
        "order_authorized_now",
        "cancel_authorized_now",
        "execute_authorized_now",
        "authority_impact",
        "blocker_min_size_not_verified_offline",
        "value_redacted",
        "no_secret_material",
    }
    assert required_keys.issubset(data.keys())


def test_validate_result_raises_on_tampered_authority() -> None:
    ok = evaluate_order_capability_demo_instrument_rules_binding(_valid_input())
    tampered = OrderCapabilityDemoInstrumentRulesBindingInput  # noqa: F841
    bad = type(ok)(
        verdict=ok.verdict,
        reason_codes=ok.reason_codes,
        blockers=ok.blockers,
        violations=ok.violations,
        demo_instrument_rules_binding_prepared=ok.demo_instrument_rules_binding_prepared,
        instrument_rules_offline_bound=ok.instrument_rules_offline_bound,
        min_size_verified_offline=ok.min_size_verified_offline,
        cap_feasible=ok.cap_feasible,
        operator_side_qty_price_decision_prep_allowed_next=ok.operator_side_qty_price_decision_prep_allowed_next,
        demo_mutation_execute_allowed_now=True,
        order_authorized_now=ok.order_authorized_now,
        cancel_authorized_now=ok.cancel_authorized_now,
        execute_authorized_now=ok.execute_authorized_now,
        authority_impact=ok.authority_impact,
        blocker_min_size_not_verified_offline=ok.blocker_min_size_not_verified_offline,
        value_redacted=ok.value_redacted,
        no_secret_material=ok.no_secret_material,
        cancelallorders_allowed=ok.cancelallorders_allowed,
        batchorder_allowed=ok.batchorder_allowed,
    )
    with pytest.raises(DemoInstrumentRulesBindingError):
        validate_order_capability_demo_instrument_rules_binding_result(bad)


def test_no_execution_risk_layer_imports() -> None:
    tree = ast.parse(CONTRACT_MODULE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("src.execution")
                assert not alias.name.startswith("src.risk_layer")
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("src.execution")
            assert not node.module.startswith("src.risk_layer")
