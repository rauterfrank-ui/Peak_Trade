"""Original BTC Core -> journal -> fill -> C1/Exit consumers; fixture sources only."""

from dataclasses import replace
from datetime import datetime, timezone
import json

import pytest

from src.ops import btc_demo_lane3_v2 as demo
from src.ops.btc_demo_offline_trading_host_v1 import (
    BtcDemoMarketObservationV1,
    BtcDemoOfflineTradingHostV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    load_current_productive_sidestate_confirmation_cursor_v1,
)
from tests.ops import test_btc_demo_budget_reconciliation_host_v1 as budget_fixture
from src.ops.exit_policy_producer_binding_v1.constants_v1 import FROZEN_PROFIT_PROTECTION_DISTANCE
from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
    layer_c_derived_exit_policy_adverse_config_digest_v1,
)

from tests.ops.test_btc_demo_source_observation_integrity_v1 import (
    NOW,
    CoverageReads,
    coverage_source,
)
from tests.ops.test_current_usdc_xperp_financial_admission_v1 import instrument
from tests.ops.test_governed_futures_universe_producer_v1 import _produce
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1 import (
    _bound,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_c1_aligned_g17_dk_producer_v1,
)
from tests.ops._current_productive_reconciliation_admission_test_helpers_v1 import (
    non_productive_harness_master_v2_reconciliation_admission_v1,
)

EXIT_CONFIG = layer_c_derived_exit_policy_adverse_config_digest_v1(
    profit_protection_distance=FROZEN_PROFIT_PROTECTION_DISTANCE
)


def setup_host(tmp_path, monkeypatch, direction=1, *, policy=None, testnet_v2=False):
    row = instrument(settlement="USD")
    row["instId"] = demo._NATIVE
    row["expTime"] = str(int(datetime(2031, 3, 28, 8, tzinfo=timezone.utc).timestamp() * 1000))
    universe = _produce([row], marks=[demo._NATIVE])
    (selected,) = universe.snapshot.instruments
    bound = replace(
        _bound(lane_id="LANE_3", instrument_id=selected.canonical_instrument_id),
        venue_native_id=demo._NATIVE,
    )
    monkeypatch.setattr(budget_fixture, "BOUND", bound)
    monkeypatch.setattr(budget_fixture, "BINDINGS", {"LANE_3": bound})
    budget, _ = budget_fixture.owner_host(tmp_path, policy=policy, testnet_v2=testnet_v2)
    c1 = NOW.timestamp() - 120
    closes = [64000 * (1 + direction * (i - 99) * 0.002) for i in range(100)]
    candles = {
        "code": "0",
        "data": [
            [str(int(1000 * (c1 + (i - 99) * 60))), *(str(p),) * 4, "5", "5", "5", "1"]
            for i, p in enumerate(closes)
        ],
    }
    producer = governed_c1_aligned_g17_dk_producer_v1(
        bound=bound,
        anchor_event_ts_unix=c1,
        evidence_store_root=tmp_path / "g17",
        mark_closes=closes,
    )
    host = BtcDemoOfflineTradingHostV1(
        budget_host=budget,
        g17_producer=producer,
        repository_sha="f" * 40,
        config_digest=EXIT_CONFIG,
        writer_session_id="btc-offline-join",
    )
    reconciliation = non_productive_harness_master_v2_reconciliation_admission_v1(
        bound=bound, session_id="btc-offline-join", repository_sha="f" * 40
    )
    return host, candles, reconciliation, row


def observation(candles, seconds, price, *, flat=True):
    c1 = NOW.timestamp() - 120
    event = c1 + 60 + seconds
    acquired = datetime.fromtimestamp(event + 0.1, timezone.utc).isoformat()
    return BtcDemoMarketObservationV1(
        "USD",
        f"btc-original-{seconds}",
        event + 0.2,
        candles,
        {
            "code": "0",
            "data": [
                {
                    "instId": demo._NATIVE,
                    "markPx": str(price),
                    "idxPx": str(price),
                    "ts": str(int(event * 1000)),
                }
            ],
        },
        acquired,
        price - 0.1,
        price + 0.1,
        100.0,
        200.0,
        0.0001,
        flat,
    )


def enter(host, candles, reconciliation, direction=1):
    for i in range(8):
        obs = observation(candles, 2 + 2 * i, 64000 + direction * 600 * i)
        result = host.prepare_entry_v1(observation=obs, reconciliation=reconciliation)
        if result.status == "ENTRY_DECIDED":
            return result, obs
    pytest.fail("Original BTC Core did not produce entry")


