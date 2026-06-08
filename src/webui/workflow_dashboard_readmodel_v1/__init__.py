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

__all__ = [
    "PIPELINE_READMODEL_ID",
    "READMODEL_ID",
    "SCHEMA_VERSION",
    "WorkflowDashboardReadModelV1",
    "build_workflow_dashboard_readmodel_v1",
    "build_workflow_pipeline_aggregate_v1",
    "to_json_dict",
]
