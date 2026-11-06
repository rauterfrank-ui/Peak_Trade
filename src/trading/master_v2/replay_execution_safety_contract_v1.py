# src/trading/master_v2/replay_execution_safety_contract_v1.py
"""Typed Replay Safety / Emergency contract for mapper consumption.

Derives from existing Replay Safety (pre-29Q) and Replay KS evidence (post-29Q).
Does not change decision_outcome. Does not grant execution permission.
Does not read durable FILEGATE / StatePersistence.

Pre-29Q Replay Safety remains the sole ENTER hard-block / decision-admission
authority before 29Q. Post-29Q KS typed fields are a POST_29Q_CONSUMPTION_GUARD:
they may HOLD/DENY consumption of an already produced ENTER plan. They are not
FILEGATE, not submission/wire permission, and not a second decision owner.

runtime_authority_effect=NONE means no execution/order/credential/FILEGATE
permission. It does not mean the typed emergency fields are consumption-inert.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 import (
    KillSwitchBoundaryMode,
    KillSwitchBoundaryOfflineReplayBoundaryV0,
    RUNTIME_AUTHORITY_EFFECT_NONE,
)
from trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0 import (
    SafetyKernelOfflineReplayBoundaryV0,
)

REPLAY_EXECUTION_SAFETY_CONTRACT_VERSION = "v1"
REPLAY_EXECUTION_SAFETY_CONTRACT_OWNER = "trading.master_v2.replay_execution_safety_contract_v1"
LEGACY_STRING_HEURISTIC_FALLBACK = "LEGACY_STRING_HEURISTIC_FALLBACK"
LEGACY_STRING_HEURISTIC_STATUS = "COMPATIBILITY_DEBT_RETAINED"
POST_29Q_CONSUMPTION_GUARD_ROLE = "POST_29Q_CONSUMPTION_GUARD"
POST_29Q_ROLE_NONE = "NONE"
CONSUMPTION_GUARD_EFFECT_ENTER_BLOCK = "ENTER_CONSUMPTION_BLOCK"
CONSUMPTION_GUARD_EFFECT_NONE = "NONE"
PRE_29Q_REPLAY_SAFETY_REASON = "PRE_29Q_REPLAY_SAFETY"
POST_29Q_CONSUMPTION_GUARD_REASON = "POST_29Q_CONSUMPTION_GUARD"


@dataclass(frozen=True)
class ReplayExecutionSafetyV1:
    """Mapper-facing typed Safety/Emergency view. Not FILEGATE. Not decision owner.

    entry_blocked = pre-29Q Replay Safety admission.
    emergency_boundary_active = post-29Q consumption-guard signal.
    runtime_authority_effect=NONE = no execution/order/credential/FILEGATE permission.
    post_29q_role / consumption_guard_effect name the post-29Q consumption role.
    """

    entry_blocked: bool
    emergency_boundary_active: bool
    emergency_mode: Optional[str]
    flatten_only: bool
    reduce_only: bool
    cancel_only: bool
    reason_codes: Tuple[str, ...]
    source_refs: Tuple[str, ...]
    runtime_authority_effect: str = RUNTIME_AUTHORITY_EFFECT_NONE
    contract_version: str = REPLAY_EXECUTION_SAFETY_CONTRACT_VERSION
    post_29q_role: str = POST_29Q_ROLE_NONE
    consumption_guard_effect: str = CONSUMPTION_GUARD_EFFECT_NONE


def derive_replay_execution_safety_v1(
    *,
    safety_boundary: SafetyKernelOfflineReplayBoundaryV0 | None = None,
    killswitch_boundary: KillSwitchBoundaryOfflineReplayBoundaryV0 | None = None,
) -> ReplayExecutionSafetyV1:
    """Project existing Safety + KS evidence into an explicit typed contract.

    No new decision semantics. Does not rewrite decision_outcome.
    Post-29Q KS projection is POST_29Q_CONSUMPTION_GUARD, not FILEGATE.
    """
    safety_hard = tuple(safety_boundary.hard_block_reasons) if safety_boundary is not None else ()
    safety_reasons = tuple(safety_boundary.reason_codes) if safety_boundary is not None else ()
    ks_reasons = tuple(killswitch_boundary.reason_codes) if killswitch_boundary is not None else ()
    ks_mode = None
    flatten_only = False
    reduce_only = False
    cancel_only = False
    emergency_active = False
    if killswitch_boundary is not None:
        ks_mode = str(killswitch_boundary.boundary_mode or "").strip() or None
        flatten_only = bool(killswitch_boundary.emergency_flatten_boundary_only)
        reduce_only = bool(killswitch_boundary.reduce_to_flat_boundary_only)
        cancel_only = bool(killswitch_boundary.cancel_pending_boundary_only)
        emergency_active = bool(
            (ks_mode and ks_mode != KillSwitchBoundaryMode.NORMAL.value)
            or flatten_only
            or killswitch_boundary.block_new_entry
            or killswitch_boundary.no_position_increase
            or reduce_only
            or cancel_only
        )
    source_refs: list[str] = []
    if safety_boundary is not None and safety_boundary.semantic_digest:
        source_refs.append(f"safety:{safety_boundary.semantic_digest}")
    if killswitch_boundary is not None and killswitch_boundary.semantic_digest:
        source_refs.append(f"killswitch:{killswitch_boundary.semantic_digest}")
    reason_codes = tuple(dict.fromkeys((*safety_reasons, *ks_reasons)))
    safety_authority = (
        safety_boundary.runtime_authority_effect
        if safety_boundary is not None
        else RUNTIME_AUTHORITY_EFFECT_NONE
    )
    ks_authority = (
        killswitch_boundary.runtime_authority_effect
        if killswitch_boundary is not None
        else RUNTIME_AUTHORITY_EFFECT_NONE
    )
    authority = (
        RUNTIME_AUTHORITY_EFFECT_NONE
        if safety_authority == RUNTIME_AUTHORITY_EFFECT_NONE
        and ks_authority == RUNTIME_AUTHORITY_EFFECT_NONE
        else RUNTIME_AUTHORITY_EFFECT_NONE
    )
    post_29q_role = (
        POST_29Q_CONSUMPTION_GUARD_ROLE if killswitch_boundary is not None else POST_29Q_ROLE_NONE
    )
    consumption_guard_effect = (
        CONSUMPTION_GUARD_EFFECT_ENTER_BLOCK if emergency_active else CONSUMPTION_GUARD_EFFECT_NONE
    )
    return ReplayExecutionSafetyV1(
        entry_blocked=bool(safety_hard),
        emergency_boundary_active=emergency_active,
        emergency_mode=ks_mode,
        flatten_only=flatten_only,
        reduce_only=reduce_only,
        cancel_only=cancel_only,
        reason_codes=reason_codes,
        source_refs=tuple(source_refs),
        runtime_authority_effect=authority,
        post_29q_role=post_29q_role,
        consumption_guard_effect=consumption_guard_effect,
    )


def legacy_string_heuristic_safety_blocked_v1(
    *,
    reason_codes: Tuple[str, ...] | list[str] | None,
    decision_outcome: str = "",
) -> bool:
    """Documented legacy fallback. Used only when typed contract is absent."""
    safety_codes = {str(x).lower() for x in (reason_codes or ())}
    outcome = str(decision_outcome or "").strip().lower()
    return any(
        x.startswith("safety") or "kill" in x or x.endswith("_blocked") for x in safety_codes
    ) or outcome in {"blocked"}


def typed_pre_29q_entry_blocked_v1(safety: ReplayExecutionSafetyV1) -> bool:
    """Pre-29Q Replay Safety hard-block. Not post-29Q KS. Not FILEGATE."""
    return bool(safety.entry_blocked)


def typed_post_29q_consumption_guard_blocks_enter_v1(safety: ReplayExecutionSafetyV1) -> bool:
    """Post-29Q consumption guard: block ENTER consumption without rewriting the plan."""
    return bool(safety.emergency_boundary_active)


def typed_enter_hold_required_v1(safety: ReplayExecutionSafetyV1) -> bool:
    """ENTER consumption HOLD when pre-29Q Safety hard-blocked or post-29Q guard active."""
    return bool(
        typed_pre_29q_entry_blocked_v1(safety)
        or typed_post_29q_consumption_guard_blocks_enter_v1(safety)
    )
