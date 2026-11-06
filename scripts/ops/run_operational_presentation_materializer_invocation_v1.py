#!/usr/bin/env python3
"""CLI for CAPABILITY_PRESENTATION_PROJECTION_OPERATIONAL_MATERIALIZER_INVOCATION_V1.

Governed, bounded sibling-only refresh of presentation projections under an explicit
archive root. Requires --owner-go and --generated-at. Does not export siblings or
mutate trading state.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from src.ops.presentation_projection_operational_materializer_invocation_v1 import (  # noqa: E402
    CAPABILITY_ID,
    OPERATIONAL_SIBLING_MATERIALIZER_FAMILIES,
    run_operational_presentation_materializer_invocation_v1,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Operational presentation materializer invocation (sibling-only). "
            "Requires explicit archive root, generated-at, and Owner-GO."
        )
    )
    parser.add_argument("--archive-root", required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument(
        "--families",
        default=None,
        help=(
            "Optional comma-separated family ids. "
            f"Default: {','.join(OPERATIONAL_SIBLING_MATERIALIZER_FAMILIES)}"
        ),
    )
    parser.add_argument("--effective-at", default=None)
    parser.add_argument("--source-reference", default=None)
    parser.add_argument(
        "--owner-go",
        action="store_true",
        default=False,
        help="Explicit Owner authorization for operational invocation.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    families = None
    if args.families is not None and str(args.families).strip():
        families = [part.strip() for part in str(args.families).split(",") if part.strip()]

    result = run_operational_presentation_materializer_invocation_v1(
        archive_root=args.archive_root,
        generated_at=args.generated_at,
        owner_go=bool(args.owner_go),
        families=families,
        effective_at=args.effective_at,
        source_reference=args.source_reference,
    )
    payload = result.to_dict()
    payload["capability_id"] = CAPABILITY_ID
    print(json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
