"""M4–M8 Optimization / Meta-Learning evidence return closure (Concept v3.4 addendum).

Read-only census + runtime proof composition. Does not close P5 Optimization/Meta-Learning
producer bridges into Evidence Adjudicator A; does not mint optimization_envelope_evidence_v1
or meta_learning_routed_evidence_v1.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_deterministic_multi_cycle_offline_replay_v1 import (
    MINIMUM_CYCLE_COUNT,
    REPLAY_STATUS_COMPLETE,
    DeterministicMultiCycleOfflineReplayRequestV1,
    OfflineReplayCycleInputV1,
    run_deterministic_multi_cycle_offline_replay_v1,
)
from src.experiments.canonical_m4_m8_evidence_return_loop_v1 import (
    LOOP_STATUS_COMPLETE,
    M4M8EvidenceReturnLoopRequestV1,
    run_m4_m8_evidence_return_loop_v1,
)
from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    build_optimization_experiment_evidence_from_plane_v1,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    PLANE_STATUS_COMPLETE,
    OptimizationUniverseExperimentPlaneRequestV1,
)
from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    CanonicalOptimizationUniverseLearningInputRequestV1,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.contract_crosswalk_v1 import (
    run_p5_contract_crosswalks_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

SCHEMA_VERSION: Final[str] = "m4_m8_optimization_meta_learning_evidence_return_closure_v1"
WORKPACKAGE_ID: Final[str] = "M4_M8_OPTIMIZATION_META_LEARNING_EVIDENCE_RETURN_CLOSURE"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/M4_M8_OPTIMIZATION_META_LEARNING_EVIDENCE_RETURN_CLOSURE_NORMATIVE_V1.md"
)
V34_ADDENDUM_SPEC: Final[str] = (
    "docs/ops/specs/PEAK_TRADE_META_LEARNING_OPTIMIZATION_UNIVERSE_CONCEPT_V3_4_CURRENT_MV2_DP_ALIGNMENT_ADDENDUM_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/m4_m8_optimization_meta_learning_evidence_return_closure_v1_decision_v1.json"
)

P5_OPTIMIZATION_TARGET_KIND: Final[str] = "optimization_envelope_evidence_v1"
P5_META_TARGET_KIND: Final[str] = "meta_learning_routed_evidence_v1"


class CensusClassification(str, Enum):
    REUSE_AS_IS = "REUSE_AS_IS"
    REUSE_WITH_BINDING = "REUSE_WITH_BINDING"
    NEEDS_IMPLEMENTATION = "NEEDS_IMPLEMENTATION"
    HISTORICAL_ONLY = "HISTORICAL_ONLY"
    LEGACY_UNSUPPORTED = "LEGACY_UNSUPPORTED"
    CONFLICTING = "CONFLICTING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CensusEntryV1:
    component_id: str
    classification: CensusClassification
    owner_path: str | None
    notes: str


_CENSUS_ENTRIES: Final[tuple[CensusEntryV1, ...]] = (
    CensusEntryV1(
        "M4_EXPERIMENT_PLANE",
        CensusClassification.REUSE_AS_IS,
        "src/experiments/canonical_optimization_universe_experiment_plane_v1.py",
        "Search/candidate/challenger/OOS/robustness/failure proposal chain",
    ),
    CensusEntryV1(
        "M4_MI_ENRICHED_INTAKE",
        CensusClassification.REUSE_WITH_BINDING,
        "src/experiments/canonical_optimization_universe_mi_enriched_m4_intake_v1.py",
        "Optional MI lineage refs; fail-closed without fabrication",
    ),
    CensusEntryV1(
        "M5_OPTIMIZATION_EXPERIMENT_EVIDENCE",
        CensusClassification.REUSE_AS_IS,
        "src/experiments/canonical_optimization_experiment_evidence_v1.py",
        "Typed return artifact from completed M4 plane; not P2 optimization_envelope_evidence_v1",
    ),
    CensusEntryV1(
        "M5_SELF_LEARNING_RETURN_INPUT",
        CensusClassification.REUSE_AS_IS,
        "src/experiments/canonical_self_learning_optimization_return_input_v1.py",
        "Return ack without learning_state mutation or meta ingest side effects",
    ),
    CensusEntryV1(
        "M6_META_LEARNING_INGEST",
        CensusClassification.REUSE_AS_IS,
        "src/experiments/canonical_meta_learning_ingest_v1.py",
        "Projects M5 to meta_learning_evidence_v1; federated join path separate",
    ),
    CensusEntryV1(
        "M6_META_LEARNING_EVIDENCE_SCHEMA",
        CensusClassification.REUSE_AS_IS,
        "src/learning/deterministic_decision_outcome_v0/meta_learning_evidence_v1.py",
        "Authority=NONE; no instrument/epoch/time fabrication fields",
    ),
    CensusEntryV1(
        "M7_META_TO_OPTIMIZATION_FEEDBACK",
        CensusClassification.REUSE_AS_IS,
        "src/experiments/canonical_meta_to_optimization_feedback_v1.py",
        "Bounded research experiment/search choice only; trading_selection_effect=NONE",
    ),
    CensusEntryV1(
        "M8_DETERMINISTIC_MULTI_CYCLE_REPLAY",
        CensusClassification.REUSE_AS_IS,
        "src/experiments/canonical_deterministic_multi_cycle_offline_replay_v1.py",
        "Forward+return loop >=2 cycles; authority invariant",
    ),
    CensusEntryV1(
        "M8_FEDERATED_BOUNDED_REPLAY",
        CensusClassification.REUSE_WITH_BINDING,
        "src/experiments/canonical_federated_bounded_multi_cycle_offline_replay_v1.py",
        "Surface_execution_identity join; M4 plane re-execution forbidden",
    ),
    CensusEntryV1(
        "M4_M8_SINGLE_CYCLE_LOOP",
        CensusClassification.REUSE_AS_IS,
        "src/experiments/canonical_m4_m8_evidence_return_loop_v1.py",
        "WP orchestrator composing M4–M7 for closure proofs",
    ),
    CensusEntryV1(
        "P5_OPTIMIZATION_PRODUCER_BRIDGE",
        CensusClassification.CONFLICTING,
        "src/governance/master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1/contract_crosswalk_v1.py",
        "Blocked until separate P5 final closure; target kind != M5 schema",
    ),
    CensusEntryV1(
        "P5_META_LEARNING_PRODUCER_BRIDGE",
        CensusClassification.CONFLICTING,
        "src/governance/master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1/contract_crosswalk_v1.py",
        "meta_evidence_v1 != meta_learning_routed_evidence_v1; sequence lock",
    ),
    CensusEntryV1(
        "PHASE23_META_EVIDENCE_DUAL_ROUTER",
        CensusClassification.HISTORICAL_ONLY,
        "src/learning/deterministic_decision_outcome_v0/meta_evidence_v1.py",
        "RESEARCH_ONLY routing envelope; not P5 P2 routed kind",
    ),
    CensusEntryV1(
        "PDF_V3_3_FINAL_COMPLETION",
        CensusClassification.HISTORICAL_ONLY,
        "src/governance/meta_learning_optimization_universe_pdf_v3_3_final_completion_adjudication_v1.py",
        "Superseded for P5/M4–M8 status by Concept v3.4 addendum pages 23–27",
    ),
)


def git_head_sha(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def build_current_census_v1(*, repo_root: Path | None = None) -> Mapping[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    entries = []
    for item in _CENSUS_ENTRIES:
        path_ok = item.owner_path is not None and (root / item.owner_path).is_file()
        entries.append(
            {
                "component_id": item.component_id,
                "classification": item.classification.value,
                "owner_path": item.owner_path,
                "owner_present": path_ok,
                "notes": item.notes,
            }
        )
    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "workpackage_id": WORKPACKAGE_ID,
            "baseline_sha": git_head_sha(root),
            "entries": tuple(entries),
        }
    )


def _fixture_learning_state(tmp_path: Path) -> Any:
    from tests.learning.test_learning_evidence_export_v1 import _learning_state

    return _learning_state(tmp_path)


def _fixture_plane_request(
    learning_evidence: Mapping[str, Any],
) -> OptimizationUniverseExperimentPlaneRequestV1:
    from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
        _plane_request,
    )

    return _plane_request(learning_evidence)


def prove_m4_m8_runtime_lineage_v1(*, repo_root: Path | None = None) -> bool:
    """Execute canonical M4→M5→M6→M7 single cycle + M8 two-cycle replay (fixture-bounded)."""
    root = repo_root or Path(__file__).resolve().parents[2]
    import tempfile

    with tempfile.TemporaryDirectory(prefix="m4_m8_closure_") as tmp:
        tmp_path = Path(tmp)
        state = _fixture_learning_state(tmp_path)
        learning_evidence = export_learning_evidence_from_state_v1(state)
        validated = validate_canonical_optimization_universe_learning_input_v1(
            CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=learning_evidence)
        )
        if not is_valid_learning_input_digest(validated):
            return False
        plane_request = _fixture_plane_request(learning_evidence)
        loop = run_m4_m8_evidence_return_loop_v1(
            M4M8EvidenceReturnLoopRequestV1(
                learning_evidence=learning_evidence,
                plane_request=plane_request,
                replay_seed=42,
            )
        )
        if loop.get("status") != LOOP_STATUS_COMPLETE:
            return False
        if loop.get("forward_return_loop_closed") is not True:
            return False
        cycle = loop.get("cycle") or {}
        plane = cycle.get("experiment_plane_result") or {}
        if plane.get("status") != PLANE_STATUS_COMPLETE:
            return False
        opt = cycle.get("optimization_experiment_evidence") or {}
        rebuilt = build_optimization_experiment_evidence_from_plane_v1(plane)
        if str(rebuilt.get("content_hash")) != str(opt.get("content_hash")):
            return False
        meta = cycle.get("meta_learning_evidence") or {}
        if meta.get("meta_evidence_authority") != "NONE":
            return False
        if _fabricated_instrument_epoch_fields(meta):
            return False

        base = OfflineReplayCycleInputV1(0, learning_evidence, plane_request, 42)
        n1 = OfflineReplayCycleInputV1(1, learning_evidence, plane_request, 42)
        replay = run_deterministic_multi_cycle_offline_replay_v1(
            DeterministicMultiCycleOfflineReplayRequestV1(cycles=(base, n1))
        )
        if replay.get("status") != REPLAY_STATUS_COMPLETE:
            return False
        if replay.get("multi_cycle_loop_closed") is not True:
            return False
        if replay.get("cycle_count", 0) < MINIMUM_CYCLE_COUNT:
            return False
        first_id = replay.get("replay_identity")
        second = run_deterministic_multi_cycle_offline_replay_v1(
            DeterministicMultiCycleOfflineReplayRequestV1(cycles=(base, n1))
        )
        if second.get("replay_identity") != first_id:
            return False
    return True


def is_valid_learning_input_digest(validated: Mapping[str, Any]) -> bool:
    digest = validated.get("learning_evidence_digest") or validated.get("result_digest")
    return isinstance(digest, str) and len(digest) == 64


def _fabricated_instrument_epoch_fields(meta: Mapping[str, Any]) -> bool:
    ref = str(meta.get("observed_regime_or_context_ref") or "")
    forbidden_tokens = (
        "market_observation_epoch",
        "InstrumentBindingV1",
        "canonical_instrument_id",
    )
    return any(token in ref for token in forbidden_tokens)


def prove_p5_final_closure_still_blocked_v1() -> bool:
    crosswalk = run_p5_contract_crosswalks_v1()
    opt = crosswalk.get("optimization") or {}
    meta = crosswalk.get("meta_learning") or {}
    return (
        opt.get("producer_bridge_allowed") is False
        and meta.get("producer_bridge_allowed") is False
        and opt.get("target_evidence_kind") == P5_OPTIMIZATION_TARGET_KIND
        and meta.get("target_evidence_kind") == P5_META_TARGET_KIND
    )


def prove_m4_m8_closure_evidence_files_v1(*, repo_root: Path) -> bool:
    required = (
        "src/experiments/canonical_m4_m8_evidence_return_loop_v1.py",
        "src/governance/m4_m8_optimization_meta_learning_evidence_return_closure_v1.py",
        NORMATIVE_SPEC,
        V34_ADDENDUM_SPEC,
        DECISION_CONFIG,
        "tests/governance/test_m4_m8_optimization_meta_learning_evidence_return_closure_v1.py",
        "tests/experiments/test_canonical_m4_m8_evidence_return_loop_v1.py",
    )
    return all((repo_root / rel).is_file() for rel in required)


def prove_m4_m8_optimization_meta_learning_evidence_return_closure_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    if not prove_m4_m8_closure_evidence_files_v1(repo_root=root):
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    if decision.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    if decision.get("p5_final_closure_ready") is not False:
        return False
    if decision.get("optimization_productive_authority") != "NONE":
        return False
    if decision.get("external_effect_authorized") is not False:
        return False
    if not prove_p5_final_closure_still_blocked_v1():
        return False
    return prove_m4_m8_runtime_lineage_v1(repo_root=root)


def build_m4_m8_closure_summary_v1(*, repo_root: Path | None = None) -> Mapping[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    crosswalk = run_p5_contract_crosswalks_v1()
    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "workpackage_id": WORKPACKAGE_ID,
            "baseline_sha": git_head_sha(root),
            "m4_status": decision.get("m4_status"),
            "m5_status": decision.get("m5_status"),
            "m6_status": decision.get("m6_status"),
            "m7_status": decision.get("m7_status"),
            "m8_status": decision.get("m8_status"),
            "p5_final_closure_ready": decision.get("p5_final_closure_ready"),
            "p5_optimization_blocker": (crosswalk.get("optimization") or {}).get(
                "first_blocking_reason"
            ),
            "p5_meta_learning_blocker": (crosswalk.get("meta_learning") or {}).get(
                "first_blocking_reason"
            ),
            "runtime_lineage_proven": prove_m4_m8_runtime_lineage_v1(repo_root=root),
            "census_entry_count": len(_CENSUS_ENTRIES),
        }
    )


def build_closure_evidence_digest_v1(*, repo_root: Path | None = None) -> str:
    summary = dict(build_m4_m8_closure_summary_v1(repo_root=repo_root))
    return compute_content_sha256(summary)


__all__ = [
    "CensusClassification",
    "CensusEntryV1",
    "DECISION_CONFIG",
    "NORMATIVE_SPEC",
    "SCHEMA_VERSION",
    "V34_ADDENDUM_SPEC",
    "WORKPACKAGE_ID",
    "build_closure_evidence_digest_v1",
    "build_current_census_v1",
    "build_m4_m8_closure_summary_v1",
    "prove_m4_m8_closure_evidence_files_v1",
    "prove_m4_m8_optimization_meta_learning_evidence_return_closure_v1",
    "prove_m4_m8_runtime_lineage_v1",
    "prove_p5_final_closure_still_blocked_v1",
]
