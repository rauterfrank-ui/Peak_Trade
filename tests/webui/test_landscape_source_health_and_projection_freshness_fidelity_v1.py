"""V03/V04 Source Health slot matrix and presentation projection fidelity (consumer-only)."""

from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.market_dashboard_landscape_v2 import (
    Availability,
    MarketDashboardReadServiceV1,
    present_market_landscape_v2,
)
from src.webui.market_dashboard_landscape_v2.source_health_projection_fidelity_v1 import (
    CAPABILITY_ID,
    PRESENTATION_PROJECTION_FAMILIES_V1,
    build_presentation_projection_presence_matrix_v1,
    presentation_presence_from_availability_v1,
)
from src.webui.market_dashboard_landscape_v2.unavailable import (
    unavailable_canonical_decision,
    unavailable_universe_ranking,
)

STAMP = datetime(2026, 9, 21, 12, 0, 0, tzinfo=timezone.utc)
REPO = Path(__file__).resolve().parents[2]
FIDELITY_MODULE = (
    REPO
    / "src"
    / "webui"
    / "market_dashboard_landscape_v2"
    / "source_health_projection_fidelity_v1.py"
)
PRODUCER_BINDING = REPO / "src" / "webui" / "market_dashboard_landscape_producer_binding_v2.py"


def _default_ctx() -> dict:
    page = MarketDashboardReadServiceV1().load_page_snapshot(generated_at=STAMP)
    return present_market_landscape_v2(page)


def test_fidelity_module_has_no_writer_or_archive_loader_imports() -> None:
    text = FIDELITY_MODULE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    imports = {
        node.names[0].name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for name in node.names
    }
    import_from = {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
    }
    forbidden_fragments = (
        "materializer",
        "workflow_dashboard_archive_root",
        "try_load_",
        "write_",
        "bind_market_universe",
    )
    blob = text + "\n".join(sorted(imports | import_from))
    for frag in forbidden_fragments:
        assert frag not in blob, frag


def test_v03_slot_matrix_deterministic_twelve_rows_default_not_bound() -> None:
    ctx = _default_ctx()
    matrix = ctx["source_health"]["slot_matrix"]
    assert len(matrix) == 12
    slots = [row["slot"] for row in matrix]
    assert slots == sorted(slots)
    assert all(row["availability"] == "NOT_BOUND" for row in matrix)
    assert ctx["source_health"]["availability"] == "NOT_BOUND"
    assert ctx["source_health"]["sources"] == matrix


def test_v04_projection_families_deterministic_eight_rows() -> None:
    ctx = _default_ctx()
    fidelity = ctx["presentation_projection_fidelity"]
    assert fidelity["capability_id"] == CAPABILITY_ID
    assert fidelity["authority"] == "NONE"
    assert fidelity["family_count"] == 8
    families = fidelity["families"]
    ids = [row["family_id"] for row in families]
    assert ids == sorted(ids)
    assert len(families) == len(PRESENTATION_PROJECTION_FAMILIES_V1)
    assert all(row["presence"] == "NOT_BOUND" for row in families)
    assert all(row["availability"] == "NOT_BOUND" for row in families)


def test_presence_vocabulary_fail_closed() -> None:
    assert presentation_presence_from_availability_v1("MISSING_SOURCE") == "ABSENT"
    assert presentation_presence_from_availability_v1("NOT_BOUND") == "NOT_BOUND"
    assert presentation_presence_from_availability_v1("INVALID") == "INVALID"
    assert presentation_presence_from_availability_v1("AVAILABLE") == "PRESENT"
    assert presentation_presence_from_availability_v1("STALE") == "PRESENT"
    assert presentation_presence_from_availability_v1("MYSTERY") == "UNKNOWN"


def test_missing_source_stays_missing_not_upgraded() -> None:
    missing = unavailable_universe_ranking(
        availability=Availability.MISSING_SOURCE,
        generated_at=STAMP,
        reason="UNIVERSE_SELECTION_READMODEL_ABSENT",
    )
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        slot_overrides={"universe_ranking": missing},
    )
    ctx = present_market_landscape_v2(page)
    row = next(r for r in ctx["source_health"]["slot_matrix"] if r["slot"] == "universe_ranking")
    assert row["availability"] == "MISSING_SOURCE"
    assert not any(
        f["slot"] == "universe_ranking" for f in ctx["presentation_projection_fidelity"]["families"]
    )


def test_stale_only_when_bound_freshness_contract_says_so() -> None:
    stale = unavailable_canonical_decision(
        availability=Availability.STALE,
        generated_at=STAMP,
        reason="EVIDENCE_STALE",
    )
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        slot_overrides={"canonical_decision": stale},
    )
    ctx = present_market_landscape_v2(page)
    row = next(r for r in ctx["source_health"]["slot_matrix"] if r["slot"] == "canonical_decision")
    assert row["availability"] == "STALE"
    assert row["is_stale"] is True
    fam = next(
        f
        for f in ctx["presentation_projection_fidelity"]["families"]
        if f["slot"] == "canonical_decision"
    )
    assert fam["presence"] == "PRESENT"
    assert fam["availability"] == "STALE"
    assert fam["is_stale"] is True


def test_ssr_renders_fidelity_region_when_sources_missing() -> None:
    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert 'data-mdl-source-projection-fidelity="true"' in html
    assert 'data-mdl-slot-matrix="true"' in html
    assert 'data-mdl-projection-matrix="true"' in html
    assert "NOT_BOUND" in html
    anchor = html.index('data-mdl-source-projection-fidelity="true"')
    fidelity_slice = html[anchor : anchor + 8000]
    assert "HEALTHY" not in fidelity_slice
    assert "OK" != fidelity_slice.split("data-mdl-slot-matrix")[0][-20:]


def test_no_productive_writer_import_from_presenter_path() -> None:
    binding_text = PRODUCER_BINDING.read_text(encoding="utf-8")
    assert "source_health_projection_fidelity_v1" not in binding_text


def test_host_contract_regression_6681() -> None:
    from tests.webui import test_market_landscape_dashboard_host_contract_isolation_v1 as mod

    mod.test_canonical_webui_poll_declares_archive_host_contract()
    mod.test_canonical_webui_market_html_carries_host_contract_attributes()


def test_persistent_host_bookmark_regression_6682() -> None:
    from src.webui.landscape_dashboard_persistent_local_host_v1.constants_v1 import (
        CANONICAL_BOOKMARK_URL,
    )

    assert CANONICAL_BOOKMARK_URL == "http://127.0.0.1:8765/market"


def test_universe_top20_regression_6683() -> None:
    from tests.webui import test_landscape_universe_top20_selection_rail_fidelity_v1 as mod

    mod.test_row_order_follows_readmodel_not_score_sort()


def test_build_presentation_projection_matrix_from_engineering_slot_views() -> None:
    page = MarketDashboardReadServiceV1().load_page_snapshot(generated_at=STAMP)
    ctx = present_market_landscape_v2(page)
    eng = ctx["engineering"]["slots"]
    matrix = build_presentation_projection_presence_matrix_v1(eng)
    assert matrix["family_count"] == 8
    assert "HEALTHY" not in json.dumps(matrix)
    assert all(row["freshness_display"] != "" for row in matrix["families"])
