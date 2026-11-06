"""Boundary guards for Surface-B regime-coverage producer v1."""

from __future__ import annotations

from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1 import (
    constants_v1 as C,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.models_v1 import (
    RegimeCoverageProducerErrorV1,
)


def assert_forbidden_effects_remain_false_v1() -> None:
    if C.INPUT_AUTHORITY:
        raise RegimeCoverageProducerErrorV1("INPUT_AUTHORITY_MUST_REMAIN_FALSE")
    if C.RUNTIME_IMPLEMENTED:
        raise RegimeCoverageProducerErrorV1("RUNTIME_IMPLEMENTED_MUST_REMAIN_FALSE")
    if C.RAW_INPUT_PACK_CREATED:
        raise RegimeCoverageProducerErrorV1("RAW_INPUT_PACK_CREATED_MUST_REMAIN_FALSE")
    if C.CAMPAIGN_STARTED:
        raise RegimeCoverageProducerErrorV1("CAMPAIGN_STARTED_MUST_REMAIN_FALSE")
    if C.PRODUCTIVE_NUMERIC_VALUES_SET != 0:
        raise RegimeCoverageProducerErrorV1("PRODUCTIVE_NUMERIC_VALUES_MUST_REMAIN_ZERO")
    if C.REGIME_COVERAGE_PRODUCER_AVAILABLE:
        raise RegimeCoverageProducerErrorV1("REGIME_COVERAGE_PRODUCER_AVAILABLE_MUST_REMAIN_FALSE")
    if C.REGIME_COVERAGE_STATUS != "SEMANTICALLY_UNRESOLVED":
        raise RegimeCoverageProducerErrorV1("REGIME_COVERAGE_STATUS_MUST_REMAIN_UNRESOLVED")
    if C.DASHBOARD_AUTHORITY_EFFECT != "NONE":
        raise RegimeCoverageProducerErrorV1("DASHBOARD_AUTHORITY_MUST_BE_NONE")
    if C.EXISTING_PRODUCERS_ELEVATED:
        raise RegimeCoverageProducerErrorV1("EXISTING_PRODUCERS_MUST_NOT_BE_ELEVATED")
    if C.TRADING_LOGIC_CHANGED:
        raise RegimeCoverageProducerErrorV1("TRADING_LOGIC_MUST_REMAIN_UNCHANGED")
    if C.ORDERS_TESTNET_LIVE_PAPER_EFFECTS:
        raise RegimeCoverageProducerErrorV1("ORDERS_TESTNET_LIVE_PAPER_MUST_REMAIN_FALSE")
    if C.EXCHANGE_CREDENTIAL_EFFECTS:
        raise RegimeCoverageProducerErrorV1("EXCHANGE_CREDENTIAL_EFFECTS_MUST_REMAIN_FALSE")
    if C.INVENT_THRESHOLDS or C.INVENT_LOOKBACKS or C.INVENT_COVERAGE_COUNTS:
        raise RegimeCoverageProducerErrorV1("INVENTION_FLAGS_MUST_REMAIN_FALSE")
    if C.PRODUCTIVE_EMISSION:
        raise RegimeCoverageProducerErrorV1("PRODUCTIVE_EMISSION_MUST_REMAIN_FALSE")


def assert_source_not_forbidden_v1(token: str) -> None:
    text = str(token or "").strip().lower()
    for forbidden in C.FORBIDDEN_EXISTING_PRODUCER_TOKENS:
        if forbidden.lower() in text:
            raise RegimeCoverageProducerErrorV1(
                f"EXISTING_PRODUCER_ELEVATION_FORBIDDEN:{forbidden}"
            )
