#!/usr/bin/env python3
"""§11.12.8 ACTUAL start operator entrypoint (stubbed acceptance / implementation GO).

Consumes the productive OWNER_GO contract through the stubbed acceptance path.
Does NOT start a real network session, load real credentials, or submit real orders.
A later separate Owner-GO for EXECUTE may use the same contract against a real path
once operators authorize real network effects outside this implementation GO.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (str(_REPO_ROOT), str(_SRC_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.acceptance_gate_v1 import (  # noqa: E402
    run_pre_merge_acceptance_gate_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    LIVE_ORDER_EFFECT,
    NETWORK_EFFECT,
    ORDER_EFFECT,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    SECTION_11_13_STARTED,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.productive_consumer_v1 import (  # noqa: E402
    ActualStartConsumerError,
    refuse_real_productive_campaign_in_implementation_go_v1,
)


def main(argv: list[str] | None = None) -> int:
    _ = argv
    refuse_status = "FAIL_CLOSED"
    refuse_reason = "NOT_RUN"
    try:
        refuse_real_productive_campaign_in_implementation_go_v1()
        refuse_status = "UNEXPECTED_SUCCESS"
        refuse_reason = "NONE"
        return 2
    except ActualStartConsumerError as exc:
        refuse_reason = str(exc)

    with tempfile.TemporaryDirectory(prefix="pt_11_12_8_actual_start_ep_") as tmp:
        gate = run_pre_merge_acceptance_gate_v1(work_dir=Path(tmp) / f"g-{uuid4().hex[:8]}")

    print(
        json.dumps(
            {
                "STATUS": "PASS" if gate.get("ok") else "FAIL",
                "CAPABILITY_ID": CAPABILITY_ID,
                "REAL_PRODUCTIVE_REFUSED": refuse_status == "FAIL_CLOSED",
                "REFUSE_REASON": refuse_reason,
                "PRE_MERGE_ACCEPTANCE_GATE": gate.get("PRE_MERGE_ACCEPTANCE_GATE"),
                "ALL_B01_B24_CLOSED": gate.get("ALL_B01_B24_CLOSED"),
                "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
                "NETWORK_EFFECT": NETWORK_EFFECT,
                "ORDER_EFFECT": ORDER_EFFECT,
                "LIVE_ORDER_EFFECT": LIVE_ORDER_EFFECT,
                "SECTION_11_13_STARTED": SECTION_11_13_STARTED,
            },
            sort_keys=True,
        )
    )
    return 0 if gate.get("ok") and refuse_status == "FAIL_CLOSED" else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
