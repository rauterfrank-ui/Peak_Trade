"""Runner/auth gates for sole ACTIVE campaign binding + S02 persistence requirement."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.active_binding_v1 import (
    assert_exactly_one_active_binding_file_v1,
    load_active_campaign_binding_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.compatibility_v1 import (
    assert_r1_materialization_provenance_locked_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.disposition_v1 import (
    assert_campaign_not_tombstone_v1,
    assert_old_campaign_cannot_complete_v1,
    assert_session_not_tombstone_v1,
    load_abandoned_campaign_disposition_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.models_v1 import (
    ActiveCampaignBindingV1,
    ProductiveCampaignR1RecoveryError,
)


def resolve_active_campaign_binding_for_runtime_v1(
    *,
    repo_root: Path,
) -> ActiveCampaignBindingV1:
    """Load disposition + ACTIVE binding; lock materialization provenance (not HEAD)."""
    load_abandoned_campaign_disposition_v1(repo_root=repo_root)
    assert_exactly_one_active_binding_file_v1(repo_root=repo_root)
    binding = load_active_campaign_binding_v1(repo_root=repo_root)
    assert_r1_materialization_provenance_locked_v1(binding, repo_root=repo_root)
    return binding


def assert_runtime_matches_active_binding_v1(
    binding: ActiveCampaignBindingV1,
    *,
    campaign_id: str,
    session_id: str,
    preregistration_digest: str,
    repository_sha: str,
) -> None:
    assert_campaign_not_tombstone_v1(campaign_id)
    assert_session_not_tombstone_v1(session_id)
    if campaign_id != binding.campaign_id:
        raise ProductiveCampaignR1RecoveryError("runtime_campaign_not_active_binding")
    if session_id not in binding.session_ids:
        raise ProductiveCampaignR1RecoveryError("runtime_session_not_active_binding")
    if preregistration_digest != binding.preregistration_digest:
        raise ProductiveCampaignR1RecoveryError("runtime_preregistration_digest_mismatch")
    if repository_sha != binding.repository_sha:
        raise ProductiveCampaignR1RecoveryError("runtime_repository_sha_mismatch")


def assert_late_age_session_has_s01_persistence_v1(
    binding: ActiveCampaignBindingV1,
    *,
    session_id: str,
    repo_root: Path,
    evidence_root: Optional[Path] = None,
) -> None:
    """S02 late-age requires durable S01 typed persistence; missing => absent (fail closed)."""
    if session_id != binding.session_02_id:
        return
    root = Path(evidence_root) if evidence_root is not None else Path(repo_root)
    persist = root / binding.typed_volatility_persistence_path
    if not persist.is_file() or persist.stat().st_size <= 0:
        raise ProductiveCampaignR1RecoveryError("missing_s01_persistence_for_late_age_session")


def assert_late_age_session_has_s01_retained_estimate_carrier_v1(
    binding: ActiveCampaignBindingV1,
    *,
    session_id: str,
    repo_root: Path,
    evidence_root: Optional[Path] = None,
) -> None:
    """S02 late-age requires atomically finalized S01 retained-estimate carrier."""
    if session_id != binding.session_02_id:
        return
    root = Path(evidence_root) if evidence_root is not None else Path(repo_root)
    carrier = root / binding.retained_estimate_lifecycle_carrier_path
    if not carrier.is_file() or carrier.stat().st_size <= 0:
        raise ProductiveCampaignR1RecoveryError(
            "missing_s01_retained_estimate_carrier_for_late_age_session"
        )


def assert_not_additional_evidence_routing_v1(*, campaign_id: str) -> None:
    if "additional_evidence" in str(campaign_id):
        raise ProductiveCampaignR1RecoveryError("additional_evidence_routing_forbidden")


def gate_status_payload_v1(
    *, ok: bool, binding: ActiveCampaignBindingV1 | None = None, blocker: str = ""
) -> dict[str, Any]:
    return {
        "ok": bool(ok),
        "blocker": str(blocker or ""),
        "active_campaign_id": None if binding is None else binding.campaign_id,
        "active_session_ids": None if binding is None else list(binding.session_ids),
        "old_campaign_completion_forbidden": True,
        "cross_sha_reuse_allowed": False,
        "synthetic_s01_allowed": False,
        "additional_evidence_reclassification": False,
    }


# Re-export completion guard for tests/callers.
__all__ = [
    "assert_late_age_session_has_s01_persistence_v1",
    "assert_late_age_session_has_s01_retained_estimate_carrier_v1",
    "assert_not_additional_evidence_routing_v1",
    "assert_old_campaign_cannot_complete_v1",
    "assert_runtime_matches_active_binding_v1",
    "gate_status_payload_v1",
    "resolve_active_campaign_binding_for_runtime_v1",
]
