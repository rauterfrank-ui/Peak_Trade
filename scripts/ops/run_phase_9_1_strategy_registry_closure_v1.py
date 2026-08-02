#!/usr/bin/env python3
"""Offline Phase 9.1 strategy registry closure evidence entrypoint (no network)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.phase_9_1_strategy_registry_closure_v1.evidence_v1 import (  # noqa: E402
    build_capability_evidence_v1,
)


def main() -> int:
    try:
        repository_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
        ).strip()
    except Exception:  # noqa: BLE001
        repository_sha = "UNKNOWN"
    evidence = build_capability_evidence_v1(repository_sha=repository_sha, repo_root=_REPO_ROOT)
    payload = evidence.to_dict()
    print(
        json.dumps(
            {
                "ok": evidence.ok,
                "strategy_count": evidence.strategy_count,
                "classification_counts": evidence.classification_counts,
                "claims": payload["claims"],
            },
            sort_keys=True,
            indent=2,
        )
    )
    return 0 if evidence.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
