"""Sealed production-lifecycle binding and long-panel inclusion for chrono PIT v1.

Research-only. Reuses the existing pit_futures production lifecycle registry SSOT.
Does not invent listing/delisting times. Does not authorize trading or economics.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.longer_chronological_pit_acquisition_v1 import (
    DATASET_ID,
    FREQUENCY,
    MARKET_TYPE,
    TARGET_PERIOD_END,
    TARGET_PERIOD_START,
    VENUE,
)
from src.research.okx_production_instrument_lifecycle_source_v1 import (
    SOURCE_ID as PRODUCTION_LIFECYCLE_SOURCE_ID,
    is_forbidden_okx_instrument_token,
)
from src.research.pit_futures_instrument_lifecycle_registry_persistence_v1 import (
    parse_registry_snapshot_dict_v1,
    read_registry_snapshot_v1,
)
from src.research.pit_futures_instrument_lifecycle_registry_validator_v1 import (
    ValidationVerdict,
    validate_pit_futures_instrument_lifecycle_registry_snapshot_v1,
)

PACKAGE_MARKER = "LONGER_CHRONOLOGICAL_PIT_SEALED_LIFECYCLE_V1=true"
SEALED_SCHEMA_VERSION = "longer_chronological_pit_sealed_lifecycle_manifest.v1"
INCLUSION_POLICY_VERSION = "longer_chronological_pit_sealed_lifecycle_inclusion_policy.v1"
MIN_HISTORY_DAYS_POLICY = 365
RELIST_GAP_HOURS = 168  # 7d — public earliest materially after listing ⇒ discontinuity
SAMPLE_UNIVERSE_TRUTH_MARKER = "scaffold_lifecycle_policy_sample_not_production_manifest"
SEAL_HASH_EXCLUDED_KEYS = frozenset(
    {
        "content_hash",
        "sealed",
        "blockers",
        "requests_used",
        "request_budget",
        "live_eligible_instrument_count",
        "written_artifacts",
        "archive_root",
    }
)
DEFAULT_PRODUCTION_REGISTRY_REL = (
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/"
    "extended_chronological_v1/lifecycle"
)


class InclusionDecision(str, Enum):
    INCLUDE_LONG_PANEL = "INCLUDE_LONG_PANEL"
    EXCLUDE_LONG_PANEL = "EXCLUDE_LONG_PANEL"
    REJECT_INSTRUMENT = "REJECT_INSTRUMENT"


class SealedLifecycleError(RuntimeError):
    """Fail-closed sealed lifecycle error."""


def _parse_utc(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stable_hash(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _days_between(start: str, end: str) -> float:
    return (_parse_utc(end) - _parse_utc(start)).total_seconds() / 86400.0


@dataclass(frozen=True)
class SealedInstrumentLifecycleRecordV1:
    canonical_instrument_id: str
    exchange: str
    inst_type: str
    settle_currency: str
    underlying_base: str
    native_instrument_id: str
    listing_timestamp: str
    delisting_timestamp: str | None
    first_public_candle_timestamp: str | None
    last_public_candle_timestamp: str | None
    relist_or_replacement_flag: bool
    predecessor_ids: tuple[str, ...]
    successor_ids: tuple[str, ...]
    lifecycle_source: str
    lifecycle_observed_at: str
    inclusion_policy_version: str
    inclusion_decision: str
    exclusion_reason: str | None
    production_interval_digest: str
    record_fingerprint: str


def compute_record_fingerprint(record: Mapping[str, Any]) -> str:
    body = {k: v for k, v in record.items() if k != "record_fingerprint"}
    return _stable_hash(body)


def assert_not_sample_universe(universe_truth: str | None) -> None:
    if universe_truth == SAMPLE_UNIVERSE_TRUTH_MARKER:
        raise SealedLifecycleError("SAMPLE_UNIVERSE_CANNOT_BE_EMITTED_AS_PRODUCTION_MANIFEST")
    if (
        universe_truth
        and "sample" in universe_truth.lower()
        and "production" not in universe_truth.lower()
    ):
        raise SealedLifecycleError(f"NON_PRODUCTION_UNIVERSE_TRUTH:{universe_truth}")


def assert_instrument_not_btc_or_spot(
    *,
    native_instrument_id: str,
    base_asset: str,
    market_type: str | None = None,
) -> None:
    if is_forbidden_okx_instrument_token(native_instrument_id, base_asset):
        raise SealedLifecycleError(f"BTC_OR_FORBIDDEN_REJECTED:{native_instrument_id}")
    if base_asset.upper() in {"BTC", "XBT", "WBTC", "TBTC", "RBTC", "BTCB"}:
        raise SealedLifecycleError(f"BTC_REJECTED:{native_instrument_id}")
    mt = (market_type or "").lower()
    if mt == "spot" or (
        native_instrument_id.upper().endswith("-USDT")
        and "SWAP" not in native_instrument_id.upper()
        and "FUTURES" not in native_instrument_id.upper()
    ):
        raise SealedLifecycleError(f"SPOT_REJECTED:{native_instrument_id}")


def evaluate_inclusion_v1(
    *,
    listing_timestamp: str | None,
    delisting_timestamp: str | None,
    first_public_candle_timestamp: str | None,
    last_public_candle_timestamp: str | None,
    panel_start: str = TARGET_PERIOD_START,
    panel_end: str = TARGET_PERIOD_END,
    min_history_days: int = MIN_HISTORY_DAYS_POLICY,
    relist_gap_hours: int = RELIST_GAP_HOURS,
    native_instrument_id: str = "",
) -> tuple[InclusionDecision, str | None, bool]:
    """Deterministic long-panel inclusion. Returns (decision, reason, relist_flag)."""
    if not listing_timestamp:
        return InclusionDecision.REJECT_INSTRUMENT, "MISSING_LISTING_TIMESTAMP", False
    if not first_public_candle_timestamp or not last_public_candle_timestamp:
        return (
            InclusionDecision.EXCLUDE_LONG_PANEL,
            "MISSING_PUBLIC_CANDLE_BOUNDARIES",
            False,
        )

    listing = _parse_utc(listing_timestamp)
    first_pub = _parse_utc(first_public_candle_timestamp)
    last_pub = _parse_utc(last_public_candle_timestamp)
    p_start = _parse_utc(panel_start)
    p_end = _parse_utc(panel_end)

    # Effective usable start: never before listing or first public candle
    effective_start = max(listing, first_pub, p_start)
    effective_end = min(last_pub, p_end)
    if delisting_timestamp:
        effective_end = min(effective_end, _parse_utc(delisting_timestamp))

    relist = False
    gap_hours = (first_pub - listing).total_seconds() / 3600.0
    # Material gap after listing is a discontinuity candidate, but only becomes a
    # relist/replacement edge when the usable research window collapses.
    discontinuity_candidate = gap_hours > float(relist_gap_hours)

    # Pre-listing candles beyond 1h bar skew are not accepted for panel use
    if (listing - first_pub).total_seconds() > 3600:
        return (
            InclusionDecision.EXCLUDE_LONG_PANEL,
            "PUBLIC_HISTORY_BEFORE_LISTING_NOT_ACCEPTED_FOR_PANEL",
            False,
        )

    if effective_end <= effective_start:
        if discontinuity_candidate:
            return (
                InclusionDecision.EXCLUDE_LONG_PANEL,
                f"RELIST_OR_PUBLIC_HISTORY_DISCONTINUITY:gap_hours={gap_hours:.1f}:empty_effective_window",
                True,
            )
        return InclusionDecision.EXCLUDE_LONG_PANEL, "EMPTY_EFFECTIVE_WINDOW", False

    history_days = (effective_end - effective_start).total_seconds() / 86400.0
    if history_days < float(min_history_days):
        if discontinuity_candidate:
            return (
                InclusionDecision.EXCLUDE_LONG_PANEL,
                (
                    f"RELIST_OR_PUBLIC_HISTORY_DISCONTINUITY:gap_hours={gap_hours:.1f}:"
                    f"below_min_history:{history_days:.2f}<{min_history_days}"
                ),
                True,
            )
        return (
            InclusionDecision.EXCLUDE_LONG_PANEL,
            f"BELOW_MIN_HISTORY_DAYS:{history_days:.2f}<{min_history_days}",
            False,
        )

    # Truncated public archive before listing is allowed if usable window is long enough;
    # do not invent candles before first_public (effective_start already clipped).
    _ = native_instrument_id
    return InclusionDecision.INCLUDE_LONG_PANEL, None, False


def load_production_registry_snapshot(
    *,
    registry_dir: Path,
    snapshot_name: str = "registry_snapshot_v1.json",
) -> dict[str, Any]:
    """Load and validator-gate the existing production lifecycle registry SSOT."""
    result = read_registry_snapshot_v1(root_dir=registry_dir, relative_path=snapshot_name)
    if not result.ok or result.snapshot is None:
        raise SealedLifecycleError(
            f"PRODUCTION_REGISTRY_LOAD_FAILED:{','.join(result.error_codes)}"
        )
    validation = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(result.snapshot)
    if validation.verdict != ValidationVerdict.ACCEPTED:
        raise SealedLifecycleError(
            f"PRODUCTION_REGISTRY_VALIDATION_FAILED:{','.join(validation.error_codes)}"
        )
    # Return dict form for sealing overlays (digest already on snapshot)
    from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
        registry_snapshot_to_dict,
    )

    payload = registry_snapshot_to_dict(result.snapshot, include_digest=True)
    digest = str(payload.get("registry_snapshot_digest") or "")
    if not digest:
        raise SealedLifecycleError("PRODUCTION_REGISTRY_MISSING_DIGEST")
    return payload


def load_production_registry_from_json_path(path: Path) -> dict[str, Any]:
    """Load registry JSON from an absolute external path (fail-closed validate)."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SealedLifecycleError("PRODUCTION_REGISTRY_NOT_OBJECT")
    snapshot, errors = parse_registry_snapshot_dict_v1(raw)
    if snapshot is None:
        raise SealedLifecycleError(f"PRODUCTION_REGISTRY_PARSE_FAILED:{','.join(errors)}")
    validation = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snapshot)
    if validation.verdict != ValidationVerdict.ACCEPTED:
        raise SealedLifecycleError(
            f"PRODUCTION_REGISTRY_VALIDATION_FAILED:{','.join(validation.error_codes)}"
        )
    return raw


