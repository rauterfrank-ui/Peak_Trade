import pytest

# Patched: skip cleanly if optional dependency is not installed
pytest.importorskip("yaml")
import json
from pathlib import Path
from typing import Any, Iterator

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_json(p: Path) -> dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _iter_expr_strings(doc: Any) -> Iterator[str]:
    stack = [doc]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                if k == "expr" and isinstance(v, str):
                    yield v
                else:
                    stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)


def test_ai_live_ops_pack_v1_rules_yaml_parses_and_contains_required_alerts() -> None:
    rules_p = (
        PROJECT_ROOT
        / "docs"
        / "webui"
        / "observability"
        / "prometheus"
        / "rules"
        / "ai_live_alerts_v1.yml"
    )
    assert rules_p.is_file(), f"missing rules file: {rules_p}"

    doc = yaml.safe_load(rules_p.read_text(encoding="utf-8"))
    assert isinstance(doc, dict)
    groups = doc.get("groups")
    assert isinstance(groups, list) and groups, "expected at least one rule group"

    alerts: set[str] = set()
    for g in groups:
        if not isinstance(g, dict):
            continue
        rules = g.get("rules") or []
        if not isinstance(rules, list):
            continue
        for r in rules:
            if isinstance(r, dict) and isinstance(r.get("alert"), str):
                alerts.add(r["alert"])

    required = {
        "AI_LIVE_ExporterDown",
        "AI_LIVE_StaleEvents",
        "AI_LIVE_ParseErrorsSpike",
        "AI_LIVE_DroppedEventsSpike",
        "AI_LIVE_LatencyP95High",
        "AI_LIVE_LatencyP99High",
    }
    assert required.issubset(alerts), f"missing alerts: {sorted(required - alerts)}"


def test_execution_watch_overview_has_ai_live_ops_summary_and_alerts_query() -> None:
    dash_p = (
        PROJECT_ROOT
        / "docs"
        / "webui"
        / "observability"
        / "grafana"
        / "dashboards"
        / "execution"
        / "peaktrade-execution-watch-overview.json"
    )
    doc = _load_json(dash_p)

    panels = doc.get("panels") or []
    assert isinstance(panels, list) and panels

    has_ops_row = any(
        isinstance(p, dict) and p.get("type") == "row" and p.get("title") == "AI Live — Ops Summary"
        for p in panels
    )
    assert has_ops_row, "missing row panel title 'AI Live — Ops Summary'"

    exprs = list(_iter_expr_strings(doc))
    assert any("ALERTS" in e for e in exprs), "expected at least one ALERTS query in dashboard"
