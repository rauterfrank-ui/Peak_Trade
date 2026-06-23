#!/usr/bin/env python3
"""Fail-closed verifier for PRE_PR_HARD_BOUNDED_VALIDATION result surfaces (v0).

Reads the canonical machine-readable result file (default: .cursor/PRE_PR_VALIDATION_RESULT.env)
and enforces the global agent-progress-checkpoint PRE_PR contract before Auto-PR dispatch.

Exit 0 only when all required fields pass. Exit 1 with stderr diagnostics otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

CANONICAL_RESULT_PATH = Path(".cursor/PRE_PR_VALIDATION_RESULT.env")

ALLOWED_VERDICTS = frozenset(
    {
        "PRE_PR_VALIDATION_PASS",
        "PRE_PR_VALIDATION_PASS_TIMING_NOT_REQUIRED",
    }
)

REQUIRED_TRUE_FIELDS = (
    "FINAL_DIFF_FROZEN",
    "FINAL_FILES_MATCH",
    "FINAL_DIFF_PATH_EQUIVALENCE_CONFIRMED",
    "REUSE_BEFORE_NEW_CHECKED",
    "COMMIT_ALLOWED",
    "PUSH_ALLOWED",
    "PR_ALLOWED",
)

REQUIRED_PASS_FIELDS = ("LOCAL_GATE_BATCH_RESULT",)

REQUIRED_FALSE_FIELDS = ("UNVALIDATED_FILES_REMAIN",)

TARGET_MAX_SECONDS = 840
HARD_STOP_SECONDS = 900
MINIMUM_SAFETY_MARGIN_SECONDS = 180


def _parse_env_file(text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"invalid line (expected KEY=value): {raw_line!r}")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not re.fullmatch(r"[A-Z0-9_]+", key):
            raise ValueError(f"invalid key: {key!r}")
        data[key] = value
    return data


def _is_true(value: str) -> bool:
    return value.lower() in {"true", "1", "yes"}


def _is_false(value: str) -> bool:
    return value.lower() in {"false", "0", "no"}


def _parse_int_field(data: dict[str, str], key: str) -> int | None:
    if key not in data or data[key] in {"", "N/A"}:
        return None
    return int(data[key])


def _diff_sha256(base_ref: str) -> str:
    proc = subprocess.run(
        ["git", "diff", f"{base_ref}...HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode not in {0, 1}:
        raise RuntimeError(proc.stderr.strip() or "git diff failed")
    digest = hashlib.sha256(proc.stdout.encode("utf-8")).hexdigest()
    return digest


def verify_pre_pr_validation_result(
    data: dict[str, str],
    *,
    check_diff_sha: bool = False,
    base_ref: str = "origin/main",
    repo_root: Path | None = None,
) -> list[str]:
    """Return a list of blocking error messages. Empty list means PASS."""
    errors: list[str] = []

    verdict = data.get("PRE_PR_VALIDATION_VERDICT", "").strip()
    if not verdict:
        errors.append("missing PRE_PR_VALIDATION_VERDICT")
    elif verdict == "PRE_PR_VALIDATION_FAIL_CLOSED":
        errors.append("PRE_PR_VALIDATION_VERDICT=PRE_PR_VALIDATION_FAIL_CLOSED")
    elif verdict not in ALLOWED_VERDICTS:
        errors.append(f"unknown PRE_PR_VALIDATION_VERDICT={verdict!r}")

    for key in REQUIRED_TRUE_FIELDS:
        if key not in data:
            errors.append(f"missing {key}")
        elif not _is_true(data[key]):
            errors.append(f"{key} must be true (got {data[key]!r})")

    for key in REQUIRED_PASS_FIELDS:
        if data.get(key) != "PASS":
            errors.append(f"{key} must be PASS (got {data.get(key)!r})")

    for key in REQUIRED_FALSE_FIELDS:
        if key not in data:
            errors.append(f"missing {key}")
        elif not _is_false(data[key]):
            errors.append(f"{key} must be false (got {data[key]!r})")

    manifest_rc = data.get("MANIFEST_VERIFY_RC")
    if manifest_rc is None:
        errors.append("missing MANIFEST_VERIFY_RC")
    elif manifest_rc != "0":
        errors.append(f"MANIFEST_VERIFY_RC must be 0 (got {manifest_rc!r})")

    timing_required_raw = data.get("TIMING_PROOF_REQUIRED", "").lower()
    timing_required = timing_required_raw in {"true", "1", "yes"}
    timing_not_required = timing_required_raw in {"false", "0", "no"}

    if not timing_required and not timing_not_required:
        errors.append(
            f"TIMING_PROOF_REQUIRED must be true or false (got {data.get('TIMING_PROOF_REQUIRED')!r})"
        )

    if timing_required:
        if verdict != "PRE_PR_VALIDATION_PASS":
            errors.append(
                "TIMING_PROOF_REQUIRED=true requires PRE_PR_VALIDATION_VERDICT=PRE_PR_VALIDATION_PASS"
            )
        timing_status = data.get("TIMING_PROOF_STATUS", "")
        if timing_status != "PASS":
            errors.append(f"TIMING_PROOF_STATUS must be PASS (got {timing_status!r})")
        wallclock = _parse_int_field(data, "TIMING_WALLCLOCK_SECONDS")
        if wallclock is None:
            errors.append("missing TIMING_WALLCLOCK_SECONDS")
        elif wallclock > TARGET_MAX_SECONDS:
            errors.append(
                f"TIMING_WALLCLOCK_SECONDS={wallclock} exceeds TARGET_MAX_SECONDS={TARGET_MAX_SECONDS}"
            )
        hard_stop = _parse_int_field(data, "TIMING_HARD_STOP_SECONDS")
        if hard_stop is not None and hard_stop > HARD_STOP_SECONDS:
            errors.append(
                f"TIMING_HARD_STOP_SECONDS={hard_stop} exceeds allowed {HARD_STOP_SECONDS}"
            )
        margin = _parse_int_field(data, "TIMING_SAFETY_MARGIN_SECONDS")
        if margin is not None and margin < MINIMUM_SAFETY_MARGIN_SECONDS:
            errors.append(
                f"TIMING_SAFETY_MARGIN_SECONDS={margin} below minimum {MINIMUM_SAFETY_MARGIN_SECONDS}"
            )
        if data.get("FINAL_DIFF_PATH_EQUIVALENCE_CONFIRMED", "").lower() != "true":
            errors.append(
                "TIMING_PROOF_REQUIRED=true requires FINAL_DIFF_PATH_EQUIVALENCE_CONFIRMED=true"
            )
    else:
        if verdict != "PRE_PR_VALIDATION_PASS_TIMING_NOT_REQUIRED":
            errors.append(
                "TIMING_PROOF_REQUIRED=false requires "
                "PRE_PR_VALIDATION_VERDICT=PRE_PR_VALIDATION_PASS_TIMING_NOT_REQUIRED"
            )
        justification = data.get("TIMING_PROOF_STATUS", "")
        has_text_justification = bool(
            data.get("TIMING_PROOF_NOT_REQUIRED_JUSTIFICATION", "").strip()
        )
        if justification != "TIMING_PROOF_NOT_REQUIRED_JUSTIFIED" and not has_text_justification:
            errors.append(
                "TIMING_PROOF_REQUIRED=false requires TIMING_PROOF_STATUS="
                "TIMING_PROOF_NOT_REQUIRED_JUSTIFIED or TIMING_PROOF_NOT_REQUIRED_JUSTIFICATION"
            )
        # Hard-stop / fail timing must never coexist with timing-not-required pass.
        if data.get("TIMING_PROOF_STATUS") == "FAIL":
            errors.append("TIMING_PROOF_STATUS=FAIL cannot pass when timing proof was required")
        wallclock = _parse_int_field(data, "TIMING_WALLCLOCK_SECONDS")
        if wallclock is not None and wallclock >= HARD_STOP_SECONDS:
            errors.append(
                f"TIMING_WALLCLOCK_SECONDS={wallclock} reached hard stop; cannot claim timing not required"
            )

    if check_diff_sha:
        expected = data.get("FINAL_DIFF_SHA256", "").strip()
        if not expected:
            errors.append("missing FINAL_DIFF_SHA256 for diff verification")
        else:
            root = repo_root or Path.cwd()
            try:
                actual = _diff_sha256(base_ref)
            except (RuntimeError, subprocess.SubprocessError) as exc:
                errors.append(f"could not compute diff sha256: {exc}")
            else:
                if actual != expected:
                    errors.append(
                        f"FINAL_DIFF_SHA256 mismatch: expected {expected}, actual {actual}"
                    )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--result-file",
        type=Path,
        default=CANONICAL_RESULT_PATH,
        help="Path to PRE_PR_VALIDATION_RESULT.env (default: .cursor/PRE_PR_VALIDATION_RESULT.env)",
    )
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="Base ref for optional diff SHA verification",
    )
    parser.add_argument(
        "--check-diff-sha",
        action="store_true",
        help="Verify FINAL_DIFF_SHA256 matches git diff against base-ref",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root for git operations (default: cwd)",
    )
    args = parser.parse_args(argv)

    if not args.result_file.is_file():
        print(
            f"PRE_PR_VALIDATION_FAIL_CLOSED: missing result file: {args.result_file}",
            file=sys.stderr,
        )
        return 1

    try:
        data = _parse_env_file(args.result_file.read_text(encoding="utf-8"))
    except ValueError as exc:
        print(f"PRE_PR_VALIDATION_FAIL_CLOSED: {exc}", file=sys.stderr)
        return 1

    errors = verify_pre_pr_validation_result(
        data,
        check_diff_sha=args.check_diff_sha,
        base_ref=args.base_ref,
        repo_root=args.repo_root,
    )
    if errors:
        print("PRE_PR_VALIDATION_FAIL_CLOSED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"PRE_PR_VALIDATION_OK verdict={data.get('PRE_PR_VALIDATION_VERDICT')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
