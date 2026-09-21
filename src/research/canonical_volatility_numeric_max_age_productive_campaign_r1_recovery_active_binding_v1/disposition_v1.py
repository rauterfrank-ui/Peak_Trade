"""Old-campaign disposition: abandoned incomplete non-authoritative tombstone."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.constants_v1 import (
    DISPOSITION_REL_PATH,
    OLD_CAMPAIGN_COMPLETION_ALLOWED,
    OLD_CAMPAIGN_REACTIVATION_ALLOWED,
    OLD_SESSION_REUSE_ALLOWED,
    OWNER_POLICY,
    SCHEMA_DISPOSITION,
    TOMBSTONE_ABANDONED_CAMPAIGN_ID,
    TOMBSTONE_ABANDONED_REPOSITORY_SHA,
    TOMBSTONE_ABANDONED_SESSION_IDS,
    TOMBSTONE_DISPOSITION,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.digest_v1 import (
    artifact_digest_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.models_v1 import (
    AbandonedCampaignDispositionV1,
    ProductiveCampaignR1RecoveryError,
    require_bool,
    require_mapping,
    require_str,
    require_str_tuple,
)


def build_abandoned_campaign_disposition_v1() -> AbandonedCampaignDispositionV1:
    provisional: dict[str, Any] = {
        "abandoned_repository_sha": TOMBSTONE_ABANDONED_REPOSITORY_SHA,
        "campaign_id": TOMBSTONE_ABANDONED_CAMPAIGN_ID,
        "completion_allowed": OLD_CAMPAIGN_COMPLETION_ALLOWED,
        "disposition": TOMBSTONE_DISPOSITION,
        "owner_policy": OWNER_POLICY,
        "reactivation_allowed": OLD_CAMPAIGN_REACTIVATION_ALLOWED,
        "schema_version": SCHEMA_DISPOSITION,
        "session_ids": list(TOMBSTONE_ABANDONED_SESSION_IDS),
        "session_reuse_allowed": OLD_SESSION_REUSE_ALLOWED,
    }
    provisional["artifact_digest"] = artifact_digest_v1(provisional)
    return parse_abandoned_campaign_disposition_v1(provisional)


def parse_abandoned_campaign_disposition_v1(
    payload: Mapping[str, Any],
) -> AbandonedCampaignDispositionV1:
    raw = require_mapping(payload, field="disposition")
    required = {
        "schema_version",
        "disposition",
        "campaign_id",
        "session_ids",
        "abandoned_repository_sha",
        "completion_allowed",
        "reactivation_allowed",
        "session_reuse_allowed",
        "owner_policy",
        "artifact_digest",
    }
    missing = sorted(required - set(raw.keys()))
    if missing:
        raise ProductiveCampaignR1RecoveryError("disposition_field_missing:" + ",".join(missing))
    unknown = sorted(set(raw.keys()) - required)
    if unknown:
        raise ProductiveCampaignR1RecoveryError("disposition_unknown_field:" + ",".join(unknown))

    parsed = AbandonedCampaignDispositionV1(
        schema_version=require_str(raw, "schema_version"),
        disposition=require_str(raw, "disposition"),
        campaign_id=require_str(raw, "campaign_id"),
        session_ids=require_str_tuple(raw, "session_ids", count=2),
        abandoned_repository_sha=require_str(raw, "abandoned_repository_sha"),
        completion_allowed=require_bool(raw, "completion_allowed", expected=False),
        reactivation_allowed=require_bool(raw, "reactivation_allowed", expected=False),
        session_reuse_allowed=require_bool(raw, "session_reuse_allowed", expected=False),
        owner_policy=require_str(raw, "owner_policy"),
        artifact_digest=require_str(raw, "artifact_digest"),
    )
    return parsed


def verify_abandoned_campaign_disposition_v1(
    disposition: AbandonedCampaignDispositionV1 | Mapping[str, Any],
) -> AbandonedCampaignDispositionV1:
    parsed = (
        disposition
        if isinstance(disposition, AbandonedCampaignDispositionV1)
        else parse_abandoned_campaign_disposition_v1(disposition)
    )
    payload = parsed.to_dict()
    expected = artifact_digest_v1(payload)
    if parsed.artifact_digest != expected:
        raise ProductiveCampaignR1RecoveryError("disposition_digest_mismatch")
    if parsed.schema_version != SCHEMA_DISPOSITION:
        raise ProductiveCampaignR1RecoveryError("disposition_schema_mismatch")
    if parsed.disposition != TOMBSTONE_DISPOSITION:
        raise ProductiveCampaignR1RecoveryError("disposition_value_mismatch")
    if parsed.campaign_id != TOMBSTONE_ABANDONED_CAMPAIGN_ID:
        raise ProductiveCampaignR1RecoveryError("disposition_campaign_mismatch")
    if parsed.session_ids != TOMBSTONE_ABANDONED_SESSION_IDS:
        raise ProductiveCampaignR1RecoveryError("disposition_session_ids_mismatch")
    if parsed.abandoned_repository_sha != TOMBSTONE_ABANDONED_REPOSITORY_SHA:
        raise ProductiveCampaignR1RecoveryError("disposition_repository_sha_mismatch")
    if parsed.owner_policy != OWNER_POLICY:
        raise ProductiveCampaignR1RecoveryError("disposition_owner_policy_mismatch")
    if parsed.completion_allowed or parsed.reactivation_allowed or parsed.session_reuse_allowed:
        raise ProductiveCampaignR1RecoveryError("disposition_must_forbid_reactivation")
    return parsed


def load_abandoned_campaign_disposition_v1(
    *, repo_root: Path, relative_path: str = DISPOSITION_REL_PATH
) -> AbandonedCampaignDispositionV1:
    path = Path(repo_root) / relative_path
    if not path.is_file():
        raise ProductiveCampaignR1RecoveryError("disposition_artifact_missing")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProductiveCampaignR1RecoveryError("disposition_parse_error") from exc
    return verify_abandoned_campaign_disposition_v1(raw)


def assert_campaign_not_tombstone_v1(campaign_id: str) -> None:
    if str(campaign_id).strip() == TOMBSTONE_ABANDONED_CAMPAIGN_ID:
        raise ProductiveCampaignR1RecoveryError("abandoned_campaign_reactivation_forbidden")


def assert_session_not_tombstone_v1(session_id: str) -> None:
    if str(session_id).strip() in TOMBSTONE_ABANDONED_SESSION_IDS:
        raise ProductiveCampaignR1RecoveryError("abandoned_session_reactivation_forbidden")


def assert_old_campaign_cannot_complete_v1(*, campaign_id: str, claimed_complete: bool) -> None:
    if claimed_complete and str(campaign_id).strip() == TOMBSTONE_ABANDONED_CAMPAIGN_ID:
        raise ProductiveCampaignR1RecoveryError("abandoned_campaign_completion_forbidden")
