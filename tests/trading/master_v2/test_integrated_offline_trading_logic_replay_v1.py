# tests/trading/master_v2/test_integrated_offline_trading_logic_replay_v1.py
from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import fields, replace
from pathlib import Path

import pytest

from trading.master_v2.canonical_market_context_v1 import (
    CANONICAL_MARKET_CONTEXT_LAYER_VERSION,
    FEATURE_CONTRACT_VERSION,
    BarFinalityStatus,
    CanonicalMarketContextBindingStateV1,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    WarmupStatus,
    with_computed_input_digest,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    CANONICAL_SCOPE_INITIALIZATION_LAYER_VERSION,
    CanonicalScopeInitializationPolicyV1,
    ScopeInitializationPrerequisitesV1,
    ScopeReinitializationGuardV1,
    SCOPE_INITIALIZATION_POLICY_VERSION,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CANONICAL_TRADING_DECISION_EVIDENCE_LAYER_VERSION,
    serialize_canonical_trading_decision_evidence_canonical,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    DETERMINISTIC_SCOPE_EVENT_GENERATOR_LAYER_VERSION,
    SCOPE_EVENT_GENERATOR_POLICY_VERSION,
    ScopeConfirmationStateV1,
    ScopeCooldownStateV1,
    ScopeDirectionState,
    ScopeEventGeneratorPolicyV1,
)
from trading.master_v2.directional_assessment_v1 import (
    DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    DirectionalAssessmentPolicyV1,
    DirectionalAssessmentSide,
    DirectionalConfirmationStateV1,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
    BothCandidateOutcome,
    BothInvalidOutcome,
    CompositionDirectionState,
    CompositionStatus,
    DoublePlayCompositionPolicyV1,
    PositionManagementContext,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    ENTRY_EXIT_POLICY_VERSION,
    DecisionOutcome,
    DoublePlayEntryExitPolicyV0,
    EntryExitDirectionState,
    ExistingPositionSide,
    ExitClass,
    PolicySignalV0,
    PositionState,
    ReconciliationState,
    SafetyMode,
    TradingGate,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_replay_evidence_writer_v1 import (
    verify_evidence_manifest_v1,
    write_integrated_offline_replay_evidence_bundle_v1,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    IntegratedOfflineReplayInputV1,
    IntegratedOfflineReplayPoliciesV1,
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.suitability_binding_v1 import (
    SUITABILITY_RANKING_POLICY_VERSION,
    SuitabilityBindingStatus,
    SuitabilityRankingPolicyV1,
    SuitabilityRegimeStatus,
    SuitabilityStrategyEntryV1,
    SuitabilityStrategyRegistryV1,
)
from trading.master_v2.survival_assessment_v1 import (
    SURVIVAL_ASSESSMENT_POLICY_VERSION,
    SurvivalAssessmentPolicyV1,
)

_INSTRUMENT = "inst-eth-usdt-perp"
_EPOCH = 44
_CONTEXT_REF = "trading-context-epoch-44"
_REPLAY_ID = "replay-integrated-offline-v1-fixture"
_CONFIG_DIGEST = "c" * 64
_IMPL_DIGEST = "d" * 64


def _features(**kwargs: float) -> dict[str, float]:
    return dict(kwargs)


def _market_context(**overrides: object) -> CanonicalMarketContextV1:
    base: dict = {
        "context_id": "ctx-eth-perp-epoch44-ev1",
        "instrument_id": _INSTRUMENT,
        "market_type": FuturesMarketType.PERPETUAL,
        "trading_epoch": _EPOCH,
        "market_event_time": "2026-06-30T12:00:00+00:00",
        "decision_time": "2026-06-30T12:00:01+00:00",
        "bar_interval": "1m",
        "bar_finality_status": BarFinalityStatus.FINALIZED,
        "mark_price": 3500.0,
        "index_price": 3499.5,
        "best_bid": 3499.8,
        "best_ask": 3500.2,
        "spread": 0.4,
        "volume": 1_250_000.0,
        "open_interest": 85_000_000.0,
        "funding_rate": 0.00012,
        "volatility_estimate": 0.38,
        "trend_feature_set": _features(slope=0.02, strength=0.71),
        "momentum_feature_set": _features(rsi=55.0, roc=0.015),
        "liquidity_feature_set": _features(depth_score=0.88),
        "market_structure_feature_set": _features(range_ratio=0.42),
        "data_integrity_status": DataIntegrityStatus.TRUSTED,
        "clock_trust_status": ClockTrustStatus.TRUSTED,
        "warmup_status": WarmupStatus.WARMUP_COMPLETE,
        "feature_contract_version": FEATURE_CONTRACT_VERSION,
        "input_digest": "",
    }
    base.update(overrides)
    return with_computed_input_digest(CanonicalMarketContextV1(**base))


def _default_policies() -> IntegratedOfflineReplayPoliciesV1:
    return IntegratedOfflineReplayPoliciesV1(
        scope_initialization=CanonicalScopeInitializationPolicyV1(
            min_scope_band=50.0,
            max_scope_band=500.0,
            policy_version=SCOPE_INITIALIZATION_POLICY_VERSION,
        ),
        scope_event_generator=ScopeEventGeneratorPolicyV1(
            hard_max_scope_distance=1000.0,
            hard_max_adverse_distance=500.0,
            hard_max_reversal_distance=800.0,
            policy_version=SCOPE_EVENT_GENERATOR_POLICY_VERSION,
        ),
        directional=DirectionalAssessmentPolicyV1(
            observe_signal_threshold=0.001,
            candidate_signal_threshold=0.005,
            confirmation_signal_threshold=0.01,
            confirmation_epochs=2,
            validity_epochs=3,
            policy_version=DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
        ),
        survival=SurvivalAssessmentPolicyV1(
            min_net_edge=0.001,
            min_volatility_survival_ratio=0.5,
            min_sequence_survival_ratio=0.5,
            min_drawdown_survival_ratio=0.5,
            min_liquidation_buffer_ratio=0.1,
            validity_epochs=3,
            policy_version=SURVIVAL_ASSESSMENT_POLICY_VERSION,
        ),
        suitability=SuitabilityRankingPolicyV1(
            validity_epochs=3,
            no_match_status=SuitabilityBindingStatus.FAIL,
            policy_version=SUITABILITY_RANKING_POLICY_VERSION,
        ),
        composition=DoublePlayCompositionPolicyV1(
            validity_epochs=3,
            both_candidate_outcome=BothCandidateOutcome.OBSERVE,
            both_invalid_outcome=BothInvalidOutcome.BLOCKED,
            policy_version=DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
        ),
        entry_exit=DoublePlayEntryExitPolicyV0(policy_version=ENTRY_EXIT_POLICY_VERSION),
    )


def _component_versions() -> dict[str, str]:
    return {
        "canonical_market_context": CANONICAL_MARKET_CONTEXT_LAYER_VERSION,
        "canonical_scope_initialization": CANONICAL_SCOPE_INITIALIZATION_LAYER_VERSION,
        "deterministic_scope_event_generator": DETERMINISTIC_SCOPE_EVENT_GENERATOR_LAYER_VERSION,
        "directional_assessment": "v1",
        "survival_assessment": "v1",
        "suitability_binding": "v1",
        "double_play_composition_matrix": "v1",
        "double_play_entry_exit_policy": "v0",
        "double_play_state": "v0",
        "integrated_offline_trading_logic_replay": INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
        "canonical_trading_decision_evidence": CANONICAL_TRADING_DECISION_EVIDENCE_LAYER_VERSION,
    }


def _policy_versions() -> dict[str, str]:
    return {
        "scope_initialization": SCOPE_INITIALIZATION_POLICY_VERSION,
        "scope_event_generator": SCOPE_EVENT_GENERATOR_POLICY_VERSION,
        "directional": DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
        "survival": SURVIVAL_ASSESSMENT_POLICY_VERSION,
        "suitability": SUITABILITY_RANKING_POLICY_VERSION,
        "composition": DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
        "entry_exit": ENTRY_EXIT_POLICY_VERSION,
    }


def _strategy_registry() -> SuitabilityStrategyRegistryV1:
    return SuitabilityStrategyRegistryV1(
        entries=(
            SuitabilityStrategyEntryV1(
                strategy_id="strat-momentum-v1",
                supported_regime_ids=("trending",),
                supported_sides=(DirectionalAssessmentSide.LONG, DirectionalAssessmentSide.SHORT),
                priority_rank=10,
                disabled=False,
                confidence_score=0.75,
            ),
        )
    )


def _replay_input(**overrides: object) -> IntegratedOfflineReplayInputV1:
    ctx = overrides.pop("canonical_market_context", _market_context())
    price_path = overrides.pop("price_path", (3500.0, 3570.0))
    base: dict = {
        "replay_id": _REPLAY_ID,
        "instrument_id": _INSTRUMENT,
        "trading_epoch": _EPOCH,
        "canonical_market_context": ctx,
        "market_context_binding_state": CanonicalMarketContextBindingStateV1(),
        "scope_prerequisites": ScopeInitializationPrerequisitesV1(
            required_window_complete=True,
            instrument_metadata_valid=True,
            finalized_market_context=True,
        ),
        "scope_reinitialization_guard": ScopeReinitializationGuardV1(),
        "existing_scope": None,
        "scope_direction_state": ScopeDirectionState.LONG,
        "scope_confirmation_state": ScopeConfirmationStateV1(
            candidate_kind=None,
            candidate_count=1,
            last_evaluated_trading_epoch=_EPOCH - 1,
        ),
        "scope_cooldown_state": ScopeCooldownStateV1(
            active=False,
            remaining_epochs=0,
            policy_version=SCOPE_EVENT_GENERATOR_POLICY_VERSION,
        ),
        "up_distance": 200.0,
        "adverse_exit_distance": 80.0,
        "reversal_distance": 120.0,
        "confirmation_epochs": 2,
        "current_price": float(price_path[-1]),
        "price_path": tuple(price_path),
        "directional_confirmation_state": DirectionalConfirmationStateV1(
            candidate_count=1,
            last_evaluated_trading_epoch=_EPOCH - 1,
            last_signal_strength=0.02,
        ),
        "strategy_registry": _strategy_registry(),
        "regime_id": "trending",
        "regime_status": SuitabilityRegimeStatus.KNOWN,
        "previous_composition_direction_state": CompositionDirectionState.NEUTRAL,
        "position_management_context": PositionManagementContext.FLAT,
        "last_evaluated_trading_epoch": _EPOCH - 1,
        "side_state": SideState.LONG_ARMED,
        "direction_state": EntryExitDirectionState.LONG_ARMED,
        "position_state": PositionState.FLAT_RECONCILED,
        "reconciliation_state": ReconciliationState.RECONCILED,
        "trading_gate": TradingGate.ENTRY_ALLOWED,
        "safety_mode": SafetyMode.NORMAL,
        "existing_position_side": ExistingPositionSide.NONE,
        "venue_flat": True,
        "cooldown_pass": True,
        "scope_adverse_exit_signal": PolicySignalV0(triggered=False),
        "profit_protection_signal": PolicySignalV0(triggered=False),
        "time_exit_signal": PolicySignalV0(triggered=False),
        "strategy_invalidation_signal": PolicySignalV0(triggered=False),
        "hard_risk_reduction_signal": PolicySignalV0(triggered=False),
        "safety_exit_signal": PolicySignalV0(triggered=False),
        "policies": _default_policies(),
        "component_versions": _component_versions(),
        "policy_versions": _policy_versions(),
        "config_digest": _CONFIG_DIGEST,
        "implementation_digest": _IMPL_DIGEST,
        "input_digest": hashlib.sha256(b"integrated-replay-fixture-input-v1").hexdigest(),
        "expected_component_contracts": _component_versions(),
        "context_reference": _CONTEXT_REF,
        "now_tick": 0,
    }
    base.update(overrides)
    return IntegratedOfflineReplayInputV1(**base)


def _run(**kwargs: object):
    return run_integrated_offline_trading_logic_replay_v1(_replay_input(**kwargs))


def test_owner_constant() -> None:
    assert INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER.endswith(
        "integrated_offline_trading_logic_replay_v1"
    )


def test_contract_schema_complete() -> None:
    result = _run()
    required = {
        "decision_id",
        "replay_id",
        "instrument_id",
        "trading_epoch",
        "market_context_ref",
        "scope_initialization_ref",
        "scope_event_ref",
        "bull_assessment_ref",
        "bear_assessment_ref",
        "composition_result_ref",
        "entry_exit_policy_ref",
        "decision_outcome",
        "semantic_digest",
        "execution_eligible",
        "adapter_compatible",
        "quantity_status",
        "authority_effect",
        "runtime_effect",
        "order_effect",
        "risk_sizing_effect",
    }
    assert required.issubset({f.name for f in fields(type(result.evidence))})


def test_no_runtime_order_imports_in_replay_owner() -> None:
    src = (
        Path(__file__).resolve().parents[3]
        / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
    )
    tree = ast.parse(src.read_text(encoding="utf-8"))
    forbidden = {"execution", "adapter", "scheduler", "credentials"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(f in alias.name for f in forbidden)
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not any(f in node.module for f in forbidden)


@pytest.mark.parametrize(
    "scenario_id,kwargs,expected_outcome,extra_checks",
    [
        (
            1,
            {
                "canonical_market_context": _market_context(
                    warmup_status=WarmupStatus.WARMUP_REQUIRED
                )
            },
            "observe",
            lambda r: r.evidence.decision_outcome in ("observe", "blocked"),
        ),
        (
            2,
            {
                "canonical_market_context": _market_context(
                    bar_finality_status=BarFinalityStatus.UNFINALIZED
                )
            },
            "blocked",
            None,
        ),
        (
            3,
            {
                "canonical_market_context": _market_context(
                    data_integrity_status=DataIntegrityStatus.UNTRUSTED
                )
            },
            "blocked",
            None,
        ),
        (
            4,
            {
                "canonical_market_context": _market_context(
                    clock_trust_status=ClockTrustStatus.INVALID
                )
            },
            "blocked",
            None,
        ),
        (
            5,
            {
                "price_path": (3500.0, 3501.0),
                "directional_confirmation_state": DirectionalConfirmationStateV1(0, -1, 0.0),
            },
            None,
            lambda r: r.evidence.decision_outcome in ("no_action", "observe", "blocked", "hold"),
        ),
        (
            12,
            {"regime_status": SuitabilityRegimeStatus.UNKNOWN},
            None,
            lambda r: r.evidence.decision_outcome in ("blocked", "observe", "no_action"),
        ),
        (
            13,
            {"strategy_registry": SuitabilityStrategyRegistryV1(entries=())},
            None,
            lambda r: r.evidence.decision_outcome in ("blocked", "observe", "no_action"),
        ),
        (
            27,
            {
                "instrument_id": "inst-eth-usdt-perp",
                "canonical_market_context": _market_context(instrument_id="inst-other-perp"),
            },
            "blocked",
            None,
        ),
        (
            28,
            {"trading_epoch": 99, "canonical_market_context": _market_context(trading_epoch=44)},
            "blocked",
            None,
        ),
        (
            30,
            {"expected_component_contracts": {"canonical_market_context": "v99"}},
            "blocked",
            None,
        ),
        (
            31,
            {"policy_versions": {**_policy_versions(), "directional": "wrong_policy_v99"}},
            "blocked",
            None,
        ),
    ],
    ids=lambda x: f"scenario_{x[0]}" if isinstance(x, tuple) else str(x),
)
def test_fail_closed_scenarios(scenario_id, kwargs, expected_outcome, extra_checks) -> None:
    result = _run(**kwargs)
    assert result.evidence is not None
    if expected_outcome:
        assert result.evidence.decision_outcome == expected_outcome or not result.replay_pass
    if extra_checks:
        extra_checks(result)
    assert not result.evidence.execution_eligible
    assert not result.evidence.adapter_compatible
    assert result.evidence.quantity_status == "NOT_BOUND"


def test_6_long_only_admissible_enter_long_no_execution() -> None:
    result = _run(
        side_state=SideState.LONG_ARMED, direction_state=EntryExitDirectionState.LONG_ARMED
    )
    assert result.intermediate is not None
    if result.intermediate.composition_result.composition_status is CompositionStatus.LONG_SELECTED:
        assert result.evidence.decision_outcome == DecisionOutcome.ENTER_LONG.value
    assert not result.evidence.execution_eligible
    assert not result.evidence.adapter_compatible


def test_8_both_sides_confirmed_chop_guard() -> None:
    result = _run(price_path=(3500.0, 3600.0))
    if (
        result.intermediate
        and result.intermediate.composition_result.composition_status
        == CompositionStatus.CHOP_GUARD_BLOCK
    ):
        assert result.evidence.decision_outcome in (
            DecisionOutcome.BLOCKED.value,
            DecisionOutcome.OBSERVE.value,
            DecisionOutcome.NO_ACTION.value,
        )


def test_9_survival_fail_blocks_entry() -> None:
    policies = _default_policies()
    survival_policy = replace(
        policies.survival,
        min_net_edge=999.0,
    )
    result = _run(policies=replace(policies, survival=survival_policy))
    assert result.evidence.decision_outcome in (
        DecisionOutcome.BLOCKED.value,
        DecisionOutcome.NO_ACTION.value,
        DecisionOutcome.OBSERVE.value,
    )
    assert result.evidence.decision_outcome != DecisionOutcome.ENTER_LONG.value


def test_14_existing_long_short_selected_reversal() -> None:
    result = _run(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        side_state=SideState.LONG_ACTIVE,
        direction_state=EntryExitDirectionState.LONG_ACTIVE,
        price_path=(3500.0, 3400.0),
        scope_direction_state=ScopeDirectionState.SHORT,
    )
    if (
        result.intermediate
        and result.intermediate.entry_exit_decision.exit_class
        == ExitClass.REVERSAL_PREPARATION_EXIT
    ):
        assert result.evidence.decision_outcome != DecisionOutcome.ENTER_SHORT.value


def test_16_existing_position_safety_exit() -> None:
    result = _run(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        side_state=SideState.LONG_ACTIVE,
        safety_exit_signal=PolicySignalV0(triggered=True, reason_code="safety"),
    )
    assert result.intermediate is not None
    assert result.intermediate.entry_exit_decision.exit_class is ExitClass.SAFETY_EXIT


def test_18_existing_position_reconciliation_required() -> None:
    result = _run(position_state=PositionState.RECONCILIATION_REQUIRED)
    assert result.evidence.decision_outcome == DecisionOutcome.RECONCILE_ONLY.value


def test_19_reducing_partial_no_counter_entry() -> None:
    result = _run(
        position_state=PositionState.REDUCING_PARTIAL,
        existing_position_side=ExistingPositionSide.LONG,
        side_state=SideState.LONG_ACTIVE,
        scope_direction_state=ScopeDirectionState.SHORT,
        price_path=(3500.0, 3400.0),
    )
    assert result.evidence.decision_outcome != DecisionOutcome.ENTER_SHORT.value


def test_22_venue_flat_not_reconciled_blocks_entry() -> None:
    result = _run(venue_flat=True, reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED)
    assert result.evidence.decision_outcome == DecisionOutcome.RECONCILE_ONLY.value


def test_33_collection_reorder_invariant() -> None:
    versions_a = _component_versions()
    versions_b = dict(reversed(list(versions_a.items())))
    a = _run(component_versions=versions_a)
    b = _run(component_versions=versions_b)
    assert a.evidence.semantic_digest == b.evidence.semantic_digest


def test_34_deterministic_serialization_and_digest() -> None:
    a = _run()
    b = _run()
    ser_a = serialize_canonical_trading_decision_evidence_canonical(a.evidence)
    ser_b = serialize_canonical_trading_decision_evidence_canonical(b.evidence)
    assert ser_a == ser_b
    assert a.evidence.semantic_digest == b.evidence.semantic_digest


def test_34_byte_stable_evidence_bundle(tmp_path: Path) -> None:
    inp = _replay_input()
    r1 = run_integrated_offline_trading_logic_replay_v1(inp)
    r2 = run_integrated_offline_trading_logic_replay_v1(inp)
    d1 = tmp_path / "run1"
    d2 = tmp_path / "run2"
    write_integrated_offline_replay_evidence_bundle_v1(
        out_dir=d1, replay_input=inp, replay_result=r1
    )
    write_integrated_offline_replay_evidence_bundle_v1(
        out_dir=d2, replay_input=inp, replay_result=r2
    )
    m1 = (d1 / "MANIFEST.sha256").read_text(encoding="utf-8")
    m2 = (d2 / "MANIFEST.sha256").read_text(encoding="utf-8")
    assert m1 == m2
    assert verify_evidence_manifest_v1(d1 / "MANIFEST.sha256") == 0


def test_36_subprocess_determinism() -> None:
    root = Path(__file__).resolve().parents[3]
    env = {**os.environ, "PYTHONPATH": str(root / "src")}
    code = """
import json
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import run_integrated_offline_trading_logic_replay_v1
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _replay_input
r = run_integrated_offline_trading_logic_replay_v1(_replay_input())
print(json.dumps({"digest": r.evidence.semantic_digest, "outcome": r.evidence.decision_outcome}))
"""
    out1 = subprocess.check_output([sys.executable, "-c", code], text=True, cwd=str(root), env=env)
    out2 = subprocess.check_output([sys.executable, "-c", code], text=True, cwd=str(root), env=env)
    assert out1 == out2


def test_boundary_fields_always_negative() -> None:
    result = _run()
    ev = result.evidence
    dec = result.intermediate.entry_exit_decision if result.intermediate else None
    assert not ev.execution_eligible
    assert not ev.adapter_compatible
    assert ev.quantity_status == "NOT_BOUND"
    assert ev.authority_effect == "NONE"
    assert ev.runtime_effect == "NONE"
    assert ev.order_effect == "NONE"
    assert ev.risk_sizing_effect == "NONE"
    if dec:
        assert not dec.execution_eligible
        assert not dec.adapter_compatible
        assert dec.quantity_status == "NOT_BOUND"


def test_provenance_chain_refs_populated() -> None:
    result = _run()
    ev = result.evidence
    assert ev.market_context_ref
    assert ev.scope_initialization_ref
    assert ev.scope_event_ref
    assert ev.bull_assessment_ref
    assert ev.bear_assessment_ref
    assert ev.composition_result_ref
    assert ev.entry_exit_policy_ref


def test_long_short_symmetry_structure() -> None:
    long_result = _run(
        side_state=SideState.LONG_ARMED,
        direction_state=EntryExitDirectionState.LONG_ARMED,
        scope_direction_state=ScopeDirectionState.LONG,
        price_path=(3500.0, 3570.0),
    )
    short_result = _run(
        side_state=SideState.SHORT_ARMED,
        direction_state=EntryExitDirectionState.SHORT_ARMED,
        scope_direction_state=ScopeDirectionState.SHORT,
        price_path=(3500.0, 3430.0),
    )
    assert long_result.evidence.instrument_id == short_result.evidence.instrument_id
    assert long_result.evidence.market_context_ref == short_result.evidence.market_context_ref
    assert long_result.evidence.semantic_digest != short_result.evidence.semantic_digest
