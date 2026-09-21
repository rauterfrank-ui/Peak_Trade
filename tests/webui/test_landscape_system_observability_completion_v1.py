"""S03–S10/V07 Landscape system observability completion (consumer-only)."""

from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.market_dashboard_landscape_producer_binding_v2 import (
    LANDSCAPE_PHASE41_MAX_AGE_SECONDS,
)
from src.webui.market_dashboard_landscape_v2 import (
    Availability,
    MarketDashboardReadServiceV1,
    present_market_landscape_v2,
)
from src.webui.market_dashboard_landscape_v2.projections import (
    project_dynamic_scope_snapshot_v1,
    project_economic_summary_snapshot_v1,
    project_execution_reconciliation_snapshot_v1,
    project_risk_sizing_capital_snapshot_v1,
)
from src.webui.market_dashboard_landscape_v2.landscape_system_observability_completion_v1 import (
    CAPABILITY_ID,
    build_landscape_system_observability_completion_v1,
)

STAMP = datetime(2026, 9, 21, 16, 0, 0, tzinfo=timezone.utc)
PRODUCER = datetime(2026, 9, 21, 15, 0, 0, tzinfo=timezone.utc)
REPO = Path(__file__).resolve().parents[2]
COMPLETION_MODULE = (
    REPO
    / "src"
    / "webui"
    / "market_dashboard_landscape_v2"
    / "landscape_system_observability_completion_v1.py"
)


def _present(**overrides: object) -> dict:
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        slot_overrides=overrides,
    )
    return present_market_landscape_v2(page)


def test_completion_module_no_writer_or_binding_imports() -> None:
    text = COMPLETION_MODULE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    import_from = {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
    }
    blob = text + "\n".join(sorted(import_from))
    for frag in ("materializer", "bind_market_universe", "try_load_", "compose_double_play"):
        assert frag not in blob


def test_s03_s10_v07_families_deterministic_six() -> None:
    ctx = _present()
    comp = ctx["system_observability_completion"]
    assert comp["capability_id"] == CAPABILITY_ID
    assert comp["family_count"] == 6
    ids = [f["family_id"] for f in comp["families"]]
    assert ids == [
        "S03_DYNAMIC_SCOPE",
        "S04_REGIME_BULL_BEAR_SWITCH",
        "S08_RISK_SIZING_CAPITAL",
        "S09_EXECUTION_RECONCILIATION",
        "S10_ECONOMIC_SUMMARY",
        "V07_OHLCV_LIVE_MARK",
    ]
    assert all(f["availability"] == "NOT_BOUND" for f in comp["families"][:-1])
    assert comp["families"][-1]["source_family"] == "V07"


def test_s03_fields_from_dynamic_scope_snapshot_only() -> None:
    scope = project_dynamic_scope_snapshot_v1(
        scope_state="ACTIVE",
        current_scope_ref="scope-a",
        next_scope_ref="scope-b",
        reason_codes=("SCOPE_PROJECTED",),
        generated_at=PRODUCER,
        effective_at=PRODUCER,
        source_reference="fixture",
        availability=Availability.AVAILABLE,
        max_age_seconds=LANDSCAPE_PHASE41_MAX_AGE_SECONDS,
        is_stale=False,
    )
    fam = next(
        f
        for f in _present(dynamic_scope=scope)["system_observability_completion"]["families"]
        if f["family_id"] == "S03_DYNAMIC_SCOPE"
    )
    assert fam["availability"] == "AVAILABLE"
    displays = {row["field_id"]: row["display"] for row in fam["fields"]}
    assert displays["scope_state"] == "ACTIVE"
    assert displays["current_scope_ref"] == "scope-a"


