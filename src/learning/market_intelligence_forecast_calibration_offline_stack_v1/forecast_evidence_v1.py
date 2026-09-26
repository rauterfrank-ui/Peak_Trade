"""Governed ForecastEvidence contract v1 (offline / observation; AUTHORITY=NONE)."""

from __future__ import annotations

from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    require_event_time_utc,
    require_mapping,
    require_non_empty_string_or_unknown,
    require_record_id,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_contracts_v1 import (
    require_positive_int,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
    compute_content_hash_v0,
    is_valid_sha256_hex_v0,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    FORECAST_HORIZON_MUST_BE_EXPLICIT,
    STACK_DOMAIN,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.probabilistic_forecast_payload_v1 import (
    validate_probabilistic_forecast_payload_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.support_disposition_v1 import (
    require_support_disposition,
)

SCHEMA_VERSION: Final[str] = "forecast_evidence_v1"
EVIDENCE_CLASS_FORECAST: Final[str] = "FORECAST_EVIDENCE"
UNIVERSE_CLASS_MARKET_INTELLIGENCE: Final[str] = "MARKET_INTELLIGENCE_UNIVERSE"
FORECAST_EVIDENCE_AUTHORITY: Final[str] = "NONE"

OUTCOME_BINDING_MODE_ACTUAL: Final[str] = "ACTUAL"
OUTCOME_BINDING_MODE_MODELLED: Final[str] = "MODELLED_COUNTERFACTUAL"

_REQUIRED: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "domain",
        "forecast_evidence_id",
        "information_set_ref",
        "forecast_created_at_utc",
        "outcome_horizon_end_utc",
        "n_bars",
        "bar_spec_ref",
        "forecast_kind",
        "probabilistic_payload",
        "market_state_refs",
        "forecast_model_ref",
        "support_disposition",
        "outcome_binding_mode",
        "provenance",
        "forecast_evidence_authority",
        "content_digest",
    }
)


class ForecastEvidenceValidationError(ValueError):
    """Fail-closed forecast evidence validation."""


def _parse_utc(value: str) -> datetime:
    text = require_event_time_utc(value, "utc")
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def derive_outcome_horizon_end_utc_v1(
    *, horizon_start_time_utc: str, bar_close_times_utc: Sequence[str]
) -> str:
    if not bar_close_times_utc:
        raise DdoValidationError("BAR_CLOSE_TIMES_REQUIRED_FOR_HORIZON_END")
    start = _parse_utc(horizon_start_time_utc)
    last_close = _parse_utc(str(bar_close_times_utc[-1]))
    if last_close <= start:
        raise DdoValidationError("HORIZON_END_NOT_AFTER_START")
    return require_event_time_utc(bar_close_times_utc[-1], "outcome_horizon_end_utc")


def derive_forecast_evidence_id_v1(*, identity_body: Mapping[str, Any]) -> str:
    digest = compute_content_hash_v0(dict(identity_body))
    return f"mi.forecast.{digest[:48]}"


def build_forecast_evidence_v1(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "forecast_evidence")
    missing = _REQUIRED - frozenset(raw.keys())
    if missing:
        raise ForecastEvidenceValidationError("FORECAST_EVIDENCE_FIELDS_MISSING")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise ForecastEvidenceValidationError("FORECAST_EVIDENCE_SCHEMA_MISMATCH")
    if raw.get("forecast_evidence_authority") != FORECAST_EVIDENCE_AUTHORITY:
        raise ForecastEvidenceValidationError("FORECAST_EVIDENCE_AUTHORITY_MUST_BE_NONE")

    n_bars = require_positive_int(raw.get("n_bars"), "n_bars")
    if not FORECAST_HORIZON_MUST_BE_EXPLICIT or n_bars <= 0:
        raise ForecastEvidenceValidationError("FORECAST_HORIZON_EXPLICIT_REQUIRED")
    bar_spec_ref = require_non_empty_string_or_unknown(raw.get("bar_spec_ref"), "bar_spec_ref")
    information_set_ref = require_record_id(raw.get("information_set_ref"), "information_set_ref")
    created_at = require_event_time_utc(
        raw.get("forecast_created_at_utc"), "forecast_created_at_utc"
    )
    horizon_end = require_event_time_utc(
        raw.get("outcome_horizon_end_utc"), "outcome_horizon_end_utc"
    )
    if _parse_utc(created_at) >= _parse_utc(horizon_end):
        raise ForecastEvidenceValidationError("FORECAST_CREATED_NOT_BEFORE_OUTCOME_BOUNDARY")

    forecast_kind = str(raw.get("forecast_kind") or "")
    probabilistic = validate_probabilistic_forecast_payload_v1(
        forecast_kind=forecast_kind,
        payload=require_mapping(raw.get("probabilistic_payload"), "probabilistic_payload"),
    )
    market_state_refs = raw.get("market_state_refs")
    if not isinstance(market_state_refs, list) or not market_state_refs:
        raise ForecastEvidenceValidationError("MARKET_STATE_REFS_REQUIRED")
    normalized_refs = [require_record_id(item, "market_state_refs[]") for item in market_state_refs]

    outcome_mode = str(raw.get("outcome_binding_mode") or OUTCOME_BINDING_MODE_ACTUAL)
    if outcome_mode not in {OUTCOME_BINDING_MODE_ACTUAL, OUTCOME_BINDING_MODE_MODELLED}:
        raise ForecastEvidenceValidationError("OUTCOME_BINDING_MODE_INVALID")

    support = require_support_disposition(raw.get("support_disposition"), "support_disposition")
    provenance = require_mapping(raw.get("provenance"), "provenance")

    identity_body = {
        "domain": STACK_DOMAIN,
        "schema_version": SCHEMA_VERSION,
        "information_set_ref": information_set_ref,
        "forecast_created_at_utc": created_at,
        "outcome_horizon_end_utc": horizon_end,
        "n_bars": n_bars,
        "bar_spec_ref": bar_spec_ref,
        "forecast_kind": forecast_kind,
        "probabilistic_payload_digest": probabilistic["payload_digest"],
        "market_state_refs": tuple(sorted(normalized_refs)),
        "forecast_model_ref": require_record_id(
            raw.get("forecast_model_ref"), "forecast_model_ref"
        ),
        "support_disposition": support,
        "outcome_binding_mode": outcome_mode,
    }
    evidence_id = derive_forecast_evidence_id_v1(identity_body=identity_body)
    if raw.get("forecast_evidence_id") != evidence_id:
        raise ForecastEvidenceValidationError("FORECAST_EVIDENCE_ID_MISMATCH")

    content_digest = compute_content_hash_v0(
        {
            **identity_body,
            "forecast_evidence_id": evidence_id,
            "provenance": dict(provenance),
        }
    )
    if raw.get("content_digest") != content_digest:
        raise ForecastEvidenceValidationError("FORECAST_CONTENT_DIGEST_MISMATCH")
    if not is_valid_sha256_hex_v0(content_digest):
        raise ForecastEvidenceValidationError("FORECAST_CONTENT_DIGEST_INVALID")

    record = {
        **identity_body,
        "forecast_evidence_id": evidence_id,
        "probabilistic_payload": dict(probabilistic["payload"]),
        "market_state_refs": list(normalized_refs),
        "provenance": dict(provenance),
        "content_digest": content_digest,
        "evidence_class": EVIDENCE_CLASS_FORECAST,
        "universe_class": UNIVERSE_CLASS_MARKET_INTELLIGENCE,
        "forecast_evidence_authority": FORECAST_EVIDENCE_AUTHORITY,
        "decision_event_ref": optional_ref(raw.get("decision_event_ref")),
        "selected_instrument_ref": optional_ref(raw.get("selected_instrument_ref")),
        "drift_assessment_refs": optional_ref_list(raw.get("drift_assessment_refs")),
    }
    return MappingProxyType(record)


