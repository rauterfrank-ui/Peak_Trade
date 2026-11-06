"""Evaluate the Owner-ratified P01 reduction-directive predicate.

Closes TRUE/FALSE/UNKNOWN application rules and P01 algebra contribution
inside the existing reconstruction boundary. No productive source.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping, Sequence

from src.ops.governed_productive_account_equity_authority_producer_v1.governed_p01_reduction_directive_v1 import (
    AMOUNT_ABSENT,
    STATE_APPLIES,
    STATE_DOES_NOT_APPLY,
    STATE_UNKNOWN_FAIL_CLOSED,
    GovernedP01ReductionDirectiveError,
    GovernedP01ReductionDirectiveV1,
    build_governed_p01_reduction_directive_v1,
    parse_p01_reduction_amount_v1,
)

REASON_READY = "P01_DIRECTIVE_READY"
REASON_MISSING = "P01_DIRECTIVE_MISSING"
REASON_DUPLICATE = "P01_DIRECTIVE_DUPLICATE"
REASON_MALFORMED = "P01_DIRECTIVE_MALFORMED"
REASON_WRONG_MEMBER = "P01_UNRATIFIED_MEMBER"
REASON_INVALID_PROVENANCE = "P01_INVALID_PROVENANCE"
REASON_UNKNOWN_STATE = "P01_APPLICABILITY_UNKNOWN_FAIL_CLOSED"
REASON_DOUBLE_COUNTING = "P01_DOUBLE_COUNTING_FORBIDDEN"
REASON_PRE_EQUITY_MISSING = "P01_PRE_EQUITY_MISSING"
REJECTED_AUTOMATIC_P01_PREDICATE_CANDIDATES: tuple[str, ...] = (
    "HAIRCUT_FAMILY_LABEL",
    "RESERVE_FAMILY_LABEL",
    "DEPLETION_FAMILY_LABEL",
    "P01_TERM_PRESENCE",
    "U04_PENDING_ORDER_RESERVATION",
    "U05_LIABILITY",
    "U06_FEE",
    "VENUE_RAW_AVAILEQ",
    "STEP_29P_RISK_CLAIM",
    "LIVE_ACCOUNT_BOUND_STATE",
    "MASTER_V2_TRADING_LOGIC_STATE",
    "DOUBLE_PLAY_STATE",
)
ALGEBRA_SUBTRACT = "SUBTRACT_AUTHORIZED_AMOUNT"
ALGEBRA_ZERO_DOES_NOT_APPLY = "ZERO_BY_EXPLICIT_DOES_NOT_APPLY"
ALGEBRA_ZERO_APPLIES = "ZERO_BY_EXPLICIT_APPLIES_AMOUNT"
ALGEBRA_UNRESOLVED = "UNRESOLVED_FAIL_CLOSED"
POST_COMPUTABLE = "COMPUTABLE"
POST_UNRESOLVED = "UNRESOLVED_FAIL_CLOSED"


@dataclass(frozen=True)
class P01PredicateDecisionV1:
    """Typed P01 applicability decision. Not an equity authority sample."""

    decision_state: str
    reason_code: str
    authorized_reduction_amount: str
    algebra_contribution_state: str
    post_p01_equity_state: str
    ready: str


@dataclass(frozen=True)
class P01ReconstructionTermResultV1:
    """Typed P01 reconstruction-term result. Not a producer sample."""

    decision: P01PredicateDecisionV1
    pre_p01_equity: str
    post_p01_equity: str
    subtracted_amount: str


def evaluate_p01_application_predicate_v1(
    directives: Sequence[GovernedP01ReductionDirectiveV1] | None,
) -> P01PredicateDecisionV1:
    if directives is None or len(tuple(directives)) == 0:
        return P01PredicateDecisionV1(
            decision_state=STATE_UNKNOWN_FAIL_CLOSED,
            reason_code=REASON_MISSING,
            authorized_reduction_amount=AMOUNT_ABSENT,
            algebra_contribution_state=ALGEBRA_UNRESOLVED,
            post_p01_equity_state=POST_UNRESOLVED,
            ready="false",
        )
    items = tuple(directives)
    if len(items) != 1:
        return P01PredicateDecisionV1(
            decision_state=STATE_UNKNOWN_FAIL_CLOSED,
            reason_code=REASON_DUPLICATE,
            authorized_reduction_amount=AMOUNT_ABSENT,
            algebra_contribution_state=ALGEBRA_UNRESOLVED,
            post_p01_equity_state=POST_UNRESOLVED,
            ready="false",
        )
    directive = items[0]
    try:
        _ = directive.to_canonical_dict()
    except GovernedP01ReductionDirectiveError as exc:
        reason = REASON_MALFORMED
        text = str(exc)
        if "P01_UNRATIFIED_MEMBER" in text:
            reason = REASON_WRONG_MEMBER
        elif "P01_PROVENANCE" in text:
            reason = REASON_INVALID_PROVENANCE
        return P01PredicateDecisionV1(
            decision_state=STATE_UNKNOWN_FAIL_CLOSED,
            reason_code=reason,
            authorized_reduction_amount=AMOUNT_ABSENT,
            algebra_contribution_state=ALGEBRA_UNRESOLVED,
            post_p01_equity_state=POST_UNRESOLVED,
            ready="false",
        )
    if directive.applicability_state == STATE_UNKNOWN_FAIL_CLOSED:
        return P01PredicateDecisionV1(
            decision_state=STATE_UNKNOWN_FAIL_CLOSED,
            reason_code=REASON_UNKNOWN_STATE,
            authorized_reduction_amount=AMOUNT_ABSENT,
            algebra_contribution_state=ALGEBRA_UNRESOLVED,
            post_p01_equity_state=POST_UNRESOLVED,
            ready="false",
        )
    if directive.applicability_state == STATE_DOES_NOT_APPLY:
        return P01PredicateDecisionV1(
            decision_state=STATE_DOES_NOT_APPLY,
            reason_code=REASON_READY,
            authorized_reduction_amount="0",
            algebra_contribution_state=ALGEBRA_ZERO_DOES_NOT_APPLY,
            post_p01_equity_state=POST_COMPUTABLE,
            ready="true",
        )
    amount = parse_p01_reduction_amount_v1(directive.authorized_reduction_amount)
    contribution = ALGEBRA_ZERO_APPLIES if amount == Decimal("0") else ALGEBRA_SUBTRACT
    return P01PredicateDecisionV1(
        decision_state=STATE_APPLIES,
        reason_code=REASON_READY,
        authorized_reduction_amount=format(amount, "f"),
        algebra_contribution_state=contribution,
        post_p01_equity_state=POST_COMPUTABLE,
        ready="true",
    )


def evaluate_p01_reconstruction_term_v1(
    *,
    pre_p01_equity: Decimal | None,
    directives: Sequence[GovernedP01ReductionDirectiveV1] | None,
    pre_p01_base_already_includes_p01_reduction: bool = False,
) -> P01ReconstructionTermResultV1:
    decision = evaluate_p01_application_predicate_v1(directives)
    if pre_p01_base_already_includes_p01_reduction:
        blocked = P01PredicateDecisionV1(
            decision_state=STATE_UNKNOWN_FAIL_CLOSED,
            reason_code=REASON_DOUBLE_COUNTING,
            authorized_reduction_amount=AMOUNT_ABSENT,
            algebra_contribution_state=ALGEBRA_UNRESOLVED,
            post_p01_equity_state=POST_UNRESOLVED,
            ready="false",
        )
        return P01ReconstructionTermResultV1(
            decision=blocked,
            pre_p01_equity="" if pre_p01_equity is None else format(pre_p01_equity, "f"),
            post_p01_equity="",
            subtracted_amount=AMOUNT_ABSENT,
        )
    if decision.decision_state == STATE_UNKNOWN_FAIL_CLOSED:
        return P01ReconstructionTermResultV1(
            decision=decision,
            pre_p01_equity="" if pre_p01_equity is None else format(pre_p01_equity, "f"),
            post_p01_equity="",
            subtracted_amount=AMOUNT_ABSENT,
        )
    if pre_p01_equity is None or not pre_p01_equity.is_finite():
        blocked = P01PredicateDecisionV1(
            decision_state=STATE_UNKNOWN_FAIL_CLOSED,
            reason_code=REASON_PRE_EQUITY_MISSING,
            authorized_reduction_amount=AMOUNT_ABSENT,
            algebra_contribution_state=ALGEBRA_UNRESOLVED,
            post_p01_equity_state=POST_UNRESOLVED,
            ready="false",
        )
        return P01ReconstructionTermResultV1(
            decision=blocked,
            pre_p01_equity="" if pre_p01_equity is None else format(pre_p01_equity, "f"),
            post_p01_equity="",
            subtracted_amount=AMOUNT_ABSENT,
        )
    subtracted = parse_p01_reduction_amount_v1(decision.authorized_reduction_amount)
    if decision.decision_state == STATE_DOES_NOT_APPLY:
        subtracted = Decimal("0")
    post = pre_p01_equity - subtracted
    return P01ReconstructionTermResultV1(
        decision=decision,
        pre_p01_equity=format(pre_p01_equity, "f"),
        post_p01_equity=format(post, "f"),
        subtracted_amount=format(subtracted, "f"),
    )


def evaluate_p01_application_predicate_from_payloads_v1(
    payloads: Sequence[Mapping[str, Any]] | None,
) -> P01PredicateDecisionV1:
    if payloads is None or len(tuple(payloads)) == 0:
        return evaluate_p01_application_predicate_v1(())
    items = tuple(payloads)
    if len(items) != 1:
        return P01PredicateDecisionV1(
            decision_state=STATE_UNKNOWN_FAIL_CLOSED,
            reason_code=REASON_DUPLICATE,
            authorized_reduction_amount=AMOUNT_ABSENT,
            algebra_contribution_state=ALGEBRA_UNRESOLVED,
            post_p01_equity_state=POST_UNRESOLVED,
            ready="false",
        )
    payload = dict(items[0])
    supplied_digest = payload.get("provenance_digest")
    supplied_semantic = payload.get("semantic_digest")
    try:
        reserved = {
            "directive_id",
            "applicability_state",
            "evidence_ref",
            "authorized_reduction_amount",
            "amount_present",
        }
        directive = build_governed_p01_reduction_directive_v1(
            directive_id=str(payload.get("directive_id", "")),
            applicability_state=str(payload.get("applicability_state", "")),
            evidence_ref=str(payload.get("evidence_ref", "")),
            authorized_reduction_amount=str(payload.get("authorized_reduction_amount", "")),
            amount_present=payload.get("amount_present"),
            **{key: value for key, value in payload.items() if key not in reserved},
        )
    except (GovernedP01ReductionDirectiveError, TypeError, ValueError) as exc:
        reason = REASON_MALFORMED
        text = str(exc)
        if "P01_UNRATIFIED_MEMBER" in text or "P01_MEMBER_ID" in text:
            reason = REASON_WRONG_MEMBER
        elif "P01_PROVENANCE" in text:
            reason = REASON_INVALID_PROVENANCE
        return P01PredicateDecisionV1(
            decision_state=STATE_UNKNOWN_FAIL_CLOSED,
            reason_code=reason,
            authorized_reduction_amount=AMOUNT_ABSENT,
            algebra_contribution_state=ALGEBRA_UNRESOLVED,
            post_p01_equity_state=POST_UNRESOLVED,
            ready="false",
        )
    if supplied_digest not in {None, ""} and str(supplied_digest) != directive.provenance_digest:
        return P01PredicateDecisionV1(
            decision_state=STATE_UNKNOWN_FAIL_CLOSED,
            reason_code=REASON_INVALID_PROVENANCE,
            authorized_reduction_amount=AMOUNT_ABSENT,
            algebra_contribution_state=ALGEBRA_UNRESOLVED,
            post_p01_equity_state=POST_UNRESOLVED,
            ready="false",
        )
    if supplied_semantic not in {None, ""} and str(supplied_semantic) != directive.semantic_digest:
        return P01PredicateDecisionV1(
            decision_state=STATE_UNKNOWN_FAIL_CLOSED,
            reason_code=REASON_INVALID_PROVENANCE,
            authorized_reduction_amount=AMOUNT_ABSENT,
            algebra_contribution_state=ALGEBRA_UNRESOLVED,
            post_p01_equity_state=POST_UNRESOLVED,
            ready="false",
        )
    return evaluate_p01_application_predicate_v1((directive,))


def reject_p01_implicit_candidate_promotion_v1(*, candidate_id: str) -> None:
    _ = candidate_id
    raise GovernedP01ReductionDirectiveError("P01_IMPLICIT_CANDIDATE_PROMOTION_FORBIDDEN")


def reject_prior_p01_predicate_candidates_as_automatic_members_v1() -> None:
    for candidate_id in REJECTED_AUTOMATIC_P01_PREDICATE_CANDIDATES:
        reject_p01_implicit_candidate_promotion_v1(candidate_id=candidate_id)


def reject_u04_u05_u06_p01_inheritance_v1() -> None:
    raise GovernedP01ReductionDirectiveError("U04_U05_U06_INPUT_INHERITANCE_FORBIDDEN")
