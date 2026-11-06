"""Purpose-pinned original data consumers and actual session→N1 integration."""

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.ops.economic_md_input_producer_v1.purpose_consumers_v1 import (
    PurposeBoundPublicFactSourceV1,
    CONSUMERS,
    purpose_profile_digest_v1,
)
from src.ops.economic_md_input_producer_v1.purpose_admission_v1 import PublicFactPurposePolicyV1
from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
    append_fact_v1,
    default_store_paths_v1,
)


def _profiles(
    root,
    *,
    canonical="inst-eth-usdt-perp",
    native="ETH-USDT-SWAP",
    now_ms=1793836802000,
    last_ms=1793836800000,
    direction=1,
):
    from tests.ops.test_public_fact_consumer_semantics_v1 import _fact

    stamp = datetime.fromtimestamp(now_ms / 1000, tz=timezone.utc).isoformat()
    last_ms -= 60000  # PT1M row timestamp is bar-open, not finalization time.
    rows = []

    def fact(kind, event):
        row = _fact(kind, native=native, event=event)
        row["instrument"]["canonical_instrument_id"] = canonical
        row["timestamps"]["captured_at"] = stamp
        row["quality"] = {
            "finalized": True,
            "in_progress": False,
            "missing": False,
            "stale": False,
            "corrected": False,
            "gap_detected": False,
        }
        return row

    for i in range(100):
        event = last_ms - (99 - i) * 60000
        row = fact("OhlcvIntervalFactV1", event)
        px = str(1000 + direction * 20 * i / 99)
        row.update(
            interval_id="PT1M",
            source_price_kind="mark_price_candle",
            volume_unit_semantics="CONTRACTS",
            interval_start_ms=event,
            open_px=px,
            high_px=px,
            low_px=px,
            close_px=px,
            volume="10",
        )
        rows.append(row)
        if i >= 39:
            mark = fact("FinalizedPt1mMarkFactV1", event)
            mark["mark_px"] = px
            rows.append(mark)
    quote = fact("BestBidAskFactV1", last_ms)
    quote.update(bid_px=str(1000 + direction * 20 - 0.1), ask_px=str(1000 + direction * 20 + 0.1))
    rows.append(quote)
    # Use the original authoritative producer, without replacing its bar rules.
    from tests.ops.test_canonical_public_md_and_ohlcv_transport_reconciliation_v1 import (
        _producer,
        _md,
    )

    producer = _producer()
    start = (last_ms // 3600000 - 3) * 3600
    for i in range(3):
        event = start + i * 3600
        producer.ingest_normalized_event(
            _md(
                mark=100 + i * 10,
                event_ts=event + 10,
                receive_ts=event + 11,
                canonical=canonical,
                venue_id=native,
            )
        )
        producer.finalize_bar(canonical_instrument_id=canonical, bar_open_time=event)
    for bar in producer.list_envelopes():
        row = fact("FinalizedPt1hO4BarFactV1", int(bar["bar_close_time"] * 1000))
        row["bar"] = dict(bar)
        rows.append(row)
    paths = default_store_paths_v1(root)
    for row in rows:
        append_fact_v1(paths, row)
    sources = {}
    kinds_by_purpose = {
        "RANKING": ("FinalizedPt1mMarkFactV1", "BestBidAskFactV1"),
        "TRADING": ("OhlcvIntervalFactV1",),
        "RESEARCH": ("OhlcvIntervalFactV1",),
        "LIQUIDITY": ("BestBidAskFactV1",),
        "OUTCOME": ("FinalizedPt1hO4BarFactV1",),
    }
    for purpose, kinds in kinds_by_purpose.items():
        policy = PublicFactPurposePolicyV1(
            purpose,
            CONSUMERS[purpose],
            canonical,
            tuple((k, "test-only-source") for k in kinds),
            tuple((k, 20000, 300) for k in kinds),
            2,
            False,
            tuple(k for k in kinds if k != "BestBidAskFactV1"),
        )
        sources[purpose] = PurposeBoundPublicFactSourceV1(
            str(root.resolve()),
            policy,
            "mark_price_candle",
            "CONTRACTS",
            now_ms,
            None if purpose == "LIQUIDITY" else 3600000 if purpose == "OUTCOME" else 60000,
        )
    return sources


def test_actual_numeric_data_consumers_and_missing_liquidity_are_distinct(tmp_path):
    sources = _profiles(tmp_path / "facts")
    from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_runtime_economic_md_adapter_v1 import (
        PublicRuntimeEconomicMdPublicSourceV1,
    )
    from src.ops.economic_md_input_producer_v1.validation_v1 import (
        select_finalized_contiguous_pt1m_marks_v1,
    )
    from src.ops.peak_trade_ranking_feature_production_v1.producer_v1 import (
        compute_b03_ratified_raw_features_pure_v1,
    )

    s = sources["RANKING"]
    raw = PublicRuntimeEconomicMdPublicSourceV1(
        Path(s.store_root), s.policy, s.as_of_ms
    ).collect_instrument_raw_input_v1(venue_native_id="ETH-USDT-SWAP")
    selected, codes = select_finalized_contiguous_pt1m_marks_v1(raw.marks)
    assert not codes and len(selected) == 61
    features = compute_b03_ratified_raw_features_pure_v1(tuple(m.mark_px for m in selected))
    assert len(features) == 2 and all(f.raw_value is not None and f.raw_value > 0 for f in features)
    payload = sources["TRADING"].trading_c1_v1(native_id="ETH-USDT-SWAP")
    assert len(payload["data"]) == 100 and payload["data"][-1][4] == "1020.0"
    returns = sources["RESEARCH"].research_returns_v1(native_id="ETH-USDT-SWAP", interval_ms=60000)
    assert len(returns) == 99 and returns.iloc[0] > 0
    # The file-based original consumer and admitted input share one calculation.
    import pandas as pd
    from src.experiments.ohlcv_returns_file import load_close_returns_from_ohlcv_parquet

    frame = pd.DataFrame(
        {"close": [float(r[4]) for r in payload["data"]]},
        index=pd.to_datetime([int(r[0]) for r in payload["data"]], unit="ms", utc=True),
    )
    path = tmp_path / "research.parquet"
    frame.to_parquet(path)
    pd.testing.assert_series_equal(returns, load_close_returns_from_ohlcv_parquet(path))
    liq = sources["LIQUIDITY"].liquidity_input_v1(
        native_id="ETH-USDT-SWAP",
        required_features=("TOP_OF_BOOK_PRICES", "DEPTH", "ADV", "SLIPPAGE"),
    )
    assert liq["status"] == "CANNOT_EVALUATE" and liq["missing_features"] == (
        "DEPTH",
        "ADV",
        "SLIPPAGE",
    )
    assert liq["depth"] is None and not liq["risk_admitted"]
    snapshot = sources["OUTCOME"].outcome_snapshot_v1(
        native_id="ETH-USDT-SWAP", decision_event_ref="ddo.dec:e1-offline-input", n_bars=2
    )
    assert snapshot["o4_interval_id"] == "PT1H" and len(snapshot["o4_bars"]) == 2


@pytest.mark.parametrize("purpose", ["TRADING", "RESEARCH", "LIQUIDITY", "OUTCOME"])
def test_foreign_purpose_rejected_at_each_actual_consumer(tmp_path, purpose):
    sources = _profiles(tmp_path / "facts")
    s = sources[purpose]
    s = replace(
        s,
        policy=replace(s.policy, purpose="RANKING", consumer=CONSUMERS["RANKING"]),
        expected_interval_ms=60000,
    )
    calls = {
        "TRADING": lambda: s.trading_c1_v1(native_id="ETH-USDT-SWAP"),
        "RESEARCH": lambda: s.research_returns_v1(native_id="ETH-USDT-SWAP", interval_ms=60000),
        "LIQUIDITY": lambda: s.liquidity_input_v1(
            native_id="ETH-USDT-SWAP", required_features=("DEPTH",)
        ),
        "OUTCOME": lambda: s.outcome_snapshot_v1(
            native_id="ETH-USDT-SWAP", decision_event_ref="ddo.dec:wrong-purpose", n_bars=2
        ),
    }
    with pytest.raises(ValueError, match="PURPOSE_MISMATCH"):
        calls[purpose]()


@pytest.mark.parametrize(
    "field,value",
    [("expected_price_kind", "trade_price_candle"), ("expected_volume_unit", "BASE_ASSET")],
)
def test_unit_or_price_basis_change_is_not_a_valid_trading_frame(tmp_path, field, value):
    source = _profiles(tmp_path / "facts")["TRADING"]
    with pytest.raises(ValueError, match="BASIS_OR_VOLUME_UNIT_MISMATCH"):
        replace(source, **{field: value}).trading_c1_v1(native_id="ETH-USDT-SWAP")


@pytest.mark.parametrize("completion_failure", [False, True])
@pytest.mark.parametrize("direction", [1, -1])
def test_profile_pinned_session_feeds_actual_n1_and_recovers_policy_identity(
    tmp_path, monkeypatch, completion_failure, direction
):
    from tests.ops import test_adverse_time_exit_consumer_semantics_v1 as scenario
    from tests.ops.test_bounded_offline_episode_session_v1 import _manifest
    from src.ops.bounded_peaktrade_system_composition_v1.profile_v1 import (
        open_e1_offline_session_v1 as BoundedOfflineEpisodeSessionV1,
    )

    original_args = scenario._args
    monkeypatch.setattr(
        scenario, "_args", lambda *args: {**original_args(*args), "repository_sha": "a" * 40}
    )
    context, accounting, recover, invoke = scenario._scenario(tmp_path, direction)
    source_ref = Path(context.entry_source_ref.split(":", 2)[2])
    profile = None
    manifest = None
    completed = 0

    def consume(pairs, **kwargs):
        nonlocal profile, manifest, completed
        kwargs.pop("position_episode_bindings")
        kwargs.pop("position_episode_scope")
        native = pairs["LANE_1"][1].venue_native_id
        asof = int(kwargs["observed_unix"] * 1000)
        if profile is None:
            profile = _profiles(
                tmp_path / "public-facts",
                canonical=context.identity.instrument_id,
                native=native,
                now_ms=asof,
                last_ms=int(kwargs["last_finalized_event_ts_unix"] * 1000),
                direction=direction,
            )
            manifest = _manifest(
                context, source_ref, Path(pairs["LANE_1"][0].lane_state_root), pairs["LANE_1"][1], 2
            )
            manifest = replace(
                manifest,
                data_profile_digest=purpose_profile_digest_v1(profile),
                host_completion_required=True,
            )
        else:
            from copy import deepcopy
            from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
                load_all_facts_v1,
            )

            path = default_store_paths_v1(tmp_path / "public-facts")
            row = deepcopy(
                next(
                    f
                    for f in reversed(load_all_facts_v1(path))
                    if f["fact_kind"] == "OhlcvIntervalFactV1"
                )
            )
            row["interval_start_ms"] += 60000
            row["timestamps"] = {
                **row["timestamps"],
                "venue_event_time_ms": row["interval_start_ms"],
                "captured_at": datetime.fromtimestamp(asof / 1000, tz=timezone.utc).isoformat(),
            }
            for key in ("open_px", "high_px", "low_px", "close_px"):
                row[key] = "1020.2" if direction == 1 else "979.8"
            append_fact_v1(path, row)
        kwargs.update(origin_main_sha="b" * 40, candles_payload=None)
        root = tmp_path / "profile-session"
        with BoundedOfflineEpisodeSessionV1(
            manifest=manifest,
            state_root=root,
            mode="create" if completed == 0 else "recover",
            data_sources=profile,
        ) as opened:
            assert (
                len(
                    opened.read_data_for_purpose_v1(
                        purpose="RESEARCH", as_of_ms=asof, interval_ms=60000
                    )
                )
                == 99 + completed
            )
            result = opened.run_occupied_cycle_v1(pairs, **kwargs)
            market_context = result[
                "LANE_1"
            ].s7_invocation.cycle_result.replay.intermediate.market_context
            assert (
                int(
                    datetime.fromisoformat(
                        market_context.decision_time.replace("Z", "+00:00")
                    ).timestamp()
                    * 1000
                )
                == asof
            )
            assert datetime.fromisoformat(
                market_context.market_event_time.replace("Z", "+00:00")
            ) < datetime.fromisoformat(market_context.decision_time.replace("Z", "+00:00"))
            assert opened.last_completion_result.productive_runtime_cardinality == "1_JOINED"
            completed += 1
        with BoundedOfflineEpisodeSessionV1(
            manifest=manifest, state_root=root, mode="recover", data_sources=profile
        ) as restored:
            assert restored.state["attempts_used"] == completed
        bad = {**profile, "TRADING": replace(profile["TRADING"], expected_volume_unit="BASE_ASSET")}
        with pytest.raises(ValueError, match="DATA_PROFILE_CHANGED"):
            with BoundedOfflineEpisodeSessionV1(
                manifest=manifest, state_root=root, mode="recover", data_sources=bad
            ):
                pass
        return result

    # Root uses its already imported original N1 port; this intercept only supplies profile input.
    original_consumer = scenario.consumer

    class ConsumerProxy:
        def __getattr__(self, name):
            return getattr(original_consumer, name)

        invoke_occupied_lane_governed_cycle_n1_consumer_v1 = staticmethod(consume)

    monkeypatch.setattr(scenario, "consumer", ConsumerProxy())
    if completion_failure:
        from src.ops.current_mf_n5_full_autonomy_runtime_n5_completion_v1 import (
            completion_join_v1 as completion,
        )

        def fail(*args, **kwargs):
            raise OSError("injected after N1 before completion ACK")

        monkeypatch.setattr(completion, "complete_occupied_lane_runtime_n5_from_readiness_v1", fail)
        with pytest.raises(OSError, match="before completion ACK"):
            invoke(recover(), 65, 1000 + direction * 94.4)
        root = tmp_path / "profile-session"
        import json
        from src.ops.bounded_peaktrade_system_composition_v1.session_v1 import RECEIPT

        receipt = json.loads((root / RECEIPT).read_text())
        assert receipt["status"] == "RECOVERY_REQUIRED" and receipt["attempts_used"] == 1
        with pytest.raises(ValueError, match="INTERRUPTED_ATTEMPT"):
            with BoundedOfflineEpisodeSessionV1(
                manifest=manifest, state_root=root, mode="recover", data_sources=profile
            ):
                pytest.fail("reopened interrupted completion")
        assert list(tmp_path.rglob("governed_cycle_orchestrator_ledger_v1.json"))
        assert str(accounting.position.qty) == "0.4"
        return
    record = invoke(recover(), 65, 1000 + direction * 94.4)
    ledger = Path(record.evidence_root) / "governed_cycle_orchestrator_ledger_v1.json"
    original_bytes = ledger.read_bytes()
    second = invoke(recover(), 66, 1000 + direction * 94.4)
    assert completed == 2 and record.evidence_root != second.evidence_root
    assert ledger.read_bytes() == original_bytes
    assert second.governed_cycle_result.final_order_envelope.quantity == "0.4"
    assert record.governed_cycle_result.final_order_envelope.quantity == "0.4"
    assert (
        not record.governed_cycle_result.permit_created
        and record.governed_cycle_result.post_count == 0
    )
    assert str(accounting.position.qty) == "0.4"


