#!/usr/bin/env python3
"""Offline P08 post-read-only-exhaustion authority-boundary persist. No GET. No POST."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.assemble_v1 import (  # noqa: E402
    P08AuthorityBoundaryAssembleError,
    assemble_p08_authority_boundary_v1,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.constants_v1 import (  # noqa: E402
    CANONICAL_EVIDENCE_RUN_ID,
    EVIDENCE_DIRNAME,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
)

REPO_ROOT = _REPO_ROOT


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-go", required=True)
    parser.add_argument("--bound-origin-main-sha", required=True)
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    if args.owner_go != OWNER_GO:
        print(f"OWNER_GO_MISMATCH:{args.owner_go}", file=sys.stderr)
        return 2
    if args.bound_origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        print(f"ORIGIN_MAIN_SHA_MISMATCH:{args.bound_origin_main_sha}", file=sys.stderr)
        return 2
    evidence_root = None
    if args.persist:
        evidence_root = REPO_ROOT / "evidence" / "ops" / EVIDENCE_DIRNAME
    try:
        result = assemble_p08_authority_boundary_v1(
            origin_main_sha=args.bound_origin_main_sha,
            evidence_root=evidence_root,
            run_id=CANONICAL_EVIDENCE_RUN_ID,
        )
    except P08AuthorityBoundaryAssembleError as exc:
        print(f"P08_AUTHORITY_BOUNDARY_ASSEMBLE_FAILED:{exc}", file=sys.stderr)
        return 2
    print("P08_AUTHORITY_BOUNDARY_RESULT=")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    if evidence_root is not None:
        print(f"EVIDENCE_PACK={result['EVIDENCE_PACK']}")
        print(f"MANIFEST_VERIFY_RC={result['MANIFEST_VERIFY_RC']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
