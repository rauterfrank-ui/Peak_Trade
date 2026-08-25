"""Orchestrate stages A–L. Fail-closed: a violation aborts validity."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.ops.forensic_structure_schema_v1.constants import (
    DR_RESIDUAL_IDS,
    OUTPUT_AUTHORITY,
    OUTPUT_NOT_CANONICAL,
    OUTPUT_NOT_PERSISTED_AS_FORENSIC_TRUTH,
    OUTPUT_NOT_SOURCE_REPLACEMENT,
    OUTPUT_ROLE,
    STAGE_ORDER,
    SW_RESIDUAL_IDS,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.stages.a_input_verification import (
    load_inputs,
    run_stage_a,
)
from scripts.ops.forensic_structure_schema_v1.stages.b_raw_occurrence_registry import (
    run_stage_b,
)
from scripts.ops.forensic_structure_schema_v1.stages.c_overlay_registry import run_stage_c
from scripts.ops.forensic_structure_schema_v1.stages.d_provenance_registry import (
    run_stage_d,
)
from scripts.ops.forensic_structure_schema_v1.stages.e_non_inference_guard import (
    run_stage_e,
)
from scripts.ops.forensic_structure_schema_v1.stages.f_semantic_envelope import run_stage_f
from scripts.ops.forensic_structure_schema_v1.stages.g_relation_projection import (
    run_stage_g,
)
from scripts.ops.forensic_structure_schema_v1.stages.h_residual_registry import run_stage_h
from scripts.ops.forensic_structure_schema_v1.stages.i_invariant_validation import (
    run_stage_i,
)
from scripts.ops.forensic_structure_schema_v1.stages.j_losslessness_audit import (
    run_stage_j,
)
from scripts.ops.forensic_structure_schema_v1.stages.k_contract_tests import run_stage_k
from scripts.ops.forensic_structure_schema_v1.stages.l_output_eligibility import (
    run_stage_l,
)
from scripts.ops.forensic_structure_schema_v1.state import PipelineState


_STAGE_RUNNERS = (
    run_stage_a,
    run_stage_b,
    run_stage_c,
    run_stage_d,
    run_stage_e,
    run_stage_f,
    run_stage_g,
    run_stage_h,
    run_stage_i,
    run_stage_j,
    run_stage_k,
    run_stage_l,
)


def run_pipeline(source_path: Path, sidecar_path: Path) -> PipelineState:
    state = load_inputs(source_path, sidecar_path)
    for runner in _STAGE_RUNNERS:
        runner(state)
    if state.stages_completed != list(STAGE_ORDER):
        raise TransformationContractViolation(
            "PIPELINE",
            f"completed stages {state.stages_completed} != {list(STAGE_ORDER)}",
        )
    return state


def canonical_test_payload(state: PipelineState) -> dict[str, Any]:
    """Deterministic test artifact. Not forensic truth. No timestamps."""
    assert state.witness is not None
    assert state.invariant_report is not None
    assert state.losslessness_audit is not None
    return {
        "output_role": OUTPUT_ROLE,
        "output_authority": OUTPUT_AUTHORITY,
        "output_not_canonical": OUTPUT_NOT_CANONICAL,
        "output_not_source_replacement": OUTPUT_NOT_SOURCE_REPLACEMENT,
        "output_not_persisted_as_forensic_truth": OUTPUT_NOT_PERSISTED_AS_FORENSIC_TRUTH,
        "output_eligible": state.output_eligible,
        "stages_completed": list(state.stages_completed),
        "input_witness": state.witness.to_canonical(),
        "residuals": [r.to_canonical() for r in state.residuals],
        "open_sw_residuals": list(SW_RESIDUAL_IDS),
        "open_dr_residuals": list(DR_RESIDUAL_IDS),
        "residuals_auto_closed": False,
        "invariant_report": state.invariant_report.to_canonical(),
        "losslessness_audit": state.losslessness_audit.to_canonical(),
        "contract_tests": {k: v.to_canonical() for k, v in sorted(state.contract_tests.items())},
        "relation_envelopes": [r.to_canonical() for r in state.relations],
        "fixture_envelopes": _fixture_envelopes(state),
        "envelope_count": len(state.envelopes),
        "layer1_count": len(state.layer1_ordered),
        "overlay_counts": {
            name: len(items) for name, items in sorted(state.overlays_by_class.items())
        },
        "source_sha256_before": state.source_sha256_before,
        "source_sha256_after": state.source_sha256_after,
        "sidecar_sha256_before": state.sidecar_sha256_before,
        "sidecar_sha256_after": state.sidecar_sha256_after,
        "source_mutated": False,
        "sidecar_mutated": False,
    }


def _fixture_envelopes(state: PipelineState) -> dict[str, Any]:
    from scripts.ops.forensic_structure_schema_v1.constants import FIXTURE_IDS

    wanted = [
        FIXTURE_IDS["TV_001_T4_OVERLAY"],
        FIXTURE_IDS["TV_003_DISTINCT"],
        FIXTURE_IDS["TV_003_DUP_LABELS"],
        FIXTURE_IDS["TV_004_FENCE_A"],
        FIXTURE_IDS["TV_004_FENCE_B"],
        FIXTURE_IDS["TV_006_SHA64"],
        FIXTURE_IDS["TV_006_SHA40"],
        FIXTURE_IDS["TV_007_H1"],
        FIXTURE_IDS["TV_008_CURRENT"],
        FIXTURE_IDS["TV_010_RECORD"],
        FIXTURE_IDS["TV_010_NULL_SHA_RECORD"],
        FIXTURE_IDS["TV_011_MENTION"],
        FIXTURE_IDS["TV_012_TICK5"],
    ]
    out: dict[str, Any] = {}
    for overlay_id in wanted:
        envs = state.envelope_by_overlay_id.get(overlay_id, [])
        out[overlay_id] = [e.to_canonical() for e in envs]
    return out
