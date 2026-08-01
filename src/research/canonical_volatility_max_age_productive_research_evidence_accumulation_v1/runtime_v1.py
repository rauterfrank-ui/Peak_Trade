"""Productive accumulation runtime bound to the diagnostic bridge/shadow path."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    CAPABILITY_ID,
    CAPABILITY_VERSION,
    DEFAULT_JOIN_LEDGER_RELATIVE_PATH,
    DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH,
    DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH,
    EVIDENCE_WRITE_FAILURE_BEHAVIOR,
    HARD_STOP,
    THRESHOLD_STATUS,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.coverage_v1 import (
    evaluate_coverage_from_ledger_v1,
    evaluate_coverage_readiness_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.join_projection_v1 import (
    append_join_projection_to_ledger_v1,
    project_productive_evidence_to_research_join_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.ledger_v1 import (
    append_productive_evidence_record_v1,
    valid_productive_records_from_ledger_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveEvidenceAccumulationError,
    ProductiveEvidenceSessionV1,
    ValidationStatusV1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.producer_v1 import (
    produce_productive_research_evidence_from_cycle_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.session_v1 import (
    complete_productive_evidence_session_v1,
    note_observation_on_session_v1,
    open_productive_evidence_session_v1,
    resume_productive_evidence_session_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.validation_v1 import (
    attach_validation_v1,
)


@dataclass
class ProductiveEvidenceAccumulationStateV1:
    session: ProductiveEvidenceSessionV1
    repository_sha: str
    productive_ledger_path: Path
    join_ledger_path: Path
    quarantine_ledger_path: Path
    prior_source_estimate_id: Optional[str] = None
    prior_reuse_count: int = 0
    prior_cycle_id: Optional[str] = None
    in_memory_join_ledger: list[dict[str, Any]] = field(default_factory=list)
    last_result: dict[str, Any] | None = None
    write_failures: list[dict[str, Any]] = field(default_factory=list)


def bind_accumulation_state_v1(
    *,
    session_id: str,
    session_start_event_time: str,
    repository_sha: str,
    venue: str,
    canonical_instrument_id: str,
    venue_instrument_id: str,
    repo_root: Path,
    productive_ledger_path: Path | None = None,
    join_ledger_path: Path | None = None,
    quarantine_ledger_path: Path | None = None,
    existing_session: ProductiveEvidenceSessionV1 | None = None,
    resume_token: str | None = None,
    process_restart: bool = False,
    restore_reuse_cursor_from_ledger: bool = True,
) -> ProductiveEvidenceAccumulationStateV1:
    root = Path(repo_root)
    if existing_session is not None:
        if resume_token is None:
            raise ProductiveEvidenceAccumulationError("resume_token_required")
        session = resume_productive_evidence_session_v1(
            existing_session,
            resume_token=resume_token,
            repository_sha=repository_sha,
            process_restart=process_restart,
        )
    else:
        session = open_productive_evidence_session_v1(
            session_id=session_id,
            session_start_event_time=session_start_event_time,
            repository_sha=repository_sha,
            venue=venue,
            canonical_instrument_id=canonical_instrument_id,
            venue_instrument_id=venue_instrument_id,
        )
    state = ProductiveEvidenceAccumulationStateV1(
        session=session,
        repository_sha=repository_sha,
        productive_ledger_path=Path(
            productive_ledger_path or (root / DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH)
        ),
        join_ledger_path=Path(join_ledger_path or (root / DEFAULT_JOIN_LEDGER_RELATIVE_PATH)),
        quarantine_ledger_path=Path(
            quarantine_ledger_path or (root / DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH)
        ),
    )
    if restore_reuse_cursor_from_ledger and state.productive_ledger_path.exists():
        for record in reversed(
            valid_productive_records_from_ledger_v1(state.productive_ledger_path)
        ):
            if record.session_id != session.session_id:
                continue
            state.prior_source_estimate_id = record.source_estimate_id
            state.prior_reuse_count = record.reuse_count
            state.prior_cycle_id = record.cycle_id
            break
    return state


def accumulate_productive_research_evidence_from_cycle_v1(
    cycle: Mapping[str, Any],
    *,
    state: ProductiveEvidenceAccumulationStateV1,
    project_to_join_ledger: bool = True,
) -> dict[str, Any]:
    """Diagnostic accumulation path: never mutates trading behavior on write failure."""
    try:
        record = produce_productive_research_evidence_from_cycle_v1(
            cycle,
            session=state.session,
            repository_sha=state.repository_sha,
            prior_source_estimate_id=state.prior_source_estimate_id,
            prior_reuse_count=state.prior_reuse_count,
            prior_cycle_id=state.prior_cycle_id,
        )
        record = attach_validation_v1(record)
        join = None
        join_payload = None
        if record.validation_status == ValidationStatusV1.VALID.value:
            join = project_productive_evidence_to_research_join_v1(record)
            join_payload = join.to_dict()

        append_result = append_productive_evidence_record_v1(
            ledger_path=state.productive_ledger_path,
            quarantine_ledger_path=state.quarantine_ledger_path,
            record=record,
            research_join=join_payload,
        )

        if (
            append_result.get("action") == "APPENDED"
            and project_to_join_ledger
            and record.validation_status == ValidationStatusV1.VALID.value
        ):
            join = append_join_projection_to_ledger_v1(
                join_ledger_path=state.join_ledger_path,
                record=record,
            )
            join_payload = join.to_dict()
            state.in_memory_join_ledger.append(dict(join_payload))

        if append_result.get("action") == "APPENDED":
            state.session = note_observation_on_session_v1(state.session)
            state.prior_source_estimate_id = record.source_estimate_id
            state.prior_reuse_count = record.reuse_count
            state.prior_cycle_id = record.cycle_id

        result = {
            "append_result": append_result,
            "capability_id": CAPABILITY_ID,
            "capability_version": CAPABILITY_VERSION,
            "evidence_record": record.to_dict(),
            "evidence_write_failure_behavior": EVIDENCE_WRITE_FAILURE_BEHAVIOR,
            "hard_stop": HARD_STOP,
            "research_join": join_payload,
            "session": state.session.to_dict(),
            "status": "PASS",
            "threshold_status": THRESHOLD_STATUS,
            "trading_behavior_mutated": False,
        }
        state.last_result = result
        return result
    except Exception as exc:  # noqa: BLE001 — diagnostic boundary by contract
        failure = {
            "error": str(exc),
            "error_type": type(exc).__name__,
            "evidence_write_failure_behavior": EVIDENCE_WRITE_FAILURE_BEHAVIOR,
            "status": "EVIDENCE_WRITE_FAILURE",
            "trading_behavior_mutated": False,
        }
        state.write_failures.append(failure)
        state.last_result = failure
        return failure


def complete_accumulation_session_v1(
    state: ProductiveEvidenceAccumulationStateV1,
    *,
    session_end_event_time: str,
) -> dict[str, Any]:
    state.session = complete_productive_evidence_session_v1(
        state.session,
        session_end_event_time=session_end_event_time,
    )
    coverage = evaluate_coverage_from_ledger_v1(
        productive_ledger_path=state.productive_ledger_path,
        quarantine_ledger_path=state.quarantine_ledger_path,
        sessions=[state.session],
    )
    return {
        "coverage": coverage.to_dict(),
        "session": state.session.to_dict(),
        "status": "PASS",
        "threshold_status": THRESHOLD_STATUS,
    }


def reconstruct_coverage_from_ledgers_v1(
    *,
    productive_ledger_path: Path,
    quarantine_ledger_path: Path | None = None,
    sessions: list[ProductiveEvidenceSessionV1] | None = None,
) -> dict[str, Any]:
    records = valid_productive_records_from_ledger_v1(productive_ledger_path)
    coverage = evaluate_coverage_from_ledger_v1(
        productive_ledger_path=productive_ledger_path,
        quarantine_ledger_path=quarantine_ledger_path,
        sessions=sessions or (),
    )
    return {
        "coverage": coverage.to_dict(),
        "record_count": len(records),
        "status": "PASS",
    }


def accumulate_from_cycles_batch_v1(
    cycles: list[Mapping[str, Any]],
    *,
    state: ProductiveEvidenceAccumulationStateV1,
    complete_session: bool = True,
) -> dict[str, Any]:
    results = []
    for cycle in cycles:
        results.append(accumulate_productive_research_evidence_from_cycle_v1(cycle, state=state))
    completion = None
    if complete_session and cycles:
        end = cycles[-1].get("market_event_time") or (
            cycles[-1].get("double_play_typed_volatility_presence_gate") or {}
        ).get("max_age_policy_evidence", {}).get("reference_event_time")
        if end:
            completion = complete_accumulation_session_v1(state, session_end_event_time=str(end))
    coverage = evaluate_coverage_readiness_v1(
        records=valid_productive_records_from_ledger_v1(state.productive_ledger_path),
        sessions=[state.session],
        invalid_count=sum(1 for r in results if r.get("status") == "EVIDENCE_WRITE_FAILURE"),
        quarantined_count=sum(
            1 for r in results if (r.get("append_result") or {}).get("action") == "QUARANTINED"
        ),
        duplicate_count=sum(
            1 for r in results if (r.get("append_result") or {}).get("action") == "IDEMPOTENT_NOOP"
        ),
    )
    return {
        "completion": completion,
        "coverage": coverage.to_dict(),
        "cycle_results": results,
        "ready_for_research_execution": coverage.ready_for_research_execution,
        "status": "PASS",
        "threshold_status": THRESHOLD_STATUS,
        "write_failures": list(state.write_failures),
    }
