"""Injectable EEA public REST MD transport (no import-time networking)."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Mapping, Optional, Sequence
from urllib.parse import urlencode

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    ALLOWED_PATHS,
    CANONICAL_HOST,
    CANONICAL_INSTRUMENT_ID,
    DEFAULT_PER_REQUEST_MAX_RETRIES,
    DEFAULT_SESSION_HTTP_429_BUDGET,
    USER_AGENT,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.network_boundary_guard_v1 import (
    NetworkBoundaryError,
    validate_request_boundary_v1,
)

HttpFetcher = Callable[[str, str, Mapping[str, str], float], tuple[int, bytes, Mapping[str, str]]]


class EeaPublicMdTransportError(RuntimeError):
    """Transport failure."""


@dataclass
class TransportFetchResultV1:
    url: str
    path: str
    status: int
    body: bytes
    payload: dict[str, Any]
    attempt: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "path": self.path,
            "status": self.status,
            "byte_size": len(self.body),
            "attempt": self.attempt,
            "provider_code": str(self.payload.get("code", "")),
        }


@dataclass
class EeaPublicMdTransportV1:
    """REST-only transport. Real urllib is never used unless explicitly injected."""

    fetcher: HttpFetcher
    timeout_seconds: float = 10.0
    max_retries: int = DEFAULT_PER_REQUEST_MAX_RETRIES
    session_http_429_budget: int = DEFAULT_SESSION_HTTP_429_BUDGET
    sleep: Callable[[float], None] = time.sleep
    environ: Optional[Mapping[str, str]] = None
    opened: bool = False
    http_429_count: int = 0
    fetch_count: int = 0
    last_url: str = ""
    events: list[dict[str, Any]] = field(default_factory=list)

    def open(self) -> None:
        if self.opened:
            raise EeaPublicMdTransportError("TRANSPORT_ALREADY_OPEN")
        # Opening does not fetch; marks transport ready after auth consumption.
        self.opened = True
        self.events.append({"event": "transport_opened", "host": CANONICAL_HOST})

    def close(self) -> None:
        self.opened = False
        self.events.append({"event": "transport_closed"})

    def _build_url(self, path: str, params: Mapping[str, str]) -> str:
        if path not in ALLOWED_PATHS:
            raise NetworkBoundaryError(f"PATH_NOT_ALLOWED:{path}")
        query = {str(k): str(v) for k, v in params.items()}
        url = f"https://{CANONICAL_HOST}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"
        return url

    def get_json(self, path: str, params: Mapping[str, str]) -> TransportFetchResultV1:
        if not self.opened:
            raise EeaPublicMdTransportError("TRANSPORT_NOT_OPEN")
        url = self._build_url(path, params)
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        boundary = validate_request_boundary_v1(
            url=url, method="GET", headers=headers, environ=self.environ
        )
        if not boundary.ok:
            raise NetworkBoundaryError(",".join(boundary.blockers))

        last_err: Exception | None = None
        for attempt in range(self.max_retries + 1):
            self.fetch_count += 1
            self.last_url = url
            try:
                status, body, _resp_headers = self.fetcher(
                    url, "GET", headers, self.timeout_seconds
                )
                if status in {401, 403}:
                    raise EeaPublicMdTransportError(
                        f"ABORT_CREDENTIAL_OR_AUTH_SURFACE:HTTP_{status}"
                    )
                if status == 429:
                    self.http_429_count += 1
                    if self.http_429_count > self.session_http_429_budget:
                        raise EeaPublicMdTransportError("HTTP_429_BUDGET_EXCEEDED")
                    last_err = EeaPublicMdTransportError("RATE_LIMIT_HTTP_429")
                    self.sleep(0.01 * (2**attempt))
                    continue
                if status >= 400:
                    raise EeaPublicMdTransportError(f"HTTP_{status}")
                payload = json.loads(body.decode("utf-8"))
                if not isinstance(payload, dict):
                    raise EeaPublicMdTransportError("PAYLOAD_NOT_OBJECT")
                if str(payload.get("code", "0")) not in {"0", ""}:
                    raise EeaPublicMdTransportError(
                        f"PROVIDER_CODE_{payload.get('code')}:{payload.get('msg')}"
                    )
                return TransportFetchResultV1(
                    url=url,
                    path=path,
                    status=status,
                    body=body,
                    payload=payload,
                    attempt=attempt,
                )
            except (NetworkBoundaryError, EeaPublicMdTransportError):
                raise
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                if attempt >= self.max_retries:
                    break
                self.sleep(0.01 * (2**attempt))
        raise EeaPublicMdTransportError(f"FETCH_FAILED:{last_err}") from last_err

    def fetch_ticker(
        self, *, instrument_id: str = CANONICAL_INSTRUMENT_ID
    ) -> TransportFetchResultV1:
        return self.get_json(
            "/api/v5/market/ticker",
            {"instId": instrument_id},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "opened": self.opened,
            "fetch_count": self.fetch_count,
            "http_429_count": self.http_429_count,
            "last_url": self.last_url,
            "events": list(self.events),
        }


def parse_ticker_mid_price_v1(payload: Mapping[str, Any]) -> float:
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise EeaPublicMdTransportError("TICKER_DATA_MISSING")
    row = data[0]
    if not isinstance(row, dict):
        raise EeaPublicMdTransportError("TICKER_ROW_INVALID")
    for key in ("last", "markPx", "askPx", "bidPx"):
        raw = row.get(key)
        if raw is None or raw == "":
            continue
        price = float(raw)
        if price > 0:
            return price
    raise EeaPublicMdTransportError("TICKER_PRICE_MISSING")
