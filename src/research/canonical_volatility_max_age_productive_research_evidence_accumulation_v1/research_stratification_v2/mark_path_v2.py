"""Research-owned observation mark path (not bridge mid_prices)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Sequence

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    sha256_hex,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.constants_v2 import (
    CROSS_CAMPAIGN_STATE_POLICY,
    RESEARCH_MARK_PATH_MAX_LEN,
)


@dataclass
class ResearchObservationMarkPathStateV2:
    """Append-only research mark path scoped to campaign/session."""

    campaign_id: str
    session_id: str
    mark_prices: list[float] = field(default_factory=list)
    state_digest: str = ""

    def append_mark(self, mark: float) -> None:
        if not isinstance(mark, (int, float)) or float(mark) <= 0:
            return
        self.mark_prices.append(float(mark))
        if len(self.mark_prices) > RESEARCH_MARK_PATH_MAX_LEN:
            self.mark_prices = self.mark_prices[-RESEARCH_MARK_PATH_MAX_LEN:]
        self._refresh_digest()

    def _refresh_digest(self) -> None:
        self.state_digest = sha256_hex(
            {
                "campaign_id": self.campaign_id,
                "mark_prices": self.mark_prices,
                "session_id": self.session_id,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "mark_prices": list(self.mark_prices),
            "session_id": self.session_id,
            "state_digest": self.state_digest,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ResearchObservationMarkPathStateV2:
        state = cls(
            campaign_id=str(payload["campaign_id"]),
            session_id=str(payload["session_id"]),
            mark_prices=[float(x) for x in payload.get("mark_prices") or []],
        )
        state.state_digest = str(payload.get("state_digest") or "")
        expected = sha256_hex(
            {
                "campaign_id": state.campaign_id,
                "mark_prices": state.mark_prices,
                "session_id": state.session_id,
            }
        )
        if state.state_digest and state.state_digest != expected:
            raise ValueError("research_mark_path_state_digest_mismatch")
        if not state.state_digest:
            state._refresh_digest()
        return state

    @classmethod
    def carry_within_campaign_v2(
        cls,
        *,
        prior: ResearchObservationMarkPathStateV2,
        campaign_id: str,
        next_session_id: str,
    ) -> ResearchObservationMarkPathStateV2:
        if prior.campaign_id != campaign_id:
            raise ValueError("cross_campaign_research_mark_path_carry_forbidden")
        _ = CROSS_CAMPAIGN_STATE_POLICY
        return cls(
            campaign_id=campaign_id,
            session_id=next_session_id,
            mark_prices=list(prior.mark_prices),
        )


def extract_cycle_mark_price_v2(cycle: dict[str, Any]) -> float | None:
    """Explicit cycle mark only — never bridge state."""
    binding = dict(cycle.get("canonical_volatility_typed_binding") or {})
    for candidate in (
        binding.get("mark_price"),
        (dict(cycle.get("price_basis") or {}).get("mid_price")),
        (dict(cycle.get("feature_regime") or {}).get("mark_price")),
    ):
        if isinstance(candidate, (int, float)) and float(candidate) > 0:
            return float(candidate)
    return None


def realized_vol_sample_v2(prices: Sequence[float]) -> float | None:
    if len(prices) < 2:
        return None
    rets = []
    for a, b in zip(prices[:-1], prices[1:]):
        if a > 0:
            rets.append((b - a) / a)
    if len(rets) < 1:
        return None
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / max(len(rets) - 1, 1)
    return var**0.5
