"""CURRENT_PRODUCTIVE P01 policy replacement v1.

Owner-GO CURRENT_PRODUCTIVE_P01_POLICY_REPLACEMENT_AND_29P_CONTINUATION_V1
ratifies a new CURRENT_PRODUCTIVE policy: P01 DOES_NOT_APPLY.

This is architectural redundancy, not historical absence. Missing/UNKNOWN
directives remain UNKNOWN_FAIL_CLOSED. Venue fields are not P01 authority.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_P01_INDEPENDENT_SAFETY_FUNCTION,
    CURRENT_PRODUCTIVE_P01_POLICY_BINDING_PRESENT,
    CURRENT_PRODUCTIVE_P01_POLICY_CREATED,
    CURRENT_PRODUCTIVE_P01_POLICY_DECISION,
    CURRENT_PRODUCTIVE_P01_POLICY_DECISION_BASIS,
    CURRENT_PRODUCTIVE_P01_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT,
    P01_RUNTIME_INSTANCE_PRESENT,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    P01_FACT_ID,
    CurrentProductiveP01ReductionFactV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.governed_p01_reduction_directive_v1 import (
    STATE_DOES_NOT_APPLY,
    GovernedP01ReductionDirectiveV1,
    build_governed_p01_reduction_directive_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_governed_reduction_directive_evaluator_v1 import (
    REASON_MISSING,
    P01PredicateDecisionV1,
    evaluate_p01_application_predicate_v1,
)

OWNER_GO = "CURRENT_PRODUCTIVE_P01_POLICY_REPLACEMENT_AND_29P_CONTINUATION_V1"
POLICY_ID = "CURRENT_PRODUCTIVE_P01_POLICY_DOES_NOT_APPLY_V1"
DIRECTIVE_ID = POLICY_ID
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
EVIDENCE_REF = (
    "OWNER_GO=CURRENT_PRODUCTIVE_P01_POLICY_REPLACEMENT_AND_29P_CONTINUATION_V1;"
    "BASIS=ARCHITECTURAL_REDUNDANCY_NOT_HISTORICAL_ABSENCE;"
    "SECTION=11.2.1.CX"
)
SOURCE_CLASS = "TYPED_GOVERNED_CURRENT_PRODUCTIVE_POLICY"
POLICY_FORMULA = "P01_CONTRIBUTION=0_BY_EXPLICIT_DOES_NOT_APPLY"
AUTHORIZED_INPUTS = "NONE_STANDING_POLICY_NOT_VENUE_DERIVED"


class CurrentProductiveP01PolicyError(ValueError):
    """Fail-closed CURRENT_PRODUCTIVE P01 policy violation."""


@dataclass(frozen=True)
class CurrentProductiveP01CoverageRowV1:
    risk_or_constraint: str
    current_owner: str
    already_reflected_in_availeq: str
    existing_peak_trade_gate: str
    p01_needed: str
    evidence: str


def current_productive_p01_coverage_matrix_v1() -> Tuple[CurrentProductiveP01CoverageRowV1, ...]:
    return (
        CurrentProductiveP01CoverageRowV1(
            risk_or_constraint="USDC_CROSS_MARGIN_FREE_MARGIN_NET_OF_IN_USE",
            current_owner="details[ccy=USDC].availEq",
            already_reflected_in_availeq="true",
            existing_peak_trade_gate="CU_OPTION_B_OBSERVATION_SURFACE",
            p01_needed="false",
            evidence="CU_VENUE_SEMANTICS_ALREADY_NET_OF_IN_USE_INCLUDING_OPEN_ORDERS",
        ),
        CurrentProductiveP01CoverageRowV1(
            risk_or_constraint="U04_PENDING_ORDER_RESERVATION",
            current_owner="venue_free_margin_in_use",
            already_reflected_in_availeq="true",
            existing_peak_trade_gate="U04_DO_NOT_SUBTRACT_ALREADY_NETTED",
            p01_needed="false",
            evidence="ORD_FROZEN_IS_REDUCTION_COMPONENT_NOT_P01",
        ),
        CurrentProductiveP01CoverageRowV1(
            risk_or_constraint="DEPLOYABILITY_CONSERVATISM_ON_SIZING_QUANTITY",
            current_owner="capital_risk_sizing_v1/STEP_29P",
            already_reflected_in_availeq="false",
            existing_peak_trade_gate=(
                "TOTAL_CAPITAL_LIMIT_ORDER_LIMIT_DAILY_LOSS_MAX_POSITIONS_"
                "RISK_CAP_EXPOSURE_CAP_VENUE_CAP"
            ),
            p01_needed="false",
            evidence="29P_POLICY_CAPS_OWN_CONSERVATISM_AFTER_FREE_MARGIN_INPUT",
        ),
        CurrentProductiveP01CoverageRowV1(
            risk_or_constraint="VENUE_DISCOUNTED_EQUITY_ADJEQ",
            current_owner="adjEq_forbidden",
            already_reflected_in_availeq="false",
            existing_peak_trade_gate="ADJ_EQ_KEEP_FORBIDDEN",
            p01_needed="false",
            evidence="USD_HAIRCUT_IS_NOT_USDC_FREE_MARGIN_SIZING",
        ),
        CurrentProductiveP01CoverageRowV1(
            risk_or_constraint="GENERIC_SAFETY_BUFFER",
            current_owner="not_p01_member",
            already_reflected_in_availeq="false",
            existing_peak_trade_gate="GENERIC_SAFETY_BUFFER_IS_NOT_P01_MEMBER",
            p01_needed="false",
            evidence="AK_AM_AP_REJECT_GENERIC_BUFFER_AS_P01_IDENTITY",
        ),
        CurrentProductiveP01CoverageRowV1(
            risk_or_constraint="CANARY_ENVELOPE",
            current_owner="section_11_13_5_canary",
            already_reflected_in_availeq="false",
            existing_peak_trade_gate="P01_IS_NOT_CANARY_ENVELOPE",
            p01_needed="false",
            evidence="P01M_IS_NOT_CANARY_ENVELOPE",
        ),
        CurrentProductiveP01CoverageRowV1(
            risk_or_constraint="ACCOUNT_MODE_ELIGIBILITY",
            current_owner="CURRENT_PRODUCTIVE_U01",
            already_reflected_in_availeq="false",
            existing_peak_trade_gate="U01_ACCTLV_2_FUTURES_MODE",
            p01_needed="false",
            evidence="U01_IS_ELIGIBILITY_NOT_NUMERIC_P01",
        ),
        CurrentProductiveP01CoverageRowV1(
            risk_or_constraint="FRESHNESS_RESTART_SAME_EPOCH",
            current_owner="U07_U09",
            already_reflected_in_availeq="false",
            existing_peak_trade_gate="FRESH_GET_PER_PRETRADE_DECISION_TTL_5S",
            p01_needed="false",
            evidence="FRESHNESS_IS_NOT_A_MONETARY_REDUCTION",
        ),
        CurrentProductiveP01CoverageRowV1(
            risk_or_constraint="EXPECTED_FUTURE_FEES_AS_RESERVE",
            current_owner="U06_not_current_productive_kind",
            already_reflected_in_availeq="false",
            existing_peak_trade_gate="U06_FUTURE_FEES_NOT_IN_U06",
            p01_needed="false",
            evidence=(
                "INTRODUCING_A_FEE_RESERVE_REQUIRES_OWNER_FORMULA_"
                "NOT_AUTHORIZED_AS_TODAY_P01_PURPOSE"
            ),
        ),
        CurrentProductiveP01CoverageRowV1(
            risk_or_constraint="EQUITY_STOCK_KIND_SET_RECONSTRUCTION",
            current_owner="retired_from_current_productive_sizing",
            already_reflected_in_availeq="false",
            existing_peak_trade_gate="LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE=false",
            p01_needed="false",
            evidence="CURRENT_PRODUCTIVE_QUANTITY_IS_FREE_MARGIN_NOT_EQUITY_STOCK",
        ),
    )


def _assert_policy_pins() -> None:
    if CURRENT_PRODUCTIVE_P01_POLICY_CREATED is not True:
        raise CurrentProductiveP01PolicyError("P01_POLICY_MUST_BE_CREATED")
    if CURRENT_PRODUCTIVE_P01_POLICY_DECISION != STATE_DOES_NOT_APPLY:
        raise CurrentProductiveP01PolicyError("P01_POLICY_MUST_BE_DOES_NOT_APPLY")
    if CURRENT_PRODUCTIVE_P01_POLICY_DECISION_BASIS != (
        "ARCHITECTURAL_REDUNDANCY_NOT_HISTORICAL_ABSENCE"
    ):
        raise CurrentProductiveP01PolicyError("P01_POLICY_BASIS_DRIFT")
    if CURRENT_PRODUCTIVE_P01_INDEPENDENT_SAFETY_FUNCTION is not False:
        raise CurrentProductiveP01PolicyError("P01_INDEPENDENT_SAFETY_FUNCTION_MUST_BE_FALSE")
    if CURRENT_PRODUCTIVE_P01_POLICY_BINDING_PRESENT is not True:
        raise CurrentProductiveP01PolicyError("P01_POLICY_BINDING_MUST_BE_PRESENT")
    if P01_RUNTIME_INSTANCE_PRESENT is not False:
        raise CurrentProductiveP01PolicyError(
            "RECONSTRUCTION_P01_RUNTIME_INSTANCE_MUST_REMAIN_FALSE"
        )
    if CURRENT_PRODUCTIVE_P01_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT is not False:
        raise CurrentProductiveP01PolicyError(
            "RECONSTRUCTION_P01_RUNTIME_INSTANCE_MUST_REMAIN_FALSE"
        )
    if any(row.p01_needed != FALSE_TOKEN for row in current_productive_p01_coverage_matrix_v1()):
        raise CurrentProductiveP01PolicyError("COVERAGE_MATRIX_P01_NEEDED_MUST_BE_FALSE")


def mint_current_productive_p01_does_not_apply_directive_v1() -> GovernedP01ReductionDirectiveV1:
    _assert_policy_pins()
    return build_governed_p01_reduction_directive_v1(
        directive_id=DIRECTIVE_ID,
        applicability_state=STATE_DOES_NOT_APPLY,
        evidence_ref=EVIDENCE_REF,
        authorized_reduction_amount="",
        amount_present=FALSE_TOKEN,
    )


def evaluate_current_productive_p01_policy_v1(
    directives: Sequence[GovernedP01ReductionDirectiveV1] | None = None,
) -> P01PredicateDecisionV1:
    if directives is None:
        directive = mint_current_productive_p01_does_not_apply_directive_v1()
        return evaluate_p01_application_predicate_v1((directive,))
    decision = evaluate_p01_application_predicate_v1(directives)
    if not directives:
        if decision.decision_state == STATE_DOES_NOT_APPLY:
            raise CurrentProductiveP01PolicyError("EMPTY_DIRECTIVE_MUST_NOT_BECOME_DOES_NOT_APPLY")
        return decision
    if decision.decision_state != STATE_DOES_NOT_APPLY or decision.ready != "true":
        raise CurrentProductiveP01PolicyError(
            "CURRENT_PRODUCTIVE_P01_POLICY_MUST_BE_DOES_NOT_APPLY"
        )
    return decision


def reject_missing_as_does_not_apply_v1() -> P01PredicateDecisionV1:
    decision = evaluate_p01_application_predicate_v1(())
    if decision.decision_state == STATE_DOES_NOT_APPLY:
        raise CurrentProductiveP01PolicyError("MISSING_MUST_NOT_BECOME_DOES_NOT_APPLY")
    if decision.reason_code != REASON_MISSING:
        raise CurrentProductiveP01PolicyError("MISSING_EVALUATOR_REASON_DRIFT")
    return decision


def bind_current_productive_p01_policy_fact_v1(
    *,
    bound_account_identity: str,
    bound_venue_identity: str,
    bound_td_mode: str,
    decision_epoch: str,
    observed_at_as_of: str,
    age_seconds: str,
    freshness_max_age: str,
    provenance_digest: str,
) -> CurrentProductiveP01ReductionFactV1:
    decision = evaluate_current_productive_p01_policy_v1()
    if decision.decision_state != STATE_DOES_NOT_APPLY:
        raise CurrentProductiveP01PolicyError("P01_POLICY_FACT_REQUIRES_DOES_NOT_APPLY")
    digest = str(provenance_digest or "").strip().lower()
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise CurrentProductiveP01PolicyError("P01_POLICY_FACT_PROVENANCE_INVALID")
    return CurrentProductiveP01ReductionFactV1(
        fact_id=P01_FACT_ID,
        applicability_state=STATE_DOES_NOT_APPLY,
        value="",
        settlement_currency="NONE",
        bound_account_identity=bound_account_identity,
        bound_venue_identity=bound_venue_identity,
        bound_td_mode=bound_td_mode,
        decision_epoch=decision_epoch,
        observed_at_as_of=observed_at_as_of,
        age_seconds=age_seconds,
        freshness_max_age=freshness_max_age,
        provenance_digest=digest,
        source_class=SOURCE_CLASS,
    )


def current_productive_p01_policy_pins_v1() -> Mapping[str, str]:
    _assert_policy_pins()
    return {
        "OWNER_GO": OWNER_GO,
        "POLICY_ID": POLICY_ID,
        "P01_POLICY_DECISION": CURRENT_PRODUCTIVE_P01_POLICY_DECISION,
        "P01_DECISION_BASIS": CURRENT_PRODUCTIVE_P01_POLICY_DECISION_BASIS,
        "P01_INDEPENDENT_SAFETY_FUNCTION": FALSE_TOKEN,
        "P01_FORMULA": POLICY_FORMULA,
        "P01_AUTHORIZED_INPUTS": AUTHORIZED_INPUTS,
        "P01_DOUBLE_COUNT_RISK": (
            "SUBTRACTING_P01_WOULD_DOUBLE_COUNT_29P_CAPS_OR_INVENT_RISK_APPETITE"
        ),
        "P01_LEGACY_RECONSTRUCTION_PERFORMED": FALSE_TOKEN,
        "P01_RUNTIME_INSTANCE_PRESENT": FALSE_TOKEN,
        "CURRENT_PRODUCTIVE_P01_POLICY_BINDING_PRESENT": TRUE_TOKEN,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "CONTRACT_VERSION": CONTRACT_VERSION,
    }
