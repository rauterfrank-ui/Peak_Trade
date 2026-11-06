"""Fixture-only Builder für `paper_shadow_summary_readmodel_v0` (offline, stdlib)."""

from __future__ import annotations

from .builder import build_paper_shadow_summary_readmodel_v0
from .types import (
    SCHEMA_VERSION,
    PaperShadowPathPolicyV0,
    PaperShadowSummaryMetadataInput,
    PaperShadowSummaryReadModelV0,
    to_json_dict,
)

__all__ = [
    "SCHEMA_VERSION",
    "PaperShadowPathPolicyV0",
    "PaperShadowSummaryMetadataInput",
    "PaperShadowSummaryReadModelV0",
    "build_paper_shadow_summary_readmodel_v0",
    "to_json_dict",
]
