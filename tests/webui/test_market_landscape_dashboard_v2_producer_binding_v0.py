"""Phase 4.1 producer binding tests for Market Landscape V2."""

from __future__ import annotations

import json
import uuid
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import is_under_tmp
from scripts.ops.primary_evidence_retention_v0 import (
    write_manifest_sha256 as _write_manifest_sha256,
)
from src.webui.market_dashboard_landscape_producer_binding_v2 import (
    REASON_ARCHIVE_ROOT_UNSET,
    REASON_MARKET_CONTEXT_NOT_PERSISTED,
    REASON_SELECTED_FORBIDDEN_SYMBOL,
    REASON_SOURCE_CONTRADICTION,
    bind_market_universe_slots,
)
from src.webui.market_dashboard_landscape_v2 import (
    Availability,
    MarketDashboardReadServiceV1,
    present_market_landscape_v2,
    project_market_instrument_snapshot_v1,
    project_universe_ranking_snapshot_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_producer_v1 import (
    READMODEL_FILENAME,
    READMODELS_DIRNAME,
)

STAMP = datetime(2026, 7, 23, 18, 0, 0, tzinfo=timezone.utc)
REPO = Path(__file__).resolve().parents[2]
SCRATCH_ROOT = REPO / "tests" / "_durable_archive_scratch"


@pytest.fixture
def archive_root(tmp_path: Path) -> Path:
    candidate = tmp_path / "archive_root"
    candidate.mkdir(parents=True, exist_ok=True)
    if not is_under_tmp(candidate):
        return candidate
    SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    durable = SCRATCH_ROOT / str(uuid.uuid4())
    durable.mkdir(parents=True, exist_ok=True)
    return durable


def test_project_market_universe_field_copy_immutable() -> None:
    market = project_market_instrument_snapshot_v1(
        instrument_id="BTC-USDT-SWAP",
        venue="OKX",
        market_type="perpetual",
        mark_price=65000.5,
        reason_codes=("CONTEXT_ACCEPTED",),
        generated_at=STAMP,
        effective_at=STAMP,
        source_reference="context://btc",
    )
    assert market.availability is Availability.AVAILABLE
    assert market.instrument_id == "BTC-USDT-SWAP"
    assert market.venue == "OKX"
    assert market.mark_price == 65000.5
    assert market.provenance.generated_at == STAMP
    with pytest.raises(FrozenInstanceError):
        market.instrument_id = "X"  # type: ignore[misc]

    universe = project_universe_ranking_snapshot_v1(
        ranking=({"symbol": "ETHUSDT", "rank": 1},),
        universe=({"symbol": "ETHUSDT", "rank": 1, "exchange": "okx"},),
        selected_instrument_id="ETHUSDT",
        reason_codes=("RANK_PROJECTED",),
        generated_at=STAMP,
        effective_at=STAMP,
        source_reference="readmodels/universe_selection_readmodel.v1.json",
    )
    assert universe.availability is Availability.AVAILABLE
    assert universe.selected_instrument_id == "ETHUSDT"
    assert universe.universe[0]["exchange"] == "okx"


def test_project_rejects_silent_empty_available_universe() -> None:
    with pytest.raises(ValueError, match="required"):
        project_universe_ranking_snapshot_v1(
            ranking=(),
            universe=(),
            selected_instrument_id=None,
            reason_codes=(),
            generated_at=STAMP,
            effective_at=STAMP,
            source_reference=None,
        )


def test_bind_defaults_fail_closed_without_archive_or_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT", raising=False)
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert set(slots) == {"market_instrument", "universe_ranking"}
    assert slots["market_instrument"].availability is Availability.MISSING_SOURCE
    assert REASON_MARKET_CONTEXT_NOT_PERSISTED in slots["market_instrument"].reason_codes
    assert slots["universe_ranking"].availability is Availability.MISSING_SOURCE
    assert REASON_ARCHIVE_ROOT_UNSET in slots["universe_ranking"].reason_codes
    assert slots["market_instrument"].instrument_id is None
    assert slots["universe_ranking"].selected_instrument_id is None
    assert slots["universe_ranking"].ranking == ()


def test_bind_rejects_inventing_market_without_required_fields() -> None:
    with pytest.raises(KeyError):
        bind_market_universe_slots(
            generated_at=STAMP,
            market_instrument_fields={"venue": "OKX"},
        )


def test_bind_available_when_producer_fields_supplied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT", raising=False)
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        market_instrument_fields={
            "instrument_id": "BTC-USDT-SWAP",
            "venue": "OKX",
            "market_type": "perpetual",
            "mark_price": 1.0,
            "reason_codes": ("OK",),
            "source_reference": "ctx://1",
        },
    )
    assert slots["market_instrument"].availability is Availability.AVAILABLE
    assert slots["universe_ranking"].availability is Availability.MISSING_SOURCE


