"""Runtime checkout vs immutable R1 materialization provenance (fail-closed)."""

from __future__ import annotations

import json
from pathlib import Path

from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.active_binding_v1 import (
    verify_active_campaign_binding_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.models_v1 import (
    ActiveCampaignBindingV1,
    ProductiveCampaignR1RecoveryError,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.preregistration_v1 import (
    verify_r1_active_preregistration_payload_v1,
)


def assert_r1_materialization_provenance_locked_v1(
    binding: ActiveCampaignBindingV1,
    *,
    repo_root: Path,
) -> None:
    """On-disk ACTIVE binding + prereg match canonical builder at materialization SHA.

    ``binding.repository_sha`` is immutable campaign-identity provenance, not CURRENT HEAD.
    """
    verify_active_campaign_binding_v1(binding)
    preg_path = Path(repo_root) / binding.preregistration_artifact_path
    if not preg_path.is_file():
        raise ProductiveCampaignR1RecoveryError("r1_preregistration_artifact_missing")
    try:
        preg_payload = json.loads(preg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProductiveCampaignR1RecoveryError("r1_preregistration_parse_error") from exc
    verify_r1_active_preregistration_payload_v1(
        preg_payload,
        expected_repository_sha=binding.repository_sha,
        expected_campaign_id=binding.campaign_id,
        expected_session_ids=binding.session_ids,
    )


def assert_r1_runtime_checkout_on_origin_main_v1(
    *,
    checkout_sha: str,
    origin_main_sha: str,
) -> None:
    if str(checkout_sha).strip() != str(origin_main_sha).strip():
        raise ProductiveCampaignR1RecoveryError("runtime_checkout_not_origin_main_head")
