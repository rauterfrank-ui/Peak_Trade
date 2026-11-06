"""Campaign/session scope filters for productive ledger evaluation (CURRENT vs forensic)."""

from __future__ import annotations

from typing import Any, Sequence

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveEvidenceAccumulationError,
)


def validate_campaign_session_scope_bindings_v1(
    *,
    campaign_id: str,
    authorized_session_ids: Sequence[str],
) -> tuple[str, ...]:
    camp = str(campaign_id or "").strip()
    if not camp:
        raise ProductiveEvidenceAccumulationError("campaign_session_scope_campaign_id_required")
    cleaned = [str(s).strip() for s in authorized_session_ids]
    if not cleaned or any(not s for s in cleaned):
        raise ProductiveEvidenceAccumulationError("campaign_session_scope_session_ids_required")
    if len(cleaned) != len(set(cleaned)):
        raise ProductiveEvidenceAccumulationError("campaign_session_scope_session_ids_not_unique")
    return tuple(sorted(cleaned))


def filter_productive_records_to_campaign_scope_v1(
    productive: Sequence[Any],
    *,
    campaign_id: str,
    authorized_session_ids: Sequence[str],
) -> list[Any]:
    allowed = set(
        validate_campaign_session_scope_bindings_v1(
            campaign_id=campaign_id,
            authorized_session_ids=authorized_session_ids,
        )
    )
    scoped: list[Any] = []
    for record in productive:
        sid = str(getattr(record, "session_id", "") or "")
        if sid not in allowed:
            continue
        rec_campaign = str(getattr(record, "campaign_id", "") or "")
        if rec_campaign != campaign_id:
            raise ProductiveEvidenceAccumulationError(
                "campaign_session_scope_productive_campaign_mismatch"
            )
        scoped.append(record)
    return scoped
