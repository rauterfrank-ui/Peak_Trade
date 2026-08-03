#!/usr/bin/env python3
"""Verify a Phase 9.2 PRE/POST restart bundle (no network, no mutation of claims)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.verifier_v1 import (  # noqa: E402
    verify_restart_bundle_v1,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--persistence-root", type=Path, required=True)
    args = parser.parse_args()
    result = verify_restart_bundle_v1(persistence_root=args.persistence_root)
    print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
    return 0 if result.verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
