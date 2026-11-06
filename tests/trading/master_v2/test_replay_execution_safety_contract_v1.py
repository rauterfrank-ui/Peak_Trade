"""Typed Replay Safety/Emergency contract: derive from existing Safety + KS evidence."""

from __future__ import annotations

from trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 import (
    KillSwitchBoundaryMode,
    KillSwitchBoundaryOfflineReplayContextV0,
    evaluate_offline_killswitch_boundary_v0,
)
from trading.master_v2.replay_execution_safety_contract_v1 import (
    CONSUMPTION_GUARD_EFFECT_ENTER_BLOCK,
    CONSUMPTION_GUARD_EFFECT_NONE,
    POST_29Q_CONSUMPTION_GUARD_ROLE,
    POST_29Q_ROLE_NONE,
    derive_replay_execution_safety_v1,
    legacy_string_heuristic_safety_blocked_v1,
    typed_enter_hold_required_v1,
    typed_post_29q_consumption_guard_blocks_enter_v1,
    typed_pre_29q_entry_blocked_v1,
)
from trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0 import (
    SafetyKernelOfflineReplayContextV0,
    evaluate_offline_safety_kernel_boundary_v0,
)


def test_typed_contract_runtime_authority_is_none() -> None:
    safety = evaluate_offline_safety_kernel_boundary_v0(
        SafetyKernelOfflineReplayContextV0(),
        decision_outcome="enter_long",
    )
    ks = evaluate_offline_killswitch_boundary_v0(
        KillSwitchBoundaryOfflineReplayContextV0(),
        decision_outcome="enter_long",
    )
    typed = derive_replay_execution_safety_v1(safety_boundary=safety, killswitch_boundary=ks)
    assert typed.runtime_authority_effect == "NONE"
    assert typed.entry_blocked is False
    assert typed.emergency_boundary_active is False


def test_safety_hard_block_sets_entry_blocked() -> None:
    safety = evaluate_offline_safety_kernel_boundary_v0(
        SafetyKernelOfflineReplayContextV0(
            killswitch_blocked=True,
            safety_decision_allowed=False,
        ),
        decision_outcome="enter_long",
    )
    typed = derive_replay_execution_safety_v1(safety_boundary=safety)
    assert typed.entry_blocked is True
    assert typed_enter_hold_required_v1(typed) is True
    assert "killswitch_blocked" in typed.reason_codes


def test_emergency_flatten_sets_emergency_boundary() -> None:
    ks = evaluate_offline_killswitch_boundary_v0(
        KillSwitchBoundaryOfflineReplayContextV0(
            boundary_mode=KillSwitchBoundaryMode.EMERGENCY_FLATTEN,
            killswitch_active=True,
        ),
        decision_outcome="enter_long",
    )
    typed = derive_replay_execution_safety_v1(killswitch_boundary=ks)
    assert typed.emergency_boundary_active is True
    assert typed.flatten_only is True
    assert typed.emergency_mode == KillSwitchBoundaryMode.EMERGENCY_FLATTEN.value
    assert typed.runtime_authority_effect == "NONE"
    assert typed.post_29q_role == POST_29Q_CONSUMPTION_GUARD_ROLE
    assert typed.consumption_guard_effect == CONSUMPTION_GUARD_EFFECT_ENTER_BLOCK
    assert typed_enter_hold_required_v1(typed) is True
    assert typed_pre_29q_entry_blocked_v1(typed) is False
    assert typed_post_29q_consumption_guard_blocks_enter_v1(typed) is True