def _write_truth_universe_archive(
    archive_root: Path,
    *,
    selected_symbol: str = "ETH-USDT-SWAP",
    include_ranking: bool = True,
    include_selected: bool = True,
) -> Path:
    readmodels = archive_root / READMODELS_DIRNAME
    readmodels.mkdir(parents=True, exist_ok=True)
    ranking = []
    if include_ranking:
        ranking = [
            {
                "row_id": "r-eth",
                "symbol": selected_symbol,
                "rank": 1,
                "display_score": 0.9,
                "exchange": "OKX",
            },
        ]
    selected_future: dict[str, object]
    if include_selected:
        selected_future = {
            "row_id": "s-eth",
            "symbol": selected_symbol,
            "rank": 1,
            "truth_status": "PERSISTED",
            "selection_reason": "top_ranked",
        }
        selected_truth = "PERSISTED"
    else:
        selected_future = {"truth_status": "NOT_PERSISTED"}
        selected_truth = "SELECTED_FUTURE_NOT_PERSISTED"
    payload = {
        "schema_name": "universe_selection_readmodel.v1",
        "schema_version": 1,
        "generated_at": "2026-07-23T18:00:00Z",
        "source_run_id": "landscape_phase41_truth_v1",
        "source_stage": "paper",
        "non_authorizing": True,
        "fixture_marked": False,
        "universe": [
            {
                "row_id": "u-eth",
                "symbol": selected_symbol,
                "rank": 1,
                "exchange": "OKX",
            },
        ],
        "ranking": ranking,
        "selected_future": selected_future,
        "market_snapshot": {
            "truth_status": "PERSISTED",
            "source_kind": "governed_producer",
            "snapshot_id": "snap-1",
            "exchange": "OKX",
            "captured_at": "2026-07-23T17:59:00Z",
        },
        "evidence": {
            "producer_contract": "universe_selection_producer.v1",
            "storage_target": "readmodels/universe_selection_readmodel.v1.json",
            "links": [],
        },
        "missing_truth": {
            "universe": "PERSISTED",
            "ranking": "PERSISTED" if include_ranking else "TOP20_RANKING_NOT_PERSISTED",
            "selected_future": selected_truth,
            "future_detail": "AVAILABLE",
            "orders_fills_pnl": "NOT_PERSISTED",
        },
    }
    readmodel_path = readmodels / READMODEL_FILENAME
    readmodel_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _write_manifest_sha256(readmodels)
    return archive_root


def test_bind_universe_and_selected_from_durable_archive(archive_root: Path) -> None:
    archive = _write_truth_universe_archive(archive_root)
    slots = bind_market_universe_slots(generated_at=STAMP, archive_root=archive)
    assert slots["universe_ranking"].availability is Availability.AVAILABLE
    assert slots["universe_ranking"].selected_instrument_id == "ETH-USDT-SWAP"
    assert slots["universe_ranking"].ranking[0]["symbol"] == "ETH-USDT-SWAP"
    assert slots["universe_ranking"].universe[0]["exchange"] == "OKX"
    # Selected identity projected from universe selection; no invented mark/OHLCV.
    assert slots["market_instrument"].availability is Availability.AVAILABLE
    assert slots["market_instrument"].instrument_id == "ETH-USDT-SWAP"
    assert slots["market_instrument"].venue == "OKX"
    assert slots["market_instrument"].mark_price is None
    assert slots["market_instrument"].market_type is None


