"""Original source-clock precision at admission and archived-context replay."""

from copy import deepcopy
from dataclasses import replace

import pytest

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    context_admission_v1 as admission,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    MarketIdentityV1,
    bytes_v1,
    instant_v1,
    seal_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_existing_fact_materialization_v1 import (
    GovernedCanonicalFactV1,
    WP_A_PRODUCER,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_phase_19_orthogonal_materialization_v1 import (
    Phase19OrthogonalMaterializationInputsV1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import fact_digest
from tests.learning.test_intelligence_context_admission_v1 import inputs, mark

MODES = ("attributed", "market")
LEGACY_VARIANTS = ("plain", "volatility", "offset", "microseconds", "huge_age", "insufficient")


def _case(mode, variant="plain"):
    args = inputs(volatility=variant == "volatility")
    if mode == "market":
        original = args["identity"]
        args["identity"] = MarketIdentityV1(
            original.dataset_generation,
            original.venue,
            original.instrument_ref,
            original.native_instrument_ref,
        )
    if variant in {"offset", "microseconds"}:
        for digest, receipt in args["receipts_by_digest"].items():
            stamp = receipt.known_at.replace("Z", "+00:00" if variant == "offset" else ".123456Z")
            args["receipts_by_digest"][digest] = replace(
                receipt, known_at=stamp, available_at=stamp
            )
    if variant == "huge_age":
        args["policy"] = replace(args["policy"], max_age_seconds_by_role={"price_mark": 10**20})
    if variant == "insufficient":
        args["policy"] = replace(args["policy"], required_families=("volatility_state_ref",))
    return args


def _compose(mode, args):
    compose = (
        admission.compose_admitted_market_context_v1
        if mode == "market"
        else admission.compose_admitted_intelligence_context_v1
    )
    return compose(**args)


def _replay(mode, package):
    replay = (
        admission.replay_admitted_market_context_v1
        if mode == "market"
        else admission.replay_admitted_intelligence_context_v1
    )
    return replay(package)


def _replace_mark_capture(args, captured):
    old = args["request"].price_mark_fact
    payload = deepcopy(old.payload)
    payload["timestamps"]["captured_at"] = captured
    fact = GovernedCanonicalFactV1(old.fact_kind, fact_digest(payload), payload, old.producer_owner)
    receipt = args["receipts_by_digest"].pop(old.fact_digest)
    args["receipts_by_digest"][fact.fact_digest] = replace(receipt, payload_bytes=bytes_v1(payload))
    args["request"] = replace(args["request"], price_mark_fact=fact)


def _add_trade(args, *, event, captured, known, available):
    payload = deepcopy(mark().payload)
    payload.update(
        fact_kind="TradeFactV1", trade_id="trade.exact", size="2", price="100", side="buy"
    )
    payload["timestamps"] = {"effective_at": event, "captured_at": captured}
    fact = GovernedCanonicalFactV1("TradeFactV1", fact_digest(payload), payload, WP_A_PRODUCER)
    args["request"] = replace(args["request"], trade_facts=(fact,))
    args["receipts_by_digest"][fact.fact_digest] = admission.FactAdmissionReceiptV1(
        "original." + fact.fact_digest,
        args["identity"].dataset_generation,
        bytes_v1(payload),
        known,
        available,
        {"price": "USDT_PER_SUI", "size": "BASE"},
    )
    args["policy"] = replace(
        args["policy"], max_age_seconds_by_role={"price_mark": 120, "flow": 120}
    )


def _forbidden(*args, **kwargs):
    pytest.fail("Contradictory source timing reached the original feature materializer")


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize(
    "fault,reason",
    [
        ("knowledge", "KNOWLEDGE_LOOKAHEAD"),
        ("availability", "KNOWLEDGE_LOOKAHEAD"),
        ("event", "KNOWLEDGE_LOOKAHEAD"),
        ("capture", "FINAL_VALUE_NOT_AVAILABLE"),
        ("age", "CONTEXT_ROLE_STALE"),
        ("future_source", "KNOWLEDGE_LOOKAHEAD"),
    ],
)
def test_fractional_contradictions_stop_before_original_features(monkeypatch, mode, fault, reason):
    args = _case(mode)
    digest, receipt = next(iter(args["receipts_by_digest"].items()))
    if fault == "knowledge":
        args["receipts_by_digest"][digest] = replace(
            receipt,
            known_at="2026-06-01T01:01:01.000000002Z",
            available_at="2026-06-01T01:01:01.000000001+00:00",
        )
    elif fault == "availability":
        args["receipts_by_digest"][digest] = replace(
            receipt, available_at="2026-06-01T01:02:00.000000001Z"
        )
    elif fault == "capture":
        _replace_mark_capture(args, "2026-06-01T01:01:01.000000002Z")
        digest, receipt = next(iter(args["receipts_by_digest"].items()))
        args["receipts_by_digest"][digest] = replace(
            receipt,
            known_at="2026-06-01T01:01:01.000000001Z",
            available_at="2026-06-01T01:01:01.000000001Z",
        )
    elif fault == "age":
        args["request"] = replace(args["request"], observed_at="2026-06-01T01:02:00.000000001Z")
    elif fault == "event":
        _add_trade(
            args,
            event="2026-06-01T01:01:01.000000002Z",
            captured="2026-06-01T01:01:01.000000002Z",
            known="2026-06-01T01:01:01.000000001Z",
            available="2026-06-01T01:01:01.000000003Z",
        )
    else:
        _add_trade(
            args,
            event="2026-06-01T01:02:00.000000001Z",
            captured="2026-06-01T01:02:00.000000001Z",
            known="2026-06-01T01:02:00.000000001Z",
            available="2026-06-01T01:02:00.000000001Z",
        )
    monkeypatch.setattr(
        admission, "materialize_market_context_v1_from_existing_facts_v1", _forbidden
    )
    with pytest.raises(ValueError, match=reason):
        _compose(mode, args)


@pytest.mark.parametrize("mode", MODES)
def test_resealed_archive_timing_rejects_before_feature_replay(monkeypatch, mode):
    package = _compose(mode, _case(mode))
    body = deepcopy(package)
    body.pop("exact_content_digest")
    body["source_bindings"][0]["available_at"] = "2026-06-01T01:02:00.000000001+00:00"
    changed = seal_v1(body)
    monkeypatch.setattr(
        admission, "materialize_market_context_v1_from_existing_facts_v1", _forbidden
    )
    with pytest.raises(ValueError, match="KNOWLEDGE_LOOKAHEAD"):
        _replay(mode, changed)


@pytest.mark.parametrize("mode", MODES)
def test_old_lossy_receipt_is_not_repaired_or_assumed_available(monkeypatch, mode):
    args = _case(mode)
    stamp = "2026-06-01T01:01:01.000000001Z"
    _replace_mark_capture(args, stamp)
    for digest, receipt in args["receipts_by_digest"].items():
        args["receipts_by_digest"][digest] = replace(receipt, known_at=stamp, available_at=stamp)
    body = _compose(mode, args)
    body.pop("exact_content_digest")
    for binding in body["source_bindings"]:
        for field in ("event_time", "captured_at", "known_at", "available_at"):
            binding[field] = instant_v1(binding[field]).isoformat()
    lossy = seal_v1(body)
    before = deepcopy(lossy)
    monkeypatch.setattr(
        admission, "materialize_market_context_v1_from_existing_facts_v1", _forbidden
    )
    with pytest.raises(ValueError, match="FINAL_VALUE_NOT_AVAILABLE"):
        _replay(mode, lossy)
    assert lossy == before


@pytest.mark.parametrize("mode", MODES)
def test_original_oi_selector_precision_fence_is_retained(monkeypatch, mode):
    args = _case(mode)
    facts = []
    for nanos in (2, 1):
        payload = deepcopy(mark().payload)
        payload.update(fact_kind="OpenInterestFactV1", open_interest=str(100 + nanos))
        stamp = f"2026-06-01T01:01:01.{nanos:09d}Z"
        payload["timestamps"] = {"effective_at": stamp, "captured_at": stamp}
        fact = GovernedCanonicalFactV1(
            "OpenInterestFactV1", fact_digest(payload), payload, WP_A_PRODUCER
        )
        facts.append(fact)
        args["receipts_by_digest"][fact.fact_digest] = admission.FactAdmissionReceiptV1(
            "original." + fact.fact_digest,
            args["identity"].dataset_generation,
            bytes_v1(payload),
            stamp,
            stamp,
            {"open_interest": "BASE"},
        )
    args["request"] = replace(
        args["request"],
        phase_19=Phase19OrthogonalMaterializationInputsV1(
            derivatives_mark_fact=args["request"].price_mark_fact,
            open_interest_facts=facts,
        ),
    )
    args["policy"] = replace(
        args["policy"],
        max_age_seconds_by_role={"price_mark": 120, "derivatives_mark": 120, "open_interest": 120},
    )
    monkeypatch.setattr(
        admission, "materialize_market_context_v1_from_existing_facts_v1", _forbidden
    )
    with pytest.raises(ValueError, match="DUPLICATE_OI_TIME_REJECTED"):
        _compose(mode, args)


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("nanos", [1, 123456789])
def test_precise_ties_preserve_source_bytes_and_cold_replay(tmp_path, mode, nanos):
    args = _case(mode)
    stamp = f"2026-06-01T01:01:01.{nanos:09d}Z"
    canonical = stamp.replace("Z", "+00:00")
    _replace_mark_capture(args, stamp)
    for digest, receipt in args["receipts_by_digest"].items():
        args["receipts_by_digest"][digest] = replace(
            receipt, known_at=canonical, available_at=stamp
        )
    _add_trade(args, event=stamp, captured=stamp, known=canonical, available=stamp)
    before = deepcopy(args)
    native = dict(admission.materialize_market_context_v1_from_existing_facts_v1(args["request"]))
    package = _compose(mode, args)
    assert package["market_context"] == native
    assert args == before
    for binding in package["source_bindings"]:
        assert binding["captured_at"] == binding["known_at"] == binding["available_at"] == canonical
        assert (
            binding["original_payload_json"].encode()
            == args["receipts_by_digest"][binding["fact_digest"]].payload_bytes
        )
        if binding["role"] == "flow":
            assert binding["event_time"] == canonical
    archive = tmp_path / "context.json"
    archive.write_bytes(bytes_v1(package))
    assert _replay(mode, admission.strict_json_v1(archive.read_bytes())) == package
    assert _compose(mode, args) == package


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("variant", LEGACY_VARIANTS)
def test_precision_faithful_legacy_context_semantics(mode, variant):
    args = _case(mode, variant)
    package = _compose(mode, args)
    native = dict(admission.materialize_market_context_v1_from_existing_facts_v1(args["request"]))
    assert package["market_context"] == native
    for binding in package["source_bindings"]:
        receipt = args["receipts_by_digest"][binding["fact_digest"]]
        assert binding["known_at"] == instant_v1(receipt.known_at).isoformat()
        assert binding["available_at"] == instant_v1(receipt.available_at).isoformat()
    assert package["context_status"] == ("INSUFFICIENT" if variant == "insufficient" else "VALID")
    assert package["forecast_disposition"] == "ABSTAIN"
    assert _replay(mode, package) == package
