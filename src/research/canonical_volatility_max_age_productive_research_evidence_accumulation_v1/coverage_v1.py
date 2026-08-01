"""Coverage readiness evaluation against existing preregistered contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    COVERAGE_SCHEMA_VERSION,
    ENFORCEMENT_APPLIED,
    THRESHOLD_STATUS,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.ledger_v1 import (
    RECORD_KIND_EVIDENCE,
    RECORD_KIND_QUARANTINE,
    load_productive_evidence_ledger_v1,
    valid_productive_records_from_ledger_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    CoverageReadinessReportV1,
    ProductiveEvidenceSessionV1,
    ProductiveResearchEvidenceRecordV1,
    SessionLifecycleStateV1,
    ValidationStatusV1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.session_v1 import (
    session_from_mapping_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.validation_v1 import (
    parse_event_time,
    productive_record_from_mapping_v1,
    validate_productive_evidence_record_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    MINIMUM_EVIDENCE_COUNT,
    MINIMUM_REGIME_COUNT,
    MINIMUM_SESSION_COUNT,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    MINIMUM_EVIDENCE_REQUIREMENTS_V1,
)


def evaluate_coverage_readiness_v1(
    *,
    records: Sequence[ProductiveResearchEvidenceRecordV1],
    sessions: Sequence[ProductiveEvidenceSessionV1] = (),
    invalid_count: int = 0,
    quarantined_count: int = 0,
    duplicate_count: int = 0,
) -> CoverageReadinessReportV1:
    """Evaluate coverage using existing design + research-execution minima only."""
    valid = []
    for record in records:
        status, _ = validate_productive_evidence_record_v1(record)
        if status == ValidationStatusV1.VALID:
            valid.append(record)

    sessions_ids = sorted({r.session_id for r in valid})
    regimes = sorted({r.regime_label for r in valid})
    per_session: dict[str, int] = {}
    per_regime: dict[str, int] = {}
    for record in valid:
        per_session[record.session_id] = per_session.get(record.session_id, 0) + 1
        per_regime[record.regime_label] = per_regime.get(record.regime_label, 0) + 1

    event_times = [r.market_event_time for r in valid]
    first_event = min(event_times) if event_times else None
    last_event = max(event_times) if event_times else None
    span: Optional[float] = None
    if first_event and last_event:
        span = (
            parse_event_time(last_event, field_name="last_event_time")
            - parse_event_time(first_event, field_name="first_event_time")
        ).total_seconds()

    restart_count = len(
        {(r.session_id, r.restart_generation) for r in valid if r.restart_generation > 0}
    )
    reused = sum(1 for r in valid if r.estimate_reused)
    fresh = sum(1 for r in valid if not r.estimate_reused)
    fallback = sum(1 for r in valid if r.fallback_used)
    trusted = sum(
        1 for r in valid if r.clock_trust_state == "TRUSTED" and r.data_trust_state == "TRUSTED"
    )
    untrusted = len(valid) - trusted

    completed_sessions = sum(
        1 for s in sessions if s.lifecycle_state == SessionLifecycleStateV1.COMPLETED.value
    )
    if not sessions:
        # Infer completed sessions only when end times are present on records.
        completed_sessions = len(
            {r.session_id for r in valid if r.session_end_event_time is not None}
        )

    design_min = dict(MINIMUM_EVIDENCE_REQUIREMENTS_V1)
    gaps: list[str] = []
    if len(valid) < int(MINIMUM_EVIDENCE_COUNT):
        gaps.append("MINIMUM_EVIDENCE_COUNT")
    if len(sessions_ids) < int(MINIMUM_SESSION_COUNT):
        gaps.append("MINIMUM_SESSION_COUNT")
    if len(regimes) < int(MINIMUM_REGIME_COUNT):
        gaps.append("MINIMUM_REGIME_COUNT")
    if len(sessions_ids) < int(design_min["minimum_distinct_sessions"]):
        gaps.append("DESIGN_MINIMUM_DISTINCT_SESSIONS")
    if len(regimes) < int(design_min["minimum_distinct_regimes"]):
        gaps.append("DESIGN_MINIMUM_DISTINCT_REGIMES")
    instruments = {r.canonical_instrument_id for r in valid}
    if len(instruments) < int(design_min["minimum_distinct_instruments"]):
        gaps.append("DESIGN_MINIMUM_DISTINCT_INSTRUMENTS")
    age_obs = sum(1 for r in valid if r.age_seconds is not None)
    if age_obs < int(design_min["minimum_computed_age_observations"]):
        gaps.append("DESIGN_MINIMUM_COMPUTED_AGE_OBSERVATIONS")
    if design_min.get("require_reuse_and_restart_label_coverage"):
        reuse_labels = {r.reuse_status for r in valid}
        restart_labels = {r.restart_status for r in valid}
        if not reuse_labels or not restart_labels:
            gaps.append("DESIGN_REUSE_RESTART_LABEL_COVERAGE")
    if design_min.get("require_durable_or_in_memory_ledger_records") and not valid:
        gaps.append("DESIGN_DURABLE_OR_IN_MEMORY_LEDGER_RECORDS")

    multi_session = len(sessions_ids) >= int(MINIMUM_SESSION_COUNT)
    multi_regime = len(regimes) >= int(MINIMUM_REGIME_COUNT)
    ready = not gaps

    return CoverageReadinessReportV1(
        coverage_schema_version=COVERAGE_SCHEMA_VERSION,
        valid_evidence_count=len(valid),
        invalid_evidence_count=int(invalid_count),
        quarantined_evidence_count=int(quarantined_count),
        duplicate_evidence_count=int(duplicate_count),
        session_count=len(sessions_ids),
        completed_session_count=completed_sessions,
        regime_count=len(regimes),
        observations_per_session=per_session,
        observations_per_regime=per_regime,
        event_time_span_seconds=span,
        first_event_time=first_event,
        last_event_time=last_event,
        restart_count=restart_count,
        reused_estimate_count=reused,
        fresh_estimate_count=fresh,
        fallback_record_count=fallback,
        trusted_record_count=trusted,
        untrusted_record_count=untrusted,
        multi_session_coverage=multi_session,
        multi_regime_coverage=multi_regime,
        coverage_gaps=tuple(sorted(set(gaps))),
        ready_for_research_execution=ready,
        readiness_authority=(
            "MINIMUM_EVIDENCE_REQUIREMENTS_V1+"
            "research_execution_MINIMUM_SESSION_REGIME_EVIDENCE_COUNTS"
        ),
        threshold_status=THRESHOLD_STATUS,
        enforcement_applied=ENFORCEMENT_APPLIED,
    )


def evaluate_coverage_from_ledger_v1(
    *,
    productive_ledger_path: Path,
    quarantine_ledger_path: Path | None = None,
    sessions: Sequence[Mapping[str, Any]] | Sequence[ProductiveEvidenceSessionV1] = (),
) -> CoverageReadinessReportV1:
    valid = valid_productive_records_from_ledger_v1(productive_ledger_path)
    envelopes = load_productive_evidence_ledger_v1(productive_ledger_path)
    invalid = 0
    duplicates = 0
    for env in envelopes:
        if env.record_kind != RECORD_KIND_EVIDENCE:
            continue
        record = productive_record_from_mapping_v1(env.productive_evidence)
        status, _ = validate_productive_evidence_record_v1(record)
        if status != ValidationStatusV1.VALID:
            invalid += 1
        if record.duplicate_status in {
            "DUPLICATE_IDEMPOTENT",
            "DUPLICATE_CONFLICT",
        }:
            duplicates += 1

    quarantined = 0
    if quarantine_ledger_path is not None and Path(quarantine_ledger_path).exists():
        for env in load_productive_evidence_ledger_v1(quarantine_ledger_path):
            if env.record_kind == RECORD_KIND_QUARANTINE:
                quarantined += 1

    typed_sessions: list[ProductiveEvidenceSessionV1] = []
    for item in sessions:
        if isinstance(item, ProductiveEvidenceSessionV1):
            typed_sessions.append(item)
        else:
            typed_sessions.append(session_from_mapping_v1(item))

    return evaluate_coverage_readiness_v1(
        records=valid,
        sessions=typed_sessions,
        invalid_count=invalid,
        quarantined_count=quarantined,
        duplicate_count=duplicates,
    )
