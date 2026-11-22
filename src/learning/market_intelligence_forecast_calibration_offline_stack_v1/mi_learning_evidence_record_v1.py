"""Typed Market Intelligence learning evidence v1 (forecast/outcome/calibration; AUTHORITY=NONE)."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    require_event_time_utc,
    require_mapping,
    require_non_empty_string_or_unknown,
    require_record_id,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_contracts_v1 import (
    require_opaque_ref,
    require_positive_int,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
    compute_content_hash_v0,
    is_valid_sha256_hex_v0,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    STACK_DOMAIN,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.calibration_evidence_v1 import (
    METHOD_BRIER_SCORE,
    METHOD_RETURN_ERROR,
    METHOD_THRESHOLD_HIT,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.support_disposition_v1 import (
    EVALUABILITY_NOT_EVALUABLE,
    EVALUABILITY_SUFFICIENT,
    require_support_disposition,
)
from src.ops.peak_trade_public_market_data_runtime_v1.canonical_fact_decoder_v1 import (
    capture_order_key_v1,
)

SCHEMA_VERSION: Final[str] = "mi_learning_evidence_record_v1"
EVIDENCE_CLASS_MI_LEARNING: Final[str] = "MARKET_INTELLIGENCE_LEARNING_EVIDENCE"
MI_LEARNING_EVIDENCE_AUTHORITY: Final[str] = "NONE"
LEARNING_PROMOTION_AUTHORITY: Final[str] = "NONE"
LEARNING_DIRECT_PRODUCTIVE_WRITE: Final[str] = "FORBIDDEN"
CONDITIONED_BINDING_SCHEMA: Final[str] = "conditioned_learning_evidence_v1"
OUTCOME_FINALIZATION_FINALIZED: Final[str] = "FINALIZED"
OUTCOME_FINALIZATION_INCOMPLETE: Final[str] = "INCOMPLETE"

_REQUIRED: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "domain",
        "mi_learning_evidence_id",
        "forecast_evidence_id",
        "calibration_evidence_id",
        "forecast_outcome_join_digest",
        "information_set_ref",
        "forecast_created_at_utc",
        "outcome_horizon_end_utc",
        "n_bars",
        "bar_spec_ref",
        "evaluation_observation_ref",
        "actual_outcome_ref",
        "horizon_observation_status",
        "outcome_finalization_status",
        "evaluability",
        "calibration_method",
        "calibration_evidence_digest",
        "temporal_integrity_digest",
        "provenance",
        "reproducibility_digest",
        "evidence_class",
        "mi_learning_evidence_authority",
        "productive_ddo_reducer_mutated",
        "forecast_is_not_decision",
    }
)


class MiLearningEvidenceValidationError(ValueError):
    """Fail-closed MI learning evidence validation."""


def derive_mi_learning_evidence_id_v1(*, reproducibility_digest: str) -> str:
    return f"mi.learn.{reproducibility_digest[:48]}"


def _assert_learning_state_semantics_v1(raw: Mapping[str, Any]) -> None:
    """Reapply the existing producer's state contract, without rebuilding its evidence."""
    try:
        require_record_id(raw["information_set_ref"], "information_set_ref")
        require_positive_int(raw["n_bars"], "n_bars")
        evaluability = require_support_disposition(raw["evaluability"], "evaluability")
        if raw["evaluability"] != evaluability:
            raise MiLearningEvidenceValidationError("MI_LEARNING_EVALUABILITY_INVALID")
        finalized = raw["outcome_finalization_status"] == OUTCOME_FINALIZATION_FINALIZED
        if finalized:
            if raw["horizon_observation_status"] != "OK":
                raise MiLearningEvidenceValidationError("MI_LEARNING_FINALIZED_STATUS_INVALID")
            for field in ("evaluation_observation_ref", "actual_outcome_ref"):
                require_opaque_ref(raw[field], field)
        else:
            if (
                raw["outcome_finalization_status"] != OUTCOME_FINALIZATION_INCOMPLETE
                or raw["horizon_observation_status"] != "OUTCOME_MISSING"
                or raw["evaluation_observation_ref"] is not None
                or raw["actual_outcome_ref"] is not None
                or evaluability != EVALUABILITY_NOT_EVALUABLE
            ):
                raise MiLearningEvidenceValidationError("MI_LEARNING_INCOMPLETE_STATE_INVALID")
        # A finalized measurement is distinct from sufficient calibration support.
        methods = (
            (METHOD_BRIER_SCORE, METHOD_RETURN_ERROR, METHOD_THRESHOLD_HIT)
            if evaluability == EVALUABILITY_SUFFICIENT
            else ("NONE",)
        )
        if raw["calibration_method"] not in methods:
            raise MiLearningEvidenceValidationError("MI_LEARNING_CALIBRATION_STATE_INVALID")
    except DdoValidationError as exc:
        raise MiLearningEvidenceValidationError(str(exc)) from exc

    created = capture_order_key_v1(raw["forecast_created_at_utc"])
    horizon_end = capture_order_key_v1(raw["outcome_horizon_end_utc"])
    if created >= horizon_end:
        raise MiLearningEvidenceValidationError("MI_LEARNING_FORECAST_HORIZON_ORDER_INVALID")