def build_sealed_record_from_registry_interval(
    interval: Mapping[str, Any],
    *,
    first_public_candle_timestamp: str | None,
    last_public_candle_timestamp: str | None,
    lifecycle_observed_at: str,
    panel_start: str = TARGET_PERIOD_START,
    panel_end: str = TARGET_PERIOD_END,
    min_history_days: int = MIN_HISTORY_DAYS_POLICY,
) -> SealedInstrumentLifecycleRecordV1:
    native = str(interval.get("venue_symbol") or interval.get("native_instrument_id") or "")
    base = str(interval.get("base_asset") or "")
    assert_instrument_not_btc_or_spot(
        native_instrument_id=native,
        base_asset=base,
        market_type=str(interval.get("contract_type") or MARKET_TYPE),
    )
    listing = interval.get("listing_time") or interval.get("eligible_from")
    if not listing:
        raise SealedLifecycleError(f"MISSING_LIFECYCLE_LISTING:{native}")

    decision, reason, relist = evaluate_inclusion_v1(
        listing_timestamp=str(listing),
        delisting_timestamp=interval.get("delisting_time"),
        first_public_candle_timestamp=first_public_candle_timestamp,
        last_public_candle_timestamp=last_public_candle_timestamp,
        panel_start=panel_start,
        panel_end=panel_end,
        min_history_days=min_history_days,
        native_instrument_id=native,
    )
    draft = {
        "canonical_instrument_id": str(interval["instrument_id"]),
        "exchange": VENUE,
        "inst_type": "SWAP",
        "settle_currency": str(interval.get("settlement_asset") or "USDT"),
        "underlying_base": base,
        "native_instrument_id": native,
        "listing_timestamp": str(listing),
        "delisting_timestamp": interval.get("delisting_time"),
        "first_public_candle_timestamp": first_public_candle_timestamp,
        "last_public_candle_timestamp": last_public_candle_timestamp,
        "relist_or_replacement_flag": relist,
        "predecessor_ids": [],
        "successor_ids": [],
        "lifecycle_source": PRODUCTION_LIFECYCLE_SOURCE_ID,
        "lifecycle_observed_at": lifecycle_observed_at,
        "inclusion_policy_version": INCLUSION_POLICY_VERSION,
        "inclusion_decision": decision.value,
        "exclusion_reason": reason,
        "production_interval_digest": str(interval.get("record_digest") or ""),
    }
    fingerprint = compute_record_fingerprint(draft)
    return SealedInstrumentLifecycleRecordV1(
        canonical_instrument_id=draft["canonical_instrument_id"],
        exchange=draft["exchange"],
        inst_type=draft["inst_type"],
        settle_currency=draft["settle_currency"],
        underlying_base=draft["underlying_base"],
        native_instrument_id=draft["native_instrument_id"],
        listing_timestamp=draft["listing_timestamp"],
        delisting_timestamp=draft["delisting_timestamp"],
        first_public_candle_timestamp=draft["first_public_candle_timestamp"],
        last_public_candle_timestamp=draft["last_public_candle_timestamp"],
        relist_or_replacement_flag=draft["relist_or_replacement_flag"],
        predecessor_ids=tuple(draft["predecessor_ids"]),
        successor_ids=tuple(draft["successor_ids"]),
        lifecycle_source=draft["lifecycle_source"],
        lifecycle_observed_at=draft["lifecycle_observed_at"],
        inclusion_policy_version=draft["inclusion_policy_version"],
        inclusion_decision=draft["inclusion_decision"],
        exclusion_reason=draft["exclusion_reason"],
        production_interval_digest=draft["production_interval_digest"],
        record_fingerprint=fingerprint,
    )


