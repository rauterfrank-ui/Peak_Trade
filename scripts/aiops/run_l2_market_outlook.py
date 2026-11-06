#!/usr/bin/env python3
"""
CLI Script: L2 Market Outlook Runner (Offline/Replay Mode)

Runs L2 Market Outlook with Proposer + Critic orchestration.

Usage:
    python scripts/aiops/run_l2_market_outlook.py \\
        --mode replay \\
        --transcript tests/fixtures/transcripts/l2_market_outlook_sample.json \\
        --out evidence_packs/L2_demo

Exit Codes:
    0: Success
    2: Validation error (SoD, capability scope)
    3: Runtime error

Reference:
- docs/governance/ai_autonomy/PHASE3_L2_MARKET_OUTLOOK_PILOT.md
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "src"))

from ai_orchestration.l2_runner import (
    L2Runner,
    L2RunnerError,
    SoDViolation,
    CapabilityScopeViolation,
)


def print_banner(mode: str):
    """Print mode banner."""
    if mode in ["replay", "dry"]:
        print("=" * 70)
        print("🔒 OFFLINE/REPLAY MODE")
        print("=" * 70)
        print("- No real model API calls")
        print("- Using pre-recorded transcript fixtures")
        print("- Deterministic, reproducible outputs")
        print("- Safe for CI/testing")
        print("=" * 70)
        print()
    elif mode in ["live", "record"]:
        print("=" * 70)
        print("🚨 WARNING: NETWORK MODE")
        print("=" * 70)
        print("- Real model API calls will be made")
        print("- Costs will be incurred")
        print("- Requires OPENAI_API_KEY environment variable")
        print("- NO-LIVE trading remains enforced")
        print("=" * 70)
        print()


def main():
    parser = argparse.ArgumentParser(
        description="L2 Market Outlook Runner (Offline/Replay Mode)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Replay mode with fixture ID (recommended)
  python scripts/aiops/run_l2_market_outlook.py \\
      --mode replay \\
      --fixture l2_market_outlook_sample \\
      --out evidence_packs/L2_demo

  # Replay mode with full transcript path
  python scripts/aiops/run_l2_market_outlook.py \\
      --mode replay \\
      --transcript tests/fixtures/transcripts/l2_market_outlook_sample.json \\
      --out evidence_packs/L2_demo

  # Dry mode (alias for replay)
  python scripts/aiops/run_l2_market_outlook.py \\
      --mode dry \\
      --fixture l2_market_outlook_sample

Exit Codes:
  0: Success
  2: Validation error (SoD, capability scope)
  3: Runtime error
        """,
    )

    parser.add_argument(
        "--mode",
        default="replay",
        choices=["replay", "dry"],
        help="Run mode (default: replay). Live/record modes not yet supported in CLI.",
    )
    parser.add_argument(
        "--transcript",
        type=Path,
        help="Path to transcript fixture (required for replay/dry mode if --fixture not provided)",
    )
    parser.add_argument(
        "--fixture",
        help="Fixture ID (e.g., 'l2_market_outlook_sample'). Resolves to tests/fixtures/transcripts/<id>.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output directory for evidence pack (default: auto-generated)",
    )
    parser.add_argument(
        "--prompt",
        help="Proposer prompt (default: sample prompt)",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Operator notes",
    )
    parser.add_argument(
        "--finding",
        action="append",
        default=[],
        help="Add finding (can be used multiple times)",
    )
    parser.add_argument(
        "--action",
        action="append",
        default=[],
        help="Add action (can be used multiple times)",
    )
    parser.add_argument(
        "--deterministic",
        action="store_true",
        help="Use fixed timestamp for determinism (for testing)",
    )

    args = parser.parse_args()

    # Resolve fixture or transcript
    if args.fixture and args.transcript:
        print("❌ ERROR: Cannot specify both --fixture and --transcript", file=sys.stderr)
        return 3

    if not args.fixture and not args.transcript:
        print("❌ ERROR: Must specify either --fixture or --transcript", file=sys.stderr)
        return 3

    # Resolve fixture ID to path
    if args.fixture:
        fixture_id = args.fixture
        # Remove .json extension if provided
        if fixture_id.endswith(".json"):
            fixture_id = fixture_id[:-5]

        transcript_path = repo_root / "tests" / "fixtures" / "transcripts" / f"{fixture_id}.json"

        if not transcript_path.exists():
            print(f"❌ ERROR: Fixture not found: {fixture_id}", file=sys.stderr)
            print(f"   Expected path: {transcript_path}", file=sys.stderr)
            print(f"   Available fixtures:", file=sys.stderr)
            fixtures_dir = repo_root / "tests" / "fixtures" / "transcripts"
            if fixtures_dir.exists():
                for f in sorted(fixtures_dir.glob("*.json")):
                    print(f"     - {f.stem}", file=sys.stderr)
            return 3
    else:
        transcript_path = args.transcript

    # Print banner
    print_banner(args.mode)

    # Deterministic clock (for testing)
    clock = None
    if args.deterministic:
        clock = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
        print("⏰ Using deterministic clock: 2026-01-10T12:00:00+00:00")
        print()

    # Validate transcript exists
    if not transcript_path.exists():
        print(f"❌ ERROR: Transcript not found: {transcript_path}", file=sys.stderr)
        return 3

    # Initialize runner
    try:
        runner = L2Runner(clock=clock)
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize runner: {e}", file=sys.stderr)
        return 3

    # Run L2 Market Outlook
    try:
        print(f"🔄 Starting L2 Market Outlook run...")
        print(f"   Mode: {args.mode}")
        if args.fixture:
            print(f"   Fixture: {args.fixture}")
        print(f"   Transcript: {transcript_path}")
        print(f"   Output: {args.out or 'auto-generated'}")
        print()

        result = runner.run(
            mode=args.mode,
            transcript_path=transcript_path,
            out_dir=args.out,
            proposer_prompt=args.prompt,
            operator_notes=args.notes,
            findings=args.finding if args.finding else None,
            actions=args.action if args.action else None,
        )

        print("✅ L2 Market Outlook run completed successfully!")
        print()
        print("=" * 70)
        print(result.summary)
        print("=" * 70)
        print()
        print(f"📦 Evidence Pack Artifacts ({len(result.artifacts)} files):")
        for name, path in sorted(result.artifacts.items()):
            print(f"   - {path}")
        print()
        print(f"✅ SUCCESS: Evidence Pack ID: {result.evidence_pack_id}")
        return 0

    except SoDViolation as e:
        print(f"❌ VALIDATION ERROR: SoD Violation", file=sys.stderr)
        print(f"   {e}", file=sys.stderr)
        return 2

    except CapabilityScopeViolation as e:
        print(f"❌ VALIDATION ERROR: Capability Scope Violation", file=sys.stderr)
        print(f"   {e}", file=sys.stderr)
        return 2

    except L2RunnerError as e:
        print(f"❌ L2 RUNNER ERROR", file=sys.stderr)
        print(f"   {e}", file=sys.stderr)
        return 2

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR", file=sys.stderr)
        print(f"   {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 3


if __name__ == "__main__":
    sys.exit(main())
