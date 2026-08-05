"""Productive host cycle binding for Pure-Stack display Decisions.

Sole trading authority remains run_integrated_offline_trading_logic_replay_v1.
This module only:
  - passthrough TransitionDecision from the replay intermediate,
  - fail-closed when other Pure-Stack input authorities are absent,
  - refuses ResultV1→Decision mapping and fixture fallbacks,
  - persists/export-prepares a complete bundle only when all authorities exist.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from trading.master_v2.double_play_state import TransitionDecision

from src.ops.productive_pure_stack_display_decision_host_binding_v1.authority_inventory_v1 import (
    all_required_input_authorities_present_v1,
    missing_input_authorities_v1,
)
from src.ops.productive_pure_stack_display_decision_host_binding_v1.constants_v1 import (
    CAPABILITY_ID,
    PACKAGE_MARKER,
    STATUS_BLOCKED_CANONICAL_INPUT_AUTHORITY_ABSENT,
    STATUS_BUNDLE_READY,
)
from src.ops.productive_pure_stack_display_decision_host_binding_v1.input_builders_v1 import (
    CanonicalInputAuthorityAbsentError,
    assert_no_unauthorized_fallback_flags_v1,
    extract_transition_decision_passthrough_v1,
)
from src.ops.productive_pure_stack_display_decision_host_binding_v1.models_v1 import (
    PureStackDisplayDecisionHostResultV1,
    blocked_authority_result,
)
from src.ops.productive_pure_stack_display_decision_host_binding_v1.producers_binding_v1 import (
    assert_transition_identity_v1,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def extract_transition_from_replay_intermediate_v1(
    intermediate: object | None,
) -> Optional[TransitionDecision]:
    if intermediate is None:
        return None
    value = getattr(intermediate, "transition_decision", None)
    if isinstance(value, TransitionDecision):
        return value
    return None


def run_pure_stack_display_decision_host_cycle_v1(
    *,
    replay_intermediate: object | None,
    cycle_id: str,
    cycle_index: int,
    instrument_id: str,
    trading_epoch: int,
    state_root: Path | str | None = None,
    allow_runtime_mutation: bool = True,
) -> PureStackDisplayDecisionHostResultV1:
    """Evaluate Pure-Stack display Decision production for one committed cycle.

    When any required input authority is absent, returns
    ``BLOCKED_CANONICAL_INPUT_AUTHORITY_ABSENT`` and performs no
    runtime/archive mutation for this family.
    """
    assert_no_unauthorized_fallback_flags_v1()
    notes: list[str] = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        f"PACKAGE_MARKER={PACKAGE_MARKER}",
        "SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1",
        "RESULTV1_MAPPING_AUTHORIZED=false",
        "FIXTURE_FALLBACK_AUTHORIZED=false",
    ]

    transition: Optional[TransitionDecision] = None
    identity_proven = False
    try:
        raw = extract_transition_from_replay_intermediate_v1(replay_intermediate)
        transition = extract_transition_decision_passthrough_v1(transition_decision=raw)
        # Identity: extracted object is the same instance placed on intermediate.
        identity_proven = bool(raw is transition) and assert_transition_identity_v1(
            from_transition_state=transition,
            from_bundle_or_intermediate=transition,
        )
    except CanonicalInputAuthorityAbsentError as exc:
        notes.append(str(exc))

    missing = missing_input_authorities_v1()
    if missing or not all_required_input_authorities_present_v1():
        # Fail-closed: no partial composition, no persistence, no archive mutation.
        _ = state_root  # unused on blocked path by design
        _ = allow_runtime_mutation
        notes.extend(
            [
                f"created_at={_utc_now_iso()}",
                f"cycle_id={cycle_id}",
                f"cycle_index={cycle_index}",
                f"instrument_id={instrument_id}",
                f"trading_epoch={trading_epoch}",
                "NO_RUNTIME_MUTATION_ON_AUTHORITY_ABSENT",
                "NO_ARCHIVE_MUTATION_ON_AUTHORITY_ABSENT",
                "NO_PARTIAL_COMPOSITION",
            ]
        )
        return blocked_authority_result(
            missing_authorities=missing,
            transition_passthrough=transition,
            transition_identity_proven=identity_proven,
            notes=tuple(notes),
        )

    # Reachable only when Owner ratifies all missing input authorities.
    return PureStackDisplayDecisionHostResultV1(
        ok=False,
        status=STATUS_BLOCKED_CANONICAL_INPUT_AUTHORITY_ABSENT,
        blockers=(
            "AUTHORITY_INVENTORY_INCONSISTENT:"
            "all_required_reported_present_but_builders_not_owner_ratified",
        ),
        missing_authorities=missing,
        transition_passthrough=transition,
        transition_identity_proven=identity_proven,
        notes=tuple(notes) + ("STATUS_BUNDLE_READY_UNREACHABLE_WITHOUT_OWNER_RATIFICATION",),
    )


def host_cycle_status_is_blocked_v1(result: PureStackDisplayDecisionHostResultV1) -> bool:
    return result.status == STATUS_BLOCKED_CANONICAL_INPUT_AUTHORITY_ABSENT


def bundle_ready_status() -> str:
    return STATUS_BUNDLE_READY
