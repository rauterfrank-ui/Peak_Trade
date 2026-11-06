"""Shadow activation state model — IMPLEMENTED vs ACTIVATABLE vs AUTHORIZED vs RUNNING."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.ops.canonical_shadow_runtime_enablement_v1.observation_authorization_v1 import (
    evaluate_observation_authorization_mechanism_v1,
)
from src.ops.canonical_shadow_runtime_enablement_v1.proof_v1 import (
    prove_canonical_shadow_runtime_safety_v1,
)
from src.ops.canonical_shadow_runtime_enablement_v1.readiness_evaluator_v1 import (
    evaluate_shadow_readiness_dimensions_v1,
)
from src.ops.canonical_shadow_runtime_enablement_v1.shadow_runtime_bridge_v1 import (
    evaluate_shadow_runtime_bridge_v1,
)


@dataclass(frozen=True)
class ShadowActivationStateV1:
    shadow_implemented: bool
    shadow_activatable: bool
    shadow_authorized: bool
    shadow_running: bool
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "SHADOW_IMPLEMENTED": self.shadow_implemented,
            "SHADOW_ACTIVATABLE": self.shadow_activatable,
            "SHADOW_AUTHORIZED": self.shadow_authorized,
            "SHADOW_RUNNING": self.shadow_running,
            "blockers": list(self.blockers),
        }


def evaluate_shadow_activation_state_v1(
    *,
    repo_root: Path | None = None,
    operator_go_token: str | None = None,
    operator_observation_go_token: str | None = None,
    shadow_running: bool = False,
) -> ShadowActivationStateV1:
    root = (repo_root or Path(__file__).resolve().parents[3]).resolve()
    safety = prove_canonical_shadow_runtime_safety_v1()
    package_marker = (
        root / "src/ops/canonical_shadow_runtime_enablement_v1/constants_v1.py"
    ).is_file()
    implemented = package_marker and safety.get("ok") is True

    bridge_inactive = evaluate_shadow_runtime_bridge_v1(
        operator_go_token=None,
        observation_authorization_present=False,
    )
    bridge_bound_ready = bridge_inactive.bridge_ready and not bridge_inactive.bridge_activated

    obs_mech_ready, _ = evaluate_observation_authorization_mechanism_v1(repo_root=root)
    readiness = evaluate_shadow_readiness_dimensions_v1(
        bridge_activated=False,
        repo_root=root,
        for_activatable=True,
    )
    activatable = (
        implemented
        and bridge_bound_ready
        and obs_mech_ready
        and readiness.get("SHADOW_ACTIVATABLE") is True
    )

    bridge_active = evaluate_shadow_runtime_bridge_v1(
        operator_go_token=operator_go_token,
        operator_observation_go_token=operator_observation_go_token,
    )
    authorized = bridge_active.bridge_activated

    blockers: list[str] = []
    if not implemented:
        blockers.append("SHADOW_NOT_IMPLEMENTED")
    if not activatable:
        blockers.extend(readiness.get("ACTIVATABLE_BLOCKERS", []))
    if authorized and shadow_running is False:
        blockers.append("AUTHORIZED_BUT_NOT_RUNNING_BY_POLICY")

    return ShadowActivationStateV1(
        shadow_implemented=implemented,
        shadow_activatable=activatable,
        shadow_authorized=authorized,
        shadow_running=bool(shadow_running),
        blockers=tuple(blockers),
    )
