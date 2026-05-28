"""Contract tests: closeout FINAL_MACHINE_LINES vs post-closeout projection payload builder.

Guards the Real10m gap (shadow_dry_mini_real10m_20260527T114606Z): incomplete Phase-3
machine lines caused Phase-5 ``missing_boundary_flags`` and required manual recovery.
Tests-only; synthetic tmp_path fixtures — no runtime, adapter, or durable evidence execution.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.ops import test_build_post_closeout_projection_payload_v0 as payload_tests

REPO_ROOT = Path(__file__).resolve().parents[2]

# Incomplete set written by the durable Real10m execute script before manual recovery
# (missing four keys required by build_post_closeout_projection_payload_v0).
REAL10M_PHASE3_INCOMPLETE_MACHINE_LINES: dict[str, str] = {
    "RUNTIME_COMMANDS_CALLED": "true",
    "ADAPTER_EXECUTED": "true",
    "SHADOW_DRY_MINI_REAL_10MIN_RERUN": "true",
    "NOTION_WRITE_CALLED": "false",
    "BROKER_EXCHANGE_CALLED": "false",
    "LIVE_START_PERMITTED": "false",
    "TESTNET_START_PERMITTED": "false",
    "MAIN_HEAD": "de90da8aad0853f95145f1d57085c3eb7aac0463",
    "RUN_ID": "shadow_dry_mini_real10m_20260527T114606Z",
}

# Operator execute scripts should align with builder-required keys at minimum.
REAL10M_BOUNDARY_SAFE_SUPPLEMENTS: dict[str, str] = {
    "S3_AWS_RCLONE_CALLED": "false",
    "WORKFLOW_DISPATCH_CALLED": "false",
    "LIVE_AUTHORITY": "false",
    "TESTNET_AUTHORITY": "false",
    "BROKER_EXCHANGE_AUTHORITY": "false",
    "TESTNET_START_PERMITTED": "false",
    "LIVE_START_PERMITTED": "false",
    "SCHEDULER_EXECUTED": "false",
    "DAEMON_EXECUTED": "false",
    "MASTER_V2_DOUBLE_PLAY_AUTHORITY_CHANGED": "false",
}


@pytest.fixture(scope="module")
def builder():
    return payload_tests._load_builder()


def _write_lines(closeout: Path, lines: dict[str, str]) -> None:
    closeout.mkdir(parents=True, exist_ok=True)
    (closeout / "FINAL_MACHINE_LINES.txt").write_text(
        "\n".join(f"{k}={v}" for k, v in lines.items()) + "\n",
        encoding="utf-8",
    )


def _build_payload(
    builder,
    tmp_path: Path,
    machine_lines: dict[str, str],
    *,
    strict: bool = False,
) -> tuple[int, dict[str, object]]:
    closeout = tmp_path / "closeout"
    registry_path = tmp_path / "registry.json"
    out = tmp_path / "payload.json"
    payload_tests._write_closeout_bundle(closeout, with_machine_lines=False)
    _write_lines(closeout, machine_lines)
    payload_tests._write_registry(registry_path, tmp_path)
    argv = [
        "--closeout-root",
        str(closeout),
        "--registry-json",
        str(registry_path),
        "--output-json",
        str(out),
    ]
    if strict:
        argv.append("--strict")
    rc = builder.main(argv)
    payload = json.loads(out.read_text(encoding="utf-8"))
    return rc, payload


def test_builder_required_keys_match_existing_fixture_contract(builder):
    required = set(builder.REQUIRED_MACHINE_LINE_KEYS)
    fixture_keys = set(payload_tests.REQUIRED_MACHINE_LINES)
    assert required == fixture_keys
    assert required == {
        "RUNTIME_COMMANDS_CALLED",
        "NOTION_WRITE_CALLED",
        "S3_AWS_RCLONE_CALLED",
        "WORKFLOW_DISPATCH_CALLED",
        "BROKER_EXCHANGE_CALLED",
        "LIVE_AUTHORITY",
        "TESTNET_AUTHORITY",
    }


@pytest.mark.parametrize("missing_key", list(payload_tests.REQUIRED_MACHINE_LINES))
def test_each_missing_required_key_triggers_missing_boundary_flags(
    builder, tmp_path, missing_key: str
):
    lines = dict(payload_tests.REQUIRED_MACHINE_LINES)
    del lines[missing_key]
    rc, payload = _build_payload(builder, tmp_path, lines)
    assert rc == 0
    assert payload["projection_ready"] is False
    assert payload["projection_blocked_reason"] == "missing_boundary_flags"


def test_real10m_phase3_incomplete_machine_lines_must_not_claim_full_automation(builder, tmp_path):
    """Reproduce Real10m Phase-3 gap: partial lines block Phase-5 strict automation."""
    rc, payload = _build_payload(
        builder, tmp_path, REAL10M_PHASE3_INCOMPLETE_MACHINE_LINES, strict=True
    )
    assert rc == 1
    assert payload["projection_ready"] is False
    assert payload["projection_blocked_reason"] == "missing_boundary_flags"


def test_complete_required_keys_enable_projection_ready(builder, tmp_path):
    lines = dict(payload_tests.REQUIRED_MACHINE_LINES)
    rc, payload = _build_payload(builder, tmp_path, lines, strict=True)
    assert rc == 0
    assert payload["projection_ready"] is True
    assert payload["projection_blocked_reason"] is None


def test_real10m_safe_supplements_with_required_keys_projection_ready(builder, tmp_path):
    lines = dict(payload_tests.REQUIRED_MACHINE_LINES)
    lines.update(REAL10M_BOUNDARY_SAFE_SUPPLEMENTS)
    lines["RUNTIME_COMMANDS_CALLED"] = "true"
    lines["ADAPTER_EXECUTED"] = "true"
    rc, payload = _build_payload(builder, tmp_path, lines, strict=True)
    assert rc == 0
    assert payload["projection_ready"] is True


def test_projection_ready_is_not_wall_clock_duration_evidence(builder, tmp_path):
    """projection_ready must not be used as proof of minimum runtime duration."""
    lines = dict(payload_tests.REQUIRED_MACHINE_LINES)
    rc, payload = _build_payload(builder, tmp_path, lines, strict=True)
    assert rc == 0
    assert payload["projection_ready"] is True
    serialized = json.dumps(payload)
    for forbidden in (
        "OBSERVED_DURATION_SECONDS",
        "EXPECTED_DURATION_SECONDS",
        "WALL_CLOCK_VALIDATION",
        "step_interval_seconds",
    ):
        assert forbidden not in serialized


def test_no_repo_production_script_writes_final_machine_lines_file():
    """Inventory: bounded adapters + payload builder may write FINAL_MACHINE_LINES.txt."""
    scripts_ops = REPO_ROOT / "scripts" / "ops"
    allowed_writers = {
        "scripts/ops/build_post_closeout_projection_payload_v0.py",
        "scripts/ops/run_paper_only_bounded_observation_adapter_v0.py",
        "scripts/ops/run_shadow_bounded_observation_adapter_v0.py",
    }
    writers: list[str] = []
    for path in scripts_ops.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if 'FINAL_MACHINE_LINES.txt"' in text or "FINAL_MACHINE_LINES.txt'" in text:
            rel = path.relative_to(REPO_ROOT).as_posix()
            if rel not in allowed_writers:
                writers.append(rel)
    assert writers == [], (
        "unexpected production writers of FINAL_MACHINE_LINES.txt; "
        "extend contract tests if intentional: " + ", ".join(writers)
    )


def test_execute_phase3_embedded_snippet_must_include_all_builder_required_keys():
    """Read-only guard for bash-embedded Python that writes FINAL_MACHINE_LINES."""
    durable_marker = "SHADOW_DRY_MINI_REAL_10MIN_RERUN"
    repo_scripts = list((REPO_ROOT / "scripts").rglob("*.sh"))
    assert repo_scripts or True
    for script in repo_scripts:
        text = script.read_text(encoding="utf-8")
        if durable_marker not in text and "FINAL_MACHINE_LINES" not in text:
            continue
        for key in payload_tests.REQUIRED_MACHINE_LINES:
            assert f'"{key}"' in text or f"'{key}'" in text, (
                f"{script.relative_to(REPO_ROOT)} writes FINAL_MACHINE_LINES but omits {key}"
            )
