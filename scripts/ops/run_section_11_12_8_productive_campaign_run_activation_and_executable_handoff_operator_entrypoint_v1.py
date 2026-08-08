#!/usr/bin/env python3
"""§11.12.8 activation+handoff operator entrypoint (implementation-only / dry proof).

Never starts a productive Testnet campaign. Separate Owner-GO required for
ACTUAL_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_START.
"""

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

from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.activation_executor_v1 import (  # noqa: E402
    Section11128ActivationExecutorError,
    prove_section_11_12_8_activation_and_executable_handoff_v1,
    refuse_productive_campaign_start_v1,
)
from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    LIVE_ORDER_EFFECT,
    NETWORK_EFFECT,
    NEXT_CONSUMER_CAPABILITY_ID,
    ORDER_EFFECT,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    SECTION_11_13_STARTED,
)


def main(argv: list[str] | None = None) -> int:
    _ = argv
    refuse_reason = "NOT_RUN"
    try:
        refuse_productive_campaign_start_v1()
        status = "UNEXPECTED_SUCCESS"
        refuse_reason = "NONE"
        rc = 2
    except Section11128ActivationExecutorError as exc:
        status = "FAIL_CLOSED"
        refuse_reason = str(exc)
        rc = 0

    with tempfile.TemporaryDirectory(prefix="pt_11_12_8_entrypoint_dry_") as tmp:
        proof = prove_section_11_12_8_activation_and_executable_handoff_v1(work_dir=Path(tmp))

    print(
        json.dumps(
            {
                "STATUS": status,
                "CAPABILITY_ID": CAPABILITY_ID,
                "PRODUCTIVE_START_REFUSED": status == "FAIL_CLOSED",
                "REFUSE_REASON": refuse_reason,
                "END_TO_END_DRY_ACTIVATION_PROOF": bool(proof.get("ok")),
                "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
                "NETWORK_EFFECT": NETWORK_EFFECT,
                "ORDER_EFFECT": ORDER_EFFECT,
                "LIVE_ORDER_EFFECT": LIVE_ORDER_EFFECT,
                "SECTION_11_13_STARTED": SECTION_11_13_STARTED,
                "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
            },
            sort_keys=True,
        )
    )
    return rc if proof.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
