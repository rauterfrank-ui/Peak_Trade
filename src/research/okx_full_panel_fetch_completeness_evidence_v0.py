"""OKX full-panel archive fetch and completeness evidence orchestrator v0.

Bounded, reproducible full-panel funding archive fetch with PIT lifecycle,
missing-funding fail-closed, carry validation, and manifest-verified evidence.
Research-only; no dataset promotion, economic evaluation, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from src.research.cross_sectional_bounded_panel_fetch_v0 import compute_bounded_window_v0
from src.research.missing_funding_policy_v0 import (
    MISSING_FUNDING_FAIL_CLOSED,
    MISSING_FUNDING_VALUE,
    is_missing_funding_value_v0,
)
from src.research.okx_historical_funding_archive_ingest_v0 import (
    MODULE_VERSION as ARCHIVE_INGEST_VERSION,
    ArchiveAccessGuardReason,
    ArchiveAccessGuardV0,
    ArchiveIngestTerminalStatus,
    ArchiveRetrievalRecordV0,
    build_archive_cdn_url_v0,
    check_full_panel_promotion_allowed_v0,
    compute_required_month_buckets_v0,
    deduplicate_archive_events_v0,
    parse_archive_zip_bytes_v0,
)
from src.research.okx_historical_funding_archive_lifecycle_integration_v0 import (
    ArchiveLifecycleGateReason,
    evaluate_archive_funding_lifecycle_gate_v0,
    integration_contract_v0,
)
from src.research.pit_futures_instrument_lifecycle_registry_persistence_v1 import (
    read_registry_snapshot_v1,
)
from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
    QueryState,
    RegistrySnapshotV1,
)

PACKAGE_MARKER = "OKX_FULL_PANEL_FETCH_COMPLETENESS_EVIDENCE_V0=true"
ORCHESTRATOR_VERSION = "okx_full_panel_fetch_completeness_evidence.v0"
GO_TOKEN = "GO_BOUNDED_OKX_FULL_PANEL_FETCH_AND_COMPLETENESS_EVIDENCE_V0"
FETCH_SCOPE_ID = "bounded_okx_full_panel_fetch_and_completeness_evidence_v0"
FETCH_SPEC_VERSION = "v0"
COMPLETENESS_POLICY_VERSION = "okx_full_panel_completeness.v0"
QUARANTINE_SUBDIR = "quarantine/okx_historical_funding_archive_v0"
ARCHIVE_CACHE_SUBDIR = "datasets/staging/okx_historical_funding_archive_v0"
DEFAULT_DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
DEFAULT_LIFECYCLE_REGISTRY_REL = (
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_historical_2024_v1/v1/"
    "lifecycle/registry_snapshot_v1.json"
)
DEFAULT_OHLCV_RAW_REL = (
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_historical_2024_v1/v1/raw"
)
DEFAULT_PROBE_ARCHIVE_REL = "probes/okx_historical_funding_archive_probe_v0_20260703T160811Z/raw"
PR4804_QUARANTINE_ROOT = ".tmp_historical_20260703T134626Z"

HttpFetcher = Callable[[str, float], tuple[int, bytes, dict[str, str]]]


class FetchReasonCode(str, Enum):
    FETCHED = "FETCHED"
    REUSED_EXISTING = "REUSED_EXISTING"
    NOT_AVAILABLE_AT_SOURCE = "NOT_AVAILABLE_AT_SOURCE"
    NOT_LISTED_AT_TIME = "NOT_LISTED_AT_TIME"
    DELISTED_OR_EXPIRED = "DELISTED_OR_EXPIRED"
    MISSING_LIFECYCLE_EVIDENCE = "MISSING_LIFECYCLE_EVIDENCE"
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"
    CHECKSUM_FAILED = "CHECKSUM_FAILED"
    ARCHIVE_CORRUPT = "ARCHIVE_CORRUPT"
    FUNDING_HISTORY_MISSING = "FUNDING_HISTORY_MISSING"
    CARRY_HISTORY_MISSING = "CARRY_HISTORY_MISSING"
    PIT_JOIN_FAILED = "PIT_JOIN_FAILED"
    QUARANTINED = "QUARANTINED"
    COMPLETE = "COMPLETE"


class PanelCompletenessOutcome(str, Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    BLOCKED = "BLOCKED"
    INCONCLUSIVE = "INCONCLUSIVE"


class ExecutionTerminalStatus(str, Enum):
    EXECUTION_COMPLETE = "EXECUTION_COMPLETE"
    GUARD_EXCEEDED_FAIL_CLOSED = "GUARD_EXCEEDED_FAIL_CLOSED"
    VALIDATION_FAILED = "VALIDATION_FAILED"


@dataclass(frozen=True)
class QuarantineMeasurementPolicyV0:
    quarantine_root_canonical: str
    quarantine_root_pr4804: str
    quarantine_root_pr4805: str
    measurement_scope: str
    count_method: str
    byte_method: str
    symlink_policy: str
    hidden_file_policy: str
    comparability_with_pr4804: str
    comparability_with_pr4805: str
    discrepancy_root_cause: str


@dataclass(frozen=True)
class QuarantineInventoryV0:
    root: str
    file_count: int
    byte_count: int


@dataclass(frozen=True)
class FullPanelFetchSpecV0:
    fetch_scope_id: str
    fetch_spec_version: str
    venue: str
    market_type: str
    instrument_selection_policy: str
    universe_snapshot_policy: str
    lifecycle_registry_version: str
    requested_instruments: tuple[str, ...]
    requested_contract_types: tuple[str, ...]
    requested_start_time: str
    requested_end_time: str
    archive_endpoints: tuple[str, ...]
    archive_object_patterns: tuple[str, ...]
    retry_policy: Mapping[str, int]
    rate_limit_policy: Mapping[str, float]
    timeout_policy: Mapping[str, float]
    checksum_policy: str
    local_staging_root: str
    quarantine_root: str
    dataset_candidate_root: str
    existing_file_policy: str
    duplicate_object_policy: str
    incomplete_download_policy: str
    corrupted_archive_policy: str
    missing_funding_policy: str
    missing_carry_policy: str
    pit_join_policy: str
    completeness_policy_version: str
    implementation_digest: str
    config_digest: str


@dataclass(frozen=True)
class ArchiveObjectResultV0:
    portal_reference: str
    instrument_id: str
    venue_symbol: str
    month: str
    reason_code: FetchReasonCode
    http_status: int
    sha256: str
    byte_count: int
    local_path: str | None
    retrieval_record: ArchiveRetrievalRecordV0 | None


@dataclass(frozen=True)
class PanelCellV0:
    instrument_id: str
    venue_symbol: str
    contract_type: str
    period_start: str
    period_end: str
    lifecycle_status: str
    archive_status: str
    price_history_status: str
    funding_history_status: str
    carry_history_status: str
    pit_join_status: str
    checksum_status: str
    completeness_status: str
    quarantine_status: str
    reason_codes: tuple[str, ...]
    source_object_refs: tuple[str, ...]
    content_digests: tuple[str, ...]


@dataclass(frozen=True)
class CompletenessAggregatesV0:
    instruments_requested: int
    instruments_lifecycle_admissible: int
    instruments_complete: int
    instruments_incomplete: int
    instruments_blocked: int
    instruments_quarantined: int
    periods_requested: int
    periods_complete: int
    periods_incomplete: int
    funding_cells_required: int
    funding_cells_present: int
    funding_cells_missing: int
    carry_cells_required: int
    carry_cells_present: int
    carry_cells_missing: int
    pit_cells_pass: int
    pit_cells_fail: int
    archive_objects_requested: int
    archive_objects_downloaded: int
    archive_objects_reused: int
    archive_objects_missing: int
    archive_objects_failed: int
    archive_objects_quarantined: int
    panel_completeness_ratio: float
    funding_completeness_ratio: float
    carry_completeness_ratio: float
    lifecycle_completeness_ratio: float
    pit_completeness_ratio: float


@dataclass(frozen=True)
class FullPanelFetchExecutionResultV0:
    status: ExecutionTerminalStatus
    fetch_spec: FullPanelFetchSpecV0
    aggregates: CompletenessAggregatesV0
    panel_outcome: PanelCompletenessOutcome
    cells: tuple[PanelCellV0, ...]
    archive_results: tuple[ArchiveObjectResultV0, ...]
    quarantine_before: QuarantineInventoryV0
    quarantine_after: QuarantineInventoryV0
    quarantine_measurement_policy: QuarantineMeasurementPolicyV0
    dataset_candidate_staged: bool
    dataset_candidate_root: str
    full_panel_fetch_executed: bool
    panel_completeness_evaluated: bool
    dataset_promoted: bool
    economic_evaluation_executed: bool
    promotion_effect: str
    runtime_effect: str
    authority_effect: str
    manifest_verify_rc: int
    guard_fail_reason: str
    request_records: tuple[Mapping[str, Any], ...]


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _is_bitcoin_venue_symbol(venue_symbol: str) -> bool:
    lowered = venue_symbol.lower()
    return any(token in lowered for token in ("btc", "xbt", "bitcoin"))


def quarantine_measurement_policy_v0(
    *, durable_archive_root: Path
) -> QuarantineMeasurementPolicyV0:
    canonical = durable_archive_root / QUARANTINE_SUBDIR
    return QuarantineMeasurementPolicyV0(
        quarantine_root_canonical=str(canonical),
        quarantine_root_pr4804=PR4804_QUARANTINE_ROOT,
        quarantine_root_pr4805=str(canonical),
        measurement_scope="regular_files_under_root_recursive",
        count_method="pathlib_rglob_is_file_not_symlink",
        byte_method="sum_path_stat_st_size_for_regular_files",
        symlink_policy="exclude_symlink_entries_from_count_and_bytes",
        hidden_file_policy="include_dotfiles",
        comparability_with_pr4804=(
            "NOT_DIRECTLY_COMPARABLE: PR4804 counted repo-root .tmp_historical_* partial "
            "OHLCV staging (9309 files); different root and artifact class"
        ),
        comparability_with_pr4805=(
            "NOT_DIRECTLY_COMPARABLE: PR4805 was code-only; canonical quarantine root "
            "did not exist yet (0 files)"
        ),
        discrepancy_root_cause=(
            "PR4804 measured ephemeral repo .tmp_historical fetch staging; PR4805 measured "
            "canonical durable quarantine before any fetch scope created it"
        ),
    )


def measure_quarantine_inventory_v0(root: Path) -> QuarantineInventoryV0:
    if not root.exists():
        return QuarantineInventoryV0(root=str(root), file_count=0, byte_count=0)
    file_count = 0
    byte_count = 0
    for path in root.rglob("*"):
        if path.is_file() and not path.is_symlink():
            file_count += 1
            byte_count += path.stat().st_size
    return QuarantineInventoryV0(root=str(root), file_count=file_count, byte_count=byte_count)


def _default_http_fetcher(url: str, timeout_seconds: float) -> tuple[int, bytes, dict[str, str]]:
    request = urllib.request.Request(url, headers={"User-Agent": "PeakTradeArchiveFetch/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read()
            headers = {k.lower(): v for k, v in response.headers.items()}
            return response.status, body, headers
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), {k.lower(): v for k, v in exc.headers.items()}
    except urllib.error.URLError:
        return 0, b"", {}


def _venue_symbol_to_ohlcv_prefix(venue_symbol: str) -> str:
    base = venue_symbol.replace("-SWAP", "").replace("-", "_").lower()
    return f"ohlcv_{base}_swap_"


def _price_history_present(raw_ohlcv_dir: Path, venue_symbol: str) -> bool:
    if not raw_ohlcv_dir.is_dir():
        return False
    prefix = _venue_symbol_to_ohlcv_prefix(venue_symbol)
    return any(raw_ohlcv_dir.glob(f"{prefix}*.json"))


def derive_registry_instruments_v0(
    snapshot: RegistrySnapshotV1,
    *,
    period_start_ms: int,
) -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]]]:
    """Return (lifecycle_admissible, all_requested) as (instrument_id, venue_symbol, contract_type)."""
    seen: dict[str, tuple[str, str, str]] = {}
    for interval in snapshot.intervals:
        if interval.superseded_by_version is not None:
            continue
        venue_symbol = interval.venue_symbol
        if not venue_symbol or _is_bitcoin_venue_symbol(venue_symbol):
            continue
        seen[interval.instrument_id] = (
            interval.instrument_id,
            venue_symbol,
            interval.contract_type,
        )
    all_requested = sorted(seen.values(), key=lambda item: item[0])
    admissible: list[tuple[str, str, str]] = []
    decision_instant = datetime.fromtimestamp(period_start_ms / 1000, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
        query_lifecycle_at_snapshot_v1,
    )

    for instrument_id, venue_symbol, contract_type in all_requested:
        query = query_lifecycle_at_snapshot_v1(
            snapshot,
            instrument_id=instrument_id,
            query_instant=decision_instant,
        )
        if query.query_state == QueryState.ELIGIBLE.value and not query.error_codes:
            admissible.append((instrument_id, venue_symbol, contract_type))
    return admissible, all_requested


def build_fetch_spec_v0(
    *,
    durable_archive_root: Path,
    execution_root: Path,
    archive_dir: Path,
    snapshot: RegistrySnapshotV1,
    admissible: Sequence[tuple[str, str, str]],
    window: Any,
    config_digest: str,
) -> FullPanelFetchSpecV0:
    quarantine_root = durable_archive_root / QUARANTINE_SUBDIR
    months = compute_required_month_buckets_v0(
        period_start_utc=window.start_inclusive_utc,
        period_end_exclusive_utc=window.end_exclusive_utc,
        pre_window_hours=window.required_pre_window_hours,
    )
    impl_payload = {
        "orchestrator_version": ORCHESTRATOR_VERSION,
        "archive_ingest_version": ARCHIVE_INGEST_VERSION,
        "integration_contract": integration_contract_v0().__dict__,
    }
    return FullPanelFetchSpecV0(
        fetch_scope_id=FETCH_SCOPE_ID,
        fetch_spec_version=FETCH_SPEC_VERSION,
        venue="OKX",
        market_type="FUTURES_OR_PERPETUALS_ONLY",
        instrument_selection_policy=(
            "pit_futures_instrument_lifecycle_registry_v1:ELIGIBLE_at_period_start;"
            "exclude_bitcoin_venue_symbols"
        ),
        universe_snapshot_policy="lifecycle_registry_snapshot_canonical_not_archive_coverage",
        lifecycle_registry_version=snapshot.registry_snapshot_version,
        requested_instruments=tuple(item[0] for item in admissible),
        requested_contract_types=tuple(sorted({item[2] for item in admissible})),
        requested_start_time=window.start_inclusive_utc,
        requested_end_time=window.end_exclusive_utc,
        archive_endpoints=("https://static.okx.com/cdn/okex/traderecords/swaprates/monthly",),
        archive_object_patterns=("{yyyymm}/{venue_symbol}-fundingrates-{yyyy}-{mm}.zip",),
        retry_policy={"max_attempts": 3, "backoff_ms": 500},
        rate_limit_policy={"min_interval_seconds": 0.15},
        timeout_policy={"connect_seconds": 15.0, "read_seconds": 60.0},
        checksum_policy="sha256_hex_required_for_valid_archive",
        local_staging_root=str(archive_dir),
        quarantine_root=str(quarantine_root),
        dataset_candidate_root=str(execution_root),
        existing_file_policy="reuse_when_sha256_matches_sidecar",
        duplicate_object_policy="quarantine_collision_safe_no_overwrite",
        incomplete_download_policy="quarantine_fail_closed",
        corrupted_archive_policy="quarantine_fail_closed",
        missing_funding_policy="missing_funding_policy_v0:fail_closed_no_zero",
        missing_carry_policy="funding_rate_proxy_fail_closed_no_zero_fallback",
        pit_join_policy="backward_asof_lifecycle_first_archive_second",
        completeness_policy_version=COMPLETENESS_POLICY_VERSION,
        implementation_digest=_stable_digest(impl_payload),
        config_digest=config_digest,
    )


def _sidecar_path(archive_path: Path) -> Path:
    return archive_path.with_suffix(archive_path.suffix + ".sha256")


def _write_sidecar(archive_path: Path, digest: str) -> None:
    _sidecar_path(archive_path).write_text(f"{digest}  {archive_path.name}\n", encoding="utf-8")


def _read_sidecar_digest(archive_path: Path) -> str | None:
    sidecar = _sidecar_path(archive_path)
    if not sidecar.is_file():
        return None
    line = sidecar.read_text(encoding="utf-8").strip().split()
    return line[0] if line else None


def _quarantine_write(
    quarantine_root: Path,
    *,
    content: bytes,
    label: str,
) -> Path:
    quarantine_root.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(content).hexdigest()
    target = quarantine_root / f"{label}_{digest[:16]}.bin"
    if not target.exists():
        target.write_bytes(content)
    return target


def fetch_archive_object_v0(
    *,
    venue_symbol: str,
    month: str,
    archive_dir: Path,
    quarantine_root: Path,
    guard: ArchiveAccessGuardV0,
    probe_archive_dir: Path | None,
    fetcher: HttpFetcher,
    timeout_seconds: float,
    min_interval_seconds: float,
    last_fetch_monotonic: float,
) -> tuple[ArchiveObjectResultV0, float]:
    year_str, month_str = month.split("-")
    year = int(year_str)
    month_num = int(month_str)
    url = build_archive_cdn_url_v0(instrument_id=venue_symbol, year=year, month=month_num)
    filename = f"{venue_symbol}-fundingrates-{month}.zip"
    target = archive_dir / filename
    retrieval_time = _utc_now_iso()

    for candidate_dir in (probe_archive_dir,):
        if candidate_dir is None or not candidate_dir.is_dir():
            continue
        probe_name = f"{venue_symbol.split('-')[0]}-USDT_{venue_symbol}-fundingrates-{month}.zip"
        probe_path = candidate_dir / probe_name
        if probe_path.is_file():
            body = probe_path.read_bytes()
            digest = hashlib.sha256(body).hexdigest()
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(body)
                _write_sidecar(target, digest)
            record = ArchiveRetrievalRecordV0(
                portal_reference=str(probe_path),
                instrument_id=venue_symbol,
                month=month,
                expected_data_type="FUNDING_ARCHIVE",
                http_status=200,
                content_type="application/zip",
                content_length=len(body),
                sha256=digest,
                retrieval_time=retrieval_time,
                raw_provenance="REUSED_PROBE",
            )
            return (
                ArchiveObjectResultV0(
                    portal_reference=str(probe_path),
                    instrument_id=venue_symbol,
                    venue_symbol=venue_symbol,
                    month=month,
                    reason_code=FetchReasonCode.REUSED_EXISTING,
                    http_status=200,
                    sha256=digest,
                    byte_count=len(body),
                    local_path=str(target),
                    retrieval_record=record,
                ),
                last_fetch_monotonic,
            )

    if target.is_file():
        body = target.read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        sidecar = _read_sidecar_digest(target)
        if sidecar == digest:
            record = ArchiveRetrievalRecordV0(
                portal_reference=url,
                instrument_id=venue_symbol,
                month=month,
                expected_data_type="FUNDING_ARCHIVE",
                http_status=200,
                content_type="application/zip",
                content_length=len(body),
                sha256=digest,
                retrieval_time=retrieval_time,
                raw_provenance="REUSED_STAGING",
            )
            return (
                ArchiveObjectResultV0(
                    portal_reference=url,
                    instrument_id=venue_symbol,
                    venue_symbol=venue_symbol,
                    month=month,
                    reason_code=FetchReasonCode.REUSED_EXISTING,
                    http_status=200,
                    sha256=digest,
                    byte_count=len(body),
                    local_path=str(target),
                    retrieval_record=record,
                ),
                last_fetch_monotonic,
            )
        _quarantine_write(quarantine_root, content=body, label=f"checksum_mismatch_{filename}")

    elapsed = time.monotonic() - last_fetch_monotonic
    if elapsed < min_interval_seconds:
        time.sleep(min_interval_seconds - elapsed)

    guard_reason = guard.check_request()
    if guard_reason:
        return (
            ArchiveObjectResultV0(
                portal_reference=url,
                instrument_id=venue_symbol,
                venue_symbol=venue_symbol,
                month=month,
                reason_code=FetchReasonCode.DOWNLOAD_FAILED,
                http_status=0,
                sha256="",
                byte_count=0,
                local_path=None,
                retrieval_record=None,
            ),
            time.monotonic(),
        )

    status, body, headers = fetcher(url, timeout_seconds)
    guard.record_request(len(body))
    last_fetch_monotonic = time.monotonic()

    if status == 404:
        return (
            ArchiveObjectResultV0(
                portal_reference=url,
                instrument_id=venue_symbol,
                venue_symbol=venue_symbol,
                month=month,
                reason_code=FetchReasonCode.NOT_AVAILABLE_AT_SOURCE,
                http_status=status,
                sha256="",
                byte_count=0,
                local_path=None,
                retrieval_record=None,
            ),
            last_fetch_monotonic,
        )
    if status != 200 or not body:
        _quarantine_write(quarantine_root, content=body, label=f"download_failed_{filename}")
        return (
            ArchiveObjectResultV0(
                portal_reference=url,
                instrument_id=venue_symbol,
                venue_symbol=venue_symbol,
                month=month,
                reason_code=FetchReasonCode.DOWNLOAD_FAILED,
                http_status=status,
                sha256="",
                byte_count=len(body),
                local_path=None,
                retrieval_record=None,
            ),
            last_fetch_monotonic,
        )

    digest = hashlib.sha256(body).hexdigest()
    if target.exists():
        existing = target.read_bytes()
        existing_digest = hashlib.sha256(existing).hexdigest()
        if existing_digest != digest:
            _quarantine_write(quarantine_root, content=body, label=f"collision_{filename}")
            return (
                ArchiveObjectResultV0(
                    portal_reference=url,
                    instrument_id=venue_symbol,
                    venue_symbol=venue_symbol,
                    month=month,
                    reason_code=FetchReasonCode.QUARANTINED,
                    http_status=status,
                    sha256=digest,
                    byte_count=len(body),
                    local_path=None,
                    retrieval_record=None,
                ),
                last_fetch_monotonic,
            )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    _write_sidecar(target, digest)
    record = ArchiveRetrievalRecordV0(
        portal_reference=url,
        instrument_id=venue_symbol,
        month=month,
        expected_data_type="FUNDING_ARCHIVE",
        http_status=status,
        content_type=headers.get("content-type", "application/zip"),
        content_length=len(body),
        sha256=digest,
        retrieval_time=retrieval_time,
        raw_provenance="FETCHED",
    )
    return (
        ArchiveObjectResultV0(
            portal_reference=url,
            instrument_id=venue_symbol,
            venue_symbol=venue_symbol,
            month=month,
            reason_code=FetchReasonCode.FETCHED,
            http_status=status,
            sha256=digest,
            byte_count=len(body),
            local_path=str(target),
            retrieval_record=record,
        ),
        last_fetch_monotonic,
    )


def _evaluate_carry_from_funding(funding_rate: str | None) -> tuple[str, str]:
    if is_missing_funding_value_v0(funding_rate):
        return "MISSING", FetchReasonCode.CARRY_HISTORY_MISSING.value
    try:
        val = float(funding_rate)
        if not math.isfinite(val):
            return "MISSING", FetchReasonCode.CARRY_HISTORY_MISSING.value
    except (TypeError, ValueError):
        return "MISSING", FetchReasonCode.CARRY_HISTORY_MISSING.value
    return "PRESENT", FetchReasonCode.COMPLETE.value


def evaluate_panel_cell_v0(
    *,
    snapshot: RegistrySnapshotV1,
    instrument_id: str,
    venue_symbol: str,
    contract_type: str,
    period_start: str,
    period_end: str,
    archive_results: Sequence[ArchiveObjectResultV0],
    events_by_symbol: Mapping[str, tuple[Any, ...]],
    raw_ohlcv_dir: Path,
    decision_bar_time_ms: int,
) -> PanelCellV0:
    period_archives = [r for r in archive_results if r.venue_symbol == venue_symbol]
    archive_reasons = [r.reason_code.value for r in period_archives]
    if any(r.reason_code == FetchReasonCode.QUARANTINED for r in period_archives):
        archive_status = "QUARANTINED"
    elif (
        all(
            r.reason_code in {FetchReasonCode.FETCHED, FetchReasonCode.REUSED_EXISTING}
            for r in period_archives
            if r.reason_code != FetchReasonCode.NOT_AVAILABLE_AT_SOURCE
        )
        and period_archives
    ):
        archive_status = "COMPLETE"
    elif any(r.reason_code == FetchReasonCode.NOT_AVAILABLE_AT_SOURCE for r in period_archives):
        archive_status = "PARTIAL_MISSING"
    else:
        archive_status = "INCOMPLETE"

    events = events_by_symbol.get(venue_symbol, ())
    gate = evaluate_archive_funding_lifecycle_gate_v0(
        snapshot,
        events,
        instrument_id=instrument_id,
        decision_bar_time_ms=decision_bar_time_ms,
        venue_symbol=venue_symbol,
    )
    if gate.allowed and not is_missing_funding_value_v0(gate.funding_rate):
        funding_status = "PRESENT"
        pit_status = "PASS"
        funding_reason = FetchReasonCode.COMPLETE.value
    elif gate.reason_code == ArchiveLifecycleGateReason.MISSING_FUNDING_NO_PRIOR_SETTLEMENT.value:
        funding_status = "MISSING"
        pit_status = "FAIL"
        funding_reason = FetchReasonCode.FUNDING_HISTORY_MISSING.value
    else:
        funding_status = "MISSING"
        pit_status = "FAIL"
        funding_reason = gate.reason_code or FetchReasonCode.PIT_JOIN_FAILED.value

    carry_status, carry_reason = _evaluate_carry_from_funding(gate.funding_rate)
    price_status = "PRESENT" if _price_history_present(raw_ohlcv_dir, venue_symbol) else "MISSING"
    checksum_status = (
        "PASS"
        if all(
            r.sha256
            for r in period_archives
            if r.reason_code != FetchReasonCode.NOT_AVAILABLE_AT_SOURCE
        )
        else "UNKNOWN"
    )
    quarantine_status = "QUARANTINED" if archive_status == "QUARANTINED" else "CLEAN"

    reason_codes = tuple(
        sorted(
            {
                code
                for code in (
                    *archive_reasons,
                    gate.reason_code or "",
                    funding_reason,
                    carry_reason,
                )
                if code
            }
        )
    )
    if gate.lifecycle_query_state != QueryState.ELIGIBLE.value:
        lifecycle_status = gate.lifecycle_query_state
    else:
        lifecycle_status = QueryState.ELIGIBLE.value

    blocked_lifecycle = gate.lifecycle_query_state != QueryState.ELIGIBLE.value
    if blocked_lifecycle:
        completeness_status = "BLOCKED"
    elif (
        archive_status == "COMPLETE"
        and funding_status == "PRESENT"
        and carry_status == "PRESENT"
        and price_status == "PRESENT"
        and pit_status == "PASS"
    ):
        completeness_status = "COMPLETE"
    else:
        completeness_status = "INCOMPLETE"

    return PanelCellV0(
        instrument_id=instrument_id,
        venue_symbol=venue_symbol,
        contract_type=contract_type,
        period_start=period_start,
        period_end=period_end,
        lifecycle_status=lifecycle_status,
        archive_status=archive_status,
        price_history_status=price_status,
        funding_history_status=funding_status,
        carry_history_status=carry_status,
        pit_join_status=pit_status,
        checksum_status=checksum_status,
        completeness_status=completeness_status,
        quarantine_status=quarantine_status,
        reason_codes=reason_codes,
        source_object_refs=tuple(r.portal_reference for r in period_archives),
        content_digests=tuple(r.sha256 for r in period_archives if r.sha256),
    )


def compute_aggregates_v0(
    *,
    all_requested: Sequence[tuple[str, str, str]],
    admissible: Sequence[tuple[str, str, str]],
    cells: Sequence[PanelCellV0],
    archive_results: Sequence[ArchiveObjectResultV0],
) -> CompletenessAggregatesV0:
    instruments_complete = len(
        {c.instrument_id for c in cells if c.completeness_status == "COMPLETE"}
    )
    instruments_incomplete = len(
        {c.instrument_id for c in cells if c.completeness_status == "INCOMPLETE"}
    )
    instruments_blocked = len(
        {c.instrument_id for c in cells if c.completeness_status == "BLOCKED"}
    )
    instruments_quarantined = len(
        {c.instrument_id for c in cells if c.quarantine_status == "QUARANTINED"}
    )
    periods_complete = sum(1 for c in cells if c.completeness_status == "COMPLETE")
    periods_incomplete = sum(1 for c in cells if c.completeness_status == "INCOMPLETE")
    funding_required = sum(1 for c in cells if c.lifecycle_status == QueryState.ELIGIBLE.value)
    funding_present = sum(
        1 for c in cells if c.funding_history_status == "PRESENT" and c.pit_join_status == "PASS"
    )
    funding_missing = funding_required - funding_present
    carry_present = sum(1 for c in cells if c.carry_history_status == "PRESENT")
    carry_missing = funding_required - carry_present
    pit_pass = sum(1 for c in cells if c.pit_join_status == "PASS")
    pit_fail = sum(1 for c in cells if c.pit_join_status == "FAIL")
    downloaded = sum(1 for r in archive_results if r.reason_code == FetchReasonCode.FETCHED)
    reused = sum(1 for r in archive_results if r.reason_code == FetchReasonCode.REUSED_EXISTING)
    missing = sum(
        1 for r in archive_results if r.reason_code == FetchReasonCode.NOT_AVAILABLE_AT_SOURCE
    )
    failed = sum(1 for r in archive_results if r.reason_code == FetchReasonCode.DOWNLOAD_FAILED)
    quarantined = sum(1 for r in archive_results if r.reason_code == FetchReasonCode.QUARANTINED)
    total_inst = len(all_requested)
    admissible_count = len(admissible)
    panel_ratio = instruments_complete / admissible_count if admissible_count else 0.0
    funding_ratio = funding_present / funding_required if funding_required else 0.0
    carry_ratio = carry_present / funding_required if funding_required else 0.0
    lifecycle_ratio = admissible_count / total_inst if total_inst else 0.0
    pit_ratio = pit_pass / (pit_pass + pit_fail) if (pit_pass + pit_fail) else 0.0
    return CompletenessAggregatesV0(
        instruments_requested=total_inst,
        instruments_lifecycle_admissible=admissible_count,
        instruments_complete=instruments_complete,
        instruments_incomplete=instruments_incomplete,
        instruments_blocked=instruments_blocked,
        instruments_quarantined=instruments_quarantined,
        periods_requested=len(cells),
        periods_complete=periods_complete,
        periods_incomplete=periods_incomplete,
        funding_cells_required=funding_required,
        funding_cells_present=funding_present,
        funding_cells_missing=funding_missing,
        carry_cells_required=funding_required,
        carry_cells_present=carry_present,
        carry_cells_missing=carry_missing,
        pit_cells_pass=pit_pass,
        pit_cells_fail=pit_fail,
        archive_objects_requested=len(archive_results),
        archive_objects_downloaded=downloaded,
        archive_objects_reused=reused,
        archive_objects_missing=missing,
        archive_objects_failed=failed,
        archive_objects_quarantined=quarantined,
        panel_completeness_ratio=round(panel_ratio, 6),
        funding_completeness_ratio=round(funding_ratio, 6),
        carry_completeness_ratio=round(carry_ratio, 6),
        lifecycle_completeness_ratio=round(lifecycle_ratio, 6),
        pit_completeness_ratio=round(pit_ratio, 6),
    )


def classify_panel_outcome_v0(aggregates: CompletenessAggregatesV0) -> PanelCompletenessOutcome:
    if aggregates.instruments_requested == 0:
        return PanelCompletenessOutcome.INCONCLUSIVE
    if aggregates.instruments_blocked == aggregates.instruments_lifecycle_admissible:
        return PanelCompletenessOutcome.BLOCKED
    if (
        aggregates.instruments_complete == aggregates.instruments_lifecycle_admissible
        and aggregates.funding_cells_missing == 0
        and aggregates.carry_cells_missing == 0
    ):
        return PanelCompletenessOutcome.COMPLETE
    if aggregates.archive_objects_failed > 0 and aggregates.archive_objects_downloaded == 0:
        return PanelCompletenessOutcome.INCONCLUSIVE
    return PanelCompletenessOutcome.INCOMPLETE


def run_okx_full_panel_fetch_completeness_evidence_v0(
    *,
    confirm: str,
    durable_archive_root: Path | None = None,
    lifecycle_registry_path: Path | None = None,
    ohlcv_raw_dir: Path | None = None,
    probe_archive_dir: Path | None = None,
    execution_root: Path | None = None,
    max_instruments: int | None = None,
    max_http_requests: int = 2500,
    max_total_bytes: int = 500_000_000,
    max_runtime_seconds: int = 900,
    fetcher: HttpFetcher | None = None,
    network_enabled: bool = True,
) -> FullPanelFetchExecutionResultV0:
    if confirm != GO_TOKEN:
        raise ValueError(f"GO_TOKEN_REQUIRED:{GO_TOKEN}")

    promotion_allowed, promotion_blocker = check_full_panel_promotion_allowed_v0()
    if not promotion_allowed:
        raise ValueError(f"FULL_PANEL_PROMOTION_BLOCKED:{promotion_blocker}")

    archive_root = durable_archive_root or DEFAULT_DURABLE_ARCHIVE_ROOT
    registry_path = lifecycle_registry_path or (archive_root / DEFAULT_LIFECYCLE_REGISTRY_REL)
    raw_ohlcv = ohlcv_raw_dir or (archive_root / DEFAULT_OHLCV_RAW_REL)
    probe_dir = probe_archive_dir or (archive_root / DEFAULT_PROBE_ARCHIVE_REL)
    quarantine_root = archive_root / QUARANTINE_SUBDIR

    measurement_policy = quarantine_measurement_policy_v0(durable_archive_root=archive_root)
    quarantine_before = measure_quarantine_inventory_v0(quarantine_root)

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    exec_root = execution_root or (
        archive_root / "datasets/candidates" / f"okx_full_panel_fetch_completeness_v0_{ts_slug}"
    )
    exec_root.mkdir(parents=True, exist_ok=True)
    archive_dir = archive_root / ARCHIVE_CACHE_SUBDIR
    archive_dir.mkdir(parents=True, exist_ok=True)

    read_result = read_registry_snapshot_v1(
        root_dir=registry_path.parent,
        relative_path=Path(registry_path.name),
    )
    if not read_result.success or read_result.snapshot is None:
        raise ValueError(f"LIFECYCLE_REGISTRY_READ_FAILED:{read_result.error_codes}")
    snapshot = read_result.snapshot

    window = compute_bounded_window_v0()
    admissible, all_requested = derive_registry_instruments_v0(
        snapshot, period_start_ms=window.start_ms
    )
    if max_instruments is not None:
        admissible = admissible[:max_instruments]

    config_digest = snapshot.registry_snapshot_digest
    fetch_spec = build_fetch_spec_v0(
        durable_archive_root=archive_root,
        execution_root=exec_root,
        archive_dir=archive_dir,
        snapshot=snapshot,
        admissible=admissible,
        window=window,
        config_digest=config_digest,
    )
    (exec_root / "fetch_spec.json").write_text(
        json.dumps(fetch_spec.__dict__, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    months = compute_required_month_buckets_v0(
        period_start_utc=window.start_inclusive_utc,
        period_end_exclusive_utc=window.end_exclusive_utc,
        pre_window_hours=window.required_pre_window_hours,
    )
    guard = ArchiveAccessGuardV0(
        max_instruments=len(admissible),
        max_months=len(months) * max(len(admissible), 1),
        max_http_requests=max_http_requests,
        max_total_bytes=max_total_bytes,
        max_runtime_seconds=max_runtime_seconds,
    )

    http_fetcher = fetcher or _default_http_fetcher
    archive_results: list[ArchiveObjectResultV0] = []
    request_records: list[Mapping[str, Any]] = []
    events_by_symbol: dict[str, tuple[Any, ...]] = {}
    last_fetch = 0.0
    guard_fail = ""
    status = ExecutionTerminalStatus.EXECUTION_COMPLETE

    for instrument_id, venue_symbol, _contract_type in admissible:
        inst_reason = guard.check_instruments()
        if inst_reason:
            guard_fail = inst_reason
            status = ExecutionTerminalStatus.GUARD_EXCEEDED_FAIL_CLOSED
            break
        guard.instruments_used += 1
        for month in months:
            month_reason = guard.check_months()
            runtime_reason = guard.check_runtime()
            if month_reason or runtime_reason:
                guard_fail = month_reason or runtime_reason or ""
                status = ExecutionTerminalStatus.GUARD_EXCEEDED_FAIL_CLOSED
                break
            guard.months_used += 1

            if network_enabled:
                result, last_fetch = fetch_archive_object_v0(
                    venue_symbol=venue_symbol,
                    month=month,
                    archive_dir=archive_dir,
                    quarantine_root=quarantine_root,
                    guard=guard,
                    probe_archive_dir=probe_dir,
                    fetcher=http_fetcher,
                    timeout_seconds=60.0,
                    min_interval_seconds=0.15,
                    last_fetch_monotonic=last_fetch,
                )
            else:
                result = ArchiveObjectResultV0(
                    portal_reference=build_archive_cdn_url_v0(
                        instrument_id=venue_symbol,
                        year=int(month.split("-")[0]),
                        month=int(month.split("-")[1]),
                    ),
                    instrument_id=instrument_id,
                    venue_symbol=venue_symbol,
                    month=month,
                    reason_code=FetchReasonCode.NOT_AVAILABLE_AT_SOURCE,
                    http_status=0,
                    sha256="",
                    byte_count=0,
                    local_path=None,
                    retrieval_record=None,
                )
            archive_results.append(result)
            request_records.append(
                {
                    "instrument_id": instrument_id,
                    "venue_symbol": venue_symbol,
                    "month": month,
                    "reason_code": result.reason_code.value,
                    "http_status": result.http_status,
                    "sha256": result.sha256,
                }
            )
            if result.local_path and result.reason_code in {
                FetchReasonCode.FETCHED,
                FetchReasonCode.REUSED_EXISTING,
            }:
                parsed = parse_archive_zip_bytes_v0(
                    Path(result.local_path).read_bytes(),
                    expected_instrument_id=venue_symbol,
                )
                if parsed.status is ArchiveIngestTerminalStatus.COMPLETE:
                    merged = (*events_by_symbol.get(venue_symbol, ()), *parsed.events)
                    deduped, _ = deduplicate_archive_events_v0(merged)
                    events_by_symbol[venue_symbol] = deduped
                elif parsed.status is ArchiveIngestTerminalStatus.VALIDATION_FAILED:
                    corrupt_path = Path(result.local_path).read_bytes()
                    _quarantine_write(
                        quarantine_root,
                        content=corrupt_path,
                        label=f"archive_corrupt_{venue_symbol}_{month}",
                    )
        if status is ExecutionTerminalStatus.GUARD_EXCEEDED_FAIL_CLOSED:
            break

    decision_ms = window.start_ms
    cells: list[PanelCellV0] = []
    for instrument_id, venue_symbol, contract_type in admissible:
        cell = evaluate_panel_cell_v0(
            snapshot=snapshot,
            instrument_id=instrument_id,
            venue_symbol=venue_symbol,
            contract_type=contract_type,
            period_start=window.start_inclusive_utc,
            period_end=window.end_exclusive_utc,
            archive_results=archive_results,
            events_by_symbol=events_by_symbol,
            raw_ohlcv_dir=raw_ohlcv,
            decision_bar_time_ms=decision_ms,
        )
        cells.append(cell)

    aggregates = compute_aggregates_v0(
        all_requested=all_requested,
        admissible=admissible,
        cells=cells,
        archive_results=archive_results,
    )
    panel_outcome = classify_panel_outcome_v0(aggregates)

    completeness_dir = exec_root / "completeness"
    completeness_dir.mkdir(parents=True, exist_ok=True)
    (completeness_dir / "panel_matrix.jsonl").write_text(
        "\n".join(json.dumps(cell.__dict__, sort_keys=True) for cell in cells) + "\n",
        encoding="utf-8",
    )
    (completeness_dir / "aggregates.json").write_text(
        json.dumps(aggregates.__dict__, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (exec_root / "archive_results.jsonl").write_text(
        "\n".join(json.dumps(r.__dict__, sort_keys=True, default=str) for r in archive_results)
        + "\n",
        encoding="utf-8",
    )
    (exec_root / "request_records.jsonl").write_text(
        "\n".join(json.dumps(rec, sort_keys=True) for rec in request_records) + "\n",
        encoding="utf-8",
    )
    (exec_root / "PROMOTION_BLOCK.md").write_text(
        "DATASET_PROMOTED=false\nECONOMIC_EVALUATION_EXECUTED=false\nPROMOTION_EFFECT=NONE\n",
        encoding="utf-8",
    )

    from scripts.ops.primary_evidence_retention_v0 import (
        verify_manifest_sha256,
        write_manifest_sha256,
    )

    write_manifest_sha256(exec_root)
    manifest_ok, _ = verify_manifest_sha256(exec_root)
    manifest_verify_rc = 0 if manifest_ok else 1

    quarantine_after = measure_quarantine_inventory_v0(quarantine_root)

    return FullPanelFetchExecutionResultV0(
        status=status,
        fetch_spec=fetch_spec,
        aggregates=aggregates,
        panel_outcome=panel_outcome,
        cells=tuple(cells),
        archive_results=tuple(archive_results),
        quarantine_before=quarantine_before,
        quarantine_after=quarantine_after,
        quarantine_measurement_policy=measurement_policy,
        dataset_candidate_staged=exec_root.is_dir(),
        dataset_candidate_root=str(exec_root),
        full_panel_fetch_executed=True,
        panel_completeness_evaluated=True,
        dataset_promoted=False,
        economic_evaluation_executed=False,
        promotion_effect="NONE",
        runtime_effect="NONE",
        authority_effect="NONE",
        manifest_verify_rc=manifest_verify_rc,
        guard_fail_reason=guard_fail,
        request_records=tuple(request_records),
    )
