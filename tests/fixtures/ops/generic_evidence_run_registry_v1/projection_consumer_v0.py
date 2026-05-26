"""Shared Registry v1 projection consumer smoke fixtures (test-only, non-authorizing).

Consumers: Notion §6a.1, Market Dashboard §6a.2, future S3 finalized-evidence export gate tests.
Does not define runtime authority, Registry v2, or new lanes.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

REGISTRY_V1_PROJECTION_CONSUMER_SMOKE_FIXTURES_V0 = True

REPO_ROOT = Path(__file__).resolve().parents[4]
TAXONOMY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
REGISTRY_SCRIPT = REPO_ROOT / "scripts" / "ops" / "build_generic_evidence_run_registry_v1.py"

POST_CLOSEOUT_PROJECTION_AUTOMATION_CHARTER_MARKERS: tuple[str, ...] = (
    "POST_CLOSEOUT_PROJECTION_AUTOMATION_V0=true",
    "NOTION_POST_CLOSEOUT_SYNC_V0=true",
    "MARKET_DASHBOARD_READONLY_RUN_PROJECTION_V0=true",
    "POST_CLOSEOUT_PROJECTION_AUTOMATION_ENABLED=false",
    "NOTION_POST_CLOSEOUT_SYNC_ENABLED=false",
    "MARKET_DASHBOARD_RUN_PROJECTION_ENABLED=false",
    "RUNTIME_CONTROL_FROM_PROJECTION=false",
    "DASHBOARD_RUNTIME_CONTROL=false",
    "BROKER_EXCHANGE_AUTHORITY=false",
    "PROJECTION_AFTER_CLOSEOUT_ONLY=true",
    "PROJECTION_AFTER_MANIFEST_VERIFY_ONLY=true",
    "REPO_AND_DURABLE_EVIDENCE_REMAIN_CANONICAL=true",
    "NOTION_IS_PROJECTION_ONLY=true",
    "MARKET_DASHBOARD_IS_PROJECTION_ONLY=true",
    "NO_PARALLEL_MARKET_SURFACE=true",
    "NO_PARALLEL_NOTION_DB=true",
    "NO_PARALLEL_READMODEL=true",
)


def taxonomy_section_6a08() -> str:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    return text.split(
        "### 6a.0.8 Post-Closeout Projection Automation Charter v0 (docs/tests-only)", 1
    )[1].split("### 6a.1 Notion post-closeout sync projection contract v0", 1)[0]

# Canonical pointer/status fields for Registry v1 projection consumers (§6a.1 + §6a.2 aligned).
ALLOWED_PROJECTION_FIELDS: tuple[str, ...] = (
    "run_id",
    "lane_id",
    "composition_id",
    "record_kind",
    "runtime_host",
    "runtime_backend",
    "runtime_mode",
    "evidence_root_type",
    "evidence_transport",
    "evidence_status",
    "review_verdict",
    "manifest_verified",
    "archive_path",
)

RUN_PROJECTION_FIELDS: tuple[str, ...] = (
    "run_id",
    "lane_id",
    "runtime_host",
    "runtime_backend",
    "runtime_mode",
    "evidence_root_type",
    "evidence_transport",
    "evidence_status",
    "review_verdict",
    "manifest_verified",
    "archive_path",
)

# Subset referenced by future S3 finalized-evidence export gate contract tests (no S3 impl here).
S3_RELEVANT_PROJECTION_FIELDS: tuple[str, ...] = (
    "evidence_transport",
    "manifest_verified",
    "archive_path",
    "evidence_status",
)

TOP_LEVEL_PROJECTION_SUMMARY_FIELDS: tuple[str, ...] = (
    "verdict",
    "issues",
    "blockers",
    "archive_root",
)

SECTION_6A_METADATA_FIELDS: tuple[str, ...] = (
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

DEFAULT_COMPOSITION_RUN_ID = "daemon_paper_24h_fixture_projection_v0"


def load_registry_module(
    *, module_name: str = "build_generic_evidence_run_registry_v1_projection_consumer"
):
    spec = importlib.util.spec_from_file_location(module_name, REGISTRY_SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_lane_manifest(run_dir: Path) -> None:
    entries: list[str] = []
    for path in sorted(run_dir.rglob("*")):
        if not path.is_file() or path.name == "MANIFEST.sha256":
            continue
        rel = path.relative_to(run_dir).as_posix()
        entries.append(f"{sha256_file(path)}  {rel}")
    (run_dir / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


def write_lane(
    archive: Path,
    lane: str,
    run_id: str,
    *,
    review: str | None = None,
) -> Path:
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
    write_lane_manifest(run_dir)
    return run_dir


def write_composition(archive: Path, run_id: str) -> Path:
    comp_dir = archive / "runs" / "daemon_paper_24h" / run_id
    comp_dir.mkdir(parents=True, exist_ok=True)
    (comp_dir / "COMPOSITION_INDEX.md").write_text(
        "composition_index_authority=false\n",
        encoding="utf-8",
    )
    manifests = comp_dir / "manifests"
    manifests.mkdir(parents=True, exist_ok=True)
    rel = "COMPOSITION_INDEX.md"
    digest = sha256_file(comp_dir / rel)
    (manifests / "MANIFEST.sha256").write_text(f"{digest}  {rel}\n", encoding="utf-8")
    return comp_dir


def write_minimal_paper_run(archive: Path, run_id: str = "paper_run") -> Path:
    """Minimal verified paper lane archive for projection consumer smoke tests."""
    return write_lane(archive, "paper", run_id)


def build_registry(archive: Path, *, repo_root: Path | None = None) -> dict[str, Any]:
    mod = load_registry_module()
    return mod.build_registry(
        mod.BuildContext(archive_root=archive, repo_root=repo_root or REPO_ROOT)
    )


def assert_non_authorizing_run_projection_defaults(run: dict[str, Any]) -> None:
    for field in RUN_PROJECTION_FIELDS:
        if field not in run:
            raise AssertionError(f"missing projection field {field!r} on runs[] row")
    if run.get("live_authority") is not False:
        raise AssertionError("live_authority must be false on projection consumer fixture runs")
    if run.get("testnet_authority") is not False:
        raise AssertionError("testnet_authority must be false on projection consumer fixture runs")
    if run.get("notion_projection") != "disabled":
        raise AssertionError("notion_projection must be disabled by default")
    if run.get("market_dashboard_projection") != "disabled":
        raise AssertionError("market_dashboard_projection must be disabled by default")
