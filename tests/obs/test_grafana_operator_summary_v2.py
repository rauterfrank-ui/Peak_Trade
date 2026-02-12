import json
import re
from pathlib import Path
from typing import Any, Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _load_json(p: Path) -> dict[str, Any]:
    return json.loads(_read_text(p))


def _iter_url_strings(doc: Any) -> Iterator[str]:
    stack = [doc]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                if k == "url" and isinstance(v, str):
                    yield v
                else:
                    stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)


def test_operator_summary_dashboard_v2_contract() -> None:
    p = (
        PROJECT_ROOT
        / "docs"
        / "webui"
        / "observability"
        / "grafana"
        / "dashboards"
        / "overview"
        / "peaktrade-operator-summary.json"
    )
    assert p.exists(), f"missing dashboard JSON: {p}"

    doc = _load_json(p)
    assert doc.get("uid") == "peaktrade-operator-summary"
    assert doc.get("title") == "PeakTrade Operator Summary"

    tags = doc.get("tags") or []
    assert isinstance(tags, list)
    tagset = {t for t in tags if isinstance(t, str)}
    assert {"operator", "summary", "watch-only"}.issubset(tagset)

    templ = (doc.get("templating") or {}).get("list") or []
    assert isinstance(templ, list)
    ds_vars = {
        t.get("name")
        for t in templ
        if isinstance(t, dict) and t.get("type") == "datasource" and isinstance(t.get("name"), str)
    }
    assert {"ds"}.issubset(ds_vars)

    # Links accept /d/<uid> and /d/<uid>/<slug>
    uid_re = re.compile(r"^/d/([^/]+)(?:/[^/]+)?$")
    linked_uids: set[str] = set()
    for url in _iter_url_strings(doc):
        m = uid_re.match(url)
        if m:
            linked_uids.add(m.group(1))

    required = {
        "peaktrade-overview",
        "peaktrade-system-health",
        "peaktrade-execution-watch-overview",
        "peaktrade-labeled-local",
        "peaktrade-shadow-pipeline-mvs",
    }
    assert required.issubset(linked_uids), f"missing linked uids: {sorted(required - linked_uids)}"
