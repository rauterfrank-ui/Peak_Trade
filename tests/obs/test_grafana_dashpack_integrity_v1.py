import json
import re
from pathlib import Path
from typing import Any, Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_json(p: Path) -> dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


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


def test_dashpack_uids_unique_and_link_targets_resolve() -> None:
    dashboards_dir = PROJECT_ROOT / "docs" / "webui" / "observability" / "grafana" / "dashboards"
    json_files = sorted(dashboards_dir.glob("*/*.json"))
    assert json_files, "expected at least one dashboard JSON"

    uids: dict[str, Path] = {}
    docs: list[tuple[Path, dict[str, Any]]] = []
    for p in json_files:
        doc = _load_json(p)
        uid = doc.get("uid")
        title = doc.get("title")
        assert isinstance(uid, str) and uid
        assert isinstance(title, str) and title
        assert uid not in uids, f"duplicate uid={uid} in {uids[uid]} and {p}"
        uids[uid] = p
        docs.append((p, doc))

    # Links accept:
    # - /d/<uid>
    # - /d/<uid>/<slug>
    # - /d/<uid>?var-x=y
    uid_re = re.compile(r"^/d/([^/?]+)(?:/[^?]+)?(?:\\?.*)?$")
    missing: list[str] = []
    for p, doc in docs:
        for url in _iter_url_strings(doc):
            m = uid_re.match(url)
            if not m:
                continue
            target = m.group(1)
            if target not in uids:
                missing.append(f"{p} links to missing uid={target} via url={url!r}")

    assert missing == [], "unresolved /d/<uid> links:\n" + "\n".join(missing)


def test_dashpack_ds_vars_hidden_and_defaults_stable() -> None:
    dashboards_dir = PROJECT_ROOT / "docs" / "webui" / "observability" / "grafana" / "dashboards"
    json_files = sorted(dashboards_dir.glob("*/*.json"))
    assert json_files, "expected at least one dashboard JSON"

    # Canonical dashpack datasource var (single selector).
    need = {"ds"}

    for p in json_files:
        doc = _load_json(p)
        templ = (doc.get("templating") or {}).get("list") or []
        ds_items = [t for t in templ if isinstance(t, dict) and t.get("type") == "datasource"]
        by_name = {t.get("name"): t for t in ds_items if isinstance(t.get("name"), str)}
        have = set(by_name.keys())
        assert need.issubset(have), f"{p} missing {sorted(need - have)}"
        t = by_name["ds"]
        # ds selector should be visible so operators can switch stacks.
        assert t.get("hide") == 0, f"{p} var ds should be visible (hide=0)"
        cur = t.get("current") or {}
        assert isinstance(cur, dict)
        # Contract: default to local Prometheus for deterministic local UX.
        # Unified operator dashboard defaults to AI Live datasource.
        expected_ds = (
            "prom_ai_live_9094"
            if p.name == "peaktrade-operator-unified.json"
            else "prom_local_9092"
        )
        assert cur.get("value") == expected_ds, f"{p} var ds default mismatch"


def test_operator_home_links_to_compare_overview() -> None:
    dashboards_dir = PROJECT_ROOT / "docs" / "webui" / "observability" / "grafana" / "dashboards"
    operator_home = _load_json(dashboards_dir / "overview" / "peaktrade-operator-home.json")

    urls = set(_iter_url_strings(operator_home))
    assert "/d/peaktrade-main-vs-shadow-overview" in urls
