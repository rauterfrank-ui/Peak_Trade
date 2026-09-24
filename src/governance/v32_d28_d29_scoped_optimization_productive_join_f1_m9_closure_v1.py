"""V32 D28/D29 F1/M9 scoped join closure v1 (read-only composition proof)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.v32_d28_d29_optimization_productive_join_policy_adjudication_v1 import (
    prove_v32_d28_d29_optimization_productive_join_policy_adjudication_v1,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_policy_v1 import (
    DECISION_CONFIG,
    F1_M9_SCOPE_PAIR_ID,
    NORMATIVE_SPEC,
    REGISTRY_CONFIG,
    WORKPACKAGE_ID,
    build_canonical_f1_m9_scope_key_v1,
    load_scoped_join_registry_v1,
    prove_scoped_join_policy_invariants_v1,
    resolve_scoped_optimization_productive_join_v1,
)

SCHEMA_VERSION: Final[str] = "v32_d28_d29_scoped_optimization_productive_join_f1_m9_closure_v1"

NEXT_TRUE_BLOCKER: Final[str] = (
    "M9_SCOPED_JOIN_REQUIRES_PER_INGRESS_EXPLICIT_PRODUCTIVE_AUTHORIZATION_AND_PRODUCTIVE_APPLY_OWNER_GO"
)
MINIMAL_NEXT_OWNER_POLICY_QUESTION: Final[str] = (
    "For the F1/M9 scoped join pair, which owner inputs (if any) may authorize "
    "productive apply/materialization beyond scoped join policy, without global "
    "optimization_universe_join_authorized or automatic promotion?"
)
BLOCKER_EDGE: Final[str] = (
    "explicit_productive_authorization_v1.evaluate_explicit_productive_authorization_v1"
)


class ClosureEdgeKindV1(str, Enum):
    PROVEN_COMPOSITION = "PROVEN_COMPOSITION"
    SCOPED_POLICY_BINDING = "SCOPED_POLICY_BINDING"
    M10_LINEAGE_BINDING = "M10_LINEAGE_BINDING"
    OWNER_POLICY_BOUNDARY = "OWNER_POLICY_BOUNDARY"


@dataclass(frozen=True, slots=True)
class ScopedJoinClosureGraphEdgeV1:
    source: str
    target: str
    kind: ClosureEdgeKindV1
    evidence_ref: str

    def to_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "target": self.target,
            "kind": self.kind.value,
            "evidence_ref": self.evidence_ref,
        }


def _load_json(root: Path, rel: str) -> dict[str, Any]:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def build_scoped_f1_m9_join_closure_graph_v1(
    *, repo_root: Path | None = None
) -> tuple[ScopedJoinClosureGraphEdgeV1, ...]:
    _ = repo_root or Path(__file__).resolve().parents[2]
    m10_test = "tests/governance/test_governed_productive_runtime_parameter_seam_join_v1.py"
    return (
        ScopedJoinClosureGraphEdgeV1(
            source=(
                "src.governance.v32_d28_d29_optimization_productive_join_policy_adjudication_v1."
                "prove_v32_d28_d29_optimization_productive_join_policy_adjudication_v1"
            ),
            target=WORKPACKAGE_ID,
            kind=ClosureEdgeKindV1.PROVEN_COMPOSITION,
            evidence_ref=(
                "config/governance/"
                "v32_d28_d29_optimization_productive_join_policy_adjudication_v1_decision_v1.json"
            ),
        ),
        ScopedJoinClosureGraphEdgeV1(
            source=REGISTRY_CONFIG,
            target=f"{WORKPACKAGE_ID}:{F1_M9_SCOPE_PAIR_ID}",
            kind=ClosureEdgeKindV1.SCOPED_POLICY_BINDING,
            evidence_ref=DECISION_CONFIG,
        ),
        ScopedJoinClosureGraphEdgeV1(
            source=(
                "src.governance.governed_productive_runtime_parameter_seam_join_v1."
                "resolve_governed_runtime_seam_for_presence_gate_v1"
            ),
            target=f"{WORKPACKAGE_ID}:{F1_M9_SCOPE_PAIR_ID}",
            kind=ClosureEdgeKindV1.M10_LINEAGE_BINDING,
            evidence_ref=m10_test,
        ),
        ScopedJoinClosureGraphEdgeV1(
            source=WORKPACKAGE_ID,
            target=BLOCKER_EDGE,
            kind=ClosureEdgeKindV1.OWNER_POLICY_BOUNDARY,
            evidence_ref=NORMATIVE_SPEC,
        ),
    )


def build_scoped_f1_m9_join_closure_summary_v1(
    *, repo_root: Path | None = None
) -> Mapping[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    registry = load_scoped_join_registry_v1(repo_root=root)
    key = build_canonical_f1_m9_scope_key_v1()
    resolution = resolve_scoped_optimization_productive_join_v1(
        key, registry=registry, repo_root=root
    )
    decision = _load_json(root, DECISION_CONFIG)
    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "workpackage_id": WORKPACKAGE_ID,
            "scoped_join_policy_status": decision.get("scoped_join_policy_status"),
            "d28_status": decision.get("d28_status"),
            "d29_status": decision.get("d29_status"),
            "d28_d29_closure_proven": decision.get("d28_d29_closure_proven"),
            "authorized_scope_pairs": decision.get("authorized_scope_pairs"),
            "f1_m9_resolution_status": resolution.status.value,
            "f1_m9_scope_pair_id": resolution.scope_pair_id,
            "registry_digest": registry.get("registry_digest"),
            "next_true_blocker": NEXT_TRUE_BLOCKER,
            "blocker_edge": BLOCKER_EDGE,
            "minimal_next_owner_policy_question": MINIMAL_NEXT_OWNER_POLICY_QUESTION,
        }
    )


def prove_v32_d28_d29_scoped_optimization_productive_join_f1_m9_max_build_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    required = (
        root / DECISION_CONFIG,
        root / REGISTRY_CONFIG,
        root / NORMATIVE_SPEC,
        root / "src/governance/v32_d28_d29_scoped_optimization_productive_join_policy_v1.py",
        root / "src/governance/v32_d28_d29_scoped_optimization_productive_join_f1_m9_closure_v1.py",
        root
        / "tests/governance/test_v32_d28_d29_scoped_optimization_productive_join_f1_m9_max_build_v1.py",
    )
    if not all(p.is_file() for p in required):
        return False
    if not prove_v32_d28_d29_optimization_productive_join_policy_adjudication_v1(repo_root=root):
        return False
    if not prove_scoped_join_policy_invariants_v1(repo_root=root):
        return False
    decision = _load_json(root, DECISION_CONFIG)
    if not decision.get("scoped_join_policy_implemented"):
        return False
    if decision.get("optimization_universe_join_authorized_changed"):
        return False
    if decision.get("optimization_universe_join_authorized_current") is not False:
        return False
    if decision.get("global_optimization_join_authorized") is not False:
        return False
    if decision.get("productive_apply_authorized"):
        return False
    if decision.get("promotion_authorized"):
        return False
    if int(decision.get("productive_numeric_values_set_current", -1)) != 0:
        return False
    if decision.get("d28_d29_closure_proven") is not True:
        return False
    pairs = decision.get("authorized_scope_pairs") or []
    if len(pairs) != 1:
        return False
    graph = build_scoped_f1_m9_join_closure_graph_v1(repo_root=root)
    if len(graph) < 4:
        return False
    return True


__all__ = [
    "BLOCKER_EDGE",
    "ClosureEdgeKindV1",
    "MINIMAL_NEXT_OWNER_POLICY_QUESTION",
    "NEXT_TRUE_BLOCKER",
    "SCHEMA_VERSION",
    "ScopedJoinClosureGraphEdgeV1",
    "build_scoped_f1_m9_join_closure_graph_v1",
    "build_scoped_f1_m9_join_closure_summary_v1",
    "prove_v32_d28_d29_scoped_optimization_productive_join_f1_m9_max_build_v1",
]
