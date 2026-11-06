"""Boundary guards: forbidden effects must remain false."""

from __future__ import annotations

from typing import Any

from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1 import (
    constants_v1 as C,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.models_v1 import (
    InputAuthorityErrorV1,
)


def assert_forbidden_effects_remain_false() -> dict[str, Any]:
    """Fail closed if any forbidden activation / authority effect is true."""
    checks = {
        "INPUT_AUTHORITY": C.INPUT_AUTHORITY,
        "RUNTIME_IMPLEMENTED": C.RUNTIME_IMPLEMENTED,
        "PRODUCTIVE_ACTIVATION": C.PRODUCTIVE_ACTIVATION,
        "PRODUCTIVE_CALIBRATION_AUTHORIZED": C.PRODUCTIVE_CALIBRATION_AUTHORIZED,
        "RESULTV1_MAPPING_AUTHORIZED": C.RESULTV1_MAPPING_AUTHORIZED,
        "CORE_LOGIC_CHANGE": C.CORE_LOGIC_CHANGE,
        "LIVE_ORDERS": C.LIVE_ORDERS,
        "TESTNET_ORDERS": C.TESTNET_ORDERS,
        "PAPER_EXCHANGE_ORDERS": C.PAPER_EXCHANGE_ORDERS,
        "EXCHANGE_CREDENTIAL_USE": C.EXCHANGE_CREDENTIAL_USE,
        "REAL_CAPITAL_MOVEMENT": C.REAL_CAPITAL_MOVEMENT,
        "OWNER_RATIFIED_INPUT_AUTHORITY": C.OWNER_RATIFIED_INPUT_AUTHORITY,
    }
    for name, value in checks.items():
        if value:
            raise InputAuthorityErrorV1(f"FORBIDDEN_EFFECT_TRUE:{name}")
    if C.PRODUCTIVE_NUMERIC_VALUES_SET != 0:
        raise InputAuthorityErrorV1("FORBIDDEN_PRODUCTIVE_NUMERIC_VALUES_SET_NONZERO")
    if C.DASHBOARD_AUTHORITY_EFFECT != "NONE":
        raise InputAuthorityErrorV1("FORBIDDEN_DASHBOARD_AUTHORITY_EFFECT")
    if not C.O4_UNCHANGED:
        raise InputAuthorityErrorV1("FORBIDDEN_O4_MUTATION_CLAIM")
    if C.AUTHORITY_SURFACE != "B":
        raise InputAuthorityErrorV1("AUTHORITY_SURFACE_MUST_BE_B")
    if C.CANDLE_MARK_TRADE_EQUIVALENCE != "FORBIDDEN":
        raise InputAuthorityErrorV1("CANDLE_MARK_TRADE_EQUIVALENCE_MUST_REMAIN_FORBIDDEN")
    return {
        "forbidden_effects_false": True,
        "productive_numeric_values_set": C.PRODUCTIVE_NUMERIC_VALUES_SET,
        "authority_surface": C.AUTHORITY_SURFACE,
        "o4_unchanged": C.O4_UNCHANGED,
        "dashboard_authority_effect": C.DASHBOARD_AUTHORITY_EFFECT,
        "sole_trading_authority": C.SOLE_TRADING_AUTHORITY,
        "arithmetic_kernel_path": C.ARITHMETIC_KERNEL_PATH,
        "sequence_survival_metrics_producer": C.SEQUENCE_SURVIVAL_METRICS_PRODUCER,
        "sequence_survival_metrics_shape": C.SEQUENCE_SURVIVAL_METRICS_SHAPE,
    }


def assert_source_not_forbidden(source_id: str) -> None:
    token = str(source_id or "").strip().lower()
    for forbidden in C.FORBIDDEN_AUTHORITY_SOURCES:
        if forbidden.lower() in token:
            raise InputAuthorityErrorV1(f"FORBIDDEN_SOURCE_AUTHORITY:{forbidden}")
