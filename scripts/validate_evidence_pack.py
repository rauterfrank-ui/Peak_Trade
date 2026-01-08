#!/usr/bin/env python3
"""
Evidence Pack Validator CLI

Validates Evidence Packs against mandatory schema requirements.

Usage:
    python3 scripts/validate_evidence_pack.py <evidence_pack.json>
    python3 scripts/validate_evidence_pack.py --strict <evidence_pack.json>
    python3 scripts/validate_evidence_pack.py --lenient <evidence_pack.json>

Examples:
    # Strict validation (fail on any error)
    python3 scripts/validate_evidence_pack.py data/evidence_packs/EVP-001.json

    # Lenient validation (collect warnings, don't fail)
    python3 scripts/validate_evidence_pack.py --lenient data/evidence_packs/EVP-001.json

Exit Codes:
    0: Validation passed
    1: Validation failed
    2: File not found or invalid arguments
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_orchestration.evidence_pack import EvidencePackValidator


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate Evidence Packs against mandatory schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "evidence_pack",
        type=Path,
        help="Path to Evidence Pack file (.json or .toml)",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        default=True,
        help="Strict mode: fail on any validation error (default)",
    )

    parser.add_argument(
        "--lenient",
        action="store_true",
        help="Lenient mode: collect warnings but don't fail",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output (show warnings)",
    )

    args = parser.parse_args()

    # Check file exists
    if not args.evidence_pack.exists():
        print(f"❌ ERROR: File not found: {args.evidence_pack}", file=sys.stderr)
        return 2

    # Determine strict mode
    strict = not args.lenient

    # Create validator
    validator = EvidencePackValidator(strict=strict)

    # Validate
    print(f"📦 Validating Evidence Pack: {args.evidence_pack}")
    print(f"   Mode: {'STRICT' if strict else 'LENIENT'}")
    print()

    try:
        result = validator.validate_file(args.evidence_pack)

        if result:
            print("✅ VALIDATION PASSED")
            print()
            print(f"   Evidence Pack: {args.evidence_pack.name}")
            print(f"   Errors: {len(validator.errors)}")
            print(f"   Warnings: {len(validator.warnings)}")

            if args.verbose and validator.warnings:
                print()
                print("⚠️  WARNINGS:")
                for warning in validator.warnings:
                    print(f"   - {warning}")

            return 0
        else:
            print("❌ VALIDATION FAILED")
            print()
            print(f"   Evidence Pack: {args.evidence_pack.name}")
            print(f"   Errors: {len(validator.errors)}")
            print(f"   Warnings: {len(validator.warnings)}")

            if validator.errors:
                print()
                print("❌ ERRORS:")
                for error in validator.errors:
                    print(f"   - {error}")

            if args.verbose and validator.warnings:
                print()
                print("⚠️  WARNINGS:")
                for warning in validator.warnings:
                    print(f"   - {warning}")

            return 1

    except ValueError as e:
        print("❌ VALIDATION FAILED")
        print()
        print(f"   Evidence Pack: {args.evidence_pack.name}")
        print(f"   Error: {e}")
        return 1

    except Exception as e:
        print(f"❌ ERROR: Unexpected error during validation", file=sys.stderr)
        print(f"   {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
