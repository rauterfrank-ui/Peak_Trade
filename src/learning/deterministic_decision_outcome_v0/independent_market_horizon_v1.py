"""Versioned offline market request admission at the existing N_BARS supplier.

No DecisionEvent, DDO evaluation input, alternate price calculation or new outcome
owner. Exact local receipts prove integrity and availability, not venue authenticity.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from types import SimpleNamespace

from .o4_n_bars_bar_evidence_bridge_contracts_v1 import (
    _normalize_o4_interval_id,
    translate_o4_market_bar_chain_v1,
    derive_o4_instrument_ref_v1,
    derive_o4_bar_spec_ref_v1,
)
from .n_bars_bar_evidence_supplier_v1 import (
    _materialize_canonical_n_bars_measurement_v1,
    PRICE_BASIS_FINALIZED,
    PRICE_BASIS_CORRECTED,
)

REQUEST_SCHEMA = "independent_market_n_bars_request_v1"
OBSERVATION_SCHEMA = "independent_market_n_bars_observation_v1"
RUNTIME_REACHABLE = False
EXTERNAL_EFFECT_AUTHORIZED = False
IDENTITY_FIELDS = {"dataset_generation", "venue", "instrument_ref", "native_instrument_ref"}
REQUEST_FIELDS = {
    "schema_version",
    "market_identity",
    "horizon_start_time_utc",
    "n_bars",
    "o4_interval_id",
    "price_unit",
    "price_family",
    "source_kind",
    "max_end_age_seconds",
    "expected_price_basis_kind",
}
RECEIPT_FIELDS = {
    "source_ref",
    "dataset_generation",
    "original_bar_json",
    "original_bar_sha256",
    "known_at_utc",
    "available_at_utc",
    "source_kind",
    "price_unit",
    "price_family",
}


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _text(value, reason):
    _require(isinstance(value, str) and bool(value.strip()), reason)
    return value


def _instant(value):
    _text(value, "MARKET_UTC_REQUIRED")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    _require(
        result.utcoffset() is not None and result.utcoffset().total_seconds() == 0,
        "MARKET_UTC_REQUIRED",
    )
    return result.astimezone(timezone.utc)


def _bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _digest(value):
    return hashlib.sha256(_bytes(value)).hexdigest()


def _original(text):
    def pairs(items):
        _require(len(items) == len({k for k, _ in items}), "DUPLICATE_SOURCE_KEY")
        return dict(items)

    def constant(value):
        raise ValueError("NONFINITE_SOURCE_NUMBER")

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def validate_market_horizon_request_v1(request):
    _require(set(request) == REQUEST_FIELDS, "MARKET_REQUEST_FIELDS")
    _require(request["schema_version"] == REQUEST_SCHEMA, "MARKET_REQUEST_SCHEMA")
    identity = request["market_identity"]
    _require(set(identity) == IDENTITY_FIELDS, "MARKET_IDENTITY_FIELDS")
    for key in IDENTITY_FIELDS:
        _text(identity[key], "MARKET_IDENTITY_REQUIRED:" + key)
    count = request["n_bars"]
    _require(type(count) is int and count >= 2, "MARKET_RETURN_NEEDS_AT_LEAST_TWO_CLOSES")
    interval, seconds = _normalize_o4_interval_id(request["o4_interval_id"])
    start = _instant(request["horizon_start_time_utc"])
    _require(start.timestamp() % seconds == 0, "MARKET_EXACT_BAR_GRID_REQUIRED")
    _text(request["price_unit"], "MARKET_PRICE_UNIT_REQUIRED")
    _require(
        request["price_unit"].upper() not in {"UNKNOWN", "MIXED"},
        "MARKET_KNOWN_PRICE_UNIT_REQUIRED",
    )
    _require(request["price_family"] == "MARK_PRICE", "MARKET_O4_MARK_PRICE_ONLY")
    _require(
        request["source_kind"] in {"SYNTHETIC_OFFLINE", "RECORDED_PUBLIC_MD"},
        "MARKET_EXPLICIT_SOURCE_KIND_REQUIRED",
    )
    age = request["max_end_age_seconds"]
    _require(type(age) is int and age >= 0, "MARKET_FRESHNESS_POLICY_REQUIRED")
    _require(
        request["expected_price_basis_kind"] in {PRICE_BASIS_FINALIZED, PRICE_BASIS_CORRECTED},
        "MARKET_EXPLICIT_PRICE_BASIS_REQUIRED",
    )
    return identity, start, interval, seconds


def _materialize_market_horizon_v1(*, request, source_receipts, evaluated_at_utc):
    _require(
        RUNTIME_REACHABLE is False and EXTERNAL_EFFECT_AUTHORIZED is False, "MARKET_OFFLINE_ONLY"
    )
    identity, start, interval, seconds = validate_market_horizon_request_v1(request)
    evaluated = _instant(evaluated_at_utc)
    _require(
        isinstance(source_receipts, (list, tuple)) and len(source_receipts) == request["n_bars"],
        "MARKET_COMPLETE_SOURCE_RECEIPTS_REQUIRED",
    )
    bars = []
    source_refs = set()
    for receipt in source_receipts:
        _require(set(receipt) == RECEIPT_FIELDS, "MARKET_SOURCE_RECEIPT_FIELDS")
        ref = _text(receipt["source_ref"], "MARKET_SOURCE_REF_REQUIRED")
        _require(ref not in source_refs, "MARKET_DUPLICATE_SOURCE_REF")
        source_refs.add(ref)
        raw = _text(receipt["original_bar_json"], "MARKET_ORIGINAL_BAR_REQUIRED")
        _require(
            hashlib.sha256(raw.encode()).hexdigest() == receipt["original_bar_sha256"],
            "MARKET_ORIGINAL_SOURCE_BYTES_CHANGED",
        )
        _require(
            receipt["dataset_generation"] == identity["dataset_generation"],
            "MARKET_SOURCE_GENERATION_MISMATCH",
        )
        _require(receipt["source_kind"] == request["source_kind"], "MARKET_SOURCE_KIND_MISMATCH")
        _require(
            receipt["price_unit"] == request["price_unit"]
            and receipt["price_family"] == request["price_family"],
            "MARKET_SOURCE_PRICE_UNIT_OR_FAMILY_MISMATCH",
        )
        bar = _original(raw)
        for key in ("session_id", "repository_sha", "config_digest"):
            _text(bar.get(key), "MARKET_SOURCE_PROVENANCE_REQUIRED:" + key)
        obs = bar["last_observation_identity"]
        for key, expected in (
            ("canonical_instrument_id", identity["instrument_ref"]),
            ("venue_instrument_id", identity["native_instrument_ref"]),
            ("venue", identity["venue"]),
        ):
            _require(bar[key] == obs[key] == expected, "MARKET_SOURCE_ENTITY_MISMATCH:" + key)
        for key in ("bar_open_time", "bar_close_time", "close"):
            _require(
                type(bar[key]) in (int, float) and math.isfinite(bar[key]),
                "MARKET_FINITE_SOURCE_NUMBER:" + key,
            )
        _require(bar["close"] > 0, "MARKET_POSITIVE_CLOSE_REQUIRED")
        _require(
            type(obs["mark_price"]) in (int, float) and obs["mark_price"] == bar["close"],
            "MARKET_CLOSE_MARK_MISMATCH",
        )
        observed = obs["venue_event_time"]
        _require(
            type(observed) in (int, float) and math.isfinite(observed),
            "MARKET_OBSERVATION_TIME_REQUIRED",
        )
        _require(
            bar["bar_open_time"] <= observed <= bar["bar_close_time"],
            "MARKET_OBSERVATION_OUTSIDE_BAR",
        )
        known, available = _instant(receipt["known_at_utc"]), _instant(receipt["available_at_utc"])
        _require(
            bar["bar_close_time"]
            <= known.timestamp()
            <= available.timestamp()
            <= evaluated.timestamp(),
            "MARKET_FINAL_VALUE_NOT_AVAILABLE",
        )
        _require(type(bar["revision"]) is int and bar["revision"] >= 0, "MARKET_REVISION_REQUIRED")
        _require(
            bar["interval"].upper() in {interval, "1H", "60M"}, "MARKET_SOURCE_INTERVAL_MISMATCH"
        )
        bars.append(bar)
    bars.sort(key=lambda b: b["bar_open_time"])
    for i, bar in enumerate(bars):
        _require(
            bar["bar_open_time"] == start.timestamp() + i * seconds
            and bar["bar_close_time"] == start.timestamp() + (i + 1) * seconds,
            "MARKET_EXACT_HORIZON_GRID_REQUIRED",
        )
        _require(
            bar["finalization_state"] in {"FINALIZED_BAR", "CORRECTED_BAR"}
            and bar["quality_state"] == bar["finalization_state"],
            "MARKET_FINALIZED_COMPLETE_BAR_REQUIRED",
        )
        if bar["finalization_state"] == "CORRECTED_BAR":
            _require(bar["revision"] > 0, "MARKET_CORRECTION_REVISION_REQUIRED")
    _require(
        0 <= evaluated.timestamp() - bars[-1]["bar_close_time"] <= request["max_end_age_seconds"],
        "MARKET_MEASUREMENT_STALE",
    )
    bindings = translate_o4_market_bar_chain_v1(
        horizon_start_time_utc=request["horizon_start_time_utc"],
        n_bars=request["n_bars"],
        o4_interval_id=request["o4_interval_id"],
        o4_bars=bars,
    )
    _require(bindings["horizon_observation_status"] == "OK", "MARKET_CANONICAL_CHAIN_INCOMPLETE")
    measurement = _materialize_canonical_n_bars_measurement_v1(
        translation=SimpleNamespace(**bindings),
        bars=bars,
        outcome_scalar_kind="LOG_RETURN",
    )
    _require(
        measurement["price_basis_kind"] == request["expected_price_basis_kind"],
        "MARKET_PRICE_BASIS_GENERATION_MISMATCH",
    )
    body = {
        "schema_version": OBSERVATION_SCHEMA,
        "authority": "NONE",
        "request": request,
        "source_receipts": list(source_receipts),
        "evaluated_at_utc": evaluated_at_utc,
        "measurement": measurement,
        "measurement_exact_digest": _digest(measurement),
        "source_authenticated": False,
        "productive_apply_authorized": False,
    }
    body = json.loads(_bytes(body))
    return {**body, "exact_content_digest": _digest(body)}


def validate_independent_market_horizon_v1(observation):
    """Reproduce canonical content from exact original receipts; no store writes."""
    _require(observation.get("schema_version") == OBSERVATION_SCHEMA, "MARKET_OBSERVATION_SCHEMA")
    expected = _materialize_market_horizon_v1(
        request=observation["request"],
        source_receipts=observation["source_receipts"],
        evaluated_at_utc=observation["evaluated_at_utc"],
    )
    _require(_bytes(expected) == _bytes(observation), "MARKET_OBSERVATION_CONTENT_MISMATCH")
    return expected


def build_independent_market_return_target_v1(request):
    """Declare exact future close anchors and source identity before prices exist."""
    identity, start, interval, seconds = validate_market_horizon_request_v1(request)
    first = datetime.fromtimestamp(start.timestamp() + seconds, timezone.utc)
    last = datetime.fromtimestamp(start.timestamp() + request["n_bars"] * seconds, timezone.utc)
    return {
        "schema_version": "independent_market_return_target_v1",
        "market_request": json.loads(_bytes(request)),
        "instrument_ref": identity["instrument_ref"],
        "measurement_instrument_ref": derive_o4_instrument_ref_v1(
            identity["instrument_ref"], identity["venue"], identity["native_instrument_ref"]
        ),
        "bar_spec_ref": derive_o4_bar_spec_ref_v1(interval),
        "n_bars": request["n_bars"],
        "price_basis_kind": request["expected_price_basis_kind"],
        "outcome_scalar_kind": "LOG_RETURN",
        "horizon_start_time_utc": request["horizon_start_time_utc"],
        "return_start_close_time_utc": first.isoformat().replace("+00:00", "Z"),
        "return_end_close_time_utc": last.isoformat().replace("+00:00", "Z"),
    }
