"""Deterministic R1 campaign/session identity derivation."""

from __future__ import annotations

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.session_campaign_preregistration_v1 import (
    _campaign_durable_paths,
    _deterministic_campaign_id,
    _deterministic_session_id,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.constants_v1 import (
    TOMBSTONE_ABANDONED_CAMPAIGN_ID,
    TOMBSTONE_ABANDONED_SESSION_IDS,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.models_v1 import (
    ProductiveCampaignR1RecoveryError,
)


def derive_r1_campaign_identity_v1(*, repository_sha: str) -> dict[str, str]:
    sha = str(repository_sha or "").strip()
    if not sha or len(sha) < 7:
        raise ProductiveCampaignR1RecoveryError("repository_sha_required")
    campaign_id = _deterministic_campaign_id(repository_sha=sha)
    if campaign_id == TOMBSTONE_ABANDONED_CAMPAIGN_ID:
        raise ProductiveCampaignR1RecoveryError("derived_campaign_collides_with_tombstone")
    session_01 = _deterministic_session_id(campaign_id=campaign_id, session_index=1)
    session_02 = _deterministic_session_id(campaign_id=campaign_id, session_index=2)
    if (
        session_01 in TOMBSTONE_ABANDONED_SESSION_IDS
        or session_02 in TOMBSTONE_ABANDONED_SESSION_IDS
    ):
        raise ProductiveCampaignR1RecoveryError("derived_session_collides_with_tombstone")
    paths = _campaign_durable_paths(campaign_id=campaign_id)
    return {
        "campaign_id": campaign_id,
        "session_01_id": session_01,
        "session_02_id": session_02,
        "typed_volatility_persistence_path": str(paths["typed_volatility_persistence_path"]),
        "campaign_manifest_path": str(paths["campaign_manifest_path"]),
    }
