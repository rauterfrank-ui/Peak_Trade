"""Export learning_state_record_v0 → learning_evidence_record_v1 (offline only)."""

from __future__ import annotations

import hashlib
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_LEARNING_EVIDENCE_RECORD,
    SCHEMA_VERSION_LEARNING_EVIDENCE_RECORD_V1,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.learning_evidence_record_v1 import (
    EVIDENCE_CLASS_LEARNING,
    UNIVERSE_CLASS_SELF_LEARNING,
    build_learning_evidence_record_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_state_record_v0 import (
    validate_learning_state_record_v0,
)

EXPORT_ID: Final[str] = "peak_trade.learning.ddo.learning_evidence_export_v1"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED: Final[bool] = False


def derive_learning_evidence_record_id_v1(
    *, source_learning_state_record_ref: str, evaluation_bundle_fingerprint: str
) -> str:
    digest = hashlib.sha256(
        f"{source_learning_state_record_ref}|{evaluation_bundle_fingerprint}".encode("utf-8")
    ).hexdigest()
    return f"ddo.lev.{digest[:40]}"


def export_learning_evidence_from_state_v1(
    learning_state: Mapping[str, Any],
    *,
    record_id: str | None = None,
    event_time_utc: str | None = None,
    correlation_id: str | None = None,
    cycle_id: str | None = None,
    code_sha: str = UNKNOWN,
    config_hash: str = UNKNOWN,
) -> dict[str, Any]:
    """Project one validated learning state snapshot into learning evidence."""
    state = validate_learning_state_record_v0(learning_state)
    fingerprint = str(state["evaluation_bundle_fingerprint"])
    source_ref = str(state["record_id"])
    evidence_id = record_id or derive_learning_evidence_record_id_v1(
        source_learning_state_record_ref=source_ref,
        evaluation_bundle_fingerprint=fingerprint,
    )
    event_time = event_time_utc or str(state["last_event_time_utc"])
    correlation = correlation_id or source_ref
    economic_label = str(state["next_cycle_economic_score_label"])
    payload = {
        "schema_name": SCHEMA_NAME_LEARNING_EVIDENCE_RECORD,
        "schema_version": SCHEMA_VERSION_LEARNING_EVIDENCE_RECORD_V1,
        "record_id": evidence_id,
        "source_learning_state_record_ref": source_ref,
        "state_scope_id": str(state["state_scope_id"]),
        "state_version": int(state["state_version"]),
        "evaluation_bundle_fingerprint": fingerprint,
        "decision_event_ref": str(state["decision_event_ref"]),
        "observed_at_utc": str(state["last_event_time_utc"]),
        "economic_score_label": economic_label,
        "evaluation_horizon": str(state["last_evaluation_horizon"]),
        "actual_outcome_ref": str(state["last_actual_outcome_ref"]),
        "decision_score_label": state.get("last_decision_score"),
        "safety_score_label": state.get("last_safety_score"),
        "universe_class": UNIVERSE_CLASS_SELF_LEARNING,
        "evidence_class": EVIDENCE_CLASS_LEARNING,
        "event_time_utc": event_time,
        "correlation_id": correlation,
        "cycle_id": cycle_id,
        "causal_parent_ids": [source_ref, str(state["decision_event_ref"])],
        "producer_id": EXPORT_ID,
        "authority_owner": UNKNOWN,
        "code_sha": code_sha,
        "config_hash": config_hash,
        "evidence_hash": fingerprint,
        "evidence_source_refs": [
            source_ref,
            str(state["outcome_record_ref"]),
            str(state["attribution_record_ref"]),
            str(state["counterfactual_record_ref"]),
        ],
        "productive_authority": "NONE",
        "runtime_reachability": False,
        "can_auto_promote": False,
        "can_mutate_core": False,
        "can_mutate_risk": False,
        "can_mutate_safety": False,
        "can_deploy": False,
    }
    return dict(build_learning_evidence_record_v1(payload))


def export_learning_evidence_from_state_or_fail_v1(
    learning_state: Mapping[str, Any], **kwargs: Any
) -> dict[str, Any]:
    try:
        return export_learning_evidence_from_state_v1(learning_state, **kwargs)
    except DdoValidationError:
        raise
    except Exception as exc:  # pragma: no cover - defensive fail-closed
        raise DdoValidationError("LEARNING_EVIDENCE_EXPORT_FAILED") from exc
