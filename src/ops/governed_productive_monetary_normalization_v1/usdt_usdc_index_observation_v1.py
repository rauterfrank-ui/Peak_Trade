"""Authoritative USDT→USDC observation from OKX index-tickers idxPx."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ENDPOINT_MARKET_INDEX_TICKERS,
    extract_index_px_from_index_tickers_payload_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
)
from src.ops.governed_productive_monetary_normalization_v1.constants_v1 import (
    AUTHORITY_SEMANTIC_MONETARY_NORMALIZATION,
    NORMALIZED_RATE_UNIT_USDC_PER_USDT,
    RAW_RATE_UNIT_USDT_PER_USDC,
    USDT_USDC_ENDPOINT,
    USDT_USDC_SOURCE_FIELD,
    USDT_USDC_SOURCE_IDENTITY,
    USDT_USDC_VENUE,
)
from src.ops.governed_productive_monetary_normalization_v1.contracts_v1 import (
    REASON_AMBIGUOUS_DIRECTION,
    REASON_EPOCH_MISMATCH,
    REASON_MALFORMED_RATE,
    REASON_MISSING_EDGE,
    REASON_MISSING_PROVENANCE,
    REASON_MISSING_SOURCE_TIMESTAMP,
    REASON_NON_POSITIVE_RATE,
    REASON_STALE_RATE,
    REASON_UNAUTHORIZED_SOURCE,
    ConversionEdgeV1,
    MonetaryNormalizationError,
    validate_conversion_edge_v1,
)


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _index_row_ts(payload: Any, *, wanted: str) -> str:
    if not isinstance(payload, Mapping):
        return ""
    data = payload.get("data")
    if not isinstance(data, list):
        return ""
    target = str(wanted or "").strip()
    for row in data:
        if not isinstance(row, Mapping):
            continue
        inst = str(row.get("instId") or "").strip()
        if inst not in {"", target}:
            continue
        return str(row.get("ts") or "").strip()
    return ""


def build_usdt_usdc_conversion_edge_from_index_tickers_v1(
    *,
    index_tickers_payload: Mapping[str, Any] | None,
    decision_epoch: str,
    observed_at: str,
    fresh_pretrade_get_status: str,
    pair_base_currency: str,
    pair_quote_currency: str,
    provenance_ref: str = "",
) -> ConversionEdgeV1:
    if index_tickers_payload is None:
        raise MonetaryNormalizationError(REASON_MISSING_EDGE)
    if ENDPOINT_MARKET_INDEX_TICKERS != USDT_USDC_ENDPOINT:
        raise MonetaryNormalizationError(REASON_UNAUTHORIZED_SOURCE)
    epoch = str(decision_epoch or "").strip()
    if not epoch:
        raise MonetaryNormalizationError(REASON_EPOCH_MISMATCH)
    status = str(fresh_pretrade_get_status or "").strip()
    if status == FreshPretradeGetStatusV1.STALE.value:
        raise MonetaryNormalizationError(REASON_STALE_RATE)
    if status not in {
        FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
        FreshPretradeGetStatusV1.NOT_REQUIRED_OFFLINE.value,
    }:
        raise MonetaryNormalizationError(REASON_STALE_RATE)

    base = str(pair_base_currency or "").strip().upper()
    quote = str(pair_quote_currency or "").strip().upper()
    if base != "USDC" or quote != "USDT":
        raise MonetaryNormalizationError(REASON_AMBIGUOUS_DIRECTION)

    raw_px_text = ""
    if isinstance(index_tickers_payload, Mapping):
        data = index_tickers_payload.get("data")
        if isinstance(data, list):
            target = USDT_USDC_SOURCE_IDENTITY
            for row in data:
                if not isinstance(row, Mapping):
                    continue
                inst = str(row.get("instId") or "").strip()
                if inst not in {"", target}:
                    continue
                raw_px_text = str(row.get("idxPx") or "").strip()
                break
    if not raw_px_text:
        raise MonetaryNormalizationError(REASON_MISSING_EDGE)
    try:
        raw_rate = Decimal(raw_px_text)
    except (InvalidOperation, ValueError) as exc:
        raise MonetaryNormalizationError(REASON_MALFORMED_RATE) from exc
    if not raw_rate.is_finite() or raw_rate <= 0:
        raise MonetaryNormalizationError(REASON_NON_POSITIVE_RATE)
    raw_px = extract_index_px_from_index_tickers_payload_v1(
        index_tickers_payload,
        wanted=USDT_USDC_SOURCE_IDENTITY,
    )
    if raw_px is None:
        raise MonetaryNormalizationError(REASON_NON_POSITIVE_RATE)

    source_ts = _index_row_ts(index_tickers_payload, wanted=USDT_USDC_SOURCE_IDENTITY)
    if not source_ts:
        raise MonetaryNormalizationError(REASON_MISSING_SOURCE_TIMESTAMP)

    normalized_rate = Decimal("1") / raw_rate
    if not normalized_rate.is_finite() or normalized_rate <= 0:
        raise MonetaryNormalizationError(REASON_NON_POSITIVE_RATE)

    digest = _sha256_text(_canonical_json(dict(index_tickers_payload)))
    prov = str(provenance_ref or digest).strip()
    if not prov:
        raise MonetaryNormalizationError(REASON_MISSING_PROVENANCE)

    edge = ConversionEdgeV1(
        source_currency="USDT",
        target_currency="USDC",
        raw_rate=raw_rate,
        raw_rate_unit=RAW_RATE_UNIT_USDT_PER_USDC,
        normalized_rate=normalized_rate,
        normalized_rate_unit=NORMALIZED_RATE_UNIT_USDC_PER_USDT,
        inversion_applied=True,
        venue=USDT_USDC_VENUE,
        endpoint=USDT_USDC_ENDPOINT,
        source_identity=USDT_USDC_SOURCE_IDENTITY,
        source_field=USDT_USDC_SOURCE_FIELD,
        source_timestamp=source_ts,
        observed_at=str(observed_at or epoch),
        decision_epoch=epoch,
        freshness_status=status,
        payload_digest=digest,
        provenance_ref=prov,
        authority_semantic=AUTHORITY_SEMANTIC_MONETARY_NORMALIZATION,
    )
    validate_conversion_edge_v1(edge)
    return edge
