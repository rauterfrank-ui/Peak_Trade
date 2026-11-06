"""§11.12.8 terminal productive campaign consumer package.

TERMINAL_PRODUCTIVE_CONSUMER_SECTION_11_12_8 — single terminal for Master
Runbook §11.12.8. Not a PATH/EXECUTION/RUN/RUN_ACTIVATION wrapper.
"""

from __future__ import annotations

from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.constants_v1 import (
    CAPABILITY_ID,
    NEW_WRAPPER_LAYER_CREATED,
    OWNER,
    TERMINAL_CONSUMER_CANONICAL_ROLE,
    TERMINAL_CONSUMER_IMPLEMENTED,
)
from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.terminal_consumer_v1 import (
    build_section_11_12_8_terminal_consumer_record_v1,
    prove_section_11_12_8_terminal_consumer_v1,
    run_section_11_12_8_terminal_consumer_v1,
)
from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.verifier_v1 import (
    verify_section_11_12_8_terminal_consumer_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "OWNER",
    "TERMINAL_CONSUMER_CANONICAL_ROLE",
    "TERMINAL_CONSUMER_IMPLEMENTED",
    "NEW_WRAPPER_LAYER_CREATED",
    "build_section_11_12_8_terminal_consumer_record_v1",
    "prove_section_11_12_8_terminal_consumer_v1",
    "run_section_11_12_8_terminal_consumer_v1",
    "verify_section_11_12_8_terminal_consumer_v1",
]
