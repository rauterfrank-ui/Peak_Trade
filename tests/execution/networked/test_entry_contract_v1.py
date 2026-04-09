"""LB-EXE-001 — entry contract v1 guards (deterministic env= isolation)."""

from __future__ import annotations

from typing import Dict, Optional

import pytest

from src.execution.networked.entry_contract_v1 import (
    ExecutionEntryGuardError,
    ExecutionNetworkedContextV1,
    build_execution_networked_context_v1,
    guard_entry_contract_v1,
    validate_execution_networked_context_v1,
)


def _ctx(
    *,
    mode: str = "paper",
    dry_run: bool = True,
    adapter: str = "mock",
    market: str = "BTC-USD",
    qty: float = 0.1,
    intent: str = "place_order",
    extra: Optional[Dict[str, str]] = None,
) -> ExecutionNetworkedContextV1:
    return ExecutionNetworkedContextV1(
        mode=mode,
        dry_run=dry_run,
        adapter=adapter,
        market=market,
        qty=qty,
        intent=intent,
        extra=extra or {},
    )


def test_validate_ok_minimal() -> None:
    validate_execution_networked_context_v1(_ctx(), env={})


def test_dry_run_must_be_true() -> None:
    with pytest.raises(ExecutionEntryGuardError, match="dry_run_must_be_true"):
        validate_execution_networked_context_v1(_ctx(dry_run=False), env={})


def test_mode_not_shadow_or_paper() -> None:
    with pytest.raises(ExecutionEntryGuardError, match="mode_not_allowed"):
        validate_execution_networked_context_v1(_ctx(mode="live"), env={})


def test_deny_env_trading_enable() -> None:
    with pytest.raises(ExecutionEntryGuardError, match="deny_env_set:TRADING_ENABLE"):
        validate_execution_networked_context_v1(_ctx(), env={"TRADING_ENABLE": "1"})


def test_secret_env_detected() -> None:
    with pytest.raises(ExecutionEntryGuardError, match="secret_env_detected"):
        validate_execution_networked_context_v1(_ctx(), env={"KRAKEN_API_KEY": "x"})


def test_market_slash_invalid() -> None:
    with pytest.raises(ExecutionEntryGuardError, match="market_invalid"):
        validate_execution_networked_context_v1(_ctx(market="BTC/EUR"), env={})


def test_place_order_qty_invalid() -> None:
    with pytest.raises(ExecutionEntryGuardError, match="qty_invalid"):
        validate_execution_networked_context_v1(_ctx(intent="place_order", qty=0), env={})


def test_intent_invalid() -> None:
    with pytest.raises(ExecutionEntryGuardError, match="intent_invalid"):
        validate_execution_networked_context_v1(_ctx(intent="nope"), env={})


def test_guard_entry_contract_v1_passes_with_empty_env() -> None:
    guard_entry_contract_v1(
        mode="shadow",
        dry_run=True,
        adapter="mock",
        intent="cancel_all",
        market="ETH-USD",
        qty=1.0,
        env={},
    )


def test_build_extra_kv_roundtrip() -> None:
    ctx = build_execution_networked_context_v1(
        mode="paper",
        dry_run=True,
        adapter="mock",
        market="BTC-USD",
        qty=0.01,
        intent="markets",
        extra_kv=("foo=bar",),
    )
    assert ctx.extra.get("foo") == "bar"
    validate_execution_networked_context_v1(ctx, env={})


def test_deny_env_live_when_zero_or_false_allows() -> None:
    validate_execution_networked_context_v1(_ctx(), env={"LIVE": "0"})
    validate_execution_networked_context_v1(_ctx(), env={"LIVE": "false"})


def test_orderbook_intent_allows_zero_qty() -> None:
    validate_execution_networked_context_v1(
        _ctx(intent="orderbook", qty=0.0),
        env={},
    )


def test_markets_intent_allows_zero_qty() -> None:
    validate_execution_networked_context_v1(
        _ctx(intent="markets", qty=0.0),
        env={},
    )
