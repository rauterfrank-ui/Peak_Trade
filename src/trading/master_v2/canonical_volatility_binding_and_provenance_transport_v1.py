"""Canonical volatility binding and provenance transport v1 (C1).

Typed-transport Model A: ``CanonicalVolatilityEstimateV1`` ends on
``CanonicalMarketContextV1.canonical_volatility_estimate``. Exactly one
typed validation and exactly one legacy-float adaptation (owned by the
typed consumption contract) occur before float consumers.

Pure offline scaffold: no runtime producer cutover, no default mutation,
no parameter change, no live authorization.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional

from trading.master_v2.canonical_market_context_v1 import (
    CanonicalMarketContextBindingOutcome,
    CanonicalMarketContextBlockReason,
    CanonicalMarketContextEligibilityV1,
    CanonicalMarketContextV1,
    evaluate_canonical_market_context_eligibility,
    with_computed_input_digest,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CanonicalTradingDecisionEvidenceV1,
    CanonicalVolatilityDecisionEvidenceProvenanceV1,
)
from trading.master_v2.canonical_volatility_estimate_feature_contract_v1 import (
    CONTRACT_OWNER as SEMANTICS_OWNER,
)
from trading.master_v2.canonical_volatility_estimate_materializer_v1 import (
    MATERIALIZER_OWNER as ESTIMATOR_OWNER,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    CANONICAL_HORIZON,
    CanonicalVolatilityEstimateV1,
    CanonicalVolatilityTypedConsumptionError,
    LEGACY_ADAPTER_OWNER,
    TYPED_CARRIER_OWNER,
    adapt_canonical_volatility_estimate_to_legacy_float_v1,
    validate_canonical_volatility_estimate_v1,
)

PACKAGE_MARKER = "MASTER_V2_CANONICAL_VOLATILITY_BINDING_AND_PROVENANCE_TRANSPORT_V1=true"

CAPABILITY_ID = "MASTER_V2_CANONICAL_VOLATILITY_BINDING_AND_PROVENANCE_TRANSPORT_V1"
CAPABILITY_VERSION = "canonical_volatility_binding_and_provenance_transport/v1"
BINDING_OWNER = "trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1"

TYPED_TRANSPORT_MODEL = "A"
TYPED_CARRIER_END_BOUNDARY = "CanonicalMarketContextV1.canonical_volatility_estimate"
SINGLE_VALIDATION_BOUNDARY = "validate_canonical_volatility_estimate_v1"
LEGACY_ADAPTATION_BOUNDARY = "adapt_canonical_volatility_estimate_to_legacy_float_v1"

RUNTIME_EFFECT = False
TRADING_LOGIC_EFFECT = False
PARAMETER_EFFECT = False
LIVE_AUTHORIZATION = False
RUNTIME_WIRING = False
RUNTIME_PRODUCER_CUTOVER = False
DEFAULT_MUTATION = False
VOLATILITY_MAX_AGE_VALUE_UNRESOLVED = True

GAPS_CLOSED: tuple[str, ...] = (
    "G3_TRANSPORT",
    "G6_BINDING_SCAFFOLD",
    "G11_EVIDENCE_SCHEMA",
)
GAPS_REMAINING: tuple[str, ...] = (
    "G4",
    "G5",
    "G7",
    "G8",
    "G9",
    "G10_NUMERIC_MAX_AGE",
    "G12",
    "G13",
    "G14",
    "G15",
)


class VolatilityStaleStatusV1(str, Enum):
    """Transport-only stale representation; no numeric max-age in C1."""

    NOT_EVALUATED = "NOT_EVALUATED"
    UNRESOLVED_MAX_AGE = "UNRESOLVED_MAX_AGE"


class VolatilityValidationResultV1(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    MISSING = "MISSING"


class CanonicalVolatilityBindingErrorCode(str, Enum):
    MISSING_TYPED_ESTIMATE = "MISSING_TYPED_ESTIMATE"
    INVALID_ESTIMATE = "INVALID_ESTIMATE"
    UNTYPED_FLOAT_REJECTED = "UNTYPED_FLOAT_REJECTED"
    LEGACY_FLOAT_MISMATCH = "LEGACY_FLOAT_MISMATCH"
    METADATA_LOSS_BEFORE_BOUNDARY = "METADATA_LOSS_BEFORE_BOUNDARY"
    ADAPTATION_WITHOUT_VALIDATION = "ADAPTATION_WITHOUT_VALIDATION"
    SECOND_ADAPTER_FORBIDDEN = "SECOND_ADAPTER_FORBIDDEN"


class CanonicalVolatilityBindingError(ValueError):
    def __init__(self, code: CanonicalVolatilityBindingErrorCode, message: str) -> None:
        self.code = code
        super().__init__(f"{code.value}:{message}")


def _raise(code: CanonicalVolatilityBindingErrorCode, message: str) -> None:
    raise CanonicalVolatilityBindingError(code, message)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def serialize_canonical_volatility_estimate_for_digest_v1(
    estimate: CanonicalVolatilityEstimateV1,
) -> dict[str, Any]:
    """Deterministic carrier payload (timezone-aware ISO event time)."""
    as_of = estimate.as_of_event_time
    if as_of.tzinfo is None:
        _raise(
            CanonicalVolatilityBindingErrorCode.INVALID_ESTIMATE,
            "as_of_event_time_must_be_timezone_aware_for_digest",
        )
    return {
        "annualized": bool(estimate.annualized),
        "as_of_event_time": as_of.astimezone(timezone.utc).isoformat(),
        "bar_interval_seconds": int(estimate.bar_interval_seconds),
        "contract_version": str(estimate.contract_version),
        "estimator": str(estimate.estimator),
        "fallback_used": bool(estimate.fallback_used),
        "horizon_seconds": int(estimate.horizon_seconds),
        "lookback_bars": int(estimate.lookback_bars),
        "observation_count": int(estimate.observation_count),
        "source_digest": str(estimate.source_digest),
        "unit": str(estimate.unit),
        "value": float(estimate.value),
    }


def compute_typed_estimate_digest_v1(estimate: CanonicalVolatilityEstimateV1) -> str:
    return _stable_digest(serialize_canonical_volatility_estimate_for_digest_v1(estimate))


def compute_legacy_adaptation_digest_v1(
    *,
    estimate: CanonicalVolatilityEstimateV1,
    legacy_float: float,
) -> str:
    return _stable_digest(
        {
            "adapter_owner": LEGACY_ADAPTER_OWNER,
            "adapter_symbol": LEGACY_ADAPTATION_BOUNDARY,
            "legacy_float_value": float(legacy_float),
            "source_digest": estimate.source_digest,
            "typed_estimate_digest": compute_typed_estimate_digest_v1(estimate),
            "validation_boundary": SINGLE_VALIDATION_BOUNDARY,
        }
    )


def compute_volatility_input_binding_digest_v1(
    *,
    estimate: CanonicalVolatilityEstimateV1,
    legacy_float: float,
    stale_status: VolatilityStaleStatusV1,
    validation_result: VolatilityValidationResultV1,
) -> str:
    return _stable_digest(
        {
            "capability_version": CAPABILITY_VERSION,
            "legacy_adaptation_digest": compute_legacy_adaptation_digest_v1(
                estimate=estimate,
                legacy_float=legacy_float,
            ),
            "legacy_float_value": float(legacy_float),
            "source_digest": estimate.source_digest,
            "stale_status": stale_status.value,
            "typed_carrier_end_boundary": TYPED_CARRIER_END_BOUNDARY,
            "typed_estimate_digest": compute_typed_estimate_digest_v1(estimate),
            "typed_transport_model": TYPED_TRANSPORT_MODEL,
            "validation_result": validation_result.value,
        }
    )


def reject_untyped_float_at_typed_cmc_boundary_v1(
    *,
    raw_float: float | None,
    typed_estimate: CanonicalVolatilityEstimateV1 | None,
) -> None:
    """Fail-closed: unproven floats may not enter the typed CMC field."""
    if typed_estimate is not None:
        return
    _raise(
        CanonicalVolatilityBindingErrorCode.UNTYPED_FLOAT_REJECTED,
        f"untyped_float_cannot_populate_typed_cmc_field:value={raw_float!r}",
    )


def validate_typed_estimate_for_cmc_binding_v1(
    estimate: CanonicalVolatilityEstimateV1 | None,
) -> CanonicalVolatilityEstimateV1:
    """Single validation boundary before CMC acceptance."""
    if estimate is None:
        _raise(
            CanonicalVolatilityBindingErrorCode.MISSING_TYPED_ESTIMATE,
            "canonical_volatility_estimate_is_none",
        )
    try:
        return validate_canonical_volatility_estimate_v1(estimate)
    except CanonicalVolatilityTypedConsumptionError as exc:
        _raise(
            CanonicalVolatilityBindingErrorCode.INVALID_ESTIMATE,
            str(exc),
        )
        raise  # pragma: no cover


def adapt_validated_typed_estimate_to_legacy_float_v1(
    estimate: CanonicalVolatilityEstimateV1,
    *,
    already_validated: bool,
) -> float:
    """Single legacy adaptation; refuses adaptation without prior validation flag."""
    if not already_validated:
        _raise(
            CanonicalVolatilityBindingErrorCode.ADAPTATION_WITHOUT_VALIDATION,
            "legacy_adaptation_requires_prior_successful_validation",
        )
    # Re-validate inside the owned adapter (idempotent single authority).
    return float(adapt_canonical_volatility_estimate_to_legacy_float_v1(estimate))


def bind_typed_canonical_volatility_estimate_into_market_context_v1(
    context: CanonicalMarketContextV1,
    estimate: CanonicalVolatilityEstimateV1,
) -> CanonicalMarketContextV1:
    """Accept typed carrier into CMC after single validation; derive legacy float."""
    validated = validate_typed_estimate_for_cmc_binding_v1(estimate)
    legacy_float = adapt_validated_typed_estimate_to_legacy_float_v1(
        validated,
        already_validated=True,
    )
    bound = replace(
        context,
        canonical_volatility_estimate=validated,
        volatility_estimate=legacy_float,
        input_digest="",
    )
    return with_computed_input_digest(bound)


def assert_typed_metadata_preserved_until_boundary_v1(
    estimate: CanonicalVolatilityEstimateV1,
) -> None:
    """Detect metadata loss before legacy adaptation boundary."""
    required = (
        estimate.unit,
        estimate.estimator,
        estimate.source_digest,
        estimate.contract_version,
        estimate.as_of_event_time,
    )
    if any(x is None or x == "" for x in required):
        _raise(
            CanonicalVolatilityBindingErrorCode.METADATA_LOSS_BEFORE_BOUNDARY,
            "required_typed_metadata_missing_before_legacy_boundary",
        )
    if not isinstance(estimate.as_of_event_time, datetime):
        _raise(
            CanonicalVolatilityBindingErrorCode.METADATA_LOSS_BEFORE_BOUNDARY,
            "as_of_event_time_type_invalid",
        )
    if estimate.as_of_event_time.tzinfo is None:
        _raise(
            CanonicalVolatilityBindingErrorCode.METADATA_LOSS_BEFORE_BOUNDARY,
            "as_of_event_time_naive_forbidden",
        )


def resolve_legacy_volatility_float_for_consumer_v1(
    context: CanonicalMarketContextV1,
) -> float:
    """Legacy float for Scope/Rules consumers.

    Typed present → sole adapter path. Typed absent → existing float field
    (legacy path unchanged; global enforcement deferred to C2/G8).
    """
    typed_estimate = context.canonical_volatility_estimate
    if typed_estimate is None:
        return float(context.volatility_estimate)
    assert_typed_metadata_preserved_until_boundary_v1(typed_estimate)
    validated = validate_typed_estimate_for_cmc_binding_v1(typed_estimate)
    legacy = adapt_validated_typed_estimate_to_legacy_float_v1(
        validated,
        already_validated=True,
    )
    if not math.isclose(float(context.volatility_estimate), legacy, rel_tol=0.0, abs_tol=0.0):
        _raise(
            CanonicalVolatilityBindingErrorCode.LEGACY_FLOAT_MISMATCH,
            "cmc_float_does_not_match_adapted_typed_value",
        )
    return legacy


def build_volatility_decision_evidence_provenance_v1(
    context: CanonicalMarketContextV1,
    *,
    stale_status: VolatilityStaleStatusV1 = VolatilityStaleStatusV1.UNRESOLVED_MAX_AGE,
) -> CanonicalVolatilityDecisionEvidenceProvenanceV1:
    """Persist full estimate identity for decision evidence (O10)."""
    estimate = context.canonical_volatility_estimate
    if estimate is None:
        _raise(
            CanonicalVolatilityBindingErrorCode.MISSING_TYPED_ESTIMATE,
            "cannot_build_evidence_provenance_without_typed_estimate",
        )
    assert_typed_metadata_preserved_until_boundary_v1(estimate)
    validated = validate_typed_estimate_for_cmc_binding_v1(estimate)
    legacy_float = adapt_validated_typed_estimate_to_legacy_float_v1(
        validated,
        already_validated=True,
    )
    typed_digest = compute_typed_estimate_digest_v1(validated)
    legacy_digest = compute_legacy_adaptation_digest_v1(
        estimate=validated,
        legacy_float=legacy_float,
    )
    binding_digest = compute_volatility_input_binding_digest_v1(
        estimate=validated,
        legacy_float=legacy_float,
        stale_status=stale_status,
        validation_result=VolatilityValidationResultV1.ACCEPTED,
    )
    oldest = validated.oldest_observation_event_time
    return CanonicalVolatilityDecisionEvidenceProvenanceV1(
        volatility_contract_version=validated.contract_version,
        value=float(validated.value),
        unit=validated.unit,
        horizon=CANONICAL_HORIZON,
        annualized=bool(validated.annualized),
        estimator=validated.estimator,
        observation_count=int(validated.observation_count),
        as_of_event_time=validated.as_of_event_time.astimezone(timezone.utc).isoformat(),
        fallback_used=bool(validated.fallback_used),
        source_digest=validated.source_digest,
        typed_estimate_digest=typed_digest,
        legacy_adaptation_digest=legacy_digest,
        stale_status=stale_status.value,
        validation_result=VolatilityValidationResultV1.ACCEPTED.value,
        volatility_input_binding_digest=binding_digest,
        legacy_float_value=float(legacy_float),
        estimator_version=str(validated.estimator_version),
        oldest_observation_event_time=(
            "" if oldest is None else oldest.astimezone(timezone.utc).isoformat()
        ),
        config_digest=str(validated.config_digest),
        fallback_identity=str(validated.fallback_identity),
        volatility_status="VALID",
        volatility_reason_codes=("VALID",),
        volatility_age_seconds=None,
        max_age_threshold=None,
        max_age_enforcement_enabled=False,
    )


def attach_volatility_provenance_to_decision_evidence_v1(
    evidence: CanonicalTradingDecisionEvidenceV1,
    provenance: CanonicalVolatilityDecisionEvidenceProvenanceV1,
) -> CanonicalTradingDecisionEvidenceV1:
    return replace(evidence, volatility_provenance=provenance)


def assert_general_input_digest_alone_insufficient_v1(
    *,
    input_digest: str,
    provenance: CanonicalVolatilityDecisionEvidenceProvenanceV1 | None,
) -> None:
    if provenance is None:
        _raise(
            CanonicalVolatilityBindingErrorCode.MISSING_TYPED_ESTIMATE,
            "general_input_digest_alone_insufficient_without_volatility_identity",
        )
    if not input_digest:
        _raise(
            CanonicalVolatilityBindingErrorCode.INVALID_ESTIMATE,
            "input_digest_empty",
        )
    if not provenance.volatility_input_binding_digest:
        _raise(
            CanonicalVolatilityBindingErrorCode.INVALID_ESTIMATE,
            "volatility_input_binding_digest_required",
        )


def collect_typed_volatility_binding_block_reasons_v1(
    context: CanonicalMarketContextV1,
) -> tuple[CanonicalMarketContextBlockReason, ...]:
    """Fail-closed typed-path gates (does not mutate legacy-only eligibility)."""
    blocks: list[CanonicalMarketContextBlockReason] = []
    typed_estimate = context.canonical_volatility_estimate
    if typed_estimate is None:
        blocks.append(CanonicalMarketContextBlockReason.TYPED_VOLATILITY_ESTIMATE_MISSING)
        return tuple(blocks)
    try:
        validated = validate_typed_estimate_for_cmc_binding_v1(typed_estimate)
        legacy = adapt_validated_typed_estimate_to_legacy_float_v1(
            validated,
            already_validated=True,
        )
    except (CanonicalVolatilityBindingError, CanonicalVolatilityTypedConsumptionError):
        blocks.append(CanonicalMarketContextBlockReason.TYPED_VOLATILITY_ESTIMATE_INVALID)
        return tuple(blocks)
    if not math.isclose(float(context.volatility_estimate), legacy, rel_tol=0.0, abs_tol=0.0):
        blocks.append(CanonicalMarketContextBlockReason.TYPED_VOLATILITY_LEGACY_FLOAT_MISMATCH)
    return tuple(blocks)


def evaluate_typed_volatility_binding_eligibility_v1(
    context: CanonicalMarketContextV1,
    *,
    binding_outcome: CanonicalMarketContextBindingOutcome = CanonicalMarketContextBindingOutcome.ACCEPTED,
) -> CanonicalMarketContextEligibilityV1:
    """Eligibility under typed binding path: missing/invalid typed blocks exposure/scope."""
    typed_blocks = collect_typed_volatility_binding_block_reasons_v1(context)
    return evaluate_canonical_market_context_eligibility(
        context,
        binding_outcome=binding_outcome,
        extra_blocks=typed_blocks,
    )


@dataclass(frozen=True)
class CanonicalVolatilityBindingCapabilityManifestV1:
    capability_id: str
    capability_version: str
    typed_transport_model: str
    typed_carrier_end_boundary: str
    single_validation_boundary: str
    legacy_adaptation_boundary: str
    typed_carrier_owner: str
    legacy_adapter_owner: str
    semantics_owner: str
    estimator_owner: str
    binding_owner: str
    runtime_wiring: bool
    runtime_producer_cutover: bool
    default_mutation: bool
    live_authorization: bool
    volatility_max_age_value_unresolved: bool
    gaps_closed: tuple[str, ...]
    gaps_remaining: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding_owner": self.binding_owner,
            "capability_id": self.capability_id,
            "capability_version": self.capability_version,
            "default_mutation": self.default_mutation,
            "estimator_owner": self.estimator_owner,
            "gaps_closed": list(self.gaps_closed),
            "gaps_remaining": list(self.gaps_remaining),
            "legacy_adaptation_boundary": self.legacy_adaptation_boundary,
            "legacy_adapter_owner": self.legacy_adapter_owner,
            "live_authorization": self.live_authorization,
            "runtime_producer_cutover": self.runtime_producer_cutover,
            "runtime_wiring": self.runtime_wiring,
            "semantics_owner": self.semantics_owner,
            "single_validation_boundary": self.single_validation_boundary,
            "typed_carrier_end_boundary": self.typed_carrier_end_boundary,
            "typed_carrier_owner": self.typed_carrier_owner,
            "typed_transport_model": self.typed_transport_model,
            "volatility_max_age_value_unresolved": self.volatility_max_age_value_unresolved,
        }


def assert_capability_non_goals_v1() -> dict[str, Any]:
    return CanonicalVolatilityBindingCapabilityManifestV1(
        capability_id=CAPABILITY_ID,
        capability_version=CAPABILITY_VERSION,
        typed_transport_model=TYPED_TRANSPORT_MODEL,
        typed_carrier_end_boundary=TYPED_CARRIER_END_BOUNDARY,
        single_validation_boundary=SINGLE_VALIDATION_BOUNDARY,
        legacy_adaptation_boundary=LEGACY_ADAPTATION_BOUNDARY,
        typed_carrier_owner=TYPED_CARRIER_OWNER,
        legacy_adapter_owner=LEGACY_ADAPTER_OWNER,
        semantics_owner=SEMANTICS_OWNER,
        estimator_owner=ESTIMATOR_OWNER,
        binding_owner=BINDING_OWNER,
        runtime_wiring=RUNTIME_WIRING,
        runtime_producer_cutover=RUNTIME_PRODUCER_CUTOVER,
        default_mutation=DEFAULT_MUTATION,
        live_authorization=LIVE_AUTHORIZATION,
        volatility_max_age_value_unresolved=VOLATILITY_MAX_AGE_VALUE_UNRESOLVED,
        gaps_closed=GAPS_CLOSED,
        gaps_remaining=GAPS_REMAINING,
    ).to_dict()


def assert_architecture_guards_v1(*, repo_root: Optional[Path] = None) -> dict[str, Any]:
    """Static guards: single adapter/validation owners; no second authorities."""
    root = repo_root or Path(__file__).resolve().parents[3]
    binding_src = (
        root / "src/trading/master_v2/canonical_volatility_binding_and_provenance_transport_v1.py"
    ).read_text(encoding="utf-8")
    typed_src = (
        root
        / "src/trading/master_v2/canonical_volatility_estimate_typed_consumption_contract_v1.py"
    ).read_text(encoding="utf-8")
    cmc_src = (root / "src/trading/master_v2/canonical_market_context_v1.py").read_text(
        encoding="utf-8"
    )

    # Build needle without embedding a full def-line that would self-match.
    adapter_def_needle = "def " + "adapt_canonical_volatility_estimate_to_legacy_float_v1("
    adapter_defs_in_binding = binding_src.count(adapter_def_needle)
    adapter_defs_in_typed = typed_src.count(adapter_def_needle)
    if adapter_defs_in_binding != 0:
        _raise(
            CanonicalVolatilityBindingErrorCode.SECOND_ADAPTER_FORBIDDEN,
            "second_adapter_function_in_binding_module",
        )
    if adapter_defs_in_typed != 1:
        _raise(
            CanonicalVolatilityBindingErrorCode.SECOND_ADAPTER_FORBIDDEN,
            f"expected_exactly_one_typed_adapter_def:actual={adapter_defs_in_typed}",
        )

    # Binding must call owned adapter; must not reimplement validation formulas.
    if "adapt_canonical_volatility_estimate_to_legacy_float_v1" not in binding_src:
        _raise(
            CanonicalVolatilityBindingErrorCode.SECOND_ADAPTER_FORBIDDEN,
            "binding_must_reuse_typed_adapter",
        )
    if "validate_canonical_volatility_estimate_v1" not in binding_src:
        _raise(
            CanonicalVolatilityBindingErrorCode.INVALID_ESTIMATE,
            "binding_must_reuse_typed_validation",
        )
    # Forbidden producer aliases (split tokens avoid self-match on this guard text).
    forbidden_tokens = (
        "feature_regime_" + "pipeline",
        "FuturesVolatility" + "Profile",
        "panel_sequential",
    )
    code_before_guards = binding_src.split("def assert_architecture_guards_v1", 1)[0]
    for token in forbidden_tokens:
        if token in code_before_guards:
            _raise(
                CanonicalVolatilityBindingErrorCode.INVALID_ESTIMATE,
                f"non_canonical_producer_token_forbidden:{token}",
            )
    true_assign = " = " + "True"
    if ("RUNTIME_WIRING" + true_assign) in code_before_guards or (
        "LIVE_AUTHORIZATION" + true_assign
    ) in code_before_guards:
        _raise(
            CanonicalVolatilityBindingErrorCode.INVALID_ESTIMATE,
            "runtime_or_live_flags_must_remain_false",
        )
    if "canonical_volatility_estimate" not in cmc_src:
        _raise(
            CanonicalVolatilityBindingErrorCode.INVALID_ESTIMATE,
            "cmc_typed_field_missing",
        )

    return {
        "adapter_defs_in_typed": adapter_defs_in_typed,
        "adapter_defs_in_binding": adapter_defs_in_binding,
        "legacy_adapter_owner": LEGACY_ADAPTER_OWNER,
        "typed_carrier_owner": TYPED_CARRIER_OWNER,
        "runtime_wiring": RUNTIME_WIRING,
        "live_authorization": LIVE_AUTHORIZATION,
        "guards_pass": True,
    }


__all__ = [
    "BINDING_OWNER",
    "CAPABILITY_ID",
    "CAPABILITY_VERSION",
    "CanonicalVolatilityBindingCapabilityManifestV1",
    "CanonicalVolatilityBindingError",
    "CanonicalVolatilityBindingErrorCode",
    "DEFAULT_MUTATION",
    "ESTIMATOR_OWNER",
    "GAPS_CLOSED",
    "GAPS_REMAINING",
    "LEGACY_ADAPTATION_BOUNDARY",
    "LIVE_AUTHORIZATION",
    "PACKAGE_MARKER",
    "PARAMETER_EFFECT",
    "RUNTIME_EFFECT",
    "RUNTIME_PRODUCER_CUTOVER",
    "RUNTIME_WIRING",
    "SEMANTICS_OWNER",
    "SINGLE_VALIDATION_BOUNDARY",
    "TRADING_LOGIC_EFFECT",
    "TYPED_CARRIER_END_BOUNDARY",
    "TYPED_TRANSPORT_MODEL",
    "VOLATILITY_MAX_AGE_VALUE_UNRESOLVED",
    "VolatilityStaleStatusV1",
    "VolatilityValidationResultV1",
    "adapt_validated_typed_estimate_to_legacy_float_v1",
    "assert_architecture_guards_v1",
    "assert_capability_non_goals_v1",
    "assert_general_input_digest_alone_insufficient_v1",
    "assert_typed_metadata_preserved_until_boundary_v1",
    "attach_volatility_provenance_to_decision_evidence_v1",
    "bind_typed_canonical_volatility_estimate_into_market_context_v1",
    "build_volatility_decision_evidence_provenance_v1",
    "collect_typed_volatility_binding_block_reasons_v1",
    "compute_legacy_adaptation_digest_v1",
    "compute_typed_estimate_digest_v1",
    "compute_volatility_input_binding_digest_v1",
    "evaluate_typed_volatility_binding_eligibility_v1",
    "reject_untyped_float_at_typed_cmc_boundary_v1",
    "resolve_legacy_volatility_float_for_consumer_v1",
    "serialize_canonical_volatility_estimate_for_digest_v1",
    "validate_typed_estimate_for_cmc_binding_v1",
]
