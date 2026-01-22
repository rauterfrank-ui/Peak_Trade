import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _load_json(p: Path) -> dict:
    return json.loads(_read_text(p))


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

    for folder in ("overview", "shadow", "execution", "http"):
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

    # Variable conventions by pack (directory)
    expected = {
        "execution": {"DS_LOCAL", "DS_MAIN", "DS_SHADOW"},
        "overview": {"DS_LOCAL", "DS_MAIN"},
        "shadow": {"DS_SHADOW"},
        "http": {"DS_LOCAL"},
    }
    # Some dashboards may include extra datasource selector vars (e.g. a unified DS_PROM).
    allow_common_extra = {"DS_PROM"}
    # Some overview dashboards include DS_SHADOW too; allow superset.
    allow_overview_extra = {"DS_SHADOW"} | allow_common_extra

    for p in json_files:
        pack = p.parent.name
        doc = _load_json(p)
        templ = (doc.get("templating") or {}).get("list") or []
        ds_vars = [
            t.get("name") for t in templ if isinstance(t, dict) and t.get("type") == "datasource"
        ]
        ds_vars = {v for v in ds_vars if isinstance(v, str)}
        need = expected.get(pack)
        assert need is not None, f"unexpected pack folder: {pack}"
        if pack == "overview":
            assert need.issubset(ds_vars), f"{p} missing {sorted(need - ds_vars)}"
            assert ds_vars.issubset(need | allow_overview_extra), (
                f"{p} unexpected vars {sorted(ds_vars - (need | allow_overview_extra))}"
            )
        else:
            assert need.issubset(ds_vars), f"{p} missing {sorted(need - ds_vars)}"
            assert ds_vars.issubset(need | allow_common_extra), (
                f"{p} unexpected vars {sorted(ds_vars - (need | allow_common_extra))}"
            )


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

    def _has_uid(urls: set[str], uid: str) -> bool:
        # Allow both Grafana link shapes:
        # - /d/<uid>
        # - d/<uid>/<slug>
        return any(uid in u for u in urls)

    assert _has_uid(ov_urls, "peaktrade-shadow-pipeline-mvs")
    assert _has_uid(ov_urls, "peaktrade-execution-watch-overview")

    assert _has_uid(sh_urls, "peaktrade-overview")
    assert _has_uid(sh_urls, "peaktrade-execution-watch-overview")

    assert _has_uid(ex_urls, "peaktrade-shadow-pipeline-mvs")
    assert _has_uid(ex_urls, "peaktrade-overview")