class MatchingReads(budget_fixture.ExecutionReads):
    def read(self, path, **query):
        payload, stamp = super().read(path, **query)
        if self.identity.selected_side == "SHORT":
            if path in {demo._ORDER, demo._FILLS}:
                for row in payload["data"]:
                    row["side"] = "sell"
            if path == demo._POSITIONS:
                for row in payload["data"]:
                    row["pos"] = "-" + self.quantity
        return payload, stamp


def seed_and_bind(tmp_path, monkeypatch, direction=1):
    host, candles, reconciliation, row = setup_host(tmp_path, monkeypatch, direction)
    entry, obs = enter(host, candles, reconciliation, direction)
    _, rid, identity = budget_fixture.seed_attempt(
        tmp_path,
        existing_host=host.budget,
        decision_id=entry.cycle.replay.evidence.decision_id,
        cycle_id=obs.cycle_id + ":LANE_3",
        quantity_cap="1",
        contract_multiplier="0.0001",
        lot_size="1",
        side="LONG" if direction == 1 else "SHORT",
    )
    reads = MatchingReads(identity, quantity=identity.final_quantity)
    episode, publication, result = host.reconcile_confirmed_entry_v1(
        reads=reads, reservation_id=rid, clock=NOW.timestamp
    )
    return host, candles, reconciliation, episode, publication, result, entry


@pytest.mark.parametrize("direction", [1, -1])
def test_original_btc_core_and_g17_reach_real_first_fill_publication(
    tmp_path, monkeypatch, direction
):
    host, candles, reconciliation, episode, publication, result, entry = seed_and_bind(
        tmp_path, monkeypatch, direction
    )
    try:
        assert publication["status"] == "PUBLISHED_RETAINED_CURSOR"
        assert episode.identity.account_scope.execution_environment == "TESTNET"
        assert episode.identity.venue_native_id == demo._NATIVE
        assert episode.identity.lane_id == "LANE_3"
        raw = load_current_productive_sidestate_confirmation_cursor_v1(host.cursor_root)
        assert raw["entry_assessment_frame"] is None
        assert (
            raw["cap61_confirmation_state"]["observation_acceptance_state"][
                "last_accepted_observation_identity"
            ]["venue_event_time"]
            == NOW.timestamp() - 120
        )
        assert host.budget.owner.active_sum_v1() > 0
        research = demo.read_btc_demo_first_fill_for_research_v1(
            host.budget.root, episode.identity.episode_id
        )
        assert research["decision_id"] == entry.cycle.replay.evidence.decision_id
        assert research["opening_fill"]["entry_price_usd"] == "64000"
    finally:
        host.budget.owner.close()


@pytest.mark.parametrize("private_settlement", ["USD", "USDC"])
def test_usd_price_and_private_settlement_never_create_implicit_usdc_operands(
    tmp_path, monkeypatch, private_settlement
):
    host, candles, reconciliation, row = setup_host(tmp_path, monkeypatch)
    try:
        entry, _ = enter(host, candles, reconciliation)
        rows = coverage_source()
        row["settleCcy"] = private_settlement
        rows[demo._INSTRUMENTS] = [row]
        report = demo.read_btc_demo_coverage_v2(
            reads=CoverageReads(rows=rows), expected_uid=budget_fixture.ACCOUNT
        )
        before = host.budget.budget_revision_ref_v1()
        result = host.assess_monetary_entry_v1(entry=entry, coverage=report, now=NOW.timestamp())
        assert result["status"] == "BLOCKED" and result["canonical_sizing_operands"] is None
        assert result["native_price_currency"] == "USD" and result["capital_currency"] == "USDC"
        assert result["authority"] == "NONE"
        assert (
            host.budget.budget_revision_ref_v1() == before
            and host.budget.owner.active_sum_v1() == 0
        )
    finally:
        host.budget.owner.close()


