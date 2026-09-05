"""Offline Core→Live composition root. No wire send. No LiveExecutionPort construction."""

from __future__ import annotations

from src.ops.full_core_live_path_composition_root_v1.canary_isolation_v1 import (
    refuse_canary_plan_as_full_core_e2e_v1,
)
from src.ops.full_core_live_path_composition_root_v1.composition_root_v1 import (
    compose_core_live_execution_intent_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CAPABILITY_ID,
    CURRENT_LIVE_CORE_PATH_PROVEN,
    FULL_CORE_RESTART_TEST_AUTHORIZED,
    FULL_CORE_SYSTEM_E2E_PROVEN,
    LIVE_ARMED,
    LIVE_ENABLED,
    OWNER,
    PACKAGE_MARKER,
    PATH_KIND,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ExecutionAdmissionDecisionV1,
    evaluate_execution_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import (
    CoreLiveExecutionIntentV1,
    FrozenPretradeEvidenceV1,
    FullCoreLivePathInputV1,
    FullCoreLivePathResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.path_v1 import (
    run_full_core_live_path_offline_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "CURRENT_LIVE_CORE_PATH_PROVEN",
    "CoreLiveExecutionIntentV1",
    "ExecutionAdmissionDecisionV1",
    "FrozenPretradeEvidenceV1",
    "FULL_CORE_RESTART_TEST_AUTHORIZED",
    "FULL_CORE_SYSTEM_E2E_PROVEN",
    "FullCoreLivePathInputV1",
    "FullCoreLivePathResultV1",
    "LIVE_ARMED",
    "LIVE_ENABLED",
    "OWNER",
    "PACKAGE_MARKER",
    "PATH_KIND",
    "WIRE_SEND_PERMITTED",
    "compose_core_live_execution_intent_v1",
    "evaluate_execution_admission_v1",
    "refuse_canary_plan_as_full_core_e2e_v1",
    "run_full_core_live_path_offline_v1",
]
