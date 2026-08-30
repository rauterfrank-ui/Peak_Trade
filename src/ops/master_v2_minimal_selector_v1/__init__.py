"""Master V2 minimal selector V1 (Owner policy; not historical GFU semantics).

OWNER_POLICY_VERSION=V1
HISTORICAL_CLAIM=false

Census → structural eligibility → exactly-one-or-none → durable artifact →
narrowed runtime-binding adapter. Ranking is not a selection authority.
"""

from __future__ import annotations

from src.ops.master_v2_minimal_selector_v1.constants_v1 import (
    CAPABILITY_ID,
    HISTORICAL_CLAIM,
    OWNER,
    OWNER_SELECTOR_POLICY_VERSION,
    PACKAGE_MARKER,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
)
from src.ops.master_v2_minimal_selector_v1.models_v1 import MasterV2SelectionDecisionV1
from src.ops.master_v2_minimal_selector_v1.persistence_v1 import (
    load_and_validate_selection_decision_v1,
    persist_selection_decision_atomic_v1,
)
from src.ops.master_v2_minimal_selector_v1.runtime_binding_adapter_v1 import (
    adapt_master_v2_selection_to_runtime_binding_v1,
)
from src.ops.master_v2_minimal_selector_v1.selection_v1 import (
    decide_master_v2_minimal_selection_v1,
    trigger_master_v2_minimal_selection_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "HISTORICAL_CLAIM",
    "OWNER",
    "OWNER_SELECTOR_POLICY_VERSION",
    "PACKAGE_MARKER",
    "PRODUCER_VERSION",
    "SCHEMA_VERSION",
    "MasterV2SelectionDecisionV1",
    "adapt_master_v2_selection_to_runtime_binding_v1",
    "decide_master_v2_minimal_selection_v1",
    "load_and_validate_selection_decision_v1",
    "persist_selection_decision_atomic_v1",
    "trigger_master_v2_minimal_selection_v1",
]
