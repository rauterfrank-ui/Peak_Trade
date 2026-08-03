#!/usr/bin/env python3
"""Canonical Peak_Trade local runtime launcher (O2).

Command surface:
  preflight | start | status | health | stop | restart | recover

Does not authorize live/testnet/paper exchange orders, credentials,
confirm-token minting, or public network sessions. Legacy launch paths
remain intact (deauthorization is O8).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ops.canonical_local_launcher_and_process_supervision_v1.cli_v1 import (  # noqa: E402
    main,
)

if __name__ == "__main__":
    raise SystemExit(main())
