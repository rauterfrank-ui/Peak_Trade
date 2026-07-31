"""Double-Play runtime typed volatility presence gate v1.

Closes productive Double-Play typed cutover: Scope / Boundary / Entry authority
may run only when CMC.canonical_volatility_estimate is present, validated, and
atomically synchronized with the legacy float. Reuses the existing typed
eligibility authority — never discards its result. Does not invent max-age,
global typed-only enforcement, a second estimator/adapter/validator, or
offline/research/scenario mutations.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Optional, Tuple

from trading.master_v2.canonical_market_context_v1 import (
    CanonicalMarketContextBindingOutcome,
    CanonicalMarketContextBlockReason,
    CanonicalMarketContextEligibilityV1,
    CanonicalMarketContextV1,
)
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    collect_typed_volatility_binding_block_reasons_v1,
    evaluate_typed_volatility_binding_eligibility_v1,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    LEGACY_ADAPTER_OWNER,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    DoublePlayEntryExitPolicyInputV0,
    DoublePlayEntryExitPolicyV0,
    EntryEligibility,
    EntryExitDirectionState,
    EntryExitPolicyDecisionV0,
    ExistingPositionSide,
    PositionState,
    PolicySignalV0,
    ReconciliationState,
    SafetyMode,
    TradingGate,
    compute_entry_exit_policy_input_digest,
    evaluate_double_play_entry_exit_policy_v0,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionChopGuardStatus,
    CompositionConflictStatus,
    CompositionDirectionState,
    CompositionSelectedSide,
    CompositionStatus,
    DoublePlayCompositionResultV1,
    PositionManagementContext,
    SuitabilityResultRefV1,
)
from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentSide
from trading.master_v2.suitability_binding_v1 import (
    DirectionalAssessmentRefV1,
    SuitabilityBindingStatus,
    SurvivalResultRefV1,
)
from trading.master_v2.survival_assessment_v1 import SurvivalAssessmentStatus
from trading.master_v2.canonical_market_context_v1 import (
    ClockTrustStatus,
    DataIntegrityStatus,
)

PACKAGE_MARKER = "MASTER_V2_DOUBLE_PLAY_RUNTIME_TYPED_VOLATILITY_PRESENCE_GATE_V1=true"

CAPABILITY_ID = "MASTER_V2_DOUBLE_PLAY_RUNTIME_TYPED_VOLATILITY_PRESENCE_GATE_V1"
CAPABILITY_VERSION = "double_play_runtime_typed_volatility_presence_gate/v1"
PRESENCE_GATE_OWNER = "trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1"
PRODUCTIVE_RUNTIME_CALLER_OWNER = (
    "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
    ".hardening_cycle_bridge_v2"
)

# Explicit gate reason code (deterministic, reconstructible).
TYPED_VOLATILITY_ESTIMATE_MISSING_REASON = "TYPED_VOLATILITY_ESTIMATE_MISSING"

DOUBLE_PLAY_TYPED_CUTOVER = True
GLOBAL_TYPED_ONLY_ENFORCEMENT = False
NUMERIC_MAX_AGE_DECIDED = False
NUMERIC_MAX_AGE_POLICY_CREATED = False
LIVE_AUTHORIZATION = False
HARD_STOP = True
SECOND_ESTIMATOR_CREATED = False
SECOND_ADAPTER_CREATED = False
SECOND_VALIDATOR_CREATED = False
LOCAL_TYPED_VALUE_EXTRACTION_CREATED = False
VOLATILITY_SEMANTICS_CHANGED = False
OFFLINE_REPLAY_LEGACY_DEFAULTS_UNCHANGED = True
RESEARCH_LEGACY_FALLBACKS_UNCHANGED = True
SCENARIO_REPLAY_UNCHANGED = True

SINGLE_ESTIMATOR_AUTHORITY_PRESERVED = True
SINGLE_VALIDATION_BOUNDARY_PRESERVED = True
SINGLE_TYPED_FLOAT_ADAPTER_AUTHORITY_PRESERVED = True
LEGACY_FLOAT_ADAPTATION_OWNER = LEGACY_ADAPTER_OWNER

_TYPED_BLOCK_REASONS: frozenset[CanonicalMarketContextBlockReason] = frozenset(
    {
        CanonicalMarketContextBlockReason.TYPED_VOLATILITY_ESTIMATE_MISSING,
        CanonicalMarketContextBlockReason.TYPED_VOLATILITY_ESTIMATE_INVALID,
        CanonicalMarketContextBlockReason.TYPED_VOLATILITY_LEGACY_FLOAT_MISMATCH,
    }
)


@dataclass(frozen=True)
class DoublePlayTypedVolatilityPresenceGateResultV1:
    """Presence-gate outcome; always carries the reused eligibility result."""

    eligibility: CanonicalMarketContextEligibilityV1
    typed_estimate_present: bool
    typed_validation_ok: bool
    typed_float_consistent: bool
    alpha_scope_entry_authority_allowed: bool
    exit_risk_safety_authority_preserved: bool
    block_reasons: Tuple[CanonicalMarketContextBlockReason, ...]
    reason_codes: Tuple[str, ...]
    double_play_typed_cutover: bool = DOUBLE_PLAY_TYPED_CUTOVER

    def to_dict(self) -> dict[str, Any]:
        return {
            "alpha_scope_entry_authority_allowed": self.alpha_scope_entry_authority_allowed,
            "block_reasons": [r.value for r in self.block_reasons],
            "double_play_typed_cutover": self.double_play_typed_cutover,
            "exit_risk_safety_authority_preserved": self.exit_risk_safety_authority_preserved,
            "reason_codes": list(self.reason_codes),
            "typed_estimate_present": self.typed_estimate_present,
            "typed_float_consistent": self.typed_float_consistent,
            "typed_validation_ok": self.typed_validation_ok,
            "eligibility_trading_decision_allowed": (self.eligibility.trading_decision_allowed),
            "eligibility_scope_confirmation_allowed": (self.eligibility.scope_confirmation_allowed),
            "eligibility_new_directional_exposure_allowed": (
                self.eligibility.new_directional_exposure_allowed
            ),
            "eligibility_observation_and_reconciliation_only": (
                self.eligibility.observation_and_reconciliation_only
            ),
        }


def evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
    context: CanonicalMarketContextV1,
    *,
    binding_outcome: CanonicalMarketContextBindingOutcome = (
        CanonicalMarketContextBindingOutcome.ACCEPTED
    ),
    eligibility: CanonicalMarketContextEligibilityV1 | None = None,
) -> DoublePlayTypedVolatilityPresenceGateResultV1:
    """Evaluate productive DP presence gate; reuse (never discard) eligibility."""
    typed_blocks = collect_typed_volatility_binding_block_reasons_v1(context)
    elig = eligibility
    if elig is None:
        elig = evaluate_typed_volatility_binding_eligibility_v1(
            context,
            binding_outcome=binding_outcome,
        )
    else:
        # Precomputed eligibility must already include typed blocks; do not drop it.
        missing = [b for b in typed_blocks if b not in elig.block_reasons]
        if missing:
            elig = evaluate_typed_volatility_binding_eligibility_v1(
                context,
                binding_outcome=binding_outcome,
            )

    typed_present = context.canonical_volatility_estimate is not None
    typed_invalid = (
        CanonicalMarketContextBlockReason.TYPED_VOLATILITY_ESTIMATE_INVALID in typed_blocks
    )
    typed_mismatch = (
        CanonicalMarketContextBlockReason.TYPED_VOLATILITY_LEGACY_FLOAT_MISMATCH in typed_blocks
    )
    typed_missing = (
        CanonicalMarketContextBlockReason.TYPED_VOLATILITY_ESTIMATE_MISSING in typed_blocks
    )

    alpha_ok = (
        typed_present
        and not typed_invalid
        and not typed_mismatch
        and not typed_missing
        and elig.scope_confirmation_allowed
        and elig.new_directional_exposure_allowed
        and not any(b in _TYPED_BLOCK_REASONS for b in elig.block_reasons)
    )

    reason_codes: list[str] = []
    if typed_missing or not typed_present:
        reason_codes.append(TYPED_VOLATILITY_ESTIMATE_MISSING_REASON)
    for block in typed_blocks:
        if block.value not in reason_codes:
            reason_codes.append(block.value)

    return DoublePlayTypedVolatilityPresenceGateResultV1(
        eligibility=elig,
        typed_estimate_present=typed_present,
        typed_validation_ok=typed_present and not typed_invalid,
        typed_float_consistent=typed_present and not typed_mismatch and not typed_invalid,
        alpha_scope_entry_authority_allowed=alpha_ok,
        exit_risk_safety_authority_preserved=True,
        block_reasons=tuple(typed_blocks),
        reason_codes=tuple(reason_codes),
    )


def demote_trading_gate_for_typed_presence_failure_v1(trading_gate: TradingGate) -> TradingGate:
    """Block new entry/increase; preserve EXIT_ONLY / BLOCKED for protection."""
    if trading_gate in (TradingGate.ENTRY_ALLOWED, TradingGate.INCREASE_ALLOWED):
        return TradingGate.EXIT_ONLY
    return trading_gate


def protection_authority_required_v1(
    *,
    position_state: PositionState,
    existing_position_side: ExistingPositionSide,
    reconciliation_state: ReconciliationState,
    safety_exit_signal: PolicySignalV0,
    hard_risk_reduction_signal: PolicySignalV0,
    scope_adverse_exit_signal: PolicySignalV0,
    profit_protection_signal: PolicySignalV0,
    time_exit_signal: PolicySignalV0,
    strategy_invalidation_signal: PolicySignalV0,
    safety_mode: SafetyMode,
) -> bool:
    """True when exit / risk / safety / reconcile authority must still run."""
    if safety_exit_signal.triggered or hard_risk_reduction_signal.triggered:
        return True
    if scope_adverse_exit_signal.triggered or profit_protection_signal.triggered:
        return True
    if time_exit_signal.triggered or strategy_invalidation_signal.triggered:
        return True
    if reconciliation_state is not ReconciliationState.RECONCILED:
        return True
    if position_state in (
        PositionState.OPEN_FULL,
        PositionState.OPEN_PARTIAL,
        PositionState.REDUCING_PARTIAL,
        PositionState.EXIT_PENDING,
        PositionState.SUBMISSION_UNKNOWN,
        PositionState.RECONCILIATION_REQUIRED,
    ):
        return True
    if existing_position_side is not ExistingPositionSide.NONE:
        return True
    if safety_mode in (SafetyMode.EXIT_ONLY, SafetyMode.BLOCKED, SafetyMode.DEGRADED):
        return True
    return False


def _non_authorizing_observe_composition_v1(
    *,
    instrument_id: str,
    trading_epoch: int,
    context_reference: str,
    previous_direction_state: CompositionDirectionState,
    position_management_context: PositionManagementContext,
) -> DoublePlayCompositionResultV1:
    """Minimal OBSERVE composition for protection-only entry/exit evaluation.

    Does not authorize scope/entry; carries identity only so safety/hard-risk
    precedence can run without inventing alpha authority.
    """
    empty = ""
    bull_a = DirectionalAssessmentRefV1(
        assessment_id="presence-gate-protection-bull",
        semantic_digest=empty,
        trading_epoch=trading_epoch,
        side=DirectionalAssessmentSide.LONG,
        status="observe",
    )
    bear_a = DirectionalAssessmentRefV1(
        assessment_id="presence-gate-protection-bear",
        semantic_digest=empty,
        trading_epoch=trading_epoch,
        side=DirectionalAssessmentSide.SHORT,
        status="observe",
    )
    bull_s = SurvivalResultRefV1(
        survival_id="presence-gate-protection-bull-survival",
        semantic_digest=empty,
        trading_epoch=trading_epoch,
        side=DirectionalAssessmentSide.LONG,
        status=SurvivalAssessmentStatus.BLOCKED,
    )
    bear_s = SurvivalResultRefV1(
        survival_id="presence-gate-protection-bear-survival",
        semantic_digest=empty,
        trading_epoch=trading_epoch,
        side=DirectionalAssessmentSide.SHORT,
        status=SurvivalAssessmentStatus.BLOCKED,
    )
    bull_u = SuitabilityResultRefV1(
        suitability_id="presence-gate-protection-bull-suit",
        semantic_digest=empty,
        trading_epoch=trading_epoch,
        side=DirectionalAssessmentSide.LONG,
        status=SuitabilityBindingStatus.BLOCKED,
    )
    bear_u = SuitabilityResultRefV1(
        suitability_id="presence-gate-protection-bear-suit",
        semantic_digest=empty,
        trading_epoch=trading_epoch,
        side=DirectionalAssessmentSide.SHORT,
        status=SuitabilityBindingStatus.BLOCKED,
    )
    return DoublePlayCompositionResultV1(
        composition_id="presence-gate-protection-observe",
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        bull_assessment_ref=bull_a,
        bear_assessment_ref=bear_a,
        bull_survival_ref=bull_s,
        bear_survival_ref=bear_s,
        bull_suitability_ref=bull_u,
        bear_suitability_ref=bear_u,
        previous_direction_state=previous_direction_state,
        position_management_context=position_management_context,
        composition_status=CompositionStatus.OBSERVE,
        selected_side=CompositionSelectedSide.NONE,
        conflict_status=CompositionConflictStatus.NONE,
        chop_guard_status=CompositionChopGuardStatus.NONE,
        reason_codes=(TYPED_VOLATILITY_ESTIMATE_MISSING_REASON, "protection_only_observe"),
        policy_version="double_play_composition_matrix_policy_v1",
        input_digest=empty,
        semantic_digest=empty,
    )


def evaluate_protection_authority_when_typed_absent_v1(
    *,
    instrument_id: str,
    trading_epoch: int,
    context_reference: str,
    direction_state: EntryExitDirectionState,
    position_state: PositionState,
    reconciliation_state: ReconciliationState,
    trading_gate: TradingGate,
    safety_mode: SafetyMode,
    data_integrity_state: DataIntegrityStatus,
    clock_trust_status: ClockTrustStatus,
    cooldown_pass: bool,
    existing_position_side: ExistingPositionSide,
    venue_flat: bool,
    scope_adverse_exit_signal: PolicySignalV0,
    profit_protection_signal: PolicySignalV0,
    time_exit_signal: PolicySignalV0,
    strategy_invalidation_signal: PolicySignalV0,
    hard_risk_reduction_signal: PolicySignalV0,
    safety_exit_signal: PolicySignalV0,
    previous_direction_state: CompositionDirectionState,
    position_management_context: PositionManagementContext,
    entry_exit_policy: DoublePlayEntryExitPolicyV0,
    gate: DoublePlayTypedVolatilityPresenceGateResultV1,
) -> EntryExitPolicyDecisionV0:
    """Run entry/exit for safety/hard-risk/reconcile/mandatory without alpha authority."""
    demoted = demote_trading_gate_for_typed_presence_failure_v1(trading_gate)
    composition = _non_authorizing_observe_composition_v1(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        previous_direction_state=previous_direction_state,
        position_management_context=position_management_context,
    )
    inp = DoublePlayEntryExitPolicyInputV0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        composition_result=composition,
        direction_state=direction_state,
        position_state=position_state,
        reconciliation_state=reconciliation_state,
        trading_gate=demoted,
        safety_mode=safety_mode,
        data_integrity_state=data_integrity_state,
        clock_trust_status=clock_trust_status,
        clock_trust_valid=clock_trust_status is ClockTrustStatus.TRUSTED,
        cooldown_pass=cooldown_pass,
        existing_position_side=existing_position_side,
        venue_flat=venue_flat,
        scope_adverse_exit_signal=scope_adverse_exit_signal,
        profit_protection_signal=profit_protection_signal,
        time_exit_signal=time_exit_signal,
        strategy_invalidation_signal=strategy_invalidation_signal,
        hard_risk_reduction_signal=hard_risk_reduction_signal,
        safety_exit_signal=safety_exit_signal,
        input_complete=True,
        input_digest="",
        explicit_blocked_reasons=(),
        policy_version=entry_exit_policy.policy_version,
    )
    inp = replace(inp, input_digest=compute_entry_exit_policy_input_digest(inp))
    decision = evaluate_double_play_entry_exit_policy_v0(inp, entry_exit_policy)
    # Preserve protection outcomes; annotate fail-closed typed absence on non-entry paths.
    if decision.decision_outcome in (
        DecisionOutcome.ENTER_LONG,
        DecisionOutcome.ENTER_SHORT,
    ):
        # Presence gate must never allow entry when typed is absent.
        return replace(
            decision,
            decision_outcome=DecisionOutcome.BLOCKED,
            entry_eligibility=EntryEligibility.BLOCKED,
            reason_codes=tuple(
                dict.fromkeys(
                    (
                        *gate.reason_codes,
                        TYPED_VOLATILITY_ESTIMATE_MISSING_REASON,
                        "entry_blocked_typed_volatility_estimate_missing",
                        *decision.reason_codes,
                    )
                )
            ),
        )
    annotated = tuple(dict.fromkeys((*gate.reason_codes, *decision.reason_codes)))
    return replace(decision, reason_codes=annotated)


def assert_architecture_guards_v1(*, repo_root: Optional[Path] = None) -> dict[str, Any]:
    """Guards: single authorities; productive gate wired; no local .value extract."""
    root = repo_root or Path(__file__).resolve().parents[3]
    this_src = (
        root / "src/trading/master_v2/double_play_runtime_typed_volatility_presence_gate_v1.py"
    ).read_text(encoding="utf-8")
    typed_src = (
        root
        / "src/trading/master_v2/canonical_volatility_estimate_typed_consumption_contract_v1.py"
    ).read_text(encoding="utf-8")
    binding_src = (
        root / "src/trading/master_v2/canonical_volatility_binding_and_provenance_transport_v1.py"
    ).read_text(encoding="utf-8")
    bridge_src = (
        root
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
        / "hardening_cycle_bridge_v2.py"
    ).read_text(encoding="utf-8")
    replay_src = (
        root / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
    ).read_text(encoding="utf-8")
    scope_src = (root / "src/trading/master_v2/canonical_scope_initialization_v1.py").read_text(
        encoding="utf-8"
    )
    offline_scenario = (
        root / "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
    ).read_text(encoding="utf-8")

    adapter_def = "def " + "adapt_canonical_volatility_estimate_to_legacy_float_v1("
    binder_def = "def " + "bind_typed_canonical_volatility_estimate_into_market_context_v1("
    materializer_def = "def " + "compute_canonical_volatility_estimate_from_mark_prices_v1("
    validate_def = "def " + "validate_canonical_volatility_estimate_v1("

    if typed_src.count(adapter_def) != 1:
        raise RuntimeError("EXPECTED_EXACTLY_ONE_TYPED_TO_FLOAT_ADAPTER_DEF")
    if typed_src.count(validate_def) != 1:
        raise RuntimeError("EXPECTED_EXACTLY_ONE_VALIDATION_BOUNDARY_DEF")
    if binding_src.count(binder_def) != 1:
        raise RuntimeError("EXPECTED_EXACTLY_ONE_BIND_TYPED_DEF")
    if this_src.count(adapter_def) != 0:
        raise RuntimeError("SECOND_ADAPTER_DEF_IN_PRESENCE_GATE_FORBIDDEN")
    if this_src.count(binder_def) != 0:
        raise RuntimeError("SECOND_BINDER_DEF_IN_PRESENCE_GATE_FORBIDDEN")
    if this_src.count(materializer_def) != 0:
        raise RuntimeError("SECOND_ESTIMATOR_DEF_IN_PRESENCE_GATE_FORBIDDEN")
    if this_src.count(validate_def) != 0:
        raise RuntimeError("SECOND_VALIDATOR_DEF_IN_PRESENCE_GATE_FORBIDDEN")

    code_before_guards = this_src.split("def assert_architecture_guards_v1", 1)[0]
    if "canonical_volatility_estimate.value" in code_before_guards:
        raise RuntimeError("LOCAL_TYPED_VALUE_EXTRACTION_FORBIDDEN")
    if "canonical_volatility_estimate.value" in bridge_src:
        raise RuntimeError("LOCAL_TYPED_VALUE_EXTRACTION_IN_BRIDGE_FORBIDDEN")
    if "canonical_volatility_estimate.value" in scope_src:
        raise RuntimeError("LOCAL_TYPED_VALUE_EXTRACTION_IN_SCOPE_FORBIDDEN")

    if "evaluate_double_play_runtime_typed_volatility_presence_gate_v1" not in bridge_src:
        raise RuntimeError("PRESENCE_GATE_NOT_WIRED_IN_PRODUCTIVE_BRIDGE")
    if "require_productive_typed_volatility_presence_gate" not in bridge_src:
        raise RuntimeError("PRESENCE_GATE_FLAG_NOT_SET_IN_PRODUCTIVE_BRIDGE")
    if "require_productive_typed_volatility_presence_gate" not in replay_src:
        raise RuntimeError("PRESENCE_GATE_FLAG_MISSING_IN_REPLAY_INPUT")

    # Offline scenario must not require the productive presence gate.
    if "require_productive_typed_volatility_presence_gate=True" in offline_scenario:
        raise RuntimeError("OFFLINE_SCENARIO_MUST_NOT_ENABLE_PRODUCTIVE_PRESENCE_GATE")

    if GLOBAL_TYPED_ONLY_ENFORCEMENT or LIVE_AUTHORIZATION:
        raise RuntimeError("GLOBAL_TYPED_ONLY_OR_LIVE_FLAG_DRIFT")
    if NUMERIC_MAX_AGE_DECIDED or NUMERIC_MAX_AGE_POLICY_CREATED:
        raise RuntimeError("NUMERIC_MAX_AGE_FLAG_DRIFT")
    if not DOUBLE_PLAY_TYPED_CUTOVER:
        raise RuntimeError("DOUBLE_PLAY_TYPED_CUTOVER_MUST_BE_TRUE")
    if (
        SECOND_ESTIMATOR_CREATED
        or SECOND_ADAPTER_CREATED
        or SECOND_VALIDATOR_CREATED
        or LOCAL_TYPED_VALUE_EXTRACTION_CREATED
    ):
        raise RuntimeError("SECOND_AUTHORITY_OR_EXTRACTION_FLAG_DRIFT")

    # Productive path cannot bypass: eligibility evaluate must be referenced.
    if "evaluate_typed_volatility_binding_eligibility_v1" not in code_before_guards:
        raise RuntimeError("PRESENCE_GATE_MUST_REUSE_TYPED_ELIGIBILITY")

    return {
        "adapter_defs_in_typed": typed_src.count(adapter_def),
        "binder_defs_in_binding": binding_src.count(binder_def),
        "validator_defs_in_typed": typed_src.count(validate_def),
        "double_play_typed_cutover": DOUBLE_PLAY_TYPED_CUTOVER,
        "global_typed_only_enforcement": GLOBAL_TYPED_ONLY_ENFORCEMENT,
        "numeric_max_age_decided": NUMERIC_MAX_AGE_DECIDED,
        "legacy_float_adaptation_owner": LEGACY_FLOAT_ADAPTATION_OWNER,
        "productive_runtime_caller_owner": PRODUCTIVE_RUNTIME_CALLER_OWNER,
        "presence_gate_owner": PRESENCE_GATE_OWNER,
        "live_authorization": LIVE_AUTHORIZATION,
        "hard_stop": HARD_STOP,
        "guards_pass": True,
    }


def assert_capability_non_goals_v1() -> dict[str, Any]:
    return {
        "capability_id": CAPABILITY_ID,
        "capability_version": CAPABILITY_VERSION,
        "presence_gate_owner": PRESENCE_GATE_OWNER,
        "double_play_typed_cutover": DOUBLE_PLAY_TYPED_CUTOVER,
        "global_typed_only_enforcement": GLOBAL_TYPED_ONLY_ENFORCEMENT,
        "numeric_max_age_decided": NUMERIC_MAX_AGE_DECIDED,
        "numeric_max_age_policy_created": NUMERIC_MAX_AGE_POLICY_CREATED,
        "live_authorization": LIVE_AUTHORIZATION,
        "hard_stop": HARD_STOP,
        "second_estimator_created": SECOND_ESTIMATOR_CREATED,
        "second_adapter_created": SECOND_ADAPTER_CREATED,
        "second_validator_created": SECOND_VALIDATOR_CREATED,
        "local_typed_value_extraction_created": LOCAL_TYPED_VALUE_EXTRACTION_CREATED,
        "volatility_semantics_changed": VOLATILITY_SEMANTICS_CHANGED,
        "offline_replay_legacy_defaults_unchanged": OFFLINE_REPLAY_LEGACY_DEFAULTS_UNCHANGED,
        "research_legacy_fallbacks_unchanged": RESEARCH_LEGACY_FALLBACKS_UNCHANGED,
        "scenario_replay_unchanged": SCENARIO_REPLAY_UNCHANGED,
        "single_estimator_authority_preserved": SINGLE_ESTIMATOR_AUTHORITY_PRESERVED,
        "single_validation_boundary_preserved": SINGLE_VALIDATION_BOUNDARY_PRESERVED,
        "single_typed_float_adapter_authority_preserved": (
            SINGLE_TYPED_FLOAT_ADAPTER_AUTHORITY_PRESERVED
        ),
        "package_marker": PACKAGE_MARKER,
        "gaps_remaining": (
            "C1_G10_NUMERIC_MAX_AGE",
            "G3_UNTYPED_EXPLICIT_LEGACY_STILL_ADMISSIBLE",
            "G8_ESTIMATOR_AMBIGUITY_ON_EXPLICIT_LEGACY",
        ),
    }


__all__ = [
    "CAPABILITY_ID",
    "CAPABILITY_VERSION",
    "DOUBLE_PLAY_TYPED_CUTOVER",
    "DoublePlayTypedVolatilityPresenceGateResultV1",
    "GLOBAL_TYPED_ONLY_ENFORCEMENT",
    "HARD_STOP",
    "LIVE_AUTHORIZATION",
    "PACKAGE_MARKER",
    "PRESENCE_GATE_OWNER",
    "PRODUCTIVE_RUNTIME_CALLER_OWNER",
    "TYPED_VOLATILITY_ESTIMATE_MISSING_REASON",
    "assert_architecture_guards_v1",
    "assert_capability_non_goals_v1",
    "demote_trading_gate_for_typed_presence_failure_v1",
    "evaluate_double_play_runtime_typed_volatility_presence_gate_v1",
    "evaluate_protection_authority_when_typed_absent_v1",
    "protection_authority_required_v1",
]
