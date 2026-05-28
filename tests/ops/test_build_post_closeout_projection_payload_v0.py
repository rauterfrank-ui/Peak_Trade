"""Tests for build_post_closeout_projection_payload_v0 (offline projection payload builder)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from tests.fixtures.ops.generic_evidence_run_registry_v1 import projection_consumer_v0 as pc

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILDER = REPO_ROOT / "scripts/ops/build_post_closeout_projection_payload_v0.py"

REQUIRED_MACHINE_LINES: dict[str, str] = {
    "RUNTIME_COMMANDS_CALLED": "false",
    "NOTION_WRITE_CALLED": "false",
    "S3_AWS_RCLONE_CALLED": "false",
    "WORKFLOW_DISPATCH_CALLED": "false",
    "BROKER_EXCHANGE_CALLED": "false",
    "LIVE_AUTHORITY": "false",
    "TESTNET_AUTHORITY": "false",
}

FORBIDDEN_BUILDER_SUBSTRINGS = (
    "aws ",
    "rclone",
    "boto3",
    "subprocess.run",
    "os.system",
    "Popen(",
    "gh workflow",
    "requests.",
)

FORBIDDEN_BUILDER_IMPORT_MARKERS = (
    "preflight_remote_runtime_runner",
    "remote_paper_validator",
    "scheduler",
    "daemon",
)


def _load_builder():
    spec = importlib.util.spec_from_file_location(
        "build_post_closeout_projection_payload_v0", BUILDER
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_machine_lines(path: Path, overrides: dict[str, str] | None = None) -> None:
    lines = dict(REQUIRED_MACHINE_LINES)
    if overrides:
        lines.update(overrides)
    path.write_text("\n".join(f"{k}={v}" for k, v in lines.items()) + "\n", encoding="utf-8")


def _write_closeout_bundle(
    closeout_root: Path,
    *,
    with_manifest: bool = True,
    manifest_valid: bool = True,
    with_verify_log: bool = True,
    verify_log_ok: bool = True,
    with_machine_lines: bool = True,
    machine_line_overrides: dict[str, str] | None = None,
) -> None:
    closeout_root.mkdir(parents=True, exist_ok=True)
    (closeout_root / "evidence.txt").write_text("fixture\n", encoding="utf-8")
    (closeout_root / "DURABLE_COPY_README.md").write_text("# durable copy\n", encoding="utf-8")
    if with_machine_lines:
        _write_machine_lines(closeout_root / "FINAL_MACHINE_LINES.txt", machine_line_overrides)
    if with_manifest:
        from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

        write_manifest_sha256(closeout_root)
        if not manifest_valid:
            manifest = closeout_root / "MANIFEST.sha256"
            manifest.write_text("deadbeef  evidence.txt\n", encoding="utf-8")
    if with_verify_log:
        log = closeout_root / "MANIFEST_VERIFY.log"
        log.write_text(
            "evidence.txt: OK\n" if verify_log_ok else "evidence.txt: FAILED\n", encoding="utf-8"
        )


def _write_registry(
    path: Path, tmp_path: Path, *, run_id: str = "paper_run", live: bool = False
) -> None:
    archive = tmp_path / "archive"
    pc.write_minimal_paper_run(archive, run_id)
    registry = pc.build_registry(archive)
    if live:
        registry["runs"][0]["live_authority"] = True
    path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")


def _run_cli(builder, closeout: Path, registry: Path, out: Path, **extra: str) -> int:
    argv = [
        "--closeout-root",
        str(closeout),
        "--registry-json",
        str(registry),
        "--output-json",
        str(out),
    ]
    for key, value in extra.items():
        argv.extend([f"--{key.replace('_', '-')}", value])
    return builder.main(argv)


def _run_hook_cli(builder, closeout: Path, registry: Path, out: Path, **extra: str) -> int:
    argv = [
        "--closeout-root",
        str(closeout),
        "--registry-json",
        str(registry),
        "--output-json",
        str(out),
        "--hook-readiness-validator-v0",
    ]
    for key, value in extra.items():
        argv.extend([f"--{key.replace('_', '-')}", value])
    return builder.main(argv)


@pytest.fixture(scope="module")
def builder():
    return _load_builder()


def test_happy_path_projection_ready(builder, tmp_path):
    closeout = tmp_path / "closeout"
    registry_path = tmp_path / "registry.json"
    out = tmp_path / "out" / "payload.json"
    _write_closeout_bundle(closeout)
    _write_registry(registry_path, tmp_path)

    rc = _run_cli(builder, closeout, registry_path, out)
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "peak_trade.post_closeout_projection_payload.v0"
    assert payload["projection_ready"] is True
    assert payload["projection_blocked_reason"] is None
    assert payload["manifest_verify_rc"] == 0
    assert payload["closeout_accepted"] is True
    assert payload["primary_evidence_finalized"] is True
    assert all(v is False for v in payload["authority"].values())
    assert payload["consumers"]["notion_write_allowed"] is False
    assert payload["consumers"]["dashboard_write_allowed"] is False
    assert payload["consumers"]["notion_projection_allowed"] is True
    assert payload["consumers"]["market_dashboard_projection_allowed"] is True


def test_missing_manifest_blocked(builder, tmp_path):
    closeout = tmp_path / "closeout"
    registry_path = tmp_path / "registry.json"
    out = tmp_path / "payload.json"
    _write_closeout_bundle(closeout, with_manifest=False)
    _write_registry(registry_path, tmp_path)

    rc = _run_cli(builder, closeout, registry_path, out)
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["projection_ready"] is False
    assert payload["projection_blocked_reason"] == "missing_manifest"


def test_manifest_verify_failed_blocked(builder, tmp_path):
    closeout = tmp_path / "closeout"
    registry_path = tmp_path / "registry.json"
    out = tmp_path / "payload.json"
    _write_closeout_bundle(
        closeout,
        manifest_valid=False,
        verify_log_ok=False,
    )
    _write_registry(registry_path, tmp_path)

    rc = _run_cli(builder, closeout, registry_path, out)
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["projection_ready"] is False
    assert payload["projection_blocked_reason"] in (
        "manifest_verify_failed",
        "manifest_verify_missing_or_failed",
    )


def test_missing_final_machine_lines_blocked(builder, tmp_path):
    closeout = tmp_path / "closeout"
    registry_path = tmp_path / "registry.json"
    out = tmp_path / "payload.json"
    _write_closeout_bundle(closeout, with_machine_lines=False)
    _write_registry(registry_path, tmp_path)

    rc = _run_cli(builder, closeout, registry_path, out)
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["projection_ready"] is False
    assert payload["projection_blocked_reason"] == "missing_final_machine_lines"


def test_boundary_violation_live_authority(builder, tmp_path):
    closeout = tmp_path / "closeout"
    registry_path = tmp_path / "registry.json"
    out = tmp_path / "payload.json"
    _write_closeout_bundle(closeout, machine_line_overrides={"LIVE_AUTHORITY": "true"})
    _write_registry(registry_path, tmp_path)

    rc = _run_cli(builder, closeout, registry_path, out)
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["projection_ready"] is False
    assert payload["projection_blocked_reason"] == "authority_boundary_violation"


def test_boundary_violation_registry_live_authority(builder, tmp_path):
    closeout = tmp_path / "closeout"
    registry_path = tmp_path / "registry.json"
    out = tmp_path / "payload.json"
    _write_closeout_bundle(closeout)
    _write_registry(registry_path, tmp_path, live=True)

    rc = _run_cli(builder, closeout, registry_path, out)
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["projection_ready"] is False
    assert payload["projection_blocked_reason"] == "authority_boundary_violation"


def test_malformed_registry_blocked(builder, tmp_path):
    closeout = tmp_path / "closeout"
    registry_path = tmp_path / "registry.json"
    out = tmp_path / "payload.json"
    _write_closeout_bundle(closeout)
    registry_path.write_text("{not-json", encoding="utf-8")

    rc = _run_cli(builder, closeout, registry_path, out)
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["projection_ready"] is False
    assert payload["projection_blocked_reason"] == "malformed_registry_v1"


def test_output_write_only_inputs_unchanged(builder, tmp_path):
    closeout = tmp_path / "closeout"
    registry_path = tmp_path / "registry.json"
    out = tmp_path / "payload.json"
    _write_closeout_bundle(closeout)
    _write_registry(registry_path, tmp_path)

    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    before = {p: digest(p) for p in closeout.rglob("*") if p.is_file()}
    before[registry_path] = digest(registry_path)

    rc = _run_cli(builder, closeout, registry_path, out)
    assert rc == 0
    assert out.is_file()

    after = {p: digest(p) for p in closeout.rglob("*") if p.is_file()}
    after[registry_path] = digest(registry_path)
    assert before == after


def test_builder_has_no_runtime_or_external_side_effect_markers():
    text = BUILDER.read_text(encoding="utf-8")
    import_lines = [
        line.strip().lower()
        for line in text.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]
    joined_imports = "\n".join(import_lines)
    for marker in FORBIDDEN_BUILDER_IMPORT_MARKERS:
        assert marker not in joined_imports, f"forbidden import marker {marker!r}"
    for marker in FORBIDDEN_BUILDER_SUBSTRINGS:
        assert marker not in joined_imports, f"forbidden import substring {marker!r}"
    assert "subprocess" not in joined_imports
    assert "import requests" not in joined_imports
    assert "import boto3" not in joined_imports


def test_missing_boundary_flags_blocked(builder, tmp_path):
    closeout = tmp_path / "closeout"
    registry_path = tmp_path / "registry.json"
    out = tmp_path / "payload.json"
    _write_closeout_bundle(closeout)
    (closeout / "FINAL_MACHINE_LINES.txt").write_text(
        "RUNTIME_COMMANDS_CALLED=false\n", encoding="utf-8"
    )
    _write_registry(registry_path, tmp_path)

    rc = _run_cli(builder, closeout, registry_path, out)
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["projection_blocked_reason"] == "missing_boundary_flags"


def test_cli_rejects_output_inside_repo(builder, tmp_path):
    closeout = tmp_path / "closeout"
    registry_path = tmp_path / "registry.json"
    _write_closeout_bundle(closeout)
    _write_registry(registry_path, tmp_path)
    out = REPO_ROOT / "out" / "_pytest_payload.json"
    try:
        rc = _run_cli(builder, closeout, registry_path, out)
        assert rc == 2
    finally:
        out.unlink(missing_ok=True)


def test_hook_readiness_happy_path_ready(builder, tmp_path):
    closeout = tmp_path / "closeout"
    registry_path = tmp_path / "registry.json"
    out = tmp_path / "hook_readiness.json"
    _write_closeout_bundle(closeout)
    (closeout / "AFTER_PR3737_MERGE_CLOSEOUT.md").write_text("# closeout\n", encoding="utf-8")
    _write_registry(registry_path, tmp_path)

    rc = _run_hook_cli(builder, closeout, registry_path, out)
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "peak_trade.post_closeout_hook_readiness_validator.v0"
    assert payload["status"] == "READY"
    assert payload["blocked_reasons"] == []
    assert payload["checks"]["scheduler_heartbeat_informational_optional"] is True
    assert payload["safety_flags"]["REMOTE_AWS_TOUCHED"] is False
    assert payload["safety_flags"]["RUNTIME_STARTED"] is False
    assert payload["non_authorizing"] is True


def test_hook_readiness_blocks_missing_manifest(builder, tmp_path):
    closeout = tmp_path / "closeout"
    registry_path = tmp_path / "registry.json"
    out = tmp_path / "hook_readiness.json"
    _write_closeout_bundle(closeout, with_manifest=False)
    (closeout / "AFTER_PR3737_MERGE_CLOSEOUT.md").write_text("# closeout\n", encoding="utf-8")
    _write_registry(registry_path, tmp_path)

    rc = _run_hook_cli(builder, closeout, registry_path, out)
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["status"] == "BLOCKED"
    assert "manifest_sha256_exists" in payload["blocked_reasons"]


def test_hook_readiness_blocks_failing_manifest_verify_log(builder, tmp_path):
    closeout = tmp_path / "closeout"
    registry_path = tmp_path / "registry.json"
    out = tmp_path / "hook_readiness.json"
    _write_closeout_bundle(closeout)
    (closeout / "AFTER_PR3737_MERGE_CLOSEOUT.md").write_text("# closeout\n", encoding="utf-8")
    (closeout / "MANIFEST_VERIFY.log").write_text("evidence.txt: FAILED\n", encoding="utf-8")
    _write_registry(registry_path, tmp_path)

    rc = _run_hook_cli(builder, closeout, registry_path, out)
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["status"] == "BLOCKED"
    assert "manifest_verify_log_ok" in payload["blocked_reasons"]


def test_hook_readiness_blocks_missing_closeout_report(builder, tmp_path):
    closeout = tmp_path / "closeout"
    registry_path = tmp_path / "registry.json"
    out = tmp_path / "hook_readiness.json"
    _write_closeout_bundle(closeout)
    _write_registry(registry_path, tmp_path)

    rc = _run_hook_cli(builder, closeout, registry_path, out)
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["status"] == "BLOCKED"
    assert "closeout_report_exists" in payload["blocked_reasons"]


def test_hook_readiness_scheduler_heartbeat_optional(builder, tmp_path):
    closeout = tmp_path / "closeout"
    registry_path = tmp_path / "registry.json"
    out = tmp_path / "hook_readiness.json"
    _write_closeout_bundle(closeout)
    (closeout / "AFTER_PR3737_MERGE_CLOSEOUT.md").write_text("# closeout\n", encoding="utf-8")
    _write_registry(registry_path, tmp_path)

    rc = _run_hook_cli(builder, closeout, registry_path, out)
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["checks"]["scheduler_heartbeat_informational_optional"] is True
    assert payload["heartbeat"]["present"] is False
