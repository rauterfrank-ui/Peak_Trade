#!/usr/bin/env python3
"""
Validator Report Normalizer CLI (Phase 4E)

Command-line tool for normalizing validator reports to canonical format.

Usage:
    # Normalize from legacy report
    python scripts/aiops/normalize_validator_report.py \\
        --input .tmp/validator_report.json \\
        --out-dir .tmp/normalized

    # Normalize with runtime context (CI mode)
    python scripts/aiops/normalize_validator_report.py \\
        --input .tmp/validator_report.json \\
        --out-dir .tmp/normalized \\
        --git-sha "${GITHUB_SHA}" \\
        --run-id "${GITHUB_RUN_ID}" \\
        --workflow "${GITHUB_WORKFLOW}" \\
        --job "${GITHUB_JOB}"

    # Normalize from stdin
    cat validator_report.json | python scripts/aiops/normalize_validator_report.py \\
        --out-dir .tmp/normalized

Outputs:
    - validator_report.normalized.json (canonical, deterministic)
    - validator_report.normalized.md (derived human summary)

Exit Codes:
    0: Success
    1: Invalid input / processing error

Reference:
    docs/governance/ai_autonomy/PHASE4E_VALIDATOR_REPORT_NORMALIZATION.md
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Add src/ to path for imports
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from ai_orchestration.validator_report_normalized import (
    normalize_validator_report,
    hash_normalized_report,
)
from ai_orchestration.validator_report_schema import ValidatorReport


def load_raw_report(input_path: Optional[Path]) -> Dict[str, Any]:
    """
    Load raw validator report from file or stdin.

    Args:
        input_path: Input file path (None = stdin)

    Returns:
        Raw report dict

    Raises:
        json.JSONDecodeError: If input is invalid JSON
        FileNotFoundError: If input file doesn't exist
    """
    if input_path is None:
        # Read from stdin
        raw_json = sys.stdin.read()
        return json.loads(raw_json)
    else:
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        return json.loads(input_path.read_text(encoding="utf-8"))


def build_runtime_context(args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    """
    Build runtime context from CLI args.

    Args:
        args: Parsed CLI arguments

    Returns:
        Runtime context dict (or None if no context provided)
    """
    context = {}

    if args.git_sha:
        context["git_sha"] = args.git_sha
    if args.run_id:
        context["run_id"] = args.run_id
    if args.workflow:
        context["workflow"] = args.workflow
    if args.job:
        context["job"] = args.job

    # Always add generation timestamp if any context provided
    if context or args.timestamp:
        context["generated_at_utc"] = datetime.utcnow().isoformat() + "Z"

    return context if context else None


def main() -> int:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Normalize validator reports to canonical format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Normalize from file
  python scripts/aiops/normalize_validator_report.py \\
      --input .tmp/validator_report.json \\
      --out-dir .tmp/normalized

  # Normalize from stdin
  cat validator_report.json | python scripts/aiops/normalize_validator_report.py \\
      --out-dir .tmp/normalized

  # CI mode (with runtime context)
  python scripts/aiops/normalize_validator_report.py \\
      --input .tmp/validator_report.json \\
      --out-dir .tmp/normalized \\
      --git-sha "${GITHUB_SHA}" \\
      --run-id "${GITHUB_RUN_ID}" \\
      --workflow "${GITHUB_WORKFLOW}" \\
      --job "${GITHUB_JOB}"

  # Determinism check (run twice, compare)
  python scripts/aiops/normalize_validator_report.py \\
      --input report.json --out-dir .tmp/run1
  python scripts/aiops/normalize_validator_report.py \\
      --input report.json --out-dir .tmp/run2
  diff .tmp/run1/validator_report.normalized.json .tmp/run2/validator_report.normalized.json
        """,
    )

    # Input
    parser.add_argument(
        "--input",
        type=Path,
        help="Input validator report (JSON). If omitted, reads from stdin.",
    )

    # Output
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Output directory for normalized artifacts",
    )

    # Runtime context (optional)
    parser.add_argument(
        "--git-sha",
        help="Git commit SHA (runtime context)",
    )
    parser.add_argument(
        "--run-id",
        help="CI run ID (runtime context)",
    )
    parser.add_argument(
        "--workflow",
        help="CI workflow name (runtime context)",
    )
    parser.add_argument(
        "--job",
        help="CI job name (runtime context)",
    )
    parser.add_argument(
        "--timestamp",
        action="store_true",
        help="Add generation timestamp to runtime context",
    )

    # Options
    parser.add_argument(
        "--no-markdown",
        action="store_true",
        help="Skip Markdown summary generation",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output (exit code only)",
    )

    args = parser.parse_args()

    # =========================================================================
    # Load Raw Report
    # =========================================================================
    try:
        raw_report = load_raw_report(args.input)
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid JSON input: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ ERROR: Failed to load input: {e}", file=sys.stderr)
        return 1

    # =========================================================================
    # Build Runtime Context
    # =========================================================================
    runtime_context = build_runtime_context(args)

    # =========================================================================
    # Normalize Report
    # =========================================================================
    try:
        normalized = normalize_validator_report(
            raw_report=raw_report,
            runtime_context=runtime_context,
        )
    except Exception as e:
        print(f"❌ ERROR: Normalization failed: {e}", file=sys.stderr)
        return 1

    # =========================================================================
    # Write Outputs
    # =========================================================================
    args.out_dir.mkdir(parents=True, exist_ok=True)

    # (1) JSON (canonical)
    json_path = args.out_dir / "validator_report.normalized.json"
    try:
        normalized.write_json(json_path, deterministic=True)
    except Exception as e:
        print(f"❌ ERROR: Failed to write JSON: {e}", file=sys.stderr)
        return 1

    # (2) Markdown (derived)
    if not args.no_markdown:
        md_path = args.out_dir / "validator_report.normalized.md"
        try:
            normalized.write_summary_md(md_path)
        except Exception as e:
            print(f"❌ ERROR: Failed to write Markdown: {e}", file=sys.stderr)
            return 1

    # =========================================================================
    # Print Summary
    # =========================================================================
    if not args.quiet:
        report_hash = hash_normalized_report(normalized)
        print(f"✅ Normalization complete")
        print(f"   Schema version: {normalized.schema_version}")
        print(f"   Tool: {normalized.tool.name} v{normalized.tool.version}")
        print(f"   Subject: {normalized.subject}")
        print(f"   Result: {normalized.result.value}")
        print(f"   Checks: {normalized.summary.passed} passed, {normalized.summary.failed} failed")
        print(f"   Canonical hash: {report_hash[:16]}...")
        print(f"   JSON: {json_path}")
        if not args.no_markdown:
            print(f"   Markdown: {md_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
