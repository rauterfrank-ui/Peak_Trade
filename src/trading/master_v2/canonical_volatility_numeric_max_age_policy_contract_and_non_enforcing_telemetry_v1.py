"""Canonical volatility numeric max-age policy contract + non-enforcing telemetry v1.

Provides a versioned, typed policy and evidence contract for the ratified
estimate-age semantics. Computes diagnostic ``computed_age_seconds`` from
market event time minus ``CanonicalVolatilityEstimateV1.as_of_event_time``.

Does **not** select a numeric threshold, enable Alpha enforcement, create a
second clock/volatility/alpha authority, rematerialize estimates, or alter
Exit/Risk/Safety authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional, Union

from trading.master_v2.canonical_market_context_v1 import (
    ClockTrustStatus,
    DataIntegrityStatus,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    CanonicalVolatilityEstimateV1,
)

PACKAGE_MARKER = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_POLICY_CONTRACT_"
    "AND_NON_ENFORCING_TELEMETRY_V1=true"
)

CAPABILITY_ID = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_POLICY_CONTRACT_AND_NON_ENFORCING_TELEMETRY_V1"
)
CAPABILITY_VERSION = (
    "canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry/v1"
)
POLICY_NAME = "canonical_volatility_numeric_max_age_policy"
POLICY_VERSION = "canonical_volatility_numeric_max_age_policy/v1"
POLICY_OWNER = (
    "trading.master_v2."
    "canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1"
)
PRESENCE_GATE_OWNER = "trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1"

AGE_REFERENCE_CLOCK = "MARKET_EVENT_TIME"
AGE_REFERENCE_FIELD = "CanonicalMarketContextV1.market_event_time"
AGE_TIMESTAMP_FIELD = "CanonicalVolatilityEstimateV1.as_of_event_time"
AGE_FORMULA = "reference_market_event_time_-_estimate.as_of_event_time"

THRESHOLD_STATUS_UNRESOLVED = "UNRESOLVED_MAX_AGE"
REMATERIALIZATION_FORBIDDEN = "FORBIDDEN"
RESTART_AGE_POLICY = "UNDEFINED_FAIL_CLOSED_UNTIL_PRODUCED"
RESTORE_POLICY = "HISTORY_ONLY_NO_ESTIMATE_NO_FRESH_MARK"

NUMERIC_MAX_AGE_DECIDED = False
NUMERIC_THRESHOLD_SELECTED = False
ENFORCEMENT_ENABLED = False
COMPUTED_AGE_DIAGNOSTIC_ONLY = True
UNRESOLVED_MAX_AGE_IS_NOT_FRESHNESS_APPROVAL = True
NO_ALPHA_ENFORCEMENT_ENABLED = True
REMATERIALIZATION_ENABLED = False
SEPARATE_FRESHNESS_GATE_CREATED = False
SECOND_CLOCK_AUTHORITY_CREATED = False
SECOND_VOLATILITY_AUTHORITY_CREATED = False
SECOND_ALPHA_DECISION_AUTHORITY_CREATED = False
GLOBAL_STALENESS_GATE_CREATED = False
LIVE_AUTHORIZATION = False
HARD_STOP = True

NEXT_AFTER_THIS_CAPABILITY = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PARAMETER_RESEARCH_"
    "DESIGN_AND_EVIDENCE_ACCUMULATION_CONTRACT_V1"
)

_TRUSTED_CLOCK = frozenset({ClockTrustStatus.TRUSTED})
_TRUSTED_DATA = frozenset({DataIntegrityStatus.TRUSTED})


class CanonicalVolatilityMaxAgePolicyContractError(ValueError):
    """Fail-closed invalid policy-contract construction."""


class VolatilityMaxAgeReasonCodeV1(str, Enum):
    VOLATILITY_ESTIMATE_PRESENT = "VOLATILITY_ESTIMATE_PRESENT"
    VOLATILITY_ESTIMATE_MISSING = "VOLATILITY_ESTIMATE_MISSING"
    VOLATILITY_ESTIMATE_INVALID = "VOLATILITY_ESTIMATE_INVALID"
    VOLATILITY_ESTIMATE_RESTART_UNAVAILABLE = "VOLATILITY_ESTIMATE_RESTART_UNAVAILABLE"
    VOLATILITY_ESTIMATE_AGE_UNRESOLVED = "VOLATILITY_ESTIMATE_AGE_UNRESOLVED"
    # Structural only — must not be emitted while threshold is unresolved.
    VOLATILITY_ESTIMATE_FRESH = "VOLATILITY_ESTIMATE_FRESH"
    VOLATILITY_ESTIMATE_STALE = "VOLATILITY_ESTIMATE_STALE"
    VOLATILITY_AS_OF_MISSING = "VOLATILITY_AS_OF_MISSING"
    VOLATILITY_REFERENCE_TIME_MISSING = "VOLATILITY_REFERENCE_TIME_MISSING"
    VOLATILITY_REFERENCE_BEFORE_AS_OF = "VOLATILITY_REFERENCE_BEFORE_AS_OF"
    VOLATILITY_FRESHNESS_CLOCK_UNTRUSTED = "VOLATILITY_FRESHNESS_CLOCK_UNTRUSTED"
    VOLATILITY_FRESHNESS_DATA_UNTRUSTED = "VOLATILITY_FRESHNESS_DATA_UNTRUSTED"


class VolatilityMaxAgeStatusV1(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"
    UNDEFINED = "UNDEFINED"
    AGE_COMPUTED_THRESHOLD_UNRESOLVED = "AGE_COMPUTED_THRESHOLD_UNRESOLVED"
    REFERENCE_BEFORE_AS_OF = "REFERENCE_BEFORE_AS_OF"
    REFERENCE_TIME_MISSING = "REFERENCE_TIME_MISSING"
    AS_OF_MISSING = "AS_OF_MISSING"
    UNRESOLVED_MAX_AGE = "UNRESOLVED_MAX_AGE"


class VolatilityPresenceStatusV1(str, Enum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"
    INVALID = "INVALID"
    RESTART_UNAVAILABLE = "RESTART_UNAVAILABLE"


class VolatilityReuseStatusV1(str, Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    FRESHLY_PRODUCED = "FRESHLY_PRODUCED"
    NO_SAMPLE_REUSE = "NO_SAMPLE_REUSE"
    DUPLICATE_SAMPLE_REUSE = "DUPLICATE_SAMPLE_REUSE"
    OUT_OF_ORDER_REJECTED_REUSE = "OUT_OF_ORDER_REJECTED_REUSE"
    WARMUP_WITHOUT_ESTIMATE = "WARMUP_WITHOUT_ESTIMATE"
    UNKNOWN = "UNKNOWN"


class VolatilityRestartStatusV1(str, Enum):
    """Restart labels for non-enforcing age telemetry.

    Persistence restores mark-history only; typed estimates are never
    rematerialized across process restart. Restore therefore yields
    ``RESTART_WITHOUT_ESTIMATE`` until a fresh PRODUCED estimate. There is
    no restored-existing-estimate status because the producer persistence
    contract does not rematerialize estimates.
    """

    NOT_APPLICABLE = "NOT_APPLICABLE"
    RESTART_WITHOUT_ESTIMATE = "RESTART_WITHOUT_ESTIMATE"
    FIRST_PRODUCTION_AFTER_RESTART = "FIRST_PRODUCTION_AFTER_RESTART"
    UNKNOWN = "UNKNOWN"


class VolatilityMaxAgeDecisionV1(str, Enum):
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
    NOT_EVALUATED_PRESENCE_AUTHORITY = "NOT_EVALUATED_PRESENCE_AUTHORITY"
    FAIL_CLOSED_DIAGNOSTIC = "FAIL_CLOSED_DIAGNOSTIC"
    COMPOSED_TRUST_SECONDARY = "COMPOSED_TRUST_SECONDARY"


@dataclass(frozen=True)
class CanonicalVolatilityNumericMaxAgePolicyContractV1:
    """Versioned non-enforcing max-age policy contract (threshold unresolved)."""

    policy_name: str
    policy_version: str
    reference_clock: str
    reference_field: str
    estimate_timestamp_field: str
    age_formula: str
    threshold_status: str
    numeric_max_age_seconds: Optional[float]
    enforcement_enabled: bool
    rematerialization_policy: str
    duplicate_reuse_refreshes: bool
    no_sample_reuse_refreshes: bool
    restart_age_policy: str
    restore_policy: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "age_formula": self.age_formula,
            "duplicate_reuse_refreshes": self.duplicate_reuse_refreshes,
            "enforcement_enabled": self.enforcement_enabled,
            "estimate_timestamp_field": self.estimate_timestamp_field,
            "no_sample_reuse_refreshes": self.no_sample_reuse_refreshes,
            "numeric_max_age_seconds": self.numeric_max_age_seconds,
            "policy_name": self.policy_name,
            "policy_version": self.policy_version,
            "reference_clock": self.reference_clock,
            "reference_field": self.reference_field,
            "rematerialization_policy": self.rematerialization_policy,
            "restart_age_policy": self.restart_age_policy,
            "restore_policy": self.restore_policy,
            "threshold_status": self.threshold_status,
        }


def validate_canonical_volatility_numeric_max_age_policy_contract_v1(
    policy: CanonicalVolatilityNumericMaxAgePolicyContractV1,
) -> CanonicalVolatilityNumericMaxAgePolicyContractV1:
    """Reject illegal contract states (unresolved+threshold, enforcement, wrong clock)."""
    if policy.reference_clock != AGE_REFERENCE_CLOCK:
        raise CanonicalVolatilityMaxAgePolicyContractError(
            f"reference_clock_must_be_{AGE_REFERENCE_CLOCK}"
        )
    if policy.reference_field != AGE_REFERENCE_FIELD:
        raise CanonicalVolatilityMaxAgePolicyContractError("reference_field_mismatch")
    if policy.estimate_timestamp_field != AGE_TIMESTAMP_FIELD:
        raise CanonicalVolatilityMaxAgePolicyContractError("estimate_timestamp_field_mismatch")
    if policy.age_formula != AGE_FORMULA:
        raise CanonicalVolatilityMaxAgePolicyContractError("age_formula_mismatch")
    if policy.rematerialization_policy != REMATERIALIZATION_FORBIDDEN:
        raise CanonicalVolatilityMaxAgePolicyContractError("rematerialization_must_be_forbidden")
    if policy.duplicate_reuse_refreshes is not False:
        raise CanonicalVolatilityMaxAgePolicyContractError("duplicate_reuse_must_not_refresh")
    if policy.no_sample_reuse_refreshes is not False:
        raise CanonicalVolatilityMaxAgePolicyContractError("no_sample_reuse_must_not_refresh")
    if policy.restart_age_policy != RESTART_AGE_POLICY:
        raise CanonicalVolatilityMaxAgePolicyContractError("restart_age_policy_mismatch")
    if policy.restore_policy != RESTORE_POLICY:
        raise CanonicalVolatilityMaxAgePolicyContractError("restore_policy_mismatch")

    if policy.threshold_status == THRESHOLD_STATUS_UNRESOLVED:
        if policy.numeric_max_age_seconds is not None:
            raise CanonicalVolatilityMaxAgePolicyContractError(
                "unresolved_threshold_forbids_numeric_max_age_seconds"
            )
        if policy.enforcement_enabled is not False:
            raise CanonicalVolatilityMaxAgePolicyContractError(
                "unresolved_threshold_forbids_enforcement"
            )
    elif policy.enforcement_enabled and policy.numeric_max_age_seconds is None:
        raise CanonicalVolatilityMaxAgePolicyContractError(
            "enforcement_requires_ratified_numeric_threshold"
        )
    elif policy.enforcement_enabled:
        # This capability never admits a ratified threshold path.
        raise CanonicalVolatilityMaxAgePolicyContractError(
            "enforcement_forbidden_while_numeric_max_age_undecided"
        )

    if policy.enforcement_enabled is True and NUMERIC_MAX_AGE_DECIDED is False:
        raise CanonicalVolatilityMaxAgePolicyContractError(
            "enforcement_forbidden_while_numeric_max_age_undecided"
        )

    return policy


def build_ratified_unresolved_max_age_policy_contract_v1() -> (
    CanonicalVolatilityNumericMaxAgePolicyContractV1
):
    """Construct the single ratified non-enforcing unresolved policy."""
    policy = CanonicalVolatilityNumericMaxAgePolicyContractV1(
        policy_name=POLICY_NAME,
        policy_version=POLICY_VERSION,
        reference_clock=AGE_REFERENCE_CLOCK,
        reference_field=AGE_REFERENCE_FIELD,
        estimate_timestamp_field=AGE_TIMESTAMP_FIELD,
        age_formula=AGE_FORMULA,
        threshold_status=THRESHOLD_STATUS_UNRESOLVED,
        numeric_max_age_seconds=None,
        enforcement_enabled=False,
        rematerialization_policy=REMATERIALIZATION_FORBIDDEN,
        duplicate_reuse_refreshes=False,
        no_sample_reuse_refreshes=False,
        restart_age_policy=RESTART_AGE_POLICY,
        restore_policy=RESTORE_POLICY,
    )
    return validate_canonical_volatility_numeric_max_age_policy_contract_v1(policy)


@dataclass(frozen=True)
class CanonicalVolatilityMaxAgePolicyEvidenceV1:
    """Non-enforcing age/freshness evidence (diagnostic only)."""

    policy_name: str
    policy_version: str
    estimate_as_of_event_time: Optional[str]
    reference_event_time: Optional[str]
    computed_age_seconds: Optional[float]
    max_age_status: str
    threshold_status: str
    presence_status: str
    clock_trust_status: str
    data_integrity_status: str
    reuse_status: str
    restart_status: str
    source_digest: Optional[str]
    decision: str
    reason_code: str
    enforcement_applied: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "clock_trust_status": self.clock_trust_status,
            "computed_age_seconds": self.computed_age_seconds,
            "data_integrity_status": self.data_integrity_status,
            "decision": self.decision,
            "enforcement_applied": self.enforcement_applied,
            "estimate_as_of_event_time": self.estimate_as_of_event_time,
            "max_age_status": self.max_age_status,
            "policy_name": self.policy_name,
            "policy_version": self.policy_version,
            "presence_status": self.presence_status,
            "reason_code": self.reason_code,
            "reference_event_time": self.reference_event_time,
            "restart_status": self.restart_status,
            "reuse_status": self.reuse_status,
            "source_digest": self.source_digest,
            "threshold_status": self.threshold_status,
        }


def parse_event_time_instant_v1(
    value: Union[str, datetime, None],
) -> Optional[datetime]:
    """Parse timezone-aware UTC event time; reject naive / unparseable values."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return None
        return value.astimezone(timezone.utc)
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _iso_utc(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat()


def _evidence(
    *,
    policy: CanonicalVolatilityNumericMaxAgePolicyContractV1,
    estimate_as_of: Optional[datetime],
    reference: Optional[datetime],
    computed_age_seconds: Optional[float],
    max_age_status: VolatilityMaxAgeStatusV1,
    presence_status: VolatilityPresenceStatusV1,
    clock_trust_status: ClockTrustStatus,
    data_integrity_status: DataIntegrityStatus,
    reuse_status: VolatilityReuseStatusV1,
    restart_status: VolatilityRestartStatusV1,
    source_digest: Optional[str],
    decision: VolatilityMaxAgeDecisionV1,
    reason_code: VolatilityMaxAgeReasonCodeV1,
) -> CanonicalVolatilityMaxAgePolicyEvidenceV1:
    # Structural FRESH/STALE must never be emitted under unresolved threshold.
    if reason_code in (
        VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_FRESH,
        VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_STALE,
    ):
        raise CanonicalVolatilityMaxAgePolicyContractError(
            "fresh_or_stale_forbidden_while_threshold_unresolved"
        )
    return CanonicalVolatilityMaxAgePolicyEvidenceV1(
        policy_name=policy.policy_name,
        policy_version=policy.policy_version,
        estimate_as_of_event_time=_iso_utc(estimate_as_of),
        reference_event_time=_iso_utc(reference),
        computed_age_seconds=computed_age_seconds,
        max_age_status=max_age_status.value,
        threshold_status=policy.threshold_status,
        presence_status=presence_status.value,
        clock_trust_status=clock_trust_status.value,
        data_integrity_status=data_integrity_status.value,
        reuse_status=reuse_status.value,
        restart_status=restart_status.value,
        source_digest=source_digest,
        decision=decision.value,
        reason_code=reason_code.value,
        enforcement_applied=False,
    )


def evaluate_canonical_volatility_estimate_age_policy_v1(
    *,
    estimate: Optional[CanonicalVolatilityEstimateV1],
    reference_market_event_time: Union[str, datetime, None],
    presence_status: VolatilityPresenceStatusV1,
    reuse_status: VolatilityReuseStatusV1 = VolatilityReuseStatusV1.NOT_APPLICABLE,
    restart_status: VolatilityRestartStatusV1 = VolatilityRestartStatusV1.NOT_APPLICABLE,
    clock_trust_status: ClockTrustStatus = ClockTrustStatus.TRUSTED,
    data_integrity_status: DataIntegrityStatus = DataIntegrityStatus.TRUSTED,
    policy: CanonicalVolatilityNumericMaxAgePolicyContractV1 | None = None,
) -> CanonicalVolatilityMaxAgePolicyEvidenceV1:
    """Pure deterministic age/policy evaluation; never enforces Alpha decisions."""
    ratified = validate_canonical_volatility_numeric_max_age_policy_contract_v1(
        policy if policy is not None else build_ratified_unresolved_max_age_policy_contract_v1()
    )
    source_digest = None if estimate is None else str(estimate.source_digest)
    as_of_raw = None if estimate is None else estimate.as_of_event_time
    as_of = parse_event_time_instant_v1(as_of_raw)
    reference = parse_event_time_instant_v1(reference_market_event_time)

    # Precedence 1: presence / restart
    if (
        restart_status is VolatilityRestartStatusV1.RESTART_WITHOUT_ESTIMATE
        or presence_status is VolatilityPresenceStatusV1.RESTART_UNAVAILABLE
    ):
        return _evidence(
            policy=ratified,
            estimate_as_of=as_of,
            reference=reference,
            computed_age_seconds=None,
            max_age_status=VolatilityMaxAgeStatusV1.UNDEFINED,
            presence_status=VolatilityPresenceStatusV1.RESTART_UNAVAILABLE,
            clock_trust_status=clock_trust_status,
            data_integrity_status=data_integrity_status,
            reuse_status=reuse_status,
            restart_status=restart_status,
            source_digest=source_digest,
            decision=VolatilityMaxAgeDecisionV1.NOT_EVALUATED_PRESENCE_AUTHORITY,
            reason_code=VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_RESTART_UNAVAILABLE,
        )

    if presence_status is VolatilityPresenceStatusV1.MISSING or estimate is None:
        return _evidence(
            policy=ratified,
            estimate_as_of=None,
            reference=reference,
            computed_age_seconds=None,
            max_age_status=VolatilityMaxAgeStatusV1.NOT_EVALUATED,
            presence_status=VolatilityPresenceStatusV1.MISSING,
            clock_trust_status=clock_trust_status,
            data_integrity_status=data_integrity_status,
            reuse_status=reuse_status,
            restart_status=restart_status,
            source_digest=None,
            decision=VolatilityMaxAgeDecisionV1.NOT_EVALUATED_PRESENCE_AUTHORITY,
            reason_code=VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_MISSING,
        )

    if presence_status is VolatilityPresenceStatusV1.INVALID:
        return _evidence(
            policy=ratified,
            estimate_as_of=as_of,
            reference=reference,
            computed_age_seconds=None,
            max_age_status=VolatilityMaxAgeStatusV1.NOT_EVALUATED,
            presence_status=VolatilityPresenceStatusV1.INVALID,
            clock_trust_status=clock_trust_status,
            data_integrity_status=data_integrity_status,
            reuse_status=reuse_status,
            restart_status=restart_status,
            source_digest=source_digest,
            decision=VolatilityMaxAgeDecisionV1.NOT_EVALUATED_PRESENCE_AUTHORITY,
            reason_code=VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_INVALID,
        )

    # Precedence 2: Data Integrity (primary authority preserved; freshness secondary)
    if data_integrity_status not in _TRUSTED_DATA:
        return _evidence(
            policy=ratified,
            estimate_as_of=as_of,
            reference=reference,
            computed_age_seconds=None,
            max_age_status=VolatilityMaxAgeStatusV1.NOT_EVALUATED,
            presence_status=VolatilityPresenceStatusV1.PRESENT,
            clock_trust_status=clock_trust_status,
            data_integrity_status=data_integrity_status,
            reuse_status=reuse_status,
            restart_status=restart_status,
            source_digest=source_digest,
            decision=VolatilityMaxAgeDecisionV1.COMPOSED_TRUST_SECONDARY,
            reason_code=VolatilityMaxAgeReasonCodeV1.VOLATILITY_FRESHNESS_DATA_UNTRUSTED,
        )

    # Precedence 3: Clock Trust (primary authority preserved; freshness secondary)
    if clock_trust_status not in _TRUSTED_CLOCK:
        return _evidence(
            policy=ratified,
            estimate_as_of=as_of,
            reference=reference,
            computed_age_seconds=None,
            max_age_status=VolatilityMaxAgeStatusV1.NOT_EVALUATED,
            presence_status=VolatilityPresenceStatusV1.PRESENT,
            clock_trust_status=clock_trust_status,
            data_integrity_status=data_integrity_status,
            reuse_status=reuse_status,
            restart_status=restart_status,
            source_digest=source_digest,
            decision=VolatilityMaxAgeDecisionV1.COMPOSED_TRUST_SECONDARY,
            reason_code=VolatilityMaxAgeReasonCodeV1.VOLATILITY_FRESHNESS_CLOCK_UNTRUSTED,
        )

    # Precedence 4: age resolution (never FRESH/STALE under unresolved threshold)
    if as_of is None:
        return _evidence(
            policy=ratified,
            estimate_as_of=None,
            reference=reference,
            computed_age_seconds=None,
            max_age_status=VolatilityMaxAgeStatusV1.AS_OF_MISSING,
            presence_status=VolatilityPresenceStatusV1.PRESENT,
            clock_trust_status=clock_trust_status,
            data_integrity_status=data_integrity_status,
            reuse_status=reuse_status,
            restart_status=restart_status,
            source_digest=source_digest,
            decision=VolatilityMaxAgeDecisionV1.FAIL_CLOSED_DIAGNOSTIC,
            reason_code=VolatilityMaxAgeReasonCodeV1.VOLATILITY_AS_OF_MISSING,
        )

    if reference is None:
        return _evidence(
            policy=ratified,
            estimate_as_of=as_of,
            reference=None,
            computed_age_seconds=None,
            max_age_status=VolatilityMaxAgeStatusV1.REFERENCE_TIME_MISSING,
            presence_status=VolatilityPresenceStatusV1.PRESENT,
            clock_trust_status=clock_trust_status,
            data_integrity_status=data_integrity_status,
            reuse_status=reuse_status,
            restart_status=restart_status,
            source_digest=source_digest,
            decision=VolatilityMaxAgeDecisionV1.FAIL_CLOSED_DIAGNOSTIC,
            reason_code=VolatilityMaxAgeReasonCodeV1.VOLATILITY_REFERENCE_TIME_MISSING,
        )

    if reference < as_of:
        return _evidence(
            policy=ratified,
            estimate_as_of=as_of,
            reference=reference,
            computed_age_seconds=None,
            max_age_status=VolatilityMaxAgeStatusV1.REFERENCE_BEFORE_AS_OF,
            presence_status=VolatilityPresenceStatusV1.PRESENT,
            clock_trust_status=clock_trust_status,
            data_integrity_status=data_integrity_status,
            reuse_status=reuse_status,
            restart_status=restart_status,
            source_digest=source_digest,
            decision=VolatilityMaxAgeDecisionV1.FAIL_CLOSED_DIAGNOSTIC,
            reason_code=VolatilityMaxAgeReasonCodeV1.VOLATILITY_REFERENCE_BEFORE_AS_OF,
        )

    age_seconds = (reference - as_of).total_seconds()
    if age_seconds < 0.0:
        # Defensive: should be unreachable after reference < as_of guard.
        raise CanonicalVolatilityMaxAgePolicyContractError("negative_age_forbidden")

    return _evidence(
        policy=ratified,
        estimate_as_of=as_of,
        reference=reference,
        computed_age_seconds=float(age_seconds),
        max_age_status=VolatilityMaxAgeStatusV1.AGE_COMPUTED_THRESHOLD_UNRESOLVED,
        presence_status=VolatilityPresenceStatusV1.PRESENT,
        clock_trust_status=clock_trust_status,
        data_integrity_status=data_integrity_status,
        reuse_status=reuse_status,
        restart_status=restart_status,
        source_digest=source_digest,
        decision=VolatilityMaxAgeDecisionV1.DIAGNOSTIC_ONLY,
        reason_code=VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_AGE_UNRESOLVED,
    )


def derive_presence_status_for_age_policy_v1(
    *,
    typed_estimate_present: bool,
    typed_validation_ok: bool,
    restart_without_estimate: bool = False,
) -> VolatilityPresenceStatusV1:
    if restart_without_estimate and not typed_estimate_present:
        return VolatilityPresenceStatusV1.RESTART_UNAVAILABLE
    if not typed_estimate_present:
        return VolatilityPresenceStatusV1.MISSING
    if not typed_validation_ok:
        return VolatilityPresenceStatusV1.INVALID
    return VolatilityPresenceStatusV1.PRESENT


def derive_reuse_and_restart_status_for_age_policy_v1(
    *,
    producer_outcome: str,
    cycle_without_sample: bool,
    estimate_bound: bool,
    restart_without_estimate: bool,
    first_production_after_restart: bool = False,
) -> tuple[VolatilityReuseStatusV1, VolatilityRestartStatusV1]:
    """Map productive producer/binding states onto typed age-telemetry labels.

    Labels are diagnostic only. Reuse must never refresh ``as_of_event_time``.
    Restart/restore must not rematerialize volatility as a freshness reset.
    """
    outcome = str(producer_outcome or "").strip().upper()

    if restart_without_estimate and not estimate_bound:
        reuse = (
            VolatilityReuseStatusV1.WARMUP_WITHOUT_ESTIMATE
            if outcome == "WARMUP"
            else VolatilityReuseStatusV1.NOT_APPLICABLE
        )
        return reuse, VolatilityRestartStatusV1.RESTART_WITHOUT_ESTIMATE

    if first_production_after_restart and outcome == "PRODUCED" and estimate_bound:
        return (
            VolatilityReuseStatusV1.FRESHLY_PRODUCED,
            VolatilityRestartStatusV1.FIRST_PRODUCTION_AFTER_RESTART,
        )

    if outcome == "PRODUCED" and estimate_bound:
        return (
            VolatilityReuseStatusV1.FRESHLY_PRODUCED,
            VolatilityRestartStatusV1.NOT_APPLICABLE,
        )

    # No-sample cycles must label process reuse even if last ingest was DUPLICATE.
    if cycle_without_sample and estimate_bound:
        return (
            VolatilityReuseStatusV1.NO_SAMPLE_REUSE,
            VolatilityRestartStatusV1.NOT_APPLICABLE,
        )

    if outcome == "DUPLICATE_NOOP" and estimate_bound:
        return (
            VolatilityReuseStatusV1.DUPLICATE_SAMPLE_REUSE,
            VolatilityRestartStatusV1.NOT_APPLICABLE,
        )

    if outcome == "OUT_OF_ORDER_REJECTED":
        return (
            VolatilityReuseStatusV1.OUT_OF_ORDER_REJECTED_REUSE,
            VolatilityRestartStatusV1.NOT_APPLICABLE,
        )

    if outcome == "WARMUP" and not estimate_bound:
        return (
            VolatilityReuseStatusV1.WARMUP_WITHOUT_ESTIMATE,
            VolatilityRestartStatusV1.NOT_APPLICABLE,
        )

    if estimate_bound:
        return (
            VolatilityReuseStatusV1.UNKNOWN,
            VolatilityRestartStatusV1.NOT_APPLICABLE,
        )

    return (
        VolatilityReuseStatusV1.NOT_APPLICABLE,
        VolatilityRestartStatusV1.NOT_APPLICABLE,
    )


def assert_architecture_guards_v1(*, repo_root: Optional[Path] = None) -> dict[str, Any]:
    """Guards: unresolved threshold, no enforcement, no second authorities."""
    root = repo_root or Path(__file__).resolve().parents[3]
    this_src = (
        root
        / "src/trading/master_v2"
        / "canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1.py"
    ).read_text(encoding="utf-8")
    presence_src = (
        root / "src/trading/master_v2/double_play_runtime_typed_volatility_presence_gate_v1.py"
    ).read_text(encoding="utf-8")

    code_before_guards = this_src.split("def assert_architecture_guards_v1", 1)[0]
    if "enforcement_applied=True" in code_before_guards:
        raise RuntimeError("ENFORCEMENT_APPLIED_TRUE_FORBIDDEN")
    if "numeric_max_age_seconds=" in code_before_guards:
        # Allow None assignment only via ratified builder; forbid literal numeric thresholds.
        for line in code_before_guards.splitlines():
            stripped = line.strip()
            if "numeric_max_age_seconds=" not in stripped:
                continue
            if "numeric_max_age_seconds=None" in stripped:
                continue
            if "numeric_max_age_seconds:" in stripped:
                continue
            if "self.numeric_max_age_seconds" in stripped:
                continue
            if "policy.numeric_max_age_seconds" in stripped:
                continue
            raise RuntimeError(f"NUMERIC_THRESHOLD_LITERAL_FORBIDDEN:{stripped}")

    if SEPARATE_FRESHNESS_GATE_CREATED or SECOND_ALPHA_DECISION_AUTHORITY_CREATED:
        raise RuntimeError("SEPARATE_FRESHNESS_OR_ALPHA_GATE_FORBIDDEN")
    if SECOND_CLOCK_AUTHORITY_CREATED or SECOND_VOLATILITY_AUTHORITY_CREATED:
        raise RuntimeError("SECOND_AUTHORITY_FLAG_DRIFT")
    if GLOBAL_STALENESS_GATE_CREATED or REMATERIALIZATION_ENABLED:
        raise RuntimeError("GLOBAL_STALE_OR_REMATERIALIZE_FORBIDDEN")
    if NUMERIC_MAX_AGE_DECIDED or ENFORCEMENT_ENABLED or LIVE_AUTHORIZATION:
        raise RuntimeError("THRESHOLD_ENFORCEMENT_OR_LIVE_FLAG_DRIFT")

    if "evaluate_canonical_volatility_estimate_age_policy_v1" not in presence_src:
        raise RuntimeError("PRESENCE_GATE_MUST_ATTACH_MAX_AGE_EVIDENCE")
    if (
        "def evaluate_freshness_gate" in presence_src
        or "def evaluate_volatility_freshness_gate" in (presence_src)
    ):
        raise RuntimeError("SEPARATE_FRESHNESS_GATE_FUNCTION_FORBIDDEN")

    policy = build_ratified_unresolved_max_age_policy_contract_v1()
    return {
        "capability_id": CAPABILITY_ID,
        "capability_version": CAPABILITY_VERSION,
        "policy_version": policy.policy_version,
        "threshold_status": policy.threshold_status,
        "numeric_max_age_seconds": policy.numeric_max_age_seconds,
        "enforcement_enabled": policy.enforcement_enabled,
        "numeric_max_age_decided": NUMERIC_MAX_AGE_DECIDED,
        "presence_gate_owner": PRESENCE_GATE_OWNER,
        "policy_owner": POLICY_OWNER,
        "separate_freshness_gate_created": SEPARATE_FRESHNESS_GATE_CREATED,
        "second_clock_authority_created": SECOND_CLOCK_AUTHORITY_CREATED,
        "second_volatility_authority_created": SECOND_VOLATILITY_AUTHORITY_CREATED,
        "second_alpha_decision_authority_created": SECOND_ALPHA_DECISION_AUTHORITY_CREATED,
        "global_staleness_gate_created": GLOBAL_STALENESS_GATE_CREATED,
        "rematerialization_enabled": REMATERIALIZATION_ENABLED,
        "live_authorization": LIVE_AUTHORIZATION,
        "hard_stop": HARD_STOP,
        "guards_pass": True,
    }


def assert_capability_non_goals_v1() -> Mapping[str, Any]:
    return {
        "capability_id": CAPABILITY_ID,
        "capability_version": CAPABILITY_VERSION,
        "numeric_max_age_decided": NUMERIC_MAX_AGE_DECIDED,
        "numeric_threshold_selected": NUMERIC_THRESHOLD_SELECTED,
        "enforcement_enabled": ENFORCEMENT_ENABLED,
        "computed_age_diagnostic_only": COMPUTED_AGE_DIAGNOSTIC_ONLY,
        "unresolved_max_age_is_not_freshness_approval": (
            UNRESOLVED_MAX_AGE_IS_NOT_FRESHNESS_APPROVAL
        ),
        "no_alpha_enforcement_enabled": NO_ALPHA_ENFORCEMENT_ENABLED,
        "rematerialization_enabled": REMATERIALIZATION_ENABLED,
        "separate_freshness_gate_created": SEPARATE_FRESHNESS_GATE_CREATED,
        "second_clock_authority_created": SECOND_CLOCK_AUTHORITY_CREATED,
        "second_volatility_authority_created": SECOND_VOLATILITY_AUTHORITY_CREATED,
        "second_alpha_decision_authority_created": SECOND_ALPHA_DECISION_AUTHORITY_CREATED,
        "global_staleness_gate_created": GLOBAL_STALENESS_GATE_CREATED,
        "live_authorization": LIVE_AUTHORIZATION,
        "hard_stop": HARD_STOP,
        "next_after_this_capability": NEXT_AFTER_THIS_CAPABILITY,
        "package_marker": PACKAGE_MARKER,
        "gaps_remaining": ("C1_G10_NUMERIC_MAX_AGE_THRESHOLD_VALUE",),
    }


__all__ = [
    "AGE_FORMULA",
    "AGE_REFERENCE_CLOCK",
    "AGE_REFERENCE_FIELD",
    "AGE_TIMESTAMP_FIELD",
    "CAPABILITY_ID",
    "CAPABILITY_VERSION",
    "CanonicalVolatilityMaxAgePolicyContractError",
    "CanonicalVolatilityMaxAgePolicyEvidenceV1",
    "CanonicalVolatilityNumericMaxAgePolicyContractV1",
    "ENFORCEMENT_ENABLED",
    "HARD_STOP",
    "LIVE_AUTHORIZATION",
    "NUMERIC_MAX_AGE_DECIDED",
    "PACKAGE_MARKER",
    "POLICY_NAME",
    "POLICY_OWNER",
    "POLICY_VERSION",
    "PRESENCE_GATE_OWNER",
    "THRESHOLD_STATUS_UNRESOLVED",
    "VolatilityMaxAgeDecisionV1",
    "VolatilityMaxAgeReasonCodeV1",
    "VolatilityMaxAgeStatusV1",
    "VolatilityPresenceStatusV1",
    "VolatilityRestartStatusV1",
    "VolatilityReuseStatusV1",
    "assert_architecture_guards_v1",
    "assert_capability_non_goals_v1",
    "build_ratified_unresolved_max_age_policy_contract_v1",
    "derive_presence_status_for_age_policy_v1",
    "derive_reuse_and_restart_status_for_age_policy_v1",
    "evaluate_canonical_volatility_estimate_age_policy_v1",
    "parse_event_time_instant_v1",
    "validate_canonical_volatility_numeric_max_age_policy_contract_v1",
]
