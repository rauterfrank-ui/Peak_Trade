"""Deterministic digests for P3 binding artifacts."""

from __future__ import annotations

import json
from typing import Any, Mapping

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.digest_v1 import (
    compute_binding_digest_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.models_v1 import (
    LayerInputBindingRequestV1,
    MasterV2LayerInputBindingResultV1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256


def binding_request_fingerprint_v1(request: LayerInputBindingRequestV1) -> dict[str, Any]:
    return {
        "adjudication_digest": request.adjudication.adjudication_digest,
        "binding_id": request.binding_id,
        "nullline_provenance_epoch": request.nullline_provenance_epoch,
        "target_contract_version": request.target_contract_version,
        "target_layer": request.target_layer.value,
    }


def compute_binding_request_fingerprint_digest_v1(request: LayerInputBindingRequestV1) -> str:
    payload = binding_request_fingerprint_v1(request)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return compute_content_sha256({"canonical_json": canonical})


def binding_result_payload_for_digest_v1(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "adjudication_digest": result.get("adjudication_digest"),
        "binding_digest": result.get("binding_digest"),
        "binding_id": result.get("binding_id"),
        "binding_result_digest": None,
        "dedup_replay": result.get("dedup_replay"),
        "disposition": result.get("disposition"),
        "reason_codes": list(result.get("reason_codes") or ()),
        "typed_layer_input_digest": result.get("typed_layer_input_digest"),
    }


def compute_binding_result_digest_v1(
    *,
    binding_id: str,
    disposition: str,
    reason_codes: tuple[str, ...],
    binding_digest: str | None,
    typed_layer_input_digest: str | None,
    adjudication_digest: str | None,
    dedup_replay: bool,
) -> str:
    payload = {
        "adjudication_digest": adjudication_digest,
        "binding_digest": binding_digest,
        "binding_id": binding_id,
        "dedup_replay": dedup_replay,
        "disposition": disposition,
        "reason_codes": list(reason_codes),
        "typed_layer_input_digest": typed_layer_input_digest,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return compute_content_sha256({"canonical_json": canonical})


def typed_layer_input_digest_v1(typed: Mapping[str, Any]) -> str:
    payload = {
        "binding_digest": typed.get("binding_digest"),
        "envelope_digest": typed.get("envelope_digest"),
        "evidence_kind": typed.get("evidence_kind"),
        "input_id": typed.get("input_id"),
        "instrument": typed.get("instrument"),
        "interpretation_authority": typed.get("interpretation_authority"),
        "market_observation_epoch": typed.get("market_observation_epoch"),
        "nullline_provenance_epoch": typed.get("nullline_provenance_epoch"),
        "provenance_refs": list(typed.get("provenance_refs") or ()),
        "schema_version": typed.get("schema_version"),
        "source_evidence_digest": typed.get("source_evidence_digest"),
        "target_layer": typed.get("target_layer"),
        "typed_payload_digest": typed.get("typed_payload_digest"),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return compute_content_sha256({"canonical_json": canonical})


def finalize_binding_result_digest_v1(
    result: MasterV2LayerInputBindingResultV1,
) -> MasterV2LayerInputBindingResultV1:
    digest = compute_binding_result_digest_v1(
        binding_id=result.binding_id,
        disposition=result.disposition,
        reason_codes=result.reason_codes,
        binding_digest=result.binding_digest,
        typed_layer_input_digest=result.typed_layer_input_digest,
        adjudication_digest=result.adjudication_digest,
        dedup_replay=result.dedup_replay,
    )
    return MasterV2LayerInputBindingResultV1(
        binding_id=result.binding_id,
        disposition=result.disposition,
        reason_codes=result.reason_codes,
        binding_result_digest=digest,
        binding=result.binding,
        binding_digest=result.binding_digest,
        typed_layer_input=result.typed_layer_input,
        typed_layer_input_digest=result.typed_layer_input_digest,
        adjudication_digest=result.adjudication_digest,
        dedup_replay=result.dedup_replay,
    )


def binding_digest_from_model_v1(binding: Mapping[str, Any]) -> str:
    return compute_binding_digest_v1(binding)
