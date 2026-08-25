"""Stage E — Non-Inference Guard. Loaded before projection; re-applied later."""

from __future__ import annotations

from scripts.ops.forensic_structure_schema_v1.guards import GuardProgram
from scripts.ops.forensic_structure_schema_v1.state import PipelineState


def run_stage_e(state: PipelineState) -> None:
    state.guards = GuardProgram()
    state.stages_completed.append("E_NON_INFERENCE_GUARD")
