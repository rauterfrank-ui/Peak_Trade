"""Read-only campaign bundle owner — aggregates completed Step-7 sessions."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.constants_v1 import (
    CAMPAIGN_BUNDLE_OWNER,
    CAMPAIGN_BUNDLE_SCHEMA_VERSION,
    CAMPAIGN_ID,
    MULTI_SESSION_REQUIREMENT_EXPRESSION,
    TARGET_CAMPAIGN_CAPABILITY_ID,
    multi_session_requirement_satisfied_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.digest_v1 import (
    read_json_v1,
    sha256_canonical_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.per_session_evidence_contract_v1 import (
    verify_per_session_evidence_v1,
)


class CampaignBundleError(ValueError):
    """Invalid campaign bundle assembly."""


def build_campaign_bundle_v1(
    *,
    sessions: Sequence[Mapping[str, Any]],
    expected_repository_sha: str,
    expected_config_digest: str,
    campaign_id: str = CAMPAIGN_ID,
    allowed_binding_transitions: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    session_list = [dict(s) for s in sessions]
    session_list.sort(key=lambda s: int(s.get("session_ordinal") or 0))
    per_session_verdicts = [verify_per_session_evidence_v1(s) for s in session_list]
    bundle: dict[str, Any] = {
        "schema_version": CAMPAIGN_BUNDLE_SCHEMA_VERSION,
        "owner": CAMPAIGN_BUNDLE_OWNER,
        "capability_id": TARGET_CAMPAIGN_CAPABILITY_ID,
        "campaign_id": campaign_id,
        "aggregation_mode": "READ_ONLY",
        "network_session_started_by_bundle_owner": False,
        "authorization_consumed_by_bundle_owner": False,
        "confirm_token_minted_by_bundle_owner": False,
        "confirm_token_consumed_by_bundle_owner": False,
        "expected_repository_sha": expected_repository_sha,
        "expected_config_digest": expected_config_digest,
        "allowed_binding_transitions": [dict(t) for t in (allowed_binding_transitions or [])],
        "multi_session_requirement_expression": MULTI_SESSION_REQUIREMENT_EXPRESSION,
        "session_count": len(session_list),
        "multi_session_requirement_satisfied": multi_session_requirement_satisfied_v1(
            len(session_list)
        ),
        "sessions": session_list,
        "per_session_verdicts": per_session_verdicts,
        "bundle_digest": "",
    }
    bundle["bundle_digest"] = sha256_canonical_v1(
        {k: v for k, v in bundle.items() if k != "bundle_digest"}
    )
    return bundle


def load_session_evidence_paths_v1(paths: Sequence[Path]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in paths:
        payload = read_json_v1(Path(path))
        if not isinstance(payload, dict):
            raise CampaignBundleError(f"SESSION_EVIDENCE_NOT_OBJECT:{path}")
        out.append(payload)
    return out


def aggregate_completed_sessions_read_only_v1(
    *,
    session_evidence_paths: Sequence[Path],
    expected_repository_sha: str,
    expected_config_digest: str,
    allowed_binding_transitions: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Aggregate already-completed Step-7 session evidence. Never starts sessions."""
    sessions = load_session_evidence_paths_v1(session_evidence_paths)
    return build_campaign_bundle_v1(
        sessions=sessions,
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        allowed_binding_transitions=allowed_binding_transitions,
    )
