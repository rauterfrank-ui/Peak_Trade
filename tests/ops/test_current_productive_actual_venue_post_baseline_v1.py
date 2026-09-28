"""POST-slice baseline: recorded pin vs live integrity (no self-referential merge loop)."""

from __future__ import annotations

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_baseline_v1 import (
    EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
    PREVIOUS_RECORDED_POST_SLICE_BASELINE_SHA,
    CurrentProductiveActualVenuePostBaselineError,
    resolve_and_assert_live_post_execution_baseline_v1,
)
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
)

RECORDED = EXPECTED_BASELINE_ORIGIN_MAIN_SHA
LIVE_AHEAD = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def test_recorded_pin_is_post_6946_merge_currency() -> None:
    assert RECORDED == "fca07afa1fa74a94cdecde3876c9c30ad79ba828"
    assert PREVIOUS_RECORDED_POST_SLICE_BASELINE_SHA == ("1e859eaa79f48308cf7037656c6465191ed9993b")


def test_post_merge_stability_live_main_ahead_of_recorded_pin_when_surfaces_clean() -> None:
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=LIVE_AHEAD,
        head=LIVE_AHEAD,
        drift="",
    )
    resolved = resolve_and_assert_live_post_execution_baseline_v1(
        declared_baseline_origin_main_sha=RECORDED,
        integrity_backend=integrity,
    )
    assert resolved == LIVE_AHEAD


def test_protected_surface_drift_fail_closed() -> None:
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=RECORDED,
        head=RECORDED,
        drift="diff in post slice",
    )
    with pytest.raises(
        CurrentProductiveActualVenuePostBaselineError,
        match="PROTECTED_POST_SLICE_SURFACE_DRIFT",
    ):
        resolve_and_assert_live_post_execution_baseline_v1(
            declared_baseline_origin_main_sha=RECORDED,
            integrity_backend=integrity,
        )


def test_head_not_at_origin_main_fail_closed() -> None:
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=RECORDED,
        head=LIVE_AHEAD,
        drift="",
    )
    with pytest.raises(
        CurrentProductiveActualVenuePostBaselineError,
        match="HEAD_NOT_SYNCHRONIZED_WITH_ORIGIN_MAIN",
    ):
        resolve_and_assert_live_post_execution_baseline_v1(
            declared_baseline_origin_main_sha=RECORDED,
            integrity_backend=integrity,
        )


def test_recorded_pin_matches_live_when_integrity_clean() -> None:
    """Simulates post-merge origin/main with no local POST-slice drift."""
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=RECORDED,
        head=RECORDED,
        drift="",
    )
    resolved = resolve_and_assert_live_post_execution_baseline_v1(
        declared_baseline_origin_main_sha=RECORDED,
        integrity_backend=integrity,
    )
    assert resolved == RECORDED
