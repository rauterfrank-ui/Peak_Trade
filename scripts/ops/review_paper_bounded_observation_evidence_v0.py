#!/usr/bin/env python3
"""Review Paper bounded observation closeout evidence without running anything.

Taxonomy cross-reference (review-input-only): indexed in
``docs/ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md`` §10
(bounded observation evidence review scripts).

Non-authorizing offline review only. Does not execute bounded observation adapters.
Does not grant Live/broker/exchange approval. Does not override scheduler, preflight,
or operator approval boundaries.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import (
    PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS,
    validate_durable_primary_evidence_root,
)
from scripts.ops.review_shadow_bounded_observation_evidence_v0 import (
    GIT_PROVENANCE_MISMATCH,
    GIT_PROVENANCE_MISSING,
    RUN_METADATA_GIT_SHA_PREFIX_FIELD,
    _append_git_provenance_issue,
    _validate_git_provenance_field,
)
from scripts.ops.run_paper_only_bounded_observation_adapter_v0 import (
    FINAL_MACHINE_LINES_FILENAME,
    REPO_HEAD_SHA_PREFIX_MACHINE_LINE_KEY,
    parse_machine_lines,
)

PASS = "PASS"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
REVIEW_REQUIRED_EXIT = 1
USAGE_EXIT = 2

SCHEMA_VERSION = "review_paper_bounded_observation_evidence.v0"
RUN_METADATA_FILENAME = "RUN_METADATA.json"
FORBIDDEN_GATE_CLAIMS = (
    "BLOCKER_CLEARANCE_GRANTED=true",
    "PAPER_RUNTIME_APPROVAL_GRANTED=true",
    "LIVE_ALLOWED=true",
    "PREFLIGHT_BLOCKED=false",
)


def _consume_argv(argv: list[str] | None) -> list[str]:
    if argv is None:
        return sys.argv[1:]
    if argv and not argv[0].startswith("-"):
        return list(argv[1:])
    return list(argv)


def _load_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"{path.name} is not valid JSON: {exc}"


def _text_contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _validate_runtime_git_provenance(
    staging_root: Path,
    *,
    issues: list[str],
    checks: dict[str, bool],
) -> None:
    provenance_values: dict[str, str] = {}

    run_metadata_path = staging_root / RUN_METADATA_FILENAME
    checks["run_metadata_present"] = run_metadata_path.is_file()
    if not checks["run_metadata_present"]:
        issues.append(f"missing {RUN_METADATA_FILENAME}")
        checks["run_metadata_repo_head_sha_prefix_valid"] = False
        _append_git_provenance_issue(
            issues,
            reason=GIT_PROVENANCE_MISSING,
            source=RUN_METADATA_FILENAME,
            detail=f"{RUN_METADATA_GIT_SHA_PREFIX_FIELD} invalid or missing",
        )
    else:
        run_metadata_payload, run_metadata_err = _load_json(run_metadata_path)
        if run_metadata_err:
            checks["run_metadata_repo_head_sha_prefix_valid"] = False
            issues.append(run_metadata_err)
        elif isinstance(run_metadata_payload, dict):
            _validate_git_provenance_field(
                issues,
                checks,
                check_key="run_metadata_repo_head_sha_prefix_valid",
                source=RUN_METADATA_FILENAME,
                field_name=RUN_METADATA_GIT_SHA_PREFIX_FIELD,
                raw=run_metadata_payload.get(RUN_METADATA_GIT_SHA_PREFIX_FIELD),
                provenance_values=provenance_values,
                provenance_key="run_metadata",
            )
        else:
            checks["run_metadata_repo_head_sha_prefix_valid"] = False
            issues.append(f"{RUN_METADATA_FILENAME} must be a JSON object")

    machine_lines_path = staging_root / FINAL_MACHINE_LINES_FILENAME
    checks["final_machine_lines_present"] = machine_lines_path.is_file()
    if not checks["final_machine_lines_present"]:
        issues.append(f"missing {FINAL_MACHINE_LINES_FILENAME}")
        checks["final_machine_lines_repo_head_sha_prefix_valid"] = False
        _append_git_provenance_issue(
            issues,
            reason=GIT_PROVENANCE_MISSING,
            source=FINAL_MACHINE_LINES_FILENAME,
            detail=f"{REPO_HEAD_SHA_PREFIX_MACHINE_LINE_KEY} invalid or missing",
        )
    else:
        machine_fields = parse_machine_lines(
            machine_lines_path.read_text(encoding="utf-8", errors="replace")
        )
        _validate_git_provenance_field(
            issues,
            checks,
            check_key="final_machine_lines_repo_head_sha_prefix_valid",
            source=FINAL_MACHINE_LINES_FILENAME,
            field_name=REPO_HEAD_SHA_PREFIX_MACHINE_LINE_KEY,
            raw=machine_fields.get(REPO_HEAD_SHA_PREFIX_MACHINE_LINE_KEY),
            provenance_values=provenance_values,
            provenance_key="final_machine_lines",
        )

    if len(provenance_values) >= 2:
        unique_values = set(provenance_values.values())
        checks["git_provenance_consistent"] = len(unique_values) == 1
        if len(unique_values) > 1:
            joined = ", ".join(f"{key}={value}" for key, value in sorted(provenance_values.items()))
            _append_git_provenance_issue(
                issues,
                reason=GIT_PROVENANCE_MISMATCH,
                source="runtime git provenance",
                detail=f"values disagree ({joined})",
            )


def review_evidence(
    staging_root: Path,
    *,
    durable_run_root: Path | None = None,
) -> dict[str, Any]:
    issues: list[str] = []
    checks: dict[str, bool] = {}

    checks["staging_root_exists"] = staging_root.is_dir()
    if not checks["staging_root_exists"]:
        issues.append(f"staging root missing: {staging_root}")

    closeout = staging_root / "CLOSEOUT.md"
    checks["closeout_present"] = closeout.is_file()
    if not checks["closeout_present"]:
        issues.append("missing CLOSEOUT.md")
    else:
        closeout_text = closeout.read_text(encoding="utf-8", errors="replace")
        checks["closeout_no_gate_claims"] = not _text_contains_any(
            closeout_text, FORBIDDEN_GATE_CLAIMS
        )
        if not checks["closeout_no_gate_claims"]:
            issues.append("CLOSEOUT.md must not claim gate clearance")

    _validate_runtime_git_provenance(staging_root, issues=issues, checks=checks)

    verdict = PASS if not issues else REVIEW_REQUIRED
    result: dict[str, Any] = {
        "verdict": verdict,
        "schema_version": SCHEMA_VERSION,
        "staging_root": str(staging_root.resolve()),
        "checks": checks,
        "issues": issues,
        "non_authorizing": True,
    }

    if durable_run_root is not None:
        durable_root = durable_run_root.resolve()
        ok, msg, durable_detail = validate_durable_primary_evidence_root(
            durable_root,
            required_rel_paths=PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS,
        )
        result["durable_run_root"] = str(durable_root)
        result["durable_checks"] = durable_detail.get("checks", {})
        durable_issues = list(durable_detail.get("issues", []))
        if not ok and msg and msg not in durable_issues:
            durable_issues.insert(0, msg)
        if durable_issues:
            result["issues"] = list(result.get("issues", [])) + durable_issues
            result["checks"]["durable_primary_evidence_valid"] = False
            result["verdict"] = REVIEW_REQUIRED
        else:
            result["checks"]["durable_primary_evidence_valid"] = True

    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Review Paper bounded observation closeout evidence. "
            "Non-authorizing; does not claim readiness or gate clearance."
        )
    )
    parser.add_argument("--staging-root", type=Path, required=True)
    parser.add_argument(
        "--durable-run-root",
        type=Path,
        default=None,
        help=(
            "Optional durable primary evidence run root outside /tmp (Preflight §2a.1). "
            "Default off; staging-only review when omitted."
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional path to write REVIEW_RESULT.json",
    )
    parser.add_argument("--json", action="store_true", help="Emit review JSON to stdout.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    try:
        args = parser.parse_args(_consume_argv(argv))
    except SystemExit as exc:
        if exc.code in (0, None):
            raise
        return USAGE_EXIT

    staging_root = args.staging_root.expanduser().resolve()
    if not staging_root.is_dir():
        print(f"staging root must exist: {staging_root}", file=sys.stderr)
        return USAGE_EXIT

    durable_run_root: Path | None = None
    if args.durable_run_root is not None:
        durable_run_root = args.durable_run_root.expanduser().resolve()
        if not durable_run_root.is_dir():
            print(f"durable run root must exist: {durable_run_root}", file=sys.stderr)
            return USAGE_EXIT

    result = review_evidence(staging_root, durable_run_root=durable_run_root)
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload + "\n", encoding="utf-8")
    if args.json or args.out is None:
        print(payload)
    return 0 if result["verdict"] == PASS else REVIEW_REQUIRED_EXIT


if __name__ == "__main__":
    raise SystemExit(main())
