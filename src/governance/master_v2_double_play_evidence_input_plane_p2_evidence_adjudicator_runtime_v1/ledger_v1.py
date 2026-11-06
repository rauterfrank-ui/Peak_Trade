"""In-memory idempotency and conflict slot tracking for bounded adjudication."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.digest_v1 import (
    compute_intake_fingerprint_digest_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.models_v1 import (
    EvidenceIntakeRecordV1,
    MasterV2EvidenceAdjudicationResultV1,
)


@dataclass
class AdjudicationLedgerV1:
    delivery_results: dict[str, MasterV2EvidenceAdjudicationResultV1] = field(default_factory=dict)
    delivery_fingerprints: dict[str, str] = field(default_factory=dict)
    admitted_slots: dict[tuple[str, int, str, str], str] = field(default_factory=dict)

    def slot_key(self, intake: EvidenceIntakeRecordV1) -> tuple[str, int, str, str]:
        return (
            intake.instrument.instrument_id,
            intake.market_observation_epoch,
            intake.evidence_kind.value,
            intake.producer_family.value,
        )

    def prior_delivery_result(
        self, intake: EvidenceIntakeRecordV1
    ) -> MasterV2EvidenceAdjudicationResultV1 | None:
        prior = self.delivery_results.get(intake.delivery_id)
        if prior is None:
            return None
        fingerprint = compute_intake_fingerprint_digest_v1(intake)
        if self.delivery_fingerprints.get(intake.delivery_id) != fingerprint:
            return None
        return prior

    def record_result(
        self, intake: EvidenceIntakeRecordV1, result: MasterV2EvidenceAdjudicationResultV1
    ) -> None:
        self.delivery_results[intake.delivery_id] = result
        self.delivery_fingerprints[intake.delivery_id] = compute_intake_fingerprint_digest_v1(
            intake
        )
        if result.disposition == "ADMIT" and result.envelope is not None:
            self.admitted_slots[self.slot_key(intake)] = intake.source_evidence_digest
