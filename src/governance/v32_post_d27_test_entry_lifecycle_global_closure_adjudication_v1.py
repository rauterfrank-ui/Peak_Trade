"""V32 post-D27 global test-entry lifecycle closure adjudication v1 (read-only composition).

Composes already-proven D27 F1/F2 executor enforcement and D27 F5 shadow campaign enforcement
into a single fail-closed closure graph. Does not wire productive paths, authorize promotion,
or mutate trading/risk authority.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1 import (
    prove_d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1,
)
from src.governance.d27_f5_shadow_test_entry_lifecycle_enforcement_v1 import (
    prove_d27_f5_shadow_test_entry_lifecycle_enforcement_v1,
)
from src.governance.d27_research_test_entry_lifecycle_enforcement_v1 import (
    prove_d27_f1_f2_test_entry_lifecycle_enforcement_v1,
)
from src.governance.naked_mv2_double_play_baseline_first_lifecycle_resolution_v1 import (
    AdjudicationVerdict,
    adjudicate_v32_baseline_first_requirements_v1,
)
from src.governance.platform_unified_native_vs_candidate_baseline_evidence_v1 import (
    prove_d26_platform_unified_baseline_evidence_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)

SCHEMA_VERSION: Final[str] = "v32_post_d27_test_entry_lifecycle_global_closure_adjudication_v1"
WORKPACKAGE_ID: Final[str] = "V32_POST_D27_TEST_ENTRY_LIFECYCLE_GLOBAL_CLOSURE_ADJUDICATION_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/V32_POST_D27_TEST_ENTRY_LIFECYCLE_GLOBAL_CLOSURE_ADJUDICATION_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "v32_post_d27_test_entry_lifecycle_global_closure_adjudication_v1_decision_v1.json"
)
F5_LIFECYCLE_DECISION: Final[str] = (
    "config/governance/v32_d27_f5_shadow_test_entry_lifecycle_enforcement_v1_decision_v1.json"
)
F1_F2_LIFECYCLE_DECISION: Final[str] = (
    "config/governance/"
    "v32_d27_test_entry_lifecycle_enforcement_forensic_bounded_completion_v1_decision_v1.json"
)

NEXT_TRUE_BLOCKER: Final[str] = (
    "D28_D29_PROMOTION_AND_OPTIMIZATION_PRODUCTIVE_JOIN_REQUIRE_OWNER_POLICY"
)

AUTHORITY_EFFECT: Final[str] = "NONE"
RUNTIME_EFFECT: Final[str] = "NONE"
PROMOTION_AUTHORITY: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
NEW_AUTHORITY_CREATED: Final[bool] = False
TRADING_DECISION_AUTHORITY_CHANGED: Final[bool] = False


class ClosureEdgeKindV1(str, Enum):
    PROVEN_COMPOSITION = "PROVEN_COMPOSITION"
    DECISION_BINDING = "DECISION_BINDING"
    ADJUDICATION_BINDING = "ADJUDICATION_BINDING"


@dataclass(frozen=True, slots=True)
class ClosureGraphEdgeV1:
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


def build_post_d27_closure_graph_v1(
    *, repo_root: Path | None = None
) -> tuple[ClosureGraphEdgeV1, ...]:
    """Dependency-closed edges for global D27 test-entry lifecycle closure."""
    root = repo_root or Path(__file__).resolve().parents[2]
    return (
        ClosureGraphEdgeV1(
            source=(
                "src.governance.platform_unified_native_vs_candidate_baseline_evidence_v1."
                "prove_d26_platform_unified_baseline_evidence_v1"
            ),
            target=WORKPACKAGE_ID,
            kind=ClosureEdgeKindV1.PROVEN_COMPOSITION,
            evidence_ref="config/governance/v32_d26_platform_unified_native_vs_candidate_baseline_evidence_closure_v1_decision_v1.json",
        ),
        ClosureGraphEdgeV1(
            source=(
                "src.governance.d27_research_test_entry_lifecycle_enforcement_v1."
                "prove_d27_f1_f2_test_entry_lifecycle_enforcement_v1"
            ),
            target=WORKPACKAGE_ID,
            kind=ClosureEdgeKindV1.PROVEN_COMPOSITION,
            evidence_ref=F1_F2_LIFECYCLE_DECISION,
        ),
        ClosureGraphEdgeV1(
            source=(
                "src.governance.d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1."
                "prove_d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1"
            ),
            target=WORKPACKAGE_ID,
            kind=ClosureEdgeKindV1.PROVEN_COMPOSITION,
            evidence_ref=(
                "config/governance/"
                "v32_d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1_decision_v1.json"
            ),
        ),
        ClosureGraphEdgeV1(
            source=(
                "src.governance.d27_f5_shadow_test_entry_lifecycle_enforcement_v1."
                "prove_d27_f5_shadow_test_entry_lifecycle_enforcement_v1"
            ),
            target=WORKPACKAGE_ID,
            kind=ClosureEdgeKindV1.PROVEN_COMPOSITION,
            evidence_ref=F5_LIFECYCLE_DECISION,
        ),
        ClosureGraphEdgeV1(
            source=F5_LIFECYCLE_DECISION,
            target=(
                "src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1."
                "campaign_runner_v1.run_shadow_campaign_v1"
            ),
            kind=ClosureEdgeKindV1.DECISION_BINDING,
            evidence_ref=NORMATIVE_SPEC,
        ),
        ClosureGraphEdgeV1(
            source=WORKPACKAGE_ID,
            target=(
                "src.governance.naked_mv2_double_play_baseline_first_lifecycle_resolution_v1."
                "adjudicate_v32_baseline_first_requirements_v1"
            ),
            kind=ClosureEdgeKindV1.ADJUDICATION_BINDING,
            evidence_ref=DECISION_CONFIG,
        ),
    )


def build_post_d27_closure_summary_v1(*, repo_root: Path | None = None) -> Mapping[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    edges = build_post_d27_closure_graph_v1(repo_root=root)
    f5_decision = _load_json(root, F5_LIFECYCLE_DECISION)
    rows = adjudicate_v32_baseline_first_requirements_v1(repo_root=root)
    d27_row = next(r for r in rows if r.requirement_id == "D27")
    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "workpackage_id": WORKPACKAGE_ID,
            "normative_spec": NORMATIVE_SPEC,
            "decision_config": DECISION_CONFIG,
            "d27_global_status": f5_decision.get("d27_status"),
            "d27_closure_proven": f5_decision.get("earliest_remaining_d27_gap") is None,
            "f5_enforced_family_gate_ids": f5_decision.get("enforced_family_gate_ids"),
            "productive_numeric_values_set": int(PRODUCTIVE_NUMERIC_VALUES_SET),
            "naked_mv2_d27_verdict": d27_row.verdict.value,
            "naked_mv2_d27_missing_edge": d27_row.earliest_missing_edge,
            "closure_graph_edges": [e.to_dict() for e in edges],
            "next_true_blocker": NEXT_TRUE_BLOCKER,
            "authority_effect": AUTHORITY_EFFECT,
            "runtime_effect": RUNTIME_EFFECT,
            "promotion_authority": PROMOTION_AUTHORITY,
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
            "new_authority_created": NEW_AUTHORITY_CREATED,
            "trading_decision_authority_changed": TRADING_DECISION_AUTHORITY_CHANGED,
        }
    )


def prove_v32_post_d27_test_entry_lifecycle_global_closure_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    required = (
        root / DECISION_CONFIG,
        root / NORMATIVE_SPEC,
        root / F5_LIFECYCLE_DECISION,
        root / F1_F2_LIFECYCLE_DECISION,
        root / "src/governance/v32_post_d27_test_entry_lifecycle_global_closure_adjudication_v1.py",
        root
        / "tests/governance/test_v32_post_d27_test_entry_lifecycle_global_closure_adjudication_v1.py",
    )
    if not all(p.is_file() for p in required):
        return False
    decision = _load_json(root, DECISION_CONFIG)
    if not decision.get("d27_global_closure_implemented"):
        return False
    if decision.get("d27_status") != "PROVEN_CURRENT":
        return False
    if decision.get("d27_closure_proven") is not True:
        return False
    if decision.get("earliest_remaining_d27_gap") is not None:
        return False
    if decision.get("next_true_blocker") != NEXT_TRUE_BLOCKER:
        return False
    if int(decision.get("productive_numeric_values_set_current", -1)) != 0:
        return False
    if not prove_d26_platform_unified_baseline_evidence_v1(repo_root=root):
        return False
    if not prove_d27_f1_f2_test_entry_lifecycle_enforcement_v1(repo_root=root):
        return False
    if not prove_d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1(repo_root=root):
        return False
    if not prove_d27_f5_shadow_test_entry_lifecycle_enforcement_v1(repo_root=root):
        return False
    rows = adjudicate_v32_baseline_first_requirements_v1(repo_root=root)
    d27 = next(r for r in rows if r.requirement_id == "D27")
    if d27.verdict != AdjudicationVerdict.PROVEN_CURRENT or d27.earliest_missing_edge is not None:
        return False
    f5 = _load_json(root, F5_LIFECYCLE_DECISION)
    enforced = set(f5.get("enforced_family_gate_ids") or [])
    if enforced != {"F5-FRESH", "F5-SURV", "F5-CAP"}:
        return False
    if PRODUCTIVE_NUMERIC_VALUES_SET != 0:
        return False
    return True


__all__ = [
    "AUTHORITY_EFFECT",
    "DECISION_CONFIG",
    "ClosureEdgeKindV1",
    "ClosureGraphEdgeV1",
    "EXTERNAL_EFFECT_AUTHORIZED",
    "NEW_AUTHORITY_CREATED",
    "NEXT_TRUE_BLOCKER",
    "NORMATIVE_SPEC",
    "PROMOTION_AUTHORITY",
    "RUNTIME_EFFECT",
    "SCHEMA_VERSION",
    "TRADING_DECISION_AUTHORITY_CHANGED",
    "WORKPACKAGE_ID",
    "build_post_d27_closure_graph_v1",
    "build_post_d27_closure_summary_v1",
    "prove_v32_post_d27_test_entry_lifecycle_global_closure_v1",
]
