"""Contract tests for combined OUTROOT composition-index v0 (Registry v1 + taxonomy §6b)."""

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
PREFLIGHT = ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
RUN_ID = "daemon_paper_24h_20260524T205447Z"

COMPOSITION_MARKERS = (
    "COMBINED_OUTROOT_COMPOSITION_INDEX_V0=true",
    "COMPOSITION_INDEX_IS_NOT_LANE=true",
    "LANE_ID_DAEMON_PAPER_24H_FORBIDDEN=true",
    "LANE_ID_REMOTE_RUNTIME_FORBIDDEN=true",
    "COMPOSITION_INDEX_AUTHORITY=false",
    "composition_index_authority=false",
    "PER_LANE_MANIFEST_SHA256_REMAINS_CANONICAL=true",
)


def _load_registry():
    spec = importlib.util.spec_from_file_location(
        "build_generic_evidence_run_registry_v1_composition",
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
        if not path.is_file():
            continue
        if path.name in {"MANIFEST.sha256", "MANIFEST_VERIFY.log"}:
            continue
        rel = path.relative_to(run_dir).as_posix()
        entries.append(f"{_sha256_file(path)}  {rel}")
    (run_dir / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


def _write_lane_run(
    archive: Path,
    lane: str,
    run_id: str,
    *,
    review_verdict: str | None = None,
    write_manifest: bool = True,
) -> Path:
    run_dir = archive / "runs" / lane / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "evidence.txt").write_text(f"{lane}:{run_id}\n", encoding="utf-8")
    if review_verdict is not None:
        review_dir = run_dir / "review"
        review_dir.mkdir(parents=True, exist_ok=True)
        (review_dir / "REVIEW_RESULT.json").write_text(
            json.dumps({"verdict": review_verdict, "issues": []}) + "\n",
            encoding="utf-8",
        )
    if write_manifest:
        _write_lane_manifest(run_dir)
    return run_dir


def _write_composition_rollup(comp_dir: Path, *, include_file: bool = True) -> None:
    if include_file:
        (comp_dir / "COMPOSITION_INDEX.md").write_text(
            "composition_index_authority=false\nlive_authority=false\n",
            encoding="utf-8",
        )
    manifests = comp_dir / "manifests"
    manifests.mkdir(parents=True, exist_ok=True)
    entries: list[str] = []
    for path in sorted(comp_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name == "MANIFEST.sha256" and path.parent.name == "manifests":
            continue
        rel = path.relative_to(comp_dir).as_posix()
        entries.append(f"{_sha256_file(path)}  {rel}")
    (manifests / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


def _write_combined_archive(
    archive: Path,
    run_id: str = RUN_ID,
    *,
    rollup: bool = True,
    paper_manifest: bool = True,
    shadow_manifest: bool = True,
    shadow_review: str = "PASS",
) -> Path:
    _write_lane_run(archive, "paper", run_id, write_manifest=paper_manifest)
    _write_lane_run(
        archive, "shadow", run_id, review_verdict=shadow_review, write_manifest=shadow_manifest
    )
    comp_dir = archive / "runs" / "daemon_paper_24h" / run_id
    comp_dir.mkdir(parents=True, exist_ok=True)
    if rollup:
        _write_composition_rollup(comp_dir)
    return comp_dir


def _build(mod, archive: Path) -> dict:
    return mod.build_registry(mod.BuildContext(archive_root=archive, repo_root=ROOT))


@pytest.fixture
def mod():
    return _load_registry()


def test_taxonomy_section_6b_markers_present() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "## 6b. Combined OUTROOT composition-index v0" in text
    for marker in COMPOSITION_MARKERS:
        assert marker in text
    assert "lane_id=daemon_paper_24h" in text
    assert "lane_id=remote_runtime" in text
    assert "manifests&#47;MANIFEST.sha256" in text


def test_preflight_cross_references_composition_index() -> None:
    section = PREFLIGHT.read_text(encoding="utf-8").split("## 2a.", 1)[1].split("## 2b.", 1)[0]
    assert "composition/index" in section.lower() or "compositions[]" in section
    assert "taxonomy §6b" in section or "§6b" in section


def test_registry_script_exposes_composition_constants() -> None:
    mod = _load_registry()
    assert mod.COMBINED_OUTROOT_COMPOSITION_INDEX_V0 is True
    assert "daemon_paper_24h" in mod.COMPOSITION_INDEX_DIRECTORIES
    assert "daemon_paper_24h" in mod.COMPOSITION_INDEX_FORBIDDEN_LANE_IDS
    assert mod.SCHEMA == "peak_trade.generic_evidence_run_registry.v1"


def test_combined_outroot_no_unknown_lane(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    _write_combined_archive(archive)
    payload = _build(mod, archive)
    codes = {i["code"] for i in payload["issues"]}
    assert "UNKNOWN_LANE" not in codes
    lane_ids = {r["lane_id"] for r in payload["runs"]}
    assert "daemon_paper_24h" not in lane_ids
    assert lane_ids <= {"paper", "shadow"}


def test_composition_record_emitted(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    _write_combined_archive(archive)
    payload = _build(mod, archive)
    assert payload["schema"] == "peak_trade.generic_evidence_run_registry.v1"
    assert payload["summaries"]["total_compositions"] == 1
    assert len(payload["compositions"]) == 1
    comp = payload["compositions"][0]
    assert comp["record_kind"] == "composition_index"
    assert comp["composition_id"] == "daemon_paper_24h"
    assert comp["run_id"] == RUN_ID
    assert comp["runtime_mode"] == "paper_then_shadow"
    assert comp["rollup_manifest_present"] is True
    assert comp["rollup_manifest_path"] == "manifests/MANIFEST.sha256"
    assert comp["rollup_manifest_verified"] is True


def test_composition_record_non_authorizing(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    _write_combined_archive(archive)
    comp = _build(mod, archive)["compositions"][0]
    assert comp["composition_index_authority"] is False
    assert comp["live_authority"] is False
    assert comp["testnet_authority"] is False
    assert comp["s3_authority"] is False
    assert comp["notion_authority"] is False
    assert comp["market_dashboard_authority"] is False
    assert comp["can_authorize_live"] is False


def test_rollup_manifest_at_manifests_path_only(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    comp_dir = _write_combined_archive(archive, rollup=True)
    payload = _build(mod, archive)
    codes = {i["code"] for i in payload["issues"]}
    assert "MISSING_MANIFEST" not in codes or all(
        "daemon_paper_24h" not in i.get("path", "") or "manifests" in i.get("path", "")
        for i in payload["issues"]
        if i["code"] == "MISSING_MANIFEST"
    )
    comp = payload["compositions"][0]
    assert comp["rollup_manifest_verified"] is True
    assert not (comp_dir / "MANIFEST.sha256").exists()


def test_root_manifest_on_composition_review_required(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    comp_dir = _write_combined_archive(archive)
    (comp_dir / "MANIFEST.sha256").write_text("deadbeef  COMPOSITION_INDEX.md\n", encoding="utf-8")
    payload = _build(mod, archive)
    codes = {i["code"] for i in payload["issues"]}
    assert "COMPOSITION_ROOT_MANIFEST_NOT_PRIMARY" in codes


def test_missing_child_lane_manifest_not_masked(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    _write_combined_archive(archive, paper_manifest=False, shadow_manifest=True)
    payload = _build(mod, archive)
    codes = {i["code"] for i in payload["issues"]}
    assert "MISSING_MANIFEST" in codes
    paper = next(r for r in payload["runs"] if r["lane_id"] == "paper")
    assert paper["manifest_present"] is False
    assert paper["evidence_status"] == "incomplete"
    comp = payload["compositions"][0]
    assert comp["evidence_status"] in ("partial", "incomplete", "indexed")
    paper_child = next(c for c in comp["child_lane_status"] if c["lane_id"] == "paper")
    assert paper_child["evidence_status"] == "incomplete"


def test_missing_rollup_manifest_review_required_not_unknown_lane(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    _write_combined_archive(archive, rollup=False)
    payload = _build(mod, archive)
    codes = {i["code"] for i in payload["issues"]}
    assert "UNKNOWN_LANE" not in codes
    assert "MISSING_COMPOSITION_ROLLUP_MANIFEST" in codes
    assert payload["compositions"][0]["rollup_manifest_present"] is False


def test_lane_catalog_unchanged_no_daemon_paper_lane(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    _write_combined_archive(archive)
    payload = _build(mod, archive)
    catalog_lane_ids = {entry["lane_id"] for entry in payload["lanes"]}
    assert "daemon_paper_24h" not in catalog_lane_ids
    assert "remote_runtime" not in catalog_lane_ids


def test_backward_compatible_runs_array(mod, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    _write_combined_archive(archive)
    payload = _build(mod, archive)
    assert payload["summaries"]["total_runs"] == 2
    for run in payload["runs"]:
        assert run["lane_id"] in {"paper", "shadow"}
        assert "record_kind" not in run
