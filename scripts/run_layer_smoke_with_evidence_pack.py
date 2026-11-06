#!/usr/bin/env python3
"""
Layer Smoke Run with Evidence Pack

Minimal smoke test that creates an Evidence Pack (Phase 4A).

Usage:
    python scripts/run_layer_smoke_with_evidence_pack.py
    python scripts/run_layer_smoke_with_evidence_pack.py --layer L1 --autonomy PROP
    python scripts/run_layer_smoke_with_evidence_pack.py --output .artifacts/evidence_packs/test-run

Features:
- Creates minimal Evidence Pack for smoke test
- Validates pack after creation
- Outputs pack to .artifacts/evidence_packs/<run_id>/
- Returns exit code 0 (success) or 1 (failure)

Exit Codes:
    0: Smoke run successful, Evidence Pack valid
    1: Smoke run failed or Evidence Pack invalid
"""

import argparse
import sys
import uuid
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_orchestration.evidence_pack import EvidencePackValidator
from src.ai_orchestration.evidence_pack_runtime import EvidencePackRuntime
from src.ai_orchestration.models import AutonomyLevel


def run_smoke_test(
    layer_id: str,
    autonomy_level: AutonomyLevel,
    output_dir: Path,
    verbose: bool = False,
) -> bool:
    """
    Run smoke test and create Evidence Pack.

    Args:
        layer_id: Layer ID (L0-L6)
        autonomy_level: Autonomy level
        output_dir: Output directory for Evidence Pack
        verbose: Verbose output

    Returns:
        True if smoke test passed, False otherwise
    """
    # Generate run ID
    run_id = f"smoke-{uuid.uuid4().hex[:8]}"

    if verbose:
        print(f"🚀 Starting smoke run: {run_id}")
        print(f"   Layer: {layer_id}")
        print(f"   Autonomy: {autonomy_level.value}")
        print()

    try:
        # Create runtime
        runtime = EvidencePackRuntime(output_dir=output_dir)

        # Start run
        pack = runtime.start_run(
            run_id=run_id,
            layer_id=layer_id,
            autonomy_level=autonomy_level,
            phase_id="smoke-test",
            description=f"Smoke test for {layer_id} at {autonomy_level.value}",
        )

        if verbose:
            print(f"✅ Evidence Pack created: {pack.evidence_pack_id}")

        # Add minimal layer run metadata (smoke test doesn't actually run models)
        runtime.add_layer_run_metadata(
            run_id=run_id,
            layer_name=f"Layer {layer_id}",
            primary_model_id="gpt-5-2-pro",
            critic_model_id="deepseek-r1",
            capability_scope_id=f"{layer_id}_smoke",
            matrix_version="v1.0",
        )

        if verbose:
            print(f"✅ Layer run metadata added")

        # Finish run
        runtime.finish_run(run_id=run_id, status="success", tests_passed=1, tests_total=1)

        if verbose:
            print(f"✅ Run finished")

        # Save pack
        pack_path = runtime.save_pack(run_id=run_id)

        if verbose:
            print(f"✅ Evidence Pack saved: {pack_path}")

        # Validate pack
        validator = EvidencePackValidator(strict=True)
        result = validator.validate_file(pack_path)

        if result:
            if verbose:
                print(f"✅ Evidence Pack validation: PASSED")
            return True
        else:
            if verbose:
                print(f"❌ Evidence Pack validation: FAILED")
                for error in validator.errors:
                    print(f"   Error: {error}")
            return False

    except Exception as e:
        if verbose:
            print(f"❌ Smoke run failed: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run smoke test with Evidence Pack creation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--layer",
        type=str,
        default="L0",
        choices=["L0", "L1", "L2", "L3", "L4", "L5", "L6"],
        help="Layer ID (default: L0)",
    )

    parser.add_argument(
        "--autonomy",
        type=str,
        default="REC",
        choices=["RO", "REC", "PROP"],
        help="Autonomy level (default: REC)",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(".artifacts/evidence_packs"),
        help="Output directory (default: .artifacts/evidence_packs)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Convert autonomy level string to enum
    autonomy_level = AutonomyLevel(args.autonomy)

    # Run smoke test
    print("🚀 Layer Smoke Run with Evidence Pack")
    print("=" * 80)

    success = run_smoke_test(
        layer_id=args.layer,
        autonomy_level=autonomy_level,
        output_dir=args.output,
        verbose=args.verbose,
    )

    print("=" * 80)
    if success:
        print("✅ SMOKE RUN PASSED")
        return 0
    else:
        print("❌ SMOKE RUN FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
