"""V3.2 baseline-first lifecycle resolution v1 — composite binding, no new runtime authority.

Composes already-adjudicated owners (hardening, layered core evidence, integrated replay,
optimization surface pre-test predecessor, learning closed-loop boundary) into an explicit
Concept v3.2 §22 trace adjudication record.

Does not wire into productive hot paths. Does not authorize cutover, research execution,
parameter seams, or external effect.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from trading.master_v2.naked_mv2_double_play_core_authority_hardening_v1 import (
    LEARNING_CORE_MUTATION_AUTHORITY,
    OPTIMIZATION_CORE_MUTATION_AUTHORITY,
    PACKAGE_MARKER as HARDENING_PACKAGE_MARKER,
    TRADING_DECISION_AUTHORITY_OWNER,
)
from src.ops.p5_productive_layered_core_authority_seam_v1.constants_v1 import (
    OPTIMIZER_PRODUCTIVE_AUTHORITY,
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
    PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED,
)

SCHEMA_VERSION: Final[str] = "naked_mv2_double_play_baseline_first_lifecycle_resolution_v1"
WORKPACKAGE_ID: Final[str] = (
    "V32_NAKED_MV2_DOUBLE_PLAY_BASELINE_FIRST_AUTHORITY_AND_LIFECYCLE_RESOLUTION_V1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/V32_NAKED_MV2_DOUBLE_PLAY_BASELINE_FIRST_AUTHORITY_AND_"
    "LIFECYCLE_RESOLUTION_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/v32_naked_mv2_double_play_baseline_first_lifecycle_resolution_v1_decision_v1.json"
)
HARDENING_DECISION_CONFIG: Final[str] = (
    "config/governance/naked_mv2_double_play_core_authority_hardening_v1_decision_v1.json"
)
PRE_TEST_DECISION_CONFIG: Final[str] = (
    "config/governance/optimization_surface_families_pre_test_preparation_v1_decision_v1.json"
)
LEARNING_CLOSED_LOOP_DECISION_CONFIG: Final[str] = (
    "config/governance/learning_outcome_evidence_ingest_and_state_decision_v1.json"
)
LAYER_SEPARATION_EVIDENCE_PATH: Final[str] = (
    "docs/evidence/naked_mv2_dp_explicit_layered_core_v1/layer_separation_evidence_v1.json"
)
F1_BASELINE_CANDIDATE_OWNER: Final[str] = (
    "research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1"
    ".BASELINE_CANDIDATE_ID"
)

NAKED_BASELINE_OWNER: Final[str] = (
    "trading.master_v2.naked_mv2_double_play_baseline_first_lifecycle_resolution_v1"
    ".composite_baseline_first_binding_v1"
)
PASSIVE_EVIDENCE_OWNER: Final[str] = (
    "trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.evidence_v1"
)

BASELINE_COMPLETION_SEMANTICS: Final[str] = (
    "COMPOSITE_GOVERNANCE_PREDECESSOR_AND_PASSIVE_LAYER_EVIDENCE_AND_RESEARCH_COUNTERFACTUAL_"
    "BASELINE_NOT_RUNTIME_CUTOVER"
)

NEW_BASELINE_GATE_RUNTIME_AUTHORITY: Final[bool] = False


class AdjudicationVerdict(str, Enum):
    PROVEN_CURRENT = "PROVEN_CURRENT"
    PARTIAL_CURRENT = "PARTIAL_CURRENT"
    ABSENT_CURRENT = "ABSENT_CURRENT"
    CONFLICTING = "CONFLICTING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class RequirementAdjudicationV1:
    requirement_id: str
    verdict: AdjudicationVerdict
    earliest_missing_edge: str | None
    authority_evidence: tuple[str, ...]
    runtime_wiring_evidence: tuple[str, ...]
    notes: str


def _load_json(repo_root: Path, rel: str) -> Mapping[str, Any]:
    path = repo_root / rel
    if not path.is_file():
        raise FileNotFoundError(rel)
    return json.loads(path.read_text(encoding="utf-8"))


def composite_baseline_first_binding_v1(*, repo_root: Path | None = None) -> Mapping[str, Any]:
    """Return machine-readable composite owner graph (reuse-only, no new authority)."""
    root = repo_root or Path(__file__).resolve().parents[3]
    hardening = _load_json(root, HARDENING_DECISION_CONFIG)
    pre_test = _load_json(root, PRE_TEST_DECISION_CONFIG)
    learning = _load_json(root, LEARNING_CLOSED_LOOP_DECISION_CONFIG)
    layer_evidence_present = (root / LAYER_SEPARATION_EVIDENCE_PATH).is_file()

    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "workpackage_id": WORKPACKAGE_ID,
            "naked_baseline_owner": NAKED_BASELINE_OWNER,
            "passive_evidence_owner": PASSIVE_EVIDENCE_OWNER,
            "baseline_completion_semantics": BASELINE_COMPLETION_SEMANTICS,
            "new_baseline_gate_runtime_authority": NEW_BASELINE_GATE_RUNTIME_AUTHORITY,
            "trading_decision_authority_owner": TRADING_DECISION_AUTHORITY_OWNER,
            "hardening_package_marker": HARDENING_PACKAGE_MARKER,
            "learning_core_mutation_authority": LEARNING_CORE_MUTATION_AUTHORITY,
            "optimization_core_mutation_authority": OPTIMIZATION_CORE_MUTATION_AUTHORITY,
            "optimizer_productive_authority": OPTIMIZER_PRODUCTIVE_AUTHORITY,
            "p5_authority_cutover_authorized": P5_AUTHORITY_CUTOVER_AUTHORIZED,
            "productive_decision_path_cutover_enabled": PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED,
            "pre_test_predecessor_closed": pre_test.get("predecessor_closed"),
            "optimization_universe_join_authorized": learning.get(
                "optimization_universe_join_authorized"
            ),
            "learning_productive_authority": learning.get("learning_productive_authority"),
            "layer_separation_evidence_present": layer_evidence_present,
            "layer_separation_evidence_path": LAYER_SEPARATION_EVIDENCE_PATH,
            "f1_baseline_candidate_owner_ref": F1_BASELINE_CANDIDATE_OWNER,
            "hardening_decision_workpackage": hardening.get("workpackage_id"),
            "pre_test_decision_workpackage": pre_test.get("workpackage_id"),
            "external_effect_authorized": False,
        }
    )


def adjudicate_v32_baseline_first_requirements_v1(
    *, repo_root: Path | None = None
) -> tuple[RequirementAdjudicationV1, ...]:
    """Forensic adjudication for Concept v3.2 D24–D27 and §22 sequence (read-only composition)."""
    binding = composite_baseline_first_binding_v1(repo_root=repo_root)
    root = repo_root or Path(__file__).resolve().parents[3]

    pre_test_ok = (
        binding["pre_test_predecessor_closed"]
        == "NAKED_MV2_DOUBLE_PLAY_CORE_AUTHORITY_HARDENING_V1"
    )
    layer_ok = bool(binding["layer_separation_evidence_present"])
    mutation_blocked = (
        binding["learning_core_mutation_authority"] == "NONE"
        and binding["optimization_core_mutation_authority"] == "NONE"
    )
    opt_join_blocked = binding["optimization_universe_join_authorized"] is False
    cutover_off = (
        not binding["p5_authority_cutover_authorized"]
        and not binding["productive_decision_path_cutover_enabled"]
    )

    auth_evidence = (
        HARDENING_DECISION_CONFIG,
        PRE_TEST_DECISION_CONFIG,
        LEARNING_CLOSED_LOOP_DECISION_CONFIG,
        LAYER_SEPARATION_EVIDENCE_PATH,
    )

    d24_missing: str | None = None
    d24_verdict = AdjudicationVerdict.PARTIAL_CURRENT
    if not pre_test_ok or not layer_ok:
        d24_verdict = AdjudicationVerdict.PARTIAL_CURRENT
        d24_missing = "governance_or_passive_layer_evidence_incomplete"
    elif cutover_off:
        d24_missing = (
            "productive_layered_core_cutover_disabled_integrated_replay_is_current_decision_ssot"
        )
    else:
        d24_verdict = AdjudicationVerdict.UNKNOWN

    d25_missing: str | None = None
    d25_verdict = AdjudicationVerdict.PARTIAL_CURRENT
    if not layer_ok:
        d25_missing = "passive_layer_separation_evidence_absent"
    elif cutover_off:
        d25_missing = "productive_native_l6_l10_observation_bundle_not_cutover_bound"
    else:
        d25_verdict = AdjudicationVerdict.UNKNOWN

    d26_missing: str | None = None
    d26_verdict = AdjudicationVerdict.PARTIAL_CURRENT
    if not layer_ok:
        d26_missing = "native_layer_trace_evidence_absent"
    else:
        d26_missing = "platform_wide_native_vs_candidate_outcome_separation_not_unified"

    d27_missing: str | None = None
    d27_verdict = AdjudicationVerdict.PARTIAL_CURRENT
    if not pre_test_ok:
        d27_missing = "pre_test_predecessor_chain_not_proven"
    else:
        d27_missing = "test_entry_gate_defined_not_lifecycle_enforced_globally"

    seq_research_after_baseline = RequirementAdjudicationV1(
        requirement_id="REQ-BL-SEQ-03",
        verdict=AdjudicationVerdict.PARTIAL_CURRENT if pre_test_ok else AdjudicationVerdict.UNKNOWN,
        earliest_missing_edge=d27_missing,
        authority_evidence=auth_evidence,
        runtime_wiring_evidence=(
            "src/experiments/canonical_optimization_surface_families_pre_test_preparation_v1.py",
            F1_BASELINE_CANDIDATE_OWNER,
        ),
        notes="F1 counterfactual baseline id exists; global test-phase gate not runtime-enforced.",
    )

    seq_governed_return = RequirementAdjudicationV1(
        requirement_id="REQ-BL-SEQ-05",
        verdict=AdjudicationVerdict.PROVEN_CURRENT
        if mutation_blocked and opt_join_blocked
        else AdjudicationVerdict.CONFLICTING,
        earliest_missing_edge=None
        if mutation_blocked and opt_join_blocked
        else "learning_or_optimization_mutation_or_join_not_blocked",
        authority_evidence=auth_evidence,
        runtime_wiring_evidence=(
            "src/governance/governed_productive_runtime_parameter_seam_join_v1.py",
            "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
        ),
        notes="Governed seam optional on replay; optimization direct write forbidden in tests.",
    )

    inv_baseline_mutation = RequirementAdjudicationV1(
        requirement_id="REQ-BL-INV-03",
        verdict=AdjudicationVerdict.PROVEN_CURRENT
        if mutation_blocked
        else AdjudicationVerdict.CONFLICTING,
        earliest_missing_edge=None if mutation_blocked else "optimization_core_mutation_not_none",
        authority_evidence=(HARDENING_DECISION_CONFIG,),
        runtime_wiring_evidence=(HARDENING_PACKAGE_MARKER,),
        notes="Hardening constants; not wired into integrated replay hot path.",
    )

    return (
        RequirementAdjudicationV1(
            requirement_id="D24",
            verdict=d24_verdict,
            earliest_missing_edge=d24_missing,
            authority_evidence=auth_evidence,
            runtime_wiring_evidence=(
                TRADING_DECISION_AUTHORITY_OWNER,
                "trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.orchestrator_v1",
            ),
            notes="Integrated replay SSOT for trading decision; explicit layered core P5 cutover off.",
        ),
        RequirementAdjudicationV1(
            requirement_id="D25",
            verdict=d25_verdict,
            earliest_missing_edge=d25_missing,
            authority_evidence=auth_evidence,
            runtime_wiring_evidence=(
                "tests/trading/master_v2/test_naked_mv2_dp_explicit_layered_core_s5_orchestrator_v1.py",
            ),
            notes="L6/L10 reachable in orchestrator proof tests; productive observation bundle partial.",
        ),
        RequirementAdjudicationV1(
            requirement_id="D26",
            verdict=d26_verdict,
            earliest_missing_edge=d26_missing,
            authority_evidence=auth_evidence,
            runtime_wiring_evidence=(LAYER_SEPARATION_EVIDENCE_PATH, F1_BASELINE_CANDIDATE_OWNER),
            notes="Layer separation + F1 UNRESOLVED baseline candidate; no unified platform schema.",
        ),
        RequirementAdjudicationV1(
            requirement_id="D27",
            verdict=d27_verdict,
            earliest_missing_edge=d27_missing,
            authority_evidence=auth_evidence,
            runtime_wiring_evidence=(
                "src/experiments/canonical_optimization_surface_families_pre_test_preparation_v1.py",
            ),
            notes="Research phases after baseline: governance predecessor + F1 counterfactual only.",
        ),
        seq_research_after_baseline,
        seq_governed_return,
        inv_baseline_mutation,
    )


def earliest_missing_edge_v1(
    adjudications: Sequence[RequirementAdjudicationV1],
) -> str | None:
    for item in adjudications:
        if item.verdict in (
            AdjudicationVerdict.PARTIAL_CURRENT,
            AdjudicationVerdict.ABSENT_CURRENT,
            AdjudicationVerdict.UNKNOWN,
        ):
            return item.earliest_missing_edge or item.requirement_id
    return None


def assert_no_new_baseline_gate_runtime_authority_v1() -> None:
    if NEW_BASELINE_GATE_RUNTIME_AUTHORITY:
        raise RuntimeError("baseline_gate_runtime_authority_forbidden")


__all__ = [
    "AdjudicationVerdict",
    "BASELINE_COMPLETION_SEMANTICS",
    "DECISION_CONFIG",
    "F1_BASELINE_CANDIDATE_OWNER",
    "LAYER_SEPARATION_EVIDENCE_PATH",
    "NAKED_BASELINE_OWNER",
    "NEW_BASELINE_GATE_RUNTIME_AUTHORITY",
    "NORMATIVE_SPEC",
    "PASSIVE_EVIDENCE_OWNER",
    "RequirementAdjudicationV1",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "adjudicate_v32_baseline_first_requirements_v1",
    "assert_no_new_baseline_gate_runtime_authority_v1",
    "composite_baseline_first_binding_v1",
    "earliest_missing_edge_v1",
]
