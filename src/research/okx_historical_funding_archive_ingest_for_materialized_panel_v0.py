"""OKX Historical Funding Archive ingest for materialized extended_chronological_v1 panel v0.

Bounded ingest of OKX Historical Data Portal monthly funding archives for the 118
already materialized panel members and period 2024-05-01..2024-09-01. Reuses
canonical funding materialization and preflight owners. No live API fallback.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from src.research.bounded_offline_funding_fetch_for_materialized_panel_v0 import (
    DEFAULT_DURABLE_ARCHIVE_ROOT,
    DEFAULT_OUTPUT_STAGING_REL,
    FUNDING_BARS_REL,
    FUNDING_MANIFEST_REL,
    FundingCoverageReportV0,
    PanelMemberBindingV0,
    clear_stale_skip_fetch_funding_artifacts_v0,
    compute_funding_coverage_report_v0,
    funding_coverage_report_to_dict,
    load_panel_member_binding_v0,
    panel_member_binding_to_dict,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0 import (
    INFRASTRUCTURE_GO_TOKEN,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0 import (
    PANEL_DATASET_ID,
)
from src.research.csf_rdm_v0_dataset_funding_binding_materialization_preflight_v0 import (
    preflight_result_to_dict,
    run_dataset_funding_binding_materialization_preflight_v0,
)
from src.research.csf_rdm_v0_extended_chronological_v1_staging_funding_panel_materialization_v0 import (
    CANONICAL_FUNDING_OWNER,
    CANONICAL_PREFLIGHT_OWNER,
)
from src.research.offline_panel_materialization_from_partial_tmp_no_fetch_v0 import (
    REASON_FUNDING_SCOPE_DRIFT,
    load_offline_panel_materialization_config_v0,
)
from src.research.okx_historical_funding_archive_ingest_v0 import (
    SOURCE_ID,
    ArchiveAccessGuardV0,
    ArchiveIngestTerminalStatus,
    ArchiveRetrievalRecordV0,
    NormalizedFundingEventV0,
    archive_events_to_rest_compatible_rows_v0,
    build_archive_cdn_url_v0,
    compute_required_month_buckets_v0,
    filter_events_for_period_v0,
    parse_archive_zip_bytes_v0,
)
from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (
    load_panel_series_from_staging,
)

PACKAGE_MARKER = "OKX_HISTORICAL_FUNDING_ARCHIVE_INGEST_FOR_MATERIALIZED_PANEL_V0=true"
MATERIALIZATION_VERSION = "okx_historical_funding_archive_ingest_for_materialized_panel.v0"
CONFIRM_GO = "GO_BOUNDED_OKX_HISTORICAL_FUNDING_ARCHIVE_INGEST_V0"
CONFIG_REL_PATH = "config/ops/okx_historical_funding_archive_ingest_v0.json"
FUNDING_SOURCE = "OKX_HISTORICAL_FUNDING_ARCHIVE"
RAW_FUNDING_DIR_REL = Path("raw/funding_history")
RAW_ARCHIVE_SUBDIR = "raw_archive"

REASON_FETCH_GUARD_BLOCKED = "FETCH_GUARD_BLOCKED"
REASON_STAGING_MISSING = "STAGING_MISSING"
REASON_PANEL_MANIFEST_MISSING = "PANEL_MANIFEST_MISSING"
REASON_FULL_UNIVERSE_SCOPE = "FULL_UNIVERSE_SCOPE_FORBIDDEN"
REASON_OKX_PUBLIC_LIVE_API_FORBIDDEN = "OKX_PUBLIC_LIVE_API_FALLBACK_FORBIDDEN"

HttpFetcher = Callable[[str, float], tuple[int, bytes, dict[str, str]]]


class ArchiveIngestFailClosedReason(str, Enum):
    ARCHIVE_FORMAT_UNKNOWN = "FAIL_CLOSED_ARCHIVE_FORMAT_UNKNOWN"
    ARCHIVE_MONTH_MISSING = "FAIL_CLOSED_ARCHIVE_MONTH_MISSING"
    INSTRUMENT_MAPPING_UNRESOLVED = "FAIL_CLOSED_INSTRUMENT_MAPPING_UNRESOLVED"
    PERIOD_COVERAGE_INCOMPLETE = "FAIL_CLOSED_PERIOD_COVERAGE_INCOMPLETE"
    PANEL_FUNDING_BINDING_INVALID = "FAIL_CLOSED_PANEL_FUNDING_BINDING_INVALID"


class HistoricalArchiveIngestVerdict(str, Enum):
    ARCHIVE_INGESTED_PREFLIGHT_COMPLETE = "ARCHIVE_INGESTED_PREFLIGHT_COMPLETE"
    FAIL_CLOSED_STAGING = "FAIL_CLOSED_STAGING"
    FAIL_CLOSED_PANEL_BINDING = "FAIL_CLOSED_PANEL_BINDING"
    FAIL_CLOSED_ARCHIVE = "FAIL_CLOSED_ARCHIVE"
    FAIL_CLOSED_FETCH = "FAIL_CLOSED_FETCH"
    FAIL_CLOSED_PREFLIGHT = "FAIL_CLOSED_PREFLIGHT"


@dataclass(frozen=True)
class ArchiveFetchRecordV0:
    native_instrument_id: str
    month: str
    url: str
    http_status: int
    byte_count: int
    sha256: str
    parse_status: str
    event_count: int
    reason_code: str | None
    local_path: str | None


@dataclass(frozen=True)
class HistoricalArchiveIngestScopeResultV0:
    verdict: HistoricalArchiveIngestVerdict
    panel_binding: PanelMemberBindingV0 | None
    archive_source_binding: dict[str, Any] | None
    coverage_before: FundingCoverageReportV0 | None
    coverage_after: FundingCoverageReportV0 | None
    fetch_records: tuple[ArchiveFetchRecordV0, ...]
    normalization_report: dict[str, Any] | None
    materialization_result: dict[str, Any] | None
    preflight_before: dict[str, Any] | None
    preflight_after: dict[str, Any] | None
    ingest_run: bool
    network_fetch_run: bool
    full_universe_fetch_run: bool
    okx_public_live_api_used: bool
    economic_evaluation_run: bool
    reason_codes: tuple[str, ...]


def load_historical_archive_ingest_config_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH
    if not path.is_file():
        return {
            "schema_version": MATERIALIZATION_VERSION,
            "output_staging_rel": DEFAULT_OUTPUT_STAGING_REL,
            "panel_calendar_start_utc": "2024-05-01T00:00:00Z",
            "panel_calendar_end_utc": "2024-09-01T00:00:00Z",
            "panel_member_count_bound": 118,
            "bound_archive_months": ["2024-04", "2024-05", "2024-06", "2024-07", "2024-08"],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_http_fetcher(url: str, timeout_seconds: float) -> tuple[int, bytes, dict[str, str]]:
    request = urllib.request.Request(url, headers={"User-Agent": "PeakTradeArchivePanelIngest/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read()
            headers = {k.lower(): v for k, v in response.headers.items()}
            return response.status, body, headers
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), {k.lower(): v for k, v in exc.headers.items()}
    except urllib.error.URLError:
        return 0, b"", {}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def _probe_archive_path(probe_dir: Path | None, venue_symbol: str, month: str) -> Path | None:
    if probe_dir is None or not probe_dir.is_dir():
        return None
    base = venue_symbol.split("-")[0]
    candidates = [
        probe_dir / f"{base}-USDT_{venue_symbol}-fundingrates-{month}.zip",
        probe_dir / f"{venue_symbol}-fundingrates-{month}.zip",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def resolve_native_instrument_mapping_v0(
    native_instrument_id: str,
) -> tuple[str | None, str | None]:
    """Map panel native instrument ID to OKX archive venue symbol."""
    normalized = native_instrument_id.strip()
    if not normalized:
        return None, ArchiveIngestFailClosedReason.INSTRUMENT_MAPPING_UNRESOLVED.value
    if not normalized.endswith("-SWAP"):
        return None, ArchiveIngestFailClosedReason.INSTRUMENT_MAPPING_UNRESOLVED.value
    lowered = normalized.lower()
    if any(token in lowered for token in ("btc", "xbt", "bitcoin")):
        return None, ArchiveIngestFailClosedReason.INSTRUMENT_MAPPING_UNRESOLVED.value
    return normalized, None


def build_archive_source_binding_v0(config: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_id": str(config.get("archive_source_id", SOURCE_ID)),
        "cdn_base": str(
            config.get(
                "archive_cdn_base",
                "https://static.okx.com/cdn/okex/traderecords/swaprates/monthly",
            )
        ),
        "access_method": "HISTORICAL_DATA_PORTAL_ARCHIVE",
        "okx_public_live_api_used": False,
        "full_universe_fetch_run": False,
        "bound_archive_months": list(config.get("bound_archive_months", [])),
        "panel_calendar_start_utc": str(config.get("panel_calendar_start_utc", "")),
        "panel_calendar_end_utc": str(config.get("panel_calendar_end_utc", "")),
    }


def _verify_panel_binding_scope_v0(
    binding: PanelMemberBindingV0,
    staging_root: Path,
    *,
    max_panel_members: int,
) -> tuple[bool, tuple[str, ...]]:
    if binding.panel_member_count > max_panel_members:
        return False, (REASON_FULL_UNIVERSE_SCOPE,)
    panel_series, _ = load_panel_series_from_staging(staging_root)
    panel_ids = {series.instrument_id for series in panel_series}
    if set(binding.instrument_ids) != panel_ids:
        return False, (REASON_FUNDING_SCOPE_DRIFT,)
    if len(binding.instrument_ids) != binding.panel_member_count:
        return False, (ArchiveIngestFailClosedReason.PANEL_FUNDING_BINDING_INVALID.value,)
    return True, ()


def _build_access_guard_v0(
    config: Mapping[str, Any], panel_member_count: int
) -> ArchiveAccessGuardV0:
    return ArchiveAccessGuardV0(
        max_instruments=int(config.get("guard_max_instruments", panel_member_count)),
        max_months=int(config.get("guard_max_months_per_instrument", 5)),
        max_http_requests=int(config.get("guard_max_http_requests", 650)),
        max_total_bytes=int(config.get("guard_max_total_bytes", 524_288_000)),
        max_runtime_seconds=int(config.get("guard_max_runtime_seconds", 900)),
    )


def fetch_panel_archive_month_v0(
    *,
    venue_symbol: str,
    month: str,
    archive_dir: Path,
    guard: ArchiveAccessGuardV0,
    probe_dir: Path | None,
    fetcher: HttpFetcher,
    timeout_seconds: float = 30.0,
    min_interval_seconds: float = 0.12,
    last_fetch_monotonic: float = 0.0,
) -> tuple[bytes | None, ArchiveFetchRecordV0, float, str | None]:
    year_str, month_str = month.split("-")
    url = build_archive_cdn_url_v0(
        instrument_id=venue_symbol,
        year=int(year_str),
        month=int(month_str),
    )
    filename = f"{venue_symbol}-fundingrates-{month}.zip"
    target = archive_dir / filename
    retrieval_time = _utc_now_iso()

    probe_path = _probe_archive_path(probe_dir, venue_symbol, month)
    if probe_path is not None:
        body = probe_path.read_bytes()
        digest = _sha256_bytes(body)
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
            _write_sidecar(target, digest)
        record = ArchiveFetchRecordV0(
            native_instrument_id=venue_symbol,
            month=month,
            url=str(probe_path),
            http_status=200,
            byte_count=len(body),
            sha256=digest,
            parse_status="PENDING",
            event_count=0,
            reason_code="REUSED_PROBE",
            local_path=str(target),
        )
        return body, record, last_fetch_monotonic, None

    if target.is_file():
        body = target.read_bytes()
        digest = _sha256_bytes(body)
        sidecar = _read_sidecar_digest(target)
        if sidecar == digest:
            record = ArchiveFetchRecordV0(
                native_instrument_id=venue_symbol,
                month=month,
                url=url,
                http_status=200,
                byte_count=len(body),
                sha256=digest,
                parse_status="PENDING",
                event_count=0,
                reason_code="REUSED_CACHE",
                local_path=str(target),
            )
            return body, record, last_fetch_monotonic, None

    guard_reason = guard.check_request()
    if guard_reason:
        record = ArchiveFetchRecordV0(
            native_instrument_id=venue_symbol,
            month=month,
            url=url,
            http_status=0,
            byte_count=0,
            sha256="",
            parse_status="GUARD_BLOCKED",
            event_count=0,
            reason_code=guard_reason,
            local_path=None,
        )
        return None, record, last_fetch_monotonic, REASON_FETCH_GUARD_BLOCKED

    elapsed = time.monotonic() - last_fetch_monotonic
    if elapsed < min_interval_seconds:
        time.sleep(min_interval_seconds - elapsed)

    status, body, _headers = fetcher(url, timeout_seconds)
    last_fetch = time.monotonic()
    if status != 200 or not body:
        record = ArchiveFetchRecordV0(
            native_instrument_id=venue_symbol,
            month=month,
            url=url,
            http_status=status,
            byte_count=len(body),
            sha256=_sha256_bytes(body) if body else "",
            parse_status="HTTP_FAILED",
            event_count=0,
            reason_code=ArchiveIngestFailClosedReason.ARCHIVE_MONTH_MISSING.value,
            local_path=None,
        )
        return None, record, last_fetch, ArchiveIngestFailClosedReason.ARCHIVE_MONTH_MISSING.value

    guard.record_request(len(body))
    digest = _sha256_bytes(body)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    _write_sidecar(target, digest)
    record = ArchiveFetchRecordV0(
        native_instrument_id=venue_symbol,
        month=month,
        url=url,
        http_status=status,
        byte_count=len(body),
        sha256=digest,
        parse_status="PENDING",
        event_count=0,
        reason_code="FETCHED",
        local_path=str(target),
    )
    _ = retrieval_time
    return body, record, last_fetch, None


def ingest_archive_bytes_for_instrument_v0(
    zip_bytes: bytes,
    *,
    venue_symbol: str,
    period_start_utc: str,
    period_end_exclusive_utc: str,
    enforce_settlement_interval: bool = True,
) -> tuple[tuple[NormalizedFundingEventV0, ...], dict[str, Any], str | None]:
    parse_result = parse_archive_zip_bytes_v0(
        zip_bytes,
        expected_instrument_id=venue_symbol,
        enforce_settlement_interval=enforce_settlement_interval,
    )
    if parse_result.status is not ArchiveIngestTerminalStatus.COMPLETE:
        return (
            (),
            {"validation_errors": list(parse_result.validation_errors)},
            (ArchiveIngestFailClosedReason.ARCHIVE_FORMAT_UNKNOWN.value),
        )
    filtered, out_of_period = filter_events_for_period_v0(
        parse_result.events,
        period_start_utc=period_start_utc,
        period_end_exclusive_utc=period_end_exclusive_utc,
    )
    report = {
        "instrument_id": venue_symbol,
        "events_total": len(parse_result.events),
        "events_in_period": len(filtered),
        "out_of_period_rows": out_of_period,
        "duplicate_keys_removed": parse_result.duplicate_keys_removed,
        "validation_errors": [],
    }
    return filtered, report, None


def fetch_and_parse_panel_archives_v0(
    *,
    panel_binding: PanelMemberBindingV0,
    config: Mapping[str, Any],
    durable_evidence_root: Path,
    execute_fetch: bool,
    fetcher: HttpFetcher | None = None,
) -> tuple[
    dict[str, list[dict[str, Any]]],
    tuple[ArchiveFetchRecordV0, ...],
    dict[str, Any],
    tuple[str, ...],
]:
    bound_months = tuple(str(item) for item in config.get("bound_archive_months", []))
    if not bound_months:
        bound_months = compute_required_month_buckets_v0(
            period_start_utc=panel_binding.panel_calendar_start_utc,
            period_end_exclusive_utc=panel_binding.panel_calendar_end_utc,
        )

    cache_root = durable_evidence_root / str(
        config.get(
            "archive_cache_subdir", "datasets/staging/okx_historical_funding_archive_panel_v0"
        )
    )
    probe_rel = str(config.get("probe_archive_rel", "")).strip()
    probe_dir = durable_evidence_root / probe_rel if probe_rel else None
    guard = _build_access_guard_v0(config, panel_binding.panel_member_count)
    http_fetcher = fetcher or _default_http_fetcher

    funding_by_native: dict[str, list[dict[str, Any]]] = {}
    fetch_records: list[ArchiveFetchRecordV0] = []
    normalization_reports: dict[str, Any] = {}
    reason_codes: list[str] = []
    last_fetch_mono = 0.0

    panel_months = {
        m
        for m in bound_months
        if m >= panel_binding.panel_calendar_start_utc[:7]
        and m < panel_binding.panel_calendar_end_utc[:7]
    }

    if not execute_fetch:
        return funding_by_native, (), normalization_reports, tuple(reason_codes)

    for native_id in panel_binding.native_instrument_ids:
        venue_symbol, mapping_reason = resolve_native_instrument_mapping_v0(native_id)
        if venue_symbol is None:
            reason_codes.append(
                mapping_reason or ArchiveIngestFailClosedReason.INSTRUMENT_MAPPING_UNRESOLVED.value
            )
            continue

        inst_reason = guard.check_instruments()
        if inst_reason:
            reason_codes.append(REASON_FETCH_GUARD_BLOCKED)
            break
        guard.instruments_used += 1

        guard.months_used = 0
        archive_dir = cache_root / venue_symbol
        all_events: list[NormalizedFundingEventV0] = []
        inst_reports: list[dict[str, Any]] = []
        missing_panel_month = False

        for month in bound_months:
            month_reason = guard.check_months()
            if month_reason:
                reason_codes.append(REASON_FETCH_GUARD_BLOCKED)
                missing_panel_month = True
                break
            guard.months_used += 1

            zip_bytes, record, last_fetch_mono, fetch_fail = fetch_panel_archive_month_v0(
                venue_symbol=venue_symbol,
                month=month,
                archive_dir=archive_dir,
                guard=guard,
                probe_dir=probe_dir,
                fetcher=http_fetcher,
                last_fetch_monotonic=last_fetch_mono,
            )
            if fetch_fail == REASON_FETCH_GUARD_BLOCKED:
                fetch_records.append(record)
                reason_codes.append(REASON_FETCH_GUARD_BLOCKED)
                missing_panel_month = True
                break
            if zip_bytes is None:
                fetch_records.append(record)
                if (
                    fetch_fail == ArchiveIngestFailClosedReason.ARCHIVE_MONTH_MISSING.value
                    and month in panel_months
                ):
                    missing_panel_month = True
                    reason_codes.append(ArchiveIngestFailClosedReason.ARCHIVE_MONTH_MISSING.value)
                continue

            events, norm_report, parse_fail = ingest_archive_bytes_for_instrument_v0(
                zip_bytes,
                venue_symbol=venue_symbol,
                period_start_utc=panel_binding.panel_calendar_start_utc,
                period_end_exclusive_utc=panel_binding.panel_calendar_end_utc,
                enforce_settlement_interval=bool(config.get("enforce_settlement_interval", False)),
            )
            inst_reports.append({"month": month, **norm_report})
            updated_record = ArchiveFetchRecordV0(
                native_instrument_id=record.native_instrument_id,
                month=record.month,
                url=record.url,
                http_status=record.http_status,
                byte_count=record.byte_count,
                sha256=record.sha256,
                parse_status="COMPLETE" if parse_fail is None else "VALIDATION_FAILED",
                event_count=len(events),
                reason_code=parse_fail or record.reason_code,
                local_path=record.local_path,
            )
            fetch_records.append(updated_record)
            if parse_fail is not None:
                reason_codes.append(parse_fail)
                missing_panel_month = True
                continue
            all_events.extend(events)

        normalization_reports[venue_symbol] = {
            "native_instrument_id": native_id,
            "venue_symbol": venue_symbol,
            "months": inst_reports,
            "events_merged": len(all_events),
        }
        if missing_panel_month and not all_events:
            continue
        if not all_events:
            reason_codes.append(ArchiveIngestFailClosedReason.PERIOD_COVERAGE_INCOMPLETE.value)
            continue

        rest_rows = archive_events_to_rest_compatible_rows_v0(all_events)
        dedup: dict[int, dict[str, str]] = {}
        for row in rest_rows:
            dedup[int(row["fundingTime"])] = row
        funding_by_native[native_id] = [dedup[k] for k in sorted(dedup)]

    return (
        funding_by_native,
        tuple(fetch_records),
        normalization_reports,
        tuple(dict.fromkeys(reason_codes)),
    )


def run_historical_archive_ingest_scope_v0(
    *,
    repo_root: Path,
    durable_evidence_root: Path,
    staging_root: Path | None = None,
    binding_origin_main_sha: str | None = None,
    confirm_go: str = CONFIRM_GO,
    execute_fetch: bool = True,
    fetcher: HttpFetcher | None = None,
) -> HistoricalArchiveIngestScopeResultV0:
    if confirm_go != CONFIRM_GO:
        return HistoricalArchiveIngestScopeResultV0(
            verdict=HistoricalArchiveIngestVerdict.FAIL_CLOSED_FETCH,
            panel_binding=None,
            archive_source_binding=None,
            coverage_before=None,
            coverage_after=None,
            fetch_records=(),
            normalization_report=None,
            materialization_result=None,
            preflight_before=None,
            preflight_after=None,
            ingest_run=False,
            network_fetch_run=False,
            full_universe_fetch_run=False,
            okx_public_live_api_used=False,
            economic_evaluation_run=False,
            reason_codes=(REASON_FETCH_GUARD_BLOCKED,),
        )

    config = load_historical_archive_ingest_config_v0(repo_root)
    offline_config = load_offline_panel_materialization_config_v0(repo_root)
    output_root = staging_root or (
        durable_evidence_root / str(config.get("output_staging_rel", DEFAULT_OUTPUT_STAGING_REL))
    )
    max_panel_members = int(config.get("panel_member_count_bound", 118))
    archive_source_binding = build_archive_source_binding_v0(config)

    try:
        panel_binding = load_panel_member_binding_v0(output_root)
    except FileNotFoundError as exc:
        return HistoricalArchiveIngestScopeResultV0(
            verdict=HistoricalArchiveIngestVerdict.FAIL_CLOSED_STAGING,
            panel_binding=None,
            archive_source_binding=archive_source_binding,
            coverage_before=None,
            coverage_after=None,
            fetch_records=(),
            normalization_report=None,
            materialization_result=None,
            preflight_before=None,
            preflight_after=None,
            ingest_run=False,
            network_fetch_run=False,
            full_universe_fetch_run=False,
            okx_public_live_api_used=False,
            economic_evaluation_run=False,
            reason_codes=(str(exc),),
        )

    scope_ok, scope_reasons = _verify_panel_binding_scope_v0(
        panel_binding,
        output_root,
        max_panel_members=max_panel_members,
    )
    if not scope_ok:
        return HistoricalArchiveIngestScopeResultV0(
            verdict=HistoricalArchiveIngestVerdict.FAIL_CLOSED_PANEL_BINDING,
            panel_binding=panel_binding,
            archive_source_binding=archive_source_binding,
            coverage_before=compute_funding_coverage_report_v0(output_root),
            coverage_after=None,
            fetch_records=(),
            normalization_report=None,
            materialization_result=None,
            preflight_before=None,
            preflight_after=None,
            ingest_run=False,
            network_fetch_run=False,
            full_universe_fetch_run=False,
            okx_public_live_api_used=False,
            economic_evaluation_run=False,
            reason_codes=scope_reasons,
        )

    resolved_binding_sha = (
        binding_origin_main_sha
        or str(config.get("binding_origin_main_sha", "")).strip()
        or str(offline_config.get("binding_origin_main_sha", "")).strip()
    )

    preflight_before = preflight_result_to_dict(
        run_dataset_funding_binding_materialization_preflight_v0(
            repo_root=repo_root,
            staging_root=output_root,
            expected_origin_main_sha=resolved_binding_sha,
            binding_origin_main_sha=resolved_binding_sha,
        )
    )
    coverage_before = compute_funding_coverage_report_v0(output_root)

    funding_by_native: dict[str, list[dict[str, Any]]] = {}
    fetch_records: tuple[ArchiveFetchRecordV0, ...] = ()
    normalization_report: dict[str, Any] | None = None
    materialization_result: dict[str, Any] | None = None
    ingest_run = False
    network_fetch_run = False
    reason_codes: list[str] = []

    if execute_fetch:
        cleared, _ = clear_stale_skip_fetch_funding_artifacts_v0(output_root)
        _ = cleared
        ingest_run = True
        network_fetch_run = True
        (
            funding_by_native,
            fetch_records,
            normalization_report,
            fetch_reasons,
        ) = fetch_and_parse_panel_archives_v0(
            panel_binding=panel_binding,
            config=config,
            durable_evidence_root=durable_evidence_root,
            execute_fetch=True,
            fetcher=fetcher,
        )
        reason_codes.extend(fetch_reasons)

        if (
            ArchiveIngestFailClosedReason.ARCHIVE_FORMAT_UNKNOWN.value in reason_codes
            or ArchiveIngestFailClosedReason.ARCHIVE_MONTH_MISSING.value in reason_codes
            or ArchiveIngestFailClosedReason.INSTRUMENT_MAPPING_UNRESOLVED.value in reason_codes
            or REASON_FETCH_GUARD_BLOCKED in reason_codes
            or len(funding_by_native) != panel_binding.panel_member_count
        ):
            if len(funding_by_native) != panel_binding.panel_member_count:
                reason_codes.append(ArchiveIngestFailClosedReason.PERIOD_COVERAGE_INCOMPLETE.value)
            return HistoricalArchiveIngestScopeResultV0(
                verdict=HistoricalArchiveIngestVerdict.FAIL_CLOSED_ARCHIVE,
                panel_binding=panel_binding,
                archive_source_binding=archive_source_binding,
                coverage_before=coverage_before,
                coverage_after=compute_funding_coverage_report_v0(output_root),
                fetch_records=fetch_records,
                normalization_report=normalization_report,
                materialization_result=None,
                preflight_before=preflight_before,
                preflight_after=None,
                ingest_run=ingest_run,
                network_fetch_run=network_fetch_run,
                full_universe_fetch_run=False,
                okx_public_live_api_used=False,
                economic_evaluation_run=False,
                reason_codes=tuple(dict.fromkeys(reason_codes)),
            )

        if set(funding_by_native) != set(panel_binding.native_instrument_ids):
            missing = sorted(set(panel_binding.native_instrument_ids) - set(funding_by_native))
            reason_codes.append(ArchiveIngestFailClosedReason.PERIOD_COVERAGE_INCOMPLETE.value)
            if missing:
                normalization_report = normalization_report or {}
                normalization_report["missing_native_instrument_ids"] = missing

        from scripts.ops import (
            materialize_cross_sectional_funding_rate_carry_v0_bound_panel_funding_dataset_v0 as funding_mod,
        )

        funding_mod.CONFIRM_GO = INFRASTRUCTURE_GO_TOKEN
        raw_dir = output_root / RAW_FUNDING_DIR_REL
        raw_dir.mkdir(parents=True, exist_ok=True)
        for native_id, rows in funding_by_native.items():
            raw_path = raw_dir / f"archive_{native_id.replace('-', '_').lower()}.json"
            raw_path.write_text(
                json.dumps({"data": rows}, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

        materialization_result = funding_mod.materialize_bound_panel_funding_from_provided_rows_v0(
            confirm=INFRASTRUCTURE_GO_TOKEN,
            staging_root=output_root,
            funding_by_native=funding_by_native,
            funding_source=FUNDING_SOURCE,
        )

        if set(funding_by_native.keys()) != set(panel_binding.native_instrument_ids):
            reason_codes.append(ArchiveIngestFailClosedReason.PANEL_FUNDING_BINDING_INVALID.value)

    coverage_after = compute_funding_coverage_report_v0(output_root)
    preflight_after = preflight_result_to_dict(
        run_dataset_funding_binding_materialization_preflight_v0(
            repo_root=repo_root,
            staging_root=output_root,
            expected_origin_main_sha=resolved_binding_sha,
            binding_origin_main_sha=resolved_binding_sha,
        )
    )

    ready = bool(preflight_after.get("ready_for_next_pre_evaluation_gate"))
    if reason_codes:
        if any(
            code.startswith("FAIL_CLOSED_ARCHIVE") or code.startswith("FAIL_CLOSED_")
            for code in reason_codes
        ):
            verdict = HistoricalArchiveIngestVerdict.FAIL_CLOSED_ARCHIVE
        else:
            verdict = HistoricalArchiveIngestVerdict.FAIL_CLOSED_PREFLIGHT
    elif ready:
        verdict = HistoricalArchiveIngestVerdict.ARCHIVE_INGESTED_PREFLIGHT_COMPLETE
    else:
        verdict = HistoricalArchiveIngestVerdict.FAIL_CLOSED_PREFLIGHT
        raw_reasons = preflight_after.get("reason_codes")
        if isinstance(raw_reasons, list):
            reason_codes.extend(str(item) for item in raw_reasons)

    return HistoricalArchiveIngestScopeResultV0(
        verdict=verdict,
        panel_binding=panel_binding,
        archive_source_binding=archive_source_binding,
        coverage_before=coverage_before,
        coverage_after=coverage_after,
        fetch_records=fetch_records,
        normalization_report=normalization_report,
        materialization_result=materialization_result,
        preflight_before=preflight_before,
        preflight_after=preflight_after,
        ingest_run=ingest_run,
        network_fetch_run=network_fetch_run,
        full_universe_fetch_run=False,
        okx_public_live_api_used=False,
        economic_evaluation_run=False,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
    )


def archive_fetch_record_to_dict(record: ArchiveFetchRecordV0) -> dict[str, Any]:
    return {
        "native_instrument_id": record.native_instrument_id,
        "month": record.month,
        "url": record.url,
        "http_status": record.http_status,
        "byte_count": record.byte_count,
        "sha256": record.sha256,
        "parse_status": record.parse_status,
        "event_count": record.event_count,
        "reason_code": record.reason_code,
        "local_path": record.local_path,
    }


def historical_archive_ingest_scope_result_to_dict(
    result: HistoricalArchiveIngestScopeResultV0,
) -> dict[str, Any]:
    return {
        "schema_version": MATERIALIZATION_VERSION,
        "verdict": result.verdict.value,
        "confirm_go": CONFIRM_GO,
        "package_marker": PACKAGE_MARKER,
        "panel_binding": (
            panel_member_binding_to_dict(result.panel_binding)
            if result.panel_binding is not None
            else None
        ),
        "archive_source_binding": result.archive_source_binding,
        "coverage_before": (
            funding_coverage_report_to_dict(result.coverage_before)
            if result.coverage_before is not None
            else None
        ),
        "coverage_after": (
            funding_coverage_report_to_dict(result.coverage_after)
            if result.coverage_after is not None
            else None
        ),
        "fetch_record_count": len(result.fetch_records),
        "normalization_report": result.normalization_report,
        "materialization_result": result.materialization_result,
        "preflight_before_status": (
            result.preflight_before.get("status") if result.preflight_before else None
        ),
        "preflight_after_status": (
            result.preflight_after.get("status") if result.preflight_after else None
        ),
        "ready_for_next_pre_evaluation_gate": bool(
            result.preflight_after
            and result.preflight_after.get("ready_for_next_pre_evaluation_gate")
        ),
        "ingest_run": result.ingest_run,
        "network_fetch_run": result.network_fetch_run,
        "full_universe_fetch_run": result.full_universe_fetch_run,
        "okx_public_live_api_used": result.okx_public_live_api_used,
        "economic_evaluation_run": result.economic_evaluation_run,
        "reason_codes": list(result.reason_codes),
        "reuse_decisions": {
            "archive_ingest_owner": "src/research/okx_historical_funding_archive_ingest_v0.py",
            "funding_owner": CANONICAL_FUNDING_OWNER,
            "preflight_owner": CANONICAL_PREFLIGHT_OWNER,
            "panel_binding_owner": (
                "src/research/bounded_offline_funding_fetch_for_materialized_panel_v0.py"
            ),
        },
    }


__all__ = [
    "CONFIRM_GO",
    "CONFIG_REL_PATH",
    "DEFAULT_DURABLE_ARCHIVE_ROOT",
    "ArchiveIngestFailClosedReason",
    "ArchiveFetchRecordV0",
    "HistoricalArchiveIngestScopeResultV0",
    "HistoricalArchiveIngestVerdict",
    "archive_fetch_record_to_dict",
    "build_archive_source_binding_v0",
    "fetch_and_parse_panel_archives_v0",
    "historical_archive_ingest_scope_result_to_dict",
    "load_historical_archive_ingest_config_v0",
    "resolve_native_instrument_mapping_v0",
    "run_historical_archive_ingest_scope_v0",
]