def test_s08_s09_s10_from_bound_snapshots_not_recomputed() -> None:
    risk = project_risk_sizing_capital_snapshot_v1(
        risk_status="PASS",
        sizing_status="PASS",
        capital_status="PASS",
        reason_codes=("RISK_OK",),
        quantity=None,
        generated_at=PRODUCER,
        effective_at=PRODUCER,
        source_reference="fixture",
        availability=Availability.AVAILABLE,
        max_age_seconds=LANDSCAPE_PHASE41_MAX_AGE_SECONDS,
        is_stale=False,
    )
    execution = project_execution_reconciliation_snapshot_v1(
        execution_status="RECONCILED",
        reconciliation_status="MATCH",
        order_intent_ref="intent-1",
        reason_codes=(),
        generated_at=PRODUCER,
        effective_at=PRODUCER,
        source_reference="fixture",
        availability=Availability.AVAILABLE,
        max_age_seconds=LANDSCAPE_PHASE41_MAX_AGE_SECONDS,
        is_stale=False,
    )
    absent_metric = {"semantic": "ABSENT", "value": None, "reason_code": "NOT_PROVIDED"}
    digest = "d" * 64
    economic = project_economic_summary_snapshot_v1(
        economic_viability_status="VIABLE",
        economic_validity_proven=True,
        profitability_claim_allowed=False,
        policy_threshold_status="PASS",
        policy_version="v1",
        authority_effect="NONE",
        runtime_effect=False,
        order_effect=False,
        reason_codes=(),
        profit_factor={"semantic": "METRIC", "value": "1.2", "reason_code": None},
        net_return=absent_metric,
        max_drawdown=absent_metric,
        sharpe=absent_metric,
        trade_count=absent_metric,
        funding_drag=absent_metric,
        evidence_ref="evidence://x",
        contract_version="v1",
        owner="test",
        strategy_id="s1",
        strategy_version="1",
        config_digest=digest,
        implementation_digest=digest,
        data_digest=digest,
        manifest_digest=digest,
        wiring_chain_digest=digest,
        policy_digest=digest,
        generated_at=PRODUCER,
        effective_at=PRODUCER,
        source_reference="fixture",
        availability=Availability.AVAILABLE,
        max_age_seconds=LANDSCAPE_PHASE41_MAX_AGE_SECONDS,
        is_stale=False,
    )
    ctx = _present(
        risk_sizing_capital=risk,
        execution_reconciliation=execution,
        economic_summary=economic,
    )
    by_id = {f["family_id"]: f for f in ctx["system_observability_completion"]["families"]}
    assert by_id["S08_RISK_SIZING_CAPITAL"]["fields"][0]["display"] == "PASS"
    assert by_id["S09_EXECUTION_RECONCILIATION"]["fields"][0]["display"] == "RECONCILED"
    assert by_id["S10_ECONOMIC_SUMMARY"]["fields"][0]["display"] == "VIABLE"
    assert "1.2" in json.dumps(by_id["S10_ECONOMIC_SUMMARY"])


def test_v07_uses_chart_binding_fields_only() -> None:
    ctx = _present()
    chart = ctx["chart"]
    direct = build_landscape_system_observability_completion_v1(
        dynamic_scope=MarketDashboardReadServiceV1()
        .load_page_snapshot(generated_at=STAMP)
        .dynamic_scope,
        regime_bull_bear_switch=MarketDashboardReadServiceV1()
        .load_page_snapshot(generated_at=STAMP)
        .regime_bull_bear_switch,
        risk_sizing_capital=MarketDashboardReadServiceV1()
        .load_page_snapshot(generated_at=STAMP)
        .risk_sizing_capital,
        execution_reconciliation=MarketDashboardReadServiceV1()
        .load_page_snapshot(generated_at=STAMP)
        .execution_reconciliation,
        economic_summary=MarketDashboardReadServiceV1()
        .load_page_snapshot(generated_at=STAMP)
        .economic_summary,
        chart=chart,
    )
    v07 = next(f for f in direct["families"] if f["family_id"] == "V07_OHLCV_LIVE_MARK")
    assert v07["fields"][0]["field_id"] == "data_connection_state"
    assert v07["fields"][0]["display"] == chart["data_connection_state"]


def test_ssr_renders_completion_hub_when_all_not_bound() -> None:
    html = TestClient(create_app()).get("/market").text
    assert 'data-mdl-system-observability-completion="true"' in html
    assert "S03_DYNAMIC_SCOPE" in html
    assert "V07_OHLCV_LIVE_MARK" in html


def test_regressions_6681_through_6685() -> None:
    from tests.webui import test_landscape_decision_double_play_observability_fidelity_v1 as s05s06
    from tests.webui import (
        test_landscape_source_health_and_projection_freshness_fidelity_v1 as v03v04,
    )
    from tests.webui import test_landscape_universe_top20_selection_rail_fidelity_v1 as s01
    from tests.webui import test_market_landscape_dashboard_host_contract_isolation_v1 as host
    from src.webui.landscape_dashboard_persistent_local_host_v1.constants_v1 import (
        CANONICAL_BOOKMARK_URL,
    )

    host.test_canonical_webui_poll_declares_archive_host_contract()
    assert CANONICAL_BOOKMARK_URL == "http://127.0.0.1:8765/market"
    s01.test_row_order_follows_readmodel_not_score_sort()
    v03v04.test_v03_slot_matrix_deterministic_twelve_rows_default_not_bound()
    s05s06.test_no_artificial_s05_s06_join()
