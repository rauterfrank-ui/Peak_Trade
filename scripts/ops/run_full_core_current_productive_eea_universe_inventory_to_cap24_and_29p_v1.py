#!/usr/bin/env python3
"""CURRENT_PRODUCTIVE EEA universe → Cap-2.1–2.4 → 29P. GET-only. No POST.

Launch via the canonical interpreter:

  ./scripts/pt scripts/ops/run_full_core_current_productive_eea_universe_inventory_to_cap24_and_29p_v1.py ...
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_eea_universe_inventory_to_cap24_and_29p_v1 import (
    main,
)

if __name__ == "__main__":
    raise SystemExit(main())
