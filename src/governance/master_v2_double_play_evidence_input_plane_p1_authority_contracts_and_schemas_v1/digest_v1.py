"""Deterministic content digests for P1 contract payloads."""

from __future__ import annotations

import json
from typing import Any, Mapping

from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def envelope_payload_for_digest_v1(envelope: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "adjudication_path": envelope.get("adjudication_path"),
        "envelope_id": envelope.get("envelope_id"),
        "evidence_kind": envelope.get("evidence_kind"),
        "freshness_horizon_seconds": envelope.get("freshness_horizon_seconds"),
        "instrument": envelope.get("instrument"),
        "market_observation_epoch": envelope.get("market_observation_epoch"),
        "observed_at_unix": envelope.get("observed_at_unix"),
        "producer_family": envelope.get("producer_family"),
        "provenance_refs": envelope.get("provenance_refs"),
        "schema_version": envelope.get("schema_version"),
        "source_evidence_digest": envelope.get("source_evidence_digest"),
        "trading_authority": envelope.get("trading_authority"),
        "typed_payload_digest": envelope.get("typed_payload_digest"),
    }


def binding_payload_for_digest_v1(binding: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "binding_evaluated_at_unix": binding.get("binding_evaluated_at_unix"),
        "binding_id": binding.get("binding_id"),
        "dp_state_mutation_authority": binding.get("dp_state_mutation_authority"),
        "envelope_digest": binding.get("envelope_digest"),
        "instrument": binding.get("instrument"),
        "market_observation_epoch": binding.get("market_observation_epoch"),
        "nullline_provenance_epoch": binding.get("nullline_provenance_epoch"),
        "producer_to_b_direct": binding.get("producer_to_b_direct"),
        "schema_version": binding.get("schema_version"),
        "target_layer": binding.get("target_layer"),
        "trading_authority": binding.get("trading_authority"),
    }


def compute_envelope_digest_v1(envelope: Mapping[str, Any]) -> str:
    return compute_content_sha256(envelope_payload_for_digest_v1(envelope))


def compute_binding_digest_v1(binding: Mapping[str, Any]) -> str:
    return compute_content_sha256(binding_payload_for_digest_v1(binding))


def require_valid_digest_v1(value: str, *, field: str) -> str | None:
    if not value or not str(value).strip():
        return f"{field}_missing"
    if not is_valid_sha256_hex(str(value).strip()):
        return f"{field}_invalid"
    return None
