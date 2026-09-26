"""Persist MI offline triad into durable store (append-only; idempotent)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_offline_durable_evidence_record_v1 import (
    build_mi_offline_durable_evidence_record_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_offline_durable_evidence_store_v1 import (
    MiOfflineDurableEvidenceStoreV1,
)

PERSIST_ID: Final[str] = (
    "peak_trade.learning.market_intelligence_mi_offline_durable_evidence_persist_v1"
)
PERSIST_STATUS_APPENDED: Final[str] = "APPENDED"
PERSIST_STATUS_IDEMPOTENT: Final[str] = "IDEMPOTENT_REPLAY"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False


@dataclass(frozen=True)
class MiOfflineDurableEvidencePersistRequestV1:
    forecast_evidence: Mapping[str, Any]
    calibration_evidence: Mapping[str, Any]
    research_evidence: Mapping[str, Any]
    provenance: Mapping[str, Any] | None = None


def persist_mi_offline_durable_evidence_v1(
    store_root: Path | str,
    request: MiOfflineDurableEvidencePersistRequestV1,
) -> dict[str, Any]:
    if EXTERNAL_EFFECT_AUTHORIZED:
        raise RuntimeError("MI_OFFLINE_DURABLE_PERSIST_EXTERNAL_EFFECT_FORBIDDEN")
    store = MiOfflineDurableEvidenceStoreV1(store_root)
    prior_ids = {str(r["durable_evidence_id"]) for r in store.list_records()}
    record = build_mi_offline_durable_evidence_record_v1(
        forecast_evidence=request.forecast_evidence,
        calibration_evidence=request.calibration_evidence,
        research_evidence=request.research_evidence,
        provenance={"persist_id": PERSIST_ID, **dict(request.provenance or {})},
    )
    stored = store.append(record)
    status = (
        PERSIST_STATUS_IDEMPOTENT
        if str(stored["durable_evidence_id"]) in prior_ids
        else PERSIST_STATUS_APPENDED
    )
    replay_store = MiOfflineDurableEvidenceStoreV1(store_root)
    first = replay_store.list_records()
    second = replay_store.list_records()
    return {
        "persist_id": PERSIST_ID,
        "persist_status": status,
        "durable_evidence_id": stored["durable_evidence_id"],
        "forecast_evidence_id": stored["forecast_evidence_id"],
        "research_evidence_id": stored["research_evidence_id"],
        "content_digest": stored["content_digest"],
        "store_record_count": len(first),
        "deterministic_replay_equal": first == second,
        "external_effect_authorized": False,
        "productive_authority": "NONE",
    }
