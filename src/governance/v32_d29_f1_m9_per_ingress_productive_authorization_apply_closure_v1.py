"""V32 D29 F1/M9 per-ingress authorization/apply closure v1 (read-only composition proof)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.v32_d28_d29_scoped_optimization_productive_join_f1_m9_closure_v1 import (
    prove_v32_d28_d29_scoped_optimization_productive_join_f1_m9_max_build_v1,
)
from src.governance.v32_d29_f1_m9_per_ingress_productive_authorization_apply_adjudication_v1 import (
    BLOCKER_EDGE,
    DECISION_CONFIG,
    MINIMAL_NEXT_OWNER_POLICY_QUESTION,
    NEXT_TRUE_BLOCKER,
    NORMATIVE_SPEC,
    WORKPACKAGE_ID,
    build_f1_m9_per_ingress_authority_census_v1,
    prove_v32_d29_f1_m9_per_ingress_productive_authorization_apply_adjudication_v1,
)

SCHEMA_VERSION: Final[str] = "v32_d29_f1_m9_per_ingress_productive_authorization_apply_closure_v1"


class ClosureEdgeKindV1(str, Enum):
    PROVEN_COMPOSITION = "PROVEN_COMPOSITION"
    AUTHORITY_CENSUS_BINDING = "AUTHORITY_CENSUS_BINDING"
    CHAIN_RESOLVER_BINDING = "CHAIN_RESOLVER_BINDING"
    OWNER_POLICY_BOUNDARY = "OWNER_POLICY_BOUNDARY"


@dataclass(frozen=True, slots=True)
class PerIngressClosureGraphEdgeV1:
    source: str
    target: str
    kind: ClosureEdgeKindV1
    evidence_ref: str

    def to_dict(self) -> dict[str, str]:
        return {
            "evidence_ref": self.evidence_ref,
            "kind": self.kind.value,
            "source": self.source,
            "target": self.target,
        }


def build_per_ingress_closure_graph_v1(
    *, repo_root: Path | None = None
) -> tuple[PerIngressClosureGraphEdgeV1, ...]:
    _ = repo_root or Path(__file__).resolve().parents[2]
    return (
        PerIngressClosureGraphEdgeV1(
            source=(
                "src.governance.v32_d28_d29_scoped_optimization_productive_join_f1_m9_closure_v1."
                "prove_v32_d28_d29_scoped_optimization_productive_join_f1_m9_max_build_v1"
            ),
            target=WORKPACKAGE_ID,
            kind=ClosureEdgeKindV1.PROVEN_COMPOSITION,
            evidence_ref=(
                "config/governance/"
                "v32_d28_d29_scoped_optimization_productive_join_f1_m9_owner_policy_v1_decision_v1.json"
            ),
        ),
        PerIngressClosureGraphEdgeV1(
            source=(
                "src.governance.v32_d29_f1_m9_per_ingress_productive_authorization_apply_"
                "adjudication_v1.build_f1_m9_per_ingress_authority_census_v1"
            ),
            target=f"{WORKPACKAGE_ID}:F1-M9-PER-INGRESS-CHAIN",
            kind=ClosureEdgeKindV1.AUTHORITY_CENSUS_BINDING,
            evidence_ref=DECISION_CONFIG,
        ),
        PerIngressClosureGraphEdgeV1(
            source=(
                "src.governance.f1_m9_per_ingress_authorization_chain_resolver_v1."
                "resolve_f1_m9_per_ingress_authorization_chain_v1"
            ),
            target=f"{WORKPACKAGE_ID}:F1-M9-PER-INGRESS-CHAIN",
            kind=ClosureEdgeKindV1.CHAIN_RESOLVER_BINDING,
            evidence_ref=(
                "tests/governance/"
                "test_v32_d29_f1_m9_per_ingress_productive_authorization_apply_max_build_v1.py"
            ),
        ),
        PerIngressClosureGraphEdgeV1(
            source=WORKPACKAGE_ID,
            target=BLOCKER_EDGE,
            kind=ClosureEdgeKindV1.OWNER_POLICY_BOUNDARY,
            evidence_ref=NORMATIVE_SPEC,
        ),
    )


def build_per_ingress_closure_summary_v1(*, repo_root: Path | None = None) -> Mapping[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    census = build_f1_m9_per_ingress_authority_census_v1(repo_root=root)
    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "workpackage_id": WORKPACKAGE_ID,
            "d29_status": decision.get("d29_status"),
            "d29_closure_proven": decision.get("d29_closure_proven"),
            "per_ingress_adjudication_implemented": decision.get(
                "per_ingress_adjudication_implemented"
            ),
            "authority_edge_count": len(census),
            "next_true_blocker": NEXT_TRUE_BLOCKER,
            "blocker_edge": BLOCKER_EDGE,
            "minimal_next_owner_policy_question": MINIMAL_NEXT_OWNER_POLICY_QUESTION,
            "productive_apply_authorized": decision.get("productive_apply_authorized"),
            "productive_numeric_values_set_current": decision.get(
                "productive_numeric_values_set_current"
            ),
        }
    )


def prove_v32_d29_f1_m9_per_ingress_productive_authorization_apply_max_build_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    if not prove_v32_d28_d29_scoped_optimization_productive_join_f1_m9_max_build_v1(repo_root=root):
        return False
    if not prove_v32_d29_f1_m9_per_ingress_productive_authorization_apply_adjudication_v1(
        repo_root=root
    ):
        return False
    graph = build_per_ingress_closure_graph_v1(repo_root=root)
    if len(graph) < 4:
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    if not decision.get("maximal_pre_blocker_scope_proven"):
        return False
    return True


__all__ = [
    "ClosureEdgeKindV1",
    "PerIngressClosureGraphEdgeV1",
    "SCHEMA_VERSION",
    "build_per_ingress_closure_graph_v1",
    "build_per_ingress_closure_summary_v1",
    "prove_v32_d29_f1_m9_per_ingress_productive_authorization_apply_max_build_v1",
]
