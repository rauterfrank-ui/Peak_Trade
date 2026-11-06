"""§11.12.8 ACTUAL productive Testnet campaign RUN START package."""

from __future__ import annotations

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.acceptance_gate_v1 import (
    run_pre_merge_acceptance_gate_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    CAPABILITY_ID,
    OWNER,
    PACKAGE_MARKER,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.productive_consumer_v1 import (
    execute_productive_section_11_12_8_campaign_run_v1,
    refuse_real_productive_campaign_in_implementation_go_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.verifier_v1 import (
    verify_section_11_12_8_actual_productive_testnet_campaign_run_start_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "OWNER",
    "PACKAGE_MARKER",
    "execute_productive_section_11_12_8_campaign_run_v1",
    "refuse_real_productive_campaign_in_implementation_go_v1",
    "run_pre_merge_acceptance_gate_v1",
    "verify_section_11_12_8_actual_productive_testnet_campaign_run_start_v1",
]
