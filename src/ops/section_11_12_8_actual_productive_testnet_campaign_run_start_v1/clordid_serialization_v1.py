"""OKX clOrdId serialization for §11.12.8 productive campaign path.

Reuses the repository OKX Europe client-order-id contract:
``^[A-Za-z0-9]+$``, max length 32. Does not authorize network, Live, or Cap 11.13.
"""

from __future__ import annotations

import hashlib
import re

from src.ops.okx_europe_adapter_lifecycle_contract_v0 import (
    CLIENT_ORDER_ID_ALLOWED_PATTERN,
    CLIENT_ORDER_ID_MAX_LENGTH,
    build_client_order_id,
)

# Forbidden character classes for OKX clOrdId (fail-closed assertions / tests).
_FORBIDDEN_CLORDID_CHARS_RE = re.compile(r"[^A-Za-z0-9]")


class CampaignClOrdIdSerializationError(RuntimeError):
    """Fail-closed clOrdId serialization violation."""


def serialize_section_11_12_8_campaign_clordid_v1(
    *,
    campaign_id: str,
    cycle_index: int,
) -> str:
    """Deterministic alphanumeric OKX clOrdId unique within a bounded campaign run.

    Historical defect (sealed evidence): ``coid-campaign-0`` contained hyphens and
    was rejected by OKX with ``sCode=51000`` / ``Parameter clOrdId error``.
    """
    if not str(campaign_id).strip():
        raise CampaignClOrdIdSerializationError("CAMPAIGN_ID_REQUIRED_FOR_CLORDID")
    if int(cycle_index) < 0:
        raise CampaignClOrdIdSerializationError("CYCLE_INDEX_MUST_BE_NON_NEGATIVE")

    material = hashlib.sha256(str(campaign_id).encode("utf-8")).hexdigest()
    coid = build_client_order_id(
        run_id=material,
        session_id=material,
        intent_id=material,
        environment="demo",
        instrument_id="BTC-USD_UM_XPERP-310328",
        sequence=int(cycle_index),
    )
    if not coid:
        raise CampaignClOrdIdSerializationError("CLORDID_EMPTY")
    if len(coid) > CLIENT_ORDER_ID_MAX_LENGTH:
        raise CampaignClOrdIdSerializationError(f"CLORDID_LENGTH_VIOLATION:{len(coid)}")
    if not CLIENT_ORDER_ID_ALLOWED_PATTERN.fullmatch(coid):
        raise CampaignClOrdIdSerializationError(f"CLORDID_ALPHANUMERIC_VIOLATION:{coid}")
    if _FORBIDDEN_CLORDID_CHARS_RE.search(coid):
        raise CampaignClOrdIdSerializationError(f"CLORDID_FORBIDDEN_CHAR:{coid}")
    return coid
