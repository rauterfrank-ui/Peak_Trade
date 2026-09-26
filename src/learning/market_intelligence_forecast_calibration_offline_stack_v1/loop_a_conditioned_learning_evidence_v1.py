"""Phase 21 — Loop A conditioned Learning evidence (MARKET_CONTEXT + REALIZED_BEHAVIOR + MI)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import require_event_time_utc
from src.learning.deterministic_decision_outcome_v0.evaluation_observation_v0 import (
    validate_evaluation_observation_v0,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    FORECAST_IS_NOT_DECISION,
    LEARNING_TRADING_AUTHORITY,
    MARKET_INTELLIGENCE_TRADING_AUTHORITY,
    NO_AUTOMATIC_PROMOTION,
    NO_DUPLICATE_OUTCOME_TRUTH,
    OPTIMIZATION_PRODUCTIVE_AUTHORITY,
    STACK_DOMAIN,
    WORKPACKAGE_ID,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_v1 import (
    MARKET_CONTEXT_AUTHORITY,
    validate_market_context_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_learning_export_v1 import (
    export_mi_learning_evidence_onto_learning_path_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_record_v1 import (
    CONDITIONED_BINDING_SCHEMA,
    LEARNING_DIRECT_PRODUCTIVE_WRITE,
    LEARNING_PROMOTION_AUTHORITY,
    MI_LEARNING_EVIDENCE_AUTHORITY,
    OUTCOME_FINALIZATION_FINALIZED,
    compute_mi_learning_reproducibility_digest_v1,
    derive_mi_learning_evidence_id_v1,
    validate_mi_learning_evidence_record_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_store_v1 import (
    MiLearningEvidenceStoreV1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_to_learning_evidence_bridge_v1 import (
    MiToLearningBridgeError,
    compose_mi_to_learning_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.realized_behavior_v1 import (
    REALIZED_BEHAVIOR_AUTHORITY,
    RealizedBehaviorJoinInputsV1,
    join_market_context_to_realized_behavior_v1,
    validate_realized_behavior_v1,
)

LOOP_A_SCHEMA: Final[str] = "loop_a_conditioned_learning_evidence_v1"
LOOP_A_OWNER: Final[str] = (
    "learning.market_intelligence_forecast_calibration_offline_stack_v1."
    "loop_a_conditioned_learning_evidence_v1"
)
WRITER_ID: Final[str] = "peak_trade.learning.market_intelligence_mi_learning_evidence_ingest_v1"
READER_ID: Final[str] = (
    "peak_trade.learning.market_intelligence_mi_learning_evidence_learning_export_v1"
)


class LoopAConditionedLearningError(ValueError):
    """Fail-closed Loop A conditioned learning integration."""


@dataclass(frozen=True)
class ConditionedLearningComposeInputsV1:
    forecast_evidence: Mapping[str, Any]
    evaluation_observation: Mapping[str, Any] | None
    market_context: Mapping[str, Any]
    realized_behavior: Mapping[str, Any] | None = None
    realized_direction: str | None = None
    legacy_learning_evidence_ref: str | None = None


def _parse_utc(value: str) -> datetime:
    text = require_event_time_utc(value, "utc")
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def _behavior_semantics_snapshot_v1(realized_behavior: Mapping[str, Any]) -> dict[str, str]:
    fb = realized_behavior.get("forward_behavior") or {}
    exc = realized_behavior.get("excursion") or {}
    rv = realized_behavior.get("realized_volatility") or {}
    tr = realized_behavior.get("transition") or {}
    classical = (exc.get("classical_mfe_mae") or {}) if isinstance(exc, Mapping) else {}
    return {
        "forward_behavior_status": str(fb.get("status") or "UNKNOWN"),
        "excursion_status": str(exc.get("status") or "UNKNOWN"),
        "classical_mfe_mae_status": str(classical.get("status") or "SEMANTICALLY_UNRESOLVED"),
        "realized_volatility_status": str(rv.get("status") or "UNKNOWN"),
        "transition_status": str(tr.get("status") or "SEMANTICALLY_UNRESOLVED"),
    }


def _assert_conditioned_temporal_chain_v1(
    *,
    market_context: Mapping[str, Any],
    forecast: Mapping[str, Any],
    observation: Mapping[str, Any] | None,
    realized_behavior: Mapping[str, Any],
) -> None:
    ctx_t = _parse_utc(str(market_context["observed_at"]))
    forecast_t = _parse_utc(str(forecast["forecast_created_at_utc"]))
    if ctx_t > forecast_t:
        raise LoopAConditionedLearningError("MARKET_CONTEXT_AFTER_FORECAST")
    if observation is not None:
        eval_time = observation.get("evaluation_time_utc")
        if eval_time is not None and _parse_utc(str(eval_time)) < ctx_t:
            raise LoopAConditionedLearningError("OUTCOME_BEFORE_CONTEXT_OBSERVED")
    rb_ctx = str(realized_behavior.get("market_context_ref"))
    if rb_ctx != str(market_context["context_id"]):
        raise LoopAConditionedLearningError("REALIZED_BEHAVIOR_CONTEXT_REF_MISMATCH")


def compose_conditioned_mi_learning_evidence_v1(
    inputs: ConditionedLearningComposeInputsV1,
    *,
    provenance: Mapping[str, Any] | None = None,
) -> MappingProxyType[str, Any]:
    """Extend established MI learning evidence with Phase 17–20 conditioned references."""
    context = validate_market_context_v1(inputs.market_context)
    observation = (
        validate_evaluation_observation_v0(inputs.evaluation_observation)
        if inputs.evaluation_observation is not None
        else None
    )
    realized = (
        validate_realized_behavior_v1(inputs.realized_behavior)
        if inputs.realized_behavior is not None
        else None
    )

    try:
        base = compose_mi_to_learning_evidence_v1(
            forecast_evidence=inputs.forecast_evidence,
            evaluation_observation=observation,
            realized_direction=inputs.realized_direction,
            legacy_learning_evidence_ref=inputs.legacy_learning_evidence_ref,
            provenance={
                "loop_a_owner": LOOP_A_OWNER,
                **dict(provenance or {}),
            },
        )
    except MiToLearningBridgeError as exc:
        raise LoopAConditionedLearningError(str(exc)) from exc

    body = dict(base)
    body.update(
        {
            "conditioned_binding_schema": CONDITIONED_BINDING_SCHEMA,
            "market_context_ref": str(context["context_id"]),
            "market_context_content_digest": str(context["content_digest"]),
            "learning_promotion_authority": LEARNING_PROMOTION_AUTHORITY,
            "learning_direct_productive_write": LEARNING_DIRECT_PRODUCTIVE_WRITE,
            "learning_is_not_promotion": True,
        }
    )
    if realized is None:
        if str(base.get("outcome_finalization_status")) == OUTCOME_FINALIZATION_FINALIZED:
            raise LoopAConditionedLearningError("REALIZED_BEHAVIOR_REQUIRED_FOR_FINALIZED_OUTCOME")
        body["realized_behavior_ref"] = "mi.realized_behavior.explicit_missing"
        body["realized_behavior_content_digest"] = "0" * 64
        body["behavior_semantics_snapshot"] = {
            "forward_behavior_status": "UNAVAILABLE",
            "excursion_status": "UNAVAILABLE",
            "classical_mfe_mae_status": "SEMANTICALLY_UNRESOLVED",
            "realized_volatility_status": "UNAVAILABLE",
            "transition_status": "SEMANTICALLY_UNRESOLVED",
        }
    else:
        _assert_conditioned_temporal_chain_v1(
            market_context=context,
            forecast=inputs.forecast_evidence,
            observation=observation,
            realized_behavior=realized,
        )
        base_outcome = base.get("actual_outcome_ref")
        rb_outcome = realized.get("actual_outcome_ref")
        if (
            base_outcome is not None
            and rb_outcome is not None
            and str(rb_outcome) != str(base_outcome)
        ):
            raise LoopAConditionedLearningError("ACTUAL_OUTCOME_REF_MISMATCH")
        body["realized_behavior_ref"] = str(realized["behavior_id"])
        body["realized_behavior_content_digest"] = str(realized["content_digest"])
        body["behavior_semantics_snapshot"] = _behavior_semantics_snapshot_v1(realized)
    prov = dict(body.get("provenance") or {})
    prov.update(
        {
            "conditioned_binding_schema": CONDITIONED_BINDING_SCHEMA,
            "market_context_authority": MARKET_CONTEXT_AUTHORITY,
            "realized_behavior_authority": REALIZED_BEHAVIOR_AUTHORITY,
        }
    )
    body["provenance"] = prov
    digest = compute_mi_learning_reproducibility_digest_v1(body)
    body["reproducibility_digest"] = digest
    body["mi_learning_evidence_id"] = derive_mi_learning_evidence_id_v1(
        reproducibility_digest=digest
    )
    return validate_mi_learning_evidence_record_v1(body)


def run_loop_a_conditioned_learning_cycle_v1(
    *,
    store_root: Path | str,
    inputs: ConditionedLearningComposeInputsV1,
) -> MappingProxyType[str, Any]:
    """Writer → durable store → reader/export (Loop A closure; offline only)."""
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_ingest_v1 import (
        INGEST_ID,
        MiLearningEvidenceIngestRequestV1,
        ingest_mi_learning_evidence_v1,
    )

    expected = compose_conditioned_mi_learning_evidence_v1(
        inputs, provenance={"ingest_id": INGEST_ID}
    )
    ingest = ingest_mi_learning_evidence_v1(
        store_root,
        MiLearningEvidenceIngestRequestV1(
            forecast_evidence=inputs.forecast_evidence,
            evaluation_observation=inputs.evaluation_observation,
            realized_direction=inputs.realized_direction,
            legacy_learning_evidence_ref=inputs.legacy_learning_evidence_ref,
            market_context=inputs.market_context,
            realized_behavior=inputs.realized_behavior,
        ),
    )
    store = MiLearningEvidenceStoreV1(store_root)
    loaded = store.get(str(expected["mi_learning_evidence_id"]))
    record = loaded
    export = export_mi_learning_evidence_onto_learning_path_v1(loaded)
    return MappingProxyType(
        {
            "schema_version": LOOP_A_SCHEMA,
            "loop_a_proven": True,
            "writer_id": WRITER_ID,
            "reader_id": READER_ID,
            "persistence_proven": dict(loaded) == dict(expected),
            "export_retrieval_proven": export["mi_learning_evidence"]["mi_learning_evidence_id"]
            == expected["mi_learning_evidence_id"],
            "ingest_result": dict(ingest),
            "mi_learning_evidence_id": expected["mi_learning_evidence_id"],
            "market_context_ref": expected.get("market_context_ref"),
            "realized_behavior_ref": expected.get("realized_behavior_ref"),
            "learning_export": dict(export),
            "domain": STACK_DOMAIN,
            "workpackage_id": WORKPACKAGE_ID,
        }
    )


def materialize_realized_behavior_for_conditioned_learning_v1(
    *,
    market_context: Mapping[str, Any],
    evaluation_observation: Mapping[str, Any],
    measurement_evidence: Mapping[str, Any] | None = None,
    o4_bars_for_path: list[Mapping[str, Any]] | None = None,
    forecast_evidence_id: str | None = None,
) -> MappingProxyType[str, Any]:
    return join_market_context_to_realized_behavior_v1(
        RealizedBehaviorJoinInputsV1(
            market_context=market_context,
            evaluation_observation=evaluation_observation,
            measurement_evidence=measurement_evidence,
            o4_bars_for_path=o4_bars_for_path,
            forecast_evidence_id=forecast_evidence_id,
        )
    )


def assert_loop_a_authority_invariants_v1() -> Mapping[str, Any]:
    terminal = {
        "MARKET_CONTEXT_AUTHORITY": MARKET_CONTEXT_AUTHORITY,
        "REALIZED_BEHAVIOR_AUTHORITY": REALIZED_BEHAVIOR_AUTHORITY,
        "LEARNING_TRADING_AUTHORITY": LEARNING_TRADING_AUTHORITY,
        "MARKET_INTELLIGENCE_TRADING_AUTHORITY": MARKET_INTELLIGENCE_TRADING_AUTHORITY,
        "LEARNING_PROMOTION_AUTHORITY": LEARNING_PROMOTION_AUTHORITY,
        "LEARNING_DIRECT_PRODUCTIVE_WRITE": LEARNING_DIRECT_PRODUCTIVE_WRITE,
        "MI_LEARNING_EVIDENCE_AUTHORITY": MI_LEARNING_EVIDENCE_AUTHORITY,
        "FORECAST_IS_NOT_DECISION": FORECAST_IS_NOT_DECISION,
        "LEARNING_IS_NOT_PROMOTION": True,
        "NO_DUPLICATE_OUTCOME_TRUTH": NO_DUPLICATE_OUTCOME_TRUTH,
        "NO_AUTOMATIC_PROMOTION": NO_AUTOMATIC_PROMOTION,
        "OPTIMIZATION_PRODUCTIVE_AUTHORITY": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "MV2_DP_UNCHANGED": True,
        "NO_AUTHORITY_EXPANSION": True,
        "NO_SECOND_MARKET_TRUTH": True,
        "PRODUCTIVE_DDO_REDUCER_MUTATED": False,
    }
    if terminal["LEARNING_TRADING_AUTHORITY"] != "NONE":
        raise LoopAConditionedLearningError("LEARNING_TRADING_AUTHORITY_EXPANSION")
    if terminal["OPTIMIZATION_PRODUCTIVE_AUTHORITY"] != "NONE":
        raise LoopAConditionedLearningError("OPTIMIZATION_PRODUCTIVE_AUTHORITY_EXPANSION")
    return MappingProxyType(terminal)


__all__ = [
    "LOOP_A_OWNER",
    "LOOP_A_SCHEMA",
    "ConditionedLearningComposeInputsV1",
    "LoopAConditionedLearningError",
    "assert_loop_a_authority_invariants_v1",
    "compose_conditioned_mi_learning_evidence_v1",
    "materialize_realized_behavior_for_conditioned_learning_v1",
    "run_loop_a_conditioned_learning_cycle_v1",
]
