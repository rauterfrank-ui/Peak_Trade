"""Tests for Testnet bounded observation retention adapter and review scripts."""

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
ADAPTER_SCRIPT = ROOT / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py"
REVIEW_SCRIPT = ROOT / "scripts" / "ops" / "review_testnet_bounded_observation_evidence_v0.py"
STAGING_SCRIPT = ROOT / "scripts" / "ops" / "run_testnet_bounded_evidence_staging_v0.sh"
APPROVAL_FIXTURE = ROOT / "tests" / "fixtures" / "ops" / "testnet_adapter_stage3_approval_sample.md"
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")


def _load_module(script: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, script)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_adapter():
    return _load_module(ADAPTER_SCRIPT, "run_testnet_bounded_observation_adapter_v0")


def _load_review():
    return _load_module(REVIEW_SCRIPT, "review_testnet_bounded_observation_evidence_v0")


def _staging(tmp_path: Path) -> Path:
    return Path("/tmp") / f"peak_trade_testnet_staging_test_{tmp_path.name}"


def _durable_archive(tmp_path: Path) -> Path:
    path = ROOT / "tests" / ".pytest_archive_roots" / tmp_path.name
    path.mkdir(parents=True, exist_ok=True)
    return path


def _base_argv(staging: Path, archive: Path | None = None) -> list[str]:
    return [
        "--staging-root",
        str(staging),
        "--archive-root",
        str(archive or ARCHIVE_ROOT),
        "--repo-root",
        str(ROOT),
        "--run-id",
        "testnet_bounded_observation_test_run",
    ]


