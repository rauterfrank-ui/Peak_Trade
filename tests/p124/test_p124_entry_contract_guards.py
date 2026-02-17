"""P124 — Entry contract guard tests."""

import pytest

from src.execution.networked import (
    ExecutionEntryGuardError,
    build_execution_networked_context_v1,
    validate_execution_networked_context_v1,
)


def test_rejects_live_mode() -> None:
    ctx = build_execution_networked_context_v1(
        mode="live",
        dry_run=True,
        adapter="mock",
        market="BTC-USD",
        qty=0.01,
        intent="place_order",
        extra_kv=None,
    )
    with pytest.raises(ExecutionEntryGuardError) as e:
        validate_execution_networked_context_v1(ctx, env={})
    assert "mode_not_allowed" in str(e.value)


def test_rejects_dry_run_false() -> None:
    ctx = build_execution_networked_context_v1(
        mode="shadow",
        dry_run=False,
        adapter="mock",
        market="BTC-USD",
        qty=0.01,
        intent="place_order",
        extra_kv=None,
    )
    with pytest.raises(ExecutionEntryGuardError) as e:
        validate_execution_networked_context_v1(ctx, env={})
    assert "dry_run_must_be_true" in str(e.value)


def test_rejects_secret_env_like() -> None:
    ctx = build_execution_networked_context_v1(
        mode="shadow",
        dry_run=True,
        adapter="mock",
        market="BTC-USD",
        qty=0.01,
        intent="place_order",
        extra_kv=None,
    )
    with pytest.raises(ExecutionEntryGuardError) as e:
        validate_execution_networked_context_v1(ctx, env={"KRAKEN_API_KEY": "x"})
    assert "secret_env_detected" in str(e.value)


def test_ok_path_shadow_dry_run() -> None:
    ctx = build_execution_networked_context_v1(
        mode="paper",
        dry_run=True,
        adapter="mock",
        market="BTC-USD",
        qty=0.01,
        intent="place_order",
        extra_kv=["post_only=YES"],
    )
    validate_execution_networked_context_v1(ctx, env={})
