"""Fail-closed validation and quarantine rules for productive evidence."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    AGE_FORMULA_VERSION,
    AGE_REFERENCE_CLOCK,
    EVIDENCE_SCHEMA_VERSION,
    KNOWN_VOLATILITY_UNITS,
    THRESHOLD_STATUS,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    DuplicateStatusV1,
    ProductiveEvidenceAccumulationError,
    ProductiveResearchEvidenceRecordV1,
    ResearchRegimeLabelV1,
    ValidationStatusV1,
    as_bool,
    as_float,
    as_int,
    digest_excluding_keys,
    optional_text,
    require_nonempty,
)


def parse_event_time(value: Any, *, field_name: str) -> datetime:
    text = require_nonempty(value, field_name=field_name)
    normalized = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ProductiveEvidenceAccumulationError(f"{field_name}_unparseable") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def compute_age_seconds_v1(*, market_event_time: str, as_of_event_time: str) -> float:
    market = parse_event_time(market_event_time, field_name="market_event_time")
    as_of = parse_event_time(as_of_event_time, field_name="as_of_event_time")
    age = (market - as_of).total_seconds()
    if age < 0:
        raise ProductiveEvidenceAccumulationError("negative_age_seconds")
    return float(age)


def validate_productive_evidence_record_v1(
    record: ProductiveResearchEvidenceRecordV1 | Mapping[str, Any],
) -> tuple[ValidationStatusV1, tuple[str, ...]]:
    """Return validation status and rejection reasons (empty when VALID)."""
    reasons: list[str] = []
    payload = (
        record.to_dict() if isinstance(record, ProductiveResearchEvidenceRecordV1) else dict(record)
    )

    def _check(cond: bool, code: str) -> None:
        if not cond:
            reasons.append(code)

    try:
        schema = require_nonempty(
            payload.get("evidence_schema_version"), field_name="evidence_schema_version"
        )
        _check(schema == EVIDENCE_SCHEMA_VERSION, "schema_version_mismatch")
    except ProductiveEvidenceAccumulationError:
        reasons.append("schema_version_mismatch")

    for field in (
        "evidence_record_id",
        "session_id",
        "repository_sha",
        "canonical_instrument_id",
        "venue",
        "venue_instrument_id",
        "volatility_source_digest",
        "source_estimate_id",
        "cycle_id",
        "preregistration_digest",
        "strategy_contract_digest",
        "volatility_contract_digest",
        "decision_context_digest",
    ):
        try:
            require_nonempty(payload.get(field), field_name=field)
        except ProductiveEvidenceAccumulationError:
            reasons.append(f"missing_{field}")

    try:
        age = as_float(payload.get("age_seconds"), field_name="age_seconds")
        _check(age >= 0.0, "negative_age")
    except ProductiveEvidenceAccumulationError:
        reasons.append("age_not_finite")
        age = None

    try:
        vol = as_float(payload.get("volatility_value"), field_name="volatility_value")
        _check(math.isfinite(vol), "volatility_not_finite")
    except ProductiveEvidenceAccumulationError:
        reasons.append("volatility_not_finite")

    unit = optional_text(payload.get("volatility_unit"))
    _check(
        unit is not None and unit in KNOWN_VOLATILITY_UNITS and unit != "UNKNOWN",
        "unknown_volatility_unit",
    )

    try:
        horizon = as_float(
            payload.get("volatility_horizon_seconds"),
            field_name="volatility_horizon_seconds",
        )
        _check(horizon > 0.0, "unknown_volatility_horizon")
    except ProductiveEvidenceAccumulationError:
        reasons.append("unknown_volatility_horizon")

    market_t = optional_text(payload.get("market_event_time"))
    as_of_t = optional_text(payload.get("as_of_event_time"))
    if market_t is None or as_of_t is None:
        reasons.append("incomplete_event_time_reference")
    else:
        try:
            recomputed = compute_age_seconds_v1(
                market_event_time=market_t,
                as_of_event_time=as_of_t,
            )
            if age is not None and abs(recomputed - age) > 1e-9:
                reasons.append("age_formula_mismatch")
        except ProductiveEvidenceAccumulationError as exc:
            reasons.append(str(exc))

    clock = optional_text(payload.get("clock_trust_state"))
    data = optional_text(payload.get("data_trust_state"))
    _check(clock == "TRUSTED", "untrusted_clock")
    _check(data == "TRUSTED", "invalid_data")

    _check(
        optional_text(payload.get("age_reference_clock")) == AGE_REFERENCE_CLOCK,
        "age_reference_clock_mismatch",
    )
    _check(
        optional_text(payload.get("age_formula_version")) == AGE_FORMULA_VERSION,
        "age_formula_version_mismatch",
    )

    regime = optional_text(payload.get("regime_label"))
    _check(
        regime is not None and regime in {r.value for r in ResearchRegimeLabelV1},
        "unknown_regime_label",
    )

    try:
        restart_generation = as_int(
            payload.get("restart_generation"), field_name="restart_generation"
        )
        reuse_count = as_int(payload.get("reuse_count"), field_name="reuse_count")
        estimate_reused = as_bool(payload.get("estimate_reused"), field_name="estimate_reused")
        _check(restart_generation >= 0, "invalid_restart_generation")
        _check(reuse_count >= 0, "invalid_reuse_count")
        if estimate_reused and reuse_count < 1:
            reasons.append("contradictory_reuse_semantics")
        if (not estimate_reused) and reuse_count != 0:
            reasons.append("contradictory_reuse_semantics")
    except ProductiveEvidenceAccumulationError as exc:
        reasons.append(str(exc))

    stored_digest = optional_text(payload.get("record_digest"))
    if stored_digest is None:
        reasons.append("missing_record_digest")
    else:
        recomputed_digest = digest_excluding_keys(payload, exclude=("record_digest",))
        if recomputed_digest != stored_digest:
            reasons.append("digest_mismatch")

    duplicate = optional_text(payload.get("duplicate_status"))
    if duplicate == DuplicateStatusV1.DUPLICATE_CONFLICT.value:
        reasons.append("unresolvable_duplicate_identity")
    if duplicate == DuplicateStatusV1.UNRESOLVED.value:
        reasons.append("unresolvable_duplicate_identity")

    # Productive accumulation never carries a decided threshold.
    if payload.get("threshold_status") not in (None, THRESHOLD_STATUS):
        reasons.append("resolved_threshold_forbidden")
    if payload.get("enforcement_applied") is True:
        reasons.append("enforcement_applied_forbidden")
    if payload.get("numeric_threshold_selected") is True:
        reasons.append("numeric_threshold_selected_forbidden")

    if payload.get("synthetic") is True:
        reasons.append("synthetic_evidence_rejected")
    if payload.get("fixture") is True:
        reasons.append("fixture_evidence_rejected")
    if payload.get("test_data") is True:
        reasons.append("test_or_fixture_evidence_rejected")

    if reasons:
        return ValidationStatusV1.INVALID, tuple(sorted(set(reasons)))
    return ValidationStatusV1.VALID, ()


def finalize_record_digest_v1(payload: Mapping[str, Any]) -> str:
    return digest_excluding_keys(payload, exclude=("record_digest",))


def attach_validation_v1(
    record: ProductiveResearchEvidenceRecordV1,
) -> ProductiveResearchEvidenceRecordV1:
    status, reasons = validate_productive_evidence_record_v1(record)
    payload = record.to_dict()
    payload["validation_status"] = status.value
    payload["rejection_reasons"] = list(reasons)
    if status != ValidationStatusV1.VALID:
        # Keep digest over validated body including rejection metadata.
        payload["record_digest"] = finalize_record_digest_v1(payload)
        return productive_record_from_mapping_v1(payload)
    # Recompute digest after validation fields are confirmed.
    payload["record_digest"] = finalize_record_digest_v1(payload)
    return productive_record_from_mapping_v1(payload)


def productive_record_from_mapping_v1(
    payload: Mapping[str, Any],
) -> ProductiveResearchEvidenceRecordV1:
    return ProductiveResearchEvidenceRecordV1(
        evidence_schema_version=str(payload["evidence_schema_version"]),
        evidence_record_id=str(payload["evidence_record_id"]),
        session_id=str(payload["session_id"]),
        session_start_event_time=str(payload["session_start_event_time"]),
        session_end_event_time=optional_text(payload.get("session_end_event_time")),
        observation_event_time=str(payload["observation_event_time"]),
        venue=str(payload["venue"]),
        canonical_instrument_id=str(payload["canonical_instrument_id"]),
        venue_instrument_id=str(payload["venue_instrument_id"]),
        repository_sha=str(payload["repository_sha"]),
        strategy_contract_digest=str(payload["strategy_contract_digest"]),
        volatility_contract_digest=str(payload["volatility_contract_digest"]),
        preregistration_digest=str(payload["preregistration_digest"]),
        market_event_time=str(payload["market_event_time"]),
        receive_time=optional_text(payload.get("receive_time")),
        as_of_event_time=str(payload["as_of_event_time"]),
        volatility_value=float(payload["volatility_value"]),
        volatility_unit=str(payload["volatility_unit"]),
        volatility_horizon_seconds=float(payload["volatility_horizon_seconds"]),
        volatility_estimator=str(payload["volatility_estimator"]),
        volatility_observation_count=int(payload["volatility_observation_count"]),
        volatility_source_digest=str(payload["volatility_source_digest"]),
        fallback_used=bool(payload["fallback_used"]),
        age_seconds=float(payload["age_seconds"]),
        age_reference_clock=str(payload["age_reference_clock"]),
        age_formula_version=str(payload["age_formula_version"]),
        source_estimate_id=str(payload["source_estimate_id"]),
        estimate_created_event_time=str(payload["estimate_created_event_time"]),
        estimate_reused=bool(payload["estimate_reused"]),
        reuse_count=int(payload["reuse_count"]),
        restart_generation=int(payload["restart_generation"]),
        regime_label=str(payload["regime_label"]),
        regime_source=str(payload["regime_source"]),
        regime_confidence=str(payload["regime_confidence"]),
        decision_context_digest=str(payload["decision_context_digest"]),
        counterfactual_eligible=bool(payload["counterfactual_eligible"]),
        data_trust_state=str(payload["data_trust_state"]),
        clock_trust_state=str(payload["clock_trust_state"]),
        duplicate_status=str(payload["duplicate_status"]),
        validation_status=str(payload["validation_status"]),
        rejection_reasons=tuple(str(x) for x in (payload.get("rejection_reasons") or ())),
        record_digest=str(payload["record_digest"]),
        cycle_id=str(payload["cycle_id"]),
        reuse_status=str(payload["reuse_status"]),
        restart_status=str(payload["restart_status"]),
        estimate_present=bool(payload["estimate_present"]),
        decision_outcome=optional_text(payload.get("decision_outcome")),
        selected_side=optional_text(payload.get("selected_side")),
        economic_metrics=(
            None
            if payload.get("economic_metrics") is None
            else dict(payload.get("economic_metrics") or {})
        ),
        campaign_id=optional_text(payload.get("campaign_id")),
        market_sample_id=optional_text(payload.get("market_sample_id")),
        productive_input_authority=optional_text(payload.get("productive_input_authority")),
        source_is_authoritative_bridge_cycle=bool(
            payload.get("source_is_authoritative_bridge_cycle") or False
        ),
        synthetic=bool(payload.get("synthetic") or False),
        fixture=bool(payload.get("fixture") or False),
        test_data=bool(payload.get("test_data") or False),
        estimate_age_seconds=(
            None
            if payload.get("estimate_age_seconds") is None and payload.get("age_seconds") is None
            else float(
                payload.get("estimate_age_seconds")
                if payload.get("estimate_age_seconds") is not None
                else payload.get("age_seconds")
            )
        ),
        volatility_regime=optional_text(payload.get("volatility_regime")),
        config_digest=optional_text(payload.get("config_digest")),
        code_sha=optional_text(payload.get("code_sha") or payload.get("repository_sha")),
        exit_path_preservation=bool(payload.get("exit_path_preservation", True)),
        productive_preregistration_digest=optional_text(
            payload.get("productive_preregistration_digest")
        ),
        estimator_observation_count=(
            None
            if payload.get("estimator_observation_count") is None
            and payload.get("volatility_observation_count") is None
            else int(
                payload.get("estimator_observation_count")
                if payload.get("estimator_observation_count") is not None
                else payload.get("volatility_observation_count")
            )
        ),
    )


def should_quarantine_v1(status: ValidationStatusV1, reasons: tuple[str, ...]) -> bool:
    _ = reasons
    return status != ValidationStatusV1.VALID
