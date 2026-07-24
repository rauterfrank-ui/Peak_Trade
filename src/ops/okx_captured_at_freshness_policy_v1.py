"""Ratified OKX capture-clock and freshness policy owner."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "OKX_CAPTURED_AT_FRESHNESS_POLICY_V1=true"
POLICY_RATIFICATION_ID = "okx_captured_at_freshness_policy_ratification_v1"
CONFIG_RELATIVE_PATH = "config/ops/okx_captured_at_freshness_policy_ratification_v1.json"

DEFAULT_THRESHOLDS_SECONDS = {
    "instrument_metadata": 86400,
    "reference_mark_price": 120,
    "ohlcv_latest_candle": 7200,
    "universe_selection": 86400,
    "dashboard_aggregate": 86400,
}


class OkxCapturedAtFreshnessPolicyError(ValueError):
    """Fail-closed freshness / capture-clock policy error."""


@dataclass(frozen=True)
class OkxCaptureClocksV1:
    capture_started_at: str
    response_received_at: str
    provider_timestamp: str | None
    captured_at: str
    effective_at: str | None

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_utc_iso(value: str) -> datetime:
    raw = str(value or "").strip()
    if not raw:
        raise OkxCapturedAtFreshnessPolicyError("EMPTY_TIMESTAMP")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        raise OkxCapturedAtFreshnessPolicyError("TIMESTAMP_MUST_BE_AWARE_UTC")
    return dt.astimezone(timezone.utc)


def provider_ms_to_utc_iso(value: Any) -> str | None:
    if value is None or value == "":
        return None
    text = str(value).strip()
    if not text.isdigit():
        return None
    ms = int(text)
    if ms <= 0:
        return None
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_freshness_policy_v1(*, repo_root: Path | None = None) -> Mapping[str, Any]:
    root = repo_root or _repo_root()
    path = root / CONFIG_RELATIVE_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise OkxCapturedAtFreshnessPolicyError("policy config must be object")
    if data.get("schema_id") != POLICY_RATIFICATION_ID:
        raise OkxCapturedAtFreshnessPolicyError("policy schema_id mismatch")
    if data.get("OKX_CAPTURED_AT_MAPPING_AUTHORIZED") is not True:
        raise OkxCapturedAtFreshnessPolicyError("captured_at mapping not authorized")
    return data


def build_okx_capture_clocks_v1(
    *,
    capture_started_at: str,
    response_received_at: str,
    provider_timestamp: str | None,
) -> OkxCaptureClocksV1:
    """captured_at := response_received_at; effective_at := provider_timestamp when valid."""
    # Validate clocks are parseable UTC ISO-8601.
    parse_utc_iso(capture_started_at)
    parse_utc_iso(response_received_at)
    effective = None
    if provider_timestamp:
        parse_utc_iso(provider_timestamp)
        effective = provider_timestamp
    return OkxCaptureClocksV1(
        capture_started_at=capture_started_at,
        response_received_at=response_received_at,
        provider_timestamp=provider_timestamp,
        captured_at=response_received_at,
        effective_at=effective,
    )


def freshness_threshold_seconds(
    source_type: str, *, policy: Mapping[str, Any] | None = None
) -> int:
    thresholds = dict(DEFAULT_THRESHOLDS_SECONDS)
    if policy is not None:
        raw = policy.get("freshness_thresholds_seconds") or {}
        if isinstance(raw, Mapping):
            for key, value in raw.items():
                thresholds[str(key)] = int(value)
    if source_type not in thresholds:
        raise OkxCapturedAtFreshnessPolicyError(f"UNKNOWN_SOURCE_TYPE:{source_type}")
    return int(thresholds[source_type])


def classify_freshness_v1(
    *,
    reference_at: str,
    as_of: str,
    source_type: str,
    policy: Mapping[str, Any] | None = None,
) -> tuple[str, bool, str | None]:
    """Return (freshness_state, is_stale, stale_reason)."""
    max_age = freshness_threshold_seconds(source_type, policy=policy)
    ref = parse_utc_iso(reference_at)
    now = parse_utc_iso(as_of)
    age = (now - ref).total_seconds()
    if age < 0:
        return "invalid", True, "CAPTURE_TIMESTAMP_IN_FUTURE"
    if age > max_age:
        return "stale", True, f"STALE_OVER_MAX_AGE_SECONDS:{max_age}"
    return "fresh", False, None
