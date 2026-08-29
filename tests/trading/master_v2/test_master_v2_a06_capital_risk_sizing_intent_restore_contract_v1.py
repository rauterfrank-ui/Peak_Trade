"""Offline contract: A06 Capital → Risk → Sizing → Position Intent restore.

REGISTRY → SUITABILITY → INTEGRATED REPLAY → DOUBLE PLAY → DECISION EVIDENCE
→ CAPITAL ENVELOPE → RISK → SIZING → POSITION INTENT

No network, no live/testnet/canary/orders. AUTH-014 remains a conservative
semantic-stage restore without a module-split owner choice.
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from src.execution_pipeline.plan_only_boundary_v0 import PLAN_ONLY_BOUNDARY_OWNER
from src.governance.capital_risk_sizing_v1 import (
    CapitalRiskSizingOutcome,
    EnvelopeStatus,
    PreSizingRiskStatus,
    evaluate_quantity_chain_v1,
)
from trading.master_v2.capital_risk_sizing_intent_restore_v1 import (
    A06_REASON_AMBIGUOUS_STRATEGY_BINDING,
    A06_REASON_UNKNOWN_STRATEGY_ID,
    AUTH_014_POLICY_CHOICE_REQUIRED,
    AUTH_014_STATUS,
    CANONICAL_STAGE_ORDER,
    CAPITAL_RISK_SIZING_INTENT_RESTORE_OWNER,
    EXECUTION_MODE_PLAN_ONLY,
    IMPLEMENTATION_MODULE_OWNERSHIP_MAY_BE_COMBINED,
    ORDER_SUBMIT_AUTHORIZED,
    REASON_ACCIDENTAL_EXECUTION_AUTHORIZATION,
    REASON_CAPITAL_RISK_PROVENANCE_MISMATCH,
    REASON_DOWNSTREAM_SIDESTATE_OVERRIDE,
    REASON_EVIDENCE_STRATEGY_MISMATCH,
    REASON_INTENT_WITHOUT_SIZING,
    REASON_LEGACY_PACKET_COMPUTE_AUTHORITY,
    REASON_MISSING_CAPITAL_ENVELOPE,
    REASON_MISSING_DECISION_EVIDENCE,
    REASON_MISSING_STRATEGY_IDENTITY,
    REASON_RISK_REJECTION,
    REASON_SIZING_WITHOUT_RISK_APPROVAL,
    SEMANTIC_STAGE_OWNERSHIP_SEPARATE,
    STAGE_CAPITAL_ENVELOPE,
    STAGE_POSITION_INTENT,
    STAGE_RISK,
    STAGE_SIZING,
    A06RestoreError,
    assert_no_accidental_execution_authorization_v1,
    capital_context_to_crs_inputs_v1,
    evaluate_position_intent_stage_v1,
    evaluate_risk_stage_v1,
    evaluate_sizing_stage_v1,
    run_a06_from_legacy_decision_packet_v1,
    run_master_v2_a06_capital_risk_sizing_intent_v1,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    default_offline_replay_capital_context_v0,
)
from trading.master_v2.decision_packet_fixtures_v1 import sample_doubleplay_decision_v1
from trading.master_v2.decision_packet_from_integrated_replay_v1 import (
    DECISION_PACKET_ROLE_HANDOFF_EVIDENCE_ONLY,
    SOURCE_ROLE_DERIVED_FROM_INTEGRATED_REPLAY,
)
from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
    initial_directional_confirmation_side_state_carrier_v1,
)
from trading.master_v2.double_play_core_wiring_v1 import (
    assert_core_wiring_authority_invariants_v1,
    run_master_v2_double_play_core_wiring_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitDirectionState,
)
from trading.master_v2.double_play_sole_authority_quarantine_v1 import (
    CANONICAL_BULL_BEAR_STATE_OWNER,
    CANONICAL_OFFLINE_ORCHESTRATOR,
    LIVE_AUTHORIZED,
    ORDERS_ENABLED,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
)
from trading.master_v2.registry_suitability_snapshot_v1 import (
    build_registry_derived_suitability_snapshot_v1,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _replay_input,
)
from tests.trading.master_v2.test_post_confirmation_survival_suitability_composition_binding_v1 import (
    _distinct_acceptor,
    _key,
    _policies_confirm_once,
    _session,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SPEC_PATH = REPO_ROOT / "docs/ops/specs/MASTER_V2_A06_CAPITAL_RISK_SIZING_INTENT_RESTORE_V1.md"
RESTORE_MODULE = REPO_ROOT / "src/trading/master_v2/capital_risk_sizing_intent_restore_v1.py"


def _enter_long_core():
    acceptor, _committed = _distinct_acceptor()
    carrier = initial_directional_confirmation_side_state_carrier_v1(
        session_id=_session(),
        venue="okx_eea",
        instrument=_key(),
    )
    inp = _replay_input(
        side_state=SideState.LONG_ARMED,
        direction_state=EntryExitDirectionState.LONG_ARMED,
        policies=_policies_confirm_once(),
        price_path=(3500.0, 3570.0),
        directional_confirmation_progress=carrier,
        observation_acceptance_result=acceptor,
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
    )
    return run_master_v2_double_play_core_wiring_v1(inp)


def _run_a06(**kwargs):
    return run_master_v2_a06_capital_risk_sizing_intent_v1(_enter_long_core(), **kwargs)


def test_auth_014_conservative_disposition() -> None:
    assert SEMANTIC_STAGE_OWNERSHIP_SEPARATE is True
    assert IMPLEMENTATION_MODULE_OWNERSHIP_MAY_BE_COMBINED is True
    assert AUTH_014_POLICY_CHOICE_REQUIRED is False
    assert AUTH_014_STATUS == "CONSERVATIVE_SEMANTIC_STAGES_SEPARATE_MODULE_MAY_COMBINE"


def test_spec_and_owner_constants() -> None:
    text = SPEC_PATH.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_MASTER_V2_A06_CAPITAL_RISK_SIZING_INTENT_RESTORE_V1" in text
    assert "HISTORICAL_REFERENCE_AUTHORITY=NONE" in text
    assert "AUTH_014_POLICY_CHOICE_REQUIRED=false" in text
    source = RESTORE_MODULE.read_text(encoding="utf-8")
    assert CAPITAL_RISK_SIZING_INTENT_RESTORE_OWNER in source
    assert "evaluate_capital_risk_sizing_v1" not in source


def test_end_to_end_registry_to_position_intent_stage_order_and_provenance() -> None:
    first = _run_a06()
    second = _run_a06()
    assert_core_wiring_authority_invariants_v1(first.core)
    assert first.compute_owner == INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER
    assert first.compute_owner == CANONICAL_OFFLINE_ORCHESTRATOR
    assert first.decision_packet_role == DECISION_PACKET_ROLE_HANDOFF_EVIDENCE_ONLY
    assert first.core.doubleplay_handoff.source_role == SOURCE_ROLE_DERIVED_FROM_INTEGRATED_REPLAY
    assert first.core.replay.evidence.decision_outcome == DecisionOutcome.ENTER_LONG.value
    assert first.observed_stage_order == CANONICAL_STAGE_ORDER
    assert first.capital.stage_id == STAGE_CAPITAL_ENVELOPE
    assert first.risk.stage_id == STAGE_RISK
    assert first.sizing is not None
    assert first.sizing.stage_id == STAGE_SIZING
    assert first.position_intent is not None
    assert first.position_intent.stage_id == STAGE_POSITION_INTENT
    evidence = first.core.replay.evidence
    assert first.capital.decision_evidence_id == evidence.decision_id
    assert first.capital.replay_id == evidence.replay_id
    assert first.capital.input_digest == evidence.input_digest
    assert first.risk.consumed_capital_envelope_digest == first.capital.stage_digest
    assert first.risk.input_digest == evidence.input_digest
    assert first.sizing.consumed_risk_digest == first.risk.stage_digest
    assert first.position_intent.consumed_sizing_digest == first.sizing.stage_digest
    assert first.position_intent.intent.decision_id == evidence.decision_id
    assert first.execution_mode == EXECUTION_MODE_PLAN_ONLY
    assert first.order_submit_authorized is ORDER_SUBMIT_AUTHORIZED is False
    assert first.live_authorized is False
    assert first.position_intent.intent.execution_eligible is False
    assert first.position_intent.intent.submission_authorized is False
    assert first.position_intent.intent.adapter_compatible is False
    assert first.position_intent.plan_only_boundary_owner == PLAN_ONLY_BOUNDARY_OWNER
    assert first.core.snapshot.live_authorized is False
    assert first.core.snapshot.orders_allowed is False
    assert LIVE_AUTHORIZED == "false"
    assert ORDERS_ENABLED == "false"
    assert first.semantic_digest == second.semantic_digest
    assert first.semantic_payload == second.semantic_payload
    assert first.position_intent.intent.semantic_digest == (
        second.position_intent.intent.semantic_digest
    )
    assert first.chain.outcome is CapitalRiskSizingOutcome.PASS
    assert first.chain.final_quantity > 0
    assert first.auth_014_policy_choice_required is False


def test_independent_stage_boundaries_observable_in_one_module() -> None:
    result = _run_a06()
    assert result.capital.module_owner == result.risk.module_owner
    assert result.capital.module_owner.endswith("capital_risk_sizing_v1")
    assert result.sizing is not None
    assert result.sizing.module_owner == result.capital.module_owner
    assert result.position_intent is not None
    assert result.position_intent.module_owner.endswith("canonical_order_intent_v1")
    assert result.observed_stage_order[0] == STAGE_CAPITAL_ENVELOPE
    assert result.observed_stage_order[1] == STAGE_RISK
    assert result.observed_stage_order[2] == STAGE_SIZING
    assert result.observed_stage_order[3] == STAGE_POSITION_INTENT


def test_missing_decision_evidence_fail_closed() -> None:
    core = _enter_long_core()
    mutated = replace(
        core,
        replay=replace(
            core.replay,
            evidence=replace(core.replay.evidence, decision_id="", replay_id=""),
        ),
    )
    with pytest.raises(A06RestoreError, match=REASON_MISSING_DECISION_EVIDENCE):
        run_master_v2_a06_capital_risk_sizing_intent_v1(mutated)


def test_unknown_strategy_identity_fail_closed() -> None:
    core = _enter_long_core()
    mutated = replace(
        core,
        replay=replace(
            core.replay,
            evidence=replace(
                core.replay.evidence,
                selected_strategy_ref="definitely_not_a_strategy_xyz",
            ),
        ),
    )
    with pytest.raises(A06RestoreError, match=A06_REASON_UNKNOWN_STRATEGY_ID):
        run_master_v2_a06_capital_risk_sizing_intent_v1(mutated)


def test_ambiguous_strategy_identity_fail_closed() -> None:
    core = _enter_long_core()
    mutated = replace(
        core,
        replay=replace(
            core.replay,
            evidence=replace(core.replay.evidence, selected_strategy_ref="ecm"),
        ),
    )
    with pytest.raises(A06RestoreError, match=A06_REASON_AMBIGUOUS_STRATEGY_BINDING):
        run_master_v2_a06_capital_risk_sizing_intent_v1(mutated)


def test_evidence_strategy_mismatch_fail_closed() -> None:
    snapshot = build_registry_derived_suitability_snapshot_v1(strategy_ids=("macd",))
    acceptor, _committed = _distinct_acceptor()
    carrier = initial_directional_confirmation_side_state_carrier_v1(
        session_id=_session(),
        venue="okx_eea",
        instrument=_key(),
    )
    core = run_master_v2_double_play_core_wiring_v1(
        _replay_input(
            side_state=SideState.LONG_ARMED,
            direction_state=EntryExitDirectionState.LONG_ARMED,
            policies=_policies_confirm_once(),
            price_path=(3500.0, 3570.0),
            directional_confirmation_progress=carrier,
            observation_acceptance_result=acceptor,
            confirmation_progress_session_id=_session(),
            confirmation_progress_venue="okx_eea",
            confirmation_progress_instrument=_key(),
        ),
        snapshot=snapshot,
    )
    mutated = replace(
        core,
        replay=replace(
            core.replay,
            evidence=replace(
                core.replay.evidence,
                selected_strategy_ref="ma_crossover",
            ),
        ),
    )
    with pytest.raises(A06RestoreError, match=REASON_EVIDENCE_STRATEGY_MISMATCH):
        run_master_v2_a06_capital_risk_sizing_intent_v1(mutated)


def test_missing_strategy_on_actionable_evidence_fail_closed() -> None:
    core = _enter_long_core()
    mutated = replace(
        core,
        replay=replace(
            core.replay,
            evidence=replace(core.replay.evidence, selected_strategy_ref=""),
        ),
    )
    with pytest.raises(A06RestoreError, match=REASON_MISSING_STRATEGY_IDENTITY):
        run_master_v2_a06_capital_risk_sizing_intent_v1(mutated)


def test_missing_capital_envelope_fail_closed() -> None:
    result = _run_a06()
    with pytest.raises(A06RestoreError, match=REASON_MISSING_CAPITAL_ENVELOPE):
        evaluate_risk_stage_v1(
            envelope=None,
            evidence=result.core.replay.evidence,
            chain=result.chain,
        )


def test_capital_risk_provenance_mismatch_fail_closed() -> None:
    result = _run_a06()
    mismatched = replace(
        result.capital,
        envelope=replace(result.capital.envelope, decision_id="other-decision"),
        decision_evidence_id="other-decision",
    )
    with pytest.raises(A06RestoreError, match=REASON_CAPITAL_RISK_PROVENANCE_MISMATCH):
        evaluate_risk_stage_v1(
            envelope=mismatched,
            evidence=result.core.replay.evidence,
            chain=result.chain,
        )


def test_duplicate_inconsistent_provenance_fail_closed() -> None:
    result = _run_a06()
    mismatched = replace(
        result.capital,
        envelope=replace(result.capital.envelope, input_digest="b" * 64),
        input_digest="b" * 64,
    )
    with pytest.raises(A06RestoreError, match=REASON_CAPITAL_RISK_PROVENANCE_MISMATCH):
        evaluate_risk_stage_v1(
            envelope=mismatched,
            evidence=result.core.replay.evidence,
            chain=result.chain,
        )


def test_risk_rejection_fail_closed() -> None:
    ctx = default_offline_replay_capital_context_v0(instrument_id="inst-eth-usdt-perp")
    exhausted = replace(ctx, daily_loss_remaining_budget=Decimal("0"))
    with pytest.raises(A06RestoreError, match=REASON_RISK_REJECTION):
        run_master_v2_a06_capital_risk_sizing_intent_v1(
            _enter_long_core(),
            capital_context=exhausted,
        )


def test_sizing_without_valid_risk_approval_fail_closed() -> None:
    result = _run_a06()
    blocked_risk = replace(result.risk, approved=False)
    with pytest.raises(A06RestoreError, match=REASON_SIZING_WITHOUT_RISK_APPROVAL):
        evaluate_sizing_stage_v1(
            risk=blocked_risk,
            chain=result.chain,
            evidence=result.core.replay.evidence,
        )
    with pytest.raises(A06RestoreError, match=REASON_SIZING_WITHOUT_RISK_APPROVAL):
        evaluate_sizing_stage_v1(
            risk=None,
            chain=result.chain,
            evidence=result.core.replay.evidence,
        )


def test_position_intent_without_valid_sizing_fail_closed() -> None:
    result = _run_a06()
    ctx = default_offline_replay_capital_context_v0(
        instrument_id=result.core.replay.evidence.instrument_id
    )
    _context, policy = capital_context_to_crs_inputs_v1(ctx)
    from src.governance.capital_risk_sizing_v1 import chain_result_to_decision_v1

    decision = chain_result_to_decision_v1(result.chain, selected_side="LONG")
    with pytest.raises(A06RestoreError, match=REASON_INTENT_WITHOUT_SIZING):
        evaluate_position_intent_stage_v1(
            sizing=None,
            decision=decision,
            sizing_input=None,  # type: ignore[arg-type]
            evidence=result.core.replay.evidence,
            policy=policy,
            ctx=ctx,
        )


def test_legacy_decision_packet_cannot_become_compute_authority() -> None:
    core = _enter_long_core()
    with pytest.raises(A06RestoreError, match=REASON_LEGACY_PACKET_COMPUTE_AUTHORITY):
        run_a06_from_legacy_decision_packet_v1(core.packet)
    with pytest.raises(A06RestoreError, match=REASON_LEGACY_PACKET_COMPUTE_AUTHORITY):
        run_master_v2_a06_capital_risk_sizing_intent_v1(
            core,
            treat_packet_as_compute_owner=True,
        )
    fixture_packet_handoff = sample_doubleplay_decision_v1()
    assert fixture_packet_handoff.source_role != SOURCE_ROLE_DERIVED_FROM_INTEGRATED_REPLAY


def test_downstream_cannot_override_double_play_sidestate() -> None:
    with pytest.raises(A06RestoreError, match=REASON_DOWNSTREAM_SIDESTATE_OVERRIDE):
        run_master_v2_a06_capital_risk_sizing_intent_v1(
            _enter_long_core(),
            claimed_side_state_writer="downstream.fake_sidestate_writer",
        )
    with pytest.raises(A06RestoreError, match=REASON_DOWNSTREAM_SIDESTATE_OVERRIDE):
        run_master_v2_a06_capital_risk_sizing_intent_v1(
            _enter_long_core(),
            override_selected_side="short",
        )
    assert CANONICAL_BULL_BEAR_STATE_OWNER.endswith("transition_state")


def test_accidental_execution_authorization_fail_closed() -> None:
    with pytest.raises(A06RestoreError, match=REASON_ACCIDENTAL_EXECUTION_AUTHORIZATION):
        assert_no_accidental_execution_authorization_v1(submission_authorized=True)
    with pytest.raises(A06RestoreError, match=REASON_ACCIDENTAL_EXECUTION_AUTHORIZATION):
        assert_no_accidental_execution_authorization_v1(live_authorized=True)
    with pytest.raises(A06RestoreError, match=REASON_ACCIDENTAL_EXECUTION_AUTHORIZATION):
        assert_no_accidental_execution_authorization_v1(execution_eligible=True)
    result = _run_a06()
    assert result.position_intent is not None
    assert result.position_intent.intent.submission_authorized is False
    assert result.position_intent.execution_mode == EXECUTION_MODE_PLAN_ONLY


def test_non_actionable_observe_does_not_emit_intent_or_execution() -> None:
    core = run_master_v2_double_play_core_wiring_v1(_replay_input())
    result = run_master_v2_a06_capital_risk_sizing_intent_v1(core)
    assert result.core.replay.evidence.decision_outcome != DecisionOutcome.ENTER_LONG.value
    assert result.capital.envelope.status in {
        EnvelopeStatus.PASS,
        EnvelopeStatus.REDUCE,
        EnvelopeStatus.BLOCK,
    }
    assert result.risk.assessment.status is PreSizingRiskStatus.BLOCK
    assert result.sizing is None
    assert result.position_intent is None
    assert result.execution_mode == EXECUTION_MODE_PLAN_ONLY
    assert result.order_submit_authorized is False
    assert result.live_authorized is False
    assert result.observed_stage_order == (STAGE_CAPITAL_ENVELOPE, STAGE_RISK)


def test_capital_envelope_consumes_replay_evidence_not_synthesized_legacy() -> None:
    result = _run_a06()
    ctx = default_offline_replay_capital_context_v0(
        instrument_id=result.core.replay.evidence.instrument_id
    )
    context, policy = capital_context_to_crs_inputs_v1(ctx)
    chain = evaluate_quantity_chain_v1(result.core.replay.evidence, context, policy)
    assert chain.scope_capital_envelope.decision_id == result.core.replay.evidence.decision_id
    assert chain.scope_capital_envelope.input_digest == result.core.replay.evidence.input_digest
    assert result.capital.replay_id == result.core.replay.evidence.replay_id
    assert result.capital.replay_id != "legacy-replay"
