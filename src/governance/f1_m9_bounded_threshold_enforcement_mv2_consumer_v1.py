"""Bounded MV2 max-age threshold enforcement at the authorized parameter seam consumer.

Does not flip global policy-module `ENFORCEMENT_ENABLED` flags. Enforcement applies
only when decision-bound `THRESHOLD_ENFORCEMENT_AUTHORIZED` and ratified numeric policy
admission are both valid.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.authorized_productive_parameter_seam_v1 import (
    evaluate_age_policy_at_consumer_boundary_v1,
    resolve_age_policy_from_authorized_seam_record_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    build_policy_admission_from_authorized_seam_record_v1,
    validate_policy_admission_request_v1,
)
from src.trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    THRESHOLD_STATUS_RATIFIED_NUMERIC,
    CanonicalVolatilityMaxAgePolicyEvidenceV1,
    VolatilityMaxAgeDecisionV1,
    VolatilityMaxAgeReasonCodeV1,
    VolatilityMaxAgeStatusV1,
    build_ratified_unresolved_max_age_policy_contract_v1,
)

DECISION_CONFIG: Final[str] = (
    "config/governance/f1_m9_threshold_enforcement_to_trading_order_effect_closure_v1_decision_v1.json"
)
WORKPACKAGE_ID: Final[str] = "THRESHOLD_ENFORCEMENT_TO_TRADING_ORDER_EFFECT_CLOSURE_V1"
SCHEMA_VERSION: Final[str] = "f1_m9_bounded_threshold_enforcement_mv2_consumer/v1"

THRESHOLD_ENFORCEMENT_AUTHORIZED: Final[bool] = True


def load_threshold_enforcement_closure_decision_v1(
    *, repo_root: Path | None = None
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    path = root / DECISION_CONFIG
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def threshold_enforcement_authorized_v1(*, repo_root: Path | None = None) -> bool:
    decision = load_threshold_enforcement_closure_decision_v1(repo_root=repo_root)
    return (
        decision.get("threshold_enforcement_authorized") is True
        and decision.get("closure_implemented") is True
        and THRESHOLD_ENFORCEMENT_AUTHORIZED is True
    )


@dataclass(frozen=True, slots=True)
class BoundedThresholdEnforcementResultV1:
    enforcement_applied: bool
    threshold_enforcement_authorized: bool
    age_evidence: CanonicalVolatilityMaxAgePolicyEvidenceV1
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "age_evidence": self.age_evidence.to_dict(),
            "enforcement_applied": self.enforcement_applied,
            "reason_codes": list(self.reason_codes),
            "threshold_enforcement_authorized": self.threshold_enforcement_authorized,
        }


def _base_age_evidence(
    *,
    seam_record: Mapping[str, Any] | None,
    estimate: Any,
    reference_market_event_time: Any,
    presence_status: Any,
    reuse_status: Any = None,
    restart_status: Any = None,
    clock_trust_status: Any = None,
    data_integrity_status: Any = None,
) -> CanonicalVolatilityMaxAgePolicyEvidenceV1:
    return evaluate_age_policy_at_consumer_boundary_v1(
        seam_record=seam_record,
        estimate=estimate,
        reference_market_event_time=reference_market_event_time,
        presence_status=presence_status,
        reuse_status=reuse_status,
        restart_status=restart_status,
        clock_trust_status=clock_trust_status,
        data_integrity_status=data_integrity_status,
    )


def evaluate_bounded_threshold_enforcement_at_mv2_consumer_v1(
    *,
    seam_record: Mapping[str, Any] | None,
    estimate: Any,
    reference_market_event_time: Any,
    presence_status: Any,
    reuse_status: Any = None,
    restart_status: Any = None,
    clock_trust_status: Any = None,
    data_integrity_status: Any = None,
    repo_root: Path | None = None,
) -> BoundedThresholdEnforcementResultV1:
    """Ratified numeric + authorized enforcement → FRESH/STALE with enforcement_applied."""
    base = _base_age_evidence(
        seam_record=seam_record,
        estimate=estimate,
        reference_market_event_time=reference_market_event_time,
        presence_status=presence_status,
        reuse_status=reuse_status,
        restart_status=restart_status,
        clock_trust_status=clock_trust_status,
        data_integrity_status=data_integrity_status,
    )
    if not threshold_enforcement_authorized_v1(repo_root=repo_root):
        return BoundedThresholdEnforcementResultV1(
            enforcement_applied=False,
            threshold_enforcement_authorized=False,
            age_evidence=base,
            reason_codes=("THRESHOLD_ENFORCEMENT_NOT_AUTHORIZED",),
        )

    if seam_record is None:
        return BoundedThresholdEnforcementResultV1(
            enforcement_applied=False,
            threshold_enforcement_authorized=True,
            age_evidence=base,
            reason_codes=("SEAM_RECORD_MISSING",),
        )

    admission = build_policy_admission_from_authorized_seam_record_v1(seam_record)
    admission_ok, admission_reasons = validate_policy_admission_request_v1(admission)
    if not admission_ok:
        return BoundedThresholdEnforcementResultV1(
            enforcement_applied=False,
            threshold_enforcement_authorized=True,
            age_evidence=base,
            reason_codes=tuple(admission_reasons),
        )

    policy = resolve_age_policy_from_authorized_seam_record_v1(seam_record)
    if policy.threshold_status != THRESHOLD_STATUS_RATIFIED_NUMERIC:
        return BoundedThresholdEnforcementResultV1(
            enforcement_applied=False,
            threshold_enforcement_authorized=True,
            age_evidence=base,
            reason_codes=("THRESHOLD_NOT_RATIFIED_NUMERIC",),
        )

    threshold_seconds = policy.numeric_max_age_seconds
    if threshold_seconds is None or base.computed_age_seconds is None:
        return BoundedThresholdEnforcementResultV1(
            enforcement_applied=False,
            threshold_enforcement_authorized=True,
            age_evidence=base,
            reason_codes=("AGE_OR_THRESHOLD_UNRESOLVED_FOR_ENFORCEMENT",),
        )

    age = float(base.computed_age_seconds)
    limit = float(threshold_seconds)
    if age <= limit:
        reason = VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_FRESH
        decision = VolatilityMaxAgeDecisionV1.DIAGNOSTIC_ONLY
        max_age_status = VolatilityMaxAgeStatusV1.AGE_COMPUTED_THRESHOLD_UNRESOLVED
    else:
        reason = VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_STALE
        decision = VolatilityMaxAgeDecisionV1.DIAGNOSTIC_ONLY
        max_age_status = VolatilityMaxAgeStatusV1.AGE_COMPUTED_THRESHOLD_UNRESOLVED

    enforced = CanonicalVolatilityMaxAgePolicyEvidenceV1(
        policy_name=policy.policy_name,
        policy_version=policy.policy_version,
        estimate_as_of_event_time=base.estimate_as_of_event_time,
        reference_event_time=base.reference_event_time,
        computed_age_seconds=base.computed_age_seconds,
        max_age_status=max_age_status.value,
        threshold_status=policy.threshold_status,
        presence_status=base.presence_status,
        clock_trust_status=base.clock_trust_status,
        data_integrity_status=base.data_integrity_status,
        reuse_status=base.reuse_status,
        restart_status=base.restart_status,
        source_digest=base.source_digest,
        decision=decision.value,
        reason_code=reason.value,
        enforcement_applied=True,
    )
    return BoundedThresholdEnforcementResultV1(
        enforcement_applied=True,
        threshold_enforcement_authorized=True,
        age_evidence=enforced,
        reason_codes=("BOUNDED_THRESHOLD_ENFORCEMENT_APPLIED",),
    )


def apply_bounded_enforcement_to_double_play_alpha_v1(
    *,
    baseline_alpha_allowed: bool,
    enforcement: BoundedThresholdEnforcementResultV1,
) -> tuple[bool, tuple[str, ...]]:
    """Consume enforcement at Double Play alpha boundary without new trading authority."""
    if not enforcement.enforcement_applied:
        return baseline_alpha_allowed, ("ENFORCEMENT_NOT_APPLIED",)
    if enforcement.age_evidence.reason_code == (
        VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_STALE.value
    ):
        return False, ("ALPHA_BLOCKED_BY_BOUNDED_MAX_AGE_ENFORCEMENT",)
    return baseline_alpha_allowed, ("ALPHA_UNCHANGED_FRESH_ESTIMATE",)


__all__ = [
    "DECISION_CONFIG",
    "SCHEMA_VERSION",
    "THRESHOLD_ENFORCEMENT_AUTHORIZED",
    "WORKPACKAGE_ID",
    "BoundedThresholdEnforcementResultV1",
    "apply_bounded_enforcement_to_double_play_alpha_v1",
    "evaluate_bounded_threshold_enforcement_at_mv2_consumer_v1",
    "load_threshold_enforcement_closure_decision_v1",
    "threshold_enforcement_authorized_v1",
    "build_ratified_unresolved_max_age_policy_contract_v1",
]
