#!/usr/bin/env python3
"""
L4 Governance Critic CLI Runner

Runs L4 Governance Critic on an Evidence Pack (offline/replay by default).

Usage:
    python scripts/aiops/run_l4_governance_critic.py --evidence-pack <path>
    python scripts/aiops/run_l4_governance_critic.py --evidence-pack <path> --allow-network --record
    python scripts/aiops/run_l4_governance_critic.py --evidence-pack <path> --mode replay --transcript <path>

Reference:
- docs/governance/ai_autonomy/PHASE4_L1_L4_INTEGRATION.md
- config/capability_scopes/L4_governance_critic.toml
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ai_orchestration.l4_critic import (
    CapabilityScopeViolation,
    L4Critic,
    L4CriticError,
    SoDViolation,
)


def print_banner(mode: str, allow_network: bool):
    """Print run mode banner."""
    if allow_network:
        print("=" * 70)
        print("⚠️  NETWORK MODE ENABLED")
        print("=" * 70)
        print("This run will make LIVE API CALLS to model providers.")
        print("Use --record to save transcripts for future replay.")
        print("=" * 70)
        print()
    else:
        print("=" * 70)
        print("✅ OFFLINE MODE (Default)")
        print("=" * 70)
        print("This run will use pre-recorded transcripts (no network calls).")
        print("Benefits: deterministic, fast, no API costs, CI-safe.")
        print("=" * 70)
        print()


def resolve_fixture_id(fixture_id: str) -> Path:
    """Resolve fixture ID to full path."""
    base_dir = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "transcripts"

    # Direct path
    if Path(fixture_id).exists():
        return Path(fixture_id)

    # Fixture ID only
    fixture_path = base_dir / f"{fixture_id}.json"
    if fixture_path.exists():
        return fixture_path

    # Not found
    raise FileNotFoundError(f"Fixture not found: {fixture_id} (tried {fixture_path})")


def main():
    parser = argparse.ArgumentParser(
        description="L4 Governance Critic CLI Runner (offline/replay by default)"
    )

    # Required
    parser.add_argument(
        "--evidence-pack",
        type=str,
        required=True,
        help="Path to Evidence Pack directory to review",
    )

    # Mode control
    parser.add_argument(
        "--mode",
        type=str,
        choices=["replay", "dry", "live", "record"],
        default="replay",
        help="Run mode (default: replay)",
    )

    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="Allow network calls (opt-in for local testing only)",
    )

    parser.add_argument(
        "--record",
        action="store_true",
        help="Record mode: save transcript for replay",
    )

    # Paths
    parser.add_argument(
        "--transcript",
        type=str,
        help="Path to transcript file (for replay/dry modes)",
    )

    parser.add_argument(
        "--fixture",
        type=str,
        help="Fixture ID (alternative to --transcript)",
    )

    parser.add_argument(
        "--out",
        type=str,
        help="Output directory for artifacts (default: auto-generated)",
    )

    # Metadata
    parser.add_argument(
        "--notes",
        type=str,
        default="",
        help="Operator notes (optional)",
    )

    parser.add_argument(
        "--deterministic",
        action="store_true",
        help="Use fixed clock for deterministic output (testing only)",
    )

    # Phase 4C: Standardized output control
    parser.add_argument(
        "--pack-id",
        type=str,
        help="Evidence pack ID override (for determinism)",
    )

    parser.add_argument(
        "--schema-version",
        type=str,
        default="1.0.0",
        help="Critic report schema version (default: 1.0.0)",
    )

    parser.add_argument(
        "--no-legacy-output",
        action="store_true",
        help="Suppress legacy artifacts (critic_report.md, critic_decision.json, etc.)",
    )

    args = parser.parse_args()

    # Resolve mode
    mode = args.mode
    if args.record:
        mode = "record"
    elif not args.allow_network and mode in ["live", "record"]:
        mode = "replay"  # Force replay if no network

    # Resolve transcript path
    transcript_path = None
    if args.transcript:
        transcript_path = Path(args.transcript)
    elif args.fixture:
        transcript_path = resolve_fixture_id(args.fixture)

    # Resolve output directory
    out_dir = Path(args.out) if args.out else None

    # Resolve evidence pack path
    evidence_pack_path = Path(args.evidence_pack)

    # Print banner
    print_banner(mode, args.allow_network)

    # Initialize runner
    clock = None
    if args.deterministic:
        clock = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)

    runner = L4Critic(
        clock=clock,
        schema_version=args.schema_version,
    )

    # Execute
    try:
        print(f"Running L4 Governance Critic...")
        print(f"Evidence Pack: {evidence_pack_path}")
        print(f"Mode: {mode}")
        if transcript_path:
            print(f"Transcript: {transcript_path}")
        print()

        result = runner.run(
            evidence_pack_path=evidence_pack_path,
            mode=mode,
            transcript_path=transcript_path,
            out_dir=out_dir,
            operator_notes=args.notes,
            pack_id=args.pack_id,
            deterministic=args.deterministic,
            fixture=args.fixture,
            legacy_output=not args.no_legacy_output,
        )

        print("=" * 70)
        print("✅ L4 GOVERNANCE CRITIC COMPLETE")
        print("=" * 70)
        print(result.summary)
        print()
        print("Decision Details:")
        print(f"  Decision:  {result.decision.decision}")
        print(f"  Severity:  {result.decision.severity}")
        print(f"  Rationale: {result.decision.rationale}")
        print()
        print("Artifacts:")
        for name, path in result.artifacts.items():
            print(f"  {name}: {path}")
        print()
        print("=" * 70)

        return 0

    except SoDViolation as e:
        print(f"❌ SoD VIOLATION: {e}", file=sys.stderr)
        return 2

    except CapabilityScopeViolation as e:
        print(f"❌ CAPABILITY SCOPE VIOLATION: {e}", file=sys.stderr)
        return 3

    except L4CriticError as e:
        print(f"❌ L4 CRITIC ERROR: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 99


if __name__ == "__main__":
    sys.exit(main())
