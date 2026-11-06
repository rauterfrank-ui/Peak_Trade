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
    OWNER_POLICY_BLOCKER,
    run_f1_m9_canonical_productive_candidate_evidence_census_v1,
)
from src.governance.f1_m9_post_real_campaign_productive_handoff_artifacts_v1 import (
    load_explicit_productive_authorization_artifact_v1,
)
from src.governance.f1_m9_prospective_real_campaign_durable_evidence_verification_v1 import (
    verify_f1_m9_prospective_real_campaign_durable_evidence_v1,
)

PROSPECTIVE_CAMPAIGN_ID: Final[str] = (
    "cv_maxage_f1_m9_prospective_candidate_selection_v1_2bab88a8289fb032"
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
BLOCKER_DURABLE_REAL_CAMPAIGN_EVIDENCE_NOT_VERIFIED: Final[str] = (
    "F1_M9_DURABLE_REAL_CAMPAIGN_EVIDENCE_NOT_VERIFIED"
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


def _explicit_auth_resolved(*, repo_root: Path) -> bool:
    artifact = load_explicit_productive_authorization_artifact_v1(repo_root=repo_root)
    if artifact is None:
        return False
    digest = str(artifact.get("artifact_digest") or "")
    body = {k: v for k, v in artifact.items() if k != "artifact_digest"}
    from src.meta.learning_loop.contract_safety_v1 import (
        compute_content_sha256,
        is_valid_sha256_hex,
    )

    if not is_valid_sha256_hex(digest):
        return False
    return compute_content_sha256(body) == digest


def adjudicate_canonical_f1_m9_productive_candidate_v1(
    *,
    repo_root: Path | None = None,
) -> F1M9CanonicalProductiveCandidateAdjudicationV1:
    """Read-only adjudication over tracked config/evidence only."""
    root = repo_root or Path(__file__).resolve().parents[2]
    surface_id = OPTIMIZATION_SURFACE_ID
    if surface_id != F1_M9_OPTIMIZATION_SURFACE_ID:
        raise ValueError("F1_M9_SURFACE_ID_MISMATCH")

    durable = verify_f1_m9_prospective_real_campaign_durable_evidence_v1(
        repo_root=root,
        campaign_id=PROSPECTIVE_CAMPAIGN_ID,
    )
    explicit_auth = _explicit_auth_resolved(repo_root=root)

    if durable.verified:
        reason_codes: list[str] = []
        if not explicit_auth:
            reason_codes.append(BLOCKER_NO_EXPLICIT_PRODUCTIVE_AUTHORIZATION_ARTIFACT)
        return F1M9CanonicalProductiveCandidateAdjudicationV1(
            resolved=True,
            reason_codes=tuple(reason_codes),
            earliest_blocker=(
                BLOCKER_NO_EXPLICIT_PRODUCTIVE_AUTHORIZATION_ARTIFACT if not explicit_auth else ""
            ),
            surface_id=surface_id,
            parameter_id=TARGET_POLICY_PARAMETER,
            source_candidate_parameter=SOURCE_CANDIDATE_PARAMETER,
            productive_target_id=PRODUCTIVE_TARGET_ID,
            candidate_id=durable.selected_candidate_id,
            candidate_value=(
                float(durable.selected_max_age_seconds)
                if durable.selected_max_age_seconds is not None
                else None
            ),
            evidence_id=durable.runtime_authorization_id,
            evidence_digest=durable.evidence_bundle_digest,
            campaign_id=durable.campaign_id,
            explicit_productive_authorization_resolved=explicit_auth,
        )

    census = run_f1_m9_canonical_productive_candidate_evidence_census_v1(repo_root=root)
    reason_codes = list(durable.reason_codes)
    reason_codes.append(BLOCKER_DURABLE_REAL_CAMPAIGN_EVIDENCE_NOT_VERIFIED)

    if not census.preregistration_threshold_selection_authorized:
        reason_codes.append(BLOCKER_THRESHOLD_SELECTION_FORBIDDEN)
    if (
        census.existing_campaign_evidence_class
        == "COUNTERFACTUAL_SESSION_REAL_PUBLIC_MD_EVIDENCE_ACCUMULATION"
    ):
        reason_codes.append(BLOCKER_COUNTERFACTUAL_EVIDENCE_ONLY)
    if not census.optimization_ingress_snapshot_tracked:
        reason_codes.append(BLOCKER_NO_GOVERNED_OPTIMIZATION_INGRESS_SNAPSHOT)
    if not explicit_auth:
        reason_codes.append(BLOCKER_NO_EXPLICIT_PRODUCTIVE_AUTHORIZATION_ARTIFACT)
    if census.owner_policy_required:
        reason_codes.append(OWNER_POLICY_BLOCKER)
    if census.new_prospective_campaign_required:
        reason_codes.append("F1_M9_NEW_PROSPECTIVE_SELECTION_CAMPAIGN_REQUIRED")
    if not census.owner_policy_required:
        reason_codes.extend(
            (
                census.earliest_blocker,
                "F1_M9_NO_DECISION_MAKING_EVIDENCE_UNDER_NEW_PREREGISTRATION",
            )
        )

    earliest = (
        BLOCKER_DURABLE_REAL_CAMPAIGN_EVIDENCE_NOT_VERIFIED
        if durable.reason_codes
        else census.earliest_blocker
    )

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
        explicit_productive_authorization_resolved=explicit_auth,
    )


__all__ = [
    "BLOCKER_DURABLE_REAL_CAMPAIGN_EVIDENCE_NOT_VERIFIED",
    "CANONICAL_EARLY_BLOCKER",
    "F1M9CanonicalProductiveCandidateAdjudicationV1",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "adjudicate_canonical_f1_m9_productive_candidate_v1",
]
