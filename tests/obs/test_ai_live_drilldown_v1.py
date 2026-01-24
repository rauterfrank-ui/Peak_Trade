from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_dashboard() -> dict[str, Any]:
    p = (
        PROJECT_ROOT
        / "docs"
        / "webui"
        / "observability"
        / "grafana"
        / "dashboards"
        / "execution"
        / "peaktrade-execution-watch-overview.json"
    )
    return json.loads(p.read_text(encoding="utf-8"))


def _all_prom_exprs(dash: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for panel in dash.get("panels", []):
        for t in panel.get("targets", []) or []:
            expr = t.get("expr")
            if isinstance(expr, str) and expr.strip():
                out.append(expr)
    return out


def test_dashboard_json_parses() -> None:
    dash = _load_dashboard()
    assert dash.get("uid") == "peaktrade-execution-watch-overview"


def test_drilldown_run_id_variable_exists_and_uses_ds_local() -> None:
    dash = _load_dashboard()
    templ = (dash.get("templating") or {}).get("list") or []
    var = next((v for v in templ if (v.get("type"), v.get("name")) == ("query", "run_id")), None)
    assert var is not None, "expected dashboard variable run_id"
    assert (var.get("datasource") or {}).get("uid") == "${DS_LOCAL}"
    q = (var.get("query") or {}).get("query")
    assert isinstance(q, str)
    assert "label_values(" in q
    assert "peaktrade_ai_decisions_total" in q
    assert ", run_id" in q
    assert var.get("includeAll") is True
    assert var.get("allValue") == ".*"


def test_drilldown_panels_filter_by_run_id_and_are_no_data_hardened() -> None:
    dash = _load_dashboard()
    exprs = _all_prom_exprs(dash)

    # Filter contract: at least the drilldown panels must use the run_id variable.
    assert any('run_id=~"$run_id"' in e for e in exprs), "expected run_id filter usage in panels"

    # Hardening contract (for the drilldown scalar panels): no-data should yield 0 not empty.
    must_be_hardened = [
        "Recent: last event age (s)",
        "Recent: decisions (1m)",
        "Recent: decisions (5m)",
        "Top reject reasons (10m)",
    ]

    for panel in dash.get("panels", []):
        title = panel.get("title")
        if title not in must_be_hardened:
            continue
        targets = panel.get("targets", []) or []
        assert targets, f"panel {title!r} has no targets"
        expr = targets[0].get("expr") if isinstance(targets[0], dict) else None
        assert isinstance(expr, str)
        if title == "Top reject reasons (10m)":
            assert "label_replace(vector(0)" in expr, "expected default bucket for empty results"
        else:
            assert "or on() vector(0)" in expr, "expected no-data hardening via vector(0)"


def test_dashboard_queries_have_no_promql_pipes_and_safe_divides() -> None:
    dash = _load_dashboard()
    exprs = _all_prom_exprs(dash)

    assert not any("|" in e for e in exprs), "unexpected '|' in PromQL expr (pipes not supported)"

    # Heuristic: if a query divides, ensure it uses clamp_min() somewhere (denominator guard).
    for e in exprs:
        if "/" in e:
            assert "clamp_min(" in e, f"divide without clamp_min guard: {e!r}"


def test_exporter_enforces_bounded_run_id_and_emits_drilldown_freshness_metric() -> None:
    p = PROJECT_ROOT / "scripts" / "obs" / "ai_live_exporter.py"
    txt = p.read_text(encoding="utf-8")
    assert "_RUN_ID_MAX_LEN = 32" in txt
    assert "peaktrade_ai_last_event_timestamp_seconds_by_run_id" in txt
    assert "def _canon_run_id(" in txt, "expected run_id normalization helper"
