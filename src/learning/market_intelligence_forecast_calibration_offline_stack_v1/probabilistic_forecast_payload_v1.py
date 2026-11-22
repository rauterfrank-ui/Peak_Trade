"""Typed probabilistic forecast payload grammar v1 (research evidence only)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
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


def _require_probability(value: Any, *, field: str, range_error: str) -> float:
    # Compare original decimal text before float conversion can round it onto a bound.
    # Validation never rewrites the payload or its existing digest representation.
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise DdoValidationError(f"FORECAST_PROBABILITY_MUST_BE_NUMERIC:{field}")
    try:
        probability = Decimal(str(value))
        if not probability.is_finite():
            raise DdoValidationError(f"FORECAST_PROBABILITY_MUST_BE_FINITE:{field}")
        if probability < 0 or probability > 1:
            raise DdoValidationError(range_error)
        # Keep the original consumer's numeric syntax and conversion as well.
        return float(value)
    except (InvalidOperation, ValueError, OverflowError) as exc:
        raise DdoValidationError(f"FORECAST_PROBABILITY_MUST_BE_NUMERIC:{field}") from exc


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
        probabilities = tuple(
            _require_probability(
                body[key], field=key, range_error=f"DIRECTIONAL_PROBABILITY_OUT_OF_RANGE:{key}"
            )
            for key in ("p_up", "p_down", "p_flat")
        )
        total = probabilities[0] + probabilities[1] + probabilities[2]
        if abs(total - 1.0) > 1e-9:
            raise DdoValidationError("DIRECTIONAL_PROBABILITIES_MUST_SUM_TO_ONE")
    elif forecast_kind == FORECAST_KIND_RETURN_DISTRIBUTION_SUMMARY:
        for key in ("mean_return", "std_return"):
            if key not in body:
                raise DdoValidationError(f"FORECAST_PAYLOAD_MISSING:{key}")
    elif forecast_kind == FORECAST_KIND_THRESHOLD_EVENT_PROBABILITY:
        if "threshold" not in body or "p_event" not in body:
            raise DdoValidationError("THRESHOLD_EVENT_PAYLOAD_INCOMPLETE")
        _require_probability(
            body["p_event"],
            field="p_event",
            range_error="THRESHOLD_EVENT_PROBABILITY_OUT_OF_RANGE",
        )
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
