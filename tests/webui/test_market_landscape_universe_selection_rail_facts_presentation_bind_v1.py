"""Presentation binding: universe_selection_rail_facts from existing readmodel.

CAPABILITY: presentation-only mapping of watchlist count, selected rank,
source_run_id→session, and selection_reason. No producer/runtime mutation.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import is_under_tmp
from scripts.ops.primary_evidence_retention_v0 import (
    write_manifest_sha256 as _write_manifest_sha256,
)
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
from src.webui.market_dashboard_landscape_v2.unavailable import (
    unavailable_universe_ranking,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_producer_v1 import (
    READMODEL_FILENAME,
    READMODELS_DIRNAME,
)

STAMP = datetime(2026, 7, 23, 18, 0, 0, tzinfo=timezone.utc)
PRODUCER_FRESH = datetime(2026, 7, 23, 17, 0, 0, tzinfo=timezone.utc)
PRODUCER_STALE = STAMP - timedelta(seconds=LANDSCAPE_PHASE41_MAX_AGE_SECONDS + 3600)
REPO = Path(__file__).resolve().parents[2]
SCRATCH_ROOT = REPO / "tests" / "_durable_archive_scratch"


def _write_universe_readmodel(archive_root: Path, payload: dict) -> None:
    rm = archive_root / READMODELS_DIRNAME
    rm.mkdir(parents=True, exist_ok=True)
    path = rm / READMODEL_FILENAME
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_manifest_sha256(rm)


def _complete_payload(
    *,
    generated_at: str,
    source_run_id: str = "run_universe_rail_facts_v1",
    selection_reason: str | None = "upstream_explicit_selection",
    selected_rank: int = 1,
    universe_n: int = 3,
    include_selected: bool = True,
) -> dict:
    universe = [
        {
            "row_id": f"u-{i}",
            "symbol": f"SYM{i}-USDT-SWAP",
            "rank": i,
            "exchange": "okx",
            "notes": "fixture",
        }
        for i in range(1, universe_n + 1)
    ]
    ranking = [
        {
            "row_id": f"r-{i}",
            "symbol": f"SYM{i}-USDT-SWAP",
            "rank": i,
            "notes": "fixture",
        }
        for i in range(1, min(universe_n, 3) + 1)
    ]
    selected = None
    if include_selected:
        selected = {
            "row_id": "s-1",
            "symbol": "SYM1-USDT-SWAP",
            "rank": selected_rank,
            "truth_status": "PERSISTED",
            "selection_reason": selection_reason,
            "notes": "fixture",
        }
    return {
        "schema_name": "universe_selection_readmodel.v1",
        "schema_version": 1,
        "non_authorizing": True,
        "source_run_id": source_run_id,
        "source_stage": "paper",
        "generated_at": generated_at,
        "fixture_marked": False,
        "universe": universe,
        "ranking": ranking,
        "selected_future": selected,
        "market_snapshot": {
            "truth_status": "PERSISTED",
            "source_kind": "fixture",
            "snapshot_id": "snap-1",
            "exchange": "okx",
            "captured_at": generated_at,
        },
        "missing_truth": {
            "universe": "PERSISTED",
            "ranking": "PERSISTED",
            "selected_future": "PERSISTED" if include_selected else "NOT_PERSISTED",
            "future_detail": "AVAILABLE",
            "orders_fills_pnl": "NOT_PERSISTED",
        },
        "evidence": {
            "producer_contract": "universe_selection_producer.v1",
            "storage_target": "readmodels/universe_selection_readmodel.v1.json",
            "links": [],
        },
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


def test_complete_canonical_source_maps_all_rail_family_members(archive_root: Path) -> None:
    _write_universe_readmodel(
        archive_root,
        _complete_payload(generated_at=PRODUCER_FRESH.isoformat().replace("+00:00", "Z")),
    )
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        git_sha=None,
        archive_root=archive_root,
    )
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        git_sha=None,
        slot_overrides=slots,
    )
    view = present_market_landscape_v2(page)
    rail = view["universe_rail"]
    assert page.universe_ranking.availability is Availability.AVAILABLE
    assert rail["watchlist_label"] == "3"
    assert rail["rank_label"] == "#1"
    assert rail["selection_reason_label"] == "upstream_explicit_selection"
    assert rail["session_label"] == "run_universe_rail_facts_v1"
    assert rail["session_availability"] == Availability.AVAILABLE.value
    assert view["bootstrap_session_id"] == "run_universe_rail_facts_v1"
    # No fabricated repository SHA from this family.
    assert (
        view.get("bootstrap_repository_sha") in (None, "", "—")
        or "bootstrap_repository_sha" not in view
    )


def test_partial_source_missing_selection_reason_stays_honest(archive_root: Path) -> None:
    payload = _complete_payload(
        generated_at=PRODUCER_FRESH.isoformat().replace("+00:00", "Z"),
        selection_reason=None,
    )
    assert payload["selected_future"] is not None
    payload["selected_future"].pop("selection_reason", None)
    _write_universe_readmodel(archive_root, payload)
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        git_sha=None,
        archive_root=archive_root,
    )
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        git_sha=None,
        slot_overrides=slots,
    )
    view = present_market_landscape_v2(page)
    assert view["universe_rail"]["selection_reason_label"] == "—"
    assert view["universe_rail"]["watchlist_label"] == "3"
    assert view["universe_rail"]["rank_label"] == "#1"
    assert page.universe_ranking.selection_reason is None


def test_absent_source_preserves_missing_source_labels() -> None:
    snap = unavailable_universe_ranking(
        availability=Availability.MISSING_SOURCE,
        generated_at=STAMP,
        reason="UNIVERSE_SELECTION_READMODEL_ABSENT",
    )
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        git_sha=None,
        slot_overrides={"universe_ranking": snap},
    )
    view = present_market_landscape_v2(page)
    rail = view["universe_rail"]
    assert rail["watchlist_label"] == "MISSING_SOURCE"
    assert rail["rank_label"] == "MISSING_SOURCE"
    assert rail["selection_reason_label"] == "MISSING_SOURCE"
    assert rail["session_label"] == "MISSING_SOURCE"
    assert rail["session_availability"] == Availability.MISSING_SOURCE.value
    assert view["bootstrap_session_id"] == ""


def test_unavailable_empty_archive_is_missing_source(archive_root: Path) -> None:
    # Archive directory exists but has no universe_selection_readmodel.v1.json.
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        git_sha=None,
        archive_root=archive_root,
    )
    assert slots["universe_ranking"].availability is Availability.MISSING_SOURCE
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        git_sha=None,
        slot_overrides=slots,
    )
    view = present_market_landscape_v2(page)
    assert view["universe_rail"]["watchlist_label"] == "MISSING_SOURCE"
    assert view["bootstrap_session_id"] == ""


def test_stale_source_still_shows_authentic_facts_not_availability_token(
    archive_root: Path,
) -> None:
    _write_universe_readmodel(
        archive_root,
        _complete_payload(
            generated_at=PRODUCER_STALE.isoformat().replace("+00:00", "Z"),
            universe_n=5,
            selected_rank=2,
            source_run_id="stale_run_v1",
            selection_reason="top_ranked",
        ),
    )
    # Force selected rank 2 on symbol SYM2 for authenticity.
    payload = json.loads(
        (archive_root / READMODELS_DIRNAME / READMODEL_FILENAME).read_text(encoding="utf-8")
    )
    payload["selected_future"] = {
        "row_id": "s-2",
        "symbol": "SYM2-USDT-SWAP",
        "rank": 2,
        "truth_status": "PERSISTED",
        "selection_reason": "top_ranked",
        "notes": "fixture",
    }
    _write_universe_readmodel(archive_root, payload)
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        git_sha=None,
        archive_root=archive_root,
    )
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        git_sha=None,
        slot_overrides=slots,
    )
    view = present_market_landscape_v2(page)
    assert page.universe_ranking.availability is Availability.STALE
    rail = view["universe_rail"]
    assert rail["watchlist_label"] == "5"
    assert rail["rank_label"] == "#2"
    assert rail["selection_reason_label"] == "top_ranked"
    assert rail["session_label"] == "stale_run_v1"
    assert rail["watchlist_label"] != "STALE"
    assert rail["rank_label"] != "STALE"


def test_projection_helper_does_not_fabricate_optional_fields() -> None:
    snap = project_universe_ranking_snapshot_v1(
        ranking=[{"row_id": "r1", "symbol": "AAA-USDT-SWAP", "rank": 1}],
        universe=[{"row_id": "u1", "symbol": "AAA-USDT-SWAP", "rank": 1, "exchange": "okx"}],
        selected_instrument_id="AAA-USDT-SWAP",
        reason_codes=("UNIVERSE_SELECTION_READMODEL_PROJECTED",),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="fixture",
        availability=Availability.AVAILABLE,
        max_age_seconds=LANDSCAPE_PHASE41_MAX_AGE_SECONDS,
        is_stale=False,
    )
    assert snap.source_run_id is None
    assert snap.selection_reason is None
    assert snap.selected_rank is None
    view = present_market_landscape_v2(
        MarketDashboardReadServiceV1().load_page_snapshot(
            generated_at=STAMP,
            git_sha=None,
            slot_overrides={"universe_ranking": snap},
        )
    )
    assert view["universe_rail"]["selection_reason_label"] == "—"
    assert view["universe_rail"]["rank_label"] == "NOT_AVAILABLE"
    assert view["universe_rail"]["session_label"] == "—"
    assert view["universe_rail"]["session_availability"] == Availability.MISSING_SOURCE.value


def test_no_presentation_boundary_imports_trading_runtime() -> None:
    import src.webui.market_dashboard_landscape_v2.contracts as contracts_mod
    import src.webui.market_dashboard_landscape_v2.presenter as presenter_mod

    for mod in (presenter_mod, contracts_mod):
        src = Path(mod.__file__).read_text(encoding="utf-8")
        assert "from trading" not in src
        assert "import trading" not in src
        assert "compose_double_play" not in src
        assert "build_canonical_order_intent" not in src
