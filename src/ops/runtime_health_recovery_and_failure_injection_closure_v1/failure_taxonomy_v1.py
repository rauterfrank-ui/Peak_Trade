"""Structured failure taxonomy for O6 offline failure injection and recovery."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional

from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.constants_v1 import (
    BOUNDED_FAILURE_CLASSES,
    HEALTH_COMPONENTS,
)


class FailureTaxonomyErrorV1(ValueError):
    """Fail-closed failure-taxonomy contract violation."""


REQUIRED_FAILURE_FIELDS = (
    "root_cause_class",
    "reason_code",
    "affected_component",
    "session_id",
    "first_failure_time",
    "last_good_time",
    "data_loss_possible",
    "state_divergence_possible",
    "automatic_recovery_allowed",
    "owner_action_required",
    "recovery_eligibility",
)


@dataclass(frozen=True)
class FailureClassificationV1:
    root_cause_class: str
    reason_code: str
    affected_component: str
    session_id: str
    first_failure_time: float
    last_good_time: Optional[float]
    data_loss_possible: bool
    state_divergence_possible: bool
    automatic_recovery_allowed: bool
    owner_action_required: bool
    recovery_eligibility: str
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify_failure_v1(
    *,
    root_cause_class: str,
    reason_code: str,
    affected_component: str,
    session_id: str,
    first_failure_time: float,
    last_good_time: Optional[float],
    data_loss_possible: bool,
    state_divergence_possible: bool,
    automatic_recovery_allowed: bool,
    owner_action_required: bool,
    recovery_eligibility: str,
    detail: str = "",
) -> FailureClassificationV1:
    clazz = str(root_cause_class or "").strip().upper()
    if clazz not in BOUNDED_FAILURE_CLASSES:
        raise FailureTaxonomyErrorV1(f"UNKNOWN_FAILURE_CLASS:{root_cause_class}")
    component = str(affected_component or "").strip().upper()
    if component not in HEALTH_COMPONENTS and component != "SYSTEM":
        raise FailureTaxonomyErrorV1(f"UNKNOWN_AFFECTED_COMPONENT:{affected_component}")
    eligibility = str(recovery_eligibility or "").strip().upper()
    if eligibility not in {"ELIGIBLE", "BLOCKED", "OWNER_LOCK", "NOT_APPLICABLE"}:
        raise FailureTaxonomyErrorV1(f"UNKNOWN_RECOVERY_ELIGIBILITY:{recovery_eligibility}")
    if automatic_recovery_allowed and owner_action_required:
        raise FailureTaxonomyErrorV1("AUTOMATIC_RECOVERY_AND_OWNER_ACTION_CONFLICT")
    record = FailureClassificationV1(
        root_cause_class=clazz,
        reason_code=str(reason_code).strip().upper(),
        affected_component=component,
        session_id=str(session_id),
        first_failure_time=float(first_failure_time),
        last_good_time=None if last_good_time is None else float(last_good_time),
        data_loss_possible=bool(data_loss_possible),
        state_divergence_possible=bool(state_divergence_possible),
        automatic_recovery_allowed=bool(automatic_recovery_allowed),
        owner_action_required=bool(owner_action_required),
        recovery_eligibility=eligibility,
        detail=str(detail or ""),
    )
    assert_failure_fields_complete_v1(record.to_dict())
    return record


def assert_failure_fields_complete_v1(payload: Mapping[str, Any]) -> None:
    missing = [name for name in REQUIRED_FAILURE_FIELDS if name not in payload]
    if missing:
        raise FailureTaxonomyErrorV1(f"MISSING_FAILURE_FIELDS:{','.join(missing)}")


def failure_taxonomy_contract_v1() -> dict[str, Any]:
    return {
        "bounded_failure_classes": list(BOUNDED_FAILURE_CLASSES),
        "required_fields": list(REQUIRED_FAILURE_FIELDS),
        "components": list(HEALTH_COMPONENTS) + ["SYSTEM"],
        "recovery_eligibility_values": ["ELIGIBLE", "BLOCKED", "OWNER_LOCK", "NOT_APPLICABLE"],
    }
