"""Deterministic transformation-local IDs. Content-hash survivor IDs are forbidden."""

from __future__ import annotations

from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)


def mint_transformation_local_id(
    *,
    kind: str,
    source_order: int,
    sidecar_stable_suffix: str,
    layer2_record_index: int | None = None,
) -> str:
    if not kind or "/" in kind or " " in kind:
        raise TransformationContractViolation("DR-007", f"invalid tlid kind {kind!r}")
    if source_order < 0:
        raise TransformationContractViolation("DR-007", "source_order must be >= 0")
    if not sidecar_stable_suffix:
        raise TransformationContractViolation("DR-007", "sidecar_stable_suffix is required")
    padded = f"{source_order:06d}"
    tlid = f"tlid-{kind}-{padded}-{sidecar_stable_suffix}"
    if layer2_record_index is not None:
        tlid = f"{tlid}-r{layer2_record_index}"
    return tlid
