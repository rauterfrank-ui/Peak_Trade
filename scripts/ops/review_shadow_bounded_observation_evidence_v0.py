#!/usr/bin/env python3
"""Review Shadow bounded dry-run observation evidence without running anything.

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
    BOUNDED_SHADOW_DURABLE_RUN_REQUIRED_REL_PATHS,
    validate_durable_primary_evidence_root,
)
from scripts.ops.run_paper_only_bounded_observation_adapter_v0 import (
    FINAL_MACHINE_LINES_FILENAME,
    REPO_HEAD_SHA_PREFIX_MACHINE_LINE_KEY,
)
from scripts.ops.run_shadow_bounded_observation_adapter_v0 import parse_machine_lines

PASS = "PASS"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
REVIEW_REQUIRED_EXIT = 1
USAGE_EXIT = 2

SCHEMA_VERSION = "review_shadow_bounded_observation_evidence.v0"
WRAPPER_EVIDENCE_DIR = "wrapper_evidence"
BOUNDED_SHADOW_DRY_RUN_MD = "SHADOW_247_FUTURES_BOUNDED_SHADOW_DRY_RUN.md"
STEPS_JSONL = "steps.jsonl"
MANIFEST_JSON = "manifest.json"
EXPECTED_MANIFEST_SCHEMA = "shadow_247_futures_bounded_shadow_dry_run.v0"
SAFETY_STRINGS = ("NO_BROKER", "NO_NETWORK", "NO_ORDER_SUBMISSION")
FORBIDDEN_GATE_CLAIMS = (
    "BLOCKER_CLEARANCE_GRANTED=true",
    "SHADOW_READY=true",
    "SHADOW_RUNTIME_APPROVAL_GRANTED=true",
    "PREFLIGHT_BLOCKED=false",
)
MANIFEST_GIT_SHA_PREFIX_FIELD = "git_sha_prefix"
RUN_METADATA_FILENAME = "RUN_METADATA.json"
RUN_METADATA_GIT_SHA_PREFIX_FIELD = "repo_head_sha_prefix"
GIT_SHA_PREFIX_CANONICAL_LENGTH = 12
GIT_PROVENANCE_MISSING = "GIT_PROVENANCE_MISSING"
GIT_PROVENANCE_UNKNOWN = "GIT_PROVENANCE_UNKNOWN"
GIT_PROVENANCE_INVALID = "GIT_PROVENANCE_INVALID"
GIT_PROVENANCE_MISMATCH = "GIT_PROVENANCE_MISMATCH"
_GIT_PROVENANCE_UNKNOWN_SENTINELS = frozenset(
    {
        "UNKNOWN",
        "NOT_AVAILABLE",
        "MISSING",
        "UNKNOWN_GITFILE_LAYOUT",
        "UNKNOWN_GITDIR_MISSING",
        "UNKNOWN_GITDIR_UNRESOLVABLE",
        "UNKNOWN_COMMONDIR_UNRESOLVABLE",
        "UNKNOWN_COMMONDIR_MISSING",
        "UNKNOWN_INCOMPLETE_GIT_STATE",
        "UNKNOWN_GIT_INDEX_LOCKED",
        "UNKNOWN_HEAD_MISSING",
        "UNKNOWN_REF_MISSING",
        "UNKNOWN_RAW_HEAD_LAYOUT",
    }
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


def _resolve_wrapper_evidence_root(staging_root: Path) -> Path:
    nested = staging_root / WRAPPER_EVIDENCE_DIR
    if nested.is_dir():
        return nested
    return staging_root


def _is_git_provenance_unknown_sentinel(value: str) -> bool:
    if value in _GIT_PROVENANCE_UNKNOWN_SENTINELS:
        return True
    return value.startswith("UNKNOWN_")


def _is_valid_canonical_git_sha_prefix(value: str) -> bool:
    if len(value) != GIT_SHA_PREFIX_CANONICAL_LENGTH:
        return False
    return all(ch in "0123456789abcdef" for ch in value.lower())


def _classify_git_provenance_value(raw: Any) -> tuple[str | None, str | None]:
    if raw is None:
        return None, GIT_PROVENANCE_MISSING
    if not isinstance(raw, str):
        return None, GIT_PROVENANCE_MISSING
    value = raw.strip()
    if not value:
        return None, GIT_PROVENANCE_MISSING
    if _is_git_provenance_unknown_sentinel(value):
        return None, GIT_PROVENANCE_UNKNOWN
    if not _is_valid_canonical_git_sha_prefix(value):
        return None, GIT_PROVENANCE_INVALID
    return value, None


def _append_git_provenance_issue(
    issues: list[str],
    *,
    reason: str,
    source: str,
    detail: str,
) -> None:
    issues.append(f"{reason}: {source} {detail}")


def _validate_git_provenance_field(
    issues: list[str],
    checks: dict[str, bool],
    *,
    check_key: str,
    source: str,
    field_name: str,
    raw: Any,
    provenance_values: dict[str, str],
    provenance_key: str,
) -> None:
    value, reason = _classify_git_provenance_value(raw)
    checks[check_key] = reason is None
    if reason is not None:
        _append_git_provenance_issue(
            issues,
            reason=reason,
            source=source,
            detail=f"{field_name} invalid or missing",
        )
        return
    assert value is not None
    provenance_values[provenance_key] = value


def _validate_runtime_git_provenance(
    staging_root: Path,
    *,
    manifest_payload: Any | None,
    issues: list[str],
    checks: dict[str, bool],
) -> None:
    provenance_values: dict[str, str] = {}

    if isinstance(manifest_payload, dict) and checks.get("manifest_schema_match"):
        _validate_git_provenance_field(
            issues,
            checks,
            check_key="manifest_git_sha_prefix_valid",
            source=MANIFEST_JSON,
            field_name=MANIFEST_GIT_SHA_PREFIX_FIELD,
            raw=manifest_payload.get(MANIFEST_GIT_SHA_PREFIX_FIELD),
            provenance_values=provenance_values,
            provenance_key="manifest",
        )

    run_metadata_path = staging_root / RUN_METADATA_FILENAME
    if run_metadata_path.is_file():
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
    if machine_lines_path.is_file():
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

    evidence_root = _resolve_wrapper_evidence_root(staging_root)
    checks["evidence_root_exists"] = evidence_root.is_dir()
    if not checks["evidence_root_exists"]:
        issues.append(f"evidence root missing: {evidence_root}")

    markdown = evidence_root / BOUNDED_SHADOW_DRY_RUN_MD
    checks["markdown_present"] = markdown.is_file()
    if not checks["markdown_present"]:
        issues.append(f"missing {BOUNDED_SHADOW_DRY_RUN_MD}")
    else:
        md_text = markdown.read_text(encoding="utf-8", errors="replace")
        checks["markdown_has_safety_strings"] = _text_contains_any(md_text, SAFETY_STRINGS)
        if not checks["markdown_has_safety_strings"]:
            issues.append(f"{BOUNDED_SHADOW_DRY_RUN_MD} missing safety boundary strings")
        checks["markdown_no_gate_claims"] = not _text_contains_any(md_text, FORBIDDEN_GATE_CLAIMS)
        if not checks["markdown_no_gate_claims"]:
            issues.append(f"{BOUNDED_SHADOW_DRY_RUN_MD} must not claim gate clearance")

    steps = evidence_root / STEPS_JSONL
    checks["steps_present"] = steps.is_file()
    if not checks["steps_present"]:
        issues.append(f"missing {STEPS_JSONL}")
    elif not steps.read_text(encoding="utf-8", errors="replace").strip():
        checks["steps_non_empty"] = False
        issues.append(f"{STEPS_JSONL} is empty")
    else:
        checks["steps_non_empty"] = True

    manifest_path = evidence_root / MANIFEST_JSON
    checks["manifest_present"] = manifest_path.is_file()
    manifest_payload: Any | None = None
    if not checks["manifest_present"]:
        issues.append(f"missing {MANIFEST_JSON}")
    else:
        manifest_payload, manifest_err = _load_json(manifest_path)
        checks["manifest_valid_json"] = manifest_err is None
        if manifest_err:
            issues.append(manifest_err)
        elif isinstance(manifest_payload, dict):
            schema = manifest_payload.get("schema")
            checks["manifest_schema_match"] = schema == EXPECTED_MANIFEST_SCHEMA
            if not checks["manifest_schema_match"]:
                issues.append(
                    f"{MANIFEST_JSON} schema must be {EXPECTED_MANIFEST_SCHEMA!r}, got {schema!r}"
                )
            manifest_blob = json.dumps(manifest_payload, sort_keys=True)
            checks["manifest_has_safety_strings"] = _text_contains_any(
                manifest_blob, SAFETY_STRINGS
            )
            if not checks["manifest_has_safety_strings"]:
                issues.append(f"{MANIFEST_JSON} missing safety boundary strings")
        else:
            checks["manifest_schema_match"] = False
            issues.append(f"{MANIFEST_JSON} must be a JSON object")

    logs_dir = staging_root / "logs"
    stdout_log = logs_dir / "wrapper_stdout.log"
    stderr_log = logs_dir / "wrapper_stderr.log"
    checks["stdout_log_present"] = stdout_log.is_file()
    checks["stderr_log_present"] = stderr_log.is_file()
    if not checks["stdout_log_present"]:
        issues.append("missing logs/wrapper_stdout.log")
    if not checks["stderr_log_present"]:
        issues.append("missing logs/wrapper_stderr.log")

    _validate_runtime_git_provenance(
        staging_root,
        manifest_payload=manifest_payload,
        issues=issues,
        checks=checks,
    )

    verdict = PASS if not issues else REVIEW_REQUIRED
    result: dict[str, Any] = {
        "verdict": verdict,
        "schema_version": SCHEMA_VERSION,
        "staging_root": str(staging_root.resolve()),
        "evidence_root": str(evidence_root.resolve()),
        "checks": checks,
        "issues": issues,
        "non_authorizing": True,
    }

    if durable_run_root is not None:
        durable_root = durable_run_root.resolve()
        ok, msg, durable_detail = validate_durable_primary_evidence_root(
            durable_root,
            required_rel_paths=BOUNDED_SHADOW_DURABLE_RUN_REQUIRED_REL_PATHS,
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
            "Review Shadow bounded dry-run observation evidence. "
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
