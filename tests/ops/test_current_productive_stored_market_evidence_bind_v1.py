"""Stored market evidence bind: real 0G candles stay incomplete; fixtures pass through."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_stored_market_evidence_bind_v1 import (
    assess_stored_balance_authority_v1,
    assess_stored_market_evidence_directory_v1,
)

_REPO = Path(__file__).resolve().parents[2]
_CANDLE_DIR = (
    _REPO
    / "evidence/ops/full_core_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v3"
    / "20260916T023738Z"
)
_BALANCE_CAPTURE = (
    _REPO
    / "evidence/ops/full_core_live_equity_stock_today_declaration_governed_binding_contract_wp1"
    / "2026-09-14T174507Z/raw_http_capture_balance_v1.json"
)
_NATIVE = "0G-USDT-SWAP"


def test_real_0g_candle_pack_is_bound_and_incomplete() -> None:
    assessment = assess_stored_market_evidence_directory_v1(
        evidence_dir=_CANDLE_DIR,
        native_id=_NATIVE,
    )
    assert assessment.body_sha256_matches is True
    assert assessment.post_count_zero is True
    assert len(assessment.finalized_closes) == 99
    assert assessment.last_finalized_event_ts_unix == 1789526160.0
    assert assessment.volume is None
    assert assessment.open_interest is None
    assert assessment.funding_rate is None
    assert assessment.complete is False
    assert "vol24h" in assessment.missing_fields
    assert "open_interest" in assessment.missing_fields
    assert "funding_rate" in assessment.missing_fields
    assert "mark_px" in assessment.missing_fields


def test_other_instrument_is_not_read_as_0g() -> None:
    assessment = assess_stored_market_evidence_directory_v1(
        evidence_dir=_CANDLE_DIR,
        native_id="BTC-USD_UM_XPERP-310404",
    )
    assert assessment.complete is False
    assert "instrument_mismatch" in assessment.missing_fields
    assert assessment.volume is None


def test_balance_capture_without_authority_is_not_capital_context() -> None:
    assessment = assess_stored_balance_authority_v1(capture_path=_BALANCE_CAPTURE)
    assert assessment.usable_for_capital_context is False
    assert assessment.reason == "VENUE_EQ_SOURCE_AUTHORITY_FALSE"
    assert assessment.observed_at_utc == "2026-09-14T17:45:07Z"


def test_fixture_bundle_passes_values_through_unchanged(tmp_path: Path) -> None:
    native = "ADA-USDT-SWAP"
    body = {
        "code": "0",
        "data": [["1700000000000", "1", "2", "0.5", "1.5", "10", "10", "15", "1"]],
        "msg": "",
    }
    raw = json.dumps(body, separators=(",", ":")).encode("utf-8")
    (tmp_path / "raw_public_candles_get_v1.json").write_bytes(raw)
    provenance = {
        "BODY_SHA256": hashlib.sha256(raw).hexdigest(),
        "C1_GATE_NATIVE_ID": native,
        "ENDPOINT": f"/api/v5/market/candles?instId={native}&bar=1m&limit=100",
        "OBSERVED_AT_UNIX": "1700000060.0",
        "POST_COUNT": "0",
        "VENUE_MUTATION_PERFORMED": "false",
    }
    (tmp_path / "raw_public_candles_get_provenance_v1.json").write_text(
        json.dumps(provenance),
        encoding="utf-8",
    )
    (tmp_path / "ticker.json").write_text(
        json.dumps(
            {
                "code": "0",
                "data": [
                    {
                        "instId": native,
                        "bidPx": "1.4",
                        "askPx": "1.6",
                        "vol24h": "2500",
                        "idxPx": "1.49",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "oi.json").write_text(
        json.dumps({"code": "0", "data": [{"instId": native, "oi": "8800"}]}),
        encoding="utf-8",
    )
    (tmp_path / "funding.json").write_text(
        json.dumps({"code": "0", "data": [{"instId": native, "fundingRate": "0.0002"}]}),
        encoding="utf-8",
    )
    (tmp_path / "mark.json").write_text(
        json.dumps({"code": "0", "data": [{"instId": native, "markPx": "1.5", "idxPx": "1.49"}]}),
        encoding="utf-8",
    )
    assessment = assess_stored_market_evidence_directory_v1(
        evidence_dir=tmp_path,
        native_id=native,
    )
    assert assessment.complete is True
    assert assessment.finalized_closes == (1.5,)
    assert assessment.volume == 2500.0
    assert assessment.open_interest == 8800.0
    assert assessment.funding_rate == pytest.approx(0.0002)
    assert assessment.bid_px == 1.4
    assert assessment.ask_px == 1.6
    assert assessment.mark_px == 1.5
    assert assessment.index_px == 1.49
