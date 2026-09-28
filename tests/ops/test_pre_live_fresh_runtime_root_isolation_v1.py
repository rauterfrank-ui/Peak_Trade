"""Fresh-root isolation guards for Actual-Venue-POST pre-live path."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.governed_productive_account_equity_authority_producer_v1.pre_live_fresh_runtime_root_isolation_v1 import (
    HISTORICAL_LOCAL_POST_STORE_MARKER,
    PreLiveFreshRuntimeRootIsolationError,
    assert_post_durable_store_root_isolation_v1,
    validate_post_durable_store_root_isolation_v1,
    validate_productivity_root_isolation_v1,
)


def test_rejects_historical_first_real_okx_post_store(tmp_path: Path) -> None:
    historical = (
        tmp_path
        / "runtime/current_productive/first_real_okx_europe_venue_post_20260928T002700Z/post_durable_store"
    )
    historical.mkdir(parents=True)
    probe = validate_post_durable_store_root_isolation_v1(
        store_root=historical,
        repo_root=tmp_path,
    )
    assert probe["OK"] is False
    assert "HISTORICAL_FIRST_REAL_OKX_POST_STORE_FORBIDDEN" in str(probe["REASON_CODES"])
    with pytest.raises(PreLiveFreshRuntimeRootIsolationError):
        assert_post_durable_store_root_isolation_v1(store_root=historical, repo_root=tmp_path)


def test_accepts_fresh_runtime_post_store(tmp_path: Path) -> None:
    fresh = tmp_path / "runtime/current_productive/pre_live_fresh_cap24/1e859eaa/post_durable_store"
    fresh.mkdir(parents=True)
    probe = validate_post_durable_store_root_isolation_v1(store_root=fresh, repo_root=tmp_path)
    assert probe["OK"] is True


def test_default_cap24_requires_explicit_binding(tmp_path: Path) -> None:
    default = tmp_path / "runtime/current_productive/cap24_selection_state"
    default.mkdir(parents=True)
    probe = validate_productivity_root_isolation_v1(
        productivity_root=default,
        repo_root=tmp_path,
    )
    assert probe["OK"] is False
    assert HISTORICAL_LOCAL_POST_STORE_MARKER not in str(probe["REASON_CODES"])
