import pytest

from src.execution.networked.allowlist_v1 import (
    ExecutionEntryGuardError,
    NetworkedAllowlistV1,
    guard_allowlist_v1,
)


def test_default_deny():
    al = NetworkedAllowlistV1.default_deny()
    assert al.is_allowed(adapter="coinbase", market="BTC-USD") is False


def test_allow_when_both_match():
    al = NetworkedAllowlistV1.from_iterables(adapters=["coinbase"], markets=["BTC-USD"])
    assert al.is_allowed(adapter="coinbase", market="BTC-USD") is True


def test_deny_if_only_adapter_matches():
    al = NetworkedAllowlistV1.from_iterables(adapters=["coinbase"], markets=["ETH-USD"])
    assert al.is_allowed(adapter="coinbase", market="BTC-USD") is False


def test_guard_raises():
    al = NetworkedAllowlistV1.default_deny()
    with pytest.raises(ExecutionEntryGuardError) as exc_info:
        guard_allowlist_v1(allowlist=al, adapter="coinbase", market="BTC-USD")
    assert "allowlist_denied" in str(exc_info.value)
