#!/usr/bin/env python3
"""
CLI Script: Layer Dry-Run (AI Orchestration)

Validates layer orchestration and generates run manifest + operator output.
NO real model API calls. Deterministic artifact generation only.

Usage:
    python scripts/aiops/run_layer_dry_run.py \\
        --layer L2 \\
        --primary gpt-5.2-pro \\
        --critic deepseek-r1 \\
        --out out/L2_dry_run

Exit Codes:
    0: Success
    2: Validation error (SoD, config, etc.)
    3: Unexpected error

Reference:
- docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "src"))

from ai_orchestration import (
    DryRunError,
    ForbiddenAutonomyError,
    InvalidLayerError,
    MultiModelRunner,
    OrchestrationError,
)


def main():
    parser = argparse.ArgumentParser(
        description="AI Orchestration Layer Dry-Run (NO real model calls)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # L2 Market Outlook dry-run
  python scripts/aiops/run_layer_dry_run.py \\
      --layer L2 \\
      --primary gpt-5.2-pro \\
      --critic deepseek-r1 \\
      --out out/L2_dry_run

  # L0 Ops/Docs dry-run
  python scripts/aiops/run_layer_dry_run.py \\
      --layer L0 \\
      --primary gpt-5.2 \\
      --critic deepseek-r1 \\
      --out out/L0_dry_run

Exit Codes:
  0: Success
  2: Validation error
  3: Unexpected error
        """,
    )

    parser.add_argument(
        "--layer",
        required=True,
        help="Layer ID (e.g., L0, L2, L4)",
    )
    parser.add_argument(
        "--primary",
        required=True,
        help="Primary model ID (e.g., gpt-5.2-pro)",
    )
    parser.add_argument(
        "--critic",
        required=True,
        help="Critic model ID (e.g., deepseek-r1)",
    )
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Output directory for artifacts",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional operator notes",
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

    # Deterministic clock (for testing)
    clock = None
    if args.deterministic:
        clock = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)

    # Initialize runner
    try:
        runner = MultiModelRunner(clock=clock)
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize runner: {e}", file=sys.stderr)
        return 3

    # Perform dry-run
    try:
        print(f"🔄 Starting dry-run for layer {args.layer}...")
        print(f"   Primary: {args.primary}")
        print(f"   Critic: {args.critic}")
        print(f"   Output: {args.out}")
        print()

        manifest = runner.dry_run(
            layer_id=args.layer,
            primary_model_id=args.primary,
            critic_model_id=args.critic,
            out_dir=args.out,
            operator_notes=args.notes,
            findings=args.finding if args.finding else None,
            actions=args.action if args.action else None,
        )

        print(f"✅ Dry-run completed successfully!")
        print()
        print(f"📋 Run Manifest:")
        print(f"   Run ID: {manifest.run_id}")
        print(f"   Layer: {manifest.layer_id} ({manifest.layer_name})")
        print(f"   Autonomy: {manifest.autonomy_level}")
        print(f"   Primary: {manifest.primary_model_id}")
        print(f"   Critic: {manifest.critic_model_id}")
        print(f"   SoD: {manifest.sod_result}")
        print()
        print(f"📦 Artifacts:")
        for artifact in sorted(manifest.artifacts):
            print(f"   - {artifact}")
        print()
        print(f"✅ SUCCESS: Dry-run validation passed")
        return 0

    except InvalidLayerError as e:
        print(f"❌ VALIDATION ERROR: Invalid layer", file=sys.stderr)
        print(f"   {e}", file=sys.stderr)
        return 2

    except ForbiddenAutonomyError as e:
        print(f"❌ VALIDATION ERROR: Forbidden autonomy level", file=sys.stderr)
        print(f"   {e}", file=sys.stderr)
        return 2

    except DryRunError as e:
        print(f"❌ VALIDATION ERROR: Dry-run failed", file=sys.stderr)
        print(f"   {e}", file=sys.stderr)
        return 2

    except OrchestrationError as e:
        print(f"❌ ORCHESTRATION ERROR", file=sys.stderr)
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
