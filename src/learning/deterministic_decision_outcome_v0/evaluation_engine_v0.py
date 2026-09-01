"""Offline DDO replay / outcome / attribution / counterfactual engine v0.

Consumes captured DecisionEvent/IncidentRecord plus an explicit evaluation
observation. Does not call the trading core, does not invent missing
facts, and does not wire into productive runtime.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import freeze_record
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    validate_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    UNKNOWN,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.evaluation_observation_v0 import (
    validate_evaluation_observation_v0,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_records_v0 import (
    build_attribution_record_v0,
    build_counterfactual_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.hindsight_guard_v0 import (
    assert_no_hindsight_safety_relabel_v0,
    assert_safety_inputs_exclude_later_economics_v0,
)
from src.learning.deterministic_decision_outcome_v0.incident_record_v0 import (
    validate_incident_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import (
    AppendOnlyDdoLedgerV0,
    AppendResultV0,
)
from src.learning.deterministic_decision_outcome_v0.outcome_v0 import build_outcome_record_v0
from src.learning.deterministic_decision_outcome_v0.replay_evaluator_v0 import (
    classify_decision_event_v0,
    classify_incident_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import compute_content_hash_v0

EVALUATION_ENGINE_ID: Final[str] = "peak_trade.learning.ddo.evaluation_engine_v0"
EVALUATION_ENGINE_PRODUCER_ID: Final[str] = EVALUATION_ENGINE_ID
EVALUATION_ENGINE_PRODUCER_VERSION: Final[str] = "evaluation_engine_v0"
EVALUATION_TRADING_CORE_REACHABLE: Final[bool] = False
EVALUATION_RUNTIME_WIRING: Final[bool] = False

_SAFETY_DECISION_TYPES: Final[frozenset[str]] = frozenset(
    {"KILL_SWITCH", "STALE_BLOCK", "RISK_BLOCK", "RECONCILIATION_BLOCK"}
)
_SAFETY_INCIDENT_CLASSES: Final[frozenset[str]] = frozenset(
    {"KILL_SWITCH", "STALE", "RISK", "RECONCILIATION"}
)
_LATER_HORIZONS: Final[frozenset[str]] = frozenset(
    {"IMMEDIATE_POST_EVENT", "EVENT_RECOVERY", "N_BARS", "POSITION_LIFECYCLE"}
)

REQUIRED_IDENTITY_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "outcome_record_id",
        "attribution_record_id",
        "counterfactual_record_id",
        "correlation_id",
        "event_time_utc",
        "code_sha",
        "config_hash",
    }
)


def _require_identity(identity: Mapping[str, Any]) -> dict[str, Any]:
    raw = dict(identity)
    missing = sorted(field for field in REQUIRED_IDENTITY_FIELDS if field not in raw)
    if missing:
        raise DdoValidationError(f"EVALUATION_IDENTITY_MISSING:{missing}")
    extra = sorted(set(raw) - REQUIRED_IDENTITY_FIELDS)
    if extra:
        raise DdoValidationError(f"EVALUATION_IDENTITY_UNEXPECTED:{extra}")
    return raw


def _kill_switch_fired(decision: Mapping[str, Any], incident: Mapping[str, Any] | None) -> bool:
    if decision["decision_type"] == "KILL_SWITCH":
        return True
    return bool(incident is not None and incident["incident_class"] == "KILL_SWITCH")


def _safety_class_in_play(decision: Mapping[str, Any], incident: Mapping[str, Any] | None) -> bool:
    if decision["decision_type"] in _SAFETY_DECISION_TYPES:
        return True
    return bool(incident is not None and incident["incident_class"] in _SAFETY_INCIDENT_CLASSES)


def _kill_switch_correctness(
    *,
    fired: bool,
    protected_condition: str | None,
) -> str:
    if protected_condition in (None, UNKNOWN):
        return UNKNOWN
    if fired and protected_condition == "PRESENT":
        return "TRUE_POSITIVE"
    if fired and protected_condition == "ABSENT":
        return "FALSE_POSITIVE"
    if (not fired) and protected_condition == "PRESENT":
        return "FALSE_NEGATIVE"
    return "TRUE_NEGATIVE"


def _safety_score(*, ks_correctness: str, safety_in_play: bool) -> str:
    if ks_correctness == "TRUE_POSITIVE" or ks_correctness == "TRUE_NEGATIVE":
        return "SAFETY_CONTRACT_SATISFIED"
    if ks_correctness == "FALSE_POSITIVE" or ks_correctness == "FALSE_NEGATIVE":
        return "SAFETY_CONTRACT_NOT_SATISFIED"
    if not safety_in_play and ks_correctness == UNKNOWN:
        return "SAFETY_NOT_APPLICABLE"
    return UNKNOWN


def _stale_root_cause(
    observation: Mapping[str, Any], incident: Mapping[str, Any] | None
) -> str | None:
    if observation["stale_root_cause"] is not None:
        return str(observation["stale_root_cause"])
    if incident is not None and incident["stale_root_cause"] is not None:
        return str(incident["stale_root_cause"])
    if incident is not None and incident["incident_class"] == "STALE":
        return UNKNOWN
    return None


def _derive_admissibility(observation: Mapping[str, Any]) -> str:
    horizon = observation["evaluation_horizon"]
    if horizon in {UNKNOWN, "DECISION_TIME"}:
        if observation["observed_alternative_ref"] is not None:
            return "OBSERVED"
        if observation["counterfactual_assumptions"] is not None:
            return "MODELLED"
        return "UNAVAILABLE"
    if observation["observed_alternative_ref"] is not None:
        return "OBSERVED"
    if observation["alternative_decision_event"] is not None:
        return "REPLAYABLE"
    if observation["counterfactual_assumptions"] is not None:
        return "MODELLED"
    return "UNAVAILABLE"


def _assert_claim_matches(claim: str | None, derived: str) -> None:
    if claim is None:
        return
    if claim != derived:
        raise DdoValidationError(f"COUNTERFACTUAL_CLAIM_CONTRADICTS_EVIDENCE:{claim}:{derived}")


def evaluate_offline_bundle_v0(
    decision_event: Mapping[str, Any],
    observation: Mapping[str, Any],
    *,
    incident_record: Mapping[str, Any] | None = None,
    identity: Mapping[str, Any],
    ledger: AppendOnlyDdoLedgerV0 | None = None,
) -> MappingProxyType[str, Any]:
    """Produce outcome, attribution, and counterfactual records offline.

    Optional ledger persistence is append-only. The decision must already
    exist in the ledger when persistence is requested.
    """
    decision = validate_decision_event_v0(decision_event)
    obs = validate_evaluation_observation_v0(observation)
    ids = _require_identity(identity)
    if obs["decision_event_ref"] != decision["record_id"]:
        raise DdoValidationError("EVALUATION_DECISION_REF_MISMATCH")
    incident: Mapping[str, Any] | None = None
    if incident_record is not None:
        incident = validate_incident_record_v0(incident_record)
        if (
            obs["incident_record_ref"] is not None
            and obs["incident_record_ref"] != incident["record_id"]
        ):
            raise DdoValidationError("EVALUATION_INCIDENT_REF_MISMATCH")
    elif obs["incident_record_ref"] is not None:
        raise DdoValidationError("EVALUATION_INCIDENT_REF_WITHOUT_RECORD")

    replayed = classify_decision_event_v0(decision)
    if incident is not None:
        classify_incident_record_v0(incident)
    if replayed["hindsight_leakage"] is not False:
        raise DdoValidationError("REPLAY_HINDSIGHT_LEAKAGE")

    safety_inputs = {
        "decision_type": decision["decision_type"],
        "decision_result": decision["decision_result"],
        "hard_block_reasons": list(decision["hard_block_reasons"]),
        "decision_time_information_set_ref": decision["decision_time_information_set_ref"],
        "incident_class": None if incident is None else incident["incident_class"],
        "protected_condition": obs["protected_condition"],
        "kill_switch_timing_label": obs["kill_switch_timing_label"],
        "stale_root_cause": obs["stale_root_cause"],
    }
    assert_safety_inputs_exclude_later_economics_v0(safety_inputs)
    assert_no_hindsight_safety_relabel_v0(obs["later_economic_path"])

    fired = _kill_switch_fired(decision, incident)
    safety_in_play = _safety_class_in_play(decision, incident)
    ks_correctness = _kill_switch_correctness(
        fired=fired, protected_condition=obs["protected_condition"]
    )
    safety_score = _safety_score(ks_correctness=ks_correctness, safety_in_play=safety_in_play)
    timing = obs["kill_switch_timing_label"]
    if ks_correctness in {UNKNOWN, "TRUE_NEGATIVE"} and timing is None:
        timing_label = UNKNOWN if ks_correctness == UNKNOWN else None
    else:
        timing_label = UNKNOWN if timing is None else str(timing)

    if obs["declared_decision_score"] is not None:
        decision_score = str(obs["declared_decision_score"])
    else:
        decision_score = (
            "REPLAY_CLASSIFICATION_MATCH"
            if replayed["decision_type"] == decision["decision_type"]
            else UNKNOWN
        )

    horizon = str(obs["evaluation_horizon"])
    if horizon in _LATER_HORIZONS:
        actual_outcome_ref = obs["actual_outcome_ref"]
        economic_score = obs["economic_score"]
        if actual_outcome_ref is None:
            actual_outcome_ref = UNKNOWN
        if economic_score is None:
            economic_score = UNKNOWN
    else:
        actual_outcome_ref = UNKNOWN
        economic_score = UNKNOWN

    # later_favorable_price_move is recorded only as economic context; ignored for safety.
    _ = obs["later_favorable_price_move"]

    admissibility = _derive_admissibility(obs)
    _assert_claim_matches(obs["counterfactual_admissibility_claim"], admissibility)
    if admissibility == "UNAVAILABLE":
        alternative_ref = None
        assumptions = None
    elif admissibility == "OBSERVED":
        alternative_ref = obs["observed_alternative_ref"]
        assumptions = None
    elif admissibility == "REPLAYABLE":
        alternative = validate_decision_event_v0(obs["alternative_decision_event"])
        classify_decision_event_v0(alternative)
        if (
            decision["decision_time_information_set_ref"] is not None
            and alternative.get("decision_time_information_set_ref") is not None
            and alternative["decision_time_information_set_ref"]
            != decision["decision_time_information_set_ref"]
        ):
            raise DdoValidationError("COUNTERFACTUAL_DECISION_TIME_SET_MISMATCH")
        alternative_ref = str(alternative["record_id"])
        assumptions = None
    else:
        if obs["counterfactual_assumptions"] is None:
            raise DdoValidationError("MODELLED_COUNTERFACTUAL_REQUIRES_ASSUMPTIONS")
        alternative_ref = None
        assumptions = str(obs["counterfactual_assumptions"])

    stale = _stale_root_cause(obs, incident)
    root_cause = obs["root_cause"] if obs["root_cause"] is not None else UNKNOWN
    evidence_hash = compute_content_hash_v0(obs)
    parent_ids = [decision["record_id"]]
    if incident is not None:
        parent_ids.append(incident["record_id"])
    incident_ref = None if incident is None else incident["record_id"]
    info_set = decision["decision_time_information_set_ref"]

    outcome = build_outcome_record_v0(
        {
            "schema_name": "outcome_record",
            "schema_version": "outcome_record_v0",
            "record_id": ids["outcome_record_id"],
            "decision_event_ref": decision["record_id"],
            "incident_record_ref": incident_ref,
            "evaluation_horizon": horizon,
            "actual_outcome_ref": actual_outcome_ref,
            "counterfactual_admissibility": admissibility,
            "safety_score": safety_score,
            "decision_score": decision_score,
            "economic_score": economic_score,
            "root_cause": root_cause,
            "confidence": obs["confidence"] if obs["confidence"] is not None else UNKNOWN,
            "event_time_utc": ids["event_time_utc"],
            "correlation_id": ids["correlation_id"],
            "cycle_id": decision["cycle_id"],
            "causal_parent_ids": parent_ids,
            "producer_id": EVALUATION_ENGINE_PRODUCER_ID,
            "producer_version": EVALUATION_ENGINE_PRODUCER_VERSION,
            "authority_owner": UNKNOWN,
            "code_sha": ids["code_sha"],
            "config_hash": ids["config_hash"],
            "evidence_hash": evidence_hash,
            "evidence_source_refs": [
                decision["record_id"],
                *([incident["record_id"]] if incident is not None else []),
            ],
        }
    )
    attribution = build_attribution_record_v0(
        {
            "schema_name": "attribution_record",
            "schema_version": "attribution_record_v0",
            "record_id": ids["attribution_record_id"],
            "decision_event_ref": decision["record_id"],
            "incident_record_ref": incident_ref,
            "outcome_record_ref": outcome["record_id"],
            "root_cause": root_cause,
            "kill_switch_correctness": ks_correctness,
            "kill_switch_timing_label": timing_label,
            "stale_root_cause": stale,
            "safety_correctness_uses_decision_time_information_set": True,
            "event_time_utc": ids["event_time_utc"],
            "correlation_id": ids["correlation_id"],
            "cycle_id": decision["cycle_id"],
            "causal_parent_ids": parent_ids,
            "producer_id": EVALUATION_ENGINE_PRODUCER_ID,
            "producer_version": EVALUATION_ENGINE_PRODUCER_VERSION,
            "authority_owner": UNKNOWN,
            "code_sha": ids["code_sha"],
            "config_hash": ids["config_hash"],
            "evidence_hash": evidence_hash,
            "evidence_source_refs": [
                decision["record_id"],
                *([incident["record_id"]] if incident is not None else []),
            ],
        }
    )
    counterfactual = build_counterfactual_record_v0(
        {
            "schema_name": "counterfactual_record",
            "schema_version": "counterfactual_record_v0",
            "record_id": ids["counterfactual_record_id"],
            "decision_event_ref": decision["record_id"],
            "incident_record_ref": incident_ref,
            "outcome_record_ref": outcome["record_id"],
            "counterfactual_admissibility": admissibility,
            "assumptions": assumptions,
            "confidence": obs["confidence"] if obs["confidence"] is not None else UNKNOWN,
            "alternative_result_ref": alternative_ref,
            "decision_time_information_set_ref": info_set,
            "evaluation_time_information_set_ref": obs["evaluation_time_information_set_ref"],
            "event_time_utc": ids["event_time_utc"],
            "correlation_id": ids["correlation_id"],
            "cycle_id": decision["cycle_id"],
            "causal_parent_ids": parent_ids,
            "producer_id": EVALUATION_ENGINE_PRODUCER_ID,
            "producer_version": EVALUATION_ENGINE_PRODUCER_VERSION,
            "authority_owner": UNKNOWN,
            "code_sha": ids["code_sha"],
            "config_hash": ids["config_hash"],
            "evidence_hash": evidence_hash,
            "evidence_source_refs": [
                decision["record_id"],
                *([incident["record_id"]] if incident is not None else []),
            ],
        }
    )

    persist: dict[str, Any] = {"outcome": None, "attribution": None, "counterfactual": None}
    if ledger is not None:
        persist = persist_evaluation_bundle_v0(
            ledger,
            outcome=outcome,
            attribution=attribution,
            counterfactual=counterfactual,
        )

    return freeze_record(
        {
            "evaluator_id": EVALUATION_ENGINE_ID,
            "hindsight_leakage": False,
            "unknown_collapsed": False,
            "trading_core_reachable": False,
            "runtime_wiring": False,
            "replay": dict(replayed),
            "outcome_record": dict(outcome),
            "attribution_record": dict(attribution),
            "counterfactual_record": dict(counterfactual),
            "persist": persist,
        }
    )


def persist_evaluation_bundle_v0(
    ledger: AppendOnlyDdoLedgerV0,
    *,
    outcome: Mapping[str, Any],
    attribution: Mapping[str, Any],
    counterfactual: Mapping[str, Any],
) -> dict[str, Any]:
    """Append evaluation records. Decision/incident must already be in the ledger."""
    outcome_result = ledger.append(outcome)
    attribution_result = ledger.append(attribution)
    counterfactual_result = ledger.append(counterfactual)
    return {
        "outcome": _append_as_dict(outcome_result),
        "attribution": _append_as_dict(attribution_result),
        "counterfactual": _append_as_dict(counterfactual_result),
    }


def _append_as_dict(result: AppendResultV0) -> dict[str, Any]:
    return {
        "status": result.status,
        "record_id": result.record_id,
        "content_hash": result.content_hash,
        "sequence": result.sequence,
        "ledger_entry_hash": result.ledger_entry_hash,
    }
