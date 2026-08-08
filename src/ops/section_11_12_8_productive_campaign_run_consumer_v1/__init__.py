"""§11.12.8 productive campaign RUN CONSUMER package.

PRODUCTIVE_SECTION_11_12_8_CAMPAIGN_RUN_CONSUMER — executable consumer surface
after the terminal. Implementation-only; hard-refuses productive execution.
"""

from __future__ import annotations

from src.ops.section_11_12_8_productive_campaign_run_consumer_v1.constants_v1 import (
    CAPABILITY_ID,
    NEW_WRAPPER_LAYER_CREATED,
    OWNER,
    PRODUCTIVE_RUN_CONSUMER_IMPLEMENTED,
    PRODUCTIVE_RUN_CONSUMER_PRESENT,
    PRODUCTIVE_RUN_EXECUTION_AUTHORIZED,
    RUN_CONSUMER_CANONICAL_ROLE,
)
from src.ops.section_11_12_8_productive_campaign_run_consumer_v1.run_consumer_v1 import (
    build_section_11_12_8_run_consumer_record_v1,
    execute_section_11_12_8_productive_campaign_run_v1,
    prove_section_11_12_8_run_consumer_v1,
)
from src.ops.section_11_12_8_productive_campaign_run_consumer_v1.verifier_v1 import (
    verify_section_11_12_8_run_consumer_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "OWNER",
    "RUN_CONSUMER_CANONICAL_ROLE",
    "PRODUCTIVE_RUN_CONSUMER_IMPLEMENTED",
    "PRODUCTIVE_RUN_CONSUMER_PRESENT",
    "PRODUCTIVE_RUN_EXECUTION_AUTHORIZED",
    "NEW_WRAPPER_LAYER_CREATED",
    "build_section_11_12_8_run_consumer_record_v1",
    "execute_section_11_12_8_productive_campaign_run_v1",
    "prove_section_11_12_8_run_consumer_v1",
    "verify_section_11_12_8_run_consumer_v1",
]
