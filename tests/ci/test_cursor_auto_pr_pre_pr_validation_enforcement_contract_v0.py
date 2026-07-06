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
    PRE_PR_RESULT_REL_PATH,
    _diff_sha256,
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


def _valid_bound_data(**overrides: str) -> dict[str, str]:
    base = _valid_timing_not_required_data(
        FEATURE_BRANCH="feat/example-v0",
        FEATURE_HEAD="deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        ORIGIN_MAIN_HEAD="cafebabecafebabecafebabecafebabecafebabe",
        FINAL_INTENDED_FILES="src/example.py,tests/ci/test_example_contract_v0.py",
    )
    base.update(overrides)
    return base


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_cursor_auto_pr_workflow_detects_existing_pr_before_pre_pr_enforcement() -> None:
    text = _workflow_text()
    detect_idx = text.index("Detect existing open PR for head branch")
    checkout_idx = text.index("Checkout for PRE_PR enforcement")
    redetect_idx = text.index("Re-detect open PR before PRE_PR enforcement")
    enforce_idx = text.index("Enforce PRE_PR validation (fail-closed)")
    create_idx = text.index("Create PR if missing")
    dispatch_idx = text.index("Dispatch required checks (workflow_dispatch)")
    assert detect_idx < checkout_idx < redetect_idx < enforce_idx < create_idx < dispatch_idx


def test_cursor_auto_pr_workflow_pre_pr_skipped_when_open_pr_exists() -> None:
    text = _workflow_text()
    assert "id: detect" in text
    assert "id: redetect" in text
    assert (
        "steps.detect.outputs.open_pr_exists != 'true' && steps.redetect.outputs.open_pr_exists != 'true'"
        in text
    )
    assert "Skipping PRE_PR enforcement; existing open PR is idempotent no-op." in text
    assert "push/manual PR create race guard" in text
    assert "IDEMPOTENT_NOOP: open PR exists before PRE_PR enforcement" in text


def test_cursor_auto_pr_workflow_retries_open_pr_lookup_for_push_race() -> None:
    text = _workflow_text()
    assert "NO_OPEN_PR attempt" in text
    assert "maxAttempts = 6" in text


def test_cursor_auto_pr_workflow_fail_closed_on_ambiguous_open_pr_lookup() -> None:
    text = _workflow_text()
    assert "FAIL_CLOSED: ambiguous open PR count=" in text
    assert "FAIL_CLOSED: open PR lookup failed" in text


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
    assert "--check-binding" in text


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
    assert "timeout-minutes: 10" in ci
    assert "timeout-minutes: 25" in ci
    assert "timeout-minutes: 30" not in ci
    assert "timeout-minutes: 40" not in ci


def test_cursor_auto_pr_workflow_does_not_mutate_matrix_or_required_contexts() -> None:
    text = _workflow_text()
    assert "strategy:" not in text
    assert "\n        matrix:" not in text
    assert "required_status" not in text.lower()


def test_stale_feature_branch_rejected() -> None:
    data = _valid_bound_data(FEATURE_BRANCH="feat/step29m-policy-contract-v3-config-registry-v0")
    errors = verify_pre_pr_validation_result(
        data,
        check_binding=True,
        current_branch="feat/new-independent-v0",
        current_head=data["FEATURE_HEAD"],
    )
    assert any("FEATURE_BRANCH mismatch" in e for e in errors)


def test_stale_feature_head_rejected() -> None:
    data = _valid_bound_data()
    errors = verify_pre_pr_validation_result(
        data,
        check_binding=True,
        current_branch=data["FEATURE_BRANCH"],
        current_head="1111111111111111111111111111111111111111",
    )
    assert any("FEATURE_HEAD mismatch" in e for e in errors)