def build_mi_learning_evidence_record_v1(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "mi_learning_evidence")
    missing = _REQUIRED - frozenset(raw.keys())
    if missing:
        raise MiLearningEvidenceValidationError("MI_LEARNING_EVIDENCE_FIELDS_MISSING")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise MiLearningEvidenceValidationError("MI_LEARNING_EVIDENCE_SCHEMA_MISMATCH")
    if raw.get("domain") != STACK_DOMAIN:
        raise MiLearningEvidenceValidationError("MI_LEARNING_EVIDENCE_DOMAIN_MISMATCH")
    if raw.get("evidence_class") != EVIDENCE_CLASS_MI_LEARNING:
        raise MiLearningEvidenceValidationError("MI_LEARNING_EVIDENCE_CLASS_INVALID")
    if raw.get("mi_learning_evidence_authority") != MI_LEARNING_EVIDENCE_AUTHORITY:
        raise MiLearningEvidenceValidationError("MI_LEARNING_EVIDENCE_AUTHORITY_MUST_BE_NONE")
    if raw.get("productive_ddo_reducer_mutated") is not False:
        raise MiLearningEvidenceValidationError("PRODUCTIVE_DDO_REDUCER_MUTATED_FORBIDDEN")
    if raw.get("forecast_is_not_decision") is not True:
        raise MiLearningEvidenceValidationError("FORECAST_IS_NOT_DECISION_REQUIRED")

    if raw.get("learning_promotion_authority") not in (None, LEARNING_PROMOTION_AUTHORITY):
        raise MiLearningEvidenceValidationError("LEARNING_PROMOTION_AUTHORITY_MUST_BE_NONE")
    if raw.get("learning_direct_productive_write") not in (
        None,
        LEARNING_DIRECT_PRODUCTIVE_WRITE,
    ):
        raise MiLearningEvidenceValidationError("LEARNING_DIRECT_PRODUCTIVE_WRITE_FORBIDDEN")

    binding_schema = raw.get("conditioned_binding_schema")
    if binding_schema is not None and binding_schema != CONDITIONED_BINDING_SCHEMA:
        raise MiLearningEvidenceValidationError("CONDITIONED_BINDING_SCHEMA_MISMATCH")
    if binding_schema == CONDITIONED_BINDING_SCHEMA:
        require_record_id(raw.get("market_context_ref"), "market_context_ref")
        require_record_id(raw.get("realized_behavior_ref"), "realized_behavior_ref")
        ctx_digest = str(raw.get("market_context_content_digest") or "")
        rb_digest = str(raw.get("realized_behavior_content_digest") or "")
        if not is_valid_sha256_hex_v0(ctx_digest):
            raise MiLearningEvidenceValidationError("MARKET_CONTEXT_CONTENT_DIGEST_INVALID")
        if not is_valid_sha256_hex_v0(rb_digest):
            raise MiLearningEvidenceValidationError("REALIZED_BEHAVIOR_CONTENT_DIGEST_INVALID")
        snapshot = require_mapping(
            raw.get("behavior_semantics_snapshot"), "behavior_semantics_snapshot"
        )
        for key in (
            "forward_behavior_status",
            "excursion_status",
            "classical_mfe_mae_status",
            "realized_volatility_status",
            "transition_status",
        ):
            if key not in snapshot:
                raise MiLearningEvidenceValidationError(
                    f"BEHAVIOR_SEMANTICS_SNAPSHOT_MISSING:{key}"
                )

    digest = str(raw.get("reproducibility_digest") or "")
    if not is_valid_sha256_hex_v0(digest):
        raise MiLearningEvidenceValidationError("REPRODUCIBILITY_DIGEST_INVALID")
    expected_id = derive_mi_learning_evidence_id_v1(reproducibility_digest=digest)
    if raw.get("mi_learning_evidence_id") != expected_id:
        raise MiLearningEvidenceValidationError("MI_LEARNING_EVIDENCE_ID_MISMATCH")

    require_record_id(raw.get("forecast_evidence_id"), "forecast_evidence_id")
    require_record_id(raw.get("calibration_evidence_id"), "calibration_evidence_id")
    require_event_time_utc(raw.get("forecast_created_at_utc"), "forecast_created_at_utc")
    require_event_time_utc(raw.get("outcome_horizon_end_utc"), "outcome_horizon_end_utc")
    require_non_empty_string_or_unknown(raw.get("bar_spec_ref"), "bar_spec_ref")
    require_non_empty_string_or_unknown(
        raw.get("horizon_observation_status"), "horizon_observation_status"
    )
    require_non_empty_string_or_unknown(
        raw.get("outcome_finalization_status"), "outcome_finalization_status"
    )
    require_mapping(raw.get("provenance"), "provenance")
    _assert_learning_state_semantics_v1(raw)

    join_digest = str(raw.get("forecast_outcome_join_digest") or "")
    if not is_valid_sha256_hex_v0(join_digest):
        raise MiLearningEvidenceValidationError("FORECAST_OUTCOME_JOIN_DIGEST_INVALID")
    calib_digest = str(raw.get("calibration_evidence_digest") or "")
    if not is_valid_sha256_hex_v0(calib_digest):
        raise MiLearningEvidenceValidationError("CALIBRATION_EVIDENCE_DIGEST_INVALID")
    temporal_digest = str(raw.get("temporal_integrity_digest") or "")
    if not is_valid_sha256_hex_v0(temporal_digest):
        raise MiLearningEvidenceValidationError("TEMPORAL_INTEGRITY_DIGEST_INVALID")
    if compute_mi_learning_reproducibility_digest_v1(raw) != digest:
        raise MiLearningEvidenceValidationError("MI_LEARNING_CONTENT_DIGEST_MISMATCH")

    return MappingProxyType(dict(raw))


