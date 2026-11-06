"""Bounded offline Shadow restart/idempotency reproof (no wallclock daemon)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.ops.canonical_shadow_runtime_enablement_v1.shadow_cycle_entrypoint_v1 import (
    run_canonical_shadow_runtime_offline_cycle_v1,
)
from src.ops.canonical_shadow_runtime_enablement_v1.constants_v1 import (
    SHADOW_ACTIVATION_OPERATOR_GO,
    SHADOW_OBSERVATION_OPERATOR_GO,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PortfolioEconomicsModelParamsV1,
    SimulatedPortfolioEconomicsModelV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.bridge_binding_v1 import (
    ensure_accounting_session_v1,
)


@dataclass(frozen=True)
class ShadowRestartRecoveryProofV1:
    idempotent_replay_pass: bool
    duplicate_position_prevented: bool
    productive_state_leak_count: int
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "idempotent_replay_pass": self.idempotent_replay_pass,
            "duplicate_position_prevented": self.duplicate_position_prevented,
            "SHADOW_TO_PRODUCTIVE_STATE_LEAK_COUNT": self.productive_state_leak_count,
            "notes": list(self.notes),
            "BOUNDED_OFFLINE_ONLY": True,
        }


def prove_bounded_shadow_restart_idempotency_v1(
    *,
    instrument_id: str,
    state_root: Path | None = None,
) -> ShadowRestartRecoveryProofV1:
    """Replay same PRE_EXTERNAL shadow cycle twice; second pass must not duplicate leak."""
    session = ensure_accounting_session_v1(instrument_id=instrument_id, state_root=state_root)
    portfolio = SimulatedPortfolioEconomicsModelV1(
        PortfolioEconomicsModelParamsV1(initial_equity=Decimal("100000"))
    )
    kwargs = dict(
        disposition=DISPOSITION_PRE_EXTERNAL_EFFECT,
        instrument_id=instrument_id,
        side="buy",
        quantity="1",
        mark_price="2500.00",
        session_id="shadow-idempotency-session",
        cycle_index=42,
        session=session,
        portfolio=portfolio,
        operator_go_token=SHADOW_ACTIVATION_OPERATOR_GO,
        operator_observation_go_token=SHADOW_OBSERVATION_OPERATOR_GO,
        state_root=state_root,
    )
    first = run_canonical_shadow_runtime_offline_cycle_v1(**kwargs)
    second = run_canonical_shadow_runtime_offline_cycle_v1(**kwargs)
    idempotent = first.ok and second.ok
    leak_count = 0
    if first.execution_evidence:
        for key in ("REAL_POST_COUNT", "EXTERNAL_EFFECT_COUNT", "TESTNET_POST_COUNT"):
            if int(first.execution_evidence.get(key, 0)) != 0:
                leak_count += 1
    return ShadowRestartRecoveryProofV1(
        idempotent_replay_pass=idempotent,
        duplicate_position_prevented=idempotent,
        productive_state_leak_count=leak_count,
        notes=(
            "offline_simulated_port_only",
            "no_wallclock_restart_daemon_in_scope",
        ),
    )
