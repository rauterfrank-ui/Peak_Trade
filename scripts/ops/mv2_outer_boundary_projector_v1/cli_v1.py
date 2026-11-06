"""CLI for the read-only Master V2 outer-boundary projector."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.ops.mv2_outer_boundary_projector_v1.input_contract_v1 import (
    ProjectorFailClosedV1,
    ProjectorRequestV1,
)
from scripts.ops.mv2_outer_boundary_projector_v1.output_contract_v1 import (
    canonical_json_v1,
)
from scripts.ops.mv2_outer_boundary_projector_v1.run_v1 import (
    run_mv2_outer_boundary_projector_v1,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only MV2 outer boundary projector")
    parser.add_argument("--commit", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default="")
    args = parser.parse_args(argv)
    output = Path(args.output) if args.output else None
    try:
        report = run_mv2_outer_boundary_projector_v1(
            ProjectorRequestV1(commit=args.commit, tree=args.tree),
            repo_root=Path(args.repo_root),
            output_path=output,
        )
    except ProjectorFailClosedV1 as exc:
        print(f"FAIL_CLOSED {exc.code} {exc.detail}", file=sys.stderr)
        return 2
    sys.stdout.write(canonical_json_v1(report))
    return 0