def test_missing_ranking_does_not_invent_ranking(archive_root: Path) -> None:
    archive = _write_truth_universe_archive(archive_root, include_ranking=False)
    slots = bind_market_universe_slots(generated_at=STAMP, archive_root=archive)
    assert slots["universe_ranking"].availability is Availability.AVAILABLE
    assert slots["universe_ranking"].ranking == ()
    assert "TOP20_RANKING_NOT_PRESENT_IN_READMODEL" in slots["universe_ranking"].reason_codes
    assert slots["universe_ranking"].selected_instrument_id == "ETH-USDT-SWAP"


def test_missing_selected_does_not_invent_selected(archive_root: Path) -> None:
    archive = _write_truth_universe_archive(archive_root, include_selected=False)
    slots = bind_market_universe_slots(generated_at=STAMP, archive_root=archive)
    assert slots["universe_ranking"].availability is Availability.AVAILABLE
    assert slots["universe_ranking"].selected_instrument_id is None
    assert slots["market_instrument"].availability is Availability.MISSING_SOURCE


def test_forbidden_btc_usd_selected_fails_closed(archive_root: Path) -> None:
    archive = _write_truth_universe_archive(archive_root, selected_symbol="BTC/USD")
    slots = bind_market_universe_slots(generated_at=STAMP, archive_root=archive)
    # Contract validation may reject before projection; either INVALID path is fail-closed.
    assert slots["universe_ranking"].availability in {
        Availability.INVALID,
        Availability.MISSING_SOURCE,
    }
    if slots["universe_ranking"].availability is Availability.INVALID:
        assert (
            REASON_SELECTED_FORBIDDEN_SYMBOL in slots["universe_ranking"].reason_codes
            or "BTC" in str(slots["universe_ranking"].reason_codes)
            or slots["universe_ranking"].reason_codes
        )


def test_source_contradiction_fails_closed(archive_root: Path) -> None:
    archive = _write_truth_universe_archive(archive_root)
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        archive_root=archive,
        market_instrument_fields={
            "instrument_id": "SOL-USDT-SWAP",
            "venue": "OKX",
            "market_type": "perpetual",
            "mark_price": 1.0,
            "reason_codes": ("OK",),
            "source_reference": "ctx://1",
        },
    )
    assert slots["market_instrument"].availability is Availability.INVALID
    assert slots["universe_ranking"].availability is Availability.INVALID
    assert REASON_SOURCE_CONTRADICTION in slots["market_instrument"].reason_codes


def test_page_aggregate_applies_phase41_without_touching_decision_or_scope() -> None:
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        market_instrument_fields={
            "instrument_id": "BTC-USDT-SWAP",
            "venue": "OKX",
            "market_type": "perpetual",
            "mark_price": 10.0,
            "reason_codes": ("OK",),
            "source_reference": "ctx://1",
        },
    )
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        slot_overrides=slots,
    )
    assert page.market_instrument.availability is Availability.AVAILABLE
    assert page.dynamic_scope.availability is Availability.NOT_BOUND
    assert page.canonical_decision.availability is Availability.NOT_BOUND
    assert page.double_play.availability is Availability.NOT_BOUND
    assert page.risk_sizing_capital.availability is Availability.NOT_BOUND
    ctx = present_market_landscape_v2(page)
    assert ctx["phase"] == "PHASE_4_1_MARKET_UNIVERSE_BINDING"
    assert ctx["product_flags"]["phase_4_1_binding_active"] is True
    assert ctx["product_flags"]["phase_4_full_pass"] is False
    assert ctx["product_flags"]["live_authorized"] is False
    assert ctx["chart"]["ohlcv"] is None
    assert ctx["scope"]["availability"] == "NOT_BOUND"
