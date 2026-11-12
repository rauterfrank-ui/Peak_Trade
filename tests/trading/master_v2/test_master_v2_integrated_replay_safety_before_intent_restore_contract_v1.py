"""Integrated Replay compute-owner contract: 29P → Safety → 29Q.

ENTER hard-block skips 29Q. Downstream recon/killswitch binders still run.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.governance.canonical_order_intent_v1 import IntentAction
from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
    initial_directional_confirmation_side_state_carrier_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitDirectionState,
    ExistingPositionSide,
    PolicySignalV0,
    PositionState,
    SafetyMode,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    IntegratedOfflineReplayInputV1,
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
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
REPLAY_MODULE = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/MASTER_V2_INTEGRATED_REPLAY_SAFETY_BEFORE_INTENT_RESTORE_V1.md"
)
A06_MODULE = REPO_ROOT / "src/trading/master_v2/capital_risk_sizing_intent_restore_v1.py"
SIBLING_MODULE = REPO_ROOT / "src/trading/master_v2/capital_risk_sizing_safety_intent_restore_v1.py"
EV_MODULE = REPO_ROOT / "src/backtest/economic_viability_evidence_v1.py"
CRS_OWNER = REPO_ROOT / "src/governance/capital_risk_sizing_v1.py"
INTENT_OWNER = REPO_ROOT / "src/governance/canonical_order_intent_v1.py"
SAFETY_OWNER = (
    REPO_ROOT / "src/trading/master_v2/safety_kernel_offline_replay_binding_adapter_v0.py"
)
SIDESTATE_OWNER = REPO_ROOT / "src/trading/master_v2/double_play_state.py"
RECON_OWNER = (
    REPO_ROOT
    / "src/trading/master_v2/reconciliation_unknown_outcome_offline_replay_binding_adapter_v0.py"
)
KS_OWNER = (
    REPO_ROOT / "src/trading/master_v2/killswitch_boundary_offline_replay_binding_adapter_v0.py"
)
XP03 = (
    REPO_ROOT
    / "src/trading/master_v2/canonical_core_runtime_integration_intent_pipeline_bridge_v0.py"
)

_ENTER_OUTCOMES = frozenset({DecisionOutcome.ENTER_LONG.value, DecisionOutcome.ENTER_SHORT.value})


def _confirmed_replay_input(*, side: str) -> IntegratedOfflineReplayInputV1:
    acceptor, _committed = _distinct_acceptor()
    carrier = initial_directional_confirmation_side_state_carrier_v1(
        session_id=_session(),
        venue="okx_eea",
        instrument=_key(),
    )
    if side == "LONG":
        return _replay_input(
            side_state=SideState.LONG_ARMED,
            direction_state=EntryExitDirectionState.LONG_ARMED,
            scope_direction_state=ScopeDirectionState.LONG,
            policies=_policies_confirm_once(),
            price_path=(3500.0, 3570.0),
            directional_confirmation_progress=carrier,
            observation_acceptance_result=acceptor,
            confirmation_progress_session_id=_session(),
            confirmation_progress_venue="okx_eea",
            confirmation_progress_instrument=_key(),
        )
    return _replay_input(
        side_state=SideState.SHORT_ARMED,
        direction_state=EntryExitDirectionState.SHORT_ARMED,
        scope_direction_state=ScopeDirectionState.SHORT,
        policies=_policies_confirm_once(),
        price_path=(3500.0, 3430.0),
        directional_confirmation_progress=carrier,
        observation_acceptance_result=acceptor,
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
    )


def _exit_replay_input() -> IntegratedOfflineReplayInputV1:
    return _replay_input(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        side_state=SideState.LONG_ACTIVE,
        direction_state=EntryExitDirectionState.LONG_ACTIVE,
        safety_exit_signal=PolicySignalV0(triggered=True, reason_code="safety"),
    )


def _patch_replay_owners(
    monkeypatch: pytest.MonkeyPatch,
    *,
    force_safety_hard_block: bool = False,
):
    import trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 as coi_mod
    import trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 as crs_mod
    import trading.master_v2.integrated_offline_trading_logic_replay_v1 as replay_mod
    import trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 as ks_mod
    import trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0 as ruo_mod
    import trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0 as sk_mod

    order: list[str] = []
    counts = {
        "29P": 0,
        "SAFETY": 0,
        "29Q": 0,
        "RECON": 0,
        "KS": 0,
        "SIDESTATE": 0,
    }
    real_29p = crs_mod.bind_capital_risk_sizing_offline_replay_evidence_v0
    real_safety = sk_mod.bind_safety_kernel_offline_replay_evidence_v0
    real_29q = coi_mod.bind_canonical_order_intent_offline_replay_evidence_v0
    real_recon = ruo_mod.bind_reconciliation_unknown_outcome_offline_replay_evidence_v0
    real_ks = ks_mod.bind_killswitch_boundary_offline_replay_evidence_v0
    real_side = replay_mod.transition_state

    def wrap_29p(*args, **kwargs):
        order.append("29P")
        counts["29P"] += 1
        return real_29p(*args, **kwargs)

    def wrap_safety(evidence, *, context):
        order.append("SAFETY")
        counts["SAFETY"] += 1
        ctx = context
        if force_safety_hard_block:
            ctx = replace(context, killswitch_blocked=True, safety_decision_allowed=False)
        return real_safety(evidence, context=ctx)

    def wrap_29q(*args, **kwargs):
        order.append("29Q")
        counts["29Q"] += 1
        return real_29q(*args, **kwargs)

    def wrap_recon(*args, **kwargs):
        order.append("RECON")
        counts["RECON"] += 1
        return real_recon(*args, **kwargs)

    def wrap_ks(*args, **kwargs):
        order.append("KS")
        counts["KS"] += 1
        return real_ks(*args, **kwargs)

    def wrap_side(*args, **kwargs):
        counts["SIDESTATE"] += 1
        return real_side(*args, **kwargs)

    monkeypatch.setattr(crs_mod, "bind_capital_risk_sizing_offline_replay_evidence_v0", wrap_29p)
    monkeypatch.setattr(sk_mod, "bind_safety_kernel_offline_replay_evidence_v0", wrap_safety)
    monkeypatch.setattr(coi_mod, "bind_canonical_order_intent_offline_replay_evidence_v0", wrap_29q)
    monkeypatch.setattr(
        ruo_mod, "bind_reconciliation_unknown_outcome_offline_replay_evidence_v0", wrap_recon
    )
    monkeypatch.setattr(ks_mod, "bind_killswitch_boundary_offline_replay_evidence_v0", wrap_ks)
    monkeypatch.setattr(replay_mod, "transition_state", wrap_side)
    return order, counts


def test_source_and_spec_restore_safety_before_intent() -> None:
    source = REPLAY_MODULE.read_text(encoding="utf-8")
    crs = source.index("bind_capital_risk_sizing_offline_replay_evidence_v0(")
    safety = source.index("bind_safety_kernel_offline_replay_evidence_v0(")
    intent = source.index("bind_canonical_order_intent_offline_replay_evidence_v0(")
    recon = source.index("bind_reconciliation_unknown_outcome_offline_replay_evidence_v0(")
    ks = source.index("bind_killswitch_boundary_offline_replay_evidence_v0(")
    assert crs < safety < intent < recon < ks
    assert source.count("bind_capital_risk_sizing_offline_replay_evidence_v0(") == 1
    assert source.count("bind_safety_kernel_offline_replay_evidence_v0(") == 1
    assert source.count("bind_canonical_order_intent_offline_replay_evidence_v0(") == 1
    assert source.count("transition_state(") == 1
    assert "SafetyKernelOfflineReplayContextV0()" not in source
    assert "capital_risk_sizing_safety_intent_restore_v1" not in source
    assert "compose_capital_risk_sizing_intent_from_core_evidence_v1" not in source
    assert "run_canonical_core_runtime_integration_intent_pipeline" not in source
    assert "economic_viability_evidence_v1" not in source
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "RESTORATION_TARGET_ID=MASTER_V2_DOUBLE_PLAY_CONSERVED_REFERENCE_V1" in spec
    assert "SLICE_ID=INTEGRATED_REPLAY_SAFETY_BEFORE_INTENT_COMPUTE_OWNER_REWIRE_V1" in spec
    assert "HISTORICAL_ORDER=Risk/Sizing → Safety → Intent" in spec
    assert "PREVIOUS_CURRENT_ORDER=Risk/Sizing → Intent → Safety" in spec
    assert "RESTORED_REPLAY_ORDER=Risk/Sizing → Safety → Intent" in spec
    assert "COMPUTE_OWNER_IDENTITY_CHANGED=false" in spec
    assert "COMPUTE_OWNER_AUTHORITY_CHANGED=false" in spec
    assert "COMPUTE_OWNER_WIRING_CHANGED=true" in spec
    assert "HISTORICAL_STAGE=Safety" in spec
    assert "A07_IDENTITY_STATUS=UNPROVEN" in spec
    assert "PROGRAM_LABEL=A08_REMAINDER" in spec
    assert INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER.endswith(
        "integrated_offline_trading_logic_replay_v1"
    )
    assert A06_MODULE.is_file()
    assert SIBLING_MODULE.is_file()
    assert EV_MODULE.is_file()
    assert CRS_OWNER.is_file()
    assert INTENT_OWNER.is_file()
    assert SAFETY_OWNER.is_file()
    assert SIDESTATE_OWNER.is_file()
    assert RECON_OWNER.is_file()
    assert KS_OWNER.is_file()
    assert XP03.is_file()


def test_call_order_pass_path_enter_long(monkeypatch: pytest.MonkeyPatch) -> None:
    order, counts = _patch_replay_owners(monkeypatch)
    result = run_integrated_offline_trading_logic_replay_v1(_confirmed_replay_input(side="LONG"))
    assert result.evidence.decision_outcome == DecisionOutcome.ENTER_LONG.value
    assert order == ["29P", "SAFETY", "29Q", "RECON", "KS"]
    assert counts["29P"] == 1
    assert counts["SAFETY"] == 1
    assert counts["29Q"] == 1
    assert counts["RECON"] == 1
    assert counts["KS"] == 1
    assert counts["SIDESTATE"] == 1
    intent = result.intermediate.canonical_order_intent if result.intermediate else None
    assert intent is not None
    assert intent.intent_action == IntentAction.ENTER_LONG.value
    assert intent.submission_authorized is False
    assert intent.execution_eligible is False
    assert result.evidence.safety_boundary_ref
    assert result.evidence.reconciliation_unknown_outcome_ref
    assert result.evidence.killswitch_boundary_ref


def test_blocked_enter_long_skips_29q_and_keeps_downstream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    order, counts = _patch_replay_owners(monkeypatch, force_safety_hard_block=True)
    result = run_integrated_offline_trading_logic_replay_v1(_confirmed_replay_input(side="LONG"))
    assert result.evidence.decision_outcome == DecisionOutcome.ENTER_LONG.value
    assert "29Q" not in order
    assert order == ["29P", "SAFETY", "RECON", "KS"]
    assert counts["29P"] == 1
    assert counts["SAFETY"] == 1
    assert counts["29Q"] == 0
    assert counts["RECON"] == 1
    assert counts["KS"] == 1
    assert counts["SIDESTATE"] == 1
    assert result.intermediate is not None
    assert result.intermediate.canonical_order_intent is None
    assert result.replay_pass is True or result.fail_reasons is not None
    assert result.evidence.safety_boundary_ref
    assert result.evidence.reconciliation_unknown_outcome_ref
    assert result.evidence.killswitch_boundary_ref
    assert "killswitch_blocked" in result.evidence.reason_codes
    assert "entry_blocked_by_safety_kernel_boundary" in result.evidence.reason_codes


def test_blocked_enter_short_skips_29q_and_keeps_downstream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    order, counts = _patch_replay_owners(monkeypatch, force_safety_hard_block=True)
    result = run_integrated_offline_trading_logic_replay_v1(_confirmed_replay_input(side="SHORT"))
    assert result.evidence.decision_outcome == DecisionOutcome.ENTER_SHORT.value
    assert "29Q" not in order
    assert order == ["29P", "SAFETY", "RECON", "KS"]
    assert counts["29Q"] == 0
    assert counts["RECON"] == 1
    assert counts["KS"] == 1
    assert counts["SIDESTATE"] == 1
    assert result.intermediate is not None
    assert result.intermediate.canonical_order_intent is None
    intent = result.intermediate.canonical_order_intent
    assert intent is None or intent.intent_action not in {
        IntentAction.ENTER_LONG.value,
        IntentAction.ENTER_SHORT.value,
    }


def test_safety_pass_enter_short_plan_only_once(monkeypatch: pytest.MonkeyPatch) -> None:
    order, counts = _patch_replay_owners(monkeypatch)
    result = run_integrated_offline_trading_logic_replay_v1(_confirmed_replay_input(side="SHORT"))
    assert result.evidence.decision_outcome == DecisionOutcome.ENTER_SHORT.value
    assert order == ["29P", "SAFETY", "29Q", "RECON", "KS"]
    assert counts["29Q"] == 1
    intent = result.intermediate.canonical_order_intent if result.intermediate else None
    if intent is not None:
        assert intent.intent_action == IntentAction.ENTER_SHORT.value
        assert intent.submission_authorized is False
        assert intent.execution_eligible is False


def test_no_pre_safety_intent_and_no_duplicate_29q(monkeypatch: pytest.MonkeyPatch) -> None:
    order, counts = _patch_replay_owners(monkeypatch)
    run_integrated_offline_trading_logic_replay_v1(_confirmed_replay_input(side="LONG"))
    assert order.index("SAFETY") < order.index("29Q")
    assert counts["29Q"] == 1
    assert order.count("29Q") == 1


def test_missing_safety_context_has_no_implicit_normal_default() -> None:
    with pytest.raises(TypeError):
        IntegratedOfflineReplayInputV1()  # type: ignore[call-arg]
    source = REPLAY_MODULE.read_text(encoding="utf-8")
    assert "SafetyKernelOfflineReplayContextV0()" not in source
    assert (
        "safety_mode=SafetyMode.NORMAL,"
        not in source.split("bind_safety_kernel_offline_replay_evidence_v0", 1)[1]
    )


def test_exit_progression_does_not_use_enter_suppression(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    order, counts = _patch_replay_owners(monkeypatch)
    result = run_integrated_offline_trading_logic_replay_v1(_exit_replay_input())
    assert result.evidence.decision_outcome == DecisionOutcome.EXIT.value
    assert result.evidence.decision_outcome not in _ENTER_OUTCOMES
    assert counts["SAFETY"] == 1
    assert counts["29Q"] == 1
    assert "SAFETY" in order and "29Q" in order
    assert order.index("SAFETY") < order.index("29Q")
    assert counts["RECON"] == 1
    assert counts["KS"] == 1
    intent = result.intermediate.canonical_order_intent if result.intermediate else None
    if intent is not None:
        assert intent.intent_action not in {
            IntentAction.ENTER_LONG.value,
            IntentAction.ENTER_SHORT.value,
        }
        assert intent.submission_authorized is False
