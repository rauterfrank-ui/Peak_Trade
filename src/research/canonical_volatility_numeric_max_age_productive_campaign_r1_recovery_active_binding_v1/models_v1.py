"""Typed models for R1 disposition and active campaign binding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


class ProductiveCampaignR1RecoveryError(ValueError):
    """Fail-closed R1 recovery / active-binding error."""


@dataclass(frozen=True)
class AbandonedCampaignDispositionV1:
    schema_version: str
    disposition: str
    campaign_id: str
    session_ids: tuple[str, ...]
    abandoned_repository_sha: str
    completion_allowed: bool
    reactivation_allowed: bool
    session_reuse_allowed: bool
    owner_policy: str
    artifact_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "abandoned_repository_sha": self.abandoned_repository_sha,
            "artifact_digest": self.artifact_digest,
            "campaign_id": self.campaign_id,
            "completion_allowed": self.completion_allowed,
            "disposition": self.disposition,
            "owner_policy": self.owner_policy,
            "reactivation_allowed": self.reactivation_allowed,
            "schema_version": self.schema_version,
            "session_ids": list(self.session_ids),
            "session_reuse_allowed": self.session_reuse_allowed,
        }


@dataclass(frozen=True)
class ActiveCampaignBindingV1:
    schema_version: str
    status: str
    owner_policy: str
    repository_sha: str
    campaign_id: str
    session_ids: tuple[str, ...]
    session_01_id: str
    session_02_id: str
    preregistration_artifact_path: str
    preregistration_digest: str
    typed_volatility_persistence_path: str
    retained_estimate_lifecycle_carrier_path: str
    early_estimate_producer_session_id: str
    late_age_observation_session_id: str
    execution_authorized: bool
    network_authorized: bool
    evidence_write_authorized: bool
    artifact_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_digest": self.artifact_digest,
            "campaign_id": self.campaign_id,
            "early_estimate_producer_session_id": self.early_estimate_producer_session_id,
            "evidence_write_authorized": self.evidence_write_authorized,
            "execution_authorized": self.execution_authorized,
            "late_age_observation_session_id": self.late_age_observation_session_id,
            "network_authorized": self.network_authorized,
            "owner_policy": self.owner_policy,
            "preregistration_artifact_path": self.preregistration_artifact_path,
            "preregistration_digest": self.preregistration_digest,
            "repository_sha": self.repository_sha,
            "retained_estimate_lifecycle_carrier_path": (
                self.retained_estimate_lifecycle_carrier_path
            ),
            "schema_version": self.schema_version,
            "session_01_id": self.session_01_id,
            "session_02_id": self.session_02_id,
            "session_ids": list(self.session_ids),
            "status": self.status,
            "typed_volatility_persistence_path": self.typed_volatility_persistence_path,
        }


def require_mapping(payload: Mapping[str, Any] | None, *, field: str) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise ProductiveCampaignR1RecoveryError(f"{field}_not_object")
    return payload


def require_str(payload: Mapping[str, Any], key: str) -> str:
    value = str(payload.get(key) or "").strip()
    if not value:
        raise ProductiveCampaignR1RecoveryError(f"{key}_required")
    return value


def require_bool(payload: Mapping[str, Any], key: str, *, expected: bool | None = None) -> bool:
    if key not in payload or not isinstance(payload[key], bool):
        raise ProductiveCampaignR1RecoveryError(f"{key}_bool_required")
    value = bool(payload[key])
    if expected is not None and value is not expected:
        raise ProductiveCampaignR1RecoveryError(f"{key}_must_be_{expected}")
    return value


def require_str_tuple(
    payload: Mapping[str, Any], key: str, *, count: int | None = None
) -> tuple[str, ...]:
    raw = payload.get(key)
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ProductiveCampaignR1RecoveryError(f"{key}_list_required")
    values = tuple(str(x).strip() for x in raw)
    if any(not x for x in values):
        raise ProductiveCampaignR1RecoveryError(f"{key}_blank_entry")
    if len(values) != len(set(values)):
        raise ProductiveCampaignR1RecoveryError(f"{key}_not_unique")
    if count is not None and len(values) != count:
        raise ProductiveCampaignR1RecoveryError(f"{key}_count_mismatch")
    return values
