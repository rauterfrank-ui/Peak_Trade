"""Productive A → B → L6 typed seam orchestration (bounded; fail-closed)."""

from __future__ import annotations

from pathlib import Path

from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.adjudicator_v1 import (
    adjudicate_evidence_intake_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.constants_v1 import (
    ADMIT_DISPOSITION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.ledger_v1 import (
    AdjudicationLedgerV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.models_v1 import (
    EvidenceIntakeAdjudicationContextV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.registry_v1 import (
    load_producer_registry_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.binder_v1 import (
    bind_layer_input_from_adjudication_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.constants_v1 import (
    BIND_DISPOSITION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.ledger_v1 import (
    BindingLedgerV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.models_v1 import (
    LayerInputBindingContextV1,
    LayerInputBindingRequestV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.constants_v1 import (
    L6_ADMIT_DISPOSITION,
    PRODUCTIVE_L6_BINDING_AUTHORIZED,
    SEAM_BIND_DISPOSITION,
    SEAM_NO_BIND_DISPOSITION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.digest_v1 import (
    compute_seam_request_fingerprint_digest_v1,
    finalize_seam_result_digest_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.l6_admission_v1 import (
    admit_l6_bounded_typed_external_evidence_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.l6_mechanical_consumption_v1 import (
    invoke_l6_passthrough_after_admission_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.ledger_v1 import (
    ProductiveL6SeamLedgerV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.models_v1 import (
    ProductiveL6SeamBindingContextV1,
    ProductiveL6SeamBindingRequestV1,
    ProductiveL6SeamBindingResultV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.reason_codes_v1 import (
    ProductiveL6SeamFailureCodeV1,
)


def _no_seam(
    seam_id: str,
    *,
    reason_codes: tuple[str, ...],
) -> ProductiveL6SeamBindingResultV1:
    return finalize_seam_result_digest_v1(
        ProductiveL6SeamBindingResultV1(
            seam_id=seam_id,
            disposition=SEAM_NO_BIND_DISPOSITION,
            reason_codes=reason_codes,
            seam_result_digest="",
        )
    )


def run_productive_l6_seam_binding_v1(
    request: ProductiveL6SeamBindingRequestV1 | None,
    *,
    context: ProductiveL6SeamBindingContextV1,
    repo_root: Path | None = None,
    adjudication_ledger: AdjudicationLedgerV1 | None = None,
    binding_ledger: BindingLedgerV1 | None = None,
    seam_ledger: ProductiveL6SeamLedgerV1 | None = None,
) -> ProductiveL6SeamBindingResultV1:
    if not PRODUCTIVE_L6_BINDING_AUTHORIZED:
        return _no_seam(
            request.seam_id if request else "",
            reason_codes=(ProductiveL6SeamFailureCodeV1.GATE_NOT_AUTHORIZED.value,),
        )

    if request is None:
        return _no_seam("", reason_codes=(ProductiveL6SeamFailureCodeV1.REQUEST_MISSING.value,))

    seam_ledger = seam_ledger or ProductiveL6SeamLedgerV1()
    seam_id = request.seam_id

    if seam_id in seam_ledger.seam_results:
        fingerprint = compute_seam_request_fingerprint_digest_v1(request)
        if seam_ledger.seam_fingerprints.get(seam_id) != fingerprint:
            return _no_seam(
                seam_id,
                reason_codes=(ProductiveL6SeamFailureCodeV1.DUPLICATE_SEAM_DIVERGENT.value,),
            )
        prior = seam_ledger.seam_results[seam_id]
        return ProductiveL6SeamBindingResultV1(
            seam_id=prior.seam_id,
            disposition=prior.disposition,
            reason_codes=prior.reason_codes,
            seam_result_digest=prior.seam_result_digest,
            adjudication=prior.adjudication,
            binding=prior.binding,
            typed_layer_input=prior.typed_layer_input,
            l6_admission=prior.l6_admission,
            l6_generator_output=prior.l6_generator_output,
            l6_consumption_evidence_id=prior.l6_consumption_evidence_id,
            dedup_replay=True,
        )

    root = repo_root or Path(__file__).resolve().parents[3]
    registry = load_producer_registry_v1(root)
    adjudication_ctx = EvidenceIntakeAdjudicationContextV1(
        evaluated_at_unix=context.evaluated_at_unix,
        expected_instrument=context.expected_instrument,
        expected_market_observation_epoch=context.expected_market_observation_epoch,
    )
    adjudication = adjudicate_evidence_intake_v1(
        request.intake,
        context=adjudication_ctx,
        registry=registry,
        ledger=adjudication_ledger or AdjudicationLedgerV1(),
    )
    if adjudication.disposition != ADMIT_DISPOSITION:
        result = _no_seam(
            seam_id,
            reason_codes=(ProductiveL6SeamFailureCodeV1.ADJUDICATION_NOT_ADMIT.value,),
        )
        result = ProductiveL6SeamBindingResultV1(
            seam_id=result.seam_id,
            disposition=result.disposition,
            reason_codes=result.reason_codes,
            seam_result_digest=result.seam_result_digest,
            adjudication=adjudication,
        )
        return finalize_seam_result_digest_v1(result)

    binding_ctx = LayerInputBindingContextV1(
        evaluated_at_unix=context.evaluated_at_unix,
        expected_instrument=context.expected_instrument,
        expected_market_observation_epoch=context.expected_market_observation_epoch,
        allow_direct_producer_to_b=False,
    )
    binding_request = LayerInputBindingRequestV1(
        binding_id=request.binding_id,
        target_layer=request.target_layer,
        target_contract_version=request.target_contract_version,
        nullline_provenance_epoch=request.nullline_provenance_epoch,
        adjudication=adjudication,
    )
    binding = bind_layer_input_from_adjudication_v1(
        binding_request,
        context=binding_ctx,
        ledger=binding_ledger or BindingLedgerV1(),
    )
    if binding.disposition != BIND_DISPOSITION or binding.typed_layer_input is None:
        result = ProductiveL6SeamBindingResultV1(
            seam_id=seam_id,
            disposition=SEAM_NO_BIND_DISPOSITION,
            reason_codes=(ProductiveL6SeamFailureCodeV1.BINDING_NOT_BIND.value,),
            seam_result_digest="",
            adjudication=adjudication,
            binding=binding,
        )
        return finalize_seam_result_digest_v1(result)

    admission = admit_l6_bounded_typed_external_evidence_v1(
        binding.typed_layer_input,
        envelope=adjudication.envelope,
        binding=binding.binding,
        context=context,
        admission_evidence_id=f"l6-admission:{seam_id}",
    )

    l6_output = None
    consumption_id = None
    extra_reasons: list[str] = []
    if admission.disposition == L6_ADMIT_DISPOSITION:
        l6_output, consumption_id, consume_failures = invoke_l6_passthrough_after_admission_v1(
            admission=admission,
            context=context,
        )
        extra_reasons.extend(consume_failures)

    disposition = (
        SEAM_BIND_DISPOSITION
        if admission.disposition == L6_ADMIT_DISPOSITION
        else SEAM_NO_BIND_DISPOSITION
    )
    reason_codes = tuple(extra_reasons) if extra_reasons else ()
    if admission.disposition != L6_ADMIT_DISPOSITION:
        reason_codes = (ProductiveL6SeamFailureCodeV1.L6_ADMISSION_REJECT.value,)

    result = finalize_seam_result_digest_v1(
        ProductiveL6SeamBindingResultV1(
            seam_id=seam_id,
            disposition=disposition,
            reason_codes=reason_codes,
            seam_result_digest="",
            adjudication=adjudication,
            binding=binding,
            typed_layer_input=binding.typed_layer_input,
            l6_admission=admission,
            l6_generator_output=l6_output,
            l6_consumption_evidence_id=consumption_id,
        )
    )
    seam_ledger.seam_results[seam_id] = result
    seam_ledger.seam_fingerprints[seam_id] = compute_seam_request_fingerprint_digest_v1(request)
    return result
