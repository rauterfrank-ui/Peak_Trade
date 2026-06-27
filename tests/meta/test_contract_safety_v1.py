"""Contract tests for shared Self-Learning safety validators v1."""

from __future__ import annotations

import pytest

from src.meta.learning_loop.contract_safety_v1 import (
    VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION,
    VERDICT_FUTURES_SCOPE_VIOLATION,
    VERDICT_TARGET_NOT_ALLOWED,
    canonical_futures_scope_ref,
    canonical_trading_logic_immutability_ref,
    classify_patch_target,
    compute_content_sha256,
    deterministic_json_dumps,
    validate_futures_scope_ref,
    validate_patch_target,
    validate_trading_logic_immutability_ref,
)


def test_canonical_futures_scope_ref_is_futures_only() -> None:
    ref = canonical_futures_scope_ref()
    assert ref["scope"] == "FUTURES_ONLY"
    assert ref["bitcoin_direction_allowed"] is False


def test_canonical_trading_logic_immutability_ref_is_fail_closed() -> None:
    ref = canonical_trading_logic_immutability_ref()
    assert ref["trading_logic_immutability"] is True
    assert ref["mutable_trading_payloads_forbidden"] is True


def test_deterministic_json_dumps_is_stable() -> None:
    payload = {"b": 2, "a": {"d": 4, "c": 3}}
    assert deterministic_json_dumps(payload) == '{"a":{"c":3,"d":4},"b":2}'


def test_compute_content_sha256_is_deterministic() -> None:
    payload = {"schema_version": "1.0", "manifest_id": "abc"}
    first = compute_content_sha256(payload)
    second = compute_content_sha256(payload)
    assert first == second
    assert len(first) == 64


@pytest.mark.parametrize(
    ("target", "allowed"),
    [
        ("research.offline.feature_flag", True),
        ("portfolio.leverage", False),
        ("strategy.trigger_delay", False),
        ("risk.stop_loss", False),
        ("macro.regime_weight", False),
        ("master_v2.config", False),
        ("double_play.slot", False),
        ("execution.routing.default", False),
        ("live.arming.enabled", False),
    ],
)
def test_classify_patch_target_cases(target: str, allowed: bool) -> None:
    is_allowed, _ = classify_patch_target(target)
    assert is_allowed is allowed


def test_validate_futures_scope_rejects_btc_scope() -> None:
    bad = dict(canonical_futures_scope_ref())
    bad["scope"] = "BTC_FUTURES"
    result = validate_futures_scope_ref(bad)
    assert result.valid is False
    assert result.verdict == VERDICT_FUTURES_SCOPE_VIOLATION


def test_validate_futures_scope_rejects_spot_scope() -> None:
    bad = dict(canonical_futures_scope_ref())
    bad["scope"] = "SPOT_ONLY"
    result = validate_futures_scope_ref(bad)
    assert result.valid is False


def test_validate_patch_target_trading_logic_verdict() -> None:
    result = validate_patch_target("strategy.trigger_delay")
    assert result.valid is False
    assert result.verdict == VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION


def test_validate_patch_target_unknown_target_verdict() -> None:
    result = validate_patch_target("")
    assert result.valid is False
    assert result.verdict == VERDICT_TARGET_NOT_ALLOWED


def test_validate_trading_logic_immutability_ref_rejects_mutation() -> None:
    bad = dict(canonical_trading_logic_immutability_ref())
    bad["reference_only"] = False
    result = validate_trading_logic_immutability_ref(bad)
    assert result.valid is False
    assert result.verdict == VERDICT_FAIL_CLOSED_TRADING_LOGIC_BOUNDARY_VIOLATION
