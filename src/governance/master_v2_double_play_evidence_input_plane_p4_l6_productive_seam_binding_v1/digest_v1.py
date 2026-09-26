"""Deterministic digests for P4 productive L6 seam artifacts."""

from __future__ import annotations

import json
from typing import Any, Mapping

from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.models_v1 import (
    ProductiveL6SeamBindingRequestV1,
    ProductiveL6SeamBindingResultV1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256


def seam_request_fingerprint_v1(request: ProductiveL6SeamBindingRequestV1) -> dict[str, Any]:
    intake = request.intake
    return {
        "binding_id": request.binding_id,
        "delivery_id": intake.delivery_id,
        "envelope_id": intake.envelope_id,
        "nullline_provenance_epoch": request.nullline_provenance_epoch,
        "seam_id": request.seam_id,
        "target_contract_version": request.target_contract_version,
        "target_layer": request.target_layer.value,
    }


def compute_seam_request_fingerprint_digest_v1(request: ProductiveL6SeamBindingRequestV1) -> str:
    payload = seam_request_fingerprint_v1(request)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return compute_content_sha256({"canonical_json": canonical})


def compute_seam_result_digest_v1(
    *,
    seam_id: str,
    disposition: str,
    reason_codes: tuple[str, ...],
    adjudication_digest: str | None,
    binding_result_digest: str | None,
    typed_input_digest: str | None,
    l6_admission_digest: str | None,
    l6_consumption_evidence_id: str | None,
    dedup_replay: bool,
) -> str:
    payload = {
        "adjudication_digest": adjudication_digest,
        "binding_result_digest": binding_result_digest,
        "dedup_replay": dedup_replay,
        "disposition": disposition,
        "l6_admission_digest": l6_admission_digest,
        "l6_consumption_evidence_id": l6_consumption_evidence_id,
        "reason_codes": list(reason_codes),
        "seam_id": seam_id,
        "typed_input_digest": typed_input_digest,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return compute_content_sha256({"canonical_json": canonical})


def finalize_seam_result_digest_v1(
    result: ProductiveL6SeamBindingResultV1,
) -> ProductiveL6SeamBindingResultV1:
    if result.seam_result_digest:
        return result
    digest = compute_seam_result_digest_v1(
        seam_id=result.seam_id,
        disposition=result.disposition,
        reason_codes=result.reason_codes,
        adjudication_digest=(
            result.adjudication.adjudication_digest if result.adjudication else None
        ),
        binding_result_digest=(result.binding.binding_result_digest if result.binding else None),
        typed_input_digest=(result.binding.typed_layer_input_digest if result.binding else None),
        l6_admission_digest=(result.l6_admission.admission_digest if result.l6_admission else None),
        l6_consumption_evidence_id=result.l6_consumption_evidence_id,
        dedup_replay=result.dedup_replay,
    )
    return ProductiveL6SeamBindingResultV1(
        seam_id=result.seam_id,
        disposition=result.disposition,
        reason_codes=result.reason_codes,
        seam_result_digest=digest,
        adjudication=result.adjudication,
        binding=result.binding,
        typed_layer_input=result.typed_layer_input,
        l6_admission=result.l6_admission,
        l6_generator_output=result.l6_generator_output,
        l6_consumption_evidence_id=result.l6_consumption_evidence_id,
        dedup_replay=result.dedup_replay,
    )


def admission_digest_v1(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), default=str)
    return compute_content_sha256({"canonical_json": canonical})
