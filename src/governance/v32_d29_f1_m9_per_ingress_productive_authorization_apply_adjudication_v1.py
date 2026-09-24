"""V32 D29 F1/M9 per-ingress productive authorization/apply adjudication v1 (read-only).

Forensic authority census and stage decomposition for the F1/M9 ingress chain.
Does not authorize apply, promotion, numeric mutation, or external effect.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.explicit_productive_authorization_v1 import (
    AUTHORIZED_FOR_PRODUCTIVE_APPLY,
    DECISION_CONFIG as EXPLICIT_AUTH_DECISION,
    OWNER_AUTHORIZATION_RECORD_FIELD_KEYS,
    OWNER_BOUNDARY_CONFIG,
)
from src.governance.f1_m9_per_ingress_productive_authorization_binding_v1 import (
    BINDING_DIMENSION_KEYS,
)
from src.governance.governed_productive_configuration_v1 import (
    DECISION_CONFIG as CONFIG_DECISION,
    RUNTIME_APPLY_AUTHORITY,
    runtime_apply_possible_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    OPTIMIZATION_SURFACE_ID,
    POLICY_CONSUMER_MODULE,
    PRODUCTIVE_TARGET_ID,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    DECISION_CONFIG as INGRESS_DECISION,
    PRODUCTIVE_APPLY_AUTHORITY,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_f1_m9_closure_v1 import (
    WORKPACKAGE_ID as SCOPED_JOIN_WP,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_policy_v1 import (
    F1_M9_SCOPE_PAIR_ID,
    REGISTRY_CONFIG,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)

SCHEMA_VERSION: Final[str] = (
    "v32_d29_f1_m9_per_ingress_productive_authorization_apply_adjudication_v1"
)
WORKPACKAGE_ID: Final[str] = (
    "V32_D29_F1_M9_PER_INGRESS_PRODUCTIVE_AUTHORIZATION_APPLY_ADJUDICATION_AND_MAX_BUILD_V1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/"
    "V32_D29_F1_M9_PER_INGRESS_PRODUCTIVE_AUTHORIZATION_APPLY_ADJUDICATION_AND_MAX_BUILD_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "v32_d29_f1_m9_per_ingress_productive_authorization_apply_adjudication_v1_decision_v1.json"
)
EDGE_REGISTRY_CONFIG: Final[str] = (
    "config/governance/v32_d29_f1_m9_per_ingress_authority_edge_registry_v1.json"
)
PREDECESSOR_DECISION: Final[str] = (
    "config/governance/"
    "v32_d28_d29_scoped_optimization_productive_join_f1_m9_owner_policy_v1_decision_v1.json"
)

NEXT_TRUE_BLOCKER: Final[str] = (
    "F1_M9_PER_INGRESS_PRODUCTIVE_APPLY_REQUIRES_EXPLICIT_OWNER_APPLY_INPUT_AND_AUTHORITY_EDGE"
)
BLOCKER_EDGE: Final[str] = "governed_productive_configuration_v1.runtime_apply_authority"
BLOCKER_CLASS: Final[str] = "OWNER_POLICY_REQUIRED"
MINIMAL_NEXT_OWNER_POLICY_QUESTION: Final[str] = (
    "For a bound F1/M9 per-ingress authorization (scoped_join_pair_id + ingress_digest + "
    "owner_authorization_record_digest), which explicit Owner apply input record and authority "
    "edge (if any) may authorize runtime/productive apply without flipping global join, "
    "automatic promotion, or PRODUCTIVE_NUMERIC_VALUES_SET>0?"
)

EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
TRADING_DECISION_AUTHORITY_CHANGED: Final[bool] = False
NEW_AUTHORITY_CLASS: Final[str] = "PER_INGRESS_ADJUDICATION_AND_BINDING_ONLY"


class AuthorityEdgeClassificationV1(str, Enum):
    CANONICAL_AUTHORITY = "CANONICAL_AUTHORITY"
    ADJUDICATED = "ADJUDICATED"
    OWNER_POLICY = "OWNER_POLICY"
    NAVIGATION_ONLY = "NAVIGATION_ONLY"
    INTERPRETATION = "INTERPRETATION"
    OPEN = "OPEN"
    CONFLICTING = "CONFLICTING"
    FORBIDDEN = "FORBIDDEN"


class AuthorityStageStatusV1(str, Enum):
    PROVEN_CURRENT = "PROVEN_CURRENT"
    OWNER_POLICY_REQUIRED = "OWNER_POLICY_REQUIRED"
    FORBIDDEN = "FORBIDDEN"
    OPEN = "OPEN"


@dataclass(frozen=True, slots=True)
class PerIngressAuthorityEdgeV1:
    edge_id: str
    producer_id: str
    consumer_id: str
    classification: AuthorityEdgeClassificationV1
    per_ingress_owner_inputs: tuple[str, ...]
    authorization_identity: str
    candidate_evidence_binding: str
    target_surface_binding: str
    constraints_risk_binding: str
    expiry_freshness_revocation: str
    replay_idempotency: str
    materialization_apply_owner: str
    rollback_fail_closed: str
    external_effect_relation: str
    evidence_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "authorization_identity": self.authorization_identity,
            "candidate_evidence_binding": self.candidate_evidence_binding,
            "classification": self.classification.value,
            "constraints_risk_binding": self.constraints_risk_binding,
            "consumer_id": self.consumer_id,
            "edge_id": self.edge_id,
            "evidence_refs": list(self.evidence_refs),
            "expiry_freshness_revocation": self.expiry_freshness_revocation,
            "external_effect_relation": self.external_effect_relation,
            "materialization_apply_owner": self.materialization_apply_owner,
            "per_ingress_owner_inputs": list(self.per_ingress_owner_inputs),
            "producer_id": self.producer_id,
            "replay_idempotency": self.replay_idempotency,
            "rollback_fail_closed": self.rollback_fail_closed,
            "target_surface_binding": self.target_surface_binding,
        }


@dataclass(frozen=True, slots=True)
class AuthorityStageDecompositionV1:
    stage: str
    status: AuthorityStageStatusV1
    owner_module: str
    implies_next_stage: bool
    evidence_ref: str

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "evidence_ref": self.evidence_ref,
            "implies_next_stage": self.implies_next_stage,
            "owner_module": self.owner_module,
            "stage": self.stage,
            "status": self.status.value,
        }


def _load_json(root: Path, rel: str) -> dict[str, Any]:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def build_f1_m9_per_ingress_authority_census_v1(
    *, repo_root: Path | None = None
) -> tuple[PerIngressAuthorityEdgeV1, ...]:
    """Evidence-bound edge census for the authorized F1/M9 scoped pair only."""
    _ = repo_root or Path(__file__).resolve().parents[2]
    owner_input_fields = tuple(OWNER_AUTHORIZATION_RECORD_FIELD_KEYS)
    return (
        PerIngressAuthorityEdgeV1(
            edge_id="CANDIDATE_TO_INGRESS",
            producer_id=(
                "research.canonical_volatility_numeric_max_age_parameter_research_execution_v1"
            ),
            consumer_id="src.governance.optimization_proposal_governance_ingress_v1",
            classification=AuthorityEdgeClassificationV1.CANONICAL_AUTHORITY,
            per_ingress_owner_inputs=(),
            authorization_identity="ingress_digest (per proposal)",
            candidate_evidence_binding="optimization_evidence_record_id + content/reproducibility digests",
            target_surface_binding=f"surface_id={OPTIMIZATION_SURFACE_ID}",
            constraints_risk_binding="risk_constraints_ref + governance_risk_constraints_ref",
            expiry_freshness_revocation="OPEN (no expiry field in ingress contract)",
            replay_idempotency="ingress_digest content-addressed",
            materialization_apply_owner="NONE (PROPOSAL_ONLY disposition)",
            rollback_fail_closed="DENIED_FAIL_CLOSED on validation mismatch",
            external_effect_relation="EXTERNAL_EFFECT_AUTHORIZED=false",
            evidence_refs=(INGRESS_DECISION,),
        ),
        PerIngressAuthorityEdgeV1(
            edge_id="INGRESS_TO_EXPLICIT_AUTHORIZATION",
            producer_id="optimization_proposal_governance_ingress_v1.evaluate_admission",
            consumer_id="explicit_productive_authorization_v1.evaluate_explicit_productive_authorization_v1",
            classification=AuthorityEdgeClassificationV1.CANONICAL_AUTHORITY,
            per_ingress_owner_inputs=owner_input_fields,
            authorization_identity="authorization_id=uuid5(NAMESPACE_URL, ingress_digest)",
            candidate_evidence_binding="bound_candidate_parameter_value_digest + evidence hashes",
            target_surface_binding=f"productive_target_id={PRODUCTIVE_TARGET_ID}",
            constraints_risk_binding="bound_risk_constraints_ref + ratified_threshold_capability_id",
            expiry_freshness_revocation="OPEN (no revocation contract on main)",
            replay_idempotency="deterministic authorization_id per ingress_digest",
            materialization_apply_owner="NONE (AUTHORIZATION_ONLY)",
            rollback_fail_closed="OWNER_AUTHORIZATION_INPUT_REQUIRED; binding mismatch => DENIED",
            external_effect_relation="authorization_implies_productive_apply=false",
            evidence_refs=(EXPLICIT_AUTH_DECISION, OWNER_BOUNDARY_CONFIG),
        ),
        PerIngressAuthorityEdgeV1(
            edge_id="SCOPED_JOIN_TO_PER_INGRESS_BINDING",
            producer_id=f"{SCOPED_JOIN_WP}:resolve_scoped_optimization_productive_join_v1",
            consumer_id="f1_m9_per_ingress_productive_authorization_binding_v1.evaluate",
            classification=AuthorityEdgeClassificationV1.ADJUDICATED,
            per_ingress_owner_inputs=(),
            authorization_identity=f"scoped_join_pair_id={F1_M9_SCOPE_PAIR_ID}",
            candidate_evidence_binding="registry_digest + lineage refs",
            target_surface_binding="scope_key (surface_id, productive_target_id)",
            constraints_risk_binding="denied_scope_families fail-closed",
            expiry_freshness_revocation="registry_policy_version v1; digest mismatch => DENIED",
            replay_idempotency="registry_digest stable hash",
            materialization_apply_owner="NONE (scoped join != authorization)",
            rollback_fail_closed="SCOPED_JOIN_DENIED_FAIL_CLOSED / UNKNOWN_FAIL_CLOSED",
            external_effect_relation="EXTERNAL_EFFECT_AUTHORIZED=false",
            evidence_refs=(REGISTRY_CONFIG, PREDECESSOR_DECISION),
        ),
        PerIngressAuthorityEdgeV1(
            edge_id="EXPLICIT_AUTH_TO_CONFIGURATION",
            producer_id="explicit_productive_authorization_v1",
            consumer_id="governed_productive_configuration_v1.materialize",
            classification=AuthorityEdgeClassificationV1.CANONICAL_AUTHORITY,
            per_ingress_owner_inputs=(),
            authorization_identity="authorization_digest on authorization_record",
            candidate_evidence_binding="candidate_parameter_value_digest (exact numeric in delta)",
            target_surface_binding="productive_target_contract_digest",
            constraints_risk_binding="VALUE_AUTHORIZATION_SCOPE=OWNER_EXPLICIT_RECORD_BOUND_CANDIDATE_VALUE_DIGEST",
            expiry_freshness_revocation="OPEN",
            replay_idempotency="configuration_digest content-addressed",
            materialization_apply_owner="governed_productive_configuration_v1 (configuration only)",
            rollback_fail_closed="AUTHORIZATION_NOT_AT_PRODUCTIVE_CONFIGURATION_BOUNDARY => DENIED",
            external_effect_relation="configuration_implies_runtime_apply=false",
            evidence_refs=(CONFIG_DECISION,),
        ),
        PerIngressAuthorityEdgeV1(
            edge_id="CONFIGURATION_TO_SEAM",
            producer_id="governed_productive_configuration_v1",
            consumer_id="authorized_productive_parameter_seam_v1.bind",
            classification=AuthorityEdgeClassificationV1.CANONICAL_AUTHORITY,
            per_ingress_owner_inputs=(),
            authorization_identity="configuration_digest",
            candidate_evidence_binding="seam binds configuration_record digest",
            target_surface_binding=POLICY_CONSUMER_MODULE,
            constraints_risk_binding="ENFORCEMENT_AUTHORITY=NONE",
            expiry_freshness_revocation="OPEN",
            replay_idempotency="seam_digest content-addressed",
            materialization_apply_owner="NONE (seam bind only)",
            rollback_fail_closed="configuration digest mismatch => DENIED",
            external_effect_relation="EXTERNAL_EFFECT_AUTHORIZED=false",
            evidence_refs=(
                "config/governance/authorized_productive_parameter_seam_v1_decision_v1.json",
            ),
        ),
        PerIngressAuthorityEdgeV1(
            edge_id="SEAM_TO_RUNTIME_TRANSPORT",
            producer_id="authorized_productive_parameter_seam_v1",
            consumer_id=(
                "governed_productive_runtime_parameter_seam_join_v1."
                "resolve_governed_runtime_seam_for_presence_gate_v1"
            ),
            classification=AuthorityEdgeClassificationV1.ADJUDICATED,
            per_ingress_owner_inputs=(),
            authorization_identity="seam_record digest binding",
            candidate_evidence_binding="forbids optimization ingress digest on seam transport",
            target_surface_binding=POLICY_CONSUMER_MODULE,
            constraints_risk_binding="optimization_can_direct_write_runtime_seam_v1=false",
            expiry_freshness_revocation="OPEN",
            replay_idempotency="transport status per seam_record",
            materialization_apply_owner="NONE (transport only)",
            rollback_fail_closed="OPTIMIZATION_INGRESS_DIGEST_FORBIDDEN; mismatch => DENIED",
            external_effect_relation="EXTERNAL_EFFECT_AUTHORIZED=false",
            evidence_refs=(
                "config/governance/governed_productive_runtime_parameter_seam_join_v1_decision_v1.json",
                "tests/governance/test_governed_productive_runtime_parameter_seam_join_v1.py",
            ),
        ),
        PerIngressAuthorityEdgeV1(
            edge_id="RUNTIME_TRANSPORT_TO_CONSUMER",
            producer_id="governed_productive_runtime_parameter_seam_join_v1",
            consumer_id="trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1",
            classification=AuthorityEdgeClassificationV1.ADJUDICATED,
            per_ingress_owner_inputs=(),
            authorization_identity="authorized_productive_parameter_seam on gate input",
            candidate_evidence_binding="max_age_policy_evidence non-enforcing telemetry",
            target_surface_binding="MV2 Double Play slot evaluation",
            constraints_risk_binding="TRADING_DECISION_AUTHORITY=MV2_DOUBLE_PLAY",
            expiry_freshness_revocation="OPEN",
            replay_idempotency="gate evaluation per market context",
            materialization_apply_owner="NONE (consumer read)",
            rollback_fail_closed="missing seam => unresolved policy fail-closed",
            external_effect_relation="enforcement_applied=false on gate path",
            evidence_refs=(
                "tests/governance/test_governed_productive_runtime_parameter_seam_join_v1.py",
            ),
        ),
        PerIngressAuthorityEdgeV1(
            edge_id="PRODUCTIVE_APPLY_BOUNDARY",
            producer_id="governed_productive_configuration_v1",
            consumer_id="NONE (no dedicated productive_apply owner module)",
            classification=AuthorityEdgeClassificationV1.OWNER_POLICY,
            per_ingress_owner_inputs=("OPEN: owner apply input record not defined",),
            authorization_identity=f"runtime_apply_authority={RUNTIME_APPLY_AUTHORITY}",
            candidate_evidence_binding="configuration_record present; apply edge absent",
            target_surface_binding=PRODUCTIVE_TARGET_ID,
            constraints_risk_binding="PRODUCTIVE_APPLY_AUTHORITY=NONE at ingress",
            expiry_freshness_revocation="OPEN",
            replay_idempotency="OPEN",
            materialization_apply_owner="OWNER_POLICY_REQUIRED",
            rollback_fail_closed="runtime_apply_possible_v1()=false",
            external_effect_relation="FORBIDDEN until explicit apply authority",
            evidence_refs=(CONFIG_DECISION, INGRESS_DECISION),
        ),
        PerIngressAuthorityEdgeV1(
            edge_id="OPTIMIZATION_DIRECT_RUNTIME_WRITE",
            producer_id="optimization plane",
            consumer_id="runtime parameter seam",
            classification=AuthorityEdgeClassificationV1.FORBIDDEN,
            per_ingress_owner_inputs=(),
            authorization_identity="NONE",
            candidate_evidence_binding="FORBIDDEN",
            target_surface_binding="FORBIDDEN",
            constraints_risk_binding="OPTIMIZATION_CAN_WRITE_PRODUCTIVE_CONFIG=false",
            expiry_freshness_revocation="N/A",
            replay_idempotency="N/A",
            materialization_apply_owner="FORBIDDEN",
            rollback_fail_closed="fail-closed guard",
            external_effect_relation="NONE",
            evidence_refs=("src/governance/governed_productive_runtime_parameter_seam_join_v1.py",),
        ),
    )


def build_authority_stage_decomposition_v1(
    *, repo_root: Path | None = None
) -> tuple[AuthorityStageDecompositionV1, ...]:
    _ = repo_root or Path(__file__).resolve().parents[2]
    return (
        AuthorityStageDecompositionV1(
            stage="PROPOSAL_REVIEW_ADMISSION",
            status=AuthorityStageStatusV1.PROVEN_CURRENT,
            owner_module="src.governance.optimization_proposal_governance_ingress_v1",
            implies_next_stage=False,
            evidence_ref=INGRESS_DECISION,
        ),
        AuthorityStageDecompositionV1(
            stage="EXPLICIT_PRODUCTIVE_AUTHORIZATION",
            status=AuthorityStageStatusV1.PROVEN_CURRENT,
            owner_module="src.governance.explicit_productive_authorization_v1",
            implies_next_stage=False,
            evidence_ref=EXPLICIT_AUTH_DECISION,
        ),
        AuthorityStageDecompositionV1(
            stage="PRODUCTIVE_CONFIGURATION_MATERIALIZATION",
            status=AuthorityStageStatusV1.PROVEN_CURRENT,
            owner_module="src.governance.governed_productive_configuration_v1",
            implies_next_stage=False,
            evidence_ref=CONFIG_DECISION,
        ),
        AuthorityStageDecompositionV1(
            stage="PRODUCTIVE_APPLY",
            status=AuthorityStageStatusV1.OWNER_POLICY_REQUIRED,
            owner_module="NONE",
            implies_next_stage=False,
            evidence_ref=CONFIG_DECISION,
        ),
        AuthorityStageDecompositionV1(
            stage="RUNTIME_CONSUMPTION",
            status=AuthorityStageStatusV1.PROVEN_CURRENT,
            owner_module="src.governance.governed_productive_runtime_parameter_seam_join_v1",
            implies_next_stage=False,
            evidence_ref=(
                "tests/governance/test_governed_productive_runtime_parameter_seam_join_v1.py"
            ),
        ),
        AuthorityStageDecompositionV1(
            stage="EXTERNAL_EFFECT",
            status=AuthorityStageStatusV1.FORBIDDEN,
            owner_module="NONE",
            implies_next_stage=False,
            evidence_ref=EXPLICIT_AUTH_DECISION,
        ),
    )


def build_per_ingress_adjudication_summary_v1(
    *, repo_root: Path | None = None
) -> Mapping[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    edges = build_f1_m9_per_ingress_authority_census_v1(repo_root=root)
    stages = build_authority_stage_decomposition_v1(repo_root=root)
    by_class: dict[str, list[str]] = {}
    for edge in edges:
        by_class.setdefault(edge.classification.value, []).append(edge.edge_id)
    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "workpackage_id": WORKPACKAGE_ID,
            "scoped_join_pair_id": F1_M9_SCOPE_PAIR_ID,
            "d28_status": "PROVEN_CURRENT",
            "d29_status": "OWNER_POLICY_REQUIRED",
            "d29_closure_proven": True,
            "d29_closure_scope": "PER_INGRESS_AUTHORIZATION_CHAIN_TO_APPLY_BOUNDARY",
            "productive_numeric_values_set": int(PRODUCTIVE_NUMERIC_VALUES_SET),
            "promotion_authorized": False,
            "productive_apply_authorized": AUTHORIZED_FOR_PRODUCTIVE_APPLY,
            "global_optimization_join_authorized": False,
            "per_ingress_owner_input_fields": list(OWNER_AUTHORIZATION_RECORD_FIELD_KEYS),
            "authorization_binding_dimensions": list(BINDING_DIMENSION_KEYS),
            "authorization_expiry_revocation_semantics": "OPEN",
            "apply_owner": "OWNER_POLICY_REQUIRED",
            "apply_authority_source": BLOCKER_EDGE,
            "authority_edge_count": len(edges),
            "authority_edges": [e.to_dict() for e in edges],
            "classification_index": {k: v for k, v in by_class.items()},
            "stage_decomposition": [s.to_dict() for s in stages],
            "next_true_blocker": NEXT_TRUE_BLOCKER,
            "blocker_edge": BLOCKER_EDGE,
            "blocker_class": BLOCKER_CLASS,
            "minimal_next_owner_policy_question": MINIMAL_NEXT_OWNER_POLICY_QUESTION,
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
            "trading_decision_authority_changed": TRADING_DECISION_AUTHORITY_CHANGED,
            "new_authority_class": NEW_AUTHORITY_CLASS,
        }
    )


def prove_v32_d29_f1_m9_per_ingress_productive_authorization_apply_adjudication_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    required = (
        root / DECISION_CONFIG,
        root / EDGE_REGISTRY_CONFIG,
        root / NORMATIVE_SPEC,
        root
        / "src/governance/v32_d29_f1_m9_per_ingress_productive_authorization_apply_adjudication_v1.py",
        root
        / "src/governance/v32_d29_f1_m9_per_ingress_productive_authorization_apply_closure_v1.py",
        root / "src/governance/f1_m9_per_ingress_productive_authorization_binding_v1.py",
        root / "src/governance/f1_m9_per_ingress_authorization_chain_resolver_v1.py",
        root
        / "tests/governance/test_v32_d29_f1_m9_per_ingress_productive_authorization_apply_max_build_v1.py",
    )
    if not all(p.is_file() for p in required):
        return False
    from src.governance.v32_d28_d29_scoped_optimization_productive_join_f1_m9_closure_v1 import (
        prove_v32_d28_d29_scoped_optimization_productive_join_f1_m9_max_build_v1,
    )

    if not prove_v32_d28_d29_scoped_optimization_productive_join_f1_m9_max_build_v1(repo_root=root):
        return False
    decision = _load_json(root, DECISION_CONFIG)
    if not decision.get("per_ingress_adjudication_implemented"):
        return False
    if decision.get("productive_apply_authorized"):
        return False
    if decision.get("promotion_authorized"):
        return False
    if int(decision.get("productive_numeric_values_set_current", -1)) != 0:
        return False
    if decision.get("next_true_blocker") != NEXT_TRUE_BLOCKER:
        return False
    if AUTHORIZED_FOR_PRODUCTIVE_APPLY is not False:
        return False
    if runtime_apply_possible_v1() is not False:
        return False
    if PRODUCTIVE_APPLY_AUTHORITY != "NONE":
        return False
    edges = build_f1_m9_per_ingress_authority_census_v1(repo_root=root)
    if len(edges) < 9:
        return False
    apply_edge = next(e for e in edges if e.edge_id == "PRODUCTIVE_APPLY_BOUNDARY")
    if apply_edge.classification != AuthorityEdgeClassificationV1.OWNER_POLICY:
        return False
    stages = build_authority_stage_decomposition_v1(repo_root=root)
    apply_stage = next(s for s in stages if s.stage == "PRODUCTIVE_APPLY")
    if apply_stage.status != AuthorityStageStatusV1.OWNER_POLICY_REQUIRED:
        return False
    return True


__all__ = [
    "AuthorityEdgeClassificationV1",
    "AuthorityStageDecompositionV1",
    "AuthorityStageStatusV1",
    "BLOCKER_CLASS",
    "BLOCKER_EDGE",
    "DECISION_CONFIG",
    "EDGE_REGISTRY_CONFIG",
    "MINIMAL_NEXT_OWNER_POLICY_QUESTION",
    "NEW_AUTHORITY_CLASS",
    "NEXT_TRUE_BLOCKER",
    "NORMATIVE_SPEC",
    "PerIngressAuthorityEdgeV1",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "build_authority_stage_decomposition_v1",
    "build_f1_m9_per_ingress_authority_census_v1",
    "build_per_ingress_adjudication_summary_v1",
    "prove_v32_d29_f1_m9_per_ingress_productive_authorization_apply_adjudication_v1",
]
