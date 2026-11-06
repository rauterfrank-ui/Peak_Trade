"""Fixture/offline builder für `last_paper_run_panel_readmodel.v0` (display-only)."""

from __future__ import annotations

from .builder import build_last_paper_run_panel_readmodel_v0
from .types import (
    READMODEL_ID,
    SCHEMA_VERSION,
    LastPaperRunPanelReadModelV0,
    to_json_dict,
)

__all__ = [
    "READMODEL_ID",
    "SCHEMA_VERSION",
    "LastPaperRunPanelReadModelV0",
    "build_last_paper_run_panel_readmodel_v0",
    "to_json_dict",
]
