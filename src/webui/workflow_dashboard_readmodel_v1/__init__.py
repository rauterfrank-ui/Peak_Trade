"""Fixture/offline builder für workflow_dashboard_readmodel.v1 (display-only)."""

from __future__ import annotations

from .builder import build_workflow_dashboard_readmodel_v1
from .pipeline_builder import build_workflow_pipeline_aggregate_v1
from .types import (
    PIPELINE_READMODEL_ID,
    READMODEL_ID,
    SCHEMA_VERSION,
    WorkflowDashboardReadModelV1,
    to_json_dict,
)
from .universe_selection_contract_v1 import (
    SCHEMA_NAME as UNIVERSE_SELECTION_SCHEMA_NAME,
    STORAGE_RELATIVE_PATH as UNIVERSE_SELECTION_STORAGE_PATH,
    UniverseSelectionContractError,
    UniverseSelectionContractV1,
    load_universe_selection_contract,
    validate_universe_selection_payload,
)

__all__ = [
    "PIPELINE_READMODEL_ID",
    "READMODEL_ID",
    "SCHEMA_VERSION",
    "UNIVERSE_SELECTION_SCHEMA_NAME",
    "UNIVERSE_SELECTION_STORAGE_PATH",
    "UniverseSelectionContractError",
    "UniverseSelectionContractV1",
    "WorkflowDashboardReadModelV1",
    "build_workflow_dashboard_readmodel_v1",
    "build_workflow_pipeline_aggregate_v1",
    "load_universe_selection_contract",
    "to_json_dict",
    "validate_universe_selection_payload",
]
