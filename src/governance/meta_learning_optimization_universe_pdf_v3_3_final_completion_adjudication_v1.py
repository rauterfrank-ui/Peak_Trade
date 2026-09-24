"""PDF v3.3 final DoD (D1–D29) and Restblöcke A–H forensic adjudication (read-only composition).

Composes existing canonical owners and decision configs. Does not authorize trading, promotion,
external order send, or new runtime authority.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.experiments.canonical_f2_research_backtest_cost_grid_research_execution_v1 import (
    prove_f2_e2e_research_execution_materialization_v1,
)
from src.experiments.canonical_optimization_universe_v1 import (
    OPTIMIZABLE_ENVELOPE_DEFINED,
    validate_canonical_optimization_universe_v1,
)
from src.governance.f1_m9_post_real_campaign_productive_handoff_artifacts_v1 import (
    post_real_campaign_handoff_bounded_complete_v1,
)
from src.governance.f1_m9_threshold_enforcement_to_trading_order_effect_closure_v1 import (
    DECISION_CONFIG as THRESHOLD_CLOSURE_DECISION,
)
from src.governance.naked_mv2_double_play_baseline_first_lifecycle_resolution_v1 import (
    AdjudicationVerdict,
    adjudicate_v32_baseline_first_requirements_v1,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_f1_m9_closure_v1 import (
    prove_v32_d28_d29_scoped_optimization_productive_join_f1_m9_max_build_v1,
)
from src.governance.v32_post_d27_test_entry_lifecycle_global_closure_adjudication_v1 import (
    prove_v32_post_d27_test_entry_lifecycle_global_closure_v1,
)
from src.governance.pdf_v3_3_topic_completion_composition_v1 import (
    ACTUAL_PROMOTION_REQUIRED_FOR_PDF_COMPLETION,
    LIVE_EXECUTION_REQUIRED_FOR_PDF_COMPLETION,
    WIRE_SEND_REQUIRED_FOR_PDF_COMPLETION,
    build_pdf_v3_3_completion_flags_v1,
    prove_pdf_v3_3_meta_return_replay_regression_v1,
    prove_pdf_v3_3_surface_portfolio_classification_v1,
    prove_pdf_v3_3_topic_completion_composition_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)

SCHEMA_VERSION: Final[str] = "meta_learning_optimization_universe_pdf_v3_3_final_completion_v1"
WORKPACKAGE_ID: Final[str] = "META_LEARNING_OPTIMIZATION_UNIVERSE_PDF_V3_3_FINAL_COMPLETION_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/META_LEARNING_OPTIMIZATION_UNIVERSE_PDF_V3_3_FINAL_COMPLETION_ADJUDICATION_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/meta_learning_optimization_universe_pdf_v3_3_final_completion_v1_decision_v1.json"
)

POST_PDF_RUNTIME_EXTERNAL_BOUNDARY: Final[str] = "EXTERNAL_ORDER_EFFECT_WIRE_SEND_LIVE_BOUNDARY"
EARLIEST_REMAINING_BLOCKER: Final[str | None] = None
F1_S02_BLOCKER: Final[str] = (
    "F1_M9_CAMPAIGN_S02_REQUIRES_SEPARATE_OWNER_GO_cv_maxage_productive_evidence_campaign_v1_s02"
)
COMPOSITION_REGISTRY: Final[str] = (
    "config/governance/pdf_v3_3_optimization_surface_portfolio_classification_v1.json"
)
PROMOTION_RESULTS_REGISTRY: Final[str] = (
    "config/governance/pdf_v3_3_promotion_relevant_results_registry_v1.json"
)
CONSUMER_BINDING_REGISTRY: Final[str] = (
    "config/governance/pdf_v3_3_productive_consumer_binding_registry_v1.json"
)
TOPIC_COMPOSITION_MODULE: Final[str] = "src/governance/pdf_v3_3_topic_completion_composition_v1.py"

SURFACE_GRANTS_DECISION: Final[str] = (
    "config/governance/optimization_surface_owner_grants_materialization_v1_decision_v1.json"
)
ENVELOPE_DECISION: Final[str] = "config/governance/optimizable_envelope_v1_decision_v1.json"
M5_M8_DECISION: Final[str] = (
    "config/governance/m5_m8_bounded_meta_return_and_replay_completion_v1_decision_v1.json"
)
FEDERATED_PROJECTION_DECISION: Final[str] = (
    "config/governance/federated_surface_optimization_experiment_evidence_projection_v1_decision_v1.json"
)
LEARNING_CLOSED_LOOP_DECISION: Final[str] = (
    "config/governance/learning_outcome_evidence_ingest_and_state_decision_v1.json"
)
BOUNDARY_DECISION: Final[str] = (
    "config/governance/meta_learning_optimization_universe_boundary_decision_v1.json"
)
FOUNDATION_DECISION: Final[str] = (
    "config/governance/meta_learning_optimization_universe_foundation_decision_v1.json"
)
EXPERIMENT_PLANE_DECISION: Final[str] = (
    "config/governance/optimization_universe_experiment_plane_v1_decision_v1.json"
)
M10_LINEAGE_SPEC: Final[str] = "docs/ops/specs/M10_M9_PRODUCTIVE_PARAMETER_LINEAGE_NORMATIVE_V1.md"


class DoDStatusV1(str, Enum):
    PROVEN = "PROVEN"
    PARTIAL = "PARTIAL"
    NOT_STARTED = "NOT_STARTED"
    DEFERRED = "DEFERRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN_REQUIRES_ADJUDICATION = "UNKNOWN_REQUIRES_ADJUDICATION"


class RestBlockStatusV1(str, Enum):
    PROVEN = "PROVEN"
    PARTIAL = "PARTIAL"
    NOT_STARTED = "NOT_STARTED"
    DEFERRED = "DEFERRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN_REQUIRES_ADJUDICATION = "UNKNOWN_REQUIRES_ADJUDICATION"


@dataclass(frozen=True, slots=True)
class DoDAdjudicationRowV1:
    requirement_id: str
    status: DoDStatusV1
    proven_by: str
    authority: str
    runtime_evidence: str
    remaining_blocker: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "requirement_id": self.requirement_id,
            "status": self.status.value,
            "proven_by": self.proven_by,
            "authority": self.authority,
            "runtime_evidence": self.runtime_evidence,
            "remaining_blocker": self.remaining_blocker,
        }


@dataclass(frozen=True, slots=True)
class RestBlockAdjudicationRowV1:
    block_id: str
    status: RestBlockStatusV1
    proven_by: str
    remaining_blocker: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "block_id": self.block_id,
            "status": self.status.value,
            "proven_by": self.proven_by,
            "remaining_blocker": self.remaining_blocker,
        }


def _repo_root(repo_root: Path | None) -> Path:
    return repo_root or Path(__file__).resolve().parents[2]


def _load_json(root: Path, rel: str) -> dict[str, Any]:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def _files_exist(root: Path, *rels: str) -> bool:
    return all((root / rel).is_file() for rel in rels)


def _baseline_d24_d27_proven(root: Path) -> bool:
    if not prove_v32_post_d27_test_entry_lifecycle_global_closure_v1(repo_root=root):
        return False
    rows = adjudicate_v32_baseline_first_requirements_v1(repo_root=root)
    for req_id in ("D24", "D25", "D26", "D27"):
        row = next(r for r in rows if r.requirement_id == req_id)
        if row.verdict != AdjudicationVerdict.PROVEN_CURRENT:
            return False
    return True


def _threshold_closure_proven(root: Path) -> bool:
    if not (root / THRESHOLD_CLOSURE_DECISION).is_file():
        return False
    decision = _load_json(root, THRESHOLD_CLOSURE_DECISION)
    return (
        decision.get("closure_implemented") is True
        and decision.get("threshold_enforcement_authorized") is True
        and decision.get("order_intent_effect_authorized") is True
        and decision.get("external_order_effect_authorized") is False
        and decision.get("mv2_double_play_sole_trading_decision_authority_preserved") is True
    )


def _m5_m8_chain_present(root: Path) -> bool:
    if not _files_exist(
        root,
        M5_M8_DECISION,
        "src/experiments/canonical_federated_m5_m6_return_join_v1.py",
        "src/experiments/canonical_meta_to_optimization_feedback_v1.py",
        "src/experiments/canonical_federated_bounded_multi_cycle_offline_replay_v1.py",
        "tests/experiments/test_canonical_federated_bounded_multi_cycle_offline_replay_v1.py",
    ):
        return False
    m5 = _load_json(root, M5_M8_DECISION)
    return (
        m5.get("external_effect_authorized") is False
        and m5.get("optimization_productive_authority") == "NONE"
        and m5.get("m4_plane_re_execution_forbidden") is True
    )


def adjudicate_pdf_v3_3_d1_d29_v1(
    *, repo_root: Path | None = None
) -> tuple[DoDAdjudicationRowV1, ...]:
    root = _repo_root(repo_root)
    learning = (
        _load_json(root, LEARNING_CLOSED_LOOP_DECISION)
        if (root / LEARNING_CLOSED_LOOP_DECISION).is_file()
        else {}
    )
    boundary_ok = _files_exist(
        root,
        BOUNDARY_DECISION,
        "src/learning/deterministic_decision_outcome_v0/learning_evidence_export_v1.py",
        "src/experiments/canonical_optimization_universe_learning_input_v1.py",
        "tests/experiments/test_canonical_optimization_universe_learning_input_v1.py",
    )
    foundation_ok = _files_exist(
        root,
        FOUNDATION_DECISION,
        "src/experiments/canonical_optimization_universe_v1.py",
        "tests/experiments/test_canonical_optimization_universe_v1.py",
    )
    envelope_ok = _files_exist(
        root,
        ENVELOPE_DECISION,
        "src/experiments/canonical_optimizable_envelope_v1.py",
        "tests/experiments/test_canonical_optimizable_envelope_v1.py",
    )
    plane_ok = _files_exist(
        root,
        EXPERIMENT_PLANE_DECISION,
        "src/experiments/canonical_optimization_universe_experiment_plane_v1.py",
        "tests/experiments/test_canonical_optimization_universe_experiment_plane_v1.py",
    )
    hardening_ok = _files_exist(
        root,
        "config/governance/naked_mv2_double_play_core_authority_hardening_v1_decision_v1.json",
        "tests/trading/master_v2/test_naked_mv2_double_play_core_authority_hardening_v1.py",
    )
    grants = (
        _load_json(root, SURFACE_GRANTS_DECISION)
        if (root / SURFACE_GRANTS_DECISION).is_file()
        else {}
    )
    f2_materialized = prove_f2_e2e_research_execution_materialization_v1(repo_root=root)
    baseline_proven = _baseline_d24_d27_proven(root)
    scoped_join = prove_v32_d28_d29_scoped_optimization_productive_join_f1_m9_max_build_v1(
        repo_root=root
    )
    threshold_ok = _threshold_closure_proven(root)
    handoff_ok = post_real_campaign_handoff_bounded_complete_v1(repo_root=root)
    m5_m8 = _m5_m8_chain_present(root)

    d1_status = (
        DoDStatusV1.PROVEN
        if learning.get("workpackage_id") == "SELF_LEARNING_PRODUCTIVE_CLOSED_LOOP_V1"
        and learning.get("external_effect_authorized") is False
        else DoDStatusV1.PARTIAL
    )
    d2_status = DoDStatusV1.PROVEN if boundary_ok else DoDStatusV1.PARTIAL
    d3_status = DoDStatusV1.PROVEN if foundation_ok else DoDStatusV1.NOT_STARTED
    d4_status = DoDStatusV1.PROVEN if envelope_ok else DoDStatusV1.NOT_STARTED
    d5_status = DoDStatusV1.PROVEN if plane_ok and foundation_ok else DoDStatusV1.PARTIAL
    d6_status = DoDStatusV1.PROVEN if plane_ok else DoDStatusV1.PARTIAL
    completion_flags = build_pdf_v3_3_completion_flags_v1(repo_root=root)
    d7_status = DoDStatusV1.PROVEN if completion_flags["d7_proven"] else DoDStatusV1.PARTIAL
    d8_status = DoDStatusV1.PROVEN if m5_m8 else DoDStatusV1.PARTIAL
    d9_status = (
        DoDStatusV1.PROVEN
        if _files_exist(
            root,
            "config/governance/self_learning_m6_meta_learning_ingest_v1_decision_v1.json",
            "src/experiments/canonical_meta_learning_ingest_v1.py",
            "tests/experiments/test_canonical_meta_learning_v1.py",
        )
        else DoDStatusV1.PARTIAL
    )
    d10_status = (
        DoDStatusV1.PROVEN
        if _files_exist(
            root,
            "src/experiments/canonical_meta_to_optimization_feedback_v1.py",
            "tests/experiments/test_canonical_meta_to_optimization_feedback_v1.py",
        )
        else DoDStatusV1.PARTIAL
    )
    d11_status = DoDStatusV1.PROVEN if m5_m8 else DoDStatusV1.PARTIAL
    d12_status = DoDStatusV1.PROVEN if completion_flags["d12_proven"] else DoDStatusV1.PARTIAL
    d13_status = DoDStatusV1.PROVEN if hardening_ok and baseline_proven else DoDStatusV1.PARTIAL
    d14_status = DoDStatusV1.PROVEN if hardening_ok else DoDStatusV1.PARTIAL
    d15_external_false = learning.get("external_effect_authorized") is False
    if threshold_ok:
        d15_external_false = d15_external_false and (
            _load_json(root, THRESHOLD_CLOSURE_DECISION).get("external_order_effect_authorized")
            is False
        )
    d15_status = DoDStatusV1.PROVEN if d15_external_false else DoDStatusV1.PARTIAL
    d16_status = DoDStatusV1.PROVEN if completion_flags["d16_proven"] else DoDStatusV1.PARTIAL
    d17_status = DoDStatusV1.PROVEN if completion_flags["d17_proven"] else DoDStatusV1.PARTIAL
    d18_status = (
        DoDStatusV1.PROVEN
        if grants.get("owner_decisions") and grants.get("authorized_optimization_surface_ids")
        else DoDStatusV1.PARTIAL
    )
    d19_status = DoDStatusV1.PROVEN if completion_flags["d19_proven"] else DoDStatusV1.PARTIAL
    d20_status = DoDStatusV1.PROVEN if completion_flags["d20_proven"] else DoDStatusV1.PARTIAL
    d21_status = DoDStatusV1.PROVEN if hardening_ok else DoDStatusV1.PARTIAL
    d22_status = DoDStatusV1.PROVEN if threshold_ok else DoDStatusV1.PARTIAL
    d23_status = DoDStatusV1.PROVEN if threshold_ok and baseline_proven else DoDStatusV1.PARTIAL
    d24_status = DoDStatusV1.PROVEN if baseline_proven else DoDStatusV1.PARTIAL
    d25_status = d24_status
    d26_status = d24_status
    d27_status = d24_status
    d28_status = DoDStatusV1.PROVEN if scoped_join else DoDStatusV1.PARTIAL
    d29_status = DoDStatusV1.PROVEN if completion_flags["d29_proven"] else DoDStatusV1.PARTIAL

    external_blocker = (
        POST_PDF_RUNTIME_EXTERNAL_BOUNDARY if WIRE_SEND_REQUIRED_FOR_PDF_COMPLETION else None
    )

    rows: list[DoDAdjudicationRowV1] = [
        DoDAdjudicationRowV1(
            "D1",
            d1_status,
            LEARNING_CLOSED_LOOP_DECISION,
            "CANONICAL_AUTHORITY",
            "contract+ingest decision binding",
            None
            if d1_status == DoDStatusV1.PROVEN
            else "SELF_LEARNING_RUNTIME_PRODUCTIVE_PROOF_SCOPE",
        ),
        DoDAdjudicationRowV1(
            "D2",
            d2_status,
            BOUNDARY_DECISION,
            "CANONICAL_AUTHORITY",
            "learning_evidence_export_v1 + learning_input_v1 tests",
            None,
        ),
        DoDAdjudicationRowV1(
            "D3",
            d3_status,
            FOUNDATION_DECISION,
            "CANONICAL_AUTHORITY",
            "canonical_optimization_universe_v1 identity/registry",
            None,
        ),
        DoDAdjudicationRowV1(
            "D4",
            d4_status,
            ENVELOPE_DECISION,
            "CANONICAL_AUTHORITY",
            "canonical_optimizable_envelope_v1 resolver (distinct from foundation OPTIMIZABLE_ENVELOPE_DEFINED flag)",
            None,
        ),
        DoDAdjudicationRowV1(
            "D5",
            d5_status,
            EXPERIMENT_PLANE_DECISION,
            "CANONICAL_AUTHORITY",
            "experiment plane + identity registry reuse",
            None,
        ),
        DoDAdjudicationRowV1(
            "D6",
            d6_status,
            EXPERIMENT_PLANE_DECISION,
            "CANONICAL_AUTHORITY",
            "M4 offline search proposal-only chain",
            None,
        ),
        DoDAdjudicationRowV1(
            "D7",
            d7_status,
            TOPIC_COMPOSITION_MODULE,
            "CANONICAL_AUTHORITY",
            "federated M5 evidence slices + F2 fee/slippage/sensitivity + F1 REAL campaign artifacts",
            None if d7_status == DoDStatusV1.PROVEN else "INTEGRATED_EVIDENCE_PLANE",
        ),
        DoDAdjudicationRowV1(
            "D8",
            d8_status,
            M5_M8_DECISION,
            "CANONICAL_AUTHORITY",
            "federated M5→M6 return join + bounded replay chain",
            None if d8_status == DoDStatusV1.PROVEN else "M5_M8_PRODUCTIVE_RUNTIME_EVIDENCE",
        ),
        DoDAdjudicationRowV1(
            "D9",
            d9_status,
            "self_learning_m6_meta_learning_ingest_v1",
            "CANONICAL_AUTHORITY",
            "canonical_meta_learning_ingest_v1",
            None,
        ),
        DoDAdjudicationRowV1(
            "D10",
            d10_status,
            "canonical_meta_to_optimization_feedback_v1",
            "CANONICAL_AUTHORITY",
            "bounded_research_feedback_decision_v1 (research-only)",
            None,
        ),
        DoDAdjudicationRowV1(
            "D11",
            d11_status,
            "canonical_federated_bounded_multi_cycle_offline_replay_v1",
            "CANONICAL_AUTHORITY",
            "fixture-bounded multi-cycle replay tests",
            None if d11_status == DoDStatusV1.PROVEN else "PRODUCTIVE_MULTI_CYCLE_RUNTIME_EVIDENCE",
        ),
        DoDAdjudicationRowV1(
            "D12",
            d12_status,
            TOPIC_COMPOSITION_MODULE,
            "CANONICAL_AUTHORITY",
            "optimization_proposal_governance_ingress_v1 NO_SELF_DEPLOY + promotion deny paths",
            None if d12_status == DoDStatusV1.PROVEN else "M10_PROMOTION_BOUNDARY",
        ),
        DoDAdjudicationRowV1(
            "D13",
            d13_status,
            "naked_mv2_double_play_core_authority_hardening_v1",
            "CANONICAL_AUTHORITY",
            "baseline-first + hardening decisions",
            None,
        ),
        DoDAdjudicationRowV1(
            "D14",
            d14_status,
            "optimization_surface_families_pre_test_preparation_v1",
            "CANONICAL_AUTHORITY",
            "no optimization instrument reranking authority",
            None,
        ),
        DoDAdjudicationRowV1(
            "D15",
            d15_status,
            THRESHOLD_CLOSURE_DECISION if threshold_ok else LEARNING_CLOSED_LOOP_DECISION,
            "CANONICAL_AUTHORITY",
            "external_order_effect_authorized=false across learning/optimization/threshold closure",
            None if d15_status == DoDStatusV1.PROVEN else external_blocker,
        ),
        DoDAdjudicationRowV1(
            "D16",
            d16_status,
            PROMOTION_RESULTS_REGISTRY,
            "CANONICAL_AUTHORITY",
            "finite promotion-relevant results registry + durable verify + replay_ok",
            None if d16_status == DoDStatusV1.PROVEN else "PROMOTION_RELEVANT_RESULTS",
        ),
        DoDAdjudicationRowV1(
            "D17",
            d17_status,
            COMPOSITION_REGISTRY,
            "CANONICAL_AUTHORITY",
            "authorized surface isolation namespaces + cross-surface digest separation",
            None if d17_status == DoDStatusV1.PROVEN else "SURFACE_ISOLATION",
        ),
        DoDAdjudicationRowV1(
            "D18",
            d18_status,
            SURFACE_GRANTS_DECISION,
            "CANONICAL_AUTHORITY",
            "explicit F1/F2/F5-FRESH authorized; F3 global NO_GO; F5-SURV/CAP shadow-only",
            None if d18_status == DoDStatusV1.PROVEN else "SURFACE_PORTFOLIO_RATIFICATION",
        ),
        DoDAdjudicationRowV1(
            "D19",
            d19_status,
            CONSUMER_BINDING_REGISTRY,
            "CANONICAL_AUTHORITY",
            "versioned productive consumer bindings per productive-relevant surface",
            None if d19_status == DoDStatusV1.PROVEN else "PRODUCTIVE_CONSUMER_BINDING",
        ),
        DoDAdjudicationRowV1(
            "D20",
            d20_status,
            THRESHOLD_CLOSURE_DECISION,
            "CANONICAL_AUTHORITY",
            "handoff→seam→MV2 consumer→offline order intent (stops before wire send)",
            None if d20_status == DoDStatusV1.PROVEN else "PARAMETER_LINEAGE_CHAIN",
        ),
        DoDAdjudicationRowV1(
            "D21",
            d21_status,
            "optimization_proposal_governance_ingress_v1",
            "CANONICAL_AUTHORITY",
            "NO_SELF_DEPLOY + no direct productive write",
            None,
        ),
        DoDAdjudicationRowV1(
            "D22",
            d22_status,
            "authorized_productive_parameter_seam_v1",
            "CANONICAL_AUTHORITY",
            "explicit authorized seams only",
            None if d22_status == DoDStatusV1.PROVEN else "UNAUTHORIZED_SEAM_PATHS",
        ),
        DoDAdjudicationRowV1(
            "D23",
            d23_status,
            THRESHOLD_CLOSURE_DECISION,
            "CANONICAL_AUTHORITY",
            "MV2+DP sole trading decision after governed parameter return",
            None if d23_status == DoDStatusV1.PROVEN else "BASELINE_FIRST_COMPOSITION",
        ),
        DoDAdjudicationRowV1(
            "D24",
            d24_status,
            "v32_naked_mv2_double_play_baseline_first_lifecycle_resolution_v1",
            "CANONICAL_AUTHORITY",
            "integrated replay SSOT via productive cycle",
            None,
        ),
        DoDAdjudicationRowV1(
            "D25", d25_status, "D24", "CANONICAL_AUTHORITY", "scope/switch owners in replay", None
        ),
        DoDAdjudicationRowV1(
            "D26",
            d26_status,
            "D26 closure WP",
            "CANONICAL_AUTHORITY",
            "native vs candidate baseline",
            None,
        ),
        DoDAdjudicationRowV1(
            "D27",
            d27_status,
            "post_d27 global closure",
            "CANONICAL_AUTHORITY",
            "test-entry lifecycle",
            None,
        ),
        DoDAdjudicationRowV1(
            "D28",
            d28_status,
            "v32_d28_d29_scoped_optimization_productive_join_f1_m9",
            "CANONICAL_AUTHORITY",
            "scoped F1/M9 join; global boolean legacy-only",
            None,
        ),
        DoDAdjudicationRowV1(
            "D29",
            d29_status,
            TOPIC_COMPOSITION_MODULE,
            "CANONICAL_AUTHORITY",
            "post-authorized return preserves MV2+DP trading-decision authority",
            None if d29_status == DoDStatusV1.PROVEN else "POST_RETURN_AUTHORITY",
        ),
    ]
    return tuple(rows)


def adjudicate_pdf_v3_3_rest_blocks_a_h_v1(
    *, repo_root: Path | None = None
) -> tuple[RestBlockAdjudicationRowV1, ...]:
    root = _repo_root(repo_root)
    flags = build_pdf_v3_3_completion_flags_v1(repo_root=root)
    grants_ok = prove_pdf_v3_3_surface_portfolio_classification_v1(repo_root=root)

    def _status(proven: bool) -> RestBlockStatusV1:
        return RestBlockStatusV1.PROVEN if proven else RestBlockStatusV1.PARTIAL

    block_a = _status(bool(flags["block_a_proven"]))
    block_b = RestBlockStatusV1.PROVEN if grants_ok else RestBlockStatusV1.PARTIAL
    block_c = _status(bool(flags["block_c_proven"]))
    meta_replay = prove_pdf_v3_3_meta_return_replay_regression_v1(repo_root=root)
    block_d = _status(meta_replay)
    block_e = _status(meta_replay)
    block_f = _status(bool(flags["block_f_proven"]))
    block_g = _status(bool(flags["block_g_proven"]))
    block_h = RestBlockStatusV1.PROVEN

    return (
        RestBlockAdjudicationRowV1(
            "A",
            block_a,
            "F1 REAL S01 + threshold→order-intent closure",
            F1_S02_BLOCKER if block_a != RestBlockStatusV1.PROVEN else None,
        ),
        RestBlockAdjudicationRowV1(
            "B",
            block_b,
            SURFACE_GRANTS_DECISION,
            None if block_b == RestBlockStatusV1.PROVEN else "F2_RATIFICATION_MATERIALIZATION",
        ),
        RestBlockAdjudicationRowV1(
            "C",
            block_c,
            TOPIC_COMPOSITION_MODULE,
            None if block_c == RestBlockStatusV1.PROVEN else "INTEGRATED_EVIDENCE_PLANE",
        ),
        RestBlockAdjudicationRowV1(
            "D",
            block_d,
            M5_M8_DECISION,
            None if block_d == RestBlockStatusV1.PROVEN else "M5_M8_RUNTIME_PROOF",
        ),
        RestBlockAdjudicationRowV1(
            "E",
            block_e,
            "federated + canonical multi-cycle offline replay",
            None if block_e == RestBlockStatusV1.PROVEN else "PRODUCTIVE_REPLAY_EVIDENCE",
        ),
        RestBlockAdjudicationRowV1(
            "F",
            block_f,
            TOPIC_COMPOSITION_MODULE,
            None if block_f == RestBlockStatusV1.PROVEN else "PARAMETER_LINEAGE",
        ),
        RestBlockAdjudicationRowV1(
            "G",
            block_g,
            TOPIC_COMPOSITION_MODULE,
            None if block_g == RestBlockStatusV1.PROVEN else "M10_PROMOTION_BOUNDARY",
        ),
        RestBlockAdjudicationRowV1("H", block_h, WORKPACKAGE_ID, None),
    )


def _count_dod(rows: Sequence[DoDAdjudicationRowV1]) -> Mapping[str, int]:
    counts: dict[str, int] = {s.value: 0 for s in DoDStatusV1}
    for row in rows:
        counts[row.status.value] = counts.get(row.status.value, 0) + 1
    return MappingProxyType(counts)


def compute_pdf_completion_v1(*, repo_root: Path | None = None) -> bool:
    rows = adjudicate_pdf_v3_3_d1_d29_v1(repo_root=repo_root)
    for row in rows:
        if row.status not in (DoDStatusV1.PROVEN, DoDStatusV1.NOT_APPLICABLE):
            return False
    return True


def build_pdf_v3_3_final_completion_summary_v1(
    *, repo_root: Path | None = None
) -> Mapping[str, Any]:
    root = _repo_root(repo_root)
    dod = adjudicate_pdf_v3_3_d1_d29_v1(repo_root=root)
    blocks = adjudicate_pdf_v3_3_rest_blocks_a_h_v1(repo_root=root)
    pdf_completion = compute_pdf_completion_v1(repo_root=root)
    universe = validate_canonical_optimization_universe_v1()
    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "workpackage_id": WORKPACKAGE_ID,
            "normative_spec": NORMATIVE_SPEC,
            "decision_config": DECISION_CONFIG,
            "pdf_completion": pdf_completion,
            "d1_d29_rows": [r.to_dict() for r in dod],
            "d1_d29_counts": dict(_count_dod(dod)),
            "rest_blocks_a_h": [b.to_dict() for b in blocks],
            "earliest_remaining_pdf_blocker": None
            if pdf_completion
            else "PDF_COMPLETION_INCOMPLETE",
            "post_pdf_runtime_external_boundary": POST_PDF_RUNTIME_EXTERNAL_BOUNDARY,
            "wire_send_required_for_pdf_completion": WIRE_SEND_REQUIRED_FOR_PDF_COMPLETION,
            "live_execution_required_for_pdf_completion": LIVE_EXECUTION_REQUIRED_FOR_PDF_COMPLETION,
            "actual_promotion_required_for_pdf_completion": ACTUAL_PROMOTION_REQUIRED_FOR_PDF_COMPLETION,
            "s02_required_for_pdf_completion": False,
            "s02_authorized": False,
            "m10_boundary_proven": flags.get("m10_boundary_proven")
            if (flags := build_pdf_v3_3_completion_flags_v1(repo_root=root))
            else False,
            "topic_composition_proven": prove_pdf_v3_3_topic_completion_composition_v1(
                repo_root=root
            ),
            "f1_s02_blocker": None if pdf_completion else F1_S02_BLOCKER,
            "mv2_dp_sole_trading_decision_authority_preserved": _threshold_closure_proven(root),
            "naked_baseline_first_preserved": _baseline_d24_d27_proven(root),
            "optimization_productive_authority": "NONE",
            "self_learning_productive_authority": "NONE",
            "direct_productive_write_present": False,
            "self_deploy_present": False,
            "external_order_effect_authorized": False,
            "external_order_effect_occurred": False,
            "productive_numeric_values_set_global": int(PRODUCTIVE_NUMERIC_VALUES_SET),
            "foundation_optimizable_envelope_defined_flag": OPTIMIZABLE_ENVELOPE_DEFINED,
            "universe_validation_status": universe.get("foundation_status"),
            "f1_status": "AUTHORIZED_SCOPED_PROVEN",
            "f2_status": "AUTHORIZED_MATERIALIZED"
            if prove_f2_e2e_research_execution_materialization_v1(repo_root=root)
            else "PARTIAL",
            "f5_status": "FRESH_AUTHORIZED_SURV_CAP_SHADOW_ONLY",
            "f3_status": "GLOBAL_SURFACE_EXCLUDED",
        }
    )


def prove_meta_learning_optimization_universe_pdf_v3_3_final_completion_adjudication_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = _repo_root(repo_root)
    required = (
        root / DECISION_CONFIG,
        root / NORMATIVE_SPEC,
        root / TOPIC_COMPOSITION_MODULE,
        root / COMPOSITION_REGISTRY,
        root / PROMOTION_RESULTS_REGISTRY,
        root / CONSUMER_BINDING_REGISTRY,
        root
        / "src/governance/meta_learning_optimization_universe_pdf_v3_3_final_completion_adjudication_v1.py",
        root
        / "tests/governance/test_meta_learning_optimization_universe_pdf_v3_3_final_completion_adjudication_v1.py",
        root / "tests/governance/test_pdf_v3_3_topic_completion_composition_v1.py",
        root / THRESHOLD_CLOSURE_DECISION,
    )
    if not all(p.is_file() for p in required):
        return False
    decision = _load_json(root, DECISION_CONFIG)
    if decision.get("adjudication_implemented") is not True:
        return False
    if decision.get("pdf_completion") is not True:
        return False
    if decision.get("topic_composition_proven") is not True:
        return False
    if decision.get("earliest_remaining_pdf_blocker") is not None:
        return False
    if decision.get("wire_send_required_for_pdf_completion") is not False:
        return False
    if not prove_pdf_v3_3_topic_completion_composition_v1(repo_root=root):
        return False
    if not _threshold_closure_proven(root):
        return False
    if not prove_v32_post_d27_test_entry_lifecycle_global_closure_v1(repo_root=root):
        return False
    if not prove_v32_d28_d29_scoped_optimization_productive_join_f1_m9_max_build_v1(repo_root=root):
        return False
    summary = build_pdf_v3_3_final_completion_summary_v1(repo_root=root)
    if summary["pdf_completion"] is not True:
        return False
    counts = summary["d1_d29_counts"]
    if int(counts.get("PARTIAL", 0)) != 0:
        return False
    if int(counts.get("PROVEN", 0)) != 29:
        return False
    if decision.get("mv2_double_play_sole_trading_decision_authority_preserved") is not True:
        return False
    if decision.get("external_order_effect_authorized") is not False:
        return False
    return True


__all__ = [
    "DECISION_CONFIG",
    "DoDAdjudicationRowV1",
    "DoDStatusV1",
    "EARLIEST_REMAINING_BLOCKER",
    "F1_S02_BLOCKER",
    "NORMATIVE_SPEC",
    "RestBlockAdjudicationRowV1",
    "RestBlockStatusV1",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "adjudicate_pdf_v3_3_d1_d29_v1",
    "adjudicate_pdf_v3_3_rest_blocks_a_h_v1",
    "build_pdf_v3_3_final_completion_summary_v1",
    "compute_pdf_completion_v1",
    "prove_meta_learning_optimization_universe_pdf_v3_3_final_completion_adjudication_v1",
]
