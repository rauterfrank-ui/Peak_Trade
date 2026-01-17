#!/usr/bin/env python3
"""
Generate Trend Ledger from Trend Seed (Phase 5B CLI)

Consumes Phase 5A Trend Seed and produces:
- Canonical Trend Ledger JSON (deterministic, stable ordering)
- Markdown summary (operator-friendly)

Design:
- Fail-closed: schema mismatch or missing fields → exit 1
- CI-friendly: clear exit codes, parseable output paths
- No secrets: no tokens, no PII in artifacts

Reference:
- docs/ops/runbooks/RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED.md

Usage:
    # Basic usage
    python scripts/aiops/generate_trend_ledger_from_seed.py \\
        --input trend_seed.json \\
        --output-json trend_ledger.json \\
        --output-markdown trend_ledger.md

    # CI mode (with run manifest)
    python scripts/aiops/generate_trend_ledger_from_seed.py \\
        --input trend_seed.json \\
        --output-json trend_ledger.json \\
        --output-markdown trend_ledger.md \\
        --run-manifest manifest.json

Exit Codes:
    0: Success
    1: Error (schema mismatch, missing fields, IO error)
    2: Usage error (missing required args)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.ai_orchestration.trends.trend_ledger import (
    SchemaVersionError,
    TrendLedgerError,
    ValidationError,
    compute_canonical_hash,
    ledger_from_seed,
    load_trend_seed,
    render_markdown_summary,
    to_canonical_json,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate Trend Ledger from Trend Seed (Phase 5B)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate ledger from seed
  python scripts/aiops/generate_trend_ledger_from_seed.py \\
      --input trend_seed.json \\
      --output-json trend_ledger.json \\
      --output-markdown trend_ledger.md

  # With run manifest (CI)
  python scripts/aiops/generate_trend_ledger_from_seed.py \\
      --input trend_seed.json \\
      --output-json trend_ledger.json \\
      --output-markdown trend_ledger.md \\
      --run-manifest manifest.json

Exit Codes:
  0: Success
  1: Error (schema mismatch, validation failure, IO error)
  2: Usage error (missing required arguments)
        """,
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to input Trend Seed JSON (from Phase 5A)",
    )

    parser.add_argument(
        "--output-json",
        required=True,
        help="Path to output Trend Ledger JSON (canonical)",
    )

    parser.add_argument(
        "--output-markdown",
        help="Path to output Markdown summary (optional)",
    )

    parser.add_argument(
        "--run-manifest",
        help="Path to write run manifest JSON (CI metadata, optional)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    return parser.parse_args()


def write_run_manifest(path: str, seed: Dict[str, Any], ledger_hash: str) -> None:
    """
    Write run manifest with metadata for CI artifact tracking.

    Args:
        path: Output manifest path
        seed: Original trend seed
        ledger_hash: Canonical hash of ledger
    """
    manifest = {
        "phase": "5B",
        "component": "trend_ledger_consumer",
        "version": "0.1.0",
        "input": {
            "seed_schema_version": seed.get("schema_version"),
            "seed_generated_at": seed.get("generated_at"),
            "seed_source_run_id": seed.get("source", {}).get("run_id"),
        },
        "output": {
            "ledger_schema_version": "0.1.0",
            "ledger_canonical_hash": ledger_hash,
        },
    }

    Path(path).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    """Main entry point."""
    args = parse_args()

    print("=" * 70)
    print("Phase 5B: Generate Trend Ledger from Trend Seed")
    print("=" * 70)
    print()

    try:
        # Load trend seed
        print(f"Loading trend seed: {args.input}")
        seed = load_trend_seed(args.input)
        print(
            f"✅ Loaded seed (schema v{seed.get('schema_version', 'N/A')}, "
            f"run {seed.get('source', {}).get('run_id', 'N/A')})"
        )
        print()

        # Generate ledger
        print("Generating trend ledger...")
        ledger = ledger_from_seed(seed)
        print(f"✅ Generated ledger (schema v{ledger.schema_version})")
        print(f"   - Items: {len(ledger.items)}")
        print(f"   - Counters: {len(ledger.counters)} keys")
        print()

        # Write canonical JSON
        print(f"Writing canonical JSON: {args.output_json}")
        canonical_json = to_canonical_json(ledger)
        Path(args.output_json).write_text(canonical_json, encoding="utf-8")
        ledger_hash = compute_canonical_hash(ledger)
        print(f"✅ Wrote canonical JSON (hash: {ledger_hash[:16]}...)")
        print()

        # Write markdown summary (optional)
        if args.output_markdown:
            print(f"Writing markdown summary: {args.output_markdown}")
            summary = render_markdown_summary(ledger)
            Path(args.output_markdown).write_text(summary, encoding="utf-8")
            print("✅ Wrote markdown summary")
            print()

        # Write run manifest (optional, for CI)
        if args.run_manifest:
            print(f"Writing run manifest: {args.run_manifest}")
            write_run_manifest(args.run_manifest, seed, ledger_hash)
            print("✅ Wrote run manifest")
            print()

        # Success summary
        print("=" * 70)
        print("✅ SUCCESS: Trend Ledger generated")
        print("=" * 70)
        print(f"Output JSON:     {args.output_json}")
        if args.output_markdown:
            print(f"Output Markdown: {args.output_markdown}")
        if args.run_manifest:
            print(f"Run Manifest:    {args.run_manifest}")
        print()

        return 0

    except SchemaVersionError as e:
        print("=" * 70)
        print(f"❌ SCHEMA VERSION ERROR: {e}")
        print("=" * 70)
        print()
        print("The input Trend Seed has an unsupported schema version.")
        print("This consumer supports Phase 5A seeds with schema v0.1.0.")
        print()
        return 1

    except ValidationError as e:
        print("=" * 70)
        print(f"❌ VALIDATION ERROR: {e}")
        print("=" * 70)
        print()
        print("The input Trend Seed is missing required fields or has invalid data.")
        print("Ensure the seed was generated by Phase 5A consumer (v0.1.0+).")
        print()
        return 1

    except TrendLedgerError as e:
        print("=" * 70)
        print(f"❌ TREND LEDGER ERROR: {e}")
        print("=" * 70)
        print()
        return 1

    except FileNotFoundError as e:
        print("=" * 70)
        print(f"❌ FILE NOT FOUND: {e}")
        print("=" * 70)
        print()
        return 1

    except Exception as e:
        print("=" * 70)
        print(f"❌ UNEXPECTED ERROR: {e}")
        print("=" * 70)
        print()
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
