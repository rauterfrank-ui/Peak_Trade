#!/usr/bin/env python3
"""Explicit control-plane CLI for MASTER_V2_MINIMAL_SELECTOR_V1.

Offline/injected OKX EEA census only. No network, no ranking authority, no
automatic refresh, no trading/activation. Invoke once per explicit call.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.master_v2_minimal_selector_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    OWNER_SELECTOR_POLICY_VERSION,
    VENUE,
)
from src.ops.master_v2_minimal_selector_v1.persistence_v1 import (  # noqa: E402
    persist_selection_decision_atomic_v1,
)
from src.ops.master_v2_minimal_selector_v1.selection_v1 import (  # noqa: E402
    trigger_master_v2_minimal_selection_v1,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=CAPABILITY_ID)
    parser.add_argument("--instruments-json", required=True, type=Path)
    parser.add_argument("--mark-price-json", type=Path, default=None)
    parser.add_argument("--source-event-time", type=str, default=None)
    parser.add_argument("--venue", type=str, default=VENUE)
    parser.add_argument("--state-root", type=Path, default=None)
    parser.add_argument("--ranking-json", type=Path, default=None)
    args = parser.parse_args(argv)

    instruments = json.loads(args.instruments_json.read_text(encoding="utf-8"))
    marks = None
    if args.mark_price_json is not None:
        marks = json.loads(args.mark_price_json.read_text(encoding="utf-8"))
    ranking = None
    if args.ranking_json is not None:
        ranking = json.loads(args.ranking_json.read_text(encoding="utf-8"))

    decision = trigger_master_v2_minimal_selection_v1(
        source_payload=instruments,
        mark_price_payload=marks,
        source_event_time=args.source_event_time,
        venue=args.venue,
        ranking_snapshot=ranking,
    )
    if args.state_root is not None:
        persist_selection_decision_atomic_v1(state_root=args.state_root, decision=decision)
    print(json.dumps(decision.to_dict(), sort_keys=True, indent=2))
    print(
        json.dumps(
            {
                "OWNER_SELECTOR_POLICY_VERSION": OWNER_SELECTOR_POLICY_VERSION,
                "HISTORICAL_CLAIM": False,
                "CONTROL_PLANE_TRIGGER": "EXPLICIT_ONCE",
            },
            sort_keys=True,
        ),
        file=sys.stderr,
    )
    return 0 if decision.decision_status == "SELECTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