@pytest.mark.parametrize("direction", [1, -1])
def test_original_btc_occupied_mark_consumes_same_episode_and_separate_c1_clock(
    tmp_path, monkeypatch, direction
):
    from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
        restore_layered_core_episode_v1,
        read_occupied_scope_mark_snapshot_v1,
    )

    host, candles, reconciliation, episode, publication, result, entry = seed_and_bind(
        tmp_path, monkeypatch, direction
    )
    try:
        held = host.budget.owner.active_sum_v1()
        core = restore_layered_core_episode_v1(
            host.cursor_root, expected_instrument_id=host.budget.bound.instrument_id
        )
        price = core.running_reference.reference_price_r_t + (
            0.1 if core.regime.value == "bull" else -0.1
        )
        obs = observation(candles, 62, price, flat=False)
        cycle = host.continue_occupied_v1(
            episode=episode,
            observation=obs,
            reconciliation=reconciliation,
            execution_reconciliation=result,
        )
        assert cycle.replay.replay_pass, cycle.fail_reasons
        assert cycle.decision_outcome not in {"enter_long", "enter_short"}
        retained = read_occupied_scope_mark_snapshot_v1(host.cursor_root)
        assert retained["mark"]["position_episode_id"] == episode.identity.episode_id
        assert retained["mark"]["prices"] == [price]
        assert retained["mark"]["event_unix"] == NOW.timestamp() + 2
        raw = load_current_productive_sidestate_confirmation_cursor_v1(host.cursor_root)
        assert (
            raw["cap61_confirmation_state"]["observation_acceptance_state"][
                "last_accepted_observation_identity"
            ]["venue_event_time"]
            == NOW.timestamp() - 120
        )
        assert host.budget.owner.active_sum_v1() == held > 0
    finally:
        host.budget.owner.close()


def test_first_entry_recovery_preserves_original_research_source_across_writer_sessions(
    tmp_path, monkeypatch
):
    host, candles, reconciliation, episode, publication, result, entry = seed_and_bind(
        tmp_path, monkeypatch
    )
    lane = demo._demo_lane_root(host.budget.root)
    receipt = lane / "research-first-fills" / f"{episode.identity.episode_id}.json"
    before = receipt.read_bytes()
    try:
        identity = demo.parse_exchange_reconciliation_identity_v1(result["identity"])
        host.writer_session_id = "btc-offline-recovered-writer"
        repeated = host.reconcile_confirmed_entry_v1(
            reads=MatchingReads(identity, quantity=identity.final_quantity),
            reservation_id=identity.portfolio_reservation_id,
            clock=NOW.timestamp,
        )
        assert repeated[1]["status"] == "ALREADY_PUBLISHED"
        assert receipt.read_bytes() == before
        assert json.loads(before)["body"]["session_id"] == "btc-offline-join"
        assert host.budget.owner.active_sum_v1() > 0
    finally:
        host.budget.owner.close()


@pytest.mark.parametrize(
    "fault", ["decision", "missing-g17", "foreign-g17", "advanced-g17", "cold-g17"]
)
def test_entry_lineage_rejection_precedes_opening_artifacts(tmp_path, monkeypatch, fault):
    from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
        CanonicalVolatilityTypedRuntimeProducerScaffoldV1 as Producer,
    )

    host, candles, reconciliation, row = setup_host(tmp_path, monkeypatch)
    entry, obs = enter(host, candles, reconciliation)
    _, rid, identity = budget_fixture.seed_attempt(
        tmp_path,
        existing_host=host.budget,
        decision_id="foreign-decision"
        if fault == "decision"
        else entry.cycle.replay.evidence.decision_id,
        quantity_cap="1",
        contract_multiplier="0.0001",
        lot_size="1",
    )
    if fault == "missing-g17":
        host.g17 = None
    elif fault == "foreign-g17":
        host.g17 = governed_c1_aligned_g17_dk_producer_v1(
            bound=replace(host.budget.bound, instrument_id="foreign-canonical"),
            anchor_event_ts_unix=NOW.timestamp() - 120,
            evidence_store_root=tmp_path / "foreign-g17",
        )
    elif fault == "advanced-g17":
        host.g17.ingest_finalized_pt1m_mark_sample_v1(
            event_time_unix_seconds=NOW.timestamp() - 60, mark_price=64001
        )
    elif fault == "cold-g17":
        host.g17 = Producer.restore_from_persistence_v1(persistence_path=host.g17.persistence_path)
    try:
        with pytest.raises(
            ValueError, match="BTC_DEMO_ORIGINAL_ENTRY_(DECISION_MISMATCH|G17_LINEAGE_REQUIRED)"
        ):
            host.reconcile_confirmed_entry_v1(
                reads=MatchingReads(identity, quantity=identity.final_quantity),
                reservation_id=rid,
                clock=NOW.timestamp,
            )
        lane = demo._demo_lane_root(host.budget.root)
        assert not (lane / "confirmed-first-fills" / f"{identity.identity_digest()}.json").exists()
        assert not (lane / "position-episodes" / identity.identity_digest()).exists()
        assert host.budget.owner.active_sum_v1() > 0
    finally:
        host.budget.owner.close()