def test_stale_origin_main_head_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    data = _valid_bound_data(ORIGIN_MAIN_HEAD="845742846aa36deb55fd858c9d6c30a4306721b4")

    def fake_rev_parse(ref: str, *, repo_root: Path) -> str:
        if ref == "origin/main":
            return "0118543e1c9424cccbb105994879f0cd1a292ed1"
        return ref

    monkeypatch.setattr(
        "verify_pre_pr_validation_result_v0._git_rev_parse",
        fake_rev_parse,
    )
    errors = verify_pre_pr_validation_result(
        data,
        check_binding=True,
        current_branch=data["FEATURE_BRANCH"],
        current_head=data["FEATURE_HEAD"],
    )
    assert any("ORIGIN_MAIN_HEAD mismatch" in e for e in errors)


def test_stale_final_intended_files_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    data = _valid_bound_data(
        FINAL_INTENDED_FILES=(
            "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v3.json,"
            "tests/ops/test_step29m_macd_v1_economic_evaluation_admissibility_contract_v1.py"
        )
    )

    def fake_changed_files(base_ref: str, *, repo_root: Path) -> frozenset[str]:
        return frozenset({"scripts/ops/verify_pre_pr_validation_result_v0.py"})

    monkeypatch.setattr(
        "verify_pre_pr_validation_result_v0._changed_files",
        fake_changed_files,
    )
    errors = verify_pre_pr_validation_result(
        data,
        check_binding=True,
        current_branch=data["FEATURE_BRANCH"],
        current_head=data["FEATURE_HEAD"],
    )
    assert any("FINAL_INTENDED_FILES" in e for e in errors)


def test_step29m_carryover_rejected_on_independent_branch() -> None:
    stale = {
        "PRE_PR_VALIDATION_VERDICT": "PRE_PR_VALIDATION_PASS_TIMING_NOT_REQUIRED",
        "FEATURE_BRANCH": "feat/step29m-policy-contract-v3-config-registry-v0",
        "FEATURE_HEAD": "845742846aa36deb55fd858c9d6c30a4306721b4",
        "ORIGIN_MAIN_HEAD": "845742846aa36deb55fd858c9d6c30a4306721b4",
        "FINAL_INTENDED_FILES": (
            "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v3.json,"
            "tests/ops/test_step29m_macd_v1_economic_evaluation_admissibility_contract_v1.py"
        ),
        "FINAL_DIFF_SHA256": "7298ce66d25bebd7c120449e274f3be6263d66252845b41fbfee250b08d14b9f",
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
        "TIMING_PROOF_REQUIRED": "false",
        "TIMING_PROOF_STATUS": "TIMING_PROOF_NOT_REQUIRED_JUSTIFIED",
        "TIMING_PROOF_NOT_REQUIRED_JUSTIFICATION": "historical step29m slice",
    }
    errors = verify_pre_pr_validation_result(
        stale,
        check_binding=True,
        check_diff_sha=False,
        current_branch="feat/pit-futures-cross-sectional-v0",
        current_head="0118543e1c9424cccbb105994879f0cd1a292ed1",
    )
    assert any("FEATURE_BRANCH mismatch" in e for e in errors)


def test_valid_branch_bound_evidence_accepted_without_git(monkeypatch: pytest.MonkeyPatch) -> None:
    data = _valid_bound_data()

    def fake_rev_parse(ref: str, *, repo_root: Path) -> str:
        if ref == "origin/main":
            return data["ORIGIN_MAIN_HEAD"]
        return ref

    def fake_changed_files(base_ref: str, *, repo_root: Path) -> frozenset[str]:
        return frozenset({"src/example.py", "tests/ci/test_example_contract_v0.py"})

    monkeypatch.setattr(
        "verify_pre_pr_validation_result_v0._git_rev_parse",
        fake_rev_parse,
    )
    monkeypatch.setattr(
        "verify_pre_pr_validation_result_v0._changed_files",
        fake_changed_files,
    )
    assert (
        verify_pre_pr_validation_result(
            data,
            check_binding=True,
            current_branch=data["FEATURE_BRANCH"],
            current_head=data["FEATURE_HEAD"],
        )
        == []
    )


