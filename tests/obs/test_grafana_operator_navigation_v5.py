import json
import re
from pathlib import Path
from typing import Any, Iterator, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _load_json(p: Path) -> dict[str, Any]:
    return json.loads(_read_text(p))


def _iter_dicts(doc: Any) -> Iterator[dict[str, Any]]:
    stack: list[Any] = [doc]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            yield cur
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)


def _iter_url_strings(doc: Any) -> Iterator[str]:
    for d in _iter_dicts(doc):
        v = d.get("url")
        if isinstance(v, str):
            yield v


def _datasource_uid(panel: dict[str, Any]) -> Optional[str]:
    ds = panel.get("datasource")
    if isinstance(ds, dict) and isinstance(ds.get("uid"), str):
        return ds["uid"]
    return None


def test_operator_home_exists_and_links_to_core_dashboards() -> None:
    dashboards_dir = PROJECT_ROOT / "docs" / "webui" / "observability" / "grafana" / "dashboards"
    p = dashboards_dir / "overview" / "peaktrade-operator-home.json"
    assert p.exists(), f"missing dashboard JSON: {p}"

    doc = _load_json(p)
    assert doc.get("uid") == "peaktrade-operator-home"

    # Links accept /d/<uid> and /d/<uid>/<slug>
    uid_re = re.compile(r"^/d/([^/]+)(?:/[^/]+)?$")
    linked_uids: set[str] = set()
    for url in _iter_url_strings(doc):
        m = uid_re.match(url)
        if m:
            linked_uids.add(m.group(1))

    required = {
        "peaktrade-operator-summary",
        "peaktrade-system-health",
        "peaktrade-execution-watch-overview",
        "peaktrade-shadow-pipeline-mvs",
        "peaktrade-contract-details",
    }
    assert required.issubset(linked_uids), f"missing linked uids: {sorted(required - linked_uids)}"


def test_required_drilldown_dashboards_exist() -> None:
    dashboards_dir = PROJECT_ROOT / "docs" / "webui" / "observability" / "grafana" / "dashboards"
    required_paths = [
        dashboards_dir / "overview" / "peaktrade-contract-details.json",
        dashboards_dir / "execution" / "peaktrade-execution-watch-details.json",
    ]
    for p in required_paths:
        assert p.exists(), f"missing dashboard JSON: {p}"


def test_execution_watch_contract_panel_scoped_to_local_ds() -> None:
    dashboards_dir = PROJECT_ROOT / "docs" / "webui" / "observability" / "grafana" / "dashboards"
    doc = _load_json(dashboards_dir / "execution" / "peaktrade-execution-watch-overview.json")

    # Find the contract panel by title and ensure datasource is DS_LOCAL (guardrail).
    for panel in doc.get("panels") or []:
        if (
            isinstance(panel, dict)
            and panel.get("title") == "Contract: execution watch metrics present"
        ):
            allowed = {"${DS_LOCAL}", "peaktrade-prometheus-local"}
            ds_value = _datasource_uid(panel)
            assert ds_value in allowed
            return

    raise AssertionError("missing panel: Contract: execution watch metrics present")