def test_cold_original_budget_and_exit_cursor_retry_preserve_opening(tmp_path, monkeypatch):
    from src.ops.btc_demo_budget_reconciliation_host_v1 import BtcDemoBudgetReconciliationHostV1

    host, candles, reconciliation, episode, publication, result, entry = seed_and_bind(
        tmp_path, monkeypatch
    )
    root = host.budget.root
    scope = host.budget.owner.durable_scope_identity_v1()
    held = host.budget.owner.active_sum_v1()
    original = demo.read_btc_demo_first_fill_for_research_v1(root, episode.identity.episode_id)
    host.budget.owner.close()
    owner = budget_fixture.Owner(
        durable_root=scope["root"],
        durable_account_identity=budget_fixture.ACCOUNT,
        durable_mode="recover",
        durable_lane_bindings={"LANE_3": host.budget.bound},
    )
    try:
        host.budget = BtcDemoBudgetReconciliationHostV1(
            owner=owner, bound=host.budget.bound, account=budget_fixture.ACCOUNT, testnet_root=root
        )
        host.writer_session_id = "cold-original-writer"
        identity = demo.parse_exchange_reconciliation_identity_v1(result["identity"])
        restored, published, _ = host.reconcile_confirmed_entry_v1(
            reads=MatchingReads(identity, quantity=identity.final_quantity),
            reservation_id=identity.portfolio_reservation_id,
            clock=NOW.timestamp,
        )
        assert restored.identity == episode.identity and published["status"] == "ALREADY_PUBLISHED"
        assert (
            demo.read_btc_demo_first_fill_for_research_v1(root, episode.identity.episode_id)
            == original
        )
        assert owner.active_sum_v1() == held > 0 and owner.budget_state_v1().recovery_required
    finally:
        owner.close()


def test_cold_g17_requires_distinct_finalized_sample_before_occupied_consumer(
    tmp_path, monkeypatch
):
    from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
        CanonicalVolatilityTypedRuntimeProducerScaffoldV1 as Producer,
    )
    from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
        restore_layered_core_episode_v1,
    )

    host, candles, reconciliation, episode, publication, result, entry = seed_and_bind(
        tmp_path, monkeypatch
    )
    try:
        prior = host.g17
        host.g17 = Producer.restore_from_persistence_v1(persistence_path=prior.persistence_path)
        assert host.g17.history.history_digest == prior.history.history_digest
        assert host.g17.output_port_v1().estimate is None
        # The original restore restores history, not a fabricated ready estimate.
        latest = host.g17.history.trailing_window_records_v1(count=1)[0]
        host.g17.ingest_finalized_pt1m_mark_sample_v1(
            event_time_unix_seconds=latest.event_time.unix_seconds, mark_price=latest.mark_price
        )
        assert host.g17.output_port_v1().estimate is None
        new_c1 = NOW.timestamp() - 60
        produced = host.g17.ingest_finalized_pt1m_mark_sample_v1(
            event_time_unix_seconds=new_c1, mark_price=64001
        )
        assert produced.estimate is not None
        next_candles = {
            "code": "0",
            "data": candles["data"]
            + [[str(int(new_c1 * 1000)), *("64001",) * 4, "5", "5", "5", "1"]],
        }
        core = restore_layered_core_episode_v1(
            host.cursor_root, expected_instrument_id=host.budget.bound.instrument_id
        )
        obs = observation(
            next_candles, 62, core.running_reference.reference_price_r_t + 0.1, flat=False
        )
        cycle = host.continue_occupied_v1(
            episode=episode,
            observation=obs,
            reconciliation=reconciliation,
            execution_reconciliation=result,
        )
        assert cycle.replay.replay_pass, cycle.fail_reasons
        raw = load_current_productive_sidestate_confirmation_cursor_v1(host.cursor_root)
        # The occupied scope-Mark consumer does not count a new C1 confirmation.
        assert (
            raw["cap61_confirmation_state"]["observation_acceptance_state"][
                "last_accepted_observation_identity"
            ]["venue_event_time"]
            == NOW.timestamp() - 120
        )
        assert (
            cycle.replay.intermediate.market_context.canonical_volatility_estimate.as_of_event_time.timestamp()
            == new_c1
        )
        assert host.budget.owner.active_sum_v1() > 0
    finally:
        host.budget.owner.close()


