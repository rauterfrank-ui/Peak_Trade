"""Read-only census of tracked/canonical F1/M9 candidate/evidence authority chain."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as F1_M9_OPTIMIZATION_SURFACE_ID,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    OPTIMIZATION_SURFACE_ID,
    SOURCE_CANDIDATE_PARAMETER,
    TARGET_POLICY_PARAMETER,
)

SCHEMA_VERSION: Final[str] = "f1_m9_canonical_productive_candidate_evidence_census/v1"
WORKPACKAGE_ID: Final[str] = "F1_M9_CANONICAL_PRODUCTIVE_CANDIDATE_AND_EVIDENCE_CLOSURE_V1"

PREREGISTRATION_ACTIVE: Final[str] = (
    "config/research/canonical_volatility_numeric_max_age_productive_evidence_session_"
    "preregistration_r1_active_v1.json"
)
CAMPAIGN_ACTIVE_BINDING: Final[str] = (
    "config/governance/canonical_volatility_numeric_max_age_productive_campaign_active_binding_v1.json"
)
M9_S1_OWNER_INPUT: Final[str] = (
    "config/governance/m9_s1_operator_authorized_numeric_max_age_parameter_research_and_"
    "selection_v1_owner_input_v1.json"
)
M9_S1_OWNER_BOUNDARY: Final[str] = (
    "config/governance/m9_s1_operator_authorized_numeric_max_age_parameter_research_and_"
    "selection_v1_owner_boundary_v1.json"
)
M9_OPTIMIZABLE_SURFACE_DECISION: Final[str] = (
    "config/governance/m9_volatility_numeric_max_age_optimizable_surface_v1_decision_v1.json"
)
RISK_CONSTRAINTS: Final[str] = (
    "config/governance/optimizable_envelope/volatility_numeric_max_age_risk_constraints_v1.json"
)

TRACKED_CAMPAIGN_AUTH: Final[str] = (
    "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
    "campaigns/cv_maxage_productive_evidence_campaign_v1_f5e3f95105cd847f/"
    "authorization/campaign_authorization.json"
)
TRACKED_PRODUCTIVE_LEDGER: Final[str] = (
    "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
    "productive_research_evidence_ledger.jsonl"
)
TRACKED_RESEARCH_JOIN_LEDGER: Final[str] = (
    "docs/evidence/canonical_volatility_numeric_max_age_research_evidence_ledger_v1/"
    "research_evidence_ledger.jsonl"
)

EVIDENCE_CLASS_COUNTERFACTUAL: Final[str] = (
    "COUNTERFACTUAL_SESSION_REAL_PUBLIC_MD_EVIDENCE_ACCUMULATION"
)

SELECTION_RULE_NONE: Final[str] = "NONE_CURRENTLY_AUTHORIZED"

OWNER_POLICY_BLOCKER: Final[str] = (
    "F1_M9_PRODUCTIVE_CANDIDATE_SELECTION_REQUIRES_OWNER_AUTHORIZED_THRESHOLD_SELECTION_"
    "POLICY_AND_PROSPECTIVE_CAMPAIGN"
)
PROSPECTIVE_POLICY_CONFIG: Final[str] = (
    "config/governance/f1_m9_productive_candidate_selection_policy_v1.json"
)
PROSPECTIVE_PREREG_CONFIG: Final[str] = (
    "config/research/f1_m9_prospective_volatility_numeric_max_age_candidate_selection_"
    "campaign_preregistration_v1.json"
)
PROSPECTIVE_CAMPAIGN_BINDING: Final[str] = (
    "config/governance/f1_m9_prospective_candidate_selection_campaign_binding_v1.json"
)
CAMPAIGN_EXECUTION_BLOCKER: Final[str] = (
    "F1_M9_PROSPECTIVE_SELECTION_CAMPAIGN_REQUIRES_SEPARATE_EXECUTION_AUTHORIZATION"
)


@dataclass(frozen=True, slots=True)
class ChainArtifactCensusV1:
    canonical_path: str
    tracked: bool
    identity: str | None
    digest: str | None
    authority_class: str
    authorizes: tuple[str, ...]
    forbids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_class": self.authority_class,
            "authorizes": list(self.authorizes),
            "canonical_path": self.canonical_path,
            "digest": self.digest,
            "forbids": list(self.forbids),
            "identity": self.identity,
            "tracked": self.tracked,
        }


@dataclass(frozen=True, slots=True)
class F1M9CandidateEvidenceCensusV1:
    chain_proven: bool
    surface_id: str
    parameter_id: str
    source_candidate_parameter: str
    preregistration_id: str | None
    preregistration_digest: str | None
    preregistration_threshold_selection_authorized: bool
    campaign_id: str | None
    existing_campaign_evidence_class: str | None
    existing_campaign_can_select_productive_candidate: bool
    candidate_selection_authority_resolved: bool
    candidate_selection_rule_id: str
    optimization_ingress_snapshot_tracked: bool
    new_prospective_campaign_required: bool
    owner_policy_required: bool
    artifacts: tuple[ChainArtifactCensusV1, ...]
    earliest_blocker: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifacts": [a.to_dict() for a in self.artifacts],
            "campaign_id": self.campaign_id,
            "candidate_selection_authority_resolved": self.candidate_selection_authority_resolved,
            "candidate_selection_rule_id": self.candidate_selection_rule_id,
            "chain_proven": self.chain_proven,
            "earliest_blocker": self.earliest_blocker,
            "existing_campaign_can_select_productive_candidate": (
                self.existing_campaign_can_select_productive_candidate
            ),
            "existing_campaign_evidence_class": self.existing_campaign_evidence_class,
            "new_prospective_campaign_required": self.new_prospective_campaign_required,
            "optimization_ingress_snapshot_tracked": self.optimization_ingress_snapshot_tracked,
            "owner_policy_required": self.owner_policy_required,
            "parameter_id": self.parameter_id,
            "preregistration_digest": self.preregistration_digest,
            "preregistration_id": self.preregistration_id,
            "preregistration_threshold_selection_authorized": (
                self.preregistration_threshold_selection_authorized
            ),
            "source_candidate_parameter": self.source_candidate_parameter,
            "surface_id": self.surface_id,
        }


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"CONFIG_NOT_MAPPING:{path}")
    return payload


def _tracked(root: Path, rel: str) -> tuple[bool, Path]:
    path = root / rel
    return path.is_file(), path


def run_f1_m9_canonical_productive_candidate_evidence_census_v1(
    *,
    repo_root: Path | None = None,
) -> F1M9CandidateEvidenceCensusV1:
    """Read-only tracked/canonical census; never selects a candidate."""
    root = repo_root or Path(__file__).resolve().parents[2]
    if OPTIMIZATION_SURFACE_ID != F1_M9_OPTIMIZATION_SURFACE_ID:
        raise ValueError("F1_M9_SURFACE_ID_MISMATCH")

    artifacts: list[ChainArtifactCensusV1] = []

    prereg_tracked, prereg_path = _tracked(root, PREREGISTRATION_ACTIVE)
    prereg_id: str | None = None
    prereg_digest: str | None = None
    threshold_sel_auth = False
    counterfactual_only = False
    if prereg_tracked:
        prereg = _load_json(prereg_path)
        prereg_id = str(prereg.get("capability_id") or "") or None
        prereg_digest = str(prereg.get("preregistration_digest") or "") or None
        abort_blocks = prereg.get("abort_block_criteria") or []
        threshold_sel_auth = "THRESHOLD_SELECTION" not in abort_blocks
        invariants = prereg.get("non_promotion_invariants") or {}
        counterfactual_only = invariants.get("COUNTERFACTUAL_ONLY") is True
        purpose = str(prereg.get("campaign_purpose") or "")
        artifacts.append(
            ChainArtifactCensusV1(
                canonical_path=PREREGISTRATION_ACTIVE,
                tracked=True,
                identity=prereg_id,
                digest=prereg_digest,
                authority_class="PREREGISTRATION_CONTRACT",
                authorizes=("COUNTERFACTUAL_AGE_GRID_EVIDENCE", "SESSION_ACCUMULATION"),
                forbids=(
                    "THRESHOLD_SELECTION",
                    "ENFORCEMENT_ACTIVATION",
                    "PARAMETER_DECISION",
                    "PROMOTION",
                )
                if "THRESHOLD_SELECTION" in abort_blocks
                else ("ENFORCEMENT_ACTIVATION",),
            )
        )
        if "never select" in purpose.lower():
            _ = purpose
    else:
        artifacts.append(
            ChainArtifactCensusV1(
                canonical_path=PREREGISTRATION_ACTIVE,
                tracked=False,
                identity=None,
                digest=None,
                authority_class="PREREGISTRATION_CONTRACT",
                authorizes=(),
                forbids=("MISSING_PREREGISTRATION",),
            )
        )

    binding_tracked, binding_path = _tracked(root, CAMPAIGN_ACTIVE_BINDING)
    campaign_id: str | None = None
    if binding_tracked:
        binding = _load_json(binding_path)
        campaign_id = str(binding.get("campaign_id") or "") or None
        artifacts.append(
            ChainArtifactCensusV1(
                canonical_path=CAMPAIGN_ACTIVE_BINDING,
                tracked=True,
                identity=campaign_id,
                digest=str(binding.get("artifact_digest") or "") or None,
                authority_class="ACTIVE_CAMPAIGN_BINDING",
                authorizes=("POINTS_TO_TRACKED_CAMPAIGN_ARTIFACTS",),
                forbids=("EXECUTION_WITHOUT_SEPARATE_AUTH", "EVIDENCE_WRITE_WITHOUT_AUTH"),
            )
        )

    auth_tracked, auth_path = _tracked(root, TRACKED_CAMPAIGN_AUTH)
    if auth_tracked:
        auth = _load_json(auth_path)
        artifacts.append(
            ChainArtifactCensusV1(
                canonical_path=TRACKED_CAMPAIGN_AUTH,
                tracked=True,
                identity=str(auth.get("authorization_id") or "") or None,
                digest=str(auth.get("artifact_digest") or "") or None,
                authority_class="CAMPAIGN_EXECUTION_AUTHORIZATION",
                authorizes=("PUBLIC_MD_SESSION_EVIDENCE_ACCUMULATION",),
                forbids=("PRODUCTIVE_THRESHOLD_SELECTION", "PROMOTION"),
            )
        )

    for rel, label, auth_class in (
        (TRACKED_PRODUCTIVE_LEDGER, "productive_ledger", "REAL_SESSION_EVIDENCE_LEDGER"),
        (TRACKED_RESEARCH_JOIN_LEDGER, "research_join", "RESEARCH_JOIN_PROJECTION"),
    ):
        t, _ = _tracked(root, rel)
        artifacts.append(
            ChainArtifactCensusV1(
                canonical_path=rel,
                tracked=t,
                identity=label,
                digest=None,
                authority_class=auth_class,
                authorizes=("EVIDENCE_ACCUMULATION", "COUNTERFACTUAL_REPLAY_INPUT") if t else (),
                forbids=("THRESHOLD_SELECTION", "PRODUCTIVE_CANDIDATE_RESOLUTION"),
            )
        )

    m9_s1_tracked, m9_s1_path = _tracked(root, M9_S1_OWNER_INPUT)
    selection_from_evidence = False
    numeric_threshold_sel = False
    if m9_s1_tracked:
        m9_s1 = _load_json(m9_s1_path)
        record = m9_s1.get("owner_authorization_record") or {}
        numeric_threshold_sel = record.get("numeric_threshold_selection_authorized") is True
        artifacts.append(
            ChainArtifactCensusV1(
                canonical_path=M9_S1_OWNER_INPUT,
                tracked=True,
                identity=str(record.get("owner_authorization_id") or "") or None,
                digest=str(m9_s1.get("owner_authorization_record_digest") or "") or None,
                authority_class="M9_S1_OWNER_RESEARCH_AUTHORIZATION",
                authorizes=("RESEARCH_EXECUTION",)
                if record.get("research_execution_authorized")
                else (),
                forbids=(
                    "NUMERIC_THRESHOLD_SELECTION",
                    "PARAMETER_PROMOTION",
                    "PRODUCTIVE_CONFIGURATION",
                ),
            )
        )

    boundary_tracked, boundary_path = _tracked(root, M9_S1_OWNER_BOUNDARY)
    if boundary_tracked:
        boundary = _load_json(boundary_path)
        selection_from_evidence = (
            boundary.get("deterministic_numeric_point_selection_from_evidence") is True
        )
        artifacts.append(
            ChainArtifactCensusV1(
                canonical_path=M9_S1_OWNER_BOUNDARY,
                tracked=True,
                identity=str(boundary.get("workpackage_id") or "") or None,
                digest=None,
                authority_class="M9_S1_OWNER_BOUNDARY",
                authorizes=(),
                forbids=(
                    "DETERMINISTIC_POINT_SELECTION_FROM_EVIDENCE",
                    "THRESHOLD_SELECTION_WITHOUT_OWNER",
                ),
            )
        )

    surface_tracked, surface_path = _tracked(root, M9_OPTIMIZABLE_SURFACE_DECISION)
    surface_threshold_sel = False
    if surface_tracked:
        surface = _load_json(surface_path)
        surface_threshold_sel = surface.get("threshold_selection_authorized") is True
        artifacts.append(
            ChainArtifactCensusV1(
                canonical_path=M9_OPTIMIZABLE_SURFACE_DECISION,
                tracked=True,
                identity=str(surface.get("authorized_surface_id") or "") or None,
                digest=None,
                authority_class="OPTIMIZABLE_SURFACE_DECISION",
                authorizes=("RESEARCH_OPTIMIZATION_ONLY",),
                forbids=("THRESHOLD_SELECTION", "PRODUCTIVE_TRADING_EFFECT"),
            )
        )

    risk_tracked, risk_path = _tracked(root, RISK_CONSTRAINTS)
    if risk_tracked:
        risk = _load_json(risk_path)
        artifacts.append(
            ChainArtifactCensusV1(
                canonical_path=RISK_CONSTRAINTS,
                tracked=True,
                identity=str(risk.get("surface_id") or "") or None,
                digest=None,
                authority_class="RESEARCH_RISK_CONSTRAINTS",
                authorizes=("RESEARCH_EVIDENCE_ONLY",),
                forbids=("THRESHOLD_SELECTION", "PROMOTION", "EXECUTION_ORDERS"),
            )
        )

    optimization_ingress_tracked = any(
        p.is_file()
        for p in root.glob("docs/evidence/**/optimization*ingress*.json")
        if "canonical_volatility" in str(p)
    )

    existing_class = EVIDENCE_CLASS_COUNTERFACTUAL if counterfactual_only else None
    campaign_can_select = (
        not counterfactual_only
        and threshold_sel_auth
        and numeric_threshold_sel
        and (surface_threshold_sel or numeric_threshold_sel)
    )
    selection_authority_resolved = (
        numeric_threshold_sel
        and selection_from_evidence is False
        and numeric_threshold_sel
        and not counterfactual_only
    )
    # Current owner input explicitly forbids numeric threshold selection.
    selection_authority_resolved = False

    policy_tracked, _ = _tracked(root, PROSPECTIVE_POLICY_CONFIG)
    prospective_prereg_tracked, _ = _tracked(root, PROSPECTIVE_PREREG_CONFIG)
    scoped_selection_policy_created = policy_tracked and prospective_prereg_tracked

    new_campaign_required = not campaign_can_select
    owner_policy_required = not scoped_selection_policy_created

    chain_proven = prereg_tracked and binding_tracked and auth_tracked
    earliest = OWNER_POLICY_BLOCKER
    if counterfactual_only and not scoped_selection_policy_created:
        earliest = "F1_M9_ACTIVE_CAMPAIGN_COUNTERFACTUAL_ONLY_CANNOT_SELECT_PRODUCTIVE_CANDIDATE"
    elif scoped_selection_policy_created:
        earliest = CAMPAIGN_EXECUTION_BLOCKER

    selection_rule_id = SELECTION_RULE_NONE
    if scoped_selection_policy_created:
        selection_rule_id = "F1_M9_ROBUST_REGION_UNIQUE_SURVIVOR_POINT_V1"

    return F1M9CandidateEvidenceCensusV1(
        chain_proven=chain_proven,
        surface_id=OPTIMIZATION_SURFACE_ID,
        parameter_id=TARGET_POLICY_PARAMETER,
        source_candidate_parameter=SOURCE_CANDIDATE_PARAMETER,
        preregistration_id=prereg_id,
        preregistration_digest=prereg_digest,
        preregistration_threshold_selection_authorized=threshold_sel_auth,
        campaign_id=campaign_id,
        existing_campaign_evidence_class=existing_class,
        existing_campaign_can_select_productive_candidate=campaign_can_select,
        candidate_selection_authority_resolved=selection_authority_resolved,
        candidate_selection_rule_id=selection_rule_id,
        optimization_ingress_snapshot_tracked=optimization_ingress_tracked,
        new_prospective_campaign_required=new_campaign_required,
        owner_policy_required=owner_policy_required,
        artifacts=tuple(artifacts),
        earliest_blocker=earliest,
    )


__all__ = [
    "EVIDENCE_CLASS_COUNTERFACTUAL",
    "F1M9CandidateEvidenceCensusV1",
    "OWNER_POLICY_BLOCKER",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "run_f1_m9_canonical_productive_candidate_evidence_census_v1",
]