def validate_mi_learning_evidence_record_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    return build_mi_learning_evidence_record_v1(payload)


def compute_mi_learning_reproducibility_digest_v1(body: Mapping[str, Any]) -> str:
    canonical = {
        "schema_version": SCHEMA_VERSION,
        "forecast_evidence_id": body["forecast_evidence_id"],
        "calibration_evidence_id": body["calibration_evidence_id"],
        "forecast_outcome_join_digest": body["forecast_outcome_join_digest"],
        "actual_outcome_ref": body.get("actual_outcome_ref"),
        "n_bars": body["n_bars"],
        "bar_spec_ref": body["bar_spec_ref"],
        "information_set_ref": body["information_set_ref"],
        "horizon_observation_status": body["horizon_observation_status"],
        "outcome_finalization_status": body["outcome_finalization_status"],
        "evaluability": body["evaluability"],
        "calibration_method": body["calibration_method"],
        "calibration_evidence_digest": body["calibration_evidence_digest"],
        "temporal_integrity_digest": body["temporal_integrity_digest"],
        "selected_instrument_ref": body.get("selected_instrument_ref"),
        "instrument_ref": body.get("instrument_ref"),
    }
    if body.get("conditioned_binding_schema") == CONDITIONED_BINDING_SCHEMA:
        canonical.update(
            {
                "conditioned_binding_schema": CONDITIONED_BINDING_SCHEMA,
                "market_context_ref": body.get("market_context_ref"),
                "market_context_content_digest": body.get("market_context_content_digest"),
                "realized_behavior_ref": body.get("realized_behavior_ref"),
                "realized_behavior_content_digest": body.get("realized_behavior_content_digest"),
                "behavior_semantics_snapshot": body.get("behavior_semantics_snapshot"),
            }
        )
    return compute_content_hash_v0(canonical)
