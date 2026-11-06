"""A–G funding-scope dimensions for R12 EG-I44 (read-only).

Research funding is never productive G16 proof. Field presence is not
accounting application.
"""

from __future__ import annotations

from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.models_v1 import (
    ContractItemStatus,
    FundingDimensionRowV1,
    R12EgI44FundError,
)

_INP = ContractItemStatus.IMPLEMENTED_NOT_PROVEN
_MISS = ContractItemStatus.MISSING
_NRA = ContractItemStatus.NOT_REQUIRED_UNTIL_ACTIVATION
_CB = ContractItemStatus.CLOSED_BOUNDARY

REQUIRED_DIMENSION_IDS = (
    "FUNDING_RATE_OBSERVATION",
    "EXPECTED_FUNDING_ESTIMATE",
    "ACTUAL_FUNDING_PAYMENT",
    "FUNDING_PAID_OR_RECEIVED",
    "FUNDING_PNL",
    "RESEARCH_FUNDING_FEATURE",
    "PRODUCTIVE_ACCOUNTING_CLAIM",
)

FUNDING_DIMENSIONS: tuple[FundingDimensionRowV1, ...] = (
    FundingDimensionRowV1(
        dimension_id="FUNDING_RATE_OBSERVATION",
        current_producer=(
            "research cross_sectional funding_rate panels; CanonicalMarketContextV1.funding_rate; "
            "OKX research staging scripts"
        ),
        current_consumer="research ranking/score; CMC context field; not Cap3.1",
        current_runtime_reachability=(
            "research YES; CMC field populated including hardcoded 0.0001 in wallclock bridge; "
            "no productive funding-accounting consumer"
        ),
        current_authority_effect="NONE",
        current_accounting_effect="NONE",
        current_evidence="research fixtures/panels; not dedicated G16 pack",
        current_tests="tests/research/*funding*; tests/backtest/test_funding_model_v1.py",
        claim_allowed_today=False,
        g16_relevance="INPUT_IF_ACTIVATED_NOT_PROOF",
        status=_INP,
    ),
    FundingDimensionRowV1(
        dimension_id="EXPECTED_FUNDING_ESTIMATE",
        current_producer=(
            "src.execution.paper.futures_accounting.funding_payment_quote; "
            "src.backtest.funding_model_v1"
        ),
        current_consumer="unit tests; backtest economic viability; not Cap3.1",
        current_runtime_reachability="helper/backtest YES; productive accounting engine NO",
        current_authority_effect="NONE",
        current_accounting_effect="NONE",
        current_evidence="library/backtest tests; not venue-actual",
        current_tests="tests/execution/paper/test_futures_accounting*.py; test_funding_model_v1.py",
        claim_allowed_today=False,
        g16_relevance="REQUIRED_INPUT_TO_FUTURE_PACK",
        status=_INP,
    ),
    FundingDimensionRowV1(
        dimension_id="ACTUAL_FUNDING_PAYMENT",
        current_producer="NONE_PRODUCTIVE",
        current_consumer="NONE_PRODUCTIVE",
        current_runtime_reachability="no venue/account funding-event ingest on Cap3.1 path",
        current_authority_effect="NONE",
        current_accounting_effect="NONE",
        current_evidence="absent dedicated actual-payment evidence",
        current_tests="none_as_productive_actual_event",
        claim_allowed_today=False,
        g16_relevance="REQUIRED_FOR_G16_CLOSEOUT",
        status=_MISS,
    ),
    FundingDimensionRowV1(
        dimension_id="FUNDING_PAID_OR_RECEIVED",
        current_producer=(
            "Master §11.14 live-metrics list names the field; snapshot alias funding_paid="
            "position.funding_pnl; Cap3.1 does not apply payments"
        ),
        current_consumer="observability requirement when live metrics apply; no proven live consumer",
        current_runtime_reachability="metric name listed; productive application absent",
        current_authority_effect="NONE",
        current_accounting_effect="NONE",
        current_evidence="none_productive",
        current_tests="kernel helper tests only",
        claim_allowed_today=False,
        g16_relevance="PRIMARY_G16_CLAIM_SURFACE",
        status=_NRA,
    ),
    FundingDimensionRowV1(
        dimension_id="FUNDING_PNL",
        current_producer="FuturesPosition.funding_pnl field; Cap3.1 persists/copies default 0",
        current_consumer="Cap3.1 portfolio state JSON; snapshot funding_paid alias",
        current_runtime_reachability="field YES; apply_funding_payment not called by Cap3.1",
        current_authority_effect="NONE",
        current_accounting_effect="FIELD_ONLY_NOT_APPLICATION",
        current_evidence="field roundtrip; typically Decimal 0; not G16",
        current_tests="Cap3.1 persistence tests; kernel apply tests unused by engine",
        claim_allowed_today=False,
        g16_relevance="FIELD_PRESENT_DOES_NOT_PROVE_ACCOUNTING",
        status=_CB,
    ),
    FundingDimensionRowV1(
        dimension_id="RESEARCH_FUNDING_FEATURE",
        current_producer="src/research/cross_sectional_funding_rate_* ; backtest funding_model_v1",
        current_consumer="research ranking/orchestration only",
        current_runtime_reachability="research scripts YES; trading/accounting authority NO",
        current_authority_effect="NONE",
        current_accounting_effect="NONE",
        current_evidence="research bindings; explicitly non-proof",
        current_tests="tests/research/*funding*",
        claim_allowed_today=False,
        g16_relevance="NAMING_COLLISION_RISK_ONLY_NOT_PROOF",
        status=_CB,
    ),
    FundingDimensionRowV1(
        dimension_id="PRODUCTIVE_ACCOUNTING_CLAIM",
        current_producer="NONE",
        current_consumer="claim surfaces fail-closed by Master G16",
        current_runtime_reachability="claims blocked",
        current_authority_effect="NONE",
        current_accounting_effect="NONE",
        current_evidence="G16 INSUFFICIENT_EVIDENCE",
        current_tests="this overlay fail-closed verifier",
        claim_allowed_today=False,
        g16_relevance="THE_G16_GATE",
        status=_NRA,
    ),
)


def require_dimension(dimension_id: str) -> FundingDimensionRowV1:
    for row in FUNDING_DIMENSIONS:
        if row.dimension_id == dimension_id:
            return row
    raise R12EgI44FundError(f"unknown_funding_dimension:{dimension_id}")
