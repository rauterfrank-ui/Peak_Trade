"""Ingest typed MI learning evidence into durable store (append-only; dedup)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_store_v1 import (
    MiLearningEvidenceStoreV1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_to_learning_evidence_bridge_v1 import (
    compose_mi_to_learning_evidence_v1,
)

INGEST_ID: Final[str] = "peak_trade.learning.market_intelligence_mi_learning_evidence_ingest_v1"
INGEST_STATUS_APPENDED: Final[str] = "APPENDED"
INGEST_STATUS_IDEMPOTENT: Final[str] = "IDEMPOTENT_REPLAY"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False


@dataclass(frozen=True)
class MiLearningEvidenceIngestRequestV1:
    forecast_evidence: Mapping[str, Any]
    evaluation_observation: Mapping[str, Any] | None
    realized_direction: str | None = None
    legacy_learning_evidence_ref: str | None = None
    market_context: Mapping[str, Any] | None = None
    realized_behavior: Mapping[str, Any] | None = None


def ingest_mi_learning_evidence_v1(
    store_root: Path | str,
    request: MiLearningEvidenceIngestRequestV1,
) -> dict[str, Any]:
    if EXTERNAL_EFFECT_AUTHORIZED:
        raise RuntimeError("MI_LEARNING_INGEST_EXTERNAL_EFFECT_FORBIDDEN")
    store = MiLearningEvidenceStoreV1(store_root)
    prior_count = len(store.list_records())
    if request.market_context is not None:
        if request.realized_behavior is None and request.evaluation_observation is not None:
            raise ValueError("CONDITIONED_INGEST_REQUIRES_REALIZED_BEHAVIOR_WHEN_OUTCOME_PRESENT")
        from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.loop_a_conditioned_learning_evidence_v1 import (
            ConditionedLearningComposeInputsV1,
            compose_conditioned_mi_learning_evidence_v1,
        )

        record = compose_conditioned_mi_learning_evidence_v1(
            ConditionedLearningComposeInputsV1(
                forecast_evidence=request.forecast_evidence,
                evaluation_observation=request.evaluation_observation,
                market_context=request.market_context,
                realized_behavior=request.realized_behavior,
                realized_direction=request.realized_direction,
                legacy_learning_evidence_ref=request.legacy_learning_evidence_ref,
            ),
            provenance={"ingest_id": INGEST_ID},
        )
    else:
        record = compose_mi_to_learning_evidence_v1(
            forecast_evidence=request.forecast_evidence,
            evaluation_observation=request.evaluation_observation,
            realized_direction=request.realized_direction,
            legacy_learning_evidence_ref=request.legacy_learning_evidence_ref,
            provenance={"ingest_id": INGEST_ID},
        )
    before_ids = {str(r["mi_learning_evidence_id"]) for r in store.list_records()}
    stored = store.append(record)
    after_count = len(store.list_records())
    status = (
        INGEST_STATUS_IDEMPOTENT
        if str(stored["mi_learning_evidence_id"]) in before_ids
        else INGEST_STATUS_APPENDED
    )
    if after_count == prior_count and status == INGEST_STATUS_APPENDED:
        status = INGEST_STATUS_IDEMPOTENT
    replay_store = MiLearningEvidenceStoreV1(store_root)
    first = replay_store.list_records()
    second = replay_store.list_records()
    return {
        "ingest_id": INGEST_ID,
        "ingest_status": status,
        "mi_learning_evidence_id": stored["mi_learning_evidence_id"],
        "forecast_evidence_id": stored["forecast_evidence_id"],
        "store_record_count": len(first),
        "deterministic_replay_equal": first == second,
        "productive_ddo_reducer_mutated": False,
    }
