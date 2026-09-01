"""Fixture-only incumbent vs candidate challenger comparison v0.

Zero productive authority. Comparison is only valid on an identical
ValidationEvidencePack identity.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import freeze_record
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.learning_records_v0 import (
    validate_candidate_artifact_v0,
    validate_validation_evidence_pack_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import VALIDATION_GATE_IDS_V0

CHALLENGER_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
CHALLENGER_RANKING_IS_ADVISORY: Final[bool] = True


def compare_challenger_v0(
    *,
    incumbent: Mapping[str, Any],
    candidate: Mapping[str, Any],
    evidence_pack: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    incumbent_rec = validate_candidate_artifact_v0(incumbent)
    candidate_rec = validate_candidate_artifact_v0(candidate)
    pack = validate_validation_evidence_pack_v0(evidence_pack)
    if pack["candidate_artifact_ref"] != candidate_rec["record_id"]:
        raise DdoValidationError("CHALLENGER_PACK_CANDIDATE_MISMATCH")
    if pack["incumbent_artifact_ref"] != incumbent_rec["record_id"]:
        raise DdoValidationError("CHALLENGER_PACK_INCUMBENT_MISMATCH")
    if incumbent_rec["record_id"] == candidate_rec["record_id"]:
        raise DdoValidationError("CHALLENGER_INCUMBENT_EQUALS_CANDIDATE")
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
            "productive_authority": "NONE",
            "ranking_advisory": True,
        }
    )
