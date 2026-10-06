"""Optional DDO learning capture join for CURRENT productive Master-V2 cycle.

Observation-only: binds ``DdoCaptureBindingV0`` around integrated offline replay
and invokes ``record_productive_cycle_capture_v0`` after the authoritative replay.
Does not change replay decisions. AUTHORITY_EFFECT=NONE.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    CAPTURE_FAILURE_CHANGES_DECISION,
    DdoCaptureBindingV0,
    bind_capture_session_v0,
    record_productive_cycle_capture_v0,
    reset_capture_session_v0,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayInputV1,
    IntegratedOfflineReplayResultV1,
    run_integrated_offline_trading_logic_replay_v1,
)

assert CAPTURE_FAILURE_CHANGES_DECISION is False


def build_productive_ddo_capture_binding_v1(*, ledger_path: Path) -> DdoCaptureBindingV0:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    return DdoCaptureBindingV0(enabled=True, ledger_path=ledger_path)


def run_integrated_offline_replay_with_productive_ddo_capture_v1(
    bind_input: IntegratedOfflineReplayInputV1,
    *,
    ddo_capture_binding: DdoCaptureBindingV0 | None,
    repository_sha: str,
    session_id: str,
    cycle_index: int,
    event_ts_unix: float,
    observation_acceptance_result: Any,
    features: Any,
    confirmation_binding: Any,
) -> tuple[IntegratedOfflineReplayResultV1, dict[str, Any] | None]:
    """Run replay; when binding is enabled, observe producer results fail-open."""
    capture_token = None
    if ddo_capture_binding is not None and ddo_capture_binding.enabled:
        capture_token = bind_capture_session_v0(ddo_capture_binding)
    try:
        replay = run_integrated_offline_trading_logic_replay_v1(bind_input)
    finally:
        if capture_token is not None:
            reset_capture_session_v0(capture_token)

    scope_capture_binding: Any = None
    intermediate = getattr(replay, "intermediate", None)
    if intermediate is not None:
        scope_capture_binding = getattr(intermediate, "scope_event", None)

    summary: dict[str, Any] | None = None
    if ddo_capture_binding is not None and ddo_capture_binding.enabled:
        summary = dict(
            record_productive_cycle_capture_v0(
                ddo_capture_binding,
                repository_sha=repository_sha,
                session_id=session_id,
                cycle_index=cycle_index,
                event_ts_unix=event_ts_unix,
                observation_acceptance_result=observation_acceptance_result,
                features=features,
                replay=replay,
                confirmation_binding=confirmation_binding,
                dynamic_scope_binding=scope_capture_binding,
            )
        )
    return replay, summary
