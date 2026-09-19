# src/trading/master_v2/naked_mv2_double_play_core_authority_hardening_v1.py
"""
Naked Master V2 + Double Play core trading-decision authority hardening v1.

Outward-only: constants, ingress denials, and optimization-touch admission checks.
Does not wire into the integrated replay hot path. Does not mutate core semantics.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping, Optional, Tuple

from trading.master_v2.double_play_sole_authority_quarantine_v1 import (
    assert_path_cannot_escalate_to_compute_owner_v1,
)

NAKED_MV2_DOUBLE_PLAY_CORE_AUTHORITY_HARDENING_LAYER_VERSION = "v1"
NAKED_MV2_DOUBLE_PLAY_CORE_AUTHORITY_HARDENING_OWNER = (
    "trading.master_v2.naked_mv2_double_play_core_authority_hardening_v1"
)
PACKAGE_MARKER = "NAKED_MV2_DOUBLE_PLAY_CORE_AUTHORITY_HARDENING_V1=true"

TRADING_DECISION_AUTHORITY_OWNER = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1."
    "run_integrated_offline_trading_logic_replay_v1"
)
TERMINAL_DECISION_PRODUCER = (
    "trading.master_v2.double_play_entry_exit_policy_v0.evaluate_double_play_entry_exit_policy_v0"
)
TERMINAL_DECISION_FIELD = "CanonicalTradingDecisionEvidenceV1.decision_outcome"
CORE_END_MARKER = "IMMEDIATELY_AFTER_ENTRY_EXIT_POLICY_V0"

DOUBLE_PLAY_ROLE = "COMPOSITION_STATE_ENTRY_EXIT_WITHIN_JOINT_CORE"

DOWNSTREAM_REDECISION_AUTHORITY = "NONE"
LEARNING_TRADING_DECISION_AUTHORITY = "NONE"
OPTIMIZATION_TRADING_DECISION_AUTHORITY = "NONE"
META_LEARNING_TRADING_DECISION_AUTHORITY = "NONE"
AUTONOMY_TRADING_DECISION_AUTHORITY = "NONE"
EXECUTION_TRADING_DECISION_AUTHORITY = "NONE"
LEARNING_CORE_MUTATION_AUTHORITY = "NONE"
OPTIMIZATION_CORE_MUTATION_AUTHORITY = "NONE"

EXTERNAL_EFFECT_AUTHORIZED = False
SELF_PROMOTION_FORBIDDEN = True
RESEARCH_EXTERNAL_EFFECT_FORBIDDEN = True

# Not an acceptance gate for this WP (baseline drift; do not repair via hardening).
LEGACY_INTEGRATED_REPLAY_CALL_ORDER_ENTER_LONG_TEST_ACCEPTANCE = False
LONG_SHORT_REGRESSION_ROLE = "NON_INTERFERENCE_AND_ENTRY_EXIT_CONTRACT_OWNER_ONLY"

NAKED_CORE_COMPONENTS: Tuple[str, ...] = (
    "trading.master_v2.canonical_market_context_v1.bind_canonical_market_context_event",
    "trading.master_v2.canonical_scope_initialization_v1.initialize_canonical_scope",
    "trading.master_v2.deterministic_scope_event_generator_v1.generate_deterministic_scope_event",
    "trading.master_v2.single_lane_confirmation_activation_v1",
    "trading.master_v2.directional_assessment_confirmation_integration_v1",
    "trading.master_v2.survival_assessment_v1.evaluate_survival_assessment_v1",
    "trading.master_v2.suitability_binding_v1.evaluate_suitability_binding_v1",
    "trading.master_v2.double_play_composition_matrix_v1.evaluate_double_play_composition_matrix_v1",
    "trading.master_v2.double_play_state.transition_state",
    "trading.master_v2.double_play_state.update_dynamic_boundaries",
    "trading.master_v2.double_play_entry_exit_policy_v0.evaluate_double_play_entry_exit_policy_v0",
)

IMMUTABLE_CORE_SEMANTIC_SURFACES: Tuple[str, ...] = (
    "C1_OBSERVATION_ACCEPTANCE",
    "C2_CONFIRMATION_PROGRESS",
    "C3_DIRECTIONAL_ASSESSMENT_CONFIRMATION",
    "SCOPE_EVENT_GENERATOR",
    "SURVIVAL_ASSESSMENT",
    "SUITABILITY_BINDING",
    "COMPOSITION_MATRIX",
    "SIDESTATE_TRANSITION",
    "DYNAMIC_BOUNDARY_UPDATE",
    "ENTRY_EXIT_PRECEDENCE",
    "DECISION_OUTCOME_MAPPING",
)

LEGACY_PRODUCTIVE_DECISION_PATHS: Tuple[str, ...] = (
    "src.ops.double_play.specialists.evaluate_double_play",
    "trading.master_v2.offline_double_play_scenario_replay_v0."
    "run_offline_double_play_scenario_replay_v0",
)

REASON_INDEPENDENT_TRADING_DECISION_AUTHORITY = "independent_trading_decision_authority_forbidden"
REASON_PRODUCTIVE_CORE_MUTATION_FROM_RESEARCH = "productive_core_mutation_from_research_forbidden"
REASON_EXECUTION_REDECISION = "execution_redecision_authority_forbidden"
REASON_OPTIMIZATION_SURFACE_NOT_ADMITTED = "optimization_surface_not_admitted_fail_closed"
REASON_DOWNSTREAM_DECISION_OUTCOME_REWRITE = "downstream_decision_outcome_rewrite_forbidden"

_OPTIMIZATION_TOUCH_REQUIRED_KEYS: Tuple[str, ...] = (
    "target_parameter_or_component",
    "research_mutability_explicitly_authorized",
    "candidate_domain_bounds_owner_authorized",
    "research_only_execution",
    "no_independent_trading_decision_authority",
    "no_instrument_reranking_or_reselection",
    "candidate_not_productive_configuration",
    "evidence_not_promotion",
    "productive_binding_requires_separate_governance",
    "external_effect_authority_none",
)


class IngressSurfaceClass(str, Enum):
    LEARNING = "learning"
    OPTIMIZATION = "optimization"
    META_LEARNING = "meta_learning"
    AUTONOMY = "autonomy"
    LEGACY_DOUBLE_PLAY = "legacy_double_play"
    RESEARCH_SHADOW = "research_shadow"
    EXECUTION_DOWNSTREAM = "execution_downstream"
    CANONICAL_CORE = "canonical_core"


class IndependentTradingDecisionAuthorityError(RuntimeError):
    """Raised when a non-core surface claims productive trading decision authority."""


class ProductiveCoreMutationFromResearchError(RuntimeError):
    """Raised when research/optimization attempts productive core mutation without governance."""


class ExecutionRedecisionAuthorityError(RuntimeError):
    """Raised when execution/downstream claims trading redecision authority."""


class OptimizationSurfaceNotAdmittedError(RuntimeError):
    """Raised when a core-touching optimization surface lacks complete admission metadata."""


class DownstreamDecisionOutcomeRewriteError(RuntimeError):
    """Raised when downstream layers rewrite terminal trading decision outcomes."""


def deny_independent_trading_decision_authority_v1(
    *,
    surface_id: str,
    surface_class: IngressSurfaceClass,
    claims_trading_decision_authority: bool,
    claims_productive_path: bool = False,
) -> None:
    """Ingress firewall: block authority escalation; allow canonical core only."""
    if surface_class is IngressSurfaceClass.CANONICAL_CORE:
        if claims_trading_decision_authority and surface_id != TRADING_DECISION_AUTHORITY_OWNER:
            raise IndependentTradingDecisionAuthorityError(
                f"{REASON_INDEPENDENT_TRADING_DECISION_AUTHORITY}:{surface_id}"
            )
        return

    if claims_trading_decision_authority:
        raise IndependentTradingDecisionAuthorityError(
            f"{REASON_INDEPENDENT_TRADING_DECISION_AUTHORITY}:{surface_class.value}:{surface_id}"
        )

    if claims_productive_path and surface_class in {
        IngressSurfaceClass.LEARNING,
        IngressSurfaceClass.OPTIMIZATION,
        IngressSurfaceClass.META_LEARNING,
        IngressSurfaceClass.AUTONOMY,
        IngressSurfaceClass.RESEARCH_SHADOW,
    }:
        raise IndependentTradingDecisionAuthorityError(
            f"{REASON_INDEPENDENT_TRADING_DECISION_AUTHORITY}:productive_path:{surface_id}"
        )

    if surface_class is IngressSurfaceClass.LEGACY_DOUBLE_PLAY and (
        claims_trading_decision_authority or claims_productive_path
    ):
        assert_path_cannot_escalate_to_compute_owner_v1(
            path_id=surface_id,
            claimed_role="CANONICAL_COMPUTE_OWNER",
        )

    if (
        surface_class is IngressSurfaceClass.EXECUTION_DOWNSTREAM
        and claims_trading_decision_authority
    ):
        raise ExecutionRedecisionAuthorityError(f"{REASON_EXECUTION_REDECISION}:{surface_id}")


def deny_productive_core_mutation_from_research_v1(
    *,
    surface_id: str,
    surface_class: IngressSurfaceClass,
    targets_immutable_core_semantic: bool,
    productive_mutation_requested: bool,
    separate_governance_owner_go_present: bool,
) -> None:
    """Research candidate != productive core mutation unless explicit separate governance."""
    if not targets_immutable_core_semantic or not productive_mutation_requested:
        return
    if surface_class is IngressSurfaceClass.CANONICAL_CORE:
        return
    if separate_governance_owner_go_present:
        return
    raise ProductiveCoreMutationFromResearchError(
        f"{REASON_PRODUCTIVE_CORE_MUTATION_FROM_RESEARCH}:{surface_class.value}:{surface_id}"
    )


def assert_downstream_preserves_terminal_decision_outcome_v1(
    *,
    terminal_before: str,
    observed_after: str,
    layer_id: str,
) -> None:
    """Downstream may veto translation; must not rewrite terminal trading decision."""
    if terminal_before != observed_after:
        raise DownstreamDecisionOutcomeRewriteError(
            f"{REASON_DOWNSTREAM_DECISION_OUTCOME_REWRITE}:{layer_id}"
        )


def assert_optimization_core_touch_surface_admitted_v1(metadata: Mapping[str, Any]) -> None:
    """Future optimization firewall (F3 not built): unknown/partial => NOT_ADMITTED."""
    missing = [k for k in _OPTIMIZATION_TOUCH_REQUIRED_KEYS if k not in metadata]
    if missing:
        raise OptimizationSurfaceNotAdmittedError(
            f"{REASON_OPTIMIZATION_SURFACE_NOT_ADMITTED}:missing:{','.join(missing)}"
        )
    for key in _OPTIMIZATION_TOUCH_REQUIRED_KEYS:
        value = metadata.get(key)
        if value is None:
            raise OptimizationSurfaceNotAdmittedError(
                f"{REASON_OPTIMIZATION_SURFACE_NOT_ADMITTED}:null:{key}"
            )
        if value is False:
            raise OptimizationSurfaceNotAdmittedError(
                f"{REASON_OPTIMIZATION_SURFACE_NOT_ADMITTED}:false:{key}"
            )
        if isinstance(value, str) and value.strip().upper() in {"", "NONE", "FALSE", "UNKNOWN"}:
            raise OptimizationSurfaceNotAdmittedError(
                f"{REASON_OPTIMIZATION_SURFACE_NOT_ADMITTED}:token:{key}"
            )


def build_naked_mv2_double_play_core_authority_status_fields_v1() -> Mapping[str, str]:
    return {
        "PACKAGE_MARKER": PACKAGE_MARKER,
        "TRADING_DECISION_AUTHORITY_OWNER": TRADING_DECISION_AUTHORITY_OWNER,
        "TERMINAL_DECISION_PRODUCER": TERMINAL_DECISION_PRODUCER,
        "TERMINAL_DECISION_FIELD": TERMINAL_DECISION_FIELD,
        "CORE_END_MARKER": CORE_END_MARKER,
        "DOUBLE_PLAY_ROLE": DOUBLE_PLAY_ROLE,
        "DOWNSTREAM_REDECISION_AUTHORITY": DOWNSTREAM_REDECISION_AUTHORITY,
        "LEARNING_TRADING_DECISION_AUTHORITY": LEARNING_TRADING_DECISION_AUTHORITY,
        "OPTIMIZATION_TRADING_DECISION_AUTHORITY": OPTIMIZATION_TRADING_DECISION_AUTHORITY,
        "META_LEARNING_TRADING_DECISION_AUTHORITY": META_LEARNING_TRADING_DECISION_AUTHORITY,
        "AUTONOMY_TRADING_DECISION_AUTHORITY": AUTONOMY_TRADING_DECISION_AUTHORITY,
        "EXECUTION_TRADING_DECISION_AUTHORITY": EXECUTION_TRADING_DECISION_AUTHORITY,
        "LEARNING_CORE_MUTATION_AUTHORITY": LEARNING_CORE_MUTATION_AUTHORITY,
        "OPTIMIZATION_CORE_MUTATION_AUTHORITY": OPTIMIZATION_CORE_MUTATION_AUTHORITY,
        "EXTERNAL_EFFECT_AUTHORIZED": "false",
        "SELF_PROMOTION_FORBIDDEN": "true",
        "RESEARCH_EXTERNAL_EFFECT_FORBIDDEN": "true",
        "MV2_DOUBLE_PLAY_SOLE_TRADING_DECISION_AUTHORITY": "true",
        "CORE_BOUNDARY_UNCHANGED": "true",
        "RANKING_SELECTION_AUTHORITY_UNCHANGED": "true",
        "AUTONOMY_ORCHESTRATION_ONLY": "true",
        "LEGACY_INTEGRATED_REPLAY_CALL_ORDER_ENTER_LONG_TEST_ACCEPTANCE": "false",
        "LONG_SHORT_REGRESSION_ROLE": LONG_SHORT_REGRESSION_ROLE,
    }


def optimization_touch_admission_template_v1(
    *,
    target_parameter_or_component: str,
) -> Mapping[str, Any]:
    """Research-only template; productive binding still requires separate governance."""
    return {
        "target_parameter_or_component": target_parameter_or_component,
        "research_mutability_explicitly_authorized": True,
        "candidate_domain_bounds_owner_authorized": True,
        "research_only_execution": True,
        "no_independent_trading_decision_authority": True,
        "no_instrument_reranking_or_reselection": True,
        "candidate_not_productive_configuration": True,
        "evidence_not_promotion": True,
        "productive_binding_requires_separate_governance": True,
        "external_effect_authority_none": True,
    }


__all__ = [
    "AUTONOMY_TRADING_DECISION_AUTHORITY",
    "CORE_END_MARKER",
    "DOUBLE_PLAY_ROLE",
    "DOWNSTREAM_REDECISION_AUTHORITY",
    "DownstreamDecisionOutcomeRewriteError",
    "EXECUTION_TRADING_DECISION_AUTHORITY",
    "EXTERNAL_EFFECT_AUTHORIZED",
    "IMMUTABLE_CORE_SEMANTIC_SURFACES",
    "IndependentTradingDecisionAuthorityError",
    "IngressSurfaceClass",
    "LEARNING_CORE_MUTATION_AUTHORITY",
    "LEARNING_TRADING_DECISION_AUTHORITY",
    "LEGACY_INTEGRATED_REPLAY_CALL_ORDER_ENTER_LONG_TEST_ACCEPTANCE",
    "LEGACY_PRODUCTIVE_DECISION_PATHS",
    "LONG_SHORT_REGRESSION_ROLE",
    "META_LEARNING_TRADING_DECISION_AUTHORITY",
    "NAKED_CORE_COMPONENTS",
    "NAKED_MV2_DOUBLE_PLAY_CORE_AUTHORITY_HARDENING_LAYER_VERSION",
    "NAKED_MV2_DOUBLE_PLAY_CORE_AUTHORITY_HARDENING_OWNER",
    "OPTIMIZATION_CORE_MUTATION_AUTHORITY",
    "OPTIMIZATION_TRADING_DECISION_AUTHORITY",
    "OptimizationSurfaceNotAdmittedError",
    "PACKAGE_MARKER",
    "ProductiveCoreMutationFromResearchError",
    "RESEARCH_EXTERNAL_EFFECT_FORBIDDEN",
    "SELF_PROMOTION_FORBIDDEN",
    "TERMINAL_DECISION_FIELD",
    "TERMINAL_DECISION_PRODUCER",
    "TRADING_DECISION_AUTHORITY_OWNER",
    "assert_downstream_preserves_terminal_decision_outcome_v1",
    "assert_optimization_core_touch_surface_admitted_v1",
    "build_naked_mv2_double_play_core_authority_status_fields_v1",
    "deny_independent_trading_decision_authority_v1",
    "deny_productive_core_mutation_from_research_v1",
    "optimization_touch_admission_template_v1",
]
