"""SOURCE_ACCEPTANCE_CONJUNCTION_V1.

Reuse existing canonical running-equity rules. Do not invent a second
semantic model. Observation is not authority. UNKNOWN fails closed.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.source_promotion_state_machine_v1 import (
    STATE_ACCEPTABLE_FOR_OWNER_RATIFICATION,
    STATE_ACCEPTANCE_FAILED,
    STATE_EVIDENCE_COMPLETE,
    STATE_EVIDENCE_INCOMPLETE,
)

SCHEMA_CLASS = "SOURCE_ACCEPTANCE_CONJUNCTION_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
OWNER_RATIFICATION_REQUIRED = True
REQUIRED_SETTLEMENT_CURRENCY = "USDC"
REQUIRED_UNIT_CLASS = "ACCOUNT_EQUITY_SETTLEMENT_UNITS"
USD_EQUALS_USDC = False

CONJUNCTION_CHECK_IDS: Tuple[str, ...] = (
    "provenance_complete",
    "account_venue_scope_bound",
    "exact_currency_unit",
    "no_implicit_usd_usdc",
    "freshness_same_epoch_age",
    "reconciliation_present",
    "observation_authority_separated",
    "deterministic_digest",
    "restart_reconstructability",
    "step_29p_compatibility",
    "forbidden_raw_equity_fields_absent",
    "no_free_cash_wallet_start_simulated_substitution",
    "unknown_inclusion_not_optimistic",
    "contradiction_fail_closed",
    "durable_evidence_refs_present",
    "not_c01_c16_revival",
    "new_generation_identity",
)

_TRUE = "true"
_FALSE = "false"
_UNKNOWN = "unknown"
_MISSING = "missing"

_FORBIDDEN_RAW_MARKERS: Tuple[str, ...] = (
    "availeq",
    "totaleq",
    "adjeq",
    "availbal",
    "cashbal",
    "frozenbal",
    "details.eq",
)
_FORBIDDEN_SUBSTITUTION_MARKERS: Tuple[str, ...] = (
    "free_balance",
    "cash_balance",
    "wallet_balance",
    "start_balance",
    "simulated",
    "default_account_equity",
    "injected_running_account_equity",
)


class SourceAcceptanceConjunctionError(ValueError):
    """Fail-closed source-acceptance conjunction violation."""


@dataclass(frozen=True)
class SourceAcceptanceConjunctionResultV1:
    conjunction_id: str
    candidate_id: str
    evidence_complete: str
    acceptance_status: str
    reason_codes: str
    failed_checks: str
    unknown_checks: str
    missing_checks: str
    authority_effect: str
    owner_ratification_required: str
    mapping_proven: str
    producer_authorized: str
    runtime_binding_authorized: str


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "")


def _pin(raw: object) -> str:
    text = str(raw or "").strip().lower()
    if text in {_TRUE, "1", "yes"}:
        return _TRUE
    if text in {_FALSE, "0", "no"}:
        return _FALSE
    if text in {_UNKNOWN, "unspecified", "unresolved"}:
        return _UNKNOWN
    if text in {_MISSING, "", "none", "null"}:
        return _MISSING
    return _UNKNOWN


def evaluate_source_acceptance_conjunction_v1(
    *,
    candidate_id: str,
    checks: Mapping[str, str],
    observation_vs_authority_class: str,
    currency: str,
    unit_class: str,
    source_object_class: str,
    producer_identity_claim: str,
    revival_equivalent: bool,
    new_generation_identity: bool,
    contradiction: bool,
) -> SourceAcceptanceConjunctionResultV1:
    cid = str(candidate_id or "").strip()
    if cid == "":
        raise SourceAcceptanceConjunctionError("CANDIDATE_ID_MISSING")

    failed: list[str] = []
    unknown: list[str] = []
    missing: list[str] = []
    reasons: list[str] = []

    for check_id in CONJUNCTION_CHECK_IDS:
        if check_id == "exact_currency_unit":
            currency_ok = str(currency or "").strip() == REQUIRED_SETTLEMENT_CURRENCY
            unit_ok = str(unit_class or "").strip() == REQUIRED_UNIT_CLASS
            pin = _TRUE if currency_ok and unit_ok else _FALSE
        elif check_id == "no_implicit_usd_usdc":
            pin = _FALSE if USD_EQUALS_USDC else _TRUE
            if str(currency or "").strip().upper() == "USD":
                pin = _FALSE
                reasons.append("USD_IS_NOT_USDC")
        elif check_id == "observation_authority_separated":
            obs = str(observation_vs_authority_class or "").strip()
            if obs == "AUTHORITY":
                pin = _FALSE
                reasons.append("OBSERVATION_CANNOT_MINT_AUTHORITY")
            elif obs in {"OBSERVATION", "NON_AUTHORITATIVE_CANDIDATE"}:
                pin = _TRUE
            else:
                pin = _UNKNOWN
        elif check_id == "not_c01_c16_revival":
            pin = _FALSE if revival_equivalent else _TRUE
        elif check_id == "new_generation_identity":
            pin = _TRUE if new_generation_identity is True else _FALSE
        elif check_id == "contradiction_fail_closed":
            pin = _FALSE if contradiction else _TRUE
        elif check_id == "forbidden_raw_equity_fields_absent":
            blob = _fold(f"{source_object_class}|{producer_identity_claim}")
            pin = (
                _FALSE
                if any(marker.replace(".", "") in blob for marker in _FORBIDDEN_RAW_MARKERS)
                else _TRUE
            )
        elif check_id == "no_free_cash_wallet_start_simulated_substitution":
            blob = _fold(f"{source_object_class}|{producer_identity_claim}")
            pin = (
                _FALSE
                if any(_fold(marker) in blob for marker in _FORBIDDEN_SUBSTITUTION_MARKERS)
                else _TRUE
            )
        else:
            pin = _pin(checks.get(check_id))

        if pin == _MISSING:
            missing.append(check_id)
        elif pin == _UNKNOWN:
            unknown.append(check_id)
            reasons.append(f"UNKNOWN_FAIL_CLOSED:{check_id}")
        elif pin != _TRUE:
            failed.append(check_id)
            reasons.append(f"ACCEPTANCE_CHECK_FAILED:{check_id}")

    evidence_complete = _TRUE if not missing else _FALSE
    if missing:
        status = STATE_EVIDENCE_INCOMPLETE
        reasons.append("EVIDENCE_INCOMPLETE")
    elif failed or unknown:
        status = STATE_ACCEPTANCE_FAILED
        if unknown:
            reasons.append("UNKNOWN_INCLUSION_NOT_OPTIMISTIC")
    else:
        status = STATE_ACCEPTABLE_FOR_OWNER_RATIFICATION
        evidence_complete = _TRUE

    if evidence_complete == _TRUE and status == STATE_EVIDENCE_INCOMPLETE:
        status = STATE_EVIDENCE_COMPLETE

    return SourceAcceptanceConjunctionResultV1(
        conjunction_id="SOURCE_ACCEPTANCE_CONJUNCTION_V1",
        candidate_id=cid,
        evidence_complete=evidence_complete,
        acceptance_status=status,
        reason_codes=",".join(reasons) if reasons else "NONE",
        failed_checks=",".join(failed) if failed else "NONE",
        unknown_checks=",".join(unknown) if unknown else "NONE",
        missing_checks=",".join(missing) if missing else "NONE",
        authority_effect=AUTHORITY_EFFECT,
        owner_ratification_required="true",
        mapping_proven="false",
        producer_authorized="false",
        runtime_binding_authorized="false",
    )