def test_e1_entry_rejects_an_unpinned_legacy_profile_before_writes(tmp_path):
    from tests.ops.test_bounded_offline_episode_session_v1 import _setup
    from src.ops.bounded_peaktrade_system_composition_v1.profile_v1 import (
        open_e1_offline_session_v1,
    )

    manifest, _ = _setup(tmp_path)
    with pytest.raises(ValueError, match="COMPLETE_DATA_AND_COMPLETION_PROFILE_REQUIRED"):
        open_e1_offline_session_v1(
            manifest=manifest, state_root=tmp_path / "strict", mode="create", data_sources={}
        )
    assert not (tmp_path / "strict").exists()


def test_a_finalized_flag_cannot_make_a_future_candle_available(tmp_path):
    source = _profiles(tmp_path / "facts")["TRADING"]
    from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import load_all_facts_v1

    facts = load_all_facts_v1(default_store_paths_v1(tmp_path / "facts"))
    row = next(dict(f) for f in reversed(facts) if f["fact_kind"] == "OhlcvIntervalFactV1")
    row["interval_start_ms"] += 60000
    row["timestamps"] = {**row["timestamps"], "venue_event_time_ms": row["interval_start_ms"]}
    append_fact_v1(default_store_paths_v1(tmp_path / "facts"), row)
    with pytest.raises(ValueError, match="FINALIZED_BAR_NOT_CLOSED_ASOF"):
        source.trading_c1_v1(native_id="ETH-USDT-SWAP")


