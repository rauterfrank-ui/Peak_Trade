"""Owner Threshold Value record materialization (digest-sealed; Owner GO required)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.f1_m9_canonical_productive_candidate_adjudication_v1 import (
    adjudicate_canonical_f1_m9_productive_candidate_v1,
)
from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
    OwnerApplyAuthorizationInputV1,
)
from src.governance.f1_m9_owner_threshold_value_authorization_record_v1 import (
    OwnerThresholdValueAuthorizationInputV1,
    build_owner_threshold_value_authorization_input_v1,
)
from src.governance.f1_m9_owner_threshold_value_ratification_artifacts_v1 import (
    OWNER_THRESHOLD_RATIFICATION_WP_DECISION_CONFIG,
)
from src.governance.f1_m9_post_real_campaign_productive_handoff_bounded_completion_v1 import (
    DECISION_CONFIG as HANDOFF_DECISION_CONFIG,
)
from src.governance.governed_productive_configuration_v1 import (
    GovernedProductiveConfigurationResultV1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    PRODUCTIVE_TARGET_ID,
    build_productive_target_contract_v1,
)
from src.governance.m9_volatility_numeric_max_age_ratified_threshold_capability_v1 import (
    CAPABILITY_ID as RATIFIED_THRESHOLD_CAPABILITY_ID,
    CAPABILITY_VERSION as RATIFIED_THRESHOLD_CAPABILITY_VERSION,
    validate_numeric_max_age_seconds_domain_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "f1_m9_owner_threshold_value_record_materialization/v1"
WORKPACKAGE_ID: Final[str] = (
    "GOVERNED_F1_M9_SCOPED_OWNER_THRESHOLD_VALUE_RATIFICATION_REAL_MECHANICAL_CONTINUATION_V1"
)

STATUS_DENIED: Final[str] = "OWNER_THRESHOLD_RECORD_MATERIALIZATION_DENIED"
STATUS_MATERIALIZED: Final[str] = "OWNER_THRESHOLD_RECORD_MATERIALIZED"


@dataclass(frozen=True, slots=True)
class OwnerThresholdValueRecordMaterializationResultV1:
    materialization_status: str
    reason_codes: tuple[str, ...]
    owner_threshold_input: OwnerThresholdValueAuthorizationInputV1 | None
    owner_wp_decision_digest: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "materialization_status": self.materialization_status,
            "owner_threshold_record_digest": (
                None
                if self.owner_threshold_input is None
                else self.owner_threshold_input.owner_threshold_authorization_record_digest
            ),
            "owner_wp_decision_digest": self.owner_wp_decision_digest,
            "reason_codes": list(self.reason_codes),
        }


def load_owner_threshold_ratification_wp_decision_v1(
    *, repo_root: Path | None = None
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    path = root / OWNER_THRESHOLD_RATIFICATION_WP_DECISION_CONFIG
    if not path.is_file():
        raise FileNotFoundError(OWNER_THRESHOLD_RATIFICATION_WP_DECISION_CONFIG)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("OWNER_WP_DECISION_NOT_MAPPING")
    return payload


def _threshold_window_from_handoff_v1(*, repo_root: Path) -> tuple[str, str]:
    path = repo_root / HANDOFF_DECISION_CONFIG
    payload = json.loads(path.read_text(encoding="utf-8"))
    return str(payload["owner_apply_not_before_utc"]), str(payload["owner_apply_expires_at_utc"])


def materialize_owner_threshold_value_record_when_owner_ratification_authorized_v1(
    *,
    registry_digest: str,
    binding_digest: str,
    applied_configuration: GovernedProductiveConfigurationResultV1,
    apply_input: OwnerApplyAuthorizationInputV1,
    repo_root: Path | None = None,
) -> OwnerThresholdValueRecordMaterializationResultV1:
    """Fail-closed: Owner WP decision + canonical candidate + applied configuration lineage."""
    root = repo_root or Path(__file__).resolve().parents[2]
    reasons: list[str] = []

    try:
        owner_wp = load_owner_threshold_ratification_wp_decision_v1(repo_root=root)
    except (FileNotFoundError, ValueError) as exc:
        return OwnerThresholdValueRecordMaterializationResultV1(
            materialization_status=STATUS_DENIED,
            reason_codes=(str(exc),),
            owner_threshold_input=None,
            owner_wp_decision_digest=None,
        )

    wp_body = {k: v for k, v in owner_wp.items() if k != "owner_wp_decision_digest"}
    wp_digest = compute_content_sha256(wp_body)

    if owner_wp.get("owner_threshold_value_ratification_authorized") is not True:
        reasons.append("OWNER_THRESHOLD_VALUE_RATIFICATION_NOT_AUTHORIZED")
    ratified_seconds = owner_wp.get("threshold_numeric_max_age_seconds")
    if not isinstance(ratified_seconds, (int, float)) or isinstance(ratified_seconds, bool):
        reasons.append("OWNER_RATIFIED_SECONDS_INVALID")
    else:
        domain_ok, domain_reason = validate_numeric_max_age_seconds_domain_v1(ratified_seconds)
        if not domain_ok:
            reasons.append(domain_reason)

    bounds_ref = str(owner_wp.get("discrete_bounds_config") or "")
    bounds_path = root / bounds_ref
    if not bounds_ref or not bounds_path.is_file():
        reasons.append("DISCRETE_BOUNDS_CONFIG_MISSING")
    else:
        bounds_payload = json.loads(bounds_path.read_text(encoding="utf-8"))
        expected_domain_digest = str(owner_wp.get("discrete_domain_digest") or "")
        actual_digest = compute_content_sha256(bounds_payload)
        if not is_valid_sha256_hex(expected_domain_digest):
            reasons.append("DISCRETE_DOMAIN_DIGEST_INVALID")
        elif expected_domain_digest != actual_digest:
            reasons.append("DISCRETE_DOMAIN_DIGEST_MISMATCH")

    if str(owner_wp.get("optimization_surface_id") or "") != (
        "VOLATILITY_NUMERIC_MAX_AGE_RESEARCH_OPTIMIZATION_V1"
    ):
        reasons.append("OPTIMIZATION_SURFACE_ID_MISMATCH")
    if str(owner_wp.get("productive_target_id") or "") != PRODUCTIVE_TARGET_ID:
        reasons.append("PRODUCTIVE_TARGET_ID_MISMATCH")

    adjudication = adjudicate_canonical_f1_m9_productive_candidate_v1(repo_root=root)
    if not adjudication.resolved:
        reasons.append(adjudication.earliest_blocker)
    elif adjudication.candidate_value != float(ratified_seconds):
        reasons.append("OWNER_RATIFIED_VALUE_CANDIDATE_MISMATCH")

    record = applied_configuration.configuration_record
    if record is None:
        reasons.append("APPLIED_CONFIGURATION_RECORD_MISSING")
        return OwnerThresholdValueRecordMaterializationResultV1(
            materialization_status=STATUS_DENIED,
            reason_codes=tuple(reasons),
            owner_threshold_input=None,
            owner_wp_decision_digest=wp_digest,
        )

    if record.get("runtime_applied") is not True:
        reasons.append("PRODUCTIVE_APPLY_REQUIRED_BEFORE_THRESHOLD")
    config_numeric = record.get("numeric_max_age_seconds")
    if float(config_numeric) != float(ratified_seconds):
        reasons.append("CONFIGURATION_NUMERIC_MISMATCH_OWNER_RATIFICATION")
    if float(record.get("authorized_candidate_max_age_seconds")) != float(ratified_seconds):
        reasons.append("AUTHORIZED_CANDIDATE_NUMERIC_MISMATCH")

    if reasons:
        return OwnerThresholdValueRecordMaterializationResultV1(
            materialization_status=STATUS_DENIED,
            reason_codes=tuple(dict.fromkeys(reasons)),
            owner_threshold_input=None,
            owner_wp_decision_digest=wp_digest,
        )

    contract = build_productive_target_contract_v1()
    not_before, expires_at = _threshold_window_from_handoff_v1(repo_root=root)
    apply_digest = str(apply_input.owner_apply_authorization_record_digest)
    authorizer = str(
        owner_wp.get("authorizer_identity") or "OWNER_GO_F1_M9_THRESHOLD_VALUE_RATIFICATION"
    )

    threshold_input = build_owner_threshold_value_authorization_input_v1(
        registry_digest=registry_digest,
        ingress_digest=str(record["ingress_digest"]),
        per_ingress_binding_digest=binding_digest,
        owner_authorization_record_digest=str(record["owner_authorization_record_digest"]),
        authorization_id=str(record["authorization_id"]),
        authorization_digest=str(record["authorization_digest"]),
        configuration_id=str(record["configuration_id"]),
        configuration_digest=str(record["configuration_digest"]),
        candidate_parameter_value_digest=str(record["candidate_parameter_value_digest"]),
        productive_target_id=str(record["productive_target_id"]),
        productive_target_version=str(record["productive_target_version"]),
        productive_target_contract_digest=str(contract["contract_digest"]),
        ratified_threshold_capability_id=str(
            record.get("threshold_capability_id") or RATIFIED_THRESHOLD_CAPABILITY_ID
        ),
        ratified_threshold_capability_version=str(
            record.get("threshold_capability_version") or RATIFIED_THRESHOLD_CAPABILITY_VERSION
        ),
        owner_apply_authorization_record_digest=apply_digest,
        productive_apply_authorization_digest=apply_digest,
        threshold_numeric_max_age_seconds=float(ratified_seconds),
        not_before=not_before,
        expires_at=expires_at,
    )
    body = dict(threshold_input.owner_threshold_authorization_record)
    body["authorizer_identity"] = authorizer
    from src.governance.f1_m9_owner_threshold_value_authorization_record_v1 import (
        compute_owner_threshold_value_authorization_record_digest_v1,
    )

    body["threshold_value_authorization_record_digest"] = (
        compute_owner_threshold_value_authorization_record_digest_v1(body)
    )
    threshold_input = OwnerThresholdValueAuthorizationInputV1(
        owner_threshold_authorization_record=body,
        owner_threshold_authorization_record_digest=str(
            body["threshold_value_authorization_record_digest"]
        ),
    )

    return OwnerThresholdValueRecordMaterializationResultV1(
        materialization_status=STATUS_MATERIALIZED,
        reason_codes=("OWNER_THRESHOLD_RECORD_MATERIALIZED",),
        owner_threshold_input=threshold_input,
        owner_wp_decision_digest=wp_digest,
    )


__all__ = [
    "OwnerThresholdValueRecordMaterializationResultV1",
    "SCHEMA_VERSION",
    "STATUS_DENIED",
    "STATUS_MATERIALIZED",
    "WORKPACKAGE_ID",
    "load_owner_threshold_ratification_wp_decision_v1",
    "materialize_owner_threshold_value_record_when_owner_ratification_authorized_v1",
]
