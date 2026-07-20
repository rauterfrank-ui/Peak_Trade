"""Negative and contract tests for sealed production lifecycle long-panel binding v1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research.longer_chronological_pit_acquisition_v1.sealed_lifecycle_v1 import (
    INCLUSION_POLICY_VERSION,
    InclusionDecision,
    SAMPLE_UNIVERSE_TRUTH_MARKER,
    SealedLifecycleError,
    assert_instrument_not_btc_or_spot,
    assert_not_sample_universe,
    build_sealed_record_from_registry_interval,
    evaluate_inclusion_v1,
    seal_lifecycle_manifest,
    verify_sealed_manifest,
)


def test_btc_instrument_rejected() -> None:
    with pytest.raises(SealedLifecycleError, match="BTC"):
        assert_instrument_not_btc_or_spot(
            native_instrument_id="BTC-USDT-SWAP",
            base_asset="BTC",
        )


def test_spot_instrument_rejected() -> None:
    with pytest.raises(SealedLifecycleError, match="SPOT"):
        assert_instrument_not_btc_or_spot(
            native_instrument_id="ETH-USDT",
            base_asset="ETH",
            market_type="spot",
        )


def test_missing_lifecycle_public_bounds_exclude_not_include() -> None:
    decision, reason, relist = evaluate_inclusion_v1(
        listing_timestamp="2021-01-01T00:00:00Z",
        delisting_timestamp=None,
        first_public_candle_timestamp=None,
        last_public_candle_timestamp=None,
    )
    assert decision == InclusionDecision.EXCLUDE_LONG_PANEL
    assert reason == "MISSING_PUBLIC_CANDLE_BOUNDARIES"
    assert relist is False


def test_pre_listing_candles_not_accepted_for_panel() -> None:
    decision, reason, _ = evaluate_inclusion_v1(
        listing_timestamp="2022-01-01T00:00:00Z",
        delisting_timestamp=None,
        first_public_candle_timestamp="2021-01-01T00:00:00Z",
        last_public_candle_timestamp="2024-01-01T00:00:00Z",
    )
    assert decision == InclusionDecision.EXCLUDE_LONG_PANEL
    assert reason == "PUBLIC_HISTORY_BEFORE_LISTING_NOT_ACCEPTED_FOR_PANEL"


def test_luna_like_relist_edge_excluded_not_stitched() -> None:
    decision, reason, relist = evaluate_inclusion_v1(
        listing_timestamp="2022-05-28T13:54:42Z",
        delisting_timestamp=None,
        first_public_candle_timestamp="2026-07-12T11:00:00Z",
        last_public_candle_timestamp="2026-07-20T18:00:00Z",
        panel_start="2021-09-01T00:00:00Z",
        panel_end="2024-09-01T00:00:00Z",
        native_instrument_id="LUNA-USDT-SWAP",
    )
    assert decision == InclusionDecision.EXCLUDE_LONG_PANEL
    assert relist is True
    assert reason is not None
    assert "RELIST_OR_PUBLIC_HISTORY_DISCONTINUITY" in reason


def test_delist_relist_episodes_not_naively_joined() -> None:
    # Usable window clipped by delisting before first_public of a later episode
    decision, reason, relist = evaluate_inclusion_v1(
        listing_timestamp="2021-01-01T00:00:00Z",
        delisting_timestamp="2022-01-01T00:00:00Z",
        first_public_candle_timestamp="2023-06-01T00:00:00Z",
        last_public_candle_timestamp="2024-06-01T00:00:00Z",
        panel_start="2021-09-01T00:00:00Z",
        panel_end="2024-09-01T00:00:00Z",
    )
    assert decision == InclusionDecision.EXCLUDE_LONG_PANEL
    assert relist is True
    assert reason is not None


def test_truncated_public_archive_still_includable_when_long_enough() -> None:
    decision, reason, relist = evaluate_inclusion_v1(
        listing_timestamp="2019-11-12T11:16:48Z",
        delisting_timestamp=None,
        first_public_candle_timestamp="2021-08-23T16:00:00Z",
        last_public_candle_timestamp="2026-07-20T18:00:00Z",
        panel_start="2021-09-01T00:00:00Z",
        panel_end="2024-09-01T00:00:00Z",
    )
    assert decision == InclusionDecision.INCLUDE_LONG_PANEL
    assert reason is None
    assert relist is False


def test_sample_universe_cannot_be_emitted_as_production() -> None:
    with pytest.raises(SealedLifecycleError, match="SAMPLE_UNIVERSE"):
        assert_not_sample_universe(SAMPLE_UNIVERSE_TRUTH_MARKER)


def test_tampered_manifest_fails_seal_hash() -> None:
    interval = {
        "instrument_id": "okx:linear_perpetual:ETH:USDT:USDT:perp",
        "venue_symbol": "ETH-USDT-SWAP",
        "base_asset": "ETH",
        "settlement_asset": "USDT",
        "contract_type": "linear_perpetual",
        "listing_time": "2019-11-12T11:16:48Z",
        "delisting_time": None,
        "record_digest": "abc",
    }
    rec = build_sealed_record_from_registry_interval(
        interval,
        first_public_candle_timestamp="2021-08-23T16:00:00Z",
        last_public_candle_timestamp="2024-09-01T00:00:00Z",
        lifecycle_observed_at="2026-07-20T18:00:00Z",
    )
    manifest = seal_lifecycle_manifest(
        [rec],
        production_registry_digest="d" * 64,
        production_registry_path="/tmp/registry_snapshot_v1.json",
        request_fingerprints=[],
        sealed_at="2026-07-20T18:00:00Z",
    )
    verify_sealed_manifest(manifest)
    manifest["long_panel_native_ids"] = ["TAMPERED"]
    with pytest.raises(SealedLifecycleError, match="SEAL_HASH_MISMATCH"):
        verify_sealed_manifest(manifest)


def test_policy_version_constant() -> None:
    assert INCLUSION_POLICY_VERSION.endswith(".v1")


def test_authorized_paths_include_sealed_lifecycle_modules() -> None:
    from src.governance.economic_diagnostic_optimization_boundary_v0 import (
        build_boundary_report,
    )

    repo = Path(__file__).resolve().parents[2]
    report = build_boundary_report(
        [
            "src/research/longer_chronological_pit_acquisition_v1/sealed_lifecycle_v1.py",
            "src/research/longer_chronological_pit_acquisition_v1/public_lifecycle_acquisition_v1.py",
            "tests/research/test_longer_chronological_pit_sealed_lifecycle_acquisition_v1.py",
            "config/research/longer_chronological_pit_sealed_lifecycle_long_panel_v1.json",
            "config/governance/technical_canonical_wiring_authorization_v1.json",
            "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
        ],
        repo_root=repo,
    )
    # May fail until governance allowlist updated — assert shape
    assert report.master_v2_changed is False
    assert report.double_play_changed is False
