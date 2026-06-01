"""Static and mocked contract tests for Gap-4 REQ-B Shadow B07/B08 adapter parity v0."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
ADAPTER_SCRIPT = ROOT / "scripts" / "ops" / "run_shadow_bounded_observation_adapter_v0.py"
REVIEW_SCRIPT = ROOT / "scripts" / "ops" / "review_shadow_bounded_observation_evidence_v0.py"
SECTION5_DOC = (
    ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)
FINAL_MACHINE_LINES_HEADER = "## Final Machine Lines"
GAP4_CRITERIA_HEADER = "## Gap 4 Output/Evidence Paths Contract v0"
GAP4_ADAPTER_PARITY_HEADER = "## Gap 4 REQ-B Shadow B07/B08 Adapter Parity v0"
GAP4_COMPLETENESS_REFLECTION_HEADER = "## Gap 4 Full-Scope Evidence Completeness Reflection v0"
GAP4_VERIFIED_REFLECTION_HEADER = "## Gap 4 Full-Scope Gap4 Verified Reflection v0"

ADAPTER_PARITY_FORBIDDEN_TRUE_OUTSIDE_SCOPED_REFLECTION = (
    "REQ_B_TIER_D_POPULATED_PATHS_FOUND=true",
    "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true",
    "FULL_SCOPE_GAP4_VERIFIED=true",
    "GAP4_FULL_SCOPE_EVIDENCE_COMPLETE=true",
)

APPROVAL_FIXTURE = ROOT / "tests" / "fixtures" / "ops" / "shadow_adapter_stage3_approval_sample.md"
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")

FORBIDDEN_DIFF_PREFIXES = (
    "src/strategies/",
    "scripts/double_play",
    "master_v2",
    "path_b",
)


def _load_module(script: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, script)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_adapter():
    return _load_module(ADAPTER_SCRIPT, "run_shadow_bounded_observation_adapter_v0_parity")


def _load_review():
    return _load_module(REVIEW_SCRIPT, "review_shadow_bounded_observation_evidence_parity")


def _staging(tmp_path: Path) -> Path:
    return Path("/tmp") / f"peak_trade_shadow_parity_test_{tmp_path.name}"


def _section5_text() -> str:
    return SECTION5_DOC.read_text(encoding="utf-8")


def _final_machine_lines(text: str) -> str:
    return text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]


def _gap4_criteria_section(text: str) -> str:
    return text.split(GAP4_CRITERIA_HEADER, 1)[1].split(
        "## Gap 6 Dry-Run Proof Criteria Contract v0", 1
    )[0]


def _gap4_adapter_parity_section(text: str) -> str:
    return text.split(GAP4_ADAPTER_PARITY_HEADER, 1)[1].split(
        GAP4_COMPLETENESS_REFLECTION_HEADER, 1
    )[0]


def _gap4_completeness_reflection_section(text: str) -> str:
    return text.split(GAP4_COMPLETENESS_REFLECTION_HEADER, 1)[1].split(
        GAP4_VERIFIED_REFLECTION_HEADER, 1
    )[0]


def _gap4_verified_reflection_section(text: str) -> str:
    return text.split(GAP4_VERIFIED_REFLECTION_HEADER, 1)[1].split(
        "## Gap 7 Governed Risk Boundary Acceptance Reflection v0", 1
    )[0]


def _base_argv(staging: Path, archive: Path) -> list[str]:
    return [
        "--staging-root",
        str(staging),
        "--archive-root",
        str(archive),
        "--repo-root",
        str(ROOT),
    ]


def _plan_dict(staging: Path, archive: Path) -> dict:
    mod = _load_adapter()
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.main(_base_argv(staging, archive) + ["--json"])
    assert rc == 0, buf.getvalue()
    return json.loads(buf.getvalue())


def _durable_archive(tmp_path: Path) -> Path:
    path = ROOT / "tests" / ".pytest_archive_roots" / f"parity_{tmp_path.name}"
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


def test_shadow_plan_lists_b07_b08_expected_artifacts_v0(tmp_path: Path) -> None:
    mod = _load_adapter()
    plan = _plan_dict(_staging(tmp_path), _durable_archive(tmp_path))
    artifacts = plan["expected_artifacts"]
    assert mod.COMMAND_TRANSCRIPT_FILENAME in artifacts
    assert mod.PROCESS_INVENTORY_BEFORE_FILENAME in artifacts
    assert mod.PROCESS_INVENTORY_AFTER_FILENAME in artifacts


def test_shadow_plan_retention_steps_mention_b07_b08_v0(tmp_path: Path) -> None:
    mod = _load_adapter()
    plan = _plan_dict(_staging(tmp_path), _durable_archive(tmp_path))
    joined = " ".join(plan["retention_steps"]).lower()
    assert mod.COMMAND_TRANSCRIPT_FILENAME.lower() in joined
    assert "process_inventory_before" in joined
    assert "process_inventory_after" in joined


def test_shadow_execute_writes_command_transcript_v0(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    review_mod = _load_review()

    def _runner(argv: Sequence[str], _cwd, stdout_path, stderr_path) -> int:
        joined = " ".join(argv)
        if "shadow_247_futures_start_wrapper_skeleton_v0.py" in joined:
            _write_wrapper_bundle(staging)
            if stdout_path is not None:
                stdout_path.write_text("mock wrapper stdout\n", encoding="utf-8")
            if stderr_path is not None:
                stderr_path.write_text("mock wrapper stderr\n", encoding="utf-8")
            return 0
        if "review_shadow_bounded_observation_evidence_v0.py" in joined:
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
    transcript = staging / mod.COMMAND_TRANSCRIPT_FILENAME
    assert transcript.is_file()
    body = transcript.read_text(encoding="utf-8")
    assert "RUN_ID=" in body
    assert "WRAPPER_COMMAND=" in body
    assert "bounded-shadow-dry-run" in body.lower()
    assert "api_key" not in body.lower()
    assert "password" not in body.lower()


def test_shadow_execute_writes_process_inventory_before_after_v0(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    review_mod = _load_review()

    def _runner(argv: Sequence[str], _cwd, stdout_path, stderr_path) -> int:
        joined = " ".join(argv)
        if "shadow_247_futures_start_wrapper_skeleton_v0.py" in joined:
            _write_wrapper_bundle(staging)
            if stdout_path is not None:
                stdout_path.write_text("mock wrapper stdout\n", encoding="utf-8")
            if stderr_path is not None:
                stderr_path.write_text("mock wrapper stderr\n", encoding="utf-8")
            return 0
        if "review_shadow_bounded_observation_evidence_v0.py" in joined:
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
    before = staging / mod.PROCESS_INVENTORY_BEFORE_FILENAME
    after = staging / mod.PROCESS_INVENTORY_AFTER_FILENAME
    assert before.is_file()
    assert after.is_file()
    before_body = before.read_text(encoding="utf-8")
    after_body = after.read_text(encoding="utf-8")
    assert "CAPTURE_PHASE=before" in before_body
    assert "CAPTURE_PHASE=after" in after_body
    assert "api_key" not in before_body.lower()
    assert "api_key" not in after_body.lower()


def test_shadow_execute_includes_b07_b08_in_manifest_v0(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    review_mod = _load_review()

    def _runner(argv: Sequence[str], _cwd, stdout_path, stderr_path) -> int:
        joined = " ".join(argv)
        if "shadow_247_futures_start_wrapper_skeleton_v0.py" in joined:
            _write_wrapper_bundle(staging)
            if stdout_path is not None:
                stdout_path.write_text("mock wrapper stdout\n", encoding="utf-8")
            if stderr_path is not None:
                stderr_path.write_text("mock wrapper stderr\n", encoding="utf-8")
            return 0
        if "review_shadow_bounded_observation_evidence_v0.py" in joined:
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
    manifest = (staging / "MANIFEST.sha256").read_text(encoding="utf-8")
    assert mod.COMMAND_TRANSCRIPT_FILENAME in manifest
    assert mod.PROCESS_INVENTORY_BEFORE_FILENAME in manifest
    assert mod.PROCESS_INVENTORY_AFTER_FILENAME in manifest


def test_sanitize_command_for_transcript_redacts_secrets_v0() -> None:
    mod = _load_adapter()
    sanitized = mod._sanitize_command_for_transcript(["python", "run.py", "--api_key=secret"])
    assert sanitized == "[REDACTED_BOUNDED_SHADOW_COMMAND]"


def test_plan_only_does_not_execute_runtime_v0(tmp_path: Path) -> None:
    mod = _load_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)
    called = {"count": 0}

    def _runner(*_args, **_kwargs) -> int:
        called["count"] += 1
        return 0

    rc = mod.main(_base_argv(staging, archive), subprocess_runner=_runner)
    assert rc == 0
    assert called["count"] == 0


def test_adapter_parity_does_not_flip_section5_evidence_tokens_v0() -> None:
    text = _section5_text()
    parity = _gap4_adapter_parity_section(text)
    parity_lines = {line.strip() for line in parity.splitlines()}
    criteria_lines = {line.strip() for line in _gap4_criteria_section(text).splitlines()}
    block_lines = {line.strip() for line in _final_machine_lines(text).splitlines()}
    completeness_lines = {
        line.strip() for line in _gap4_completeness_reflection_section(text).splitlines()
    }
    verified_lines = {line.strip() for line in _gap4_verified_reflection_section(text).splitlines()}
    repo_ssot_lines = criteria_lines | block_lines | parity_lines

    assert "SHADOW_B07_B08_MISSING=true" in parity_lines
    assert "REQ_B_TIER_D_POPULATED_PATHS_FOUND=false" in parity_lines
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in parity_lines
    assert "FULL_SCOPE_GAP4_VERIFIED=false" in parity_lines
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in parity_lines
    assert "SHADOW_B07_B08_MISSING=false" not in parity_lines

    for token in ADAPTER_PARITY_FORBIDDEN_TRUE_OUTSIDE_SCOPED_REFLECTION:
        assert token not in repo_ssot_lines

    assert "REQ_B_TIER_D_POPULATED_PATHS_FOUND=true" in completeness_lines
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in completeness_lines
    assert "FULL_SCOPE_GAP4_VERIFIED=true" in verified_lines
    assert "FULL_SCOPE_GAP4_VERIFIED=true" not in completeness_lines


def test_pr_scope_excludes_trading_and_double_play_paths() -> None:
    touched = [
        ADAPTER_SCRIPT,
        ADAPTER_SCRIPT,
        Path(__file__),
        ROOT / "tests" / "ops" / "test_run_shadow_bounded_observation_adapter_v0.py",
    ]
    for path in touched:
        rel = path.relative_to(ROOT).as_posix().lower()
        for forbidden in FORBIDDEN_DIFF_PREFIXES:
            assert forbidden not in rel
