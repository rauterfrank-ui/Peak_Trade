"""Tests for Testnet bounded observation retention adapter and review scripts."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Mapping, Sequence
from unittest.mock import patch

import pytest

from src.ops.wallclock_session_evidence_v0 import (
    WALLCLOCK_EVIDENCE_FILENAME,
    evaluate_wallclock_evidence_fields,
)
from src.ops.bounded_testnet_market_input_admission_wiring_v0 import (
    REPO_GROUNDED_ETH_PERP_SELECTED_FUTURE_ID,
    REPO_GROUNDED_ETH_PERP_VENUE_SYMBOL,
    BoundedTestnetFuturesMarketObservationV0,
    BoundedTestnetFuturesMarketPriceTickObservationV0,
)
from src.ops.bounded_testnet_runtime_market_observation_producer_v0 import (
    BoundedTestnetRuntimeClockV0,
    build_canonical_testnet_public_ticker_url,
)
from trading.master_v2.double_play_futures_input import (
    FuturesFreshnessState,
    FuturesMarketType,
)

ROOT = Path(__file__).resolve().parent.parent.parent
ADAPTER_SCRIPT = ROOT / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py"
REVIEW_SCRIPT = ROOT / "scripts" / "ops" / "review_testnet_bounded_observation_evidence_v0.py"
STAGING_SCRIPT = ROOT / "scripts" / "ops" / "run_testnet_bounded_evidence_staging_v0.sh"
APPROVAL_FIXTURE = ROOT / "tests" / "fixtures" / "ops" / "testnet_adapter_stage3_approval_sample.md"
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
SELECTOR = ROOT / "scripts" / "ops" / "ci_test_selection_v1.py"
CLOSEOUT_BINDING_FILES = (
    "scripts/ops/run_testnet_bounded_observation_adapter_v0.py",
    "tests/ops/test_run_testnet_bounded_observation_adapter_v0.py",
    "scripts/ops/ci_test_selection_v1.py",
)
CLOSEOUT_BINDING_ASSERTION_ONLY_FILES = (
    "tests/ops/test_run_testnet_bounded_observation_adapter_v0.py",
    "scripts/ops/ci_test_selection_v1.py",
)
RUNTIME_PRODUCER_FILES = (
    "src/ops/bounded_testnet_runtime_market_observation_producer_v0.py",
    "tests/ops/test_bounded_testnet_runtime_market_observation_producer_v0.py",
    "scripts/ops/run_testnet_bounded_observation_adapter_v0.py",
    "tests/ops/test_run_testnet_bounded_observation_adapter_v0.py",
    "scripts/ops/ci_test_selection_v1.py",
)


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


def _tmp_path_namespace(tmp_path: Path) -> str:
    digest = hashlib.sha256(str(tmp_path.resolve()).encode()).hexdigest()[:12]
    return f"{tmp_path.name}_{digest}"


_test_owned_paths: list[Path] = []


def _register_test_owned_path(path: Path) -> None:
    resolved = path.resolve()
    if resolved not in _test_owned_paths:
        _test_owned_paths.append(resolved)


def _staging(tmp_path: Path, *, tag: str = "") -> Path:
    suffix = f"_{tag}" if tag else ""
    path = Path("/tmp") / f"peak_trade_testnet_staging_test_{_tmp_path_namespace(tmp_path)}{suffix}"
    _register_test_owned_path(path)
    return path


WALLCLOCK_FIELD_NAMES = (
    "utc_started",
    "utc_completed",
    "duration_minutes_requested",
    "start_monotonic_seconds",
    "end_monotonic_seconds",
)


def _injected_wallclock_env(
    *,
    duration_minutes: int = 10,
    start_iso: str = "2026-06-22T10:00:00Z",
) -> dict[str, str]:
    planned_seconds = duration_minutes * 60
    start_dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
    end_dt = start_dt + timedelta(seconds=planned_seconds + 1)
    end_iso = end_dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    start_mono = 1000.0
    end_mono = start_mono + planned_seconds + 1.0
    return {
        "PEAK_TRADE_BOUNDED_TESTNET_STAGING_UTC_STARTED": start_iso,
        "PEAK_TRADE_BOUNDED_TESTNET_STAGING_UTC_COMPLETED": end_iso,
        "PEAK_TRADE_BOUNDED_TESTNET_STAGING_START_MONOTONIC_SECONDS": str(start_mono),
        "PEAK_TRADE_BOUNDED_TESTNET_STAGING_END_MONOTONIC_SECONDS": str(end_mono),
    }


def _stub_sleep_env() -> dict[str, str]:
    return {"PEAK_TRADE_BOUNDED_TESTNET_STAGING_STUB_SLEEP": "1"}


def _run_staging_shell(
    staging: Path,
    *,
    duration_minutes: int = 10,
    max_steps: int = 120,
    step_interval_seconds: float = 5.0,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged = {**os.environ, **(env or {})}
    return subprocess.run(
        [
            "/bin/bash",
            str(STAGING_SCRIPT),
            "--staging-root",
            str(staging),
            "--run-id",
            "testnet_bounded_observation_test_run",
            "--duration-minutes",
            str(duration_minutes),
            "--max-steps",
            str(max_steps),
            "--step-interval-seconds",
            str(step_interval_seconds),
        ],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
        env=merged,
    )


def _load_shell_manifest(staging: Path) -> dict[str, object]:
    manifest_path = staging / "wrapper_evidence" / "manifest.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _durable_archive(tmp_path: Path, *, tag: str = "") -> Path:
    suffix = f"_{tag}" if tag else ""
    path = ROOT / "tests" / ".pytest_archive_roots" / f"{_tmp_path_namespace(tmp_path)}{suffix}"
    path.mkdir(parents=True, exist_ok=True)
    _register_test_owned_path(path)
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


def _passing_wrapper_manifest_fields(
    *,
    duration_minutes: int = 10,
    start_iso: str = "2026-06-22T10:00:00Z",
    end_iso: str | None = None,
    start_monotonic_seconds: float = 1000.0,
    end_monotonic_seconds: float | None = None,
) -> dict[str, object]:
    planned_seconds = duration_minutes * 60
    if end_iso is None:
        from datetime import datetime, timedelta, timezone

        start_dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        end_dt = start_dt + timedelta(seconds=planned_seconds + 1)
        end_iso = end_dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    if end_monotonic_seconds is None:
        end_monotonic_seconds = start_monotonic_seconds + planned_seconds + 1.0
    return {
        "duration_minutes_requested": duration_minutes,
        "utc_started": start_iso,
        "utc_completed": end_iso,
        "start_monotonic_seconds": start_monotonic_seconds,
        "end_monotonic_seconds": end_monotonic_seconds,
        "elapsed_monotonic_seconds": round(end_monotonic_seconds - start_monotonic_seconds, 6),
        "step_interval_seconds": 5.0,
    }


def _write_wrapper_bundle(
    staging: Path,
    *,
    manifest_overrides: dict[str, object] | None = None,
    duration_minutes: int = 10,
) -> None:
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
                **_passing_wrapper_manifest_fields(duration_minutes=duration_minutes),
                **(manifest_overrides or {}),
            },
            indent=2,
            sort_keys=True,
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
    _test_owned_paths.clear()
    yield
    for path in reversed(_test_owned_paths):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
    _test_owned_paths.clear()


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
    assert (staging / WALLCLOCK_EVIDENCE_FILENAME).is_file()
    wallclock = json.loads((staging / WALLCLOCK_EVIDENCE_FILENAME).read_text(encoding="utf-8"))
    assert wallclock["duration_evidence_valid"] is True
    assert wallclock["duration_proven"] is True
    assert wallclock["planned_duration_seconds"] == 600
    metadata = json.loads((staging / "RUN_METADATA.json").read_text(encoding="utf-8"))
    assert metadata["wallclock_duration_proven"] is True


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


def _mock_execute_runner(staging: Path):
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

    return _runner


def _runner_with_overrides(staging: Path, manifest_overrides: dict[str, object]):
    def _runner(argv: Sequence[str], _cwd, stdout_path, stderr_path) -> int:
        joined = " ".join(argv)
        if "run_testnet_bounded_evidence_staging_v0.sh" in joined:
            _write_wrapper_bundle(staging, manifest_overrides=manifest_overrides)
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

    return _runner


def test_plan_lists_wallclock_evidence_artifact(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    assert WALLCLOCK_EVIDENCE_FILENAME in plan["expected_artifacts"]


def test_execute_emits_wallclock_evidence_pass_standard_tier(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    rc = mod.main(
        _base_argv(staging, archive)
        + [
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE),
            "--no-strict-repo-clean",
        ],
        subprocess_runner=_mock_execute_runner(staging),
        prerequisite_checker=lambda _root: (True, ""),
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc == 0
    payload = json.loads((staging / WALLCLOCK_EVIDENCE_FILENAME).read_text(encoding="utf-8"))
    evaluation = evaluate_wallclock_evidence_fields(payload)
    assert evaluation["duration_evidence_valid"] is True
    assert payload["evidence_source"] == mod.TESTNET_BOUNDED_EVIDENCE_SOURCE


def test_execute_fast_sim_false_claim_fails_closed(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path) / "fast_sim"
    archive = _durable_archive(tmp_path)
    overrides = _passing_wrapper_manifest_fields(
        duration_minutes=10,
        end_iso="2026-06-22T10:00:05Z",
        end_monotonic_seconds=1005.0,
    )
    rc = mod.main(
        _base_argv(staging, archive)
        + [
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE),
            "--no-strict-repo-clean",
        ],
        subprocess_runner=_runner_with_overrides(staging, overrides),
        prerequisite_checker=lambda _root: (True, ""),
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0
    assert not (staging / "CLOSEOUT.md").is_file()


@pytest.mark.parametrize(
    "manifest_overrides",
    [
        {"start_monotonic_seconds": None},
        {"end_monotonic_seconds": None},
        {"utc_started": ""},
        {"utc_completed": ""},
    ],
)
def test_execute_missing_wallclock_inputs_fail_closed(
    tmp_path: Path,
    manifest_overrides: dict[str, object],
) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path) / "missing"
    archive = _durable_archive(tmp_path)
    rc = mod.main(
        _base_argv(staging, archive)
        + [
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE),
            "--no-strict-repo-clean",
        ],
        subprocess_runner=_runner_with_overrides(staging, manifest_overrides),
        prerequisite_checker=lambda _root: (True, ""),
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0
    assert not (staging / "CLOSEOUT.md").is_file()


def test_execute_negative_elapsed_monotonic_fails_closed(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path) / "negative"
    archive = _durable_archive(tmp_path)
    rc = mod.main(
        _base_argv(staging, archive)
        + [
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE),
            "--no-strict-repo-clean",
        ],
        subprocess_runner=_runner_with_overrides(
            staging,
            {"start_monotonic_seconds": 2000.0, "end_monotonic_seconds": 1000.0},
        ),
        prerequisite_checker=lambda _root: (True, ""),
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc != 0


def test_execute_wallclock_writer_failure_fails_closed(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)

    def _failing_writer(_path: Path, _evidence: dict) -> Path:
        raise OSError("simulated wallclock write failure")

    with patch.object(mod, "write_wallclock_evidence", side_effect=_failing_writer):
        rc = mod.main(
            _base_argv(staging, archive)
            + [
                "--execute",
                "--approval-record",
                str(APPROVAL_FIXTURE),
                "--no-strict-repo-clean",
            ],
            subprocess_runner=_mock_execute_runner(staging),
            prerequisite_checker=lambda _root: (True, ""),
            repo_clean_checker=lambda _root: (True, ""),
        )
    assert rc != 0
    assert not (staging / WALLCLOCK_EVIDENCE_FILENAME).is_file()


def test_execute_wallclock_emitter_preserves_closeout_chain(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    rc = mod.main(
        _base_argv(staging, archive)
        + [
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE),
            "--no-strict-repo-clean",
        ],
        subprocess_runner=_mock_execute_runner(staging),
        prerequisite_checker=lambda _root: (True, ""),
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc == 0
    assert (staging / "CLOSEOUT.md").is_file()
    assert (staging / "MANIFEST.sha256").is_file()
    assert (archive / "runs" / "testnet" / "testnet_bounded_observation_test_run").is_dir()


def test_staging_shell_manifest_emits_all_wallclock_fields(tmp_path: Path) -> None:
    staging = _staging(tmp_path)
    proc = _run_staging_shell(staging, env=_injected_wallclock_env(duration_minutes=7))
    assert proc.returncode == 0, proc.stderr
    manifest = _load_shell_manifest(staging)
    for field in WALLCLOCK_FIELD_NAMES:
        assert field in manifest
        assert manifest[field] not in (None, "")


def test_staging_shell_wallclock_fields_are_ordered_and_valid(tmp_path: Path) -> None:
    staging = _staging(tmp_path)
    proc = _run_staging_shell(staging, env=_injected_wallclock_env())
    assert proc.returncode == 0, proc.stderr
    manifest = _load_shell_manifest(staging)
    start_dt = datetime.fromisoformat(str(manifest["utc_started"]).replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(str(manifest["utc_completed"]).replace("Z", "+00:00"))
    assert end_dt >= start_dt
    start_mono = float(manifest["start_monotonic_seconds"])
    end_mono = float(manifest["end_monotonic_seconds"])
    assert end_mono >= start_mono


def test_staging_shell_duration_minutes_requested_matches_cli(tmp_path: Path) -> None:
    staging = _staging(tmp_path)
    proc = _run_staging_shell(
        staging, duration_minutes=8, env=_injected_wallclock_env(duration_minutes=8)
    )
    assert proc.returncode == 0, proc.stderr
    manifest = _load_shell_manifest(staging)
    assert manifest["duration_minutes_requested"] == 8


def test_adapter_emits_wallclock_from_real_shell_manifest_without_mock(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    proc = _run_staging_shell(staging, env=_injected_wallclock_env())
    assert proc.returncode == 0, proc.stderr
    ok, reason, evidence = mod._emit_wallclock_evidence_from_wrapper_manifest(
        staging,
        staging / "wrapper_evidence",
    )
    assert ok, reason
    assert evidence is not None
    assert evidence["duration_evidence_valid"] is True
    assert evidence["duration_proven"] is True


def _real_staging_execute_runner(staging: Path, *, shell_env: Mapping[str, str] | None = None):
    def _runner(argv: Sequence[str], _cwd, stdout_path, stderr_path) -> int:
        joined = " ".join(argv)
        if "run_testnet_bounded_evidence_staging_v0.sh" in joined:
            proc = _run_staging_shell(staging, env=shell_env)
            if stdout_path is not None:
                stdout_path.write_text(proc.stdout or "stdout\n", encoding="utf-8")
            if stderr_path is not None:
                stderr_path.write_text(proc.stderr or "stderr\n", encoding="utf-8")
            return proc.returncode
        if "review_testnet_bounded_observation_evidence_v0.py" in joined:
            review_mod = _load_review()
            result = review_mod.review_evidence(staging)
            if stdout_path is not None:
                stdout_path.parent.mkdir(parents=True, exist_ok=True)
                stdout_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            return 0 if result["verdict"] == review_mod.PASS else 1
        return 0

    return _runner


def test_execute_shell_to_adapter_happy_path_without_manifest_mock(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    rc = mod.main(
        _base_argv(staging, archive)
        + [
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE),
            "--no-strict-repo-clean",
        ],
        subprocess_runner=_real_staging_execute_runner(
            staging,
            shell_env=_injected_wallclock_env(),
        ),
        prerequisite_checker=lambda _root: (True, ""),
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc == 0
    wallclock = json.loads((staging / WALLCLOCK_EVIDENCE_FILENAME).read_text(encoding="utf-8"))
    assert wallclock["duration_evidence_valid"] is True
    manifest = _load_shell_manifest(staging)
    for field in WALLCLOCK_FIELD_NAMES:
        assert field in manifest


@pytest.mark.parametrize("duration_minutes", [0, 11, -1])
def test_staging_shell_invalid_duration_fail_closed(tmp_path: Path, duration_minutes: int) -> None:
    staging = _staging(tmp_path)
    proc = subprocess.run(
        [
            "/bin/bash",
            str(STAGING_SCRIPT),
            "--staging-root",
            str(staging),
            "--duration-minutes",
            str(duration_minutes),
        ],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0


def test_staging_shell_partial_wallclock_override_fail_closed(tmp_path: Path) -> None:
    staging = _staging(tmp_path)
    proc = _run_staging_shell(
        staging,
        env={"PEAK_TRADE_BOUNDED_TESTNET_STAGING_UTC_STARTED": "2026-06-22T10:00:00Z"},
    )
    assert proc.returncode != 0
    assert "partial wallclock override" in proc.stderr


def test_staging_shell_negative_monotonic_elapsed_fail_closed(tmp_path: Path) -> None:
    staging = _staging(tmp_path)
    env = _injected_wallclock_env()
    env["PEAK_TRADE_BOUNDED_TESTNET_STAGING_START_MONOTONIC_SECONDS"] = "2000.0"
    env["PEAK_TRADE_BOUNDED_TESTNET_STAGING_END_MONOTONIC_SECONDS"] = "1000.0"
    proc = _run_staging_shell(staging, env=env)
    assert proc.returncode != 0
    assert "end_monotonic_seconds" in proc.stderr


def test_staging_shell_manifest_write_failure_fail_closed(tmp_path: Path) -> None:
    staging = _staging(tmp_path)
    proc = _run_staging_shell(staging, env=_injected_wallclock_env())
    assert proc.returncode == 0, proc.stderr
    evidence_root = staging / "wrapper_evidence"
    evidence_root.chmod(0o500)
    try:
        retry = _run_staging_shell(staging, env=_injected_wallclock_env())
        assert retry.returncode != 0
        assert "manifest" in retry.stderr.lower()
    finally:
        evidence_root.chmod(0o700)


def test_execute_missing_duration_minutes_requested_in_manifest_fail_closed(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)

    def _runner(argv: Sequence[str], _cwd, stdout_path, stderr_path) -> int:
        joined = " ".join(argv)
        if "run_testnet_bounded_evidence_staging_v0.sh" in joined:
            proc = _run_staging_shell(staging, env=_injected_wallclock_env())
            if proc.returncode != 0:
                return proc.returncode
            manifest_path = staging / "wrapper_evidence" / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.pop("duration_minutes_requested", None)
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            if stdout_path is not None:
                stdout_path.write_text("stdout\n", encoding="utf-8")
            if stderr_path is not None:
                stderr_path.write_text("stderr\n", encoding="utf-8")
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
    assert rc != 0
    assert not (staging / WALLCLOCK_EVIDENCE_FILENAME).is_file()


def test_plan_forwards_step_interval_seconds_to_staging_cmd(tmp_path: Path) -> None:
    plan = _plan_dict(_staging(tmp_path))
    staging_cmd = plan["commands"]["bounded_evidence_staging"]
    assert "--step-interval-seconds" in staging_cmd
    assert staging_cmd[staging_cmd.index("--step-interval-seconds") + 1] == "0.0"


def test_plan_forwards_duration_minutes_and_max_steps_unchanged(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.main(
            _base_argv(staging)
            + [
                "--json",
                "--duration-minutes",
                "8",
                "--max-steps",
                "96",
                "--step-interval-seconds",
                "5.0",
            ]
        )
    assert rc == 0
    plan = json.loads(buf.getvalue())
    staging_cmd = plan["commands"]["bounded_evidence_staging"]
    assert staging_cmd[staging_cmd.index("--duration-minutes") + 1] == "8"
    assert staging_cmd[staging_cmd.index("--max-steps") + 1] == "96"
    assert staging_cmd[staging_cmd.index("--step-interval-seconds") + 1] == "5.0"
    assert plan["duration_minutes"] == 8
    assert plan["max_steps"] == 96
    assert plan["step_interval_seconds"] == 5.0


def test_staging_shell_step_interval_zero_fail_closed(tmp_path: Path) -> None:
    staging = _staging(tmp_path)
    proc = _run_staging_shell(staging, step_interval_seconds=0.0)
    assert proc.returncode != 0
    assert "step-interval-seconds" in proc.stderr


def test_staging_shell_missing_step_interval_fail_closed(tmp_path: Path) -> None:
    staging = _staging(tmp_path)
    proc = subprocess.run(
        [
            "/bin/bash",
            str(STAGING_SCRIPT),
            "--staging-root",
            str(staging),
            "--duration-minutes",
            "10",
            "--max-steps",
            "10",
        ],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "step-interval-seconds" in proc.stderr


def test_staging_shell_bounded_loop_emits_deterministic_steps(tmp_path: Path) -> None:
    staging = _staging(tmp_path)
    proc = _run_staging_shell(
        staging,
        max_steps=5,
        step_interval_seconds=2.0,
        env=_stub_sleep_env(),
    )
    assert proc.returncode == 0, proc.stderr
    manifest = _load_shell_manifest(staging)
    assert manifest["steps_emitted"] == 5
    assert manifest["step_interval_seconds"] == pytest.approx(2.0)
    steps = (
        (staging / "wrapper_evidence" / "steps.jsonl")
        .read_text(encoding="utf-8")
        .strip()
        .split("\n")
    )
    assert len(steps) == 5
    first = json.loads(steps[0])
    assert first["mode"] == "bounded_staging_observation"
    assert first["step"] == 1


def test_staging_shell_duration_cap_limits_steps(tmp_path: Path) -> None:
    staging = _staging(tmp_path)
    proc = _run_staging_shell(
        staging,
        duration_minutes=1,
        max_steps=100,
        step_interval_seconds=30.0,
        env=_stub_sleep_env(),
    )
    assert proc.returncode == 0, proc.stderr
    manifest = _load_shell_manifest(staging)
    assert manifest["steps_emitted"] == 2


def test_staging_shell_max_steps_limits_run(tmp_path: Path) -> None:
    staging = _staging(tmp_path)
    proc = _run_staging_shell(
        staging,
        duration_minutes=10,
        max_steps=3,
        step_interval_seconds=5.0,
        env=_stub_sleep_env(),
    )
    assert proc.returncode == 0, proc.stderr
    manifest = _load_shell_manifest(staging)
    assert manifest["steps_emitted"] == 3


def test_staging_shell_stub_monotonic_produces_coherent_wallclock_fields(tmp_path: Path) -> None:
    staging = _staging(tmp_path)
    proc = _run_staging_shell(
        staging,
        duration_minutes=10,
        max_steps=120,
        step_interval_seconds=5.0,
        env=_stub_sleep_env(),
    )
    assert proc.returncode == 0, proc.stderr
    manifest = _load_shell_manifest(staging)
    start_dt = datetime.fromisoformat(str(manifest["utc_started"]).replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(str(manifest["utc_completed"]).replace("Z", "+00:00"))
    assert end_dt >= start_dt
    start_mono = float(manifest["start_monotonic_seconds"])
    end_mono = float(manifest["end_monotonic_seconds"])
    assert end_mono >= start_mono
    assert end_mono - start_mono == pytest.approx(119 * 5.0, rel=1e-6)


def test_wallclock_r1_accepts_stub_elapsed_at_least_540_seconds(tmp_path: Path) -> None:
    staging = _staging(tmp_path)
    proc = _run_staging_shell(
        staging,
        duration_minutes=10,
        max_steps=120,
        step_interval_seconds=5.0,
        env=_stub_sleep_env(),
    )
    assert proc.returncode == 0, proc.stderr
    mod = _load_adapter()
    ok, reason, evidence = mod._emit_wallclock_evidence_from_wrapper_manifest(
        staging,
        staging / "wrapper_evidence",
    )
    assert ok, reason
    assert evidence is not None
    assert evidence["elapsed_monotonic_seconds"] >= 540
    assert evidence["real_sleep_used"] is True
    evaluation = evaluate_wallclock_evidence_fields(evidence)
    assert evaluation["duration_evidence_valid"] is True


def test_staging_shell_zero_order_network_disabled_unchanged(tmp_path: Path) -> None:
    staging = _staging(tmp_path)
    proc = _run_staging_shell(staging, env=_stub_sleep_env())
    assert proc.returncode == 0, proc.stderr
    manifest = _load_shell_manifest(staging)
    assert manifest["broker_connected"] is False
    assert manifest["production_fallback"] is False
    assert manifest["dry_run_only"] is True
    assert manifest["TESTNET_SANDBOX_ONLY"] is True
    text = (staging / "wrapper_evidence" / "TESTNET_BOUNDED_OBSERVATION.md").read_text(
        encoding="utf-8"
    )
    assert "NO_LIVE_ORDER_SUBMISSION" in text
    lowered = STAGING_SCRIPT.read_text(encoding="utf-8").lower()
    assert "curl" not in lowered
    assert "wget" not in lowered


def _valid_market_price_tick(
    *,
    tick_index: int = 0,
    timestamp_ms: int = 1_700_000_000_000,
    mark_price: float = 2500.0,
    sequence: int = 1,
) -> BoundedTestnetFuturesMarketPriceTickObservationV0:
    return BoundedTestnetFuturesMarketPriceTickObservationV0(
        tick_index=tick_index,
        timestamp_ms=timestamp_ms,
        mark_price=mark_price,
        sequence=sequence,
    )


def _valid_market_observation(
    *,
    price_ticks: tuple[BoundedTestnetFuturesMarketPriceTickObservationV0, ...] | None = None,
    **overrides: object,
) -> BoundedTestnetFuturesMarketObservationV0:
    ticks = price_ticks or (_valid_market_price_tick(),)
    base = {
        "selected_future_id": REPO_GROUNDED_ETH_PERP_SELECTED_FUTURE_ID,
        "venue_symbol": REPO_GROUNDED_ETH_PERP_VENUE_SYMBOL,
        "exchange": "kraken_futures",
        "market_type": FuturesMarketType.PERPETUAL,
        "source_run_id": "testnet-closeout-binding-run",
        "dataset_id": "testnet-bounded-observation-v0",
        "price_source": "testnet_bounded_observation",
        "freshness_state": FuturesFreshnessState.FRESH,
        "observed_at_utc": "2026-06-23T00:00:00Z",
        "price_timestamp_utc": "2026-06-23T00:00:00Z",
        "mark_price_available": True,
        "last_price_available": True,
        "index_price_available": True,
        "price_ticks": ticks,
    }
    base.update(overrides)
    return BoundedTestnetFuturesMarketObservationV0(**base)


def _execute_with_mocked_runner(
    mod,
    staging: Path,
    archive: Path,
    *,
    market_observation: BoundedTestnetFuturesMarketObservationV0 | None = None,
) -> int:
    return mod.main(
        _base_argv(staging, archive)
        + [
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE),
            "--no-strict-repo-clean",
        ],
        subprocess_runner=_mock_execute_runner(staging),
        prerequisite_checker=lambda _root: (True, ""),
        repo_clean_checker=lambda _root: (True, ""),
        market_observation=market_observation,
    )


def test_closeout_without_market_observation_fail_closed(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    rc = _execute_with_mocked_runner(mod, staging, archive)
    assert rc == 0
    metadata = json.loads((staging / "RUN_METADATA.json").read_text(encoding="utf-8"))
    wiring = metadata["completion_path_wiring"]
    machine = wiring["machine_summary"]
    assert metadata["market_input_bound"] is False
    assert machine["MISSING_TESTNET_MARKET_INPUT_FAILS_CLOSED"] is True
    closeout = (staging / "CLOSEOUT.md").read_text(encoding="utf-8")
    assert "MISSING_TESTNET_MARKET_INPUT_FAILS_CLOSED=True" in closeout
    assert "TESTNET_EXECUTES_CANONICAL_MASTER_V2=False" in closeout


def test_closeout_forwards_validated_market_observation(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    observation = _valid_market_observation(
        price_ticks=(
            _valid_market_price_tick(tick_index=0, timestamp_ms=1_700_000_000_000, sequence=1),
            _valid_market_price_tick(
                tick_index=1,
                timestamp_ms=1_700_000_060_000,
                mark_price=2501.0,
                sequence=2,
            ),
        )
    )
    rc = _execute_with_mocked_runner(mod, staging, archive, market_observation=observation)
    assert rc == 0
    metadata = json.loads((staging / "RUN_METADATA.json").read_text(encoding="utf-8"))
    plan_wiring = mod.build_plan(
        mode="execute",
        staging_root=staging,
        archive_root=archive,
        repo_root=ROOT,
        duration_minutes=10,
        max_steps=120,
        step_interval_seconds=0.0,
        run_id="testnet_bounded_observation_test_run",
        market_observation=observation,
    ).completion_path_wiring
    closeout_wiring = metadata["completion_path_wiring"]
    assert metadata["market_input_bound"] is True
    assert closeout_wiring == plan_wiring
    assert closeout_wiring["machine_summary"]["MISSING_TESTNET_MARKET_INPUT_FAILS_CLOSED"] is False
    assert (
        closeout_wiring["machine_summary"][
            "BOUNDED_TESTNET_COMPLETION_PATH_MASTER_V2_WIRING_PRESENT"
        ]
        == plan_wiring["machine_summary"][
            "BOUNDED_TESTNET_COMPLETION_PATH_MASTER_V2_WIRING_PRESENT"
        ]
    )
    assert closeout_wiring["machine_summary"]["ORDERS_TOTAL"] == 0
    assert closeout_wiring["machine_summary"]["TESTNET_EXECUTES_CANONICAL_MASTER_V2"] is False


def test_closeout_stale_market_observation_fail_closed(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    observation = _valid_market_observation(freshness_state=FuturesFreshnessState.STALE)
    rc = _execute_with_mocked_runner(mod, staging, archive, market_observation=observation)
    assert rc == 0
    metadata = json.loads((staging / "RUN_METADATA.json").read_text(encoding="utf-8"))
    assert metadata["market_input_bound"] is False
    assert (
        metadata["completion_path_wiring"]["machine_summary"][
            "MISSING_TESTNET_MARKET_INPUT_FAILS_CLOSED"
        ]
        is True
    )


def test_staging_execute_without_market_observation_remains_non_authorizing(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    rc = _execute_with_mocked_runner(mod, staging, archive)
    assert rc == 0
    closeout = (staging / "CLOSEOUT.md").read_text(encoding="utf-8")
    assert "TESTNET_AUTHORIZED=false" in closeout
    assert "START_TESTNET_NOW=false" in closeout
    metadata = json.loads((staging / "RUN_METADATA.json").read_text(encoding="utf-8"))
    assert metadata["market_input_bound"] is False


def _run_selector(*files: str) -> dict[str, str]:
    cmd = [sys.executable, str(SELECTOR), "--event-name", "pull_request", "--files", *files]
    out = subprocess.check_output(cmd, text=True, cwd=str(ROOT))
    result: dict[str, str] = {}
    for line in out.splitlines():
        key, _, value = line.partition("=")
        result[key] = value
    return result


def test_ci_selector_closeout_binding_five_file_diff_focused() -> None:
    sel = _run_selector(*CLOSEOUT_BINDING_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert (
        sel["test_selection_reason"]
        == "bounded_testnet_execute_path_market_observation_closeout_binding_focused"
    )
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    targets = sorted(sel.get("focused_pytest_targets", "").split())
    assert (
        "tests/ops/test_run_testnet_bounded_observation_adapter_v0.py::test_closeout_forwards_validated_market_observation"
        in targets
    )
    assert (
        "tests/ops/test_run_testnet_bounded_observation_adapter_v0.py::test_adapter_replay_proof_classification_plan_execute_closeout_parity"
        in targets
    )
    assert all("::test_" in target for target in targets if not target.endswith(".py"))
    assert len(targets) >= 8


def test_ci_selector_closeout_binding_assertion_only_two_file_diff_focused() -> None:
    sel = _run_selector(*CLOSEOUT_BINDING_ASSERTION_ONLY_FILES)
    assert sel["test_selection_mode"] == "CONTRACT_FOCUSED"
    assert (
        sel["test_selection_reason"]
        == "bounded_testnet_execute_path_market_observation_closeout_binding_focused"
    )
    targets = sorted(sel.get("focused_pytest_targets", "").split())
    assert (
        "tests/ops/test_run_testnet_bounded_observation_adapter_v0.py::test_adapter_replay_proof_classification_plan_execute_closeout_parity"
        in targets
    )


class _AdapterFakeTickerFetcher:
    def __init__(self, *, status: int = 200, body: bytes | None = None) -> None:
        self.status = status
        self.body = body
        self.calls = 0

    def fetch(self, url: str, *, timeout_seconds: float) -> tuple[int, bytes]:
        self.calls += 1
        assert url == build_canonical_testnet_public_ticker_url("https://demo-futures.kraken.com")
        if self.body is not None:
            return self.status, self.body
        payload = {
            "result": "success",
            "tickers": [
                {
                    "symbol": "PF_ETHUSD",
                    "markPrice": 3500.0,
                    "last": 3499.5,
                    "indexPrice": 3500.1,
                    "lastTime": "2026-06-23T11:59:30Z",
                }
            ],
        }
        return self.status, json.dumps(payload).encode("utf-8")


def test_plan_only_collect_public_testnet_market_observation_rejected(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    rc = mod.main(
        _base_argv(staging)
        + [
            "--plan-only",
            "--collect-public-testnet-market-observation",
            "--step-interval-seconds",
            "5.0",
        ]
    )
    assert rc == mod.USAGE_EXIT


def test_execute_collect_public_testnet_market_observation_forwards_closeout(
    tmp_path: Path,
) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    fetcher = _AdapterFakeTickerFetcher()
    clock = BoundedTestnetRuntimeClockV0(_now=datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc))
    rc = mod.main(
        _base_argv(staging, archive)
        + [
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE),
            "--no-strict-repo-clean",
            "--collect-public-testnet-market-observation",
            "--step-interval-seconds",
            "5.0",
            "--max-steps",
            "1",
        ],
        subprocess_runner=_mock_execute_runner(staging),
        prerequisite_checker=lambda _root: (True, ""),
        repo_clean_checker=lambda _root: (True, ""),
        public_ticker_fetcher=fetcher,
        runtime_market_clock=clock,
    )
    assert rc == 0
    assert fetcher.calls == 1
    metadata = json.loads((staging / "RUN_METADATA.json").read_text(encoding="utf-8"))
    assert metadata["market_input_bound"] is True
    assert metadata["completion_path_wiring"]["machine_summary"]["ORDERS_TOTAL"] == 0


def test_execute_collect_http_503_fail_closed(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    fetcher = _AdapterFakeTickerFetcher(status=503, body=b"")
    clock = BoundedTestnetRuntimeClockV0(_now=datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc))
    rc = mod.main(
        _base_argv(staging, archive)
        + [
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE),
            "--no-strict-repo-clean",
            "--collect-public-testnet-market-observation",
            "--step-interval-seconds",
            "5.0",
            "--max-steps",
            "1",
        ],
        subprocess_runner=_mock_execute_runner(staging),
        prerequisite_checker=lambda _root: (True, ""),
        repo_clean_checker=lambda _root: (True, ""),
        public_ticker_fetcher=fetcher,
        runtime_market_clock=clock,
    )
    assert rc == 0
    assert fetcher.calls == 1
    metadata = json.loads((staging / "RUN_METADATA.json").read_text(encoding="utf-8"))
    assert metadata["market_input_bound"] is False
    assert (
        metadata["completion_path_wiring"]["machine_summary"][
            "MISSING_TESTNET_MARKET_INPUT_FAILS_CLOSED"
        ]
        is True
    )


def test_ci_selector_runtime_market_observation_producer_five_file_diff_focused() -> None:
    sel = _run_selector(*RUNTIME_PRODUCER_FILES)
    assert sel["test_selection_mode"] == "FOCUSED"
    assert (
        sel["test_selection_reason"]
        == "bounded_testnet_runtime_market_observation_producer_focused"
    )
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    targets = sorted(sel.get("focused_pytest_targets", "").split())
    assert (
        "tests/ops/test_bounded_testnet_runtime_market_observation_producer_v0.py::test_http_503_fails_closed_without_retry"
        in targets
    )
    assert (
        "tests/ops/test_run_testnet_bounded_observation_adapter_v0.py::test_execute_collect_public_testnet_market_observation_forwards_closeout"
        in targets
    )


def _plan_wiring_section(mod, *, market_observation=None) -> dict:
    return mod.build_plan(
        mode="execute",
        staging_root=Path("/tmp/peak_trade_gap007_plan"),
        archive_root=ARCHIVE_ROOT,
        repo_root=ROOT,
        duration_minutes=10,
        max_steps=120,
        step_interval_seconds=0.0,
        run_id="gap007_plan_section",
        market_observation=market_observation,
    ).completion_path_wiring


def test_plan_prepare_contains_full_completion_path_wiring_section() -> None:
    mod = _load_adapter()
    section = _plan_wiring_section(mod)
    assert section["dashboard_display_projection_digest"] is None or len(
        section["dashboard_display_projection_digest"] or ""
    ) in (0, 64)
    assert section["canonical_retention_owner"]
    assert section["retention_verify_owner"]
    assert section["machine_summary"]


def test_execute_closeout_preserves_full_completion_path_wiring_section(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    observation = _valid_market_observation()
    rc = _execute_with_mocked_runner(mod, staging, archive, market_observation=observation)
    assert rc == 0
    metadata = json.loads((staging / "RUN_METADATA.json").read_text(encoding="utf-8"))
    plan_section = mod.build_plan(
        mode="execute",
        staging_root=staging,
        archive_root=archive,
        repo_root=ROOT,
        duration_minutes=10,
        max_steps=120,
        step_interval_seconds=0.0,
        run_id="testnet_bounded_observation_test_run",
        market_observation=observation,
    ).completion_path_wiring
    assert metadata["completion_path_wiring"] == plan_section


def test_execute_closeout_digest_matches_plan_section(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    observation = _valid_market_observation()
    rc = _execute_with_mocked_runner(mod, staging, archive, market_observation=observation)
    assert rc == 0
    metadata = json.loads((staging / "RUN_METADATA.json").read_text(encoding="utf-8"))
    plan_section = mod.build_plan(
        mode="execute",
        staging_root=staging,
        archive_root=archive,
        repo_root=ROOT,
        duration_minutes=10,
        max_steps=120,
        step_interval_seconds=0.0,
        run_id="testnet_bounded_observation_test_run",
        market_observation=observation,
    ).completion_path_wiring
    assert (
        metadata["completion_path_wiring"]["dashboard_display_projection_digest"]
        == plan_section["dashboard_display_projection_digest"]
    )


def test_execute_closeout_owner_map_matches_plan_section(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    observation = _valid_market_observation()
    rc = _execute_with_mocked_runner(mod, staging, archive, market_observation=observation)
    assert rc == 0
    metadata = json.loads((staging / "RUN_METADATA.json").read_text(encoding="utf-8"))
    section = metadata["completion_path_wiring"]
    for key in (
        "canonical_testnet_runner",
        "canonical_testnet_completion_owner",
        "canonical_master_v2_replay_owner",
        "canonical_six_node_graph_owner",
        "canonical_digest_binding_owner",
        "canonical_retention_owner",
    ):
        assert section[key]


def test_execute_closeout_retention_verify_owner_matches_plan_section(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    observation = _valid_market_observation()
    rc = _execute_with_mocked_runner(mod, staging, archive, market_observation=observation)
    assert rc == 0
    metadata = json.loads((staging / "RUN_METADATA.json").read_text(encoding="utf-8"))
    plan_section = mod.build_plan(
        mode="execute",
        staging_root=staging,
        archive_root=archive,
        repo_root=ROOT,
        duration_minutes=10,
        max_steps=120,
        step_interval_seconds=0.0,
        run_id="testnet_bounded_observation_test_run",
        market_observation=observation,
    ).completion_path_wiring
    assert (
        metadata["completion_path_wiring"]["retention_verify_owner"]
        == plan_section["retention_verify_owner"]
    )


def test_missing_completion_path_wiring_section_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    real_build_plan = mod.build_plan

    def _plan_without_section(*args, **kwargs):
        plan = real_build_plan(*args, **kwargs)
        return mod.AdapterPlan(**{**plan.to_dict(), "completion_path_wiring": {}})

    monkeypatch.setattr(mod, "build_plan", _plan_without_section)
    rc = _execute_with_mocked_runner(mod, staging, archive)
    assert rc == mod.VALIDATION_EXIT


def test_completion_path_wiring_digest_drift_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    real_build_plan = mod.build_plan

    def _plan_with_digest_drift(*args, **kwargs):
        plan = real_build_plan(*args, **kwargs)
        bad_section = {
            **plan.completion_path_wiring,
            "dashboard_display_projection_digest": "f" * 64,
        }
        return mod.AdapterPlan(**{**plan.to_dict(), "completion_path_wiring": bad_section})

    monkeypatch.setattr(mod, "build_plan", _plan_with_digest_drift)
    rc = _execute_with_mocked_runner(
        mod, staging, archive, market_observation=_valid_market_observation()
    )
    assert rc == mod.VALIDATION_EXIT


def test_completion_path_wiring_owner_map_drift_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    real_build_plan = mod.build_plan

    def _plan_with_owner_drift(*args, **kwargs):
        plan = real_build_plan(*args, **kwargs)
        bad_section = {**plan.completion_path_wiring, "canonical_retention_owner": "drift"}
        return mod.AdapterPlan(**{**plan.to_dict(), "completion_path_wiring": bad_section})

    monkeypatch.setattr(mod, "build_plan", _plan_with_owner_drift)
    rc = _execute_with_mocked_runner(mod, staging, archive)
    assert rc == mod.VALIDATION_EXIT


def test_adapter_closeout_does_not_recompute_digest() -> None:
    text = ADAPTER_SCRIPT.read_text(encoding="utf-8")
    assert "build_testnet_bounded_adapter_completion_path_wiring_section" in text
    assert "evaluate_bounded_master_v2_testnet_completion_path_wiring" not in text


def test_execute_closeout_machine_summary_compat_preserved(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    rc = _execute_with_mocked_runner(mod, staging, archive)
    assert rc == 0
    metadata = json.loads((staging / "RUN_METADATA.json").read_text(encoding="utf-8"))
    assert "machine_summary" in metadata["completion_path_wiring"]
    assert metadata["completion_path_wiring"]["machine_summary"]["ORDERS_TOTAL"] == 0


def test_adapter_plan_wiring_exposes_replay_proof_classification_fields() -> None:
    mod = _load_adapter()
    machine = _plan_wiring_section(mod)["machine_summary"]
    assert "OFFLINE_END_TO_END_REPLAY_PROOF_CLASSIFICATION" in machine
    assert "REPLAY_PROOF_CLASSIFICATION_BOUND" in machine
    assert machine["REPLAY_PROOF_CLASSIFICATION_BOUND"] is False


def test_adapter_replay_proof_classification_plan_execute_closeout_parity(
    tmp_path: Path,
) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path, tag="replay_parity")
    archive = _durable_archive(tmp_path, tag="replay_parity")
    observation = _valid_market_observation()
    plan_section = mod.build_plan(
        mode="execute",
        staging_root=staging,
        archive_root=archive,
        repo_root=ROOT,
        duration_minutes=10,
        max_steps=120,
        step_interval_seconds=0.0,
        run_id="testnet_bounded_observation_test_run",
        market_observation=observation,
    ).completion_path_wiring
    plan_machine = plan_section["machine_summary"]
    rc = _execute_with_mocked_runner(mod, staging, archive, market_observation=observation)
    assert rc == 0
    metadata = json.loads((staging / "RUN_METADATA.json").read_text(encoding="utf-8"))
    closeout_machine = metadata["completion_path_wiring"]["machine_summary"]
    assert (
        closeout_machine["OFFLINE_END_TO_END_REPLAY_PROOF_CLASSIFICATION"]
        == plan_machine["OFFLINE_END_TO_END_REPLAY_PROOF_CLASSIFICATION"]
    )
    assert (
        closeout_machine["REPLAY_PROOF_CLASSIFICATION_BOUND"]
        == plan_machine["REPLAY_PROOF_CLASSIFICATION_BOUND"]
    )
    closeout = (staging / "CLOSEOUT.md").read_text(encoding="utf-8")
    assert (
        "OFFLINE_END_TO_END_REPLAY_PROOF_CLASSIFICATION="
        f"{plan_machine['OFFLINE_END_TO_END_REPLAY_PROOF_CLASSIFICATION']}" in closeout
    )
    assert (
        f"REPLAY_PROOF_CLASSIFICATION_BOUND={plan_machine['REPLAY_PROOF_CLASSIFICATION_BOUND']}"
        in closeout
    )


def test_adapter_replay_proof_classification_preserves_non_authorizing_boundaries(
    tmp_path: Path,
) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path, tag="replay_boundaries")
    archive = _durable_archive(tmp_path, tag="replay_boundaries")
    observation = _valid_market_observation()
    rc = _execute_with_mocked_runner(mod, staging, archive, market_observation=observation)
    assert rc == 0
    metadata = json.loads((staging / "RUN_METADATA.json").read_text(encoding="utf-8"))
    machine = metadata["completion_path_wiring"]["machine_summary"]
    assert "OFFLINE_END_TO_END_REPLAY_PROOF_CLASSIFICATION" in machine
    assert "REPLAY_PROOF_CLASSIFICATION_BOUND" in machine
    assert machine["ORDERS_TOTAL"] == 0
    assert machine["TESTNET_EXECUTES_CANONICAL_MASTER_V2"] is False
    closeout = (staging / "CLOSEOUT.md").read_text(encoding="utf-8")
    assert "TESTNET_AUTHORIZED=false" in closeout
    assert "START_TESTNET_NOW=false" in closeout
    assert "LIVE_ALLOWED=false" in closeout
