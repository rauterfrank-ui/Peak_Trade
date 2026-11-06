"""Governed P5 binding context for M4–M8 Optimization / Meta-Learning producer closure.

Pairs authoritative market_context_v1 observation fields with M5/M6 lineage digests.
Does not fabricate instrument, epoch, or timestamps.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_v1 import (
    validate_market_context_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "p5_m4_m8_governed_evidence_binding_context_v1"
BINDING_DOMAIN: Final[str] = "peak_trade.p5.m4_m8_governed_evidence_binding_context.v1"


class P5M4M8BindingContextError(ValueError):
    """Fail-closed binding context build/validation."""


def build_p5_m4_m8_governed_evidence_binding_context_v1(
    *,
    market_context: Mapping[str, Any],
    market_observation_epoch: int,
    source_lineage_schema: str,
    source_lineage_content_digest: str,
    freshness_horizon_seconds: int = 86_400,
) -> MappingProxyType[str, Any]:
    if not source_lineage_schema.strip():
        raise P5M4M8BindingContextError("SOURCE_LINEAGE_SCHEMA_REQUIRED")
    if not is_valid_sha256_hex(source_lineage_content_digest):
        raise P5M4M8BindingContextError("SOURCE_LINEAGE_DIGEST_INVALID")
    if market_observation_epoch < 0:
        raise P5M4M8BindingContextError("MARKET_OBSERVATION_EPOCH_INVALID")
    if freshness_horizon_seconds <= 0:
        raise P5M4M8BindingContextError("FRESHNESS_HORIZON_INVALID")

    validated_ctx = validate_market_context_v1(market_context)
    instrument_ref = str(validated_ctx["instrument_ref"])
    observed_at = str(validated_ctx["observed_at"])
    market_context_digest = str(validated_ctx["content_digest"])
    if not is_valid_sha256_hex(market_context_digest):
        raise P5M4M8BindingContextError("MARKET_CONTEXT_DIGEST_INVALID")

    body = {
        "schema_version": SCHEMA_VERSION,
        "domain": BINDING_DOMAIN,
        "instrument_ref": instrument_ref,
        "observed_at": observed_at,
        "market_observation_epoch": market_observation_epoch,
        "freshness_horizon_seconds": freshness_horizon_seconds,
        "market_context_id": str(validated_ctx["context_id"]),
        "market_context_content_digest": market_context_digest,
        "source_lineage_schema": source_lineage_schema,
        "source_lineage_content_digest": source_lineage_content_digest,
    }
    binding_digest = compute_content_sha256(body)
    record_id = compute_content_sha256(
        {
            "binding_domain": BINDING_DOMAIN,
            "binding_digest": binding_digest,
            "source_lineage_content_digest": source_lineage_content_digest,
        }
    )
    payload = {
        **body,
        "binding_record_id": record_id,
        "binding_digest": binding_digest,
    }
    return validate_p5_m4_m8_governed_evidence_binding_context_v1(payload)


def validate_p5_m4_m8_governed_evidence_binding_context_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    if not isinstance(payload, Mapping):
        raise P5M4M8BindingContextError("BINDING_CONTEXT_MUST_BE_MAPPING")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise P5M4M8BindingContextError("BINDING_CONTEXT_SCHEMA_MISMATCH")
    for field in (
        "instrument_ref",
        "observed_at",
        "market_context_content_digest",
        "source_lineage_schema",
        "source_lineage_content_digest",
        "binding_digest",
        "binding_record_id",
    ):
        if not str(payload.get(field) or "").strip():
            raise P5M4M8BindingContextError(f"BINDING_FIELD_MISSING_{field.upper()}")
    if not is_valid_sha256_hex(str(payload["source_lineage_content_digest"])):
        raise P5M4M8BindingContextError("SOURCE_LINEAGE_DIGEST_INVALID")
    if not is_valid_sha256_hex(str(payload["market_context_content_digest"])):
        raise P5M4M8BindingContextError("MARKET_CONTEXT_DIGEST_INVALID")
    epoch = payload.get("market_observation_epoch")
    if not isinstance(epoch, int) or epoch < 0:
        raise P5M4M8BindingContextError("MARKET_OBSERVATION_EPOCH_INVALID")
    return MappingProxyType(dict(payload))