def test_final_intended_files_must_not_include_pre_pr_result_path() -> None:
    data = _valid_bound_data(
        FINAL_INTENDED_FILES=(
            "src/example.py,.cursor/PRE_PR_VALIDATION_RESULT.env,"
            "tests/ci/test_example_contract_v0.py"
        )
    )
    errors = verify_pre_pr_validation_result(
        data,
        check_binding=True,
        current_branch=data["FEATURE_BRANCH"],
        current_head=data["FEATURE_HEAD"],
    )
    assert any("self-referential" in e for e in errors)


def test_missing_binding_fields_fail_closed() -> None:
    data = _valid_bound_data()
    del data["FEATURE_HEAD"]
    errors = verify_pre_pr_validation_result(
        data,
        check_binding=True,
        current_branch=data["FEATURE_BRANCH"],
    )
    assert any("missing FEATURE_HEAD" in e for e in errors)


def test_check_binding_enabled_when_check_diff_sha() -> None:
    data = _valid_bound_data(FEATURE_BRANCH="feat/wrong-branch-v0")
    errors = verify_pre_pr_validation_result(
        data,
        check_diff_sha=True,
        check_binding=True,
        current_branch="feat/actual-branch-v0",
        current_head=data["FEATURE_HEAD"],
    )
    assert any("FEATURE_BRANCH mismatch" in e for e in errors)


def test_diff_sha_excludes_pre_pr_result_file(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "base"], cwd=repo, check=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=repo, check=True)

    (repo / "change.py").write_text("x = 1\n", encoding="utf-8")
    cursor_dir = repo / ".cursor"
    cursor_dir.mkdir()
    (cursor_dir / "PRE_PR_VALIDATION_RESULT.env").write_text("VERDICT=PASS\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "feature"], cwd=repo, check=True)

    digest_with_exclusion = _diff_sha256("main~1", repo_root=repo)
    proc_full = subprocess.run(
        ["git", "diff", "main~1...HEAD"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    digest_full = __import__("hashlib").sha256(proc_full.stdout.encode("utf-8")).hexdigest()
    assert digest_with_exclusion != digest_full
    proc_code_only = subprocess.run(
        ["git", "diff", "main~1...HEAD", "--", "change.py"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    digest_code_only = (
        __import__("hashlib").sha256(proc_code_only.stdout.encode("utf-8")).hexdigest()
    )
    assert digest_with_exclusion == digest_code_only


def test_pre_pr_result_file_not_on_main_after_cleanup() -> None:
    stale_path = REPO_ROOT / ".cursor" / "PRE_PR_VALIDATION_RESULT.env"
    assert not stale_path.is_file()


def test_stale_main_carryover_would_fail_binding_and_diff() -> None:
    stale = {
        "PRE_PR_VALIDATION_VERDICT": "PRE_PR_VALIDATION_PASS_TIMING_NOT_REQUIRED",
        "FEATURE_BRANCH": "feat/step29m-policy-contract-v3-config-registry-v0",
        "ORIGIN_MAIN_HEAD": "845742846aa36deb55fd858c9d6c30a4306721b4",
        "FINAL_INTENDED_FILES": (
            "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v3.json,"
            ".cursor/PRE_PR_VALIDATION_RESULT.env"
        ),
        "FINAL_DIFF_SHA256": "7298ce66d25bebd7c120449e274f3be6263d66252845b41fbfee250b08d14b9f",
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
        "TIMING_PROOF_REQUIRED": "false",
        "TIMING_PROOF_STATUS": "TIMING_PROOF_NOT_REQUIRED_JUSTIFIED",
        "TIMING_PROOF_NOT_REQUIRED_JUSTIFICATION": "historical step29m slice",
    }
    errors = verify_pre_pr_validation_result(
        stale,
        check_binding=True,
        current_branch="feat/stale-pre-pr-validation-carryover-cleanup-v0",
        current_head="0118543e1c9424cccbb105994879f0cd1a292ed1",
    )
    assert any("missing FEATURE_HEAD" in e for e in errors)
    assert any("self-referential" in e for e in errors)
