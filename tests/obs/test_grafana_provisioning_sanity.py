import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _load_json(p: Path) -> dict:
    return json.loads(_read_text(p))


def _iter_url_strings(doc: object):
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


def test_dashboards_provider_folders_from_files_structure_enabled() -> None:
    p = (
        PROJECT_ROOT
        / "docs"
        / "webui"
        / "observability"
        / "grafana"
        / "provisioning"
        / "dashboards"
        / "dashboards.yaml"
    )
    txt = _read_text(p)
    assert "foldersFromFilesStructure: true" in txt
    assert "path: /etc/grafana/dashboards" in txt


def test_dashboards_folder_layout_no_root_jsons() -> None:
    dashboards_dir = PROJECT_ROOT / "docs" / "webui" / "observability" / "grafana" / "dashboards"
    assert dashboards_dir.is_dir()
    root_jsons = sorted(dashboards_dir.glob("*.json"))
    assert root_jsons == []

    for folder in ("overview", "shadow", "execution", "http", "compare"):
        assert (dashboards_dir / folder).is_dir()


def test_dashboard_uids_unique_and_required_vars_present() -> None:
    dashboards_dir = PROJECT_ROOT / "docs" / "webui" / "observability" / "grafana" / "dashboards"
    json_files = sorted(dashboards_dir.glob("*/*.json"))
    assert json_files, "expected at least one dashboard JSON"

    uids: dict[str, Path] = {}
    for p in json_files:
        doc = _load_json(p)
        uid = doc.get("uid")
        title = doc.get("title")
        assert isinstance(uid, str) and uid
        assert isinstance(title, str) and title
        assert uid not in uids, f"duplicate uid={uid} in {uids[uid]} and {p}"
        uids[uid] = p

    # Variable conventions: all dashboards carry the same canonical datasource var (`ds`)
    # so navigation can include vars and panels can scope correctly.
    expected = {"ds"}

    for p in json_files:
        doc = _load_json(p)
        templ = (doc.get("templating") or {}).get("list") or []
        ds_items = [t for t in templ if isinstance(t, dict) and t.get("type") == "datasource"]
        by_name = {t.get("name"): t for t in ds_items if isinstance(t.get("name"), str)}
        ds_vars = set(by_name.keys())
        assert expected.issubset(ds_vars), f"{p} missing {sorted(expected - ds_vars)}"
        t = by_name["ds"]
        assert t.get("hide") == 0, f"{p} var ds should be visible (hide=0)"
        cur = t.get("current") or {}
        assert isinstance(cur, dict)
        expected_ds = "prom_ai_live_9094" if p.name == "peaktrade-operator-unified.json" else "prom_local_9092"
        assert cur.get("value") == expected_ds, f"{p} var ds default mismatch"


def test_all_internal_dashboard_links_resolve_to_known_uids() -> None:
    dashboards_dir = PROJECT_ROOT / "docs" / "webui" / "observability" / "grafana" / "dashboards"
    json_files = sorted(dashboards_dir.glob("*/*.json"))
    assert json_files, "expected at least one dashboard JSON"

    uids: set[str] = set()
    docs: list[tuple[Path, dict]] = []
    for p in json_files:
        doc = _load_json(p)
        uid = doc.get("uid")
        assert isinstance(uid, str) and uid
        uids.add(uid)
        docs.append((p, doc))

    uid_re = re.compile(r"^/d/([^/?]+)(?:/[^?]+)?(?:\\?.*)?$")
    missing: list[str] = []
    for p, doc in docs:
        for url in _iter_url_strings(doc):
            m = uid_re.match(url)
            if not m:
                continue
            target_uid = m.group(1)
            if target_uid not in uids:
                missing.append(f"{p} links to missing uid={target_uid} via url={url!r}")

    assert missing == [], "unresolved /d/<uid> links:\n" + "\n".join(missing)


def test_drilldown_links_present_between_core_dashboards() -> None:
    dashboards_dir = PROJECT_ROOT / "docs" / "webui" / "observability" / "grafana" / "dashboards"
    # Core dashboards we expect to interlink (via uid-based /d/<uid> urls).
    overview = _load_json(dashboards_dir / "overview" / "peaktrade-overview.json")
    shadow = _load_json(dashboards_dir / "shadow" / "peaktrade-shadow-pipeline-mvs.json")
    execution = _load_json(dashboards_dir / "execution" / "peaktrade-execution-watch-overview.json")

    def _link_urls(d: dict) -> set[str]:
        links = d.get("links") or []
        urls = set()
        for it in links:
            if isinstance(it, dict) and isinstance(it.get("url"), str):
                urls.add(it["url"])
        return urls

    ov_urls = _link_urls(overview)
    sh_urls = _link_urls(shadow)
    ex_urls = _link_urls(execution)

    assert "/d/peaktrade-shadow-pipeline-mvs" in ov_urls
    assert "/d/peaktrade-execution-watch-overview" in ov_urls

    assert "/d/peaktrade-overview" in sh_urls
    assert "/d/peaktrade-execution-watch-overview" in sh_urls

    assert "/d/peaktrade-shadow-pipeline-mvs" in ex_urls
    assert "/d/peaktrade-overview" in ex_urls
