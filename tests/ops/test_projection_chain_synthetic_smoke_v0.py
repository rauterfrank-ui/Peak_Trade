"""Synthetic post-closeout projection chain smoke (tmp_path only, non-authorizing).

Chains: closeout + registry fixtures -> payload builder -> market display context -> Notion dry-run report.
Does not start runtime, MCP, Notion API, or dashboard servers.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from src.webui.market_surface import (
    MARKET_RUN_PROJECTION_ENABLED_ENV,
    MARKET_RUN_PROJECTION_PAYLOAD_JSON_ENV,
    build_market_run_projection_display_context,
)
from tests.fixtures.ops.generic_evidence_run_registry_v1 import projection_consumer_v0 as pc
from tests.ops import test_build_post_closeout_projection_payload_v0 as payload_tests

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILDER_SCRIPT = REPO_ROOT / "scripts/ops/build_post_closeout_projection_payload_v0.py"
DRY_RUN_SCRIPT = REPO_ROOT / "scripts/ops/notion_post_closeout_sync_dry_run_v0.py"

PAYLOAD_SCHEMA = "peak_trade.post_closeout_projection_payload.v0"
REPORT_SCHEMA = "peak_trade.notion_post_closeout_sync_dry_run_report.v0"

FORBIDDEN_LEAK_SUBSTRINGS = ("/Users/", "source_files", "AKIA", "sk-", "Bearer ")


def _load_module(script: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_chain_fixtures(
    work: Path,
    *,
    with_valid_manifest: bool = True,
    manifest_valid: bool = True,
    verify_log_ok: bool = True,
    machine_line_overrides: dict[str, str] | None = None,
    registry_live_authority: bool = False,
) -> tuple[Path, Path]:
    """Return (closeout_root, registry_path)."""
    registry_path = work / "registry.json"
    payload_tests._write_registry(registry_path, work, live=registry_live_authority)
    closeout_root = work / "closeout"
    payload_tests._write_closeout_bundle(
        closeout_root,
        with_manifest=with_valid_manifest,
        manifest_valid=manifest_valid,
        verify_log_ok=verify_log_ok,
        machine_line_overrides=machine_line_overrides,
    )
    return closeout_root, registry_path


def _run_payload_builder(builder, closeout: Path, registry: Path, out: Path) -> int:
    return payload_tests._run_cli(builder, closeout, registry, out)


def _run_notion_dry_run(
    dry_run,
    payload: Path,
    report: Path,
    *,
    boundary_verified: bool = True,
) -> int:
    argv = [
        "--projection-payload-json",
        str(payload),
        "--target-name",
        "Evidence & Closeouts",
        "--output-report-json",
        str(report),
    ]
    if boundary_verified:
        argv.append("--boundary-text-verified")
    return dry_run.main(argv)


def _market_context(monkeypatch: pytest.MonkeyPatch, payload_path: Path) -> dict[str, Any]:
    monkeypatch.setenv(MARKET_RUN_PROJECTION_ENABLED_ENV, "1")
    monkeypatch.setenv(MARKET_RUN_PROJECTION_PAYLOAD_JSON_ENV, str(payload_path))
    return build_market_run_projection_display_context()


def _assert_no_leaks(blob: str) -> None:
    for forbidden in FORBIDDEN_LEAK_SUBSTRINGS:
        assert forbidden not in blob


@pytest.fixture(scope="module")
def builder():
    return _load_module(BUILDER_SCRIPT, "build_post_closeout_projection_payload_v0_chain")


@pytest.fixture(scope="module")
def dry_run():
    return _load_module(DRY_RUN_SCRIPT, "notion_post_closeout_sync_dry_run_v0_chain")


def test_happy_path_chain_smoke(builder, dry_run, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    work = tmp_path / "chain_happy"
    closeout, registry = _write_chain_fixtures(work)
    payload_path = work / "out" / "payload.json"
    report_path = work / "out" / "notion_report.json"

    digests = {
        closeout / "FINAL_MACHINE_LINES.txt": _file_digest(closeout / "FINAL_MACHINE_LINES.txt"),
        registry: _file_digest(registry),
    }

    assert _run_payload_builder(builder, closeout, registry, payload_path) == 0
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == PAYLOAD_SCHEMA
    assert payload["projection_ready"] is True
    assert payload["consumers"]["notion_projection_allowed"] is True
    assert payload["consumers"]["market_dashboard_projection_allowed"] is True
    assert all(v is False for v in payload["authority"].values())

    market = _market_context(monkeypatch, payload_path)
    assert market["gate_enabled"] is True
    assert market["section_visible"] is True
    assert market["status"] == "ready"
    assert market["projection_ready"] is True
    assert market["dashboard_projection_allowed"] is True
    assert market["registry_run"]
    _assert_no_leaks(json.dumps(market))

    assert _run_notion_dry_run(dry_run, payload_path, report_path) == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["schema_version"] == REPORT_SCHEMA
    assert report["dry_run"] is True
    assert report["write_requested"] is False
    assert report["write_allowed"] is False
    assert report["would_update"] is True
    assert report["would_create"] is False
    assert report["blocked_reason"] is None
    _assert_no_leaks(json.dumps(report))

    for path, digest in digests.items():
        assert _file_digest(path) == digest


def test_manifest_verify_failed_blocks_chain(
    builder, dry_run, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    work = tmp_path / "chain_manifest_fail"
    closeout, registry = _write_chain_fixtures(
        work, with_valid_manifest=False, manifest_valid=False, verify_log_ok=False
    )
    payload_path = work / "payload.json"
    report_path = work / "notion_report.json"

    assert _run_payload_builder(builder, closeout, registry, payload_path) == 0
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    assert payload["projection_ready"] is False

    market = _market_context(monkeypatch, payload_path)
    assert market["status"] == "blocked"
    assert market["projection_ready"] is False

    assert _run_notion_dry_run(dry_run, payload_path, report_path) == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["would_update"] is False
    assert report["blocked_reason"] is not None


def test_notion_projection_not_allowed_blocks_notion_only(
    builder, dry_run, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    work = tmp_path / "chain_notion_blocked"
    closeout, registry = _write_chain_fixtures(work)
    payload_path = work / "payload.json"
    report_path = work / "notion_report.json"

    assert _run_payload_builder(builder, closeout, registry, payload_path) == 0
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    assert payload["projection_ready"] is True

    payload["consumers"]["notion_projection_allowed"] = False
    payload["consumers"]["market_dashboard_projection_allowed"] = True
    payload_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    market = _market_context(monkeypatch, payload_path)
    assert market["status"] == "ready"
    assert market["dashboard_projection_allowed"] is True

    assert _run_notion_dry_run(dry_run, payload_path, report_path) == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["would_update"] is False
    assert report["blocked_reason"] == "NOTION_PROJECTION_NOT_ALLOWED"


def test_market_dashboard_not_allowed_blocks_market_only(
    builder, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    work = tmp_path / "chain_market_blocked"
    closeout, registry = _write_chain_fixtures(work)
    payload_path = work / "payload.json"

    assert _run_payload_builder(builder, closeout, registry, payload_path) == 0
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    payload["consumers"]["market_dashboard_projection_allowed"] = False
    payload["consumers"]["notion_projection_allowed"] = True
    payload_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    market = _market_context(monkeypatch, payload_path)
    assert market["status"] == "consumer_not_allowed"
    assert market["projection_ready"] is False
    assert market["dashboard_projection_allowed"] is False


def test_authority_violation_blocks_chain(
    builder, dry_run, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    work = tmp_path / "chain_authority"
    closeout, registry = _write_chain_fixtures(work, registry_live_authority=True)
    payload_path = work / "payload.json"
    report_path = work / "notion_report.json"

    assert _run_payload_builder(builder, closeout, registry, payload_path) == 0
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    assert payload["projection_ready"] is False

    market = _market_context(monkeypatch, payload_path)
    assert market["projection_ready"] is False

    assert _run_notion_dry_run(dry_run, payload_path, report_path) == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["would_update"] is False
    assert report["blocked_reason"] is not None


def test_repo_local_output_paths_rejected(builder, dry_run, tmp_path: Path):
    work = tmp_path / "chain_repo_paths"
    closeout, registry = _write_chain_fixtures(work)
    payload_path = work / "payload.json"
    _run_payload_builder(builder, closeout, registry, payload_path)

    forbidden_payload_out = REPO_ROOT / "forbidden_chain_payload_out.json"
    forbidden_report_out = REPO_ROOT / "forbidden_chain_report_out.json"
    try:
        assert _run_payload_builder(builder, closeout, registry, forbidden_payload_out) == 2
        assert _run_notion_dry_run(dry_run, payload_path, forbidden_report_out) == 2
    finally:
        forbidden_payload_out.unlink(missing_ok=True)
        forbidden_report_out.unlink(missing_ok=True)


def test_chain_reuses_projection_consumer_fixture_marker():
    assert pc.REGISTRY_V1_PROJECTION_CONSUMER_SMOKE_FIXTURES_V0 is True
