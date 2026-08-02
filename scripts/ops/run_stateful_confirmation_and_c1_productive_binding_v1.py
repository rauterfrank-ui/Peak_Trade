#!/usr/bin/env python3
"""Offline Cap 6.1 runner — no network, no activation, no authorization consumption."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.stateful_confirmation_and_c1_productive_binding_v1.cycle_harness_v1 import (  # noqa: E402
    ConfirmationHarnessEventV1,
    run_confirmation_harness_v1,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.host_binding_v1 import (  # noqa: E402
    ObservationCycleKindV1,
)


def main() -> int:
    import subprocess
    import tempfile

    repository_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
    ).strip()
    root = Path(tempfile.mkdtemp(prefix="cap61_run_"))
    events = [
        ConfirmationHarnessEventV1(
            kind=ObservationCycleKindV1.MARKET_SAMPLE, mid_price=100.0 + i * 0.5
        )
        for i in range(6)
    ]
    result = run_confirmation_harness_v1(
        events,
        repository_sha=repository_sha,
        confirmation_state_root=root,
    )
    print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
