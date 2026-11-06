"""Typed probabilistic forecast payload grammar v1 (research evidence only)."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

FORECAST_KIND_DIRECTIONAL_PROBABILITY: Final[str] = "DIRECTIONAL_PROBABILITY"
FORECAST_KIND_RETURN_DISTRIBUTION_SUMMARY: Final[str] = "RETURN_DISTRIBUTION_SUMMARY"
FORECAST_KIND_THRESHOLD_EVENT_PROBABILITY: Final[str] = "THRESHOLD_EVENT_PROBABILITY"
FORECAST_KIND_EXPECTED_BEHAVIOR: Final[str] = "EXPECTED_BEHAVIOR"


def _canonicalize_numeric_tree(value: Any) -> Any:
    if isinstance(value, float):
        return format(value, ".12g")
    if isinstance(value, Mapping):
        return {str(k): _canonicalize_numeric_tree(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_canonicalize_numeric_tree(v) for v in value]
    return value


ALLOWED_FORECAST_KINDS: Final[frozenset[str]] = frozenset(
    {
        FORECAST_KIND_DIRECTIONAL_PROBABILITY,
        FORECAST_KIND_RETURN_DISTRIBUTION_SUMMARY,
        FORECAST_KIND_THRESHOLD_EVENT_PROBABILITY,
        FORECAST_KIND_EXPECTED_BEHAVIOR,
    }
)

PAYLOAD_SCHEMA_VERSION: Final[str] = "probabilistic_forecast_payload_v1"


def validate_probabilistic_forecast_payload_v1(
    *, forecast_kind: str, payload: Mapping[str, Any]
) -> MappingProxyType[str, Any]:
    if forecast_kind not in ALLOWED_FORECAST_KINDS:
        raise DdoValidationError("FORECAST_KIND_UNSUPPORTED")
    if not isinstance(payload, Mapping):
        raise DdoValidationError("FORECAST_PAYLOAD_MUST_BE_MAPPING")
    body = dict(payload)
    if forecast_kind == FORECAST_KIND_DIRECTIONAL_PROBABILITY:
        for key in ("p_up", "p_down", "p_flat"):
            if key not in body:
                raise DdoValidationError(f"FORECAST_PAYLOAD_MISSING:{key}")
        total = float(body["p_up"]) + float(body["p_down"]) + float(body["p_flat"])
        if abs(total - 1.0) > 1e-9:
            raise DdoValidationError("DIRECTIONAL_PROBABILITIES_MUST_SUM_TO_ONE")
    elif forecast_kind == FORECAST_KIND_RETURN_DISTRIBUTION_SUMMARY:
        for key in ("mean_return", "std_return"):
            if key not in body:
                raise DdoValidationError(f"FORECAST_PAYLOAD_MISSING:{key}")
    elif forecast_kind == FORECAST_KIND_THRESHOLD_EVENT_PROBABILITY:
        if "threshold" not in body or "p_event" not in body:
            raise DdoValidationError("THRESHOLD_EVENT_PAYLOAD_INCOMPLETE")
        prob = float(body["p_event"])
        if prob < 0.0 or prob > 1.0:
            raise DdoValidationError("THRESHOLD_EVENT_PROBABILITY_OUT_OF_RANGE")
    elif forecast_kind == FORECAST_KIND_EXPECTED_BEHAVIOR:
        if "behavior_label" not in body:
            raise DdoValidationError("EXPECTED_BEHAVIOR_LABEL_REQUIRED")
    normalized = {
        "schema_version": PAYLOAD_SCHEMA_VERSION,
        "forecast_kind": forecast_kind,
        "payload": body,
        "payload_digest": compute_content_sha256(
            _canonicalize_numeric_tree({"forecast_kind": forecast_kind, "payload": body})
        ),
    }
    return MappingProxyType(normalized)
