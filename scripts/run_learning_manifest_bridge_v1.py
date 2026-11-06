#!/usr/bin/env python3
"""
Offline Learning Bridge v1 — explicit snippet input to ConfigPatch-Manifest v1.

Produces a validated, deterministic ConfigPatch-Manifest v1 JSON artifact only.
No promotion, apply, runtime, or live authority.

Usage:
    python3 scripts/run_learning_manifest_bridge_v1.py \\
        --input-path reports/learning_snippets/example.json \\
        --output-path reports/learning_manifests/example_manifest.json \\
        --manifest-id 11111111-1111-4111-8111-111111111111 \\
        --lineage-manifest-ref 22222222-2222-4222-8222-222222222222
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.meta.learning_loop.config_patch_manifest_v1 import ConfigPatchManifestValidationError
from src.meta.learning_loop.manifest_bridge_v1 import (
    LearningManifestBridgeError,
    produce_config_patch_manifest_v1_from_paths,
)

EXIT_OK = 0
EXIT_BRIDGE_ERROR = 1
EXIT_USAGE_ERROR = 2


def _parse_generated_at(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("generated-at must be an ISO8601 timestamp") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline Learning Bridge v1: explicit snippet/patch input to "
            "validated ConfigPatch-Manifest v1 JSON."
        )
    )
    parser.add_argument(
        "--input-path",
        type=Path,
        required=True,
        help="Explicit offline learning snippet input (.json or .jsonl).",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        required=True,
        help="Destination path for the validated ConfigPatch-Manifest v1 JSON file.",
    )
    parser.add_argument(
        "--manifest-id",
        required=True,
        help="Explicit UUID for the produced ConfigPatch-Manifest v1 manifest_id.",
    )
    parser.add_argument(
        "--lineage-manifest-ref",
        required=True,
        help="Explicit UUID lineage_manifest_ref (never invented by the bridge).",
    )
    parser.add_argument(
        "--generated-at",
        type=_parse_generated_at,
        default=None,
        help="Optional ISO8601 timestamp for manifest generated_at (default: UTC now).",
    )
    parser.add_argument(
        "--generated-by",
        default="package_d_learning_manifest_bridge_v1",
        help="Optional generated_by label stored in the manifest envelope.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.input_path.is_file():
        print(
            f"[learning_manifest_bridge] ERROR: input file not found: {args.input_path}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        manifest = produce_config_patch_manifest_v1_from_paths(
            input_path=args.input_path,
            output_path=args.output_path,
            manifest_id=args.manifest_id,
            lineage_manifest_ref=args.lineage_manifest_ref,
            generated_at=args.generated_at,
            generated_by=args.generated_by,
        )
    except LearningManifestBridgeError as exc:
        print(f"[learning_manifest_bridge] ERROR: {exc}", file=sys.stderr)
        return EXIT_BRIDGE_ERROR
    except ConfigPatchManifestValidationError as exc:
        print(f"[learning_manifest_bridge] VALIDATION_ERROR: {exc}", file=sys.stderr)
        if exc.verdict:
            print(f"[learning_manifest_bridge] VERDICT={exc.verdict}", file=sys.stderr)
        return EXIT_BRIDGE_ERROR

    print(
        "[learning_manifest_bridge] wrote validated ConfigPatch-Manifest v1 to "
        f"{args.output_path} (manifest_id={manifest.manifest_id}, "
        f"patches={len(manifest.patches)})"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
