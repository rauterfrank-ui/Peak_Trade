"""Deterministic replay of sealed F1/M9 prospective campaign evidence (read-only)."""

from __future__ import annotations

from typing import Any, Mapping

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.completeness_v1 import (
    adjudicate_campaign_completeness_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    SEALED_EVIDENCE_SCHEMA_VERSION,
)
from src.governance.f1_m9_prospective_candidate_selection_evidence_leakage_guard_v1 import (
    assert_decision_evidence_downstream_of_new_preregistration_v1,
)
from src.governance.f1_m9_productive_candidate_selection_policy_v1 import (
    OUTCOME_NO_SELECTION,
    apply_f1_m9_selection_rule_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex


class CampaignReplayError(ValueError):
    """Fail-closed replay error."""


def verify_sealed_bundle_digest_v1(sealed_bundle: Mapping[str, Any]) -> None:
    stored = str(sealed_bundle.get("evidence_bundle_digest") or "")
    if not is_valid_sha256_hex(stored):
        raise CampaignReplayError("EVIDENCE_BUNDLE_DIGEST_INVALID")
    body = {k: v for k, v in sealed_bundle.items() if k != "evidence_bundle_digest"}
    if compute_content_sha256(body) != stored:
        raise CampaignReplayError("EVIDENCE_BUNDLE_DIGEST_MISMATCH")


def replay_sealed_campaign_evidence_v1(
    sealed_bundle: Mapping[str, Any],
    *,
    repo_root=None,
) -> dict[str, Any]:
    if str(sealed_bundle.get("schema_version") or "") != SEALED_EVIDENCE_SCHEMA_VERSION:
        raise CampaignReplayError("SEALED_BUNDLE_SCHEMA_MISMATCH")
    verify_sealed_bundle_digest_v1(sealed_bundle)

    completeness = adjudicate_campaign_completeness_v1(sealed_bundle, repo_root=repo_root)
    leakage = assert_decision_evidence_downstream_of_new_preregistration_v1(
        sealed_bundle, repo_root=repo_root
    )

    selection_payload: dict[str, Any] = {
        "outcome": OUTCOME_NO_SELECTION,
        "selected_max_age_seconds": None,
        "selected_candidate_id": None,
        "reason_codes": ["COMPLETENESS_OR_LEAKAGE_BLOCK"],
    }
    if completeness.campaign_selection_eligible and leakage.get("selection_permitted"):
        conclusion = str(sealed_bundle.get("research_conclusion") or "")
        rejection_matrix = list(sealed_bundle.get("rejection_matrix") or [])
        robust_region = sealed_bundle.get("robust_candidate_region")
        selection_payload = apply_f1_m9_selection_rule_v1(
            research_conclusion=conclusion,
            robust_candidate_region=robust_region,
            rejection_matrix=rejection_matrix,
        )

    return {
        "replay_ok": True,
        "network_required": False,
        "evidence_mutated": False,
        "completeness": completeness.to_dict(),
        "leakage_assessment": leakage,
        "selection": selection_payload,
        "robust_candidate_region": sealed_bundle.get("robust_candidate_region"),
    }


__all__ = [
    "CampaignReplayError",
    "replay_sealed_campaign_evidence_v1",
    "verify_sealed_bundle_digest_v1",
]