def seal_lifecycle_manifest(
    records: Sequence[SealedInstrumentLifecycleRecordV1],
    *,
    production_registry_digest: str,
    production_registry_path: str,
    request_fingerprints: Sequence[Mapping[str, Any]],
    panel_start: str = TARGET_PERIOD_START,
    panel_end: str = TARGET_PERIOD_END,
    sealed_at: str | None = None,
    universe_truth: str = "production_lifecycle_registry_binding_v1",
) -> dict[str, Any]:
    assert_not_sample_universe(universe_truth)
    if not production_registry_digest:
        raise SealedLifecycleError("MISSING_PRODUCTION_REGISTRY_DIGEST")
    sealed_at = sealed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    sorted_records = sorted(
        records,
        key=lambda r: (r.native_instrument_id, r.canonical_instrument_id),
    )
    included = [
        r
        for r in sorted_records
        if r.inclusion_decision == InclusionDecision.INCLUDE_LONG_PANEL.value
    ]
    excluded = [
        r
        for r in sorted_records
        if r.inclusion_decision != InclusionDecision.INCLUDE_LONG_PANEL.value
    ]
    relist_edges = [r for r in sorted_records if r.relist_or_replacement_flag]

    # Common panel among included only
    common_start = None
    common_end = None
    if included:
        starts = []
        ends = []
        for r in included:
            assert r.first_public_candle_timestamp and r.last_public_candle_timestamp
            starts.append(
                max(
                    r.listing_timestamp,
                    r.first_public_candle_timestamp,
                    panel_start,
                )
            )
            end_cands = [r.last_public_candle_timestamp, panel_end]
            if r.delisting_timestamp:
                end_cands.append(r.delisting_timestamp)
            ends.append(min(end_cands))
        common_start = max(starts)
        common_end = min(ends)
        if _parse_utc(common_end) <= _parse_utc(common_start):
            common_start = None
            common_end = None

    duration_days = _days_between(common_start, common_end) if common_start and common_end else 0.0

    luna = next((r for r in sorted_records if r.underlying_base.upper() == "LUNA"), None)
    luna_decision = luna.inclusion_decision if luna else "NOT_PRESENT"
    luna_reason = luna.exclusion_reason if luna else None

    body = {
        "schema_version": SEALED_SCHEMA_VERSION,
        "dataset_id": DATASET_ID,
        "venue": VENUE,
        "market_type": MARKET_TYPE,
        "frequency": FREQUENCY,
        "btc_excluded": True,
        "spot_excluded": True,
        "economic_gate_opened": False,
        "promotion_eligible": False,
        "live_authorized": False,
        "orders": False,
        "inclusion_policy_version": INCLUSION_POLICY_VERSION,
        "min_history_days_policy": MIN_HISTORY_DAYS_POLICY,
        "relist_gap_hours": RELIST_GAP_HOURS,
        "panel_target_start": panel_start,
        "panel_target_end": panel_end,
        "production_lifecycle_source_id": PRODUCTION_LIFECYCLE_SOURCE_ID,
        "production_registry_digest": production_registry_digest,
        "production_registry_path": production_registry_path,
        "universe_truth": universe_truth,
        "sample_universe_replaced": True,
        "sealed_at": sealed_at,
        "sort_rules": [
            "native_instrument_id ASC",
            "canonical_instrument_id ASC",
        ],
        "instrument_count_discovered": len(sorted_records),
        "instrument_count_lifecycle_valid": sum(
            1
            for r in sorted_records
            if r.inclusion_decision != InclusionDecision.REJECT_INSTRUMENT.value
        ),
        "instrument_count_long_panel_included": len(included),
        "instrument_count_excluded": len(excluded),
        "relist_edge_count": len(relist_edges),
        "replacement_edge_count": 0,
        "luna_decision": luna_decision,
        "luna_decision_reason": luna_reason,
        "common_panel_start": common_start,
        "common_panel_end": common_end,
        "common_panel_duration_days": duration_days,
        "instruments": [asdict(r) for r in sorted_records],
        "long_panel_native_ids": [r.native_instrument_id for r in included],
        "excluded_summary": [
            {
                "native_instrument_id": r.native_instrument_id,
                "inclusion_decision": r.inclusion_decision,
                "exclusion_reason": r.exclusion_reason,
                "relist_or_replacement_flag": r.relist_or_replacement_flag,
            }
            for r in excluded
        ],
        "request_fingerprints": list(request_fingerprints),
        "reproduction": {
            "bind_production_registry": production_registry_path,
            "policy": INCLUSION_POLICY_VERSION,
            "commands": [
                "python -m src.research.longer_chronological_pit_acquisition_v1 seal-lifecycle",
                "python -m src.research.longer_chronological_pit_acquisition_v1 acquire-long-panel",
            ],
        },
    }
    content_hash = _stable_hash(body)
    body["content_hash"] = content_hash
    body["sealed"] = True
    return body


