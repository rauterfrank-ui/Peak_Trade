#!/usr/bin/env python3
"""Materialize momentum 1h v2 execution authorization supersession v1 config."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.momentum_1h_v2_offline_economic_evaluation_execution_authorization_supersession_v1 import (  # noqa: E402
    CONFIG_REL_PATH,
    materialize_execution_authorization_supersession_v1,
)


def main() -> None:
    payload = materialize_execution_authorization_supersession_v1(repo_root=_REPO_ROOT)
    out_path = _REPO_ROOT / CONFIG_REL_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
