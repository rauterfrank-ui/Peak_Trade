#!/usr/bin/env python3
"""
L4 Critic Determinism Contract Validator CLI (Phase 4D)

Command-line tool for validating L4 Critic report determinism.

Usage:
    python scripts/aiops/validate_l4_critic_determinism_contract.py \\
        --baseline tests/fixtures/.../critic_report.json \\
        --candidate .tmp/l4_critic_out/critic_report.json \\
        --out validator_report.json

Exit Codes:
    0: Reports are equal (deterministic)
    2: Reports differ (non-deterministic)
    3: Invalid input (missing files, invalid JSON, etc.)

Reference:
    docs/governance/ai_autonomy/PHASE4D_L4_CRITIC_DETERMINISM_CONTRACT.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Add src/ to path for imports
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from ai_orchestration.l4_critic_determinism_contract import (
    CONTRACT_SCHEMA_VERSION,
    ComparisonResult,
    DeterminismContract,
    canonicalize,
    compare_reports,
    dumps_canonical_json,
    hash_canonical,
    load_json,
)


def build_validator_report(
    comparison: ComparisonResult,
    contract_version: str,
    baseline_path: str,
    candidate_path: str,
) -> Dict[str, Any]:
    """
    Build deterministic validator report.

    Args:
        comparison: Comparison result
        contract_version: Contract schema version used
        baseline_path: Path to baseline report
        candidate_path: Path to candidate report

    Returns:
        Validator report dict (ready for JSON serialization)
    """
    return {
        "validator": {
            "name": "l4_critic_determinism_contract_validator",
            "version": "1.0.0",
        },
        "contract_version": contract_version,
        "inputs": {
            "baseline": baseline_path,
            "candidate": candidate_path,
        },
        "result": {
            "equal": comparison.equal,
            "baseline_hash": comparison.baseline_hash,
            "candidate_hash": comparison.candidate_hash,
            "diff_summary": comparison.diff_summary,
            "first_mismatch_path": comparison.first_mismatch_path,
        },
    }


def main() -> int:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Validate L4 Critic report determinism",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare baseline vs candidate
  python scripts/aiops/validate_l4_critic_determinism_contract.py \\
      --baseline tests/fixtures/l4_critic_determinism/.../critic_report.json \\
      --candidate .tmp/l4_critic_out/critic_report.json

  # Save validator report
  python scripts/aiops/validate_l4_critic_determinism_contract.py \\
      --baseline <baseline> --candidate <candidate> \\
      --out validator_report.json

  # Print canonical JSON (debug)
  python scripts/aiops/validate_l4_critic_determinism_contract.py \\
      --baseline <baseline> --candidate <candidate> \\
      --print-canonical .tmp/canonical_baseline.json
        """,
    )

    parser.add_argument(
        "--baseline",
        required=True,
        type=Path,
        help="Path to baseline report (JSON)",
    )
    parser.add_argument(
        "--candidate",
        required=True,
        type=Path,
        help="Path to candidate report (JSON)",
    )
    parser.add_argument(
        "--contract-version",
        default="1.0.0",
        help="Contract schema version (default: 1.0.0)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output validator report to file (default: stdout)",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        default=True,
        help="Exit immediately on mismatch (default: true)",
    )
    parser.add_argument(
        "--print-canonical",
        type=Path,
        metavar="FILE",
        help="Print canonical JSON of baseline to FILE (debug)",
    )

    args = parser.parse_args()

    # =========================================================================
    # Input Validation
    # =========================================================================
    baseline_path: Path = args.baseline
    candidate_path: Path = args.candidate

    if not baseline_path.exists():
        print(f"❌ ERROR: Baseline file not found: {baseline_path}", file=sys.stderr)
        return 3

    if not candidate_path.exists():
        print(f"❌ ERROR: Candidate file not found: {candidate_path}", file=sys.stderr)
        return 3

    # =========================================================================
    # Load Reports
    # =========================================================================
    try:
        baseline_data = load_json(baseline_path)
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Baseline JSON invalid: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"❌ ERROR: Failed to load baseline: {e}", file=sys.stderr)
        return 3

    try:
        candidate_data = load_json(candidate_path)
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Candidate JSON invalid: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"❌ ERROR: Failed to load candidate: {e}", file=sys.stderr)
        return 3

    # =========================================================================
    # Initialize Contract
    # =========================================================================
    if args.contract_version == "1.0.0":
        contract = DeterminismContract.default_v1_0_0()
    else:
        print(
            f"❌ ERROR: Unsupported contract version: {args.contract_version}",
            file=sys.stderr,
        )
        return 3

    # =========================================================================
    # Print Canonical (Debug)
    # =========================================================================
    if args.print_canonical:
        canonical_baseline = canonicalize(baseline_data, contract=contract)
        canonical_json = dumps_canonical_json(canonical_baseline)
        args.print_canonical.parent.mkdir(parents=True, exist_ok=True)
        args.print_canonical.write_text(canonical_json, encoding="utf-8")
        print(f"✅ Canonical baseline written to: {args.print_canonical}")

    # =========================================================================
    # Compare Reports
    # =========================================================================
    comparison = compare_reports(baseline_data, candidate_data, contract)

    # =========================================================================
    # Build Validator Report
    # =========================================================================
    validator_report = build_validator_report(
        comparison=comparison,
        contract_version=args.contract_version,
        baseline_path=str(baseline_path),
        candidate_path=str(candidate_path),
    )

    # =========================================================================
    # Output Validator Report
    # =========================================================================
    report_json = dumps_canonical_json(validator_report)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report_json, encoding="utf-8")
        print(f"✅ Validator report written to: {args.out}")
    else:
        print(report_json)

    # =========================================================================
    # Print Summary & Exit
    # =========================================================================
    if comparison.equal:
        print(f"✅ PASS: {comparison.diff_summary}")
        print(f"   Baseline hash: {comparison.baseline_hash}")
        print(f"   Candidate hash: {comparison.candidate_hash}")
        return 0
    else:
        print(f"❌ FAIL: {comparison.diff_summary}", file=sys.stderr)
        print(f"   Baseline hash:  {comparison.baseline_hash}", file=sys.stderr)
        print(f"   Candidate hash: {comparison.candidate_hash}", file=sys.stderr)
        if comparison.first_mismatch_path:
            print(
                f"   First mismatch: {comparison.first_mismatch_path}",
                file=sys.stderr,
            )
        return 2


if __name__ == "__main__":
    sys.exit(main())
