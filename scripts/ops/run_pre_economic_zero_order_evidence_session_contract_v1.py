#!/usr/bin/env python3
"""Offline evaluator CLI for PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1.

Never starts a session, never opens network, never submits orders.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ops.pre_economic_zero_order_evidence_session_contract_v1 import (  # noqa: E402
    evaluate_pre_economic_zero_order_evidence_session_contract_v1,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1 (offline, "
            "non-activating). Does not execute a session."
        )
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Optional path to write JSON result",
    )
    args = parser.parse_args(argv)

    result = evaluate_pre_economic_zero_order_evidence_session_contract_v1()
    payload = result.to_dict()

    if args.output_path is not None:
        args.output_path.parent.mkdir(parents=True, exist_ok=True)
        args.output_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"capability_id={result.capability_id}")
        print(f"session_contract_id={result.session_contract_id}")
        print(f"authority_effect={result.authority_effect}")
        print(f"activation_effect={result.activation_effect}")
        print(f"economic_gate_effect={result.economic_gate_effect}")
        print(f"default_state={result.default_state}")
        print(f"runtime_execution={result.runtime_execution}")
        print(f"session_admissible={result.session_admissible}")
        print(f"six_hour_session_ready={result.six_hour_session_ready}")
        print(f"orders_allowed={result.orders_allowed}")
        print(f"broker_writes_allowed={result.broker_writes_allowed}")
        print(
            "economic_validity_offline_gate_pass_changed="
            f"{result.economic_validity_offline_gate_pass_changed}"
        )
        if result.blockers:
            print("blockers=" + ",".join(result.blockers))

    # Exit 0 = evaluator healthy; admissibility remains encoded in payload.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
