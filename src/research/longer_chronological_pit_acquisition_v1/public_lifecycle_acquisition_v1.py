"""Public OKX lifecycle enrichment and bounded long-panel acquisition v1.

Research-only. Public GET allowlist. No credentials, orders, or runtime authority.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import urlencode, urlparse

from src.research.longer_chronological_pit_acquisition_v1 import (
    DATASET_ID,
    ENV_ARCHIVE_ROOT,
    FREQUENCY,
    OKX_BAR_PARAM,
    TARGET_PERIOD_END,
    TARGET_PERIOD_START,
)
from src.research.longer_chronological_pit_acquisition_v1.archive_root import (
    ArchiveRootError,
    archive_layout,
    assert_path_under_archive,
    resolve_archive_root,
)
from src.research.longer_chronological_pit_acquisition_v1.history_depth_probe import (
    DEFAULT_MAX_RESPONSE_BYTES,
    DEFAULT_MAX_RETRIES,
    DEFAULT_PAGE_LIMIT,
    DEFAULT_TIMEOUT_SECONDS,
    RequestBudget,
    RequestBudgetExceeded,
    parse_history_candles_payload,
)
from src.research.longer_chronological_pit_acquisition_v1.sealed_lifecycle_v1 import (
    INCLUSION_POLICY_VERSION,
    MIN_HISTORY_DAYS_POLICY,
    PRODUCTION_LIFECYCLE_SOURCE_ID,
    SealedLifecycleError,
    build_sealed_record_from_registry_interval,
    load_production_registry_from_json_path,
    seal_lifecycle_manifest,
    verify_sealed_manifest,
)
from src.research.okx_production_instrument_lifecycle_source_v1 import (
    build_okx_lifecycle_source_snapshot_v1,
)

ALLOWED_HOST = "www.okx.com"
ALLOWED_PATHS = (
    "/api/v5/public/instruments",
    "/api/v5/market/history-candles",
)
HttpFetcher = Callable[[str], bytes]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ms(ts: str) -> int:
    return int(
        datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp()
        * 1000
    )


def _fmt_ms(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _assert_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != ALLOWED_HOST:
        raise SealedLifecycleError(f"URL_NOT_ALLOWED:{url}")
    if not any(parsed.path.startswith(p) for p in ALLOWED_PATHS):
        raise SealedLifecycleError(f"PATH_NOT_ALLOWED:{parsed.path}")
    q = (parsed.query or "").lower()
    for banned in ("apikey", "secret", "passphrase", "password", "token", "authorization"):
        if banned in q:
            raise SealedLifecycleError("SENSITIVE_QUERY_REFUSED")


def default_public_get(url: str, *, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> bytes:
    _assert_public_url(url)
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json",
            "User-Agent": "PeakTradeSealedLifecycleProbe/1.0 (+research; no-credentials)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            status = getattr(resp, "status", 200)
            if status in {401, 403}:
                raise SealedLifecycleError(f"AUTH_REQUIRED:HTTP_{status}")
            if status == 429:
                raise SealedLifecycleError("RATE_LIMIT_HTTP_429")
            if status >= 400:
                raise SealedLifecycleError(f"HTTP_{status}")
            return resp.read(DEFAULT_MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403}:
            raise SealedLifecycleError(f"AUTH_REQUIRED:HTTP_{exc.code}") from exc
        if exc.code == 429:
            raise SealedLifecycleError("RATE_LIMIT_HTTP_429") from exc
        raise SealedLifecycleError(f"HTTP_{exc.code}") from exc


class SealHttpClient:
    """Bounded public HTTP client allowing instruments + history-candles only."""

    def __init__(
        self,
        *,
        budget: RequestBudget,
        fetcher: HttpFetcher | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        sleep: Callable[[float], None] = time.sleep,
        min_interval_seconds: float = 0.25,
    ) -> None:
        self.budget = budget
        self.fetcher = fetcher
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.sleep = sleep
        self.min_interval_seconds = min_interval_seconds
        self._last = 0.0

    def get(self, url: str) -> bytes:
        _assert_public_url(url)
        self.budget.consume(1)
        last_err: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                now = time.monotonic()
                if self._last > 0 and now - self._last < self.min_interval_seconds:
                    self.sleep(self.min_interval_seconds - (now - self._last))
                self._last = time.monotonic()
                fetch = self.fetcher or (
                    lambda u: default_public_get(u, timeout_seconds=self.timeout_seconds)
                )
                body = fetch(url)
                if len(body) > DEFAULT_MAX_RESPONSE_BYTES:
                    raise SealedLifecycleError(
                        f"RESPONSE_TOO_LARGE:bytes={len(body)}:max={DEFAULT_MAX_RESPONSE_BYTES}"
                    )
                return body
            except RequestBudgetExceeded:
                raise
            except SealedLifecycleError:
                raise
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                if attempt >= self.max_retries:
                    break
                self.sleep(0.5 * (2**attempt))
        assert last_err is not None
        raise SealedLifecycleError(f"FETCH_FAILED:{last_err}") from last_err


def fetch_public_swap_instruments(
    client: SealHttpClient,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    url = f"https://www.okx.com/api/v5/public/instruments?{urlencode({'instType': 'SWAP'})}"
    body = client.get(url)
    payload = json.loads(body.decode("utf-8"))
    if str(payload.get("code")) != "0" or not isinstance(payload.get("data"), list):
        raise SealedLifecycleError(f"INSTRUMENTS_FETCH_FAILED:{payload.get('code')}")
    data = [dict(x) for x in payload["data"] if isinstance(x, dict)]
    fp = {
        "url_path": "/api/v5/public/instruments",
        "query": "instType=SWAP",
        "sha256": hashlib.sha256(body).hexdigest(),
        "byte_size": len(body),
        "row_count": len(data),
        "observed_at": _utc_now(),
    }
    return data, fp


def probe_public_candle_bounds(
    *,
    native_instrument_id: str,
    listing_timestamp: str,
    client: SealHttpClient,
    per_instrument_cap: int = 5,
    panel_start: str = TARGET_PERIOD_START,
) -> tuple[str | None, str | None, list[dict[str, Any]], dict[str, Any]]:
    """Return (first_public, last_public, request_log, stats)."""
    requests_log: list[dict[str, Any]] = []
    earliest_ms: int | None = None
    latest_ms: int | None = None
    used = 0
    rate_limits = 0
    failures = 0

    def _one(after_ms: int | None) -> dict[str, Any]:
        nonlocal used, earliest_ms, latest_ms, rate_limits, failures
        if used >= per_instrument_cap:
            raise SealedLifecycleError(f"PER_INSTRUMENT_CAP:{native_instrument_id}")
        params: dict[str, str] = {
            "instId": native_instrument_id,
            "bar": OKX_BAR_PARAM,
            "limit": str(DEFAULT_PAGE_LIMIT),
        }
        if after_ms is not None:
            params["after"] = str(after_ms)
        url = f"https://www.okx.com/api/v5/market/history-candles?{urlencode(params)}"
        try:
            body = client.get(url)
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            if "429" in msg:
                rate_limits += 1
            failures += 1
            raise
        used += 1
        parsed = parse_history_candles_payload(body)
        entry = {
            "url_path": "/api/v5/market/history-candles",
            "instId": native_instrument_id,
            "after_ms": after_ms,
            "row_count": parsed["row_count"],
            "earliest_ms": parsed["earliest_ms"],
            "latest_ms": parsed["latest_ms"],
            "sha256": hashlib.sha256(body).hexdigest(),
            "byte_size": len(body),
        }
        requests_log.append(entry)
        if parsed["earliest_ms"] is not None:
            earliest_ms = (
                parsed["earliest_ms"]
                if earliest_ms is None
                else min(earliest_ms, parsed["earliest_ms"])
            )
        if parsed["latest_ms"] is not None:
            latest_ms = (
                parsed["latest_ms"] if latest_ms is None else max(latest_ms, parsed["latest_ms"])
            )
        return parsed

    # 1) latest
    latest_page = _one(None)
    if latest_page["empty"]:
        return (
            None,
            None,
            requests_log,
            {
                "requests_used": used,
                "rate_limits": rate_limits,
                "failures": failures,
                "pagination_end_reached": True,
            },
        )

    # 2) around target panel start (required for long-history instruments)
    _one(_ms(panel_start))

    # 3) near listing
    listing_ms = _ms(listing_timestamp)
    _one(listing_ms + 3_600_000)

    # 4+) walk older from current earliest
    pagination_end = False
    while used < per_instrument_cap and earliest_ms is not None:
        page = _one(earliest_ms)
        if page["empty"] or page["earliest_ms"] is None:
            pagination_end = True
            break
        if page["earliest_ms"] >= earliest_ms:
            pagination_end = True
            break

    first = _fmt_ms(earliest_ms) if earliest_ms is not None else None
    last = _fmt_ms(latest_ms) if latest_ms is not None else None
    return (
        first,
        last,
        requests_log,
        {
            "requests_used": used,
            "rate_limits": rate_limits,
            "failures": failures,
            "pagination_end_reached": pagination_end,
        },
    )


def run_seal_lifecycle(
    *,
    production_registry_path: Path,
    archive_root: str | Path | None,
    allow_network: bool,
    allow_write: bool,
    request_budget: int,
    max_instruments: int | None = None,
    panel_start: str = TARGET_PERIOD_START,
    panel_end: str = TARGET_PERIOD_END,
    dataset_id: str = DATASET_ID,
    fetcher: HttpFetcher | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    if allow_network and request_budget <= 0:
        raise SealedLifecycleError("REQUEST_BUDGET_REQUIRED")
    if not allow_network:
        raise SealedLifecycleError("NETWORK_REQUIRED_FOR_SEAL_ENRICHMENT")
    if not str(dataset_id or "").strip():
        raise SealedLifecycleError("MISSING_DATASET_ID")

    registry = load_production_registry_from_json_path(production_registry_path)
    production_digest = str(registry.get("registry_snapshot_digest") or "")
    if not production_digest:
        raise SealedLifecycleError("PRODUCTION_REGISTRY_MISSING_DIGEST")

    intervals = list(registry.get("intervals") or [])
    intervals = sorted(
        intervals,
        key=lambda i: (
            str(i.get("venue_symbol") or ""),
            str(i.get("instrument_id") or ""),
        ),
    )
    if max_instruments is not None:
        intervals = intervals[: max(0, int(max_instruments))]

    root = None
    if allow_write:
        root = resolve_archive_root(explicit=archive_root, require_for_write=True)
        layout = archive_layout(root)
        for key in ("base", "manifests", "logs", "raw", "state"):
            layout[key].mkdir(parents=True, exist_ok=True)

    client = SealHttpClient(
        fetcher=fetcher,
        budget=RequestBudget(request_budget),
        sleep=sleep,
        min_interval_seconds=0.25,
    )

    # Public instruments discovery (validation / drift signal; not a second universe truth)
    instruments_raw, instruments_fp = fetch_public_swap_instruments(client)
    live_snapshot = build_okx_lifecycle_source_snapshot_v1(
        instruments_raw,
        retrieval_timestamp_utc=_utc_now(),
        source_snapshot_ref=f"okx_public_instruments_seal:{_utc_now()}",
    )
    live_native = {m.inst_id for m in live_snapshot.eligible_instruments}

    request_fingerprints: list[dict[str, Any]] = [instruments_fp]
    records = []
    observed_at = _utc_now()
    blockers: list[str] = []

    for idx, interval in enumerate(intervals):
        native = str(interval.get("venue_symbol") or "")
        listing = str(interval.get("listing_time") or interval.get("eligible_from") or "")
        if not native or not listing:
            blockers.append(f"MISSING_FIELDS:{interval.get('instrument_id')}")
            continue
        try:
            first, last, req_log, _stats = probe_public_candle_bounds(
                native_instrument_id=native,
                listing_timestamp=listing,
                client=client,
                panel_start=panel_start,
            )
            request_fingerprints.extend(req_log)
            rec = build_sealed_record_from_registry_interval(
                interval,
                first_public_candle_timestamp=first,
                last_public_candle_timestamp=last,
                lifecycle_observed_at=observed_at,
                panel_start=panel_start,
                panel_end=panel_end,
            )
            # Drift note: instrument absent from current live eligible set
            if native not in live_native and not rec.relist_or_replacement_flag:
                # still seal from production registry; mark exclusion if needed elsewhere
                pass
            records.append(rec)
            if (idx + 1) % 10 == 0 or (idx + 1) == len(intervals):
                print(
                    (
                        f"SEAL_PROGRESS instruments={idx + 1}/{len(intervals)} "
                        f"records={len(records)} requests_used={client.budget.used} "
                        f"blockers={len(blockers)}"
                    ),
                    file=sys.stderr,
                    flush=True,
                )
        except SealedLifecycleError as exc:
            blockers.append(f"{native}:{exc}")
            if "REQUEST_BUDGET" in str(exc) or "PER_INSTRUMENT_CAP" in str(exc):
                # continue other instruments only if budget remains; else stop
                if "REQUEST_BUDGET" in str(exc) or client.budget.used >= client.budget.max_requests:
                    blockers.append("REQUEST_BUDGET_EXHAUSTED_STOP")
                    break
            continue
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"{native}:FETCH_FAILED:{exc}")
            continue

    manifest = seal_lifecycle_manifest(
        records,
        production_registry_digest=production_digest,
        production_registry_path=str(production_registry_path),
        request_fingerprints=request_fingerprints,
        panel_start=panel_start,
        panel_end=panel_end,
        sealed_at=observed_at,
        dataset_id=dataset_id,
    )
    manifest["blockers"] = blockers
    manifest["requests_used"] = client.budget.used
    manifest["request_budget"] = request_budget
    manifest["live_eligible_instrument_count"] = len(live_snapshot.eligible_instruments)
    manifest["production_lifecycle_source_id"] = PRODUCTION_LIFECYCLE_SOURCE_ID
    manifest["inclusion_policy_version"] = INCLUSION_POLICY_VERSION
    verify_sealed_manifest(manifest)

    written = {}
    if allow_write and root is not None:
        layout = archive_layout(root)
        seal_dir = layout["manifests"] / "sealed_lifecycle_v1"
        seal_dir.mkdir(parents=True, exist_ok=True)
        mpath = assert_path_under_archive(seal_dir / "sealed_lifecycle_manifest.json", root)
        if mpath.exists():
            raise ArchiveRootError("IMMUTABLE_SEALED_MANIFEST_EXISTS_NO_OVERWRITE")
        payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        mpath.write_text(payload, encoding="utf-8")
        written["sealed_manifest"] = str(mpath)
        written["sealed_manifest_sha256"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        # compact summary
        summary = {
            "content_hash": manifest["content_hash"],
            "production_registry_digest": production_digest,
            "instrument_count_discovered": manifest["instrument_count_discovered"],
            "instrument_count_long_panel_included": manifest[
                "instrument_count_long_panel_included"
            ],
            "common_panel_start": manifest["common_panel_start"],
            "common_panel_end": manifest["common_panel_end"],
            "common_panel_duration_days": manifest["common_panel_duration_days"],
            "luna_decision": manifest["luna_decision"],
            "luna_decision_reason": manifest["luna_decision_reason"],
            "requests_used": client.budget.used,
            "blockers": blockers,
        }
        spath = assert_path_under_archive(layout["logs"] / "sealed_lifecycle_summary.json", root)
        if spath.exists():
            raise ArchiveRootError("IMMUTABLE_SEAL_SUMMARY_EXISTS_NO_OVERWRITE")
        spath.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written["summary"] = str(spath)

    manifest["written_artifacts"] = written
    manifest["archive_root"] = str(root) if root else None
    return manifest


def _audit_series(timestamps_ms: list[int]) -> dict[str, Any]:
    if not timestamps_ms:
        return {
            "gaps_found": 0,
            "duplicates_found": 0,
            "ordering_errors": 0,
            "bar_count": 0,
        }
    ordered = sorted(timestamps_ms)
    duplicates = len(timestamps_ms) - len(set(timestamps_ms))
    ordering_errors = 0
    # expect ascending unique hourly steps for panel slice
    gaps = 0
    expected_step = 3_600_000
    for a, b in zip(ordered, ordered[1:]):
        if b < a:
            ordering_errors += 1
        delta = b - a
        if delta == 0:
            continue
        if delta != expected_step:
            # count missing hours
            if delta > expected_step and delta % expected_step == 0:
                gaps += (delta // expected_step) - 1
            else:
                gaps += 1
    return {
        "gaps_found": gaps,
        "duplicates_found": duplicates,
        "ordering_errors": ordering_errors,
        "bar_count": len(set(timestamps_ms)),
        "first_ms": ordered[0],
        "last_ms": ordered[-1],
    }


def acquire_long_panel_ohlcv(
    *,
    sealed_manifest: Mapping[str, Any],
    archive_root: str | Path | None,
    allow_network: bool,
    allow_write: bool,
    request_budget: int,
    max_instruments: int | None = None,
    fetcher: HttpFetcher | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    verify_sealed_manifest(sealed_manifest)
    if not allow_network:
        raise SealedLifecycleError("NETWORK_REQUIRED_FOR_ACQUISITION")
    if request_budget <= 0:
        raise SealedLifecycleError("REQUEST_BUDGET_REQUIRED")

    common_start = sealed_manifest.get("common_panel_start")
    common_end = sealed_manifest.get("common_panel_end")
    duration = float(sealed_manifest.get("common_panel_duration_days") or 0.0)
    native_ids = list(sealed_manifest.get("long_panel_native_ids") or [])
    if max_instruments is not None:
        native_ids = native_ids[: max(0, int(max_instruments))]

    root = (
        resolve_archive_root(explicit=archive_root, require_for_write=True) if allow_write else None
    )
    if allow_write and root is not None:
        layout = archive_layout(root)
        for key in ("base", "raw", "normalized", "manifests", "logs"):
            layout[key].mkdir(parents=True, exist_ok=True)

    client = SealHttpClient(
        fetcher=fetcher,
        budget=RequestBudget(request_budget),
        sleep=sleep,
        min_interval_seconds=0.25,
    )

    if not common_start or not common_end or duration < float(MIN_HISTORY_DAYS_POLICY):
        return {
            "acquisition_executed": False,
            "reason": "COMMON_PANEL_BELOW_MIN_HISTORY_OR_MISSING",
            "common_panel_start": common_start,
            "common_panel_end": common_end,
            "common_panel_duration_days": duration,
            "instrument_count_acquired": 0,
            "full_series_gap_audit": False,
            "economic_reevaluation_ready": False,
        }

    start_ms = _ms(str(common_start))
    end_ms = _ms(str(common_end))
    instrument_reports: list[dict[str, Any]] = []
    total_bars = 0
    total_pages = 0
    gaps = 0
    dups = 0
    ordering = 0
    rate_limits = 0
    failures = 0
    retries_exhausted = 0

    for native in native_ids:
        ts_ms: list[int] = []
        pages = 0
        cursor = end_ms
        exhausted = False
        try:
            while cursor > start_ms:
                params = {
                    "instId": native,
                    "bar": OKX_BAR_PARAM,
                    "limit": str(DEFAULT_PAGE_LIMIT),
                    "after": str(cursor),
                }
                url = "https://www.okx.com/api/v5/market/history-candles?" + urlencode(params)
                try:
                    body = client.get(url)
                except Exception as exc:  # noqa: BLE001
                    if "429" in str(exc):
                        rate_limits += 1
                    if "FETCH_FAILED" in str(exc) or "REQUEST_BUDGET" in str(exc):
                        if "REQUEST_BUDGET" in str(exc):
                            retries_exhausted += 0
                        failures += 1
                        raise
                    failures += 1
                    raise
                pages += 1
                total_pages += 1
                if pages == 1 or pages % 25 == 0:
                    print(
                        (
                            f"ACQUIRE_PROGRESS instrument={native} "
                            f"pages={pages} total_pages={total_pages} "
                            f"requests_used={client.budget.used}"
                        ),
                        file=sys.stderr,
                        flush=True,
                    )
                parsed = parse_history_candles_payload(body)
                if parsed["empty"]:
                    exhausted = True
                    break
                page_ts = [t for t in parsed["timestamps_ms"] if start_ms <= t < end_ms]
                if not page_ts:
                    # page entirely outside / older than window
                    if parsed["latest_ms"] is not None and parsed["latest_ms"] < start_ms:
                        exhausted = True
                        break
                    if parsed["earliest_ms"] is not None:
                        cursor = parsed["earliest_ms"]
                        continue
                    exhausted = True
                    break
                ts_ms.extend(page_ts)
                if allow_write and root is not None:
                    raw_dir = archive_layout(root)["raw"] / "ohlcv_pt1h" / native
                    raw_dir.mkdir(parents=True, exist_ok=True)
                    digest = hashlib.sha256(body).hexdigest()
                    (raw_dir / f"page_{pages:05d}_{digest[:12]}.json").write_bytes(body)
                earliest = min(parsed["timestamps_ms"])
                if earliest >= cursor:
                    exhausted = True
                    break
                cursor = earliest
                if parsed["row_count"] < DEFAULT_PAGE_LIMIT:
                    exhausted = True
                    break
        except SealedLifecycleError as exc:
            instrument_reports.append(
                {
                    "native_instrument_id": native,
                    "status": "FAILED",
                    "error": str(exc),
                }
            )
            if "REQUEST_BUDGET" in str(exc):
                break
            continue
        except Exception as exc:  # noqa: BLE001
            instrument_reports.append(
                {
                    "native_instrument_id": native,
                    "status": "FAILED",
                    "error": str(exc),
                }
            )
            continue

        audit = _audit_series(ts_ms)
        gaps += int(audit["gaps_found"])
        dups += int(audit["duplicates_found"])
        ordering += int(audit["ordering_errors"])
        total_bars += int(audit["bar_count"])
        instrument_reports.append(
            {
                "native_instrument_id": native,
                "status": "ACQUIRED",
                "pages": pages,
                "pagination_exhausted": exhausted,
                **audit,
                "frequency": FREQUENCY,
            }
        )

    acquired = sum(1 for r in instrument_reports if r.get("status") == "ACQUIRED")
    full_audit = acquired == len(native_ids) and acquired > 0
    lifecycle_clipping_valid = all(
        (r.get("first_ms") is None or r.get("first_ms") >= start_ms - 3_600_000)
        for r in instrument_reports
        if r.get("status") == "ACQUIRED"
    )
    long_ids = set(native_ids)
    blockers = list(sealed_manifest.get("blockers") or [])
    long_panel_blockers = [b for b in blockers if any(str(i) in str(b) for i in long_ids)]
    ready = bool(
        sealed_manifest.get("sealed")
        and sealed_manifest.get("universe_truth") == "production_lifecycle_registry_binding_v1"
        and duration >= float(MIN_HISTORY_DAYS_POLICY)
        and full_audit
        and gaps == 0
        and dups == 0
        and ordering == 0
        and lifecycle_clipping_valid
        and acquired > 0
        and not long_panel_blockers
    )

    result = {
        "acquisition_executed": True,
        "schema_version": "longer_chronological_pit_bounded_long_panel_acquisition.v1",
        "sealed_content_hash": sealed_manifest.get("content_hash"),
        "common_panel_start": common_start,
        "common_panel_end": common_end,
        "common_panel_duration_days": duration,
        "instrument_count_requested": len(native_ids),
        "instrument_count_acquired": acquired,
        "total_bars": total_bars,
        "total_pages": total_pages,
        "full_series_gap_audit": full_audit,
        "gaps_found": gaps,
        "duplicates_found": dups,
        "ordering_errors": ordering,
        "lifecycle_clipping_valid": lifecycle_clipping_valid,
        "rate_limit_events": rate_limits,
        "request_failures": failures,
        "retries_exhausted": retries_exhausted,
        "requests_used": client.budget.used,
        "request_budget": request_budget,
        "instrument_reports": instrument_reports,
        "economic_gate_opened": False,
        "economic_reevaluation_ready": ready,
        "public_endpoints_only": True,
        "credentials_used": False,
        "orders": False,
    }

    if allow_write and root is not None:
        layout = archive_layout(root)
        apath = assert_path_under_archive(
            layout["logs"] / "bounded_long_panel_acquisition_summary.json", root
        )
        if apath.exists():
            raise ArchiveRootError("IMMUTABLE_ACQUISITION_SUMMARY_EXISTS_NO_OVERWRITE")
        payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
        apath.write_text(payload, encoding="utf-8")
        result["archive_manifest_hash"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        result["archive_path"] = str(root)
        result["written_summary"] = str(apath)
        # size
        size = sum(f.stat().st_size for f in Path(root).rglob("*") if f.is_file())
        result["archive_size_bytes"] = size

    return result


__all__ = [
    "acquire_long_panel_ohlcv",
    "fetch_public_swap_instruments",
    "probe_public_candle_bounds",
    "run_seal_lifecycle",
]
