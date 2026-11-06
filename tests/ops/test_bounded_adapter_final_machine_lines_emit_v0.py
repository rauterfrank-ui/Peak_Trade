"""Tests for bounded adapter FINAL_MACHINE_LINES.txt emission (non-authorizing)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.ops import test_build_post_closeout_projection_payload_v0 as payload_tests

REPO_ROOT = Path(__file__).resolve().parents[2]
PAPER_ADAPTER = REPO_ROOT / "scripts" / "ops" / "run_paper_only_bounded_observation_adapter_v0.py"
SHADOW_ADAPTER = REPO_ROOT / "scripts" / "ops" / "run_shadow_bounded_observation_adapter_v0.py"
FORBIDDEN_CHAIN_SCRIPT = REPO_ROOT / "scripts" / "ops" / "post_closeout_chain_execute_v0.py"

SAFETY_FLAGS: tuple[str, ...] = (
    "REMOTE_AWS_TOUCHED",
    "RUNTIME_STARTED",
    "SCHEDULER_STARTED",
    "PAPER_SHADOW_TESTNET_LIVE_STARTED",
    "LIVE_AUTHORITY_CHANGED",
)


def _load_paper():
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location(
        "run_paper_only_bounded_observation_adapter_v0", PAPER_ADAPTER
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_shadow():
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location(
        "run_shadow_bounded_observation_adapter_v0", SHADOW_ADAPTER
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def builder():
    return payload_tests._load_builder()


@pytest.fixture(scope="module")
def paper():
    return _load_paper()


@pytest.fixture(scope="module")
def shadow():
    return _load_shadow()


def _parse_machine_lines(path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or "=" not in line:
            continue
        key, _, value = line.partition("=")
        parsed[key.strip()] = value.strip()
    return parsed


def _machine_line_keys_from_text(path: Path) -> list[str]:
    keys: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or "=" not in line:
            continue
        key, _, _ = line.partition("=")
        keys.append(key.strip())
    return keys


def test_forbidden_post_closeout_chain_execute_script_absent() -> None:
    assert not FORBIDDEN_CHAIN_SCRIPT.exists()


@pytest.mark.parametrize(
    "lane",
    [
        "paper_only_bounded_observation_v0",
        "shadow_bounded_observation_v0",
    ],
)
def test_build_bounded_adapter_final_machine_lines_has_required_keys(
    paper, builder, lane: str
) -> None:
    lines = paper.build_bounded_adapter_final_machine_lines_v0(
        run_id="fixture_run",
        adapter_lane=lane,
        execution_performed=True,
        review_verdict="PASS",
    )
    for key in builder.REQUIRED_MACHINE_LINE_KEYS:
        assert key in lines
    for flag in SAFETY_FLAGS:
        assert lines[flag] == "false"


@pytest.mark.parametrize(
    "repo_head_sha_prefix,expected",
    [
        ("abcdef012345", "abcdef012345"),
        ("UNKNOWN_REF_MISSING", "UNKNOWN_REF_MISSING"),
        (None, "UNKNOWN_HEAD_MISSING"),
        ("", "UNKNOWN_HEAD_MISSING"),
        ("   ", "UNKNOWN_HEAD_MISSING"),
    ],
)
def test_build_bounded_adapter_final_machine_lines_emits_repo_head_sha_prefix(
    paper, repo_head_sha_prefix: str | None, expected: str
) -> None:
    lines = paper.build_bounded_adapter_final_machine_lines_v0(
        run_id="fixture_run",
        adapter_lane="shadow_bounded_observation_v0",
        execution_performed=True,
        review_verdict="PASS",
        repo_head_sha_prefix=repo_head_sha_prefix,
    )
    assert paper.REPO_HEAD_SHA_PREFIX_MACHINE_LINE_KEY in lines
    assert lines[paper.REPO_HEAD_SHA_PREFIX_MACHINE_LINE_KEY] == expected
    assert lines[paper.REPO_HEAD_SHA_PREFIX_MACHINE_LINE_KEY] != "18a79ede"


def test_build_bounded_adapter_final_machine_lines_repo_head_key_is_deterministic(
    paper,
) -> None:
    kwargs = {
        "run_id": "fixture_run",
        "adapter_lane": paper.BOUNDED_ADAPTER_LANE_PAPER,
        "execution_performed": True,
        "review_verdict": "PASS",
        "repo_head_sha_prefix": "0123456789ab",
    }
    first = paper.build_bounded_adapter_final_machine_lines_v0(**kwargs)
    second = paper.build_bounded_adapter_final_machine_lines_v0(**kwargs)
    assert first == second
    assert len(first) == len(set(first))


def test_paper_write_closeout_artifacts_fail_closed_repo_head_sha_prefix(
    paper, tmp_path: Path
) -> None:
    from unittest.mock import patch

    staging = tmp_path / "staging"
    staging.mkdir(parents=True, exist_ok=True)
    archive_dest = tmp_path / "archive" / "runs" / "paper" / "fixture_run"
    ctx = paper.ExecuteContext(
        args=type("Args", (), {})(),
        repo_root=REPO_ROOT,
        staging_root=staging,
        archive_root=tmp_path / "archive",
        runtime_out=staging / "runtime_out",
        logs_dir=staging / "logs",
        plan_dir=staging / "plan",
        review_dir=staging / "review",
        temp_jobs=staging / "jobs.toml",
        run_id="fixture_run",
    )
    plan = paper.AdapterPlan(
        adapter_version="test",
        mode="execute",
        staging_root=str(staging),
        archive_root=str(tmp_path / "archive"),
        duration_seconds=60,
        poll_interval_seconds=30,
        job_name="paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0",
        include_tags="paper_runtime",
        run_id="fixture_run",
        repo_root=str(REPO_ROOT),
        source_jobs_toml=str(REPO_ROOT / "config/scheduler/jobs.toml"),
        commands={},
        retention_steps=[],
        expected_artifacts=[],
    )
    with patch.object(paper, "_read_git_sha_prefix", return_value="UNKNOWN_HEAD_MISSING"):
        paper._write_closeout_artifacts(
            ctx,
            plan,
            archive_dest,
            {"verdict": "PASS", "issues": []},
        )
    path = staging / paper.FINAL_MACHINE_LINES_FILENAME
    assert path.is_file()
    lines = _parse_machine_lines(path)
    assert lines["ADAPTER_LANE"] == paper.BOUNDED_ADAPTER_LANE_PAPER
    assert lines["REVIEW_VERDICT"] == "PASS"
    assert lines[paper.REPO_HEAD_SHA_PREFIX_MACHINE_LINE_KEY] == (
        paper.REPO_HEAD_SHA_PREFIX_FAIL_CLOSED
    )
    metadata = json.loads((staging / "RUN_METADATA.json").read_text(encoding="utf-8"))
    assert metadata["repo_head_sha_prefix"] == paper.REPO_HEAD_SHA_PREFIX_FAIL_CLOSED
    assert len(_machine_line_keys_from_text(path)) == len(lines)


def test_paper_write_closeout_artifacts_emits_final_machine_lines(paper, tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    staging.mkdir(parents=True, exist_ok=True)
    archive_dest = tmp_path / "archive" / "runs" / "paper" / "fixture_run"
    ctx = paper.ExecuteContext(
        args=type("Args", (), {})(),
        repo_root=REPO_ROOT,
        staging_root=staging,
        archive_root=tmp_path / "archive",
        runtime_out=staging / "runtime_out",
        logs_dir=staging / "logs",
        plan_dir=staging / "plan",
        review_dir=staging / "review",
        temp_jobs=staging / "jobs.toml",
        run_id="fixture_run",
    )
    plan = paper.AdapterPlan(
        adapter_version="test",
        mode="execute",
        staging_root=str(staging),
        archive_root=str(tmp_path / "archive"),
        duration_seconds=60,
        poll_interval_seconds=30,
        job_name="paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0",
        include_tags="paper_runtime",
        run_id="fixture_run",
        repo_root=str(REPO_ROOT),
        source_jobs_toml=str(REPO_ROOT / "config/scheduler/jobs.toml"),
        commands={},
        retention_steps=[],
        expected_artifacts=[],
    )
    paper._write_closeout_artifacts(
        ctx,
        plan,
        archive_dest,
        {"verdict": "PASS", "issues": []},
    )
    path = staging / paper.FINAL_MACHINE_LINES_FILENAME
    assert path.is_file()
    lines = _parse_machine_lines(path)
    assert lines["ADAPTER_LANE"] == paper.BOUNDED_ADAPTER_LANE_PAPER
    assert lines["REVIEW_VERDICT"] == "PASS"


def test_shadow_write_closeout_artifacts_emits_final_machine_lines(shadow, tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    staging.mkdir(parents=True, exist_ok=True)
    archive_dest = tmp_path / "archive" / "runs" / "shadow" / "fixture_run"
    ctx = shadow.ExecuteContext(
        args=type("Args", (), {})(),
        repo_root=REPO_ROOT,
        staging_root=staging,
        archive_root=tmp_path / "archive",
        wrapper_evidence=staging / "wrapper_evidence",
        logs_dir=staging / "logs",
        plan_dir=staging / "plan",
        review_dir=staging / "review",
        run_id="fixture_run",
    )
    plan = shadow.AdapterPlan(
        adapter_version="test",
        mode="execute",
        staging_root=str(staging),
        archive_root=str(tmp_path / "archive"),
        duration_minutes=10,
        max_steps=120,
        step_interval_seconds=0.0,
        run_id="fixture_run",
        repo_root=str(REPO_ROOT),
        wrapper_script="scripts/ops/shadow_247_futures_start_wrapper_skeleton_v0.py",
        wrapper_mode="bounded-shadow-dry-run",
        commands={},
        retention_steps=[],
        expected_artifacts=[],
    )
    shadow._write_closeout_artifacts(
        ctx,
        plan,
        archive_dest,
        {"verdict": "PASS", "issues": []},
    )
    path = staging / shadow.FINAL_MACHINE_LINES_FILENAME
    assert path.is_file()
    lines = _parse_machine_lines(path)
    assert lines["ADAPTER_LANE"] == shadow.BOUNDED_ADAPTER_LANE_SHADOW
    metadata = json.loads((staging / "RUN_METADATA.json").read_text(encoding="utf-8"))
    assert lines["REPO_HEAD_SHA_PREFIX"] == metadata["repo_head_sha_prefix"]


def test_emitted_lines_accepted_by_projection_builder(builder, paper, tmp_path: Path) -> None:
    staging = tmp_path / "closeout"
    staging.mkdir()
    lines = paper.build_bounded_adapter_final_machine_lines_v0(
        run_id="fixture_run",
        adapter_lane=paper.BOUNDED_ADAPTER_LANE_PAPER,
        execution_performed=True,
        review_verdict="PASS",
    )
    (staging / "FINAL_MACHINE_LINES.txt").write_text(
        "\n".join(f"{k}={v}" for k, v in sorted(lines.items())) + "\n",
        encoding="utf-8",
    )
    payload_tests._write_closeout_bundle(staging, with_machine_lines=False, closeout_artifact="md")
    registry_path = tmp_path / "registry.json"
    payload_tests._write_registry(registry_path, tmp_path)
    out = tmp_path / "payload.json"
    rc = builder.main(
        [
            "--closeout-root",
            str(staging),
            "--registry-json",
            str(registry_path),
            "--output-json",
            str(out),
            "--strict",
        ]
    )
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["projection_ready"] is True
