#!/usr/bin/env python3
"""Review Shadow bounded dry-run observation evidence without running anything."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

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


def review_evidence(staging_root: Path) -> dict[str, Any]:
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

    verdict = PASS if not issues else REVIEW_REQUIRED
    return {
        "verdict": verdict,
        "schema_version": SCHEMA_VERSION,
        "staging_root": str(staging_root.resolve()),
        "evidence_root": str(evidence_root.resolve()),
        "checks": checks,
        "issues": issues,
        "non_authorizing": True,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Review Shadow bounded dry-run observation evidence. "
            "Non-authorizing; does not claim readiness or gate clearance."
        )
    )
    parser.add_argument("--staging-root", type=Path, required=True)
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

    result = review_evidence(staging_root)
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload + "\n", encoding="utf-8")
    if args.json or args.out is None:
        print(payload)
    return 0 if result["verdict"] == PASS else REVIEW_REQUIRED_EXIT


if __name__ == "__main__":
    raise SystemExit(main())