def test_native_usd_reaches_original_missing_conversion_gate(tmp_path, monkeypatch):
    from decimal import Decimal
    from src.ops.governed_productive_monetary_normalization_v1.normalize_v1 import (
        build_capital_risk_sizing_monetary_context_v1,
    )
    from src.ops.governed_productive_monetary_normalization_v1.contracts_v1 import (
        MonetaryNormalizationError,
    )

    host, candles, reconciliation, row = setup_host(tmp_path, monkeypatch)
    try:
        with pytest.raises(MonetaryNormalizationError, match="NORMALIZATION_UNAVAILABLE_FOR_USD"):
            build_capital_risk_sizing_monetary_context_v1(
                decision_epoch=NOW.isoformat(),
                observed_at=NOW.isoformat(),
                fresh_pretrade_get_status="TRUSTED_PRESENT",
                account_equity_amount=Decimal("30"),
                account_equity_currency="USDC",
                native_reference_price=Decimal("64000"),
                native_protective_stop_price=Decimal("63000"),
                instruments_payload={"code": "0", "data": [row]},
                venue_native_id=demo._NATIVE,
                index_tickers_payload=None,
            )
        assert host.budget.owner.active_sum_v1() == 0
    finally:
        host.budget.owner.close()


@pytest.mark.parametrize("fault", ["currency", "flat", "stale-mark", "productive-context"])
def test_occupied_input_rejections_preserve_cursor_and_hold(tmp_path, monkeypatch, fault):
    host, candles, reconciliation, episode, publication, result, entry = seed_and_bind(
        tmp_path, monkeypatch
    )
    try:
        held = host.budget.owner.active_sum_v1()
        before = load_current_productive_sidestate_confirmation_cursor_v1(host.cursor_root)
        obs = observation(candles, 62, 64000, flat=False)
        if fault == "currency":
            obs = replace(obs, native_price_currency="USDC")
        elif fault == "flat":
            obs = replace(obs, venue_flat=True)
        elif fault == "stale-mark":
            obs = replace(obs, observed_unix=obs.observed_unix + 6)
        else:
            from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_reconciliation_admission_v1 import (
                ProductiveMasterV2ReconciliationAdmissionContextV1,
            )

            reconciliation = replace(
                reconciliation,
                context_class=ProductiveMasterV2ReconciliationAdmissionContextV1.PRODUCTIVE_UPSTREAM_GATE,
            )
        with pytest.raises(ValueError):
            host.continue_occupied_v1(
                episode=episode,
                observation=obs,
                reconciliation=reconciliation,
                execution_reconciliation=result,
            )
        assert load_current_productive_sidestate_confirmation_cursor_v1(host.cursor_root) == before
        assert host.budget.owner.active_sum_v1() == held
    finally:
        host.budget.owner.close()


def test_existing_hold_blocks_new_flat_entry(tmp_path, monkeypatch):
    host, candles, reconciliation, episode, publication, result, entry = seed_and_bind(
        tmp_path, monkeypatch
    )
    try:
        with pytest.raises(ValueError, match="EXISTING_OBLIGATION_BLOCKS_NEW_ENTRY"):
            host.prepare_entry_v1(
                observation=observation(candles, 62, 64000), reconciliation=reconciliation
            )
        assert host.budget.owner.active_sum_v1() > 0
    finally:
        host.budget.owner.close()


