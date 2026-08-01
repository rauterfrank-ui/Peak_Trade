"""Injectable EEA public REST MD transport (no import-time networking)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
from typing import Any, Callable, Mapping, Optional, Protocol
from urllib.parse import urlencode

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    ALLOWED_PATHS,
    CANONICAL_HOST,
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


class AttemptGateV1(Protocol):
    """Pre/post hooks around each physical HTTP attempt (budget + pacing + evidence)."""

    def before_physical_attempt(
        self, *, url: str, path: str, attempt_index: int
    ) -> Mapping[str, Any]: ...

    def after_physical_attempt(
        self,
        *,
        url: str,
        path: str,
        attempt_index: int,
        status: Optional[int],
        headers: Mapping[str, str],
        error_code: str,
        terminal: bool,
        backoff_source: str,
        scheduled_backoff_seconds: float,
        retry_after_raw: Optional[str],
        retry_after_parsed_seconds: Optional[float],
        started_monotonic: float,
        finished_monotonic: float,
        budget_before: int,
        budget_after: int,
    ) -> None: ...


@dataclass
class TransportFetchResultV1:
    url: str
    path: str
    status: int
    body: bytes
    payload: dict[str, Any]
    attempt: int
    response_headers: Mapping[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "path": self.path,
            "status": self.status,
            "byte_size": len(self.body),
            "attempt": self.attempt,
            "provider_code": str(self.payload.get("code", "")),
        }


def _legacy_backoff_seconds(attempt: int) -> float:
    # Retained only when no hardened rate-limit policy is attached.
    return 0.01 * (2**attempt)


def _header_get_ci(headers: Mapping[str, str] | None, name: str) -> Optional[str]:
    if not headers:
        return None
    wanted = name.lower()
    for key, value in headers.items():
        if str(key).lower() == wanted:
            text = str(value).strip()
            return text if text else None
    return None


def _parse_retry_after_seconds(
    headers: Mapping[str, str] | None,
    *,
    now_unix: float,
    max_seconds: float,
) -> tuple[Optional[str], Optional[float], str, bool, str]:
    raw = _header_get_ci(headers, "Retry-After")
    if raw is None:
        return None, None, "absent", False, ""
    try:
        seconds = float(raw)
        if seconds < 0:
            return raw, None, "delta_seconds", False, "RATE_LIMIT_RETRY_AFTER_INVALID"
        capped = min(seconds, float(max_seconds))
        source = "delta_seconds_capped" if capped < seconds else "delta_seconds"
        return raw, float(capped), source, True, ""
    except ValueError:
        pass
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            return raw, None, "http_date", False, "RATE_LIMIT_RETRY_AFTER_INVALID"
        delta = dt.timestamp() - float(now_unix)
        if delta < 0:
            return raw, None, "http_date", False, "RATE_LIMIT_RETRY_AFTER_INVALID"
        capped = min(delta, float(max_seconds))
        source = "http_date_capped" if capped < delta else "http_date"
        return raw, float(capped), source, True, ""
    except (TypeError, ValueError, IndexError, OverflowError):
        return raw, None, "unparseable", False, "RATE_LIMIT_RETRY_AFTER_INVALID"


def _policy_exponential_backoff(policy: Any, *, attempt: int, jitter_unit: float) -> float:
    initial = float(getattr(policy, "backoff_initial_seconds"))
    mult = float(getattr(policy, "backoff_multiplier"))
    maximum = float(getattr(policy, "backoff_max_seconds"))
    jitter_fraction = float(getattr(policy, "jitter_fraction"))
    base = initial * (mult ** int(attempt))
    capped = min(base, maximum)
    unit = max(0.0, min(0.999999, float(jitter_unit)))
    span = capped * jitter_fraction
    return max(0.0, capped - span + (span * unit))


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
    # Hardened 429/pacing policy (optional; productive runner attaches it).
    rate_limit_policy: Any = None
    attempt_gate: Optional[AttemptGateV1] = None
    monotonic_clock: Callable[[], float] = time.monotonic
    wall_clock: Callable[[], float] = time.time
    jitter_unit_fn: Optional[Callable[[int], float]] = None

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

    def _schedule_429_backoff(
        self, *, attempt: int, headers: Mapping[str, str]
    ) -> tuple[float, str, Optional[str], Optional[float], str]:
        """Return (delay, backoff_source, retry_after_raw, retry_after_parsed, error_code)."""
        if self.rate_limit_policy is None:
            return (
                _legacy_backoff_seconds(attempt),
                "legacy_millisecond_backoff",
                None,
                None,
                "",
            )
        raw, parsed_seconds, source, valid, parse_err = _parse_retry_after_seconds(
            headers,
            now_unix=float(self.wall_clock()),
            max_seconds=float(self.rate_limit_policy.retry_after_max_seconds),
        )
        if valid and parsed_seconds is not None:
            return (
                float(parsed_seconds),
                f"retry_after:{source}",
                raw,
                float(parsed_seconds),
                "RATE_LIMIT_RETRY_SCHEDULED",
            )
        jitter_unit = 0.0
        if self.jitter_unit_fn is not None:
            jitter_unit = float(self.jitter_unit_fn(int(self.fetch_count)))
        delay = _policy_exponential_backoff(
            self.rate_limit_policy, attempt=attempt, jitter_unit=jitter_unit
        )
        err = parse_err or "RATE_LIMIT_RETRY_SCHEDULED"
        backoff_source = (
            "exponential_backoff_after_invalid_retry_after" if parse_err else "exponential_backoff"
        )
        return float(delay), backoff_source, raw, parsed_seconds, err

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

        max_attempts = int(self.max_retries) + 1
        if self.rate_limit_policy is not None:
            max_attempts = min(
                max_attempts, int(self.rate_limit_policy.maximum_consecutive_rate_limits)
            )

        last_err: Exception | None = None
        consecutive_429 = 0
        for attempt in range(max_attempts):
            gate_meta: Mapping[str, Any] = {}
            if self.attempt_gate is not None:
                gate_meta = self.attempt_gate.before_physical_attempt(
                    url=url, path=path, attempt_index=attempt
                )
            budget_before = int(gate_meta.get("budget_before", -1))
            budget_after = int(gate_meta.get("budget_after", -1))
            started = float(self.monotonic_clock())
            status: Optional[int] = None
            resp_headers: Mapping[str, str] = {}
            error_code = ""
            backoff_source = ""
            scheduled_backoff = 0.0
            retry_after_raw: Optional[str] = None
            retry_after_parsed: Optional[float] = None
            terminal = False
            try:
                self.fetch_count += 1
                self.last_url = url
                status, body, resp_headers = self.fetcher(url, "GET", headers, self.timeout_seconds)
                finished = float(self.monotonic_clock())
                if status in {401, 403}:
                    terminal = True
                    error_code = f"ABORT_CREDENTIAL_OR_AUTH_SURFACE:HTTP_{status}"
                    if self.attempt_gate is not None:
                        self.attempt_gate.after_physical_attempt(
                            url=url,
                            path=path,
                            attempt_index=attempt,
                            status=status,
                            headers=resp_headers,
                            error_code=error_code,
                            terminal=True,
                            backoff_source="",
                            scheduled_backoff_seconds=0.0,
                            retry_after_raw=None,
                            retry_after_parsed_seconds=None,
                            started_monotonic=started,
                            finished_monotonic=finished,
                            budget_before=budget_before,
                            budget_after=budget_after,
                        )
                    raise EeaPublicMdTransportError(error_code)
                if status == 429:
                    consecutive_429 += 1
                    self.http_429_count += 1
                    if self.http_429_count > self.session_http_429_budget:
                        terminal = True
                        error_code = "RATE_LIMIT_SESSION_BUDGET_EXCEEDED"
                        if self.attempt_gate is not None:
                            self.attempt_gate.after_physical_attempt(
                                url=url,
                                path=path,
                                attempt_index=attempt,
                                status=status,
                                headers=resp_headers,
                                error_code=error_code,
                                terminal=True,
                                backoff_source="",
                                scheduled_backoff_seconds=0.0,
                                retry_after_raw=None,
                                retry_after_parsed_seconds=None,
                                started_monotonic=started,
                                finished_monotonic=finished,
                                budget_before=budget_before,
                                budget_after=budget_after,
                            )
                        raise EeaPublicMdTransportError(error_code)
                    (
                        scheduled_backoff,
                        backoff_source,
                        retry_after_raw,
                        retry_after_parsed,
                        error_code,
                    ) = self._schedule_429_backoff(attempt=attempt, headers=resp_headers)
                    last_err = EeaPublicMdTransportError("RATE_LIMIT_HTTP_429")
                    if attempt + 1 >= max_attempts:
                        terminal = True
                        error_code = "RATE_LIMIT_RETRY_EXHAUSTED"
                        if self.attempt_gate is not None:
                            self.attempt_gate.after_physical_attempt(
                                url=url,
                                path=path,
                                attempt_index=attempt,
                                status=status,
                                headers=resp_headers,
                                error_code=error_code,
                                terminal=True,
                                backoff_source=backoff_source,
                                scheduled_backoff_seconds=scheduled_backoff,
                                retry_after_raw=retry_after_raw,
                                retry_after_parsed_seconds=retry_after_parsed,
                                started_monotonic=started,
                                finished_monotonic=finished,
                                budget_before=budget_before,
                                budget_after=budget_after,
                            )
                        raise EeaPublicMdTransportError(
                            f"FETCH_FAILED:{error_code}:RATE_LIMIT_HTTP_429"
                        )
                    if self.attempt_gate is not None:
                        self.attempt_gate.after_physical_attempt(
                            url=url,
                            path=path,
                            attempt_index=attempt,
                            status=status,
                            headers=resp_headers,
                            error_code=error_code or "RATE_LIMIT_RETRY_SCHEDULED",
                            terminal=False,
                            backoff_source=backoff_source,
                            scheduled_backoff_seconds=scheduled_backoff,
                            retry_after_raw=retry_after_raw,
                            retry_after_parsed_seconds=retry_after_parsed,
                            started_monotonic=started,
                            finished_monotonic=finished,
                            budget_before=budget_before,
                            budget_after=budget_after,
                        )
                    self.sleep(float(scheduled_backoff))
                    continue
                if status >= 400:
                    terminal = True
                    error_code = f"HTTP_{status}"
                    if self.attempt_gate is not None:
                        self.attempt_gate.after_physical_attempt(
                            url=url,
                            path=path,
                            attempt_index=attempt,
                            status=status,
                            headers=resp_headers,
                            error_code=error_code,
                            terminal=True,
                            backoff_source="",
                            scheduled_backoff_seconds=0.0,
                            retry_after_raw=None,
                            retry_after_parsed_seconds=None,
                            started_monotonic=started,
                            finished_monotonic=finished,
                            budget_before=budget_before,
                            budget_after=budget_after,
                        )
                    raise EeaPublicMdTransportError(error_code)
                payload = json.loads(body.decode("utf-8"))
                if not isinstance(payload, dict):
                    error_code = "PAYLOAD_NOT_OBJECT"
                    if self.attempt_gate is not None:
                        self.attempt_gate.after_physical_attempt(
                            url=url,
                            path=path,
                            attempt_index=attempt,
                            status=status,
                            headers=resp_headers,
                            error_code=error_code,
                            terminal=True,
                            backoff_source="",
                            scheduled_backoff_seconds=0.0,
                            retry_after_raw=None,
                            retry_after_parsed_seconds=None,
                            started_monotonic=started,
                            finished_monotonic=finished,
                            budget_before=budget_before,
                            budget_after=budget_after,
                        )
                    raise EeaPublicMdTransportError(error_code)
                if str(payload.get("code", "0")) not in {"0", ""}:
                    error_code = f"PROVIDER_CODE_{payload.get('code')}:{payload.get('msg')}"
                    if self.attempt_gate is not None:
                        self.attempt_gate.after_physical_attempt(
                            url=url,
                            path=path,
                            attempt_index=attempt,
                            status=status,
                            headers=resp_headers,
                            error_code=error_code,
                            terminal=True,
                            backoff_source="",
                            scheduled_backoff_seconds=0.0,
                            retry_after_raw=None,
                            retry_after_parsed_seconds=None,
                            started_monotonic=started,
                            finished_monotonic=finished,
                            budget_before=budget_before,
                            budget_after=budget_after,
                        )
                    raise EeaPublicMdTransportError(error_code)
                if self.attempt_gate is not None:
                    self.attempt_gate.after_physical_attempt(
                        url=url,
                        path=path,
                        attempt_index=attempt,
                        status=status,
                        headers=resp_headers,
                        error_code="",
                        terminal=False,
                        backoff_source="",
                        scheduled_backoff_seconds=0.0,
                        retry_after_raw=None,
                        retry_after_parsed_seconds=None,
                        started_monotonic=started,
                        finished_monotonic=finished,
                        budget_before=budget_before,
                        budget_after=budget_after,
                    )
                return TransportFetchResultV1(
                    url=url,
                    path=path,
                    status=status,
                    body=body,
                    payload=payload,
                    attempt=attempt,
                    response_headers=dict(resp_headers),
                )
            except (NetworkBoundaryError, EeaPublicMdTransportError):
                raise
            except Exception as exc:  # noqa: BLE001
                finished = float(self.monotonic_clock())
                last_err = exc
                if attempt >= max_attempts - 1:
                    if self.attempt_gate is not None:
                        self.attempt_gate.after_physical_attempt(
                            url=url,
                            path=path,
                            attempt_index=attempt,
                            status=status,
                            headers=resp_headers,
                            error_code=f"FETCH_FAILED:{exc}",
                            terminal=True,
                            backoff_source="",
                            scheduled_backoff_seconds=0.0,
                            retry_after_raw=None,
                            retry_after_parsed_seconds=None,
                            started_monotonic=started,
                            finished_monotonic=finished,
                            budget_before=budget_before,
                            budget_after=budget_after,
                        )
                    break
                if self.rate_limit_policy is None:
                    delay = _legacy_backoff_seconds(attempt)
                    source = "legacy_millisecond_backoff"
                else:
                    jitter_unit = (
                        float(self.jitter_unit_fn(int(self.fetch_count)))
                        if self.jitter_unit_fn is not None
                        else 0.0
                    )
                    delay = _policy_exponential_backoff(
                        self.rate_limit_policy, attempt=attempt, jitter_unit=jitter_unit
                    )
                    source = "exponential_backoff"
                if self.attempt_gate is not None:
                    self.attempt_gate.after_physical_attempt(
                        url=url,
                        path=path,
                        attempt_index=attempt,
                        status=status,
                        headers=resp_headers,
                        error_code=str(exc),
                        terminal=False,
                        backoff_source=source,
                        scheduled_backoff_seconds=float(delay),
                        retry_after_raw=None,
                        retry_after_parsed_seconds=None,
                        started_monotonic=started,
                        finished_monotonic=finished,
                        budget_before=budget_before,
                        budget_after=budget_after,
                    )
                self.sleep(float(delay))
        raise EeaPublicMdTransportError(f"FETCH_FAILED:{last_err}") from last_err

    def fetch_instruments(
        self, *, venue_instrument_id: str, inst_type: str = "FUTURES"
    ) -> TransportFetchResultV1:
        """Public instruments lookup by native OKX venue_instrument_id only."""
        if not venue_instrument_id or not str(venue_instrument_id).strip():
            raise EeaPublicMdTransportError("VENUE_INSTRUMENT_ID_REQUIRED")
        return self.get_json(
            "/api/v5/public/instruments",
            {"instType": inst_type, "instId": str(venue_instrument_id)},
        )

    def fetch_mark_price(
        self, *, venue_instrument_id: str, inst_type: str = "FUTURES"
    ) -> TransportFetchResultV1:
        """Public mark-price contract. Never accepts Peak_Trade canonical ID param name."""
        if not venue_instrument_id or not str(venue_instrument_id).strip():
            raise EeaPublicMdTransportError("VENUE_INSTRUMENT_ID_REQUIRED")
        return self.get_json(
            "/api/v5/public/mark-price",
            {"instType": inst_type, "instId": str(venue_instrument_id)},
        )

    def fetch_ticker(self, *, venue_instrument_id: str) -> TransportFetchResultV1:
        """Public ticker for declared last/bid/ask semantics only (not markPx)."""
        if not venue_instrument_id or not str(venue_instrument_id).strip():
            raise EeaPublicMdTransportError("VENUE_INSTRUMENT_ID_REQUIRED")
        return self.get_json(
            "/api/v5/market/ticker",
            {"instId": str(venue_instrument_id)},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "opened": self.opened,
            "fetch_count": self.fetch_count,
            "http_429_count": self.http_429_count,
            "last_url": self.last_url,
            "events": list(self.events),
            "hardened_rate_limit_policy_attached": self.rate_limit_policy is not None,
        }


def parse_ticker_mid_price_v1(payload: Mapping[str, Any]) -> float:
    """Deprecated for mark semantics — ticker must not supply markPx.

    Kept as a fail-closed guard so accidental ticker→markPx use aborts without
    silent last/bid/ask substitution.
    """
    del payload  # unused; always fail-closed
    raise EeaPublicMdTransportError(
        "REQUIRED_PRICE_FIELD_MISSING:markPx_not_on_ticker_use_public_mark_price"
    )