def test_reduce_and_cancel_modes_are_explicit() -> None:
    reduce_ks = evaluate_offline_killswitch_boundary_v0(
        KillSwitchBoundaryOfflineReplayContextV0(
            boundary_mode=KillSwitchBoundaryMode.REDUCE_TO_FLAT,
            killswitch_active=True,
        )
    )
    cancel_ks = evaluate_offline_killswitch_boundary_v0(
        KillSwitchBoundaryOfflineReplayContextV0(
            boundary_mode=KillSwitchBoundaryMode.CANCEL_PENDING,
            killswitch_active=True,
        )
    )
    reduce_typed = derive_replay_execution_safety_v1(killswitch_boundary=reduce_ks)
    cancel_typed = derive_replay_execution_safety_v1(killswitch_boundary=cancel_ks)
    assert reduce_typed.reduce_only is True
    assert reduce_typed.emergency_boundary_active is True
    assert cancel_typed.cancel_only is True
    assert cancel_typed.emergency_boundary_active is True


def test_legacy_heuristic_parity_with_typed_kill_reason() -> None:
    reasons = ("killswitch_emergency_flatten",)
    legacy = legacy_string_heuristic_safety_blocked_v1(
        reason_codes=reasons,
        decision_outcome="enter_long",
    )
    ks = evaluate_offline_killswitch_boundary_v0(
        KillSwitchBoundaryOfflineReplayContextV0(
            boundary_mode=KillSwitchBoundaryMode.EMERGENCY_FLATTEN,
            killswitch_active=True,
        ),
        decision_outcome="enter_long",
    )
    typed = derive_replay_execution_safety_v1(killswitch_boundary=ks)
    assert legacy is True
    assert typed_enter_hold_required_v1(typed) is True


def test_ks_binder_does_not_mutate_decision_outcome_or_grant_submission() -> None:
    from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _run
    from trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 import (
        bind_killswitch_boundary_offline_replay_evidence_v0,
    )

    replay = _run()
    original_outcome = replay.evidence.decision_outcome
    bound = bind_killswitch_boundary_offline_replay_evidence_v0(
        replay.evidence,
        context=KillSwitchBoundaryOfflineReplayContextV0(
            boundary_mode=KillSwitchBoundaryMode.EMERGENCY_FLATTEN,
            killswitch_active=True,
        ),
    )
    assert bound.evidence.decision_outcome == original_outcome
    assert bound.boundary.runtime_authority_effect == "NONE"
    assert bound.boundary.order_effect == "NONE"
    assert bound.evidence.execution_eligible is False
    assert all("FILEGATE" not in str(code) for code in bound.boundary.reason_codes)
    assert all(code != "FILEGATE_KILLED" for code in bound.boundary.reason_codes)


def test_normal_ks_mode_is_consumption_guard_owner_with_none_effect() -> None:
    ks = evaluate_offline_killswitch_boundary_v0(
        KillSwitchBoundaryOfflineReplayContextV0(),
        decision_outcome="enter_long",
    )
    typed = derive_replay_execution_safety_v1(killswitch_boundary=ks)
    assert typed.post_29q_role == POST_29Q_CONSUMPTION_GUARD_ROLE
    assert typed.consumption_guard_effect == CONSUMPTION_GUARD_EFFECT_NONE
    assert typed.emergency_boundary_active is False
    assert typed.runtime_authority_effect == "NONE"


def test_safety_only_projection_has_no_post_29q_role() -> None:
    safety = evaluate_offline_safety_kernel_boundary_v0(
        SafetyKernelOfflineReplayContextV0(),
        decision_outcome="enter_long",
    )
    typed = derive_replay_execution_safety_v1(safety_boundary=safety)
    assert typed.post_29q_role == POST_29Q_ROLE_NONE
    assert typed.consumption_guard_effect == CONSUMPTION_GUARD_EFFECT_NONE
    assert typed_pre_29q_entry_blocked_v1(typed) is False


def test_productive_replay_projects_post_29q_guard_without_filegate() -> None:
    from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _run

    replay = _run()
    typed = replay.replay_execution_safety
    assert typed is not None
    assert typed.post_29q_role == POST_29Q_CONSUMPTION_GUARD_ROLE
    assert typed.runtime_authority_effect == "NONE"
    assert replay.evidence.execution_eligible is False
    if replay.intermediate is not None and replay.intermediate.canonical_order_intent is not None:
        assert replay.intermediate.canonical_order_intent.submission_authorized is False
