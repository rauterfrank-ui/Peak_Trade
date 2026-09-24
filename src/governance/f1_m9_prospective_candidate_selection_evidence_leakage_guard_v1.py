"""Negative proof helpers: pre-prereg / historical evidence cannot decide selection."""

from __future__ import annotations

from typing import Any, Final, Mapping

from src.governance.f1_m9_productive_candidate_selection_policy_v1 import (
    HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID,
    HISTORICAL_PREREGISTRATION_DIGEST,
    OUTCOME_NO_SELECTION,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_preregistration_v1 import (
    load_prospective_candidate_selection_campaign_preregistration_v1,
)

LEAKAGE_HISTORICAL_PREREG: Final[str] = "HISTORICAL_PREREGISTRATION_DIGEST"
LEAKAGE_HISTORICAL_CAMPAIGN: Final[str] = "HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID"
LEAKAGE_PRE_PREREG_TIMESTAMP: Final[str] = "EVIDENCE_TIMESTAMP_NOT_DOWNSTREAM_OF_PREREGISTRATION"
LEAKAGE_MISSING_BINDING: Final[str] = "EVIDENCE_PREREGISTRATION_DIGEST_MISMATCH"


def assert_decision_evidence_downstream_of_new_preregistration_v1(
    evidence_bundle: Mapping[str, Any],
    *,
    repo_root=None,
) -> dict[str, Any]:
    """Fail-closed guard; returns leakage assessment without selecting a candidate."""
    from pathlib import Path

    root = repo_root or Path(__file__).resolve().parents[2]
    prereg = load_prospective_candidate_selection_campaign_preregistration_v1(repo_root=root)
    new_digest = str(prereg.get("preregistration_digest") or "")
    new_campaign = str(prereg.get("campaign_id") or "")
    frozen_at = str(prereg.get("frozen_at_utc") or prereg.get("created_at_utc") or "")

    evidence_digest = str(evidence_bundle.get("preregistration_digest") or "")
    evidence_campaign = str(evidence_bundle.get("campaign_id") or "")
    evidence_ts = str(
        evidence_bundle.get("decision_making_evidence_timestamp_utc")
        or evidence_bundle.get("created_at_utc")
        or evidence_bundle.get("run_id")
        or ""
    )

    leakage_reasons: list[str] = []
    if evidence_digest == HISTORICAL_PREREGISTRATION_DIGEST:
        leakage_reasons.append(LEAKAGE_HISTORICAL_PREREG)
    if evidence_campaign == HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID:
        leakage_reasons.append(LEAKAGE_HISTORICAL_CAMPAIGN)
    if evidence_digest and evidence_digest != new_digest:
        leakage_reasons.append(LEAKAGE_MISSING_BINDING)
    if frozen_at and evidence_ts and evidence_ts < frozen_at:
        leakage_reasons.append(LEAKAGE_PRE_PREREG_TIMESTAMP)

    contaminated = bool(leakage_reasons)
    return {
        "historical_evidence_decision_leakage": contaminated,
        "leakage_reasons": leakage_reasons,
        "selection_permitted": not contaminated,
        "forced_outcome": OUTCOME_NO_SELECTION if contaminated else None,
        "bound_new_preregistration_digest": new_digest,
        "bound_new_campaign_id": new_campaign,
    }


def historical_evidence_cannot_select_v1(
    *,
    historical_campaign_id: str,
    historical_preregistration_digest: str,
) -> bool:
    """True when historical identifiers are explicitly blocked from selection."""
    return (
        historical_campaign_id == HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID
        and historical_preregistration_digest == HISTORICAL_PREREGISTRATION_DIGEST
    )


__all__ = [
    "LEAKAGE_HISTORICAL_CAMPAIGN",
    "LEAKAGE_HISTORICAL_PREREG",
    "LEAKAGE_MISSING_BINDING",
    "LEAKAGE_PRE_PREREG_TIMESTAMP",
    "assert_decision_evidence_downstream_of_new_preregistration_v1",
    "historical_evidence_cannot_select_v1",
]
