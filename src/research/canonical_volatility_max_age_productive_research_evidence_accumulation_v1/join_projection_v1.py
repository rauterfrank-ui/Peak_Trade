"""Project productive evidence into the PR #5616 join ledger schema."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveEvidenceAccumulationError,
    ProductiveResearchEvidenceRecordV1,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    JOIN_CONTRACT_VERSION,
    CanonicalVolatilityMaxAgeResearchEvidenceJoinV1,
    append_max_age_research_evidence_ledger_record_v1,
    build_max_age_research_evidence_join_v1,
)


def project_productive_evidence_to_research_join_v1(
    record: ProductiveResearchEvidenceRecordV1,
) -> CanonicalVolatilityMaxAgeResearchEvidenceJoinV1:
    """Map productive evidence onto the existing research-evidence join contract.

    Does not invent a second competing evidence specification: join identity,
    digests, and nullability follow the design/accumulation contract consumed
    by the PR #5616 evidence loader.
    """
    if record.validation_status != "VALID":
        raise ProductiveEvidenceAccumulationError("join_projection_requires_valid_record")

    return build_max_age_research_evidence_join_v1(
        session_id=record.session_id,
        cycle_id=record.cycle_id,
        instrument_id=record.canonical_instrument_id,
        regime_id=record.regime_label,
        max_age_policy_evidence={
            "estimate_as_of_event_time": record.as_of_event_time,
            "reference_event_time": record.market_event_time,
            "computed_age_seconds": float(record.age_seconds),
            "max_age_status": "AGE_COMPUTED_THRESHOLD_UNRESOLVED",
            "threshold_status": "UNRESOLVED_MAX_AGE",
            "presence_status": "PRESENT" if record.estimate_present else "ABSENT",
            "clock_trust_status": record.clock_trust_state,
            "data_integrity_status": record.data_trust_state,
            "reuse_status": record.reuse_status,
            "restart_status": record.restart_status,
            "source_digest": record.volatility_source_digest,
            "decision": "AGE_COMPUTED",
            "reason_code": "VOLATILITY_ESTIMATE_AGE_UNRESOLVED",
            "enforcement_applied": False,
            "numeric_threshold_selected": False,
            "session_id": record.session_id,
            "cycle_id": record.cycle_id,
            "instrument_id": record.canonical_instrument_id,
            "regime_id": record.regime_label,
        },
        producer_outcome="PRODUCED" if record.estimate_present else "ABSENT",
        reuse_status=record.reuse_status,
        restart_status=record.restart_status,
        restart_without_estimate=record.restart_status == "RESTART_WITHOUT_ESTIMATE",
        estimate_present=record.estimate_present,
        observation_count=record.volatility_observation_count,
        source_digest=record.volatility_source_digest,
        decision_outcome=record.decision_outcome,
        selected_side=record.selected_side,
        economic_metrics=record.economic_metrics,
        join_contract_version=JOIN_CONTRACT_VERSION,
    )


def assert_join_compatibility_matrix_v1(
    record: ProductiveResearchEvidenceRecordV1,
    join: CanonicalVolatilityMaxAgeResearchEvidenceJoinV1,
) -> dict[str, Any]:
    payload = join.to_dict()
    checks = {
        "schema_compatible": payload.get("join_contract_version") == JOIN_CONTRACT_VERSION,
        "digest_present": bool(payload.get("join_digest")),
        "session_key_match": payload.get("session_id") == record.session_id,
        "regime_key_match": payload.get("regime_id") == record.regime_label,
        "age_field_match": float(payload.get("computed_age_seconds")) == float(record.age_seconds),
        "volatility_provenance_match": payload.get("source_digest")
        == record.volatility_source_digest,
        "restart_field_present": payload.get("restart_status") == record.restart_status,
        "reuse_field_present": payload.get("reuse_status") == record.reuse_status,
        "threshold_unresolved": payload.get("threshold_status") == "UNRESOLVED_MAX_AGE",
        "enforcement_false": payload.get("enforcement_applied") is False,
        "nullability_ok": payload.get("reference_event_time") is not None
        and payload.get("estimate_as_of_event_time") is not None,
    }
    if not all(checks.values()):
        failed = [k for k, v in checks.items() if not v]
        raise ProductiveEvidenceAccumulationError("join_compatibility_failed:" + ",".join(failed))
    return checks


def append_join_projection_to_ledger_v1(
    *,
    join_ledger_path: Path,
    record: ProductiveResearchEvidenceRecordV1,
) -> CanonicalVolatilityMaxAgeResearchEvidenceJoinV1:
    join = project_productive_evidence_to_research_join_v1(record)
    assert_join_compatibility_matrix_v1(record, join)
    return append_max_age_research_evidence_ledger_record_v1(
        ledger_path=join_ledger_path,
        record=join,
    )


def join_payload_from_mapping_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    return dict(payload)
