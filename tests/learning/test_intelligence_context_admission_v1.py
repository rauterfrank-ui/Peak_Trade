"""Actual original producers behind strict integration admission; all data synthetic."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import math

import pytest

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.context_admission_v1 import (
    ContextAdmissionPolicyV1,
    FactAdmissionReceiptV1,
    compose_admitted_intelligence_context_v1,
    compose_admitted_market_context_v1,
    replay_admitted_market_context_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    IntelligenceIdentityV1,
    MarketIdentityV1,
    bytes_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_existing_fact_materialization_v1 import (
    ExistingFactMaterializationRequestV1,
    GovernedCanonicalFactV1,
    WP_A_PRODUCER,
    materialize_market_context_v1_from_existing_facts_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    market_context_existing_fact_mi_bridge_v1 as bridge,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import fact_digest
from src.ops.peak_trade_public_market_data_runtime_v1.o4_pt1h_bar_fact_v1 import (
    FinalizedPt1hO4BarFactV1,
)

BASE = datetime(2026, 6, 1, tzinfo=timezone.utc)
IDENTITY = IntelligenceIdentityV1(
    "generation.1", "okx_eea", "inst.sui", "SUI-USDT-SWAP", "LANE_1", "epoch.1", "decision.1"
)


def mark(minute=60, price="100"):
    dt = BASE + timedelta(minutes=minute)
    payload = {
        "fact_kind": "FinalizedPt1mMarkFactV1",
        "interval_start_ms": int(dt.timestamp() * 1000),
        "mark_px": price,
        "instrument": {
            "canonical_instrument_id": IDENTITY.instrument_ref,
            "venue": IDENTITY.venue,
            "venue_native_id": IDENTITY.native_instrument_ref,
        },
        "timestamps": {
            "effective_at": dt.isoformat().replace("+00:00", "Z"),
            "captured_at": (dt + timedelta(seconds=61)).isoformat().replace("+00:00", "Z"),
        },
        "quality": {"finalized": True, "missing": False},
    }
    return GovernedCanonicalFactV1(
        payload["fact_kind"], fact_digest(payload), payload, WP_A_PRODUCER
    )


def inputs(*, volatility=False):
    facts = [mark(i, str(100 * math.exp(0.001 * i))) for i in range(61)] if volatility else [mark()]
    request = ExistingFactMaterializationRequestV1(
        observed_at=(BASE + timedelta(minutes=62)).isoformat().replace("+00:00", "Z"),
        instrument_ref=IDENTITY.instrument_ref,
        provenance_refs=("prov.original",),
        price_mark_fact=facts[-1],
        volatility_mark_facts=facts if volatility else None,
    )
    receipts = {
        f.fact_digest: FactAdmissionReceiptV1(
            "original." + f.fact_digest,
            IDENTITY.dataset_generation,
            bytes_v1(f.payload),
            f.payload["timestamps"]["captured_at"],
            f.payload["timestamps"]["captured_at"],
            {"price": "USDT_PER_SUI"},
        )
        for f in facts
    }
    return dict(
        identity=IDENTITY,
        request=request,
        receipts_by_digest=receipts,
        policy=ContextAdmissionPolicyV1(
            "explicit.synthetic.policy",
            {"price_mark": 120, "volatility": 120},
            ("price_state_ref",),
        ),
    )


def test_original_ids_values_and_inputs_survive_sidecar_and_abstention():
    args = inputs(volatility=True)
    before = deepcopy(args)
    legacy = dict(materialize_market_context_v1_from_existing_facts_v1(args["request"]))
    result = compose_admitted_intelligence_context_v1(**args)
    assert result["market_context"] == legacy
    assert args == before
    assert result["forecast_disposition"] == "ABSTAIN"
    assert result["forecast_reason"] == "NO_ADMITTED_FORECAST_PROVIDER"
    ref = legacy["volatility_state_ref"]["state_ref"]
    assert math.isfinite(float(result["derivations"][ref]["volatility_estimate"]))
    assert result == compose_admitted_intelligence_context_v1(**args)
    assert result["source_authenticated"] is False


def test_finalized_o4_float_values_keep_original_bytes_and_replay_exactly():
    identity = MarketIdentityV1(
        IDENTITY.dataset_generation,
        IDENTITY.venue,
        IDENTITY.instrument_ref,
        IDENTITY.native_instrument_ref,
    )
    captured = "2026-06-01T01:02:00Z"
    close = 100.12345678901235
    opened = BASE.timestamp()
    payload = FinalizedPt1hO4BarFactV1(
        bar={
            "canonical_instrument_id": identity.instrument_ref,
            "venue_instrument_id": identity.native_instrument_ref,
            "venue": identity.venue,
            "interval": "PT1H",
            "bar_open_time": opened,
            "bar_close_time": opened + 3600,
            "close": close,
            "finalization_state": "FINALIZED_BAR",
            "quality_state": "FINALIZED_BAR",
        }
    ).to_dict()
    payload["timestamps"] = {"captured_at": captured}
    payload["quality"] = {"finalized": True, "missing": False}
    original = bytes_v1(payload)
    fact = GovernedCanonicalFactV1(
        payload["fact_kind"], fact_digest(payload), payload, WP_A_PRODUCER
    )
    package = compose_admitted_market_context_v1(
        identity=identity,
        request=ExistingFactMaterializationRequestV1(
            captured, identity.instrument_ref, ("prov.original",), price_o4_bar_fact=fact
        ),
        receipts_by_digest={
            fact.fact_digest: FactAdmissionReceiptV1(
                "prov.original",
                identity.dataset_generation,
                original,
                captured,
                captured,
                {"price": "USDT_PER_SUI"},
            )
        },
        policy=ContextAdmissionPolicyV1(
            "explicit.test.policy", {"price_o4": 120}, ("price_state_ref",)
        ),
    )
    state_ref = package["market_context"]["price_state_ref"]["state_ref"]
    derived = package["derivations"][state_ref]
    assert float(derived["close"]) == close
    assert float(derived["bar_open_time"]) == opened
    assert package["source_bindings"][0]["original_payload_json"].encode() == original
    assert bytes_v1(fact.payload) == original
    assert replay_admitted_market_context_v1(package) == package


@pytest.mark.parametrize("pin", [True, None, "OFFLINE_ONLY", 0])
def test_bridge_rejects_non_boolean_false_runtime_pin(monkeypatch, pin):
    monkeypatch.setattr(bridge, "RUNTIME_REACHABILITY", pin)
    with pytest.raises(ValueError, match="RUNTIME_FORBIDDEN"):
        bridge.attach_market_context_to_mi_offline_cycle_v1(request=inputs()["request"])


def test_bridge_default_reaches_original_context():
    request = inputs()["request"]
    result = bridge.attach_market_context_to_mi_offline_cycle_v1(request=request)
    assert (
        result["context_id"]
        == materialize_market_context_v1_from_existing_facts_v1(request)["context_id"]
    )


@pytest.mark.parametrize(
    "change,reason",
    [
        ("late", "LOOKAHEAD"),
        ("generation", "GENERATION"),
        ("bytes", "BYTES"),
        ("stale", "STALE"),
        ("native", "NATIVE"),
        ("instrument", "ENTITY"),
        ("unit", "UNIT"),
        ("nonfinite", "FINITE"),
        ("not_available", "NOT_AVAILABLE"),
    ],
)
def test_bad_fact_or_receipt_never_reaches_numeric_success(change, reason):
    args = inputs()
    fact = args["request"].price_mark_fact
    receipt = args["receipts_by_digest"][fact.fact_digest]
    if change == "late":
        receipt = replace(receipt, available_at="2026-06-02T00:00:00Z")
    if change == "generation":
        receipt = replace(receipt, dataset_generation="generation.foreign")
    if change == "bytes":
        receipt = replace(receipt, payload_bytes=b"{}")
    if change == "stale":
        args["policy"] = replace(args["policy"], max_age_seconds_by_role={"price_mark": 1})
    if change == "unit":
        receipt = replace(receipt, units={"price": "UNKNOWN"})
    if change == "not_available":
        receipt = replace(
            receipt, known_at="2026-06-01T01:00:00Z", available_at="2026-06-01T01:00:00Z"
        )
    if change in {"native", "instrument", "nonfinite"}:
        p = deepcopy(fact.payload)
        if change == "native":
            p["instrument"]["venue_native_id"] = "FOREIGN"
        if change == "instrument":
            p["instrument"]["canonical_instrument_id"] = "inst.foreign"
        if change == "nonfinite":
            p["mark_px"] = "NaN"
        fact = replace(fact, payload=p, fact_digest=fact_digest(p))
        args["request"] = replace(args["request"], price_mark_fact=fact)
        receipt = replace(receipt, payload_bytes=bytes_v1(p))
    args["receipts_by_digest"] = {fact.fact_digest: receipt}
    with pytest.raises(ValueError, match=reason):
        compose_admitted_intelligence_context_v1(**args)


@pytest.mark.parametrize("kind", ["gap", "duplicate", "unit"])
def test_series_gap_duplicates_and_mixed_units_reject(kind):
    args = inputs(volatility=True)
    series = list(args["request"].volatility_mark_facts)
    if kind == "gap":
        removed = series.pop(30)
        args["receipts_by_digest"].pop(removed.fact_digest)
    if kind == "duplicate":
        series.append(series[30])
    if kind == "unit":
        digest = series[30].fact_digest
        args["receipts_by_digest"][digest] = replace(
            args["receipts_by_digest"][digest], units={"price": "OTHER"}
        )
    args["request"] = replace(args["request"], volatility_mark_facts=series)
    with pytest.raises(
        ValueError, match={"gap": "GRID", "duplicate": "DUPLICATE", "unit": "UNITS"}[kind]
    ):
        compose_admitted_intelligence_context_v1(**args)


def test_missing_required_family_does_not_fabricate_zero():
    args = inputs()
    args["policy"] = replace(args["policy"], required_families=("volatility_state_ref",))
    result = compose_admitted_intelligence_context_v1(**args)
    assert result["context_status"] == "INSUFFICIENT"
    assert result["missing_families"] == ["volatility_state_ref"]
    assert len(result["derivations"]) == 1


def test_phase19_derivatives_and_cross_market_keep_original_equations_and_replay():
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.context_admission_v1 import (
        replay_admitted_intelligence_context_v1,
    )
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_phase_19_orthogonal_materialization_v1 import (
        Phase19OrthogonalMaterializationInputsV1,
        load_cross_market_anchor_binding_v1,
    )

    args = inputs()
    anchor_ref = load_cross_market_anchor_binding_v1()["admissible_anchor_instrument_refs"][0]
    selected = [mark(i, str(100 * math.exp(0.001 * i + 0.0001 * i * i))) for i in (58, 59, 60)]
    anchors = []
    for i in (58, 59, 60):
        original = mark(i, str(200 * math.exp(0.002 * i + 0.00002 * i * i)))
        payload = deepcopy(original.payload)
        payload["instrument"]["canonical_instrument_id"] = anchor_ref
        payload["instrument"]["venue_native_id"] = "ANCHOR-SWAP"
        anchors.append(replace(original, payload=payload, fact_digest=fact_digest(payload)))
    request = replace(
        args["request"],
        price_mark_fact=selected[-1],
        phase_19=Phase19OrthogonalMaterializationInputsV1(
            derivatives_mark_fact=selected[-1],
            cross_market_selected_marks=selected,
            cross_market_anchor_marks_by_ref={anchor_ref: anchors},
            cross_market_lookback_bars=3,
        ),
    )
    args["request"] = request
    all_facts = selected + anchors
    args["receipts_by_digest"] = {
        f.fact_digest: FactAdmissionReceiptV1(
            "original." + f.fact_digest,
            IDENTITY.dataset_generation,
            bytes_v1(f.payload),
            f.payload["timestamps"]["captured_at"],
            f.payload["timestamps"]["captured_at"],
            {"price": "USDT_PER_SUI" if f in selected else "USDT_PER_ANCHOR"},
        )
        for f in all_facts
    }
    args["policy"] = replace(
        args["policy"],
        max_age_seconds_by_role={
            role: 120
            for role in ("price_mark", "derivatives_mark", "cross_selected", "anchor:" + anchor_ref)
        },
    )
    expected = dict(materialize_market_context_v1_from_existing_facts_v1(request))
    result = compose_admitted_intelligence_context_v1(**args)
    assert result["market_context"] == expected
    metrics = result["derivations"][expected["cross_market_state_ref"]["state_ref"]][
        "anchor_metrics"
    ][anchor_ref]
    assert float(metrics["idiosyncratic_move_1bar"]) == pytest.approx(
        float(metrics["relative_return_1bar"]) - float(metrics["common_move_1bar"])
    )
    assert replay_admitted_intelligence_context_v1(result) == result


def test_flow_replay_retains_original_input_order():
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.context_admission_v1 import (
        replay_admitted_intelligence_context_v1,
    )

    args = inputs()
    trades = []
    for i, (size, side) in enumerate((("1e16", "buy"), ("1", "buy"), ("1e16", "sell"))):
        p = deepcopy(mark().payload)
        p.update(
            fact_kind="TradeFactV1", trade_id="trade." + str(i), size=size, price="1", side=side
        )
        trades.append(GovernedCanonicalFactV1("TradeFactV1", fact_digest(p), p, WP_A_PRODUCER))
    args["request"] = replace(args["request"], trade_facts=trades)
    for f in trades:
        args["receipts_by_digest"][f.fact_digest] = FactAdmissionReceiptV1(
            "original." + f.fact_digest,
            IDENTITY.dataset_generation,
            bytes_v1(f.payload),
            f.payload["timestamps"]["captured_at"],
            f.payload["timestamps"]["captured_at"],
            {"price": "USDT_PER_SUI", "size": "BASE"},
        )
    args["policy"] = replace(
        args["policy"], max_age_seconds_by_role={"price_mark": 120, "flow": 120}
    )
    result = compose_admitted_intelligence_context_v1(**args)
    assert replay_admitted_intelligence_context_v1(result) == result