@pytest.mark.parametrize("direction", [1, -1])
@pytest.mark.parametrize(
    "fault",
    [None, "expired-before", "expired-after", "older-reads", "budget-change", "wrong-account"],
)
def test_testnet_entry_reads_bound_to_original_decision_and_budget(
    tmp_path, monkeypatch, direction, fault
):
    from datetime import timedelta

    host, candles, admission, row = setup_host(tmp_path, monkeypatch, direction)
    try:
        entry, _ = enter(host, candles, admission, direction)
        epoch = entry.cycle.replay.intermediate.market_context.decision_time
        start = datetime.fromisoformat(epoch.replace("Z", "+00:00"))
        captured = start - timedelta(milliseconds=1) if fault == "older-reads" else start
        data = coverage_source()
        data[demo._INSTRUMENTS] = [dict(row, settleCcy="USDC")]
        data[demo._FX][0]["ts"] = str(int(captured.timestamp() * 1000))
        if fault == "wrong-account":
            data[demo._CONFIG][0]["uid"] = "999"

        class Reads(CoverageReads):
            def read(self, path, **query):
                if fault == "budget-change" and path == demo._FX:
                    host.budget.owner.restart_fail_closed_v1()
                return super().read(path, **query)

        reads = Reads(rows=data, times={key: captured for key in data})
        clock = iter(
            [
                start.timestamp() + (6 if fault == "expired-before" else 0),
                start.timestamp() + (6 if fault == "expired-after" else 0),
            ]
        )
        before = host.budget.budget_revision_ref_v1()
        if fault:
            reason = {
                "expired-before": "ACQUISITION_STALE",
                "expired-after": "ACQUISITION_STALE",
                "older-reads": "READ_PREDATES_REQUEST",
                "budget-change": "BUDGET_HEAD_CHANGED",
                "wrong-account": "DEMO_ACCOUNT_MISMATCH",
            }[fault]
            with pytest.raises(ValueError, match=reason):
                host.inspect_testnet_entry_v1(entry=entry, reads=reads, clock=clock.__next__)
            if fault == "expired-before":
                assert not reads.calls
        else:
            report = host.inspect_testnet_entry_v1(entry=entry, reads=reads, clock=clock.__next__)
            assert report["execution_environment"] == "TESTNET" and report["lane_id"] == "LANE_3"
            assert report["decision_id"] == entry.cycle.replay.evidence.decision_id
            assert report["decision_epoch"] == epoch and report["cycle_id"] == entry.cycle.cycle_id
            assert report["decision_outcome"] == ("enter_long" if direction == 1 else "enter_short")
            assert report["venue_native_id"] == demo._NATIVE
            assert report["budget_revision"] == before
            read = report["demo_capital_read"]
            assert (
                read.observed_usdc_available == "30"
                and read.account_identity == host.budget.account
            )
            assert read.balance_acquired_at == captured.isoformat()
            assert (
                read.budget_revision == before and read.coverage_digest == report["coverage_digest"]
            )
            assert (read.decision_id, read.cycle_id, read.decision_epoch) == (
                report["decision_id"],
                entry.cycle.cycle_id,
                epoch,
            )
            from src.ops.full_core_live_path_composition_root_v1.current_productive_treasury_single_source_capital_handoff_v1 import (
                execute_current_productive_treasury_single_source_capital_handoff_v1,
            )
            from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
                admit_sized_slot_reservation_v1,
            )

            treasury = execute_current_productive_treasury_single_source_capital_handoff_v1(
                margin_observation=read,
                instrument_id=read.instrument_id,
                body_sha256=read.coverage_digest,
                fresh_pretrade_get_status="TRUSTED_PRESENT",
                live_account_bound_status="TRUSTED_PRESENT",
            )
            assert (
                treasury.fail_closed
                and "PRODUCTIVE_USDC_MARGIN_OBSERVATION_REQUIRED" in treasury.reason_codes
            )
            reserved = admit_sized_slot_reservation_v1(
                host.budget.owner,
                observation=read,
                p01=None,
                eligibility=None,
                slot_id="LANE_3",
                decision_id=read.decision_id,
                cycle_id=read.cycle_id,
                instrument_id=read.instrument_id,
                account_identity=read.account_identity,
                sizing_input=None,
                fresh_pretrade_get_status="TRUSTED_PRESENT",
                live_account_bound_status="TRUSTED_PRESENT",
                fresh_evidence_fetched=True,
                fresh_evidence_validated=True,
            )
            assert reserved.disposition.value == "FAIL_CLOSED" and reserved.reservation is None
            assert reserved.reason_codes == (
                "PRODUCTIVE_USDC_MARGIN_OBSERVATION_REQUIRED",
                "PRODUCER_OUTPUT_NOT_ADMITTED",
            )
            assert report["available_usdc_covers_declared_budget"] is True
            assert report["taker_fee_rate_signed"] == "-0.0005"
            assert [path for path, _ in reads.calls] == [
                demo._CONFIG,
                demo._BALANCE,
                demo._INSTRUMENTS,
                demo._FEE,
                demo._FX,
            ]
            assert report["status"] == "BLOCKED" and report["canonical_sizing_operands"] is None
        if fault != "budget-change":
            assert host.budget.budget_revision_ref_v1() == before
        assert host.budget.owner.active_sum_v1() == 0
    finally:
        host.budget.owner.close()