def sealed_manifest_hash_payload(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in manifest.items() if k not in SEAL_HASH_EXCLUDED_KEYS}


def verify_sealed_manifest(manifest: Mapping[str, Any]) -> str:
    """Recompute content hash; fail-closed on tamper or sample binding."""
    assert_not_sample_universe(str(manifest.get("universe_truth") or ""))
    if not manifest.get("sealed"):
        raise SealedLifecycleError("MANIFEST_NOT_SEALED")
    if not manifest.get("production_registry_digest"):
        raise SealedLifecycleError("MANIFEST_MISSING_PRODUCTION_DIGEST")
    if manifest.get("universe_truth") != "production_lifecycle_registry_binding_v1":
        raise SealedLifecycleError("MANIFEST_UNIVERSE_TRUTH_NOT_PRODUCTION_BINDING")
    digest = _stable_hash(sealed_manifest_hash_payload(manifest))
    expected = str(manifest.get("content_hash") or "")
    if digest != expected:
        raise SealedLifecycleError(f"SEAL_HASH_MISMATCH:expected={expected}:got={digest}")
    return digest


__all__ = [
    "INCLUSION_POLICY_VERSION",
    "InclusionDecision",
    "MIN_HISTORY_DAYS_POLICY",
    "PACKAGE_MARKER",
    "PRODUCTION_LIFECYCLE_SOURCE_ID",
    "RELIST_GAP_HOURS",
    "SEALED_SCHEMA_VERSION",
    "SAMPLE_UNIVERSE_TRUTH_MARKER",
    "SealedInstrumentLifecycleRecordV1",
    "SealedLifecycleError",
    "assert_instrument_not_btc_or_spot",
    "assert_not_sample_universe",
    "build_sealed_record_from_registry_interval",
    "compute_record_fingerprint",
    "evaluate_inclusion_v1",
    "load_production_registry_from_json_path",
    "load_production_registry_snapshot",
    "seal_lifecycle_manifest",
    "verify_sealed_manifest",
]
