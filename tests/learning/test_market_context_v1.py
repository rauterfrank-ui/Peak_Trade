"""MARKET_CONTEXT_V1 contract and governance tests (offline; AUTHORITY=NONE)."""

from __future__ import annotations

import json

import pytest

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_v1 import (
    CONTEXT_FAMILY_SLOT_SCHEMA,
    CROSS_MARKET_CONTEXT_ONLY,
    MICROSTRUCTURE_KIND_PROXY_OHLCV,
    MICROSTRUCTURE_KIND_TRUE_L2,
    GovernedMarketContextInputsV1,
    MarketContextValidationError,
    compose_market_context_v1_from_governed_inputs,
    derive_information_set_ref_v1,
    serialize_market_context_canonical_v1,
    validate_market_context_v1,
)

_OBSERVED = "2026-09-26T12:00:00Z"
_INSTRUMENT = "inst.SUI-USD_UM_XPERP.test"
_INFO_BODY = {
    "instrument_ref": _INSTRUMENT,
    "observed_at": _OBSERVED,
    "pit_fact_refs": ["fact.wp_a.mark.0001"],
}


def _present_slot(
    *,
    state_ref: str,
    producer_owner: str,
    pit: str = "2026-09-26T11:59:00Z",
    extra: dict | None = None,
) -> dict:
    body = {
        "schema_version": CONTEXT_FAMILY_SLOT_SCHEMA,
        "presence": "PRESENT",
        "state_ref": state_ref,
        "pit_observed_at_utc": pit,
        "producer_owner": producer_owner,
        "producer_ownership": "GOVERNED",
        "feature_version": "v1",
    }
    if extra:
        body.update(extra)
    return body


def _minimal_compose(**overrides) -> dict:
    inputs = GovernedMarketContextInputsV1(
        observed_at=_OBSERVED,
        instrument_ref=_INSTRUMENT,
        information_set_identity_body=_INFO_BODY,
        provenance_refs=["prov.canonical.fact.0001"],
        feature_versions={"market_context_v1": "v1"},
        price_state=_present_slot(
            state_ref="fact.wp_a.mark.0001",
            producer_owner="ops.peak_trade_public_market_data_runtime_v1",
        ),
        volatility_state=_present_slot(
            state_ref="fact.i25.vol.0001",
            producer_owner="trading.master_v2.canonical_volatility_estimate_feature_contract_v1",
        ),
        **overrides,
    )
    return dict(compose_market_context_v1_from_governed_inputs(inputs))


def test_compose_missing_families_explicit_not_zero_filled() -> None:
    record = _minimal_compose()
    assert record["flow_state_ref"]["presence"] == "MISSING"
    assert record["flow_state_ref"]["state_ref"] is None
    assert record["derivatives_state_ref"]["presence"] == "MISSING"
    assert record["liquidity_microstructure_state_ref"]["presence"] == "MISSING"


def test_information_set_identity_deterministic() -> None:
    record = _minimal_compose()
    expected = derive_information_set_ref_v1(identity_body=_INFO_BODY)
    assert record["information_set_ref"] == expected


def test_pit_lookahead_rejected() -> None:
    record = _minimal_compose()
    record["price_state_ref"] = _present_slot(
        state_ref="fact.wp_a.mark.0001",
        producer_owner="ops.peak_trade_public_market_data_runtime_v1",
        pit="2026-09-26T12:01:00Z",
    )
    with pytest.raises(MarketContextValidationError, match="LOOKAHEAD"):
        validate_market_context_v1(record)


def test_unknown_mixed_ownership_fail_closed() -> None:
    record = _minimal_compose()
    record["flow_state_ref"] = {
        "schema_version": CONTEXT_FAMILY_SLOT_SCHEMA,
        "presence": "MISSING",
        "state_ref": None,
        "missing_reason": "UNOWNED",
        "producer_ownership": "UNKNOWN",
    }
    with pytest.raises(MarketContextValidationError, match="OWNERSHIP_FAIL_CLOSED"):
        validate_market_context_v1(record)


def test_microstructure_proxy_and_l2_must_not_collapse() -> None:
    with pytest.raises(MarketContextValidationError, match="COLLAPSE"):
        _minimal_compose(
            liquidity_microstructure_state=_present_slot(
                state_ref="fact.micro.proxy.0001",
                producer_owner="research.bouchaud_microstructure_ohlcv_proxy_v1",
                extra={
                    "microstructure_kind": MICROSTRUCTURE_KIND_PROXY_OHLCV,
                    "microstructure_kind_collapsed": True,
                },
            )
        )

    ok = _minimal_compose(
        liquidity_microstructure_state=_present_slot(
            state_ref="fact.micro.l2.0001",
            producer_owner="reserved.bouchaud_microstructure_tick_l2",
            extra={"microstructure_kind": MICROSTRUCTURE_KIND_TRUE_L2},
        )
    )
    assert (
        ok["liquidity_microstructure_state_ref"]["microstructure_kind"]
        == MICROSTRUCTURE_KIND_TRUE_L2
    )


def test_cross_market_context_only_no_rerank() -> None:
    with pytest.raises(MarketContextValidationError, match="RERANK"):
        _minimal_compose(
            cross_market_state=_present_slot(
                state_ref="fact.cross.0001",
                producer_owner="learning.market_intelligence_forecast_calibration_offline_stack_v1",
                extra={
                    "cross_market_authority": CROSS_MARKET_CONTEXT_ONLY,
                    "rerank_authorized": True,
                },
            )
        )


def test_authority_invariants_and_n_bars_backbone() -> None:
    record = _minimal_compose()
    assert record["market_context_authority"] == "NONE"
    assert record["n_bars_backbone_semantics"] == "N_BARS_REALIZED_OUTCOME_BACKBONE_UNCHANGED"


def test_serialization_deterministic() -> None:
    record = _minimal_compose()
    a = serialize_market_context_canonical_v1(record)
    b = serialize_market_context_canonical_v1(record)
    assert a == b
    assert json.loads(a)["context_id"] == record["context_id"]
