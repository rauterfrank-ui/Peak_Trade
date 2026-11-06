#!/usr/bin/env python3
"""
Evidence Pack CI Validation

Validates all Evidence Packs in a directory (Phase 4A CI Gate).

Usage:
    python scripts/validate_evidence_pack_ci.py --root .artifacts/evidence_packs
    python scripts/validate_evidence_pack_ci.py --root .artifacts/evidence_packs --strict
    python scripts/validate_evidence_pack_ci.py --root .artifacts/evidence_packs --output validation_report.json

Features:
- Discovers all evidence_pack.json files in directory tree
- Validates each pack with EvidencePackValidator
- Generates JSON + text summary reports
- Returns exit code 0 (success) or 1 (failure)

Exit Codes:
    0: All packs valid
    1: One or more packs invalid
    2: No packs found or invalid arguments
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_orchestration.evidence_pack import EvidencePackValidator


class ValidationReport:
    """Validation report for CI gate."""

    def __init__(self):
        self.total_packs = 0
        self.valid_packs = 0
        self.invalid_packs = 0
        self.pack_results: List[Dict[str, Any]] = []
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def add_result(
        self,
        pack_path: Path,
        valid: bool,
        errors: List[str],
        warnings: List[str],
        exception: str = "",
    ) -> None:
        """Add validation result for a pack."""
        self.total_packs += 1
        if valid:
            self.valid_packs += 1
        else:
            self.invalid_packs += 1

        self.pack_results.append(
            {
                "pack_path": str(pack_path),
                "valid": valid,
                "errors": errors,
                "warnings": warnings,
                "exception": exception,
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "timestamp": self.timestamp,
            "total_packs": self.total_packs,
            "valid_packs": self.valid_packs,
            "invalid_packs": self.invalid_packs,
            "success_rate": (
                round(self.valid_packs / self.total_packs * 100, 2) if self.total_packs > 0 else 0.0
            ),
            "pack_results": self.pack_results,
        }

    def to_text_summary(self) -> str:
        """Generate text summary for console output."""
        lines = []
        lines.append("=" * 80)
        lines.append("Evidence Pack CI Validation Report")
        lines.append("=" * 80)
        lines.append(f"Timestamp: {self.timestamp}")
        lines.append(f"Total Packs: {self.total_packs}")
        lines.append(f"Valid Packs: {self.valid_packs}")
        lines.append(f"Invalid Packs: {self.invalid_packs}")
        lines.append(
            f"Success Rate: {round(self.valid_packs / self.total_packs * 100, 2) if self.total_packs > 0 else 0.0}%"
        )
        lines.append("=" * 80)

        if self.invalid_packs > 0:
            lines.append("\n❌ INVALID PACKS:")
            for result in self.pack_results:
                if not result["valid"]:
                    lines.append(f"\n  Pack: {result['pack_path']}")
                    if result["exception"]:
                        lines.append(f"    Exception: {result['exception']}")
                    if result["errors"]:
                        lines.append("    Errors:")
                        for error in result["errors"]:
                            lines.append(f"      - {error}")
                    if result["warnings"]:
                        lines.append("    Warnings:")
                        for warning in result["warnings"]:
                            lines.append(f"      - {warning}")

        lines.append("\n" + "=" * 80)
        if self.invalid_packs == 0:
            lines.append("✅ ALL PACKS VALID")
        else:
            lines.append("❌ VALIDATION FAILED")
        lines.append("=" * 80)

        return "\n".join(lines)


def discover_evidence_packs(root_dir: Path) -> List[Path]:
    """
    Discover all evidence_pack.json files in directory tree.

    Args:
        root_dir: Root directory to search

    Returns:
        List of paths to evidence_pack.json files
    """
    if not root_dir.exists():
        return []

    # Find all evidence_pack.json files
    return list(root_dir.rglob("evidence_pack.json"))


def validate_packs(
    pack_paths: List[Path], strict: bool = True, verbose: bool = False
) -> ValidationReport:
    """
    Validate all Evidence Packs.

    Args:
        pack_paths: List of paths to Evidence Packs
        strict: Strict validation mode
        verbose: Verbose output

    Returns:
        ValidationReport instance
    """
    report = ValidationReport()
    validator = EvidencePackValidator(strict=strict)

    for pack_path in pack_paths:
        if verbose:
            print(f"📦 Validating: {pack_path}")

        try:
            result = validator.validate_file(pack_path)
            report.add_result(
                pack_path=pack_path,
                valid=result,
                errors=validator.errors.copy(),
                warnings=validator.warnings.copy(),
            )

            if verbose:
                if result:
                    print(f"   ✅ VALID")
                else:
                    print(f"   ❌ INVALID")

        except Exception as e:
            report.add_result(
                pack_path=pack_path,
                valid=False,
                errors=[],
                warnings=[],
                exception=str(e),
            )

            if verbose:
                print(f"   ❌ EXCEPTION: {e}")

    return report


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate Evidence Packs for CI gate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--root",
        type=Path,
        default=Path(".artifacts/evidence_packs"),
        help="Root directory to search for Evidence Packs (default: .artifacts/evidence_packs)",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for JSON report (optional)",
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
        help="Verbose output",
    )

    args = parser.parse_args()

    # Determine strict mode
    strict = not args.lenient

    # Discover packs
    print(f"🔍 Discovering Evidence Packs in: {args.root}")
    pack_paths = discover_evidence_packs(args.root)

    if not pack_paths:
        print(f"❌ ERROR: No Evidence Packs found in {args.root}", file=sys.stderr)
        return 2

    print(f"   Found {len(pack_paths)} Evidence Pack(s)")
    print()

    # Validate packs
    print("📦 Validating Evidence Packs...")
    print(f"   Mode: {'STRICT' if strict else 'LENIENT'}")
    print()

    report = validate_packs(pack_paths, strict=strict, verbose=args.verbose)

    # Print text summary
    print(report.to_text_summary())

    # Save JSON report if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"\n📄 JSON report saved to: {args.output}")

    # Return exit code
    if report.invalid_packs == 0:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
