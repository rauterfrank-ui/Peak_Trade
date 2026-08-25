"""Locate bound forensic inputs. Does not import or copy them into the repo."""

from __future__ import annotations

from pathlib import Path

from scripts.ops.forensic_structure_schema_v1.constants import (
    BOUND_SIDECAR_PATH,
    BOUND_SOURCE_PATH,
)
from scripts.ops.forensic_structure_schema_v1.transformer import (
    TransformResult,
    transform_read_only,
)

BOUND_SOURCE = Path(BOUND_SOURCE_PATH)
BOUND_SIDECAR = Path(BOUND_SIDECAR_PATH)

_CACHED: TransformResult | None = None


def bound_inputs_available() -> bool:
    return BOUND_SOURCE.is_file() and BOUND_SIDECAR.is_file()


def run_bound_transformer() -> TransformResult:
    """Read-only cached run against the Documents locator. Caller must skip if absent."""
    global _CACHED
    if _CACHED is None:
        _CACHED = transform_read_only(
            source_path=BOUND_SOURCE,
            sidecar_path=BOUND_SIDECAR,
        )
    return _CACHED
