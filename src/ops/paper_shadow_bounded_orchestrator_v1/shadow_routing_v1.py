"""PRE_EXTERNAL -> canonical Shadow boundary (same event identity)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.ops.canonical_shadow_runtime_enablement_v1.constants_v1 import (
    SHADOW_ACTIVATION_OPERATOR_GO,
    SHADOW_OBSERVATION_OPERATOR_GO,
)
from src.ops.canonical_shadow_runtime_enablement_v1.shadow_cycle_entrypoint_v1 import (
    run_canonical_shadow_runtime_offline_cycle_v1,
)
from src.ops.canonical_shadow_runtime_enablement_v1.shadow_reconciliation_v1 import (
    ShadowReconciliationLedgerV1,
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
class PreExternalProductiveEventV1:
    event_key: str
    flight_id: str
    cycle_id: int
    instrument_id: str
    side: str
    quantity: str
    mark_price: str
    terminal_disposition: str
    substituted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_key": self.event_key,
            "flight_id": self.flight_id,
            "cycle_id": self.cycle_id,
            "instrument_id": self.instrument_id,
            "side": self.side,
            "quantity": self.quantity,
            "mark_price": self.mark_price,
            "terminal_disposition": self.terminal_disposition,
            "substituted": self.substituted,
        }


@dataclass
class ShadowRoutingResultV1:
    ok: bool
    shadow_continuation: bool
    event: PreExternalProductiveEventV1 | None
    shadow_evidence: dict[str, Any] | None
    reconcile: dict[str, Any] | None
    fail_reason: str
    causal_event_identity_break_count: int = 0
    event_substitution_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "shadow_continuation": self.shadow_continuation,
            "event": None if self.event is None else self.event.to_dict(),
            "shadow_evidence": self.shadow_evidence,
            "reconcile": self.reconcile,
            "fail_reason": self.fail_reason,
            "CAUSAL_EVENT_IDENTITY_BREAK_COUNT": self.causal_event_identity_break_count,
            "EVENT_SUBSTITUTION_COUNT": self.event_substitution_count,
        }


def route_pre_external_to_shadow_v1(
    *,
    event: PreExternalProductiveEventV1,
    operator_go_token: str | None,
    operator_observation_go_token: str | None,
    session: Any,
    portfolio: Any,
    ledger: ShadowReconciliationLedgerV1,
    state_root: Path | None = None,
    max_open_positions: int = 1,
    open_simulated_positions: int = 0,
) -> ShadowRoutingResultV1:
    if event.substituted:
        return ShadowRoutingResultV1(
            ok=False,
            shadow_continuation=False,
            event=event,
            shadow_evidence=None,
            reconcile=None,
            fail_reason="EVENT_SUBSTITUTION_FORBIDDEN",
            event_substitution_count=1,
        )
    if str(event.terminal_disposition) != DISPOSITION_PRE_EXTERNAL_EFFECT:
        return ShadowRoutingResultV1(
            ok=False,
            shadow_continuation=False,
            event=event,
            shadow_evidence=None,
            reconcile=None,
            fail_reason="NOT_PRE_EXTERNAL",
        )
    if open_simulated_positions >= max_open_positions:
        return ShadowRoutingResultV1(
            ok=False,
            shadow_continuation=False,
            event=event,
            shadow_evidence=None,
            reconcile=None,
            fail_reason="MAX_SIMULATED_OPEN_POSITION_COUNT",
        )

    result = run_canonical_shadow_runtime_offline_cycle_v1(
        disposition=DISPOSITION_PRE_EXTERNAL_EFFECT,
        instrument_id=event.instrument_id,
        side=event.side,
        quantity=event.quantity,
        mark_price=event.mark_price,
        session_id=f"paper-shadow-{event.flight_id}",
        cycle_index=int(event.cycle_id),
        session=session,
        portfolio=portfolio,
        operator_go_token=operator_go_token,
        operator_observation_go_token=operator_observation_go_token,
        state_root=state_root,
    )
    rec_ok, rec_reason = ledger.record_simulated_execution(
        flight_id=event.flight_id,
        cycle_id=int(event.cycle_id),
        session_id=f"paper-shadow-{event.flight_id}",
    )
    ok = result.ok and rec_ok
    return ShadowRoutingResultV1(
        ok=ok,
        shadow_continuation=ok,
        event=event,
        shadow_evidence=result.execution_evidence,
        reconcile={"ok": rec_ok, "reason": rec_reason},
        fail_reason="" if ok else (result.fail_reason or rec_reason),
    )


def default_shadow_session_bundle_v1(
    *,
    instrument_id: str,
    state_root: Path | None = None,
) -> tuple[Any, Any, ShadowReconciliationLedgerV1]:
    session = ensure_accounting_session_v1(instrument_id=instrument_id, state_root=state_root)
    portfolio = SimulatedPortfolioEconomicsModelV1(
        PortfolioEconomicsModelParamsV1(initial_equity=Decimal("100000"))
    )
    return session, portfolio, ShadowReconciliationLedgerV1()
