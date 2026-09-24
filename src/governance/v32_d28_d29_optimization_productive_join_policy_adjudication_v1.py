"""V32 D28/D29 optimization productive join policy adjudication v1 (read-only).

Forensic join matrix and owner-policy boundary for optimization→productive paths.
Does not authorize join, promotion, apply, numeric mutation, or external effect.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    SURFACE_ID as F2_SURFACE_ID,
)
from src.experiments.canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1 import (
    SURFACE_ID as F5_FRESH_SURFACE_ID,
)
from src.governance.explicit_productive_authorization_v1 import (
    AUTHORIZED_FOR_PRODUCTIVE_APPLY,
    OPTIMIZATION_APPLY_AUTHORITY,
    OPTIMIZATION_PROMOTION_AUTHORITY,
)
from src.governance.governed_productive_runtime_parameter_seam_join_v1 import (
    optimization_can_direct_write_runtime_seam_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    PRODUCTIVE_TARGET_ID,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    OPTIMIZATION_CAN_WRITE_PRODUCTIVE_CONFIG,
    PROMOTION_AUTHORITY,
)
from src.governance.v32_post_d27_test_entry_lifecycle_global_closure_adjudication_v1 import (
    prove_v32_post_d27_test_entry_lifecycle_global_closure_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)

SCHEMA_VERSION: Final[str] = "v32_d28_d29_optimization_productive_join_policy_adjudication_v1"
WORKPACKAGE_ID: Final[str] = (
    "V32_D28_D29_OPTIMIZATION_PRODUCTIVE_JOIN_POLICY_ADJUDICATION_AND_MAX_PRE_BLOCKER_BUILD_V1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/V32_D28_D29_OPTIMIZATION_PRODUCTIVE_JOIN_POLICY_ADJUDICATION_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "v32_d28_d29_optimization_productive_join_policy_adjudication_v1_decision_v1.json"
)
LEARNING_CLOSED_LOOP_DECISION: Final[str] = (
    "config/governance/learning_outcome_evidence_ingest_and_state_decision_v1.json"
)
META_BOUNDARY_DECISION: Final[str] = (
    "config/governance/meta_learning_optimization_universe_boundary_decision_v1.json"
)
META_FOUNDATION_DECISION: Final[str] = (
    "config/governance/meta_learning_optimization_universe_foundation_decision_v1.json"
)

NEXT_TRUE_BLOCKER: Final[str] = (
    "GLOBAL_OPTIMIZATION_UNIVERSE_JOIN_BOOLEAN_REQUIRES_SCOPED_OWNER_POLICY"
)
MINIMAL_OWNER_POLICY_QUESTION: Final[str] = (
    "Should productive optimization join be expressed as scoped per-(surface_id,"
    " productive_target_id) owner flags (F1/M9 lineage first) instead of flipping the "
    "global learning decision field optimization_universe_join_authorized?"
)
BLOCKER_EDGE: Final[str] = (
    "learning_outcome_evidence_ingest_and_state_decision_v1.optimization_universe_join_authorized"
)

AUTHORITY_EFFECT: Final[str] = "NONE"
RUNTIME_EFFECT: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
NEW_AUTHORITY_CREATED: Final[bool] = False
TRADING_DECISION_AUTHORITY_CHANGED: Final[bool] = False
SELF_DEPLOY_AUTHORIZED: Final[bool] = False


class JoinClosureEdgeKindV1(str, Enum):
    PROVEN_COMPOSITION = "PROVEN_COMPOSITION"
    MATRIX_BINDING = "MATRIX_BINDING"
    DECISION_BINDING = "DECISION_BINDING"
    OWNER_POLICY_BOUNDARY = "OWNER_POLICY_BOUNDARY"


@dataclass(frozen=True, slots=True)
class JoinClosureGraphEdgeV1:
    source: str
    target: str
    kind: JoinClosureEdgeKindV1
    evidence_ref: str

    def to_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "target": self.target,
            "kind": self.kind.value,
            "evidence_ref": self.evidence_ref,
        }


class JoinEdgeStatusV1(str, Enum):
    PROVEN_CURRENT = "PROVEN_CURRENT"
    AUTHORIZED_BUT_UNBUILT = "AUTHORIZED_BUT_UNBUILT"
    OWNER_POLICY_REQUIRED = "OWNER_POLICY_REQUIRED"
    UNRESOLVED = "UNRESOLVED"
    CONFLICTING = "CONFLICTING"
    FORBIDDEN = "FORBIDDEN"


class D28D29AdjudicationStatusV1(str, Enum):
    OWNER_POLICY_REQUIRED = "OWNER_POLICY_REQUIRED"
    NAVIGATION_ONLY = "NAVIGATION_ONLY"


@dataclass(frozen=True, slots=True)
class OptimizationProductiveJoinMatrixRowV1:
    row_id: str
    surface_or_subfamily: str
    candidate_producer: str
    evidence_lineage: str
    governance_risk_admission: str
    explicit_authorization_owner: str
    productive_config_target: str
    authorized_productive_seam: str
    current_productive_consumer: str
    apply_materialization_owner: str
    rollback_fail_closed: str
    promotion_authority: str
    external_effect_relation: str
    status: JoinEdgeStatusV1
    blocking_evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "apply_materialization_owner": self.apply_materialization_owner,
            "authorized_productive_seam": self.authorized_productive_seam,
            "blocking_evidence": list(self.blocking_evidence),
            "candidate_producer": self.candidate_producer,
            "current_productive_consumer": self.current_productive_consumer,
            "evidence_lineage": self.evidence_lineage,
            "explicit_authorization_owner": self.explicit_authorization_owner,
            "external_effect_relation": self.external_effect_relation,
            "governance_risk_admission": self.governance_risk_admission,
            "productive_config_target": self.productive_config_target,
            "promotion_authority": self.promotion_authority,
            "rollback_fail_closed": self.rollback_fail_closed,
            "row_id": self.row_id,
            "status": self.status.value,
            "surface_or_subfamily": self.surface_or_subfamily,
        }


def _load_json(root: Path, rel: str) -> dict[str, Any]:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def build_optimization_productive_join_matrix_v1(
    *, repo_root: Path | None = None
) -> tuple[OptimizationProductiveJoinMatrixRowV1, ...]:
    """Evidence-bound join matrix; no runtime authorization effect."""
    _ = repo_root or Path(__file__).resolve().parents[2]
    return (
        OptimizationProductiveJoinMatrixRowV1(
            row_id="F1-M9-M10-PARAMETER-LINEAGE",
            surface_or_subfamily="F1 / M9 volatility max-age",
            candidate_producer=(
                "research.canonical_volatility_numeric_max_age_parameter_research_execution_v1"
            ),
            evidence_lineage=(
                "canonical_optimization_experiment_evidence_v1 + D26 native/candidate classification"
            ),
            governance_risk_admission="optimization_proposal_governance_ingress_v1 (PROPOSAL_ONLY)",
            explicit_authorization_owner="explicit_productive_authorization_v1",
            productive_config_target=f"governed_productive_configuration_v1 → {PRODUCTIVE_TARGET_ID}",
            authorized_productive_seam="authorized_productive_parameter_seam_v1",
            current_productive_consumer=(
                "trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 "
                "(transport via governed_productive_runtime_parameter_seam_join_v1)"
            ),
            apply_materialization_owner="governed_productive_configuration_v1 (explicit owner input)",
            rollback_fail_closed="fail-closed deny on digest/seam mismatch; no self-deploy",
            promotion_authority=OPTIMIZATION_PROMOTION_AUTHORITY,
            external_effect_relation="EXTERNAL_EFFECT_AUTHORIZED=false on all M10 slices",
            status=JoinEdgeStatusV1.PROVEN_CURRENT,
            blocking_evidence=(
                "tests/governance/test_governed_productive_runtime_parameter_seam_join_v1.py",
                "config/governance/explicit_productive_authorization_v1_decision_v1.json",
            ),
        ),
        OptimizationProductiveJoinMatrixRowV1(
            row_id="F2-RESEARCH-COUNTERFACTUAL",
            surface_or_subfamily="F2 backtest cost grid",
            candidate_producer="canonical_f2_research_backtest_cost_grid_research_execution_v1",
            evidence_lineage="optimization experiment evidence; D27 F2 test-entry lifecycle",
            governance_risk_admission="optimization_proposal_governance_ingress_v1 (F2 surface registry)",
            explicit_authorization_owner="NONE (no M10 productive target bound)",
            productive_config_target="NONE",
            authorized_productive_seam="NONE",
            current_productive_consumer="NONE (research executor only)",
            apply_materialization_owner="FORBIDDEN",
            rollback_fail_closed="research-only; no productive apply path",
            promotion_authority="NONE",
            external_effect_relation="NONE",
            status=JoinEdgeStatusV1.FORBIDDEN,
            blocking_evidence=(
                f"surface_id={F2_SURFACE_ID}",
                "optimization_surface_families_pre_test_preparation_v1 F2 TEST_READY research",
            ),
        ),
        OptimizationProductiveJoinMatrixRowV1(
            row_id="F5-FRESH-SHADOW-RESEARCH",
            surface_or_subfamily="F5-FRESH",
            candidate_producer="resolve_optimizable_envelope_v1 (shadow research envelope)",
            evidence_lineage="shadow campaign + D27 F5-FRESH lifecycle",
            governance_risk_admission="D27 F5 shadow campaign digest gate (not governance ingress apply)",
            explicit_authorization_owner="NONE",
            productive_config_target="NONE",
            authorized_productive_seam="NONE",
            current_productive_consumer="run_shadow_campaign_v1 (provisional observations only)",
            apply_materialization_owner="FORBIDDEN",
            rollback_fail_closed="PRODUCTIVE_NUMERIC_VALUES_SET=0",
            promotion_authority="NONE",
            external_effect_relation="NONE",
            status=JoinEdgeStatusV1.FORBIDDEN,
            blocking_evidence=(
                f"surface_id={F5_FRESH_SURFACE_ID}",
                "owner_grants D1 shadow-only; no productive threshold mutation",
            ),
        ),
        OptimizationProductiveJoinMatrixRowV1(
            row_id="F5-SURV-PER-TOKEN-SHADOW",
            surface_or_subfamily="F5-SURV",
            candidate_producer="canonical_f5_shadow_per_token_calibration_test_entry_v1",
            evidence_lineage="per-token registry + D27 SURV lifecycle at campaign seam",
            governance_risk_admission="SHADOW_PER_TOKEN_THRESHOLD_SENSITIVITY_V1 (calibration only)",
            explicit_authorization_owner="NONE",
            productive_config_target="NONE",
            authorized_productive_seam="NONE",
            current_productive_consumer="run_shadow_campaign_v1 Stage-2 observation notes",
            apply_materialization_owner="FORBIDDEN (optimizer_envelope_authorized=false)",
            rollback_fail_closed="fail-closed D27 admission before shadow work",
            promotion_authority="NONE",
            external_effect_relation="NONE",
            status=JoinEdgeStatusV1.FORBIDDEN,
            blocking_evidence=("owner_decision D2 SHADOW_CALIBRATION_ONLY",),
        ),
        OptimizationProductiveJoinMatrixRowV1(
            row_id="F5-CAP-PER-TOKEN-SHADOW",
            surface_or_subfamily="F5-CAP",
            candidate_producer="canonical_f5_shadow_per_token_calibration_test_entry_v1",
            evidence_lineage="per-token registry + D27 CAP lifecycle at campaign seam",
            governance_risk_admission="SHADOW_PER_TOKEN_THRESHOLD_SENSITIVITY_V1 (calibration only)",
            explicit_authorization_owner="NONE",
            productive_config_target="NONE",
            authorized_productive_seam="NONE",
            current_productive_consumer="run_shadow_campaign_v1 Stage-2 observation notes",
            apply_materialization_owner="FORBIDDEN (optimizer_envelope_authorized=false)",
            rollback_fail_closed="fail-closed D27 admission before shadow work",
            promotion_authority="NONE",
            external_effect_relation="NONE",
            status=JoinEdgeStatusV1.FORBIDDEN,
            blocking_evidence=("owner_decision D3 SHADOW_CALIBRATION_ONLY",),
        ),
        OptimizationProductiveJoinMatrixRowV1(
            row_id="LEARNING-EVIDENCE-EXPORT-TO-OPTIMIZATION-INPUT",
            surface_or_subfamily="Learning → Optimization universe (offline)",
            candidate_producer="learning_evidence_export_v1 (boundary contract)",
            evidence_lineage="learning_evidence_record_v1 → optimization learning input contract",
            governance_risk_admission="meta_learning_optimization_universe_boundary (read-only export)",
            explicit_authorization_owner="NONE",
            productive_config_target="NONE",
            authorized_productive_seam="NONE",
            current_productive_consumer="canonical_optimization_universe_v1 (offline plane)",
            apply_materialization_owner="NONE",
            rollback_fail_closed="export-only; no productive write",
            promotion_authority="NONE",
            external_effect_relation="EXTERNAL_EFFECT_AUTHORIZED=false",
            status=JoinEdgeStatusV1.PROVEN_CURRENT,
            blocking_evidence=(META_BOUNDARY_DECISION,),
        ),
        OptimizationProductiveJoinMatrixRowV1(
            row_id="GLOBAL-OPTIMIZATION-UNIVERSE-PRODUCTIVE-JOIN",
            surface_or_subfamily="Global join boolean",
            candidate_producer="SELF_LEARNING_PRODUCTIVE_CLOSED_LOOP_V1 decision field",
            evidence_lineage="learning_outcome_evidence_ingest_and_state_decision_v1",
            governance_risk_admission="NONE until owner policy defines scoped join semantics",
            explicit_authorization_owner="NONE (global boolean not scoped)",
            productive_config_target="UNDEFINED for global flip",
            authorized_productive_seam="NONE for auto-join",
            current_productive_consumer="NONE (join_authorized=false)",
            apply_materialization_owner="FORBIDDEN while false",
            rollback_fail_closed="fail-closed: join false blocks naked_mv2 productive join path",
            promotion_authority=PROMOTION_AUTHORITY,
            external_effect_relation="EXTERNAL_EFFECT_AUTHORIZED=false",
            status=JoinEdgeStatusV1.OWNER_POLICY_REQUIRED,
            blocking_evidence=(
                LEARNING_CLOSED_LOOP_DECISION,
                META_FOUNDATION_DECISION,
                "naked_mv2_double_play_baseline_first_lifecycle_resolution_v1 D24 join blocked",
            ),
        ),
        OptimizationProductiveJoinMatrixRowV1(
            row_id="OPTIMIZATION-DIRECT-RUNTIME-SEAM-WRITE",
            surface_or_subfamily="Cross-cutting guard",
            candidate_producer="optimization plane / ingress",
            evidence_lineage="governed_productive_runtime_parameter_seam_join_v1",
            governance_risk_admission="FORBIDDEN at transport join",
            explicit_authorization_owner="NONE",
            productive_config_target="NONE",
            authorized_productive_seam="transport forbids optimization ingress digest on seam record",
            current_productive_consumer="resolve_governed_runtime_seam_for_presence_gate_v1",
            apply_materialization_owner="optimization_can_direct_write_runtime_seam_v1=false",
            rollback_fail_closed="OPTIMIZATION_INGRESS_DIGEST_FORBIDDEN on seam transport",
            promotion_authority=OPTIMIZATION_APPLY_AUTHORITY,
            external_effect_relation="NONE",
            status=JoinEdgeStatusV1.FORBIDDEN,
            blocking_evidence=(
                "src/governance/governed_productive_runtime_parameter_seam_join_v1.py",
                "OPTIMIZATION_CAN_WRITE_PRODUCTIVE_CONFIG=false",
            ),
        ),
    )


def build_d28_d29_join_closure_graph_v1(
    *, repo_root: Path | None = None
) -> tuple[JoinClosureGraphEdgeV1, ...]:
    """Dependency-closed composition through post-D27 closure to join matrix (read-only)."""
    _ = repo_root or Path(__file__).resolve().parents[2]
    post_d27_wp = "V32_POST_D27_TEST_ENTRY_LIFECYCLE_GLOBAL_CLOSURE_ADJUDICATION_V1"
    return (
        JoinClosureGraphEdgeV1(
            source=(
                "src.governance.v32_post_d27_test_entry_lifecycle_global_closure_adjudication_v1."
                "prove_v32_post_d27_test_entry_lifecycle_global_closure_v1"
            ),
            target=WORKPACKAGE_ID,
            kind=JoinClosureEdgeKindV1.PROVEN_COMPOSITION,
            evidence_ref=(
                "config/governance/"
                "v32_post_d27_test_entry_lifecycle_global_closure_adjudication_v1_decision_v1.json"
            ),
        ),
        JoinClosureGraphEdgeV1(
            source=(
                "src.governance.governed_productive_runtime_parameter_seam_join_v1."
                "optimization_can_direct_write_runtime_seam_v1"
            ),
            target=f"{WORKPACKAGE_ID}:F1-M9-M10-PARAMETER-LINEAGE",
            kind=JoinClosureEdgeKindV1.MATRIX_BINDING,
            evidence_ref=(
                "tests/governance/test_governed_productive_runtime_parameter_seam_join_v1.py"
            ),
        ),
        JoinClosureGraphEdgeV1(
            source=LEARNING_CLOSED_LOOP_DECISION,
            target=f"{WORKPACKAGE_ID}:GLOBAL-OPTIMIZATION-UNIVERSE-PRODUCTIVE-JOIN",
            kind=JoinClosureEdgeKindV1.OWNER_POLICY_BOUNDARY,
            evidence_ref=DECISION_CONFIG,
        ),
        JoinClosureGraphEdgeV1(
            source=WORKPACKAGE_ID,
            target=post_d27_wp,
            kind=JoinClosureEdgeKindV1.DECISION_BINDING,
            evidence_ref=NORMATIVE_SPEC,
        ),
    )


def build_d28_d29_join_adjudication_summary_v1(
    *, repo_root: Path | None = None
) -> Mapping[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    rows = build_optimization_productive_join_matrix_v1(repo_root=root)
    learning = _load_json(root, LEARNING_CLOSED_LOOP_DECISION)
    by_status: dict[str, list[str]] = {}
    for row in rows:
        by_status.setdefault(row.status.value, []).append(row.row_id)
    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "workpackage_id": WORKPACKAGE_ID,
            "d28_status": D28D29AdjudicationStatusV1.OWNER_POLICY_REQUIRED.value,
            "d29_status": D28D29AdjudicationStatusV1.OWNER_POLICY_REQUIRED.value,
            "d28_d29_concept_class": D28D29AdjudicationStatusV1.NAVIGATION_ONLY.value,
            "optimization_productive_join_status": JoinEdgeStatusV1.OWNER_POLICY_REQUIRED.value,
            "optimization_universe_join_authorized_current": bool(
                learning.get("optimization_universe_join_authorized")
            ),
            "productive_numeric_values_set": int(PRODUCTIVE_NUMERIC_VALUES_SET),
            "promotion_authorized": False,
            "productive_apply_authorized": AUTHORIZED_FOR_PRODUCTIVE_APPLY,
            "self_deploy_authorized": SELF_DEPLOY_AUTHORIZED,
            "join_matrix_row_count": len(rows),
            "join_matrix_rows": [r.to_dict() for r in rows],
            "status_index": {k: v for k, v in by_status.items()},
            "next_true_blocker": NEXT_TRUE_BLOCKER,
            "blocker_edge": BLOCKER_EDGE,
            "minimal_owner_policy_question": MINIMAL_OWNER_POLICY_QUESTION,
            "global_join_boolean_too_coarse": True,
            "authority_effect": AUTHORITY_EFFECT,
            "new_authority_created": NEW_AUTHORITY_CREATED,
            "trading_decision_authority_changed": TRADING_DECISION_AUTHORITY_CHANGED,
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        }
    )


def prove_v32_d28_d29_optimization_productive_join_policy_adjudication_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    required = (
        root / DECISION_CONFIG,
        root / NORMATIVE_SPEC,
        root / "src/governance/v32_d28_d29_optimization_productive_join_policy_adjudication_v1.py",
        root
        / "tests/governance/test_v32_d28_d29_optimization_productive_join_policy_adjudication_v1.py",
    )
    if not all(p.is_file() for p in required):
        return False
    if not prove_v32_post_d27_test_entry_lifecycle_global_closure_v1(repo_root=root):
        return False
    decision = _load_json(root, DECISION_CONFIG)
    if not decision.get("d28_d29_adjudication_implemented"):
        return False
    if decision.get("optimization_universe_join_authorized_current") is not False:
        return False
    if decision.get("optimization_universe_join_authorized_changed"):
        return False
    if decision.get("promotion_authorized"):
        return False
    if decision.get("productive_apply_authorized"):
        return False
    if int(decision.get("productive_numeric_values_set_current", -1)) != 0:
        return False
    learning = _load_json(root, LEARNING_CLOSED_LOOP_DECISION)
    if learning.get("optimization_universe_join_authorized") is not False:
        return False
    if optimization_can_direct_write_runtime_seam_v1() is not False:
        return False
    if OPTIMIZATION_CAN_WRITE_PRODUCTIVE_CONFIG is not False:
        return False
    rows = build_optimization_productive_join_matrix_v1(repo_root=root)
    if len(rows) < 8:
        return False
    global_row = next(r for r in rows if r.row_id == "GLOBAL-OPTIMIZATION-UNIVERSE-PRODUCTIVE-JOIN")
    if global_row.status != JoinEdgeStatusV1.OWNER_POLICY_REQUIRED:
        return False
    graph = build_d28_d29_join_closure_graph_v1(repo_root=root)
    if len(graph) < 4:
        return False
    return True


__all__ = [
    "AUTHORITY_EFFECT",
    "BLOCKER_EDGE",
    "DECISION_CONFIG",
    "D28D29AdjudicationStatusV1",
    "EXTERNAL_EFFECT_AUTHORIZED",
    "JoinClosureEdgeKindV1",
    "JoinClosureGraphEdgeV1",
    "JoinEdgeStatusV1",
    "MINIMAL_OWNER_POLICY_QUESTION",
    "NEW_AUTHORITY_CREATED",
    "NEXT_TRUE_BLOCKER",
    "NORMATIVE_SPEC",
    "OptimizationProductiveJoinMatrixRowV1",
    "RUNTIME_EFFECT",
    "SCHEMA_VERSION",
    "SELF_DEPLOY_AUTHORIZED",
    "TRADING_DECISION_AUTHORITY_CHANGED",
    "WORKPACKAGE_ID",
    "build_d28_d29_join_adjudication_summary_v1",
    "build_d28_d29_join_closure_graph_v1",
    "build_optimization_productive_join_matrix_v1",
    "prove_v32_d28_d29_optimization_productive_join_policy_adjudication_v1",
]
