"""M9 ratified numeric max-age threshold capability v1 (semantic only).

Separate capability contract per policy normative: admits typed representation of
an explicitly authorized numeric threshold later. Does not select a value, enable
enforcement, or grant optimization/productive apply authority.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

CAPABILITY_ID: Final[str] = "M9_VOLATILITY_NUMERIC_MAX_AGE_RATIFIED_THRESHOLD_CAPABILITY_V1"
CAPABILITY_VERSION: Final[str] = "m9_volatility_numeric_max_age_ratified_threshold_capability/v1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/M9_VOLATILITY_NUMERIC_MAX_AGE_RATIFIED_THRESHOLD_CAPABILITY_NORMATIVE_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/m9_volatility_numeric_max_age_numeric_productive_target_v1_decision_v1.json"
)
BOUNDS_REF: Final[str] = (
    "config/governance/optimizable_envelope/volatility_numeric_max_age_discrete_bounds_v1.json"
)

THRESHOLD_SEMANTIC_UNIT: Final[str] = "SECONDS"
CONCRETE_THRESHOLD_VALUE_RATIFIED: Final[bool] = False
ENFORCEMENT_ENABLED: Final[bool] = False
OPTIMIZATION_CAN_RATIFY_THRESHOLD: Final[bool] = False

THRESHOLD_STATUS_UNRESOLVED: Final[str] = "UNRESOLVED_MAX_AGE"
THRESHOLD_STATUS_RATIFIED_NUMERIC: Final[str] = "RATIFIED_NUMERIC_THRESHOLD"

_REPO_ROOT = Path(__file__).resolve().parents[2]


class RatifiedThresholdCapabilityError(ValueError):
    """Fail-closed ratified threshold capability validation error."""


class ThresholdValueAuthorizationStatusV1(str, Enum):
    NONE = "NONE"
    AUTHORIZED = "AUTHORIZED"


@dataclass(frozen=True)
class RatifiedNumericMaxAgeThresholdValueV1:
    """Typed numeric threshold value with provenance (value authorization is separate)."""

    numeric_max_age_seconds: float
    threshold_status: str
    unit: str
    authorization_status: ThresholdValueAuthorizationStatusV1
    authorization_digest: str | None
    capability_id: str
    capability_version: str
    provenance_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "authorization_digest": self.authorization_digest,
            "authorization_status": self.authorization_status.value,
            "capability_id": self.capability_id,
            "capability_version": self.capability_version,
            "numeric_max_age_seconds": self.numeric_max_age_seconds,
            "provenance_digest": self.provenance_digest,
            "threshold_status": self.threshold_status,
            "unit": self.unit,
        }


def _load_json(relative_path: str) -> dict[str, Any]:
    path = _REPO_ROOT / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RatifiedThresholdCapabilityError(f"config_not_mapping:{relative_path}")
    return payload


def load_discrete_max_age_seconds_domain_v1() -> tuple[int, ...]:
    bounds = _load_json(BOUNDS_REF)
    candidates = bounds.get("candidate_max_age_seconds")
    if not isinstance(candidates, list) or not candidates:
        raise RatifiedThresholdCapabilityError("DISCRETE_DOMAIN_MISSING")
    return tuple(int(value) for value in candidates)


def validate_numeric_max_age_seconds_domain_v1(value: Any) -> tuple[bool, str]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False, "NUMERIC_TYPE_INVALID"
    numeric = float(value)
    if numeric != numeric or numeric <= 0.0 or numeric == float("inf"):
        return False, "NUMERIC_NOT_POSITIVE_FINITE"
    domain = load_discrete_max_age_seconds_domain_v1()
    if int(numeric) != numeric:
        return False, "NUMERIC_NOT_INTEGER_SECONDS"
    if int(numeric) not in domain:
        return False, "NUMERIC_OUT_OF_DISCRETE_DOMAIN"
    return True, "DOMAIN_OK"


def build_ratified_threshold_capability_identity_v1() -> MappingProxyType[str, Any]:
    body = {
        "capability_id": CAPABILITY_ID,
        "capability_version": CAPABILITY_VERSION,
        "concrete_threshold_value_ratified": CONCRETE_THRESHOLD_VALUE_RATIFIED,
        "enforcement_enabled": ENFORCEMENT_ENABLED,
        "normative_spec": NORMATIVE_SPEC,
        "optimization_can_ratify_threshold": OPTIMIZATION_CAN_RATIFY_THRESHOLD,
        "threshold_semantic_unit": THRESHOLD_SEMANTIC_UNIT,
        "threshold_status_unresolved": THRESHOLD_STATUS_UNRESOLVED,
        "threshold_status_ratified_numeric": THRESHOLD_STATUS_RATIFIED_NUMERIC,
        "discrete_domain_ref": BOUNDS_REF,
        "discrete_domain_digest": compute_content_sha256(_load_json(BOUNDS_REF)),
    }
    body["capability_identity_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "capability_identity_digest"}
    )
    return MappingProxyType(body)


def materialize_ratified_numeric_max_age_threshold_value_v1(
    *,
    numeric_max_age_seconds: float,
    authorization_status: ThresholdValueAuthorizationStatusV1,
    authorization_digest: str | None,
) -> RatifiedNumericMaxAgeThresholdValueV1:
    ok, reason = validate_numeric_max_age_seconds_domain_v1(numeric_max_age_seconds)
    if not ok:
        raise RatifiedThresholdCapabilityError(reason)
    if authorization_status is ThresholdValueAuthorizationStatusV1.NONE:
        raise RatifiedThresholdCapabilityError("THRESHOLD_VALUE_AUTHORIZATION_REQUIRED")
    if not authorization_digest or not is_valid_sha256_hex(authorization_digest):
        raise RatifiedThresholdCapabilityError("THRESHOLD_VALUE_AUTHORIZATION_DIGEST_INVALID")
    capability = build_ratified_threshold_capability_identity_v1()
    provenance_body = {
        "capability_identity_digest": capability["capability_identity_digest"],
        "numeric_max_age_seconds": float(numeric_max_age_seconds),
        "authorization_digest": authorization_digest,
    }
    return RatifiedNumericMaxAgeThresholdValueV1(
        numeric_max_age_seconds=float(numeric_max_age_seconds),
        threshold_status=THRESHOLD_STATUS_RATIFIED_NUMERIC,
        unit=THRESHOLD_SEMANTIC_UNIT,
        authorization_status=authorization_status,
        authorization_digest=authorization_digest,
        capability_id=CAPABILITY_ID,
        capability_version=CAPABILITY_VERSION,
        provenance_digest=compute_content_sha256(provenance_body),
    )


def assert_ratified_threshold_capability_non_goals_v1() -> MappingProxyType[str, Any]:
    return MappingProxyType(
        {
            "capability_id": CAPABILITY_ID,
            "concrete_threshold_value_ratified": CONCRETE_THRESHOLD_VALUE_RATIFIED,
            "enforcement_enabled": ENFORCEMENT_ENABLED,
            "optimization_can_ratify_threshold": OPTIMIZATION_CAN_RATIFY_THRESHOLD,
            "threshold_selection_by_capability": False,
            "default_threshold_introduced": False,
        }
    )
