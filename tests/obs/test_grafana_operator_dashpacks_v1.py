import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _load_json(p: Path) -> dict:
    return json.loads(_read_text(p))


def test_dashboards_provider_foldered_filestructure_enabled() -> None:
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


def test_no_root_dashboard_json_files() -> None:
    dashboards_dir = PROJECT_ROOT / "docs" / "webui" / "observability" / "grafana" / "dashboards"
    assert dashboards_dir.is_dir()
    assert sorted(dashboards_dir.glob("*.json")) == []


def test_dashboard_uids_unique_and_vars_present() -> None:
    dashboards_dir = PROJECT_ROOT / "docs" / "webui" / "observability" / "grafana" / "dashboards"
    json_files = sorted(dashboards_dir.glob("*/*.json"))
    assert json_files, "expected dashboard JSON files under pack folders"

    uids: dict[str, Path] = {}
    for p in json_files:
        doc = _load_json(p)
        uid = doc.get("uid")
        assert isinstance(uid, str) and uid
        assert uid not in uids, f"duplicate uid={uid} in {uids[uid]} and {p}"
        uids[uid] = p

    # Ensure the core operator dashboards exist
    for uid in (
        "peaktrade-overview",
        "peaktrade-shadow-pipeline-mvs",
        "peaktrade-execution-watch-overview",
        "peaktrade-labeled-local",
    ):
        assert uid in uids, f"missing dashboard uid={uid}"

    # Datasource variable conventions by dashboard uid
    want_vars = {
        "peaktrade-overview": {"DS_LOCAL", "DS_MAIN"},
        "peaktrade-shadow-pipeline-mvs": {"DS_SHADOW"},
        "peaktrade-execution-watch-overview": {"DS_LOCAL", "DS_MAIN", "DS_SHADOW"},
        "peaktrade-labeled-local": {"DS_LOCAL"},
    }
    for uid, p in uids.items():
        if uid not in want_vars:
            continue
        doc = _load_json(p)
        templ = (doc.get("templating") or {}).get("list") or []
        names = [
            t.get("name") for t in templ if isinstance(t, dict) and t.get("type") == "datasource"
        ]
        names = {n for n in names if isinstance(n, str)}
        assert names == want_vars[uid], (
            f"{uid} expected {sorted(want_vars[uid])} got {sorted(names)}"
        )


def test_cross_links_between_dashboards_present() -> None:
    dashboards_dir = PROJECT_ROOT / "docs" / "webui" / "observability" / "grafana" / "dashboards"
    overview = _load_json(dashboards_dir / "overview" / "peaktrade-overview.json")
    shadow = _load_json(dashboards_dir / "shadow" / "peaktrade-shadow-pipeline-mvs.json")
    execution = _load_json(dashboards_dir / "execution" / "peaktrade-execution-watch-overview.json")
    http = _load_json(dashboards_dir / "http" / "peaktrade-labeled-local.json")

    def _urls(doc: dict) -> set[str]:
        links = doc.get("links") or []
        out: set[str] = set()
        for it in links:
            if isinstance(it, dict) and isinstance(it.get("url"), str):
                out.add(it["url"])
        return out

    ov = _urls(overview)
    sh = _urls(shadow)
    ex = _urls(execution)
    ht = _urls(http)

    # Bidirectional operator nav: overview <-> shadow <-> execution <-> http (with extra edges OK)
    assert "/d/peaktrade-shadow-pipeline-mvs" in ov
    assert "/d/peaktrade-execution-watch-overview" in ov
    assert "/d/peaktrade-labeled-local" in ov

    assert "/d/peaktrade-overview" in sh
    assert "/d/peaktrade-execution-watch-overview" in sh
    assert "/d/peaktrade-labeled-local" in sh

    assert "/d/peaktrade-overview" in ex
    assert "/d/peaktrade-shadow-pipeline-mvs" in ex
    assert "/d/peaktrade-labeled-local" in ex

    assert "/d/peaktrade-overview" in ht
    assert "/d/peaktrade-shadow-pipeline-mvs" in ht
    assert "/d/peaktrade-execution-watch-overview" in ht
