#!/usr/bin/env python3
"""Offline Cap 7.2 activation evidence entrypoint (no network session)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.single_future_stateful_no_order_runtime_activation_v1.cycle_harness_v1 import (  # noqa: E402
    build_capability_evidence_v1,
)


def main() -> int:
    import subprocess
    import tempfile

    try:
        repository_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
        ).strip()
    except Exception:  # noqa: BLE001
        repository_sha = "UNKNOWN"
    with tempfile.TemporaryDirectory(prefix="cap72_activation_") as tmp:
        evidence = build_capability_evidence_v1(
            repository_sha=repository_sha, work_root=Path(tmp) / "work"
        )
    payload = evidence.to_dict()
    print(json.dumps({"ok": evidence.ok, "claims": payload["claims"]}, sort_keys=True, indent=2))
    return 0 if evidence.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
