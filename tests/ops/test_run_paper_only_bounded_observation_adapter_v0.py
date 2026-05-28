"""Tests for scripts/ops/run_paper_only_bounded_observation_adapter_v0.py."""

from __future__ import annotations

import importlib.util
import io
import json
import shutil
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Mapping, Sequence

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "ops" / "run_paper_only_bounded_observation_adapter_v0.py"
APPROVAL_FIXTURE = (
    ROOT / "tests" / "fixtures" / "ops" / "paper_only_adapter_stage3_approval_sample.md"
)
APPROVAL_FIXTURE_24H = (
    ROOT / "tests" / "fixtures" / "ops" / "daemon_paper_shadow_24h_adapter_approval_sample.md"
)
RUN_ID_24H = "daemon_paper_24h_20260524T093549Z"
PROFILE_24H = "daemon_paper_shadow_24h_v0"
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")


def _load_mod():
    name = "run_paper_only_bounded_observation_adapter_v0"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _staging(tmp_path: Path) -> Path:
    return Path("/tmp") / f"peak_trade_paper_only_bounded_observation_test_{tmp_path.name}"


def _base_argv(staging: Path, archive: Path | None = None) -> list[str]:
    return [
        "--staging-root",
        str(staging),
        "--archive-root",
        str(archive or ARCHIVE_ROOT),
        "--repo-root",
        str(ROOT),
    ]


def _base_argv_24h(staging: Path, archive: Path | None = None) -> list[str]:
    return _base_argv(staging, archive) + [
        "--profile",
        PROFILE_24H,
        "--run-id",
        RUN_ID_24H,
    ]


def _durable_archive(tmp_path: Path) -> Path:
    # pytest tmp_path on Linux CI lives under /tmp; adapter rejects archive roots there.
    path = ROOT / "tests" / ".pytest_archive_roots" / tmp_path.name
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(autouse=True)
def _cleanup_durable_archive_dirs():
    yield
    archive_roots = ROOT / "tests" / ".pytest_archive_roots"
    if archive_roots.is_dir():
        shutil.rmtree(archive_roots, ignore_errors=True)


def _plan_dict(staging: Path, archive: Path | None = None) -> dict:
    mod = _load_mod()
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.main(_base_argv(staging, archive) + ["--json"])
    assert rc == 0, buf.getvalue()
    return json.loads(buf.getvalue())


def test_script_exists() -> None:
    assert SCRIPT.is_file()


def test_help_works() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "plan-only" in proc.stdout.lower() or "plan only" in proc.stdout.lower()


