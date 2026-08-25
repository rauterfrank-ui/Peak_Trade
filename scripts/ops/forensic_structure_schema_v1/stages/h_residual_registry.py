"""Stage H — Residual Registry. Testability is not adjudication; residuals stay OPEN."""

from __future__ import annotations

from scripts.ops.forensic_structure_schema_v1.constants import (
    DR_RESIDUAL_IDS,
    DR_RESIDUAL_TITLES,
    SW_RESIDUAL_IDS,
    SW_RESIDUAL_TITLES,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.models import ResidualRecord
from scripts.ops.forensic_structure_schema_v1.state import PipelineState


def run_stage_h(state: PipelineState) -> None:
    residuals: list[ResidualRecord] = []
    for residual_id in SW_RESIDUAL_IDS:
        residuals.append(
            ResidualRecord(
                residual_id=residual_id,
                title=SW_RESIDUAL_TITLES[residual_id],
                status="OPEN",
                auto_closed=False,
                residual_class="SW-R",
            )
        )
    for residual_id in DR_RESIDUAL_IDS:
        residuals.append(
            ResidualRecord(
                residual_id=residual_id,
                title=DR_RESIDUAL_TITLES[residual_id],
                status="OPEN",
                auto_closed=False,
                residual_class="DR",
            )
        )
    if any(r.status != "OPEN" or r.auto_closed for r in residuals):
        raise TransformationContractViolation(
            "STAGE_H",
            "residuals must remain OPEN and not auto-closed",
        )
    expected = len(SW_RESIDUAL_IDS) + len(DR_RESIDUAL_IDS)
    if len(residuals) != expected:
        raise TransformationContractViolation(
            "STAGE_H",
            f"residual omitted: {len(residuals)} != {expected}",
        )
    state.residuals = residuals
    state.stages_completed.append("H_RESIDUAL_REGISTRY")
