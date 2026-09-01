"""Fixture-only incumbent vs candidate challenger comparison v0.

Zero productive authority. Comparison is only valid on an identical
ValidationEvidencePack identity. Comparison cannot make a candidate
authoritative and cannot mutate the incumbent.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.learning.deterministic_decision_outcome_v0.common_v0 import freeze_record, require_mapping
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN, VALIDATION_GATE_IDS_V0
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.learning_records_v0 import (
    validate_candidate_artifact_v0,
    validate_validation_evidence_pack_v0,
)

CHALLENGER_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
CHALLENGER_RANKING_IS_ADVISORY: Final[bool] = True
SHADOW_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
SHADOW_COMPARISON_CAN_BECOME_AUTHORITATIVE: Final[bool] = False
SHADOW_COMPARISON_CAN_MUTATE_INCUMBENT: Final[bool] = False
SHADOW_COMPARISON_CAN_EXECUTE: Final[bool] = False


def _require_same_pack(
    *,
    incumbent: Mapping[str, Any],
    candidate: Mapping[str, Any],
    evidence_pack: Mapping[str, Any],
) -> tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]]:
    incumbent_rec = validate_candidate_artifact_v0(incumbent)
    candidate_rec = validate_candidate_artifact_v0(candidate)
    pack = validate_validation_evidence_pack_v0(evidence_pack)
    if pack["candidate_artifact_ref"] != candidate_rec["record_id"]:
        raise DdoValidationError("CHALLENGER_PACK_CANDIDATE_MISMATCH")
    if pack["incumbent_artifact_ref"] != incumbent_rec["record_id"]:
        raise DdoValidationError("CHALLENGER_PACK_INCUMBENT_MISMATCH")
    if incumbent_rec["record_id"] == candidate_rec["record_id"]:
        raise DdoValidationError("CHALLENGER_INCUMBENT_EQUALS_CANDIDATE")
    return incumbent_rec, candidate_rec, pack


def compare_challenger_v0(
    *,
    incumbent: Mapping[str, Any],
    candidate: Mapping[str, Any],
    evidence_pack: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    incumbent_rec, candidate_rec, pack = _require_same_pack(
        incumbent=incumbent, candidate=candidate, evidence_pack=evidence_pack
    )
    deltas = {
        gate: {"incumbent": "BOUND_BY_SAME_PACK", "candidate": pack["gates"][gate]}
        for gate in VALIDATION_GATE_IDS_V0
    }
    return freeze_record(
        {
            "incumbent_artifact_ref": incumbent_rec["record_id"],
            "candidate_artifact_ref": candidate_rec["record_id"],
            "validation_evidence_pack_ref": pack["record_id"],
            "identical_evidence_pack": True,
            "gate_deltas": deltas,
            "productive_authority": CHALLENGER_PRODUCTIVE_AUTHORITY,
            "ranking_advisory": CHALLENGER_RANKING_IS_ADVISORY,
        }
    )


def _index_by_record_id(
    rows: Sequence[Mapping[str, Any]], *, label: str
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        mapping = require_mapping(row, label)
        record_id = mapping.get("record_id")
        if not isinstance(record_id, str) or not record_id:
            raise DdoValidationError(f"{label.upper()}_RECORD_ID_MISSING")
        if record_id in out:
            raise DdoValidationError(f"{label.upper()}_DUPLICATE_RECORD_ID:{record_id}")
        out[record_id] = dict(mapping)
    return out


def _token_or_unknown(value: Any) -> str:
    if value is None:
        return UNKNOWN
    if not isinstance(value, str) or value == "":
        raise DdoValidationError("SHADOW_TOKEN_MUST_BE_NON_EMPTY_STRING_OR_UNKNOWN")
    return value


def _decision_deltas(
    incumbent_rows: Sequence[Mapping[str, Any]],
    candidate_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    left = _index_by_record_id(incumbent_rows, label="incumbent_decision")
    right = _index_by_record_id(candidate_rows, label="candidate_decision")
    deltas: list[dict[str, Any]] = []
    for record_id in sorted(set(left) | set(right)):
        incumbent_row = left.get(record_id)
        candidate_row = right.get(record_id)
        incumbent_type = (
            _token_or_unknown(incumbent_row.get("decision_type")) if incumbent_row else UNKNOWN
        )
        candidate_type = (
            _token_or_unknown(candidate_row.get("decision_type")) if candidate_row else UNKNOWN
        )
        incumbent_result = (
            _token_or_unknown(incumbent_row.get("decision_result")) if incumbent_row else UNKNOWN
        )
        candidate_result = (
            _token_or_unknown(candidate_row.get("decision_result")) if candidate_row else UNKNOWN
        )
        deltas.append(
            {
                "record_id": record_id,
                "incumbent_present": incumbent_row is not None,
                "candidate_present": candidate_row is not None,
                "incumbent_decision_type": incumbent_type,
                "candidate_decision_type": candidate_type,
                "incumbent_decision_result": incumbent_result,
                "candidate_decision_result": candidate_result,
                "changed": (
                    incumbent_row is None
                    or candidate_row is None
                    or incumbent_type != candidate_type
                    or incumbent_result != candidate_result
                ),
            }
        )
    return deltas


def _incident_deltas(
    incumbent_rows: Sequence[Mapping[str, Any]],
    candidate_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    left = _index_by_record_id(incumbent_rows, label="incumbent_incident")
    right = _index_by_record_id(candidate_rows, label="candidate_incident")
    deltas: list[dict[str, Any]] = []
    for record_id in sorted(set(left) | set(right)):
        incumbent_row = left.get(record_id)
        candidate_row = right.get(record_id)
        incumbent_class = (
            _token_or_unknown(incumbent_row.get("incident_class")) if incumbent_row else UNKNOWN
        )
        candidate_class = (
            _token_or_unknown(candidate_row.get("incident_class")) if candidate_row else UNKNOWN
        )
        deltas.append(
            {
                "record_id": record_id,
                "incumbent_present": incumbent_row is not None,
                "candidate_present": candidate_row is not None,
                "incumbent_incident_class": incumbent_class,
                "candidate_incident_class": candidate_class,
                "changed": (
                    incumbent_row is None
                    or candidate_row is None
                    or incumbent_class != candidate_class
                ),
            }
        )
    return deltas


def _metric_deltas(
    incumbent_metrics: Mapping[str, Any],
    candidate_metrics: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    if not isinstance(incumbent_metrics, Mapping) or not isinstance(candidate_metrics, Mapping):
        raise DdoValidationError("SHADOW_METRICS_MUST_BE_OBJECT")
    keys = sorted(set(incumbent_metrics) | set(candidate_metrics))
    out: dict[str, dict[str, Any]] = {}
    for key in keys:
        if not isinstance(key, str) or not key:
            raise DdoValidationError("SHADOW_METRIC_KEY_INVALID")
        left = incumbent_metrics[key] if key in incumbent_metrics else UNKNOWN
        right = candidate_metrics[key] if key in candidate_metrics else UNKNOWN
        out[key] = {
            "incumbent": _token_or_unknown(left),
            "candidate": _token_or_unknown(right),
            "changed": _token_or_unknown(left) != _token_or_unknown(right),
        }
    return out


def compare_shadow_challenger_v0(
    *,
    incumbent: Mapping[str, Any],
    candidate: Mapping[str, Any],
    evidence_pack: Mapping[str, Any],
    incumbent_decisions: Sequence[Mapping[str, Any]] | None = None,
    candidate_decisions: Sequence[Mapping[str, Any]] | None = None,
    incumbent_incidents: Sequence[Mapping[str, Any]] | None = None,
    candidate_incidents: Sequence[Mapping[str, Any]] | None = None,
    incumbent_metrics: Mapping[str, Any] | None = None,
    candidate_metrics: Mapping[str, Any] | None = None,
    incumbent_gates: Mapping[str, Any] | None = None,
) -> MappingProxyType[str, Any]:
    incumbent_rec, candidate_rec, pack = _require_same_pack(
        incumbent=incumbent, candidate=candidate, evidence_pack=evidence_pack
    )
    if incumbent_rec["artifact_hash"] == UNKNOWN or candidate_rec["artifact_hash"] == UNKNOWN:
        raise DdoValidationError("UNVERSIONED_CANDIDATE_FORBIDDEN")
    pack_gates = {gate: str(pack["gates"][gate]) for gate in VALIDATION_GATE_IDS_V0}
    if incumbent_gates is None:
        baseline_gates = {gate: UNKNOWN for gate in VALIDATION_GATE_IDS_V0}
    else:
        if set(incumbent_gates) != set(VALIDATION_GATE_IDS_V0):
            raise DdoValidationError("SHADOW_INCUMBENT_GATES_MUST_COVER_ALL_NAMED_GATES")
        baseline_gates = {
            gate: _token_or_unknown(incumbent_gates[gate]) for gate in VALIDATION_GATE_IDS_V0
        }
    gate_deltas = {
        gate: {
            "incumbent": baseline_gates[gate],
            "candidate": pack_gates[gate],
            "changed": baseline_gates[gate] != pack_gates[gate],
        }
        for gate in VALIDATION_GATE_IDS_V0
    }
    safety_regression = pack_gates["safety_regression_pass"] != "PASS"
    authority_regression = pack_gates["authority_invariants_pass"] != "PASS"
    return freeze_record(
        {
            "incumbent_artifact_ref": incumbent_rec["record_id"],
            "candidate_artifact_ref": candidate_rec["record_id"],
            "incumbent_artifact_hash": incumbent_rec["artifact_hash"],
            "candidate_artifact_hash": candidate_rec["artifact_hash"],
            "validation_evidence_pack_ref": pack["record_id"],
            "validation_evidence_pack_hash": pack["content_hash"],
            "identical_evidence_pack": True,
            "gate_deltas": gate_deltas,
            "decision_deltas": _decision_deltas(
                incumbent_decisions or (), candidate_decisions or ()
            ),
            "incident_deltas": _incident_deltas(
                incumbent_incidents or (), candidate_incidents or ()
            ),
            "metric_deltas": _metric_deltas(incumbent_metrics or {}, candidate_metrics or {}),
            "safety_regression": safety_regression,
            "authority_regression": authority_regression,
            "economic_improvement_cannot_compensate": True,
            "productive_authority": SHADOW_PRODUCTIVE_AUTHORITY,
            "ranking_advisory": True,
            "becomes_authoritative": SHADOW_COMPARISON_CAN_BECOME_AUTHORITATIVE,
            "incumbent_mutated": SHADOW_COMPARISON_CAN_MUTATE_INCUMBENT,
            "execution_effect": "NONE",
            "promotion_authority": "NONE",
            "comparison_cannot_authorize_promotion": True,
        }
    )
