"""REALIZED_BEHAVIOR_V1 — typed outcome view bound to MARKET_CONTEXT_V1 (AUTHORITY=NONE).

Consumes Phase 19 MARKET_CONTEXT_V1 and canonical N_BARS evaluation/measurement evidence.
Does not mint actual_outcome_ref, mutate N_BARS SSOT, or grant trading authority.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    require_event_time_utc,
    require_mapping,
    require_record_id,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_observation_v0 import (
    validate_evaluation_observation_v0,
)
from src.learning.deterministic_decision_outcome_v0.n_bars_bar_evidence_supplier_v1 import (
    MEASUREMENT_SCHEMA_NAME,
    MEASUREMENT_SCHEMA_VERSION,
    N_BARS_BAR_EVIDENCE_SUPPLIER_ID,
)
from src.learning.deterministic_decision_outcome_v0.o4_n_bars_bar_evidence_bridge_contracts_v1 import (
    mint_ddo_content_ref_v1,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_contracts_v1 import (
    REAL_OUTCOME_HORIZON_V1_REAL_CAPABLE_TOKEN,
    require_positive_int,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import compute_content_hash_v0
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    FORECAST_IS_NOT_DECISION,
    NO_DUPLICATE_OUTCOME_TRUTH,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_v1 import (
    MARKET_CONTEXT_AUTHORITY,
    N_BARS_BACKBONE_TOKEN,
    validate_market_context_v1,
)

SCHEMA_VERSION: Final[str] = "realized_behavior_v1"
REALIZED_BEHAVIOR_AUTHORITY: Final[str] = "NONE"
JOIN_OWNER: Final[str] = (
    "learning.market_intelligence_forecast_calibration_offline_stack_v1.realized_behavior_v1"
)
N_BARS_OUTCOME_OWNER: Final[str] = "peak_trade.learning.ddo.real_outcome_horizon_engine_v1"

CLOSE_PATH_EXCURSION_KIND: Final[str] = "CLOSE_PATH_DIRECTION_NEUTRAL"
REALIZED_VOL_ESTIMATOR_ID: Final[str] = "close_to_close_log_return_sample_std_v1"
TRANSITION_UNRESOLVED_REASON: Final[str] = "NO_AUTHORITATIVE_REGIME_OWNER_FOR_MI_JOIN"

MFE_MAE_CLASSICAL_UNAVAILABLE_REASON: Final[str] = (
    "O4_BAR_CONTRACT_CLOSE_ONLY_NO_HIGH_LOW_FOR_CLASSICAL_MFE_MAE"
)


class RealizedBehaviorError(ValueError):
    """Fail-closed realized behavior join."""


def _decimal_text(value: float) -> str:
    if not math.isfinite(value):
        raise RealizedBehaviorError("NON_FINITE_DECIMAL")
    return format(value, ".12g")


@dataclass(frozen=True)
class RealizedBehaviorJoinInputsV1:
    market_context: Mapping[str, Any]
    evaluation_observation: Mapping[str, Any]
    measurement_evidence: Mapping[str, Any] | None = None
    o4_bars_for_path: Sequence[Mapping[str, Any]] | None = None
    forecast_evidence_id: str | None = None


def _parse_utc_ms(value: str) -> float:
    text = require_event_time_utc(value, "utc")
    from datetime import datetime, timezone

    dt = datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    return dt.timestamp()


def _assert_temporal_integrity_v1(
    *,
    context: Mapping[str, Any],
    observation: Mapping[str, Any],
    measurement: Mapping[str, Any] | None,
    o4_bars: Sequence[Mapping[str, Any]] | None,
) -> None:
    context_t = _parse_utc_ms(str(context["observed_at"]))
    horizon_start = observation.get("horizon_start_time_utc")
    if horizon_start is not None:
        if _parse_utc_ms(str(horizon_start)) < context_t:
            raise RealizedBehaviorError("CONTEXT_OBSERVED_AFTER_HORIZON_START")
    eval_time = require_event_time_utc(
        observation.get("evaluation_time_utc"), "evaluation_time_utc"
    )
    if _parse_utc_ms(eval_time) < context_t:
        raise RealizedBehaviorError("CONTEXT_OBSERVED_AFTER_OUTCOME_END")

    closes = observation.get("bar_close_times_utc")
    if isinstance(closes, list) and closes:
        last_close = require_event_time_utc(closes[-1], "bar_close_times_utc[-1]")
        if _parse_utc_ms(last_close) > _parse_utc_ms(eval_time):
            raise RealizedBehaviorError("EVAL_TIME_BEFORE_LAST_BAR_CLOSE")

    if measurement is not None:
        meas_eval = measurement.get("evaluation_time_utc")
        if meas_eval is not None and str(meas_eval) != eval_time:
            raise RealizedBehaviorError("MEASUREMENT_EVAL_TIME_MISMATCH")

    if o4_bars is not None and closes:
        boundary = _parse_utc_ms(eval_time)
        for index, bar in enumerate(o4_bars):
            identity = require_mapping(
                bar.get("last_observation_identity"), f"o4_bars[{index}].last_observation_identity"
            )
            vet = identity.get("venue_event_time")
            if vet is None:
                raise RealizedBehaviorError(f"O4_BAR_PIT_TIME_MISSING:{index}")
            if isinstance(vet, (int, float)) and not isinstance(vet, bool):
                obs_ms = float(vet)
            elif isinstance(vet, str):
                obs_ms = _parse_utc_ms(require_event_time_utc(vet, "venue_event_time"))
            else:
                raise RealizedBehaviorError(f"O4_BAR_PIT_TIME_INVALID:{index}")
            if obs_ms > boundary:
                raise RealizedBehaviorError("O4_BAR_POST_OUTCOME_BOUNDARY_LEAKAGE")


def _materialize_forward_behavior_v1(
    *,
    observation: Mapping[str, Any],
    measurement: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    status = str(observation.get("horizon_observation_status"))
    if status != "OK":
        return {
            "status": "UNAVAILABLE",
            "reason": f"HORIZON_OBSERVATION_{status}",
            "outcome_scalar_kind": observation.get("outcome_scalar_kind"),
        }
    if measurement is None:
        return {
            "status": "UNAVAILABLE",
            "reason": "MEASUREMENT_EVIDENCE_REQUIRED_FOR_FORWARD_BEHAVIOR",
            "outcome_scalar_kind": observation.get("outcome_scalar_kind"),
        }
    if measurement.get("schema_name") != MEASUREMENT_SCHEMA_NAME:
        raise RealizedBehaviorError("MEASUREMENT_SCHEMA_NAME_MISMATCH")
    if measurement.get("schema_version") != MEASUREMENT_SCHEMA_VERSION:
        raise RealizedBehaviorError("MEASUREMENT_SCHEMA_VERSION_MISMATCH")
    if str(measurement.get("measurement_producer_id")) != N_BARS_BAR_EVIDENCE_SUPPLIER_ID:
        raise RealizedBehaviorError("MEASUREMENT_PRODUCER_NOT_CANONICAL")

    scalar = str(measurement.get("outcome_scalar_kind"))
    body: dict[str, Any] = {
        "status": "PROVEN_TYPED",
        "outcome_scalar_kind": scalar,
        "price_basis_kind": measurement.get("price_basis_kind"),
        "start_price": _decimal_text(float(measurement.get("start_price"))),
        "end_price": _decimal_text(float(measurement.get("end_price"))),
        "start_bar_identity_ref": measurement.get("start_bar_identity_ref"),
        "end_bar_identity_ref": measurement.get("end_bar_identity_ref"),
        "actual_outcome_ref": measurement.get("actual_outcome_ref")
        or observation.get("actual_outcome_ref"),
    }
    if scalar == "LOG_RETURN":
        if measurement.get("log_return") is None:
            raise RealizedBehaviorError("LOG_RETURN_MISSING")
        body["forward_return"] = {
            "kind": "LOG_RETURN",
            "value": _decimal_text(float(measurement.get("log_return"))),
        }
    elif scalar == "ABS_RETURN":
        if measurement.get("abs_return") is None:
            raise RealizedBehaviorError("ABS_RETURN_MISSING")
        body["forward_return"] = {
            "kind": "ABS_RETURN",
            "value": _decimal_text(float(measurement.get("abs_return"))),
        }
    elif scalar == "HIT_TARGET":
        for field in ("target_value", "comparator", "hit_result", "compared_price"):
            if field not in measurement:
                raise RealizedBehaviorError(f"HIT_TARGET_FIELD_MISSING:{field}")
        body["forward_return"] = {
            "kind": "HIT_TARGET",
            "target_value": _decimal_text(float(measurement.get("target_value"))),
            "comparator": measurement.get("comparator"),
            "hit_result": measurement.get("hit_result"),
            "compared_price": _decimal_text(float(measurement.get("compared_price"))),
        }
    else:
        body["status"] = "UNAVAILABLE"
        body["reason"] = f"UNSUPPORTED_SCALAR:{scalar}"
    return body


def _o4_bar_identity_ref_v1(bar: Mapping[str, Any]) -> str:
    open_t = float(bar["bar_open_time"])
    return mint_ddo_content_ref_v1(
        prefix="ddo.o4.bar.",
        payload={
            "canonical_instrument_id": str(bar["canonical_instrument_id"]),
            "interval": str(bar["interval"]),
            "bar_open_time": format(open_t, ".12g"),
            "revision": int(bar["revision"]),
        },
    )


def _ordered_closes_from_o4_v1(
    *,
    o4_bars: Sequence[Mapping[str, Any]],
    bar_identity_refs: Sequence[str] | None,
) -> tuple[float, ...]:
    if not o4_bars:
        return ()
    by_id = {_o4_bar_identity_ref_v1(bar): bar for bar in o4_bars}
    if bar_identity_refs:
        ordered: list[float] = []
        for ref in bar_identity_refs:
            matched = by_id.get(str(ref))
            if matched is None:
                raise RealizedBehaviorError(f"O4_BAR_IDENTITY_UNRESOLVED:{ref}")
            ordered.append(float(matched["close"]))
        return tuple(ordered)
    sorted_bars = sorted(o4_bars, key=lambda b: float(b["bar_open_time"]))
    return tuple(float(b["close"]) for b in sorted_bars)


def _materialize_excursion_v1(
    *,
    observation: Mapping[str, Any],
    measurement: Mapping[str, Any] | None,
    o4_bars: Sequence[Mapping[str, Any]] | None,
) -> Mapping[str, Any]:
    status = str(observation.get("horizon_observation_status"))
    if status != "OK":
        return {"status": "UNAVAILABLE", "reason": f"HORIZON_OBSERVATION_{status}"}
    if measurement is None or o4_bars is None:
        return {
            "status": "UNAVAILABLE",
            "reason": "MEASUREMENT_AND_O4_BARS_REQUIRED_FOR_CLOSE_PATH_EXCURSION",
            "classical_mfe_mae": {
                "status": "SEMANTICALLY_UNRESOLVED",
                "reason": MFE_MAE_CLASSICAL_UNAVAILABLE_REASON,
            },
        }
    start_price = measurement.get("start_price")
    if start_price is None or float(start_price) <= 0:
        raise RealizedBehaviorError("EXCURSION_START_PRICE_INVALID")
    refs = observation.get("bar_identity_refs")
    bar_refs = tuple(str(r) for r in refs) if isinstance(refs, list) else None
    closes = _ordered_closes_from_o4_v1(o4_bars=o4_bars, bar_identity_refs=bar_refs)
    if not closes:
        return {"status": "UNAVAILABLE", "reason": "NO_CLOSES_IN_OUTCOME_WINDOW"}

    start = float(start_price)
    rel_moves = [(c - start) / start for c in closes]
    max_up = max(rel_moves)
    max_down = min(rel_moves)
    return {
        "status": "PROVEN_TYPED",
        "excursion_kind": CLOSE_PATH_EXCURSION_KIND,
        "reference_price": _decimal_text(start),
        "reference_price_semantic": "MEASUREMENT_START_BAR_CLOSE",
        "outcome_interval_closes": [_decimal_text(c) for c in closes],
        "max_up_fraction_from_reference": _decimal_text(max_up),
        "max_down_fraction_from_reference": _decimal_text(max_down),
        "classical_mfe_mae": {
            "status": "SEMANTICALLY_UNRESOLVED",
            "reason": MFE_MAE_CLASSICAL_UNAVAILABLE_REASON,
        },
    }


def _materialize_realized_volatility_v1(
    *,
    observation: Mapping[str, Any],
    o4_bars: Sequence[Mapping[str, Any]] | None,
) -> Mapping[str, Any]:
    status = str(observation.get("horizon_observation_status"))
    if status != "OK":
        return {"status": "UNAVAILABLE", "reason": f"HORIZON_OBSERVATION_{status}"}
    if o4_bars is None:
        return {"status": "UNAVAILABLE", "reason": "O4_BARS_REQUIRED_FOR_REALIZED_VOLATILITY"}
    refs = observation.get("bar_identity_refs")
    bar_refs = tuple(str(r) for r in refs) if isinstance(refs, list) else None
    closes = _ordered_closes_from_o4_v1(o4_bars=o4_bars, bar_identity_refs=bar_refs)
    n_bars = require_positive_int(observation.get("n_bars"), "n_bars")
    if len(closes) < n_bars:
        return {
            "status": "UNAVAILABLE",
            "reason": "INSUFFICIENT_CLOSE_COVERAGE",
            "minimum_returns_required": 2,
            "closes_available": len(closes),
        }
    log_returns: list[float] = []
    for prev, curr in zip(closes, closes[1:], strict=False):
        if prev <= 0 or curr <= 0:
            return {"status": "UNAVAILABLE", "reason": "NON_POSITIVE_CLOSE_FOR_LOG_RETURN"}
        log_returns.append(math.log(curr / prev))
    if len(log_returns) < 1:
        return {"status": "UNAVAILABLE", "reason": "INSUFFICIENT_RETURNS_FOR_VOLATILITY"}
    mean = sum(log_returns) / len(log_returns)
    var = sum((r - mean) ** 2 for r in log_returns) / len(log_returns)
    return {
        "status": "PROVEN_TYPED",
        "estimator_id": REALIZED_VOL_ESTIMATOR_ID,
        "observation_frequency": str(observation.get("bar_spec_ref")),
        "window_bars": n_bars,
        "returns_count": len(log_returns),
        "minimum_coverage_met": len(log_returns) >= 1,
        "realized_volatility": _decimal_text(math.sqrt(var)),
        "volatility_tails": {
            "status": "SEMANTICALLY_UNRESOLVED",
            "reason": "NO_CANONICAL_TAIL_SHOCK_DEFINITION",
        },
    }


def _materialize_transition_v1() -> Mapping[str, Any]:
    return {
        "status": "SEMANTICALLY_UNRESOLVED",
        "reason": TRANSITION_UNRESOLVED_REASON,
    }


def derive_behavior_id_v1(*, identity_body: Mapping[str, Any]) -> str:
    digest = compute_content_hash_v0(dict(identity_body))
    return f"mi.realized_behavior.{digest[:48]}"


def join_market_context_to_realized_behavior_v1(
    inputs: RealizedBehaviorJoinInputsV1,
) -> MappingProxyType[str, Any]:
    """MARKET_CONTEXT(t) + N_BARS outcome → REALIZED_BEHAVIOR(t+N); reference-only."""
    context = validate_market_context_v1(inputs.market_context)
    observation = validate_evaluation_observation_v0(inputs.evaluation_observation)
    if str(observation.get("evaluation_horizon")) != REAL_OUTCOME_HORIZON_V1_REAL_CAPABLE_TOKEN:
        raise RealizedBehaviorError("EVALUATION_HORIZON_MUST_BE_N_BARS")

    measurement = (
        require_mapping(inputs.measurement_evidence, "measurement_evidence")
        if inputs.measurement_evidence is not None
        else None
    )
    o4_bars = tuple(inputs.o4_bars_for_path) if inputs.o4_bars_for_path is not None else None

    _assert_temporal_integrity_v1(
        context=context,
        observation=observation,
        measurement=measurement,
        o4_bars=o4_bars,
    )

    obs_instrument = observation.get("instrument_ref")
    if obs_instrument is not None and str(obs_instrument) != str(context["instrument_ref"]):
        raise RealizedBehaviorError("INSTRUMENT_REF_MISMATCH")

    n_bars = require_positive_int(observation.get("n_bars"), "n_bars")
    horizon_identity = {
        "evaluation_horizon": REAL_OUTCOME_HORIZON_V1_REAL_CAPABLE_TOKEN,
        "n_bars": n_bars,
        "bar_spec_ref": str(observation.get("bar_spec_ref")),
        "horizon_start_time_utc": observation.get("horizon_start_time_utc"),
        "evaluation_time_utc": observation.get("evaluation_time_utc"),
    }
    outcome_window = {
        "horizon_start_time_utc": observation.get("horizon_start_time_utc"),
        "evaluation_time_utc": observation.get("evaluation_time_utc"),
        "bar_close_times_utc": observation.get("bar_close_times_utc"),
        "bar_identity_refs": observation.get("bar_identity_refs"),
        "horizon_observation_status": observation.get("horizon_observation_status"),
        "horizon_observation_reason": observation.get("horizon_observation_reason"),
    }

    forward_behavior = _materialize_forward_behavior_v1(
        observation=observation, measurement=measurement
    )
    excursion = _materialize_excursion_v1(
        observation=observation, measurement=measurement, o4_bars=o4_bars
    )
    realized_volatility = _materialize_realized_volatility_v1(
        observation=observation, o4_bars=o4_bars
    )
    transition = _materialize_transition_v1()

    actual_ref = observation.get("actual_outcome_ref")
    provenance_refs = [
        str(context["context_id"]),
        str(context["information_set_ref"]),
    ]
    if actual_ref is not None:
        provenance_refs.append(str(actual_ref))
    if measurement is not None and measurement.get("actual_outcome_ref"):
        provenance_refs.append(str(measurement["actual_outcome_ref"]))
    if inputs.forecast_evidence_id:
        provenance_refs.append(str(inputs.forecast_evidence_id))

    feature_versions = {
        "realized_behavior_v1": SCHEMA_VERSION,
        "market_context_v1": str(context["schema_version"]),
        "n_bars_outcome_owner": N_BARS_OUTCOME_OWNER,
    }

    identity_body = {
        "schema_version": SCHEMA_VERSION,
        "market_context_ref": str(context["context_id"]),
        "instrument_ref": str(context["instrument_ref"]),
        "information_set_ref": str(context["information_set_ref"]),
        "observed_at": str(context["observed_at"]),
        "horizon_identity": horizon_identity,
        "outcome_window": outcome_window,
        "forward_behavior": forward_behavior,
        "excursion": excursion,
        "realized_volatility": realized_volatility,
        "transition": transition,
        "actual_outcome_ref": actual_ref,
        "provenance_refs": tuple(sorted(set(provenance_refs))),
        "feature_versions": feature_versions,
    }
    behavior_id = derive_behavior_id_v1(identity_body=identity_body)
    content_digest = compute_content_hash_v0(identity_body)

    record = {
        **identity_body,
        "behavior_id": behavior_id,
        "market_context_ref": str(context["context_id"]),
        "quality_state": {
            "join_status": "JOINED"
            if str(observation.get("horizon_observation_status")) == "OK"
            else "OUTCOME_INCOMPLETE",
            "market_context_authority": MARKET_CONTEXT_AUTHORITY,
            "realized_behavior_authority": REALIZED_BEHAVIOR_AUTHORITY,
            "n_bars_backbone_semantics": N_BARS_BACKBONE_TOKEN,
            "no_duplicate_outcome_truth": NO_DUPLICATE_OUTCOME_TRUTH,
            "outcome_fields_mutated": False,
        },
        "provenance_refs": list(identity_body["provenance_refs"]),
        "content_digest": content_digest,
        "realized_behavior_authority": REALIZED_BEHAVIOR_AUTHORITY,
        "n_bars_outcome_owner": N_BARS_OUTCOME_OWNER,
        "forecast_is_not_decision": FORECAST_IS_NOT_DECISION,
    }
    expected_id = derive_behavior_id_v1(identity_body=identity_body)
    if record["behavior_id"] != expected_id:
        raise RealizedBehaviorError("BEHAVIOR_ID_MISMATCH")
    return MappingProxyType(record)


def assert_realized_behavior_authority_invariants_v1() -> Mapping[str, Any]:
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
        EXTERNAL_EFFECT_AUTHORIZED,
        LEARNING_TRADING_AUTHORITY,
        MARKET_INTELLIGENCE_TRADING_AUTHORITY,
        MULTI_FUTURE_RUNTIME_AUTHORIZED,
        NO_AUTOMATIC_PROMOTION,
        NO_NEW_EXTERNAL_EFFECT_PATH,
        OPTIMIZATION_PRODUCTIVE_AUTHORITY,
    )

    terminal = {
        "MARKET_CONTEXT_AUTHORITY": MARKET_CONTEXT_AUTHORITY,
        "REALIZED_BEHAVIOR_AUTHORITY": REALIZED_BEHAVIOR_AUTHORITY,
        "FORECAST_IS_NOT_DECISION": FORECAST_IS_NOT_DECISION,
        "CROSS_MARKET_IS_CONTEXT_ONLY": True,
        "MV2_DP_UNCHANGED": True,
        "NO_SECOND_MARKET_TRUTH": True,
        "NO_AUTHORITY_EXPANSION": True,
        "NO_DUPLICATE_OUTCOME_TRUTH": NO_DUPLICATE_OUTCOME_TRUTH,
        "LEARNING_TRADING_AUTHORITY": LEARNING_TRADING_AUTHORITY,
        "MARKET_INTELLIGENCE_TRADING_AUTHORITY": MARKET_INTELLIGENCE_TRADING_AUTHORITY,
        "EXTERNAL_EFFECT_AUTHORIZED": EXTERNAL_EFFECT_AUTHORIZED,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "NO_AUTOMATIC_PROMOTION": NO_AUTOMATIC_PROMOTION,
        "OPTIMIZATION_PRODUCTIVE_AUTHORITY": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "NO_NEW_EXTERNAL_EFFECT_PATH": NO_NEW_EXTERNAL_EFFECT_PATH,
        "RUNTIME_APPLY_AUTHORIZED": False,
        "PRODUCTIVE_ORDER_PATH": False,
    }
    if terminal["REALIZED_BEHAVIOR_AUTHORITY"] != "NONE":
        raise RealizedBehaviorError("AUTHORITY_EXPANSION_FORBIDDEN")
    if terminal["MARKET_CONTEXT_AUTHORITY"] != "NONE":
        raise RealizedBehaviorError("MARKET_CONTEXT_AUTHORITY_EXPANSION_FORBIDDEN")
    if terminal["EXTERNAL_EFFECT_AUTHORIZED"] is not False:
        raise RealizedBehaviorError("EXTERNAL_EFFECT_FORBIDDEN")
    return MappingProxyType(terminal)


__all__ = [
    "CLOSE_PATH_EXCURSION_KIND",
    "JOIN_OWNER",
    "REALIZED_BEHAVIOR_AUTHORITY",
    "RealizedBehaviorError",
    "RealizedBehaviorJoinInputsV1",
    "SCHEMA_VERSION",
    "assert_realized_behavior_authority_invariants_v1",
    "derive_behavior_id_v1",
    "join_market_context_to_realized_behavior_v1",
]
