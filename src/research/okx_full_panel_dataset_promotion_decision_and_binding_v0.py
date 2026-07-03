"""OKX full-panel dataset promotion decision and immutable binding v0.

Deterministic, fail-closed promotion evaluation for manifest-verified OKX full-panel
fetch completeness candidates. Reuses fetch/completeness, lifecycle, PIT, funding,
and carry owners from PR #4806 without economic evaluation or runtime authority.

Research-only; dataset binding only on full policy PASS.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_bounded_panel_fetch_v0 import compute_bounded_window_v0
from src.research.missing_funding_policy_v0 import POLICY_VERSION as FUNDING_POLICY_VERSION
from src.research.okx_full_panel_fetch_completeness_evidence_v0 import (
    COMPLETENESS_POLICY_VERSION,
    DEFAULT_DURABLE_ARCHIVE_ROOT,
    DEFAULT_LIFECYCLE_REGISTRY_REL,
    FETCH_SCOPE_ID,
    ORCHESTRATOR_VERSION as FETCH_ORCHESTRATOR_VERSION,
    PanelCellV0,
    derive_registry_instruments_v0,
)
from src.research.pit_futures_instrument_lifecycle_registry_persistence_v1 import (
    read_registry_snapshot_v1,
)
from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
    QueryState,
    query_lifecycle_at_snapshot_v1,
)

PACKAGE_MARKER = "OKX_FULL_PANEL_DATASET_PROMOTION_DECISION_AND_BINDING_V0=true"
ORCHESTRATOR_VERSION = "okx_full_panel_dataset_promotion_decision_and_binding.v0"
GO_TOKEN = "GO_BOUNDED_DATASET_PROMOTION_DECISION_AND_BINDING_V0"
PROMOTION_SCOPE_ID = "bounded_dataset_promotion_decision_and_binding_v0"
PROMOTION_DECISION_VERSION = "v0"
DATASET_ID = "okx_full_panel_historical_funding_archive_v0"
DATASET_VERSION = "v0"
DATASET_SCHEMA_VERSION = "okx_full_panel_dataset.v0"
REGISTRY_CONFIG_REL = "config/research/okx_full_panel_dataset_promotion_registry_v0.json"
PROMOTED_DATASET_REL = f"datasets/admissible_futures/{DATASET_ID}/{DATASET_VERSION}"

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
PROMOTION_EFFECT_BINDING_ONLY = "DATASET_BINDING_ONLY"
PROMOTION_EFFECT_NONE = "NONE"

_FORBIDDEN_INSTRUMENT_TOKENS = frozenset(
    {"btc", "xbt", "bitcoin", "spot", "synthetic_spot", "synthetic-spot"}
)
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_CANDIDATE_REQUIRED_REL_PATHS = (
    "fetch_spec.json",
    "archive_results.jsonl",
    "request_records.jsonl",
    "completeness/aggregates.json",
    "completeness/panel_matrix.jsonl",
    "PROMOTION_BLOCK.md",
    "MANIFEST.sha256",
)

FEE_MODEL_VERSION = "backtest_fee_taker_symmetric_v0"
SLIPPAGE_MODEL_VERSION = "backtest_slippage_symmetric_v0"
FUNDING_MODEL_VERSION = "backtest_funding_perpetual_interval_v1"
EXECUTION_MODEL_VERSION = "backtest_execution_v0"
ECONOMIC_POLICY_VERSION = "economic_validity_policy_v1"


class UniverseClassificationCode(str, Enum):
    LIFECYCLE_ADMISSIBLE = "LIFECYCLE_ADMISSIBLE"
    NOT_LISTED_IN_PERIOD = "NOT_LISTED_IN_PERIOD"
    DELISTED_OR_EXPIRED = "DELISTED_OR_EXPIRED"
    OUTSIDE_BOUND_PERIOD = "OUTSIDE_BOUND_PERIOD"
    UNSUPPORTED_CONTRACT_TYPE = "UNSUPPORTED_CONTRACT_TYPE"
    MISSING_LIFECYCLE_EVIDENCE = "MISSING_LIFECYCLE_EVIDENCE"
    POLICY_EXCLUDED = "POLICY_EXCLUDED"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    OTHER_BLOCKING_REASON = "OTHER_BLOCKING_REASON"


class PromotionDecisionStatus(str, Enum):
    PROMOTED = "PROMOTED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    INCONCLUSIVE = "INCONCLUSIVE"


class IdempotentRepromotionStatus(str, Enum):
    NO_OP_SUCCESS = "NO_OP_SUCCESS"
    NEW_PROMOTION = "NEW_PROMOTION"
    CONFLICT_BLOCKED = "CONFLICT_BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class UniverseInstrumentRecordV0:
    instrument_id: str
    venue_symbol: str
    contract_type: str
    classification: UniverseClassificationCode
    lifecycle_query_state: str
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class CandidateIntegrityReportV0:
    status: str
    candidate_root: str
    candidate_manifest_digest: str
    dataset_content_digest: str
    file_count: int
    total_bytes: int
    schema_version: str
    row_count: int
    instrument_count: int
    period_count: int
    min_event_time: str
    max_event_time: str
    venue: str
    market_type: str
    contract_types: tuple[str, ...]
    source_archive_count: int
    source_archive_digests: tuple[str, ...]
    reused_archive_count: int
    downloaded_archive_count: int
    lifecycle_registry_version: int
    lifecycle_binding_digest: str
    pit_policy_version: str
    pit_binding_digest: str
    funding_policy_version: str
    funding_binding_digest: str
    carry_policy_version: str
    carry_binding_digest: str
    completeness_policy_version: str
    completeness_binding_digest: str
    implementation_digest: str
    config_digest: str
    reason_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class PromotionBindingV0:
    promotion_scope_id: str
    promotion_decision_version: str
    decision_timestamp_utc: str
    source_candidate_id: str
    source_candidate_root: str
    source_candidate_manifest_digest: str
    dataset_content_digest: str
    dataset_schema_version: str
    dataset_version: str
    venue: str
    market_type: str
    instrument_binding: Mapping[str, Any]
    universe_binding: Mapping[str, Any]
    period_binding: Mapping[str, Any]
    lifecycle_registry_binding: Mapping[str, Any]
    pit_policy_binding: Mapping[str, Any]
    funding_model_binding: Mapping[str, Any]
    carry_model_binding: Mapping[str, Any]
    fee_model_binding: Mapping[str, Any]
    slippage_model_binding: Mapping[str, Any]
    execution_model_binding: Mapping[str, Any]
    completeness_policy_binding: Mapping[str, Any]
    economic_policy_binding: Mapping[str, Any]
    implementation_digest: str
    config_digest: str
    input_evidence_refs: tuple[str, ...]
    decision_status: PromotionDecisionStatus
    reason_codes: tuple[str, ...]
    promotion_effect: str
    economic_evaluation_authorized: bool
    runtime_effect: str
    authority_effect: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "promotion_scope_id": self.promotion_scope_id,
            "promotion_decision_version": self.promotion_decision_version,
            "decision_timestamp_utc": self.decision_timestamp_utc,
            "source_candidate_id": self.source_candidate_id,
            "source_candidate_root": self.source_candidate_root,
            "source_candidate_manifest_digest": self.source_candidate_manifest_digest,
            "dataset_content_digest": self.dataset_content_digest,
            "dataset_schema_version": self.dataset_schema_version,
            "dataset_version": self.dataset_version,
            "venue": self.venue,
            "market_type": self.market_type,
            "instrument_binding": dict(self.instrument_binding),
            "universe_binding": dict(self.universe_binding),
            "period_binding": dict(self.period_binding),
            "lifecycle_registry_binding": dict(self.lifecycle_registry_binding),
            "pit_policy_binding": dict(self.pit_policy_binding),
            "funding_model_binding": dict(self.funding_model_binding),
            "carry_model_binding": dict(self.carry_model_binding),
            "fee_model_binding": dict(self.fee_model_binding),
            "slippage_model_binding": dict(self.slippage_model_binding),
            "execution_model_binding": dict(self.execution_model_binding),
            "completeness_policy_binding": dict(self.completeness_policy_binding),
            "economic_policy_binding": dict(self.economic_policy_binding),
            "implementation_digest": self.implementation_digest,
            "config_digest": self.config_digest,
            "input_evidence_refs": list(self.input_evidence_refs),
            "decision_status": self.decision_status.value,
            "reason_codes": list(self.reason_codes),
            "promotion_effect": self.promotion_effect,
            "economic_evaluation_authorized": self.economic_evaluation_authorized,
            "runtime_effect": self.runtime_effect,
            "authority_effect": self.authority_effect,
        }


@dataclass(frozen=True)
class PromotionDecisionResultV0:
    decision: PromotionDecisionStatus
    reason_codes: tuple[str, ...]
    candidate_integrity: CandidateIntegrityReportV0
    universe_records: tuple[UniverseInstrumentRecordV0, ...]
    promotion_binding: PromotionBindingV0 | None
    dataset_promoted: bool
    dataset_binding_active: bool
    registry_entry_path: str | None
    alias_updated: bool
    idempotent_status: IdempotentRepromotionStatus
    registry_mutation: bool
    economic_evaluation_authorized: bool
    promotion_effect: str
    runtime_effect: str
    authority_effect: str
    promoted_dataset_root: str | None = None


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_implementation_digest_v0() -> str:
    return _stable_digest(
        {
            "module": ORCHESTRATOR_VERSION,
            "fetch_orchestrator": FETCH_ORCHESTRATOR_VERSION,
            "promotion_scope_id": PROMOTION_SCOPE_ID,
            "schema_version": DATASET_SCHEMA_VERSION,
        }
    )


def _manifest_digest(root: Path) -> str:
    manifest = root / "MANIFEST.sha256"
    return hashlib.sha256(manifest.read_bytes()).hexdigest()


def _is_bitcoin_venue_symbol(venue_symbol: str) -> bool:
    lowered = venue_symbol.lower()
    return any(token in lowered for token in _FORBIDDEN_INSTRUMENT_TOKENS)


def _map_lifecycle_to_classification(
    query_state: str,
    *,
    error_codes: Sequence[str],
) -> UniverseClassificationCode:
    if error_codes:
        return UniverseClassificationCode.MISSING_LIFECYCLE_EVIDENCE
    mapping = {
        QueryState.ELIGIBLE.value: UniverseClassificationCode.LIFECYCLE_ADMISSIBLE,
        QueryState.NOT_LISTED.value: UniverseClassificationCode.NOT_LISTED_IN_PERIOD,
        QueryState.DELISTED.value: UniverseClassificationCode.DELISTED_OR_EXPIRED,
        QueryState.EXPIRED.value: UniverseClassificationCode.DELISTED_OR_EXPIRED,
        QueryState.LISTED_INELIGIBLE.value: UniverseClassificationCode.OUTSIDE_BOUND_PERIOD,
        QueryState.SUSPENDED.value: UniverseClassificationCode.OTHER_BLOCKING_REASON,
        QueryState.UNKNOWN.value: UniverseClassificationCode.MISSING_LIFECYCLE_EVIDENCE,
    }
    return mapping.get(query_state, UniverseClassificationCode.OTHER_BLOCKING_REASON)


def build_universe_denominator_matrix_v0(
    *,
    snapshot: Any,
    period_start_ms: int,
) -> tuple[UniverseInstrumentRecordV0, ...]:
    admissible, all_requested = derive_registry_instruments_v0(
        snapshot, period_start_ms=period_start_ms
    )
    admissible_ids = {item[0] for item in admissible}
    decision_instant = datetime.fromtimestamp(period_start_ms / 1000, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    records: list[UniverseInstrumentRecordV0] = []
    for instrument_id, venue_symbol, contract_type in all_requested:
        if _is_bitcoin_venue_symbol(venue_symbol):
            records.append(
                UniverseInstrumentRecordV0(
                    instrument_id=instrument_id,
                    venue_symbol=venue_symbol,
                    contract_type=contract_type,
                    classification=UniverseClassificationCode.POLICY_EXCLUDED,
                    lifecycle_query_state="POLICY_EXCLUDED",
                    reason_codes=("BITCOIN_DIRECTION_PROHIBITED",),
                )
            )
            continue
        if instrument_id in admissible_ids:
            records.append(
                UniverseInstrumentRecordV0(
                    instrument_id=instrument_id,
                    venue_symbol=venue_symbol,
                    contract_type=contract_type,
                    classification=UniverseClassificationCode.LIFECYCLE_ADMISSIBLE,
                    lifecycle_query_state=QueryState.ELIGIBLE.value,
                    reason_codes=("LIFECYCLE_ELIGIBLE_AT_PERIOD_START",),
                )
            )
            continue
        query = query_lifecycle_at_snapshot_v1(
            snapshot,
            instrument_id=instrument_id,
            query_instant=decision_instant,
        )
        classification = _map_lifecycle_to_classification(
            query.query_state,
            error_codes=query.error_codes,
        )
        records.append(
            UniverseInstrumentRecordV0(
                instrument_id=instrument_id,
                venue_symbol=venue_symbol,
                contract_type=contract_type,
                classification=classification,
                lifecycle_query_state=query.query_state,
                reason_codes=tuple(query.error_codes)
                if query.error_codes
                else (query.query_state,),
            )
        )
    return tuple(sorted(records, key=lambda r: r.instrument_id))


def _load_panel_cells(candidate_root: Path) -> tuple[PanelCellV0, ...]:
    matrix_path = candidate_root / "completeness" / "panel_matrix.jsonl"
    cells: list[PanelCellV0] = []
    for line in matrix_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        cells.append(
            PanelCellV0(
                instrument_id=payload["instrument_id"],
                venue_symbol=payload["venue_symbol"],
                contract_type=payload["contract_type"],
                period_start=payload["period_start"],
                period_end=payload["period_end"],
                lifecycle_status=payload["lifecycle_status"],
                archive_status=payload["archive_status"],
                price_history_status=payload["price_history_status"],
                funding_history_status=payload["funding_history_status"],
                carry_history_status=payload["carry_history_status"],
                pit_join_status=payload["pit_join_status"],
                checksum_status=payload["checksum_status"],
                completeness_status=payload["completeness_status"],
                quarantine_status=payload["quarantine_status"],
                reason_codes=tuple(payload.get("reason_codes", ())),
                source_object_refs=tuple(payload.get("source_object_refs", ())),
                content_digests=tuple(payload.get("content_digests", ())),
            )
        )
    return tuple(cells)


def verify_candidate_integrity_v0(
    *,
    candidate_root: Path,
    closeout_manifest_digest: str | None = None,
) -> CandidateIntegrityReportV0:
    reason_codes: list[str] = []
    if not candidate_root.is_dir():
        return CandidateIntegrityReportV0(
            status="BLOCKED",
            candidate_root=str(candidate_root),
            candidate_manifest_digest="",
            dataset_content_digest="",
            file_count=0,
            total_bytes=0,
            schema_version=DATASET_SCHEMA_VERSION,
            row_count=0,
            instrument_count=0,
            period_count=0,
            min_event_time="",
            max_event_time="",
            venue="",
            market_type="",
            contract_types=(),
            source_archive_count=0,
            source_archive_digests=(),
            reused_archive_count=0,
            downloaded_archive_count=0,
            lifecycle_registry_version=0,
            lifecycle_binding_digest="",
            pit_policy_version="",
            pit_binding_digest="",
            funding_policy_version="",
            funding_binding_digest="",
            carry_policy_version="",
            carry_binding_digest="",
            completeness_policy_version="",
            completeness_binding_digest="",
            implementation_digest="",
            config_digest="",
            reason_codes=("CANDIDATE_ROOT_MISSING",),
        )
    if candidate_root.is_symlink():
        reason_codes.append("CANDIDATE_ROOT_IS_SYMLINK")

    from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256

    manifest_ok, manifest_msg = verify_manifest_sha256(candidate_root)
    if not manifest_ok:
        reason_codes.append(f"CANDIDATE_MANIFEST_VERIFY_FAILED:{manifest_msg}")

    manifest_digest = _manifest_digest(candidate_root) if manifest_ok else ""
    if closeout_manifest_digest and manifest_digest != closeout_manifest_digest:
        reason_codes.append("CANDIDATE_MUTATED_AFTER_CLOSEOUT")

    for rel in _CANDIDATE_REQUIRED_REL_PATHS:
        if rel == "MANIFEST.sha256":
            continue
        if not (candidate_root / rel).is_file():
            reason_codes.append(f"CANDIDATE_REQUIRED_FILE_MISSING:{rel}")

    manifest_lines = (candidate_root / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
    manifest_rels = {line.split(None, 1)[1] for line in manifest_lines if line.strip()}
    expected_rels = {p for p in _CANDIDATE_REQUIRED_REL_PATHS if p != "MANIFEST.sha256"}
    extra = manifest_rels - expected_rels
    missing = expected_rels - manifest_rels
    if extra:
        reason_codes.append(f"CANDIDATE_UNEXPECTED_FILES:{','.join(sorted(extra))}")
    if missing:
        reason_codes.append(f"CANDIDATE_MANIFEST_MISSING_ENTRIES:{','.join(sorted(missing))}")

    fetch_spec = json.loads((candidate_root / "fetch_spec.json").read_text(encoding="utf-8"))
    aggregates = json.loads(
        (candidate_root / "completeness" / "aggregates.json").read_text(encoding="utf-8")
    )
    archive_lines = [
        json.loads(line)
        for line in (candidate_root / "archive_results.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    cells = _load_panel_cells(candidate_root)

    file_count = sum(1 for p in candidate_root.rglob("*") if p.is_file() and not p.is_symlink())
    total_bytes = sum(
        p.stat().st_size for p in candidate_root.rglob("*") if p.is_file() and not p.is_symlink()
    )
    archive_digests = tuple(
        sorted(
            {
                r["sha256"]
                for r in archive_lines
                if r.get("sha256") and _SHA256_HEX_RE.match(r["sha256"])
            }
        )
    )
    reused = sum(1 for r in archive_lines if r.get("reason_code") == "REUSED_EXISTING")
    downloaded = sum(1 for r in archive_lines if r.get("reason_code") == "FETCHED")

    content_payload = {
        "candidate_root": str(candidate_root.resolve()),
        "manifest_digest": manifest_digest,
        "fetch_spec_digest": _stable_digest(fetch_spec),
        "aggregates": aggregates,
        "archive_digests": archive_digests,
        "panel_cell_digests": [_stable_digest(cell.__dict__) for cell in cells],
    }
    dataset_content_digest = _stable_digest(content_payload)

    pit_binding_digest = _stable_digest(
        {
            "pit_join_policy": fetch_spec.get("pit_join_policy"),
            "pit_cells_pass": aggregates.get("pit_cells_pass"),
            "pit_cells_fail": aggregates.get("pit_cells_fail"),
        }
    )
    funding_binding_digest = _stable_digest(
        {
            "policy": fetch_spec.get("missing_funding_policy"),
            "funding_policy_version": FUNDING_POLICY_VERSION,
            "funding_cells_present": aggregates.get("funding_cells_present"),
            "funding_cells_missing": aggregates.get("funding_cells_missing"),
        }
    )
    carry_binding_digest = _stable_digest(
        {
            "policy": fetch_spec.get("missing_carry_policy"),
            "carry_cells_present": aggregates.get("carry_cells_present"),
            "carry_cells_missing": aggregates.get("carry_cells_missing"),
        }
    )
    completeness_binding_digest = _stable_digest(
        {
            "completeness_policy_version": fetch_spec.get("completeness_policy_version"),
            "panel_completeness_ratio": aggregates.get("panel_completeness_ratio"),
            "instruments_complete": aggregates.get("instruments_complete"),
        }
    )

    status = "PASS" if not reason_codes else "BLOCKED"
    return CandidateIntegrityReportV0(
        status=status,
        candidate_root=str(candidate_root.resolve()),
        candidate_manifest_digest=manifest_digest,
        dataset_content_digest=dataset_content_digest,
        file_count=file_count,
        total_bytes=total_bytes,
        schema_version=DATASET_SCHEMA_VERSION,
        row_count=len(archive_lines),
        instrument_count=int(aggregates.get("instruments_lifecycle_admissible", 0)),
        period_count=int(aggregates.get("periods_requested", 0)),
        min_event_time=str(fetch_spec.get("requested_start_time", "")),
        max_event_time=str(fetch_spec.get("requested_end_time", "")),
        venue=str(fetch_spec.get("venue", "OKX")),
        market_type=str(fetch_spec.get("market_type", "")),
        contract_types=tuple(fetch_spec.get("requested_contract_types", ())),
        source_archive_count=len(archive_digests),
        source_archive_digests=archive_digests,
        reused_archive_count=reused,
        downloaded_archive_count=downloaded,
        lifecycle_registry_version=int(fetch_spec.get("lifecycle_registry_version", 0)),
        lifecycle_binding_digest=str(fetch_spec.get("config_digest", "")),
        pit_policy_version=str(fetch_spec.get("pit_join_policy", "")),
        pit_binding_digest=pit_binding_digest,
        funding_policy_version=FUNDING_POLICY_VERSION,
        funding_binding_digest=funding_binding_digest,
        carry_policy_version=str(fetch_spec.get("missing_carry_policy", "")),
        carry_binding_digest=carry_binding_digest,
        completeness_policy_version=str(fetch_spec.get("completeness_policy_version", "")),
        completeness_binding_digest=completeness_binding_digest,
        implementation_digest=str(fetch_spec.get("implementation_digest", "")),
        config_digest=str(fetch_spec.get("config_digest", "")),
        reason_codes=tuple(reason_codes),
    )


def _validate_admissible_completeness(
    *,
    cells: Sequence[PanelCellV0],
    aggregates: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    admissible_count = int(aggregates.get("instruments_lifecycle_admissible", 0))
    if aggregates.get("funding_cells_missing", 1) != 0:
        reasons.append("FUNDING_CELLS_MISSING")
    if aggregates.get("carry_cells_missing", 1) != 0:
        reasons.append("CARRY_CELLS_MISSING")
    if aggregates.get("pit_cells_fail", 1) != 0:
        reasons.append("PIT_CELLS_FAIL")
    if aggregates.get("instruments_complete", 0) != admissible_count:
        reasons.append("INCOMPLETE_ADMISSIBLE_INSTRUMENTS")
    if aggregates.get("instruments_quarantined", 0) != 0:
        reasons.append("QUARANTINED_REQUIRED_INPUT")
    if aggregates.get("instruments_blocked", 0) != 0:
        reasons.append("BLOCKED_ADMISSIBLE_INSTRUMENTS")
    for cell in cells:
        if cell.completeness_status != "COMPLETE":
            reasons.append(f"CELL_NOT_COMPLETE:{cell.instrument_id}")
        if cell.quarantine_status == "QUARANTINED":
            reasons.append(f"CELL_QUARANTINED:{cell.instrument_id}")
        if cell.funding_history_status != "PRESENT":
            reasons.append(f"FUNDING_MISSING:{cell.instrument_id}")
        if cell.carry_history_status != "PRESENT":
            reasons.append(f"CARRY_MISSING:{cell.instrument_id}")
        if cell.pit_join_status != "PASS":
            reasons.append(f"PIT_FAIL:{cell.instrument_id}")
    return len(reasons) == 0, tuple(sorted(set(reasons)))


def _validate_universe_denominator(
    universe_records: Sequence[UniverseInstrumentRecordV0],
    *,
    aggregates: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if len(universe_records) != int(aggregates.get("instruments_requested", 0)):
        reasons.append("UNIVERSE_COUNT_MISMATCH")
    admissible = [
        r
        for r in universe_records
        if r.classification == UniverseClassificationCode.LIFECYCLE_ADMISSIBLE
    ]
    if len(admissible) != int(aggregates.get("instruments_lifecycle_admissible", 0)):
        reasons.append("LIFECYCLE_ADMISSIBLE_COUNT_MISMATCH")
    unresolved = [
        r
        for r in universe_records
        if r.classification == UniverseClassificationCode.MISSING_LIFECYCLE_EVIDENCE
    ]
    if unresolved:
        reasons.append(f"UNRESOLVED_LIFECYCLE_EXCLUSIONS:{len(unresolved)}")
    for record in universe_records:
        if _is_bitcoin_venue_symbol(record.venue_symbol):
            reasons.append(f"BITCOIN_INSTRUMENT_PRESENT:{record.instrument_id}")
        if (
            record.contract_type not in {"linear_perpetual"}
            and record.classification == UniverseClassificationCode.LIFECYCLE_ADMISSIBLE
        ):
            reasons.append(f"UNSUPPORTED_CONTRACT_TYPE:{record.instrument_id}")
    return len(reasons) == 0, tuple(sorted(set(reasons)))


def evaluate_promotion_decision_v0(
    *,
    candidate_integrity: CandidateIntegrityReportV0,
    universe_records: Sequence[UniverseInstrumentRecordV0],
    cells: Sequence[PanelCellV0],
    aggregates: Mapping[str, Any],
    fetch_spec: Mapping[str, Any],
) -> tuple[PromotionDecisionStatus, tuple[str, ...]]:
    all_reasons: list[str] = []
    if candidate_integrity.status != "PASS":
        all_reasons.extend(candidate_integrity.reason_codes)
    if fetch_spec.get("market_type") != "FUTURES_OR_PERPETUALS_ONLY":
        all_reasons.append("NON_FUTURES_MARKET_TYPE")
    if fetch_spec.get("fetch_scope_id") != FETCH_SCOPE_ID:
        all_reasons.append("FETCH_SCOPE_MISMATCH")

    universe_ok, universe_reasons = _validate_universe_denominator(
        universe_records, aggregates=aggregates
    )
    if not universe_ok:
        all_reasons.extend(universe_reasons)

    completeness_ok, completeness_reasons = _validate_admissible_completeness(
        cells=cells, aggregates=aggregates
    )
    if not completeness_ok:
        all_reasons.extend(completeness_reasons)

    if all_reasons:
        if any(
            code.startswith(
                (
                    "CANDIDATE_",
                    "UNRESOLVED_",
                    "UNIVERSE_COUNT",
                    "LIFECYCLE_ADMISSIBLE_COUNT",
                )
            )
            for code in all_reasons
        ):
            return PromotionDecisionStatus.BLOCKED, tuple(sorted(set(all_reasons)))
        return PromotionDecisionStatus.REJECTED, tuple(sorted(set(all_reasons)))
    return PromotionDecisionStatus.PROMOTED, ()


def build_promotion_binding_v0(
    *,
    candidate_integrity: CandidateIntegrityReportV0,
    universe_records: Sequence[UniverseInstrumentRecordV0],
    fetch_spec: Mapping[str, Any],
    decision: PromotionDecisionStatus,
    reason_codes: Sequence[str],
    input_evidence_refs: Sequence[str],
    decision_timestamp_utc: str,
) -> PromotionBindingV0:
    window = compute_bounded_window_v0()
    candidate_id = Path(candidate_integrity.candidate_root).name
    admissible_ids = [
        r.instrument_id
        for r in universe_records
        if r.classification == UniverseClassificationCode.LIFECYCLE_ADMISSIBLE
    ]
    exclusion_summary = {
        code.value: sum(1 for r in universe_records if r.classification == code)
        for code in UniverseClassificationCode
        if code != UniverseClassificationCode.LIFECYCLE_ADMISSIBLE
    }
    promotion_effect = (
        PROMOTION_EFFECT_BINDING_ONLY
        if decision == PromotionDecisionStatus.PROMOTED
        else PROMOTION_EFFECT_NONE
    )
    return PromotionBindingV0(
        promotion_scope_id=PROMOTION_SCOPE_ID,
        promotion_decision_version=PROMOTION_DECISION_VERSION,
        decision_timestamp_utc=decision_timestamp_utc,
        source_candidate_id=candidate_id,
        source_candidate_root=candidate_integrity.candidate_root,
        source_candidate_manifest_digest=candidate_integrity.candidate_manifest_digest,
        dataset_content_digest=candidate_integrity.dataset_content_digest,
        dataset_schema_version=DATASET_SCHEMA_VERSION,
        dataset_version=DATASET_VERSION,
        venue=candidate_integrity.venue,
        market_type=candidate_integrity.market_type,
        instrument_binding={
            "binding_mode": "lifecycle_admissible_complete_panel_v0",
            "instrument_count": len(admissible_ids),
            "instrument_ids": admissible_ids,
            "futures_only": True,
            "bitcoin_direction_allowed": False,
        },
        universe_binding={
            "instruments_requested": len(universe_records),
            "instruments_lifecycle_admissible": len(admissible_ids),
            "instruments_excluded": len(universe_records) - len(admissible_ids),
            "lifecycle_completeness_ratio": round(len(admissible_ids) / len(universe_records), 5)
            if universe_records
            else 0.0,
            "exclusion_summary": exclusion_summary,
        },
        period_binding={
            "requested_start_time": fetch_spec.get("requested_start_time"),
            "requested_end_time": fetch_spec.get("requested_end_time"),
            "bounded_window_policy": "cross_sectional_bounded_panel_fetch_v0",
            "period_start_ms": window.start_ms,
            "period_end_exclusive_ms": window.end_exclusive_ms,
        },
        lifecycle_registry_binding={
            "registry_version": candidate_integrity.lifecycle_registry_version,
            "registry_digest": candidate_integrity.lifecycle_binding_digest,
            "registry_ref": DEFAULT_LIFECYCLE_REGISTRY_REL,
        },
        pit_policy_binding={
            "pit_join_policy": fetch_spec.get("pit_join_policy"),
            "pit_binding_digest": candidate_integrity.pit_binding_digest,
        },
        funding_model_binding={
            "funding_policy_version": candidate_integrity.funding_policy_version,
            "funding_binding_digest": candidate_integrity.funding_binding_digest,
            "missing_funding_policy": fetch_spec.get("missing_funding_policy"),
            "funding_model_version": FUNDING_MODEL_VERSION,
        },
        carry_model_binding={
            "carry_policy_version": candidate_integrity.carry_policy_version,
            "carry_binding_digest": candidate_integrity.carry_binding_digest,
            "missing_carry_policy": fetch_spec.get("missing_carry_policy"),
        },
        fee_model_binding={"fee_model_version": FEE_MODEL_VERSION},
        slippage_model_binding={"slippage_model_version": SLIPPAGE_MODEL_VERSION},
        execution_model_binding={"execution_model_version": EXECUTION_MODEL_VERSION},
        completeness_policy_binding={
            "completeness_policy_version": candidate_integrity.completeness_policy_version,
            "completeness_binding_digest": candidate_integrity.completeness_binding_digest,
        },
        economic_policy_binding={
            "economic_policy_version": ECONOMIC_POLICY_VERSION,
            "economic_evaluation_authorized": False,
        },
        implementation_digest=compute_implementation_digest_v0(),
        config_digest=candidate_integrity.config_digest,
        input_evidence_refs=tuple(input_evidence_refs),
        decision_status=decision,
        reason_codes=tuple(reason_codes),
        promotion_effect=promotion_effect,
        economic_evaluation_authorized=False,
        runtime_effect=RUNTIME_EFFECT,
        authority_effect=AUTHORITY_EFFECT,
    )


def _load_existing_registry_entry(registry_path: Path) -> dict[str, Any] | None:
    if not registry_path.is_file():
        return None
    return json.loads(registry_path.read_text(encoding="utf-8"))


def write_promoted_dataset_registry_v0(
    *,
    durable_archive_root: Path,
    repo_root: Path,
    promotion_binding: PromotionBindingV0,
) -> tuple[Path, IdempotentRepromotionStatus, bool]:
    promoted_root = durable_archive_root / PROMOTED_DATASET_REL
    registry_entry_path = promoted_root / "registry_entry.json"
    binding_path = promoted_root / "promotion_binding.json"
    candidate_ref_path = promoted_root / "candidate_reference.json"
    alias_path = promoted_root / "alias" / "current.json"

    existing = _load_existing_registry_entry(registry_entry_path)
    if existing:
        if existing.get("dataset_content_digest") == promotion_binding.dataset_content_digest:
            return promoted_root, IdempotentRepromotionStatus.NO_OP_SUCCESS, False
        if existing.get("dataset_version") == promotion_binding.dataset_version:
            return promoted_root, IdempotentRepromotionStatus.CONFLICT_BLOCKED, False

    promoted_root.mkdir(parents=True, exist_ok=True)
    binding_path.write_text(
        json.dumps(promotion_binding.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    registry_entry = {
        "dataset_id": DATASET_ID,
        "dataset_version": DATASET_VERSION,
        "dataset_schema_version": DATASET_SCHEMA_VERSION,
        "dataset_content_digest": promotion_binding.dataset_content_digest,
        "source_candidate_id": promotion_binding.source_candidate_id,
        "source_candidate_root": promotion_binding.source_candidate_root,
        "source_candidate_manifest_digest": promotion_binding.source_candidate_manifest_digest,
        "promotion_binding_path": "promotion_binding.json",
        "candidate_reference_path": "candidate_reference.json",
        "promoted_at_utc": promotion_binding.decision_timestamp_utc,
        "promotion_effect": promotion_binding.promotion_effect,
        "economic_evaluation_authorized": False,
        "runtime_effect": RUNTIME_EFFECT,
        "authority_effect": AUTHORITY_EFFECT,
        "immutable_versioned_binding": True,
        "alias_paths": ["alias/current.json"],
    }
    registry_entry_path.write_text(
        json.dumps(registry_entry, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    candidate_ref_path.write_text(
        json.dumps(
            {
                "candidate_root": promotion_binding.source_candidate_root,
                "candidate_manifest_digest": promotion_binding.source_candidate_manifest_digest,
                "dataset_content_digest": promotion_binding.dataset_content_digest,
                "immutable": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    alias_path.parent.mkdir(parents=True, exist_ok=True)
    alias_path.write_text(
        json.dumps(
            {
                "alias": "current",
                "dataset_id": DATASET_ID,
                "dataset_version": DATASET_VERSION,
                "registry_entry_path": "../registry_entry.json",
                "dataset_content_digest": promotion_binding.dataset_content_digest,
                "not_sole_binding": True,
                "versioned_binding_required": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

    write_manifest_sha256(promoted_root)

    repo_config_path = repo_root / REGISTRY_CONFIG_REL
    repo_config_path.parent.mkdir(parents=True, exist_ok=True)
    repo_config = {
        "artifact_kind": "okx_full_panel_dataset_promotion_registry",
        "artifact_version": PROMOTION_DECISION_VERSION,
        "dataset_id": DATASET_ID,
        "dataset_version": DATASET_VERSION,
        "dataset_schema_version": DATASET_SCHEMA_VERSION,
        "dataset_content_digest": promotion_binding.dataset_content_digest,
        "source_candidate_id": promotion_binding.source_candidate_id,
        "source_candidate_root": promotion_binding.source_candidate_root,
        "promoted_dataset_root": str(promoted_root),
        "registry_entry_ref": f"{PROMOTED_DATASET_REL}/registry_entry.json",
        "promotion_binding_ref": f"{PROMOTED_DATASET_REL}/promotion_binding.json",
        "alias_ref": f"{PROMOTED_DATASET_REL}/alias/current.json",
        "immutable_versioned_binding": True,
        "alias_is_not_sole_binding": True,
        "economic_evaluation_authorized": False,
        "runtime_effect": RUNTIME_EFFECT,
        "authority_effect": AUTHORITY_EFFECT,
    }
    repo_config_path.write_text(
        json.dumps(repo_config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    return promoted_root, IdempotentRepromotionStatus.NEW_PROMOTION, True


def run_okx_full_panel_dataset_promotion_decision_and_binding_v0(
    *,
    confirm: str,
    candidate_root: Path,
    durable_archive_root: Path | None = None,
    repo_root: Path | None = None,
    implementation_evidence_ref: str = "",
    closeout_evidence_ref: str = "",
    closeout_manifest_digest: str | None = None,
    lifecycle_registry_path: Path | None = None,
    write_registry: bool = True,
) -> PromotionDecisionResultV0:
    if confirm != GO_TOKEN:
        raise ValueError(f"GO_TOKEN_REQUIRED:{GO_TOKEN}")

    archive_root = durable_archive_root or DEFAULT_DURABLE_ARCHIVE_ROOT
    root = repo_root or Path(__file__).resolve().parents[2]
    registry_path = lifecycle_registry_path or (archive_root / DEFAULT_LIFECYCLE_REGISTRY_REL)
    if not registry_path.is_file():
        registry_path = DEFAULT_DURABLE_ARCHIVE_ROOT / DEFAULT_LIFECYCLE_REGISTRY_REL

    candidate_integrity = verify_candidate_integrity_v0(
        candidate_root=candidate_root,
        closeout_manifest_digest=closeout_manifest_digest,
    )
    fetch_spec = json.loads((candidate_root / "fetch_spec.json").read_text(encoding="utf-8"))
    aggregates = json.loads(
        (candidate_root / "completeness" / "aggregates.json").read_text(encoding="utf-8")
    )
    cells = _load_panel_cells(candidate_root)

    read_result = read_registry_snapshot_v1(
        root_dir=registry_path.parent,
        relative_path=Path(registry_path.name),
    )
    if not read_result.success or read_result.snapshot is None:
        decision = PromotionDecisionStatus.BLOCKED
        reason_codes = ("LIFECYCLE_REGISTRY_READ_FAILED",)
        binding = build_promotion_binding_v0(
            candidate_integrity=candidate_integrity,
            universe_records=(),
            fetch_spec=fetch_spec,
            decision=decision,
            reason_codes=reason_codes,
            input_evidence_refs=(implementation_evidence_ref, closeout_evidence_ref),
            decision_timestamp_utc=_utc_now_iso(),
        )
        return PromotionDecisionResultV0(
            decision=decision,
            reason_codes=reason_codes,
            candidate_integrity=candidate_integrity,
            universe_records=(),
            promotion_binding=binding,
            dataset_promoted=False,
            dataset_binding_active=False,
            registry_entry_path=None,
            alias_updated=False,
            idempotent_status=IdempotentRepromotionStatus.NOT_APPLICABLE,
            registry_mutation=False,
            economic_evaluation_authorized=False,
            promotion_effect=PROMOTION_EFFECT_NONE,
            runtime_effect=RUNTIME_EFFECT,
            authority_effect=AUTHORITY_EFFECT,
        )

    window = compute_bounded_window_v0()
    universe_records = build_universe_denominator_matrix_v0(
        snapshot=read_result.snapshot,
        period_start_ms=window.start_ms,
    )
    decision, reason_codes = evaluate_promotion_decision_v0(
        candidate_integrity=candidate_integrity,
        universe_records=universe_records,
        cells=cells,
        aggregates=aggregates,
        fetch_spec=fetch_spec,
    )
    decision_ts = _utc_now_iso()
    binding = build_promotion_binding_v0(
        candidate_integrity=candidate_integrity,
        universe_records=universe_records,
        fetch_spec=fetch_spec,
        decision=decision,
        reason_codes=reason_codes,
        input_evidence_refs=(implementation_evidence_ref, closeout_evidence_ref),
        decision_timestamp_utc=decision_ts,
    )

    promoted_root: str | None = None
    registry_entry_path: str | None = None
    alias_updated = False
    idempotent_status = IdempotentRepromotionStatus.NOT_APPLICABLE
    registry_mutation = False

    if decision == PromotionDecisionStatus.PROMOTED and write_registry:
        promoted_path, idempotent_status, alias_updated = write_promoted_dataset_registry_v0(
            durable_archive_root=archive_root,
            repo_root=root,
            promotion_binding=binding,
        )
        promoted_root = str(promoted_path)
        registry_entry_path = str(promoted_path / "registry_entry.json")

    dataset_promoted = decision == PromotionDecisionStatus.PROMOTED and idempotent_status in {
        IdempotentRepromotionStatus.NEW_PROMOTION,
        IdempotentRepromotionStatus.NO_OP_SUCCESS,
    }
    registry_mutation = idempotent_status == IdempotentRepromotionStatus.NEW_PROMOTION

    return PromotionDecisionResultV0(
        decision=decision,
        reason_codes=reason_codes,
        candidate_integrity=candidate_integrity,
        universe_records=universe_records,
        promotion_binding=binding,
        dataset_promoted=dataset_promoted,
        dataset_binding_active=dataset_promoted,
        registry_entry_path=registry_entry_path,
        alias_updated=alias_updated,
        idempotent_status=idempotent_status,
        registry_mutation=registry_mutation,
        economic_evaluation_authorized=False,
        promotion_effect=binding.promotion_effect,
        runtime_effect=RUNTIME_EFFECT,
        authority_effect=AUTHORITY_EFFECT,
        promoted_dataset_root=promoted_root,
    )
