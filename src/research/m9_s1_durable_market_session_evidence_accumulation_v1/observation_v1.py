"""Build typed market-session observations from bridge cycles (observed fields only)."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from research.m9_s1_durable_market_session_evidence_accumulation_v1.constants_v1 import (
    OBSERVATION_SCHEMA_VERSION,
    WORKPACKAGE_ID,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.models_v1 import (
    M9S1EvidenceAccumulationError,
    M9S1MarketSessionObservationV1,
    ObservationSourceClassV1,
    digest_excluding_keys,
    sha256_hex,
)


def _optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def classify_source_class_v1(
    *,
    source_class: str | ObservationSourceClassV1,
    cycle: Mapping[str, Any],
) -> ObservationSourceClassV1:
    if isinstance(source_class, ObservationSourceClassV1):
        chosen = source_class
    else:
        try:
            chosen = ObservationSourceClassV1(str(source_class).strip().upper())
        except ValueError as exc:
            raise M9S1EvidenceAccumulationError(f"unknown_source_class:{source_class}") from exc

    authority = dict(cycle.get("productive_bridge_cycle_authority") or {})
    if authority.get("fixture") is True or cycle.get("forced_wiring") is True:
        if chosen is not ObservationSourceClassV1.SYNTHETIC_FIXTURE:
            raise M9S1EvidenceAccumulationError(
                "fixture_cycle_requires_SYNTHETIC_FIXTURE_source_class"
            )
    if chosen is ObservationSourceClassV1.SYNTHETIC_FIXTURE:
        if not (authority.get("fixture") is True or cycle.get("fixture") is True):
            # Explicit fixture flag on cycle or authority required for synthetic class.
            if cycle.get("fixture") is not True:
                raise M9S1EvidenceAccumulationError(
                    "synthetic_fixture_class_requires_fixture_marker_on_cycle"
                )
    return chosen


def build_observation_from_bridge_cycle_v1(
    cycle: Mapping[str, Any],
    *,
    source_class: str | ObservationSourceClassV1,
    repository_sha: str,
    accumulation_result: Mapping[str, Any] | None = None,
) -> M9S1MarketSessionObservationV1:
    """Materialize observation from cycle + optional accumulation output (no inference)."""
    src = classify_source_class_v1(source_class=source_class, cycle=cycle)
    session_id = _optional_str(cycle.get("session_id"))
    cycle_id = _optional_str(cycle.get("cycle_id"))
    instrument_id = _optional_str(
        cycle.get("instrument_id") or cycle.get("canonical_instrument_id")
    )
    if not session_id or not cycle_id or not instrument_id:
        raise M9S1EvidenceAccumulationError("observation_identity_incomplete")

    gate = dict(cycle.get("double_play_typed_volatility_presence_gate") or {})
    age_evidence = dict(gate.get("max_age_policy_evidence") or {})
    binding = dict(cycle.get("canonical_volatility_typed_binding") or {})

    ref_time = _optional_str(
        age_evidence.get("reference_event_time") or cycle.get("market_event_time")
    )
    as_of = _optional_str(age_evidence.get("estimate_as_of_event_time"))
    age = _optional_float(age_evidence.get("computed_age_seconds"))
    source_digest = _optional_str(age_evidence.get("source_digest"))
    vol_value = _optional_float(
        binding.get("volatility_value") or binding.get("legacy_volatility_float")
    )

    join_digest = None
    productive_record_id = None
    outcome = "SKIPPED"
    missing_reason = None
    if accumulation_result is not None:
        append = dict(accumulation_result.get("append_result") or {})
        action = str(append.get("action") or "")
        if action == "APPENDED":
            outcome = "APPENDED"
        elif action.startswith("DUPLICATE"):
            outcome = "DUPLICATE_IDEMPOTENT"
        elif action.startswith("SKIP"):
            outcome = "SKIPPED"
            missing_reason = _optional_str(append.get("action"))
        elif accumulation_result.get("status") == "EVIDENCE_WRITE_FAILURE":
            outcome = "WRITE_FAILURE"
            missing_reason = _optional_str(accumulation_result.get("error"))
        evidence = accumulation_result.get("evidence_record")
        if isinstance(evidence, dict):
            productive_record_id = _optional_str(evidence.get("evidence_record_id"))
            if vol_value is None:
                vol_value = _optional_float(evidence.get("volatility_value"))
        join_payload = accumulation_result.get("research_join")
        if isinstance(join_payload, dict):
            join_digest = _optional_str(join_payload.get("join_digest"))

    authority = dict(cycle.get("productive_bridge_cycle_authority") or {})
    market_sample_id = _optional_str(
        authority.get("market_sample_id") or cycle.get("market_sample_id")
    )
    runtime_identity = _optional_str(cycle.get("repository_sha") or repository_sha)

    dedup_material = {
        "cycle_id": cycle_id,
        "market_sample_id": market_sample_id,
        "session_id": session_id,
    }
    dedup_identity = sha256_hex(dedup_material)
    observation_id = f"m9s1_obs_{dedup_identity[:32]}"

    provisional = {
        "observation_schema_version": OBSERVATION_SCHEMA_VERSION,
        "workpackage_id": WORKPACKAGE_ID,
        "observation_id": observation_id,
        "session_id": session_id,
        "cycle_id": cycle_id,
        "instrument_id": instrument_id,
        "evidence_source_class": src.value,
        "reference_market_event_time": ref_time,
        "estimate_as_of_event_time": as_of,
        "computed_age_seconds": age,
        "volatility_source_digest": source_digest,
        "volatility_value": vol_value,
        "repository_sha": repository_sha,
        "runtime_build_identity": runtime_identity,
        "market_sample_id": market_sample_id,
        "join_digest": join_digest,
        "productive_evidence_record_id": productive_record_id,
        "observation_outcome": outcome,
        "missing_invalid_reason": missing_reason,
        "ordering_key": ref_time,
        "dedup_identity": dedup_identity,
        "synthetic": src is ObservationSourceClassV1.SYNTHETIC_FIXTURE,
        "fixture": src is ObservationSourceClassV1.SYNTHETIC_FIXTURE,
        "replay": src is ObservationSourceClassV1.REPLAY,
    }
    record_digest = digest_excluding_keys(provisional, exclude=frozenset({"record_digest"}))
    return M9S1MarketSessionObservationV1(record_digest=record_digest, **provisional)
