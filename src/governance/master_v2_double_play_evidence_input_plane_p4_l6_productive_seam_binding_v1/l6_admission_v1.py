"""L6 owner admission gate for bounded typed external evidence (no D_t interpretation)."""

from __future__ import annotations

from dataclasses import asdict

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    CanonicalDpLayerInputBindingV1,
    CanonicalMasterV2EvidenceEnvelopeV1,
    L6BoundedTypedExternalEvidenceInputV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.validator_v1 import (
    validate_l6_bounded_typed_external_evidence_input_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.digest_v1 import (
    typed_layer_input_digest_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.constants_v1 import (
    L6_ADMIT_DISPOSITION,
    L6_REJECT_DISPOSITION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.digest_v1 import (
    admission_digest_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.models_v1 import (
    L6TypedEvidenceAdmissionResultV1,
    ProductiveL6SeamBindingContextV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.reason_codes_v1 import (
    ProductiveL6SeamFailureCodeV1,
)


def admit_l6_bounded_typed_external_evidence_v1(
    typed_input: L6BoundedTypedExternalEvidenceInputV1 | None,
    *,
    envelope: CanonicalMasterV2EvidenceEnvelopeV1 | None,
    binding: CanonicalDpLayerInputBindingV1 | None,
    context: ProductiveL6SeamBindingContextV1,
    admission_evidence_id: str,
) -> L6TypedEvidenceAdmissionResultV1:
    """Validate typed L6 input against P1 contracts and binding context; L6 semantics unchanged."""
    if typed_input is None or envelope is None or binding is None:
        return L6TypedEvidenceAdmissionResultV1(
            disposition=L6_REJECT_DISPOSITION,
            reason_codes=(ProductiveL6SeamFailureCodeV1.L6_ADMISSION_REJECT.value,),
            admission_evidence_id=admission_evidence_id,
            admission_digest=admission_digest_v1(
                {
                    "disposition": L6_REJECT_DISPOSITION,
                    "admission_evidence_id": admission_evidence_id,
                }
            ),
        )

    failures: list[str] = []
    if typed_input.instrument != context.expected_instrument:
        failures.append(ProductiveL6SeamFailureCodeV1.INSTRUMENT_MISMATCH.value)
    if typed_input.market_observation_epoch != context.expected_market_observation_epoch:
        failures.append(ProductiveL6SeamFailureCodeV1.EPOCH_MISMATCH.value)
    if context.expected_nullline_provenance_epoch is not None:
        if typed_input.nullline_provenance_epoch != context.expected_nullline_provenance_epoch:
            failures.append(ProductiveL6SeamFailureCodeV1.NULLLINE_EPOCH_MISMATCH.value)

    validation = validate_l6_bounded_typed_external_evidence_input_v1(
        typed_input, binding=binding, envelope=envelope
    )
    if not validation.ok:
        failures.extend(list(validation.failure_codes))

    typed_digest = typed_layer_input_digest_v1(asdict(typed_input))
    if failures:
        digest_payload = {
            "admission_evidence_id": admission_evidence_id,
            "disposition": L6_REJECT_DISPOSITION,
            "reason_codes": failures,
            "typed_input_digest": typed_digest,
        }
        return L6TypedEvidenceAdmissionResultV1(
            disposition=L6_REJECT_DISPOSITION,
            reason_codes=tuple(dict.fromkeys(failures)),
            admission_evidence_id=admission_evidence_id,
            admission_digest=admission_digest_v1(digest_payload),
            typed_input_digest=typed_digest,
        )

    digest_payload = {
        "admission_evidence_id": admission_evidence_id,
        "binding_digest": typed_input.binding_digest,
        "disposition": L6_ADMIT_DISPOSITION,
        "envelope_digest": typed_input.envelope_digest,
        "instrument_id": typed_input.instrument.instrument_id,
        "market_observation_epoch": typed_input.market_observation_epoch,
        "target_layer": typed_input.target_layer.value,
        "typed_input_digest": typed_digest,
    }
    return L6TypedEvidenceAdmissionResultV1(
        disposition=L6_ADMIT_DISPOSITION,
        reason_codes=(),
        admission_evidence_id=admission_evidence_id,
        admission_digest=admission_digest_v1(digest_payload),
        typed_input_digest=typed_digest,
    )
