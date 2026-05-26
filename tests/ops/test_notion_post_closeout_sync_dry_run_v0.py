"""Tests for notion_post_closeout_sync_dry_run_v0 (offline Notion dry-run report CLI)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from tests.fixtures.ops.generic_evidence_run_registry_v1 import projection_consumer_v0 as pc

REPO_ROOT = Path(__file__).resolve().parents[2]
DRY_RUN_CLI = REPO_ROOT / "scripts/ops/notion_post_closeout_sync_dry_run_v0.py"
BUILDER = REPO_ROOT / "scripts/ops/build_post_closeout_projection_payload_v0.py"

PAYLOAD_SCHEMA = "peak_trade.post_closeout_projection_payload.v0"
REPORT_SCHEMA = "peak_trade.notion_post_closeout_sync_dry_run_report.v0"

FORBIDDEN_CLI_SUBSTRINGS = (
    "notion-",
    "notion.",
    "create_database",
    "create_pages",
    "update_page",
    "move_pages",
    "archive",
    "httpx",
    "requests.",
    "--write",
    "confirm-token",
    "confirm_token",
    "boto3",
    "rclone",
    "subprocess.run",
    "Popen(",
)

FORBIDDEN_IMPORT_MARKERS = (
    "import requests",
    "from requests",
    "import httpx",
    "from httpx",
)


def _load_dry_run():
    spec = importlib.util.spec_from_file_location(
        "notion_post_closeout_sync_dry_run_v0", DRY_RUN_CLI
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _authority_false() -> dict[str, bool]:
    return {
        key: False
        for key in (
            "notion_authority",
            "market_dashboard_authority",
            "runtime_authority",
            "scheduler_authority",
            "daemon_authority",
            "adapter_authority",
            "s3_authority",
            "workflow_dispatch_authority",
            "broker_exchange_authority",
            "testnet_authority",
            "live_authority",
            "master_v2_double_play_authority",
        )
    }


def _valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": PAYLOAD_SCHEMA,
        "generated_at_utc": "2026-05-26T00:00:00Z",
        "run_id": "paper_run",
        "projection_ready": True,
        "projection_blocked_reason": None,
        "manifest_verify_rc": 0,
        "closeout_accepted": True,
        "primary_evidence_finalized": True,
        "registry_pointer": "registry.json",
        "closeout_pointer": "closeout_bundle",
        "repo_commit": "fd61ca07",
        "s3_export_status": "disabled",
        "download_verify_rc": None,
        "authority": _authority_false(),
        "consumers": {
            "notion_projection_allowed": True,
            "market_dashboard_projection_allowed": True,
            "notion_write_allowed": False,
            "dashboard_write_allowed": False,
        },
        "source_files": {
            "registry_json": "/secret/path/registry.json",
            "final_machine_lines": "/secret/path/FINAL_MACHINE_LINES.txt",
        },
    }
    payload.update(overrides)
    return payload


def _write_payload(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _run_cli(
    dry_run,
    payload: Path,
    out: Path,
    *,
    boundary: bool = True,
    target_name: str = "Evidence & Closeouts",
    target_id_file: Path | None = None,
    strict: bool = False,
) -> int:
    argv = [
        "--projection-payload-json",
        str(payload),
        "--target-name",
        target_name,
        "--output-report-json",
        str(out),
    ]
    if boundary:
        argv.append("--boundary-text-verified")
    if target_id_file is not None:
        argv.extend(["--target-id-file", str(target_id_file)])
    if strict:
        argv.append("--strict")
    return dry_run.main(argv)


@pytest.fixture(scope="module")
def dry_run():
    return _load_dry_run()


def test_happy_dry_run(dry_run, tmp_path):
    payload_path = tmp_path / "payload.json"
    out = tmp_path / "report.json"
    _write_payload(payload_path, _valid_payload())

    rc = _run_cli(dry_run, payload_path, out)
    assert rc == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["schema_version"] == REPORT_SCHEMA
    assert report["dry_run"] is True
    assert report["write_requested"] is False
    assert report["write_allowed"] is False
    assert report["would_update"] is True
    assert report["would_create"] is False
    assert report["blocked_reason"] is None
    assert report["boundary_text_verified"] is True
    assert report["notion_target_name_safe"] == "Evidence & Closeouts"
    assert all(v is False for v in report["would_write_fields"]["authority"].values())
    assert report["source"]["projection_payload_basename"] == "payload.json"
    assert "/secret" not in json.dumps(report)
    assert "source_files" not in json.dumps(report)


def test_projection_ready_false_blocked(dry_run, tmp_path):
    payload_path = tmp_path / "payload.json"
    out = tmp_path / "report.json"
    _write_payload(
        payload_path,
        _valid_payload(projection_ready=False, projection_blocked_reason="REGISTRY_FAIL_CLOSED"),
    )

    rc = _run_cli(dry_run, payload_path, out)
    assert rc == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["would_update"] is False
    assert report["blocked_reason"] == "REGISTRY_FAIL_CLOSED"


def test_notion_projection_not_allowed(dry_run, tmp_path):
    payload_path = tmp_path / "payload.json"
    out = tmp_path / "report.json"
    consumers = {
        "notion_projection_allowed": False,
        "market_dashboard_projection_allowed": True,
        "notion_write_allowed": False,
        "dashboard_write_allowed": False,
    }
    _write_payload(payload_path, _valid_payload(consumers=consumers))

    rc = _run_cli(dry_run, payload_path, out)
    assert rc == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["blocked_reason"] == "NOTION_PROJECTION_NOT_ALLOWED"


def test_boundary_not_verified_blocked(dry_run, tmp_path):
    payload_path = tmp_path / "payload.json"
    out = tmp_path / "report.json"
    _write_payload(payload_path, _valid_payload())

    rc = _run_cli(dry_run, payload_path, out, boundary=False)
    assert rc == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["blocked_reason"] == "BOUNDARY_TEXT_NOT_VERIFIED"


def test_boundary_not_verified_strict_exit_one(dry_run, tmp_path):
    payload_path = tmp_path / "payload.json"
    out = tmp_path / "report.json"
    _write_payload(payload_path, _valid_payload())

    rc = _run_cli(dry_run, payload_path, out, boundary=False, strict=True)
    assert rc == 1


def test_authority_violation_blocked(dry_run, tmp_path):
    payload_path = tmp_path / "payload.json"
    out = tmp_path / "report.json"
    authority = _authority_false()
    authority["live_authority"] = True
    _write_payload(payload_path, _valid_payload(authority=authority))

    rc = _run_cli(dry_run, payload_path, out)
    assert rc == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["blocked_reason"] == "UNSAFE_AUTHORITY_TRUE"


def test_wrong_schema_blocked(dry_run, tmp_path):
    payload_path = tmp_path / "payload.json"
    out = tmp_path / "report.json"
    _write_payload(payload_path, _valid_payload(schema_version="peak_trade.other.v0"))

    rc = _run_cli(dry_run, payload_path, out)
    assert rc == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["blocked_reason"] == "PAYLOAD_SCHEMA_UNSUPPORTED"


def test_malformed_payload_blocked(dry_run, tmp_path):
    payload_path = tmp_path / "payload.json"
    out = tmp_path / "report.json"
    payload_path.write_text("{not json", encoding="utf-8")

    rc = _run_cli(dry_run, payload_path, out)
    assert rc == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["blocked_reason"] == "PAYLOAD_MALFORMED"


def test_output_path_inside_repo_exit_two(dry_run, tmp_path):
    payload_path = tmp_path / "payload.json"
    _write_payload(payload_path, _valid_payload())
    out = REPO_ROOT / "tmp_forbidden_report.json"
    try:
        rc = _run_cli(dry_run, payload_path, out)
        assert rc == 2
    finally:
        if out.exists():
            out.unlink()


def test_target_id_redaction(dry_run, tmp_path):
    raw_id = "85f00bc3-a934-476a-9b16-9ec295dc00b3"
    id_file = tmp_path / "notion_target_id.txt"
    id_file.write_text(raw_id + "\n", encoding="utf-8")
    payload_path = tmp_path / "payload.json"
    out = tmp_path / "report.json"
    _write_payload(payload_path, _valid_payload())

    rc = _run_cli(dry_run, payload_path, out, target_id_file=id_file)
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    assert raw_id not in text
    report = json.loads(text)
    assert report["notion_target_id_redacted"]
    assert len(report["notion_target_id_redacted"]) == 8


def test_input_payload_unchanged(dry_run, tmp_path):
    payload_path = tmp_path / "payload.json"
    out = tmp_path / "report.json"
    _write_payload(payload_path, _valid_payload())
    before = payload_path.read_bytes()

    rc = _run_cli(dry_run, payload_path, out)
    assert rc == 0
    assert payload_path.read_bytes() == before


def test_no_mcp_or_write_in_cli_source():
    text = DRY_RUN_CLI.read_text(encoding="utf-8")
    help_text = _load_dry_run().build_arg_parser().format_help()
    for marker in FORBIDDEN_IMPORT_MARKERS:
        assert marker not in text
    for sub in FORBIDDEN_CLI_SUBSTRINGS:
        assert sub not in help_text
    assert "notion_post_closeout_sync_dry_run" in text


def test_manifest_verify_failed_blocked(dry_run, tmp_path):
    payload_path = tmp_path / "payload.json"
    out = tmp_path / "report.json"
    _write_payload(payload_path, _valid_payload(manifest_verify_rc=1))

    rc = _run_cli(dry_run, payload_path, out)
    assert rc == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["blocked_reason"] == "MANIFEST_VERIFY_FAILED"


def test_empty_target_name_blocked(dry_run, tmp_path):
    payload_path = tmp_path / "payload.json"
    out = tmp_path / "report.json"
    _write_payload(payload_path, _valid_payload())

    rc = _run_cli(dry_run, payload_path, out, target_name="  ")
    assert rc == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["blocked_reason"] == "TARGET_DB_NOT_APPROVED"


def test_build_dry_run_report_unit(dry_run, tmp_path):
    payload_path = tmp_path / "payload.json"
    _write_payload(payload_path, _valid_payload())
    report = dry_run.build_dry_run_report(
        payload_path=payload_path,
        target_name="Evidence & Closeouts",
        boundary_text_verified=True,
    )
    assert report["schema_version"] == REPORT_SCHEMA
    assert (
        "NOTION_DRY_RUN_WRITER_DEFAULT_DRY_RUN=true"
        in pc.POST_CLOSEOUT_NOTION_DRY_RUN_WRITER_PLANNING_MARKERS
    )
