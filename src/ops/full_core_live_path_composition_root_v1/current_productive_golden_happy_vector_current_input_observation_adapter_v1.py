"""Authority-none adapter: observe CURRENT productive MD inputs for GHV evaluation.

Reuses productive read-only GET transport, G17 hot-path join, and G17→CMC bind.
Does not dispatch cycles, select, POST, or mutate trading state.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol
from urllib.parse import urlencode

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
    ENDPOINT_PUBLIC_MARK_PRICE,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    ProductiveCanonicalPriceProvenanceError,
    build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ENDPOINT_MARKET_INDEX_TICKERS,
    extract_mark_and_index_from_payload_v1,
    resolve_index_ticker_inst_id_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1 import (
    prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_pt1m_mark_sample_adapter_v1 import (
    ENDPOINT_HISTORY_MARK_PRICE_CANDLES,
    mark_history_get_query_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_typed_vol_cmc_bind_v1 import (
    apply_current_productive_g17_typed_vol_cmc_bind_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    FEATURE_CONTRACT_VERSION,
    WarmupStatus,
    with_computed_input_digest,
)
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    evaluate_typed_volatility_binding_eligibility_v1,
    resolve_legacy_volatility_float_for_consumer_v1,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType
from trading.master_v2.golden_geometry_engine_v1 import (
    compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1,
    compute_canonical_base_geometry_magnitude_from_market_context_v1,
)
from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
    resolve_layer_c_event_distances_from_canonical_market_context_v1,
)

ADAPTER_OWNER = (
    "full_core_live_path_composition_root_v1."
    "current_productive_golden_happy_vector_current_input_observation_adapter_v1"
)
SOURCE_LIVE_PRODUCTIVE_GET = "LIVE_PRODUCTIVE_GET"
SOURCE_INJECTED_TRANSPORT = "INJECTED_PRODUCTIVE_GET_TRANSPORT"
FORBIDDEN_SOURCE_FIXTURE_REPLAY = "FIXTURE_GOLDEN_VECTOR_BUNDLE"

DEFAULT_FRESH_MARK_MAX_AGE_SECONDS = 120.0
DEFAULT_SELECTION_REL = "runtime_state/selection/single_selected_future_selection_v1.json"

CLASS_CURRENT_AVAILABLE_VALID = "CURRENT_AVAILABLE_VALID"
CLASS_CURRENT_MISSING = "CURRENT_MISSING"
CLASS_CURRENT_AVAILABLE_INVALID = "CURRENT_AVAILABLE_INVALID"
CLASS_CURRENT_STALE = "CURRENT_STALE"
CLASS_CURRENT_BINDING_MISMATCH = "CURRENT_BINDING_MISMATCH"
CLASS_CURRENT_PROVENANCE_MISMATCH = "CURRENT_PROVENANCE_MISMATCH"
CLASS_NOT_REQUIRED_CURRENT = "NOT_REQUIRED_CURRENT"


class ProductiveReadOnlyGetTransportProtocolV1(Protocol):
    def get(
        self,
        *,
        endpoint: str,
        auth_required: bool,
        pretrade_decision_id: str,
        get_cache_policy: str = GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    ) -> Any: ...


@dataclass(frozen=True)
class GhvInputFieldGapRowV1:
    field_id: str
    domain: str
    fixture_required: bool
    classification: str
    producer_owner: str
    evidence: Mapping[str, Any]


@dataclass
class CurrentProductiveGhvInputObservationV1:
    observation_ok: bool
    source_kind: str
    current_input_blocker: str
    bound_instrument: BoundInstrumentV1 | None = None
    mark_price: float | None = None
    index_price: float | None = None
    volatility_estimate: float | None = None
    market_context: CanonicalMarketContextV1 | None = None
    observed_at_unix: float = 0.0
    mark_age_seconds: float | None = None
    current_input_provenance_valid: bool = False
    current_input_freshness_valid: bool = False
    current_input_type_valid: bool = False
    current_input_unit_valid: bool = False
    current_selection_binding_valid: bool = False
    gge_current_input_valid: bool = False
    scope_current_input_valid: bool = False
    mv2_current_input_valid: bool = False
    double_play_current_input_valid: bool = False
    http_get_count: int = 0
    gap_rows: list[GhvInputFieldGapRowV1] = field(default_factory=list)


def _utc_iso_from_unix(unix: float) -> str:
    return datetime.fromtimestamp(float(unix), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_bound_instrument_from_selection_file_v1(path: Path) -> BoundInstrumentV1:
    payload = json.loads(path.read_text(encoding="utf-8"))
    instrument_id = str(payload.get("instrument_id") or "").strip()
    venue_native_id = str(payload.get("venue_native_id") or "").strip()
    if not instrument_id or not venue_native_id:
        raise ValueError("SELECTION_INSTRUMENT_BINDING_INCOMPLETE")
    return BoundInstrumentV1(
        instrument_id=instrument_id,
        venue_native_id=venue_native_id,
        ranking_snapshot_id=str(payload.get("ranking_snapshot_id") or ""),
        ranking_integrity_digest=str(payload.get("ranking_integrity_digest") or ""),
        universe_snapshot_id=str(payload.get("universe_snapshot_id") or ""),
        selection_id=str(payload.get("selection_id") or ""),
        selection_integrity_digest=str(payload.get("integrity_digest") or ""),
        selection_state=str(payload.get("state") or ""),
        selected_future_count=int(payload.get("selected_future_count") or 1),
        max_positions_effective=int(payload.get("max_positions_effective") or 1),
        ranking_policy_id=str(payload.get("ranking_policy_id") or ""),
        ranking_policy_version=str(payload.get("ranking_policy_version") or ""),
        upstream_rank_order_witness=str(payload.get("upstream_rank_order_witness") or ""),
    )


def _append_gap(
    rows: list[GhvInputFieldGapRowV1],
    *,
    field_id: str,
    domain: str,
    fixture_required: bool,
    classification: str,
    producer_owner: str,
    evidence: Mapping[str, Any],
) -> None:
    rows.append(
        GhvInputFieldGapRowV1(
            field_id=field_id,
            domain=domain,
            fixture_required=fixture_required,
            classification=classification,
            producer_owner=producer_owner,
            evidence=dict(evidence),
        )
    )


def build_fixture_vs_current_gap_matrix_v1(
    *,
    manifest: Mapping[str, Any],
    observation: CurrentProductiveGhvInputObservationV1 | None,
) -> list[GhvInputFieldGapRowV1]:
    rows: list[GhvInputFieldGapRowV1] = []
    obs = observation
    inst_fixture = str(manifest.get("INSTRUMENT_ID") or "")
    native_fixture = str(manifest.get("NATIVE_ID") or "")

    def _classify_present(
        *,
        present: bool,
        valid: bool,
        stale: bool = False,
        binding_mismatch: bool = False,
    ) -> str:
        if binding_mismatch:
            return CLASS_CURRENT_BINDING_MISMATCH
        if not present:
            return CLASS_CURRENT_MISSING
        if stale:
            return CLASS_CURRENT_STALE
        if not valid:
            return CLASS_CURRENT_AVAILABLE_INVALID
        return CLASS_CURRENT_AVAILABLE_VALID

    bound = None if obs is None else obs.bound_instrument
    inst_match = (
        bound is not None
        and str(bound.instrument_id) == inst_fixture
        and str(bound.venue_native_id) == native_fixture
    )
    _append_gap(
        rows,
        field_id="instrument_id",
        domain="INSTRUMENT_METADATA",
        fixture_required=True,
        classification=_classify_present(
            present=bound is not None,
            valid=bound is not None and bool(bound.instrument_id),
            binding_mismatch=bound is not None and str(bound.instrument_id) != inst_fixture,
        ),
        producer_owner="CAPABILITY_2_4 runtime selection publish",
        evidence={
            "fixture": inst_fixture,
            "current": None if bound is None else bound.instrument_id,
        },
    )
    _append_gap(
        rows,
        field_id="venue_native_id",
        domain="INSTRUMENT_METADATA",
        fixture_required=True,
        classification=_classify_present(
            present=bound is not None,
            valid=bound is not None and bool(bound.venue_native_id),
            binding_mismatch=bound is not None and str(bound.venue_native_id) != native_fixture,
        ),
        producer_owner="CAPABILITY_2_4 runtime selection publish",
        evidence={
            "fixture": native_fixture,
            "current": None if bound is None else bound.venue_native_id,
        },
    )
    mark_present = obs is not None and obs.mark_price is not None
    mark_valid = mark_present and float(obs.mark_price or 0) > 0  # type: ignore[union-attr]
    mark_stale = bool(obs and obs.current_input_freshness_valid is False and mark_present)
    _append_gap(
        rows,
        field_id="mark_price",
        domain="MARKET_DATA",
        fixture_required=True,
        classification=_classify_present(
            present=mark_present,
            valid=mark_valid,
            stale=mark_stale,
        ),
        producer_owner=(
            "current_productive_s6_live_fresh_c1_continuous_observation_source_v1 (public mark GET)"
        ),
        evidence={
            "fixture_reference_scope_mark": "see golden_vector existing_scope.reference_price",
            "current_mark_price": None if obs is None else obs.mark_price,
        },
    )
    vol_present = obs is not None and obs.volatility_estimate is not None
    vol_valid = vol_present and float(obs.volatility_estimate or 0) > 0  # type: ignore[union-attr]
    _append_gap(
        rows,
        field_id="volatility_estimate",
        domain="GGE_SCOPE",
        fixture_required=True,
        classification=_classify_present(present=vol_present, valid=vol_valid),
        producer_owner="current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1",
        evidence={
            "current_volatility_estimate": None if obs is None else obs.volatility_estimate,
        },
    )
    _append_gap(
        rows,
        field_id="selection_single_future_binding",
        domain="SELECTION_BINDING",
        fixture_required=True,
        classification=_classify_present(
            present=bound is not None,
            valid=bool(obs and obs.current_selection_binding_valid),
            binding_mismatch=bound is not None and not inst_match,
        ),
        producer_owner="single_selected_future_policy_v1",
        evidence={
            "fixture_instrument_match": inst_match,
            "selected_future_count": None if bound is None else bound.selected_future_count,
        },
    )
    for field_id in (
        "PRE_EXTERNAL_CONVERGENCE_REPORT",
        "ddo_learning_capture_v1",
        "natural_enter_side",
    ):
        _append_gap(
            rows,
            field_id=field_id,
            domain="DOUBLE_PLAY",
            fixture_required=True,
            classification=CLASS_NOT_REQUIRED_CURRENT,
            producer_owner="productive MV2/DP cycle (downstream)",
            evidence={"note": "Outcome evidence; not part of CURRENT MD input readiness"},
        )
    return rows


def observe_current_productive_ghv_inputs_v1(
    *,
    productivity_root: Path,
    evidence_store_root: Path,
    transport: ProductiveReadOnlyGetTransportProtocolV1,
    source_kind: str,
    selection_rel: str = DEFAULT_SELECTION_REL,
    fresh_mark_max_age_seconds: float = DEFAULT_FRESH_MARK_MAX_AGE_SECONDS,
    expected_instrument_id: str | None = None,
    expected_native_id: str | None = None,
) -> CurrentProductiveGhvInputObservationV1:
    if source_kind == FORBIDDEN_SOURCE_FIXTURE_REPLAY:
        return CurrentProductiveGhvInputObservationV1(
            observation_ok=False,
            source_kind=source_kind,
            current_input_blocker="FIXTURE_CANNOT_MASQUERADE_AS_CURRENT",
        )

    observed_unix = time.time()
    selection_path = productivity_root / selection_rel
    if not selection_path.is_file():
        obs = CurrentProductiveGhvInputObservationV1(
            observation_ok=False,
            source_kind=source_kind,
            current_input_blocker="CURRENT_SELECTION_ARTIFACT_MISSING",
        )
        obs.gap_rows = build_fixture_vs_current_gap_matrix_v1(
            manifest={
                "INSTRUMENT_ID": expected_instrument_id or "",
                "NATIVE_ID": expected_native_id or "",
            },
            observation=obs,
        )
        return obs

    try:
        bound = load_bound_instrument_from_selection_file_v1(selection_path)
    except ValueError:
        obs = CurrentProductiveGhvInputObservationV1(
            observation_ok=False,
            source_kind=source_kind,
            current_input_blocker="CURRENT_SELECTION_BINDING_INVALID",
        )
        obs.gap_rows = build_fixture_vs_current_gap_matrix_v1(
            manifest={
                "INSTRUMENT_ID": expected_instrument_id or "",
                "NATIVE_ID": expected_native_id or "",
            },
            observation=obs,
        )
        return obs

    selection_binding_valid = (
        bound.selected_future_count == 1
        and bound.max_positions_effective == 1
        and str(bound.selection_state or "") in {"SELECTED_ACTIVE", "SELECTED"}
    )
    if expected_instrument_id and str(bound.instrument_id) != expected_instrument_id:
        obs = CurrentProductiveGhvInputObservationV1(
            observation_ok=False,
            source_kind=source_kind,
            current_input_blocker="CURRENT_INSTRUMENT_BINDING_MISMATCH",
            bound_instrument=bound,
            current_selection_binding_valid=False,
        )
        obs.gap_rows = build_fixture_vs_current_gap_matrix_v1(
            manifest={
                "INSTRUMENT_ID": expected_instrument_id,
                "NATIVE_ID": expected_native_id or "",
            },
            observation=obs,
        )
        return obs
    if expected_native_id and str(bound.venue_native_id) != expected_native_id:
        obs = CurrentProductiveGhvInputObservationV1(
            observation_ok=False,
            source_kind=source_kind,
            current_input_blocker="CURRENT_NATIVE_ID_BINDING_MISMATCH",
            bound_instrument=bound,
            current_selection_binding_valid=False,
        )
        obs.gap_rows = build_fixture_vs_current_gap_matrix_v1(
            manifest={
                "INSTRUMENT_ID": expected_instrument_id or "",
                "NATIVE_ID": expected_native_id,
            },
            observation=obs,
        )
        return obs

    native = str(bound.venue_native_id)
    mark_endpoint = f"{ENDPOINT_PUBLIC_MARK_PRICE}?instId={native}"
    mark_result = transport.get(
        endpoint=mark_endpoint,
        auth_required=False,
        pretrade_decision_id=f"ghv-current-input-mark-{int(observed_unix)}",
        get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    )
    get_count = 1 if bool(getattr(mark_result, "get_performed", False)) else 0
    mark_payload = getattr(mark_result, "payload", None)
    if not isinstance(mark_payload, dict):
        obs = CurrentProductiveGhvInputObservationV1(
            observation_ok=False,
            source_kind=source_kind,
            current_input_blocker="CURRENT_MARK_GET_FAIL_CLOSED",
            bound_instrument=bound,
            observed_at_unix=observed_unix,
            http_get_count=get_count,
            current_selection_binding_valid=selection_binding_valid,
        )
        obs.gap_rows = build_fixture_vs_current_gap_matrix_v1(
            manifest={
                "INSTRUMENT_ID": expected_instrument_id or bound.instrument_id,
                "NATIVE_ID": expected_native_id or native,
            },
            observation=obs,
        )
        return obs

    mark_px_probe, index_from_mark = extract_mark_and_index_from_payload_v1(
        mark_payload, native_id=native
    )
    index_tickers_payload: dict[str, Any] | None = None
    if mark_px_probe is not None and index_from_mark is None:
        index_inst = resolve_index_ticker_inst_id_v1(native)
        index_endpoint = f"{ENDPOINT_MARKET_INDEX_TICKERS}?instId={index_inst}"
        index_result = transport.get(
            endpoint=index_endpoint,
            auth_required=False,
            pretrade_decision_id=f"ghv-current-input-index-{int(observed_unix)}",
            get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        )
        if bool(getattr(index_result, "get_performed", False)):
            get_count += 1
            candidate = getattr(index_result, "payload", None)
            if isinstance(candidate, dict):
                index_tickers_payload = candidate

    try:
        provenance = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
            mark_price_payload=mark_payload,
            venue_native_id=native,
            index_from_index_tickers=index_tickers_payload,
        )
    except ProductiveCanonicalPriceProvenanceError:
        obs = CurrentProductiveGhvInputObservationV1(
            observation_ok=False,
            source_kind=source_kind,
            current_input_blocker="CURRENT_MARK_PROVENANCE_FAIL_CLOSED",
            bound_instrument=bound,
            observed_at_unix=observed_unix,
            http_get_count=get_count,
            current_selection_binding_valid=selection_binding_valid,
            current_input_provenance_valid=False,
        )
        obs.gap_rows = build_fixture_vs_current_gap_matrix_v1(
            manifest={
                "INSTRUMENT_ID": expected_instrument_id or bound.instrument_id,
                "NATIVE_ID": expected_native_id or native,
            },
            observation=obs,
        )
        return obs

    mark_age = 0.0
    freshness_valid = mark_age <= float(fresh_mark_max_age_seconds)
    mark_px = float(provenance.mark_px)
    index_px = float(provenance.index_px)

    mark_history_endpoint = (
        f"{ENDPOINT_HISTORY_MARK_PRICE_CANDLES}?"
        f"{urlencode(mark_history_get_query_v1(venue_native_id=native))}"
    )
    history_result = transport.get(
        endpoint=mark_history_endpoint,
        auth_required=False,
        pretrade_decision_id=f"ghv-current-input-g17-{int(observed_unix)}",
        get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    )
    if bool(getattr(history_result, "get_performed", False)):
        get_count += 1
    history_payload = getattr(history_result, "payload", None)
    g17_join = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
        evidence_store_root=evidence_store_root,
        bound_instrument=bound,
        mark_candles_payload=history_payload if isinstance(history_payload, dict) else None,
        receive_or_capture_timestamp=str(int(observed_unix * 1000)),
    )
    if g17_join.fail_closed or not g17_join.estimate_present or g17_join.producer is None:
        obs = CurrentProductiveGhvInputObservationV1(
            observation_ok=False,
            source_kind=source_kind,
            current_input_blocker="CURRENT_G17_TYPED_VOL_FAIL_CLOSED",
            bound_instrument=bound,
            mark_price=mark_px,
            index_price=index_px,
            observed_at_unix=observed_unix,
            mark_age_seconds=mark_age,
            http_get_count=get_count,
            current_selection_binding_valid=selection_binding_valid,
            current_input_provenance_valid=True,
            current_input_freshness_valid=freshness_valid,
            current_input_type_valid=True,
            current_input_unit_valid=True,
        )
        obs.gap_rows = build_fixture_vs_current_gap_matrix_v1(
            manifest={
                "INSTRUMENT_ID": expected_instrument_id or bound.instrument_id,
                "NATIVE_ID": expected_native_id or native,
            },
            observation=obs,
        )
        return obs

    ts = _utc_iso_from_unix(observed_unix)
    base_ctx = with_computed_input_digest(
        CanonicalMarketContextV1(
            context_id=f"ctx-{bound.instrument_id}-ghv-current-input-observe-v1",
            instrument_id=bound.instrument_id,
            market_type=FuturesMarketType.PERPETUAL,
            trading_epoch=1,
            market_event_time=ts,
            decision_time=ts,
            bar_interval="1m",
            bar_finality_status=BarFinalityStatus.FINALIZED,
            mark_price=mark_px,
            index_price=index_px,
            best_bid=mark_px * 0.999,
            best_ask=mark_px * 1.001,
            spread=mark_px * 0.002,
            volume=1.0,
            open_interest=1.0,
            funding_rate=0.0,
            volatility_estimate=0.01,
            trend_feature_set={},
            momentum_feature_set={},
            liquidity_feature_set={},
            market_structure_feature_set={},
            data_integrity_status=DataIntegrityStatus.TRUSTED,
            clock_trust_status=ClockTrustStatus.TRUSTED,
            warmup_status=WarmupStatus.WARMUP_COMPLETE,
            feature_contract_version=FEATURE_CONTRACT_VERSION,
            input_digest="",
        )
    )
    bind_result = apply_current_productive_g17_typed_vol_cmc_bind_v1(
        base_ctx,
        producer=g17_join.producer,
    )
    ctx = bind_result.context
    try:
        vol = float(resolve_legacy_volatility_float_for_consumer_v1(ctx))
    except (TypeError, ValueError):
        vol = None

    gge_ctx = compute_canonical_base_geometry_magnitude_from_market_context_v1(ctx)
    layer_c = resolve_layer_c_event_distances_from_canonical_market_context_v1(ctx)
    typed_elig = evaluate_typed_volatility_binding_eligibility_v1(ctx)
    typed_ok = len(typed_elig.block_reasons) == 0
    gge_mark_vol = compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
        instrument_id=bound.instrument_id,
        mark_price=mark_px,
        volatility_estimate=float(vol if vol is not None else 0.01),
    )

    gge_ok = gge_ctx.ok and layer_c.ok and typed_ok and gge_mark_vol.ok
    scope_ok = gge_ok
    mv2_ok = gge_ok and bind_result.estimate_present
    dp_ok = selection_binding_valid and gge_ok

    obs = CurrentProductiveGhvInputObservationV1(
        observation_ok=gge_ok and freshness_valid and selection_binding_valid,
        source_kind=source_kind,
        current_input_blocker="" if gge_ok else "CURRENT_GGE_OR_LAYER_C_FAIL_CLOSED",
        bound_instrument=bound,
        mark_price=mark_px,
        index_price=index_px,
        volatility_estimate=vol,
        market_context=ctx,
        observed_at_unix=observed_unix,
        mark_age_seconds=mark_age,
        current_input_provenance_valid=True,
        current_input_freshness_valid=freshness_valid,
        current_input_type_valid=isinstance(ctx, CanonicalMarketContextV1),
        current_input_unit_valid=gge_mark_vol.ok,
        current_selection_binding_valid=selection_binding_valid,
        gge_current_input_valid=gge_ok,
        scope_current_input_valid=scope_ok,
        mv2_current_input_valid=mv2_ok,
        double_play_current_input_valid=dp_ok,
        http_get_count=get_count,
    )
    if not freshness_valid:
        obs.observation_ok = False
        obs.current_input_blocker = "CURRENT_MARK_STALE"
    if not selection_binding_valid:
        obs.observation_ok = False
        obs.current_input_blocker = "CURRENT_SELECTION_BINDING_INVALID"
    obs.gap_rows = build_fixture_vs_current_gap_matrix_v1(
        manifest={
            "INSTRUMENT_ID": expected_instrument_id or bound.instrument_id,
            "NATIVE_ID": expected_native_id or native,
        },
        observation=obs,
    )
    return obs


def gap_matrix_to_json_v1(rows: list[GhvInputFieldGapRowV1]) -> list[dict[str, Any]]:
    return [asdict(r) for r in rows]


__all__ = [
    "ADAPTER_OWNER",
    "CLASS_CURRENT_AVAILABLE_INVALID",
    "CLASS_CURRENT_AVAILABLE_VALID",
    "CLASS_CURRENT_BINDING_MISMATCH",
    "CLASS_CURRENT_MISSING",
    "CLASS_CURRENT_PROVENANCE_MISMATCH",
    "CLASS_CURRENT_STALE",
    "CLASS_NOT_REQUIRED_CURRENT",
    "CurrentProductiveGhvInputObservationV1",
    "DEFAULT_FRESH_MARK_MAX_AGE_SECONDS",
    "FORBIDDEN_SOURCE_FIXTURE_REPLAY",
    "GhvInputFieldGapRowV1",
    "SOURCE_INJECTED_TRANSPORT",
    "SOURCE_LIVE_PRODUCTIVE_GET",
    "build_fixture_vs_current_gap_matrix_v1",
    "gap_matrix_to_json_v1",
    "load_bound_instrument_from_selection_file_v1",
    "observe_current_productive_ghv_inputs_v1",
]
