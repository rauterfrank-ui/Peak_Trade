"""Contract tests for GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_JSON = (
    REPO_ROOT / "docs" / "ops" / "specs" / "GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1.json"
)
POLICY_MD = (
    REPO_ROOT / "docs" / "ops" / "specs" / "GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1.md"
)
ORCHESTRATOR = REPO_ROOT / "scripts" / "ops" / "verification_minimum_local_ci_dedup_v1.py"
RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
REQUIRED_CHECKS = REPO_ROOT / "config" / "ci" / "required_status_checks.json"

sys.path.insert(0, str(REPO_ROOT / "scripts" / "ops"))
import verification_minimum_local_ci_dedup_v1 as dedup  # noqa: E402
from verify_pre_pr_validation_result_v0 import (  # noqa: E402
    verify_pre_pr_validation_result,
)


def _valid_pre_pr(**overrides: str) -> dict[str, str]:
    base = {
        "PRE_PR_VALIDATION_VERDICT": "PRE_PR_VALIDATION_PASS_TIMING_NOT_REQUIRED",
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
        "TIMING_PROOF_NOT_REQUIRED_JUSTIFICATION": "selector FOCUSED small governance dedup",
    }
    base.update(overrides)
    return base


def test_policy_owners_exist() -> None:
    assert POLICY_JSON.is_file()
    assert POLICY_MD.is_file()
    assert ORCHESTRATOR.is_file()
    assert "15.3 Minimum Local CI Dedup" in RUNBOOK.read_text(encoding="utf-8")


def test_policy_json_invariants() -> None:
    payload = json.loads(POLICY_JSON.read_text(encoding="utf-8"))
    assert payload["policy_id"] == dedup.POLICY_ID
    assert payload["runtime_authorization_effect"] == "NONE"
    assert payload["core_logic_change"] is False
    assert payload["capability_11_13_started"] is False
    assert payload["github_required_checks_role"] == (
        "BINDING_BROAD_INTEGRATION_AND_REGRESSION_LAYER"
    )
    retained = {row["check_id"] for row in payload["local_checks_retained"]}
    redundant = {row["check_id"] for row in payload["redundant_local_reexecutions_removed"]}
    assert "safety_activation_credential_order_hard_stops" in retained
    assert "bound_capability_or_owner_test_once" in retained
    assert "capability_suite_rerun_for_evidence_seal_only" in redundant
    assert "pre_pr_rerun_of_identical_bound_suite" in redundant
    assert "WEAKEN_SAFETY_ACTIVATION_CREDENTIAL_ORDER_HARD_STOPS" in payload["forbidden"]
    assert "START_CAPABILITY_11_13" in payload["forbidden"]


def test_load_policy_and_required_contexts() -> None:
    policy = dedup.load_policy(repo_root=REPO_ROOT)
    assert policy["policy_id"] == dedup.POLICY_ID
    contexts = dedup.load_required_contexts(repo_root=REPO_ROOT)
    live = json.loads(REQUIRED_CHECKS.read_text(encoding="utf-8"))
    expected = set(live["required_contexts"]) - set(live.get("ignored_contexts") or [])
    assert contexts == frozenset(expected)
    assert "tests (3.11)" in contexts
    assert "Lint Gate" in contexts


def test_classify_skip_github_covered_without_local_value() -> None:
    contexts = dedup.load_required_contexts(repo_root=REPO_ROOT)
    action = dedup.classify_local_check(
        check_id="local_full_suite_mirror_of_github_required_tests",
        github_required_contexts=contexts,
        github_context_name="tests (3.11)",
        local_pre_push_value_required=False,
    )
    assert action == dedup.ACTION_SKIP_GITHUB


def test_classify_retain_ruff_first_diagnosis() -> None:
    contexts = dedup.load_required_contexts(repo_root=REPO_ROOT)
    action = dedup.classify_local_check(
        check_id="ruff_format_and_check_on_python_diff",
        github_required_contexts=contexts,
        github_context_name="Lint Gate",
        local_pre_push_value_required=True,
    )
    assert action == dedup.ACTION_EXECUTE


def test_classify_reuse_bound_pass() -> None:
    contexts = dedup.load_required_contexts(repo_root=REPO_ROOT)
    action = dedup.classify_local_check(
        check_id="pre_pr_rerun_of_identical_bound_suite",
        github_required_contexts=contexts,
        local_pre_push_value_required=True,
        bound_pass_reusable=True,
    )
    assert action == dedup.ACTION_REUSE


def test_bound_evidence_reuse_fail_closed() -> None:
    good = {
        "bound_stand_sha256": "abc123",
        "test_selector_or_command": "pytest -q tests/ci/test_verification_minimum_local_ci_dedup_v1.py",
        "full_run": True,
        "result": "PASS",
        "exit_code": 0,
    }
    assert dedup.validate_bound_test_evidence(good) == []
    assert dedup.bound_pass_is_reusable(
        binding=good,
        current_stand_sha256="abc123",
        current_test_selector_or_command=good["test_selector_or_command"],
    )
    assert not dedup.bound_pass_is_reusable(
        binding=good,
        current_stand_sha256="changed",
        current_test_selector_or_command=good["test_selector_or_command"],
    )
    bad = dict(good, exit_code=1, result="FAIL")
    assert dedup.validate_bound_test_evidence(bad)
    assert not dedup.bound_pass_is_reusable(
        binding=bad,
        current_stand_sha256="abc123",
        current_test_selector_or_command=good["test_selector_or_command"],
    )


def test_pre_pr_legacy_envelope_without_reuse_fields_still_passes() -> None:
    assert verify_pre_pr_validation_result(_valid_pre_pr()) == []


def test_pre_pr_reuse_fields_valid() -> None:
    data = _valid_pre_pr(
        LOCAL_TEST_EVIDENCE_REUSE_STATUS="REUSED",
        BOUND_LOCAL_TEST_STAND_SHA256="deadbeef",
        BOUND_LOCAL_TEST_COMMAND="pytest -q tests/ci/test_verification_minimum_local_ci_dedup_v1.py",
        BOUND_LOCAL_TEST_EXIT_CODE="0",
        BOUND_LOCAL_TEST_RESULT="PASS",
        BOUND_LOCAL_TEST_FULL_RUN="true",
    )
    assert verify_pre_pr_validation_result(data) == []


def test_pre_pr_reuse_fields_invalid_exit_blocks() -> None:
    data = _valid_pre_pr(
        LOCAL_TEST_EVIDENCE_REUSE_STATUS="REUSED",
        BOUND_LOCAL_TEST_STAND_SHA256="deadbeef",
        BOUND_LOCAL_TEST_COMMAND="pytest -q tests/ci/test_verification_minimum_local_ci_dedup_v1.py",
        BOUND_LOCAL_TEST_EXIT_CODE="1",
        BOUND_LOCAL_TEST_RESULT="PASS",
        BOUND_LOCAL_TEST_FULL_RUN="true",
    )
    errors = verify_pre_pr_validation_result(data)
    assert errors


def test_cli_print_policy() -> None:
    proc = subprocess.run(
        [sys.executable, str(ORCHESTRATOR), "--print-policy"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["policy_id"] == dedup.POLICY_ID
    assert "capability_suite_rerun_for_evidence_seal_only" in payload["redundant_removed"]


def test_generic_not_cap_11_12_special_case() -> None:
    text = POLICY_MD.read_text(encoding="utf-8")
    assert "capability-generic" in text.lower() or "Cap-11.12-only" in text
    assert "CAPABILITY_11_13_STARTED=false" in text
    orch = ORCHESTRATOR.read_text(encoding="utf-8")
    assert "Cap-11.13" in orch or "capability_11_13" in orch
