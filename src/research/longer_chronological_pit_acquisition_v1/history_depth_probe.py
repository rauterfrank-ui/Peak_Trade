"""Bounded public OKX history-depth probe for chronological PIT acquisition.

Defaults: network off, write off, no credentials.
Writes only under an external archive root when explicitly enabled.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import urlencode, urlparse

from src.research.longer_chronological_pit_acquisition_v1 import (
    DATASET_ID,
    ENV_ARCHIVE_ROOT,
    FREQUENCY,
    MARKET_TYPE,
    OKX_BAR_PARAM,
    SOURCE_ID_HISTORY_CANDLES,
    TARGET_PERIOD_END,
    TARGET_PERIOD_START,
    VENUE,
)
from src.research.longer_chronological_pit_acquisition_v1.archive_root import (
    ArchiveRootError,
    archive_layout,
    assert_path_under_archive,
    resolve_archive_root,
)
from src.research.longer_chronological_pit_acquisition_v1.manifest import (
    build_acquisition_manifest,
)
from src.research.longer_chronological_pit_acquisition_v1.partition_planner import (
    InstrumentLifecycleV1,
    PartitionPlanError,
    assert_instrument_admissible,
    plan_partitions_for_instrument,
)
from src.research.longer_chronological_pit_acquisition_v1.resume_state import (
    new_state_store,
    transition,
    write_state_atomic,
)
from src.research.longer_chronological_pit_acquisition_v1.source_discovery import (
    build_history_candle_locator,
)

PROBE_SCHEMA_VERSION = "longer_chronological_pit_okx_history_depth_probe.v1"
DEFAULT_REQUEST_BUDGET = 25
DEFAULT_MAX_INSTRUMENTS = 5
DEFAULT_TIMEOUT_SECONDS = 15.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_BACKOFF_SECONDS = 0.5
DEFAULT_PAGE_LIMIT = 100
DEFAULT_MAX_RESPONSE_BYTES = 512_000
DEFAULT_RAW_SAMPLE_BYTES = 2048
THREE_YEAR_MS = 3 * 365 * 24 * 3600 * 1000
ALLOWED_HOST = "www.okx.com"
ALLOWED_PATH_PREFIXES = ("/api/v5/market/history-candles",)

HttpFetcher = Callable[[str], bytes]


class HistoryDepthProbeError(RuntimeError):
    """Fail-closed probe error."""


class RequestBudgetExceeded(HistoryDepthProbeError):
    """Raised when the hard request budget would be exceeded."""


class SchemaDriftError(HistoryDepthProbeError):
    """Raised when OKX response schema drifts from the expected candle shape."""


class AuthRequiredError(HistoryDepthProbeError):
    """Raised when the endpoint demands authentication."""


class NetworkProbeDisabledError(HistoryDepthProbeError):
    """Raised when network is attempted without explicit probe freigabe."""


class WriteProbeDisabledError(HistoryDepthProbeError):
    """Raised when write is attempted without explicit probe freigabe."""


@dataclass
class RequestBudget:
    max_requests: int
    used: int = 0

    def consume(self, n: int = 1) -> None:
        if self.max_requests <= 0:
            raise RequestBudgetExceeded("REQUEST_BUDGET_MUST_BE_POSITIVE")
        if self.used + n > self.max_requests:
            raise RequestBudgetExceeded(
                f"REQUEST_BUDGET_EXCEEDED:used={self.used}:max={self.max_requests}"
            )
        self.used += n


@dataclass
class ProbeHttpClient:
    fetcher: HttpFetcher | None = None
    allow_network: bool = False
    budget: RequestBudget = field(default_factory=lambda: RequestBudget(DEFAULT_REQUEST_BUDGET))
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_retries: int = DEFAULT_MAX_RETRIES
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS
    max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES
    sleep: Callable[[float], None] = time.sleep
    min_interval_seconds: float = 0.2
    _last_request_monotonic: float = field(default=0.0, init=False, repr=False)

    def get(self, url: str) -> bytes:
        if not self.allow_network:
            raise NetworkProbeDisabledError("NETWORK_PROBE_DISABLED_DEFAULT")
        _assert_public_okx_url(url)
        self.budget.consume(1)
        if self.fetcher is not None:
            return self._get_with_retries(url, self.fetcher)
        return self._get_with_retries(url, _default_public_http_get)

    def _get_with_retries(self, url: str, fetcher: HttpFetcher) -> bytes:
        last_err: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                self._respect_rate_limit()
                body = fetcher(url)
                if len(body) > self.max_response_bytes:
                    raise HistoryDepthProbeError(
                        f"RESPONSE_TOO_LARGE:bytes={len(body)}:max={self.max_response_bytes}"
                    )
                return body
            except AuthRequiredError:
                raise
            except SchemaDriftError:
                raise
            except RequestBudgetExceeded:
                raise
            except Exception as exc:  # noqa: BLE001 — bounded retry boundary
                last_err = exc
                msg = str(exc).upper()
                if "401" in msg or "403" in msg or "AUTH" in msg:
                    raise AuthRequiredError(f"AUTH_REQUIRED:{exc}") from exc
                if attempt >= self.max_retries:
                    break
                self.sleep(self.backoff_seconds * (2**attempt))
        assert last_err is not None
        raise HistoryDepthProbeError(f"FETCH_FAILED:{last_err}") from last_err

    def _respect_rate_limit(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request_monotonic
        if self._last_request_monotonic > 0 and elapsed < self.min_interval_seconds:
            self.sleep(self.min_interval_seconds - elapsed)
        self._last_request_monotonic = time.monotonic()


def _default_public_http_get(
    url: str, *, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
) -> bytes:
    _assert_public_okx_url(url)
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json",
            "User-Agent": "PeakTradeHistoryDepthProbe/1.0 (+research; no-credentials)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            status = getattr(resp, "status", 200)
            if status in {401, 403}:
                raise AuthRequiredError(f"HTTP_{status}")
            if status == 429:
                raise HistoryDepthProbeError("RATE_LIMIT_HTTP_429")
            if status >= 400:
                raise HistoryDepthProbeError(f"HTTP_{status}")
            return resp.read(DEFAULT_MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403}:
            raise AuthRequiredError(f"HTTP_{exc.code}") from exc
        if exc.code == 429:
            raise HistoryDepthProbeError("RATE_LIMIT_HTTP_429") from exc
        raise HistoryDepthProbeError(f"HTTP_{exc.code}") from exc


def _assert_public_okx_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise HistoryDepthProbeError("NON_HTTPS_URL_REFUSED")
    if parsed.netloc != ALLOWED_HOST:
        raise HistoryDepthProbeError(f"HOST_NOT_ALLOWED:{parsed.netloc}")
    if not any(parsed.path.startswith(p) for p in ALLOWED_PATH_PREFIXES):
        raise HistoryDepthProbeError(f"PATH_NOT_ALLOWED:{parsed.path}")
    # Refuse credential leakage via query
    q = (parsed.query or "").lower()
    for banned in ("apikey", "secret", "passphrase", "password", "token", "authorization"):
        if banned in q:
            raise HistoryDepthProbeError("SENSITIVE_QUERY_REFUSED")


def _parse_utc(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def _fmt_ms(ms: int) -> str:
    # Guard absurd timestamps (schema / mock drift)
    if ms < 1_000_000_000_000 or ms > 4_000_000_000_000:
        raise SchemaDriftError(f"TIMESTAMP_OUT_OF_RANGE:{ms}")
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ms(ts: str) -> int:
    return int(_parse_utc(ts).timestamp() * 1000)


def coerce_instrument(raw: InstrumentLifecycleV1 | Mapping[str, Any]) -> InstrumentLifecycleV1:
    if isinstance(raw, InstrumentLifecycleV1):
        return raw
    return InstrumentLifecycleV1(
        instrument_id=str(raw["instrument_id"]),
        native_instrument_id=str(raw["native_instrument_id"]),
        base_asset=str(raw.get("base_asset") or ""),
        quote_asset=str(raw.get("quote_asset") or "USDT"),
        market_type=str(raw.get("market_type") or MARKET_TYPE),
        listing_time=raw.get("listing_time"),  # type: ignore[arg-type]
        delisting_time=raw.get("delisting_time"),  # type: ignore[arg-type]
        state=str(raw.get("state") or "KNOWN"),
    )


def default_probe_universe_sample() -> list[InstrumentLifecycleV1]:
    """Policy-compatible representative sample (not a second universe truth).

    Uses the scaffold InstrumentLifecycleV1 shape + BTC/spot exclusion gates.
    Listing times are deterministic probe inputs for clipping checks.
    """
    return [
        InstrumentLifecycleV1(
            instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
            native_instrument_id="ETH-USDT-SWAP",
            base_asset="ETH",
            quote_asset="USDT",
            market_type="linear_usdt_perpetual",
            listing_time="2019-12-01T00:00:00Z",
            delisting_time=None,
            state="KNOWN",
        ),
        InstrumentLifecycleV1(
            instrument_id="okx:linear_perpetual:LINK:USDT:USDT:perp",
            native_instrument_id="LINK-USDT-SWAP",
            base_asset="LINK",
            quote_asset="USDT",
            market_type="linear_usdt_perpetual",
            listing_time="2020-06-15T00:00:00Z",
            delisting_time=None,
            state="KNOWN",
        ),
        InstrumentLifecycleV1(
            instrument_id="okx:linear_perpetual:SOL:USDT:USDT:perp",
            native_instrument_id="SOL-USDT-SWAP",
            base_asset="SOL",
            quote_asset="USDT",
            market_type="linear_usdt_perpetual",
            listing_time="2021-06-01T00:00:00Z",
            delisting_time=None,
            state="KNOWN",
        ),
        InstrumentLifecycleV1(
            instrument_id="okx:linear_perpetual:APT:USDT:USDT:perp",
            native_instrument_id="APT-USDT-SWAP",
            base_asset="APT",
            quote_asset="USDT",
            market_type="linear_usdt_perpetual",
            listing_time="2022-10-19T00:00:00Z",
            delisting_time=None,
            state="KNOWN",
        ),
        InstrumentLifecycleV1(
            instrument_id="okx:linear_perpetual:TIA:USDT:USDT:perp",
            native_instrument_id="TIA-USDT-SWAP",
            base_asset="TIA",
            quote_asset="USDT",
            market_type="linear_usdt_perpetual",
            listing_time="2023-11-01T00:00:00Z",
            delisting_time=None,
            state="KNOWN",
        ),
        # Edge: short-lived (delisting) — only used if selected as edge case
        InstrumentLifecycleV1(
            instrument_id="okx:linear_perpetual:LUNA:USDT:USDT:perp",
            native_instrument_id="LUNA-USDT-SWAP",
            base_asset="LUNA",
            quote_asset="USDT",
            market_type="linear_usdt_perpetual",
            listing_time="2022-01-01T00:00:00Z",
            delisting_time="2022-05-13T00:00:00Z",
            state="KNOWN",
        ),
    ]


def select_probe_instruments(
    instruments: Sequence[InstrumentLifecycleV1 | Mapping[str, Any]],
    *,
    max_instruments: int = DEFAULT_MAX_INSTRUMENTS,
    seed: int = 0,
) -> dict[str, Any]:
    """Deterministically select up to max_instruments admissible instruments.

    Selection: oldest listing, middle listing, youngest listing, then up to two
    edge cases (delisted; listing near target period start). Stable tie-break by
    native_instrument_id. ``seed`` is recorded for reproducibility (sort is
    primary; seed only affects edge-case tie order via rotation).
    """
    if max_instruments < 1 or max_instruments > DEFAULT_MAX_INSTRUMENTS:
        raise HistoryDepthProbeError(f"MAX_INSTRUMENTS_OUT_OF_RANGE:1..{DEFAULT_MAX_INSTRUMENTS}")
    admissible: list[InstrumentLifecycleV1] = []
    excluded: list[dict[str, str]] = []
    for raw in instruments:
        inst = coerce_instrument(raw)
        try:
            assert_instrument_admissible(inst)
        except PartitionPlanError as exc:
            excluded.append({"instrument_id": inst.instrument_id, "reason": str(exc)})
            continue
        if not inst.listing_time:
            excluded.append({"instrument_id": inst.instrument_id, "reason": "MISSING_LISTING_TIME"})
            continue
        admissible.append(inst)

    if not admissible:
        raise HistoryDepthProbeError("NO_ADMISSIBLE_INSTRUMENTS_FOR_PROBE")

    ordered = sorted(
        admissible,
        key=lambda i: (_ms(i.listing_time or TARGET_PERIOD_END), i.native_instrument_id),
    )
    selected: list[InstrumentLifecycleV1] = []
    roles: dict[str, str] = {}

    def _add(inst: InstrumentLifecycleV1, role: str) -> None:
        if len(selected) >= max_instruments:
            return
        if any(s.native_instrument_id == inst.native_instrument_id for s in selected):
            return
        selected.append(inst)
        roles[inst.native_instrument_id] = role

    _add(ordered[0], "oldest")
    _add(ordered[len(ordered) // 2], "middle")
    _add(ordered[-1], "youngest")

    # Edge cases
    delisted = [i for i in ordered if i.delisting_time]
    if delisted:
        # rotate by seed for stable but seed-aware pick among edges
        idx = abs(int(seed)) % len(delisted)
        _add(delisted[idx], "edge_delisted")

    target_ms = _ms(TARGET_PERIOD_START)
    near_boundary = sorted(
        ordered,
        key=lambda i: abs(_ms(i.listing_time or TARGET_PERIOD_END) - target_ms),
    )
    if near_boundary:
        _add(near_boundary[0], "edge_near_period_start")

    # Fill remaining slots deterministically from ordered list
    for inst in ordered:
        if len(selected) >= max_instruments:
            break
        _add(inst, "fill")

    selected_sorted = sorted(
        selected,
        key=lambda i: (_ms(i.listing_time or TARGET_PERIOD_END), i.native_instrument_id),
    )
    return {
        "selection_seed": int(seed),
        "max_instruments": max_instruments,
        "candidate_count": len(admissible),
        "excluded": excluded,
        "roles": {
            i.native_instrument_id: roles.get(i.native_instrument_id, "fill")
            for i in selected_sorted
        },
        "instruments": selected_sorted,
        "native_ids": [i.native_instrument_id for i in selected_sorted],
        "btc_excluded": True,
        "spot_excluded": True,
        "universe_truth": "scaffold_lifecycle_policy_sample_not_production_manifest",
    }


def parse_history_candles_payload(body: bytes) -> dict[str, Any]:
    """Parse and validate OKX history-candles JSON; fail-closed on schema drift."""
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SchemaDriftError(f"INVALID_JSON:{exc}") from exc
    if not isinstance(payload, dict):
        raise SchemaDriftError("PAYLOAD_NOT_OBJECT")
    code = str(payload.get("code", ""))
    if code in {"50111", "50113", "50114"} or "api key" in str(payload.get("msg", "")).lower():
        raise AuthRequiredError(f"AUTH_HINT_IN_PAYLOAD:code={code}")
    if code != "0":
        raise HistoryDepthProbeError(f"OKX_ERROR_CODE:{code}:{payload.get('msg')}")
    data = payload.get("data")
    if data is None:
        raise SchemaDriftError("MISSING_DATA_FIELD")
    if not isinstance(data, list):
        raise SchemaDriftError("DATA_NOT_LIST")
    timestamps: list[int] = []
    for idx, row in enumerate(data):
        if not isinstance(row, list) or len(row) < 5:
            raise SchemaDriftError(f"ROW_SHAPE_INVALID:index={idx}")
        try:
            ts = int(str(row[0]))
        except (TypeError, ValueError) as exc:
            raise SchemaDriftError(f"TS_NOT_INT:index={idx}") from exc
        # basic OHLC presence
        for j in range(1, 5):
            try:
                float(str(row[j]))
            except (TypeError, ValueError) as exc:
                raise SchemaDriftError(f"OHLC_NOT_NUMERIC:index={idx}:col={j}") from exc
        timestamps.append(ts)
    return {
        "code": code,
        "row_count": len(data),
        "timestamps_ms": timestamps,
        "earliest_ms": min(timestamps) if timestamps else None,
        "latest_ms": max(timestamps) if timestamps else None,
        "empty": len(timestamps) == 0,
    }


def _body_meta(body: bytes) -> dict[str, Any]:
    digest = hashlib.sha256(body).hexdigest()
    sample = body[:DEFAULT_RAW_SAMPLE_BYTES]
    return {
        "sha256": digest,
        "byte_size": len(body),
        "sample_b64_prefix_sha256": hashlib.sha256(sample).hexdigest(),
        "sample_bytes_kept": len(sample),
    }


def evaluate_three_year_depth(
    *,
    earliest_ms: int | None,
    listing_ms: int | None,
    target_start_ms: int,
    pagination_exhausted: bool,
) -> str:
    if earliest_ms is None:
        return "INCONCLUSIVE"
    effective_need = target_start_ms
    if listing_ms is not None and listing_ms > target_start_ms:
        effective_need = listing_ms
    if earliest_ms <= effective_need:
        return "YES"
    if pagination_exhausted:
        return "NO"
    return "INCONCLUSIVE"


def evaluate_lifecycle_clipping(
    *,
    earliest_ms: int | None,
    listing_ms: int | None,
    delisting_ms: int | None,
    latest_ms: int | None,
    planned_start: str | None,
    planned_end: str | None,
) -> dict[str, Any]:
    """Check public history does not precede listing and respects planned clip window."""
    reasons: list[str] = []
    valid = True
    if earliest_ms is None or listing_ms is None or planned_start is None:
        return {
            "valid": False,
            "reasons": ["INSUFFICIENT_DATA"],
            "planned_start": planned_start,
            "planned_end": planned_end,
        }
    planned_start_ms = _ms(planned_start)
    # Public earliest should not be materially before listing (allow 1h bar skew)
    if earliest_ms + 3600_000 < listing_ms:
        valid = False
        reasons.append("PUBLIC_HISTORY_BEFORE_LISTING")
    # Planned start should be >= listing (planner clipping)
    if planned_start_ms + 1000 < listing_ms:
        valid = False
        reasons.append("PLANNED_START_BEFORE_LISTING")
    if delisting_ms is not None and planned_end is not None:
        planned_end_ms = _ms(planned_end)
        if planned_end_ms > delisting_ms + 1000:
            valid = False
            reasons.append("PLANNED_END_AFTER_DELISTING")
        if latest_ms is not None and latest_ms > delisting_ms + 3600_000:
            # soft signal only — public may still serve after delist briefly
            reasons.append("PUBLIC_LATEST_AFTER_DELISTING_OBSERVED")
    if not reasons:
        reasons.append("CLIPPING_CONSISTENT")
    return {
        "valid": valid,
        "reasons": reasons,
        "planned_start": planned_start,
        "planned_end": planned_end,
        "listing_ms": listing_ms,
        "delisting_ms": delisting_ms,
        "earliest_public_ms": earliest_ms,
        "latest_public_ms": latest_ms,
    }


def probe_instrument_history_depth(
    inst: InstrumentLifecycleV1,
    *,
    client: ProbeHttpClient,
    period_start: str = TARGET_PERIOD_START,
    period_end: str = TARGET_PERIOD_END,
    per_instrument_request_cap: int = 5,
) -> dict[str, Any]:
    assert_instrument_admissible(inst)
    partitions = plan_partitions_for_instrument(
        inst, period_start=period_start, period_end=period_end
    )
    planned_start = partitions[0]["period_start"] if partitions else None
    planned_end = partitions[-1]["period_end"] if partitions else None
    listing_ms = _ms(inst.listing_time) if inst.listing_time else None
    delisting_ms = _ms(inst.delisting_time) if inst.delisting_time else None
    target_start_ms = _ms(period_start)
    target_end_ms = _ms(period_end)

    requests_log: list[dict[str, Any]] = []
    earliest_ms: int | None = None
    latest_ms: int | None = None
    pagination_exhausted = False
    local_used = 0

    def _fetch(after_ms: int | None) -> dict[str, Any]:
        nonlocal local_used, earliest_ms, latest_ms
        if local_used >= per_instrument_request_cap:
            raise RequestBudgetExceeded(
                f"PER_INSTRUMENT_CAP:{inst.native_instrument_id}:{per_instrument_request_cap}"
            )
        if after_ms is None:
            # most recent page — build locator with after=now for determinism of URL shape
            after_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
            # For latest, OKX without after is preferred; use after far future via end
            locator = (
                f"https://www.okx.com/api/v5/market/history-candles"
                f"?{urlencode({'instId': inst.native_instrument_id, 'bar': OKX_BAR_PARAM, 'limit': str(DEFAULT_PAGE_LIMIT)})}"
            )
        else:
            locator = build_history_candle_locator(
                native_instrument_id=inst.native_instrument_id,
                after_ms=after_ms,
                limit=DEFAULT_PAGE_LIMIT,
            )
        body = client.get(locator)
        local_used += 1
        parsed = parse_history_candles_payload(body)
        meta = _body_meta(body)
        entry = {
            "url_path": urlparse(locator).path,
            "query_instId": inst.native_instrument_id,
            "after_ms": after_ms,
            "row_count": parsed["row_count"],
            "earliest_ms": parsed["earliest_ms"],
            "latest_ms": parsed["latest_ms"],
            "response_meta": meta,
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

    # 1) Latest page
    latest_page = _fetch(None)
    if latest_page["empty"]:
        return {
            "native_instrument_id": inst.native_instrument_id,
            "instrument_id": inst.instrument_id,
            "status": "NO_DATA",
            "earliest_public_ts": None,
            "latest_public_ts": None,
            "three_year_depth": "INCONCLUSIVE",
            "lifecycle_clipping": evaluate_lifecycle_clipping(
                earliest_ms=None,
                listing_ms=listing_ms,
                delisting_ms=delisting_ms,
                latest_ms=None,
                planned_start=planned_start,
                planned_end=planned_end,
            ),
            "pagination_end_reached": True,
            "requests": requests_log,
            "source_id": SOURCE_ID_HISTORY_CANDLES,
        }

    # 2) Probe around target period start (3y window start)
    _fetch(target_start_ms)

    # 3) Probe near listing (lifecycle)
    if listing_ms is not None:
        _fetch(listing_ms + 3_600_000)

    # 4) Walk older from current earliest until empty or cap
    while local_used < per_instrument_request_cap and earliest_ms is not None:
        page = _fetch(earliest_ms)
        if page["empty"] or page["earliest_ms"] is None:
            pagination_exhausted = True
            break
        if page["earliest_ms"] >= earliest_ms:
            # cursor did not advance older — treat as end
            pagination_exhausted = True
            break

    three = evaluate_three_year_depth(
        earliest_ms=earliest_ms,
        listing_ms=listing_ms,
        target_start_ms=target_start_ms,
        pagination_exhausted=pagination_exhausted,
    )
    clipping = evaluate_lifecycle_clipping(
        earliest_ms=earliest_ms,
        listing_ms=listing_ms,
        delisting_ms=delisting_ms,
        latest_ms=latest_ms,
        planned_start=planned_start,
        planned_end=planned_end,
    )
    return {
        "native_instrument_id": inst.native_instrument_id,
        "instrument_id": inst.instrument_id,
        "base_asset": inst.base_asset,
        "listing_time": inst.listing_time,
        "delisting_time": inst.delisting_time,
        "status": "PROBED",
        "earliest_public_ts": _fmt_ms(earliest_ms) if earliest_ms is not None else None,
        "latest_public_ts": _fmt_ms(latest_ms) if latest_ms is not None else None,
        "earliest_public_ms": earliest_ms,
        "latest_public_ms": latest_ms,
        "target_period_start": period_start,
        "target_period_end": period_end,
        "target_start_ms": target_start_ms,
        "target_end_ms": target_end_ms,
        "three_year_depth": three,
        "lifecycle_clipping": clipping,
        "pagination_end_reached": pagination_exhausted,
        "partition_count_planned": len(partitions),
        "requests": requests_log,
        "requests_used": local_used,
        "source_id": SOURCE_ID_HISTORY_CANDLES,
        "endpoint": "https://www.okx.com/api/v5/market/history-candles",
        "bar": OKX_BAR_PARAM,
        "frequency": FREQUENCY,
    }


def run_history_depth_probe(
    instruments: Sequence[InstrumentLifecycleV1 | Mapping[str, Any]] | None = None,
    *,
    allow_network_probe: bool = False,
    allow_write_probe: bool = False,
    request_budget: int | None = None,
    archive_root: str | Path | None = None,
    max_instruments: int = DEFAULT_MAX_INSTRUMENTS,
    selection_seed: int = 0,
    period_start: str = TARGET_PERIOD_START,
    period_end: str = TARGET_PERIOD_END,
    fetcher: HttpFetcher | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    env: dict[str, str] | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Run bounded history-depth probe. Network/write require explicit freigabe."""
    if allow_network_probe and request_budget is None:
        raise HistoryDepthProbeError("REQUEST_BUDGET_REQUIRED_WHEN_NETWORK_ENABLED")
    if allow_write_probe and not allow_network_probe:
        # write of dry metadata without network is allowed only with root — still require root
        pass

    universe = list(instruments) if instruments is not None else default_probe_universe_sample()
    selection = select_probe_instruments(
        universe, max_instruments=max_instruments, seed=selection_seed
    )
    selected: list[InstrumentLifecycleV1] = selection["instruments"]

    # Hard BTC/spot assertions on selected set
    for inst in selected:
        assert_instrument_admissible(inst)
        if "BTC" in inst.native_instrument_id.upper() or inst.base_asset.upper() in {
            "BTC",
            "XBT",
            "WBTC",
        }:
            raise HistoryDepthProbeError(f"BTC_LEAK:{inst.native_instrument_id}")
        if inst.market_type.lower() == "spot" or (
            inst.native_instrument_id.upper().endswith("-USDT")
            and "SWAP" not in inst.native_instrument_id.upper()
        ):
            raise HistoryDepthProbeError(f"SPOT_LEAK:{inst.native_instrument_id}")

    budget_max = int(request_budget) if request_budget is not None else DEFAULT_REQUEST_BUDGET
    if allow_network_probe and budget_max > DEFAULT_REQUEST_BUDGET:
        raise HistoryDepthProbeError(
            f"REQUEST_BUDGET_ABOVE_HARD_CAP:{budget_max}>{DEFAULT_REQUEST_BUDGET}"
        )

    root: Path | None = None
    if allow_write_probe:
        root = resolve_archive_root(explicit=archive_root, env=env, require_for_write=True)
    elif archive_root is not None or (env or {}).get(ENV_ARCHIVE_ROOT):
        root = resolve_archive_root(explicit=archive_root, env=env, require_for_write=False)

    client = ProbeHttpClient(
        fetcher=fetcher,
        allow_network=bool(allow_network_probe),
        budget=RequestBudget(budget_max if allow_network_probe else 0),
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
        sleep=sleep,
    )

    instrument_results: list[dict[str, Any]] = []
    blockers: list[str] = []
    network_executed = False

    if not allow_network_probe:
        # Dry-run planning only
        for inst in selected:
            parts = plan_partitions_for_instrument(
                inst, period_start=period_start, period_end=period_end
            )
            instrument_results.append(
                {
                    "native_instrument_id": inst.native_instrument_id,
                    "instrument_id": inst.instrument_id,
                    "status": "DRY_RUN_NO_NETWORK",
                    "earliest_public_ts": None,
                    "latest_public_ts": None,
                    "three_year_depth": "INCONCLUSIVE",
                    "lifecycle_clipping": {
                        "valid": True,
                        "reasons": ["PLANNER_CLIP_ONLY_NETWORK_DISABLED"],
                        "planned_start": parts[0]["period_start"] if parts else None,
                        "planned_end": parts[-1]["period_end"] if parts else None,
                    },
                    "pagination_end_reached": False,
                    "partition_count_planned": len(parts),
                    "requests": [],
                    "requests_used": 0,
                }
            )
    else:
        network_executed = True
        for inst in selected:
            try:
                instrument_results.append(
                    probe_instrument_history_depth(
                        inst,
                        client=client,
                        period_start=period_start,
                        period_end=period_end,
                    )
                )
            except RequestBudgetExceeded as exc:
                blockers.append(str(exc))
                instrument_results.append(
                    {
                        "native_instrument_id": inst.native_instrument_id,
                        "status": "BUDGET_EXCEEDED",
                        "three_year_depth": "INCONCLUSIVE",
                        "error": str(exc),
                    }
                )
                break
            except (SchemaDriftError, AuthRequiredError) as exc:
                blockers.append(str(exc))
                instrument_results.append(
                    {
                        "native_instrument_id": inst.native_instrument_id,
                        "status": "FAILED",
                        "three_year_depth": "INCONCLUSIVE",
                        "error": str(exc),
                    }
                )
                break
            except HistoryDepthProbeError as exc:
                # Per-instrument OKX/business errors — record and continue within budget
                instrument_results.append(
                    {
                        "native_instrument_id": inst.native_instrument_id,
                        "status": "FAILED",
                        "three_year_depth": "INCONCLUSIVE",
                        "error": str(exc),
                    }
                )
                blockers.append(f"{inst.native_instrument_id}:{exc}")

    clipping_valid = all(
        bool((r.get("lifecycle_clipping") or {}).get("valid", False))
        for r in instrument_results
        if r.get("status") in {"PROBED", "DRY_RUN_NO_NETWORK"}
    )

    # Manifest + resume state (small) when write enabled
    written: dict[str, Any] = {}
    external_artifact_hashes: dict[str, str] = {}
    if allow_write_probe:
        if root is None:
            raise WriteProbeDisabledError("WRITE_REQUIRES_EXTERNAL_ARCHIVE_ROOT")
        layout = archive_layout(root)
        for key in ("base", "manifests", "state", "logs", "raw"):
            layout[key].mkdir(parents=True, exist_ok=True)

        # Tiny probe partitions (at most one per instrument) for manifest/resume demo
        tiny_parts: list[dict[str, Any]] = []
        for inst in selected:
            parts = plan_partitions_for_instrument(
                inst, period_start=period_start, period_end=period_end
            )
            if parts:
                tiny_parts.append(parts[0])
        manifest = build_acquisition_manifest(tiny_parts, created_at="1970-01-01T00:00:00Z")
        # Use probe-specific manifest name to avoid colliding with full acquisition
        probe_manifest_name = "history_depth_probe_manifest.json"
        mpath = assert_path_under_archive(layout["manifests"] / probe_manifest_name, root)
        if mpath.exists():
            raise ArchiveRootError("IMMUTABLE_PROBE_MANIFEST_EXISTS_NO_OVERWRITE")
        mpath.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written["manifest"] = str(mpath)
        external_artifact_hashes[probe_manifest_name] = hashlib.sha256(
            mpath.read_bytes()
        ).hexdigest()

        store = new_state_store()
        for part in tiny_parts:
            transition(store, part["partition_id"], "DISCOVERED")
        spath = write_state_atomic(store, archive_root=root)
        written["resume_state"] = str(spath)
        external_artifact_hashes["resume_state.json"] = hashlib.sha256(
            spath.read_bytes()
        ).hexdigest()

        summary_path = assert_path_under_archive(
            layout["logs"] / "history_depth_probe_summary.json", root
        )
        # filled below after summary built — placeholder path reserved
        written["summary"] = str(summary_path)

    earliest_map = {
        r["native_instrument_id"]: r.get("earliest_public_ts")
        for r in instrument_results
        if "native_instrument_id" in r
    }
    three_map = {
        r["native_instrument_id"]: r.get("three_year_depth")
        for r in instrument_results
        if "native_instrument_id" in r
    }
    latest_map = {
        r["native_instrument_id"]: r.get("latest_public_ts")
        for r in instrument_results
        if "native_instrument_id" in r
    }

    summary: dict[str, Any] = {
        "schema_version": PROBE_SCHEMA_VERSION,
        "dataset_id": DATASET_ID,
        "venue": VENUE,
        "market_type": MARKET_TYPE,
        "frequency": FREQUENCY,
        "source_id": SOURCE_ID_HISTORY_CANDLES,
        "endpoint": "https://www.okx.com/api/v5/market/history-candles",
        "public_endpoints_only": True,
        "credentials_used": False,
        "network_probe_executed": network_executed,
        "allow_network_probe": bool(allow_network_probe),
        "allow_write_probe": bool(allow_write_probe),
        "mass_download_started": False,
        "request_budget": budget_max if allow_network_probe else 0,
        "requests_used": client.budget.used if allow_network_probe else 0,
        "timeout_seconds": timeout_seconds,
        "max_retries": max_retries,
        "backoff_seconds": backoff_seconds,
        "selection": {
            "seed": selection["selection_seed"],
            "roles": selection["roles"],
            "native_ids": selection["native_ids"],
            "candidate_count": selection["candidate_count"],
            "universe_truth": selection["universe_truth"],
            "excluded_count": len(selection["excluded"]),
        },
        "instruments_probed": selection["native_ids"],
        "btc_excluded": True,
        "spot_excluded": True,
        "earliest_history_by_instrument": earliest_map,
        "latest_history_by_instrument": latest_map,
        "three_year_depth_by_instrument": three_map,
        "lifecycle_clipping_valid": clipping_valid,
        "instrument_results": instrument_results,
        "written_artifacts": written,
        "external_artifact_hashes": external_artifact_hashes,
        "archive_root": str(root) if root is not None else None,
        "economic_gate_opened": False,
        "promotion_eligible": False,
        "live_authorized": False,
        "orders": False,
        "shadow": False,
        "paper": False,
        "testnet": False,
        "blockers": blockers,
        "limitations": [
            "Probe measures public history-candles depth only; not a mass download.",
            "Default instrument list is a policy-compatible scaffold sample, not a "
            "second production universe manifest.",
            "Three-year depth YES requires earliest public ts at/before effective need "
            "(target start or listing if later).",
            "INCONCLUSIVE when pagination end not reached within request budget.",
        ],
    }

    if allow_write_probe and root is not None:
        summary_path = Path(written["summary"])
        if summary_path.exists():
            raise ArchiveRootError("IMMUTABLE_PROBE_SUMMARY_EXISTS_NO_OVERWRITE")
        payload = json.dumps(summary, indent=2, sort_keys=True) + "\n"
        summary_path.write_text(payload, encoding="utf-8")
        external_artifact_hashes["history_depth_probe_summary.json"] = hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()
        summary["external_artifact_hashes"] = external_artifact_hashes

    return summary
