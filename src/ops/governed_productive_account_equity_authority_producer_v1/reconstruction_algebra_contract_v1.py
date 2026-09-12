"""Typed reconstruction algebra contract schema.

Algebra semantics and completeness rules only. Does not calculate a
productive running-equity value. Algebra-schema presence is not algebra
completeness. Algebra completeness is not reconstruction proof.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ALGEBRA_PROVENANCE_REQUIRED_FIELDS,
    EQUITY_DIMENSION_BOUND,
    GOVERNED_PRODUCER_CREATED,
    INCLUSION_PROVEN,
    INTERNAL_RECONSTRUCTION_PROVEN,
    INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT,
    INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT,
    LIVE_RESTART_RECONSTRUCTED,
    MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING,
    RECONCILIATION_CONTRACT_CREATED,
    RECONSTRUCTION_ALGEBRA_AUTHORITY_EFFECT,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT,
    SEMANTIC_MAPPING_PROVEN,
    SOURCE_OBJECT_PRESENT,
    SOURCE_SELECTED,
)

SCHEMA_CLASS = "RECONSTRUCTION_ALGEBRA_CONTRACT_V1"
ALGEBRA_CONTRACT_VERSION = "v1"
RECONSTRUCTION_CONTRACT_SCHEMA_CLASS = "INTERNAL_RECONSTRUCTION_CONTRACT_V1"
DIMENSION_ID = "RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING"
ALGEBRA_AUTHORITY_EFFECT_NONE = "NONE"
ALGEBRA_STATUS_INCOMPLETE = "INCOMPLETE"
ALGEBRA_STATUS_COMPLETE = "COMPLETE"
CANONICAL_FORMULA_STATUS_UNPROVEN = "UNPROVEN"
CANONICAL_FORMULA_STATUS_PROVEN = "PROVEN"
CANONICAL_FORMULA_REPRESENTATION = ""
REJECTED_NAIVE_FORMULA = (
    "INITIAL_EQUITY_PLUS_REALIZED_PNL_PLUS_UNREALIZED_PNL_MINUS_FEES_MINUS_SLIPPAGE"
)
ALGEBRA_REPRESENTATION = (
    "EQUITY_BASE=ADDITIVE;"
    "U02_REALIZED_PNL=EMBEDDED_NOT_SEPARATE;"
    "U03_UNREALIZED_PNL_MTM=EMBEDDED_NOT_SEPARATE;"
    "U03_NOTIONAL=VALUATION_INPUT_ONLY;"
    "U04_PENDING_ORDER_RESERVATION=CONDITIONAL_SUBTRACTIVE_IF_NOT_IN_BASE;"
    "U05_LIABILITY=CONDITIONAL_SUBTRACTIVE_IF_NOT_IN_BASE;"
    "U06_FEE=CONDITIONAL_ONCE_IN_BASE_OR_SINGLE_SUBTRACTION;"
    "P01_HAIRCUT_RESERVE_DEPLETION=NON_NEGATIVE_ABSOLUTE_MONETARY_REDUCTION_SUBTRACTION;"
    "SLIPPAGE=PROHIBITED_INDEPENDENT_TERM;"
    "U01=NON_ALGEBRAIC;"
    "U07=NON_ALGEBRAIC;"
    "U08=USDC_NATIVE_OR_OWNER_RATIFIED_CONVERSION_ELSE_FAIL_CLOSED;"
    "U09=NON_ALGEBRAIC;"
    "NAIVE_BASE_PLUS_PNL_MINUS_FEE_SLIPPAGE=REJECTED;"
    "ALGEBRA_COMPLETE=false"
)
ROLE_ADDITIVE = "ADDITIVE"
ROLE_SUBTRACTIVE = "SUBTRACTIVE"
ROLE_REDUCTION_ONLY_UNSPECIFIED = "REDUCTION_ONLY_UNSPECIFIED"
ROLE_EMBEDDED_NOT_SEPARATE = "EMBEDDED_NOT_SEPARATE"
ROLE_VALUATION_INPUT_ONLY = "VALUATION_INPUT_ONLY"
ROLE_NON_ALGEBRAIC = "NON_ALGEBRAIC"
ROLE_PROHIBITED = "PROHIBITED"
ROLE_UNRESOLVED = "UNRESOLVED"
ROLE_CONDITIONAL_SUBTRACTIVE_IF_NOT_IN_BASE = "CONDITIONAL_SUBTRACTIVE_IF_NOT_IN_BASE"
ROLE_CONDITIONAL_ONCE_IN_BASE_OR_SINGLE_SUBTRACTION = (
    "CONDITIONAL_ONCE_IN_BASE_OR_SINGLE_SUBTRACTION"
)
SIGN_ADD = "ADD"
SIGN_SUBTRACT = "SUBTRACT"
SIGN_REDUCTION_ONLY = "REDUCTION_ONLY"
SIGN_NONE = "NONE"
SIGN_CONDITIONAL = "CONDITIONAL"
SIGN_PROHIBITED = "PROHIBITED"
INCLUSION_UNRESOLVED = "UNRESOLVED"
INCLUSION_IN_BASE = "IN_BASE"
INCLUSION_NOT_IN_BASE = "NOT_IN_BASE"
INCLUSION_NOT_APPLICABLE = "NOT_APPLICABLE"
EMBEDDED_YES = "EMBEDDED"
EMBEDDED_NO = "NOT_EMBEDDED"
EMBEDDED_CONDITIONAL = "CONDITIONAL"
EMBEDDED_UNRESOLVED = "UNRESOLVED"
EMBEDDED_NOT_APPLICABLE = "NOT_APPLICABLE"
TERM_SET_SPECIFIED = "SPECIFIED"
TERM_SET_UNSPECIFIED = "UNSPECIFIED"
TERM_SET_NOT_APPLICABLE = "NOT_APPLICABLE"
PARTICIPATION_PARTICIPATING = "PARTICIPATING"
PARTICIPATION_BLOCKING = "BLOCKING"
PARTICIPATION_NOT_APPLICABLE = "NOT_APPLICABLE"
NUMERIC_NOT_COMPUTED = "NOT_COMPUTED"
NUMERIC_MISSING = "MISSING"
NUMERIC_MALFORMED = "MALFORMED"
NUMERIC_PRESENT_ZERO = "PRESENT_ZERO"
NUMERIC_PRESENT_NONZERO = "PRESENT_NONZERO"
CONTRADICTION_NONE = "NO_CONTRADICTION"
CONTRADICTION_PRESENT = "CONTRADICTION_PRESENT"
CURRENCY_DOMAIN_USDC = "USDC"
CURRENCY_DOMAIN_UNSPECIFIED = "UNSPECIFIED"
VALUATION_NONE = "NONE"
VALUATION_MTM_MARK_IN_EQUITY_BASE = "MTM_MARK_IN_EQUITY_BASE"
VALUATION_NOTIONAL_PROHIBITED_AS_ADDEND = "NOTIONAL_PROHIBITED_AS_ADDEND"
TERM_EQUITY_BASE = "EQUITY_BASE"
TERM_REALIZED_PNL = "REALIZED_PNL"
TERM_UNREALIZED_PNL_MTM = "UNREALIZED_PNL_MTM"
TERM_PENDING_ORDER_RESERVATION = "PENDING_ORDER_RESERVATION"
TERM_LIABILITY = "LIABILITY"
TERM_FEE = "FEE"
TERM_P01_HAIRCUT_RESERVE_DEPLETION = "P01_HAIRCUT_RESERVE_DEPLETION"
TERM_SLIPPAGE = "SLIPPAGE"
TERM_U01_ACCOUNT_MODE = "U01_ACCOUNT_MODE"
TERM_U07_RESTART_RECONCILIATION = "U07_RESTART_RECONCILIATION"
TERM_U08_CURRENCY_CONVERSION = "U08_CURRENCY_CONVERSION"
TERM_U09_FRESHNESS = "U09_FRESHNESS"
EARLIEST_UNRESOLVED_ALGEBRA_TERM = "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED"
UNRESOLVED_ALGEBRA_TERMS: Tuple[str, ...] = (
    "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED",
    "U05_LIABILITY_INCLUSION_OR_VALUE_UNRESOLVED",
    "U06_FEE_INCLUSION_UNRESOLVED",
)
P01_HAIRCUTS_RESERVE_DEPLETION = "NON_NEGATIVE_ABSOLUTE_MONETARY_REDUCTION_SUBTRACTION"
U01_ACCOUNT_MODE_ROLE = "ELIGIBILITY_CONTEXT_NOT_NUMERIC_EQUITY_TERM"
U02_REALIZED_UNREALIZED_TREATMENT = "IN_EQUITY_BASE_ONLY_NO_SEPARATE_ADDEND"
U03_OPEN_POSITION_TREATMENT = "MTM_IN_EQUITY_BASE_ONLY_NO_NOTIONAL_ADD"
U04_PENDING_ORDER_RESERVATIONS = "ENTRY_SUBTRACT_IF_NOT_IN_BASE_REDUCE_ONLY_NO_PRE_FILL_INCREASE"
U05_LIABILITIES_BORROWINGS = "REDUCE_ONCE_UNKNOWN_FAIL_CLOSED"
U06_FEES = "ACCRUED_ONCE_FUTURE_NOT_IN_U06"
U07_RESTART_RECONCILIATION = "FAIL_CLOSED_UNTIL_FRESH_SAME_EPOCH_RECONCILED"
U08_MULTI_CURRENCY_CONVERSION = "USDC_NATIVE_OR_OWNER_RATIFIED_CONTRACT_ELSE_FAIL_CLOSED"
U09_FRESHNESS_CLASS = "FRESH_GET_PER_PRETRADE_DECISION"
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_FALLBACK_MARKERS: Tuple[str, ...] = ("|", " or ", ",", ";")
_FORBIDDEN_VENUE_FIELD_MARKERS: Tuple[str, ...] = (
    "details.availeq",
    "availeq",
    "totaleq",
    "adjeq",
    "availbal",
    "cashbal",
    "frozenbal",
    "isoeq",
    "ordfrozen",
)
_BARE_FORBIDDEN_TOKENS: Tuple[str, ...] = ("eq", "upl")
_FORBIDDEN_OBJECT_TOKENS: Tuple[str, ...] = (
    "accountingportfoliostatev1",
    "ledgersnapshot",
    "equitybyccy",
    "simulatedportfoliostatev1",
    "fundingaccountbalanceobservationv1",
    "freshavailablemarginobservationv1",
    "balancesnapshot",
    "start_balance",
)
_TERM_VECTOR_FIELDS: Tuple[str, ...] = (
    "term_id",
    "policy_id",
    "component_semantic_class",
    "algebraic_role",
    "operator_semantics",
    "sign_semantics",
    "inclusion_state",
    "embedded_term_state",
    "double_count_guard_id",
    "economic_effect_id",
    "valuation_dependency",
    "currency_unit_domain",
    "term_set_status",
    "completeness_participation",
    "numeric_participation_state",
    "contradiction_state",
)
ALGEBRAIC_ROLES: Tuple[str, ...] = (
    ROLE_ADDITIVE,
    ROLE_SUBTRACTIVE,
    ROLE_REDUCTION_ONLY_UNSPECIFIED,
    ROLE_EMBEDDED_NOT_SEPARATE,
    ROLE_VALUATION_INPUT_ONLY,
    ROLE_NON_ALGEBRAIC,
    ROLE_PROHIBITED,
    ROLE_UNRESOLVED,
    ROLE_CONDITIONAL_SUBTRACTIVE_IF_NOT_IN_BASE,
    ROLE_CONDITIONAL_ONCE_IN_BASE_OR_SINGLE_SUBTRACTION,
)
INCLUSION_STATES: Tuple[str, ...] = (
    INCLUSION_UNRESOLVED,
    INCLUSION_IN_BASE,
    INCLUSION_NOT_IN_BASE,
    INCLUSION_NOT_APPLICABLE,
)
EMBEDDED_STATES: Tuple[str, ...] = (
    EMBEDDED_YES,
    EMBEDDED_NO,
    EMBEDDED_CONDITIONAL,
    EMBEDDED_UNRESOLVED,
    EMBEDDED_NOT_APPLICABLE,
)
NUMERIC_STATES: Tuple[str, ...] = (
    NUMERIC_NOT_COMPUTED,
    NUMERIC_MISSING,
    NUMERIC_MALFORMED,
    NUMERIC_PRESENT_ZERO,
    NUMERIC_PRESENT_NONZERO,
)
REQUIRED_TERM_IDS: Tuple[str, ...] = (
    TERM_EQUITY_BASE,
    TERM_FEE,
    TERM_LIABILITY,
    TERM_P01_HAIRCUT_RESERVE_DEPLETION,
    TERM_PENDING_ORDER_RESERVATION,
    TERM_REALIZED_PNL,
    TERM_SLIPPAGE,
    TERM_U01_ACCOUNT_MODE,
    TERM_U07_RESTART_RECONCILIATION,
    TERM_U08_CURRENCY_CONVERSION,
    TERM_U09_FRESHNESS,
    TERM_UNREALIZED_PNL_MTM,
)


class ReconstructionAlgebraContractError(ValueError):
    """Fail-closed reconstruction algebra contract violation."""


def _policy_pins() -> Mapping[str, Any]:
    from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
        DOUBLE_COUNT_CONTROL_U02_U03_MTM_ONCE,
        DOUBLE_COUNT_CONTROL_U04_HOLD_ONCE,
        DOUBLE_COUNT_CONTROL_U05_LIABILITY_ONCE,
        DOUBLE_COUNT_CONTROL_U06_FEE_ONCE,
        P01_HAIRCUTS_RESERVE_DEPLETION as PIN_P01,
        P01_MAY_INCREASE_EQUITY,
        U01_ACCOUNT_MODE_ROLE as PIN_U01,
        U02_REALIZED_UNREALIZED_TREATMENT as PIN_U02,
        U03_OPEN_POSITION_TREATMENT as PIN_U03,
        U04_PENDING_ORDER_RESERVATIONS as PIN_U04,
        U05_LIABILITIES_BORROWINGS as PIN_U05,
        U06_FEES as PIN_U06,
        U07_RESTART_RECONCILIATION as PIN_U07,
        U08_MULTI_CURRENCY_CONVERSION as PIN_U08,
        U09_FRESHNESS_CLASS as PIN_U09,
        USD_EQUALS_USDC,
    )

    return {
        "P01_HAIRCUTS_RESERVE_DEPLETION": PIN_P01,
        "P01_MAY_INCREASE_EQUITY": P01_MAY_INCREASE_EQUITY,
        "U01_ACCOUNT_MODE_ROLE": PIN_U01,
        "U02_REALIZED_UNREALIZED_TREATMENT": PIN_U02,
        "U03_OPEN_POSITION_TREATMENT": PIN_U03,
        "U04_PENDING_ORDER_RESERVATIONS": PIN_U04,
        "U05_LIABILITIES_BORROWINGS": PIN_U05,
        "U06_FEES": PIN_U06,
        "U07_RESTART_RECONCILIATION": PIN_U07,
        "U08_MULTI_CURRENCY_CONVERSION": PIN_U08,
        "U09_FRESHNESS_CLASS": PIN_U09,
        "USD_EQUALS_USDC": USD_EQUALS_USDC,
        "DOUBLE_COUNT_CONTROL_U02_U03_MTM_ONCE": DOUBLE_COUNT_CONTROL_U02_U03_MTM_ONCE,
        "DOUBLE_COUNT_CONTROL_U04_HOLD_ONCE": DOUBLE_COUNT_CONTROL_U04_HOLD_ONCE,
        "DOUBLE_COUNT_CONTROL_U05_LIABILITY_ONCE": DOUBLE_COUNT_CONTROL_U05_LIABILITY_ONCE,
        "DOUBLE_COUNT_CONTROL_U06_FEE_ONCE": DOUBLE_COUNT_CONTROL_U06_FEE_ONCE,
    }


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "")


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise ReconstructionAlgebraContractError(f"RECONSTRUCTION_ALGEBRA_FIELD_MISSING:{field}")
    if not isinstance(raw, str):
        raise ReconstructionAlgebraContractError(f"RECONSTRUCTION_ALGEBRA_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise ReconstructionAlgebraContractError(f"RECONSTRUCTION_ALGEBRA_FIELD_MISSING:{field}")
    return text


def _require_str_allow_empty(*, field: str, raw: Any) -> str:
    if raw is None:
        raise ReconstructionAlgebraContractError(f"RECONSTRUCTION_ALGEBRA_FIELD_MISSING:{field}")
    if not isinstance(raw, str):
        raise ReconstructionAlgebraContractError(f"RECONSTRUCTION_ALGEBRA_FIELD_NOT_STRING:{field}")
    if raw.strip() != raw:
        raise ReconstructionAlgebraContractError(f"RECONSTRUCTION_ALGEBRA_FIELD_NOT_EXACT:{field}")
    return raw


def _reject_fallback_chain(*, field: str, raw: str) -> None:
    lowered = raw.lower()
    for marker in _FORBIDDEN_FALLBACK_MARKERS:
        if marker in lowered:
            raise ReconstructionAlgebraContractError(
                f"RECONSTRUCTION_ALGEBRA_FALLBACK_CHAIN_FORBIDDEN:{field}"
            )


def _token_is_forbidden(raw: str) -> bool:
    folded = _fold(raw)
    if not folded:
        return False
    if folded in _BARE_FORBIDDEN_TOKENS:
        return True
    if any(marker in folded for marker in _FORBIDDEN_VENUE_FIELD_MARKERS):
        return True
    return any(token in folded for token in _FORBIDDEN_OBJECT_TOKENS)


def _reject_forbidden_authority_token(*, field: str, raw: str) -> None:
    if _token_is_forbidden(raw):
        raise ReconstructionAlgebraContractError(
            f"RECONSTRUCTION_ALGEBRA_FORBIDDEN_AUTHORITY_FIELD:{field}"
        )


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def encode_algebra_term_vector_v1(terms: Sequence["AlgebraTermV1"]) -> str:
    payload = [term.to_canonical_dict() for term in terms]
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_reconstruction_algebra_provenance_digest_v1(
    canonical: Mapping[str, str],
) -> str:
    payload = {
        key: canonical[key]
        for key in ALGEBRA_PROVENANCE_REQUIRED_FIELDS
        if key != "provenance_digest"
    }
    return _sha256_hex(_canonical_json(payload))


def attach_reconstruction_algebra_provenance_digest_v1(
    fields: Mapping[str, Any],
) -> dict[str, Any]:
    """Attach the deterministic digest. Does not reconstruct or bind."""

    canonical: dict[str, str] = {}
    for canonical_name in ALGEBRA_PROVENANCE_REQUIRED_FIELDS:
        if canonical_name == "provenance_digest":
            continue
        if canonical_name not in fields:
            raise ReconstructionAlgebraContractError(
                f"RECONSTRUCTION_ALGEBRA_FIELD_MISSING:{canonical_name}"
            )
        raw = fields[canonical_name]
        canonical[canonical_name] = "" if raw is None else str(raw)
    attached = dict(fields)
    attached["provenance_digest"] = compute_reconstruction_algebra_provenance_digest_v1(canonical)
    return attached


@dataclass(frozen=True)
class AlgebraTermV1:
    """Typed algebra term. Not a numeric reconstructed-equity mint."""

    term_id: str
    policy_id: str
    component_semantic_class: str
    algebraic_role: str
    operator_semantics: str
    sign_semantics: str
    inclusion_state: str
    embedded_term_state: str
    double_count_guard_id: str
    economic_effect_id: str
    valuation_dependency: str
    currency_unit_domain: str
    term_set_status: str
    completeness_participation: str
    numeric_participation_state: str
    contradiction_state: str

    def __post_init__(self) -> None:
        _validate_algebra_term_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        return {
            "term_id": self.term_id,
            "policy_id": self.policy_id,
            "component_semantic_class": self.component_semantic_class,
            "algebraic_role": self.algebraic_role,
            "operator_semantics": self.operator_semantics,
            "sign_semantics": self.sign_semantics,
            "inclusion_state": self.inclusion_state,
            "embedded_term_state": self.embedded_term_state,
            "double_count_guard_id": self.double_count_guard_id,
            "economic_effect_id": self.economic_effect_id,
            "valuation_dependency": self.valuation_dependency,
            "currency_unit_domain": self.currency_unit_domain,
            "term_set_status": self.term_set_status,
            "completeness_participation": self.completeness_participation,
            "numeric_participation_state": self.numeric_participation_state,
            "contradiction_state": self.contradiction_state,
        }


def build_algebra_term_v1(**fields: str) -> AlgebraTermV1:
    missing = [name for name in _TERM_VECTOR_FIELDS if name not in fields]
    if missing:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_TERM_FIELD_MISSING:" + ",".join(missing)
        )
    extra = [name for name in fields if name not in _TERM_VECTOR_FIELDS]
    if extra:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_TERM_FIELD_UNKNOWN:" + ",".join(sorted(extra))
        )
    return AlgebraTermV1(**{name: fields[name] for name in _TERM_VECTOR_FIELDS})


def _validate_algebra_term_v1(term: AlgebraTermV1) -> None:
    term_id = _require_non_empty_str(field="term_id", raw=term.term_id)
    if term_id not in REQUIRED_TERM_IDS:
        raise ReconstructionAlgebraContractError(
            f"RECONSTRUCTION_ALGEBRA_TERM_ID_UNKNOWN:{term_id}"
        )
    policy_id = _require_non_empty_str(field="policy_id", raw=term.policy_id)
    component_class = _require_non_empty_str(
        field="component_semantic_class", raw=term.component_semantic_class
    )
    role = _require_non_empty_str(field="algebraic_role", raw=term.algebraic_role)
    if role not in ALGEBRAIC_ROLES:
        raise ReconstructionAlgebraContractError(f"RECONSTRUCTION_ALGEBRA_ROLE_UNKNOWN:{role}")
    operator = _require_non_empty_str(field="operator_semantics", raw=term.operator_semantics)
    sign = _require_non_empty_str(field="sign_semantics", raw=term.sign_semantics)
    inclusion = _require_non_empty_str(field="inclusion_state", raw=term.inclusion_state)
    if inclusion not in INCLUSION_STATES:
        raise ReconstructionAlgebraContractError(
            f"RECONSTRUCTION_ALGEBRA_INCLUSION_UNKNOWN:{inclusion}"
        )
    embedded = _require_non_empty_str(field="embedded_term_state", raw=term.embedded_term_state)
    if embedded not in EMBEDDED_STATES:
        raise ReconstructionAlgebraContractError(
            f"RECONSTRUCTION_ALGEBRA_EMBEDDED_STATE_UNKNOWN:{embedded}"
        )
    _require_non_empty_str(field="double_count_guard_id", raw=term.double_count_guard_id)
    economic_effect = _require_non_empty_str(
        field="economic_effect_id", raw=term.economic_effect_id
    )
    valuation = _require_non_empty_str(field="valuation_dependency", raw=term.valuation_dependency)
    currency = _require_non_empty_str(field="currency_unit_domain", raw=term.currency_unit_domain)
    term_set = _require_non_empty_str(field="term_set_status", raw=term.term_set_status)
    participation = _require_non_empty_str(
        field="completeness_participation", raw=term.completeness_participation
    )
    numeric = _require_non_empty_str(
        field="numeric_participation_state", raw=term.numeric_participation_state
    )
    contradiction = _require_non_empty_str(
        field="contradiction_state", raw=term.contradiction_state
    )
    if numeric not in NUMERIC_STATES:
        raise ReconstructionAlgebraContractError(
            f"RECONSTRUCTION_ALGEBRA_NUMERIC_STATE_UNKNOWN:{numeric}"
        )
    if contradiction not in {CONTRADICTION_NONE, CONTRADICTION_PRESENT}:
        raise ReconstructionAlgebraContractError(
            f"RECONSTRUCTION_ALGEBRA_TERM_CONTRADICTION_UNKNOWN:{contradiction}"
        )
    if role == ROLE_PROHIBITED and numeric in {NUMERIC_PRESENT_ZERO, NUMERIC_PRESENT_NONZERO}:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_PROHIBITED_TERM_CANNOT_PARTICIPATE"
        )
    if role == ROLE_VALUATION_INPUT_ONLY and sign == SIGN_ADD:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_VALUATION_INPUT_CANNOT_BECOME_ADDITIVE"
        )
    if role == ROLE_EMBEDDED_NOT_SEPARATE and sign == SIGN_ADD:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_EMBEDDED_TERM_CANNOT_BE_INDEPENDENTLY_COUNTED"
        )
    if (
        role in {ROLE_UNRESOLVED, ROLE_REDUCTION_ONLY_UNSPECIFIED}
        and participation == PARTICIPATION_PARTICIPATING
    ):
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_UNRESOLVED_TERM_CANNOT_PARTICIPATE"
        )
    participating_signs = {SIGN_ADD, SIGN_SUBTRACT, SIGN_REDUCTION_ONLY}
    if numeric == NUMERIC_MISSING and sign in participating_signs:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_MISSING_TERM_ZERO_COERCION_FORBIDDEN"
        )
    if numeric == NUMERIC_MALFORMED and sign in participating_signs:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_MALFORMED_TERM_ZERO_COERCION_FORBIDDEN"
        )
    if term_id == TERM_P01_HAIRCUT_RESERVE_DEPLETION:
        if role != ROLE_SUBTRACTIVE:
            raise ReconstructionAlgebraContractError("P01_OPERATOR_MUST_BE_SUBTRACTION")
        if sign not in {SIGN_SUBTRACT, SIGN_REDUCTION_ONLY}:
            raise ReconstructionAlgebraContractError("P01_SIGN_MUST_BE_NON_NEGATIVE_REDUCTION")
        if role == ROLE_ADDITIVE or sign == SIGN_ADD:
            raise ReconstructionAlgebraContractError("P01_MAY_INCREASE_EQUITY_FORBIDDEN")
        if inclusion == INCLUSION_NOT_APPLICABLE:
            raise ReconstructionAlgebraContractError("P01_UNKNOWN_APPLICABILITY_AUTO_NA_FORBIDDEN")
        if inclusion != INCLUSION_NOT_IN_BASE:
            raise ReconstructionAlgebraContractError("P01_MUST_BE_EXCLUDED_FROM_EQUITY_BASE")
        if embedded == EMBEDDED_NOT_APPLICABLE:
            raise ReconstructionAlgebraContractError("P01_UNKNOWN_APPLICABILITY_AUTO_NA_FORBIDDEN")
        if embedded != EMBEDDED_NO:
            raise ReconstructionAlgebraContractError("P01_MUST_NOT_BE_EMBEDDED_IN_BASE")
        if currency == CURRENCY_DOMAIN_USDC:
            raise ReconstructionAlgebraContractError("P01_UNIT_INFERRED_CURRENCY_FORBIDDEN")
        if "safe" in _fold(term.double_count_guard_id):
            raise ReconstructionAlgebraContractError("P01_UNKNOWN_OVERLAP_AUTO_SAFE_FORBIDDEN")
    if currency == "USD":
        raise ReconstructionAlgebraContractError("RECONSTRUCTION_ALGEBRA_USD_IS_NOT_USDC")
    pins = _policy_pins()
    if pins["USD_EQUALS_USDC"] is True:
        raise ReconstructionAlgebraContractError("RECONSTRUCTION_ALGEBRA_USD_EQUALS_USDC_PIN")
    _reject_fallback_chain(field="term_id", raw=term_id)
    _reject_forbidden_authority_token(field="term_id", raw=term_id)
    _reject_forbidden_authority_token(field="operator_semantics", raw=operator)
    _reject_forbidden_authority_token(field="economic_effect_id", raw=economic_effect)
    _reject_forbidden_authority_token(field="valuation_dependency", raw=valuation)
    _ = (policy_id, component_class, term_set)


def _canonical_terms() -> Tuple[AlgebraTermV1, ...]:
    return (
        build_algebra_term_v1(
            term_id=TERM_EQUITY_BASE,
            policy_id="EQUITY_BASE",
            component_semantic_class=TERM_EQUITY_BASE,
            algebraic_role=ROLE_ADDITIVE,
            operator_semantics="EQUITY_BASE_ADDITIVE_SAME_EPOCH_SOURCE_UNBOUND",
            sign_semantics=SIGN_ADD,
            inclusion_state=INCLUSION_NOT_APPLICABLE,
            embedded_term_state=EMBEDDED_NO,
            double_count_guard_id="EQUITY_BASE_ONCE",
            economic_effect_id="EQUITY_BASE",
            valuation_dependency=VALUATION_MTM_MARK_IN_EQUITY_BASE,
            currency_unit_domain=CURRENCY_DOMAIN_USDC,
            term_set_status=TERM_SET_SPECIFIED,
            completeness_participation=PARTICIPATION_PARTICIPATING,
            numeric_participation_state=NUMERIC_NOT_COMPUTED,
            contradiction_state=CONTRADICTION_NONE,
        ),
        build_algebra_term_v1(
            term_id=TERM_FEE,
            policy_id="U06",
            component_semantic_class=TERM_FEE,
            algebraic_role=ROLE_CONDITIONAL_ONCE_IN_BASE_OR_SINGLE_SUBTRACTION,
            operator_semantics=U06_FEES,
            sign_semantics=SIGN_CONDITIONAL,
            inclusion_state=INCLUSION_UNRESOLVED,
            embedded_term_state=EMBEDDED_CONDITIONAL,
            double_count_guard_id="U06_FEE_ONCE",
            economic_effect_id="FEE",
            valuation_dependency=VALUATION_NONE,
            currency_unit_domain=CURRENCY_DOMAIN_USDC,
            term_set_status=TERM_SET_SPECIFIED,
            completeness_participation=PARTICIPATION_BLOCKING,
            numeric_participation_state=NUMERIC_NOT_COMPUTED,
            contradiction_state=CONTRADICTION_NONE,
        ),
        build_algebra_term_v1(
            term_id=TERM_LIABILITY,
            policy_id="U05",
            component_semantic_class=TERM_LIABILITY,
            algebraic_role=ROLE_CONDITIONAL_SUBTRACTIVE_IF_NOT_IN_BASE,
            operator_semantics=U05_LIABILITIES_BORROWINGS,
            sign_semantics=SIGN_CONDITIONAL,
            inclusion_state=INCLUSION_UNRESOLVED,
            embedded_term_state=EMBEDDED_CONDITIONAL,
            double_count_guard_id="U05_LIABILITY_ONCE",
            economic_effect_id="LIABILITY",
            valuation_dependency=VALUATION_NONE,
            currency_unit_domain=CURRENCY_DOMAIN_USDC,
            term_set_status=TERM_SET_SPECIFIED,
            completeness_participation=PARTICIPATION_BLOCKING,
            numeric_participation_state=NUMERIC_NOT_COMPUTED,
            contradiction_state=CONTRADICTION_NONE,
        ),
        build_algebra_term_v1(
            term_id=TERM_P01_HAIRCUT_RESERVE_DEPLETION,
            policy_id="P01",
            component_semantic_class=TERM_P01_HAIRCUT_RESERVE_DEPLETION,
            algebraic_role=ROLE_SUBTRACTIVE,
            operator_semantics=P01_HAIRCUTS_RESERVE_DEPLETION,
            sign_semantics=SIGN_SUBTRACT,
            inclusion_state=INCLUSION_NOT_IN_BASE,
            embedded_term_state=EMBEDDED_NO,
            double_count_guard_id="P01_REDUCTION_ONCE",
            economic_effect_id="HAIRCUT_RESERVE_DEPLETION",
            valuation_dependency=VALUATION_NONE,
            currency_unit_domain=CURRENCY_DOMAIN_UNSPECIFIED,
            term_set_status=TERM_SET_SPECIFIED,
            completeness_participation=PARTICIPATION_PARTICIPATING,
            numeric_participation_state=NUMERIC_NOT_COMPUTED,
            contradiction_state=CONTRADICTION_NONE,
        ),
        build_algebra_term_v1(
            term_id=TERM_PENDING_ORDER_RESERVATION,
            policy_id="U04",
            component_semantic_class=TERM_PENDING_ORDER_RESERVATION,
            algebraic_role=ROLE_CONDITIONAL_SUBTRACTIVE_IF_NOT_IN_BASE,
            operator_semantics=U04_PENDING_ORDER_RESERVATIONS,
            sign_semantics=SIGN_CONDITIONAL,
            inclusion_state=INCLUSION_UNRESOLVED,
            embedded_term_state=EMBEDDED_CONDITIONAL,
            double_count_guard_id="U04_HOLD_ONCE",
            economic_effect_id="PENDING_ORDER_RESERVATION",
            valuation_dependency=VALUATION_NONE,
            currency_unit_domain=CURRENCY_DOMAIN_USDC,
            term_set_status=TERM_SET_SPECIFIED,
            completeness_participation=PARTICIPATION_BLOCKING,
            numeric_participation_state=NUMERIC_NOT_COMPUTED,
            contradiction_state=CONTRADICTION_NONE,
        ),
        build_algebra_term_v1(
            term_id=TERM_REALIZED_PNL,
            policy_id="U02",
            component_semantic_class=TERM_REALIZED_PNL,
            algebraic_role=ROLE_EMBEDDED_NOT_SEPARATE,
            operator_semantics=U02_REALIZED_UNREALIZED_TREATMENT,
            sign_semantics=SIGN_NONE,
            inclusion_state=INCLUSION_IN_BASE,
            embedded_term_state=EMBEDDED_YES,
            double_count_guard_id="U02_U03_MTM_ONCE",
            economic_effect_id="REALIZED_PNL",
            valuation_dependency=VALUATION_NONE,
            currency_unit_domain=CURRENCY_DOMAIN_USDC,
            term_set_status=TERM_SET_SPECIFIED,
            completeness_participation=PARTICIPATION_PARTICIPATING,
            numeric_participation_state=NUMERIC_NOT_COMPUTED,
            contradiction_state=CONTRADICTION_NONE,
        ),
        build_algebra_term_v1(
            term_id=TERM_SLIPPAGE,
            policy_id="SLIPPAGE",
            component_semantic_class=TERM_SLIPPAGE,
            algebraic_role=ROLE_PROHIBITED,
            operator_semantics="NOT_A_RATIFIED_U_TERM_PROHIBITED_INDEPENDENT_ADDEND",
            sign_semantics=SIGN_PROHIBITED,
            inclusion_state=INCLUSION_NOT_APPLICABLE,
            embedded_term_state=EMBEDDED_NOT_APPLICABLE,
            double_count_guard_id="SLIPPAGE_NOT_INDEPENDENT",
            economic_effect_id="SLIPPAGE",
            valuation_dependency=VALUATION_NONE,
            currency_unit_domain="NOT_APPLICABLE",
            term_set_status=TERM_SET_NOT_APPLICABLE,
            completeness_participation=PARTICIPATION_NOT_APPLICABLE,
            numeric_participation_state=NUMERIC_NOT_COMPUTED,
            contradiction_state=CONTRADICTION_NONE,
        ),
        build_algebra_term_v1(
            term_id=TERM_U01_ACCOUNT_MODE,
            policy_id="U01",
            component_semantic_class="NON_ALGEBRAIC_CONSTRAINT",
            algebraic_role=ROLE_NON_ALGEBRAIC,
            operator_semantics=U01_ACCOUNT_MODE_ROLE,
            sign_semantics=SIGN_NONE,
            inclusion_state=INCLUSION_NOT_APPLICABLE,
            embedded_term_state=EMBEDDED_NOT_APPLICABLE,
            double_count_guard_id="U01_NON_ALGEBRAIC",
            economic_effect_id="ACCOUNT_MODE_ELIGIBILITY",
            valuation_dependency=VALUATION_NONE,
            currency_unit_domain="NOT_APPLICABLE",
            term_set_status=TERM_SET_NOT_APPLICABLE,
            completeness_participation=PARTICIPATION_NOT_APPLICABLE,
            numeric_participation_state=NUMERIC_NOT_COMPUTED,
            contradiction_state=CONTRADICTION_NONE,
        ),
        build_algebra_term_v1(
            term_id=TERM_U07_RESTART_RECONCILIATION,
            policy_id="U07",
            component_semantic_class="NON_ALGEBRAIC_CONSTRAINT",
            algebraic_role=ROLE_NON_ALGEBRAIC,
            operator_semantics=U07_RESTART_RECONCILIATION,
            sign_semantics=SIGN_NONE,
            inclusion_state=INCLUSION_NOT_APPLICABLE,
            embedded_term_state=EMBEDDED_NOT_APPLICABLE,
            double_count_guard_id="U07_NON_ALGEBRAIC",
            economic_effect_id="RESTART_RECONCILIATION_CONSTRAINT",
            valuation_dependency=VALUATION_NONE,
            currency_unit_domain="NOT_APPLICABLE",
            term_set_status=TERM_SET_NOT_APPLICABLE,
            completeness_participation=PARTICIPATION_NOT_APPLICABLE,
            numeric_participation_state=NUMERIC_NOT_COMPUTED,
            contradiction_state=CONTRADICTION_NONE,
        ),
        build_algebra_term_v1(
            term_id=TERM_U08_CURRENCY_CONVERSION,
            policy_id="U08",
            component_semantic_class="NON_ALGEBRAIC_CONSTRAINT",
            algebraic_role=ROLE_NON_ALGEBRAIC,
            operator_semantics=U08_MULTI_CURRENCY_CONVERSION,
            sign_semantics=SIGN_NONE,
            inclusion_state=INCLUSION_NOT_APPLICABLE,
            embedded_term_state=EMBEDDED_NOT_APPLICABLE,
            double_count_guard_id="U08_CURRENCY_ONCE",
            economic_effect_id="CURRENCY_CONVERSION_CONSTRAINT",
            valuation_dependency=VALUATION_NONE,
            currency_unit_domain=CURRENCY_DOMAIN_USDC,
            term_set_status=TERM_SET_SPECIFIED,
            completeness_participation=PARTICIPATION_PARTICIPATING,
            numeric_participation_state=NUMERIC_NOT_COMPUTED,
            contradiction_state=CONTRADICTION_NONE,
        ),
        build_algebra_term_v1(
            term_id=TERM_U09_FRESHNESS,
            policy_id="U09",
            component_semantic_class="NON_ALGEBRAIC_CONSTRAINT",
            algebraic_role=ROLE_NON_ALGEBRAIC,
            operator_semantics=U09_FRESHNESS_CLASS,
            sign_semantics=SIGN_NONE,
            inclusion_state=INCLUSION_NOT_APPLICABLE,
            embedded_term_state=EMBEDDED_NOT_APPLICABLE,
            double_count_guard_id="U09_NON_ALGEBRAIC",
            economic_effect_id="FRESHNESS_CONSTRAINT",
            valuation_dependency=VALUATION_NONE,
            currency_unit_domain="NOT_APPLICABLE",
            term_set_status=TERM_SET_NOT_APPLICABLE,
            completeness_participation=PARTICIPATION_NOT_APPLICABLE,
            numeric_participation_state=NUMERIC_NOT_COMPUTED,
            contradiction_state=CONTRADICTION_NONE,
        ),
        build_algebra_term_v1(
            term_id=TERM_UNREALIZED_PNL_MTM,
            policy_id="U03",
            component_semantic_class=TERM_UNREALIZED_PNL_MTM,
            algebraic_role=ROLE_EMBEDDED_NOT_SEPARATE,
            operator_semantics=U03_OPEN_POSITION_TREATMENT,
            sign_semantics=SIGN_NONE,
            inclusion_state=INCLUSION_IN_BASE,
            embedded_term_state=EMBEDDED_YES,
            double_count_guard_id="U02_U03_MTM_ONCE",
            economic_effect_id="UNREALIZED_PNL_MTM",
            valuation_dependency=VALUATION_NOTIONAL_PROHIBITED_AS_ADDEND,
            currency_unit_domain=CURRENCY_DOMAIN_USDC,
            term_set_status=TERM_SET_SPECIFIED,
            completeness_participation=PARTICIPATION_PARTICIPATING,
            numeric_participation_state=NUMERIC_NOT_COMPUTED,
            contradiction_state=CONTRADICTION_NONE,
        ),
    )


def _validate_term_set(terms: Tuple[AlgebraTermV1, ...]) -> None:
    if not terms:
        raise ReconstructionAlgebraContractError("RECONSTRUCTION_ALGEBRA_TERM_SET_EMPTY")
    ids = tuple(term.term_id for term in terms)
    if len(set(ids)) != len(ids):
        raise ReconstructionAlgebraContractError("RECONSTRUCTION_ALGEBRA_TERM_ID_DUPLICATE")
    if tuple(sorted(ids)) != ids:
        raise ReconstructionAlgebraContractError("RECONSTRUCTION_ALGEBRA_TERM_SET_NOT_SORTED")
    missing = [name for name in REQUIRED_TERM_IDS if name not in ids]
    if missing:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_REQUIRED_TERM_MISSING:" + ",".join(missing)
        )
    extra = [name for name in ids if name not in REQUIRED_TERM_IDS]
    if extra:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_TERM_ID_UNKNOWN:" + ",".join(extra)
        )
    effect_roles: dict[str, str] = {}
    for term in terms:
        if term.algebraic_role in {
            ROLE_PROHIBITED,
            ROLE_NON_ALGEBRAIC,
            ROLE_VALUATION_INPUT_ONLY,
        }:
            continue
        prior = effect_roles.get(term.economic_effect_id)
        if prior is not None:
            raise ReconstructionAlgebraContractError(
                f"RECONSTRUCTION_ALGEBRA_DUPLICATE_ECONOMIC_EFFECT:{term.economic_effect_id}"
            )
        effect_roles[term.economic_effect_id] = term.algebraic_role


def _completeness_blockers(
    *,
    terms: Tuple[AlgebraTermV1, ...],
    completeness_status: str,
    contradiction_status: str,
    canonical_formula_status: str,
) -> Tuple[str, ...]:
    reasons: list[str] = []
    pins = _policy_pins()
    if pins["P01_HAIRCUTS_RESERVE_DEPLETION"] != P01_HAIRCUTS_RESERVE_DEPLETION:
        reasons.append("P01_CANONICAL_PIN_DRIFT")
    if pins["P01_MAY_INCREASE_EQUITY"] is True:
        reasons.append("P01_MAY_INCREASE_EQUITY_FORBIDDEN")
    if pins["U02_REALIZED_UNREALIZED_TREATMENT"] != U02_REALIZED_UNREALIZED_TREATMENT:
        reasons.append("U02_CANONICAL_PIN_DRIFT")
    if pins["U03_OPEN_POSITION_TREATMENT"] != U03_OPEN_POSITION_TREATMENT:
        reasons.append("U03_CANONICAL_PIN_DRIFT")
    if pins["U04_PENDING_ORDER_RESERVATIONS"] != U04_PENDING_ORDER_RESERVATIONS:
        reasons.append("U04_CANONICAL_PIN_DRIFT")
    if pins["U05_LIABILITIES_BORROWINGS"] != U05_LIABILITIES_BORROWINGS:
        reasons.append("U05_CANONICAL_PIN_DRIFT")
    if pins["U06_FEES"] != U06_FEES:
        reasons.append("U06_CANONICAL_PIN_DRIFT")
    if pins["U08_MULTI_CURRENCY_CONVERSION"] != U08_MULTI_CURRENCY_CONVERSION:
        reasons.append("U08_CANONICAL_PIN_DRIFT")
    if not pins["DOUBLE_COUNT_CONTROL_U02_U03_MTM_ONCE"]:
        reasons.append("DOUBLE_COUNT_U02_U03_GUARD_MISSING")
    if not pins["DOUBLE_COUNT_CONTROL_U04_HOLD_ONCE"]:
        reasons.append("DOUBLE_COUNT_U04_GUARD_MISSING")
    if not pins["DOUBLE_COUNT_CONTROL_U05_LIABILITY_ONCE"]:
        reasons.append("DOUBLE_COUNT_U05_GUARD_MISSING")
    if not pins["DOUBLE_COUNT_CONTROL_U06_FEE_ONCE"]:
        reasons.append("DOUBLE_COUNT_U06_GUARD_MISSING")
    for term in terms:
        if term.contradiction_state == CONTRADICTION_PRESENT:
            reasons.append("CONTRADICTORY_TERM")
        if term.term_id == TERM_P01_HAIRCUT_RESERVE_DEPLETION:
            if term.term_set_status != TERM_SET_SPECIFIED:
                reasons.append("P01_TERM_SET_STATUS_DRIFT")
            if term.algebraic_role != ROLE_SUBTRACTIVE:
                reasons.append("P01_OPERATOR_MUST_BE_SUBTRACTION")
        if term.term_id == TERM_PENDING_ORDER_RESERVATION:
            if term.inclusion_state == INCLUSION_UNRESOLVED:
                reasons.append("U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED")
            if term.algebraic_role == ROLE_UNRESOLVED:
                reasons.append("UNRESOLVED_REQUIRED_TERM")
        if term.term_id == TERM_LIABILITY:
            if term.inclusion_state == INCLUSION_UNRESOLVED:
                reasons.append("U05_LIABILITY_INCLUSION_OR_VALUE_UNRESOLVED")
        if term.term_id == TERM_FEE:
            if term.inclusion_state == INCLUSION_UNRESOLVED:
                reasons.append("U06_FEE_INCLUSION_UNRESOLVED")
        if (
            term.completeness_participation == PARTICIPATION_BLOCKING
            and completeness_status == ALGEBRA_STATUS_COMPLETE
        ):
            reasons.append("BLOCKING_TERM_PREVENTS_COMPLETENESS")
        if term.numeric_participation_state == NUMERIC_MISSING:
            reasons.append("MISSING_TERM_NOT_ZERO")
        if term.numeric_participation_state == NUMERIC_MALFORMED:
            reasons.append("MALFORMED_TERM_NOT_ZERO")
        if term.algebraic_role == ROLE_UNRESOLVED:
            reasons.append("UNRESOLVED_REQUIRED_TERM")
    if contradiction_status == CONTRADICTION_PRESENT:
        reasons.append("CONTRADICTION_PRESENT")
    if canonical_formula_status != CANONICAL_FORMULA_STATUS_UNPROVEN:
        reasons.append("CANONICAL_FORMULA_MUST_REMAIN_UNPROVEN")
    if RECONSTRUCTION_ALGEBRA_COMPLETE is True:
        reasons.append("RECONSTRUCTION_ALGEBRA_COMPLETE_PIN_TRUE")
    return tuple(sorted(set(reasons)))


@dataclass(frozen=True)
class ReconstructionAlgebraContractV1:
    """Typed immutable reconstruction algebra contract. Schema only."""

    algebra_contract_id: str
    algebra_contract_version: str
    reconstruction_contract_schema_class: str
    target_semantic_dimension_id: str
    algebra_representation: str
    algebra_completeness_status: str
    canonical_formula_status: str
    canonical_formula_representation: str
    unresolved_required_terms: str
    contradiction_status: str
    currency_unit_compatibility_status: str
    valuation_dependency_status: str
    reconstruction_algebra_authority_effect: str
    provenance_digest: str
    terms: Tuple[AlgebraTermV1, ...]

    def __post_init__(self) -> None:
        _validate_reconstruction_algebra_contract_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {
            "algebra_contract_id": self.algebra_contract_id,
            "algebra_contract_version": self.algebra_contract_version,
            "reconstruction_contract_schema_class": (self.reconstruction_contract_schema_class),
            "target_semantic_dimension_id": self.target_semantic_dimension_id,
            "algebra_representation": self.algebra_representation,
            "algebra_completeness_status": self.algebra_completeness_status,
            "canonical_formula_status": self.canonical_formula_status,
            "canonical_formula_representation": self.canonical_formula_representation,
            "unresolved_required_terms": self.unresolved_required_terms,
            "contradiction_status": self.contradiction_status,
            "currency_unit_compatibility_status": self.currency_unit_compatibility_status,
            "valuation_dependency_status": self.valuation_dependency_status,
            "reconstruction_algebra_authority_effect": (
                self.reconstruction_algebra_authority_effect
            ),
            "term_vector": encode_algebra_term_vector_v1(self.terms),
            "provenance_digest": self.provenance_digest,
        }
        return {key: values[key] for key in ALGEBRA_PROVENANCE_REQUIRED_FIELDS}


def _validate_reconstruction_algebra_contract_v1(
    contract: ReconstructionAlgebraContractV1,
) -> None:
    if RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT is not True:
        raise ReconstructionAlgebraContractError("RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT_REQUIRED")
    if RECONSTRUCTION_ALGEBRA_COMPLETE is True:
        raise ReconstructionAlgebraContractError("RECONSTRUCTION_ALGEBRA_COMPLETE_PIN_FORBIDDEN")
    if INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT is not True:
        raise ReconstructionAlgebraContractError("INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT_REQUIRED")
    if INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT is True:
        raise ReconstructionAlgebraContractError(
            "INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if INTERNAL_RECONSTRUCTION_PROVEN is True:
        raise ReconstructionAlgebraContractError("INTERNAL_RECONSTRUCTION_PROVEN_PIN_FORBIDDEN")
    if SOURCE_SELECTED is True or SOURCE_OBJECT_PRESENT is True:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_SOURCE_SELECTION_FORBIDDEN"
        )
    if GOVERNED_PRODUCER_CREATED is True:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_GOVERNED_PRODUCER_CREATED_FORBIDDEN"
        )
    if RECONCILIATION_CONTRACT_CREATED is True:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_RECONCILIATION_CONTRACT_CREATED_FORBIDDEN"
        )
    if SEMANTIC_MAPPING_PROVEN is True or INCLUSION_PROVEN is True:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_MAPPING_OR_INCLUSION_PROVEN_FORBIDDEN"
        )
    if EQUITY_DIMENSION_BOUND is True:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_EQUITY_DIMENSION_BOUND_FORBIDDEN"
        )
    if MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING is True:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_TARGET_DIMENSION_MAPPING_FORBIDDEN"
        )
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_LIVE_RESTART_RECONSTRUCTED_FORBIDDEN"
        )
    algebra_id = _require_non_empty_str(
        field="algebra_contract_id", raw=contract.algebra_contract_id
    )
    version = _require_non_empty_str(
        field="algebra_contract_version", raw=contract.algebra_contract_version
    )
    reconstruction_ref = _require_non_empty_str(
        field="reconstruction_contract_schema_class",
        raw=contract.reconstruction_contract_schema_class,
    )
    target = _require_non_empty_str(
        field="target_semantic_dimension_id", raw=contract.target_semantic_dimension_id
    )
    representation = _require_non_empty_str(
        field="algebra_representation", raw=contract.algebra_representation
    )
    completeness = _require_non_empty_str(
        field="algebra_completeness_status", raw=contract.algebra_completeness_status
    )
    formula_status = _require_non_empty_str(
        field="canonical_formula_status", raw=contract.canonical_formula_status
    )
    formula = _require_str_allow_empty(
        field="canonical_formula_representation",
        raw=contract.canonical_formula_representation,
    )
    unresolved = _require_non_empty_str(
        field="unresolved_required_terms", raw=contract.unresolved_required_terms
    )
    contradiction = _require_non_empty_str(
        field="contradiction_status", raw=contract.contradiction_status
    )
    currency_status = _require_non_empty_str(
        field="currency_unit_compatibility_status",
        raw=contract.currency_unit_compatibility_status,
    )
    valuation_status = _require_non_empty_str(
        field="valuation_dependency_status", raw=contract.valuation_dependency_status
    )
    effect = _require_non_empty_str(
        field="reconstruction_algebra_authority_effect",
        raw=contract.reconstruction_algebra_authority_effect,
    )
    digest = _require_non_empty_str(field="provenance_digest", raw=contract.provenance_digest)
    if not isinstance(contract.terms, tuple) or not contract.terms:
        raise ReconstructionAlgebraContractError("RECONSTRUCTION_ALGEBRA_TERMS_REQUIRED")
    if any(not isinstance(term, AlgebraTermV1) for term in contract.terms):
        raise ReconstructionAlgebraContractError("RECONSTRUCTION_ALGEBRA_TERMS_MUST_BE_TYPED")
    _validate_term_set(contract.terms)
    if version != ALGEBRA_CONTRACT_VERSION:
        raise ReconstructionAlgebraContractError("RECONSTRUCTION_ALGEBRA_CONTRACT_VERSION_MISMATCH")
    if reconstruction_ref != RECONSTRUCTION_CONTRACT_SCHEMA_CLASS:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_RECONSTRUCTION_CONTRACT_REFERENCE_MISMATCH"
        )
    if target != DIMENSION_ID:
        raise ReconstructionAlgebraContractError("RECONSTRUCTION_ALGEBRA_TARGET_DIMENSION_MISMATCH")
    if representation != ALGEBRA_REPRESENTATION:
        raise ReconstructionAlgebraContractError("RECONSTRUCTION_ALGEBRA_REPRESENTATION_MISMATCH")
    if completeness == ALGEBRA_STATUS_COMPLETE:
        raise ReconstructionAlgebraContractError("RECONSTRUCTION_ALGEBRA_COMPLETE_STATUS_FORBIDDEN")
    if completeness != ALGEBRA_STATUS_INCOMPLETE:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_STATUS_MUST_REMAIN_INCOMPLETE"
        )
    if formula_status == CANONICAL_FORMULA_STATUS_PROVEN:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_CANONICAL_FORMULA_PROVEN_FORBIDDEN"
        )
    if formula_status != CANONICAL_FORMULA_STATUS_UNPROVEN:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_CANONICAL_FORMULA_STATUS_MUST_REMAIN_UNPROVEN"
        )
    if formula != CANONICAL_FORMULA_REPRESENTATION:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_CANONICAL_FORMULA_MUST_REMAIN_EMPTY"
        )
    if REJECTED_NAIVE_FORMULA in formula:
        raise ReconstructionAlgebraContractError("RECONSTRUCTION_ALGEBRA_NAIVE_FORMULA_REJECTED")
    if contradiction not in {CONTRADICTION_NONE, CONTRADICTION_PRESENT}:
        raise ReconstructionAlgebraContractError(
            f"RECONSTRUCTION_ALGEBRA_CONTRADICTION_STATUS_UNKNOWN:{contradiction}"
        )
    if effect != RECONSTRUCTION_ALGEBRA_AUTHORITY_EFFECT or effect != ALGEBRA_AUTHORITY_EFFECT_NONE:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )
    expected_unresolved = ",".join(UNRESOLVED_ALGEBRA_TERMS)
    if unresolved != expected_unresolved:
        raise ReconstructionAlgebraContractError("RECONSTRUCTION_ALGEBRA_UNRESOLVED_TERMS_MISMATCH")
    if currency_status != U08_MULTI_CURRENCY_CONVERSION:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_CURRENCY_COMPATIBILITY_MISMATCH"
        )
    if valuation_status != "U03_MTM_IN_EQUITY_BASE_NOTIONAL_NOT_ADDITIVE":
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_VALUATION_DEPENDENCY_MISMATCH"
        )
    blockers = _completeness_blockers(
        terms=contract.terms,
        completeness_status=completeness,
        contradiction_status=contradiction,
        canonical_formula_status=formula_status,
    )
    if not blockers:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_COMPLETENESS_BLOCKERS_REQUIRED"
        )
    if EARLIEST_UNRESOLVED_ALGEBRA_TERM not in blockers:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_EARLIEST_UNRESOLVED_TERM_REQUIRED"
        )
    for field, raw in (
        ("algebra_contract_id", algebra_id),
        ("reconstruction_contract_schema_class", reconstruction_ref),
        ("target_semantic_dimension_id", target),
    ):
        _reject_fallback_chain(field=field, raw=raw)
        _reject_forbidden_authority_token(field=field, raw=raw)
    canonical = contract.to_canonical_dict()
    expected_digest = compute_reconstruction_algebra_provenance_digest_v1(canonical)
    if not _SHA256_HEX.fullmatch(digest):
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_PROVENANCE_DIGEST_NOT_SHA256"
        )
    if digest != expected_digest:
        raise ReconstructionAlgebraContractError(
            "RECONSTRUCTION_ALGEBRA_PROVENANCE_DIGEST_MISMATCH"
        )


def build_reconstruction_algebra_contract_v1(
    **fields: Any,
) -> ReconstructionAlgebraContractV1:
    """Construct the typed algebra contract. Does not reconstruct equity."""

    terms_raw = fields.get("terms")
    if terms_raw is None:
        typed_terms = _canonical_terms()
    else:
        if not isinstance(terms_raw, tuple) or not terms_raw:
            raise ReconstructionAlgebraContractError("RECONSTRUCTION_ALGEBRA_TERMS_REQUIRED")
        terms: list[AlgebraTermV1] = []
        for item in terms_raw:
            if isinstance(item, AlgebraTermV1):
                terms.append(item)
            elif isinstance(item, Mapping):
                terms.append(build_algebra_term_v1(**dict(item)))
            else:
                raise ReconstructionAlgebraContractError(
                    "RECONSTRUCTION_ALGEBRA_TERMS_MUST_BE_TYPED"
                )
        typed_terms = tuple(terms)
    payload = dict(fields)
    payload["terms"] = typed_terms
    if "algebra_contract_version" not in payload:
        payload["algebra_contract_version"] = ALGEBRA_CONTRACT_VERSION
    if "reconstruction_contract_schema_class" not in payload:
        payload["reconstruction_contract_schema_class"] = RECONSTRUCTION_CONTRACT_SCHEMA_CLASS
    if "target_semantic_dimension_id" not in payload:
        payload["target_semantic_dimension_id"] = DIMENSION_ID
    if "algebra_representation" not in payload:
        payload["algebra_representation"] = ALGEBRA_REPRESENTATION
    if "algebra_completeness_status" not in payload:
        payload["algebra_completeness_status"] = ALGEBRA_STATUS_INCOMPLETE
    if "canonical_formula_status" not in payload:
        payload["canonical_formula_status"] = CANONICAL_FORMULA_STATUS_UNPROVEN
    if "canonical_formula_representation" not in payload:
        payload["canonical_formula_representation"] = CANONICAL_FORMULA_REPRESENTATION
    if "unresolved_required_terms" not in payload:
        payload["unresolved_required_terms"] = ",".join(UNRESOLVED_ALGEBRA_TERMS)
    if "contradiction_status" not in payload:
        payload["contradiction_status"] = CONTRADICTION_NONE
    if "currency_unit_compatibility_status" not in payload:
        payload["currency_unit_compatibility_status"] = U08_MULTI_CURRENCY_CONVERSION
    if "valuation_dependency_status" not in payload:
        payload["valuation_dependency_status"] = "U03_MTM_IN_EQUITY_BASE_NOTIONAL_NOT_ADDITIVE"
    if "reconstruction_algebra_authority_effect" not in payload:
        payload["reconstruction_algebra_authority_effect"] = ALGEBRA_AUTHORITY_EFFECT_NONE
    if "term_vector" not in payload:
        payload["term_vector"] = encode_algebra_term_vector_v1(typed_terms)
    attached = attach_reconstruction_algebra_provenance_digest_v1(
        {key: value for key, value in payload.items() if key != "terms"}
    )
    attached["terms"] = typed_terms
    return ReconstructionAlgebraContractV1(
        algebra_contract_id=attached["algebra_contract_id"],
        algebra_contract_version=attached["algebra_contract_version"],
        reconstruction_contract_schema_class=attached["reconstruction_contract_schema_class"],
        target_semantic_dimension_id=attached["target_semantic_dimension_id"],
        algebra_representation=attached["algebra_representation"],
        algebra_completeness_status=attached["algebra_completeness_status"],
        canonical_formula_status=attached["canonical_formula_status"],
        canonical_formula_representation=attached["canonical_formula_representation"],
        unresolved_required_terms=attached["unresolved_required_terms"],
        contradiction_status=attached["contradiction_status"],
        currency_unit_compatibility_status=attached["currency_unit_compatibility_status"],
        valuation_dependency_status=attached["valuation_dependency_status"],
        reconstruction_algebra_authority_effect=attached["reconstruction_algebra_authority_effect"],
        provenance_digest=attached["provenance_digest"],
        terms=typed_terms,
    )
