from __future__ import annotations

import pytest

from src.ops.treasury_separation_gate import (
    BOT,
    TREASURY,
    DEPOSIT_ADDRESS,
    INTERNAL_TRANSFER,
    WITHDRAW,
    TreasurySeparationError,
    enforce_treasury_policy,
    evaluate_treasury_policy,
    get_key_role,
)


def test_default_env_role_is_bot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PT_KEY_ROLE", raising=False)
    assert get_key_role() == BOT


@pytest.mark.parametrize("operation", [WITHDRAW, DEPOSIT_ADDRESS, INTERNAL_TRANSFER])
def test_bot_role_blocks_treasury_operations(
    monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    monkeypatch.setenv("PT_KEY_ROLE", BOT)
    decision = evaluate_treasury_policy(operation)
    assert decision.allowed is False
    assert decision.role == BOT
    assert decision.operation == operation
    assert decision.event_type == "treasury_block"
    assert "treasury_block" in decision.reason
    assert f"operation={operation}" in decision.reason
    assert "role=bot" in decision.reason

    with pytest.raises(TreasurySeparationError, match="treasury_block"):
        enforce_treasury_policy(operation)


@pytest.mark.parametrize("operation", [WITHDRAW, DEPOSIT_ADDRESS, INTERNAL_TRANSFER])
def test_treasury_role_allows_treasury_operations(
    monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    monkeypatch.setenv("PT_KEY_ROLE", TREASURY)
    decision = evaluate_treasury_policy(operation)
    assert decision.allowed is True
    assert decision.role == TREASURY
    assert decision.operation == operation
    assert decision.event_type == "treasury_allow"
    assert "allowed:" in decision.reason

    enforced = enforce_treasury_policy(operation)
    assert enforced.allowed is True


def test_unknown_role_falls_back_to_bot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PT_KEY_ROLE", "weird-role")
    assert get_key_role() == BOT

    decision = evaluate_treasury_policy(WITHDRAW)
    assert decision.allowed is False
    assert decision.role == BOT


def test_non_treasury_operation_allowed_in_bot_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PT_KEY_ROLE", BOT)
    decision = evaluate_treasury_policy("place_order")
    assert decision.allowed is True
    assert decision.role == BOT
    assert decision.operation == "place_order"
    assert decision.event_type == "treasury_allow"
