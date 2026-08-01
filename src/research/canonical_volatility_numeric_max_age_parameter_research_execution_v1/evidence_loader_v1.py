"""Fail-closed loader for joinable max-age research evidence."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    AUTHORITY_SCOPE,
    INPUT_EVIDENCE_MANIFEST_SCHEMA_VERSION,
    MINIMUM_EVIDENCE_COUNT,
    MINIMUM_REGIME_COUNT,
    MINIMUM_SESSION_COUNT,
    NON_AUTHORITY_SCOPE,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.contracts_v1 import (
    MaxAgeResearchExecutionError,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.serialization_v1 import (
    digest_excluding_keys,
    sha256_hex_bytes,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    JOIN_CONTRACT_VERSION,
    MaxAgeResearchDesignContractError,
    load_max_age_research_evidence_ledger_v1,
)


@dataclass(frozen=True)
class ResearchEvidenceRecordV1:
    session_id: str
    cycle_id: str
    instrument_id: str
    regime_id: str
    join_contract_version: str
    join_digest: str
    volatility_source_digest: Optional[str]
    market_event_time: Optional[str]
    volatility_as_of_event_time: Optional[str]
    computed_age_seconds: Optional[float]
    reuse_status: Optional[str]
    restart_status: Optional[str]
    estimate_present: Optional[bool]
    decision_outcome: Optional[str]
    selected_side: Optional[str]
    economic_metrics: Optional[Mapping[str, Any]]
    event_time_epoch_seconds: Optional[float]
    raw: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "computed_age_seconds": self.computed_age_seconds,
            "cycle_id": self.cycle_id,
            "decision_outcome": self.decision_outcome,
            "economic_metrics": (
                None if self.economic_metrics is None else dict(self.economic_metrics)
            ),
            "estimate_present": self.estimate_present,
            "event_time_epoch_seconds": self.event_time_epoch_seconds,
            "instrument_id": self.instrument_id,
            "join_contract_version": self.join_contract_version,
            "join_digest": self.join_digest,
            "market_event_time": self.market_event_time,
            "regime_id": self.regime_id,
            "restart_status": self.restart_status,
            "reuse_status": self.reuse_status,
            "selected_side": self.selected_side,
            "session_id": self.session_id,
            "volatility_as_of_event_time": self.volatility_as_of_event_time,
            "volatility_source_digest": self.volatility_source_digest,
        }


def _parse_event_time_epoch(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        pass
    normalized = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise MaxAgeResearchExecutionError(
            f"incomplete_event_time_reference:unparseable={text}"
        ) from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def _map_join_to_record(join_payload: Mapping[str, Any]) -> ResearchEvidenceRecordV1:
    if join_payload.get("join_contract_version") not in (None, JOIN_CONTRACT_VERSION):
        # Unknown schema versions fail closed.
        if join_payload.get("join_contract_version") != JOIN_CONTRACT_VERSION:
            raise MaxAgeResearchExecutionError(
                f"unknown_schema_version:{join_payload.get('join_contract_version')}"
            )
    for field in ("session_id", "cycle_id", "instrument_id", "regime_id", "join_digest"):
        value = join_payload.get(field)
        if value is None or not str(value).strip():
            raise MaxAgeResearchExecutionError(f"empty_identity:{field}")

    if join_payload.get("threshold_status") not in (None, "UNRESOLVED_MAX_AGE"):
        raise MaxAgeResearchExecutionError("resolved_threshold_in_input_forbidden")
    if join_payload.get("numeric_threshold_selected") is True:
        raise MaxAgeResearchExecutionError("numeric_threshold_selected_in_input_forbidden")
    if join_payload.get("enforcement_applied") is True:
        raise MaxAgeResearchExecutionError("enforcement_applied_in_input_forbidden")

    market_event_time = join_payload.get("reference_event_time")
    as_of = join_payload.get("estimate_as_of_event_time")
    age = join_payload.get("computed_age_seconds")
    if age is not None and (market_event_time is None or as_of is None):
        raise MaxAgeResearchExecutionError("incomplete_event_time_reference")

    return ResearchEvidenceRecordV1(
        session_id=str(join_payload["session_id"]),
        cycle_id=str(join_payload["cycle_id"]),
        instrument_id=str(join_payload["instrument_id"]),
        regime_id=str(join_payload["regime_id"]),
        join_contract_version=str(
            join_payload.get("join_contract_version") or JOIN_CONTRACT_VERSION
        ),
        join_digest=str(join_payload["join_digest"]),
        volatility_source_digest=(
            None
            if join_payload.get("source_digest") is None
            else str(join_payload.get("source_digest"))
        ),
        market_event_time=None if market_event_time is None else str(market_event_time),
        volatility_as_of_event_time=None if as_of is None else str(as_of),
        computed_age_seconds=(None if age is None else float(age)),
        reuse_status=(
            None if join_payload.get("reuse_status") is None else str(join_payload["reuse_status"])
        ),
        restart_status=(
            None
            if join_payload.get("restart_status") is None
            else str(join_payload["restart_status"])
        ),
        estimate_present=(
            None
            if join_payload.get("estimate_present") is None
            else bool(join_payload.get("estimate_present"))
        ),
        decision_outcome=(
            None
            if join_payload.get("decision_outcome") is None
            else str(join_payload["decision_outcome"])
        ),
        selected_side=(
            None
            if join_payload.get("selected_side") is None
            else str(join_payload["selected_side"])
        ),
        economic_metrics=(
            None
            if join_payload.get("economic_metrics") is None
            else dict(join_payload.get("economic_metrics") or {})
        ),
        event_time_epoch_seconds=_parse_event_time_epoch(market_event_time),
        raw=dict(join_payload),
    )


def load_research_evidence_records_v1(
    ledger_path: Path,
) -> tuple[ResearchEvidenceRecordV1, ...]:
    if not ledger_path.exists():
        raise MaxAgeResearchExecutionError(f"missing_join_ledger:{ledger_path}")
    try:
        joins = load_max_age_research_evidence_ledger_v1(ledger_path)
    except MaxAgeResearchDesignContractError as exc:
        code = str(exc)
        if "ledger_join_digest_mismatch" in code:
            raise MaxAgeResearchExecutionError("join_digest_mismatch") from exc
        if "ledger_duplicate_identity_digest_conflict" in code:
            raise MaxAgeResearchExecutionError("duplicate_identity_divergent_digest") from exc
        if "unknown" in code.lower() and "schema" in code.lower():
            raise MaxAgeResearchExecutionError("unknown_schema_version") from exc
        if "enforcement" in code:
            raise MaxAgeResearchExecutionError("enforcement_applied_in_input_forbidden") from exc
        if "numeric_threshold_selected" in code:
            raise MaxAgeResearchExecutionError(
                "numeric_threshold_selected_in_input_forbidden"
            ) from exc
        if "threshold" in code:
            raise MaxAgeResearchExecutionError("resolved_threshold_in_input_forbidden") from exc
        if "corrupt" in code:
            raise MaxAgeResearchExecutionError("corrupt_ledger") from exc
        raise MaxAgeResearchExecutionError(f"missing_join:{code}") from exc

    records = tuple(_map_join_to_record(j.to_dict()) for j in joins)
    _assert_no_cross_identity_conflicts(records)
    return records


def load_research_evidence_from_payloads_v1(
    payloads: Sequence[Mapping[str, Any]],
) -> tuple[ResearchEvidenceRecordV1, ...]:
    """Test/helper path: validate payloads through the same mapping rules."""
    records = tuple(_map_join_to_record(dict(p)) for p in payloads)
    _assert_no_cross_identity_conflicts(records)
    return records


def _assert_no_cross_identity_conflicts(
    records: Sequence[ResearchEvidenceRecordV1],
) -> None:
    by_cycle: dict[str, ResearchEvidenceRecordV1] = {}
    for record in records:
        prior = by_cycle.get(record.cycle_id)
        if prior is None:
            by_cycle[record.cycle_id] = record
            continue
        if prior.session_id != record.session_id:
            raise MaxAgeResearchExecutionError("cross_session_conflict")
        if prior.instrument_id != record.instrument_id:
            raise MaxAgeResearchExecutionError("cross_instrument_conflict")
        if prior.regime_id != record.regime_id:
            raise MaxAgeResearchExecutionError("cross_regime_conflict")
        if prior.join_digest != record.join_digest:
            raise MaxAgeResearchExecutionError("duplicate_identity_divergent_digest")


def assert_restore_does_not_invent_estimate_evidence_v1(
    *,
    before: Sequence[ResearchEvidenceRecordV1],
    after: Sequence[ResearchEvidenceRecordV1],
) -> None:
    before_ids = {(r.session_id, r.cycle_id, r.instrument_id, r.join_digest) for r in before}
    after_ids = {(r.session_id, r.cycle_id, r.instrument_id, r.join_digest) for r in after}
    invented = after_ids - before_ids
    if invented:
        raise MaxAgeResearchExecutionError("restore_invented_estimate_evidence")


def coverage_summary_v1(records: Sequence[ResearchEvidenceRecordV1]) -> dict[str, Any]:
    sessions = {r.session_id for r in records}
    regimes = {r.regime_id for r in records}
    instruments = {r.instrument_id for r in records}
    ages = [r.computed_age_seconds for r in records if r.computed_age_seconds is not None]
    return {
        "evidence_count": len(records),
        "session_count": len(sessions),
        "regime_count": len(regimes),
        "instrument_count": len(instruments),
        "computed_age_observation_count": len(ages),
        "multi_session_coverage": len(sessions) >= MINIMUM_SESSION_COUNT,
        "multi_regime_coverage": len(regimes) >= MINIMUM_REGIME_COUNT,
        "sufficient_for_research": (
            len(records) >= MINIMUM_EVIDENCE_COUNT
            and len(sessions) >= MINIMUM_SESSION_COUNT
            and len(regimes) >= MINIMUM_REGIME_COUNT
            and len(ages) >= 1
        ),
    }


def build_input_evidence_manifest_v1(
    *,
    repository_sha: str,
    preregistration_digest: str,
    execution_id: str,
    ledger_path: Optional[Path],
    records: Sequence[ResearchEvidenceRecordV1],
    created_at_utc: str,
) -> dict[str, Any]:
    coverage = coverage_summary_v1(records)
    record_digests = sorted(r.join_digest for r in records)
    ledger_sha = None
    if ledger_path is not None and ledger_path.exists():
        ledger_sha = sha256_hex_bytes(ledger_path.read_bytes())
    provisional: dict[str, Any] = {
        "authority_scope": AUTHORITY_SCOPE,
        "coverage": coverage,
        "created_at_utc": created_at_utc,
        "execution_id": execution_id,
        "join_contract_version": JOIN_CONTRACT_VERSION,
        "ledger_path": None if ledger_path is None else str(ledger_path),
        "ledger_sha256": ledger_sha,
        "non_authority_scope": NON_AUTHORITY_SCOPE,
        "preregistration_digest": preregistration_digest,
        "record_count": len(records),
        "record_join_digests": record_digests,
        "repository_sha": repository_sha,
        "schema_version": INPUT_EVIDENCE_MANIFEST_SCHEMA_VERSION,
        "synthetic_evidence_invented": False,
    }
    provisional["input_evidence_manifest_digest"] = digest_excluding_keys(
        provisional,
        exclude={"input_evidence_manifest_digest", "execution_id", "created_at_utc"},
    )
    return provisional


def empty_input_evidence_manifest_v1(
    *,
    repository_sha: str,
    preregistration_digest: str,
    execution_id: str,
    created_at_utc: str,
    reason: str,
) -> dict[str, Any]:
    provisional: dict[str, Any] = {
        "authority_scope": AUTHORITY_SCOPE,
        "coverage": {
            "evidence_count": 0,
            "session_count": 0,
            "regime_count": 0,
            "instrument_count": 0,
            "computed_age_observation_count": 0,
            "multi_session_coverage": False,
            "multi_regime_coverage": False,
            "sufficient_for_research": False,
        },
        "created_at_utc": created_at_utc,
        "execution_id": execution_id,
        "insufficient_research_evidence": True,
        "join_contract_version": JOIN_CONTRACT_VERSION,
        "ledger_path": None,
        "ledger_sha256": None,
        "non_authority_scope": NON_AUTHORITY_SCOPE,
        "preregistration_digest": preregistration_digest,
        "reason": reason,
        "record_count": 0,
        "record_join_digests": [],
        "repository_sha": repository_sha,
        "schema_version": INPUT_EVIDENCE_MANIFEST_SCHEMA_VERSION,
        "synthetic_evidence_invented": False,
    }
    provisional["input_evidence_manifest_digest"] = digest_excluding_keys(
        provisional,
        exclude={"input_evidence_manifest_digest", "execution_id", "created_at_utc"},
    )
    return provisional


def stable_records_fingerprint_v1(records: Sequence[ResearchEvidenceRecordV1]) -> str:
    material = "|".join(
        f"{r.session_id}:{r.cycle_id}:{r.instrument_id}:{r.join_digest}" for r in records
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()
