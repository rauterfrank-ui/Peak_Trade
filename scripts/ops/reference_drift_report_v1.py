#!/usr/bin/env python3
"""
Reference Drift Visibility Report v1 — non-blocking analysis layer.

Runs the canonical docs token policy validator in global (--all) mode, classifies
violations for visibility, and writes a structured JSON report. Does not modify
source files or fail CI-style on violations.

Classification (review-input only):
  LEGACY  — historical / low-risk illustrative drift (non-blocking)
  BROKEN  — potentially critical missing or broken reference surface
  UNKNOWN — unclassified violations

NO-LIVE: local docs / git metadata only — not a trading or execution path.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "peak_trade.reference_drift_report.v1"

REPO_PATH_EXTENSIONS = (
    ".py",
    ".toml",
    ".yml",
    ".yaml",
    ".md",
    ".txt",
    ".json",
    ".sh",
    ".sql",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".css",
    ".html",
    ".xml",
    ".csv",
    ".log",
)

CRITICAL_DOC_PREFIXES = (
    "docs/ops/runbooks/",
    "docs/ops/specs/",
    "docs/governance/",
)

LEGACY_DOC_MARKERS = (
    "IMPLEMENTATION_REPORT",
    "MERGE_LOG",
    "docs/ops/reviews/",
    "docs/ops/planning/",
    "docs/archive/",
)

GENERIC_PLACEHOLDER_PATTERN = re.compile(
    r"^(some|your|path|example|foo|bar|test)/",
    re.IGNORECASE,
)


def repo_root() -> Path:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise SystemExit("Error: Not in a git repository") from exc
    return Path(out)


def git_head(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        return "unknown"


def _looks_like_repo_path(token: str) -> bool:
    return any(token.endswith(ext) for ext in REPO_PATH_EXTENSIONS)


def classify_violation(violation: dict[str, Any], root: Path) -> str:
    """Classify a single validator violation as LEGACY, BROKEN, or UNKNOWN."""
    token_type = str(violation.get("token_type", ""))
    file_path = str(violation.get("file", ""))
    token = str(violation.get("token", ""))

    if token_type == "ERROR":
        return "BROKEN"

    if any(marker in file_path for marker in LEGACY_DOC_MARKERS):
        return "LEGACY"

    if GENERIC_PLACEHOLDER_PATTERN.match(token):
        return "LEGACY"

    if _looks_like_repo_path(token):
        candidate = root / token
        if not candidate.exists():
            if any(file_path.startswith(prefix) for prefix in CRITICAL_DOC_PREFIXES):
                return "BROKEN"
            parent = candidate.parent
            if parent.exists() and str(parent) != str(root):
                return "BROKEN"

    if any(file_path.startswith(prefix) for prefix in CRITICAL_DOC_PREFIXES):
        return "BROKEN"

    return "UNKNOWN"


def run_validator(root: Path, json_out: Path) -> dict[str, Any]:
    validator = root / "scripts" / "ops" / "validate_docs_token_policy.py"
    if not validator.is_file():
        raise SystemExit(f"Error: validator not found: {validator}")

    json_out.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, str(validator), "--all", "--json", str(json_out)],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if proc.returncode not in (0, 1):
        raise SystemExit(f"Validator failed (exit {proc.returncode}): {proc.stderr or proc.stdout}")

    if not json_out.is_file():
        raise SystemExit("Validator did not produce JSON output")

    return json.loads(json_out.read_text(encoding="utf-8"))


def build_report(
    validator_report: dict[str, Any],
    *,
    root: Path,
    timestamp: str,
    head: str,
) -> dict[str, Any]:
    legacy_list: list[dict[str, Any]] = []
    broken_list: list[dict[str, Any]] = []
    unknown_count = 0
    affected_files: set[str] = set()

    for result in validator_report.get("results", []):
        for violation in result.get("violations", []):
            if not isinstance(violation, dict):
                continue
            classification = classify_violation(violation, root)
            entry = {
                **violation,
                "classification": classification,
            }
            file_path = str(violation.get("file", ""))
            if file_path:
                affected_files.add(file_path)

            if classification == "LEGACY":
                legacy_list.append(entry)
            elif classification == "BROKEN":
                broken_list.append(entry)
            else:
                unknown_count += 1

    total_violations = len(legacy_list) + len(broken_list) + unknown_count

    return {
        "schema": SCHEMA,
        "total_violations": total_violations,
        "affected_files": sorted(affected_files),
        "classification_counts": {
            "LEGACY": len(legacy_list),
            "BROKEN": len(broken_list),
            "UNKNOWN": unknown_count,
        },
        "legacy_list": legacy_list,
        "broken_list": broken_list,
        "timestamp": timestamp,
        "git_head": head,
        "validator_summary": {
            "mode": validator_report.get("mode"),
            "files_scanned": validator_report.get("files_scanned"),
            "files_with_violations": validator_report.get("files_with_violations"),
        },
        "non_blocking": True,
    }


def write_report(report: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a non-blocking reference drift visibility report from "
            "validate_docs_token_policy.py --all output."
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output JSON path (default: reports/reference_drift_v1.json)",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    out_path = args.out or (root / "reports" / "reference_drift_v1.json")
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    head = git_head(root)

    temp_validator_json = out_path.parent / ".reference_drift_validator_scratch.json"
    try:
        validator_report = run_validator(root, temp_validator_json)
        report = build_report(validator_report, root=root, timestamp=timestamp, head=head)
        write_report(report, out_path)
    finally:
        if temp_validator_json.exists():
            temp_validator_json.unlink()

    print(f"Reference drift report written to: {out_path}")
    print(
        "Violations: "
        f"total={report['total_violations']} "
        f"legacy={report['classification_counts']['LEGACY']} "
        f"broken={report['classification_counts']['BROKEN']} "
        f"unknown={report['classification_counts']['UNKNOWN']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
