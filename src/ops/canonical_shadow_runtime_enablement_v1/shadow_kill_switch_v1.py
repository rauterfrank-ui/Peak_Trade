"""Shadow kill-switch — fail-closed stop without Live/Testnet promotion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.canonical_shadow_runtime_enablement_v1.constants_v1 import (
    SHADOW_KILL_SWITCH_DISENGAGED,
    SHADOW_KILL_SWITCH_ENGAGED,
    TESTNET_AUTHORIZED,
)


@dataclass(frozen=True)
class ShadowKillSwitchEvaluationV1:
    kill_switch_state: str
    shadow_continuation_permitted: bool
    mechanism_ready: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "kill_switch_state": self.kill_switch_state,
            "shadow_continuation_permitted": self.shadow_continuation_permitted,
            "KILL_SWITCH_MECHANISM_READY": self.mechanism_ready,
            "TESTNET_AUTHORIZED": TESTNET_AUTHORIZED,
        }


def evaluate_shadow_kill_switch_v1(
    *,
    kill_switch_engaged: bool = False,
) -> ShadowKillSwitchEvaluationV1:
    """Engaged kill-switch blocks further Shadow continuation; never arms Live/Testnet."""
    state = SHADOW_KILL_SWITCH_ENGAGED if kill_switch_engaged else SHADOW_KILL_SWITCH_DISENGAGED
    return ShadowKillSwitchEvaluationV1(
        kill_switch_state=state,
        shadow_continuation_permitted=not kill_switch_engaged,
        mechanism_ready=True,
    )
