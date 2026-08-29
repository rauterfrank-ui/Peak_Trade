"""Owner-composition contract: A01–A05 → STEP-29P → Safety → STEP-29Q PLAN_ONLY.

Thin sibling adapter. No live/order side effect. A06 is not wrapped.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.governance.canonical_order_intent_v1 import CanonicalOrderIntentBuildOutcome
from src.governance.capital_risk_sizing_v1 import CapitalRiskSizingOutcome
from trading.master_v2.capital_risk_sizing_safety_intent_restore_v1 import (
    ADAPTER_IS_COMPUTE_OWNER,
    ADAPTER_IS_INTENT_OWNER,
    ADAPTER_IS_RISK_OWNER,
    ADAPTER_IS_SAFETY_OWNER,
    ADAPTER_IS_SIZING_OWNER,
    ADAPTER_ROLE,
    EXECUTION_MODE_PLAN_ONLY,
    INTENT_OWNER,
    QUANTITY_CHAIN_OWNER,
    SAFETY_AUTHORITY_CHANGED,
    SAFETY_OWNER,
    SAFETY_OWNER_CHANGED,
    SAFETY_WIRING_CHANGED,
    SUBMISSION_AUTHORIZED,
    compose_capital_risk_sizing_safety_intent_from_core_evidence_v1,
    safety_context_from_integrated_replay_input_v1,
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
    SafetyMode,
)
from trading.master_v2.double_play_sole_authority_quarantine_v1 import (
    CANONICAL_BULL_BEAR_STATE_OWNER,
    CANONICAL_OFFLINE_ORCHESTRATOR,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
)
from trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0 import (
    SAFETY_BOUNDARY_EFFECT_BOUND_OFFLINE,
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
RESTORE_MODULE = REPO_ROOT / "src/trading/master_v2/capital_risk_sizing_safety_intent_restore_v1.py"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/MASTER_V2_CAPITAL_RISK_SIZING_SAFETY_INTENT_RESTORE_V1.md"
A06_MODULE = REPO_ROOT / "src/trading/master_v2/capital_risk_sizing_intent_restore_v1.py"
REPLAY_MODULE = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
EV_MODULE = REPO_ROOT / "src/backtest/economic_viability_evidence_v1.py"
SAFETY_OWNER_MODULE = (
    REPO_ROOT / "src/trading/master_v2/safety_kernel_offline_replay_binding_adapter_v0.py"
)
CRS_OWNER = REPO_ROOT / "src/governance/capital_risk_sizing_v1.py"
INTENT_OWNER_MODULE = REPO_ROOT / "src/governance/canonical_order_intent_v1.py"


def _enter_long_core_and_input():
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
    return run_master_v2_double_play_core_wiring_v1(inp), inp


def test_adapter_is_composition_only_not_an_owner() -> None:
    assert ADAPTER_IS_COMPUTE_OWNER is False
    assert ADAPTER_IS_RISK_OWNER is False
    assert ADAPTER_IS_SIZING_OWNER is False
    assert ADAPTER_IS_SAFETY_OWNER is False
    assert ADAPTER_IS_INTENT_OWNER is False
    assert ADAPTER_ROLE == "COMPOSITION_ONLY"
    assert QUANTITY_CHAIN_OWNER.endswith("capital_risk_sizing_v1")
    assert SAFETY_OWNER.endswith("safety_kernel_offline_replay_binding_adapter_v0")
    assert INTENT_OWNER.endswith("canonical_order_intent_v1")
    assert SAFETY_OWNER_CHANGED is False
    assert SAFETY_AUTHORITY_CHANGED is False
    assert SAFETY_WIRING_CHANGED is True
    source = RESTORE_MODULE.read_text(encoding="utf-8")
    assert source.count("evaluate_quantity_chain_v1(") == 1
    assert source.count("bind_safety_kernel_offline_replay_evidence_v0(") == 1
    assert source.count("build_canonical_order_intent_v1(") == 1
    assert "compose_capital_risk_sizing_intent_from_core_evidence_v1(" not in source
    assert "SafetyKernelOfflineReplayContextV0()" not in source
    assert "evaluate_offline_safety_kernel_boundary_v0(" not in source
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "HISTORICAL_STAGE=Safety" in spec
    assert "A07_IDENTITY_STATUS=UNPROVEN" in spec
    assert "A07_LABEL_DISPOSITION=RETIRE_AS_HISTORICAL_STAGE_LABEL" in spec
    assert "RESTORED_CHAIN=29P → Safety → 29Q PLAN_ONLY" in spec
    assert "A06_REWRITTEN=false" in spec
    assert "REPLAY_REORDERED=false" in spec
    assert "EV_RESTORED=false" in spec
    assert "SAFETY_WIRING_CHANGED=true" in spec
    assert "SAFETY_AUTHORITY_CHANGED=false" in spec
    assert "CURRENT_SYSTEM_SEMANTIC_DELTA=true" in spec
    assert "`MASTER_V2_HISTORICAL_STAGE_NAME` is Safety" in spec


def test_call_order_is_29p_then_safety_then_29q(monkeypatch: pytest.MonkeyPatch) -> None:
    import trading.master_v2.capital_risk_sizing_safety_intent_restore_v1 as mod

    core, inp = _enter_long_core_and_input()
    order: list[str] = []
    counts = {"29P": 0, "SAFETY": 0, "29Q": 0}
    real_29p = mod.evaluate_quantity_chain_v1
    real_safety = mod.bind_safety_kernel_offline_replay_evidence_v0
    real_29q = mod.build_canonical_order_intent_v1

    def wrap_29p(*args, **kwargs):
        order.append("29P")
        counts["29P"] += 1
        return real_29p(*args, **kwargs)

    def wrap_safety(*args, **kwargs):
        order.append("SAFETY")
        counts["SAFETY"] += 1
        return real_safety(*args, **kwargs)

    def wrap_29q(*args, **kwargs):
        order.append("29Q")
        counts["29Q"] += 1
        return real_29q(*args, **kwargs)

    monkeypatch.setattr(mod, "evaluate_quantity_chain_v1", wrap_29p)
    monkeypatch.setattr(mod, "bind_safety_kernel_offline_replay_evidence_v0", wrap_safety)
    monkeypatch.setattr(mod, "build_canonical_order_intent_v1", wrap_29q)
    composed = compose_capital_risk_sizing_safety_intent_from_core_evidence_v1(
        core,
        safety_context=safety_context_from_integrated_replay_input_v1(inp),
    )
    assert order == ["29P", "SAFETY", "29Q"]
    assert counts == {"29P": 1, "SAFETY": 1, "29Q": 1}
    assert composed.intent is not None


def test_safety_pass_path_plan_only_once() -> None:
    core, inp = _enter_long_core_and_input()
    assert_core_wiring_authority_invariants_v1(core)
    safety_context = safety_context_from_integrated_replay_input_v1(inp)
    composed = compose_capital_risk_sizing_safety_intent_from_core_evidence_v1(
        core, safety_context=safety_context
    )
    evidence = core.replay.evidence
    assert composed.compute_owner == INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER
    assert composed.compute_owner == CANONICAL_OFFLINE_ORCHESTRATOR
    assert composed.decision_packet_role == DECISION_PACKET_ROLE_HANDOFF_EVIDENCE_ONLY
    assert core.doubleplay_handoff.source_role == SOURCE_ROLE_DERIVED_FROM_INTEGRATED_REPLAY
    assert composed.side_state_writer == CANONICAL_BULL_BEAR_STATE_OWNER
    assert evidence.decision_outcome == DecisionOutcome.ENTER_LONG.value
    assert composed.chain.outcome is CapitalRiskSizingOutcome.PASS
    assert composed.safety_binding.boundary.hard_block_reasons == ()
    assert composed.safety_binding.boundary.no_permission_issued is True
    assert composed.safety_binding.safety_boundary_effect == SAFETY_BOUNDARY_EFFECT_BOUND_OFFLINE
    assert composed.intent is not None
    assert composed.intent_build is not None
    assert composed.intent_build.outcome is CanonicalOrderIntentBuildOutcome.PASS
    assert composed.intent.decision_id == evidence.decision_id
    assert composed.execution_mode == EXECUTION_MODE_PLAN_ONLY
    assert composed.submission_authorized is SUBMISSION_AUTHORIZED is False
    assert composed.intent.submission_authorized is False
    assert composed.intent.execution_eligible is False
    assert composed.adapter_is_safety_owner is False
    assert composed.safety_owner_changed is False
    assert composed.safety_authority_changed is False
    assert composed.safety_wiring_changed is True


def test_safety_block_skips_29q_and_preserves_block_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import trading.master_v2.capital_risk_sizing_safety_intent_restore_v1 as mod

    core, inp = _enter_long_core_and_input()
    counts = {"29P": 0, "SAFETY": 0, "29Q": 0}
    real_29p = mod.evaluate_quantity_chain_v1
    real_safety = mod.bind_safety_kernel_offline_replay_evidence_v0
    real_29q = mod.build_canonical_order_intent_v1

    def wrap_29p(*args, **kwargs):
        counts["29P"] += 1
        return real_29p(*args, **kwargs)

    def wrap_safety(*args, **kwargs):
        counts["SAFETY"] += 1
        return real_safety(*args, **kwargs)

    def wrap_29q(*args, **kwargs):
        counts["29Q"] += 1
        return real_29q(*args, **kwargs)

    monkeypatch.setattr(mod, "evaluate_quantity_chain_v1", wrap_29p)
    monkeypatch.setattr(mod, "bind_safety_kernel_offline_replay_evidence_v0", wrap_safety)
    monkeypatch.setattr(mod, "build_canonical_order_intent_v1", wrap_29q)
    blocked = replace(
        safety_context_from_integrated_replay_input_v1(inp),
        safety_mode=SafetyMode.BLOCKED,
        killswitch_blocked=True,
        safety_decision_allowed=False,
    )
    composed = compose_capital_risk_sizing_safety_intent_from_core_evidence_v1(
        core, safety_context=blocked
    )
    assert counts == {"29P": 1, "SAFETY": 1, "29Q": 0}
    assert composed.intent is None
    assert composed.intent_build is None
    assert composed.submission_authorized is False
    assert composed.safety_binding.boundary.hard_block_reasons
    assert "killswitch_boundary_blocks_new_entry" in (
        composed.safety_binding.boundary.hard_block_reasons
    )
    assert "entry_blocked_by_safety_kernel_boundary" in (
        composed.safety_binding.boundary.reason_codes
    )
    assert composed.safety_binding.boundary.no_permission_issued is True


def test_missing_safety_context_has_no_implicit_permissive_default() -> None:
    core, _inp = _enter_long_core_and_input()
    with pytest.raises(TypeError):
        compose_capital_risk_sizing_safety_intent_from_core_evidence_v1(core)
    with pytest.raises(TypeError):
        safety_context_from_integrated_replay_input_v1(None)  # type: ignore[arg-type]


def test_negative_coupling_and_authority_contract() -> None:
    source = RESTORE_MODULE.read_text(encoding="utf-8")
    forbidden = (
        "submit_order",
        "place_order",
        "create_order",
        "ccxt",
        "exchange_client",
        "network_session",
        "economic_viability_evidence_v1",
        "run_canonical_core_runtime_integration_intent_pipeline_bridge_v0",
        "run_canonical_core_runtime_integration_intent_pipeline_from_harness_v0",
        "transition_state(",
        "LIVE_AUTHORIZED = True",
        "TESTNET_AUTHORIZED = True",
        "CANARY_AUTHORIZED = True",
        "independent_pre_trade_safety_kernel_v1",
        "section_11_13_5_live_canary",
        "flatten_execute",
        "a06-intent::",
        "stage_digest",
    )
    for token in forbidden:
        assert token not in source, token
    assert "from trading.master_v2.capital_risk_sizing_intent_restore_v1" not in source
    assert A06_MODULE.is_file()
    assert REPLAY_MODULE.is_file()
    assert EV_MODULE.is_file()
    assert SAFETY_OWNER_MODULE.is_file()
    assert CRS_OWNER.is_file()
    assert INTENT_OWNER_MODULE.is_file()
    a06_source = A06_MODULE.read_text(encoding="utf-8")
    replay_source = REPLAY_MODULE.read_text(encoding="utf-8")
    assert "def compose_capital_risk_sizing_intent_from_core_evidence_v1(" in a06_source
    assert "bind_safety_kernel_offline_replay_evidence_v0" in replay_source
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "REPLAY_ORDERING_REMEDIATED_THIS_SLICE=false" in spec
    assert "XP03_ACTIVATED=false" in spec
    assert "ADAPTER_COMPUTE_OWNER=false" in spec
