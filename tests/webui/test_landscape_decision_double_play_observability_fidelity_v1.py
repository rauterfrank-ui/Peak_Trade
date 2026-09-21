"""S05/S06 Decision and Double Play observability fidelity (consumer-only)."""

from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.market_dashboard_landscape_producer_binding_v2 import (
    LANDSCAPE_PHASE43A_MAX_AGE_SECONDS,
)
from src.webui.market_dashboard_landscape_v2 import (
    Availability,
    MarketDashboardReadServiceV1,
    present_market_landscape_v2,
    project_canonical_decision_snapshot_v1,
    project_double_play_snapshot_v1,
)
from src.webui.market_dashboard_landscape_v2.decision_double_play_observability_v1 import (
    CAPABILITY_ID,
    JOIN_CONTRACT_PRESENT,
    MULTI_DECISION_TIMELINE_STATUS,
    build_decision_double_play_observability_v1,
)
from src.webui.market_dashboard_landscape_v2.unavailable import (
    unavailable_canonical_decision,
    unavailable_double_play,
)

STAMP = datetime(2026, 9, 21, 14, 0, 0, tzinfo=timezone.utc)
PRODUCER = datetime(2026, 9, 21, 13, 0, 0, tzinfo=timezone.utc)
REPO = Path(__file__).resolve().parents[2]
OBS_MODULE = (
    REPO
    / "src"
    / "webui"
    / "market_dashboard_landscape_v2"
    / "decision_double_play_observability_v1.py"
)


def _decision_snap(**kwargs: object):
    defaults = {
        "instrument_id": "ETH-USDT-SWAP",
        "decision": "observe",
        "direction": "neutral_observe",
        "reason_codes": ("WARMUP_ACTIVE",),
        "blockers": (),
        "decision_id": "dec-1",
        "evidence_schema_version": "canonical_trading_decision_evidence_v1",
        "evidence_digest": "a" * 64,
        "generated_at": PRODUCER,
        "effective_at": PRODUCER,
        "source_reference": "presentation://decision_test",
        "availability": Availability.AVAILABLE,
        "max_age_seconds": LANDSCAPE_PHASE43A_MAX_AGE_SECONDS,
        "is_stale": False,
    }
    defaults.update(kwargs)
    return project_canonical_decision_snapshot_v1(**defaults)  # type: ignore[arg-type]


def _dp_snap(**kwargs: object):
    defaults = {
        "overall_status": "display_ready",
        "panel_summaries": (
            {
                "name": "composition",
                "status": "display_ready",
                "summary": "Composition panel fact",
                "blockers": (),
            },
        ),
        "blockers": ("DP_BLOCK",),
        "generated_at": PRODUCER,
        "effective_at": PRODUCER,
        "source_reference": "presentation://dp_test",
        "availability": Availability.AVAILABLE,
        "max_age_seconds": LANDSCAPE_PHASE43A_MAX_AGE_SECONDS,
        "is_stale": False,
    }
    defaults.update(kwargs)
    return project_double_play_snapshot_v1(**defaults)  # type: ignore[arg-type]


def _ctx(**overrides: object) -> dict:
    decision = overrides.pop("decision", _decision_snap())
    double_play = overrides.pop("double_play", _dp_snap())
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        slot_overrides={
            "canonical_decision": decision,
            "double_play": double_play,
        },
    )
    return present_market_landscape_v2(page)


def test_observability_module_no_writer_or_composer_imports() -> None:
    text = OBS_MODULE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    import_from = {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
    }
    blob = text + "\n".join(sorted(import_from))
    for frag in (
        "materializer",
        "compose_double_play",
        "build_dashboard_display",
        "try_load_",
        "bind_market_universe",
    ):
        assert frag not in blob


def test_s05_fields_from_snapshot_only() -> None:
    obs = _ctx()["decision_double_play_observability"]
    s05 = obs["canonical_decision"]
    assert obs["capability_id"] == CAPABILITY_ID
    assert s05["decision_display"] == "observe"
    assert s05["direction_display"] == "neutral_observe"
    assert s05["instrument_id_display"] == "ETH-USDT-SWAP"
    assert s05["decision_id_display"] == "dec-1"
    assert s05["reason_codes"] == ["WARMUP_ACTIVE"]
    assert s05["source_kind"] == "canonical_trading_decision_evidence"


