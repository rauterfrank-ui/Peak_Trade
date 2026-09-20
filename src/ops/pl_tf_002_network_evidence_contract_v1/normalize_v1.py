"""Normalize NE-TF-001 venue perm field to typed permission facts. Pure. No network."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.pl_tf_002_network_evidence_contract_v1.constants_v1 import (
    NE_TF_001_RESPONSE_CODE_FIELD,
    NE_TF_001_RESPONSE_PERM_FIELD,
    NE_TF_001_RESPONSE_UID_FIELD,
    OKX_PERM_KNOWN_TOKENS,
    OKX_PERM_TOKEN_READ,
    OKX_PERM_TOKEN_TRADE,
    OKX_PERM_TOKEN_WITHDRAW,
)
from src.ops.pl_tf_002_network_evidence_contract_v1.errors_v1 import PlTf002NetworkEvidenceError


def _extract_data_row(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    code = str(raw.get("code") or "")
    if code != "0":
        raise PlTf002NetworkEvidenceError(
            f"VENUE_CODE_NOT_ZERO:{NE_TF_001_RESPONSE_CODE_FIELD}={code}"
        )
    data = raw.get("data")
    if not isinstance(data, list) or len(data) != 1:
        raise PlTf002NetworkEvidenceError("VENUE_DATA_ROW_COUNT_NOT_ONE")
    row = data[0]
    if not isinstance(row, Mapping):
        raise PlTf002NetworkEvidenceError("VENUE_DATA_ROW_NOT_OBJECT")
    return row


def normalize_okx_account_config_perm_v1(raw_venue_response: Mapping[str, Any]) -> dict[str, Any]:
    """Map RAW_VENUE_RESPONSE → NORMALIZED_PERMISSION_FACTS for NE-TF-001."""
    row = _extract_data_row(raw_venue_response)
    perm_raw = row.get("perm")
    if perm_raw is None or str(perm_raw).strip() == "":
        raise PlTf002NetworkEvidenceError("PERM_FIELD_MISSING")
    uid = str(row.get("uid") or "").strip()
    if uid == "":
        raise PlTf002NetworkEvidenceError("UID_FIELD_MISSING")
    tokens = [part.strip().lower() for part in str(perm_raw).split(",") if part.strip()]
    if not tokens:
        raise PlTf002NetworkEvidenceError("PERM_TOKEN_SET_EMPTY")
    unknown = sorted({t for t in tokens if t not in OKX_PERM_KNOWN_TOKENS})
    if unknown:
        raise PlTf002NetworkEvidenceError(f"UNKNOWN_PERM_TOKEN:{','.join(unknown)}")
    read = OKX_PERM_TOKEN_READ in tokens
    trade = OKX_PERM_TOKEN_TRADE in tokens
    withdraw = OKX_PERM_TOKEN_WITHDRAW in tokens
    return {
        "READ": read,
        "TRADE": trade,
        "WITHDRAW": withdraw,
        "uid": uid,
        "perm_raw": str(perm_raw),
        "perm_tokens": tokens,
        "normalization_contract": "OKX_ACCOUNT_CONFIG_PERM_COMMA_TOKENS_V1",
        "source_field": NE_TF_001_RESPONSE_PERM_FIELD,
        "identity_field": NE_TF_001_RESPONSE_UID_FIELD,
    }
