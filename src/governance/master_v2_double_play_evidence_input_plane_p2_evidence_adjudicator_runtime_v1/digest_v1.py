"""Deterministic digests for P2 adjudication artifacts."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Mapping

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.digest_v1 import (
    compute_envelope_digest_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.models_v1 import (
    EvidenceIntakeRecordV1,
    MasterV2EvidenceAdjudicationResultV1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256


def intake_fingerprint_v1(intake: EvidenceIntakeRecordV1) -> dict[str, Any]:
    return {
        "delivery_id": intake.delivery_id,
        "envelope_id": intake.envelope_id,
        "producer_id": intake.producer_id,
        "producer_version": intake.producer_version,
        "evidence_type_version": intake.evidence_type_version,
        "producer_family": intake.producer_family.value,
        "evidence_kind": intake.evidence_kind.value,
        "instrument": asdict(intake.instrument),
        "market_observation_epoch": intake.market_observation_epoch,
        "observed_at_unix": intake.observed_at_unix,
        "freshness_horizon_seconds": intake.freshness_horizon_seconds,
        "source_evidence_digest": intake.source_evidence_digest,
        "typed_payload_digest": intake.typed_payload_digest,
        "provenance_refs": list(intake.provenance_refs),
        "lineage_refs": list(intake.lineage_refs),
        "confidence_score": intake.confidence_score,
        "quality_score": intake.quality_score,
    }


def compute_intake_fingerprint_digest_v1(intake: EvidenceIntakeRecordV1) -> str:
    payload = intake_fingerprint_v1(intake)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return compute_content_sha256({"canonical_json": canonical})


def adjudication_payload_for_digest_v1(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "adjudication_digest": None,
        "dedup_replay": result.get("dedup_replay"),
        "delivery_id": result.get("delivery_id"),
        "disposition": result.get("disposition"),
        "envelope_digest": result.get("envelope_digest"),
        "reason_codes": list(result.get("reason_codes") or ()),
    }


def compute_adjudication_digest_v1(
    *,
    delivery_id: str,
    disposition: str,
    reason_codes: tuple[str, ...],
    envelope_digest: str | None,
    dedup_replay: bool,
) -> str:
    payload = {
        "delivery_id": delivery_id,
        "disposition": disposition,
        "reason_codes": list(reason_codes),
        "envelope_digest": envelope_digest,
        "dedup_replay": dedup_replay,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return compute_content_sha256({"canonical_json": canonical})


def envelope_digest_from_model_v1(envelope: Mapping[str, Any]) -> str:
    return compute_envelope_digest_v1(envelope)


def finalize_adjudication_digest_v1(
    result: MasterV2EvidenceAdjudicationResultV1,
) -> MasterV2EvidenceAdjudicationResultV1:
    digest = compute_adjudication_digest_v1(
        delivery_id=result.delivery_id,
        disposition=result.disposition,
        reason_codes=result.reason_codes,
        envelope_digest=result.envelope_digest,
        dedup_replay=result.dedup_replay,
    )
    return MasterV2EvidenceAdjudicationResultV1(
        delivery_id=result.delivery_id,
        disposition=result.disposition,
        reason_codes=result.reason_codes,
        adjudication_digest=digest,
        envelope=result.envelope,
        envelope_digest=result.envelope_digest,
        dedup_replay=result.dedup_replay,
    )
