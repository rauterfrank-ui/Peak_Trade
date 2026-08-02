"""Single Selected Future Policy V1 (Capability 2.3).

Consumes Cap 2.2 productive ranking snapshots and produces a deterministic,
persistable single selected future with open-position replacement semantics,
atomic persistence, and restart proof. Does not grant alpha, execution,
multi-future, or runtime activation authority. Dashboard/allowlist/legacy
inputs are rejected.
"""

from __future__ import annotations

from src.ops.single_selected_future_policy_v1.constants_v1 import (
    CAPABILITY_ID,
    OWNER,
    PACKAGE_MARKER,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    SELECTION_POLICY_ID,
    SELECTION_POLICY_VERSION,
)
from src.ops.single_selected_future_policy_v1.models_v1 import (
    SingleSelectedFutureSelectionV1,
)
from src.ops.single_selected_future_policy_v1.persistence_v1 import (
    load_and_validate_selection_v1,
)
from src.ops.single_selected_future_policy_v1.producer_v1 import (
    produce_from_ranking_state_root_v1,
    run_single_selected_future_policy_v1,
)
from src.ops.single_selected_future_policy_v1.selection_v1 import (
    produce_single_selected_future_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "OWNER",
    "PACKAGE_MARKER",
    "PRODUCER_VERSION",
    "SCHEMA_VERSION",
    "SELECTION_POLICY_ID",
    "SELECTION_POLICY_VERSION",
    "SingleSelectedFutureSelectionV1",
    "load_and_validate_selection_v1",
    "produce_from_ranking_state_root_v1",
    "produce_single_selected_future_v1",
    "run_single_selected_future_policy_v1",
]