def test_fresh_ohlcv_is_not_promoted_to_authoritative_outcome(tmp_path):
    source = _profiles(tmp_path / "facts")["TRADING"]
    source = replace(
        source,
        policy=replace(source.policy, purpose="OUTCOME", consumer=CONSUMERS["OUTCOME"]),
        expected_interval_ms=3600000,
    )
    with pytest.raises(ValueError, match="AUTHORITATIVE_O4_KIND_REQUIRED"):
        source.outcome_snapshot_v1(
            native_id="ETH-USDT-SWAP", decision_event_ref="ddo.dec:e1-negative", n_bars=2
        )


def test_research_window_is_part_of_the_pinned_data_profile(tmp_path):
    sources = _profiles(tmp_path / "facts")
    before = purpose_profile_digest_v1(sources)
    changed = replace(sources["RESEARCH"], expected_interval_ms=3600000)
    assert purpose_profile_digest_v1({**sources, "RESEARCH": changed}) != before
    with pytest.raises(ValueError, match="WINDOW_MISMATCH"):
        changed.research_returns_v1(native_id="ETH-USDT-SWAP", interval_ms=60000)


def test_reobservation_and_explicit_correction_keep_one_pit_sample(tmp_path):
    from copy import deepcopy
    from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import load_all_facts_v1

    sources = _profiles(tmp_path / "facts")
    source = sources["RESEARCH"]
    path = default_store_paths_v1(tmp_path / "facts")
    row = deepcopy(
        next(
            f for f in reversed(load_all_facts_v1(path)) if f["fact_kind"] == "OhlcvIntervalFactV1"
        )
    )
    before = source.research_returns_v1(native_id="ETH-USDT-SWAP", interval_ms=60000)
    row["timestamps"]["captured_at"] = datetime.fromtimestamp(
        (source.as_of_ms + 1000) / 1000, tz=timezone.utc
    ).isoformat()
    append_fact_v1(path, row)
    later = source.at_v1(source.as_of_ms + 1000)
    assert len(later.research_returns_v1(native_id="ETH-USDT-SWAP", interval_ms=60000)) == len(
        before
    )
    changed = deepcopy(row)
    changed["timestamps"]["captured_at"] = datetime.fromtimestamp(
        (source.as_of_ms + 2000) / 1000, tz=timezone.utc
    ).isoformat()
    changed["quality"]["corrected"] = True
    for k in ("open_px", "high_px", "low_px", "close_px"):
        changed[k] = "1021"
    append_fact_v1(path, changed)
    with pytest.raises(ValueError, match="CORRECTION_FORBIDDEN"):
        source.at_v1(source.as_of_ms + 2000).research_returns_v1(
            native_id="ETH-USDT-SWAP", interval_ms=60000
        )
    allowed = replace(source, policy=replace(source.policy, allow_corrected=True))
    corrected = allowed.at_v1(source.as_of_ms + 2000).research_returns_v1(
        native_id="ETH-USDT-SWAP", interval_ms=60000
    )
    assert len(corrected) == len(before) and corrected.iloc[-1] > before.iloc[-1]
    import pandas as pd

    pd.testing.assert_series_equal(
        before, allowed.research_returns_v1(native_id="ETH-USDT-SWAP", interval_ms=60000)
    )
