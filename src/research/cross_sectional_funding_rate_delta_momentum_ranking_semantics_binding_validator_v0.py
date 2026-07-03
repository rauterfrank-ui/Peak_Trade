"""Fail-closed validator for cross_sectional_funding_rate_delta_momentum_ranking_semantics_binding.v0."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from src.research.cross_sectional_funding_rate_delta_momentum_ranking_semantics_binding_v0 import (
    DIRECTION_POLICY,
    DIGEST_BINDING_KEYS,
    EXTERNAL_BINDING_KEYS,
    HYPOTHESIS_ID,
    NUMERIC_BINDING_KEYS,
    SCHEMA_VERSION,
    SCORE_FAMILY_POLICY,
    BindingFieldStatus,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUNDING_RATE_DELTA_MOMENTUM_RANKING_SEMANTICS_BINDING_VALIDATOR_V0=true"
)

POSITIVE_NUMERIC_KEYS = frozenset(NUMERIC_BINDING_KEYS)


class ValidationVerdict(str, Enum):
    ACCEPTED_INCOMPLETE = "ACCEPTED_INCOMPLETE"
    ACCEPTED_COMPLETE = "ACCEPTED_COMPLETE"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class FundingDeltaRankingSemanticsBindingValidationResult:
    verdict: ValidationVerdict
    valid: bool
    fail_reasons: tuple[str, ...]
    binding_status: Mapping[str, Any]


def _is_bound(field: Mapping[str, Any]) -> bool:
    return field.get("status") == BindingFieldStatus.BOUND.value


def validate_funding_rate_delta_momentum_ranking_semantics_binding_v0(
    binding: Mapping[str, Any],
) -> FundingDeltaRankingSemanticsBindingValidationResult:
    fail_reasons: list[str] = []

    if binding.get("schema_version") != SCHEMA_VERSION:
        fail_reasons.append("INVALID_SCHEMA_VERSION")
    if binding.get("hypothesis_id") != HYPOTHESIS_ID:
        fail_reasons.append("HYPOTHESIS_ID_MISMATCH")

    policy = binding.get("policy_classes", {})
    if policy.get("score_family_policy") != SCORE_FAMILY_POLICY:
        fail_reasons.append("SCORE_FAMILY_POLICY_MISMATCH")
    if policy.get("direction_policy") != DIRECTION_POLICY:
        fail_reasons.append("DIRECTION_POLICY_MISMATCH")

    numeric = binding.get("numeric_bindings", {})
    for key in NUMERIC_BINDING_KEYS:
        field = numeric.get(key, {})
        if not _is_bound(field):
            fail_reasons.append(f"NUMERIC_BINDING_UNBOUND:{key}")
            continue
        if key in POSITIVE_NUMERIC_KEYS:
            value = field.get("value")
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                fail_reasons.append(f"NON_POSITIVE_NUMERIC:{key}")

    external = binding.get("external_bindings", {})
    for key in EXTERNAL_BINDING_KEYS:
        if not _is_bound(external.get(key, {})):
            fail_reasons.append(f"EXTERNAL_BINDING_UNBOUND:{key}")

    digest = binding.get("digest_bindings", {})
    for key in DIGEST_BINDING_KEYS:
        if not _is_bound(digest.get(key, {})):
            fail_reasons.append(f"DIGEST_BINDING_UNBOUND:{key}")

    status = binding.get("binding_status", {})
    overall = status.get("overall_binding_status")
    all_bound = not fail_reasons
    if all_bound and overall != "COMPLETE":
        fail_reasons.append("INCOMPLETE_BINDING_MARKED_INCOMPLETE")

    if fail_reasons:
        return FundingDeltaRankingSemanticsBindingValidationResult(
            verdict=ValidationVerdict.REJECTED,
            valid=False,
            fail_reasons=tuple(fail_reasons),
            binding_status=status,
        )
    return FundingDeltaRankingSemanticsBindingValidationResult(
        verdict=ValidationVerdict.ACCEPTED_COMPLETE,
        valid=True,
        fail_reasons=(),
        binding_status=status,
    )
