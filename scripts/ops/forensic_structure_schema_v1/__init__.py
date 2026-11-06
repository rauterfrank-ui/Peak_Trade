"""FORENSIC_STRUCTURE_SCHEMA_V1 read-only transformer.

AUTHORITY_EFFECT=NONE
OUTPUT_ROLE=TEST_ARTIFACT_ONLY
OUTPUT_NOT_CANONICAL=true
Does not mutate source or sidecar. Does not import trading surfaces.
"""

from __future__ import annotations

from scripts.ops.forensic_structure_schema_v1.transformer import (
    transform_read_only,
)

__all__ = ["transform_read_only"]
