#!/usr/bin/env python3
"""CLI for the current-SHA no-order Package-N wiring orchestrator (non-activating)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.canonical_current_sha_no_order_package_n_e2e_v1.constants_v1 import (  # noqa: E402
    COMPLETE_CURRENT_SYSTEM_E2E_PROVEN,
    EXPECTED_ORIGIN_MAIN_SHA,
)
from src.ops.canonical_current_sha_no_order_package_n_e2e_v1.orchestrator_v1 import (  # noqa: E402
    CanonicalCurrentShaNoOrderPackageNE2EError,
    run_canonical_current_sha_no_order_package_n_e2e_v1,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Wire Cap 7.1/7.2 no-order evidence to Package-N and EG-I82 owners."
    )
    parser.add_argument(
        "--run-id", required=True, help="Unique run identifier (not Package-N IDENTITY)."
    )
    parser.add_argument(
        "--repository-sha",
        default=EXPECTED_ORIGIN_MAIN_SHA,
        help="Must equal origin/main SHA 9f09d6d18484e35e788f5e4eaada2c598926b77f.",
    )
    parser.add_argument(
        "--repo-root",
        default=str(_REPO_ROOT),
        help="Repository root. Evidence is written under out/ops/ only.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if COMPLETE_CURRENT_SYSTEM_E2E_PROVEN is not False:
        print("COMPLETE_CURRENT_SYSTEM_E2E_PROVEN must remain false", file=sys.stderr)
        return 2
    try:
        result = run_canonical_current_sha_no_order_package_n_e2e_v1(
            repo_root=Path(args.repo_root),
            run_id=str(args.run_id),
            repository_sha=str(args.repository_sha),
        )
    except CanonicalCurrentShaNoOrderPackageNE2EError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
