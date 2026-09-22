#!/usr/bin/env python3
"""Canonical Cap-24 selection-state productivity root writer (Cap-2.1–2.3 only).

Launch via the canonical interpreter:

  ./scripts/pt scripts/ops/run_current_productive_cap24_selection_state_canonical_writer_v1.py ...

Productive execution requires Owner-GO and injected/fresh EEA acquisition input.
"""

from __future__ import annotations

from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_cap24_selection_state_canonical_writer_v1 import (
    main,
)

if __name__ == "__main__":
    raise SystemExit(main())
