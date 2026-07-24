"""Captured-at / freshness policy ratification tests."""

from __future__ import annotations

from pathlib import Path

from src.ops.okx_captured_at_freshness_policy_v1 import (
    build_okx_capture_clocks_v1,
    classify_freshness_v1,
    load_freshness_policy_v1,
)

REPO = Path(__file__).resolve().parents[2]


def test_policy_ratified() -> None:
    cfg = load_freshness_policy_v1(repo_root=REPO)
    assert cfg["OKX_CAPTURED_AT_MAPPING_AUTHORIZED"] is True
    assert cfg["timestamp_policy"]["captured_at"] == "response_received_at"
    assert cfg["timestamp_policy"]["filesystem_mtime_forbidden"] is True


def test_captured_at_equals_response_received() -> None:
    clocks = build_okx_capture_clocks_v1(
        capture_started_at="2026-07-24T21:00:00Z",
        response_received_at="2026-07-24T21:00:01Z",
        provider_timestamp="2026-07-24T20:59:59Z",
    )
    assert clocks.captured_at == "2026-07-24T21:00:01Z"
    assert clocks.effective_at == "2026-07-24T20:59:59Z"


def test_stale_classification() -> None:
    state, is_stale, reason = classify_freshness_v1(
        reference_at="2026-07-24T20:00:00Z",
        as_of="2026-07-24T21:00:00Z",
        source_type="reference_mark_price",
    )
    assert state == "stale"
    assert is_stale is True
    assert reason is not None
