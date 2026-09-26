"""Pure fail-closed validators for P1 Evidence & Input Plane contracts."""

from __future__ import annotations

import math
from dataclasses import asdict
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.constants_v1 import (
    BINDING_SCHEMA_VERSION,
    ENVELOPE_SCHEMA_VERSION,
    L6_TYPED_INPUT_SCHEMA_VERSION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.digest_v1 import (
    compute_binding_digest_v1,
    compute_envelope_digest_v1,
    require_valid_digest_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    ALLOWED_L6_EVIDENCE_KINDS_V1,
    ALLOWED_PRODUCER_FAMILIES_V1,
    AdjudicationContextV1,
    BindingContextV1,
    CanonicalDpLayerInputBindingV1,
    CanonicalMasterV2EvidenceEnvelopeV1,
    ContractValidationResultV1,
    L6BoundedTypedExternalEvidenceInputV1,
    P1_ALLOWED_B_TARGET_LAYERS_V1,
    envelope_forbidden_numeric_fields_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.reason_codes_v1 import (
    DpLayerBindingFailureCodeV1,
    EvidenceEnvelopeFailureCodeV1,
    L6TypedEvidenceInputFailureCodeV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.layer_catalog_v1 import (
    LayerIdV1,
)


def _fail(*codes: str) -> ContractValidationResultV1:
    return ContractValidationResultV1(ok=False, failure_codes=tuple(dict.fromkeys(codes)))


def _ok() -> ContractValidationResultV1:
    return ContractValidationResultV1(ok=True, failure_codes=())


def validate_canonical_master_v2_evidence_envelope_v1(
    envelope: CanonicalMasterV2EvidenceEnvelopeV1 | None,
    *,
    context: AdjudicationContextV1,
) -> ContractValidationResultV1:
    if envelope is None:
        return _fail(EvidenceEnvelopeFailureCodeV1.ENVELOPE_MISSING.value)
    failures: list[str] = []
    if envelope.schema_version != ENVELOPE_SCHEMA_VERSION:
        failures.append(EvidenceEnvelopeFailureCodeV1.SCHEMA_VERSION_UNSUPPORTED.value)
    if not envelope.envelope_id.strip():
        failures.append(EvidenceEnvelopeFailureCodeV1.ENVELOPE_ID_MISSING.value)
    if envelope.producer_family not in ALLOWED_PRODUCER_FAMILIES_V1:
        failures.append(EvidenceEnvelopeFailureCodeV1.PRODUCER_FAMILY_INVALID.value)
    if envelope.evidence_kind not in ALLOWED_L6_EVIDENCE_KINDS_V1:
        failures.append(EvidenceEnvelopeFailureCodeV1.EVIDENCE_KIND_INVALID.value)
    if envelope.trading_authority != "NONE":
        failures.append(EvidenceEnvelopeFailureCodeV1.TRADING_AUTHORITY_NOT_NONE.value)
    inst = envelope.instrument
    if not inst.instrument_id.strip():
        failures.append(EvidenceEnvelopeFailureCodeV1.INSTRUMENT_ID_MISSING.value)
    if not inst.venue.strip():
        failures.append(EvidenceEnvelopeFailureCodeV1.VENUE_MISSING.value)
    if not inst.venue_instrument_id.strip():
        failures.append(EvidenceEnvelopeFailureCodeV1.VENUE_INSTRUMENT_ID_MISSING.value)
    if envelope.market_observation_epoch < 0:
        failures.append(EvidenceEnvelopeFailureCodeV1.EPOCH_INVALID.value)
    if not math.isfinite(envelope.observed_at_unix):
        failures.append(EvidenceEnvelopeFailureCodeV1.OBSERVED_AT_INVALID.value)
    if envelope.freshness_horizon_seconds <= 0:
        failures.append(EvidenceEnvelopeFailureCodeV1.FRESHNESS_HORIZON_INVALID.value)
    else:
        age = float(context.evaluated_at_unix) - float(envelope.observed_at_unix)
        if age < 0 or age > float(envelope.freshness_horizon_seconds):
            failures.append(EvidenceEnvelopeFailureCodeV1.FRESHNESS_STALE.value)
    if not envelope.provenance_refs:
        failures.append(EvidenceEnvelopeFailureCodeV1.PROVENANCE_EMPTY.value)
    for field, code in (
        (
            envelope.source_evidence_digest,
            EvidenceEnvelopeFailureCodeV1.SOURCE_EVIDENCE_DIGEST_MISSING,
        ),
        (envelope.typed_payload_digest, EvidenceEnvelopeFailureCodeV1.TYPED_PAYLOAD_DIGEST_MISSING),
    ):
        err = require_valid_digest_v1(field, field="digest")
        if err == "digest_missing":
            failures.append(code.value)
        elif err == "digest_invalid":
            failures.append(
                EvidenceEnvelopeFailureCodeV1.SOURCE_EVIDENCE_DIGEST_INVALID.value
                if field == envelope.source_evidence_digest
                else EvidenceEnvelopeFailureCodeV1.TYPED_PAYLOAD_DIGEST_INVALID.value
            )
    forbidden = envelope_forbidden_numeric_fields_v1(envelope.extra_fields)
    if forbidden:
        failures.append(DpLayerBindingFailureCodeV1.PROPOSED_D_T_FIELD_FORBIDDEN.value)
    if context.allow_direct_producer_to_b:
        failures.append(EvidenceEnvelopeFailureCodeV1.DIRECT_PRODUCER_TO_B_FORBIDDEN.value)
    if failures:
        return _fail(*failures)
    return _ok()


def validate_canonical_dp_layer_input_binding_v1(
    binding: CanonicalDpLayerInputBindingV1 | None,
    *,
    context: BindingContextV1,
) -> ContractValidationResultV1:
    if binding is None:
        return _fail(DpLayerBindingFailureCodeV1.BINDING_MISSING.value)
    failures: list[str] = []
    if binding.schema_version != BINDING_SCHEMA_VERSION:
        failures.append(DpLayerBindingFailureCodeV1.SCHEMA_VERSION_UNSUPPORTED.value)
    if not binding.binding_id.strip():
        failures.append(DpLayerBindingFailureCodeV1.BINDING_ID_MISSING.value)
    if binding.target_layer not in P1_ALLOWED_B_TARGET_LAYERS_V1:
        failures.append(DpLayerBindingFailureCodeV1.TARGET_LAYER_INVALID.value)
    if binding.trading_authority != "NONE":
        failures.append(DpLayerBindingFailureCodeV1.TRADING_AUTHORITY_NOT_NONE.value)
    if binding.dp_state_mutation_authority != "NONE":
        failures.append(DpLayerBindingFailureCodeV1.DP_STATE_MUTATION_FORBIDDEN.value)
    if binding.producer_to_b_direct:
        failures.append(DpLayerBindingFailureCodeV1.DIRECT_PRODUCER_TO_B_FORBIDDEN.value)
    env_result = validate_canonical_master_v2_evidence_envelope_v1(
        context.adjudicated_envelope,
        context=AdjudicationContextV1(
            evaluated_at_unix=context.evaluated_at_unix,
            allow_direct_producer_to_b=False,
        ),
    )
    if not env_result.ok:
        failures.append(DpLayerBindingFailureCodeV1.ENVELOPE_NOT_ADJUDICATED.value)
        failures.extend(env_result.failure_codes)
    env_digest = compute_envelope_digest_v1(asdict(context.adjudicated_envelope))
    if not binding.envelope_digest.strip():
        failures.append(DpLayerBindingFailureCodeV1.ENVELOPE_DIGEST_MISSING.value)
    elif binding.envelope_digest != context.expected_envelope_digest:
        failures.append(DpLayerBindingFailureCodeV1.ENVELOPE_DIGEST_MISMATCH.value)
    elif binding.envelope_digest != env_digest:
        failures.append(DpLayerBindingFailureCodeV1.ENVELOPE_DIGEST_MISMATCH.value)
    env = context.adjudicated_envelope
    if binding.instrument != env.instrument:
        failures.append(DpLayerBindingFailureCodeV1.INSTRUMENT_BINDING_MISMATCH.value)
    if binding.market_observation_epoch != env.market_observation_epoch:
        failures.append(DpLayerBindingFailureCodeV1.EPOCH_BINDING_MISMATCH.value)
    forbidden = envelope_forbidden_numeric_fields_v1(binding.extra_fields)
    if "proposed_d_t" in forbidden:
        failures.append(DpLayerBindingFailureCodeV1.COLLAPSE_TO_PROPOSED_D_T_FORBIDDEN.value)
    if "d_t" in forbidden or "final_d_t" in forbidden:
        failures.append(DpLayerBindingFailureCodeV1.D_T_FIELD_FORBIDDEN.value)
    if failures:
        return _fail(*failures)
    return _ok()


def validate_l6_bounded_typed_external_evidence_input_v1(
    typed_input: L6BoundedTypedExternalEvidenceInputV1 | None,
    *,
    binding: CanonicalDpLayerInputBindingV1,
    envelope: CanonicalMasterV2EvidenceEnvelopeV1,
) -> ContractValidationResultV1:
    if typed_input is None:
        return _fail(L6TypedEvidenceInputFailureCodeV1.INPUT_MISSING.value)
    failures: list[str] = []
    if typed_input.schema_version != L6_TYPED_INPUT_SCHEMA_VERSION:
        failures.append(L6TypedEvidenceInputFailureCodeV1.SCHEMA_VERSION_UNSUPPORTED.value)
    if typed_input.target_layer != LayerIdV1.L6_DYNAMIC_SCOPE_GENERATOR:
        failures.append(L6TypedEvidenceInputFailureCodeV1.LAYER_TARGET_INVALID.value)
    if typed_input.interpretation_authority != "L6_ONLY":
        failures.append(L6TypedEvidenceInputFailureCodeV1.INTERPRETATION_AUTHORITY_NOT_L6.value)
    expected_binding_digest = compute_binding_digest_v1(asdict(binding))
    if typed_input.binding_digest != expected_binding_digest:
        failures.append(L6TypedEvidenceInputFailureCodeV1.BINDING_DIGEST_MISMATCH.value)
    env_digest = compute_envelope_digest_v1(asdict(envelope))
    if typed_input.envelope_digest != env_digest:
        failures.append(L6TypedEvidenceInputFailureCodeV1.BINDING_DIGEST_MISMATCH.value)
    if failures:
        return _fail(*failures)
    return _ok()


def materialize_l6_bounded_typed_external_evidence_input_v1(
    *,
    binding: CanonicalDpLayerInputBindingV1,
    envelope: CanonicalMasterV2EvidenceEnvelopeV1,
    input_id: str,
) -> L6BoundedTypedExternalEvidenceInputV1:
    """Contract-only materialization from validated A+B artifacts (no D_t fields)."""
    return L6BoundedTypedExternalEvidenceInputV1(
        input_id=input_id,
        target_layer=LayerIdV1.L6_DYNAMIC_SCOPE_GENERATOR,
        evidence_kind=envelope.evidence_kind,
        instrument=envelope.instrument,
        market_observation_epoch=envelope.market_observation_epoch,
        nullline_provenance_epoch=binding.nullline_provenance_epoch,
        envelope_digest=compute_envelope_digest_v1(asdict(envelope)),
        binding_digest=compute_binding_digest_v1(asdict(binding)),
        source_evidence_digest=envelope.source_evidence_digest,
        typed_payload_digest=envelope.typed_payload_digest,
        provenance_refs=envelope.provenance_refs,
    )
