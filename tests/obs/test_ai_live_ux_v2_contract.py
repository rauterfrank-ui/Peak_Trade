from __future__ import annotations

import json
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


def _panels_by_title(dash: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for p in dash.get("panels", []) or []:
        if isinstance(p, dict) and isinstance(p.get("title"), str):
            out[p["title"]] = p
    return out


def _panel_exprs(panel: dict[str, Any]) -> list[str]:
    exprs: list[str] = []
    for t in panel.get("targets", []) or []:
        if isinstance(t, dict) and isinstance(t.get("expr"), str) and t["expr"].strip():
            exprs.append(t["expr"])
    return exprs


def _all_exprs(dash: dict[str, Any]) -> list[str]:
    exprs: list[str] = []
    for p in dash.get("panels", []) or []:
        if not isinstance(p, dict):
            continue
        exprs.extend(_panel_exprs(p))
    return exprs


def test_dashboard_parses_and_uid_is_stable() -> None:
    dash = _load_dashboard()
    assert dash.get("uid") == "peaktrade-execution-watch-overview"


def test_run_id_variable_exists_and_uses_ds_local() -> None:
    dash = _load_dashboard()
    templ = (dash.get("templating") or {}).get("list") or []
    var = next((v for v in templ if (v.get("type"), v.get("name")) == ("query", "run_id")), None)
    assert var is not None, "expected dashboard variable run_id"
    allowed = {"${DS_LOCAL}", "peaktrade-prometheus-local"}
    ds_value = (var.get("datasource") or {}).get("uid")
    assert ds_value in allowed


def test_ai_live_ux_v2_required_panels_exist() -> None:
    dash = _load_dashboard()
    by_title = _panels_by_title(dash)
    required = {
        "Reject reasons (5m)",
        "Noop reasons (5m)",
        "Latency SLO > 500ms (5m) — breach %",
        "Latency breach % (>500ms) (5m)",
        "AI Activity State (per decision type, last 30m)",
    }
    missing = sorted(t for t in required if t not in by_title)
    assert not missing, f"missing required panel(s): {missing}"


def test_ai_live_ux_v2_promql_contracts_run_scoped_and_hardened() -> None:
    dash = _load_dashboard()
    by_title = _panels_by_title(dash)

    # Panels that must be run-scoped and hardened.
    must_scope = {
        "Reject reasons (5m)",
        "Noop reasons (5m)",
        "Latency SLO > 500ms (5m) — breach %",
        "Latency breach % (>500ms) (5m)",
        "AI Activity State (per decision type, last 30m)",
    }

    for title in must_scope:
        panel = by_title[title]
        exprs = _panel_exprs(panel)
        assert exprs, f"panel {title!r} has no Prometheus expr"
        for e in exprs:
            # run_id scoping contract (exceptions are handled in separate tests for ops-only panels)
            assert 'run_id=~"$run_id"' in e, f"missing run_id scope in {title!r}: {e!r}"

            # hardening contract: must not go empty on no-data
            assert "or on() vector(0)" in e or "label_replace(vector(0)" in e, (
                f"missing no-data hardening in {title!r}: {e!r}"
            )

            # safe divide heuristic
            if "/" in e:
                assert "clamp_min(" in e, f"divide without clamp_min guard in {title!r}: {e!r}"


def test_dashboard_has_no_promql_pipes_and_safe_divides() -> None:
    dash = _load_dashboard()
    exprs = _all_exprs(dash)

    assert not any("|" in e for e in exprs), "unexpected '|' in PromQL expr (pipes not supported)"

    for e in exprs:
        if "/" in e:
            assert "clamp_min(" in e, f"divide without clamp_min guard: {e!r}"
