#!/usr/bin/env python3
"""OKX public futures market-data ingestion and canonical dataset staging v1.

Public GET allowlist only. No auth, no orders, no runtime effect.
Operator GO: GO_OKX_FUTURES_MARKET_DATA_INGESTION_AND_CANONICAL_DATASET_STAGING_V1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
from urllib import error, parse, request

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CONFIRM_TOKEN = "GO_OKX_FUTURES_MARKET_DATA_INGESTION_AND_CANONICAL_DATASET_STAGING_V1"
PROVIDER_ID = "okx_futures_public_market_data_only"
GO_TOKEN = CONFIRM_TOKEN

OKX_DOCS_REFERENCE = "https://www.okx.com/docs-v5/en/"
OKX_API_BASE_URL = "https://www.okx.com"
OKX_DOMAIN_DECISION = "www.okx.com"
OKX_DOMAIN_RATIONALE = (
    "Production REST base URL per official OKX API v5 documentation "
    "(flag=0 production trading; public market-data endpoints require no auth)."
)

NATIVE_INSTRUMENT_ID = "ETH-USDT-SWAP"
OKX_INDEX_CANDLE_INST_ID = "ETH-USDT"
CANONICAL_INSTRUMENT_ID = "inst-eth-usdt-perp"
CANONICAL_CONTRACT_TYPE = "perpetual"
INST_TYPE = "SWAP"
BAR_GRANULARITY = "1m"
DEFAULT_STAGING_WINDOW_DAYS = 14

MAX_TIMEOUT_SECONDS = 30.0
MAX_RESPONSE_BYTES_HARD_CAP = 50_000_000
MAX_RETRIES = 5
BASE_BACKOFF_SECONDS = 1.0
MAX_BACKOFF_SECONDS = 32.0
REQUESTS_PER_TWO_SECONDS = 18
PAGE_LIMIT = "300"

_FORBIDDEN_INSTRUMENT_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "spot", "synthetic_spot"})
_FORBIDDEN_PATH_PREFIXES: Tuple[str, ...] = (
    "/api/v5/trade/",
    "/api/v5/account/",
    "/api/v5/asset/",
)
_FORBIDDEN_AUTH_HEADERS = frozenset(
    {"OK-ACCESS-KEY", "OK-ACCESS-SIGN", "OK-ACCESS-TIMESTAMP", "OK-ACCESS-PASSPHRASE"}
)

ALLOWED_PUBLIC_GET_PATHS: frozenset[str] = frozenset(
    {
        "/api/v5/public/instruments",
        "/api/v5/market/history-candles",
        "/api/v5/market/history-mark-price-candles",
        "/api/v5/market/history-index-candles",
        "/api/v5/public/funding-rate-history",
        "/api/v5/rubik/stat/contracts/open-interest-history",
        "/api/v5/market/books",
        "/api/v5/public/time",
    }
)

ACQUISITION_ENDPOINT_ORDER: Tuple[str, ...] = (
    "/api/v5/public/instruments",
    "/api/v5/market/history-candles",
    "/api/v5/market/history-mark-price-candles",
    "/api/v5/market/history-index-candles",
    "/api/v5/public/funding-rate-history",
    "/api/v5/market/books",
)

REQUIRED_BAR_FIELDS = (
    "open",
    "high",
    "low",
    "close",
    "volume",
    "mark_price",
    "index_price",
    "best_bid",
    "best_ask",
    "funding_rate",
    "is_final",
)

JOIN_POLICY_VERSION = "okx_public_rest_join_v1"
MARK_INDEX_ASOF_RULE = "backward_exact_or_previous_finalized_candle_close"
FUNDING_ASOF_RULE = "backward_funding_time_no_lookahead"
BID_ASK_ASOF_RULE = "not_available_historical_public_api"
MAX_MARK_INDEX_STALENESS_MS = 60_000
MAX_FUNDING_STALENESS_MS = 28_800_000

PublicGetFetcher = Callable[..., Tuple[int, bytes, Dict[str, str]]]


@dataclass(frozen=True)
class RequestRecord:
    endpoint: str
    query_params: Dict[str, str]
    request_time_utc: str
    response_time_utc: str
    http_status: int
    okx_code: str
    pagination_cursor: str
    row_count: int
    raw_response_sha256: str
    raw_response_path: str


class IngestionError(Exception):
    """Fail-closed ingestion error."""


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def validate_public_get_url(url: str, *, api_base_url: str = OKX_API_BASE_URL) -> List[str]:
    reasons: List[str] = []
    parsed = parse.urlparse(url)
    if parsed.scheme != "https":
        reasons.append("FORBIDDEN_SCHEME")
    if parsed.netloc != OKX_DOMAIN_DECISION:
        reasons.append("FORBIDDEN_DOMAIN")
    path = parsed.path or ""
    path_lower = path.lower()
    for prefix in _FORBIDDEN_PATH_PREFIXES:
        if path_lower.startswith(prefix):
            reasons.append("FORBIDDEN_PRIVATE_ENDPOINT_PREFIX")
            break
    if path not in ALLOWED_PUBLIC_GET_PATHS:
        reasons.append("ENDPOINT_NOT_IN_ALLOWLIST")
    base = api_base_url.rstrip("/")
    if not url.startswith(base):
        reasons.append("URL_OUTSIDE_API_BASE")
    return reasons


def _read_body_capped(resp: Any, max_response_bytes: int) -> bytes:
    out = bytearray()
    while len(out) <= max_response_bytes:
        chunk = resp.read(min(65536, max(0, max_response_bytes - len(out) + 1)))
        if not chunk:
            break
        out.extend(chunk)
        if len(out) > max_response_bytes:
            raise IngestionError(f"response_exceeds_max_bytes:{len(out)}")
    return bytes(out)


class RateLimiter:
    def __init__(self, *, requests_per_two_seconds: int = REQUESTS_PER_TWO_SECONDS) -> None:
        self._interval = 2.0 / max(1, requests_per_two_seconds)
        self._last_at = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_at
        if elapsed < self._interval:
            time.sleep(self._interval - elapsed)
        self._last_at = time.monotonic()


def okx_public_fetch_v1(
    url: str,
    *,
    timeout_seconds: float,
    max_response_bytes: int,
    headers: Optional[Mapping[str, str]] = None,
) -> Tuple[int, bytes, Dict[str, str]]:
    """One public GET to allowlisted OKX endpoint. Tests patch this."""
    reasons = validate_public_get_url(url)
    if reasons:
        raise IngestionError(f"url_blocked:{reasons[0]}")
    hdrs = {"User-Agent": "PeakTradeOKXPublicIngestion/1", "Accept": "application/json"}
    if headers:
        for key in headers:
            if key.upper() in _FORBIDDEN_AUTH_HEADERS:
                raise IngestionError("auth_header_forbidden")
        hdrs.update(dict(headers))
    bounded_timeout = min(float(timeout_seconds), MAX_TIMEOUT_SECONDS)
    req = request.Request(url, method="GET", headers=hdrs)
    try:
        with request.urlopen(req, timeout=bounded_timeout) as resp:
            code = int(getattr(resp, "status", resp.getcode()))
            body = _read_body_capped(resp, max_response_bytes)
            resp_headers = {k: v for k, v in resp.headers.items()}
            return code, body, resp_headers
    except error.HTTPError as exc:
        body = _read_body_capped(exc, max_response_bytes)
        return int(exc.code), body, {k: v for k, v in exc.headers.items()}
    except (error.URLError, TimeoutError, OSError) as exc:
        raise IngestionError(f"fetch_failed:{exc}") from exc


def fetch_with_retry(
    url: str,
    *,
    timeout_seconds: float,
    max_response_bytes: int,
    rate_limiter: RateLimiter,
    fetcher: PublicGetFetcher = okx_public_fetch_v1,
) -> Tuple[int, bytes, Dict[str, str]]:
    last_exc: Optional[Exception] = None
    for attempt in range(MAX_RETRIES):
        rate_limiter.wait()
        status, body, headers = fetcher(
            url, timeout_seconds=timeout_seconds, max_response_bytes=max_response_bytes
        )
        if status == 429 or status >= 500:
            if attempt + 1 >= MAX_RETRIES:
                raise IngestionError(f"retry_exhausted:http_{status}")
            backoff = min(MAX_BACKOFF_SECONDS, BASE_BACKOFF_SECONDS * (2**attempt))
            jitter = random.uniform(0, backoff * 0.25)
            time.sleep(backoff + jitter)
            last_exc = IngestionError(f"transient_http_{status}")
            continue
        return status, body, headers
    raise IngestionError(f"retry_exhausted:{last_exc}")


def _build_url(path: str, params: Mapping[str, str]) -> str:
    base = OKX_API_BASE_URL.rstrip("/")
    query = parse.urlencode(dict(params))
    return f"{base}{path}?{query}" if query else f"{base}{path}"


def _parse_okx_json(body: bytes) -> Dict[str, Any]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IngestionError(f"invalid_json:{exc}") from exc
    if not isinstance(payload, dict):
        raise IngestionError("okx_payload_not_object")
    return payload


def is_forbidden_instrument(inst_id: str, inst_type: str, base_ccy: str) -> bool:
    combined = f"{inst_id} {inst_type} {base_ccy}".lower()
    return any(token in combined for token in _FORBIDDEN_INSTRUMENT_SUBSTRINGS)


def validate_okx_usdt_linear_swap_instrument(
    inst: Mapping[str, Any],
    *,
    expected_native_instrument_id: str,
    expected_canonical_instrument_id: str,
) -> Dict[str, Any]:
    inst_id = str(inst.get("instId", ""))
    inst_type = str(inst.get("instType", ""))
    if inst_id != expected_native_instrument_id:
        raise IngestionError(f"instrument_id_mismatch:{inst_id}")
    if inst_type != INST_TYPE:
        raise IngestionError(f"inst_type_mismatch:{inst_type}")
    base = str(inst.get("baseCcy") or inst.get("uly") or "").strip()
    if not base and inst.get("uly"):
        base = str(inst.get("uly", "")).split("-")[0]
    settle = str(inst.get("settleCcy") or "USDT")
    if is_forbidden_instrument(inst_id, inst_type, base):
        raise IngestionError("instrument_forbidden_token")
    if "btc" in base.lower() or "xbt" in base.lower():
        raise IngestionError("instrument_btc_forbidden")
    exp = inst.get("expTime") or inst.get("expiry") or ""
    if exp not in ("", None, "0"):
        raise IngestionError(f"instrument_not_perpetual_expiry:{exp}")
    return {
        "instId": inst_id,
        "instType": inst_type,
        "baseCcy": base,
        "settleCcy": settle,
        "uly": str(inst.get("uly") or ""),
        "ctVal": str(inst.get("ctVal", "")),
        "ctValCcy": str(inst.get("ctValCcy", "")),
        "tickSz": str(inst.get("tickSz", "")),
        "lotSz": str(inst.get("lotSz", "")),
        "minSz": str(inst.get("minSz", "")),
        "state": str(inst.get("state", "")),
        "listTime": str(inst.get("listTime", "")),
        "expTime": str(exp),
        "canonical_instrument_id": expected_canonical_instrument_id,
        "canonical_contract_type": CANONICAL_CONTRACT_TYPE,
    }


def validate_eth_usdt_swap_instrument(inst: Mapping[str, Any]) -> Dict[str, Any]:
    """Legacy explicit ETH binding (not a CURRENT-selection fallback)."""
    return validate_okx_usdt_linear_swap_instrument(
        inst,
        expected_native_instrument_id=NATIVE_INSTRUMENT_ID,
        expected_canonical_instrument_id=CANONICAL_INSTRUMENT_ID,
    )


def validate_index_candle_inst_id(inst_id: str) -> None:
    if is_forbidden_instrument(inst_id, "INDEX", inst_id.split("-")[0]):
        raise IngestionError("index_instrument_forbidden")


def resolve_okx_index_candle_inst_id_from_swap_metadata_v1(
    instrument_metadata: Mapping[str, Any],
) -> str:
    uly = str(instrument_metadata.get("uly") or "").strip()
    if uly:
        validate_index_candle_inst_id(uly)
        return uly
    base = str(instrument_metadata.get("baseCcy") or "").strip()
    settle = str(instrument_metadata.get("settleCcy") or "USDT").strip()
    if base and settle:
        candidate = f"{base}-{settle}"
        validate_index_candle_inst_id(candidate)
        return candidate
    raise IngestionError("index_candle_inst_id_unresolvable")


def fetch_instrument_metadata(
    *,
    fetcher: PublicGetFetcher,
    rate_limiter: RateLimiter,
    timeout_seconds: float,
    max_response_bytes: int,
    raw_dir: Path,
    request_log: List[RequestRecord],
    native_instrument_id: str,
    expected_canonical_instrument_id: str,
) -> Dict[str, Any]:
    params = {"instType": INST_TYPE, "instId": native_instrument_id}
    url = _build_url("/api/v5/public/instruments", params)
    req_at = _utc_now_z()
    status, body, _ = fetch_with_retry(
        url,
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
        rate_limiter=rate_limiter,
        fetcher=fetcher,
    )
    resp_at = _utc_now_z()
    digest = _sha256_bytes(body)
    raw_path = raw_dir / f"instruments_{digest[:16]}.json"
    raw_path.write_bytes(body)
    payload = _parse_okx_json(body)
    okx_code = str(payload.get("code", ""))
    data = payload.get("data") or []
    row_count = len(data) if isinstance(data, list) else 0
    request_log.append(
        RequestRecord(
            endpoint="/api/v5/public/instruments",
            query_params=dict(params),
            request_time_utc=req_at,
            response_time_utc=resp_at,
            http_status=status,
            okx_code=okx_code,
            pagination_cursor="",
            row_count=row_count,
            raw_response_sha256=digest,
            raw_response_path=str(raw_path),
        )
    )
    if status < 200 or status >= 300 or okx_code != "0":
        raise IngestionError(f"instruments_fetch_failed:http_{status}:code_{okx_code}")
    if not isinstance(data, list) or not data:
        raise IngestionError("instruments_empty")
    first = data[0]
    if not isinstance(first, Mapping):
        raise IngestionError("instrument_record_invalid")
    return validate_okx_usdt_linear_swap_instrument(
        first,
        expected_native_instrument_id=native_instrument_id,
        expected_canonical_instrument_id=expected_canonical_instrument_id,
    )


def _oldest_ts(rows: Sequence[Sequence[Any]]) -> Optional[str]:
    if not rows:
        return None
    return str(rows[-1][0])


def _candle_is_final(row: Sequence[Any]) -> bool:
    if len(row) >= 9:
        return str(row[8]) == "1"
    if len(row) >= 6:
        return str(row[5]) == "1"
    return False


def paginate_candles(
    *,
    path: str,
    params_base: Mapping[str, str],
    fetcher: PublicGetFetcher,
    rate_limiter: RateLimiter,
    timeout_seconds: float,
    max_response_bytes: int,
    raw_dir: Path,
    request_log: List[RequestRecord],
    start_ms: int,
    end_ms: int,
    series_name: str,
) -> List[List[Any]]:
    all_rows: List[List[Any]] = []
    after: Optional[str] = None
    page = 0
    while True:
        params = dict(params_base)
        params["limit"] = PAGE_LIMIT
        if after is not None:
            params["after"] = after
        url = _build_url(path, params)
        req_at = _utc_now_z()
        status, body, _ = fetch_with_retry(
            url,
            timeout_seconds=timeout_seconds,
            max_response_bytes=max_response_bytes,
            rate_limiter=rate_limiter,
            fetcher=fetcher,
        )
        resp_at = _utc_now_z()
        digest = _sha256_bytes(body)
        raw_path = raw_dir / f"{series_name}_p{page:04d}_{digest[:16]}.json"
        raw_path.write_bytes(body)
        payload = _parse_okx_json(body)
        okx_code = str(payload.get("code", ""))
        rows = payload.get("data") or []
        if not isinstance(rows, list):
            rows = []
        finalized = [r for r in rows if isinstance(r, list) and _candle_is_final(r)]
        request_log.append(
            RequestRecord(
                endpoint=path,
                query_params=dict(params),
                request_time_utc=req_at,
                response_time_utc=resp_at,
                http_status=status,
                okx_code=okx_code,
                pagination_cursor=after or "",
                row_count=len(finalized),
                raw_response_sha256=digest,
                raw_response_path=str(raw_path),
            )
        )
        if status < 200 or status >= 300 or okx_code != "0":
            raise IngestionError(f"{series_name}_fetch_failed:http_{status}:code_{okx_code}")
        if not rows:
            break
        for row in finalized:
            ts = int(str(row[0]))
            if start_ms <= ts <= end_ms:
                all_rows.append(row)
        oldest = _oldest_ts(rows)
        if oldest is None:
            break
        if int(oldest) <= start_ms:
            break
        if len(rows) < int(PAGE_LIMIT):
            break
        after = oldest
        page += 1
    dedup: Dict[int, List[Any]] = {}
    for row in all_rows:
        dedup[int(str(row[0]))] = row
    return [dedup[k] for k in sorted(dedup)]


def paginate_funding_history(
    *,
    fetcher: PublicGetFetcher,
    rate_limiter: RateLimiter,
    timeout_seconds: float,
    max_response_bytes: int,
    raw_dir: Path,
    request_log: List[RequestRecord],
    start_ms: int,
    end_ms: int,
    native_instrument_id: str,
) -> List[Dict[str, Any]]:
    path = "/api/v5/public/funding-rate-history"
    params_base = {"instId": native_instrument_id}
    all_rows: List[Dict[str, Any]] = []
    after: Optional[str] = None
    page = 0
    while True:
        params = dict(params_base)
        params["limit"] = PAGE_LIMIT
        if after is not None:
            params["after"] = after
        url = _build_url(path, params)
        req_at = _utc_now_z()
        status, body, _ = fetch_with_retry(
            url,
            timeout_seconds=timeout_seconds,
            max_response_bytes=max_response_bytes,
            rate_limiter=rate_limiter,
            fetcher=fetcher,
        )
        resp_at = _utc_now_z()
        digest = _sha256_bytes(body)
        raw_path = raw_dir / f"funding_p{page:04d}_{digest[:16]}.json"
        raw_path.write_bytes(body)
        payload = _parse_okx_json(body)
        okx_code = str(payload.get("code", ""))
        rows = payload.get("data") or []
        if not isinstance(rows, list):
            rows = []
        request_log.append(
            RequestRecord(
                endpoint=path,
                query_params=dict(params),
                request_time_utc=req_at,
                response_time_utc=resp_at,
                http_status=status,
                okx_code=okx_code,
                pagination_cursor=after or "",
                row_count=len(rows),
                raw_response_sha256=digest,
                raw_response_path=str(raw_path),
            )
        )
        if status < 200 or status >= 300 or okx_code != "0":
            raise IngestionError(f"funding_fetch_failed:http_{status}:code_{okx_code}")
        if not rows:
            break
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            ts = int(str(row.get("fundingTime", "0")))
            if start_ms <= ts <= end_ms:
                all_rows.append(dict(row))
        oldest_ts = min(
            (int(str(r.get("fundingTime", "0"))) for r in rows if isinstance(r, Mapping)),
            default=0,
        )
        if oldest_ts <= start_ms or len(rows) < int(PAGE_LIMIT):
            break
        after = str(oldest_ts)
        page += 1
    dedup: Dict[int, Dict[str, Any]] = {}
    for row in all_rows:
        dedup[int(str(row["fundingTime"]))] = row
    return [dedup[k] for k in sorted(dedup)]


def probe_historical_bid_ask_capability(
    *,
    fetcher: PublicGetFetcher,
    rate_limiter: RateLimiter,
    timeout_seconds: float,
    max_response_bytes: int,
) -> Dict[str, Any]:
    """Official OKX public API exposes orderbook snapshot only (no historical books endpoint)."""
    return {
        "historical_public_bid_ask_available": False,
        "snapshot_endpoint": "/api/v5/market/books",
        "historical_orderbook_endpoint_documented": False,
        "documentation_reference": OKX_DOCS_REFERENCE,
        "capability_verdict": "SNAPSHOT_ONLY_NO_HISTORICAL_PUBLIC_ORDERBOOK",
        "synthetic_bid_ask_forbidden": True,
    }


def compute_staging_window_ms(
    *,
    instrument_metadata: Mapping[str, Any],
    staging_window_days: int,
) -> Tuple[int, int, str, str]:
    now = datetime.now(timezone.utc)
    end_dt = now.replace(second=0, microsecond=0) - timedelta(minutes=1)
    start_dt = end_dt - timedelta(days=staging_window_days)
    list_time_raw = str(instrument_metadata.get("listTime") or "")
    if list_time_raw.isdigit():
        list_dt = datetime.fromtimestamp(int(list_time_raw) / 1000, tz=timezone.utc)
        if list_dt > start_dt:
            start_dt = list_dt.replace(second=0, microsecond=0)
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)
    return (
        start_ms,
        end_ms,
        start_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def build_availability_matrix(
    *,
    ohlcv_rows: int,
    mark_rows: int,
    index_rows: int,
    funding_rows: int,
    bid_ask_capability: Mapping[str, Any],
    start_utc: str,
    end_utc: str,
) -> Dict[str, Any]:
    return {
        "OHLCV": {
            "available": ohlcv_rows > 0,
            "row_count": ohlcv_rows,
            "period_start_utc": start_utc,
            "period_end_utc": end_utc,
        },
        "mark_price": {
            "available": mark_rows > 0,
            "row_count": mark_rows,
        },
        "index_price": {
            "available": index_rows > 0,
            "row_count": index_rows,
        },
        "funding_rate": {
            "available": funding_rows > 0,
            "row_count": funding_rows,
        },
        "best_bid": {
            "available": False,
            "row_count": 0,
            "reason": "NOT_AVAILABLE_BY_PUBLIC_SOURCE",
            "reason_detail": bid_ask_capability.get("capability_verdict"),
        },
        "best_ask": {
            "available": False,
            "row_count": 0,
            "reason": "NOT_AVAILABLE_BY_PUBLIC_SOURCE",
            "reason_detail": bid_ask_capability.get("capability_verdict"),
        },
        "is_final": {
            "available": ohlcv_rows > 0,
            "policy": "confirm=1_only",
        },
    }


_RUNTIME_REQUIRED_AVAILABILITY_FIELDS = (
    "OHLCV",
    "mark_price",
    "index_price",
    "best_bid",
    "best_ask",
    "funding_rate",
    "is_final",
)

_ECONOMIC_RESEARCH_REQUIRED_AVAILABILITY_FIELDS = (
    "OHLCV",
    "mark_price",
    "index_price",
    "funding_rate",
    "is_final",
)


def required_availability_fields_for_profile(
    dataset_profile: str = "runtime_market_context_v1",
) -> Tuple[str, ...]:
    if dataset_profile == "economic_research_v1":
        return _ECONOMIC_RESEARCH_REQUIRED_AVAILABILITY_FIELDS
    return _RUNTIME_REQUIRED_AVAILABILITY_FIELDS


def all_required_series_available(
    matrix: Mapping[str, Any],
    *,
    dataset_profile: str = "runtime_market_context_v1",
) -> bool:
    for field in required_availability_fields_for_profile(dataset_profile):
        if field == "OHLCV":
            if not matrix.get("OHLCV", {}).get("available"):
                return False
            continue
        entry = matrix.get(field)
        if not isinstance(entry, Mapping) or not entry.get("available"):
            return False
    return True


def classify_verdict(
    *,
    schema_complete: bool,
    integrity_pass: bool,
) -> str:
    if not schema_complete:
        return "OKX_DATA_ACQUIRED_SCHEMA_INCOMPLETE"
    if not integrity_pass:
        return "OKX_INGESTION_INVALID"
    return "OKX_CANONICAL_DATASET_STAGING_COMPLETE"


@dataclass(frozen=True)
class OkxFuturesIngestInstrumentBindingV1:
    native_instrument_id: str
    canonical_instrument_id: str
    selection_id: str = ""
    selection_integrity_digest: str = ""


def _legacy_explicit_eth_ingest_binding_v1() -> OkxFuturesIngestInstrumentBindingV1:
    return OkxFuturesIngestInstrumentBindingV1(
        native_instrument_id=NATIVE_INSTRUMENT_ID,
        canonical_instrument_id=CANONICAL_INSTRUMENT_ID,
        selection_id="legacy_explicit_eth_binding",
        selection_integrity_digest="",
    )


def run_ingestion(
    *,
    confirm: str,
    target_dataset_root: Path,
    durable_evidence_root: Path,
    staging_window_days: int = DEFAULT_STAGING_WINDOW_DAYS,
    timeout_seconds: float = 15.0,
    max_response_bytes: int = MAX_RESPONSE_BYTES_HARD_CAP,
    fetcher: PublicGetFetcher = okx_public_fetch_v1,
    skip_network: bool = False,
    instrument_binding: Optional[OkxFuturesIngestInstrumentBindingV1] = None,
) -> Dict[str, Any]:
    if confirm != CONFIRM_TOKEN:
        _die("ERR: confirm token required")
    if target_dataset_root.exists():
        _die(f"ERR: target_dataset_root_exists:{target_dataset_root}")

    binding = instrument_binding or _legacy_explicit_eth_ingest_binding_v1()
    native_instrument_id = binding.native_instrument_id
    canonical_instrument_id = binding.canonical_instrument_id
    index_candle_inst_id = OKX_INDEX_CANDLE_INST_ID

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tmp_root = target_dataset_root.parent / f".tmp_{ts_slug}"
    raw_dir = tmp_root / "raw"
    reports_dir = tmp_root / "reports"
    normalized_dir = tmp_root / "normalized"
    for d in (raw_dir, reports_dir, normalized_dir):
        d.mkdir(parents=True, exist_ok=True)

    rate_limiter = RateLimiter()
    request_log: List[RequestRecord] = []

    domain_decision = {
        "documentation_reference": OKX_DOCS_REFERENCE,
        "domain": OKX_DOMAIN_DECISION,
        "api_base_url": OKX_API_BASE_URL,
        "decision_rationale": OKX_DOMAIN_RATIONALE,
        "resolved_at_utc": _utc_now_z(),
        "https_required": True,
        "auth_required": False,
        "regional_ambiguity": False,
    }
    (reports_dir / "DOMAIN_DECISION.json").write_text(
        json.dumps(domain_decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    bid_ask_capability = probe_historical_bid_ask_capability(
        fetcher=fetcher,
        rate_limiter=rate_limiter,
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
    )
    (reports_dir / "BID_ASK_CAPABILITY.json").write_text(
        json.dumps(bid_ask_capability, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if skip_network:
        instrument_metadata = {
            "instId": native_instrument_id,
            "instType": INST_TYPE,
            "baseCcy": native_instrument_id.split("-")[0],
            "settleCcy": "USDT",
            "uly": index_candle_inst_id,
            "listTime": "0",
            "canonical_instrument_id": canonical_instrument_id,
        }
        start_ms, end_ms, start_utc, end_utc = compute_staging_window_ms(
            instrument_metadata=instrument_metadata,
            staging_window_days=staging_window_days,
        )
        matrix = build_availability_matrix(
            ohlcv_rows=0,
            mark_rows=0,
            index_rows=0,
            funding_rows=0,
            bid_ask_capability=bid_ask_capability,
            start_utc=start_utc,
            end_utc=end_utc,
        )
        verdict = classify_verdict(schema_complete=False, integrity_pass=True)
        return _finalize_reports(
            tmp_root=tmp_root,
            target_dataset_root=target_dataset_root,
            durable_evidence_root=durable_evidence_root,
            ts_slug=ts_slug,
            instrument_metadata=instrument_metadata,
            request_log=request_log,
            availability_matrix=matrix,
            verdict=verdict,
            start_utc=start_utc,
            end_utc=end_utc,
            staging_window_days=staging_window_days,
            series_counts={"ohlcv": 0, "mark": 0, "index": 0, "funding": 0},
            bid_ask_capability=bid_ask_capability,
            domain_decision=domain_decision,
            ingest_binding=binding,
            okx_index_candle_inst_id=index_candle_inst_id,
        )

    instrument_metadata = fetch_instrument_metadata(
        fetcher=fetcher,
        rate_limiter=rate_limiter,
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
        raw_dir=raw_dir,
        request_log=request_log,
        native_instrument_id=native_instrument_id,
        expected_canonical_instrument_id=canonical_instrument_id,
    )
    index_candle_inst_id = resolve_okx_index_candle_inst_id_from_swap_metadata_v1(
        instrument_metadata
    )
    start_ms, end_ms, start_utc, end_utc = compute_staging_window_ms(
        instrument_metadata=instrument_metadata,
        staging_window_days=staging_window_days,
    )

    candle_params = {"instId": native_instrument_id, "bar": BAR_GRANULARITY}
    ohlcv_rows = paginate_candles(
        path="/api/v5/market/history-candles",
        params_base=candle_params,
        fetcher=fetcher,
        rate_limiter=rate_limiter,
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
        raw_dir=raw_dir,
        request_log=request_log,
        start_ms=start_ms,
        end_ms=end_ms,
        series_name="ohlcv",
    )
    mark_rows = paginate_candles(
        path="/api/v5/market/history-mark-price-candles",
        params_base=candle_params,
        fetcher=fetcher,
        rate_limiter=rate_limiter,
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
        raw_dir=raw_dir,
        request_log=request_log,
        start_ms=start_ms,
        end_ms=end_ms,
        series_name="mark",
    )
    validate_index_candle_inst_id(index_candle_inst_id)
    index_rows = paginate_candles(
        path="/api/v5/market/history-index-candles",
        params_base={"instId": index_candle_inst_id, "bar": BAR_GRANULARITY},
        fetcher=fetcher,
        rate_limiter=rate_limiter,
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
        raw_dir=raw_dir,
        request_log=request_log,
        start_ms=start_ms,
        end_ms=end_ms,
        series_name="index",
    )
    funding_rows = paginate_funding_history(
        fetcher=fetcher,
        rate_limiter=rate_limiter,
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
        raw_dir=raw_dir,
        request_log=request_log,
        start_ms=start_ms,
        end_ms=end_ms,
        native_instrument_id=native_instrument_id,
    )

    matrix = build_availability_matrix(
        ohlcv_rows=len(ohlcv_rows),
        mark_rows=len(mark_rows),
        index_rows=len(index_rows),
        funding_rows=len(funding_rows),
        bid_ask_capability=bid_ask_capability,
        start_utc=start_utc,
        end_utc=end_utc,
    )
    schema_complete = all_required_series_available(matrix)
    verdict = classify_verdict(schema_complete=schema_complete, integrity_pass=True)

    return _finalize_reports(
        tmp_root=tmp_root,
        target_dataset_root=target_dataset_root,
        durable_evidence_root=durable_evidence_root,
        ts_slug=ts_slug,
        instrument_metadata=instrument_metadata,
        request_log=request_log,
        availability_matrix=matrix,
        verdict=verdict,
        start_utc=start_utc,
        end_utc=end_utc,
        staging_window_days=staging_window_days,
        series_counts={
            "ohlcv": len(ohlcv_rows),
            "mark": len(mark_rows),
            "index": len(index_rows),
            "funding": len(funding_rows),
        },
        bid_ask_capability=bid_ask_capability,
        domain_decision=domain_decision,
        ingest_binding=binding,
        okx_index_candle_inst_id=index_candle_inst_id,
    )


def _finalize_reports(
    *,
    tmp_root: Path,
    target_dataset_root: Path,
    durable_evidence_root: Path,
    ts_slug: str,
    instrument_metadata: Mapping[str, Any],
    request_log: Sequence[RequestRecord],
    availability_matrix: Mapping[str, Any],
    verdict: str,
    start_utc: str,
    end_utc: str,
    staging_window_days: int,
    series_counts: Mapping[str, int],
    bid_ask_capability: Mapping[str, Any],
    domain_decision: Mapping[str, Any],
    ingest_binding: OkxFuturesIngestInstrumentBindingV1,
    okx_index_candle_inst_id: str,
) -> Dict[str, Any]:
    reports_dir = tmp_root / "reports"
    ingestion_config = {
        "go_token": GO_TOKEN,
        "provider_id": PROVIDER_ID,
        "native_instrument_id": ingest_binding.native_instrument_id,
        "canonical_instrument_id": ingest_binding.canonical_instrument_id,
        "selection_id": ingest_binding.selection_id,
        "selection_integrity_digest": ingest_binding.selection_integrity_digest,
        "bar_granularity": BAR_GRANULARITY,
        "staging_window_days": staging_window_days,
        "data_period": {"start_utc": start_utc, "end_utc": end_utc},
        "domain_decision": dict(domain_decision),
        "allowed_endpoints": sorted(ALLOWED_PUBLIC_GET_PATHS),
        "acquisition_endpoint_order": list(ACQUISITION_ENDPOINT_ORDER),
        "auth_required": False,
        "credentials_used": False,
        "http_client": "urllib.request",
        "rate_limit_policy": {
            "requests_per_two_seconds": REQUESTS_PER_TWO_SECONDS,
            "max_retries": MAX_RETRIES,
            "retry_on": [429, "5xx"],
        },
        "join_policies": {
            "version": JOIN_POLICY_VERSION,
            "primary_index": "finalized_candle_close_utc",
            "mark_price_asof": MARK_INDEX_ASOF_RULE,
            "index_price_asof": MARK_INDEX_ASOF_RULE,
            "funding_asof": FUNDING_ASOF_RULE,
            "bid_ask_asof": BID_ASK_ASOF_RULE,
            "max_mark_index_staleness_ms": MAX_MARK_INDEX_STALENESS_MS,
            "max_funding_staleness_ms": MAX_FUNDING_STALENESS_MS,
        },
    }
    (tmp_root / "INGESTION_CONFIG.json").write_text(
        json.dumps(ingestion_config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    instrument_binding = {
        "native_instrument_id": ingest_binding.native_instrument_id,
        "okx_index_candle_inst_id": okx_index_candle_inst_id,
        "index_candle_inst_id_rationale": (
            "OKX history-index-candles uses the index pair instId from public "
            "instrument metadata (uly or base-settle), not the SWAP instId."
        ),
        "canonical_instrument_id": ingest_binding.canonical_instrument_id,
        "selection_id": ingest_binding.selection_id,
        "selection_integrity_digest": ingest_binding.selection_integrity_digest,
        "validated": True,
        "mapping_basis": "okx_public_instruments_specification",
        "venue": "OKX",
        "instrument_metadata": dict(instrument_metadata),
    }
    (tmp_root / "INSTRUMENT_BINDING.json").write_text(
        json.dumps(instrument_binding, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    request_log_payload = [
        {
            "endpoint": r.endpoint,
            "query_params": r.query_params,
            "request_time_utc": r.request_time_utc,
            "response_time_utc": r.response_time_utc,
            "http_status": r.http_status,
            "okx_code": r.okx_code,
            "pagination_cursor": r.pagination_cursor,
            "row_count": r.row_count,
            "raw_response_sha256": r.raw_response_sha256,
            "raw_response_path": r.raw_response_path,
        }
        for r in request_log
    ]
    (reports_dir / "REQUEST_LOG.json").write_text(
        json.dumps(request_log_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    data_quality = {
        "verdict": verdict,
        "schema_complete": verdict == "OKX_CANONICAL_DATASET_STAGING_COMPLETE",
        "availability_matrix": dict(availability_matrix),
        "series_row_counts": dict(series_counts),
        "discarded_rows": [],
        "integrity_status": "NOT_RUN"
        if verdict != "OKX_CANONICAL_DATASET_STAGING_COMPLETE"
        else "PASS",
        "admissible_bars_parquet_emitted": False,
        "reason": (
            "historical_public_bid_ask_unavailable"
            if verdict == "OKX_DATA_ACQUIRED_SCHEMA_INCOMPLETE"
            else ""
        ),
    }
    (tmp_root / "DATA_QUALITY_REPORT.json").write_text(
        json.dumps(data_quality, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    provenance = {
        "source_type": "operator_staged_futures_v1",
        "source_venue": "OKX",
        "native_instrument_id": ingest_binding.native_instrument_id,
        "canonical_instrument_id": ingest_binding.canonical_instrument_id,
        "acquisition_method": "okx_public_rest_api_v5",
        "authenticated": False,
        "credentials_used": False,
        "generation_method": "okx_public_rest_api_v5_ingestion",
        "ingestion_timestamp_utc": _utc_now_z(),
    }
    (reports_dir / "PROVENANCE.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = {
        "verdict": verdict,
        "go_token": GO_TOKEN,
        "tmp_staging_root": str(tmp_root),
        "target_dataset_root": str(target_dataset_root),
        "series_row_counts": dict(series_counts),
        "availability_matrix": dict(availability_matrix),
        "instrument_binding": instrument_binding,
        "provenance": provenance,
        "domain_decision": dict(domain_decision),
        "bid_ask_capability": dict(bid_ask_capability),
        "data_period": {"start_utc": start_utc, "end_utc": end_utc},
        "request_count": len(request_log),
        "real_admissible_futures_dataset_found": verdict
        == "OKX_CANONICAL_DATASET_STAGING_COMPLETE",
        "real_admissible_futures_evidence_present": verdict
        == "OKX_CANONICAL_DATASET_STAGING_COMPLETE",
        "real_evaluation_performed": False,
        "economic_validity_result": "NOT_PROVEN",
    }

    evidence_dir = (
        durable_evidence_root
        / "planning_or_validation"
        / f"okx_futures_market_data_ingestion_canonical_dataset_staging_v1_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)
    summary_path = evidence_dir / "INGESTION_RESULT.json"
    summary_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for rel in (
        "INGESTION_CONFIG.json",
        "INSTRUMENT_BINDING.json",
        "DATA_QUALITY_REPORT.json",
        "reports/DOMAIN_DECISION.json",
        "reports/BID_ASK_CAPABILITY.json",
        "reports/REQUEST_LOG.json",
        "reports/PROVENANCE.json",
    ):
        src = tmp_root / rel
        if src.is_file():
            dst = evidence_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())

    if verdict == "OKX_CANONICAL_DATASET_STAGING_COMPLETE":
        target_dataset_root.parent.mkdir(parents=True, exist_ok=True)
        tmp_root.rename(target_dataset_root)
        result["target_dataset_root"] = str(target_dataset_root)
    else:
        result["staging_note"] = (
            "Schema incomplete; tmp staging retained under parent directory; "
            "target_dataset_root not promoted."
        )
        result["tmp_staging_root"] = str(tmp_root)

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)
    result["durable_evidence_path"] = str(evidence_dir)
    result["manifest_verify_rc"] = rc
    result["manifest_verify_msg"] = verify_msg

    _emit_machine_lines(result)
    return result


def _emit_machine_lines(result: Mapping[str, Any]) -> None:
    lines = [
        f"VERDICT={result.get('verdict')}",
        f"GO_TOKEN={GO_TOKEN}",
        f"REAL_ADMISSIBLE_FUTURES_DATASET_FOUND={str(result.get('real_admissible_futures_dataset_found')).lower()}",
        f"REAL_ADMISSIBLE_FUTURES_EVIDENCE_PRESENT={str(result.get('real_admissible_futures_evidence_present')).lower()}",
        f"REAL_EVALUATION_PERFORMED=false",
        f"ECONOMIC_VALIDITY_RESULT=NOT_PROVEN",
        f"MANIFEST_VERIFY_RC={result.get('manifest_verify_rc', 1)}",
        "ORDER_EFFECT=false",
        "RUNTIME_EFFECT=false",
        "LIVE_AUTHORIZED=false",
    ]
    for line in lines:
        print(line)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="OKX public futures market-data ingestion and canonical dataset staging v1."
    )
    parser.add_argument(
        "--confirm-go-token",
        required=True,
        choices=[CONFIRM_TOKEN],
    )
    parser.add_argument(
        "--target-dataset-root",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--durable-evidence-root",
        type=Path,
        required=True,
    )
    parser.add_argument("--staging-window-days", type=int, default=DEFAULT_STAGING_WINDOW_DAYS)
    parser.add_argument("--timeout-seconds", type=float, default=15.0)
    parser.add_argument("--max-response-bytes", type=int, default=MAX_RESPONSE_BYTES_HARD_CAP)
    parser.add_argument(
        "--skip-network",
        action="store_true",
        help="Offline contract path for tests only.",
    )
    parser.add_argument(
        "--selection-state-root",
        type=Path,
        default=None,
        help=(
            "Cap 2.3 persisted selection state root; binds ingest instrument from "
            "post-selection output only (no ranking/universe consumption)."
        ),
    )
    parser.add_argument(
        "--native-instrument-id",
        default="",
        help="Explicit OKX SWAP instId binding (requires --canonical-instrument-id).",
    )
    parser.add_argument(
        "--canonical-instrument-id",
        default="",
        help="Explicit canonical instrument id binding (requires --native-instrument-id).",
    )
    ns = parser.parse_args(argv)
    instrument_binding: Optional[OkxFuturesIngestInstrumentBindingV1] = None
    if ns.selection_state_root is not None:
        from src.backtest import (  # noqa: PLC0415
            step29m_current_single_selected_future_dynamic_binding_v1 as step29m_bind,
        )

        step29m_binding = (
            step29m_bind.resolve_step29m_instrument_binding_from_selection_state_root_v1(
                ns.selection_state_root
            )
        )
        ingest_payload = step29m_bind.to_public_market_data_ingest_instrument_binding_v1(
            step29m_binding
        )
        instrument_binding = OkxFuturesIngestInstrumentBindingV1(
            native_instrument_id=ingest_payload.native_instrument_id,
            canonical_instrument_id=ingest_payload.canonical_instrument_id,
            selection_id=ingest_payload.selection_id,
            selection_integrity_digest=ingest_payload.selection_integrity_digest,
        )
    native_explicit = str(ns.native_instrument_id or "").strip()
    canon_explicit = str(ns.canonical_instrument_id or "").strip()
    if native_explicit or canon_explicit:
        if not native_explicit or not canon_explicit:
            _die("ERR: native_instrument_id_and_canonical_instrument_id_required_together")
        explicit = OkxFuturesIngestInstrumentBindingV1(
            native_instrument_id=native_explicit,
            canonical_instrument_id=canon_explicit,
            selection_id="explicit_operator_instrument_binding",
            selection_integrity_digest="",
        )
        if instrument_binding is not None and (
            instrument_binding.native_instrument_id != explicit.native_instrument_id
            or instrument_binding.canonical_instrument_id != explicit.canonical_instrument_id
        ):
            _die("ERR: selection_state_root_binding_conflicts_with_explicit_instrument_binding")
        instrument_binding = explicit
    try:
        run_ingestion(
            confirm=ns.confirm_go_token,
            target_dataset_root=ns.target_dataset_root,
            durable_evidence_root=ns.durable_evidence_root,
            staging_window_days=ns.staging_window_days,
            timeout_seconds=ns.timeout_seconds,
            max_response_bytes=ns.max_response_bytes,
            skip_network=ns.skip_network,
            instrument_binding=instrument_binding,
        )
    except (IngestionError, SystemExit) as exc:
        if isinstance(exc, SystemExit):
            raise
        _die(f"ERR: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