def optional_ref(value: Any) -> str | None:
    if value is None:
        return None
    return require_record_id(value, "optional_ref")


def optional_ref_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ForecastEvidenceValidationError("DRIFT_ASSESSMENT_REFS_INVALID")
    return [require_record_id(item, "drift_assessment_refs[]") for item in value]


def validate_forecast_evidence_v1(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_forecast_evidence_v1(payload)


def mint_forecast_evidence_v1(
    *,
    information_set_ref: str,
    forecast_created_at_utc: str,
    outcome_horizon_end_utc: str,
    n_bars: int,
    bar_spec_ref: str,
    forecast_kind: str,
    probabilistic_payload: Mapping[str, Any],
    market_state_refs: Sequence[str],
    forecast_model_ref: str,
    support_disposition: str,
    provenance: Mapping[str, Any],
    outcome_binding_mode: str = OUTCOME_BINDING_MODE_ACTUAL,
    decision_event_ref: str | None = None,
    selected_instrument_ref: str | None = None,
    drift_assessment_refs: Sequence[str] | None = None,
) -> MappingProxyType[str, Any]:
    probabilistic = validate_probabilistic_forecast_payload_v1(
        forecast_kind=forecast_kind,
        payload=probabilistic_payload,
    )
    normalized_refs = [require_record_id(item, "market_state_refs[]") for item in market_state_refs]
    identity_body = {
        "domain": STACK_DOMAIN,
        "schema_version": SCHEMA_VERSION,
        "information_set_ref": information_set_ref,
        "forecast_created_at_utc": forecast_created_at_utc,
        "outcome_horizon_end_utc": outcome_horizon_end_utc,
        "n_bars": require_positive_int(n_bars, "n_bars"),
        "bar_spec_ref": bar_spec_ref,
        "forecast_kind": forecast_kind,
        "probabilistic_payload_digest": probabilistic["payload_digest"],
        "market_state_refs": tuple(sorted(normalized_refs)),
        "forecast_model_ref": forecast_model_ref,
        "support_disposition": require_support_disposition(
            support_disposition, "support_disposition"
        ),
        "outcome_binding_mode": outcome_binding_mode,
    }
    evidence_id = derive_forecast_evidence_id_v1(identity_body=identity_body)
    content_digest = compute_content_hash_v0(
        {
            **identity_body,
            "forecast_evidence_id": evidence_id,
            "provenance": dict(provenance),
        }
    )
    return build_forecast_evidence_v1(
        {
            **identity_body,
            "domain": STACK_DOMAIN,
            "forecast_evidence_id": evidence_id,
            "probabilistic_payload": dict(probabilistic["payload"]),
            "market_state_refs": list(normalized_refs),
            "provenance": dict(provenance),
            "content_digest": content_digest,
            "forecast_evidence_authority": FORECAST_EVIDENCE_AUTHORITY,
            "decision_event_ref": decision_event_ref,
            "selected_instrument_ref": selected_instrument_ref,
            "drift_assessment_refs": list(drift_assessment_refs or []),
        }
    )
