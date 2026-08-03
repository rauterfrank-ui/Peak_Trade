#!/usr/bin/env python3
"""Canonical Peak_Trade local runtime launcher (O2 + O8 activation surface).

CANONICAL_OPERATOR_ENTRYPOINT for Peak_Trade local runtime operations.

Command surface:
  preflight | start | status | health | logs | stop | restart | recover | verify

Does not authorize live/testnet/paper exchange orders, credentials,
confirm-token minting, or public network sessions.

Legacy launch paths remain physically present and callable. Operator
recommendation and documentation pointers are activated to this entrypoint
under CAPABILITY_O8_CANONICAL_RUNTIME_OPERATIONS_ACTIVATION_V1. Legacy
deletion or functional mutation is out of scope for O8 bounded activation.
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
