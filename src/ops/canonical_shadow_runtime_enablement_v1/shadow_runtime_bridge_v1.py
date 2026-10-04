"""Canonical Shadow runtime bridge — BOUND_READY vs ACTIVATED (operator GO required)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.canonical_shadow_runtime_enablement_v1.constants_v1 import (
    RUNTIME_BRIDGE_STATE_ACTIVATED,
    RUNTIME_BRIDGE_STATE_BOUND_NOT_ACTIVATED,
    RUNTIME_BRIDGE_STATE_BOUND_READY,
    SHADOW_ACTIVATION_OPERATOR_GO,
)


class ShadowRuntimeBridgeError(ValueError):
    pass


@dataclass(frozen=True)
class ShadowRuntimeBridgeEvaluationV1:
    runtime_bridge_state: str
    operator_go_consumed: bool
    observation_authorization_present: bool
    bridge_ready: bool
    bridge_activated: bool
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtime_bridge_state": self.runtime_bridge_state,
            "operator_go_consumed": self.operator_go_consumed,
            "observation_authorization_present": self.observation_authorization_present,
            "bridge_ready": self.bridge_ready,
            "bridge_activated": self.bridge_activated,
            "blockers": list(self.blockers),
        }


def evaluate_shadow_runtime_bridge_v1(
    *,
    operator_go_token: str | None,
    observation_authorization_present: bool = False,
) -> ShadowRuntimeBridgeEvaluationV1:
    """Classify bridge state. ACTIVATED only when exact operator GO consumed."""
    go_ok = str(operator_go_token or "").strip() == SHADOW_ACTIVATION_OPERATOR_GO
    blockers: list[str] = []
    if not observation_authorization_present:
        blockers.append("PAPER_SHADOW_OBSERVATION_NOT_AUTHORIZED")
    if not go_ok:
        blockers.append("NO_ACTIVATION_AUTHORIZED")
        state = RUNTIME_BRIDGE_STATE_BOUND_READY
        return ShadowRuntimeBridgeEvaluationV1(
            runtime_bridge_state=state,
            operator_go_consumed=False,
            observation_authorization_present=observation_authorization_present,
            bridge_ready=True,
            bridge_activated=False,
            blockers=tuple(blockers),
        )
    if not observation_authorization_present:
        state = RUNTIME_BRIDGE_STATE_BOUND_NOT_ACTIVATED
        return ShadowRuntimeBridgeEvaluationV1(
            runtime_bridge_state=state,
            operator_go_consumed=True,
            observation_authorization_present=False,
            bridge_ready=False,
            bridge_activated=False,
            blockers=tuple(blockers),
        )
    return ShadowRuntimeBridgeEvaluationV1(
        runtime_bridge_state=RUNTIME_BRIDGE_STATE_ACTIVATED,
        operator_go_consumed=True,
        observation_authorization_present=True,
        bridge_ready=True,
        bridge_activated=True,
        blockers=(),
    )
