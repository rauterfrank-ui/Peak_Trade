#!/usr/bin/env python3
"""Verify §11.12.8 ACTUAL productive Testnet campaign RUN START package."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (str(_REPO_ROOT), str(_SRC_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.verifier_v1 import (  # noqa: E402
    verify_section_11_12_8_actual_productive_testnet_campaign_run_start_v1,
)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="pt_11_12_8_actual_verify_") as tmp:
        result = verify_section_11_12_8_actual_productive_testnet_campaign_run_start_v1(
            work_dir=Path(tmp)
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
