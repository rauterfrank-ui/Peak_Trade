#!/usr/bin/env python3
"""Productive §11.12.8 Testnet campaign run activation operator entrypoint.

IMPLEMENTATION_ONLY hard-refuse surface. This entrypoint never activates a
campaign run, never mints/consumes confirm tokens, and never produces
network/order side effects. A later separate Owner-GO is required.
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

from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_run_activation_v1.activation_v1 import (  # noqa: E402
    Productive11128CampaignRunActivationError,
    activate_productive_testnet_campaign_run_v1,
)
from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_run_activation_v1.constants_v1 import (  # noqa: E402
    ACTIVATION_AUTHORIZED,
    CAPABILITY_ID,
    NETWORK_EFFECT,
    NEXT_CONSUMER_CAPABILITY_ID,
    ORDER_EFFECT,
    LIVE_ORDER_EFFECT,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    RUN_AUTHORIZED,
    RUN_PREDECESSOR_ORIGIN_MAIN_SHA,
    SECTION_11_13_STARTED,
)


def main(argv: list[str] | None = None) -> int:
    _ = argv
    refuse_reason = "NOT_RUN"
    try:
        activate_productive_testnet_campaign_run_v1(owner_go=False)
        status = "UNEXPECTED_SUCCESS"
        refuse_reason = "NONE"
        rc = 2
    except Productive11128CampaignRunActivationError as exc:
        status = "FAIL_CLOSED"
        refuse_reason = str(exc)
        rc = 0

    print(
        json.dumps(
            {
                "STATUS": status,
                "CAPABILITY_ID": CAPABILITY_ID,
                "RUN_PREDECESSOR_ORIGIN_MAIN_SHA": RUN_PREDECESSOR_ORIGIN_MAIN_SHA,
                "ACTIVATION_PERFORMED": False,
                "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
                "RUN_AUTHORIZED": RUN_AUTHORIZED,
                "ACTIVATION_AUTHORIZED": ACTIVATION_AUTHORIZED,
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
