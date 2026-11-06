#!/usr/bin/env python3
"""Minimum local CI dedup / bound-test-evidence reuse orchestration (v1).

Generic governance verification orchestration. Does not mutate trading,
activation, credential, order, or Cap-11.13 surfaces.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

POLICY_ID = "GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1"
PACKAGE_MARKER = "VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1=true"
POLICY_REL_PATH = "docs/ops/specs/GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1.json"
REQUIRED_CHECKS_REL_PATH = "config/ci/required_status_checks.json"

ACTION_EXECUTE = "EXECUTE_REQUIRED_LOCAL"
ACTION_REUSE = "REUSE_BOUND_PASS"
ACTION_SKIP_GITHUB = "SKIP_GITHUB_COVERED_NO_EXTRA_LOCAL_VALUE"

REUSE_STATUS_EXECUTED = "EXECUTED"
REUSE_STATUS_REUSED = "REUSED"
REUSE_STATUS_NA = "N/A"

_REPO_ROOT = Path(__file__).resolve().parents[2]


def policy_path(*, repo_root: Path | None = None) -> Path:
    root = repo_root or _REPO_ROOT
    return root / POLICY_REL_PATH


def load_policy(*, repo_root: Path | None = None) -> dict[str, Any]:
    path = policy_path(repo_root=repo_root)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("policy_id") != POLICY_ID:
        raise ValueError(f"policy_id mismatch in {path}")
    if payload.get("runtime_authorization_effect") != "NONE":
        raise ValueError("runtime_authorization_effect must remain NONE")
    if payload.get("capability_11_13_started") is not False:
        raise ValueError("capability_11_13_started must remain false")
    return payload


def load_required_contexts(*, repo_root: Path | None = None) -> frozenset[str]:
    root = repo_root or _REPO_ROOT
    path = root / REQUIRED_CHECKS_REL_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = set(payload.get("required_contexts") or [])
    ignored = set(payload.get("ignored_contexts") or [])
    return frozenset(required - ignored)


def classify_local_check(
    *,
    check_id: str,
    github_required_contexts: frozenset[str] | set[str],
    github_context_name: str | None = None,
    local_pre_push_value_required: bool,
    bound_pass_reusable: bool = False,
) -> str:
    """Return one of EXECUTE / REUSE / SKIP_GITHUB actions."""
    if bound_pass_reusable:
        return ACTION_REUSE
    covered = False
    if github_context_name and github_context_name in github_required_contexts:
        covered = True
    if check_id in github_required_contexts:
        covered = True
    if covered and not local_pre_push_value_required:
        return ACTION_SKIP_GITHUB
    return ACTION_EXECUTE


def validate_bound_test_evidence(binding: Mapping[str, Any]) -> list[str]:
    """Fail-closed validation for a reusable local test PASS binding."""
    errors: list[str] = []
    stand = str(binding.get("bound_stand_sha256") or "").strip()
    if not stand:
        errors.append("missing bound_stand_sha256")
    command = binding.get("test_selector_or_command")
    if isinstance(command, list):
        if not command:
            errors.append("empty test_selector_or_command")
    elif not str(command or "").strip():
        errors.append("missing test_selector_or_command")
    if binding.get("full_run") is not True:
        errors.append("full_run must be true")
    if str(binding.get("result") or "").upper() != "PASS":
        errors.append("result must be PASS")
    try:
        exit_code = int(binding.get("exit_code"))
    except (TypeError, ValueError):
        errors.append("exit_code must be int 0")
    else:
        if exit_code != 0:
            errors.append(f"exit_code must be 0 (got {exit_code})")
    return errors


def bound_pass_is_reusable(
    *,
    binding: Mapping[str, Any],
    current_stand_sha256: str,
    current_test_selector_or_command: str | list[str],
) -> bool:
    if validate_bound_test_evidence(binding):
        return False
    if str(binding.get("bound_stand_sha256") or "").strip() != current_stand_sha256.strip():
        return False
    bound_cmd = binding.get("test_selector_or_command")
    if isinstance(bound_cmd, list) or isinstance(current_test_selector_or_command, list):
        left = [str(x) for x in (bound_cmd if isinstance(bound_cmd, list) else [bound_cmd])]
        right = [
            str(x)
            for x in (
                current_test_selector_or_command
                if isinstance(current_test_selector_or_command, list)
                else [current_test_selector_or_command]
            )
        ]
        if left != right:
            return False
    elif str(bound_cmd).strip() != str(current_test_selector_or_command).strip():
        return False
    return True


def validate_pre_pr_reuse_fields(data: Mapping[str, str]) -> list[str]:
    """Optional PRE_PR reuse surface. Absent fields are allowed (legacy envelopes)."""
    status = str(data.get("LOCAL_TEST_EVIDENCE_REUSE_STATUS") or "").strip()
    if not status:
        return []
    errors: list[str] = []
    allowed = {REUSE_STATUS_EXECUTED, REUSE_STATUS_REUSED, REUSE_STATUS_NA}
    if status not in allowed:
        errors.append(
            f"LOCAL_TEST_EVIDENCE_REUSE_STATUS must be one of {sorted(allowed)} (got {status!r})"
        )
        return errors
    if status == REUSE_STATUS_NA:
        return errors
    stand = str(data.get("BOUND_LOCAL_TEST_STAND_SHA256") or "").strip()
    command = str(data.get("BOUND_LOCAL_TEST_COMMAND") or "").strip()
    if status in {REUSE_STATUS_EXECUTED, REUSE_STATUS_REUSED}:
        if not stand:
            errors.append("BOUND_LOCAL_TEST_STAND_SHA256 required for reuse status")
        if not command:
            errors.append("BOUND_LOCAL_TEST_COMMAND required for reuse status")
    if status == REUSE_STATUS_REUSED:
        exit_raw = str(data.get("BOUND_LOCAL_TEST_EXIT_CODE") or "").strip()
        result = str(data.get("BOUND_LOCAL_TEST_RESULT") or "").strip().upper()
        full_run = str(data.get("BOUND_LOCAL_TEST_FULL_RUN") or "").strip().lower()
        if exit_raw != "0":
            errors.append("BOUND_LOCAL_TEST_EXIT_CODE must be 0 when REUSED")
        if result != "PASS":
            errors.append("BOUND_LOCAL_TEST_RESULT must be PASS when REUSED")
        if full_run not in {"true", "1", "yes"}:
            errors.append("BOUND_LOCAL_TEST_FULL_RUN must be true when REUSED")
        binding = {
            "bound_stand_sha256": stand,
            "test_selector_or_command": command,
            "full_run": full_run in {"true", "1", "yes"},
            "result": result or "FAIL",
            "exit_code": int(exit_raw) if exit_raw.isdigit() else -1,
        }
        errors.extend(validate_bound_test_evidence(binding))
    return errors


def retained_check_ids(*, repo_root: Path | None = None) -> list[str]:
    policy = load_policy(repo_root=repo_root)
    return [str(row["check_id"]) for row in policy.get("local_checks_retained") or []]


def redundant_check_ids(*, repo_root: Path | None = None) -> list[str]:
    policy = load_policy(repo_root=repo_root)
    return [
        str(row["check_id"]) for row in policy.get("redundant_local_reexecutions_removed") or []
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Minimum local CI dedup orchestrator v1")
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument(
        "--print-policy",
        action="store_true",
        help="Print machine-readable policy summary JSON",
    )
    parser.add_argument(
        "--classify",
        metavar="CHECK_ID",
        help="Classify one local check id",
    )
    parser.add_argument("--github-context", default=None)
    parser.add_argument(
        "--local-pre-push-value",
        choices=("true", "false"),
        default="false",
    )
    parser.add_argument(
        "--bound-pass-reusable",
        choices=("true", "false"),
        default="false",
    )
    parser.add_argument(
        "--validate-binding-json",
        type=Path,
        default=None,
        help="Validate a bound test evidence JSON object",
    )
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()

    if args.print_policy:
        policy = load_policy(repo_root=repo_root)
        summary = {
            "ok": True,
            "PACKAGE_MARKER": PACKAGE_MARKER,
            "policy_id": policy["policy_id"],
            "github_required_checks_role": policy["github_required_checks_role"],
            "retained": retained_check_ids(repo_root=repo_root),
            "redundant_removed": redundant_check_ids(repo_root=repo_root),
            "required_contexts": sorted(load_required_contexts(repo_root=repo_root)),
        }
        print(json.dumps(summary, sort_keys=True, indent=2))
        return 0

    if args.validate_binding_json is not None:
        binding = json.loads(args.validate_binding_json.read_text(encoding="utf-8"))
        errors = validate_bound_test_evidence(binding)
        if errors:
            print(json.dumps({"ok": False, "errors": errors}, sort_keys=True))
            return 1
        print(json.dumps({"ok": True, "reusable": True}, sort_keys=True))
        return 0

    if args.classify:
        action = classify_local_check(
            check_id=args.classify,
            github_required_contexts=load_required_contexts(repo_root=repo_root),
            github_context_name=args.github_context,
            local_pre_push_value_required=args.local_pre_push_value == "true",
            bound_pass_reusable=args.bound_pass_reusable == "true",
        )
        print(
            json.dumps(
                {
                    "ok": True,
                    "check_id": args.classify,
                    "action": action,
                    "PACKAGE_MARKER": PACKAGE_MARKER,
                },
                sort_keys=True,
            )
        )
        return 0

    parser.error("one of --print-policy / --classify / --validate-binding-json is required")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
