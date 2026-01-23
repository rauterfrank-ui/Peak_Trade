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

    # Variable conventions: all dashboards carry the same DS_* set (even if some
    # packs only actively use one of them), so navigation/drilldowns can always
    # include vars and panels can scope correctly.
    expected = {"DS_LOCAL", "DS_MAIN", "DS_SHADOW"}

    for p in json_files:
        doc = _load_json(p)
        templ = (doc.get("templating") or {}).get("list") or []
        ds_vars = [
            t.get("name") for t in templ if isinstance(t, dict) and t.get("type") == "datasource"
        ]
        ds_vars = {v for v in ds_vars if isinstance(v, str)}
        assert expected.issubset(ds_vars), f"{p} missing {sorted(expected - ds_vars)}"


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
