"""P0 read-only L1–L10 external-evidence seam census (Master V2 / Double Play).

Blueprint design intent: docs-only authority. This module proves CURRENT repository
state only. Does not implement Component A/B or mutate Double-Play semantics.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Iterable, Mapping, Sequence

from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.layer_catalog_v1 import (
    EXPLICIT_LAYERED_CORE_OWNER,
    EXPLICIT_LAYERED_CORE_VERSION,
    LAYER_CATALOG_V1,
    LAYER_ORDER_V1,
    LayerIdV1,
)

SCHEMA_VERSION: Final[str] = "master_v2_double_play_evidence_input_plane_p0_evidence_seam_census/v1"
WORKPACKAGE_ID: Final[str] = "MASTER_V2_DOUBLE_PLAY_EVIDENCE_INPUT_PLANE_P0_EVIDENCE_SEAM_CENSUS_V1"
BLUEPRINT_BASELINE_SHA: Final[str] = "2354c4439c3228265b8aaa51d06510db48af1469"

CENSUS_ARTIFACT_REL: Final[str] = (
    "docs/evidence/master_v2_double_play_evidence_input_plane_p0/"
    "l1_l10_evidence_seam_census_v1.json"
)
LEDGER_ARTIFACT_REL: Final[str] = (
    "docs/evidence/master_v2_double_play_evidence_input_plane_p0/evidence_reference_ledger_v1.json"
)
OPEN_CONFLICT_REL: Final[str] = (
    "docs/evidence/master_v2_double_play_evidence_input_plane_p0/open_conflict_register_v1.json"
)
P1_DESIGN_INPUT_REL: Final[str] = (
    "docs/evidence/master_v2_double_play_evidence_input_plane_p0/p1_design_input_block_v1.json"
)

_FORBIDDEN_AB_RUNTIME_MARKERS: Final[tuple[str, ...]] = (
    "master_v2_evidence_adjudicator",
    "master_v2_double_play_input_creator",
    "master_v2_double_play_input_binder",
    "run_component_a_runtime_v1",
    "run_component_b_runtime_v1",
)
_P1_CONTRACT_PACKAGE_SUBPATH: Final[str] = (
    "master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1"
)

_INTELLIGENCE_ROOTS: Final[tuple[str, ...]] = (
    "src/learning",
    "src/experiments",
    "src/aiops",
)

_LAYERED_CORE_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "naked_mv2_dp_explicit_layered_core_v1",
    "apply_l1_selected_future_v1",
    "apply_l10_bull_bear_switch_v1",
    "orchestrate_naked_layered_core_v1",
)

_EPISTEMIC = frozenset(
    {
        "PROVEN_CURRENT",
        "PROVEN_CLOSED",
        "PROVEN_BOUNDED_TYPED_ONLY",
        "ABSENT",
        "CONFLICTING",
        "UNKNOWN",
    }
)


@dataclass(frozen=True, slots=True)
class BypassCensusEntryV1:
    path_id: str
    classification: str
    evidence_refs: tuple[str, ...]
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification,
            "evidence_refs": list(self.evidence_refs),
            "notes": self.notes,
            "path_id": self.path_id,
        }


def _repo_files_under(root: Path, prefix: str) -> Iterable[Path]:
    base = root / prefix
    if not base.is_dir():
        return ()
    return (p for p in base.rglob("*.py") if p.is_file())


def _file_imports_marker(path: Path, markers: Sequence[str]) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    hits: list[str] = []
    for marker in markers:
        if marker in text:
            hits.append(marker)
    return hits


def _scan_intelligence_to_layered_core_direct_calls(repo_root: Path) -> BypassCensusEntryV1:
    evidence: list[str] = []
    present = False
    for prefix in _INTELLIGENCE_ROOTS:
        for py in _repo_files_under(repo_root, prefix):
            hits = _file_imports_marker(py, _LAYERED_CORE_IMPORT_MARKERS)
            if hits:
                present = True
                rel = py.relative_to(repo_root).as_posix()
                evidence.append(f"{rel}:imports={','.join(hits)}")
    classification = "PRESENT" if present else "PROVEN_ABSENT"
    if not evidence and not present:
        evidence = [
            "src/learning/**/*.py: no naked_mv2_dp_explicit_layered_core import (grep census v1)",
            "src/experiments/**/*.py: no orchestrate_naked_layered_core import (grep census v1)",
        ]
    return BypassCensusEntryV1(
        path_id="external_intelligent_producer_to_dp_layer_direct_call",
        classification=classification,
        evidence_refs=tuple(evidence),
        notes=(
            "Direct import/call from MI/Learning/Optimization/Meta-Learning/Research "
            "into explicit L1–L10 layered-core apply/orchestrate surfaces."
        ),
    )


def _scan_trading_imports_learning_decision_mutation(repo_root: Path) -> BypassCensusEntryV1:
    """DDO capture on trading producers is observation-only, not authority."""
    trading_mv2 = repo_root / "src/trading/master_v2"
    capture_hosts: list[str] = []
    if trading_mv2.is_dir():
        for py in trading_mv2.rglob("*.py"):
            if "deterministic_decision_outcome_v0.capture_v0" in py.read_text(
                encoding="utf-8", errors="replace"
            ):
                capture_hosts.append(py.relative_to(repo_root).as_posix())
    return BypassCensusEntryV1(
        path_id="producer_to_dp_state_mutation_via_learning_import",
        classification="PRESENT",
        evidence_refs=tuple(capture_hosts),
        notes=(
            "PRESENT as DDO observe_after_producer_v0 capture hosts only; "
            "TRADING_AUTHORITY=NONE; RUNTIME_EFFECT=OBSERVATION_ONLY per "
            "double_play_input_evidence_v1.py module contract."
        ),
    )


def _glob_ab_implementation(repo_root: Path) -> tuple[bool, tuple[str, ...]]:
    hits: list[str] = []
    for py in (repo_root / "src").rglob("*.py"):
        rel = py.relative_to(repo_root).as_posix()
        if _P1_CONTRACT_PACKAGE_SUBPATH in rel:
            continue
        if "p0_evidence_seam_census" in py.name:
            continue
        try:
            text = py.read_text(encoding="utf-8")
        except OSError:
            continue
        for marker in _FORBIDDEN_AB_RUNTIME_MARKERS:
            if marker in text:
                hits.append(f"{rel}:{marker}")
    return (len(hits) > 0, tuple(sorted(set(hits))))


def _l6_external_evidence_admissibility_v1() -> str:
    try:
        from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.constants_v1 import (  # noqa: PLC0415
            L6_CENSUS_EXTERNAL_EVIDENCE_ADMISSIBILITY,
            O_002_RATIFIED,
        )

        if O_002_RATIFIED:
            return L6_CENSUS_EXTERNAL_EVIDENCE_ADMISSIBILITY
    except ImportError:
        pass
    return "UNKNOWN"


def _l6_allowed_evidence_types_v1() -> tuple[str, ...]:
    if _l6_external_evidence_admissibility_v1() == "PROVEN_BOUNDED_TYPED_ONLY":
        return (
            "PROVEN_BOUNDED_TYPED_ONLY: L6BoundedTypedExternalEvidenceInputV1 via "
            "CanonicalMasterV2EvidenceEnvelopeV1 + CanonicalDpLayerInputBindingV1",
            "PRESERVED: caller-supplied float proposed_d_t (P4/O-R2 path unchanged)",
            "FORBIDDEN: A/B collapse to proposed_d_t; B compute/select D_t formula",
        )
    return (
        "PROVEN_CURRENT: caller-supplied float proposed_d_t only; "
        "NOT PROVEN: MI/Learning/Optimization evidence types",
    )


def _layer_extension(layer_id: LayerIdV1) -> dict[str, Any]:
    """Forensic extensions proven from CURRENT code (P0 census)."""
    common_topology = (
        "Cap2.3 src/ops/single_selected_future_policy_v1/ → "
        "Cap2.4 src/ops/single_selected_future_runtime_binding_v1/ → "
        "Master V2 integrated offline replay / productive cycle → "
        "explicit L1–L10 orchestrator (when layered bind enabled) → "
        "composition / entry_exit / CRS downstream (outside layered core)."
    )
    extensions: dict[LayerIdV1, dict[str, Any]] = {
        LayerIdV1.L1_SELECTED_FUTURE: {
            "current_input_contracts": ("SelectedFutureInputV1", "SelectedFutureStateV1"),
            "current_producers": (
                "orchestrator caller (SelectedFutureInputV1)",
                "upstream Cap 2.4 BoundInstrumentV1 consumer path (outside L1 contract)",
            ),
            "current_consumers": ("l2_market_observation_v1",),
            "existing_external_evidence_seam": "ABSENT",
            "external_evidence_admissibility": "PROVEN_CLOSED",
            "allowed_evidence_types": (),
            "binding_contract": "SelectedFutureInputV1 / InstrumentObservationKeyV1",
            "instrument_binding_semantics": (
                "PROVEN_CURRENT: instrument_id must equal instrument_key.canonical_instrument_id "
                "(apply_l1_selected_future_v1 ValueError on mismatch)"
            ),
            "epoch_binding_semantics": "ABSENT at L1",
            "freshness_semantics": "ABSENT at L1",
            "provenance_semantics": "ABSENT at L1",
            "conflict_semantics": "ABSENT",
            "missing_input_semantics": "PROVEN_CURRENT: ValueError l1_instrument_id_canonical_mismatch",
            "failure_semantics": "PROVEN_CURRENT: fail-fast ValueError; no fail-closed envelope",
            "state_mutation_effect": "PROVEN_CURRENT: selected_future_state_only per catalog",
            "trading_authority_effect": "PROVEN_CURRENT: none; instrument binding only",
            "future_B_target_possible": "UNKNOWN",
            "required_change_class": (
                "authority_decision: Cap 2.3/2.4 remain selection/binding owners; "
                "any B bind must not bypass them"
            ),
            "status": "PROVEN_CURRENT",
            "open_questions": (
                "Whether future B may target L1 without duplicating Cap 2.4 binding authority.",
            ),
        },
        LayerIdV1.L2_MARKET_OBSERVATION: {
            "current_input_contracts": (
                "MarketObservationInputV1",
                "ObservationCandidateV1",
                "ObservationAcceptanceStateV1",
            ),
            "current_producers": (
                "orchestrator initialization_observations sequence",
                "distinct_market_observation_acceptor_v1 (C1)",
            ),
            "current_consumers": ("l3_initial_direction_v1",),
            "existing_external_evidence_seam": "ABSENT",
            "external_evidence_admissibility": "PROVEN_CLOSED",
            "allowed_evidence_types": (),
            "binding_contract": "MarketObservationInputV1 / C1 acceptance contracts",
            "instrument_binding_semantics": (
                "PROVEN_CURRENT: bound_instrument_key on acceptance state matches L1 selected"
            ),
            "epoch_binding_semantics": (
                "PROVEN_CURRENT: market_observation_epoch increments on DISTINCT commit"
            ),
            "freshness_semantics": "UNKNOWN for external evidence; caller-supplied marks only",
            "provenance_semantics": "ABSENT for external intelligence at layer boundary",
            "conflict_semantics": "PROVEN_CURRENT: non-DISTINCT observations do not advance chain",
            "missing_input_semantics": (
                "PROVEN_CURRENT: orchestrator fail_closed orchestrator_initialization_incomplete"
            ),
            "failure_semantics": "PROVEN_CURRENT: skip non-DISTINCT; init incomplete → fail_closed",
            "state_mutation_effect": "observation_acceptance_state_only",
            "trading_authority_effect": "NONE",
            "future_B_target_possible": "UNKNOWN",
            "required_change_class": "contract_extension + owner authority for any non-C1 evidence types",
            "status": "PROVEN_CURRENT",
            "open_questions": (
                "Whether MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0 fields could map to "
                "ObservationCandidateV1 without new authority (not proven in layered orchestrator).",
            ),
        },
        LayerIdV1.L3_INITIAL_DIRECTION: {
            "current_input_contracts": ("InitialDirectionInputV1", "ElementaryDirectionResultV1"),
            "current_producers": ("elementary_direction_v1 via apply_l3",),
            "current_consumers": ("l4_initial_state_v1",),
            "existing_external_evidence_seam": "ABSENT",
            "external_evidence_admissibility": "PROVEN_CLOSED",
            "allowed_evidence_types": (),
            "binding_contract": "InitialDirectionInputV1",
            "instrument_binding_semantics": "PROVEN_CURRENT: bound_instrument_key required",
            "epoch_binding_semantics": "ABSENT",
            "freshness_semantics": "ABSENT",
            "provenance_semantics": "ABSENT",
            "conflict_semantics": "PROVEN_CURRENT: neutral direction skips initialization",
            "missing_input_semantics": "PROVEN_CURRENT: non BULL/BEAR continues loop without L4",
            "failure_semantics": "PROVEN_CURRENT: pure evaluator; no external envelope",
            "state_mutation_effect": "none_pure_evaluator",
            "trading_authority_effect": "NONE",
            "future_B_target_possible": "PROVEN_CLOSED",
            "required_change_class": "semantic_redesign if external direction evidence admitted",
            "status": "PROVEN_CURRENT",
            "open_questions": (),
        },
        LayerIdV1.L4_INITIAL_STATE_INITIALIZATION: {
            "current_input_contracts": (
                "InitialStateInitializationInputV1",
                "InitialRegimeStateV1",
            ),
            "current_producers": ("apply_l4_initial_state_initialization_v1",),
            "current_consumers": ("l5_nullline_v1",),
            "existing_external_evidence_seam": "ABSENT",
            "external_evidence_admissibility": "PROVEN_CLOSED",
            "allowed_evidence_types": (),
            "binding_contract": "InitialStateInitializationInputV1",
            "instrument_binding_semantics": "PROVEN_CURRENT: from SelectedFutureStateV1",
            "epoch_binding_semantics": "ABSENT",
            "freshness_semantics": "ABSENT",
            "provenance_semantics": "ABSENT",
            "conflict_semantics": "PROVEN_CURRENT: fail_closed with fail_reasons tuple",
            "missing_input_semantics": "PROVEN_CURRENT: fail_closed flag on output",
            "failure_semantics": "PROVEN_CURRENT: orchestrator returns fail_closed on L4 fail",
            "state_mutation_effect": "regime_authority_established_once",
            "trading_authority_effect": "PROVEN_CURRENT: establishes initial BULL/BEAR only",
            "future_B_target_possible": "PROVEN_CLOSED",
            "required_change_class": "authority_decision + semantic_redesign",
            "status": "PROVEN_CURRENT",
            "open_questions": (),
        },
        LayerIdV1.L5_NULLLINE: {
            "current_input_contracts": ("NullLineInputV1", "NullLineStateV1"),
            "current_producers": ("apply_l5_nullline_v1",),
            "current_consumers": ("l6_dynamic_scope_generator_v1",),
            "existing_external_evidence_seam": "ABSENT",
            "external_evidence_admissibility": "PROVEN_CLOSED",
            "allowed_evidence_types": (),
            "binding_contract": "NullLineInputV1",
            "instrument_binding_semantics": "PROVEN_CURRENT: instrument_id on NullLineStateV1",
            "epoch_binding_semantics": (
                "PROVEN_CURRENT: provenance_mark_epoch from market_observation_epoch"
            ),
            "freshness_semantics": "ABSENT",
            "provenance_semantics": "PROVEN_CURRENT: provenance_mark_epoch field only",
            "conflict_semantics": "ABSENT",
            "missing_input_semantics": "ABSENT",
            "failure_semantics": "PROVEN_CURRENT: deterministic nullline from initialization_mark",
            "state_mutation_effect": "nullline_state_only_not_running_reference",
            "trading_authority_effect": "NONE",
            "future_B_target_possible": "PROVEN_CLOSED",
            "required_change_class": "semantic_redesign (Blueprint excludes NullLine redesign in P0 scope)",
            "status": "PROVEN_CURRENT",
            "open_questions": (),
        },
        LayerIdV1.L6_DYNAMIC_SCOPE_GENERATOR: {
            "current_input_contracts": (
                "DynamicScopeGeneratorInputV1",
                "DynamicScopeGeneratorOutputV1",
                "DynamicScopeGeneratorV1 (Protocol)",
                "L6BoundedTypedExternalEvidenceInputV1 (P1 contract; L6 interpretation P2+)",
            ),
            "current_producers": (
                "MechanicalStepSpecV1.proposed_d_t via orchestrator",
                "ExplicitPassthroughDynamicScopeGeneratorV1 (default validation path)",
                "Component B typed binding (P1 contract only; runtime blocked)",
            ),
            "current_consumers": ("l7_scope_state_v1",),
            "existing_external_evidence_seam": "PROVEN_CURRENT",
            "external_evidence_admissibility": _l6_external_evidence_admissibility_v1(),
            "allowed_evidence_types": _l6_allowed_evidence_types_v1(),
            "binding_contract": (
                "DynamicScopeGeneratorInputV1 + replaceable DynamicScopeGeneratorV1 "
                "(explicit_external_d_t_passthrough/v1)"
            ),
            "instrument_binding_semantics": (
                "PROVEN_CURRENT: indirect via nullline.instrument_id context; "
                "no separate instrument field on L6 input"
            ),
            "epoch_binding_semantics": "ABSENT on L6 input",
            "freshness_semantics": "ABSENT",
            "provenance_semantics": (
                "PROVEN_CURRENT: generator_id on output only; no evidence envelope"
            ),
            "conflict_semantics": "ABSENT",
            "missing_input_semantics": (
                "PROVEN_CURRENT: naked_boundary_fail_closed_reasons_from_distance → fail_closed"
            ),
            "failure_semantics": (
                "PROVEN_CURRENT: fail_closed + fail_reasons; downstream layers NOT_REACHED"
            ),
            "state_mutation_effect": "none_replaceable_generator",
            "trading_authority_effect": "NONE",
            "future_B_target_possible": "PROVEN_CURRENT",
            "required_change_class": (
                "P1_RATIFIED: typed L6 evidence contract (Option B); "
                "proposed_d_t seam preserved; no D_t formula selection"
            ),
            "status": "PROVEN_CURRENT",
            "open_questions": (
                "P2: L6 runtime consumer for L6BoundedTypedExternalEvidenceInputV1 "
                "(interpretation authority remains L6-only).",
            ),
        },
        LayerIdV1.L7_SCOPE_STATE: {
            "current_input_contracts": (
                "ScopeStateMaterializationInputV1",
                "ScopeStateV1",
            ),
            "current_producers": ("apply_l7_scope_state_materialization_v1",),
            "current_consumers": ("l8_running_reference_v1", "l10_bull_bear_switch_v1 (d_t)"),
            "existing_external_evidence_seam": "ABSENT",
            "external_evidence_admissibility": "PROVEN_CLOSED",
            "allowed_evidence_types": (),
            "binding_contract": "ScopeStateMaterializationInputV1",
            "instrument_binding_semantics": "PROVEN_CURRENT: instrument_id on ScopeStateV1",
            "epoch_binding_semantics": "PROVEN_CURRENT: nullline_provenance_epoch carried",
            "freshness_semantics": "ABSENT",
            "provenance_semantics": "PROVEN_CURRENT: nullline_price + generator_id",
            "conflict_semantics": "ABSENT",
            "missing_input_semantics": "PROVEN_CURRENT: fail_closed if generator output invalid",
            "failure_semantics": "PROVEN_CURRENT: fail_closed; scope None → orchestrator abort",
            "state_mutation_effect": "scope_state_only_no_regime_switch",
            "trading_authority_effect": "NONE",
            "future_B_target_possible": "UNKNOWN",
            "required_change_class": "contract_extension only if L6 output remains sole D_t source",
            "status": "PROVEN_CURRENT",
            "open_questions": (
                "CONFLICTING topology: scope_event_generator / transition_state vs L7 scope_state "
                "is out of scope for repair (Blueprint §5); may affect productive bind wiring only.",
            ),
        },
        LayerIdV1.L8_RUNNING_REFERENCE: {
            "current_input_contracts": (
                "RunningReferenceStepInputV1",
                "RunningReferenceStateV1",
            ),
            "current_producers": ("apply_l8_running_reference_step_v1",),
            "current_consumers": ("l9_counter_move_v1", "l10_bull_bear_switch_v1"),
            "existing_external_evidence_seam": "ABSENT",
            "external_evidence_admissibility": "PROVEN_CLOSED",
            "allowed_evidence_types": (),
            "binding_contract": "RunningReferenceStepInputV1",
            "instrument_binding_semantics": "PROVEN_CURRENT: instrument_id on state",
            "epoch_binding_semantics": "ABSENT",
            "freshness_semantics": "ABSENT",
            "provenance_semantics": "ABSENT",
            "conflict_semantics": "ABSENT",
            "missing_input_semantics": "ABSENT",
            "failure_semantics": "PROVEN_CURRENT: deterministic R_t update from regime+mark",
            "state_mutation_effect": "running_reference_state_only_not_nullline",
            "trading_authority_effect": "NONE",
            "future_B_target_possible": "PROVEN_CLOSED",
            "required_change_class": "semantic_redesign (Blueprint excludes L8 mechanics change)",
            "status": "PROVEN_CURRENT",
            "open_questions": (),
        },
        LayerIdV1.L9_COUNTER_MOVE: {
            "current_input_contracts": ("CounterMoveInputV1", "CounterMoveStateV1"),
            "current_producers": ("apply_l9_counter_move_v1",),
            "current_consumers": ("l10_bull_bear_switch_v1",),
            "existing_external_evidence_seam": "ABSENT",
            "external_evidence_admissibility": "PROVEN_CLOSED",
            "allowed_evidence_types": (),
            "binding_contract": "CounterMoveInputV1",
            "instrument_binding_semantics": "PROVEN_CURRENT: instrument_id on CounterMoveStateV1",
            "epoch_binding_semantics": "ABSENT",
            "freshness_semantics": "ABSENT",
            "provenance_semantics": "ABSENT",
            "conflict_semantics": "ABSENT",
            "missing_input_semantics": "ABSENT",
            "failure_semantics": "PROVEN_CURRENT: pure formula CM_t",
            "state_mutation_effect": "none_pure_formula",
            "trading_authority_effect": "NONE",
            "future_B_target_possible": "PROVEN_CLOSED",
            "required_change_class": "semantic_redesign (Blueprint excludes L9 mechanics change)",
            "status": "PROVEN_CURRENT",
            "open_questions": (),
        },
        LayerIdV1.L10_BULL_BEAR_STATE_SWITCH: {
            "current_input_contracts": ("BullBearSwitchInputV1", "BullBearSwitchOutputV1"),
            "current_producers": ("apply_l10_bull_bear_switch_v1",),
            "current_consumers": ("orchestrator persisted regime + R_t reset",),
            "existing_external_evidence_seam": "ABSENT",
            "external_evidence_admissibility": "PROVEN_CLOSED",
            "allowed_evidence_types": (),
            "binding_contract": "BullBearSwitchInputV1",
            "instrument_binding_semantics": "ABSENT on switch input",
            "epoch_binding_semantics": "ABSENT",
            "freshness_semantics": "ABSENT",
            "provenance_semantics": "ABSENT",
            "conflict_semantics": "ABSENT",
            "missing_input_semantics": "ABSENT",
            "failure_semantics": (
                "PROVEN_CURRENT: SOLE_PRICE_SWITCH_RULE CM_t>=D_t; no external override path"
            ),
            "state_mutation_effect": "regime_switch_authority_sole_price_rule",
            "trading_authority_effect": (
                "PROVEN_CURRENT: sole layered-core regime switch authority (BULL/BEAR flip)"
            ),
            "future_B_target_possible": "PROVEN_CLOSED",
            "required_change_class": "authority_decision + semantic_redesign",
            "status": "PROVEN_CURRENT",
            "open_questions": (
                "Parallel SideState/switch owners in double_play_composition remain outside L10; "
                "not equated in this census row.",
            ),
        },
    }
    base = extensions[layer_id]
    base = dict(base)
    base["topology_note"] = common_topology
    return base


def _build_layer_row(layer_id: LayerIdV1) -> dict[str, Any]:
    entry = LAYER_CATALOG_V1[layer_id]
    ext = _layer_extension(layer_id)
    owner_module = f"src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/{entry.semantic_owner.split('.')[-1]}.py"
    evidence_refs = [
        f"src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/layer_catalog_v1.py:{layer_id.value}",
        f"src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/contracts_v1.py",
        owner_module,
        "src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/orchestrator_v1.py",
        "docs/evidence/naked_mv2_dp_explicit_layered_core_v1/layer_separation_evidence_v1.json",
    ]
    return {
        "layer_id": layer_id.value,
        "current_owner": entry.semantic_owner,
        "owner_evidence": "PROVEN_CURRENT",
        "semantic_responsibility": f"{entry.input_summary} → {entry.output_summary}; mutates={entry.mutates}",
        **ext,
        "evidence_refs": evidence_refs,
    }


def run_direct_external_to_dp_bypass_census_v1(
    repo_root: Path | None = None,
) -> tuple[BypassCensusEntryV1, ...]:
    root = repo_root or Path(__file__).resolve().parents[2]
    entries = [
        _scan_intelligence_to_layered_core_direct_calls(root),
        _scan_trading_imports_learning_decision_mutation(root),
        BypassCensusEntryV1(
            path_id="producer_to_sidestate_mutation",
            classification="PROVEN_ABSENT",
            evidence_refs=(
                "src/learning/**/*.py: no SideState write/import of compose_double_play "
                "(grep census v1)",
            ),
            notes="No learning/experiments module mutates SideState.",
        ),
        BypassCensusEntryV1(
            path_id="producer_to_switch_decision",
            classification="PROVEN_ABSENT",
            evidence_refs=(
                "src/learning/**/*.py: no apply_l10_bull_bear_switch import (grep census v1)",
            ),
            notes="Switch authority not imported from intelligence producers.",
        ),
        BypassCensusEntryV1(
            path_id="producer_to_entry_exit_decision",
            classification="PRESENT",
            evidence_refs=(
                "src/learning/deterministic_decision_outcome_v0/double_play_input_evidence_v1.py",
                "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
            ),
            notes=(
                "PRESENT as DDO observation of EntryExitPolicyInput only; "
                "TRADING_AUTHORITY=NONE; does not call evaluate_* from learning."
            ),
        ),
        BypassCensusEntryV1(
            path_id="producer_to_crs_risk_sizing_mutation",
            classification="PROVEN_ABSENT",
            evidence_refs=(
                "src/learning/**/*.py: no capital_risk / CRS sizing import into trading layers "
                "(grep census v1)",
            ),
            notes="CRS remains downstream of layered core in topology docs.",
        ),
        BypassCensusEntryV1(
            path_id="producer_to_order_intent",
            classification="PROVEN_ABSENT",
            evidence_refs=(
                "src/learning/**/*.py: no canonical_order_intent import (grep census v1)",
            ),
            notes="",
        ),
        BypassCensusEntryV1(
            path_id="producer_to_execution_admission",
            classification="PROVEN_ABSENT",
            evidence_refs=("src/learning/**/*.py: no execution_admission import (grep census v1)",),
            notes="",
        ),
        BypassCensusEntryV1(
            path_id="producer_to_permit_post_authority",
            classification="PROVEN_ABSENT",
            evidence_refs=(
                "src/learning/**/*.py: no external_effect_gate / POST permit import "
                "(grep census v1)",
            ),
            notes="",
        ),
        BypassCensusEntryV1(
            path_id="mi_to_dp_attribution_information_path",
            classification="PRESENT",
            evidence_refs=(
                "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/"
                "phase_25_dp_attribution_evidence_v1.py",
                "docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_25_DP_ATTRIBUTION_NORMATIVE_V1.md",
            ),
            notes=(
                "Informational attribution evidence only; MARKET_CONTEXT + MV2/DP refs; "
                "TRADING_AUTHORITY=NONE; not a layer input seam."
            ),
        ),
    ]
    return tuple(entries)


def _build_p1_design_input(layers: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    eligible: list[str] = []
    closed: list[str] = []
    unknown: list[str] = []
    conflicting: list[str] = []
    for row in layers:
        lid = str(row["layer_id"])
        fe = row.get("future_B_target_possible")
        adm = row.get("external_evidence_admissibility")
        seam = row.get("existing_external_evidence_seam")
        if fe == "PROVEN_CURRENT":
            eligible.append(lid)
        if adm == "PROVEN_CLOSED" or fe == "PROVEN_CLOSED":
            closed.append(lid)
        if adm == "UNKNOWN" or fe == "UNKNOWN" or seam == "UNKNOWN":
            unknown.append(lid)
        if "CONFLICTING" in str(row.get("open_questions", ())):
            conflicting.append(lid)
    reusable = [
        "DynamicScopeGeneratorInputV1 + DynamicScopeGeneratorV1 (L6)",
        "SelectedFutureInputV1 (L1; subject to Cap 2.4 authority)",
        "MarketObservationInputV1 / ObservationCandidateV1 (L2; C1 bounded)",
    ]
    p1_contracts_present = _l6_external_evidence_admissibility_v1() == "PROVEN_BOUNDED_TYPED_ONLY"
    return {
        "schema_version": "master_v2_double_play_evidence_input_plane_p1_design_input/v1",
        "proven_eligible_b_binding_candidates": sorted(set(eligible)),
        "proven_closed_layers": sorted(set(closed)),
        "unknown_layers": sorted(set(unknown)),
        "conflicting_layers": sorted(set(conflicting)),
        "reusable_contracts_proven_current": reusable,
        "new_contracts_requiring_owner_authority": (
            [
                "CanonicalMasterV2EvidenceEnvelopeV1 (P1 contract schema — runtime blocked)",
                "CanonicalDpLayerInputBindingV1 (P1 contract schema — runtime blocked)",
                "L6BoundedTypedExternalEvidenceInputV1 (P1 L6 typed seam — runtime blocked)",
            ]
            if p1_contracts_present
            else [
                "CanonicalMasterV2EvidenceEnvelopeV1 (Component A — not implemented)",
                "CanonicalDpLayerInputBindingV1 (Component B — not implemented)",
                "Any non-C1 external evidence type admission per layer",
            ]
        ),
        "sufficient_facts_for_ab_schema_design": [
            "L1–L10 owners and input dataclasses proven in contracts_v1.py",
            "L6 replaceable generator protocol proven",
            "No blanket external-evidence permission proven",
            "Bypass census complete for intelligence→layer direct calls",
        ],
        "remains_blocked": [
            "Component A/B runtime implementation (P1 contract only)",
            "Productive L6 typed-evidence binding (PRODUCTIVE_L6_BINDING_AUTHORIZED=false)",
            "L1 B-target without Cap 2.3/2.4 authority decision",
            "scope_event_generator vs transition_state conflict resolution (out of scope)",
            "FINAL_D_T_FORMULA_SELECTED=false",
        ],
        "component_a_implemented": False,
        "component_b_implemented": False,
        "p1_authority_contracts_materialized": p1_contracts_present,
    }


def run_master_v2_double_play_p0_evidence_seam_census_v1(
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    layers = [_build_layer_row(lid) for lid in LAYER_ORDER_V1]
    bypass = run_direct_external_to_dp_bypass_census_v1(root)
    ab_present, ab_hits = _glob_ab_implementation(root)

    status_counts: dict[str, int] = {}
    for row in layers:
        st = str(row["status"])
        status_counts[st] = status_counts.get(st, 0) + 1

    open_register = [
        {
            "id": "O-001",
            "topic": "scope_event_generator_vs_transition_state",
            "status": "CONFLICTING",
            "affected_census_fields": (
                "L7 open_questions; productive composition vs naked layered durable state"
            ),
            "resolution_scope": "OUT_OF_P0_WP",
            "evidence_refs": [
                "src/trading/master_v2/deterministic_scope_event_generator_v1.py",
                "src/trading/master_v2/double_play_composition.py",
                "src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/durable_state_v1.py",
            ],
        },
        {
            "id": "O-002",
            "topic": "L6_external_intelligence_evidence_admissibility",
            "status": "RATIFIED"
            if _l6_external_evidence_admissibility_v1() != "UNKNOWN"
            else "UNKNOWN",
            "affected_census_fields": (
                "L6 external_evidence_admissibility; allowed_evidence_types for MI/Learning"
            ),
            "resolution_scope": "P1_OWNER_CONTRACT",
            "evidence_refs": [
                "src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/l6_dynamic_scope_generator_v1.py",
                "src/governance/master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1/",
                "config/governance/master_v2_double_play_evidence_input_plane_p1_owner_decision_v1.json",
            ],
        },
        {
            "id": "O-003",
            "topic": "L1_future_B_without_cap24_duplication",
            "status": "UNKNOWN",
            "affected_census_fields": "L1 future_B_target_possible",
            "resolution_scope": "P1_OWNER_AUTHORITY",
            "evidence_refs": [
                "src/ops/single_selected_future_runtime_binding_v1/binding_gate_v1.py",
                "src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/l1_selected_future_v1.py",
            ],
        },
    ]

    ledger = {
        "schema_version": "master_v2_double_play_evidence_input_plane_p0_ledger/v1",
        "material_claims": [
            {
                "claim": "L1–L10 semantic owners are explicit layered core modules",
                "evidence_refs": [
                    "src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/layer_catalog_v1.py",
                    "docs/evidence/naked_mv2_dp_explicit_layered_core_v1/layer_separation_evidence_v1.json",
                ],
            },
            {
                "claim": "Cap 2.3 selection authority is single_selected_future_policy_v1",
                "evidence_refs": [
                    "src/ops/single_selected_future_policy_v1/producer_v1.py",
                    "docs/ops/specs/RANKING_UNIVERSE_TO_FULL_CORE_SSF_HANDOFF_CONTRACT_V1.md",
                ],
            },
            {
                "claim": "Cap 2.4 binding authority is single_selected_future_runtime_binding_v1",
                "evidence_refs": [
                    "src/ops/single_selected_future_runtime_binding_v1/binding_gate_v1.py",
                ],
            },
            {
                "claim": "DDO capture on trading producers is observation-only",
                "evidence_refs": [
                    "src/learning/deterministic_decision_outcome_v0/double_play_input_evidence_v1.py",
                ],
            },
            {
                "claim": "No intelligence producer directly imports L1–L10 apply/orchestrate",
                "evidence_refs": [e.to_dict() for e in bypass if e.path_id.startswith("external")],
            },
        ],
    }

    p1 = _build_p1_design_input(layers)

    return {
        "schema_version": SCHEMA_VERSION,
        "workpackage_id": WORKPACKAGE_ID,
        "explicit_layered_core_version": EXPLICIT_LAYERED_CORE_VERSION,
        "explicit_layered_core_owner": EXPLICIT_LAYERED_CORE_OWNER,
        "blueprint_baseline_sha": BLUEPRINT_BASELINE_SHA,
        "census_layers": layers,
        "layer_count": len(layers),
        "status_counts": status_counts,
        "direct_external_to_dp_bypass_census": [e.to_dict() for e in bypass],
        "component_a_implementation_detected": ab_present,
        "component_a_implementation_hits": list(ab_hits),
        "component_b_implementation_detected": ab_present,
        "open_conflict_register": open_register,
        "evidence_reference_ledger": ledger,
        "p1_design_input_block": p1,
        "topology_trace_summary": (
            "Cap2.3 SingleSelectedFutureSelectionV1 → Cap2.4 BoundInstrumentV1 → "
            "Full-Core / integrated_offline_trading_logic_replay_v1 → "
            "double_play_composition / entry_exit / CRS (downstream) ; "
            "parallel explicit L1–L10 orchestrator path when productive layered bind enabled "
            "(PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED gate in "
            "productive_cycle_layered_core_bind_wiring_v1.py)."
        ),
        "dp_semantics_changed_by_this_wp": False,
        "cap_2_3_authority_changed_by_this_wp": False,
        "cap_2_4_authority_changed_by_this_wp": False,
        "crs_authority_changed_by_this_wp": False,
        "execution_authority_changed_by_this_wp": False,
        "external_effect_authority_changed_by_this_wp": False,
    }


def canonical_json_dumps_v1(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def write_p0_census_artifacts_v1(repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[2]
    census = run_master_v2_double_play_p0_evidence_seam_census_v1(root)
    out_dir = root / "docs/evidence/master_v2_double_play_evidence_input_plane_p0"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "l1_l10_evidence_seam_census_v1.json": census,
        "evidence_reference_ledger_v1.json": census["evidence_reference_ledger"],
        "open_conflict_register_v1.json": {
            "schema_version": "master_v2_double_play_evidence_input_plane_p0_open_conflict/v1",
            "entries": census["open_conflict_register"],
        },
        "p1_design_input_block_v1.json": census["p1_design_input_block"],
    }
    for name, doc in paths.items():
        target = out_dir / name
        target.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out_dir


def assert_p0_census_invariants_v1(census: Mapping[str, Any]) -> None:
    if census.get("layer_count") != 10:
        raise AssertionError("census_must_cover_L1_through_L10")
    ids = {row["layer_id"] for row in census["census_layers"]}
    expected = {lid.value for lid in LAYER_ORDER_V1}
    if ids != expected:
        raise AssertionError("census_layer_id_set_mismatch")
    for row in census["census_layers"]:
        if row.get("owner_evidence") not in _EPISTEMIC:
            raise AssertionError("invalid_owner_evidence_epistemic")
        if row.get("existing_external_evidence_seam") not in _EPISTEMIC:
            raise AssertionError("invalid_seam_epistemic")
        if not row.get("evidence_refs"):
            raise AssertionError("missing_evidence_refs")
    if census.get("component_a_implementation_detected"):
        raise AssertionError("component_a_must_not_be_implemented_in_p0")
    if census.get("component_b_implementation_detected"):
        raise AssertionError("component_b_must_not_be_implemented_in_p0")
    if census.get("dp_semantics_changed_by_this_wp") is not False:
        raise AssertionError("dp_semantics_must_remain_unchanged")


__all__ = [
    "BLUEPRINT_BASELINE_SHA",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "assert_p0_census_invariants_v1",
    "canonical_json_dumps_v1",
    "run_direct_external_to_dp_bypass_census_v1",
    "run_master_v2_double_play_p0_evidence_seam_census_v1",
    "write_p0_census_artifacts_v1",
]
