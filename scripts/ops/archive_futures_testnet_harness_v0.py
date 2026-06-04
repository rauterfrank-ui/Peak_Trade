#!/usr/bin/env python3
"""Governed bounded Kraken demo-futures testnet archive harness (zero-order reachability v0).

Produces durable primary evidence under an archive root. Default is plan-only (no network).
Network reachability requires explicit confirm token and injectable fetcher (tests use fakes).

Does not authorize futures execute, orders, scheduler, live, preflight lift, or credentials.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Mapping, Protocol, Sequence
from urllib import error, request
from urllib.parse import urlparse

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    write_manifest_sha256,
)
from src.ops.bounded_futures_testnet_adapter_contract_v0 import (
    DEFAULT_FUTURES_TESTNET_NETWORK_HOST,
)
from src.ops.bounded_futures_private_readonly_contract_v0 import (
    CONFIRM_TOKEN_PRIVATE_READONLY_REACHABILITY,
    DEMO_FUTURES_REST_BASE_URL,
    FUTURES_PRIVATE_READONLY_GET_ENDPOINTS,
    PRIVATE_READONLY_MODE,
    assert_private_readonly_authority_unchanged,
    build_private_readonly_plan_evidence_skeleton,
)
from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_INSTRUMENT,
    DEFAULT_MARGIN_MODE,
    DEFAULT_MARKET_TYPE,
    DEFAULT_ORDER_POLICY,
    DEFAULT_POSITION_MODE,
    DEFAULT_SESSION_CLASS,
    EVIDENCE_SOURCE_FUTURES_HARNESS,
    FUTURES_SESSION_AUTHORIZED_NOW,
    REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS,
    default_bounded_futures_private_readonly_reachability_v0_spec,
    default_bounded_futures_zero_order_reachability_v0_spec,
    evaluate_bounded_futures_testnet_evidence,
)
from src.ops.bounded_futures_testnet_runtime_harness_contract_v0 import (
    ARCHIVE_HARNESS_SCRIPT_EXECUTE_AUTHORIZED_NOW,
    ARCHIVE_HARNESS_SCRIPT_PRESENT,
    ARCHIVE_HARNESS_SCRIPT_REL_PATH,
    RUNTIME_HARNESS_EXECUTE_ALLOWED,
    RUNTIME_HARNESS_NETWORK_ALLOWED,
)

PACKAGE_MARKER = "ARCHIVE_FUTURES_TESTNET_HARNESS_V0=true"
SAFE_PUBLIC_URLLIB_FETCHER_PRESENT = True
HARNESS_VERSION = "archive_futures_testnet_harness_v0"

DEFAULT_MODE = "zero_order_reachability_only"
DEFAULT_FUTURES_SYMBOL = DEFAULT_INSTRUMENT
DEFAULT_REST_BASE_URL = f"{DEFAULT_FUTURES_TESTNET_NETWORK_HOST}/derivatives/api/v3"
DEFAULT_EXCHANGE = "kraken_futures_demo"
DEFAULT_MARKET_TYPE_LABEL = DEFAULT_MARKET_TYPE
DEFAULT_ORDER_CAP = 0
DEFAULT_VALIDATE_ONLY_ORDER_CAP = 0
DEFAULT_DURATION_CAP_SECONDS = 300

CONFIRM_TOKEN_ZERO_ORDER_REACHABILITY = (
    "I_ACCEPT_ARCHIVE_FUTURES_ZERO_ORDER_REACHABILITY_MANUAL_EXECUTE"
)

# Zero-order public GET allowlist only (no sendorder/cancel/private).
ZERO_ORDER_PUBLIC_ENDPOINTS: frozenset[str] = frozenset(
    {
        "/derivatives/api/v3/tickers",
        "/derivatives/api/v3/instruments",
    }
)
ZERO_ORDER_PUBLIC_ENDPOINT_ORDER: tuple[str, ...] = (
    "/derivatives/api/v3/tickers",
    "/derivatives/api/v3/instruments",
)

DEFAULT_PUBLIC_GET_TIMEOUT_SECONDS = 10.0

SymbolVisibility = Literal[
    "visible",
    "not_visible",
    "not_checked",
    "response_unparseable",
]

FORBIDDEN_SPOT_ENTRYPOINT_SUBSTRINGS: tuple[str, ...] = (
    "run_testnet_session",
    "run_execution_session",
    "orchestrate_testnet_runs",
    "run_bounded_pilot_session",
    "run_scheduler.py",
)

FORBIDDEN_HOST_PREFIXES: frozenset[str] = frozenset(
    {
        "https://api.kraken.com",
        "https://futures.kraken.com",
    }
)

_SAFE_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

USAGE_EXIT = 2


class PublicRestFetcher(Protocol):
    def fetch(self, url: str, *, timeout_seconds: float) -> tuple[int, bytes]:
        """Return HTTP status and body bytes."""


@dataclass(frozen=True)
class NetworkCallRecord:
    endpoint: str
    http_status: int
    http_status_class: str
    response_size_bytes: int
    response_sha256: str


@dataclass(frozen=True)
class NetworkReachabilityResult:
    endpoints_called: list[str]
    request_count: int
    network_calls: list[NetworkCallRecord]
    pf_xbtusd_symbol_visibility: SymbolVisibility
    network_reachability_proven: bool


class SafePublicUrllibRestFetcher:
    """Bounded stdlib urllib public GET client (demo futures allowlist only)."""

    def __init__(self, rest_base_url: str) -> None:
        self._rest_base_url = rest_base_url

    def fetch(self, url: str, *, timeout_seconds: float) -> tuple[int, bytes]:
        _assert_network_url_allowed(url, self._rest_base_url)
        bounded_timeout = min(
            float(timeout_seconds),
            DEFAULT_PUBLIC_GET_TIMEOUT_SECONDS,
            float(DEFAULT_DURATION_CAP_SECONDS),
        )
        req = request.Request(url, method="GET")
        try:
            with request.urlopen(req, timeout=bounded_timeout) as resp:
                status = int(getattr(resp, "status", resp.getcode()))
                return status, resp.read()
        except error.HTTPError as exc:
            return int(exc.code), exc.read() or b""


def default_safe_public_rest_fetcher(rest_base_url: str) -> SafePublicUrllibRestFetcher:
    return SafePublicUrllibRestFetcher(rest_base_url)


@dataclass(frozen=True)
class HarnessPlan:
    harness_version: str
    mode: str
    instrument: str
    rest_base_url: str
    exchange: str
    market_type: str
    order_cap: int
    validate_only_order_cap: int
    duration_cap_seconds: int
    archive_root: str
    run_id: str
    network_enabled: bool
    scheduler_enabled: bool
    background_enabled: bool
    spot_lane_forbidden: bool


@dataclass(frozen=True)
class HarnessTiming:
    monotonic_start: float
    monotonic_end: float
    wall_clock_start_utc: str
    wall_clock_end_utc: str

    @property
    def monotonic_elapsed_seconds(self) -> float:
        return max(0.0, self.monotonic_end - self.monotonic_start)

    @property
    def wall_clock_elapsed_seconds(self) -> float:
        start = datetime.fromisoformat(self.wall_clock_start_utc.replace("Z", "+00:00"))
        end = datetime.fromisoformat(self.wall_clock_end_utc.replace("Z", "+00:00"))
        return max(0.0, (end - start).total_seconds())


def _die(msg: str, code: int = USAGE_EXIT) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _require_safe_run_id(run_id: str) -> None:
    if not run_id.strip() or run_id != run_id.strip():
        _die("ERR: run-id must be non-empty trimmed")
    if _SAFE_RUN_ID_RE.match(run_id) is None:
        _die("ERR: run-id must match ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _rest_base_url_fail_reason(rest_base: str) -> str | None:
    parsed = urlparse(rest_base)
    if parsed.scheme != "https":
        return "rest_base_url must use https"
    if parsed.netloc != "demo-futures.kraken.com":
        return "rest_base_url host must be demo-futures.kraken.com"
    path = (parsed.path or "").rstrip("/")
    if path != "/derivatives/api/v3":
        return "rest_base_url path must be /derivatives/api/v3"
    return None


def _reject_spot_lane_flags(args: argparse.Namespace) -> None:
    if getattr(args, "use_spot_testnet_session", False):
        _die("ERR: spot testnet session lane forbidden for futures harness")
    for frag in FORBIDDEN_SPOT_ENTRYPOINT_SUBSTRINGS:
        if frag in str(getattr(args, "delegated_entrypoint", "") or ""):
            _die(f"ERR: forbidden spot entrypoint reference: {frag}")


def _validate_private_readonly_harness_namespace(
    args: argparse.Namespace,
    *,
    environ: Mapping[str, str] | None = None,
) -> list[str]:
    """Fail-closed validation for private_readonly_reachability_only (plan-only v0)."""
    reasons: list[str] = []
    env = environ if environ is not None else {}
    assert_private_readonly_authority_unchanged()

    if args.mode != PRIVATE_READONLY_MODE:
        reasons.append(f"mode must be {PRIVATE_READONLY_MODE!r}")
    if args.instrument in REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS:
        reasons.append(f"instrument {args.instrument!r} is rejected placeholder")
    if args.instrument != DEFAULT_FUTURES_SYMBOL:
        reasons.append(f"instrument must default to {DEFAULT_FUTURES_SYMBOL!r}")
    if args.order_cap != DEFAULT_ORDER_CAP or args.order_cap < 0:
        reasons.append("order_cap must be 0")
    if args.validate_only_order_cap != DEFAULT_VALIDATE_ONLY_ORDER_CAP:
        reasons.append("validate_only_order_cap must be 0")
    if args.duration_cap_seconds > DEFAULT_DURATION_CAP_SECONDS or args.duration_cap_seconds <= 0:
        reasons.append("duration_cap_seconds must be in (0, 300]")
    url_reason = _rest_base_url_fail_reason(args.rest_base_url)
    if url_reason:
        reasons.append(url_reason)
    if args.scheduler_enabled or args.background_enabled:
        reasons.append("scheduler/background must be disabled")
    if args.allow_unbounded:
        reasons.append("unbounded loops forbidden")
    if args.execute_network:
        reasons.append("execute-network forbidden for private_readonly mode in v0")

    for key in (
        "FUTURES_EXECUTE_AUTHORIZED",
        "FUTURES_PRIVATE_API_AUTHORIZED",
        "FUTURES_SESSION_AUTHORIZED_NOW",
        "NEXT_EXECUTE_ALLOWED",
        "READY_FOR_OPERATOR_ARMING",
    ):
        if env.get(key, "").lower() in ("1", "true", "yes"):
            reasons.append(f"{key} must not be true in environment")

    _reject_spot_lane_flags(args)
    return reasons


def validate_harness_namespace(
    args: argparse.Namespace,
    *,
    environ: Mapping[str, str] | None = None,
) -> list[str]:
    """Fail-closed validation; returns fail reasons (empty = pass)."""
    if args.mode == PRIVATE_READONLY_MODE:
        return _validate_private_readonly_harness_namespace(args, environ=environ)

    reasons: list[str] = []
    env = environ if environ is not None else {}

    if args.mode != DEFAULT_MODE:
        reasons.append(f"mode must be {DEFAULT_MODE!r}")
    if args.instrument in REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS:
        reasons.append(f"instrument {args.instrument!r} is rejected placeholder")
    if args.instrument != DEFAULT_FUTURES_SYMBOL:
        reasons.append(f"instrument must default to {DEFAULT_FUTURES_SYMBOL!r}")
    if args.order_cap != DEFAULT_ORDER_CAP or args.order_cap < 0:
        reasons.append("order_cap must be 0")
    if args.validate_only_order_cap != DEFAULT_VALIDATE_ONLY_ORDER_CAP:
        reasons.append("validate_only_order_cap must be 0")
    if args.duration_cap_seconds > DEFAULT_DURATION_CAP_SECONDS or args.duration_cap_seconds <= 0:
        reasons.append("duration_cap_seconds must be in (0, 300]")
    url_reason = _rest_base_url_fail_reason(args.rest_base_url)
    if url_reason:
        reasons.append(url_reason)
    if args.scheduler_enabled or args.background_enabled:
        reasons.append("scheduler/background must be disabled")
    if args.allow_unbounded:
        reasons.append("unbounded loops forbidden")

    for key in (
        "FUTURES_EXECUTE_AUTHORIZED",
        "FUTURES_SESSION_AUTHORIZED_NOW",
        "NEXT_EXECUTE_ALLOWED",
        "READY_FOR_OPERATOR_ARMING",
    ):
        if env.get(key, "").lower() in ("1", "true", "yes"):
            reasons.append(f"{key} must not be true in environment")

    _reject_spot_lane_flags(args)
    return reasons


def _http_status_class(status: int) -> str:
    if 200 <= status < 300:
        return "2xx"
    if 300 <= status < 400:
        return "3xx"
    if 400 <= status < 500:
        return "4xx"
    if 500 <= status < 600:
        return "5xx"
    return "other"


def _sha256_hex(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def classify_pf_xbtusd_symbol_visibility(
    body: bytes,
    *,
    endpoint: str,
) -> SymbolVisibility:
    if endpoint != "/derivatives/api/v3/tickers":
        return "not_checked"
    if not body:
        return "response_unparseable"
    try:
        payload = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return "response_unparseable"
    tickers: Any = payload.get("tickers") if isinstance(payload, dict) else None
    if tickers is None and isinstance(payload, list):
        tickers = payload
    if not isinstance(tickers, list):
        return "response_unparseable"
    for entry in tickers:
        if isinstance(entry, dict) and entry.get("symbol") == DEFAULT_FUTURES_SYMBOL:
            return "visible"
    return "not_visible"


def build_zero_order_evidence_payload(
    *,
    timing: HarnessTiming,
    endpoints_called: Sequence[str],
    request_count: int,
    network_host: str,
    run_id: str,
    pe8_pass: bool,
    network_reachability_proven: bool = False,
    network_calls: Sequence[NetworkCallRecord] | None = None,
    pf_xbtusd_symbol_visibility: SymbolVisibility = "not_checked",
) -> dict[str, Any]:
    """Evidence fields aligned with PE-8 zero-order spec."""
    calls_payload = [
        {
            "endpoint": rec.endpoint,
            "http_status": rec.http_status,
            "http_status_class": rec.http_status_class,
            "response_size_bytes": rec.response_size_bytes,
            "response_sha256": rec.response_sha256,
        }
        for rec in (network_calls or [])
    ]
    return {
        "session_class": DEFAULT_SESSION_CLASS,
        "order_policy": DEFAULT_ORDER_POLICY,
        "instrument": DEFAULT_FUTURES_SYMBOL,
        "market_type": DEFAULT_MARKET_TYPE_LABEL,
        "margin_mode": DEFAULT_MARGIN_MODE,
        "max_leverage": 5.0,
        "leverage_within_cap": True,
        "position_mode": DEFAULT_POSITION_MODE,
        "order_side_semantics": "long",
        "reduce_only_supported": True,
        "order_attempt_count": 0,
        "real_orders_created_count": 0,
        "cancel_or_close_attempt_count": 0,
        "order_notional_eur": 0.0,
        "order_notional_within_cap": True,
        "position_flattened_by_end": True,
        "cancel_or_close_evidence_valid": True,
        "futures_endpoint_isolation_pass": True,
        "spot_endpoint_isolation_pass": True,
        "funding_risk_acknowledged": True,
        "liquidation_risk_acknowledged": True,
        "risk_killswitch_scope_active": True,
        "risk_killswitch_scope_pass": True,
        "master_v2_double_play_authority_used": False,
        "endpoints_called": list(endpoints_called),
        "network_host": network_host,
        "scheduler_started": False,
        "runtime_started": False,
        "live_env_present": False,
        "futures_session_authorized_now": False,
        "order_attempted": False,
        "order_created": False,
        "fills": 0,
        "positions_changed": False,
        "evidence_source": EVIDENCE_SOURCE_FUTURES_HARNESS,
        "harness_version": HARNESS_VERSION,
        "run_id": run_id,
        "monotonic_elapsed_seconds": timing.monotonic_elapsed_seconds,
        "wall_clock_elapsed_seconds": timing.wall_clock_elapsed_seconds,
        "wall_clock_start_utc": timing.wall_clock_start_utc,
        "wall_clock_end_utc": timing.wall_clock_end_utc,
        "request_count": request_count,
        "network_reachability_proven": network_reachability_proven,
        "network_calls": calls_payload,
        "pf_xbtusd_symbol_visibility": pf_xbtusd_symbol_visibility,
        "network_target_allowlist": sorted(ZERO_ORDER_PUBLIC_ENDPOINTS),
        "manifest_verification_expected": True,
        "bounded_futures_testnet_pass": pe8_pass,
    }


def build_private_readonly_evidence_payload(
    *,
    timing: HarnessTiming,
    run_id: str,
    pe8_pass: bool,
) -> dict[str, Any]:
    """Plan-only private-readonly evidence (no network, no credential values)."""
    evidence = build_private_readonly_plan_evidence_skeleton(run_id=run_id)
    evidence.update(
        {
            "harness_version": HARNESS_VERSION,
            "monotonic_elapsed_seconds": timing.monotonic_elapsed_seconds,
            "wall_clock_elapsed_seconds": timing.wall_clock_elapsed_seconds,
            "wall_clock_start_utc": timing.wall_clock_start_utc,
            "wall_clock_end_utc": timing.wall_clock_end_utc,
            "bounded_futures_testnet_pass": pe8_pass,
            "network_target_allowlist": sorted(FUTURES_PRIVATE_READONLY_GET_ENDPOINTS),
            "rest_base_url": DEMO_FUTURES_REST_BASE_URL,
            "private_readonly_execute_wired": False,
            "confirm_token_reserved": CONFIRM_TOKEN_PRIVATE_READONLY_REACHABILITY,
        }
    )
    return evidence


def _assert_network_url_allowed(url: str, rest_base: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "demo-futures.kraken.com":
        _die(f"ERR: network host not allowlisted: {url}")
    for prefix in FORBIDDEN_HOST_PREFIXES:
        if url.startswith(prefix):
            _die(f"ERR: forbidden host prefix: {prefix}")
    path = parsed.path or ""
    if path not in ZERO_ORDER_PUBLIC_ENDPOINTS:
        _die(f"ERR: endpoint not in zero-order allowlist: {path}")
    if not url.startswith(rest_base.rstrip("/")):
        _die("ERR: url must be under rest-base-url")


def run_zero_order_public_reachability(
    *,
    rest_base_url: str,
    duration_cap_seconds: int,
    fetcher: PublicRestFetcher,
) -> NetworkReachabilityResult:
    endpoints_called: list[str] = []
    network_calls: list[NetworkCallRecord] = []
    symbol_visibility: SymbolVisibility = "not_checked"
    deadline = time.monotonic() + float(duration_cap_seconds)
    for ep in ZERO_ORDER_PUBLIC_ENDPOINT_ORDER:
        if ep not in ZERO_ORDER_PUBLIC_ENDPOINTS:
            continue
        if time.monotonic() > deadline:
            break
        suffix = ep.split("/derivatives/api/v3", 1)[-1]
        url = f"{rest_base_url.rstrip('/')}{suffix}"
        _assert_network_url_allowed(url, rest_base_url)
        status, body = fetcher.fetch(
            url,
            timeout_seconds=min(DEFAULT_PUBLIC_GET_TIMEOUT_SECONDS, duration_cap_seconds),
        )
        visibility = classify_pf_xbtusd_symbol_visibility(body, endpoint=ep)
        if visibility != "not_checked":
            symbol_visibility = visibility
        network_calls.append(
            NetworkCallRecord(
                endpoint=ep,
                http_status=status,
                http_status_class=_http_status_class(status),
                response_size_bytes=len(body),
                response_sha256=_sha256_hex(body),
            )
        )
        endpoints_called.append(ep)
    request_count = len(endpoints_called)
    proven = request_count > 0 and all(200 <= rec.http_status < 300 for rec in network_calls)
    return NetworkReachabilityResult(
        endpoints_called=endpoints_called,
        request_count=request_count,
        network_calls=network_calls,
        pf_xbtusd_symbol_visibility=symbol_visibility,
        network_reachability_proven=proven,
    )


def write_durable_evidence_bundle(
    *,
    archive_root: Path,
    run_id: str,
    plan: HarnessPlan,
    timing: HarnessTiming,
    evidence: dict[str, Any],
    evaluation: dict[str, Any],
) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    runtime_prefix = (
        "bounded_futures_private_readonly"
        if plan.mode == PRIVATE_READONLY_MODE
        else "bounded_futures_zero_order"
    )
    out = archive_root / "runtime" / f"{runtime_prefix}_{run_id}_{ts}"
    if is_under_tmp(out):
        _die("ERR: evidence root must not be under /tmp")
    out.mkdir(parents=True, exist_ok=True)
    (out / "HARNESS_PLAN.json").write_text(
        json.dumps(asdict(plan), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / "FUTURES_EVIDENCE.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / "PE8_EVALUATION.json").write_text(
        json.dumps(evaluation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / "AUTHORITY_BOUNDARY.env").write_text(
        "\n".join(
            [
                "FUTURES_EXECUTE_AUTHORIZED=false",
                "FUTURES_SESSION_AUTHORIZED_NOW=false",
                "NEXT_EXECUTE_ALLOWED=false",
                "LIVE_NOT_AUTHORIZED=true",
                "PREFLIGHT_REMAINS_BLOCKED=true",
                "READY_FOR_OPERATOR_ARMING=false",
                "RUNTIME_HARNESS_EXECUTE_ALLOWED=false",
                "ARCHIVE_HARNESS_SCRIPT_EXECUTE_AUTHORIZED_NOW=false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_manifest_sha256(out)
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Governed bounded futures testnet archive harness (zero-order v0).",
    )
    parser.add_argument(
        "--mode",
        default=DEFAULT_MODE,
        choices=[DEFAULT_MODE, PRIVATE_READONLY_MODE],
        help="Run mode: zero-order public or private-readonly plan-only (v0).",
    )
    parser.add_argument("--instrument", default=DEFAULT_FUTURES_SYMBOL)
    parser.add_argument("--rest-base-url", default=DEFAULT_REST_BASE_URL)
    parser.add_argument("--exchange", default=DEFAULT_EXCHANGE)
    parser.add_argument("--market-type", default=DEFAULT_MARKET_TYPE_LABEL)
    parser.add_argument("--order-cap", type=int, default=DEFAULT_ORDER_CAP)
    parser.add_argument(
        "--validate-only-order-cap",
        type=int,
        default=DEFAULT_VALIDATE_ONLY_ORDER_CAP,
    )
    parser.add_argument(
        "--duration-cap-seconds",
        type=int,
        default=DEFAULT_DURATION_CAP_SECONDS,
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="Durable primary evidence root (must not be /tmp-only).",
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--execute-network",
        action="store_true",
        help="Allow allowlisted public GET after confirm token (default: plan-only, no network).",
    )
    parser.add_argument(
        "--confirm-futures-zero-order-reachability",
        default="",
        help="Required exact token when --execute-network is set.",
    )
    parser.add_argument(
        "--confirm-futures-private-readonly-reachability",
        default="",
        help="Reserved for future private-readonly execute (not wired in v0).",
    )
    parser.add_argument("--scheduler-enabled", action="store_true")
    parser.add_argument("--background-enabled", action="store_true")
    parser.add_argument("--allow-unbounded", action="store_true")
    parser.add_argument(
        "--use-spot-testnet-session",
        action="store_true",
        help="Fail-closed: must remain false.",
    )
    parser.add_argument("--delegated-entrypoint", default="")
    return parser


def main(argv: list[str] | None = None, *, fetcher: PublicRestFetcher | None = None) -> int:
    if FUTURES_SESSION_AUTHORIZED_NOW:
        _die("ERR: FUTURES_SESSION_AUTHORIZED_NOW must be false")
    if RUNTIME_HARNESS_EXECUTE_ALLOWED or RUNTIME_HARNESS_NETWORK_ALLOWED:
        _die("ERR: runtime harness execute/network flags must be false")
    if ARCHIVE_HARNESS_SCRIPT_EXECUTE_AUTHORIZED_NOW:
        _die("ERR: archive harness script execute must remain false at module level")

    parser = build_parser()
    args = parser.parse_args(argv)
    _require_safe_run_id(args.run_id)

    fail_reasons = validate_harness_namespace(args)
    if fail_reasons:
        for r in fail_reasons:
            print(f"ERR: {r}", file=sys.stderr)
        return USAGE_EXIT

    archive_root = args.archive_root.resolve()
    if is_under_tmp(archive_root):
        _die("ERR: --archive-root must not be under /tmp")

    plan = HarnessPlan(
        harness_version=HARNESS_VERSION,
        mode=args.mode,
        instrument=args.instrument,
        rest_base_url=args.rest_base_url,
        exchange=args.exchange,
        market_type=args.market_type,
        order_cap=args.order_cap,
        validate_only_order_cap=args.validate_only_order_cap,
        duration_cap_seconds=args.duration_cap_seconds,
        archive_root=str(archive_root),
        run_id=args.run_id,
        network_enabled=False,
        scheduler_enabled=args.scheduler_enabled,
        background_enabled=args.background_enabled,
        spot_lane_forbidden=True,
    )

    mono_start = time.monotonic()
    wall_start = _utc_now_z()

    endpoints_called: list[str] = []
    request_count = 0

    network_result: NetworkReachabilityResult | None = None
    if args.execute_network:
        if args.confirm_futures_zero_order_reachability != CONFIRM_TOKEN_ZERO_ORDER_REACHABILITY:
            _die("ERR: missing or invalid --confirm-futures-zero-order-reachability token")
        active_fetcher: PublicRestFetcher = (
            fetcher if fetcher is not None else default_safe_public_rest_fetcher(args.rest_base_url)
        )
        network_result = run_zero_order_public_reachability(
            rest_base_url=args.rest_base_url,
            duration_cap_seconds=args.duration_cap_seconds,
            fetcher=active_fetcher,
        )
        endpoints_called = network_result.endpoints_called
        request_count = network_result.request_count
        plan = HarnessPlan(**{**asdict(plan), "network_enabled": True})

    mono_end = time.monotonic()
    wall_end = _utc_now_z()
    timing = HarnessTiming(
        monotonic_start=mono_start,
        monotonic_end=mono_end,
        wall_clock_start_utc=wall_start,
        wall_clock_end_utc=wall_end,
    )

    if args.mode == PRIVATE_READONLY_MODE:
        spec = default_bounded_futures_private_readonly_reachability_v0_spec()
        evidence = build_private_readonly_evidence_payload(
            timing=timing,
            run_id=args.run_id,
            pe8_pass=False,
        )
    else:
        spec = default_bounded_futures_zero_order_reachability_v0_spec()
        evidence = build_zero_order_evidence_payload(
            timing=timing,
            endpoints_called=endpoints_called,
            request_count=request_count,
            network_host=DEFAULT_FUTURES_TESTNET_NETWORK_HOST,
            run_id=args.run_id,
            pe8_pass=False,
            network_reachability_proven=(
                network_result.network_reachability_proven if network_result else False
            ),
            network_calls=network_result.network_calls if network_result else None,
            pf_xbtusd_symbol_visibility=(
                network_result.pf_xbtusd_symbol_visibility if network_result else "not_checked"
            ),
        )
    evaluation = evaluate_bounded_futures_testnet_evidence(evidence, spec=spec)
    evidence["bounded_futures_testnet_pass"] = evaluation["bounded_futures_testnet_pass"]
    if not evaluation["bounded_futures_testnet_pass"]:
        print(json.dumps(evaluation, indent=2), file=sys.stderr)
        return USAGE_EXIT

    out = write_durable_evidence_bundle(
        archive_root=archive_root,
        run_id=args.run_id,
        plan=plan,
        timing=timing,
        evidence=evidence,
        evaluation=evaluation,
    )
    plan_only = not args.execute_network or args.mode == PRIVATE_READONLY_MODE
    print(
        json.dumps(
            {"evidence_dir": str(out), "plan_only": plan_only, "mode": args.mode},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
