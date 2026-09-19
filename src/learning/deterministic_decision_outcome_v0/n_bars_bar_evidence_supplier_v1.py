"""DDO N_BARS bar evidence supplier v1 — sole authority for supplier_input materialization."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Final, Literal, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    require_event_time_utc,
    require_mapping,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    validate_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import OUTCOME_SCALAR_KIND_V0
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.o4_n_bars_bar_evidence_bridge_contracts_v1 import (
    CHAIN_GAPLESS_FINALIZED,
    O4_N_BARS_BAR_EVIDENCE_BRIDGE_ID,
    O4_STATE_CORRECTED,
    DdoNbarsBridgeTranslationV1,
    _bar_state_token,
    mint_ddo_content_ref_v1,
    translate_o4_snapshot_to_ddo_n_bars_bindings_v1,
    unix_seconds_to_event_time_utc,
    validate_o4_n_bars_bar_evidence_snapshot_v1,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_contracts_v1 import (
    validate_real_outcome_horizon_supplier_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_engine_v1 import (
    supply_n_bars_evaluation_observation_v1,
)

N_BARS_BAR_EVIDENCE_SUPPLIER_ID: Final[str] = (
    "peak_trade.learning.ddo.n_bars_bar_evidence_supplier_v1"
)

EVAL_INFO_SET_SCHEMA_NAME: Final[str] = "ddo_n_bars_evaluation_time_information_set"
EVAL_INFO_SET_SCHEMA_VERSION: Final[str] = "ddo_n_bars_evaluation_time_information_set_v1"
MEASUREMENT_SCHEMA_NAME: Final[str] = "ddo_n_bars_outcome_measurement_evidence"
MEASUREMENT_SCHEMA_VERSION: Final[str] = "ddo_n_bars_outcome_measurement_evidence_v1"

PRICE_BASIS_FINALIZED: Final[str] = "O4_BAR_CLOSE_FINALIZED"
PRICE_BASIS_CORRECTED: Final[str] = "O4_BAR_CLOSE_CORRECTED"

HitComparator = Literal["GE", "LE", "EQ"]


@dataclass(frozen=True)
class NbarsSupplierMaterializationV1:
    supplier_input: Mapping[str, Any]
    evaluation_time_information_set_artifact: Mapping[str, Any]
    measurement_evidence_artifact: Mapping[str, Any]
    bridge_translation: DdoNbarsBridgeTranslationV1


def _price_basis_for_bar(finalization_state: str) -> str:
    fin = _bar_state_token(finalization_state)
    if fin == O4_STATE_CORRECTED:
        return PRICE_BASIS_CORRECTED
    return PRICE_BASIS_FINALIZED


def _resolve_price_basis(start_state: str, end_state: str) -> str:
    start = _price_basis_for_bar(start_state)
    end = _price_basis_for_bar(end_state)
    if start == PRICE_BASIS_CORRECTED or end == PRICE_BASIS_CORRECTED:
        return PRICE_BASIS_CORRECTED
    return PRICE_BASIS_FINALIZED


def _assert_pit_observation_boundary(
    *,
    bars: tuple[Mapping[str, Any], ...],
    evaluation_boundary_time_utc: str,
) -> None:
    boundary = require_event_time_utc(evaluation_boundary_time_utc, "evaluation_boundary_time_utc")
    for index, bar in enumerate(bars):
        identity = require_mapping(
            bar.get("last_observation_identity"), f"last_observation_identity[{index}]"
        )
        venue_event_time = identity.get("venue_event_time")
        if venue_event_time is None:
            raise DdoValidationError(f"PIT_OBSERVATION_TIME_MISSING:{index}")
        if isinstance(venue_event_time, (int, float)) and not isinstance(venue_event_time, bool):
            obs_time = unix_seconds_to_event_time_utc(
                venue_event_time, f"venue_event_time[{index}]"
            )
        elif isinstance(venue_event_time, str):
            obs_time = require_event_time_utc(venue_event_time, f"venue_event_time[{index}]")
        else:
            raise DdoValidationError(f"PIT_OBSERVATION_TIME_INVALID:{index}")
        if obs_time > boundary:
            raise DdoValidationError("PIT_POST_BOUNDARY_OBSERVATION")


def _build_measurement_fields(
    *,
    outcome_scalar_kind: str,
    start_price: float,
    end_price: float,
    target_value: float | None,
    comparator: HitComparator | None,
) -> dict[str, Any]:
    if outcome_scalar_kind not in OUTCOME_SCALAR_KIND_V0:
        raise DdoValidationError(f"UNSUPPORTED_OUTCOME_SCALAR_KIND:{outcome_scalar_kind}")
    if start_price <= 0:
        raise DdoValidationError("MEASUREMENT_START_PRICE_NON_POSITIVE")
    fields: dict[str, Any] = {
        "start_price": start_price,
        "end_price": end_price,
    }
    if outcome_scalar_kind == "LOG_RETURN":
        fields["log_return"] = math.log(end_price / start_price)
    elif outcome_scalar_kind == "ABS_RETURN":
        fields["abs_return"] = abs(end_price - start_price) / start_price
    else:
        if target_value is None or comparator is None:
            raise DdoValidationError("HIT_TARGET_PARAMS_REQUIRED")
        if comparator not in {"GE", "LE", "EQ"}:
            raise DdoValidationError("HIT_TARGET_COMPARATOR_INVALID")
        compared = end_price
        if comparator == "GE":
            hit = compared >= target_value
        elif comparator == "LE":
            hit = compared <= target_value
        else:
            hit = compared == target_value
        fields.update(
            {
                "target_value": target_value,
                "comparator": comparator,
                "hit_result": hit,
                "compared_price": compared,
            }
        )
    return fields


def materialize_real_outcome_horizon_supplier_input_v1(
    decision_event: Mapping[str, Any],
    o4_snapshot: Mapping[str, Any],
    *,
    outcome_scalar_kind: str,
    hit_target_value: float | None = None,
    hit_target_comparator: HitComparator | None = None,
    economic_score: str | None = None,
) -> NbarsSupplierMaterializationV1:
    """Mint info-set + measurement evidence and return validated supplier_input."""
    decision = validate_decision_event_v0(decision_event)
    if outcome_scalar_kind not in OUTCOME_SCALAR_KIND_V0:
        raise DdoValidationError(f"UNSUPPORTED_OUTCOME_SCALAR_KIND:{outcome_scalar_kind}")
    snapshot = validate_o4_n_bars_bar_evidence_snapshot_v1(o4_snapshot)
    if str(snapshot["decision_event_ref"]) != str(decision["record_id"]):
        raise DdoValidationError("DECISION_EVENT_REF_MISMATCH")

    translation = translate_o4_snapshot_to_ddo_n_bars_bindings_v1(
        {key: (list(value) if key == "o4_bars" else value) for key, value in snapshot.items()}
    )
    decision_time = require_event_time_utc(decision["event_time_utc"], "event_time_utc")
    if translation.horizon_start_time_utc < decision_time:
        raise DdoValidationError("HORIZON_START_BEFORE_DECISION_EVENT")

    bars = snapshot["o4_bars"]
    status = translation.horizon_observation_status
    reason = translation.horizon_observation_reason

    supplier_core: dict[str, Any] = {
        "horizon_start_time_utc": translation.horizon_start_time_utc,
        "instrument_ref": translation.instrument_ref,
        "bar_spec_ref": translation.bar_spec_ref,
        "n_bars": translation.n_bars,
        "horizon_observation_status": status,
        "horizon_observation_reason": reason,
        "outcome_scalar_kind": outcome_scalar_kind,
    }

    if translation.chain_completeness != CHAIN_GAPLESS_FINALIZED or status != "OK":
        if (
            translation.bar_close_times_utc
            and len(translation.bar_close_times_utc) == translation.n_bars
        ):
            supplier_core["bar_close_times_utc"] = list(translation.bar_close_times_utc)
        if (
            translation.bar_identity_refs
            and len(translation.bar_identity_refs) == translation.n_bars
        ):
            supplier_core["bar_identity_refs"] = list(translation.bar_identity_refs)
        bundle = validate_real_outcome_horizon_supplier_input_v1(
            _non_ok_supplier_payload(supplier_core)
        )
        return NbarsSupplierMaterializationV1(
            supplier_input=dict(bundle),
            evaluation_time_information_set_artifact={},
            measurement_evidence_artifact={},
            bridge_translation=translation,
        )

    bar_closes = translation.bar_close_times_utc
    bar_ids = translation.bar_identity_refs
    evaluation_boundary = bar_closes[-1]
    _assert_pit_observation_boundary(bars=bars, evaluation_boundary_time_utc=evaluation_boundary)

    decision_time_ref = decision.get("decision_time_information_set_ref")
    if decision_time_ref is not None and isinstance(decision_time_ref, str):
        forbidden_reuse = str(decision_time_ref)
    else:
        forbidden_reuse = None

    sorted_bars = tuple(sorted(bars, key=lambda b: float(b["bar_open_time"])))
    start_bar = sorted_bars[0]
    end_bar = sorted_bars[-1]
    start_price = float(start_bar["close"])
    end_price = float(end_bar["close"])
    price_basis = _resolve_price_basis(
        str(start_bar["finalization_state"]), str(end_bar["finalization_state"])
    )

    eval_artifact_body: dict[str, Any] = {
        "schema_name": EVAL_INFO_SET_SCHEMA_NAME,
        "schema_version": EVAL_INFO_SET_SCHEMA_VERSION,
        "decision_event_ref": str(decision["record_id"]),
        "instrument_ref": translation.instrument_ref,
        "bar_spec_ref": translation.bar_spec_ref,
        "horizon_start_time_utc": translation.horizon_start_time_utc,
        "n_bars": translation.n_bars,
        "bar_close_times_utc": list(bar_closes),
        "bar_identity_refs": list(bar_ids),
        "evaluation_boundary_time_utc": evaluation_boundary,
        "last_bar_last_observation_identity": dict(end_bar["last_observation_identity"]),
        "o4_provenance": dict(translation.o4_provenance),
        "bridge_contract_id": O4_N_BARS_BAR_EVIDENCE_BRIDGE_ID,
        "information_set_kind": "N_BARS_HORIZON_END_PIT",
    }
    eval_ref = mint_ddo_content_ref_v1(prefix="ddo.eval_info_set.", payload=eval_artifact_body)
    if forbidden_reuse is not None and eval_ref == forbidden_reuse:
        raise DdoValidationError("DECISION_TIME_INFORMATION_SET_REUSE_FORBIDDEN")
    eval_artifact = {**eval_artifact_body, "evaluation_time_information_set_ref": eval_ref}

    measurement_body: dict[str, Any] = {
        "schema_name": MEASUREMENT_SCHEMA_NAME,
        "schema_version": MEASUREMENT_SCHEMA_VERSION,
        "outcome_scalar_kind": outcome_scalar_kind,
        "instrument_ref": translation.instrument_ref,
        "bar_spec_ref": translation.bar_spec_ref,
        "horizon_start_time_utc": translation.horizon_start_time_utc,
        "n_bars": translation.n_bars,
        "bar_close_times_utc": list(bar_closes),
        "bar_identity_refs": list(bar_ids),
        "evaluation_time_utc": evaluation_boundary,
        "price_basis_kind": price_basis,
        "start_bar_identity_ref": bar_ids[0],
        "end_bar_identity_ref": bar_ids[-1],
        "o4_provenance": dict(translation.o4_provenance),
        "bridge_contract_id": O4_N_BARS_BAR_EVIDENCE_BRIDGE_ID,
        "measurement_producer_id": N_BARS_BAR_EVIDENCE_SUPPLIER_ID,
        **_build_measurement_fields(
            outcome_scalar_kind=outcome_scalar_kind,
            start_price=start_price,
            end_price=end_price,
            target_value=hit_target_value,
            comparator=hit_target_comparator,
        ),
    }
    actual_outcome_ref = mint_ddo_content_ref_v1(
        prefix="ddo.outcome.measure.",
        payload=measurement_body,
    )
    measurement_artifact = {**measurement_body, "actual_outcome_ref": actual_outcome_ref}

    supplier_payload: dict[str, Any] = {
        **supplier_core,
        "horizon_observation_status": "OK",
        "horizon_observation_reason": None,
        "bar_close_times_utc": list(bar_closes),
        "bar_identity_refs": list(bar_ids),
        "evaluation_time_information_set_ref": eval_ref,
        "actual_outcome_ref": actual_outcome_ref,
        "economic_score": economic_score,
    }
    validated = validate_real_outcome_horizon_supplier_input_v1(supplier_payload)
    return NbarsSupplierMaterializationV1(
        supplier_input=dict(validated),
        evaluation_time_information_set_artifact=eval_artifact,
        measurement_evidence_artifact=measurement_artifact,
        bridge_translation=translation,
    )


def _non_ok_supplier_payload(core: dict[str, Any]) -> dict[str, Any]:
    """Fail-closed supplier_input for non-OK horizons (no REAL claim)."""
    status = str(core["horizon_observation_status"])
    if status == "OK":
        raise DdoValidationError("NON_OK_PAYLOAD_HELPER_INVOKED_FOR_OK")
    return {
        **core,
        "actual_outcome_ref": "evidence/unproven-measurement",
        "evaluation_time_information_set_ref": "ddo.eval_info_set.unproven0001",
        "bar_close_times_utc": core.get("bar_close_times_utc"),
        "bar_identity_refs": core.get("bar_identity_refs"),
    }


def run_offline_n_bars_horizon_pipeline_v1(
    decision_event: Mapping[str, Any],
    o4_snapshot: Mapping[str, Any],
    *,
    outcome_scalar_kind: str,
    hit_target_value: float | None = None,
    hit_target_comparator: HitComparator | None = None,
    economic_score: str | None = None,
) -> dict[str, Any]:
    """O4 snapshot → supplier → horizon observation (offline only)."""
    materialized = materialize_real_outcome_horizon_supplier_input_v1(
        decision_event,
        o4_snapshot,
        outcome_scalar_kind=outcome_scalar_kind,
        hit_target_value=hit_target_value,
        hit_target_comparator=hit_target_comparator,
        economic_score=economic_score,
    )
    decision = validate_decision_event_v0(decision_event)
    observation = supply_n_bars_evaluation_observation_v1(
        decision,
        materialized.supplier_input,
    )
    return {
        "materialization": materialized,
        "evaluation_observation": observation,
    }
