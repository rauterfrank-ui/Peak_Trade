#!/usr/bin/env python3
"""Offline Phase 9.2 public-MD smoke session preflight (no network, no auth)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.phase_9_2_public_md_session_preflight_v1.evidence_v1 import (  # noqa: E402
    build_preflight_evidence_v1,
)


def main() -> int:
    try:
        repository_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
        ).strip()
    except Exception:  # noqa: BLE001
        repository_sha = "UNKNOWN"
    evidence = build_preflight_evidence_v1(
        repository_sha=repository_sha,
        repo_root=_REPO_ROOT,
        materialize=True,
    )
    payload = evidence.to_dict()
    print(
        json.dumps(
            {
                "ok": evidence.ok,
                "capability_id": evidence.capability_id,
                "task_id": evidence.task_id,
                "repository_sha": evidence.repository_sha,
                "smoke_contract_digest": evidence.smoke_contract_digest,
                "PHASE_9_2_SMOKE_SESSION_PREFLIGHT_READY": payload["claims"].get(
                    "PHASE_9_2_SMOKE_SESSION_PREFLIGHT_READY"
                ),
                "gaps": evidence.gaps,
            },
            sort_keys=True,
            indent=2,
        )
    )
    return 0 if evidence.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
