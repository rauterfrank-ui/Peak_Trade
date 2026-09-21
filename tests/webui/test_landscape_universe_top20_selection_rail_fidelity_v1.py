"""Universe / TOP-20 / Selection rail fidelity (S01 consumer-only)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.ops.primary_evidence_retention_v0 import is_under_tmp
from scripts.ops.primary_evidence_retention_v0 import (
    write_manifest_sha256 as _write_manifest_sha256,
)
from src.webui.app import create_app
from src.webui.market_dashboard_landscape_producer_binding_v2 import (
    LANDSCAPE_PHASE41_MAX_AGE_SECONDS,
    bind_market_universe_slots,
)
from src.webui.market_dashboard_landscape_v2 import (
    Availability,
    MarketDashboardReadServiceV1,
    present_market_landscape_v2,
    project_universe_ranking_snapshot_v1,
)
from src.webui.market_dashboard_landscape_v2.universe_rail_presentation_v1 import (
    REASON_SELECTED_ABSENT,
    REASON_TOP20_ABSENT,
    build_universe_rail_presentation_v1,
)
from src.webui.market_dashboard_landscape_v2.unavailable import (
    unavailable_universe_ranking,
)
from src.webui.workflow_dashboard_archive_root_v1 import ENV_ARCHIVE_ROOT
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_producer_v1 import (
    READMODEL_FILENAME,
    READMODELS_DIRNAME,
)

STAMP = datetime(2026, 9, 21, 12, 0, 0, tzinfo=timezone.utc)
PRODUCER_FRESH = datetime(2026, 9, 21, 11, 0, 0, tzinfo=timezone.utc)
PRODUCER_STALE = STAMP - timedelta(seconds=LANDSCAPE_PHASE41_MAX_AGE_SECONDS + 60)
REPO = Path(__file__).resolve().parents[2]
SCRATCH_ROOT = REPO / "tests" / "_durable_archive_scratch"


def _snap(**kwargs: object):  # type: ignore[no-untyped-def]
    defaults = {
        "ranking": (),
        "universe": (),
        "selected_instrument_id": None,
        "reason_codes": ("UNIVERSE_SELECTION_READMODEL_PROJECTED",),
        "generated_at": PRODUCER_FRESH,
        "effective_at": PRODUCER_FRESH,
        "source_reference": "fixture",
        "availability": Availability.AVAILABLE,
        "max_age_seconds": LANDSCAPE_PHASE41_MAX_AGE_SECONDS,
        "is_stale": False,
    }
    defaults.update(kwargs)
    return project_universe_ranking_snapshot_v1(**defaults)  # type: ignore[arg-type]


def _present(snap):  # type: ignore[no-untyped-def]
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        git_sha=None,
        slot_overrides={"universe_ranking": snap},
    )
    return present_market_landscape_v2(page)


def _write_universe_readmodel(archive_root: Path, payload: dict) -> None:
    rm = archive_root / READMODELS_DIRNAME
    rm.mkdir(parents=True, exist_ok=True)
    path = rm / READMODEL_FILENAME
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_manifest_sha256(rm)


def _payload_full_top20(*, generated_at: str, n: int = 20) -> dict:
    ranking = [
        {
            "row_id": f"r-{i}",
            "symbol": f"SYM{i:02d}-USDT-SWAP",
            "rank": i,
            "display_score": float(100 - i),
        }
        for i in range(1, n + 1)
    ]
    universe = ranking[:]
    return {
        "schema_name": "universe_selection_readmodel.v1",
        "schema_version": 1,
        "non_authorizing": True,
        "source_run_id": "run_top20_full",
        "source_stage": "paper",
        "generated_at": generated_at,
        "fixture_marked": False,
        "universe": universe,
        "ranking": ranking,
        "selected_future": {
            "row_id": "s-1",
            "symbol": "SYM01-USDT-SWAP",
            "rank": 1,
            "truth_status": "PERSISTED",
            "selection_reason": "top_ranked",
        },
        "market_snapshot": {"truth_status": "PERSISTED", "source_kind": "fixture"},
        "missing_truth": {
            "universe": "PERSISTED",
            "ranking": "PERSISTED",
            "selected_future": "PERSISTED",
            "future_detail": "AVAILABLE",
            "orders_fills_pnl": "NOT_PERSISTED",
        },
        "evidence": {"links": []},
    }


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


def test_full_top20_renders_all_rows_without_truncation(archive_root: Path) -> None:
    _write_universe_readmodel(
        archive_root,
        _payload_full_top20(generated_at=PRODUCER_FRESH.isoformat().replace("+00:00", "Z")),
    )
    slots = bind_market_universe_slots(generated_at=STAMP, archive_root=archive_root)
    view = _present(slots["universe_ranking"])
    board = view["universe_rail"]["ranking_board"]
    assert board["display_state"] == "FULL"
    assert board["row_count"] == 20
    assert len(board["rows"]) == 20
    assert board["rows"][0]["symbol"] == "SYM01-USDT-SWAP"
    assert board["rows"][0]["is_selected"] is True
    assert "eligibility_label" not in view["universe_rail"]


def test_partial_ranking_fewer_than_twenty_not_padded() -> None:
    snap = _snap(
        ranking=[
            {"row_id": "r1", "symbol": "A-USDT-SWAP", "rank": 1, "display_score": 9.0},
            {"row_id": "r2", "symbol": "B-USDT-SWAP", "rank": 2},
        ],
        universe=[{"row_id": "u1", "symbol": "A-USDT-SWAP", "rank": 1}],
        selected_instrument_id="A-USDT-SWAP",
        selected_rank=1,
        reason_codes=("UNIVERSE_SELECTION_READMODEL_PROJECTED", REASON_TOP20_ABSENT),
    )
    rail = build_universe_rail_presentation_v1(snap)
    assert rail.ranking_board_display_state == "PARTIAL"
    assert rail.ranking_board_row_count == 2


def test_ranking_absent_display_state_missing() -> None:
    snap = _snap(
        ranking=[],
        universe=[{"row_id": "u1", "symbol": "A-USDT-SWAP", "rank": 1}],
        reason_codes=("UNIVERSE_SELECTION_READMODEL_PROJECTED", REASON_TOP20_ABSENT),
        selected_instrument_id=None,
    )
    assert build_universe_rail_presentation_v1(snap).ranking_board_display_state == "MISSING"


def test_selected_future_absent() -> None:
    snap = _snap(
        ranking=[{"row_id": "r1", "symbol": "X-USDT-SWAP", "rank": 1}],
        selected_instrument_id=None,
        reason_codes=("UNIVERSE_SELECTION_READMODEL_PROJECTED", REASON_SELECTED_ABSENT),
    )
    rail = build_universe_rail_presentation_v1(snap)
    assert rail.selected_future_display_state in {"MISSING", "PARTIAL"}


def test_selected_not_in_ranking_still_shown_without_dashboard_selection() -> None:
    snap = _snap(
        ranking=[{"row_id": "r1", "symbol": "A-USDT-SWAP", "rank": 1}],
        selected_instrument_id="Z-USDT-SWAP",
        selected_rank=99,
        selection_reason="explicit",
    )
    view = _present(snap)
    assert view["universe_rail"]["selected_future"]["instrument_id"] == "Z-USDT-SWAP"
    assert all(not row["is_selected"] for row in view["universe_rail"]["ranking_board"]["rows"])


def test_score_absent_shows_dash() -> None:
    snap = _snap(
        ranking=[{"row_id": "r1", "symbol": "A-USDT-SWAP", "rank": 1}],
        selected_instrument_id="A-USDT-SWAP",
    )
    assert build_universe_rail_presentation_v1(snap).selected_future_score == "—"


def test_selection_reason_absent_shows_dash_when_available() -> None:
    snap = _snap(
        ranking=[{"row_id": "r1", "symbol": "A-USDT-SWAP", "rank": 1}],
        selected_instrument_id="A-USDT-SWAP",
        selection_reason=None,
    )
    view = _present(snap)
    assert view["universe_rail"]["selected_future"]["selection_reason_display"] == "—"


def test_stale_source_preserves_facts() -> None:
    snap = _snap(
        ranking=[{"row_id": "r1", "symbol": "A-USDT-SWAP", "rank": 1, "display_score": 1.5}],
        selected_instrument_id="A-USDT-SWAP",
        selected_rank=1,
        source_run_id="stale_run",
        availability=Availability.STALE,
        is_stale=True,
        stale_reason="PRODUCER_DATA_EXCEEDED_LANDSCAPE_MAX_AGE",
    )
    rail = build_universe_rail_presentation_v1(snap)
    assert rail.provenance_freshness_label.startswith("STALE")
    assert rail.selected_future_instrument == "A-USDT-SWAP"


def test_missing_source_fail_closed() -> None:
    snap = unavailable_universe_ranking(
        availability=Availability.MISSING_SOURCE,
        generated_at=STAMP,
        reason="UNIVERSE_SELECTION_READMODEL_ABSENT",
    )
    rail = build_universe_rail_presentation_v1(snap)
    assert rail.ranking_board_display_state == "MISSING"
    assert rail.ranking_board_row_count == 0


def test_source_run_id_present_and_absent() -> None:
    with_id = _snap(source_run_id="run_abc", selected_instrument_id="A-USDT-SWAP", ranking=[])
    without = _snap(source_run_id=None, selected_instrument_id="A-USDT-SWAP", ranking=[])
    assert build_universe_rail_presentation_v1(with_id).source_run_id == "run_abc"
    assert build_universe_rail_presentation_v1(without).source_run_id is None


def test_row_order_follows_readmodel_not_score_sort() -> None:
    snap = _snap(
        ranking=[
            {"row_id": "r-low", "symbol": "LOW-USDT-SWAP", "rank": 2, "display_score": 1.0},
            {"row_id": "r-high", "symbol": "HIGH-USDT-SWAP", "rank": 1, "display_score": 99.0},
        ],
        selected_instrument_id="LOW-USDT-SWAP",
    )
    rows = build_universe_rail_presentation_v1(snap).ranking_board_rows
    assert [r["symbol"] for r in rows] == ["LOW-USDT-SWAP", "HIGH-USDT-SWAP"]
    assert rows[0]["row_order_index"] == 0


def test_membership_descriptive_not_eligibility_label() -> None:
    snap = _snap(
        ranking=[{"row_id": "r1", "symbol": "A-USDT-SWAP", "rank": 1}],
        universe=[{"row_id": "u1", "symbol": "A-USDT-SWAP", "rank": 1}],
        selected_instrument_id="A-USDT-SWAP",
    )
    view = _present(snap)
    assert view["universe_rail"]["membership_in_universe_label"] == "IN_UNIVERSE"
    assert "eligibility_label" not in view["universe_rail"]


def _ranking_board_empty_html_text(html: str) -> str:
    chunk = html.split('data-mdl-field="ranking_board_empty"', 1)[1]
    return chunk.split(">", 1)[1].split("<", 1)[0].strip()


def test_empty_ranking_board_uses_display_state_not_slot_availability() -> None:
    snap = unavailable_universe_ranking(
        availability=Availability.NOT_BOUND,
        generated_at=STAMP,
        reason="UNIVERSE_NOT_BOUND",
    )
    view = _present(snap)
    board = view["universe_rail"]["ranking_board"]
    assert board["row_count"] == 0
    assert board["display_state"] == "MISSING"
    assert view["universe"]["availability_label"] == "NOT_BOUND"
    assert board["display_state"] != view["universe"]["availability_label"]


def test_ssr_ranking_board_empty_binds_display_state(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive_root))
    slots = bind_market_universe_slots(generated_at=STAMP, archive_root=archive_root)
    view = _present(slots["universe_ranking"])
    expected = view["universe_rail"]["ranking_board"]["display_state"]
    assert expected == "MISSING"
    assert view["universe"]["availability_label"] == "MISSING_SOURCE"

    html = TestClient(create_app()).get("/market").text
    assert 'data-mdl-field="ranking_board_empty"' in html
    assert _ranking_board_empty_html_text(html) == expected
    assert _ranking_board_empty_html_text(html) != view["universe"]["availability_label"]


def test_invalid_empty_board_display_state_matches_template_field() -> None:
    snap = unavailable_universe_ranking(
        availability=Availability.INVALID,
        generated_at=STAMP,
        reason="INVALID_PROVENANCE",
    )
    view = _present(snap)
    assert view["universe_rail"]["ranking_board"]["display_state"] == "INVALID"
    assert view["universe"]["availability_label"] == "INVALID"


def test_market_route_html_includes_top20_panel(archive_root: Path) -> None:
    _write_universe_readmodel(
        archive_root,
        _payload_full_top20(generated_at=PRODUCER_FRESH.isoformat().replace("+00:00", "Z"), n=5),
    )
    # SSR path uses bind at request time — inject via env would be heavy; assert presenter+template fields.
    slots = bind_market_universe_slots(generated_at=STAMP, archive_root=archive_root)
    view = _present(slots["universe_ranking"])
    assert view["universe_rail"]["ranking_board"]["row_count"] == 5

    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "TOP-20 Ranking" in html
    assert "Selected Future" in html
    assert "Membership (descriptive)" in html


def test_host_contract_isolation_regression() -> None:
    from tests.webui import test_market_landscape_dashboard_host_contract_isolation_v1 as mod

    mod.test_canonical_webui_poll_declares_archive_host_contract()


def test_persistent_host_constants_unchanged() -> None:
    from src.webui.landscape_dashboard_persistent_local_host_v1.constants_v1 import (
        CANONICAL_BOOKMARK_URL,
    )

    assert CANONICAL_BOOKMARK_URL == "http://127.0.0.1:8765/market"
