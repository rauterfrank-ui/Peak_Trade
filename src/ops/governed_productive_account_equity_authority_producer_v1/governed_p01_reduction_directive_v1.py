"""Typed governed P01 reduction directive.

The Owner-ratified concrete predicate-input member. Schema/evaluator only.
Not a productive external source. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    P01_EXACT_MEMBER_IDENTITY_SET,
    P01_PARENT_DIMENSION_COMPATIBILITY,
    P01_PREDICATE_INPUT_MEMBER,
    P01_PREDICATE_INPUT_MEMBER_CLASS,
    P01_SEMANTIC_DIMENSION,
    P01_VALUE_UNIT_CLASS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_value_unit_class_contract_v1 import (
    MEMBER_ID,
    VALUE_UNIT_CLASS,
)

DIRECTIVE_TYPE = P01_PREDICATE_INPUT_MEMBER
DIRECTIVE_VERSION = "v1"
DIRECTIVE_CLASS = P01_PREDICATE_INPUT_MEMBER_CLASS
STATE_APPLIES = "APPLIES"
STATE_DOES_NOT_APPLY = "DOES_NOT_APPLY"
STATE_UNKNOWN_FAIL_CLOSED = "UNKNOWN_FAIL_CLOSED"
ALLOWED_APPLICABILITY_STATES: tuple[str, ...] = (
    STATE_APPLIES,
    STATE_DOES_NOT_APPLY,
    STATE_UNKNOWN_FAIL_CLOSED,
)
AMOUNT_ABSENT = ""
TRUE_PIN = "true"
FALSE_PIN = "false"
AUTHORITY_EFFECT_NONE = "NONE"
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
DIRECTIVE_VECTOR_FIELDS: tuple[str, ...] = (
    "directive_id",
    "directive_version",
    "directive_type",
    "directive_class",
    "member_id",
    "applicability_state",
    "authorized_reduction_amount",
    "amount_present",
    "semantic_dimension",
    "value_unit_class",
    "parent_dimension_compatibility",
    "requires_dimensional_transformation",
    "evidence_ref",
    "source_class",
    "authority_effect",
)


class GovernedP01ReductionDirectiveError(ValueError):
    """Fail-closed governed P01 reduction directive violation."""


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise GovernedP01ReductionDirectiveError(f"P01_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise GovernedP01ReductionDirectiveError(f"P01_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise GovernedP01ReductionDirectiveError(f"P01_FIELD_MISSING:{field}")
    return text


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_governed_p01_reduction_directive_digest_v1(canonical: Mapping[str, str]) -> str:
    payload = {key: canonical[key] for key in DIRECTIVE_VECTOR_FIELDS}
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def parse_p01_reduction_amount_v1(raw: str) -> Decimal:
    try:
        amount = Decimal(raw)
    except (InvalidOperation, ValueError) as exc:
        raise GovernedP01ReductionDirectiveError("P01_AMOUNT_MALFORMED") from exc
    if not amount.is_finite():
        raise GovernedP01ReductionDirectiveError("P01_AMOUNT_NON_FINITE")
    if amount < 0:
        raise GovernedP01ReductionDirectiveError("P01_NEGATIVE_AMOUNT_FORBIDDEN")
    return amount


@dataclass(frozen=True)
class GovernedP01ReductionDirectiveV1:
    """Typed immutable P01 reduction directive. Not a producer."""

    directive_id: str
    directive_version: str
    directive_type: str
    directive_class: str
    member_id: str
    applicability_state: str
    authorized_reduction_amount: str
    amount_present: str
    semantic_dimension: str
    value_unit_class: str
    parent_dimension_compatibility: str
    requires_dimensional_transformation: str
    evidence_ref: str
    source_class: str
    authority_effect: str
    provenance_digest: str
    semantic_digest: str

    def __post_init__(self) -> None:
        _validate_governed_p01_reduction_directive_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {name: getattr(self, name) for name in DIRECTIVE_VECTOR_FIELDS}
        values["provenance_digest"] = self.provenance_digest
        values["semantic_digest"] = self.semantic_digest
        return values


def _validate_governed_p01_reduction_directive_v1(
    directive: GovernedP01ReductionDirectiveV1,
) -> None:
    for field in DIRECTIVE_VECTOR_FIELDS:
        if field in {"authorized_reduction_amount"}:
            raw = getattr(directive, field)
            if raw is None or not isinstance(raw, str) or raw != raw.strip():
                raise GovernedP01ReductionDirectiveError(f"P01_FIELD_NOT_STRING:{field}")
            continue
        _require_non_empty_str(field=field, raw=getattr(directive, field))
    digest = _require_non_empty_str(field="provenance_digest", raw=directive.provenance_digest)
    semantic = _require_non_empty_str(field="semantic_digest", raw=directive.semantic_digest)
    if _SHA256_HEX.fullmatch(digest) is None or _SHA256_HEX.fullmatch(semantic) is None:
        raise GovernedP01ReductionDirectiveError("P01_PROVENANCE_DIGEST_MALFORMED")
    expected = compute_governed_p01_reduction_directive_digest_v1(
        {key: getattr(directive, key) for key in DIRECTIVE_VECTOR_FIELDS}
    )
    if digest != expected or semantic != expected:
        raise GovernedP01ReductionDirectiveError("P01_PROVENANCE_DIGEST_MISMATCH")
    if directive.directive_version != DIRECTIVE_VERSION:
        raise GovernedP01ReductionDirectiveError("P01_UNSUPPORTED_DIRECTIVE_VERSION")
    if directive.directive_type != DIRECTIVE_TYPE:
        raise GovernedP01ReductionDirectiveError("P01_UNSUPPORTED_DIRECTIVE_TYPE")
    if directive.directive_class != DIRECTIVE_CLASS:
        raise GovernedP01ReductionDirectiveError("P01_DIRECTIVE_CLASS_MISMATCH")
    if directive.member_id != MEMBER_ID or directive.member_id != P01_EXACT_MEMBER_IDENTITY_SET:
        raise GovernedP01ReductionDirectiveError("P01_UNRATIFIED_MEMBER")
    if directive.applicability_state not in ALLOWED_APPLICABILITY_STATES:
        raise GovernedP01ReductionDirectiveError("P01_UNSUPPORTED_APPLICABILITY_STATE")
    if directive.value_unit_class != VALUE_UNIT_CLASS:
        raise GovernedP01ReductionDirectiveError("P01_VALUE_UNIT_CLASS_MISMATCH")
    if directive.semantic_dimension != P01_SEMANTIC_DIMENSION:
        raise GovernedP01ReductionDirectiveError("P01_SEMANTIC_DIMENSION_MISMATCH")
    if directive.parent_dimension_compatibility != P01_PARENT_DIMENSION_COMPATIBILITY:
        raise GovernedP01ReductionDirectiveError("P01_PARENT_DIMENSION_MISMATCH")
    if directive.requires_dimensional_transformation != FALSE_PIN:
        raise GovernedP01ReductionDirectiveError("P01_DIMENSIONAL_TRANSFORMATION_FORBIDDEN")
    if directive.source_class != DIRECTIVE_CLASS:
        raise GovernedP01ReductionDirectiveError("P01_SOURCE_CLASS_MISMATCH")
    if directive.authority_effect != AUTHORITY_EFFECT_NONE:
        raise GovernedP01ReductionDirectiveError("P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    amount_present = directive.amount_present
    amount_raw = directive.authorized_reduction_amount
    if amount_present not in {TRUE_PIN, FALSE_PIN}:
        raise GovernedP01ReductionDirectiveError("P01_AMOUNT_PRESENT_MALFORMED")
    if directive.applicability_state == STATE_APPLIES:
        if amount_present != TRUE_PIN or amount_raw == AMOUNT_ABSENT:
            raise GovernedP01ReductionDirectiveError("P01_APPLIES_AMOUNT_REQUIRED")
        parse_p01_reduction_amount_v1(amount_raw)
        return
    if directive.applicability_state == STATE_DOES_NOT_APPLY:
        if amount_present == FALSE_PIN:
            if amount_raw != AMOUNT_ABSENT:
                raise GovernedP01ReductionDirectiveError("P01_DOES_NOT_APPLY_AMOUNT_CONTRADICTION")
            return
        amount = parse_p01_reduction_amount_v1(amount_raw)
        if amount != Decimal("0"):
            raise GovernedP01ReductionDirectiveError("P01_DOES_NOT_APPLY_NONZERO_FORBIDDEN")
        return
    if amount_present == TRUE_PIN:
        parse_p01_reduction_amount_v1(amount_raw)


def build_governed_p01_reduction_directive_v1(
    *,
    directive_id: str,
    applicability_state: str,
    evidence_ref: str,
    authorized_reduction_amount: str = AMOUNT_ABSENT,
    amount_present: str | None = None,
    **overrides: Any,
) -> GovernedP01ReductionDirectiveV1:
    present = amount_present
    if present is None:
        present = FALSE_PIN if authorized_reduction_amount == AMOUNT_ABSENT else TRUE_PIN
    payload: dict[str, Any] = dict(overrides)
    defaults: dict[str, str] = {
        "directive_id": directive_id,
        "directive_version": DIRECTIVE_VERSION,
        "directive_type": DIRECTIVE_TYPE,
        "directive_class": DIRECTIVE_CLASS,
        "member_id": MEMBER_ID,
        "applicability_state": applicability_state,
        "authorized_reduction_amount": authorized_reduction_amount,
        "amount_present": present,
        "semantic_dimension": P01_SEMANTIC_DIMENSION,
        "value_unit_class": P01_VALUE_UNIT_CLASS,
        "parent_dimension_compatibility": P01_PARENT_DIMENSION_COMPATIBILITY,
        "requires_dimensional_transformation": FALSE_PIN,
        "evidence_ref": evidence_ref,
        "source_class": DIRECTIVE_CLASS,
        "authority_effect": AUTHORITY_EFFECT_NONE,
    }
    for key, value in defaults.items():
        payload.setdefault(key, value)
    canonical = {key: str(payload[key]) for key in DIRECTIVE_VECTOR_FIELDS}
    digest = compute_governed_p01_reduction_directive_digest_v1(canonical)
    return GovernedP01ReductionDirectiveV1(
        **canonical,
        provenance_digest=digest,
        semantic_digest=digest,
    )
