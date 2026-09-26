"""Phase 18 — existing-fact MARKET_CONTEXT_V1 materialization (AUTHORITY=NONE).

Deterministic, PIT-safe composition from explicitly supplied governed canonical facts
only. No runtime producer discovery, no second market truth, no trading authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

import pandas as pd

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    require_event_time_utc,
    require_mapping,
    require_record_id,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import compute_content_hash_v0
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_v1 import (
    CONTEXT_FAMILY_SLOT_SCHEMA,
    GovernedMarketContextInputsV1,
    MICROSTRUCTURE_KIND_PROXY_OHLCV,
    compose_market_context_v1_from_governed_inputs,
    serialize_market_context_canonical_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import fact_digest
from src.ops.peak_trade_public_market_data_runtime_v1.o4_pt1h_bar_fact_v1 import (
    FACT_KIND_FINALIZED_PT1H_O4_BAR,
)
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0 import (
    LONG_WINDOW,
    compute_ohlcv_proxy_features_v0,
)
from src.trading.master_v2 import canonical_volatility_estimate_feature_contract_v1 as vol_contract
from src.trading.master_v2.canonical_volatility_estimate_materializer_v1 import (
    MATERIALIZER_OWNER as VOL_MATERIALIZER_OWNER,
    compute_canonical_volatility_estimate_from_mark_prices_v1,
    validate_finalized_mark_price_inputs_v1,
)

MATERIALIZATION_SCHEMA: Final[str] = "market_context_existing_fact_materialization_v1"
MATERIALIZATION_OWNER: Final[str] = (
    "learning.market_intelligence_forecast_calibration_offline_stack_v1."
    "market_context_existing_fact_materialization_v1"
)

WP_A_PRODUCER: Final[str] = "ops.peak_trade_public_market_data_runtime_v1"
BOUCHAUD_PROXY_PRODUCER: Final[str] = "research.bouchaud_microstructure_ohlcv_proxy_v1"
VOL_FEATURE_PRODUCER: Final[str] = (
    "trading.master_v2.canonical_volatility_estimate_feature_contract_v1"
)

FACT_KIND_FINALIZED_PT1M_MARK: Final[str] = "FinalizedPt1mMarkFactV1"
FACT_KIND_TRADE: Final[str] = "TradeFactV1"
FACT_KIND_OHLCV_INTERVAL: Final[str] = "OhlcvIntervalFactV1"

_ADMISSIBLE_FACT_KINDS: Final[frozenset[str]] = frozenset(
    {
        FACT_KIND_FINALIZED_PT1M_MARK,
        FACT_KIND_FINALIZED_PT1H_O4_BAR,
        FACT_KIND_TRADE,
        FACT_KIND_OHLCV_INTERVAL,
    }
)

_EXPECTED_PRODUCER_BY_KIND: Final[Mapping[str, frozenset[str]]] = MappingProxyType(
    {
        FACT_KIND_FINALIZED_PT1M_MARK: frozenset({WP_A_PRODUCER}),
        FACT_KIND_FINALIZED_PT1H_O4_BAR: frozenset({WP_A_PRODUCER}),
        FACT_KIND_TRADE: frozenset({WP_A_PRODUCER}),
        FACT_KIND_OHLCV_INTERVAL: frozenset({WP_A_PRODUCER}),
    }
)

PRICE_STATE_FEATURE_VERSION: Final[str] = "wp_a_finalized_mark_or_o4_bar_v1"
FLOW_STATE_FEATURE_VERSION: Final[str] = "wp_a_trade_signed_notional_v1"
MICROSTRUCTURE_FEATURE_VERSION: Final[str] = "bouchaud_ohlcv_proxy_snapshot_v1"
VOLATILITY_FEATURE_VERSION: Final[str] = vol_contract.CONTRACT_VERSION

DERIVATIVES_MISSING_REASON: Final[str] = "NO_GOVERNED_DERIVATIVES_PRODUCER_PHASE_19_SCOPE"
CROSS_MARKET_MISSING_REASON: Final[str] = "NO_GOVERNED_CROSS_MARKET_PRODUCER_PHASE_19_SCOPE"
FLOW_INTENSITY_MISSING_REASON: Final[str] = "TRADE_INTENSITY_SIZE_DISTRIBUTION_NOT_PROVEN_CURRENT"


class ExistingFactMaterializationError(ValueError):
    """Fail-closed existing-fact materialization."""


class MaterializationRejection(str, Enum):
    UNGOVERNED_FACT_KIND = "ungoverned_fact_kind_rejected"
    UNGOVERNED_PRODUCER = "ungoverned_producer_rejected"
    FACT_DIGEST_MISMATCH = "fact_digest_mismatch_rejected"
    PIT_LOOKAHEAD = "pit_lookahead_rejected"
    UNFINALIZED_FACT = "unfinalized_fact_rejected"
    AMBIGUOUS_PRICE_SOURCE = "ambiguous_price_source_rejected"
    INSUFFICIENT_VOLATILITY_WARMUP = "insufficient_volatility_warmup_rejected"
    INSUFFICIENT_MICROSTRUCTURE_WARMUP = "insufficient_microstructure_warmup_rejected"
    UNKNOWN_TRADE_SIDE = "unknown_trade_side_rejected"
    PROXY_L2_UPGRADE_FORBIDDEN = "proxy_l2_upgrade_forbidden"


def _parse_utc(value: str) -> datetime:
    text = require_event_time_utc(value, "utc")
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def _ms_to_utc_iso(ms: int) -> str:
    dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _quality_finalized(payload: Mapping[str, Any]) -> bool:
    quality = payload.get("quality")
    if not isinstance(quality, Mapping):
        return False
    return quality.get("finalized") is True and quality.get("missing") is not True


@dataclass(frozen=True)
class GovernedCanonicalFactV1:
    fact_kind: str
    fact_digest: str
    payload: Mapping[str, Any]
    producer_owner: str

    def validated_payload(self) -> Mapping[str, Any]:
        return require_mapping(self.payload, "fact_payload")


def validate_governed_canonical_fact_v1(
    fact: GovernedCanonicalFactV1,
    *,
    observed_at: str,
) -> Mapping[str, Any]:
    observed_dt = _parse_utc(observed_at)
    kind = str(fact.fact_kind or "").strip()
    if kind not in _ADMISSIBLE_FACT_KINDS:
        msg = MaterializationRejection.UNGOVERNED_FACT_KIND.value
        raise ExistingFactMaterializationError(msg)
    allowed = _EXPECTED_PRODUCER_BY_KIND.get(kind, frozenset())
    owner = str(fact.producer_owner or "").strip()
    if owner not in allowed:
        msg = MaterializationRejection.UNGOVERNED_PRODUCER.value
        raise ExistingFactMaterializationError(msg)
    payload = fact.validated_payload()
    if payload.get("fact_kind") not in (None, kind):
        raise ExistingFactMaterializationError("FACT_KIND_PAYLOAD_MISMATCH")
    expected_digest = fact_digest(payload)
    if str(fact.fact_digest) != expected_digest:
        msg = MaterializationRejection.FACT_DIGEST_MISMATCH.value
        raise ExistingFactMaterializationError(msg)
    if not _quality_finalized(payload):
        msg = MaterializationRejection.UNFINALIZED_FACT.value
        raise ExistingFactMaterializationError(msg)
    pit = _pit_observed_at_for_fact_v1(kind, payload)
    if _parse_utc(pit) > observed_dt:
        msg = MaterializationRejection.PIT_LOOKAHEAD.value
        raise ExistingFactMaterializationError(msg)
    return payload


def _pit_observed_at_for_fact_v1(kind: str, payload: Mapping[str, Any]) -> str:
    if kind == FACT_KIND_FINALIZED_PT1M_MARK:
        ms = payload.get("interval_start_ms")
        if not isinstance(ms, int):
            raise ExistingFactMaterializationError("MARK_INTERVAL_START_INVALID")
        return _ms_to_utc_iso(ms)
    if kind == FACT_KIND_FINALIZED_PT1H_O4_BAR:
        bar = payload.get("bar")
        if not isinstance(bar, Mapping):
            raise ExistingFactMaterializationError("O4_BAR_MISSING")
        close_time = bar.get("bar_close_time")
        if not isinstance(close_time, (int, float)):
            raise ExistingFactMaterializationError("O4_BAR_CLOSE_TIME_INVALID")
        return _ms_to_utc_iso(int(close_time * 1000))
    if kind == FACT_KIND_TRADE:
        timestamps = payload.get("timestamps")
        if not isinstance(timestamps, Mapping):
            raise ExistingFactMaterializationError("TRADE_TIMESTAMPS_MISSING")
        effective = timestamps.get("effective_at") or timestamps.get("captured_at")
        if not isinstance(effective, str):
            raise ExistingFactMaterializationError("TRADE_PIT_TIME_MISSING")
        return require_event_time_utc(effective, "trade_pit")
    if kind == FACT_KIND_OHLCV_INTERVAL:
        ms = payload.get("interval_start_ms")
        if not isinstance(ms, int):
            raise ExistingFactMaterializationError("OHLCV_INTERVAL_START_INVALID")
        return _ms_to_utc_iso(ms)
    raise ExistingFactMaterializationError("PIT_KIND_UNSUPPORTED")


def _decimal_text(value: float) -> str:
    return format(value, ".16g")


def _state_ref_for_family(*, family: str, identity_body: Mapping[str, Any]) -> str:
    digest = compute_content_hash_v0(dict(identity_body))
    return f"mi.ctx.{family}.{digest[:40]}"


def _present_slot_from_derivation(
    *,
    field_name: str,
    state_ref: str,
    pit_observed_at_utc: str,
    producer_owner: str,
    feature_version: str,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": CONTEXT_FAMILY_SLOT_SCHEMA,
        "presence": "PRESENT",
        "state_ref": state_ref,
        "pit_observed_at_utc": pit_observed_at_utc,
        "producer_owner": producer_owner,
        "producer_ownership": "GOVERNED",
        "feature_version": feature_version,
    }
    if extra:
        body.update(dict(extra))
    return body


def derive_price_state_slot_v1(
    *,
    mark_fact: GovernedCanonicalFactV1 | None,
    o4_bar_fact: GovernedCanonicalFactV1 | None,
    observed_at: str,
) -> dict[str, Any] | None:
    if mark_fact is not None and o4_bar_fact is not None:
        msg = MaterializationRejection.AMBIGUOUS_PRICE_SOURCE.value
        raise ExistingFactMaterializationError(msg)
    if mark_fact is None and o4_bar_fact is None:
        return None
    if mark_fact is not None:
        payload = validate_governed_canonical_fact_v1(mark_fact, observed_at=observed_at)
        pit = _pit_observed_at_for_fact_v1(FACT_KIND_FINALIZED_PT1M_MARK, payload)
        identity = {
            "family": "price_state",
            "fact_kind": FACT_KIND_FINALIZED_PT1M_MARK,
            "fact_digest": mark_fact.fact_digest,
            "mark_px": payload.get("mark_px"),
            "interval_start_ms": payload.get("interval_start_ms"),
        }
        return _present_slot_from_derivation(
            field_name="price_state_ref",
            state_ref=_state_ref_for_family(family="price_state", identity_body=identity),
            pit_observed_at_utc=pit,
            producer_owner=WP_A_PRODUCER,
            feature_version=PRICE_STATE_FEATURE_VERSION,
        )
    assert o4_bar_fact is not None
    payload = validate_governed_canonical_fact_v1(o4_bar_fact, observed_at=observed_at)
    pit = _pit_observed_at_for_fact_v1(FACT_KIND_FINALIZED_PT1H_O4_BAR, payload)
    bar = require_mapping(payload.get("bar"), "o4_bar")
    identity = {
        "family": "price_state",
        "fact_kind": FACT_KIND_FINALIZED_PT1H_O4_BAR,
        "fact_digest": o4_bar_fact.fact_digest,
        "close": bar.get("close"),
        "bar_open_time": bar.get("bar_open_time"),
    }
    return _present_slot_from_derivation(
        field_name="price_state_ref",
        state_ref=_state_ref_for_family(family="price_state", identity_body=identity),
        pit_observed_at_utc=pit,
        producer_owner=WP_A_PRODUCER,
        feature_version=PRICE_STATE_FEATURE_VERSION,
    )


def _signed_trade_notional_v1(payload: Mapping[str, Any]) -> float:
    side = str(payload.get("side") or "").strip().lower()
    if side in {"buy", "b"}:
        sign = 1.0
    elif side in {"sell", "s"}:
        sign = -1.0
    else:
        msg = MaterializationRejection.UNKNOWN_TRADE_SIDE.value
        raise ExistingFactMaterializationError(msg)
    size = float(payload["size"])
    price = float(payload["price"])
    return sign * size * price


def derive_flow_state_slot_v1(
    *,
    trade_facts: Sequence[GovernedCanonicalFactV1] | None,
    observed_at: str,
) -> dict[str, Any] | None:
    if not trade_facts:
        return None
    observed_dt = _parse_utc(observed_at)
    signed_total = 0.0
    trade_count = 0
    latest_pit: datetime | None = None
    digests: list[str] = []
    for fact in trade_facts:
        payload = validate_governed_canonical_fact_v1(fact, observed_at=observed_at)
        if fact.fact_kind != FACT_KIND_TRADE:
            raise ExistingFactMaterializationError("FLOW_REQUIRES_TRADE_FACTS")
        signed_total += _signed_trade_notional_v1(payload)
        trade_count += 1
        digests.append(fact.fact_digest)
        pit_dt = _parse_utc(_pit_observed_at_for_fact_v1(FACT_KIND_TRADE, payload))
        if latest_pit is None or pit_dt > latest_pit:
            latest_pit = pit_dt
    assert latest_pit is not None
    if latest_pit > observed_dt:
        msg = MaterializationRejection.PIT_LOOKAHEAD.value
        raise ExistingFactMaterializationError(msg)
    identity = {
        "family": "flow_state",
        "semantic": "signed_notional_sum_only",
        "trade_count": trade_count,
        "signed_net_notional": _decimal_text(signed_total),
        "fact_digests": tuple(sorted(digests)),
        "intensity_semantics": FLOW_INTENSITY_MISSING_REASON,
    }
    pit_iso = latest_pit.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return _present_slot_from_derivation(
        field_name="flow_state_ref",
        state_ref=_state_ref_for_family(family="flow_state", identity_body=identity),
        pit_observed_at_utc=pit_iso,
        producer_owner=WP_A_PRODUCER,
        feature_version=FLOW_STATE_FEATURE_VERSION,
    )


def _ohlcv_facts_to_bars_frame_v1(
    facts: Sequence[GovernedCanonicalFactV1],
    *,
    observed_at: str,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for fact in facts:
        payload = validate_governed_canonical_fact_v1(fact, observed_at=observed_at)
        if fact.fact_kind != FACT_KIND_OHLCV_INTERVAL:
            raise ExistingFactMaterializationError("MICROSTRUCTURE_REQUIRES_OHLCV_FACTS")
        rows.append(
            {
                "timestamp": _pit_observed_at_for_fact_v1(FACT_KIND_OHLCV_INTERVAL, payload),
                "open": float(payload["open_px"]),
                "high": float(payload["high_px"]),
                "low": float(payload["low_px"]),
                "close": float(payload["close_px"]),
                "volume": float(payload["volume"]),
                "is_final": True,
            }
        )
    frame = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
    return frame


def derive_liquidity_microstructure_slot_v1(
    *,
    ohlcv_facts: Sequence[GovernedCanonicalFactV1] | None,
    observed_at: str,
) -> dict[str, Any] | None:
    if not ohlcv_facts:
        return None
    frame = _ohlcv_facts_to_bars_frame_v1(ohlcv_facts, observed_at=observed_at)
    if len(frame) < LONG_WINDOW + 1:
        msg = MaterializationRejection.INSUFFICIENT_MICROSTRUCTURE_WARMUP.value
        raise ExistingFactMaterializationError(msg)
    features = compute_ohlcv_proxy_features_v0(frame)
    observed_dt = _parse_utc(observed_at)
    eligible = features[pd.to_datetime(features["decision_time"], utc=True) <= observed_dt]
    if eligible.empty:
        msg = MaterializationRejection.PIT_LOOKAHEAD.value
        raise ExistingFactMaterializationError(msg)
    row = eligible.iloc[-1]
    snapshot = {
        name: _decimal_text(float(row[name]))
        for name in (
            "signed_return_volume_pressure",
            "volatility_normalized_price_impact",
            "liquidity_resilience_proxy",
        )
        if pd.notna(row[name])
    }
    if not snapshot:
        msg = MaterializationRejection.INSUFFICIENT_MICROSTRUCTURE_WARMUP.value
        raise ExistingFactMaterializationError(msg)
    pit = str(row["decision_time"])
    digests = tuple(sorted(f.fact_digest for f in ohlcv_facts))
    identity = {
        "family": "liquidity_microstructure",
        "microstructure_kind": MICROSTRUCTURE_KIND_PROXY_OHLCV,
        "proxy_features": snapshot,
        "fact_digests": digests,
    }
    return _present_slot_from_derivation(
        field_name="liquidity_microstructure_state_ref",
        state_ref=_state_ref_for_family(family="liquidity_microstructure", identity_body=identity),
        pit_observed_at_utc=require_event_time_utc(pit, "micro_pit"),
        producer_owner=BOUCHAUD_PROXY_PRODUCER,
        feature_version=MICROSTRUCTURE_FEATURE_VERSION,
        extra={"microstructure_kind": MICROSTRUCTURE_KIND_PROXY_OHLCV},
    )


def derive_volatility_state_slot_v1(
    *,
    mark_facts: Sequence[GovernedCanonicalFactV1] | None,
    observed_at: str,
) -> dict[str, Any] | None:
    if not mark_facts:
        return None
    payloads = [validate_governed_canonical_fact_v1(f, observed_at=observed_at) for f in mark_facts]
    if any(f.fact_kind != FACT_KIND_FINALIZED_PT1M_MARK for f in mark_facts):
        raise ExistingFactMaterializationError("VOLATILITY_REQUIRES_PT1M_MARKS")
    series_rows: list[tuple[datetime, float]] = []
    for payload in payloads:
        ms = int(payload["interval_start_ms"])
        series_rows.append((_parse_utc(_ms_to_utc_iso(ms)), float(payload["mark_px"])))
    series_rows.sort(key=lambda item: item[0])
    index = pd.DatetimeIndex([item[0] for item in series_rows], tz="UTC")
    mark_prices = pd.Series([item[1] for item in series_rows], index=index, dtype=float)
    is_final = pd.Series([True] * len(mark_prices), index=index)
    validate_finalized_mark_price_inputs_v1(mark_prices, is_final=is_final)
    vol = compute_canonical_volatility_estimate_from_mark_prices_v1(mark_prices, is_final=is_final)
    observed_dt = _parse_utc(observed_at)
    eligible = vol[vol.index <= observed_dt]
    if eligible.empty or pd.isna(eligible.iloc[-1]):
        msg = MaterializationRejection.INSUFFICIENT_VOLATILITY_WARMUP.value
        raise ExistingFactMaterializationError(msg)
    value = float(eligible.iloc[-1])
    pit_dt = eligible.index[-1]
    pit_iso = pit_dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    digests = tuple(sorted(f.fact_digest for f in mark_facts))
    identity = {
        "family": "volatility_state",
        "horizon": vol_contract.WINDOW_DURATION,
        "lookback_bars": vol_contract.LOOKBACK_BARS,
        "volatility_estimate": _decimal_text(value),
        "fact_digests": digests,
    }
    return _present_slot_from_derivation(
        field_name="volatility_state_ref",
        state_ref=_state_ref_for_family(family="volatility_state", identity_body=identity),
        pit_observed_at_utc=pit_iso,
        producer_owner=VOL_FEATURE_PRODUCER,
        feature_version=VOLATILITY_FEATURE_VERSION,
    )


def build_information_set_identity_from_facts_v1(
    *,
    instrument_ref: str,
    observed_at: str,
    fact_digests: Sequence[str],
) -> Mapping[str, Any]:
    return {
        "instrument_ref": require_record_id(instrument_ref, "instrument_ref"),
        "observed_at": require_event_time_utc(observed_at, "observed_at"),
        "pit_fact_refs": tuple(sorted(require_record_id(d, "fact_digest") for d in fact_digests)),
        "materialization_schema": MATERIALIZATION_SCHEMA,
    }


@dataclass(frozen=True)
class ExistingFactMaterializationRequestV1:
    observed_at: str
    instrument_ref: str
    provenance_refs: Sequence[str]
    price_mark_fact: GovernedCanonicalFactV1 | None = None
    price_o4_bar_fact: GovernedCanonicalFactV1 | None = None
    trade_facts: Sequence[GovernedCanonicalFactV1] | None = None
    ohlcv_facts: Sequence[GovernedCanonicalFactV1] | None = None
    volatility_mark_facts: Sequence[GovernedCanonicalFactV1] | None = None
    information_set_identity_body: Mapping[str, Any] | None = None


def collect_fact_digests_from_request_v1(
    request: ExistingFactMaterializationRequestV1,
) -> tuple[str, ...]:
    digests: list[str] = []
    for part in (
        request.price_mark_fact,
        request.price_o4_bar_fact,
    ):
        if part is not None:
            digests.append(part.fact_digest)
    for seq in (request.trade_facts, request.ohlcv_facts, request.volatility_mark_facts):
        if seq:
            digests.extend(f.fact_digest for f in seq)
    return tuple(sorted(set(digests)))


def materialize_market_context_v1_from_existing_facts_v1(
    request: ExistingFactMaterializationRequestV1,
) -> MappingProxyType[str, Any]:
    """Materialize MARKET_CONTEXT_V1 from governed existing facts (explicit inputs only)."""
    observed_at = require_event_time_utc(request.observed_at, "observed_at")
    instrument_ref = require_record_id(request.instrument_ref, "instrument_ref")
    if not request.provenance_refs:
        raise ExistingFactMaterializationError("PROVENANCE_REFS_REQUIRED")

    price_slot = derive_price_state_slot_v1(
        mark_fact=request.price_mark_fact,
        o4_bar_fact=request.price_o4_bar_fact,
        observed_at=observed_at,
    )
    flow_slot = derive_flow_state_slot_v1(
        trade_facts=request.trade_facts,
        observed_at=observed_at,
    )
    micro_slot = derive_liquidity_microstructure_slot_v1(
        ohlcv_facts=request.ohlcv_facts,
        observed_at=observed_at,
    )
    vol_slot = derive_volatility_state_slot_v1(
        mark_facts=request.volatility_mark_facts,
        observed_at=observed_at,
    )

    fact_digests = collect_fact_digests_from_request_v1(request)
    info_body = request.information_set_identity_body
    if info_body is None:
        info_body = build_information_set_identity_from_facts_v1(
            instrument_ref=instrument_ref,
            observed_at=observed_at,
            fact_digests=fact_digests,
        )

    feature_versions = {
        "market_context_v1": "v1",
        "market_context_existing_fact_materialization_v1": MATERIALIZATION_SCHEMA,
        "price_state": PRICE_STATE_FEATURE_VERSION,
        "flow_state": FLOW_STATE_FEATURE_VERSION,
        "liquidity_microstructure": MICROSTRUCTURE_FEATURE_VERSION,
        "volatility_state": VOLATILITY_FEATURE_VERSION,
    }

    inputs = GovernedMarketContextInputsV1(
        observed_at=observed_at,
        instrument_ref=instrument_ref,
        information_set_identity_body=info_body,
        provenance_refs=tuple(
            require_record_id(item, "provenance_refs[]") for item in request.provenance_refs
        ),
        feature_versions=feature_versions,
        price_state=price_slot,
        flow_state=flow_slot,
        liquidity_microstructure_state=micro_slot,
        volatility_state=vol_slot,
        derivatives_state=None,
        cross_market_state=None,
        quality_state=None,
    )
    return compose_market_context_v1_from_governed_inputs(inputs)


def replay_market_context_serialization_v1(record: Mapping[str, Any]) -> str:
    """Deterministic replay serialization contract for persisted contexts."""
    return serialize_market_context_canonical_v1(record)


__all__ = [
    "BOUCHAUD_PROXY_PRODUCER",
    "DERIVATIVES_MISSING_REASON",
    "ExistingFactMaterializationError",
    "ExistingFactMaterializationRequestV1",
    "GovernedCanonicalFactV1",
    "MATERIALIZATION_OWNER",
    "MATERIALIZATION_SCHEMA",
    "MaterializationRejection",
    "VOL_MATERIALIZER_OWNER",
    "WP_A_PRODUCER",
    "build_information_set_identity_from_facts_v1",
    "collect_fact_digests_from_request_v1",
    "derive_flow_state_slot_v1",
    "derive_liquidity_microstructure_slot_v1",
    "derive_price_state_slot_v1",
    "derive_volatility_state_slot_v1",
    "materialize_market_context_v1_from_existing_facts_v1",
    "replay_market_context_serialization_v1",
    "validate_governed_canonical_fact_v1",
]
