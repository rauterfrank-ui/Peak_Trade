"""Runtime Owner authorization record schema and resolver (no live record in max-build)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    CAMPAIGN_ID,
    PREREGISTRATION_DIGEST,
    PREREGISTRATION_ID,
    RUNTIME_AUTHORIZATION_SCHEMA_VERSION,
    SELECTION_POLICY_DIGEST,
    SELECTION_POLICY_ID,
    SELECTION_RULE_ID,
    SOURCE_PARAMETER_ID,
    SURFACE_ID,
    TARGET_PARAMETER_ID,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex


@dataclass(frozen=True, slots=True)
class F1M9ProspectiveCampaignRuntimeAuthorizationV1:
    schema_version: str
    authorization_id: str
    campaign_id: str
    preregistration_id: str
    preregistration_digest: str
    selection_policy_id: str
    selection_policy_digest: str
    selection_rule_id: str
    surface_id: str
    parameter_id: str
    source_parameter_id: str
    campaign_execution_authorized: bool
    public_market_data_read_authorized: bool
    durable_evidence_write_authorized: bool
    authorized_data_source: str
    authorized_public_md_venue: str
    authorized_public_md_host: str
    earliest_valid_utc: str
    expires_at_utc: str
    owner_identity: str
    decision_identity: str
    execution_idempotency_key: str
    authorization_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "authorization_id": self.authorization_id,
            "campaign_id": self.campaign_id,
            "preregistration_id": self.preregistration_id,
            "preregistration_digest": self.preregistration_digest,
            "selection_policy_id": self.selection_policy_id,
            "selection_policy_digest": self.selection_policy_digest,
            "selection_rule_id": self.selection_rule_id,
            "surface_id": self.surface_id,
            "parameter_id": self.parameter_id,
            "source_parameter_id": self.source_parameter_id,
            "campaign_execution_authorized": self.campaign_execution_authorized,
            "public_market_data_read_authorized": self.public_market_data_read_authorized,
            "durable_evidence_write_authorized": self.durable_evidence_write_authorized,
            "authorized_data_source": self.authorized_data_source,
            "authorized_public_md_venue": self.authorized_public_md_venue,
            "authorized_public_md_host": self.authorized_public_md_host,
            "earliest_valid_utc": self.earliest_valid_utc,
            "expires_at_utc": self.expires_at_utc,
            "owner_identity": self.owner_identity,
            "decision_identity": self.decision_identity,
            "execution_idempotency_key": self.execution_idempotency_key,
            "authorization_digest": self.authorization_digest,
        }


def authorization_body_for_digest(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k != "authorization_digest"}


def compute_runtime_authorization_digest(payload: Mapping[str, Any]) -> str:
    return compute_content_sha256(authorization_body_for_digest(payload))


def build_runtime_authorization_template_v1(
    *,
    authorization_id: str = "TEMPLATE_INACTIVE",
    owner_identity: str = "OWNER",
    decision_identity: str = "PENDING_OWNER_GO",
    execution_idempotency_key: str = "",
    authorized_data_source: str = "REAL_PUBLIC_MARKET_DATA",
    authorized_public_md_venue: str = "OKX_EEA",
    authorized_public_md_host: str = "eea.okx.com",
    earliest_valid_utc: str = "2099-01-01T00:00:00Z",
    expires_at_utc: str = "2099-01-01T00:01:00Z",
) -> dict[str, Any]:
    """Inactive template for schema/tests; not a live authorization."""
    body: dict[str, Any] = {
        "schema_version": RUNTIME_AUTHORIZATION_SCHEMA_VERSION,
        "authorization_id": authorization_id,
        "campaign_id": CAMPAIGN_ID,
        "preregistration_id": PREREGISTRATION_ID,
        "preregistration_digest": PREREGISTRATION_DIGEST,
        "selection_policy_id": SELECTION_POLICY_ID,
        "selection_policy_digest": SELECTION_POLICY_DIGEST,
        "selection_rule_id": SELECTION_RULE_ID,
        "surface_id": SURFACE_ID,
        "parameter_id": TARGET_PARAMETER_ID,
        "source_parameter_id": SOURCE_PARAMETER_ID,
        "campaign_execution_authorized": False,
        "public_market_data_read_authorized": False,
        "durable_evidence_write_authorized": False,
        "authorized_data_source": authorized_data_source,
        "authorized_public_md_venue": authorized_public_md_venue,
        "authorized_public_md_host": authorized_public_md_host,
        "earliest_valid_utc": earliest_valid_utc,
        "expires_at_utc": expires_at_utc,
        "owner_identity": owner_identity,
        "decision_identity": decision_identity,
        "execution_idempotency_key": execution_idempotency_key or f"{CAMPAIGN_ID}:pending",
    }
    body["authorization_digest"] = compute_runtime_authorization_digest(body)
    return body


def verify_runtime_authorization_v1(payload: Mapping[str, Any]) -> None:
    stored = str(payload.get("authorization_digest") or "")
    if not is_valid_sha256_hex(stored):
        raise ValueError("AUTHORIZATION_DIGEST_INVALID")
    if compute_runtime_authorization_digest(payload) != stored:
        raise ValueError("AUTHORIZATION_DIGEST_MISMATCH")
    if str(payload.get("campaign_id") or "") != CAMPAIGN_ID:
        raise ValueError("CAMPAIGN_ID_MISMATCH")
    if str(payload.get("preregistration_digest") or "") != PREREGISTRATION_DIGEST:
        raise ValueError("PREREGISTRATION_DIGEST_MISMATCH")
    if str(payload.get("selection_policy_digest") or "") != SELECTION_POLICY_DIGEST:
        raise ValueError("SELECTION_POLICY_DIGEST_MISMATCH")
    if str(payload.get("selection_rule_id") or "") != SELECTION_RULE_ID:
        raise ValueError("SELECTION_RULE_MISMATCH")


def resolve_runtime_authorization_v1(
    payload: Mapping[str, Any] | None,
    *,
    evaluation_time_utc: datetime | None = None,
) -> tuple[F1M9ProspectiveCampaignRuntimeAuthorizationV1 | None, tuple[str, ...]]:
    if payload is None:
        return None, ("RUNTIME_AUTHORIZATION_ABSENT",)
    try:
        verify_runtime_authorization_v1(payload)
    except ValueError as exc:
        return None, (str(exc),)

    now = evaluation_time_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    earliest = datetime.fromisoformat(str(payload["earliest_valid_utc"]).replace("Z", "+00:00"))
    expires = datetime.fromisoformat(str(payload["expires_at_utc"]).replace("Z", "+00:00"))
    reasons: list[str] = []
    if now < earliest:
        reasons.append("AUTHORIZATION_NOT_YET_VALID")
    if now >= expires:
        reasons.append("AUTHORIZATION_EXPIRED")
    if payload.get("campaign_execution_authorized") is not True:
        reasons.append("CAMPAIGN_EXECUTION_NOT_AUTHORIZED")

    auth = F1M9ProspectiveCampaignRuntimeAuthorizationV1(
        schema_version=str(payload["schema_version"]),
        authorization_id=str(payload["authorization_id"]),
        campaign_id=str(payload["campaign_id"]),
        preregistration_id=str(payload["preregistration_id"]),
        preregistration_digest=str(payload["preregistration_digest"]),
        selection_policy_id=str(payload["selection_policy_id"]),
        selection_policy_digest=str(payload["selection_policy_digest"]),
        selection_rule_id=str(payload["selection_rule_id"]),
        surface_id=str(payload["surface_id"]),
        parameter_id=str(payload["parameter_id"]),
        source_parameter_id=str(payload["source_parameter_id"]),
        campaign_execution_authorized=bool(payload.get("campaign_execution_authorized")),
        public_market_data_read_authorized=bool(payload.get("public_market_data_read_authorized")),
        durable_evidence_write_authorized=bool(payload.get("durable_evidence_write_authorized")),
        authorized_data_source=str(payload.get("authorized_data_source") or ""),
        authorized_public_md_venue=str(payload.get("authorized_public_md_venue") or ""),
        authorized_public_md_host=str(payload.get("authorized_public_md_host") or ""),
        earliest_valid_utc=str(payload["earliest_valid_utc"]),
        expires_at_utc=str(payload["expires_at_utc"]),
        owner_identity=str(payload.get("owner_identity") or ""),
        decision_identity=str(payload.get("decision_identity") or ""),
        execution_idempotency_key=str(payload.get("execution_idempotency_key") or ""),
        authorization_digest=str(payload["authorization_digest"]),
    )
    if reasons:
        return auth, tuple(reasons)
    return auth, ()


def load_runtime_authorization_from_path_v1(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("RUNTIME_AUTHORIZATION_NOT_MAPPING")
    return payload


__all__ = [
    "F1M9ProspectiveCampaignRuntimeAuthorizationV1",
    "authorization_body_for_digest",
    "build_runtime_authorization_template_v1",
    "compute_runtime_authorization_digest",
    "load_runtime_authorization_from_path_v1",
    "resolve_runtime_authorization_v1",
    "verify_runtime_authorization_v1",
]
