#!/usr/bin/env python3
"""§11.12.8 productive campaign RUN CONSUMER operator entrypoint (implementation-only).

Never starts a productive campaign, never loads credentials, never submits
orders, never opens network sessions. Separate Owner-GO required for productive
run activation/execution.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (str(_REPO_ROOT), str(_SRC_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from src.ops.section_11_12_8_productive_campaign_run_consumer_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    CREDENTIAL_PLAINTEXT_LOADED,
    LIVE_ORDER_EFFECT,
    NETWORK_EFFECT,
    NEW_WRAPPER_LAYER_CREATED,
    NEXT_CONSUMER_CAPABILITY_ID,
    ORDER_EFFECT,
    PRODUCTIVE_RUN_CONSUMER_PRESENT,
    PRODUCTIVE_RUN_EXECUTION_AUTHORIZED,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    RUN_CONSUMER_CANONICAL_ROLE,
    SECTION_11_13_STARTED,
)
from src.ops.section_11_12_8_productive_campaign_run_consumer_v1.run_consumer_v1 import (  # noqa: E402
    Section11128RunConsumerError,
    execute_section_11_12_8_productive_campaign_run_v1,
)


def main(argv: list[str] | None = None) -> int:
    _ = argv
    refuse_reason = "NOT_RUN"
    try:
        execute_section_11_12_8_productive_campaign_run_v1(owner_go=False)
        status = "UNEXPECTED_SUCCESS"
        refuse_reason = "NONE"
        rc = 2
    except Section11128RunConsumerError as exc:
        status = "FAIL_CLOSED"
        refuse_reason = str(exc)
        rc = 0

    print(
        json.dumps(
            {
                "STATUS": status,
                "CAPABILITY_ID": CAPABILITY_ID,
                "RUN_CONSUMER_CANONICAL_ROLE": RUN_CONSUMER_CANONICAL_ROLE,
                "PRODUCTIVE_RUN_CONSUMER_PRESENT": PRODUCTIVE_RUN_CONSUMER_PRESENT,
                "PRODUCTIVE_RUN_EXECUTION_AUTHORIZED": PRODUCTIVE_RUN_EXECUTION_AUTHORIZED,
                "NEW_WRAPPER_LAYER_CREATED": NEW_WRAPPER_LAYER_CREATED,
                "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
                "CREDENTIAL_PLAINTEXT_LOADED": CREDENTIAL_PLAINTEXT_LOADED,
                "NETWORK_EFFECT": NETWORK_EFFECT,
                "ORDER_EFFECT": ORDER_EFFECT,
                "LIVE_ORDER_EFFECT": LIVE_ORDER_EFFECT,
                "SECTION_11_13_STARTED": SECTION_11_13_STARTED,
                "CONFIRM_TOKEN_MINTED": False,
                "CONFIRM_TOKEN_CONSUMED": False,
                "REFUSE_REASON": refuse_reason,
                "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
            },
            sort_keys=True,
        )
    )
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