def _write_wrapper_bundle(staging: Path) -> None:
    evidence = staging / "wrapper_evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "TESTNET_BOUNDED_OBSERVATION.md").write_text(
        "\n".join(
            [
                "# Bounded Testnet Observation",
                "TESTNET_SANDBOX_ONLY",
                "NO_PRODUCTION_FALLBACK",
                "NO_LIVE_ORDER_SUBMISSION",
                "docs/ops/specs/FUTURES_TESTNET_DRY_RUN_PROOF_CONTRACT_V0.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence / "steps.jsonl").write_text('{"step": 1}\n', encoding="utf-8")
    (evidence / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "testnet_bounded_dry_run.v0",
                "TESTNET_SANDBOX_ONLY": True,
                "NO_PRODUCTION_FALLBACK": True,
                "NO_LIVE_ORDER_SUBMISSION": True,
                "broker_connected": False,
                "production_fallback": False,
                "proof_contract_doc": "docs/ops/specs/FUTURES_TESTNET_DRY_RUN_PROOF_CONTRACT_V0.md",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    logs = staging / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "wrapper_stdout.log").write_text("stdout\n", encoding="utf-8")
    (logs / "wrapper_stderr.log").write_text("stderr\n", encoding="utf-8")


@pytest.fixture(autouse=True)
def _cleanup_durable_archive_dirs():
    yield
    archive_roots = ROOT / "tests" / ".pytest_archive_roots"
    if archive_roots.is_dir():
        shutil.rmtree(archive_roots, ignore_errors=True)
    for path in Path("/tmp").glob("peak_trade_testnet_staging_test_*"):
        shutil.rmtree(path, ignore_errors=True)


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


def test_staging_shell_exists() -> None:
    assert STAGING_SCRIPT.is_file()


def test_adapter_help_works() -> None:
    proc = subprocess.run(
        [sys.executable, str(ADAPTER_SCRIPT), "--help"],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0


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


def test_plan_archive_dest_is_runs_testnet(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    joined = " ".join(plan["retention_steps"])
    assert "runs/testnet/" in joined


def test_execute_without_approval_record_fails(tmp_path: Path) -> None:
    mod = _load_adapter()
    rc = mod.main(
        _base_argv(_staging(tmp_path)) + ["--execute", "--no-strict-repo-clean"],
        prerequisite_checker=lambda _root: (True, ""),
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0


def test_execute_with_missing_approval_token_fails(tmp_path: Path) -> None:
    mod = _load_adapter()
    bad = tmp_path / "bad.md"
    bad.write_text("APPROVE_EXECUTE_TESTNET_BOUNDED_OBSERVATION_NOW=false\n", encoding="utf-8")
    rc = mod.main(
        _base_argv(_staging(tmp_path))
        + [
            "--execute",
            "--approval-record",
            str(bad),
            "--no-strict-repo-clean",
        ],
        prerequisite_checker=lambda _root: (True, ""),
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0


def test_execute_rejects_start_testnet_now_true(tmp_path: Path) -> None:
    mod = _load_adapter()
    bad = tmp_path / "bad.md"
    bad.write_text(
        "\n".join(
            [
                "APPROVE_EXECUTE_TESTNET_BOUNDED_OBSERVATION_NOW=true",
                "START_TESTNET_NOW=true",
            ]
        ),
        encoding="utf-8",
    )
    rc = mod.main(
        _base_argv(_staging(tmp_path))
        + ["--execute", "--approval-record", str(bad), "--no-strict-repo-clean"],
        prerequisite_checker=lambda _root: (True, ""),
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0


def test_missing_credentials_fail_before_staging_subprocess(tmp_path: Path) -> None:
    mod = _load_adapter()
    called = {"count": 0}

    def _runner(*_args, **_kwargs) -> int:
        called["count"] += 1
        return 0

    rc = mod.main(
        _base_argv(_staging(tmp_path))
        + [
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE),
            "--no-strict-repo-clean",
        ],
        subprocess_runner=_runner,
        repo_clean_checker=lambda _root: (True, ""),
        environ={},
    )
    assert rc != 0
    assert called["count"] == 0


def test_execute_accepts_sample_approval_with_mocked_runner(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)

    def _runner(argv: Sequence[str], _cwd, stdout_path, stderr_path) -> int:
        joined = " ".join(argv)
        if "run_testnet_bounded_evidence_staging_v0.sh" in joined:
            _write_wrapper_bundle(staging)
            if stdout_path is not None:
                stdout_path.write_text("mock\n", encoding="utf-8")
            if stderr_path is not None:
                stderr_path.write_text("mock\n", encoding="utf-8")
            return 0
        if "review_testnet_bounded_observation_evidence_v0.py" in joined:
            review_mod = _load_review()
            result = review_mod.review_evidence(staging)
            if stdout_path is not None:
                stdout_path.parent.mkdir(parents=True, exist_ok=True)
                stdout_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
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
        prerequisite_checker=lambda _root: (True, ""),
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc == 0
    run_dirs = list((archive / "runs" / "testnet").iterdir())
    assert run_dirs
    copied = run_dirs[0]
    assert (copied / "MANIFEST.sha256").is_file()
    ok, reason = mod.verify_manifest_sha256(copied)
    assert ok, reason


def test_mocked_review_required_fails_closed_no_archive(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)

    def _runner(argv: Sequence[str], _cwd, stdout_path, stderr_path) -> int:
        joined = " ".join(argv)
        if "run_testnet_bounded_evidence_staging_v0.sh" in joined:
            evidence = staging / "wrapper_evidence"
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / "TESTNET_BOUNDED_OBSERVATION.md").write_text(
                "incomplete\n", encoding="utf-8"
            )
            return 0
        if "review_testnet_bounded_observation_evidence_v0.py" in joined:
            if stdout_path is not None:
                stdout_path.parent.mkdir(parents=True, exist_ok=True)
                stdout_path.write_text(
                    json.dumps({"verdict": "REVIEW_REQUIRED"}) + "\n",
                    encoding="utf-8",
                )
            return 1
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
        prerequisite_checker=lambda _root: (True, ""),
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0
    assert not (archive / "runs" / "testnet" / "testnet_bounded_observation_test_run").exists()


def test_review_fails_missing_schema(tmp_path: Path) -> None:
    review_mod = _load_review()
    staging = _staging(tmp_path)
    _write_wrapper_bundle(staging)
    bad_manifest = staging / "wrapper_evidence" / "manifest.json"
    bad_manifest.write_text('{"schema": "wrong.v0"}\n', encoding="utf-8")
    result = review_mod.review_evidence(staging)
    assert result["verdict"] == review_mod.REVIEW_REQUIRED


def test_review_fails_missing_safety_markers(tmp_path: Path) -> None:
    review_mod = _load_review()
    staging = _staging(tmp_path)
    evidence = staging / "wrapper_evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "TESTNET_BOUNDED_OBSERVATION.md").write_text("no markers\n", encoding="utf-8")
    (evidence / "steps.jsonl").write_text("{}\n", encoding="utf-8")
    (evidence / "manifest.json").write_text(
        '{"schema": "testnet_bounded_dry_run.v0"}\n', encoding="utf-8"
    )
    staging.mkdir(parents=True, exist_ok=True)
    logs = staging / "logs"
    logs.mkdir(exist_ok=True)
    (logs / "wrapper_stdout.log").write_text("x\n", encoding="utf-8")
    (logs / "wrapper_stderr.log").write_text("x\n", encoding="utf-8")
    result = review_mod.review_evidence(staging)
    assert result["verdict"] == review_mod.REVIEW_REQUIRED


def test_staging_shell_static_contract_excludes_orchestrator() -> None:
    text = STAGING_SCRIPT.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "orchestrate_testnet_runs" not in lowered
    assert "run_testnet_evidence_flow" not in lowered
    assert "live_allowed" not in lowered


def test_command_plan_never_uses_forbidden_paths(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    blob = json.dumps(plan["commands"]).lower()
    assert "orchestrate_testnet_runs" not in blob
    assert "run_testnet_evidence_flow" not in blob
    assert "run_scheduler.py" not in blob
    assert plan["forbidden_paths_absent"] is True


def test_adapter_plan_no_live_authorization_escalation(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    rendered = json.dumps(plan).lower()
    assert "live_allowed=true" not in rendered
    assert "testnet_authorized=true" not in rendered


def test_strict_repo_clean_blocks_execute(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    rc = mod.main(
        _base_argv(staging)
        + [
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE),
        ],
        prerequisite_checker=lambda _root: (True, ""),
        repo_clean_checker=lambda _root: (False, "dirty"),
    )
    assert rc != 0


def test_prerequisite_checker_output_has_no_secret_values() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/ops/check_testnet_prerequisites_readonly.py"),
            "--json",
        ],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["prerequisites"][0]["value_redacted"] is True
    assert "PEAK_TRADE_TESTNET_OPERATOR_GATE_ACK=" not in proc.stdout
