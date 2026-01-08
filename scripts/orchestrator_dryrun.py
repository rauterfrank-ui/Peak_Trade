#!/usr/bin/env python3
"""
Orchestrator Dry-Run CLI

Test model selection without side effects.

Usage:
    python3 scripts/orchestrator_dryrun.py --layer L0 --autonomy REC
    python3 scripts/orchestrator_dryrun.py --layer L2 --autonomy PROP --verbose
"""

import argparse
import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from src.ai_orchestration.orchestrator import Orchestrator, SelectionConstraints
from src.ai_orchestration.models import AutonomyLevel


def main():
    parser = argparse.ArgumentParser(description="Orchestrator Dry-Run (Model Selection Test)")
    parser.add_argument(
        "--layer",
        "-l",
        required=True,
        choices=["L0", "L1", "L2", "L3", "L4", "L5", "L6"],
        help="Layer ID (L0-L6)",
    )
    parser.add_argument(
        "--autonomy",
        "-a",
        required=True,
        choices=["RO", "REC", "PROP", "EXEC"],
        help="Autonomy Level (RO, REC, PROP, EXEC)",
    )
    parser.add_argument(
        "--task-type",
        "-t",
        default="general",
        help="Task type (e.g., 'general', 'research', 'critique')",
    )
    parser.add_argument(
        "--enable-orchestrator",
        action="store_true",
        help="Enable orchestrator (sets ORCHESTRATOR_ENABLED=true)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output (show full selection details)",
    )

    args = parser.parse_args()

    # Enable orchestrator if requested
    if args.enable_orchestrator:
        import os
        os.environ["ORCHESTRATOR_ENABLED"] = "true"

    print("=" * 70)
    print("Orchestrator Dry-Run (Model Selection Test)")
    print("=" * 70)
    print(f"Layer: {args.layer}")
    print(f"Autonomy: {args.autonomy}")
    print(f"Task Type: {args.task_type}")
    print()

    try:
        # Initialize orchestrator
        config_dir = repo_root / "config"
        orch = Orchestrator(config_dir=config_dir)

        # Health check
        health = orch.health_check()
        print("Health Check:")
        print(f"  - Enabled: {health['enabled']}")
        print(f"  - Registry Version: {health['registry_version']}")
        print(f"  - Models: {health['models_count']}")
        print(f"  - Layers Mapped: {health['layers_mapped']}")
        print(f"  - Status: {health['status']}")
        print()

        if not health["enabled"]:
            print("⚠️  Orchestrator is disabled. Use --enable-orchestrator to enable.")
            return 1

        # Select model
        autonomy_level = AutonomyLevel[args.autonomy]
        selection = orch.select_model(
            layer_id=args.layer,
            autonomy_level=autonomy_level,
            task_type=args.task_type,
        )

        # Print selection
        print("✅ Model Selection Successful")
        print("-" * 70)
        print(f"Primary Model:     {selection.primary_model_id}")
        print(f"Critic Model:      {selection.critic_model_id}")
        print(f"Fallback Models:   {', '.join(selection.fallback_model_ids) or 'none'}")
        print(f"Capability Scope:  {selection.capability_scope_id}")
        print(f"Registry Version:  {selection.registry_version}")
        print(f"SoD Validated:     {selection.sod_validated}")
        print(f"Timestamp:         {selection.selection_timestamp}")
        print()
        print(f"Reason: {selection.selection_reason}")

        if args.verbose:
            print()
            print("Full Selection (dict):")
            import json
            print(json.dumps(selection.to_dict(), indent=2))

        print()
        print("=" * 70)
        print("✅ Dry-Run Complete (No Side Effects)")
        print("=" * 70)

        return 0

    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ Error: {type(e).__name__}")
        print(f"   {e}")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