def test_plan_only_default_does_not_call_subprocess(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    called = {"count": 0}

    def _runner(*_args, **_kwargs) -> int:
        called["count"] += 1
        return 0

    rc = mod.main(_base_argv(staging), subprocess_runner=_runner)
    assert rc == 0
    assert called["count"] == 0


def test_plan_only_emits_paper_only_job_allowlist(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    assert plan["job_name"] == "paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0"


def test_default_duration_is_7200(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    assert plan["duration_seconds"] == 7200


def test_default_tag_is_paper_runtime(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    assert plan["include_tags"] == "paper_runtime"


def test_default_poll_interval_is_30(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    assert plan["poll_interval_seconds"] == 30


def test_execute_without_approval_record_fails(tmp_path: Path) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    rc = mod.main(
        _base_argv(staging) + ["--execute", "--no-strict-repo-clean"],
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0
    start_rc = staging / mod.START_RETURN_CODE_ARTIFACT
    assert start_rc.is_file()
    content = start_rc.read_text(encoding="utf-8")
    assert f"START_RC={mod.VALIDATION_EXIT}" in content
    assert "execute requires --approval-record" in content


def test_execute_without_archive_root_fails(tmp_path: Path) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    missing_archive = tmp_path / "missing_archive"
    rc = mod.main(
        [
            "adapter.py",
            "--staging-root",
            str(staging),
            "--archive-root",
            str(missing_archive),
            "--repo-root",
            str(ROOT),
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE),
            "--no-strict-repo-clean",
        ],
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0


def test_execute_with_missing_approval_fields_fails(tmp_path: Path) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    bad = tmp_path / "bad_approval.md"
    bad.write_text("APPROVE_EXECUTE_PAPER_ONLY_120MIN_NOW=false\n", encoding="utf-8")
    rc = mod.main(
        _base_argv(staging)
        + [
            "--execute",
            "--approval-record",
            str(bad),
            "--no-strict-repo-clean",
        ],
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0


def test_execute_rejects_start_shadow_now_true(tmp_path: Path) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    bad = tmp_path / "shadow_approval.md"
    bad.write_text(
        "\n".join(
            [
                "APPROVE_EXECUTE_PAPER_ONLY_120MIN_NOW=true",
                "START_PAPER_NOW=true",
                "START_SHADOW_NOW=true",
            ]
        ),
        encoding="utf-8",
    )
    rc = mod.main(
        _base_argv(staging)
        + ["--execute", "--approval-record", str(bad), "--no-strict-repo-clean"],
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0


def test_execute_rejects_start_testnet_now_true(tmp_path: Path) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    bad = tmp_path / "testnet_approval.md"
    bad.write_text(
        "\n".join(
            [
                "APPROVE_EXECUTE_PAPER_ONLY_120MIN_NOW=true",
                "START_PAPER_NOW=true",
                "START_TESTNET_NOW=true",
            ]
        ),
        encoding="utf-8",
    )
    rc = mod.main(
        _base_argv(staging)
        + ["--execute", "--approval-record", str(bad), "--no-strict-repo-clean"],
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0


def test_execute_rejects_live_allowed_true(tmp_path: Path) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    bad = tmp_path / "live_approval.md"
    bad.write_text(
        "\n".join(
            [
                "APPROVE_EXECUTE_PAPER_ONLY_120MIN_NOW=true",
                "START_PAPER_NOW=true",
                "LIVE_ALLOWED=true",
            ]
        ),
        encoding="utf-8",
    )
    rc = mod.main(
        _base_argv(staging)
        + ["--execute", "--approval-record", str(bad), "--no-strict-repo-clean"],
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0


def test_execute_accepts_sample_approval_with_mocked_runner(tmp_path: Path) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    calls: list[str] = []
    scheduler_extra_env: dict[str, str] | None = None

    def _runner(
        argv: Sequence[str],
        _cwd,
        _stdout,
        _stderr,
        *,
        extra_env: Mapping[str, str] | None = None,
    ) -> int:
        calls.append(" ".join(argv))
        if "run_with_timeout.py" in " ".join(argv):
            nonlocal scheduler_extra_env
            scheduler_extra_env = dict(extra_env) if extra_env else None
            return mod.TIMEOUT_EXIT
        if "review_scheduler_paper_runtime_evidence.py" in " ".join(argv):
            review_dir = staging / "review"
            review_dir.mkdir(parents=True, exist_ok=True)
            (review_dir / "REVIEW_RESULT.json").write_text(
                json.dumps({"verdict": "PASS", "metrics": {}, "issues": []}),
                encoding="utf-8",
            )
            return 0
        return 0

    archive = _durable_archive(tmp_path)
    rc = mod.main(
        _base_argv(staging, archive)
        + [
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE),
            "--no-strict-repo-clean",
        ],
        subprocess_runner=_runner,
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc == 0
    assert calls
    assert scheduler_extra_env is None
    start_rc = staging / mod.START_RETURN_CODE_ARTIFACT
    assert start_rc.is_file()
    assert f"START_RC=0" in start_rc.read_text(encoding="utf-8")


def test_command_plan_includes_make_scheduler_temp_config(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    joined = " ".join(plan["commands"]["temp_config"])
    assert "make_scheduler_temp_config.py" in joined


def test_command_plan_includes_run_with_timeout(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    joined = " ".join(plan["commands"]["scheduler_bounded"])
    assert "run_with_timeout.py" in joined


def test_command_plan_includes_run_scheduler(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    joined = " ".join(plan["commands"]["scheduler_bounded"])
    assert "run_scheduler.py" in joined
    assert "--heartbeat-file" in joined
    assert "scheduler_heartbeat_freshness_v0.json" in joined


def test_command_plan_includes_review_helper(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    joined = " ".join(plan["commands"]["review"])
    assert "review_scheduler_paper_runtime_evidence.py" in joined


def test_command_plan_uses_high_vol_job(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    assert plan["job_name"] == "paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0"
    joined = " ".join(plan["commands"]["temp_config"])
    assert "paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0" in joined


def test_command_plan_never_uses_shadow_testnet_live_jobs(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    blob = json.dumps(plan["commands"]).lower()
    assert "shadow_247_futures" not in blob
    assert "testnet" not in blob
    assert "bounded_pilot" not in blob


def test_archive_retention_steps_include_checksum_manifest(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    joined = " ".join(plan["retention_steps"]).lower()
    assert "manifest.sha256" in joined


def test_staging_root_is_under_tmp(tmp_path: Path) -> None:
    staging = _staging(tmp_path)
    plan = _plan_dict(staging)
    assert "/tmp" in plan["staging_root"] or str(staging).startswith("/tmp")


def test_durable_archive_root_outside_tmp_in_execute_mode(tmp_path: Path) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    issues = mod.validate_execute_preconditions(
        mod.ExecuteContext(
            args=type(
                "Args",
                (),
                {
                    "approval_record": APPROVAL_FIXTURE,
                    "strict_repo_clean": False,
                },
            )(),
            repo_root=ROOT,
            staging_root=staging,
            archive_root=archive,
            runtime_out=staging / "runtime_out",
            logs_dir=staging / "logs",
            plan_dir=staging / "plan",
            review_dir=staging / "review",
            temp_jobs=staging / "plan" / "temp_jobs.toml",
            run_id="test_run",
        ),
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert not issues


def test_execute_rejects_tmp_archive_root(tmp_path: Path) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    tmp_archive = Path("/tmp/peak_trade_adapter_reject_archive_test")
    tmp_archive.mkdir(parents=True, exist_ok=True)
    issues = mod.validate_execute_preconditions(
        mod.ExecuteContext(
            args=type(
                "Args",
                (),
                {
                    "approval_record": APPROVAL_FIXTURE,
                    "strict_repo_clean": False,
                },
            )(),
            repo_root=ROOT,
            staging_root=staging,
            archive_root=tmp_archive,
            runtime_out=staging / "runtime_out",
            logs_dir=staging / "logs",
            plan_dir=staging / "plan",
            review_dir=staging / "review",
            temp_jobs=staging / "plan" / "temp_jobs.toml",
            run_id="test_run",
        ),
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert any("outside /tmp" in issue for issue in issues)


def test_json_output_parseable(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    assert isinstance(plan, dict)
    assert "commands" in plan


def test_fixed_job_constant_matches_allowlist() -> None:
    mod = _load_mod()
    assert mod.ALLOWED_JOB == "paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0"


def test_validate_env_guardrails_blocks_live() -> None:
    mod = _load_mod()
    issues = mod.validate_env_guardrails({"PT_LIVE_ENABLED": "true"})
    assert issues


def test_module_build_plan_forbidden_paths_absent(tmp_path: Path) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    plan = mod.build_plan(
        mode="plan-only",
        staging_root=staging,
        archive_root=ARCHIVE_ROOT,
        repo_root=ROOT,
        source_jobs_toml=ROOT / "config/scheduler/jobs.toml",
        duration_seconds=7200,
        poll_interval_seconds=30,
        run_id="test_run",
    )
    assert plan.forbidden_paths_absent is True


def test_default_profile_unchanged_still_7200(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    assert plan["duration_seconds"] == 7200
    assert plan.get("contract_profile", "") == ""


def test_24h_profile_plan_only_default_duration_86400(tmp_path: Path) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.main(_base_argv_24h(staging) + ["--json"])
    assert rc == 0, buf.getvalue()
    plan = json.loads(buf.getvalue())
    assert plan["duration_seconds"] == 86400
    assert plan["contract_profile"] == PROFILE_24H
    assert plan["run_id"] == RUN_ID_24H


def test_24h_profile_rejects_7200_duration(tmp_path: Path) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    rc = mod.main(
        _base_argv_24h(staging) + ["--duration-seconds", "7200"],
    )
    assert rc != 0


def test_24h_profile_requires_run_id(tmp_path: Path) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    rc = mod.main(
        _base_argv(staging) + ["--profile", PROFILE_24H],
    )
    assert rc != 0


def test_unknown_profile_rejected(tmp_path: Path) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    rc = mod.main(
        _base_argv(staging) + ["--profile", "unknown_profile_v0"],
    )
    assert rc != 0


def test_24h_profile_execute_rejects_120min_approval_fixture(tmp_path: Path) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    rc = mod.main(
        _base_argv_24h(staging, archive)
        + [
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE),
            "--no-strict-repo-clean",
        ],
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0


def test_24h_profile_execute_rejects_run_id_mismatch(tmp_path: Path) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    rc = mod.main(
        _base_argv(staging, archive)
        + [
            "--profile",
            PROFILE_24H,
            "--run-id",
            "other_run_id",
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE_24H),
            "--no-strict-repo-clean",
        ],
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0


@pytest.mark.parametrize("key", ["PAPER_LANE_AUTHORIZED", "SHADOW_LANE_AUTHORIZED"])
def test_24h_profile_execute_rejects_missing_lane_key(tmp_path: Path, key: str) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    text = APPROVAL_FIXTURE_24H.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if not line.strip().startswith(f"{key}=")]
    bad = tmp_path / "bad_approval.md"
    bad.write_text("\n".join(lines) + "\n", encoding="utf-8")
    rc = mod.main(
        _base_argv_24h(staging, archive)
        + [
            "--execute",
            "--approval-record",
            str(bad),
            "--no-strict-repo-clean",
        ],
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("START_TESTNET_NOW", "true"),
        ("START_LIVE_NOW", "true"),
        ("LIVE_ALLOWED", "true"),
        ("BROKER_EXCHANGE_ALLOWED", "true"),
    ],
)
def test_24h_profile_execute_rejects_forbidden_flags(
    tmp_path: Path, field: str, value: str
) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    text = APPROVAL_FIXTURE_24H.read_text(encoding="utf-8").replace(
        f"{field}=false", f"{field}={value}"
    )
    bad = tmp_path / f"bad_{field}.md"
    bad.write_text(text, encoding="utf-8")
    rc = mod.main(
        _base_argv_24h(staging, archive)
        + [
            "--execute",
            "--approval-record",
            str(bad),
            "--no-strict-repo-clean",
        ],
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0


def test_24h_profile_execute_accepts_sample_fixture_mocked(tmp_path: Path) -> None:
    mod = _load_mod()
    staging = _staging(tmp_path)
    calls: list[str] = []
    scheduler_extra_env: dict[str, str] | None = None

    def _runner(
        argv: Sequence[str],
        _cwd,
        _stdout,
        _stderr,
        *,
        extra_env: Mapping[str, str] | None = None,
    ) -> int:
        calls.append(" ".join(argv))
        if "review_scheduler_paper_runtime_evidence.py" in " ".join(argv):
            review_dir = staging / "review"
            review_dir.mkdir(parents=True, exist_ok=True)
            (review_dir / "REVIEW_RESULT.json").write_text(
                json.dumps({"verdict": "PASS", "metrics": {}, "issues": []}),
                encoding="utf-8",
            )
            return 0
        if "run_with_timeout.py" in " ".join(argv):
            nonlocal scheduler_extra_env
            scheduler_extra_env = dict(extra_env) if extra_env else None
            return mod.TIMEOUT_EXIT
        return 0

    archive = _durable_archive(tmp_path)
    rc = mod.main(
        _base_argv_24h(staging, archive)
        + [
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE_24H),
            "--no-strict-repo-clean",
        ],
        subprocess_runner=_runner,
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc == 0
    assert calls
    timeout_cmd = next(cmd for cmd in calls if "run_with_timeout.py" in cmd)
    assert "--timeout-seconds 86400" in timeout_cmd
    from scripts.ops.scheduler_start_boundary_guard_v0 import (
        SCHEDULER_HOLD_RUNTIME_OUTROOT_ENV,
        SCHEDULER_HOLD_RUNTIME_RUN_ID_ENV,
    )

    expected_outroot = str(APPROVAL_FIXTURE_24H.resolve().parent.parent)
    assert scheduler_extra_env is not None
    assert scheduler_extra_env.get(SCHEDULER_HOLD_RUNTIME_OUTROOT_ENV) == expected_outroot
    assert scheduler_extra_env.get(SCHEDULER_HOLD_RUNTIME_RUN_ID_ENV) == RUN_ID_24H
    start_rc = staging / mod.START_RETURN_CODE_ARTIFACT
    assert start_rc.is_file()
    assert "START_RC=0" in start_rc.read_text(encoding="utf-8")
