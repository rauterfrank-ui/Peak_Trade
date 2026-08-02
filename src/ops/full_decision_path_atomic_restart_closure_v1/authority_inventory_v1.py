"""Authority inventory for Cap 6.4 — coordinator only; members keep their owners."""

from __future__ import annotations

from typing import Any

from src.ops.full_decision_path_atomic_restart_closure_v1.constants_v1 import (
    ATOMICITY_MODEL,
    MASTER_V2_NEW_PERSISTENCE_DOMAIN_MODEL_ALLOWED,
    DOUBLE_PLAY_NEW_PERSISTENCE_DOMAIN_MODEL_ALLOWED,
    NO_NEW_PARALLEL_STATE_MODEL,
    OWNER,
    PREDECESSOR_CAP31,
    PREDECESSOR_CAP61,
    PREDECESSOR_CAP62,
    PREDECESSOR_CAPABILITY,
    SERIALIZATION_ADAPTER_HAS_NO_DECISION_AUTHORITY,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.state_classification_v1 import (
    build_state_root_classification_matrix_v1,
    classify_fields_by_bucket_v1,
)


def inventory_decision_path_atomic_authority_v1() -> dict[str, Any]:
    buckets = classify_fields_by_bucket_v1()
    return {
        "coordinator_owner": OWNER,
        "atomicity_model": ATOMICITY_MODEL,
        "serialization_adapter_has_no_decision_authority": (
            SERIALIZATION_ADAPTER_HAS_NO_DECISION_AUTHORITY
        ),
        "no_new_parallel_state_model": NO_NEW_PARALLEL_STATE_MODEL,
        "master_v2_new_persistence_domain_model_allowed": (
            MASTER_V2_NEW_PERSISTENCE_DOMAIN_MODEL_ALLOWED
        ),
        "double_play_new_persistence_domain_model_allowed": (
            DOUBLE_PLAY_NEW_PERSISTENCE_DOMAIN_MODEL_ALLOWED
        ),
        "member_owners": {
            "confirmation": PREDECESSOR_CAP61,
            "dynamic_scope": PREDECESSOR_CAP62,
            "decision_config": PREDECESSOR_CAPABILITY,
            "accounting_portfolio": PREDECESSOR_CAP31,
        },
        "state_root_matrix": build_state_root_classification_matrix_v1(),
        "classification_buckets": buckets,
        "parallel_state_authority_created": False,
        "core_logic_changed": False,
        "one_state_owner_per_state_root": True,
        "one_authoritative_writer_per_state_root": True,
    }
