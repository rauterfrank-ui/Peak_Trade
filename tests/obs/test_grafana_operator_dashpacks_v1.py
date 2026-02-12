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

    # Datasource variable convention:
    # Canonical dashpack uses a single datasource variable `ds` (multi-Prom switching).
    want_vars = {
        "peaktrade-overview": {"ds"},
        "peaktrade-shadow-pipeline-mvs": {"ds"},
        "peaktrade-execution-watch-overview": {"ds"},
        "peaktrade-labeled-local": {"ds"},
    }
    allow_extra: set[str] = {"DS_LOCAL", "DS_MAIN", "DS_SHADOW"}
    for uid, p in uids.items():
        if uid not in want_vars:
            continue
        doc = _load_json(p)
        templ = (doc.get("templating") or {}).get("list") or []
        names = [
            t.get("name") for t in templ if isinstance(t, dict) and t.get("type") == "datasource"
        ]
        names = {n for n in names if isinstance(n, str)}
        need = want_vars[uid]
        assert need.issubset(names), f"{uid} missing {sorted(need - names)}"
        assert names.issubset(need | allow_extra), (
            f"{uid} unexpected vars {sorted(names - (need | allow_extra))}"
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

    def _has_uid(urls: set[str], uid: str) -> bool:
        # Allow both Grafana link shapes:
        # - /d/<uid>
        # - d/<uid>/<slug>
        return any(uid in u for u in urls)

    # Bidirectional operator nav: overview <-> shadow <-> execution
    # (HTTP dashboard may be more minimal; don't require full mesh).
    assert _has_uid(ov, "peaktrade-shadow-pipeline-mvs")
    assert _has_uid(ov, "peaktrade-execution-watch-overview")

    assert _has_uid(sh, "peaktrade-overview")
    assert _has_uid(sh, "peaktrade-execution-watch-overview")

    assert _has_uid(ex, "peaktrade-overview")
    assert _has_uid(ex, "peaktrade-shadow-pipeline-mvs")
    assert _has_uid(ht, "peaktrade-execution-watch-overview")
