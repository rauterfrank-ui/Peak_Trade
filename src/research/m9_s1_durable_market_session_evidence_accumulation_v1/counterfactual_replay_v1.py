"""Deterministic offline replay: join ledger → 8-candidate counterfactual diagnostics."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.evidence_loader_v1 import (
    ResearchEvidenceRecordV1,
    load_research_evidence_records_v1,
    stable_records_fingerprint_v1,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.constants_v1 import (
    COUNTERFACTUAL_CANDIDATE_MAX_AGE_SECONDS,
    COUNTERFACTUAL_ONLY,
    REPLAY_ARTIFACT_SCHEMA_VERSION,
    WORKPACKAGE_ID,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.models_v1 import (
    M9S1EvidenceAccumulationError,
    digest_excluding_keys,
    sha256_hex,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    CounterfactualAgeLabelV1,
    evaluate_counterfactual_max_age_threshold_diagnostic_v1,
)


def _candidate_summary(
    records: Sequence[ResearchEvidenceRecordV1],
    *,
    candidate_max_age_seconds: int,
) -> dict[str, Any]:
    observation_count = len(records)
    valid_age = 0
    missing_invalid = 0
    fresh = 0
    stale = 0
    sessions: set[str] = set()
    source_epochs: list[float] = []

    for record in records:
        sessions.add(record.session_id)
        if record.event_time_epoch_seconds is not None:
            source_epochs.append(float(record.event_time_epoch_seconds))
        age = record.computed_age_seconds
        if age is None or record.estimate_present is False:
            missing_invalid += 1
            continue
        valid_age += 1
        diagnostic = evaluate_counterfactual_max_age_threshold_diagnostic_v1(
            computed_age_seconds=float(age),
            candidate_max_age_seconds_argument=float(candidate_max_age_seconds),
        )
        if diagnostic.enforcement_applied or diagnostic.alpha_decision_mutated:
            raise M9S1EvidenceAccumulationError("counterfactual_authority_leak")
        label = diagnostic.counterfactual_label
        if label == CounterfactualAgeLabelV1.WOULD_BE_FRESH_IF_THRESHOLD.value:
            fresh += 1
        elif label == CounterfactualAgeLabelV1.WOULD_BE_STALE_IF_THRESHOLD.value:
            stale += 1
        else:
            missing_invalid += 1

    denom = max(observation_count, 1)
    return {
        "candidate_max_age_seconds": int(candidate_max_age_seconds),
        "observation_count": observation_count,
        "valid_age_count": valid_age,
        "missing_invalid_count": missing_invalid,
        "would_be_fresh_count": fresh,
        "would_be_stale_count": stale,
        "would_be_fresh_rate": fresh / denom,
        "would_be_stale_rate": stale / denom,
        "session_coverage_count": len(sessions),
        "temporal_coverage": {
            "first_event_epoch_seconds": min(source_epochs) if source_epochs else None,
            "last_event_epoch_seconds": max(source_epochs) if source_epochs else None,
        },
        "counterfactual_only": COUNTERFACTUAL_ONLY,
        "ranking": None,
    }


def run_counterfactual_replay_v1(
    *,
    join_ledger_path: Path,
    candidate_seconds: Sequence[int] | None = None,
    config_domain_digest: str | None = None,
) -> dict[str, Any]:
    grid = tuple(
        int(x)
        for x in (
            candidate_seconds
            if candidate_seconds is not None
            else COUNTERFACTUAL_CANDIDATE_MAX_AGE_SECONDS
        )
    )
    if grid != COUNTERFACTUAL_CANDIDATE_MAX_AGE_SECONDS:
        raise M9S1EvidenceAccumulationError("candidate_grid_must_match_operator_bound_domain")

    records = load_research_evidence_records_v1(Path(join_ledger_path))
    input_digest = stable_records_fingerprint_v1(records)
    domain_digest = config_domain_digest or sha256_hex(
        {"candidate_max_age_seconds": list(grid), "workpackage_id": WORKPACKAGE_ID}
    )

    per_candidate = [
        _candidate_summary(records, candidate_max_age_seconds=int(seconds)) for seconds in grid
    ]
    artifact = {
        "schema_version": REPLAY_ARTIFACT_SCHEMA_VERSION,
        "workpackage_id": WORKPACKAGE_ID,
        "join_ledger_path": str(join_ledger_path),
        "input_record_digest": input_digest,
        "config_domain_digest": domain_digest,
        "candidate_max_age_seconds": list(grid),
        "observation_count": len(records),
        "per_candidate": per_candidate,
        "counterfactual_only": COUNTERFACTUAL_ONLY,
        "enforcement_applied": False,
        "numeric_threshold_selected": False,
        "productive_threshold_recommendation": None,
    }
    artifact["artifact_digest"] = digest_excluding_keys(
        artifact, exclude=frozenset({"artifact_digest"})
    )
    return artifact
