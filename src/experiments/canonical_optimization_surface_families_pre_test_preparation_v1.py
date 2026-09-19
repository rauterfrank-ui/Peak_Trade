"""Optimization surface family pre-test preparation v1 — matrix, isolation, TEST_ENTRY_GATE.

Research/proposal only. Does not authorize search, OOS, promotion, or productive mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    SURFACE_ID as F2_SURFACE_ID,
    SURFACE_OWNER_REF as F2_SURFACE_OWNER_REF,
    TARGET_FAMILY as F2_TARGET_FAMILY,
)
from src.experiments.canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1 import (
    SURFACE_ID as F5_FRESH_SURFACE_ID,
    SURFACE_OWNER_REF as F5_FRESH_SURFACE_OWNER_REF,
    TARGET_FAMILY as F5_FRESH_TARGET_FAMILY,
)
from src.experiments.canonical_f3_strategy_hyperparameter_optimizable_surface_exclusion_v1 import (
    GLOBAL_F3_OPTIMIZABLE_SURFACE_AUTHORIZED,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as F1_SURFACE_ID,
    SURFACE_OWNER_REF as F1_SURFACE_OWNER_REF,
    TARGET_FAMILY as F1_TARGET_FAMILY,
)
from src.experiments.canonical_optimizable_envelope_v1 import (
    RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION,
    OptimizableEnvelopeResolveRequestV1,
    build_authorized_surface_registry_v1,
    resolve_optimizable_envelope_v1,
)

SCHEMA_VERSION: Final[str] = "canonical_optimization_surface_families_pre_test_preparation_v1"
WORKPACKAGE_ID: Final[str] = "OPTIMIZATION_SURFACE_FAMILIES_PRE_TEST_PREPARATION_V1"
BOUND_ORIGIN_MAIN_SHA: Final[str] = "3abeffae801f2973408e8e613b1c03f903b08d0a"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/OPTIMIZATION_SURFACE_FAMILIES_PRE_TEST_PREPARATION_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/optimization_surface_families_pre_test_preparation_v1_decision_v1.json"
)

PRODUCTIVE_EFFECT: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
MV2_DOUBLE_PLAY_SOLE_TRADING_DECISION_AUTHORITY: Final[bool] = True
CORE_BOUNDARY_CHANGED: Final[bool] = False
TRADING_LOGIC_CHANGED: Final[bool] = False


class PreparationStatus(str, Enum):
    TEST_READY = "TEST_READY"
    TEST_READY_SHADOW_RESEARCH = "TEST_READY_SHADOW_RESEARCH"
    TEST_READY_PER_TOKEN_SHADOW_CALIBRATION_ONLY = "TEST_READY_PER_TOKEN_SHADOW_CALIBRATION_ONLY"
    EXCLUDED_BY_AUTHORITY_BOUNDARY = "EXCLUDED_BY_AUTHORITY_BOUNDARY"
    EXCLUDED = "EXCLUDED"
    EXCLUDED_AS_OPTIMIZATION_AXIS = "EXCLUDED_AS_OPTIMIZATION_AXIS"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
    CONSTITUTIONAL_NOT_OPTIMIZABLE = "CONSTITUTIONAL_NOT_OPTIMIZABLE"
    OWNER_DECISION_REQUIRED = "OWNER_DECISION_REQUIRED"


class ResearchTestEntryGateV1(str, Enum):
    PREREGISTERED_VOLATILITY_MAX_AGE_PARAMETER_RESEARCH_EXECUTION_V1 = (
        "PREREGISTERED_VOLATILITY_MAX_AGE_PARAMETER_RESEARCH_EXECUTION_V1"
    )
    DETERMINISTIC_F2_COST_GRID_IDENTITY_REPLAY_THEN_BOUNDED_SENSITIVITY_OOS_V1 = (
        "DETERMINISTIC_F2_COST_GRID_IDENTITY_REPLAY_THEN_BOUNDED_SENSITIVITY_OOS_V1"
    )
    SHADOW_PURE_STACK_NUMERIC_EVIDENCE_PACK_VALIDATION_V1 = (
        "SHADOW_PURE_STACK_NUMERIC_EVIDENCE_PACK_VALIDATION_V1"
    )
    SHADOW_PER_TOKEN_THRESHOLD_SENSITIVITY_V1 = "SHADOW_PER_TOKEN_THRESHOLD_SENSITIVITY_V1"
    UNKNOWN_FAIL_CLOSED = "UNKNOWN_FAIL_CLOSED"


_FAMILY_SET_CLOSED_ALLOWED_STATUSES: frozenset[PreparationStatus] = frozenset(
    {
        PreparationStatus.TEST_READY,
        PreparationStatus.TEST_READY_SHADOW_RESEARCH,
        PreparationStatus.TEST_READY_PER_TOKEN_SHADOW_CALIBRATION_ONLY,
        PreparationStatus.EXCLUDED_BY_AUTHORITY_BOUNDARY,
        PreparationStatus.EXCLUDED,
        PreparationStatus.EXCLUDED_AS_OPTIMIZATION_AXIS,
        PreparationStatus.DIAGNOSTIC_ONLY,
        PreparationStatus.CONSTITUTIONAL_NOT_OPTIMIZABLE,
    }
)


@dataclass(frozen=True)
class OptimizationSurfaceFamilyRecordV1:
    family_gate_id: str
    display_name: str
    preparation_status: PreparationStatus
    owner_refs: tuple[str, ...]
    parameter_domain_summary: str
    authority_boundary_summary: str
    existing_seam_refs: tuple[str, ...]
    isolation_requirements: tuple[str, ...]
    productive_effect: str
    unresolved_blocker: str | None
    authorized_surface_id: str | None
    test_entry_gate: ResearchTestEntryGateV1
    promotion_boundary: str
    instrument_reselection_forbidden: bool
    core_mutation_forbidden: bool


_FAMILY_RECORDS: tuple[OptimizationSurfaceFamilyRecordV1, ...] = (
    OptimizationSurfaceFamilyRecordV1(
        family_gate_id="F1",
        display_name="Volatility Numeric Max-Age",
        preparation_status=PreparationStatus.TEST_READY,
        owner_refs=(
            "src/experiments/canonical_m9_volatility_numeric_max_age_optimizable_surface_v1.py",
            "research.canonical_volatility_numeric_max_age_parameter_research_execution_v1",
            "src/trading/master_v2/canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1.py",
        ),
        parameter_domain_summary="Discrete operator-bound candidate_max_age_seconds",
        authority_boundary_summary=(
            "Envelope-authorized research optimization only; watchdog policy non-enforcing; "
            "no threshold selection or MV2 core mutation"
        ),
        existing_seam_refs=(
            "config/governance/optimizable_envelope/volatility_numeric_max_age_allowed_policy_domain_v1.json",
            "config/governance/optimizable_envelope/volatility_numeric_max_age_discrete_bounds_v1.json",
        ),
        isolation_requirements=(
            "distinct_surface_id",
            "distinct_envelope_identity",
            "distinct_candidate_domain",
            "canonical_experiment_identity",
            "research_only_no_promotion",
        ),
        productive_effect=PRODUCTIVE_EFFECT,
        unresolved_blocker=None,
        authorized_surface_id=F1_SURFACE_ID,
        test_entry_gate=ResearchTestEntryGateV1.PREREGISTERED_VOLATILITY_MAX_AGE_PARAMETER_RESEARCH_EXECUTION_V1,
        promotion_boundary="separate_governed_promotion_false",
        instrument_reselection_forbidden=True,
        core_mutation_forbidden=True,
    ),
    OptimizationSurfaceFamilyRecordV1(
        family_gate_id="F2",
        display_name="Research Backtest Fee/Slippage Cost Grid",
        preparation_status=PreparationStatus.TEST_READY,
        owner_refs=(
            "src/experiments/canonical_f2_research_backtest_cost_grid_optimizable_surface_v1.py",
            "src/experiments/canonical_f2_research_backtest_cost_grid_research_execution_v1.py",
            "src/backtest/parameter_sensitivity_v1.py",
        ),
        parameter_domain_summary="Discrete fee_bps x slippage_bps (Step29M operator-bound 3x3 grid)",
        authority_boundary_summary=(
            "Envelope-authorized research backtest costs only; funding not a grid axis; "
            "no productive config or execution authority"
        ),
        existing_seam_refs=(
            "config/ops/step29m_okx_inst_eth_usdt_perp_vol_breakout_v1_economic_evaluation_v1.json",
            "src/backtest/okx_eth_perp_research_cost_grid_v1_constants.py",
        ),
        isolation_requirements=(
            "distinct_surface_id",
            "distinct_envelope_identity",
            "distinct_mutable_candidate_state",
            "reproducible_execution_digest",
            "research_only_no_promotion",
        ),
        productive_effect=PRODUCTIVE_EFFECT,
        unresolved_blocker=None,
        authorized_surface_id=F2_SURFACE_ID,
        test_entry_gate=(
            ResearchTestEntryGateV1.DETERMINISTIC_F2_COST_GRID_IDENTITY_REPLAY_THEN_BOUNDED_SENSITIVITY_OOS_V1
        ),
        promotion_boundary="separate_governed_promotion_false",
        instrument_reselection_forbidden=True,
        core_mutation_forbidden=True,
    ),
    OptimizationSurfaceFamilyRecordV1(
        family_gate_id="F3",
        display_name="Strategy Hyperparameter Research",
        preparation_status=PreparationStatus.EXCLUDED_BY_AUTHORITY_BOUNDARY,
        owner_refs=(
            "src/backtest/parameter_sensitivity_v1.py",
            "src/backtest/strategy_signal_binding_v1.py",
            "src/trading/master_v2/naked_mv2_double_play_core_authority_hardening_v1.py",
        ),
        parameter_domain_summary="strategy.* axes (per-strategy external schema); not fee/slippage",
        authority_boundary_summary=(
            "Not in optimizable envelope registry; core-touch requires ten-key admission; "
            "optimizer must not override MV2+Double Play trading-decision semantics"
        ),
        existing_seam_refs=(
            "src/research/linear_evidence/parameter_sensitivity_productive_contract_v0.py",
        ),
        isolation_requirements=(
            "separate_surface_registration",
            "core_touch_admission_metadata",
            "no_parallel_trading_decision_authority",
            "constitutional_params_forbidden",
        ),
        productive_effect=PRODUCTIVE_EFFECT,
        unresolved_blocker="GLOBAL_SURFACE_NO_GO_OWNER_D4;NAMED_BINDING_REQUIRES_SEPARATE_OWNER_SCOPE",
        authorized_surface_id=None,
        test_entry_gate=ResearchTestEntryGateV1.UNKNOWN_FAIL_CLOSED,
        promotion_boundary="separate_governed_promotion_false",
        instrument_reselection_forbidden=True,
        core_mutation_forbidden=True,
    ),
    OptimizationSurfaceFamilyRecordV1(
        family_gate_id="F5-FRESH",
        display_name="Pure-Stack Input Freshness Numeric (shadow)",
        preparation_status=PreparationStatus.TEST_READY_SHADOW_RESEARCH,
        owner_refs=(
            "src/experiments/canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1.py",
            "src/ops/productive_pure_stack_numeric_policy_shadow_campaign_v1/f5_fresh_research_candidate_domain_constants_v1.py",
            "src/ops/productive_pure_stack_numeric_policy_shadow_campaign_v1/shadow_futures_input_freshness_age_collector_v1.py",
        ),
        parameter_domain_summary="OWNER_VALUE_FUTURES_INPUT_FRESHNESS_MAX_AGE_SECONDS (not F1 dedupe)",
        authority_boundary_summary=(
            "Shadow calibration protocol only; distinct from F1 volatility numeric max-age policy"
        ),
        existing_seam_refs=(
            "config/governance/optimizable_envelope/f5_fresh_futures_input_freshness_allowed_policy_domain_v1.json",
            "config/governance/f5_fresh_futures_input_freshness_optimizable_surface_owner_grant_v1.json",
        ),
        isolation_requirements=(
            "distinct_surface_id_from_F1_M9",
            "shadow_evidence_only",
            "no_productive_freshness_state_admission",
            "input_authority_false",
            "distinct_owner_token_from_F1",
        ),
        productive_effect=PRODUCTIVE_EFFECT,
        unresolved_blocker=None,
        authorized_surface_id=F5_FRESH_SURFACE_ID,
        test_entry_gate=ResearchTestEntryGateV1.SHADOW_PURE_STACK_NUMERIC_EVIDENCE_PACK_VALIDATION_V1,
        promotion_boundary="separate_governed_promotion_false",
        instrument_reselection_forbidden=True,
        core_mutation_forbidden=True,
    ),
    OptimizationSurfaceFamilyRecordV1(
        family_gate_id="F5-SURV",
        display_name="Pure-Stack Survival Limit Numerics",
        preparation_status=PreparationStatus.TEST_READY_PER_TOKEN_SHADOW_CALIBRATION_ONLY,
        owner_refs=("docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_PROTOCOL_V1.md",),
        parameter_domain_summary="Survival ratio, toxicity, leverage, liquidation buffer tokens",
        authority_boundary_summary="Must not become casually optimizable without explicit owner grant",
        existing_seam_refs=(
            "src/experiments/canonical_f5_shadow_per_token_calibration_test_entry_v1.py",
            "docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_CAMPAIGN_MANIFEST_V1.json",
        ),
        isolation_requirements=(
            "per_token_identity",
            "no_shared_optimizer_envelope",
            "shadow_calibration_only",
        ),
        productive_effect=PRODUCTIVE_EFFECT,
        unresolved_blocker=None,
        authorized_surface_id=None,
        test_entry_gate=ResearchTestEntryGateV1.SHADOW_PER_TOKEN_THRESHOLD_SENSITIVITY_V1,
        promotion_boundary="separate_governed_promotion_false",
        instrument_reselection_forbidden=True,
        core_mutation_forbidden=True,
    ),
    OptimizationSurfaceFamilyRecordV1(
        family_gate_id="F5-CAP",
        display_name="Pure-Stack Capital-Slot Numerics",
        preparation_status=PreparationStatus.TEST_READY_PER_TOKEN_SHADOW_CALIBRATION_ONLY,
        owner_refs=("docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_PROTOCOL_V1.md",),
        parameter_domain_summary="Capital slot profit step, vol floors, opportunity score floors",
        authority_boundary_summary="Must not become casually optimizable without explicit owner grant",
        existing_seam_refs=(
            "src/experiments/canonical_f5_shadow_per_token_calibration_test_entry_v1.py",
            "docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_CAMPAIGN_MANIFEST_V1.json",
        ),
        isolation_requirements=(
            "per_token_identity",
            "no_shared_optimizer_envelope",
            "shadow_calibration_only",
        ),
        productive_effect=PRODUCTIVE_EFFECT,
        unresolved_blocker=None,
        authorized_surface_id=None,
        test_entry_gate=ResearchTestEntryGateV1.SHADOW_PER_TOKEN_THRESHOLD_SENSITIVITY_V1,
        promotion_boundary="separate_governed_promotion_false",
        instrument_reselection_forbidden=True,
        core_mutation_forbidden=True,
    ),
    OptimizationSurfaceFamilyRecordV1(
        family_gate_id="F4-OPTUNA",
        display_name="Optuna / Bayesian Advanced Search",
        preparation_status=PreparationStatus.EXCLUDED,
        owner_refs=("docs/ops/specs/CANONICAL_ADVANCED_SEARCH_V1.md",),
        parameter_domain_summary="Search method vocabulary only",
        authority_boundary_summary="No CURRENT owner-authorized optimizable envelope",
        existing_seam_refs=(),
        isolation_requirements=("not_a_parameter_family_surface",),
        productive_effect=PRODUCTIVE_EFFECT,
        unresolved_blocker="EXCLUDED_UNLESS_FUTURE_ENVELOPE_OWNER_GRANT",
        authorized_surface_id=None,
        test_entry_gate=ResearchTestEntryGateV1.UNKNOWN_FAIL_CLOSED,
        promotion_boundary="separate_governed_promotion_false",
        instrument_reselection_forbidden=True,
        core_mutation_forbidden=True,
    ),
    OptimizationSurfaceFamilyRecordV1(
        family_gate_id="FUNDING-ONLY",
        display_name="Funding-Only Grid Axis",
        preparation_status=PreparationStatus.EXCLUDED_AS_OPTIMIZATION_AXIS,
        owner_refs=("src/backtest/cost_config_v0.py",),
        parameter_domain_summary="Funding rate parameters as sole optimization axis",
        authority_boundary_summary="Explicit F2 non-goal; diagnostic binding only elsewhere",
        existing_seam_refs=(),
        isolation_requirements=("not_in_F2_envelope_domain",),
        productive_effect=PRODUCTIVE_EFFECT,
        unresolved_blocker="EXCLUDED_BY_F2_NORMATIVE_NON_GOALS",
        authorized_surface_id=None,
        test_entry_gate=ResearchTestEntryGateV1.UNKNOWN_FAIL_CLOSED,
        promotion_boundary="separate_governed_promotion_false",
        instrument_reselection_forbidden=True,
        core_mutation_forbidden=True,
    ),
    OptimizationSurfaceFamilyRecordV1(
        family_gate_id="OLS-DIAG",
        display_name="OLS / signal_scale Diagnostic",
        preparation_status=PreparationStatus.DIAGNOSTIC_ONLY,
        owner_refs=(
            "src/research/linear_evidence/parameter_sensitivity_productive_contract_v0.py",
        ),
        parameter_domain_summary="signal_scale diagnostic_only",
        authority_boundary_summary="DIAGNOSTIC_ONLY_PARAMETERS; variation forbidden in productive contract",
        existing_seam_refs=(),
        isolation_requirements=("diagnostic_only",),
        productive_effect=PRODUCTIVE_EFFECT,
        unresolved_blocker="EXCLUDED_DIAGNOSTIC_ONLY",
        authorized_surface_id=None,
        test_entry_gate=ResearchTestEntryGateV1.UNKNOWN_FAIL_CLOSED,
        promotion_boundary="separate_governed_promotion_false",
        instrument_reselection_forbidden=True,
        core_mutation_forbidden=True,
    ),
    OptimizationSurfaceFamilyRecordV1(
        family_gate_id="RISK-SIZE",
        display_name="Risk / Sizing Parameter Grid",
        preparation_status=PreparationStatus.CONSTITUTIONAL_NOT_OPTIMIZABLE,
        owner_refs=("src/backtest/parameter_sensitivity_v1.py",),
        parameter_domain_summary="risk.risk_per_trade cfg path",
        authority_boundary_summary="Not in F2 allowed calibratable parameters; no envelope",
        existing_seam_refs=(),
        isolation_requirements=("not_in_current_authorized_surfaces",),
        productive_effect=PRODUCTIVE_EFFECT,
        unresolved_blocker="EXCLUDED_RISK_SIZING_NOT_ENVELOPE_AUTHORIZED",
        authorized_surface_id=None,
        test_entry_gate=ResearchTestEntryGateV1.UNKNOWN_FAIL_CLOSED,
        promotion_boundary="separate_governed_promotion_false",
        instrument_reselection_forbidden=True,
        core_mutation_forbidden=True,
    ),
    OptimizationSurfaceFamilyRecordV1(
        family_gate_id="META-M4-M8",
        display_name="Optimization Universe / Meta Replay Plane",
        preparation_status=PreparationStatus.EXCLUDED,
        owner_refs=(
            "src/experiments/canonical_optimization_universe_v1.py",
            "docs/ops/specs/OPTIMIZATION_META_M8_DETERMINISTIC_MULTI_CYCLE_OFFLINE_REPLAY_NORMATIVE_V1.md",
        ),
        parameter_domain_summary="Evidence identity and M1-M8 orchestration (not parameter domains)",
        authority_boundary_summary="Infrastructure plane; does not authorize parameter optimization",
        existing_seam_refs=(),
        isolation_requirements=("meta_plane_not_parameter_family",),
        productive_effect=PRODUCTIVE_EFFECT,
        unresolved_blocker="EXCLUDED_INFRASTRUCTURE_NOT_PARAMETER_FAMILY",
        authorized_surface_id=None,
        test_entry_gate=ResearchTestEntryGateV1.UNKNOWN_FAIL_CLOSED,
        promotion_boundary="separate_governed_promotion_false",
        instrument_reselection_forbidden=True,
        core_mutation_forbidden=True,
    ),
)


def optimization_surface_family_records_v1() -> tuple[OptimizationSurfaceFamilyRecordV1, ...]:
    return _FAMILY_RECORDS


def build_optimization_surface_family_matrix_v1() -> Mapping[str, Any]:
    rows = []
    for record in _FAMILY_RECORDS:
        rows.append(
            {
                "family_gate_id": record.family_gate_id,
                "display_name": record.display_name,
                "preparation_status": record.preparation_status.value,
                "owner_refs": list(record.owner_refs),
                "parameter_domain_summary": record.parameter_domain_summary,
                "authority_boundary_summary": record.authority_boundary_summary,
                "existing_seam_refs": list(record.existing_seam_refs),
                "isolation_requirements": list(record.isolation_requirements),
                "productive_effect": record.productive_effect,
                "unresolved_blocker": record.unresolved_blocker,
                "authorized_surface_id": record.authorized_surface_id,
                "test_entry_gate": record.test_entry_gate.value,
                "promotion_boundary": record.promotion_boundary,
                "instrument_reselection_forbidden": record.instrument_reselection_forbidden,
                "core_mutation_forbidden": record.core_mutation_forbidden,
            }
        )
    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "workpackage_id": WORKPACKAGE_ID,
            "bound_origin_main_sha": BOUND_ORIGIN_MAIN_SHA,
            "productive_effect": PRODUCTIVE_EFFECT,
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
            "mv2_double_play_sole_trading_decision_authority": (
                MV2_DOUBLE_PLAY_SOLE_TRADING_DECISION_AUTHORITY
            ),
            "core_boundary_changed": CORE_BOUNDARY_CHANGED,
            "trading_logic_changed": TRADING_LOGIC_CHANGED,
            "families": rows,
        }
    )


def list_test_ready_surface_ids_v1() -> tuple[str, ...]:
    return tuple(
        record.authorized_surface_id
        for record in _FAMILY_RECORDS
        if record.preparation_status == PreparationStatus.TEST_READY
        and record.authorized_surface_id is not None
    )


def list_authorized_optimization_surface_ids_v1() -> tuple[str, ...]:
    return tuple(
        record.authorized_surface_id
        for record in _FAMILY_RECORDS
        if record.authorized_surface_id is not None
        and record.preparation_status
        in (
            PreparationStatus.TEST_READY,
            PreparationStatus.TEST_READY_SHADOW_RESEARCH,
        )
    )


def list_owner_decision_required_family_gate_ids_v1() -> tuple[str, ...]:
    return tuple(
        record.family_gate_id
        for record in _FAMILY_RECORDS
        if record.preparation_status == PreparationStatus.OWNER_DECISION_REQUIRED
    )


def list_excluded_family_gate_ids_v1() -> tuple[str, ...]:
    return tuple(
        record.family_gate_id
        for record in _FAMILY_RECORDS
        if record.preparation_status
        in (
            PreparationStatus.EXCLUDED,
            PreparationStatus.EXCLUDED_BY_AUTHORITY_BOUNDARY,
            PreparationStatus.EXCLUDED_AS_OPTIMIZATION_AXIS,
            PreparationStatus.DIAGNOSTIC_ONLY,
            PreparationStatus.CONSTITUTIONAL_NOT_OPTIMIZABLE,
        )
    )


def list_unclassified_current_family_gate_ids_v1() -> tuple[str, ...]:
    return tuple(
        record.family_gate_id
        for record in _FAMILY_RECORDS
        if record.preparation_status not in _FAMILY_SET_CLOSED_ALLOWED_STATUSES
    )


def assert_family_set_closed_v1() -> None:
    unclassified = list_unclassified_current_family_gate_ids_v1()
    if unclassified:
        raise ValueError(f"family_set_not_closed:{','.join(unclassified)}")
    if not GLOBAL_F3_OPTIMIZABLE_SURFACE_AUTHORIZED:
        f3 = next(r for r in _FAMILY_RECORDS if r.family_gate_id == "F3")
        if f3.preparation_status != PreparationStatus.EXCLUDED_BY_AUTHORITY_BOUNDARY:
            raise ValueError("f3_must_be_excluded_by_authority_boundary")


def verify_test_ready_cross_surface_isolation_v1() -> Mapping[str, Any]:
    """Prove resolver admission and isolation for all authorized envelope surfaces."""
    registry = build_authorized_surface_registry_v1()
    authorized = set(registry["authorized_surface_ids"])
    expected = set(list_authorized_optimization_surface_ids_v1())
    if authorized != expected:
        raise ValueError(
            f"authorized_registry_drift:expected={sorted(expected)} registry={sorted(authorized)}"
        )

    resolved = {
        sid: resolve_optimizable_envelope_v1(OptimizableEnvelopeResolveRequestV1(surface_id=sid))
        for sid in sorted(authorized)
    }
    identities = [item["envelope_identity"] for item in resolved.values()]
    if len(set(identities)) != len(identities):
        raise ValueError("envelope_identity_collision")

    families = {
        F1_SURFACE_ID: F1_TARGET_FAMILY,
        F2_SURFACE_ID: F2_TARGET_FAMILY,
        F5_FRESH_SURFACE_ID: F5_FRESH_TARGET_FAMILY,
    }
    owners = {
        F1_SURFACE_ID: F1_SURFACE_OWNER_REF,
        F2_SURFACE_ID: F2_SURFACE_OWNER_REF,
        F5_FRESH_SURFACE_ID: F5_FRESH_SURFACE_OWNER_REF,
    }
    for sid, result in resolved.items():
        if result["resolution"] != RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION:
            raise ValueError(f"surface_not_authorized:{sid}")

    owner_values = set(owners.values())
    family_values = set(families.values())
    if len(owner_values) != len(owners):
        raise ValueError("surface_owner_collision")
    if len(family_values) != len(families):
        raise ValueError("target_family_collision")

    return MappingProxyType(
        {
            "isolation_proven": True,
            "authorized_surface_ids": tuple(sorted(authorized)),
            "envelope_identities": {
                sid: resolved[sid]["envelope_identity"] for sid in sorted(authorized)
            },
            "productive_effect": PRODUCTIVE_EFFECT,
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        }
    )


def assert_f3_preparation_fail_closed_v1() -> None:
    assert_f3_excluded_by_authority_boundary_v1()


def assert_f3_excluded_by_authority_boundary_v1() -> None:
    record = next(r for r in _FAMILY_RECORDS if r.family_gate_id == "F3")
    if record.preparation_status != PreparationStatus.EXCLUDED_BY_AUTHORITY_BOUNDARY:
        raise ValueError("f3_must_be_excluded_by_authority_boundary")
    if record.authorized_surface_id is not None:
        raise ValueError("f3_must_not_have_authorized_surface")
    if GLOBAL_F3_OPTIMIZABLE_SURFACE_AUTHORIZED:
        raise ValueError("global_f3_must_remain_unauthorized")


def f5_subfamily_status_v1() -> Mapping[str, str]:
    return MappingProxyType(
        {
            row.family_gate_id: row.preparation_status.value
            for row in _FAMILY_RECORDS
            if row.family_gate_id.startswith("F5")
        }
    )


def build_preparation_status_summary_v1() -> Mapping[str, Any]:
    return MappingProxyType(
        {
            "f1_status": next(
                r for r in _FAMILY_RECORDS if r.family_gate_id == "F1"
            ).preparation_status.value,
            "f2_status": next(
                r for r in _FAMILY_RECORDS if r.family_gate_id == "F2"
            ).preparation_status.value,
            "f3_status": next(
                r for r in _FAMILY_RECORDS if r.family_gate_id == "F3"
            ).preparation_status.value,
            "f5_subfamily_status": dict(f5_subfamily_status_v1()),
            "f5_fresh_status": next(
                r for r in _FAMILY_RECORDS if r.family_gate_id == "F5-FRESH"
            ).preparation_status.value,
            "test_ready_surface_ids": list(list_test_ready_surface_ids_v1()),
            "authorized_optimization_surface_ids": list(
                list_authorized_optimization_surface_ids_v1()
            ),
            "owner_decision_required": list(list_owner_decision_required_family_gate_ids_v1()),
            "excluded_surfaces": list(list_excluded_family_gate_ids_v1()),
            "unclassified_families": list(list_unclassified_current_family_gate_ids_v1()),
            "family_set_closed": len(list_unclassified_current_family_gate_ids_v1()) == 0,
        }
    )


__all__ = [
    "BOUND_ORIGIN_MAIN_SHA",
    "CORE_BOUNDARY_CHANGED",
    "DECISION_CONFIG",
    "EXTERNAL_EFFECT_AUTHORIZED",
    "MV2_DOUBLE_PLAY_SOLE_TRADING_DECISION_AUTHORITY",
    "NORMATIVE_SPEC",
    "PRODUCTIVE_EFFECT",
    "PreparationStatus",
    "OptimizationSurfaceFamilyRecordV1",
    "SCHEMA_VERSION",
    "TRADING_LOGIC_CHANGED",
    "ResearchTestEntryGateV1",
    "WORKPACKAGE_ID",
    "assert_f3_excluded_by_authority_boundary_v1",
    "assert_f3_preparation_fail_closed_v1",
    "assert_family_set_closed_v1",
    "build_optimization_surface_family_matrix_v1",
    "build_preparation_status_summary_v1",
    "f5_subfamily_status_v1",
    "list_authorized_optimization_surface_ids_v1",
    "list_excluded_family_gate_ids_v1",
    "list_owner_decision_required_family_gate_ids_v1",
    "list_test_ready_surface_ids_v1",
    "list_unclassified_current_family_gate_ids_v1",
    "optimization_surface_family_records_v1",
    "verify_test_ready_cross_surface_isolation_v1",
]
