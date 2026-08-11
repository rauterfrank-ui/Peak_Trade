#!/usr/bin/env python3
"""Verify LONG_RUNNING_TESTNET_PROVEN prep/eval package (offline; PROVEN=false)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (str(_REPO_ROOT), str(_SRC_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from src.ops.capability_11_long_running_testnet_proven_prep_eval_v1.constants_v1 import (  # noqa: E402
    EVIDENCE_DIRNAME,
)
from src.ops.capability_11_long_running_testnet_proven_prep_eval_v1.verifier_v1 import (  # noqa: E402
    verify_capability_11_long_running_testnet_proven_prep_eval_v1,
)


def main(argv: list[str] | None = None) -> int:
    _ = argv
    evidence_dir = _REPO_ROOT / "docs" / "evidence" / EVIDENCE_DIRNAME
    result = verify_capability_11_long_running_testnet_proven_prep_eval_v1(
        evidence_dir=evidence_dir
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
