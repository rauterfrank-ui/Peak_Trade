"""Offline learning registry v0.

Append-only view over the DDO ledger for hypotheses, candidates, and
validation packs. Unversioned candidates cannot enter validation. Rejected
candidates remain auditable.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_CANDIDATE_ARTIFACT,
    SCHEMA_NAME_LEARNING_HYPOTHESIS,
    SCHEMA_NAME_VALIDATION_EVIDENCE_PACK,
)
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
