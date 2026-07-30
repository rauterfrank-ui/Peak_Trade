"""Idempotent analytical portfolio wrapper (intent_id / fill_id fail-closed)."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Mapping, Optional, Set

from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PortfolioEconomicsModelParamsV1,
    SimulatedFillV1,
    SimulatedPortfolioEconomicsModelV1,
)


class IdempotencyErrorV2(ValueError):
    """Duplicate intent/fill application."""


@dataclass
class IdempotentPortfolioV2:
    """Session-persistent portfolio with fail-closed intent/fill idempotency."""

    model: SimulatedPortfolioEconomicsModelV1 = field(
        default_factory=SimulatedPortfolioEconomicsModelV1
    )
    applied_intent_ids: Set[str] = field(default_factory=set)
    applied_fill_ids: Set[str] = field(default_factory=set)

    @classmethod
    def from_params(
        cls, params: PortfolioEconomicsModelParamsV1 | None = None
    ) -> IdempotentPortfolioV2:
        return cls(model=SimulatedPortfolioEconomicsModelV1(params))

    def snapshot(self) -> Mapping[str, Any]:
        snap = dict(self.model.snapshot())
        snap["applied_intent_ids"] = sorted(self.applied_intent_ids)
        snap["applied_fill_ids"] = sorted(self.applied_fill_ids)
        return snap

    def economic_metrics(self) -> Any:
        return self.model.economic_metrics()

    def apply_intended_action(
        self,
        *,
        instrument_id: str,
        side: str,
        quantity: Decimal,
        mark_price: Decimal,
        intent_id: str,
        fill_id: str | None = None,
    ) -> Optional[SimulatedFillV1]:
        if not intent_id:
            raise IdempotencyErrorV2("INTENT_ID_REQUIRED")
        if intent_id in self.applied_intent_ids:
            raise IdempotencyErrorV2(f"DUPLICATE_INTENT_ID:{intent_id}")
        side_u = str(side or "").strip().upper()
        if side_u in {"", "HOLD", "NONE", "FLAT"}:
            self.applied_intent_ids.add(intent_id)
            return self.model.apply_intended_action(
                instrument_id=instrument_id,
                side=side_u or "HOLD",
                quantity=Decimal("0"),
                mark_price=mark_price,
            )
        if fill_id is None or not fill_id:
            raise IdempotencyErrorV2("FILL_ID_REQUIRED_FOR_ACTIONABLE_INTENT")
        if fill_id in self.applied_fill_ids:
            raise IdempotencyErrorV2(f"DUPLICATE_FILL_ID:{fill_id}")
        fill = self.model.apply_intended_action(
            instrument_id=instrument_id,
            side=side_u,
            quantity=quantity,
            mark_price=mark_price,
        )
        self.applied_intent_ids.add(intent_id)
        if fill is not None:
            self.applied_fill_ids.add(fill_id)
        return fill
