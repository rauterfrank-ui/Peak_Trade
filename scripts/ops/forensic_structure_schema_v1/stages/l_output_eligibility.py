"""Stage L — Output Eligibility Decision. Eligible != canonical, != retained forensic truth."""

from __future__ import annotations

from scripts.ops.forensic_structure_schema_v1.constants import STAGE_ORDER
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.state import PipelineState


def run_stage_l(state: PipelineState) -> None:
    expected = list(STAGE_ORDER[:-1])
    if state.stages_completed != expected:
        raise TransformationContractViolation(
            "STAGE_L",
            f"stage sequence {state.stages_completed} != {expected}",
        )
    if state.invariant_report is None or not state.invariant_report.passed:
        raise TransformationContractViolation("STAGE_L", "invariant report not passed")
    if state.losslessness_audit is None or not state.losslessness_audit.passed:
        raise TransformationContractViolation("STAGE_L", "losslessness audit not passed")
    if any(r.status != "OPEN" for r in state.residuals):
        raise TransformationContractViolation("STAGE_L", "residual auto-closed")
    if any(t.status != "PASS" for t in state.contract_tests.values()):
        raise TransformationContractViolation("STAGE_L", "contract test not PASS")
    state.output_eligible = True
    state.stages_completed.append("L_OUTPUT_ELIGIBILITY_DECISION")
