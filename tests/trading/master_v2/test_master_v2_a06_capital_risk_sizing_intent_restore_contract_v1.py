"""Owner-composition contract: A01–A05 evidence → STEP-29P → STEP-29Q.

A06 is a thin adapter. Safety is not restored. No live/order side effect.
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from src.governance.canonical_order_intent_v1 import CanonicalOrderIntentBuildOutcome
from src.governance.capital_risk_sizing_v1 import (
    CapitalRiskSizingOutcome,
    evaluate_quantity_chain_v1,
)
from trading.master_v2.capital_risk_sizing_intent_restore_v1 import (
    A06_ADAPTER_COMPUTE_OWNER,
    A06_ADAPTER_INTENT_OWNER,
    A06_ADAPTER_RISK_OWNER,
    A06_ADAPTER_SIZING_OWNER,
    A08_SAFETY_IMPLEMENTED,
    A08_STARTED,
    ADAPTER_ROLE,
    EXECUTION_MODE_PLAN_ONLY,
    INTENT_OWNER,
    QUANTITY_CHAIN_OWNER,
    SAFETY_RESTORED,
    SUBMISSION_AUTHORIZED,
    capital_context_to_quantity_chain_inputs_v1,
    compose_capital_risk_sizing_intent_from_core_evidence_v1,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    default_offline_replay_capital_context_v0,
)
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
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
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
RESTORE_MODULE = REPO_ROOT / "src/trading/master_v2/capital_risk_sizing_intent_restore_v1.py"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/MASTER_V2_A06_CAPITAL_RISK_SIZING_INTENT_RESTORE_V1.md"
CRS_OWNER = REPO_ROOT / "src/governance/capital_risk_sizing_v1.py"


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


def test_adapter_is_composition_only_not_an_owner() -> None:
    assert A06_ADAPTER_COMPUTE_OWNER is False
    assert A06_ADAPTER_RISK_OWNER is False
    assert A06_ADAPTER_SIZING_OWNER is False
    assert A06_ADAPTER_INTENT_OWNER is False
    assert ADAPTER_ROLE == "COMPOSITION_ONLY"
    assert QUANTITY_CHAIN_OWNER.endswith("capital_risk_sizing_v1")
    assert INTENT_OWNER.endswith("canonical_order_intent_v1")
    assert SAFETY_RESTORED is False
    assert A08_SAFETY_IMPLEMENTED is False
    assert A08_STARTED is False
    source = RESTORE_MODULE.read_text(encoding="utf-8")
    assert source.count("evaluate_quantity_chain_v1(") == 1
    assert "evaluate_scope_capital_envelope" not in source
    assert "evaluate_capital_risk_sizing_v1" not in source
    assert "a06-intent::" not in source
    assert "stage_digest" not in source
    assert "A06RestoreError" not in source
    assert "STAGE_CAPITAL_ENVELOPE" not in source
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "DEFERRED_TO_A08" in spec
    assert "SAFETY_RESTORED=false" in spec
    assert "HISTORICAL_REFERENCE_AUTHORITY=NONE" in spec
    assert "A06 facade architecture" in spec


def test_29p_owner_file_unmodified_by_adapter() -> None:
    source = CRS_OWNER.read_text(encoding="utf-8")
    assert "def evaluate_scope_capital_envelope_v1(" not in source
    assert "def chain_result_to_decision_v1(" not in source
    assert "def compute_capital_risk_sizing_policy_digest_v1(" not in source


def test_a01_a05_evidence_feeds_29p_then_29q_plan_only() -> None:
    core = _enter_long_core()
    assert_core_wiring_authority_invariants_v1(core)
    first = compose_capital_risk_sizing_intent_from_core_evidence_v1(core)
    second = compose_capital_risk_sizing_intent_from_core_evidence_v1(core)
    evidence = core.replay.evidence
    assert first.compute_owner == INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER
    assert first.compute_owner == CANONICAL_OFFLINE_ORCHESTRATOR
    assert first.decision_packet_role == DECISION_PACKET_ROLE_HANDOFF_EVIDENCE_ONLY
    assert core.doubleplay_handoff.source_role == SOURCE_ROLE_DERIVED_FROM_INTEGRATED_REPLAY
    assert first.side_state_writer == CANONICAL_BULL_BEAR_STATE_OWNER
    assert first.side_state_writer == core.side_state_writer
    assert evidence.decision_outcome == DecisionOutcome.ENTER_LONG.value
    assert first.chain.scope_capital_envelope.decision_id == evidence.decision_id
    assert first.chain.scope_capital_envelope.input_digest == evidence.input_digest
    assert first.chain.pre_sizing_risk.decision_id == evidence.decision_id
    assert first.chain.canonical_position_sizing is not None
    assert first.chain.post_sizing_risk is not None
    assert first.chain.quantity_provenance is not None
    assert first.chain.outcome is CapitalRiskSizingOutcome.PASS
    assert first.intent is not None
    assert first.intent_build is not None
    assert first.intent_build.outcome is CanonicalOrderIntentBuildOutcome.PASS
    assert first.intent.decision_id == evidence.decision_id
    assert first.intent.intent_id == f"intent-{evidence.decision_id}"
    assert first.execution_mode == EXECUTION_MODE_PLAN_ONLY
    assert first.submission_authorized is SUBMISSION_AUTHORIZED is False
    assert first.intent.submission_authorized is False
    assert first.intent.execution_eligible is False
    assert first.intent.adapter_compatible is False
    assert first.safety_restored is False
    assert first.a08_started is False
    assert first.adapter_is_compute_owner is False
    assert first.intent.semantic_digest == second.intent.semantic_digest
    assert first.chain.outcome == second.chain.outcome
    assert first.chain.final_quantity == second.chain.final_quantity
    assert first.chain.reason_codes == second.chain.reason_codes


def test_29p_is_the_quantity_chain_owner_used() -> None:
    core = _enter_long_core()
    composed = compose_capital_risk_sizing_intent_from_core_evidence_v1(core)
    ctx = default_offline_replay_capital_context_v0(
        instrument_id=core.replay.evidence.instrument_id,
    )
    context, policy = capital_context_to_quantity_chain_inputs_v1(ctx)
    direct = evaluate_quantity_chain_v1(core.replay.evidence, context, policy)
    assert composed.quantity_chain_owner == QUANTITY_CHAIN_OWNER
    assert composed.chain.outcome == direct.outcome
    assert composed.chain.final_quantity == direct.final_quantity
    assert composed.chain.reason_codes == direct.reason_codes
    assert composed.chain.scope_capital_envelope.input_digest == (
        direct.scope_capital_envelope.input_digest
    )


def test_29p_rejection_stays_fail_closed_and_skips_29q() -> None:
    core = _enter_long_core()
    blocked_ctx = replace(
        default_offline_replay_capital_context_v0(
            instrument_id=core.replay.evidence.instrument_id,
        ),
        daily_loss_remaining_budget=Decimal("0"),
        per_trade_risk_limit=Decimal("0"),
        scope_capital_limit=Decimal("0"),
    )
    composed = compose_capital_risk_sizing_intent_from_core_evidence_v1(
        core, capital_context=blocked_ctx
    )
    assert composed.chain.outcome is CapitalRiskSizingOutcome.BLOCKED
    assert composed.intent is None
    assert composed.intent_build is None
    assert composed.submission_authorized is False
    assert composed.safety_restored is False


def test_packet_is_not_the_evidence_source() -> None:
    core = _enter_long_core()
    composed = compose_capital_risk_sizing_intent_from_core_evidence_v1(core)
    assert composed.chain.scope_capital_envelope.decision_id == (core.replay.evidence.decision_id)
    assert composed.chain.scope_capital_envelope.decision_id != ""
    assert core.packet.doubleplay is not None
    assert composed.decision_packet_role == DECISION_PACKET_ROLE_HANDOFF_EVIDENCE_ONLY
    source = RESTORE_MODULE.read_text(encoding="utf-8")
    assert "core.replay.evidence" in source
    assert "treat_packet_as_compute_owner" not in source
    assert "assert_legacy_decision_packet" not in source
    assert "assert_no_downstream_sidestate_override" not in source
