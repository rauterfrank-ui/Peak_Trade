"""Tests for Shadow bounded observation retention adapter and review scripts."""

from __future__ import annotations

import importlib.util
import io
import json
import shutil
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Sequence

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
ADAPTER_SCRIPT = ROOT / "scripts" / "ops" / "run_shadow_bounded_observation_adapter_v0.py"
REVIEW_SCRIPT = ROOT / "scripts" / "ops" / "review_shadow_bounded_observation_evidence_v0.py"
APPROVAL_FIXTURE = ROOT / "tests" / "fixtures" / "ops" / "shadow_adapter_stage3_approval_sample.md"
APPROVAL_FIXTURE_24H = (
    ROOT / "tests" / "fixtures" / "ops" / "daemon_paper_shadow_24h_adapter_approval_sample.md"
)
RUN_ID_24H = "daemon_paper_24h_20260524T093549Z"
PROFILE_24H = "daemon_paper_shadow_24h_v0"
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")


def _load_module(script: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, script)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_adapter():
    return _load_module(ADAPTER_SCRIPT, "run_shadow_bounded_observation_adapter_v0")


def _load_review():
    return _load_module(REVIEW_SCRIPT, "review_shadow_bounded_observation_evidence_v0")


def _staging(tmp_path: Path) -> Path:
    return Path("/tmp") / f"peak_trade_shadow_staging_test_{tmp_path.name}"


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
    path = ROOT / "tests" / ".pytest_archive_roots" / tmp_path.name
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_wrapper_bundle(staging: Path) -> None:
    evidence = staging / "wrapper_evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "SHADOW_247_FUTURES_BOUNDED_SHADOW_DRY_RUN.md").write_text(
        "\n".join(
            [
                "# Bounded Shadow Dry Run",
                "NO_BROKER",
                "NO_NETWORK",
                "NO_ORDER_SUBMISSION",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence / "steps.jsonl").write_text('{"step": 1}\n', encoding="utf-8")
    (evidence / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "shadow_247_futures_bounded_shadow_dry_run.v0",
                "NO_BROKER": True,
                "NO_NETWORK": True,
                "NO_ORDER_SUBMISSION": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    logs = staging / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "wrapper_stdout.log").write_text("wrapper stdout\n", encoding="utf-8")
    (logs / "wrapper_stderr.log").write_text("wrapper stderr\n", encoding="utf-8")


@pytest.fixture(autouse=True)
def _cleanup_durable_archive_dirs():
    yield
    archive_roots = ROOT / "tests" / ".pytest_archive_roots"
    if archive_roots.is_dir():
        shutil.rmtree(archive_roots, ignore_errors=True)


def _plan_dict(staging: Path, archive: Path | None = None) -> dict:
    mod = _load_adapter()
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.main(_base_argv(staging, archive) + ["--json"])
    assert rc == 0, buf.getvalue()
    return json.loads(buf.getvalue())


def test_adapter_script_exists() -> None:
    assert ADAPTER_SCRIPT.is_file()


def test_review_script_exists() -> None:
    assert REVIEW_SCRIPT.is_file()


def test_adapter_help_works() -> None:
    proc = subprocess.run(
        [sys.executable, str(ADAPTER_SCRIPT), "--help"],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "plan-only" in proc.stdout.lower() or "plan only" in proc.stdout.lower()


def test_plan_only_default_does_not_call_subprocess(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    called = {"count": 0}

    def _runner(*_args, **_kwargs) -> int:
        called["count"] += 1
        return 0

    rc = mod.main(_base_argv(staging), subprocess_runner=_runner)
    assert rc == 0
    assert called["count"] == 0


def test_plan_only_emits_wrapper_allowlist(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    joined = json.dumps(plan["commands"]).lower()
    assert "bounded-shadow-dry-run" in joined
    assert plan["wrapper_mode"] == "bounded-shadow-dry-run"


def test_default_duration_minutes_is_10(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    assert plan["duration_minutes"] == 10


def test_plan_includes_retention_steps(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    joined = " ".join(plan["retention_steps"]).lower()
    assert "manifest.sha256" in joined
    assert "verify" in joined


def test_plan_archive_dest_is_runs_shadow(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    joined = " ".join(plan["retention_steps"])
    assert "runs/shadow/" in joined


def test_execute_without_approval_record_fails(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    rc = mod.main(
        _base_argv(staging) + ["--execute", "--no-strict-repo-clean"],
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0


def test_execute_without_archive_root_fails(tmp_path: Path) -> None:
    mod = _load_adapter()
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
    mod = _load_adapter()
    staging = _staging(tmp_path)
    bad = tmp_path / "bad_approval.md"
    bad.write_text("APPROVE_EXECUTE_SHADOW_BOUNDED_DRY_RUN_NOW=false\n", encoding="utf-8")
    rc = mod.main(
        _base_argv(staging)
        + ["--execute", "--approval-record", str(bad), "--no-strict-repo-clean"],
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0


def test_execute_rejects_start_shadow_now_true(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    bad = tmp_path / "shadow_approval.md"
    bad.write_text(
        "\n".join(
            [
                "APPROVE_EXECUTE_SHADOW_BOUNDED_DRY_RUN_NOW=true",
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
    mod = _load_adapter()
    staging = _staging(tmp_path)
    bad = tmp_path / "testnet_approval.md"
    bad.write_text(
        "\n".join(
            [
                "APPROVE_EXECUTE_SHADOW_BOUNDED_DRY_RUN_NOW=true",
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
    mod = _load_adapter()
    staging = _staging(tmp_path)
    bad = tmp_path / "live_approval.md"
    bad.write_text(
        "\n".join(
            [
                "APPROVE_EXECUTE_SHADOW_BOUNDED_DRY_RUN_NOW=true",
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


def test_execute_rejects_start_paper_now_true(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    bad = tmp_path / "paper_approval.md"
    bad.write_text(
        "\n".join(
            [
                "APPROVE_EXECUTE_SHADOW_BOUNDED_DRY_RUN_NOW=true",
                "START_PAPER_NOW=true",
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
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    calls: list[str] = []

    def _runner(argv: Sequence[str], _cwd, stdout_path, stderr_path) -> int:
        joined = " ".join(argv)
        calls.append(joined)
        if "shadow_247_futures_start_wrapper_skeleton_v0.py" in joined:
            _write_wrapper_bundle(staging)
            if stdout_path is not None:
                stdout_path.write_text("mock wrapper stdout\n", encoding="utf-8")
            if stderr_path is not None:
                stderr_path.write_text("mock wrapper stderr\n", encoding="utf-8")
            return 0
        if "review_shadow_bounded_observation_evidence_v0.py" in joined:
            review_mod = _load_review()
            result = review_mod.review_evidence(staging)
            if stdout_path is not None:
                stdout_path.parent.mkdir(parents=True, exist_ok=True)
                stdout_path.write_text(
                    json.dumps(result, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
            return 0 if result["verdict"] == review_mod.PASS else 1
        return 0

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
    archive_dest = archive / "runs" / "shadow"
    run_dirs = list(archive_dest.iterdir())
    assert run_dirs
    copied = run_dirs[0]
    assert (copied / "MANIFEST.sha256").is_file()
    ok, reason = mod.verify_manifest_sha256(copied)
    assert ok, reason
    assert (copied / "review" / "REVIEW_RESULT.json").is_file()


def test_command_plan_never_uses_scheduler_or_shadow_loop(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    blob = json.dumps(plan["commands"]).lower()
    assert "run_shadow_loop" not in blob
    assert "run_scheduler.py" not in blob
    assert "testnet" not in blob
    assert "bounded_pilot" not in blob


def test_archive_retention_steps_include_checksum_manifest(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    joined = " ".join(plan["retention_steps"]).lower()
    assert "manifest.sha256" in joined


def test_staging_root_is_under_tmp(tmp_path: Path) -> None:
    staging = _staging(tmp_path)
    plan = _plan_dict(staging)
    assert "/tmp" in plan["staging_root"] or plan["staging_root"].startswith("/tmp")


def test_execute_rejects_tmp_archive_root(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    tmp_archive = Path("/tmp/peak_trade_shadow_adapter_reject_archive_test")
    tmp_archive.mkdir(parents=True, exist_ok=True)
    issues = mod.validate_execute_preconditions(
        mod.ExecuteContext(
            args=type(
                "Args",
                (),
                {"approval_record": APPROVAL_FIXTURE, "strict_repo_clean": False},
            )(),
            repo_root=ROOT,
            staging_root=staging,
            archive_root=tmp_archive,
            wrapper_evidence=staging / "wrapper_evidence",
            logs_dir=staging / "logs",
            plan_dir=staging / "plan",
            review_dir=staging / "review",
            run_id="test_run",
        ),
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert any("outside /tmp" in issue for issue in issues)


def test_durable_archive_root_outside_tmp_in_execute_mode(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    issues = mod.validate_execute_preconditions(
        mod.ExecuteContext(
            args=type(
                "Args",
                (),
                {"approval_record": APPROVAL_FIXTURE, "strict_repo_clean": False},
            )(),
            repo_root=ROOT,
            staging_root=staging,
            archive_root=archive,
            wrapper_evidence=staging / "wrapper_evidence",
            logs_dir=staging / "logs",
            plan_dir=staging / "plan",
            review_dir=staging / "review",
            run_id="test_run",
        ),
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert not issues


def test_json_output_parseable(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    assert isinstance(plan, dict)
    assert "commands" in plan


def test_wrapper_script_constant_matches_allowlist() -> None:
    mod = _load_adapter()
    assert mod.WRAPPER_SCRIPT == "scripts/ops/shadow_247_futures_start_wrapper_skeleton_v0.py"


def test_validate_env_guardrails_blocks_live() -> None:
    mod = _load_adapter()
    issues = mod.validate_env_guardrails({"PT_LIVE_ENABLED": "true"})
    assert issues


def test_module_build_plan_forbidden_paths_absent(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    plan = mod.build_plan(
        mode="plan-only",
        staging_root=staging,
        archive_root=ARCHIVE_ROOT,
        repo_root=ROOT,
        duration_minutes=10,
        max_steps=120,
        step_interval_seconds=0.0,
        run_id="test_run",
    )
    assert plan.forbidden_paths_absent is True


def test_verify_manifest_sha256_detects_mismatch(tmp_path: Path) -> None:
    mod = _load_adapter()
    root = tmp_path / "bundle"
    root.mkdir()
    payload = root / "data.txt"
    payload.write_text("hello\n", encoding="utf-8")
    (root / "MANIFEST.sha256").write_text("deadbeef  data.txt\n", encoding="utf-8")
    ok, reason = mod.verify_manifest_sha256(root)
    assert not ok
    assert "checksum mismatch" in reason


def test_review_passes_complete_fixture(tmp_path: Path) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_wrapper_bundle(staging)
    result = review.review_evidence(staging)
    assert result["verdict"] == review.PASS


def test_review_fails_missing_steps_jsonl(tmp_path: Path) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_wrapper_bundle(staging)
    (staging / "wrapper_evidence" / "steps.jsonl").unlink()
    result = review.review_evidence(staging)
    assert result["verdict"] == review.REVIEW_REQUIRED


def test_review_fails_missing_markdown_artifact(tmp_path: Path) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_wrapper_bundle(staging)
    (staging / "wrapper_evidence" / "SHADOW_247_FUTURES_BOUNDED_SHADOW_DRY_RUN.md").unlink()
    result = review.review_evidence(staging)
    assert result["verdict"] == review.REVIEW_REQUIRED


def test_review_fails_invalid_manifest_schema(tmp_path: Path) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_wrapper_bundle(staging)
    (staging / "wrapper_evidence" / "manifest.json").write_text(
        json.dumps({"schema": "wrong.schema.v0"}) + "\n",
        encoding="utf-8",
    )
    result = review.review_evidence(staging)
    assert result["verdict"] == review.REVIEW_REQUIRED


def test_review_fails_missing_manifest_schema(tmp_path: Path) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_wrapper_bundle(staging)
    manifest_path = staging / "wrapper_evidence" / "manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload.pop("schema", None)
    manifest_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    result = review.review_evidence(staging)
    assert result["verdict"] == review.REVIEW_REQUIRED
    assert any("schema must be" in issue for issue in result["issues"])


def test_review_fails_missing_safety_boundary_strings(tmp_path: Path) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_wrapper_bundle(staging)
    md_path = staging / "wrapper_evidence" / "SHADOW_247_FUTURES_BOUNDED_SHADOW_DRY_RUN.md"
    md_path.write_text("# Bounded Shadow Dry Run\n", encoding="utf-8")
    manifest_path = staging / "wrapper_evidence" / "manifest.json"
    manifest_path.write_text(
        json.dumps({"schema": "shadow_247_futures_bounded_shadow_dry_run.v0"}) + "\n",
        encoding="utf-8",
    )
    result = review.review_evidence(staging)
    assert result["verdict"] == review.REVIEW_REQUIRED
    assert any("missing safety boundary strings" in issue for issue in result["issues"])


def test_review_does_not_claim_gate_clearance(tmp_path: Path) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_wrapper_bundle(staging)
    result = review.review_evidence(staging)
    blob = json.dumps(result)
    assert "SHADOW_READY" not in blob
    assert result["non_authorizing"] is True


def test_default_profile_unchanged_still_10_minutes(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    assert plan["duration_minutes"] == 10
    assert plan.get("contract_profile", "") == ""


def test_default_profile_rejects_duration_11(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    rc = mod.main(_base_argv(staging) + ["--duration-minutes", "11"])
    assert rc != 0


def test_24h_profile_plan_only_default_duration_1440(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.main(_base_argv_24h(staging) + ["--json"])
    assert rc == 0, buf.getvalue()
    plan = json.loads(buf.getvalue())
    assert plan["duration_minutes"] == 1440
    assert plan["contract_profile"] == PROFILE_24H
    assert plan["run_id"] == RUN_ID_24H


def test_24h_profile_plan_includes_candidate_24h_wrapper_flags(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.main(_base_argv_24h(staging) + ["--json"])
    assert rc == 0
    plan = json.loads(buf.getvalue())
    joined = json.dumps(plan["commands"]).lower()
    assert "candidate-24h-bounded-shadow-validation" in joined
    assert "candidate-24h-confirm-token" in joined


def test_24h_profile_rejects_10_minutes_explicit(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    rc = mod.main(_base_argv_24h(staging) + ["--duration-minutes", "10"])
    assert rc != 0


def test_24h_profile_requires_run_id(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    rc = mod.main(_base_argv(staging) + ["--profile", PROFILE_24H])
    assert rc != 0


def test_unknown_profile_rejected(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    rc = mod.main(_base_argv(staging) + ["--profile", "unknown_profile_v0"])
    assert rc != 0


def test_24h_profile_execute_rejects_shadow_only_approval_fixture(tmp_path: Path) -> None:
    mod = _load_adapter()
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


def test_24h_profile_execute_rejects_120min_paper_approval_fixture(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    paper_fixture = (
        ROOT / "tests" / "fixtures" / "ops" / "paper_only_adapter_stage3_approval_sample.md"
    )
    rc = mod.main(
        _base_argv_24h(staging, archive)
        + [
            "--execute",
            "--approval-record",
            str(paper_fixture),
            "--no-strict-repo-clean",
        ],
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0


def test_24h_profile_execute_rejects_run_id_mismatch(tmp_path: Path) -> None:
    mod = _load_adapter()
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
    mod = _load_adapter()
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
    mod = _load_adapter()
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


def test_24h_profile_execute_accepts_shared_fixture_mocked(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    calls: list[str] = []

    def _runner(argv: Sequence[str], _cwd, stdout_path, stderr_path) -> int:
        joined = " ".join(argv)
        calls.append(joined)
        if "shadow_247_futures_start_wrapper_skeleton_v0.py" in joined:
            assert "candidate-24h-bounded-shadow-validation" in joined
            assert "--duration-minutes 1440" in joined
            _write_wrapper_bundle(staging)
            if stdout_path is not None:
                stdout_path.write_text("mock wrapper stdout\n", encoding="utf-8")
            if stderr_path is not None:
                stderr_path.write_text("mock wrapper stderr\n", encoding="utf-8")
            return 0
        if "review_shadow_bounded_observation_evidence_v0.py" in joined:
            review_mod = _load_review()
            result = review_mod.review_evidence(staging)
            if stdout_path is not None:
                stdout_path.parent.mkdir(parents=True, exist_ok=True)
                stdout_path.write_text(
                    json.dumps(result, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
            return 0 if result["verdict"] == review_mod.PASS else 1
        return 0

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


def test_review_json_output_parseable(tmp_path: Path) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_wrapper_bundle(staging)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = review.main(["--staging-root", str(staging), "--json"])
    assert rc == 0
    payload = json.loads(buf.getvalue())
    assert payload["verdict"] == review.PASS
