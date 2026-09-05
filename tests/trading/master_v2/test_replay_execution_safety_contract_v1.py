"""Typed Replay Safety/Emergency contract: derive from existing Safety + KS evidence."""

from __future__ import annotations

from trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 import (
    KillSwitchBoundaryMode,
    KillSwitchBoundaryOfflineReplayContextV0,
    evaluate_offline_killswitch_boundary_v0,
)
from trading.master_v2.replay_execution_safety_contract_v1 import (
    derive_replay_execution_safety_v1,
    legacy_string_heuristic_safety_blocked_v1,
    typed_enter_hold_required_v1,
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
    assert typed_enter_hold_required_v1(typed) is True


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
