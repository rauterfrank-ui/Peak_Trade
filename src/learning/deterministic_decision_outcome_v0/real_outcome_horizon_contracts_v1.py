"""S2 fail-closed REAL N_BARS horizon contracts (DDO Real Outcome Horizon S1 binding).

Normative authority:
docs/ops/specs/DDO_REAL_OUTCOME_EVALUATION_HORIZON_NORMATIVE_SEMANTICS_V1.md

Does not confer trading, capture, runtime, or promotion authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    REF_OR_UNKNOWN_RE,
    require_enum,
    require_event_time_utc,
    require_mapping,
    require_record_id,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    HORIZON_OBSERVATION_STATUS_V0,
    OUTCOME_SCALAR_KIND_V0,
    UNKNOWN,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError

REAL_OUTCOME_HORIZON_V1_REAL_CAPABLE_TOKEN: Final[str] = "N_BARS"

DEFERRED_REAL_EVALUATION_HORIZONS_V1: Final[frozenset[str]] = frozenset(
    {
        "IMMEDIATE_POST_EVENT",
        "EVENT_RECOVERY",
        "POSITION_LIFECYCLE",
    }
)

N_BARS_OBSERVATION_FIELD_NAMES_V1: Final[frozenset[str]] = frozenset(
    {
        "horizon_start_time_utc",
        "instrument_ref",
        "bar_spec_ref",
        "n_bars",
        "horizon_observation_status",
        "horizon_observation_reason",
        "outcome_scalar_kind",
        "bar_close_times_utc",
        "bar_identity_refs",
    }
)

SUPPLIER_MINTS_ACTUAL_OUTCOME_REF: Final[bool] = False
SUPPLIER_COMPUTES_ECONOMIC_SCORE: Final[bool] = False
REAL_OUTCOME_HORIZON_ENGINE_WIRED: Final[bool] = False
EVALUATION_RUNTIME_WIRING: Final[bool] = False


def require_opaque_ref(value: Any, field: str) -> str:
    if not isinstance(value, str) or value == UNKNOWN or not REF_OR_UNKNOWN_RE.fullmatch(value):
        raise DdoValidationError(f"INVALID_REF:{field}")
    return value


def require_positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DdoValidationError(f"INVALID_POSITIVE_INT:{field}")
    if value <= 0:
        raise DdoValidationError(f"N_BARS_MUST_BE_POSITIVE:{field}")
    return value


def validate_bar_close_chain_v1(
    *,
    horizon_start_time_utc: str,
    n_bars: int,
    bar_close_times_utc: Any,
) -> tuple[str, ...]:
    """Machine-check UTC closes: count == N, strict increase, anchor vs horizon_start."""
    if not isinstance(bar_close_times_utc, list):
        raise DdoValidationError("BAR_CLOSE_TIMES_MUST_BE_LIST")
    if len(bar_close_times_utc) != n_bars:
        raise DdoValidationError("BAR_CLOSE_COUNT_MISMATCH")
    normalized: list[str] = []
    previous: str | None = None
    for index, item in enumerate(bar_close_times_utc):
        close = require_event_time_utc(item, f"bar_close_times_utc[{index}]")
        if index == 0 and close < horizon_start_time_utc:
            raise DdoValidationError("HORIZON_START_AFTER_FIRST_BAR_CLOSE")
        if previous is not None and close <= previous:
            raise DdoValidationError("BAR_CLOSE_CHAIN_NOT_STRICTLY_INCREASING")
        normalized.append(close)
        previous = close
    return tuple(normalized)


def validate_bar_identity_refs_v1(
    *,
    n_bars: int,
    bar_identity_refs: Any,
) -> tuple[str, ...] | None:
    if bar_identity_refs is None:
        return None
    if not isinstance(bar_identity_refs, list):
        raise DdoValidationError("BAR_IDENTITY_REFS_MUST_BE_LIST")
    if len(bar_identity_refs) != n_bars:
        raise DdoValidationError("BAR_IDENTITY_REF_COUNT_MISMATCH")
    seen: set[str] = set()
    out: list[str] = []
    for index, item in enumerate(bar_identity_refs):
        ident = require_opaque_ref(item, f"bar_identity_refs[{index}]")
        if ident in seen:
            raise DdoValidationError(f"BAR_IDENTITY_REF_DUPLICATE:{ident}")
        seen.add(ident)
        out.append(ident)
    return tuple(out)


def assert_no_n_bars_fields_on_non_n_bars_horizon_v1(
    evaluation_horizon: str,
    raw: Mapping[str, Any],
) -> None:
    if evaluation_horizon == REAL_OUTCOME_HORIZON_V1_REAL_CAPABLE_TOKEN:
        return
    present = sorted(
        name for name in N_BARS_OBSERVATION_FIELD_NAMES_V1 if raw.get(name) is not None
    )
    if present:
        raise DdoValidationError(
            f"N_BARS_FIELDS_NOT_ALLOWED_FOR_HORIZON:{evaluation_horizon}:{present}"
        )


def assert_deferred_horizon_rejects_real_fields_v1(
    evaluation_horizon: str,
    *,
    actual_outcome_ref: str | None,
) -> None:
    if evaluation_horizon not in DEFERRED_REAL_EVALUATION_HORIZONS_V1:
        return
    if actual_outcome_ref is not None and actual_outcome_ref != UNKNOWN:
        raise DdoValidationError(f"DEFERRED_HORIZON_REAL_OUTCOME_REF_REJECTED:{evaluation_horizon}")


@dataclass(frozen=True)
class NBarsRealEligibilityV1:
    real_claim_eligible: bool
    horizon_observation_status: str
    horizon_observation_reason: str | None
    actual_outcome_ref: str
    economic_score: str | None


def classify_n_bars_real_eligibility_v1(
    observation: Mapping[str, Any],
) -> NBarsRealEligibilityV1:
    status = observation.get("horizon_observation_status")
    if status is None:
        raise DdoValidationError("HORIZON_OBSERVATION_STATUS_REQUIRED_FOR_N_BARS")
    if status not in HORIZON_OBSERVATION_STATUS_V0:
        raise DdoValidationError(f"UNKNOWN_ENUM_VALUE:horizon_observation_status:{status!r}")

    reason = observation.get("horizon_observation_reason")
    if reason is not None and not isinstance(reason, str):
        raise DdoValidationError("HORIZON_OBSERVATION_REASON_MUST_BE_STRING")

    economic_score = observation.get("economic_score")
    actual_ref = observation.get("actual_outcome_ref")

    if status != "OK":
        resolved_actual = UNKNOWN
        if actual_ref is not None and actual_ref != UNKNOWN:
            resolved_actual = UNKNOWN
        return NBarsRealEligibilityV1(
            real_claim_eligible=False,
            horizon_observation_status=status,
            horizon_observation_reason=reason if isinstance(reason, str) else None,
            actual_outcome_ref=resolved_actual,
            economic_score=economic_score,
        )

    horizon_start = require_event_time_utc(
        observation.get("horizon_start_time_utc"), "horizon_start_time_utc"
    )
    n_bars = require_positive_int(observation.get("n_bars"), "n_bars")
    require_opaque_ref(observation.get("instrument_ref"), "instrument_ref")
    require_opaque_ref(observation.get("bar_spec_ref"), "bar_spec_ref")
    require_enum(
        observation.get("outcome_scalar_kind"),
        "outcome_scalar_kind",
        OUTCOME_SCALAR_KIND_V0,
    )
    eval_info = observation.get("evaluation_time_information_set_ref")
    if eval_info is None or eval_info == UNKNOWN:
        raise DdoValidationError("EVALUATION_TIME_INFORMATION_SET_REF_REQUIRED_FOR_REAL_N_BARS")
    require_record_id(eval_info, "evaluation_time_information_set_ref")

    if actual_ref is None or actual_ref == UNKNOWN:
        raise DdoValidationError("ACTUAL_OUTCOME_REF_REQUIRED_FOR_OK_N_BARS")

    validate_bar_close_chain_v1(
        horizon_start_time_utc=horizon_start,
        n_bars=n_bars,
        bar_close_times_utc=observation.get("bar_close_times_utc"),
    )
    validate_bar_identity_refs_v1(
        n_bars=n_bars,
        bar_identity_refs=observation.get("bar_identity_refs"),
    )

    return NBarsRealEligibilityV1(
        real_claim_eligible=True,
        horizon_observation_status=status,
        horizon_observation_reason=reason if isinstance(reason, str) else None,
        actual_outcome_ref=str(actual_ref),
        economic_score=economic_score,
    )


def validate_n_bars_observation_for_decision_v1(
    decision_event: Mapping[str, Any],
    observation: Mapping[str, Any],
) -> NBarsRealEligibilityV1:
    decision_time = require_event_time_utc(decision_event["event_time_utc"], "event_time_utc")
    horizon_start = observation.get("horizon_start_time_utc")
    if horizon_start is not None:
        start = require_event_time_utc(horizon_start, "horizon_start_time_utc")
        if start < decision_time:
            raise DdoValidationError("HORIZON_START_BEFORE_DECISION_EVENT")
    return classify_n_bars_real_eligibility_v1(observation)


def resolve_later_horizon_outcome_fields_v1(
    observation: Mapping[str, Any],
    *,
    decision_event: Mapping[str, Any] | None = None,
) -> tuple[str, str | None]:
    """Map observation to outcome actual_outcome_ref and economic_score (fail-closed REAL)."""
    horizon = str(observation["evaluation_horizon"])
    economic_score = observation.get("economic_score")
    if economic_score is None:
        economic_score = UNKNOWN

    if horizon in {"DECISION_TIME", UNKNOWN}:
        return UNKNOWN, UNKNOWN

    if horizon in DEFERRED_REAL_EVALUATION_HORIZONS_V1:
        assert_deferred_horizon_rejects_real_fields_v1(
            horizon,
            actual_outcome_ref=observation.get("actual_outcome_ref"),
        )
        return UNKNOWN, economic_score if economic_score != UNKNOWN else UNKNOWN

    if horizon == REAL_OUTCOME_HORIZON_V1_REAL_CAPABLE_TOKEN:
        if decision_event is None:
            raise DdoValidationError("DECISION_EVENT_REQUIRED_FOR_N_BARS_RESOLUTION")
        eligibility = validate_n_bars_observation_for_decision_v1(decision_event, observation)
        if not eligibility.real_claim_eligible:
            return UNKNOWN, eligibility.economic_score if eligibility.economic_score else UNKNOWN
        return eligibility.actual_outcome_ref, eligibility.economic_score

    actual = observation.get("actual_outcome_ref")
    if actual is None:
        actual = UNKNOWN
    return str(actual), economic_score


def normalize_n_bars_extension_fields_v1(
    raw: Mapping[str, Any],
) -> dict[str, Any]:
    """Canonicalize optional N_BARS extension fields for evaluation_observation_v0."""
    n_bars_raw = raw.get("n_bars")
    n_bars: int | None
    if n_bars_raw is None:
        n_bars = None
    else:
        n_bars = require_positive_int(n_bars_raw, "n_bars")

    bar_closes = raw.get("bar_close_times_utc")
    bar_closes_norm: tuple[str, ...] | None = None
    if bar_closes is not None:
        if n_bars is None:
            raise DdoValidationError("N_BARS_REQUIRED_WHEN_BAR_CLOSE_TIMES_PRESENT")
        bar_closes_norm = validate_bar_close_chain_v1(
            horizon_start_time_utc=require_event_time_utc(
                raw.get("horizon_start_time_utc"), "horizon_start_time_utc"
            ),
            n_bars=n_bars,
            bar_close_times_utc=bar_closes,
        )

    bar_ids = validate_bar_identity_refs_v1(
        n_bars=n_bars if n_bars is not None else 0,
        bar_identity_refs=raw.get("bar_identity_refs"),
    )
    if raw.get("bar_identity_refs") is not None and n_bars is None:
        raise DdoValidationError("N_BARS_REQUIRED_WHEN_BAR_IDENTITY_REFS_PRESENT")

    status = raw.get("horizon_observation_status")
    status_norm: str | None = None
    if status is not None:
        status_norm = require_enum(
            status, "horizon_observation_status", HORIZON_OBSERVATION_STATUS_V0
        )

    scalar_kind = raw.get("outcome_scalar_kind")
    scalar_norm: str | None = None
    if scalar_kind is not None:
        scalar_norm = require_enum(scalar_kind, "outcome_scalar_kind", OUTCOME_SCALAR_KIND_V0)

    reason = raw.get("horizon_observation_reason")
    if reason is not None and not isinstance(reason, str):
        raise DdoValidationError("HORIZON_OBSERVATION_REASON_MUST_BE_STRING")

    horizon_start: str | None = None
    if raw.get("horizon_start_time_utc") is not None:
        horizon_start = require_event_time_utc(
            raw.get("horizon_start_time_utc"), "horizon_start_time_utc"
        )

    instrument: str | None = None
    if raw.get("instrument_ref") is not None:
        instrument = require_opaque_ref(raw.get("instrument_ref"), "instrument_ref")

    bar_spec: str | None = None
    if raw.get("bar_spec_ref") is not None:
        bar_spec = require_opaque_ref(raw.get("bar_spec_ref"), "bar_spec_ref")

    return {
        "horizon_start_time_utc": horizon_start,
        "instrument_ref": instrument,
        "bar_spec_ref": bar_spec,
        "n_bars": n_bars,
        "horizon_observation_status": status_norm,
        "horizon_observation_reason": reason if isinstance(reason, str) else None,
        "outcome_scalar_kind": scalar_norm,
        "bar_close_times_utc": None if bar_closes_norm is None else list(bar_closes_norm),
        "bar_identity_refs": None if bar_ids is None else list(bar_ids),
    }


def validate_real_outcome_horizon_supplier_input_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    """Validate offline supplier input bundle (does not mint measurement refs)."""
    raw = require_mapping(payload, "real_outcome_horizon_supplier_input")
    normalized = normalize_n_bars_extension_fields_v1(raw)
    for field in (
        "horizon_start_time_utc",
        "instrument_ref",
        "bar_spec_ref",
        "n_bars",
        "horizon_observation_status",
        "outcome_scalar_kind",
    ):
        if normalized.get(field) is None:
            raise DdoValidationError(f"SUPPLIER_INPUT_MISSING:{field}")
    if raw.get("actual_outcome_ref") is None:
        raise DdoValidationError("SUPPLIER_INPUT_MISSING:actual_outcome_ref")
    require_opaque_ref(raw.get("actual_outcome_ref"), "actual_outcome_ref")
    if raw.get("evaluation_time_information_set_ref") is None:
        raise DdoValidationError("SUPPLIER_INPUT_MISSING:evaluation_time_information_set_ref")
    require_record_id(
        raw.get("evaluation_time_information_set_ref"),
        "evaluation_time_information_set_ref",
    )
    return MappingProxyType(
        {
            **normalized,
            "actual_outcome_ref": require_opaque_ref(
                raw.get("actual_outcome_ref"), "actual_outcome_ref"
            ),
            "evaluation_time_information_set_ref": require_record_id(
                raw.get("evaluation_time_information_set_ref"),
                "evaluation_time_information_set_ref",
            ),
            "economic_score": raw.get("economic_score"),
        }
    )
