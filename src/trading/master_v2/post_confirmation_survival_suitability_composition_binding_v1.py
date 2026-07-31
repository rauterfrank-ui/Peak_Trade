"""C4 — Post-Confirmation Survival / Suitability / Composition Binding V1.

Capability: POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_V1

Productive binding owner (call-graph):
  ``integrated_offline_trading_logic_replay_v1.run_integrated_offline_trading_logic_replay_v1``

This module owns C4 authority markers, downstream confirmation non-authority
guards, and assessment-identity binding asserts. It does **not** redefine
Survival / Suitability / Composition semantics or introduce a new status taxonomy.

Authority chain (unchanged productive path):
  C1 Observation Acceptance
  → C2 Confirmation Progress
  → C3 DirectionalAssessmentV1.status
  → Survival (domain-only)
  → Suitability (domain-only)
  → Composition (sole CONFIRMED admissibility + side selection)
  → Double-Play State
  → Entry/Exit

Owner decisions (immutable for this capability):
  COMPOSITION_REMAINS_SOLE_CONFIRMED_ADMISSIBILITY_GATE=true
  SURVIVAL_CONFIRMED_EARLY_GATE=false
  SUITABILITY_CONFIRMED_EARLY_GATE=false
  SURVIVAL_SEMANTICS_CHANGE=false
  SUITABILITY_SEMANTICS_CHANGE=false
  COMPOSITION_SEMANTICS_CHANGE=false
  DOWNSTREAM_CONTRACT_CHANGE=false

C4 has no new persistent state carrier. DirectionalConfirmationSideStateCarrierV1
remains caller-owned and Bull/Bear-isolated via C3.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable, Optional, Sequence, Set

from trading.master_v2.directional_assessment_v1 import (
    DirectionalAssessmentSide,
    DirectionalAssessmentV1,
)
from trading.master_v2.double_play_composition_matrix_v1 import DoublePlayCompositionInputV1
from trading.master_v2.suitability_binding_v1 import SuitabilityResultV1
from trading.master_v2.survival_assessment_v1 import SurvivalResultV1

POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_CAPABILITY_ID = (
    "POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_V1"
)
POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_COMPONENT = (
    "PostConfirmationSurvivalSuitabilityCompositionBindingV1"
)
POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_PURITY = "PURE_DETERMINISTIC_NO_IO"

COMPOSITION_REMAINS_SOLE_CONFIRMED_ADMISSIBILITY_GATE = True
SURVIVAL_CONFIRMED_EARLY_GATE = False
SUITABILITY_CONFIRMED_EARLY_GATE = False
SURVIVAL_SEMANTICS_CHANGE = False
SUITABILITY_SEMANTICS_CHANGE = False
COMPOSITION_SEMANTICS_CHANGE = False
DOWNSTREAM_CONTRACT_CHANGE = False
C4_INTRODUCES_PERSISTENT_STATE_CARRIER = False
PARALLEL_CONFIRMATION_AUTHORITY_FORBIDDEN = True
RUNTIME_WIRING_INCLUDED = False
PARAMETER_CHANGE_INCLUDED = False
VOLATILITY_CHANGE_INCLUDED = False
READY_FOR_C5 = False
READY_FOR_RUNTIME_ACTIVATION = False
READY_FOR_PARAMETER_RESEARCH = False
PROMOTION_AUTHORITY = False

# Forbidden confirmation authorities downstream of C3 (Survival/Suitability/Composition
# and productive orchestrator bindings must not call these).
_FORBIDDEN_DOWNSTREAM_CONFIRMATION_CALLS: frozenset[str] = frozenset(
    {
        "commit_observation_acceptance_v1",
        "evaluate_confirmation_progress_v1",
        "map_confirmation_assessment_state_to_directional_status_v1",
        "evaluate_directional_assessment_v1",
        "evaluate_directional_assessment_with_confirmation_progress_v1",
        "evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1",
        "project_directional_confirmation_state_from_assessments_v1",
        "_legacy_project_directional_confirmation_state_from_assessments_v1_quarantined",
    }
)

_FORBIDDEN_SCENARIO_LEGACY_IMPORT_MODULES: frozenset[str] = frozenset(
    {
        "double_play_survival",
        "double_play_suitability",
        "double_play_composition",
        "survival_suitability_scenario_binding_adapter_v0",
    }
)

_PRODUCTIVE_C4_MODULES_RELATIVE: tuple[str, ...] = (
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
    "src/trading/master_v2/survival_assessment_v1.py",
    "src/trading/master_v2/suitability_binding_v1.py",
    "src/trading/master_v2/double_play_composition_matrix_v1.py",
    "src/backtest/mv2_research_wiring_v1.py",
)


class PostC3DownstreamConfirmationAuthorityErrorV1(ValueError):
    """Raised when a post-C3 surface usurps confirmation authority."""


def assert_post_c3_downstream_confirmation_non_authority_v1(
    *,
    confirmation_recompute_enabled: bool = False,
    parallel_confirmation_authority_enabled: bool = False,
    survival_confirmed_early_gate_enabled: bool = False,
    suitability_confirmed_early_gate_enabled: bool = False,
) -> None:
    """Fail-closed runtime guard: post-C3 surfaces must not own confirmation."""
    if not COMPOSITION_REMAINS_SOLE_CONFIRMED_ADMISSIBILITY_GATE:
        raise PostC3DownstreamConfirmationAuthorityErrorV1(
            "COMPOSITION_SOLE_CONFIRMED_ADMISSIBILITY_GATE_DRIFT"
        )
    if SURVIVAL_CONFIRMED_EARLY_GATE or survival_confirmed_early_gate_enabled:
        raise PostC3DownstreamConfirmationAuthorityErrorV1(
            "SURVIVAL_CONFIRMED_EARLY_GATE_FORBIDDEN"
        )
    if SUITABILITY_CONFIRMED_EARLY_GATE or suitability_confirmed_early_gate_enabled:
        raise PostC3DownstreamConfirmationAuthorityErrorV1(
            "SUITABILITY_CONFIRMED_EARLY_GATE_FORBIDDEN"
        )
    if confirmation_recompute_enabled:
        raise PostC3DownstreamConfirmationAuthorityErrorV1(
            "DOWNSTREAM_CONFIRMATION_RECOMPUTATION_FORBIDDEN"
        )
    if parallel_confirmation_authority_enabled or not PARALLEL_CONFIRMATION_AUTHORITY_FORBIDDEN:
        raise PostC3DownstreamConfirmationAuthorityErrorV1(
            "PARALLEL_CONFIRMATION_AUTHORITY_FORBIDDEN"
        )
    if C4_INTRODUCES_PERSISTENT_STATE_CARRIER:
        raise PostC3DownstreamConfirmationAuthorityErrorV1("C4_PERSISTENT_STATE_CARRIER_FORBIDDEN")


def assert_c4_c3_assessment_identity_binding_v1(
    *,
    bull_assessment: DirectionalAssessmentV1,
    bear_assessment: DirectionalAssessmentV1,
    bull_survival: SurvivalResultV1,
    bear_survival: SurvivalResultV1,
    bull_suitability: SuitabilityResultV1,
    bear_suitability: SuitabilityResultV1,
    composition_input: DoublePlayCompositionInputV1,
    trading_epoch: int,
) -> None:
    """Runtime binding: Survival/Suitability/Composition consume exact C3 assessments."""
    if bull_assessment.side is not DirectionalAssessmentSide.LONG:
        raise PostC3DownstreamConfirmationAuthorityErrorV1("C4_BULL_SIDE_MISMATCH")
    if bear_assessment.side is not DirectionalAssessmentSide.SHORT:
        raise PostC3DownstreamConfirmationAuthorityErrorV1("C4_BEAR_SIDE_MISMATCH")
    if bull_assessment.trading_epoch != trading_epoch:
        raise PostC3DownstreamConfirmationAuthorityErrorV1("C4_BULL_TRADING_EPOCH_MISMATCH")
    if bear_assessment.trading_epoch != trading_epoch:
        raise PostC3DownstreamConfirmationAuthorityErrorV1("C4_BEAR_TRADING_EPOCH_MISMATCH")

    bull_surv_ref = bull_survival.directional_assessment_ref
    bear_surv_ref = bear_survival.directional_assessment_ref
    if bull_surv_ref.assessment_id != bull_assessment.assessment_id:
        raise PostC3DownstreamConfirmationAuthorityErrorV1("C4_BULL_SURVIVAL_ASSESSMENT_ID_DRIFT")
    if bull_surv_ref.semantic_digest != bull_assessment.semantic_digest:
        raise PostC3DownstreamConfirmationAuthorityErrorV1(
            "C4_BULL_SURVIVAL_ASSESSMENT_DIGEST_DRIFT"
        )
    if bull_surv_ref.side != bull_assessment.side:
        raise PostC3DownstreamConfirmationAuthorityErrorV1("C4_BULL_SURVIVAL_SIDE_DRIFT")
    if bear_surv_ref.assessment_id != bear_assessment.assessment_id:
        raise PostC3DownstreamConfirmationAuthorityErrorV1("C4_BEAR_SURVIVAL_ASSESSMENT_ID_DRIFT")
    if bear_surv_ref.semantic_digest != bear_assessment.semantic_digest:
        raise PostC3DownstreamConfirmationAuthorityErrorV1(
            "C4_BEAR_SURVIVAL_ASSESSMENT_DIGEST_DRIFT"
        )
    if bear_surv_ref.side != bear_assessment.side:
        raise PostC3DownstreamConfirmationAuthorityErrorV1("C4_BEAR_SURVIVAL_SIDE_DRIFT")

    bull_suit_ref = bull_suitability.directional_assessment_ref
    bear_suit_ref = bear_suitability.directional_assessment_ref
    if bull_suit_ref.assessment_id != bull_assessment.assessment_id:
        raise PostC3DownstreamConfirmationAuthorityErrorV1(
            "C4_BULL_SUITABILITY_ASSESSMENT_ID_DRIFT"
        )
    if bull_suit_ref.semantic_digest != bull_assessment.semantic_digest:
        raise PostC3DownstreamConfirmationAuthorityErrorV1(
            "C4_BULL_SUITABILITY_ASSESSMENT_DIGEST_DRIFT"
        )
    if bull_suit_ref.side != bull_assessment.side:
        raise PostC3DownstreamConfirmationAuthorityErrorV1("C4_BULL_SUITABILITY_SIDE_DRIFT")
    if bear_suit_ref.assessment_id != bear_assessment.assessment_id:
        raise PostC3DownstreamConfirmationAuthorityErrorV1(
            "C4_BEAR_SUITABILITY_ASSESSMENT_ID_DRIFT"
        )
    if bear_suit_ref.semantic_digest != bear_assessment.semantic_digest:
        raise PostC3DownstreamConfirmationAuthorityErrorV1(
            "C4_BEAR_SUITABILITY_ASSESSMENT_DIGEST_DRIFT"
        )
    if bear_suit_ref.side != bear_assessment.side:
        raise PostC3DownstreamConfirmationAuthorityErrorV1("C4_BEAR_SUITABILITY_SIDE_DRIFT")

    # Composition must receive the full C3 assessment objects (identity, not rebuild).
    if composition_input.bull_directional_assessment is not bull_assessment:
        if (
            composition_input.bull_directional_assessment.assessment_id
            != bull_assessment.assessment_id
            or composition_input.bull_directional_assessment.semantic_digest
            != bull_assessment.semantic_digest
        ):
            raise PostC3DownstreamConfirmationAuthorityErrorV1(
                "C4_COMPOSITION_BULL_ASSESSMENT_IDENTITY_DRIFT"
            )
    if composition_input.bear_directional_assessment is not bear_assessment:
        if (
            composition_input.bear_directional_assessment.assessment_id
            != bear_assessment.assessment_id
            or composition_input.bear_directional_assessment.semantic_digest
            != bear_assessment.semantic_digest
        ):
            raise PostC3DownstreamConfirmationAuthorityErrorV1(
                "C4_COMPOSITION_BEAR_ASSESSMENT_IDENTITY_DRIFT"
            )
    if composition_input.bull_directional_assessment.side is not DirectionalAssessmentSide.LONG:
        raise PostC3DownstreamConfirmationAuthorityErrorV1("C4_COMPOSITION_CROSS_SIDE_BULL")
    if composition_input.bear_directional_assessment.side is not DirectionalAssessmentSide.SHORT:
        raise PostC3DownstreamConfirmationAuthorityErrorV1("C4_COMPOSITION_CROSS_SIDE_BEAR")
    if composition_input.bull_survival_result is not bull_survival:
        if composition_input.bull_survival_result.survival_id != bull_survival.survival_id:
            raise PostC3DownstreamConfirmationAuthorityErrorV1("C4_COMPOSITION_BULL_SURVIVAL_DRIFT")
    if composition_input.bear_survival_result is not bear_survival:
        if composition_input.bear_survival_result.survival_id != bear_survival.survival_id:
            raise PostC3DownstreamConfirmationAuthorityErrorV1("C4_COMPOSITION_BEAR_SURVIVAL_DRIFT")
    if composition_input.bull_suitability_result is not bull_suitability:
        if (
            composition_input.bull_suitability_result.suitability_id
            != bull_suitability.suitability_id
        ):
            raise PostC3DownstreamConfirmationAuthorityErrorV1(
                "C4_COMPOSITION_BULL_SUITABILITY_DRIFT"
            )
    if composition_input.bear_suitability_result is not bear_suitability:
        if (
            composition_input.bear_suitability_result.suitability_id
            != bear_suitability.suitability_id
        ):
            raise PostC3DownstreamConfirmationAuthorityErrorV1(
                "C4_COMPOSITION_BEAR_SUITABILITY_DRIFT"
            )


def _call_names_from_ast(tree: ast.AST) -> Set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return names


def _imported_module_tails_from_ast(tree: ast.AST) -> Set[str]:
    tails: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            tails.add(node.module.rsplit(".", 1)[-1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                tails.add(alias.name.rsplit(".", 1)[-1])
    return tails


def collect_forbidden_downstream_confirmation_calls_v1(
    source: str,
    *,
    allow_calls: Optional[Iterable[str]] = None,
) -> Set[str]:
    """AST scan: return forbidden confirmation-authority calls present in source."""
    allowed = set(allow_calls or ())
    tree = ast.parse(source)
    found = _call_names_from_ast(tree) & _FORBIDDEN_DOWNSTREAM_CONFIRMATION_CALLS
    return found - allowed


def collect_forbidden_scenario_legacy_imports_v1(source: str) -> Set[str]:
    """AST scan: scenario/legacy confirmation-adjacent modules must stay quarantined."""
    tree = ast.parse(source)
    return _imported_module_tails_from_ast(tree) & _FORBIDDEN_SCENARIO_LEGACY_IMPORT_MODULES


def assert_productive_c4_modules_confirmation_non_authority_v1(
    *,
    repo_root: Path,
    modules: Optional[Sequence[str]] = None,
) -> None:
    """Static fail-closed scan of productive C4 call-graph modules."""
    relative_modules = tuple(modules) if modules is not None else _PRODUCTIVE_C4_MODULES_RELATIVE
    violations: list[str] = []
    for rel in relative_modules:
        path = repo_root / rel
        source = path.read_text(encoding="utf-8")
        # Orchestrator may call C3 evaluators (not forbidden there); Survival/Suitability/
        # Composition must not. Research may call C1 commit (observation authority only).
        if rel.endswith("integrated_offline_trading_logic_replay_v1.py"):
            allow = {
                "evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1",
            }
            forbidden = collect_forbidden_downstream_confirmation_calls_v1(
                source, allow_calls=allow
            )
            # Productive orchestrator must never call legacy DA evaluator or lossy projector.
            if "evaluate_directional_assessment_v1" in _call_names_from_ast(ast.parse(source)):
                forbidden.add("evaluate_directional_assessment_v1")
            if "project_directional_confirmation_state_from_assessments_v1" in forbidden:
                pass
        elif rel.endswith("mv2_research_wiring_v1.py"):
            allow = {"commit_observation_acceptance_v1"}
            forbidden = collect_forbidden_downstream_confirmation_calls_v1(
                source, allow_calls=allow
            )
            # Lossy projector may be defined but must raise; call sites outside the
            # quarantined definition are still forbidden. Definition itself is a FunctionDef.
            tree = ast.parse(source)
            call_names = _call_names_from_ast(tree)
            if "project_directional_confirmation_state_from_assessments_v1" in call_names:
                # Allowed only if the only references are the def + legacy quarantine helper.
                # A Call node named that way is a productive invocation → forbidden.
                forbidden.add("project_directional_confirmation_state_from_assessments_v1")
            if "evaluate_directional_assessment_v1" in call_names:
                forbidden.add("evaluate_directional_assessment_v1")
        else:
            forbidden = collect_forbidden_downstream_confirmation_calls_v1(source)
        legacy_imports = collect_forbidden_scenario_legacy_imports_v1(source)
        if forbidden:
            violations.append(f"{rel}:calls={sorted(forbidden)}")
        if legacy_imports:
            violations.append(f"{rel}:imports={sorted(legacy_imports)}")
    if violations:
        raise PostC3DownstreamConfirmationAuthorityErrorV1(
            "C4_DOWNSTREAM_CONFIRMATION_AUTHORITY_VIOLATION:" + ";".join(violations)
        )


__all__ = [
    "POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_CAPABILITY_ID",
    "POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_COMPONENT",
    "POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_PURITY",
    "COMPOSITION_REMAINS_SOLE_CONFIRMED_ADMISSIBILITY_GATE",
    "SURVIVAL_CONFIRMED_EARLY_GATE",
    "SUITABILITY_CONFIRMED_EARLY_GATE",
    "SURVIVAL_SEMANTICS_CHANGE",
    "SUITABILITY_SEMANTICS_CHANGE",
    "COMPOSITION_SEMANTICS_CHANGE",
    "DOWNSTREAM_CONTRACT_CHANGE",
    "C4_INTRODUCES_PERSISTENT_STATE_CARRIER",
    "PARALLEL_CONFIRMATION_AUTHORITY_FORBIDDEN",
    "RUNTIME_WIRING_INCLUDED",
    "PARAMETER_CHANGE_INCLUDED",
    "VOLATILITY_CHANGE_INCLUDED",
    "READY_FOR_C5",
    "READY_FOR_RUNTIME_ACTIVATION",
    "READY_FOR_PARAMETER_RESEARCH",
    "PROMOTION_AUTHORITY",
    "PostC3DownstreamConfirmationAuthorityErrorV1",
    "assert_post_c3_downstream_confirmation_non_authority_v1",
    "assert_c4_c3_assessment_identity_binding_v1",
    "collect_forbidden_downstream_confirmation_calls_v1",
    "collect_forbidden_scenario_legacy_imports_v1",
    "assert_productive_c4_modules_confirmation_non_authority_v1",
]