def test_s06_panels_from_snapshot_only_no_recomputation() -> None:
    s06 = _ctx()["decision_double_play_observability"]["double_play"]
    assert s06["overall_status_display"] == "display_ready"
    assert s06["blockers"] == ["DP_BLOCK"]
    assert s06["panel_count"] == 1
    assert s06["panels"][0]["name_display"] == "composition"
    assert s06["panels"][0]["summary_display"] == "Composition panel fact"


def test_no_artificial_s05_s06_join() -> None:
    rel = _ctx()["decision_double_play_observability"]["relationship"]
    assert JOIN_CONTRACT_PRESENT is False
    assert rel["join_contract_present"] is False
    assert rel["join_status"] == "SEPARATE_NO_SHARED_IDENTIFIER"


def test_missing_and_not_bound_distinct() -> None:
    missing = unavailable_canonical_decision(
        availability=Availability.MISSING_SOURCE,
        generated_at=STAMP,
        reason="CANONICAL_DECISION_EVIDENCE_NOT_PERSISTED_FOR_DASHBOARD",
    )
    not_bound = unavailable_double_play(
        availability=Availability.NOT_BOUND,
        generated_at=STAMP,
        reason="NOT_BOUND",
    )
    obs = _ctx(decision=missing, double_play=not_bound)["decision_double_play_observability"]
    assert obs["canonical_decision"]["availability"] == "MISSING_SOURCE"
    assert obs["double_play"]["availability"] == "NOT_BOUND"
    assert obs["canonical_decision"]["decision_display"] == "MISSING_SOURCE"
    assert obs["double_play"]["overall_status_display"] == "NOT_BOUND"


def test_stale_preserves_producer_facts() -> None:
    stale_decision = unavailable_canonical_decision(
        availability=Availability.STALE,
        generated_at=STAMP,
        reason="EVIDENCE_STALE",
    )
    # Replace with real stale projected snap
    stale_decision = _decision_snap(
        availability=Availability.STALE,
        is_stale=True,
        stale_reason="PRODUCER_AGE_EXCEEDED",
    )
    obs = _ctx(decision=stale_decision)["decision_double_play_observability"]
    assert obs["canonical_decision"]["availability"] == "STALE"
    assert obs["canonical_decision"]["is_stale_flag"] is True
    assert obs["canonical_decision"]["decision_display"] == "observe"


def test_multi_decision_timeline_missing_observability() -> None:
    assert (
        _ctx()["decision_double_play_observability"]["multi_decision_timeline_status"]
        == MULTI_DECISION_TIMELINE_STATUS
    )


def test_standalone_builder_matches_presenter() -> None:
    decision = _decision_snap()
    double_play = _dp_snap()
    direct = build_decision_double_play_observability_v1(
        decision=decision,
        double_play=double_play,
    )
    via_page = _ctx(decision=decision, double_play=double_play)[
        "decision_double_play_observability"
    ]
    assert direct == via_page


def test_ssr_renders_when_s05_s06_missing() -> None:
    client = TestClient(create_app())
    html = client.get("/market").text
    assert 'data-mdl-decision-dp-observability="true"' in html
    assert "SEPARATE_NO_SHARED_IDENTIFIER" in html
    assert MULTI_DECISION_TIMELINE_STATUS in html


def test_host_contract_regression_6681() -> None:
    from tests.webui import test_market_landscape_dashboard_host_contract_isolation_v1 as mod

    mod.test_canonical_webui_poll_declares_archive_host_contract()


def test_persistent_host_regression_6682() -> None:
    from src.webui.landscape_dashboard_persistent_local_host_v1.constants_v1 import (
        CANONICAL_BOOKMARK_URL,
    )

    assert CANONICAL_BOOKMARK_URL == "http://127.0.0.1:8765/market"


def test_universe_top20_regression_6683() -> None:
    from tests.webui import test_landscape_universe_top20_selection_rail_fidelity_v1 as mod

    mod.test_row_order_follows_readmodel_not_score_sort()


def test_source_health_fidelity_regression_6684() -> None:
    from tests.webui import test_landscape_source_health_and_projection_freshness_fidelity_v1 as mod

    mod.test_v03_slot_matrix_deterministic_twelve_rows_default_not_bound()
