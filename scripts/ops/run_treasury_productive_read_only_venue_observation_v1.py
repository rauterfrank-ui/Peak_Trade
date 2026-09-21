#!/usr/bin/env python3
"""One-shot productive Treasury read-only venue observation (Owner-GO scoped)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _origin_main_sha() -> str:
    proc = subprocess.run(
        ["git", "-C", str(_REPO_ROOT), "rev-parse", "origin/main"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit("ORIGIN_MAIN_SHA_RESOLVE_FAILED")
    return (proc.stdout or "").strip()


def main(argv: list[str] | None = None) -> int:
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))

    from src.ops.treasury_productive_read_only_venue_observation_v1.constants_v1 import (  # noqa: E402
        ALLOWED_WP_OWNER_GOS,
        EVIDENCE_RELROOT,
        SESSION_OWNER_GO,
    )
    from src.ops.treasury_productive_read_only_venue_observation_v1.capture_v1 import (  # noqa: E402
        execute_treasury_productive_read_only_venue_observation_v1,
    )
    from src.ops.treasury_productive_read_only_venue_observation_v1.persist_v1 import (  # noqa: E402
        persist_treasury_productive_observation_evidence_pack_v1,
    )

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wp-owner-go", required=True)
    parser.add_argument("--session-owner-go", required=True)
    parser.add_argument("--bound-origin-main-sha", default="")
    parser.add_argument("--execute-network", action="store_true")
    args = parser.parse_args(argv)

    bound_sha = str(args.bound_origin_main_sha or "").strip() or _origin_main_sha()
    if str(args.wp_owner_go or "").strip() not in ALLOWED_WP_OWNER_GOS:
        print(f"WP_OWNER_GO_NOT_AUTHORIZED:{args.wp_owner_go}", file=sys.stderr)
        return 2
    if args.session_owner_go != SESSION_OWNER_GO:
        print(f"SESSION_OWNER_GO_MISMATCH:{args.session_owner_go}", file=sys.stderr)
        return 2

    result = execute_treasury_productive_read_only_venue_observation_v1(
        wp_owner_go=args.wp_owner_go,
        session_owner_go=args.session_owner_go,
        origin_main_sha=bound_sha,
        execute_network=args.execute_network,
    )
    public = {k: v for k, v in result.items() if k not in ("pre_network_gate",)}
    print(json.dumps(public, indent=2))

    if result.get("disposition") != "PRODUCTIVE_OBSERVATION_COMPLETE":
        return 0

    persist = persist_treasury_productive_observation_evidence_pack_v1(
        evidence_root=_REPO_ROOT / EVIDENCE_RELROOT,
        origin_main_sha=bound_sha,
        capture_result=result,
    )
    print(json.dumps(persist, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
