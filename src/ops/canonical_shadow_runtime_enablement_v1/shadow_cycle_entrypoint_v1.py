"""Canonical Shadow runtime offline cycle entrypoint (executable contract, not activation)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.ops.canonical_shadow_runtime_enablement_v1.constants_v1 import EXECUTION_LANE_SHADOW
from src.ops.canonical_shadow_runtime_enablement_v1.pre_external_lane_isolation_v1 import (
    assert_pre_external_disposition_v1,
    resolve_post_pre_external_continuation_v1,
)
from src.ops.canonical_shadow_runtime_enablement_v1.shadow_execution_sink_v1 import (
    ShadowExecutionRequestV1,
    execute_shadow_simulated_intent_v1,
)
from src.ops.canonical_shadow_runtime_enablement_v1.shadow_runtime_bridge_v1 import (
    evaluate_shadow_runtime_bridge_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)


@dataclass(frozen=True)
class CanonicalShadowRuntimeCycleResultV1:
    ok: bool
    continuation: str
    bridge: dict[str, Any]
    execution_evidence: dict[str, Any] | None
    fail_reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "continuation": self.continuation,
            "bridge": self.bridge,
            "execution_evidence": self.execution_evidence,
            "fail_reason": self.fail_reason,
        }


def run_canonical_shadow_runtime_offline_cycle_v1(
    *,
    disposition: str,
    instrument_id: str,
    side: str,
    quantity: str,
    mark_price: str,
    session_id: str,
    cycle_index: int,
    session: Any,
    portfolio: Any,
    operator_go_token: str | None = None,
    observation_authorization_present: bool = False,
    operator_observation_go_token: str | None = None,
    kill_switch_engaged: bool = False,
    state_root: Path | None = None,
) -> CanonicalShadowRuntimeCycleResultV1:
    """Run one Shadow lane cycle after PRE_EXTERNAL (offline simulated execution only)."""
    try:
        assert_pre_external_disposition_v1(disposition=disposition)
        continuation = resolve_post_pre_external_continuation_v1(
            execution_lane=EXECUTION_LANE_SHADOW,
            pre_external_reached=disposition == DISPOSITION_PRE_EXTERNAL_EFFECT,
        )
    except Exception as exc:  # noqa: BLE001 — fail-closed envelope
        return CanonicalShadowRuntimeCycleResultV1(
            ok=False,
            continuation="",
            bridge={},
            execution_evidence=None,
            fail_reason=str(exc),
        )

    bridge = evaluate_shadow_runtime_bridge_v1(
        operator_go_token=operator_go_token,
        observation_authorization_present=observation_authorization_present,
        operator_observation_go_token=operator_observation_go_token,
        kill_switch_engaged=kill_switch_engaged,
    )
    if not bridge.bridge_activated:
        return CanonicalShadowRuntimeCycleResultV1(
            ok=False,
            continuation=continuation,
            bridge=bridge.to_dict(),
            execution_evidence=None,
            fail_reason="shadow_runtime_bridge_not_activated",
        )

    request = ShadowExecutionRequestV1(
        instrument_id=instrument_id,
        side=side,
        quantity=quantity,
        mark_price=mark_price,
        session_id=session_id,
        cycle_index=cycle_index,
    )
    _apply, evidence = execute_shadow_simulated_intent_v1(
        request=request,
        session=session,
        portfolio=portfolio,
        state_root=state_root,
    )
    return CanonicalShadowRuntimeCycleResultV1(
        ok=True,
        continuation=continuation,
        bridge=bridge.to_dict(),
        execution_evidence=evidence.to_dict(),
        fail_reason="",
    )
