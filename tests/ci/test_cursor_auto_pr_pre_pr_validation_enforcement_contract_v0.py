"""Contract tests for cursor_auto_pr PRE_PR validation enforcement (v0).

Static workflow structure plus fail-closed verifier semantics. Never dispatches
workflows, never calls GitHub APIs, and never touches runtime or trading paths.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "cursor_auto_pr.yml"
VERIFIER = REPO_ROOT / "scripts" / "ops" / "verify_pre_pr_validation_result_v0.py"

sys.path.insert(0, str(REPO_ROOT / "scripts" / "ops"))
from verify_pre_pr_validation_result_v0 import (  # noqa: E402
    verify_pre_pr_validation_result,
)


def _valid_pass_data(**overrides: str) -> dict[str, str]:
    base = {
        "PRE_PR_VALIDATION_VERDICT": "PRE_PR_VALIDATION_PASS",
        "FINAL_DIFF_FROZEN": "true",
        "FINAL_FILES_MATCH": "true",
        "FINAL_DIFF_PATH_EQUIVALENCE_CONFIRMED": "true",
        "REUSE_BEFORE_NEW_CHECKED": "true",
        "LOCAL_GATE_BATCH_RESULT": "PASS",
        "UNVALIDATED_FILES_REMAIN": "false",
        "COMMIT_ALLOWED": "true",
        "PUSH_ALLOWED": "true",
        "PR_ALLOWED": "true",
        "MANIFEST_VERIFY_RC": "0",
        "TIMING_PROOF_REQUIRED": "true",
        "TIMING_PROOF_STATUS": "PASS",
        "TIMING_WALLCLOCK_SECONDS": "120",
        "TIMING_HARD_STOP_SECONDS": "900",
        "TIMING_SAFETY_MARGIN_SECONDS": "180",
        "FINAL_DIFF_SHA256": "abc",
    }
    base.update(overrides)
    return base


def _valid_timing_not_required_data(**overrides: str) -> dict[str, str]:
    base = _valid_pass_data(
        PRE_PR_VALIDATION_VERDICT="PRE_PR_VALIDATION_PASS_TIMING_NOT_REQUIRED",
        TIMING_PROOF_REQUIRED="false",
        TIMING_PROOF_STATUS="TIMING_PROOF_NOT_REQUIRED_JUSTIFIED",
        TIMING_PROOF_NOT_REQUIRED_JUSTIFICATION="selector NO_OP small FOCUSED",
    )
    # remove timing pass-only fields that are not required
    base.pop("TIMING_WALLCLOCK_SECONDS", None)
    base.update(overrides)
    return base


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_cursor_auto_pr_workflow_enforces_pre_pr_before_create_pr() -> None:
    text = _workflow_text()
    enforce_idx = text.index("Enforce PRE_PR validation (fail-closed)")
    create_idx = text.index("Create PR if missing")
    dispatch_idx = text.index("Dispatch required checks (workflow_dispatch)")
    assert enforce_idx < create_idx < dispatch_idx


def test_cursor_auto_pr_workflow_checks_out_before_enforcement() -> None:
    text = _workflow_text()
    checkout_idx = text.index("Checkout for PRE_PR enforcement")
    enforce_idx = text.index("Enforce PRE_PR validation (fail-closed)")
    assert checkout_idx < enforce_idx


def test_cursor_auto_pr_workflow_invokes_canonical_verifier() -> None:
    text = _workflow_text()
    assert "verify_pre_pr_validation_result_v0.py" in text
    assert ".cursor/PRE_PR_VALIDATION_RESULT.env" in text
    assert "--check-diff-sha" in text


def test_verifier_module_exists() -> None:
    assert VERIFIER.is_file()


def test_full_valid_pass_allows() -> None:
    assert verify_pre_pr_validation_result(_valid_pass_data()) == []


def test_fail_closed_verdict_blocks() -> None:
    data = _valid_pass_data(PRE_PR_VALIDATION_VERDICT="PRE_PR_VALIDATION_FAIL_CLOSED")
    errors = verify_pre_pr_validation_result(data)
    assert any("FAIL_CLOSED" in e for e in errors)


def test_missing_verdict_blocks() -> None:
    data = _valid_pass_data()
    del data["PRE_PR_VALIDATION_VERDICT"]
    assert verify_pre_pr_validation_result(data)


def test_timing_fail_with_pass_verdict_blocks() -> None:
    data = _valid_pass_data(TIMING_PROOF_STATUS="FAIL")
    errors = verify_pre_pr_validation_result(data)
    assert any("TIMING_PROOF_STATUS" in e for e in errors)


def test_timing_hard_stop_wallclock_blocks() -> None:
    data = _valid_pass_data(TIMING_WALLCLOCK_SECONDS="900")
    errors = verify_pre_pr_validation_result(data)
    assert any("900" in e for e in errors)


def test_timing_required_without_pass_blocks() -> None:
    data = _valid_pass_data(
        PRE_PR_VALIDATION_VERDICT="PRE_PR_VALIDATION_PASS_TIMING_NOT_REQUIRED",
        TIMING_PROOF_REQUIRED="true",
    )
    errors = verify_pre_pr_validation_result(data)
    assert errors


def test_timing_not_required_without_justification_blocks() -> None:
    data = _valid_timing_not_required_data(TIMING_PROOF_STATUS="PASS")
    data.pop("TIMING_PROOF_NOT_REQUIRED_JUSTIFICATION", None)
    errors = verify_pre_pr_validation_result(data)
    assert errors


def test_timing_not_required_valid_pass() -> None:
    assert verify_pre_pr_validation_result(_valid_timing_not_required_data()) == []


def test_final_files_match_false_blocks() -> None:
    data = _valid_pass_data(FINAL_FILES_MATCH="false")
    assert verify_pre_pr_validation_result(data)


def test_path_equivalence_false_blocks() -> None:
    data = _valid_pass_data(FINAL_DIFF_PATH_EQUIVALENCE_CONFIRMED="false")
    assert verify_pre_pr_validation_result(data)


def test_local_gate_not_pass_blocks() -> None:
    data = _valid_pass_data(LOCAL_GATE_BATCH_RESULT="FAIL")
    assert verify_pre_pr_validation_result(data)


def test_manifest_verify_rc_nonzero_blocks() -> None:
    data = _valid_pass_data(MANIFEST_VERIFY_RC="1")
    assert verify_pre_pr_validation_result(data)


def test_commit_allowed_false_blocks() -> None:
    data = _valid_pass_data(COMMIT_ALLOWED="false")
    assert verify_pre_pr_validation_result(data)


def test_push_allowed_false_blocks() -> None:
    data = _valid_pass_data(PUSH_ALLOWED="false")
    assert verify_pre_pr_validation_result(data)


def test_pr_allowed_false_blocks() -> None:
    data = _valid_pass_data(PR_ALLOWED="false")
    assert verify_pre_pr_validation_result(data)


def test_unvalidated_files_remain_true_blocks() -> None:
    data = _valid_pass_data(UNVALIDATED_FILES_REMAIN="true")
    assert verify_pre_pr_validation_result(data)


def test_timing_not_required_with_hard_stop_wallclock_blocks() -> None:
    data = _valid_timing_not_required_data(TIMING_WALLCLOCK_SECONDS="900")
    errors = verify_pre_pr_validation_result(data)
    assert any("hard stop" in e for e in errors)


def test_cli_missing_result_file_exits_nonzero(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(VERIFIER),
            "--result-file",
            str(tmp_path / "missing.env"),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 1
    assert "missing result file" in proc.stderr


def test_required_check_names_unchanged_in_ci_yml() -> None:
    ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "timeout-minutes: 17" in ci
    assert "timeout-minutes: 25" in ci
    assert "timeout-minutes: 30" not in ci
    assert "timeout-minutes: 40" not in ci


def test_cursor_auto_pr_workflow_does_not_mutate_matrix_or_required_contexts() -> None:
    text = _workflow_text()
    assert "strategy:" not in text
    assert "\n        matrix:" not in text
    assert "required_status" not in text.lower()
