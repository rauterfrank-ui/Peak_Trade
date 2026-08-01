"""Productive non-enforcing research evidence producer."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    AGE_FORMULA_VERSION,
    AGE_REFERENCE_CLOCK,
    AUTHORITATIVE_BRIDGE_CYCLE_OUTPUT_ID,
    EVIDENCE_SCHEMA_VERSION,
    LEGACY_FALLBACK_VALUES_FORBIDDEN_AS_RESEARCH_TRUTH,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    DuplicateStatusV1,
    ProductiveEvidenceAccumulationError,
    ProductiveEvidenceSessionV1,
    ProductiveResearchEvidenceRecordV1,
    ValidationStatusV1,
    digest_excluding_keys,
    optional_text,
    require_nonempty,
    sha256_hex_text,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.regime_v1 import (
    map_typed_feature_regime_to_research_label_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.session_v1 import (
    assert_observation_binds_session_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.validation_v1 import (
    compute_age_seconds_v1,
    finalize_record_digest_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.preregistration_v1 import (
    assert_preregistration_before_evidence_v1,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    build_ratified_max_age_research_design_contract_v1,
)


def _evidence_record_id_v1(
    *,
    session_id: str,
    cycle_id: str,
    instrument_id: str,
    market_event_time: str,
    source_estimate_id: str,
    volatility_source_digest: str,
) -> str:
    material = "|".join(
        [
            session_id,
            cycle_id,
            instrument_id,
            market_event_time,
            source_estimate_id,
            volatility_source_digest,
        ]
    )
    return "evr_" + sha256_hex_text(material)[:32]


def _decision_context_digest_v1(cycle: Mapping[str, Any]) -> str:
    body = {
        "cycle_id": cycle.get("cycle_id"),
        "decision_outcome": cycle.get("decision_outcome"),
        "selected_side": cycle.get("selected_side"),
        "session_id": cycle.get("session_id"),
        "trading_epoch": cycle.get("trading_epoch"),
    }
    return digest_excluding_keys(body, exclude=())


def produce_productive_research_evidence_from_cycle_v1(
    cycle: Mapping[str, Any],
    *,
    session: ProductiveEvidenceSessionV1,
    repository_sha: str,
    prior_source_estimate_id: Optional[str] = None,
    prior_reuse_count: int = 0,
    prior_cycle_id: Optional[str] = None,
) -> ProductiveResearchEvidenceRecordV1:
    """Produce one productive evidence record from a hardening/shadow cycle.

    Evidence is derived only from typed cycle fields (event times, estimate
    provenance, trust states). Runtime cycle index / poll counts are never used
    as synthetic market evidence.
    """
    # Preregistration must be bound before any productive evidence materialization.
    productive_prereg = assert_preregistration_before_evidence_v1()
    design = build_ratified_max_age_research_design_contract_v1()
    if design.preregistration_digest != productive_prereg.design_preregistration_digest:
        raise ProductiveEvidenceAccumulationError("design_preregistration_digest_drift")
    binding = dict(cycle.get("canonical_volatility_typed_binding") or {})
    gate = dict(cycle.get("double_play_typed_volatility_presence_gate") or {})
    age = dict(gate.get("max_age_policy_evidence") or {})
    feature_regime = dict(cycle.get("feature_regime") or {})

    if not age:
        raise ProductiveEvidenceAccumulationError("cycle_missing_max_age_policy_evidence")

    session_id = require_nonempty(cycle.get("session_id"), field_name="session_id")
    cycle_id = require_nonempty(cycle.get("cycle_id"), field_name="cycle_id")
    instrument_id = require_nonempty(cycle.get("instrument_id"), field_name="instrument_id")
    venue = require_nonempty(
        cycle.get("venue") or binding.get("venue") or session.venue,
        field_name="venue",
    )
    venue_instrument_id = require_nonempty(
        cycle.get("venue_instrument_id")
        or binding.get("venue_instrument_id")
        or session.venue_instrument_id
        or instrument_id,
        field_name="venue_instrument_id",
    )
    assert_observation_binds_session_v1(
        session,
        session_id=session_id,
        repository_sha=repository_sha,
        venue=venue,
        canonical_instrument_id=instrument_id,
    )

    market_event_time = require_nonempty(
        age.get("reference_event_time") or cycle.get("market_event_time"),
        field_name="market_event_time",
    )
    as_of_event_time = require_nonempty(
        age.get("estimate_as_of_event_time") or binding.get("estimate_as_of_event_time"),
        field_name="as_of_event_time",
    )
    age_seconds = age.get("computed_age_seconds")
    if age_seconds is None:
        age_seconds = compute_age_seconds_v1(
            market_event_time=market_event_time,
            as_of_event_time=as_of_event_time,
        )
    else:
        age_seconds = float(age_seconds)
        recomputed = compute_age_seconds_v1(
            market_event_time=market_event_time,
            as_of_event_time=as_of_event_time,
        )
        if abs(recomputed - age_seconds) > 1e-9:
            raise ProductiveEvidenceAccumulationError("age_formula_mismatch")

    source_digest = require_nonempty(
        age.get("source_digest") or binding.get("source_digest"),
        field_name="volatility_source_digest",
    )
    source_estimate_id = require_nonempty(
        binding.get("estimate_id")
        or binding.get("source_estimate_id")
        or cycle.get("source_estimate_id")
        or f"est_{source_digest[:24]}",
        field_name="source_estimate_id",
    )

    estimate_reused = False
    reuse_count = 0
    # Reuse applies only across distinct observations/cycles. Exact replay of the
    # same cycle must remain byte-stable for idempotent ledger resume.
    if (
        prior_source_estimate_id is not None
        and prior_source_estimate_id == source_estimate_id
        and prior_cycle_id is not None
        and prior_cycle_id != cycle_id
    ):
        estimate_reused = True
        reuse_count = int(prior_reuse_count) + 1

    reuse_status = optional_text(binding.get("reuse_status") or age.get("reuse_status"))
    if estimate_reused:
        # Same estimate identity across observations → reuse semantics win.
        reuse_status = "DUPLICATE_SAMPLE_REUSE"
    elif reuse_status is None:
        reuse_status = "FRESHLY_PRODUCED"

    restart_status = optional_text(binding.get("restart_status") or age.get("restart_status"))
    if restart_status is None:
        restart_status = (
            "FIRST_PRODUCTION_AFTER_RESTART"
            if session.restart_generation > 0 and not estimate_reused
            else "NOT_APPLICABLE"
        )

    regime_label, regime_source, regime_confidence = map_typed_feature_regime_to_research_label_v1(
        feature_regime
    )
    volatility_regime = optional_text(feature_regime.get("volatility_regime"))
    if volatility_regime is None:
        if regime_label in {"HIGH_VOLATILITY", "LOW_VOLATILITY"}:
            volatility_regime = regime_label
        elif regime_label == "STRESS_OR_GAP":
            volatility_regime = "STRESS_OR_GAP"
        else:
            volatility_regime = "UNCLASSIFIED"

    def _normalize_trust(raw: Any, *, default: str) -> str:
        text = optional_text(raw)
        if text is None:
            return default
        mapping = {
            "trusted": "TRUSTED",
            "TRUSTED": "TRUSTED",
            "untrusted": "UNTRUSTED",
            "UNTRUSTED": "UNTRUSTED",
        }
        return mapping.get(text, text.upper())

    clock_trust = _normalize_trust(age.get("clock_trust_status"), default="UNTRUSTED")
    data_trust = _normalize_trust(age.get("data_integrity_status"), default="UNTRUSTED")
    estimate_present = bool(
        binding.get("estimate_present")
        if binding.get("estimate_present") is not None
        else str(age.get("presence_status") or "").upper() == "PRESENT"
    )

    volatility_value = binding.get("volatility_value")
    if volatility_value is None:
        volatility_value = feature_regime.get("volatility_estimate")
    if volatility_value is None:
        raise ProductiveEvidenceAccumulationError("volatility_value_required")

    # Legacy naked defaults must never become productive research truth.
    if bool(binding.get("fallback_used") or feature_regime.get("default_regime_fallback_active")):
        try:
            numeric_vol = float(volatility_value)
        except (TypeError, ValueError) as exc:
            raise ProductiveEvidenceAccumulationError("volatility_value_not_numeric") from exc
        if numeric_vol in set(LEGACY_FALLBACK_VALUES_FORBIDDEN_AS_RESEARCH_TRUTH):
            raise ProductiveEvidenceAccumulationError("legacy_fallback_forbidden_as_research_truth")

    volatility_unit = optional_text(binding.get("volatility_unit")) or "DECIMAL_FRACTION"
    horizon = binding.get("volatility_horizon_seconds")
    if horizon is None:
        horizon = binding.get("horizon_seconds")
    if horizon is None and estimate_present:
        # Canonical typed estimate horizon from the productive CMC binding contract.
        from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
            CANONICAL_HORIZON_SECONDS,
        )

        horizon = CANONICAL_HORIZON_SECONDS
    if horizon is None:
        raise ProductiveEvidenceAccumulationError("unknown_volatility_horizon")

    observation_count = binding.get("observation_count")
    if observation_count is None:
        raise ProductiveEvidenceAccumulationError("volatility_observation_count_required")

    estimator = optional_text(binding.get("volatility_estimator") or binding.get("estimator"))
    if estimator is None:
        estimator = "TYPED_RUNTIME_PRODUCER"

    fallback_used = bool(
        binding.get("fallback_used")
        or feature_regime.get("default_regime_fallback_active")
        or cycle.get("synthetic_bid_ask_fallback_active")
        or False
    )

    strategy_contract_digest = optional_text(
        cycle.get("strategy_contract_digest")
    ) or sha256_hex_text("strategy_contract_absent")
    volatility_contract_digest = optional_text(
        binding.get("volatility_contract_digest") or cycle.get("volatility_contract_digest")
    ) or sha256_hex_text("volatility_contract_from_binding|" + source_digest)

    evidence_record_id = _evidence_record_id_v1(
        session_id=session_id,
        cycle_id=cycle_id,
        instrument_id=instrument_id,
        market_event_time=market_event_time,
        source_estimate_id=source_estimate_id,
        volatility_source_digest=source_digest,
    )

    counterfactual_eligible = (
        estimate_present
        and clock_trust == "TRUSTED"
        and data_trust == "TRUSTED"
        and age_seconds is not None
        and float(age_seconds) >= 0.0
        and not fallback_used
    )

    authority = dict(cycle.get("productive_bridge_cycle_authority") or {})
    provisional: dict[str, Any] = {
        "age_formula_version": AGE_FORMULA_VERSION,
        "age_reference_clock": AGE_REFERENCE_CLOCK,
        "age_seconds": float(age_seconds),
        "as_of_event_time": as_of_event_time,
        "campaign_id": optional_text(authority.get("campaign_id") or cycle.get("campaign_id")),
        "canonical_instrument_id": instrument_id,
        "clock_trust_state": clock_trust,
        "code_sha": require_nonempty(repository_sha, field_name="repository_sha"),
        "config_digest": optional_text(cycle.get("config_digest"))
        or sha256_hex_text(
            "config|"
            + str(strategy_contract_digest)
            + "|"
            + str(volatility_contract_digest)
            + "|"
            + source_digest
        ),
        "counterfactual_eligible": counterfactual_eligible,
        "cycle_id": cycle_id,
        "data_trust_state": data_trust,
        "decision_context_digest": _decision_context_digest_v1(cycle),
        "decision_outcome": optional_text(cycle.get("decision_outcome")),
        "duplicate_status": DuplicateStatusV1.UNIQUE.value,
        "economic_metrics": (
            None
            if cycle.get("economic_metrics") is None
            else dict(cycle.get("economic_metrics") or {})
        ),
        "estimate_age_seconds": float(age_seconds),
        "estimate_created_event_time": optional_text(
            binding.get("estimate_created_event_time") or as_of_event_time
        ),
        "estimate_present": estimate_present,
        "estimate_reused": estimate_reused,
        "estimator_observation_count": int(observation_count),
        "evidence_record_id": evidence_record_id,
        "evidence_schema_version": EVIDENCE_SCHEMA_VERSION,
        "exit_path_preservation": True,
        "fallback_used": fallback_used,
        "fixture": bool(
            authority.get("fixture") if "fixture" in authority else cycle.get("fixture") or False
        ),
        "market_event_time": market_event_time,
        "market_sample_id": optional_text(
            authority.get("market_sample_id") or cycle.get("market_sample_id")
        ),
        "observation_event_time": market_event_time,
        "preregistration_digest": design.preregistration_digest,
        "productive_input_authority": optional_text(
            authority.get("authority_id") or cycle.get("productive_input_authority")
        ),
        "productive_preregistration_digest": productive_prereg.productive_preregistration_digest,
        "receive_time": optional_text(cycle.get("receive_time") or binding.get("receive_time")),
        "regime_confidence": regime_confidence,
        "regime_label": regime_label,
        "regime_source": regime_source,
        "rejection_reasons": [],
        "repository_sha": require_nonempty(repository_sha, field_name="repository_sha"),
        "restart_generation": int(session.restart_generation),
        "restart_status": restart_status,
        "reuse_count": int(reuse_count),
        "reuse_status": reuse_status,
        "selected_side": optional_text(cycle.get("selected_side")),
        "session_end_event_time": session.session_end_event_time,
        "session_id": session_id,
        "session_start_event_time": session.session_start_event_time,
        "source_estimate_id": source_estimate_id,
        "source_is_authoritative_bridge_cycle": bool(
            authority.get("source_is_authoritative_bridge_cycle")
            or cycle.get("source_is_authoritative_bridge_cycle")
            or False
        ),
        "strategy_contract_digest": strategy_contract_digest,
        "synthetic": bool(
            authority.get("synthetic")
            if "synthetic" in authority
            else cycle.get("synthetic") or False
        ),
        "test_data": bool(
            authority.get("test_data")
            if "test_data" in authority
            else cycle.get("test_data") or False
        ),
        "validation_status": ValidationStatusV1.VALID.value,
        "venue": venue,
        "venue_instrument_id": venue_instrument_id,
        "volatility_contract_digest": volatility_contract_digest,
        "volatility_estimator": estimator,
        "volatility_horizon_seconds": float(horizon),
        "volatility_observation_count": int(observation_count),
        "volatility_regime": volatility_regime,
        "volatility_source_digest": source_digest,
        "volatility_unit": volatility_unit,
        "volatility_value": float(volatility_value),
    }
    if (
        provisional["source_is_authoritative_bridge_cycle"]
        and not provisional["productive_input_authority"]
    ):
        provisional["productive_input_authority"] = AUTHORITATIVE_BRIDGE_CYCLE_OUTPUT_ID
    provisional["estimate_created_event_time"] = require_nonempty(
        provisional["estimate_created_event_time"],
        field_name="estimate_created_event_time",
    )
    provisional["record_digest"] = finalize_record_digest_v1(provisional)

    return ProductiveResearchEvidenceRecordV1(
        evidence_schema_version=str(provisional["evidence_schema_version"]),
        evidence_record_id=str(provisional["evidence_record_id"]),
        session_id=str(provisional["session_id"]),
        session_start_event_time=str(provisional["session_start_event_time"]),
        session_end_event_time=provisional.get("session_end_event_time"),
        observation_event_time=str(provisional["observation_event_time"]),
        venue=str(provisional["venue"]),
        canonical_instrument_id=str(provisional["canonical_instrument_id"]),
        venue_instrument_id=str(provisional["venue_instrument_id"]),
        repository_sha=str(provisional["repository_sha"]),
        strategy_contract_digest=str(provisional["strategy_contract_digest"]),
        volatility_contract_digest=str(provisional["volatility_contract_digest"]),
        preregistration_digest=str(provisional["preregistration_digest"]),
        market_event_time=str(provisional["market_event_time"]),
        receive_time=provisional.get("receive_time"),
        as_of_event_time=str(provisional["as_of_event_time"]),
        volatility_value=float(provisional["volatility_value"]),
        volatility_unit=str(provisional["volatility_unit"]),
        volatility_horizon_seconds=float(provisional["volatility_horizon_seconds"]),
        volatility_estimator=str(provisional["volatility_estimator"]),
        volatility_observation_count=int(provisional["volatility_observation_count"]),
        volatility_source_digest=str(provisional["volatility_source_digest"]),
        fallback_used=bool(provisional["fallback_used"]),
        age_seconds=float(provisional["age_seconds"]),
        age_reference_clock=str(provisional["age_reference_clock"]),
        age_formula_version=str(provisional["age_formula_version"]),
        source_estimate_id=str(provisional["source_estimate_id"]),
        estimate_created_event_time=str(provisional["estimate_created_event_time"]),
        estimate_reused=bool(provisional["estimate_reused"]),
        reuse_count=int(provisional["reuse_count"]),
        restart_generation=int(provisional["restart_generation"]),
        regime_label=str(provisional["regime_label"]),
        regime_source=str(provisional["regime_source"]),
        regime_confidence=str(provisional["regime_confidence"]),
        decision_context_digest=str(provisional["decision_context_digest"]),
        counterfactual_eligible=bool(provisional["counterfactual_eligible"]),
        data_trust_state=str(provisional["data_trust_state"]),
        clock_trust_state=str(provisional["clock_trust_state"]),
        duplicate_status=str(provisional["duplicate_status"]),
        validation_status=str(provisional["validation_status"]),
        rejection_reasons=(),
        record_digest=str(provisional["record_digest"]),
        cycle_id=str(provisional["cycle_id"]),
        reuse_status=str(provisional["reuse_status"]),
        restart_status=str(provisional["restart_status"]),
        estimate_present=bool(provisional["estimate_present"]),
        decision_outcome=provisional.get("decision_outcome"),
        selected_side=provisional.get("selected_side"),
        economic_metrics=provisional.get("economic_metrics"),
        campaign_id=provisional.get("campaign_id"),
        market_sample_id=provisional.get("market_sample_id"),
        productive_input_authority=provisional.get("productive_input_authority"),
        source_is_authoritative_bridge_cycle=bool(
            provisional.get("source_is_authoritative_bridge_cycle")
        ),
        synthetic=bool(provisional.get("synthetic")),
        fixture=bool(provisional.get("fixture")),
        test_data=bool(provisional.get("test_data")),
        estimate_age_seconds=float(provisional["estimate_age_seconds"]),
        volatility_regime=optional_text(provisional.get("volatility_regime")),
        config_digest=optional_text(provisional.get("config_digest")),
        code_sha=optional_text(provisional.get("code_sha")),
        exit_path_preservation=bool(provisional.get("exit_path_preservation", True)),
        productive_preregistration_digest=optional_text(
            provisional.get("productive_preregistration_digest")
        ),
        estimator_observation_count=int(provisional["estimator_observation_count"]),
    )
