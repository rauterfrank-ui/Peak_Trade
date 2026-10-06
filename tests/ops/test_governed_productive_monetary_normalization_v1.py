"""Fail-closed + GHV dimensional parity for monetary normalization v1."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
)
from src.ops.governed_productive_monetary_normalization_v1.constants_v1 import (
    CANONICAL_INTERNAL_RISK_NUMERAIRE,
    NORMALIZED_RATE_UNIT_USDC_PER_USDT,
    RAW_RATE_UNIT_USDT_PER_USDC,
    USDT_USDC_ENDPOINT,
    USDT_USDC_SOURCE_IDENTITY,
)
from src.ops.governed_productive_monetary_normalization_v1.contracts_v1 import (
    REASON_AMBIGUOUS_DIRECTION,
    REASON_CONVERSION_TARGET_NOT_NUMERAIRE,
    REASON_DOUBLE_CONVERSION,
    REASON_EPOCH_MISMATCH,
    REASON_MISSING_EDGE,
    REASON_MISSING_PROVENANCE,
    REASON_MISSING_SOURCE_TIMESTAMP,
    REASON_NAKED_DECIMAL_FX,
    REASON_NON_POSITIVE_RATE,
    REASON_QUOTE_CURRENCY_MISMATCH,
    REASON_STALE_RATE,
    REASON_UNAUTHORIZED_SOURCE,
    REASON_UNKNOWN_RATE_UNIT,
    REASON_UNKNOWN_SOURCE_CURRENCY,
    REASON_UNKNOWN_TARGET_CURRENCY,
    ConversionEdgeV1,
    MonetaryAmountV1,
    MonetaryNormalizationError,
    require_monetary_amount_v1,
    validate_conversion_edge_v1,
)
from src.ops.governed_productive_monetary_normalization_v1.identity_edge_v1 import (
    build_usdc_identity_conversion_edge_v1,
)
from src.ops.governed_productive_monetary_normalization_v1.normalize_v1 import (
    build_capital_risk_sizing_monetary_context_v1,
    crs_operands_from_monetary_context_v1,
)
from src.ops.governed_productive_monetary_normalization_v1.usdt_usdc_index_observation_v1 import (
    build_usdt_usdc_conversion_edge_from_index_tickers_v1,
)
from tests.ops._monetary_normalization_test_helpers_v1 import (
    api3_usdt_swap_instruments_row_v1,
    combined_instruments_payload_v1,
    conversion_pair_instruments_payload_v1,
    usdc_usdt_swap_instruments_row_v1,
    usdt_usdc_index_tickers_payload_v1,
)

_EPOCH = "2026-09-17T06:50:00Z"
_TRUSTED = FreshPretradeGetStatusV1.TRUSTED_PRESENT.value


def _base_kwargs() -> dict[str, object]:
    return {
        "decision_epoch": _EPOCH,
        "observed_at": _EPOCH,
        "fresh_pretrade_get_status": _TRUSTED,
        "account_equity_amount": Decimal("777.77"),
        "account_equity_currency": "USDC",
        "native_reference_price": Decimal("0.3403"),
        "native_protective_stop_price": Decimal("0.2603"),
        "instruments_payload": combined_instruments_payload_v1(
            api3_usdt_swap_instruments_row_v1(),
            usdc_usdt_swap_instruments_row_v1(),
        ),
        "venue_native_id": "API3-USDT-SWAP",
        "index_tickers_payload": usdt_usdc_index_tickers_payload_v1(),
        "conversion_pair_instruments_payload": conversion_pair_instruments_payload_v1(),
    }


def test_valid_usdt_usdc_edge_and_identity() -> None:
    ctx = build_capital_risk_sizing_monetary_context_v1(**_base_kwargs())  # type: ignore[arg-type]
    assert ctx.usdt_usdc_edge is not None
    assert ctx.usdc_identity_edge.normalized_rate == Decimal("1")
    eq, ref, stop = crs_operands_from_monetary_context_v1(ctx)
    assert eq == Decimal("777.77")
    assert ref > Decimal("0.3403")
    assert stop > Decimal("0.2603")
    assert ctx.reference_price.currency == CANONICAL_INTERNAL_RISK_NUMERAIRE


def test_missing_edge() -> None:
    kwargs = _base_kwargs()
    kwargs["index_tickers_payload"] = None
    with pytest.raises(MonetaryNormalizationError, match=REASON_MISSING_EDGE):
        build_capital_risk_sizing_monetary_context_v1(**kwargs)  # type: ignore[arg-type]


def test_unknown_source_currency_on_amount() -> None:
    with pytest.raises(MonetaryNormalizationError, match=REASON_UNKNOWN_SOURCE_CURRENCY):
        MonetaryAmountV1(amount=Decimal("1"), currency="")


def test_unknown_target_on_bad_edge() -> None:
    edge = build_usdt_usdc_conversion_edge_from_index_tickers_v1(
        index_tickers_payload=usdt_usdc_index_tickers_payload_v1(),
        decision_epoch=_EPOCH,
        observed_at=_EPOCH,
        fresh_pretrade_get_status=_TRUSTED,
        pair_base_currency="USDC",
        pair_quote_currency="USDT",
    )
    bad = ConversionEdgeV1(
        **{
            **edge.__dict__,
            "target_currency": "",
        }
    )
    with pytest.raises(MonetaryNormalizationError, match=REASON_UNKNOWN_TARGET_CURRENCY):
        validate_conversion_edge_v1(bad)


def test_unknown_rate_unit() -> None:
    edge = build_usdt_usdc_conversion_edge_from_index_tickers_v1(
        index_tickers_payload=usdt_usdc_index_tickers_payload_v1(),
        decision_epoch=_EPOCH,
        observed_at=_EPOCH,
        fresh_pretrade_get_status=_TRUSTED,
        pair_base_currency="USDC",
        pair_quote_currency="USDT",
    )
    bad = ConversionEdgeV1(**{**edge.__dict__, "raw_rate_unit": ""})
    with pytest.raises(MonetaryNormalizationError, match=REASON_UNKNOWN_RATE_UNIT):
        validate_conversion_edge_v1(bad)


def test_ambiguous_direction_wrong_pair_metadata() -> None:
    with pytest.raises(MonetaryNormalizationError, match=REASON_AMBIGUOUS_DIRECTION):
        build_usdt_usdc_conversion_edge_from_index_tickers_v1(
            index_tickers_payload=usdt_usdc_index_tickers_payload_v1(),
            decision_epoch=_EPOCH,
            observed_at=_EPOCH,
            fresh_pretrade_get_status=_TRUSTED,
            pair_base_currency="BTC",
            pair_quote_currency="USDT",
        )


def test_zero_rate() -> None:
    with pytest.raises(MonetaryNormalizationError, match=REASON_NON_POSITIVE_RATE):
        build_usdt_usdc_conversion_edge_from_index_tickers_v1(
            index_tickers_payload=usdt_usdc_index_tickers_payload_v1(idx_px="0"),
            decision_epoch=_EPOCH,
            observed_at=_EPOCH,
            fresh_pretrade_get_status=_TRUSTED,
            pair_base_currency="USDC",
            pair_quote_currency="USDT",
        )


def test_negative_rate() -> None:
    with pytest.raises(MonetaryNormalizationError, match=REASON_NON_POSITIVE_RATE):
        build_usdt_usdc_conversion_edge_from_index_tickers_v1(
            index_tickers_payload=usdt_usdc_index_tickers_payload_v1(idx_px="-1"),
            decision_epoch=_EPOCH,
            observed_at=_EPOCH,
            fresh_pretrade_get_status=_TRUSTED,
            pair_base_currency="USDC",
            pair_quote_currency="USDT",
        )


def test_malformed_rate() -> None:
    with pytest.raises(MonetaryNormalizationError, match="MALFORMED_RATE"):
        build_usdt_usdc_conversion_edge_from_index_tickers_v1(
            index_tickers_payload={"code": "0", "data": [{"instId": "USDC-USDT", "idxPx": "bad"}]},
            decision_epoch=_EPOCH,
            observed_at=_EPOCH,
            fresh_pretrade_get_status=_TRUSTED,
            pair_base_currency="USDC",
            pair_quote_currency="USDT",
        )


def test_stale_rate() -> None:
    with pytest.raises(MonetaryNormalizationError, match=REASON_STALE_RATE):
        build_usdt_usdc_conversion_edge_from_index_tickers_v1(
            index_tickers_payload=usdt_usdc_index_tickers_payload_v1(),
            decision_epoch=_EPOCH,
            observed_at=_EPOCH,
            fresh_pretrade_get_status=FreshPretradeGetStatusV1.STALE.value,
            pair_base_currency="USDC",
            pair_quote_currency="USDT",
        )


def test_epoch_mismatch() -> None:
    with pytest.raises(MonetaryNormalizationError, match=REASON_EPOCH_MISMATCH):
        build_usdt_usdc_conversion_edge_from_index_tickers_v1(
            index_tickers_payload=usdt_usdc_index_tickers_payload_v1(),
            decision_epoch="",
            observed_at=_EPOCH,
            fresh_pretrade_get_status=_TRUSTED,
            pair_base_currency="USDC",
            pair_quote_currency="USDT",
        )


def test_unauthorized_source_endpoint() -> None:
    edge = build_usdt_usdc_conversion_edge_from_index_tickers_v1(
        index_tickers_payload=usdt_usdc_index_tickers_payload_v1(),
        decision_epoch=_EPOCH,
        observed_at=_EPOCH,
        fresh_pretrade_get_status=_TRUSTED,
        pair_base_currency="USDC",
        pair_quote_currency="USDT",
    )
    bad = ConversionEdgeV1(**{**edge.__dict__, "endpoint": "/api/v5/market/ticker"})
    with pytest.raises(MonetaryNormalizationError, match=REASON_UNAUTHORIZED_SOURCE):
        validate_conversion_edge_v1(bad)


def test_missing_provenance() -> None:
    edge = build_usdt_usdc_conversion_edge_from_index_tickers_v1(
        index_tickers_payload=usdt_usdc_index_tickers_payload_v1(),
        decision_epoch=_EPOCH,
        observed_at=_EPOCH,
        fresh_pretrade_get_status=_TRUSTED,
        pair_base_currency="USDC",
        pair_quote_currency="USDT",
    )
    bad = ConversionEdgeV1(**{**edge.__dict__, "provenance_ref": ""})
    with pytest.raises(MonetaryNormalizationError, match=REASON_MISSING_PROVENANCE):
        validate_conversion_edge_v1(bad)


def test_missing_source_timestamp() -> None:
    payload = {"code": "0", "data": [{"instId": "USDC-USDT", "idxPx": "0.999676"}]}
    with pytest.raises(MonetaryNormalizationError, match=REASON_MISSING_SOURCE_TIMESTAMP):
        build_usdt_usdc_conversion_edge_from_index_tickers_v1(
            index_tickers_payload=payload,
            decision_epoch=_EPOCH,
            observed_at=_EPOCH,
            fresh_pretrade_get_status=_TRUSTED,
            pair_base_currency="USDC",
            pair_quote_currency="USDT",
        )


def test_missing_instrument_monetary_identity() -> None:
    kwargs = _base_kwargs()
    kwargs["instruments_payload"] = {"code": "0", "data": []}
    with pytest.raises(MonetaryNormalizationError, match="INSTRUMENT_MONETARY_IDENTITY_MISSING"):
        build_capital_risk_sizing_monetary_context_v1(**kwargs)  # type: ignore[arg-type]


def test_quote_currency_mismatch_on_equity() -> None:
    kwargs = _base_kwargs()
    kwargs["account_equity_currency"] = "USDT"
    with pytest.raises(MonetaryNormalizationError, match=REASON_QUOTE_CURRENCY_MISMATCH):
        build_capital_risk_sizing_monetary_context_v1(**kwargs)  # type: ignore[arg-type]


def test_conversion_target_not_numeraire() -> None:
    edge = build_usdt_usdc_conversion_edge_from_index_tickers_v1(
        index_tickers_payload=usdt_usdc_index_tickers_payload_v1(),
        decision_epoch=_EPOCH,
        observed_at=_EPOCH,
        fresh_pretrade_get_status=_TRUSTED,
        pair_base_currency="USDC",
        pair_quote_currency="USDT",
    )
    bad = ConversionEdgeV1(**{**edge.__dict__, "target_currency": "EUR"})
    with pytest.raises(MonetaryNormalizationError, match=REASON_CONVERSION_TARGET_NOT_NUMERAIRE):
        validate_conversion_edge_v1(bad)


def test_double_conversion_rejection() -> None:
    kwargs = _base_kwargs()
    kwargs["already_canonical"] = True
    with pytest.raises(MonetaryNormalizationError, match=REASON_DOUBLE_CONVERSION):
        build_capital_risk_sizing_monetary_context_v1(**kwargs)  # type: ignore[arg-type]


def test_naked_decimal_fx_rejection() -> None:
    with pytest.raises(MonetaryNormalizationError, match=REASON_NAKED_DECIMAL_FX):
        require_monetary_amount_v1(Decimal("1"), field="reference_price")


def test_ghv_dimensional_parity_static_chain() -> None:
    """API3-USDT-SWAP: native USDT/contract operands × USDC/USDT → USDC/contract."""
    idx_px = Decimal("0.999676")
    r_usdc_per_usdt = Decimal("1") / idx_px
    stop_distance = Decimal("80")
    ct_val = Decimal("1")
    ref = Decimal("0.3403")
    risk_native = stop_distance * ct_val
    notional_native = ref * ct_val
    risk_usdc = risk_native * r_usdc_per_usdt
    notional_usdc = notional_native * r_usdc_per_usdt
    capital_usdc = Decimal("777.77")
    qty_risk_cap = capital_usdc / risk_usdc
    qty_notional_cap = capital_usdc / notional_usdc
    assert risk_native == Decimal("80")
    assert notional_native == ref
    assert risk_usdc > risk_native
    assert qty_risk_cap < capital_usdc / risk_native


def test_identity_edge_explicit() -> None:
    edge = build_usdc_identity_conversion_edge_v1(
        decision_epoch=_EPOCH,
        observed_at=_EPOCH,
    )
    assert edge.inversion_applied is False
    assert edge.normalized_rate_unit == "USDC/USDC"


def test_adjudicated_endpoint_constants() -> None:
    edge = build_usdt_usdc_conversion_edge_from_index_tickers_v1(
        index_tickers_payload=usdt_usdc_index_tickers_payload_v1(),
        decision_epoch=_EPOCH,
        observed_at=_EPOCH,
        fresh_pretrade_get_status=_TRUSTED,
        pair_base_currency="USDC",
        pair_quote_currency="USDT",
    )
    assert edge.endpoint == USDT_USDC_ENDPOINT
    assert edge.source_identity == USDT_USDC_SOURCE_IDENTITY
    assert edge.raw_rate_unit == RAW_RATE_UNIT_USDT_PER_USDC
    assert edge.normalized_rate_unit == NORMALIZED_RATE_UNIT_USDC_PER_USDT
    assert edge.inversion_applied is True


def test_productive_fx_get_enrolled_in_fresh_pretrade_v1() -> None:
    from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
        ENDPOINT_PUBLIC_INSTRUMENTS,
        REQUIRED_GET_ITEM_SPECS,
        build_required_get_endpoint_v1,
        collect_fresh_pretrade_runtime_get_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
        TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
        FreshPretradeGetTransportResultV1,
    )

    fx_specs = [
        spec
        for spec in REQUIRED_GET_ITEM_SPECS
        if spec.item_id == "MONETARY_NORMALIZATION_USDT_USDC_INDEX"
    ]
    assert len(fx_specs) == 1
    spec = fx_specs[0]
    endpoint = build_required_get_endpoint_v1(
        spec,
        instrument_id="API3-USDT-SWAP",
        td_mode="cross",
        limit_px="",
    )
    assert endpoint == f"{USDT_USDC_ENDPOINT}?instId={USDT_USDC_SOURCE_IDENTITY}"

    class _RecordingTransport:
        transport_class = TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET
        venue_live_contact = True
        payloads_by_path: dict[str, object] = {}

        def __init__(self) -> None:
            self.endpoints: list[str] = []

        def get(self, *, endpoint, auth_required, pretrade_decision_id):
            self.endpoints.append(str(endpoint))
            path = str(endpoint).split("?", 1)[0]
            text = str(endpoint)
            if path == ENDPOINT_PUBLIC_INSTRUMENTS and "USDC-USDT-SWAP" in text:
                payload: dict[str, object] = conversion_pair_instruments_payload_v1()
            elif path == ENDPOINT_PUBLIC_INSTRUMENTS:
                payload = {"code": "0", "data": [{"instId": "API3-USDT-SWAP"}]}
            elif path == USDT_USDC_ENDPOINT:
                payload = usdt_usdc_index_tickers_payload_v1()
            else:
                payload = {"code": "0", "data": [{"instId": "API3-USDT-SWAP"}]}
            self.payloads_by_path[path] = payload
            return FreshPretradeGetTransportResultV1(
                get_performed=True,
                method="GET",
                endpoint=endpoint,
                http_status=200,
                payload=payload,
                auth_header_sent=bool(auth_required),
                transport_class=self.transport_class,
                venue_live_contact=True,
                historical_reuse=False,
                error_class="",
            )

    transport = _RecordingTransport()
    evidence = collect_fresh_pretrade_runtime_get_v1(
        pretrade_decision_id=_EPOCH,
        instrument_id="API3-USDT-SWAP",
        td_mode="cross",
        inst_type="SWAP",
        transport=transport,
        require_collection=True,
    )
    assert any(
        endpoint == f"{USDT_USDC_ENDPOINT}?instId={USDT_USDC_SOURCE_IDENTITY}"
        for endpoint in transport.endpoints
    )
    fx_item = next(
        item for item in evidence.items if item.item_id == "MONETARY_NORMALIZATION_USDT_USDC_INDEX"
    )
    assert fx_item.evidence_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value


def test_productive_conversion_pair_get_enrolled_in_fresh_pretrade_v1() -> None:
    from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
        ENDPOINT_PUBLIC_INSTRUMENTS,
        REQUIRED_GET_ITEM_SPECS,
        FreshPretradeGetTransportResultV1,
        TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
        build_required_get_endpoint_v1,
        collect_fresh_pretrade_runtime_get_v1,
    )
    from src.ops.governed_productive_monetary_normalization_v1.constants_v1 import (
        USDT_USDC_PAIR_NATIVE_ID,
    )

    pair_specs = [
        spec
        for spec in REQUIRED_GET_ITEM_SPECS
        if spec.item_id == "MONETARY_NORMALIZATION_CONVERSION_PAIR_INSTRUMENTS"
    ]
    assert len(pair_specs) == 1
    spec = pair_specs[0]
    endpoint = build_required_get_endpoint_v1(
        spec,
        instrument_id="API3-USDT-SWAP",
        td_mode="cross",
        limit_px="",
        inst_type="SWAP",
    )
    assert endpoint == (
        f"{ENDPOINT_PUBLIC_INSTRUMENTS}?instType=SWAP&instId={USDT_USDC_PAIR_NATIVE_ID}"
    )

    class _RecordingTransport:
        transport_class = TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET
        venue_live_contact = True

        def __init__(self) -> None:
            self.endpoints: list[str] = []

        def get(self, *, endpoint, auth_required, pretrade_decision_id):
            self.endpoints.append(str(endpoint))
            path = str(endpoint).split("?", 1)[0]
            if path == ENDPOINT_PUBLIC_INSTRUMENTS and USDT_USDC_PAIR_NATIVE_ID in str(endpoint):
                payload = conversion_pair_instruments_payload_v1()
            else:
                payload = {"code": "0", "data": [{"instId": "API3-USDT-SWAP"}]}
            return FreshPretradeGetTransportResultV1(
                get_performed=True,
                method="GET",
                endpoint=endpoint,
                http_status=200,
                payload=payload,
                auth_header_sent=bool(auth_required),
                transport_class=TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
                venue_live_contact=True,
                historical_reuse=False,
                error_class="",
            )

    transport = _RecordingTransport()
    evidence = collect_fresh_pretrade_runtime_get_v1(
        pretrade_decision_id=_EPOCH,
        instrument_id="API3-USDT-SWAP",
        td_mode="cross",
        inst_type="SWAP",
        transport=transport,
        require_collection=True,
    )
    assert any(USDT_USDC_PAIR_NATIVE_ID in ep for ep in transport.endpoints)
    pair_item = next(
        item
        for item in evidence.items
        if item.item_id == "MONETARY_NORMALIZATION_CONVERSION_PAIR_INSTRUMENTS"
    )
    assert pair_item.evidence_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
    assert USDT_USDC_PAIR_NATIVE_ID in pair_item.observed_inst_ids


def test_common_epoch_handoff_keeps_bound_and_conversion_pair_payloads_separate_v1() -> None:
    bound, _handoff, injected, _transport = _api3_productive_handoff_injected_v1()
    assert injected.conversion_pair_instruments_payload is not None
    assert injected.instruments_payload is not injected.conversion_pair_instruments_payload
    pair_data = injected.conversion_pair_instruments_payload.get("data")
    bound_data = injected.instruments_payload.get("data")
    assert isinstance(pair_data, list) and isinstance(bound_data, list)
    pair_ids = {str(row.get("instId")) for row in pair_data if isinstance(row, dict)}
    bound_ids = {str(row.get("instId")) for row in bound_data if isinstance(row, dict)}
    assert "USDC-USDT-SWAP" in pair_ids
    assert bound.venue_native_id in bound_ids
    assert bound.venue_native_id not in pair_ids


def test_common_epoch_handoff_fail_closed_without_conversion_pair_metadata_v1() -> None:
    from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
        ENDPOINT_PUBLIC_INSTRUMENTS,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_common_epoch_to_enter_live_29p_handoff_v1 import (
        CurrentProductiveCommonEpochToEnterLive29PHandoffError,
        build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1,
    )
    from src.ops.governed_productive_monetary_normalization_v1.constants_v1 import (
        USDT_USDC_PAIR_NATIVE_ID,
    )
    from tests.ops.test_full_core_current_productive_29p_common_epoch_handoff_v1 import (
        _identity_payloads,
    )
    from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
        ProductiveClassFreshGetTransportV1,
    )

    bound, handoff, _injected, _transport = _api3_productive_handoff_injected_v1()
    payloads = dict(_identity_payloads(instrument_id=bound.venue_native_id))
    del payloads[f"{ENDPOINT_PUBLIC_INSTRUMENTS}#instId={USDT_USDC_PAIR_NATIVE_ID}"]
    transport = ProductiveClassFreshGetTransportV1(payloads=payloads)
    with pytest.raises(CurrentProductiveCommonEpochToEnterLive29PHandoffError):
        build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1(
            handoff=handoff,
            transport=transport,
        )


def _api3_productive_handoff_injected_v1():
    from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
        ENDPOINT_PUBLIC_INSTRUMENTS,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_common_epoch_handoff_v1 import (
        compose_current_productive_29p_common_epoch_handoff_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_common_epoch_to_enter_live_29p_handoff_v1 import (
        build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1,
    )
    from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
        MAX_POSITIONS_EFFECTIVE,
        STATE_SELECTED_ACTIVE,
    )
    from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
    from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
        ProductiveClassFreshGetTransportV1,
    )
    from tests.ops.test_full_core_current_productive_29p_common_epoch_handoff_v1 import (
        _identity_payloads,
    )

    api3 = "API3-USDT-SWAP"
    bound = BoundInstrumentV1(
        instrument_id=f"cap24-{api3}",
        venue_native_id=api3,
        ranking_snapshot_id="rank-api3-1",
        ranking_integrity_digest="rank-digest-api3-1",
        universe_snapshot_id="uni-api3-1",
        selection_id="sel-api3-1",
        selection_integrity_digest="sel-digest-api3-1",
        selection_state=STATE_SELECTED_ACTIVE,
        selected_future_count=1,
        max_positions_effective=MAX_POSITIONS_EFFECTIVE,
    )
    from src.ops.governed_productive_monetary_normalization_v1.constants_v1 import (
        USDT_USDC_PAIR_NATIVE_ID,
    )

    payloads = dict(_identity_payloads(instrument_id=api3))
    payloads[f"{ENDPOINT_PUBLIC_INSTRUMENTS}#instId={USDT_USDC_PAIR_NATIVE_ID}"] = (
        combined_instruments_payload_v1(usdc_usdt_swap_instruments_row_v1())
    )
    transport = ProductiveClassFreshGetTransportV1(payloads=payloads)
    handoff = compose_current_productive_29p_common_epoch_handoff_v1(
        decision_epoch=_EPOCH,
        bound_instrument=bound,
        fresh_get_transport=transport,
        inst_type="SWAP",
    )
    injected = build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1(
        handoff=handoff,
        transport=transport,
    )
    return bound, handoff, injected, transport


def test_productive_common_epoch_fx_transport_and_epoch_bound_v1() -> None:
    bound, handoff, injected, _transport = _api3_productive_handoff_injected_v1()
    assert handoff.decision_epoch == _EPOCH
    assert handoff.get_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
    assert injected.index_tickers_payload is not None
    assert injected.fresh_pretrade_get_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
    edge = build_usdt_usdc_conversion_edge_from_index_tickers_v1(
        index_tickers_payload=injected.index_tickers_payload,
        decision_epoch=_EPOCH,
        observed_at=_EPOCH,
        fresh_pretrade_get_status=_TRUSTED,
        pair_base_currency="USDC",
        pair_quote_currency="USDT",
    )
    assert edge.decision_epoch == _EPOCH
    assert edge.source_identity == USDT_USDC_SOURCE_IDENTITY
    assert bound.venue_native_id == "API3-USDT-SWAP"


def test_ghv_api3_productive_normalization_join_venue_plan_v1() -> None:
    """API3-USDT-SWAP monetary chain + productive join/venue plan on host-enter replay."""
    from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
        STATUS_PASS,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_common_epoch_to_enter_live_29p_handoff_v1 import (
        build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
        join_current_productive_enter_live_29p_before_venue_plan_v1,
    )
    from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
        _enter_replay,
    )
    from tests.ops.test_full_core_current_productive_host_enter_29p_invalid_stop_price_repair_v1 import (
        _host_enter_cycle,
    )
    from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
        _compose_handoff,
        _bound,
    )
    from tests.ops.test_full_core_current_productive_29p_common_epoch_handoff_v1 import (
        _EPOCH as _COMMON_EPOCH,
    )

    bound_api3, _handoff_api3, injected_api3, _ = _api3_productive_handoff_injected_v1()
    ctx = build_capital_risk_sizing_monetary_context_v1(
        decision_epoch=_EPOCH,
        observed_at=_EPOCH,
        fresh_pretrade_get_status=_TRUSTED,
        account_equity_amount=Decimal("123.45"),
        account_equity_currency=CANONICAL_INTERNAL_RISK_NUMERAIRE,
        native_reference_price=Decimal("0.3403"),
        native_protective_stop_price=Decimal("0.2603"),
        instruments_payload=injected_api3.instruments_payload,
        venue_native_id=bound_api3.venue_native_id,
        index_tickers_payload=injected_api3.index_tickers_payload,
        conversion_pair_instruments_payload=injected_api3.conversion_pair_instruments_payload,
    )
    assert ctx.account_equity.currency == "USDC"
    assert ctx.usdt_usdc_edge is not None
    assert ctx.usdt_usdc_edge.inversion_applied is True
    assert bound_api3.venue_native_id == "API3-USDT-SWAP"

    from unittest.mock import patch

    with patch(
        "src.ops.governed_productive_account_equity_authority_producer_v1."
        "current_productive_29p_common_epoch_handoff_v1._utc_now_iso_v1",
        return_value=_COMMON_EPOCH,
    ):
        handoff, transport = _compose_handoff()
    injected = build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1(
        handoff=handoff,
        transport=transport,
    )
    _, cycle_b, _path = _host_enter_cycle()
    replay = _enter_replay(cycle_b)
    join = join_current_productive_enter_live_29p_before_venue_plan_v1(
        replay=replay,
        injected=injected,
        bound_instrument=_bound(),
        decision_epoch=str(handoff.decision_epoch),
    )
    assert join.status == STATUS_PASS
    assert join.venue_plan_authorized is True
    assert join.step_29p_risk_admissible == "true"
    rebound = join.replay
    assert rebound is not None
    sizing = rebound.intermediate.capital_risk_sizing_decision
    assert sizing is not None
    assert str(getattr(sizing.outcome, "value", sizing.outcome)) == "PASS"
    intent = rebound.intermediate.canonical_order_intent
    assert intent is not None
    assert intent.quantity_unit == "CONTRACTS"
