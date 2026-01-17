#!/usr/bin/env python3
"""
Generate Trend Seed from Normalized Validator Report (Phase 5A)

Consumes Phase 4E normalized validator reports and generates deterministic Trend Seeds.

Usage:
    python scripts/aiops/generate_trend_seed_from_normalized_report.py \\
        --input validator_report.normalized.json \\
        --out-dir .tmp/trend_seed \\
        --repo owner/repo \\
        --workflow-name "L4 Critic Replay Determinism" \\
        --run-id 12345 \\
        --head-sha abc123 \\
        --ref refs/heads/main \\
        --run-created-at "2026-01-11T12:00:00Z"

Exit Codes:
    0: Success
    1: Error (validation failure, missing file, etc.)

Reference:
    docs/ops/runbooks/RUNBOOK_PHASE5A_NORMALIZED_REPORT_CONSUMER_TREND_SEED_CURSOR_MULTI_AGENT.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ai_orchestration.trends.trend_seed_consumer import (
    TrendSeedError,
    generate_trend_seed,
    load_normalized_report,
    render_markdown_summary,
    write_deterministic_json,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate Trend Seed from Normalized Validator Report (Phase 5A)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Input
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to validator_report.normalized.json",
    )

    # Output
    parser.add_argument(
        "--out-dir",
        type=str,
        required=True,
        help="Output directory for Trend Seed artifacts",
    )

    # Source metadata (required)
    parser.add_argument(
        "--repo",
        type=str,
        required=True,
        help="Repository (e.g. owner/repo)",
    )
    parser.add_argument(
        "--workflow-name",
        type=str,
        required=True,
        help="Workflow name (e.g. 'L4 Critic Replay Determinism')",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        required=True,
        help="Workflow run ID",
    )
    parser.add_argument(
        "--head-sha",
        type=str,
        required=True,
        help="Git commit SHA",
    )
    parser.add_argument(
        "--ref",
        type=str,
        required=True,
        help="Git ref (e.g. refs/heads/main)",
    )
    parser.add_argument(
        "--run-created-at",
        type=str,
        required=True,
        help="Workflow run created_at timestamp (ISO-8601 UTC with Z)",
    )

    # Optional metadata
    parser.add_argument(
        "--run-attempt",
        type=int,
        default=1,
        help="Workflow run attempt (default: 1)",
    )
    parser.add_argument(
        "--consumer-version",
        type=str,
        default="0.1.0",
        help="Consumer version (default: 0.1.0)",
    )
    parser.add_argument(
        "--consumer-commit-sha",
        type=str,
        default=None,
        help="Consumer commit SHA (optional)",
    )
    parser.add_argument(
        "--notes",
        type=str,
        default=None,
        help="Optional notes (max 280 chars)",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    try:
        print("=" * 70)
        print("Trend Seed Generator (Phase 5A)")
        print("=" * 70)
        print()

        # Load normalized report
        print(f"Loading normalized report: {args.input}")
        normalized_report = load_normalized_report(args.input)
        print(
            f"✅ Loaded normalized report (schema v{normalized_report.get('schema_version', 'N/A')})"
        )
        print()

        # Build metadata
        meta = {
            "repo": args.repo,
            "workflow_name": args.workflow_name,
            "run_id": args.run_id,
            "run_attempt": args.run_attempt,
            "head_sha": args.head_sha,
            "ref": args.ref,
            "run_created_at": args.run_created_at,
            "consumer_name": "trend_seed_consumer",
            "consumer_version": args.consumer_version,
            "consumer_commit_sha": args.consumer_commit_sha,
        }
        if args.notes:
            meta["notes"] = args.notes

        # Generate Trend Seed
        print("Generating Trend Seed...")
        seed = generate_trend_seed(normalized_report, meta=meta)
        print(f"✅ Generated Trend Seed (schema v{seed.get('schema_version', 'N/A')})")
        print()

        # Write outputs
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1) Trend Seed JSON (deterministic)
        seed_json_path = out_dir / "trend_seed.normalized_report.json"
        write_deterministic_json(str(seed_json_path), seed)
        print(f"✅ Wrote: {seed_json_path}")

        # 2) Run Manifest JSON (deterministic)
        manifest = {
            "trend_seed_schema_version": seed.get("schema_version"),
            "source": seed.get("source"),
            "consumer": seed.get("consumer"),
            "generated_at": seed.get("generated_at"),
        }
        manifest_path = out_dir / "trend_seed.run_manifest.json"
        write_deterministic_json(str(manifest_path), manifest)
        print(f"✅ Wrote: {manifest_path}")

        # 3) Markdown Summary (optional but recommended)
        summary_md = render_markdown_summary(seed)
        summary_path = out_dir / "trend_seed.normalized_report.md"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary_md)
        print(f"✅ Wrote: {summary_path}")

        print()
        print("=" * 70)
        print("✅ SUCCESS: Trend Seed generation complete")
        print("=" * 70)
        return 0

    except TrendSeedError as e:
        print()
        print("=" * 70)
        print(f"❌ FAILURE: {e}")
        print("=" * 70)
        return 1

    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ UNEXPECTED ERROR: {e}")
        print("=" * 70)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
