"""Optional L6 passthrough consumption using caller mechanical proposed_d_t only."""

from __future__ import annotations

from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.constants_v1 import (
    L6_ADMIT_DISPOSITION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.models_v1 import (
    L6TypedEvidenceAdmissionResultV1,
    ProductiveL6SeamBindingContextV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.reason_codes_v1 import (
    ProductiveL6SeamFailureCodeV1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    DynamicScopeGeneratorInputV1,
    DynamicScopeGeneratorOutputV1,
    NullLineStateV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l6_dynamic_scope_generator_v1 import (
    ExplicitPassthroughDynamicScopeGeneratorV1,
    apply_l6_dynamic_scope_generator_v1,
)


def invoke_l6_passthrough_after_admission_v1(
    *,
    admission: L6TypedEvidenceAdmissionResultV1,
    context: ProductiveL6SeamBindingContextV1,
) -> tuple[DynamicScopeGeneratorOutputV1 | None, str | None, tuple[str, ...]]:
    """
    Run existing L6 owner passthrough when mechanical proposed_d_t is supplied out-of-band.
    Typed evidence admission is required; proposed_d_t is never read from evidence payloads.
    """
    if admission.disposition != L6_ADMIT_DISPOSITION:
        return None, None, (ProductiveL6SeamFailureCodeV1.L6_ADMISSION_REJECT.value,)

    if context.mechanical_proposed_d_t is None:
        return None, None, ()

    if context.nullline_for_mechanical_l6 is None:
        return None, None, (ProductiveL6SeamFailureCodeV1.L6_ADMISSION_REJECT.value,)

    nullline: NullLineStateV1 = context.nullline_for_mechanical_l6
    if nullline.instrument_id != context.expected_instrument.instrument_id:
        return None, None, (ProductiveL6SeamFailureCodeV1.INSTRUMENT_MISMATCH.value,)

    generator = ExplicitPassthroughDynamicScopeGeneratorV1()
    inp = DynamicScopeGeneratorInputV1(
        nullline=nullline,
        proposed_d_t=float(context.mechanical_proposed_d_t),
    )
    output = apply_l6_dynamic_scope_generator_v1(generator, inp)
    consumption_id = compute_content_sha256(
        {
            "admission_digest": admission.admission_digest,
            "generator_id": output.generator_id,
            "proposed_d_t": float(context.mechanical_proposed_d_t),
            "typed_input_digest": admission.typed_input_digest,
        }
    )
    return output, consumption_id, ()
