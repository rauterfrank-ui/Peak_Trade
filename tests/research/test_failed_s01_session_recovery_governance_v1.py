"""Failed S01 campaign recovery governance (read-only semantics)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.active_binding_v1 import (
    build_active_campaign_binding_v1,
    load_active_campaign_binding_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.failed_s01_session_recovery_governance_v1 import (
    FRESH_CAMPAIGN_REMATERIALIZATION_REQUIRED_FOR_SUCCESS_PATH,
    REMAINING_AUTH_SLOT_IS_NOT_RECOVERY,
    S01_RETRY_SAME_SESSION_FORBIDDEN,
    S02_START_AFTER_FAILED_S01_FORBIDDEN,
    assert_session_start_allowed_under_failed_s01_governance_v1,
    evaluate_failed_s01_campaign_governance_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.models_v1 import (
    ProductiveCampaignR1RecoveryError,
)

ROOT = Path(__file__).resolve().parents[2]
# Closed failed-S01 campaign (forensic); not the sole ACTIVE binding after rematerialization.
D01_MATERIALIZATION_SHA = "2ceecc994b86eaf548ec157d73574118e4a91bab"
D01_CAMPAIGN_ID = "cv_maxage_productive_evidence_campaign_v1_d01e77c281c7a34d"
D01_S01_MANIFEST_REL = (
    "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
    f"campaigns/{D01_CAMPAIGN_ID}/sessions/session_01_manifest.json"
)


def _d01_forensic_binding():
    return build_active_campaign_binding_v1(repository_sha=D01_MATERIALIZATION_SHA)


def _d01_forensic_evidence_root() -> Path:
    for base in [ROOT, *ROOT.parents]:
        if (base / D01_S01_MANIFEST_REL).is_file():
            return base
    pytest.skip("d01 forensic session manifest absent (local durable evidence only)")


def _d01_forensic_auth_path(evidence_root: Path) -> Path:
    return (
        evidence_root
        / "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1"
        / f"campaigns/{D01_CAMPAIGN_ID}/authorization/campaign_authorization.json"
    )


def test_d01_failed_s01_state_detected_from_runtime_evidence() -> None:
    binding = _d01_forensic_binding()
    evidence_root = _d01_forensic_evidence_root()
    auth = _d01_forensic_auth_path(evidence_root)
    gov = evaluate_failed_s01_campaign_governance_v1(
        binding=binding,
        evidence_root=evidence_root,
        authorization_artifact_path=auth,
        authorization_id="cv_maxage_campaign_auth_v1_fdbc845e13f1abfc",
    )
    assert gov.failed_s01_closed is True
    assert gov.s01_consumed is True
    assert gov.retained_estimate_carrier_present is False
    assert gov.s01_retry_same_session_forbidden is S01_RETRY_SAME_SESSION_FORBIDDEN
    assert gov.s02_start_forbidden is S02_START_AFTER_FAILED_S01_FORBIDDEN
    assert gov.remaining_auth_slot_is_not_recovery is REMAINING_AUTH_SLOT_IS_NOT_RECOVERY
    assert gov.fresh_campaign_rematerialization_required is (
        FRESH_CAMPAIGN_REMATERIALIZATION_REQUIRED_FOR_SUCCESS_PATH
    )


def test_failed_s01_blocks_s01_and_s02_preflight_gate() -> None:
    binding = _d01_forensic_binding()
    evidence_root = _d01_forensic_evidence_root()
    auth = _d01_forensic_auth_path(evidence_root)
    gov = evaluate_failed_s01_campaign_governance_v1(
        binding=binding,
        evidence_root=evidence_root,
        authorization_artifact_path=auth,
        authorization_id="cv_maxage_campaign_auth_v1_fdbc845e13f1abfc",
    )
    with pytest.raises(ProductiveCampaignR1RecoveryError, match="failed_s01_retry"):
        assert_session_start_allowed_under_failed_s01_governance_v1(
            session_id=binding.session_01_id,
            governance=gov,
        )
    with pytest.raises(ProductiveCampaignR1RecoveryError, match="failed_s01_s02"):
        assert_session_start_allowed_under_failed_s01_governance_v1(
            session_id=binding.session_02_id,
            governance=gov,
        )


def test_clean_campaign_without_manifest_not_failed_closed(tmp_path: Path) -> None:
    binding = load_active_campaign_binding_v1(repo_root=ROOT)
    gov = evaluate_failed_s01_campaign_governance_v1(
        binding=binding,
        evidence_root=tmp_path,
        authorization_artifact_path=None,
        authorization_id=None,
    )
    assert gov.failed_s01_closed is False
