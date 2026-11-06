"""Bounded Component B — layer input creation and binding from Component A output only."""

from __future__ import annotations

from dataclasses import asdict

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.constants_v1 import (
    L6_TYPED_INPUT_SCHEMA_VERSION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    BindingContextV1,
    CanonicalDpLayerInputBindingV1,
    P1_ALLOWED_B_TARGET_LAYERS_V1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.validator_v1 import (
    materialize_l6_bounded_typed_external_evidence_input_v1,
    validate_canonical_dp_layer_input_binding_v1,
    validate_l6_bounded_typed_external_evidence_input_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.constants_v1 import (
    ADMIT_DISPOSITION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.constants_v1 import (
    BIND_DISPOSITION,
    NO_BIND_DISPOSITION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.digest_v1 import (
    binding_digest_from_model_v1,
    finalize_binding_result_digest_v1,
    typed_layer_input_digest_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.ledger_v1 import (
    BindingLedgerV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.models_v1 import (
    LayerInputBindingContextV1,
    LayerInputBindingRequestV1,
    MasterV2LayerInputBindingResultV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.reason_codes_v1 import (
    LayerInputBindingIntakeFailureCodeV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.layer_catalog_v1 import LayerIdV1


def _no_bind(
    binding_id: str,
    *,
    reason_codes: tuple[str, ...],
    adjudication_digest: str | None = None,
) -> MasterV2LayerInputBindingResultV1:
    return finalize_binding_result_digest_v1(
        MasterV2LayerInputBindingResultV1(
            binding_id=binding_id,
            disposition=NO_BIND_DISPOSITION,
            reason_codes=reason_codes,
            binding_result_digest="",
            adjudication_digest=adjudication_digest,
            dedup_replay=False,
        )
    )


def bind_layer_input_from_adjudication_v1(
    request: LayerInputBindingRequestV1 | None,
    *,
    context: LayerInputBindingContextV1,
    ledger: BindingLedgerV1 | None = None,
) -> MasterV2LayerInputBindingResultV1:
    if request is None:
        return finalize_binding_result_digest_v1(
            MasterV2LayerInputBindingResultV1(
                binding_id="",
                disposition=NO_BIND_DISPOSITION,
                reason_codes=(LayerInputBindingIntakeFailureCodeV1.REQUEST_MISSING.value,),
                binding_result_digest="",
                dedup_replay=False,
            )
        )

    ledger = ledger or BindingLedgerV1()
    binding_id = request.binding_id

    if binding_id in ledger.binding_results:
        from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.digest_v1 import (  # noqa: PLC0415
            compute_binding_request_fingerprint_digest_v1,
        )

        fingerprint = compute_binding_request_fingerprint_digest_v1(request)
        if ledger.binding_fingerprints.get(binding_id) != fingerprint:
            return _no_bind(
                binding_id,
                reason_codes=(
                    LayerInputBindingIntakeFailureCodeV1.DUPLICATE_BINDING_DIVERGENT.value,
                ),
                adjudication_digest=request.adjudication.adjudication_digest,
            )

    prior = ledger.prior_binding_result(request)
    if prior is not None:
        return MasterV2LayerInputBindingResultV1(
            binding_id=prior.binding_id,
            disposition=prior.disposition,
            reason_codes=prior.reason_codes,
            binding_result_digest=prior.binding_result_digest,
            binding=prior.binding,
            binding_digest=prior.binding_digest,
            typed_layer_input=prior.typed_layer_input,
            typed_layer_input_digest=prior.typed_layer_input_digest,
            adjudication_digest=prior.adjudication_digest,
            dedup_replay=True,
        )

    if context.allow_direct_producer_to_b:
        result = _no_bind(
            binding_id,
            reason_codes=(
                LayerInputBindingIntakeFailureCodeV1.DIRECT_PRODUCER_TO_B_FORBIDDEN.value,
            ),
            adjudication_digest=request.adjudication.adjudication_digest,
        )
        ledger.record_result(request, result)
        return result

    if not binding_id.strip():
        result = _no_bind(
            binding_id,
            reason_codes=(LayerInputBindingIntakeFailureCodeV1.BINDING_ID_MISSING.value,),
            adjudication_digest=request.adjudication.adjudication_digest,
        )
        ledger.record_result(request, result)
        return result

    adjudication = request.adjudication
    if adjudication.disposition != ADMIT_DISPOSITION:
        result = _no_bind(
            binding_id,
            reason_codes=(LayerInputBindingIntakeFailureCodeV1.ADJUDICATION_NOT_ADMIT.value,),
            adjudication_digest=adjudication.adjudication_digest,
        )
        ledger.record_result(request, result)
        return result

    envelope = adjudication.envelope
    if envelope is None:
        result = _no_bind(
            binding_id,
            reason_codes=(LayerInputBindingIntakeFailureCodeV1.ENVELOPE_MISSING.value,),
            adjudication_digest=adjudication.adjudication_digest,
        )
        ledger.record_result(request, result)
        return result

    if not adjudication.envelope_digest:
        result = _no_bind(
            binding_id,
            reason_codes=(LayerInputBindingIntakeFailureCodeV1.ENVELOPE_DIGEST_MISSING.value,),
            adjudication_digest=adjudication.adjudication_digest,
        )
        ledger.record_result(request, result)
        return result

    if request.target_layer not in P1_ALLOWED_B_TARGET_LAYERS_V1:
        result = _no_bind(
            binding_id,
            reason_codes=(LayerInputBindingIntakeFailureCodeV1.TARGET_LAYER_INVALID.value,),
            adjudication_digest=adjudication.adjudication_digest,
        )
        ledger.record_result(request, result)
        return result

    if request.target_contract_version != L6_TYPED_INPUT_SCHEMA_VERSION:
        result = _no_bind(
            binding_id,
            reason_codes=(
                LayerInputBindingIntakeFailureCodeV1.TARGET_CONTRACT_VERSION_UNSUPPORTED.value,
            ),
            adjudication_digest=adjudication.adjudication_digest,
        )
        ledger.record_result(request, result)
        return result

    if request.nullline_provenance_epoch < 0:
        result = _no_bind(
            binding_id,
            reason_codes=(LayerInputBindingIntakeFailureCodeV1.NULLEPOCH_INVALID.value,),
            adjudication_digest=adjudication.adjudication_digest,
        )
        ledger.record_result(request, result)
        return result

    if (
        context.expected_instrument is not None
        and envelope.instrument != context.expected_instrument
    ):
        result = _no_bind(
            binding_id,
            reason_codes=(LayerInputBindingIntakeFailureCodeV1.INSTRUMENT_BINDING_MISMATCH.value,),
            adjudication_digest=adjudication.adjudication_digest,
        )
        ledger.record_result(request, result)
        return result

    if context.expected_market_observation_epoch is not None:
        if envelope.market_observation_epoch != context.expected_market_observation_epoch:
            result = _no_bind(
                binding_id,
                reason_codes=(LayerInputBindingIntakeFailureCodeV1.EPOCH_BINDING_MISMATCH.value,),
                adjudication_digest=adjudication.adjudication_digest,
            )
            ledger.record_result(request, result)
            return result

    binding = CanonicalDpLayerInputBindingV1(
        binding_id=binding_id,
        target_layer=request.target_layer,
        envelope_digest=adjudication.envelope_digest,
        instrument=envelope.instrument,
        market_observation_epoch=envelope.market_observation_epoch,
        nullline_provenance_epoch=request.nullline_provenance_epoch,
        binding_evaluated_at_unix=context.evaluated_at_unix,
    )
    validation = validate_canonical_dp_layer_input_binding_v1(
        binding,
        context=BindingContextV1(
            evaluated_at_unix=context.evaluated_at_unix,
            expected_envelope_digest=adjudication.envelope_digest,
            adjudicated_envelope=envelope,
        ),
    )
    if not validation.ok:
        result = _no_bind(
            binding_id,
            reason_codes=(
                LayerInputBindingIntakeFailureCodeV1.BINDING_CONTRACT_VALIDATION_FAILED.value,
                *validation.failure_codes,
            ),
            adjudication_digest=adjudication.adjudication_digest,
        )
        ledger.record_result(request, result)
        return result

    binding_digest = binding_digest_from_model_v1(asdict(binding))
    typed_input = materialize_l6_bounded_typed_external_evidence_input_v1(
        binding=binding,
        envelope=envelope,
        input_id=f"l6-in:{binding_id}",
    )
    typed_validation = validate_l6_bounded_typed_external_evidence_input_v1(
        typed_input,
        binding=binding,
        envelope=envelope,
    )
    if not typed_validation.ok:
        result = _no_bind(
            binding_id,
            reason_codes=(
                LayerInputBindingIntakeFailureCodeV1.TYPED_INPUT_VALIDATION_FAILED.value,
                *typed_validation.failure_codes,
            ),
            adjudication_digest=adjudication.adjudication_digest,
        )
        ledger.record_result(request, result)
        return result

    typed_digest = typed_layer_input_digest_v1(asdict(typed_input))
    admit = finalize_binding_result_digest_v1(
        MasterV2LayerInputBindingResultV1(
            binding_id=binding_id,
            disposition=BIND_DISPOSITION,
            reason_codes=(),
            binding_result_digest="",
            binding=binding,
            binding_digest=binding_digest,
            typed_layer_input=typed_input,
            typed_layer_input_digest=typed_digest,
            adjudication_digest=adjudication.adjudication_digest,
            dedup_replay=False,
        )
    )
    ledger.record_result(request, admit)
    return admit


def run_component_b_runtime_v1(
    request: LayerInputBindingRequestV1,
    *,
    context: LayerInputBindingContextV1,
    ledger: BindingLedgerV1 | None = None,
) -> MasterV2LayerInputBindingResultV1:
    """Stable entrypoint for bounded Component B runtime (isolated; not productively bound)."""
    return bind_layer_input_from_adjudication_v1(
        request,
        context=context,
        ledger=ledger,
    )
