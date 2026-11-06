"""Offline learning registry v0.

Append-only view over the DDO ledger for hypotheses, candidates, and
validation packs. Unversioned candidates cannot enter evaluated
validation. Rejected and superseded candidates remain auditable.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_CANDIDATE_ARTIFACT,
    SCHEMA_NAME_LEARNING_HYPOTHESIS,
    SCHEMA_NAME_VALIDATION_EVIDENCE_PACK,
    freeze_record,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import (
    AppendOnlyDdoLedgerV0,
    AppendResultV0,
)
from src.learning.deterministic_decision_outcome_v0.learning_records_v0 import (
    validate_candidate_artifact_v0,
    validate_learning_hypothesis_v0,
    validate_validation_evidence_pack_v0,
)
from src.learning.deterministic_decision_outcome_v0.validation_pack_engine_v0 import (
    VALIDATION_PACK_ENGINE_ID,
)


class OfflineLearningRegistryV0:
    """Typed registry facade. Persistence is the append-only ledger."""

    def __init__(self, ledger: AppendOnlyDdoLedgerV0) -> None:
        self._ledger = ledger

    def register_hypothesis(
        self, payload: Mapping[str, Any], *, ingested_at_utc: str | None = None
    ) -> AppendResultV0:
        validate_learning_hypothesis_v0(payload)
        return self._ledger.append(payload, ingested_at_utc=ingested_at_utc)

    def register_candidate(
        self, payload: Mapping[str, Any], *, ingested_at_utc: str | None = None
    ) -> AppendResultV0:
        candidate = validate_candidate_artifact_v0(payload)
        if not candidate.get("schema_version"):
            raise DdoValidationError("UNVERSIONED_CANDIDATE_FORBIDDEN")
        if candidate.get("artifact_hash") in (None, ""):
            raise DdoValidationError("UNVERSIONED_CANDIDATE_FORBIDDEN")
        return self._ledger.append(payload, ingested_at_utc=ingested_at_utc)

    def register_validation_pack(
        self, payload: Mapping[str, Any], *, ingested_at_utc: str | None = None
    ) -> AppendResultV0:
        pack = validate_validation_evidence_pack_v0(payload)
        candidate = self._ledger.get(str(pack["candidate_artifact_ref"]))
        if candidate["schema_name"] != SCHEMA_NAME_CANDIDATE_ARTIFACT:
            raise DdoValidationError("VALIDATION_PACK_CANDIDATE_TYPE_MISMATCH")
        if candidate.get("rejected") is True:
            # Rejected candidates remain auditable and may still be packed.
            pass
        return self._ledger.append(payload, ingested_at_utc=ingested_at_utc)

    def register_evaluated_validation_pack(
        self, payload: Mapping[str, Any], *, ingested_at_utc: str | None = None
    ) -> AppendResultV0:
        pack = validate_validation_evidence_pack_v0(payload)
        if pack.get("producer_id") != VALIDATION_PACK_ENGINE_ID:
            raise DdoValidationError("EVALUATED_PACK_REQUIRES_VALIDATION_PACK_ENGINE")
        candidate = self._ledger.get(str(pack["candidate_artifact_ref"]))
        if candidate["schema_name"] != SCHEMA_NAME_CANDIDATE_ARTIFACT:
            raise DdoValidationError("VALIDATION_PACK_CANDIDATE_TYPE_MISMATCH")
        if candidate.get("artifact_hash") in (None, "", UNKNOWN):
            raise DdoValidationError("UNVERSIONED_CANDIDATE_FORBIDDEN")
        return self._ledger.append(payload, ingested_at_utc=ingested_at_utc)

    def hypotheses(self) -> tuple[MappingProxyType[str, Any], ...]:
        return tuple(
            row
            for row in self._ledger.read_all()
            if row["schema_name"] == SCHEMA_NAME_LEARNING_HYPOTHESIS
        )

    def candidates(
        self, *, include_rejected: bool = True
    ) -> tuple[MappingProxyType[str, Any], ...]:
        rows = [
            row
            for row in self._ledger.read_all()
            if row["schema_name"] == SCHEMA_NAME_CANDIDATE_ARTIFACT
        ]
        if include_rejected:
            return tuple(rows)
        return tuple(row for row in rows if row.get("rejected") is not True)

    def validation_packs(self) -> tuple[MappingProxyType[str, Any], ...]:
        return tuple(
            row
            for row in self._ledger.read_all()
            if row["schema_name"] == SCHEMA_NAME_VALIDATION_EVIDENCE_PACK
        )

    def superseded_ids(self) -> frozenset[str]:
        ids: set[str] = set()
        for row in self.candidates(include_rejected=True):
            target = row.get("supersedes_id")
            if target:
                ids.add(str(target))
        return frozenset(ids)

    def candidate_lineage(self, candidate_id: str) -> MappingProxyType[str, Any]:
        candidate = self._ledger.get(candidate_id)
        if candidate["schema_name"] != SCHEMA_NAME_CANDIDATE_ARTIFACT:
            raise DdoValidationError("CANDIDATE_LINEAGE_TYPE_MISMATCH")
        hypothesis = self._ledger.get(str(candidate["hypothesis_ref"]))
        return freeze_record(
            {
                "candidate_artifact_ref": candidate["record_id"],
                "hypothesis_ref": candidate["hypothesis_ref"],
                "hypothesis_record_id": hypothesis["record_id"],
                "experiment_ref": candidate.get("experiment_ref"),
                "dataset_ref": candidate.get("dataset_ref"),
                "artifact_hash": candidate["artifact_hash"],
                "rejected": candidate["rejected"],
                "supersedes_id": candidate.get("supersedes_id"),
                "corrects_id": candidate.get("corrects_id"),
                "is_superseded": str(candidate["record_id"]) in self.superseded_ids(),
                "evidence_source_refs": list(candidate.get("evidence_source_refs") or []),
                "causal_parent_ids": list(candidate.get("causal_parent_ids") or []),
            }
        )
