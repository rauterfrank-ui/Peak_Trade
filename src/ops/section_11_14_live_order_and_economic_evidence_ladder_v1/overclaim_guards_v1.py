"""Refuse Live-field overclaim from inadmissible sources or predecessor promotion."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CURRENTLY_REACHABLE_IS_NOT_LIVE_EXECUTION_PATH_REACHABLE,
    FORBIDDEN_LIVE_SOURCE_KINDS,
    G12_DOES_NOT_AUTHORIZE_SECTION_11_14,
    G12_DOES_NOT_SATISFY_SECTION_11_14_OBSERVED_FIELDS,
    LADDER_FIELDS,
    LIVE_RECONCILIATION_PROVEN_IS_NOT_LIVE_POSITION_RECONCILED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)


def refuse_forbidden_live_source_v1(*, field_name: str, source_kind: str) -> None:
    if field_name not in LADDER_FIELDS:
        raise Section1114OfflineSurfaceError(f"UNKNOWN_LADDER_FIELD:{field_name}")
    kind = str(source_kind or "").strip().upper()
    if kind in FORBIDDEN_LIVE_SOURCE_KINDS:
        raise Section1114OfflineSurfaceError(f"FORBIDDEN_LIVE_SOURCE:{kind}:{field_name}")


def refuse_live_field_true_claim_v1(*, field_name: str, source_kind: str) -> None:
    refuse_forbidden_live_source_v1(field_name=field_name, source_kind=source_kind)
    raise Section1114OfflineSurfaceError(
        f"LIVE_FIELD_TRUE_CLAIM_FORBIDDEN_IN_OFFLINE_SURFACE:{field_name}"
    )


def refuse_alias_promotion_v1(*, claimed_alias: str) -> dict[str, Any]:
    aliases = {
        "G12_CLOSURE_AUTHORIZES_SECTION_11_14": G12_DOES_NOT_AUTHORIZE_SECTION_11_14,
        "G12_SATISFIES_SECTION_11_14_OBSERVED_FIELDS": (
            G12_DOES_NOT_SATISFY_SECTION_11_14_OBSERVED_FIELDS
        ),
        "LIVE_RECONCILIATION_PROVEN_EQUALS_LIVE_POSITION_RECONCILED": (
            LIVE_RECONCILIATION_PROVEN_IS_NOT_LIVE_POSITION_RECONCILED
        ),
        "CURRENTLY_REACHABLE_EQUALS_LIVE_EXECUTION_PATH_REACHABLE": (
            CURRENTLY_REACHABLE_IS_NOT_LIVE_EXECUTION_PATH_REACHABLE
        ),
        "FIELD_NAME_SIMILARITY_EQUALS_SEMANTIC_IDENTITY": True,
        "HISTORICAL_EVIDENCE_EQUALS_CURRENT_TRUTH": True,
    }
    if claimed_alias not in aliases:
        raise Section1114OfflineSurfaceError(f"UNKNOWN_ALIAS:{claimed_alias}")
    raise Section1114OfflineSurfaceError(f"ALIAS_PROMOTION_FORBIDDEN:{claimed_alias}")
