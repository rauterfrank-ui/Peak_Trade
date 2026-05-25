"""Contract tests for Registry v1 taxonomy §6a field population v0."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_SCRIPT = ROOT / "scripts" / "ops" / "build_generic_evidence_run_registry_v1.py"
TAXONOMY_SPEC = (
    ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)

SECTION_6A_FIELDS = (
    "runtime_host",
    "runtime_backend",
    "runtime_mode",
    "evidence_root_type",
    "evidence_transport",
    "notion_projection",
    "market_dashboard_projection",
    "live_authority",
    "testnet_authority",
)

RUN_ID = "daemon_paper_24h_fixture_6a_v0"


def _load_registry():
    spec = importlib.util.spec_from_file_location(
        "build_generic_evidence_run_registry_v1_section_6a",
        REGISTRY_SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_lane_manifest(run_dir: Path) -> None:
    entries: list[str] = []
    for path in sorted(run_dir.rglob("*")):
        if not path.is_file() or path.name == "MANIFEST.sha256":
            continue
        rel = path.relative_to(run_dir).as_posix()
        entries.append(f"{_sha256_file(path)}  {rel}")
    (run_dir / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


def _write_lane(archive: Path, lane: str, run_id: str, *, review: str | None = None) -> Path:
    run_dir = archive / "runs" / lane / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "evidence.txt").write_text(f"{lane}:{run_id}\n", encoding="utf-8")
    if review is not None:
        review_dir = run_dir / "review"
        review_dir.mkdir(parents=True, exist_ok=True)
        (review_dir / "REVIEW_RESULT.json").write_text(
            json.dumps({"verdict": review, "issues": []}) + "\n",
            encoding="utf-8",
        )
    _write_lane_manifest(run_dir)
    return run_dir


def _write_composition(archive: Path, run_id: str) -> Path:
    comp_dir = archive / "runs" / "daemon_paper_24h" / run_id
    comp_dir.mkdir(parents=True, exist_ok=True)
    (comp_dir / "COMPOSITION_INDEX.md").write_text(
        "composition_index_authority=false\n", encoding="utf-8"
    )
    manifests = comp_dir / "manifests"
    manifests.mkdir(parents=True, exist_ok=True)
    rel = "COMPOSITION_INDEX.md"
    digest = _sha256_file(comp_dir / rel)
    (manifests / "MANIFEST.sha256").write_text(f"{digest}  {rel}\n", encoding="utf-8")
    return comp_dir


def _build(mod, archive: Path) -> dict:
    return mod.build_registry(mod.BuildContext(archive_root=archive, repo_root=ROOT))


@pytest.fixture
def mod():
    return _load_registry()


def test_registry_module_exposes_section_6a_population_marker() -> None:
    mod = _load_registry()
    assert mod.REGISTRY_V1_SECTION_6A_FIELDS_POPULATED is True
    assert mod.SCHEMA == "peak_trade.generic_evidence_run_registry.v1"


def test_taxonomy_documents_section_6a_population() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "REGISTRY_V1_SECTION_6A_FIELDS_POPULATED=true" in text
    assert "non-authorizing metadata defaults" in text


def test_runs_include_all_section_6a_fields(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    _write_lane(archive, "paper", "paper_run")
    _write_lane(archive, "shadow", "shadow_run", review="PASS")
    payload = _build(mod, archive)
    for run in payload["runs"]:
        for field in SECTION_6A_FIELDS:
            assert field in run
        assert run["live_authority"] is False
        assert run["testnet_authority"] is False
        assert run["notion_projection"] == "disabled"
        assert run["market_dashboard_projection"] == "disabled"
        assert run["evidence_transport"] == "local_only"


def test_paper_lane_runtime_mode_paper_only(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    _write_lane(archive, "paper", "paper_run")
    paper = _build(mod, archive)["runs"][0]
    assert paper["lane_id"] == "paper"
    assert paper["runtime_mode"] == "paper_only"
    assert paper["runtime_host"] == "local"
    assert paper["runtime_backend"] == "laptop"


def test_shadow_lane_uses_safe_section_6a_default(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    _write_lane(archive, "shadow", "shadow_run", review="PASS")
    shadow = _build(mod, archive)["runs"][0]
    assert shadow["lane_id"] == "shadow"
    assert shadow["runtime_mode"] == "paper_only"
    assert shadow["live_authority"] is False


def test_composition_includes_section_6a_fields(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    _write_lane(archive, "paper", RUN_ID)
    _write_lane(archive, "shadow", RUN_ID, review="PASS")
    _write_composition(archive, RUN_ID)
    payload = _build(mod, archive)
    assert len(payload["compositions"]) == 1
    comp = payload["compositions"][0]
    for field in SECTION_6A_FIELDS:
        assert field in comp
    assert comp["runtime_mode"] == "paper_then_shadow"
    assert comp["composition_index_authority"] is False
    assert comp["notion_projection"] == "disabled"
    assert comp["market_dashboard_projection"] == "disabled"


def test_no_registry_v2_or_new_lane_ids(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    _write_lane(archive, "paper", RUN_ID)
    _write_composition(archive, RUN_ID)
    payload = _build(mod, archive)
    assert payload["schema"] == "peak_trade.generic_evidence_run_registry.v1"
    assert "generic_evidence_run_registry.v2" not in json.dumps(payload)
    lane_ids = {r["lane_id"] for r in payload["runs"]}
    assert "daemon_paper_24h" not in lane_ids
    assert "remote_runtime" not in lane_ids


def test_manifest_hash_mismatch_still_fail_closed(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    run_dir = _write_lane(archive, "paper", "paper_run")
    (run_dir / "MANIFEST.sha256").write_text("deadbeef  evidence.txt\n", encoding="utf-8")
    payload = _build(mod, archive)
    assert payload["verdict"] == mod.VERDICT_FAIL_CLOSED
    paper = payload["runs"][0]
    for field in SECTION_6A_FIELDS:
        assert field in paper
    assert any(i["code"] == "MANIFEST_HASH_MISMATCH" for i in payload["issues"])
