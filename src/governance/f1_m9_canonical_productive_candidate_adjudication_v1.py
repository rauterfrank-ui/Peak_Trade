"""Adjudicate whether CURRENT tracked/canonical evidence resolves one F1/M9 productive candidate.

Does not select, optimize, or reconstruct candidates from fixtures or research grids.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as F1_M9_OPTIMIZATION_SURFACE_ID,
)
from src.governance.f1_m9_canonical_productive_candidate_evidence_census_v1 import (
    CAMPAIGN_EXECUTION_BLOCKER,
    OWNER_POLICY_BLOCKER,
    run_f1_m9_canonical_productive_candidate_evidence_census_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    OPTIMIZATION_SURFACE_ID,
    PRODUCTIVE_TARGET_ID,
    SOURCE_CANDIDATE_PARAMETER,
    TARGET_POLICY_PARAMETER,
)

SCHEMA_VERSION: Final[str] = "f1_m9_canonical_productive_candidate_adjudication/v1"
WORKPACKAGE_ID: Final[str] = "F1_M9_REAL_PRODUCTIVE_APPLY_GOVERNED_PREPARATION_V1"

ACTIVE_CAMPAIGN_BINDING_CONFIG: Final[str] = (
    "config/governance/canonical_volatility_numeric_max_age_productive_campaign_active_binding_v1.json"
)
PREREGISTRATION_CONFIG: Final[str] = (
    "config/research/canonical_volatility_numeric_max_age_productive_evidence_session_"
    "preregistration_r1_active_v1.json"
)

BLOCKER_COUNTERFACTUAL_EVIDENCE_ONLY: Final[str] = (
    "F1_M9_CANONICAL_EVIDENCE_COUNTERFACTUAL_ACCUMULATION_ONLY_NO_SINGLE_CANDIDATE"
)
BLOCKER_THRESHOLD_SELECTION_FORBIDDEN: Final[str] = (
    "F1_M9_PREREGISTRATION_FORBIDS_THRESHOLD_SELECTION"
)
BLOCKER_NO_GOVERNED_OPTIMIZATION_INGRESS_SNAPSHOT: Final[str] = (
    "F1_M9_NO_TRACKED_GOVERNED_OPTIMIZATION_INGRESS_SNAPSHOT_FOR_PRODUCTIVE_CANDIDATE"
)
BLOCKER_NO_EXPLICIT_PRODUCTIVE_AUTHORIZATION_ARTIFACT: Final[str] = (
    "F1_M9_NO_TRACKED_EXPLICIT_PRODUCTIVE_AUTHORIZATION_ARTIFACT"
)

CANONICAL_EARLY_BLOCKER: Final[str] = BLOCKER_COUNTERFACTUAL_EVIDENCE_ONLY


@dataclass(frozen=True, slots=True)
class F1M9CanonicalProductiveCandidateAdjudicationV1:
    resolved: bool
    reason_codes: tuple[str, ...]
    earliest_blocker: str
    surface_id: str
    parameter_id: str
    source_candidate_parameter: str
    productive_target_id: str
    candidate_id: str | None
    candidate_value: float | None
    evidence_id: str | None
    evidence_digest: str | None
    campaign_id: str | None
    explicit_productive_authorization_resolved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "candidate_id": self.candidate_id,
            "candidate_value": self.candidate_value,
            "earliest_blocker": self.earliest_blocker,
            "evidence_digest": self.evidence_digest,
            "evidence_id": self.evidence_id,
            "explicit_productive_authorization_resolved": (
                self.explicit_productive_authorization_resolved
            ),
            "parameter_id": self.parameter_id,
            "productive_target_id": self.productive_target_id,
            "reason_codes": list(self.reason_codes),
            "resolved": self.resolved,
            "source_candidate_parameter": self.source_candidate_parameter,
            "surface_id": self.surface_id,
        }


def _load_json_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"CONFIG_NOT_MAPPING:{path}")
    return payload


def adjudicate_canonical_f1_m9_productive_candidate_v1(
    *,
    repo_root: Path | None = None,
) -> F1M9CanonicalProductiveCandidateAdjudicationV1:
    """Read-only adjudication over tracked config/evidence only."""
    root = repo_root or Path(__file__).resolve().parents[2]
    surface_id = OPTIMIZATION_SURFACE_ID
    if surface_id != F1_M9_OPTIMIZATION_SURFACE_ID:
        raise ValueError("F1_M9_SURFACE_ID_MISMATCH")

    census = run_f1_m9_canonical_productive_candidate_evidence_census_v1(repo_root=root)
    reason_codes: list[str] = []

    if not census.preregistration_threshold_selection_authorized:
        reason_codes.append(BLOCKER_THRESHOLD_SELECTION_FORBIDDEN)
    if (
        census.existing_campaign_evidence_class
        == "COUNTERFACTUAL_SESSION_REAL_PUBLIC_MD_EVIDENCE_ACCUMULATION"
    ):
        reason_codes.append(BLOCKER_COUNTERFACTUAL_EVIDENCE_ONLY)
    if not census.optimization_ingress_snapshot_tracked:
        reason_codes.append(BLOCKER_NO_GOVERNED_OPTIMIZATION_INGRESS_SNAPSHOT)
    reason_codes.append(BLOCKER_NO_EXPLICIT_PRODUCTIVE_AUTHORIZATION_ARTIFACT)
    if census.owner_policy_required:
        reason_codes.append(OWNER_POLICY_BLOCKER)
    if census.new_prospective_campaign_required:
        reason_codes.append("F1_M9_NEW_PROSPECTIVE_SELECTION_CAMPAIGN_REQUIRED")
    if not census.owner_policy_required:
        reason_codes.append(CAMPAIGN_EXECUTION_BLOCKER)
        reason_codes.append("F1_M9_NO_DECISION_MAKING_EVIDENCE_UNDER_NEW_PREREGISTRATION")

    earliest = census.earliest_blocker

    return F1M9CanonicalProductiveCandidateAdjudicationV1(
        resolved=False,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        earliest_blocker=earliest,
        surface_id=surface_id,
        parameter_id=TARGET_POLICY_PARAMETER,
        source_candidate_parameter=SOURCE_CANDIDATE_PARAMETER,
        productive_target_id=PRODUCTIVE_TARGET_ID,
        candidate_id=None,
        candidate_value=None,
        evidence_id=None,
        evidence_digest=None,
        campaign_id=census.campaign_id,
        explicit_productive_authorization_resolved=False,
    )


__all__ = [
    "CANONICAL_EARLY_BLOCKER",
    "F1M9CanonicalProductiveCandidateAdjudicationV1",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "adjudicate_canonical_f1_m9_productive_candidate_v1",
]
