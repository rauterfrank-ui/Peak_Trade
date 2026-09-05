"""Explicit STEP-29P capital / risk admissibility conjunction.

Replaces the unconditional live-context deny LIVE_VENUE_CAPITAL_NOT_ADMITTED_TO_STEP_29P
with a testable fail-closed predicate. Does not invent haircuts, reserve, depletion,
or OKX-field-to-account_equity mapping.

RISK_ADMISSIBLE=true only when every required fact is fresh, contract-valid,
instrument-bound, currency-bound, internally consistent, and sufficient under
current STEP-29P input rules. Standing Live gates are independent and are not
required and are not implied.

Does not construct LiveExecutionPort. Does not POST. Does not send wire.
Does not set LIVE_ENABLED / LIVE_ARMED / WIRE_SEND_PERMITTED.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol, Tuple

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    CAPITAL_AUTHORITY_OBSERVED_NOT_RISK_ADMISSIBLE,
    CAPITAL_AUTHORITY_RISK_ADMISSIBLE,
    CapitalAdmissionStatusV1,
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
)

CAPITAL_ADMISSION_AUTHORITY = "capital_admission_contract_v1"
CAPITAL_JOIN_SEAM_ID = "FULL_CORE_PRE_LIVE_CAPITAL_ADMISSION_SEAM_V1"
_FORBIDDEN_AUTHORITY_FIELD_MARKERS = (
    "totaleq",
    "adjeq",
    "availeq",
    "availbal",
    "cashbal",
)
_BARE_EQ_FIELD = "eq"


class CapitalAdmissionEvidenceLikeV1(Protocol):
    evidence_status: str
    capital_authority_class: str
    risk_admissible: bool


def _field_is_forbidden_authority(name: str) -> bool:
    folded = str(name or "").strip().lower().replace("_", "").replace("-", "")
    if not folded:
        return False
    if folded == _BARE_EQ_FIELD:
        return True
    return any(marker in folded for marker in _FORBIDDEN_AUTHORITY_FIELD_MARKERS)


def _parse_non_negative_decimal(raw: str, *, field: str) -> Decimal | None:
    text = str(raw or "").strip()
    if text == "":
        return None
    if text != str(raw):
        return None
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    if not value.is_finite() or value < 0:
        return None
    _ = field
    return value


JOIN_SEAM_ID = "FULL_CORE_STEP_29P_CAPITAL_RISK_ADMISSIBILITY_SEAM_V1"
STEP_29P_RISK_ADMISSIBILITY_AUTHORITY = "capital_risk_sizing_v1/STEP_29P"
RISK_EQUITY_DIMENSION = "RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING"
REQUIRED_SETTLEMENT_CURRENCY = "USDC"

FRESH_EVIDENCE_FETCHED = "FRESH_EVIDENCE_FETCHED"
FRESH_EVIDENCE_VALIDATED = "FRESH_EVIDENCE_VALIDATED"
CAPITAL_EVIDENCE_COMPLETE = "CAPITAL_EVIDENCE_COMPLETE"
STEP_29P_RISK_ADMISSIBLE = "STEP_29P_RISK_ADMISSIBLE"
STANDING_GATES_SATISFIED = "STANDING_GATES_SATISFIED"
PORT_CONSTRUCTION_AUTHORIZED = "PORT_CONSTRUCTION_AUTHORIZED"
PORT_CONSTRUCTED = "PORT_CONSTRUCTED"
WIRE_SEND_AUTHORIZED = "WIRE_SEND_AUTHORIZED"
WIRE_SEND_EXECUTED = "WIRE_SEND_EXECUTED"


@dataclass(frozen=True)
class Step29PCapitalRiskAdmissibilityClaimV1:
    """Typed 29P capital-risk claim. Observation is not automatic grant."""

    fresh_pretrade_get_status: str
    live_account_bound_status: str
    expected_instrument_id: str
    observed_instrument_id: str
    expected_currency: str = REQUIRED_SETTLEMENT_CURRENCY
    observed_currency: str = ""
    equity_dimension: str = ""
    typed_account_equity_raw: str = ""
    typed_account_equity_source_field: str = ""
    fresh_evidence_fetched: bool = False
    fresh_evidence_validated: bool = False


@dataclass(frozen=True)
class Step29PCapitalRiskAdmissibilityV1:
    risk_admissible: bool
    fail_closed: bool
    capital_evidence_complete: bool
    fresh_evidence_fetched: bool
    fresh_evidence_validated: bool
    instrument_bound: bool
    currency_bound: bool
    equity_dimension_bound: bool
    reason_codes: Tuple[str, ...]
    live_enabled: bool
    live_armed: bool
    wire_send_permitted: bool
    standing_gates_satisfied: bool
    port_construction_authorized: bool
    port_constructed: bool
    wire_send_authorized: bool
    wire_send_executed: bool
    join_seam_id: str = JOIN_SEAM_ID
    authority: str = STEP_29P_RISK_ADMISSIBILITY_AUTHORITY
    capital_authority: str = CAPITAL_ADMISSION_AUTHORITY


def _standing_false() -> bool:
    return LIVE_ENABLED is not True and LIVE_ARMED is not True and WIRE_SEND_PERMITTED is not True


def evaluate_step_29p_capital_risk_admissibility_v1(
    *,
    capital: CapitalAdmissionEvidenceLikeV1,
    claim: Step29PCapitalRiskAdmissibilityClaimV1 | None,
) -> Step29PCapitalRiskAdmissibilityV1:
    reasons: list[str] = []
    fetched = False
    validated = False
    instrument_bound = False
    currency_bound = False
    equity_bound = False
    capital_complete = False

    if claim is None:
        reasons.extend(
            (
                "STEP_29P_RISK_ADMISSIBILITY_CLAIM_MISSING",
                "FRESH_EVIDENCE_MISSING",
                "CAPITAL_EVIDENCE_INCOMPLETE",
                "LIVE_VENUE_CAPITAL_NOT_ADMITTED_TO_STEP_29P",
            )
        )
    else:
        fetched = claim.fresh_evidence_fetched is True
        get_trusted = (
            str(claim.fresh_pretrade_get_status or "").strip()
            == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
        )
        bound_trusted = (
            str(claim.live_account_bound_status or "").strip()
            == LiveAccountBoundStatusV1.TRUSTED_PRESENT.value
        )
        validated = claim.fresh_evidence_validated is True and get_trusted is True
        if fetched is not True:
            reasons.append("FRESH_EVIDENCE_NOT_FETCHED")
        if get_trusted is not True:
            reasons.append("FRESH_EVIDENCE_GET_NOT_TRUSTED")
        if claim.fresh_evidence_validated is not True:
            reasons.append("FRESH_EVIDENCE_NOT_VALIDATED")
        if bound_trusted is not True:
            reasons.append("LIVE_ACCOUNT_BOUND_NOT_TRUSTED_FOR_29P")

        expected_inst = str(claim.expected_instrument_id or "")
        observed_inst = str(claim.observed_instrument_id or "")
        if expected_inst == "" or observed_inst == "":
            reasons.append("STEP_29P_INSTRUMENT_SCOPE_MISSING")
        elif expected_inst != observed_inst:
            reasons.append("STEP_29P_WRONG_INSTRUMENT")
        else:
            instrument_bound = True

        expected_ccy = str(claim.expected_currency or "").strip()
        observed_ccy = str(claim.observed_currency or "").strip()
        if expected_ccy != REQUIRED_SETTLEMENT_CURRENCY:
            reasons.append("STEP_29P_WRONG_CURRENCY")
        elif observed_ccy == "":
            reasons.append("STEP_29P_CURRENCY_SCOPE_MISSING")
        elif observed_ccy != expected_ccy:
            reasons.append("STEP_29P_WRONG_CURRENCY")
        else:
            currency_bound = True

        dimension = str(claim.equity_dimension or "").strip()
        if dimension != RISK_EQUITY_DIMENSION:
            reasons.append("STEP_29P_EQUITY_DIMENSION_UNBOUND")
        else:
            equity_bound = True

        source_field = str(claim.typed_account_equity_source_field or "")
        if _field_is_forbidden_authority(source_field):
            reasons.append("CAPITAL_ADMISSION_OPTIMISTIC_FIELD_FALLBACK")
            equity_bound = False

        equity = _parse_non_negative_decimal(
            claim.typed_account_equity_raw, field="typed_account_equity_raw"
        )
        if str(claim.typed_account_equity_raw or "") == "" or equity is None:
            reasons.append("STEP_29P_TYPED_ACCOUNT_EQUITY_MISSING")
        elif equity <= 0:
            reasons.append("STEP_29P_TYPED_ACCOUNT_EQUITY_NOT_POSITIVE")
        else:
            try:
                if not Decimal(str(claim.typed_account_equity_raw)).is_finite():
                    reasons.append("STEP_29P_TYPED_ACCOUNT_EQUITY_NOT_FINITE")
            except (InvalidOperation, ValueError):
                reasons.append("STEP_29P_TYPED_ACCOUNT_EQUITY_NOT_DECIMAL")

        capital_trusted = capital.evidence_status == CapitalAdmissionStatusV1.TRUSTED_PRESENT.value
        if capital_trusted is not True:
            reasons.append("CAPITAL_EVIDENCE_INCOMPLETE")
        else:
            capital_complete = True
        if capital.risk_admissible is True and equity_bound is not True:
            reasons.append("CAPITAL_ADMISSION_RISK_ADMISSIBLE_CONJUNCTION_INCOMPLETE")

    unique = tuple(dict.fromkeys((*reasons, JOIN_SEAM_ID, CAPITAL_JOIN_SEAM_ID)))
    risk_admissible = len(reasons) == 0
    if risk_admissible is True:
        unique = tuple(
            dict.fromkeys(
                (
                    "STEP_29P_RISK_ADMISSIBLE",
                    JOIN_SEAM_ID,
                    STEP_29P_RISK_ADMISSIBILITY_AUTHORITY,
                )
            )
        )
    else:
        unique = tuple(
            dict.fromkeys(
                (
                    *unique,
                    "LIVE_VENUE_CAPITAL_NOT_ADMITTED_TO_STEP_29P",
                    "OBSERVED_CAPITAL_NOT_RISK_ADMISSIBLE",
                )
            )
        )
    return Step29PCapitalRiskAdmissibilityV1(
        risk_admissible=risk_admissible,
        fail_closed=True,
        capital_evidence_complete=capital_complete,
        fresh_evidence_fetched=fetched,
        fresh_evidence_validated=validated,
        instrument_bound=instrument_bound,
        currency_bound=currency_bound,
        equity_dimension_bound=equity_bound,
        reason_codes=unique,
        live_enabled=LIVE_ENABLED is True,
        live_armed=LIVE_ARMED is True,
        wire_send_permitted=WIRE_SEND_PERMITTED is True,
        standing_gates_satisfied=False,
        port_construction_authorized=False,
        port_constructed=False,
        wire_send_authorized=False,
        wire_send_executed=False,
    )


def live_venue_capital_may_bind_step_29p_v1(
    evidence: Any,
    *,
    admissibility: Step29PCapitalRiskAdmissibilityV1 | None = None,
) -> bool:
    """STEP-29P may consume venue capital only via the 29P conjunction.

    Standing LIVE_ENABLED / LIVE_ARMED / WIRE_SEND_PERMITTED are not required
    and are not implied.
    """
    _ = _standing_false()
    if admissibility is None:
        return False
    return (
        admissibility.risk_admissible is True
        and evidence.evidence_status == CapitalAdmissionStatusV1.TRUSTED_PRESENT.value
        and evidence.capital_authority_class
        in {
            CAPITAL_AUTHORITY_RISK_ADMISSIBLE,
            CAPITAL_AUTHORITY_OBSERVED_NOT_RISK_ADMISSIBLE,
        }
    )


def persist_class_fields_v1(
    admissibility: Step29PCapitalRiskAdmissibilityV1,
) -> dict[str, bool]:
    """Distinct persist classes. Never collapsed."""
    return {
        FRESH_EVIDENCE_FETCHED: admissibility.fresh_evidence_fetched is True,
        FRESH_EVIDENCE_VALIDATED: admissibility.fresh_evidence_validated is True,
        CAPITAL_EVIDENCE_COMPLETE: admissibility.capital_evidence_complete is True,
        STEP_29P_RISK_ADMISSIBLE: admissibility.risk_admissible is True,
        STANDING_GATES_SATISFIED: False,
        PORT_CONSTRUCTION_AUTHORIZED: False,
        PORT_CONSTRUCTED: False,
        WIRE_SEND_AUTHORIZED: False,
        WIRE_SEND_EXECUTED: False,
    }
