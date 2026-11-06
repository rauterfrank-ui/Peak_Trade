"""Tests for decision context v1 hardening (costs + mu_bp defaults)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class _MinimalIntent:
    symbol: str = "BTC/EUR"
    side: str = "buy"
    quantity: float = 0.01
    order_type: Optional[str] = "market"


def test_decision_context_v1_always_has_costs_and_mu_bp():
    from src.observability.nowcast.decision_context_v1 import build_decision_context_v1

    intent = _MinimalIntent()
    d = build_decision_context_v1(
        intent=intent,
        env="paper",
        is_testnet=False,
        current_price=100.0,
    )
    assert isinstance(d["costs"], dict)
    for k in ("fees_bp", "slippage_bp", "impact_bp", "latency_bp"):
        assert k in d["costs"]
        assert isinstance(d["costs"][k], float)
    assert isinstance(d["forecast"], dict)
    assert "mu_bp" in d["forecast"]
    assert isinstance(d["forecast"]["mu_bp"], float)


def test_decision_context_v1_accepts_price_change_bp_as_mu():
    from src.observability.nowcast.decision_context_v1 import build_decision_context_v1

    intent = _MinimalIntent()
    d = build_decision_context_v1(
        intent=intent,
        env="paper",
        is_testnet=False,
        current_price=100.0,
        extra_inputs={"price_change_bp": 12.5},
    )
    assert d["forecast"]["mu_bp"] == 12.5


def test_decision_context_v1_accepts_mu_bp_directly():
    from src.observability.nowcast.decision_context_v1 import build_decision_context_v1

    intent = _MinimalIntent()
    d = build_decision_context_v1(
        intent=intent,
        env="paper",
        is_testnet=False,
        current_price=100.0,
        extra_inputs={"mu_bp": 8.0},
    )
    assert d["forecast"]["mu_bp"] == 8.0
