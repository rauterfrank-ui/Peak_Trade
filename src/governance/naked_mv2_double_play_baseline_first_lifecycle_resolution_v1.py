"""V3.2 baseline-first lifecycle resolution v1 — composite binding, no new runtime authority.

Composes already-adjudicated owners (integrated replay SSOT, productive cycle host, hardening,
layered core passive evidence, optimization surface pre-test predecessor, learning closed-loop
boundary) into an explicit Concept v3.2 §22 trace adjudication record.

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
from src.governance.d27_f5_shadow_test_entry_authority_subfamily_adjudication_v1 import (
    prove_d27_f5_shadow_test_entry_subfamily_adjudication_v1,
)
from src.governance.d27_research_test_entry_lifecycle_enforcement_v1 import (
    EARLIEST_GAP_AFTER_F1_F2_ENFORCED,
    prove_d27_f1_f2_test_entry_lifecycle_enforcement_v1,
)
from src.governance.platform_unified_native_vs_candidate_baseline_evidence_v1 import (
    prove_d26_platform_unified_baseline_evidence_v1,
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

CURRENT_MV2_DP_DECISION_SSOT: Final[str] = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1."
    "run_integrated_offline_trading_logic_replay_v1"
)
CURRENT_PRODUCTIVE_ENTRYPOINT: Final[str] = (
    "ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1."
    "run_current_productive_master_v2_runtime_cycle_v1"
)
CURRENT_DYNAMIC_SCOPE_OWNER: Final[str] = (
    "trading.master_v2.deterministic_scope_event_generator_v1.generate_deterministic_scope_event"
)
CURRENT_BULL_BEAR_STATE_SWITCH_OWNER: Final[str] = (
    "trading.master_v2.double_play_state.transition_state"
)
CURRENT_COMPOSITION_OWNER: Final[str] = (
    "trading.master_v2.double_play_composition_matrix_v1.evaluate_double_play_composition_matrix_v1"
)
CURRENT_ENTRY_EXIT_OWNER: Final[str] = (
    "trading.master_v2.double_play_entry_exit_policy_v0.evaluate_double_play_entry_exit_policy_v0"
)

LAYERED_CORE_CURRENT_ROLE: Final[str] = (
    "PRESERVED_NON_PRODUCTIVE_EXPLICIT_L1_L10_MECHANICAL_ARTICULATION_AND_"
    "OPTIONAL_P5_BIND_SEAL_SOURCE"
)
INTEGRATED_REPLAY_CURRENT_ROLE: Final[str] = (
    "CANONICAL_PRODUCTIVE_TRADING_DECISION_COMPUTE_OWNER_AND_ORCHESTRATOR"
)
P5_ADJUDICATION_LABEL: Final[str] = "P5_CUTOVER_OBSOLETE_CURRENT_REPLAY_IS_CANONICAL"

EARLIEST_TRUE_REMAINING_GAP_D26: Final[str] = (
    "platform_unified_native_vs_candidate_baseline_evidence_schema"
)
EARLIEST_TRUE_REMAINING_GAP: Final[str] = "test_entry_gate_defined_not_lifecycle_enforced_globally"
EARLIEST_TRUE_REMAINING_GAP_AFTER_F1_F2: Final[str] = EARLIEST_GAP_AFTER_F1_F2_ENFORCED

NAKED_BASELINE_OWNER: Final[str] = (
    "governance.naked_mv2_double_play_baseline_first_lifecycle_resolution_v1"
    ".composite_baseline_first_binding_v1"
)
PASSIVE_EVIDENCE_OWNER: Final[str] = (
    "trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.evidence_v1"
)

BASELINE_COMPLETION_SEMANTICS: Final[str] = (
    "INTEGRATED_REPLAY_SSOT_VIA_PRODUCTIVE_CYCLE_WITH_CANONICAL_NATURAL_INPUTS_AND_"
    "GOVERNANCE_PREDECESSOR_PLUS_PASSIVE_LAYER_EVIDENCE_AND_F1_COUNTERFACTUAL_RESEARCH_"
    "BASELINE_P5_CUTOVER_NOT_REQUIRED"
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


def _replay_ssot_proven_v1(*, binding: Mapping[str, Any], hardening: Mapping[str, Any]) -> bool:
    owner = str(hardening.get("trading_decision_authority_owner") or "")
    if owner != CURRENT_MV2_DP_DECISION_SSOT:
        return False
    if TRADING_DECISION_AUTHORITY_OWNER != CURRENT_MV2_DP_DECISION_SSOT:
        return False
    if binding["optimization_universe_join_authorized"] is not False:
        return False
    if P5_AUTHORITY_CUTOVER_AUTHORIZED is not False:
        return False
    if PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED:
        return False
    return True


def composite_baseline_first_binding_v1(*, repo_root: Path | None = None) -> Mapping[str, Any]:
    """Return machine-readable composite owner graph (reuse-only, no new authority)."""
    root = repo_root or Path(__file__).resolve().parents[2]
    hardening = _load_json(root, HARDENING_DECISION_CONFIG)
    pre_test = _load_json(root, PRE_TEST_DECISION_CONFIG)
    learning = _load_json(root, LEARNING_CLOSED_LOOP_DECISION_CONFIG)
    layer_evidence_present = (root / LAYER_SEPARATION_EVIDENCE_PATH).is_file()
    d26_proven = prove_d26_platform_unified_baseline_evidence_v1(repo_root=root)
    d27_f1_f2 = prove_d27_f1_f2_test_entry_lifecycle_enforcement_v1(repo_root=root)
    if not d26_proven:
        earliest_gap = EARLIEST_TRUE_REMAINING_GAP_D26
    elif d27_f1_f2:
        earliest_gap = EARLIEST_TRUE_REMAINING_GAP_AFTER_F1_F2
    else:
        earliest_gap = EARLIEST_TRUE_REMAINING_GAP

    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "workpackage_id": WORKPACKAGE_ID,
            "naked_baseline_owner": NAKED_BASELINE_OWNER,
            "passive_evidence_owner": PASSIVE_EVIDENCE_OWNER,
            "baseline_completion_semantics": BASELINE_COMPLETION_SEMANTICS,
            "new_baseline_gate_runtime_authority": NEW_BASELINE_GATE_RUNTIME_AUTHORITY,
            "current_mv2_dp_decision_ssot": CURRENT_MV2_DP_DECISION_SSOT,
            "current_productive_entrypoint": CURRENT_PRODUCTIVE_ENTRYPOINT,
            "integrated_replay_current_role": INTEGRATED_REPLAY_CURRENT_ROLE,
            "layered_core_current_role": LAYERED_CORE_CURRENT_ROLE,
            "p5_adjudication": P5_ADJUDICATION_LABEL,
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
            "d26_platform_unified_baseline_evidence_proven": d26_proven,
            "d27_f1_f2_test_entry_lifecycle_enforcement_proven": d27_f1_f2,
            "earliest_true_remaining_gap": earliest_gap,
        }
    )


def adjudicate_v32_baseline_first_requirements_v1(
    *, repo_root: Path | None = None
) -> tuple[RequirementAdjudicationV1, ...]:
    """Forensic adjudication for Concept v3.2 D24–D27 and §22 sequence (read-only composition)."""
    root = repo_root or Path(__file__).resolve().parents[2]
    binding = composite_baseline_first_binding_v1(repo_root=root)
    hardening = _load_json(root, HARDENING_DECISION_CONFIG)

    pre_test_ok = (
        binding["pre_test_predecessor_closed"]
        == "NAKED_MV2_DOUBLE_PLAY_CORE_AUTHORITY_HARDENING_V1"
    )
    replay_ssot = _replay_ssot_proven_v1(binding=binding, hardening=hardening)
    mutation_blocked = (
        binding["learning_core_mutation_authority"] == "NONE"
        and binding["optimization_core_mutation_authority"] == "NONE"
    )
    opt_join_blocked = binding["optimization_universe_join_authorized"] is False

    auth_evidence = (
        HARDENING_DECISION_CONFIG,
        PRE_TEST_DECISION_CONFIG,
        LEARNING_CLOSED_LOOP_DECISION_CONFIG,
        "docs/ops/specs/DOUBLE_PLAY_SOLE_AUTHORITY_FAIL_CLOSED_QUARANTINE_CONTRACT_V1.md",
    )
    replay_wiring = (
        CURRENT_PRODUCTIVE_ENTRYPOINT,
        CURRENT_MV2_DP_DECISION_SSOT,
        "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py",
    )
    canonical_scope_switch_wiring = (
        CURRENT_DYNAMIC_SCOPE_OWNER,
        CURRENT_BULL_BEAR_STATE_SWITCH_OWNER,
        CURRENT_COMPOSITION_OWNER,
        CURRENT_ENTRY_EXIT_OWNER,
    )

    if replay_ssot and pre_test_ok:
        d24_verdict = AdjudicationVerdict.PROVEN_CURRENT
        d24_missing = None
        d24_notes = (
            "Productive cycle invokes integrated replay SSOT; optimization productive join blocked."
        )
    elif not replay_ssot:
        d24_verdict = AdjudicationVerdict.CONFLICTING
        d24_missing = "integrated_replay_ssot_or_optimization_join_adjudication_conflict"
        d24_notes = (
            "Hardening owner, constants, or learning join boundary do not match replay SSOT."
        )
    else:
        d24_verdict = AdjudicationVerdict.PARTIAL_CURRENT
        d24_missing = "pre_test_predecessor_chain_not_proven"
        d24_notes = "Replay SSOT intact; governance predecessor chain incomplete."

    if replay_ssot:
        d25_verdict = AdjudicationVerdict.PROVEN_CURRENT
        d25_missing = None
        d25_notes = (
            "Dynamic scope and bull/bear/switch owners live in integrated replay SSOT; "
            "layered-core productive cutover not required."
        )
    else:
        d25_verdict = AdjudicationVerdict.CONFLICTING
        d25_missing = "canonical_replay_scope_and_switch_owners_not_adjudicated"
        d25_notes = "Replay SSOT conflict prevents D25 proof."

    d26_proven = prove_d26_platform_unified_baseline_evidence_v1(repo_root=root)
    if d26_proven:
        d26_verdict = AdjudicationVerdict.PROVEN_CURRENT
        d26_missing = None
        d26_notes = (
            "Platform-unified native vs candidate baseline evidence schema wired with "
            "integrated replay native producer, F1/DDO/optimization candidate classifiers, "
            "and comparison join (read-only, non-authority)."
        )
        d26_wiring = (
            "src/governance/platform_unified_native_vs_candidate_baseline_evidence_v1.py",
            "src/governance/integrated_replay_native_baseline_evidence_adapter_v1.py",
            "src/research/canonical_volatility_numeric_max_age_parameter_research_execution_v1/"
            "baseline_evidence_classification_adapter_v1.py",
        )
    else:
        d26_verdict = AdjudicationVerdict.PARTIAL_CURRENT
        d26_missing = "platform_wide_native_vs_candidate_outcome_separation_not_unified"
        d26_notes = (
            "Passive layer evidence + F1 counterfactual; no unified platform baseline schema."
        )
        d26_wiring = (
            LAYER_SEPARATION_EVIDENCE_PATH,
            F1_BASELINE_CANDIDATE_OWNER,
        )

    d27_f1_f2 = prove_d27_f1_f2_test_entry_lifecycle_enforcement_v1(repo_root=root)
    d27_verdict = AdjudicationVerdict.PARTIAL_CURRENT
    d27_wiring = (
        "src/experiments/canonical_optimization_surface_families_pre_test_preparation_v1.py",
    )
    if not pre_test_ok:
        d27_missing = "pre_test_predecessor_chain_not_proven"
        d27_notes = "Research phases after baseline: governance predecessor incomplete."
    elif d27_f1_f2:
        d27_missing = EARLIEST_TRUE_REMAINING_GAP_AFTER_F1_F2
        f5_adj = prove_d27_f5_shadow_test_entry_subfamily_adjudication_v1(repo_root=root)
        d27_notes = (
            "F1/F2 TEST_READY executors enforce pre-test TEST_ENTRY_GATE plus D26 native "
            "baseline admission at research entry; F5 shadow families not lifecycle-wired."
        )
        if f5_adj:
            d27_notes += (
                " F5-FRESH/F5-SURV/F5-CAP forensically adjudicated (read-only); "
                "bounded wiring deferred pending owner policy on D26 shadow baseline binding."
            )
        d27_wiring = d27_wiring + (
            "src/governance/d27_research_test_entry_lifecycle_enforcement_v1.py",
            (
                "research.canonical_volatility_numeric_max_age_parameter_research_execution_v1."
                "runner_v1.run_max_age_parameter_research_execution_v1"
            ),
            "src/experiments/canonical_f2_research_backtest_cost_grid_research_execution_v1.py",
        )
        if f5_adj:
            d27_wiring = d27_wiring + (
                "src/governance/d27_f5_shadow_test_entry_authority_subfamily_adjudication_v1.py",
            )
    else:
        d27_missing = "test_entry_gate_defined_not_lifecycle_enforced_globally"
        d27_notes = (
            "Research phases after baseline: governance predecessor + F1 counterfactual only."
        )

    seq_research_verdict = AdjudicationVerdict.UNKNOWN
    if not pre_test_ok:
        seq_research_verdict = AdjudicationVerdict.UNKNOWN
    elif d27_f1_f2:
        seq_research_verdict = AdjudicationVerdict.PROVEN_CURRENT
    else:
        seq_research_verdict = AdjudicationVerdict.PARTIAL_CURRENT

    seq_research_after_baseline = RequirementAdjudicationV1(
        requirement_id="REQ-BL-SEQ-03",
        verdict=seq_research_verdict,
        earliest_missing_edge=None
        if seq_research_verdict == AdjudicationVerdict.PROVEN_CURRENT
        else d27_missing,
        authority_evidence=auth_evidence,
        runtime_wiring_evidence=(
            "src/experiments/canonical_optimization_surface_families_pre_test_preparation_v1.py",
            F1_BASELINE_CANDIDATE_OWNER,
        )
        + (
            ("src/governance/d27_research_test_entry_lifecycle_enforcement_v1.py",)
            if d27_f1_f2
            else ()
        ),
        notes=(
            "F1/F2 parameter research requires D26 native baseline + matrix test-entry gate."
            if d27_f1_f2
            else "F1 counterfactual baseline id exists; global test-phase gate not runtime-enforced."
        ),
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
            CURRENT_MV2_DP_DECISION_SSOT,
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
        notes="Hardening constants; outward-only (not a hot-path gate).",
    )

    return (
        RequirementAdjudicationV1(
            requirement_id="D24",
            verdict=d24_verdict,
            earliest_missing_edge=d24_missing,
            authority_evidence=auth_evidence,
            runtime_wiring_evidence=replay_wiring,
            notes=d24_notes,
        ),
        RequirementAdjudicationV1(
            requirement_id="D25",
            verdict=d25_verdict,
            earliest_missing_edge=d25_missing,
            authority_evidence=auth_evidence,
            runtime_wiring_evidence=canonical_scope_switch_wiring + replay_wiring,
            notes=d25_notes,
        ),
        RequirementAdjudicationV1(
            requirement_id="D26",
            verdict=d26_verdict,
            earliest_missing_edge=d26_missing,
            authority_evidence=auth_evidence
            + (
                (
                    "config/governance/"
                    "v32_d26_platform_unified_native_vs_candidate_baseline_evidence_closure_v1_decision_v1.json",
                )
                if d26_proven
                else ()
            ),
            runtime_wiring_evidence=d26_wiring,
            notes=d26_notes,
        ),
        RequirementAdjudicationV1(
            requirement_id="D27",
            verdict=d27_verdict,
            earliest_missing_edge=d27_missing,
            authority_evidence=auth_evidence
            + (
                (
                    "config/governance/"
                    "v32_d27_test_entry_lifecycle_enforcement_forensic_bounded_completion_v1_decision_v1.json",
                )
                if d27_f1_f2
                else ()
            ),
            runtime_wiring_evidence=d27_wiring,
            notes=d27_notes,
        ),
        seq_research_after_baseline,
        seq_governed_return,
        inv_baseline_mutation,
    )


def earliest_missing_edge_v1(
    adjudications: Sequence[RequirementAdjudicationV1],
) -> str | None:
    for item in adjudications:
        if item.requirement_id in ("D24", "D25"):
            continue
        if item.verdict in (
            AdjudicationVerdict.PARTIAL_CURRENT,
            AdjudicationVerdict.ABSENT_CURRENT,
            AdjudicationVerdict.UNKNOWN,
        ):
            return item.earliest_missing_edge or item.requirement_id
    binding = composite_baseline_first_binding_v1()
    return str(binding.get("earliest_true_remaining_gap") or EARLIEST_TRUE_REMAINING_GAP)


def assert_no_new_baseline_gate_runtime_authority_v1() -> None:
    if NEW_BASELINE_GATE_RUNTIME_AUTHORITY:
        raise RuntimeError("baseline_gate_runtime_authority_forbidden")


def assert_replay_remains_decision_ssot_v1() -> None:
    if TRADING_DECISION_AUTHORITY_OWNER != CURRENT_MV2_DP_DECISION_SSOT:
        raise RuntimeError("trading_decision_ssot_drift")
    if P5_AUTHORITY_CUTOVER_AUTHORIZED or PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED:
        raise RuntimeError("p5_cutover_must_remain_false")


__all__ = [
    "AdjudicationVerdict",
    "BASELINE_COMPLETION_SEMANTICS",
    "CURRENT_BULL_BEAR_STATE_SWITCH_OWNER",
    "CURRENT_COMPOSITION_OWNER",
    "CURRENT_DYNAMIC_SCOPE_OWNER",
    "CURRENT_ENTRY_EXIT_OWNER",
    "CURRENT_MV2_DP_DECISION_SSOT",
    "CURRENT_PRODUCTIVE_ENTRYPOINT",
    "DECISION_CONFIG",
    "EARLIEST_TRUE_REMAINING_GAP",
    "EARLIEST_TRUE_REMAINING_GAP_AFTER_F1_F2",
    "EARLIEST_TRUE_REMAINING_GAP_D26",
    "F1_BASELINE_CANDIDATE_OWNER",
    "INTEGRATED_REPLAY_CURRENT_ROLE",
    "LAYERED_CORE_CURRENT_ROLE",
    "LAYER_SEPARATION_EVIDENCE_PATH",
    "NAKED_BASELINE_OWNER",
    "NEW_BASELINE_GATE_RUNTIME_AUTHORITY",
    "NORMATIVE_SPEC",
    "PASSIVE_EVIDENCE_OWNER",
    "P5_ADJUDICATION_LABEL",
    "RequirementAdjudicationV1",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "adjudicate_v32_baseline_first_requirements_v1",
    "assert_no_new_baseline_gate_runtime_authority_v1",
    "assert_replay_remains_decision_ssot_v1",
    "composite_baseline_first_binding_v1",
    "earliest_missing_edge_v1",
]
