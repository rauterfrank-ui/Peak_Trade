"""Bounded tests for Cap 2.2 offline MVR threshold set and evidence harness."""

from __future__ import annotations

import math
import socket
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.cap22_offline_mvr_evidence_harness_v1.constants_v1 import (
    CHALLENGER_A_POLICY_ID,
    CHALLENGER_B_POLICY_ID,
    CHALLENGER_C_POLICY_ID,
    CHALLENGER_D_POLICY_ID,
    HARNESS_NETWORK_READ_REQUIRED,
    MINIMUM_FINALIZED_PT1M_MARKS,
    NEGATIVE_CONTROL_POLICY_ID,
    POLICY_B_THRESHOLD_MODE,
    POLICY_B_THRESHOLD_SET_ID,
    POLICY_B_THRESHOLD_SET_RATIFIED,
    POLICY_WINNER_OUTPUT_PRESENT,
    TOP20_DIAGNOSTIC_ONLY,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.evaluators_v1 import (
    evaluate_challenger_a_v1,
    evaluate_challenger_b_v1,
    evaluate_challenger_c_v1,
    evaluate_challenger_d_v1,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.features_v1 import (
    population_sigma_log_returns_v1,
    relative_bid_ask_spread_over_mid_v1,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.harness_v1 import (
    OfflineMvrHarnessError,
    run_offline_mvr_evidence_harness_v1,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.reason_codes_v1 import (
    OfflineMvrHarnessFailureCodeV1,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.threshold_set_v1 import (
    injected_test_only_non_canonical_policy_b_threshold_set_v1,
)
from src.ops.cap22_offline_mvr_spread_challenger_order_contract_v1 import (
    POLICY_C_ZERO_SPREAD_RESULT,
    SPREAD_FORMULA_ID,
    SPREAD_UNITS,
)
from src.ops.cap22_offline_mvr_threshold_set_and_evidence_harness_contract_v1 import (
    AUTHORITATIVE_POLICY_B_THRESHOLD_SCALE_FOUND,
    ECONOMIC_RANK_ACTIVATED,
    FORWARD_LABEL_METRICS_PRESENT,
    HISTORICAL_PIT_WALK_FORWARD_EVIDENCE_PRESENT,
    NEXT_CAP22_DEPENDENCY,
    PDF_STEP_5_STATUS,
    RUNTIME_AUTHORITY_GRANTED,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import (
    ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED,
)
from src.ops.economic_md_input_producer_v1.models_v1 import (
    EconomicMdInputSnapshotV1,
)
from src.ops.economic_md_input_producer_v1.producer_v1 import (
    produce_economic_md_input_snapshot_v1,
)
from src.ops.economic_md_input_producer_v1.public_md_source_v1 import (
    InjectedEconomicMdPublicSourceV1,
    InstrumentPublicMdBundleV1,
    RawMarkCandleV1,
    RawTickerQuoteV1,
)
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
)
from src.ops.productive_futures_ranking_producer_v1.ranking_v1 import (
    classify_and_rank_candidates_v1,
)

REPO = Path(__file__).resolve().parents[2]
HARNESS_DIR = REPO / "src/ops/cap22_offline_mvr_evidence_harness_v1"
CAPTURE_TS = "1700000260000"
BASE_TS_MS = 1_700_000_000_000
REPO_SHA = "ea7582f298c4fbc032f50c18db756face6310497"
START_UNIX = 1_700_000_200.0
COMPLETE_UNIX = 1_700_000_260.0


def _perp(inst_id: str, *, base: str) -> dict:
    return {
        "instId": inst_id,
        "instType": "SWAP",
        "state": "live",
        "baseCcy": base,
        "quoteCcy": "USDT",
        "settleCcy": "USDT",
        "ctType": "linear",
        "ctVal": "0.01",
        "ctValCcy": base,
        "tickSz": "0.01",
        "lotSz": "1",
        "minSz": "1",
        "uly": f"{base}-USDT",
        "expTime": "",
    }


def _universe_snapshot(rows: list[dict]) -> dict:
    mark_ids = [r["instId"] for r in rows]
    return produce_governed_futures_universe_v1(
        source_payload={"code": "0", "msg": "", "data": rows},
        mark_price_payload={
            "code": "0",
            "msg": "",
            "data": [{"instId": i, "markPx": "100.5"} for i in mark_ids],
        },
        repository_sha=REPO_SHA,
        producer_observed_at_unix=1_700_000_100.0,
        source_event_time="1700000000000",
    ).snapshot.to_dict()


def _marks(venue_native_id: str, prices: list[str]) -> tuple[RawMarkCandleV1, ...]:
    return tuple(
        RawMarkCandleV1(
            venue_native_id=venue_native_id,
            ts_ms=str(BASE_TS_MS + i * 60_000),
            mark_px=price,
            confirm="1",
            receive_or_capture_timestamp=CAPTURE_TS,
        )
        for i, price in enumerate(prices)
    )


def _linear_prices(*, start: str, step: str) -> list[str]:
    value = Decimal(start)
    delta = Decimal(step)
    out: list[str] = []
    for _ in range(MINIMUM_FINALIZED_PT1M_MARKS):
        out.append(format(value, "f"))
        value += delta
    return out


def _alt_prices(*, low: str, high: str) -> list[str]:
    out: list[str] = []
    for i in range(MINIMUM_FINALIZED_PT1M_MARKS):
        out.append(high if i % 2 else low)
    return out


def _ticker(venue_native_id: str, *, bid: str, ask: str) -> RawTickerQuoteV1:
    return RawTickerQuoteV1(
        venue_native_id=venue_native_id,
        bid_px=bid,
        ask_px=ask,
        ticker_event_timestamp="1700000259000",
        capture_or_receive_timestamp=CAPTURE_TS,
    )


def _bundle(
    venue_native_id: str, *, prices: list[str], bid: str, ask: str
) -> InstrumentPublicMdBundleV1:
    return InstrumentPublicMdBundleV1(
        venue_native_id=venue_native_id,
        marks=_marks(venue_native_id, prices),
        ticker=_ticker(venue_native_id, bid=bid, ask=ask),
    )


INSTRUMENTS = (
    ("ETH-USDT-SWAP", "ETH"),
    ("SOL-USDT-SWAP", "SOL"),
    ("AVAX-USDT-SWAP", "AVAX"),
    ("LINK-USDT-SWAP", "LINK"),
    ("DOGE-USDT-SWAP", "DOGE"),
)


def _standard_universe() -> dict:
    return _universe_snapshot([_perp(inst, base=base) for inst, base in INSTRUMENTS])


def _standard_source() -> InjectedEconomicMdPublicSourceV1:
    # Spreads at mid=1000: 0.0001, 0.0005, 0.001, 0, 0.01
    # Vol: high alt, identical medium linear, identical medium linear, high-ish alt, low linear
    return InjectedEconomicMdPublicSourceV1(
        {
            "ETH-USDT-SWAP": _bundle(
                "ETH-USDT-SWAP",
                prices=_alt_prices(low="1000", high="1100"),
                bid="999.95",
                ask="1000.05",
            ),
            "SOL-USDT-SWAP": _bundle(
                "SOL-USDT-SWAP",
                prices=_linear_prices(start="1000", step="0.2"),
                bid="999.75",
                ask="1000.25",
            ),
            "AVAX-USDT-SWAP": _bundle(
                "AVAX-USDT-SWAP",
                prices=_linear_prices(start="1000", step="0.2"),
                bid="999.95",
                ask="1000.05",
            ),
            "LINK-USDT-SWAP": _bundle(
                "LINK-USDT-SWAP",
                prices=_alt_prices(low="1000", high="1050"),
                bid="1000",
                ask="1000",
            ),
            "DOGE-USDT-SWAP": _bundle(
                "DOGE-USDT-SWAP",
                prices=_linear_prices(start="1000", step="0.01"),
                bid="995",
                ask="1005",
            ),
        }
    )


def _produce(universe: dict | None = None, source: InjectedEconomicMdPublicSourceV1 | None = None):
    universe = universe or _standard_universe()
    source = source or _standard_source()
    produced = produce_economic_md_input_snapshot_v1(
        universe_snapshot=universe,
        public_md_source=source,
        collection_started_at_unix=START_UNIX,
        collection_completed_at_unix=COMPLETE_UNIX,
    )
    assert produced.ok, produced.failure_codes
    return universe, produced.snapshot


def _run(**overrides):
    universe, snapshot = _produce()
    kwargs = {
        "economic_md_snapshot": snapshot,
        "universe_snapshot": universe,
        "policy_b_threshold_set": injected_test_only_non_canonical_policy_b_threshold_set_v1(),
        "evidence_class": "OFFLINE_FIXTURE_EVIDENCE",
        "expected_provenance": {"network_used": False},
    }
    kwargs.update(overrides)
    return run_offline_mvr_evidence_harness_v1(**kwargs)


def _ranking(result: dict, policy_id: str, threshold_id: str | None = None) -> dict:
    matches = [
        row
        for row in result["challenger_rankings"]
        if row["policy_id"] == policy_id
        and (threshold_id is None or row.get("threshold_id") == threshold_id)
    ]
    assert matches, policy_id
    return matches[0]


def test_same_input_same_features_rankings_digests_and_run_id() -> None:
    first = _run()
    second = _run()
    assert first["feature_digest"] == second["feature_digest"]
    assert first["raw_input_digest"] == second["raw_input_digest"]
    assert first["candidate_universe_digest"] == second["candidate_universe_digest"]
    assert first["harness_run_id"] == second["harness_run_id"]
    assert [row["ranking_output_digest"] for row in first["challenger_rankings"]] == [
        row["ranking_output_digest"] for row in second["challenger_rankings"]
    ]
    assert [row["ordered_ranking"] for row in first["challenger_rankings"]] == [
        row["ordered_ranking"] for row in second["challenger_rankings"]
    ]


def test_volatility_formula_population_sigma_ddof0() -> None:
    prices = tuple(_alt_prices(low="1000", high="1100"))
    logs = [math.log(float(Decimal(prices[i]) / Decimal(prices[i - 1]))) for i in range(1, 61)]
    mean = sum(logs) / 60.0
    expected = math.sqrt(sum((item - mean) ** 2 for item in logs) / 60.0)
    got = population_sigma_log_returns_v1(prices)
    assert got == Decimal(format(expected, ".16e"))


def test_spread_formula_relative_bid_ask_over_mid() -> None:
    spread = relative_bid_ask_spread_over_mid_v1(bid_px="999.5", ask_px="1000.5")
    assert spread == Decimal("0.001")
    zero = relative_bid_ask_spread_over_mid_v1(bid_px="1000", ask_px="1000")
    assert zero == Decimal("0")
    result = _run()
    features = {row["canonical_instrument_id"]: row for row in result["features"]}
    assert all(row["spread_formula_id"] == SPREAD_FORMULA_ID for row in result["features"])
    assert all(row["spread_units"] == SPREAD_UNITS for row in result["features"])
    eth = next(row for row in features.values() if row["venue_native_id"] == "ETH-USDT-SWAP")
    assert Decimal(eth["relative_spread"]) == Decimal("0.0001")


def test_challenger_a_order_and_residual_tie_break() -> None:
    result = _run()
    ranking = _ranking(result, CHALLENGER_A_POLICY_ID)
    ids = [row["venue_native_id"] for row in ranking["ordered_ranking"]]
    assert ids[0] == "ETH-USDT-SWAP"
    sol_idx = ids.index("SOL-USDT-SWAP")
    avax_idx = ids.index("AVAX-USDT-SWAP")
    assert avax_idx < sol_idx
    features = {row["venue_native_id"]: row for row in result["features"]}
    assert features["SOL-USDT-SWAP"]["volatility"] == features["AVAX-USDT-SWAP"]["volatility"]


def test_policy_b_without_threshold_set_fail_closed() -> None:
    universe, snapshot = _produce()
    with pytest.raises(OfflineMvrHarnessError) as exc:
        run_offline_mvr_evidence_harness_v1(
            economic_md_snapshot=snapshot,
            universe_snapshot=universe,
            policy_b_threshold_set=None,
            evidence_class="OFFLINE_FIXTURE_EVIDENCE",
        )
    assert exc.value.failure_code == (
        OfflineMvrHarnessFailureCodeV1.POLICY_B_THRESHOLD_SET_MISSING.value
    )
    features = evaluate_challenger_a_v1  # keep import used via harness
    assert features is not None
    with pytest.raises(Exception) as inner:
        evaluate_challenger_b_v1([], threshold_set=None)
    assert OfflineMvrHarnessFailureCodeV1.POLICY_B_THRESHOLD_SET_MISSING.value in str(inner.value)


def test_policy_b_each_threshold_member_and_boundary() -> None:
    result = _run()
    b_rows = [
        row for row in result["challenger_rankings"] if row["policy_id"] == CHALLENGER_B_POLICY_ID
    ]
    assert len(b_rows) == 5
    by_threshold = {row["threshold_value"]: row for row in b_rows}
    tight = by_threshold["0.0001"]
    assert tight["gate_pass_count"] == 3  # ETH 0.0001, AVAX 0.0001, LINK 0
    mid = by_threshold["0.001"]
    mid_ids = {row["venue_native_id"] for row in mid["ordered_ranking"]}
    assert "ETH-USDT-SWAP" in mid_ids
    assert "SOL-USDT-SWAP" in mid_ids
    assert "DOGE-USDT-SWAP" not in mid_ids
    exact = next(row for row in result["features"] if row["venue_native_id"] == "ETH-USDT-SWAP")
    assert Decimal(exact["relative_spread"]) <= Decimal("0.0001")
    wide = by_threshold["0.01"]
    assert wide["gate_pass_count"] == 5


def test_policy_c_ratio_orientation_and_exact_zero_not_rankable() -> None:
    result = _run()
    ranking = _ranking(result, CHALLENGER_C_POLICY_ID)
    not_rankable = {row["venue_native_id"]: row for row in ranking["not_rankable"]}
    assert "LINK-USDT-SWAP" in not_rankable
    assert not_rankable["LINK-USDT-SWAP"]["reason_code"] == POLICY_C_ZERO_SPREAD_RESULT
    assert ranking["exact_zero_not_rankable_count"] == 1
    for row in ranking["ordered_ranking"]:
        assert "inf" not in str(row["sort_keys"]).lower()
        assert Decimal(row["sort_keys"]["ratio"]).is_finite()
    ordered = ranking["ordered_ranking"]
    ratios = [Decimal(row["sort_keys"]["ratio"]) for row in ordered]
    assert ratios == sorted(ratios, reverse=True)


def test_policy_d_spread_asc_then_volatility_desc() -> None:
    result = _run()
    ranking = _ranking(result, CHALLENGER_D_POLICY_ID)
    rows = ranking["ordered_ranking"]
    spreads = [Decimal(row["sort_keys"]["relative_spread"]) for row in rows]
    assert spreads == sorted(spreads)
    eth = next(row for row in rows if row["venue_native_id"] == "ETH-USDT-SWAP")
    avax = next(row for row in rows if row["venue_native_id"] == "AVAX-USDT-SWAP")
    assert Decimal(eth["sort_keys"]["relative_spread"]) == Decimal(
        avax["sort_keys"]["relative_spread"]
    )
    assert Decimal(eth["sort_keys"]["volatility"]) > Decimal(avax["sort_keys"]["volatility"])
    assert eth["rank"] < avax["rank"]


def test_residual_tie_break_deterministic_across_challengers() -> None:
    result = _run()
    for policy_id in (CHALLENGER_A_POLICY_ID, CHALLENGER_D_POLICY_ID):
        ranking = _ranking(result, policy_id)
        sol = next(
            row for row in ranking["ordered_ranking"] if row["venue_native_id"] == "SOL-USDT-SWAP"
        )
        avax = next(
            row for row in ranking["ordered_ranking"] if row["venue_native_id"] == "AVAX-USDT-SWAP"
        )
        assert avax["rank"] < sol["rank"]
        assert sol["residual_tie_break"]["venue_native_id"] == "SOL-USDT-SWAP"


def test_negative_control_reproduces_structural_rule() -> None:
    universe, snapshot = _produce()
    result = run_offline_mvr_evidence_harness_v1(
        economic_md_snapshot=snapshot,
        universe_snapshot=universe,
        policy_b_threshold_set=injected_test_only_non_canonical_policy_b_threshold_set_v1(),
        evidence_class="OFFLINE_FIXTURE_EVIDENCE",
    )
    ranking = _ranking(result, NEGATIVE_CONTROL_POLICY_ID)
    allowed = {
        (row["canonical_instrument_id"], row["venue_native_id"])
        for row in result["candidate_universe"]
    }
    filtered = dict(universe)
    filtered["instruments"] = [
        dict(row)
        for row in universe["instruments"]
        if (
            str(row.get("canonical_instrument_id") or ""),
            str(row.get("venue_native_inst_id") or ""),
        )
        in allowed
    ]
    expected, _excluded, _counts = classify_and_rank_candidates_v1(
        filtered, top_n=len(filtered["instruments"])
    )
    got_ids = [row["canonical_instrument_id"] for row in ranking["ordered_ranking"]]
    expected_ids = [row.canonical_instrument_id for row in expected]
    assert got_ids == expected_ids


def test_identical_candidate_universe_enforced() -> None:
    result = _run()
    expected = {
        (row["canonical_instrument_id"], row["venue_native_id"])
        for row in result["candidate_universe"]
    }
    assert len(expected) == 5
    for ranking in result["challenger_rankings"]:
        observed = {
            (row["canonical_instrument_id"], row["venue_native_id"])
            for row in ranking["ordered_ranking"]
        } | {
            (row["canonical_instrument_id"], row["venue_native_id"])
            for row in ranking["not_rankable"]
        }
        assert observed == expected


def test_cap21_ineligible_injection_rejected() -> None:
    universe, snapshot = _produce()
    payload = snapshot.to_dict()
    extra = dict(payload["instruments"][0])
    extra["canonical_instrument_id"] = "injected-ineligible"
    extra["venue_native_id"] = "INELIGIBLE-USDT-SWAP"
    payload["instruments"].append(extra)
    mutated = EconomicMdInputSnapshotV1.from_dict(payload).with_payload_digest()
    with pytest.raises(OfflineMvrHarnessError) as exc:
        run_offline_mvr_evidence_harness_v1(
            economic_md_snapshot=mutated,
            universe_snapshot=universe,
            policy_b_threshold_set=injected_test_only_non_canonical_policy_b_threshold_set_v1(),
            evidence_class="OFFLINE_FIXTURE_EVIDENCE",
        )
    assert (
        exc.value.failure_code
        == OfflineMvrHarnessFailureCodeV1.INELIGIBLE_INSTRUMENT_INJECTION.value
    )


def test_snapshot_digest_mismatch_rejected() -> None:
    universe, snapshot = _produce()
    payload = snapshot.to_dict()
    payload["payload_digest"] = "0" * 64
    with pytest.raises(OfflineMvrHarnessError) as exc:
        run_offline_mvr_evidence_harness_v1(
            economic_md_snapshot=payload,
            universe_snapshot=universe,
            policy_b_threshold_set=injected_test_only_non_canonical_policy_b_threshold_set_v1(),
            evidence_class="OFFLINE_FIXTURE_EVIDENCE",
        )
    assert exc.value.failure_code == OfflineMvrHarnessFailureCodeV1.SNAPSHOT_DIGEST_MISMATCH.value


def test_provenance_mismatch_rejected() -> None:
    universe, snapshot = _produce()
    with pytest.raises(OfflineMvrHarnessError) as exc:
        run_offline_mvr_evidence_harness_v1(
            economic_md_snapshot=snapshot,
            universe_snapshot=universe,
            policy_b_threshold_set=injected_test_only_non_canonical_policy_b_threshold_set_v1(),
            evidence_class="OFFLINE_FIXTURE_EVIDENCE",
            expected_provenance={"network_used": True},
        )
    assert exc.value.failure_code == OfflineMvrHarnessFailureCodeV1.PROVENANCE_MISMATCH.value


def test_no_network_on_replay_and_source_has_no_network_client() -> None:
    assert HARNESS_NETWORK_READ_REQUIRED is False
    forbidden = ("import requests", "import urllib", "import httpx", "socket.create_connection")
    for path in HARNESS_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, path
        assert "evaluate_policy_a_v1(" not in text
        assert "from src.ops.mf_membership" not in text
        assert "apply_rotation(" not in text

    original = socket.socket

    class Boom(socket.socket):
        def __init__(self, *args, **kwargs):
            raise AssertionError("network forbidden")

    socket.socket = Boom  # type: ignore[misc]
    try:
        result = _run()
        assert result["harness_network_read"] is False
        assert result["ok"] is True
    finally:
        socket.socket = original  # type: ignore[misc]


def test_no_policy_a_active_set_execution_or_productive_ranking() -> None:
    result = _run()
    assert result["authority"]["ECONOMIC_RANK_ACTIVATED"] is False
    assert result["authority"]["ACTIVE_SET_SEMANTICS_CREATED"] is False
    assert result["authority"]["POLICY_WINNER_OUTPUT_PRESENT"] is False
    assert "active_set" not in result
    assert "policy_winner" not in result
    for ranking in result["challenger_rankings"]:
        assert ranking["top20_diagnostic_only"] is True
        assert ranking["top20_authoritative"] is False
        assert len(ranking["top20_diagnostic"]) <= 20
    assert TOP20_DIAGNOSTIC_ONLY is True
    assert POLICY_WINNER_OUTPUT_PRESENT is False
    assert ECONOMIC_RANK_ACTIVATED is False
    assert ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED is False
    assert RUNTIME_AUTHORITY_GRANTED is False


def test_evidence_classification_and_no_forward_or_winner_metrics() -> None:
    result = _run()
    assert result["evidence_class"] == "OFFLINE_FIXTURE_EVIDENCE"
    assert FORWARD_LABEL_METRICS_PRESENT is False
    assert HISTORICAL_PIT_WALK_FORWARD_EVIDENCE_PRESENT is False
    for forbidden in (
        "forward_abs_return",
        "forward_realized_vol",
        "spearman",
        "pnl",
        "sharpe",
        "walk_forward",
        "policy_winner",
    ):
        assert forbidden not in result
    with pytest.raises(OfflineMvrHarnessError) as exc:
        universe, snapshot = _produce()
        run_offline_mvr_evidence_harness_v1(
            economic_md_snapshot=snapshot,
            universe_snapshot=universe,
            policy_b_threshold_set=injected_test_only_non_canonical_policy_b_threshold_set_v1(),
            evidence_class="HISTORICAL_PIT_WALK_FORWARD_EVIDENCE",
        )
    assert exc.value.failure_code == OfflineMvrHarnessFailureCodeV1.EVIDENCE_CLASS_FORBIDDEN.value


def test_unknown_policy_id_fail_closed() -> None:
    universe, snapshot = _produce()
    with pytest.raises(OfflineMvrHarnessError) as exc:
        run_offline_mvr_evidence_harness_v1(
            economic_md_snapshot=snapshot,
            universe_snapshot=universe,
            policy_b_threshold_set=injected_test_only_non_canonical_policy_b_threshold_set_v1(),
            evidence_class="OFFLINE_FIXTURE_EVIDENCE",
            extra_policy_ids=("ANTI_CHURN_POLICY_A",),
        )
    assert exc.value.failure_code == OfflineMvrHarnessFailureCodeV1.UNKNOWN_POLICY_ID.value


def test_invalid_quote_and_insufficient_marks_fail_closed() -> None:
    universe = _standard_universe()
    source = _standard_source()
    crossed = dict(source.bundles)
    crossed["ETH-USDT-SWAP"] = _bundle(
        "ETH-USDT-SWAP",
        prices=_alt_prices(low="1000", high="1100"),
        bid="1001",
        ask="1000",
    )
    produced = produce_economic_md_input_snapshot_v1(
        universe_snapshot=universe,
        public_md_source=InjectedEconomicMdPublicSourceV1(crossed),
        collection_started_at_unix=START_UNIX,
        collection_completed_at_unix=COMPLETE_UNIX,
    )
    if produced.ok:
        with pytest.raises(OfflineMvrHarnessError) as exc:
            run_offline_mvr_evidence_harness_v1(
                economic_md_snapshot=produced.snapshot,
                universe_snapshot=universe,
                policy_b_threshold_set=injected_test_only_non_canonical_policy_b_threshold_set_v1(),
                evidence_class="OFFLINE_FIXTURE_EVIDENCE",
            )
        assert exc.value.failure_code in {
            OfflineMvrHarnessFailureCodeV1.CROSSED_QUOTE.value,
            OfflineMvrHarnessFailureCodeV1.RAW_INPUT_NOT_ELIGIBLE.value,
            OfflineMvrHarnessFailureCodeV1.INVALID_BID_ASK.value,
        }
    short_prices = _linear_prices(start="1000", step="0.2")[:60]
    short_source = _standard_source()
    short_map = dict(short_source.bundles)
    short_map["SOL-USDT-SWAP"] = _bundle(
        "SOL-USDT-SWAP",
        prices=short_prices,
        bid="999.75",
        ask="1000.25",
    )
    produced_short = produce_economic_md_input_snapshot_v1(
        universe_snapshot=universe,
        public_md_source=InjectedEconomicMdPublicSourceV1(short_map),
        collection_started_at_unix=START_UNIX,
        collection_completed_at_unix=COMPLETE_UNIX,
    )
    if produced_short.ok:
        with pytest.raises(OfflineMvrHarnessError) as exc2:
            run_offline_mvr_evidence_harness_v1(
                economic_md_snapshot=produced_short.snapshot,
                universe_snapshot=universe,
                policy_b_threshold_set=injected_test_only_non_canonical_policy_b_threshold_set_v1(),
                evidence_class="OFFLINE_FIXTURE_EVIDENCE",
            )
        assert exc2.value.failure_code in {
            OfflineMvrHarnessFailureCodeV1.INSUFFICIENT_MARKS.value,
            OfflineMvrHarnessFailureCodeV1.RAW_INPUT_NOT_ELIGIBLE.value,
            OfflineMvrHarnessFailureCodeV1.MISSING_MARK.value,
        }
    else:
        assert produced_short.ok is False


def test_existing_cap21_cap22_contracts_remain_green() -> None:
    from src.ops.cap22_offline_mvr_spread_challenger_order_contract_v1 import (
        ECONOMIC_RANK_ACTIVATED as SPREAD_RANK,
        POLICY_B_THRESHOLD_SET_RATIFIED as SPREAD_SET_RATIFIED,
        SPREAD_FORMULA_RATIFIED,
    )
    from src.ops.cap22_offline_policy_candidates_and_evidence_contract_v1 import (
        IDENTICAL_CANDIDATE_UNIVERSE_PER_POLICY_COMPARISON,
        NO_OFFLINE_POLICY_CLASS_HAS_PRODUCTIVE_AUTHORITY,
    )

    assert SPREAD_FORMULA_RATIFIED is True
    assert SPREAD_RANK is False
    assert SPREAD_SET_RATIFIED is False
    assert IDENTICAL_CANDIDATE_UNIVERSE_PER_POLICY_COMPARISON is True
    assert NO_OFFLINE_POLICY_CLASS_HAS_PRODUCTIVE_AUTHORITY is True
    assert POLICY_B_THRESHOLD_MODE == "VERSIONED_OFFLINE_THRESHOLD_SET"
    assert POLICY_B_THRESHOLD_SET_ID == "CAP22_MVR_POLICY_B_INJECTED_THRESHOLD_SET_V1"
    assert POLICY_B_THRESHOLD_SET_RATIFIED is False
    assert AUTHORITATIVE_POLICY_B_THRESHOLD_SCALE_FOUND is False
    assert PDF_STEP_5_STATUS == "UNRESOLVED"
    assert NEXT_CAP22_DEPENDENCY.startswith("SEPARATE_OWNER_GO_REQUIRED_TO_RATIFY_RANKING_CADENCE")
    threshold_set = injected_test_only_non_canonical_policy_b_threshold_set_v1()
    assert threshold_set.ratified is False
    assert all(member.test_only and not member.canonical for member in threshold_set.members)
    result = evaluate_challenger_c_v1.__name__
    assert result
    result_d = evaluate_challenger_d_v1
    assert result_d is not None
