"""BTC occupied decisions require current original execution truth, not an old fill."""

from copy import deepcopy
from datetime import timedelta
import json

import pytest

from src.ops import btc_demo_lane3_v2 as demo
from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
    restore_layered_core_episode_v1,
    read_occupied_scope_mark_snapshot_v1,
)
from tests.ops.test_btc_demo_source_observation_integrity_v1 import (
    NOW,
    CoverageReads,
    coverage_source,
)

from tests.ops.test_btc_demo_offline_trading_host_v1 import (
    EXIT_CONFIG,
    observation,
    seed_and_bind,
    setup_host,
    enter,
    MatchingReads,
)


class CurrentReads(MatchingReads):
    def __init__(self, identity, *, seconds=10, config_age=0, pending=False, position=None):
        super().__init__(identity, quantity=identity.final_quantity)
        self.seconds, self.config_age, self.pending, self.position = (
            seconds,
            config_age,
            pending,
            position,
        )

    def read(self, path, **query):
        payload, _ = super().read(path, **query)
        if self.pending and path == demo._PENDING:
            payload["data"] = [
                {
                    "instId": demo._NATIVE,
                    "ordId": "987",
                    "clOrdId": "foreign-pending",
                    "state": "live",
                    "sz": "1",
                    "side": "buy",
                    "posSide": "net",
                }
            ]
        if self.position is not None and path == demo._POSITIONS:
            payload["data"][0]["pos"] = self.position
        return payload, NOW + timedelta(
            seconds=self.seconds - (self.config_age if path == demo._CONFIG else 0)
        )


def core_files(host, episode):
    from pathlib import Path

    return {
        str(p): p.read_bytes()
        for root in (host.cursor_root, Path(episode.binding.state_root))
        for p in root.rglob("*")
        if p.is_file()
    }


def continue_at(host, candles, admission, episode, report, seconds=70, price=None):
    if price is None:
        core = restore_layered_core_episode_v1(
            host.cursor_root, expected_instrument_id=host.budget.bound.instrument_id
        )
        price = core.running_reference.reference_price_r_t + (
            0.1 if core.regime.value == "bull" else -0.1
        )
    return host.continue_occupied_v1(
        episode=episode,
        observation=observation(candles, seconds, price, flat=False),
        reconciliation=admission,
        execution_reconciliation=report,
    )


def test_stale_original_fill_cannot_advance_current_occupied_mark(tmp_path, monkeypatch):
    host, candles, admission, episode, _, report, _ = seed_and_bind(tmp_path, monkeypatch)
    try:
        with pytest.raises(ValueError, match="BTC_DEMO_OCCUPIED_RECONCILIATION_STALE_OR_FUTURE"):
            host.continue_occupied_v1(
                episode=episode,
                observation=observation(candles, 70, 64000, flat=False),
                reconciliation=admission,
                execution_reconciliation=report,
            )
    finally:
        host.budget.owner.close()


@pytest.mark.parametrize("direction", [1, -1])
def test_fresh_original_reconciliation_reaches_core_without_budget_admission(
    tmp_path, monkeypatch, direction
):
    host, candles, admission, episode, _, old, _ = seed_and_bind(tmp_path, monkeypatch, direction)
    try:
        identity = demo.parse_exchange_reconciliation_identity_v1(old["identity"])
        fresh = host.budget.reconcile_attempt_v1(
            reads=CurrentReads(identity),
            reservation_id=identity.portfolio_reservation_id,
            clock=lambda: NOW.timestamp() + 10,
        )
        head = host.budget.budget_revision_ref_v1()
        held = host.budget.owner.active_sum_v1()
        cycle = continue_at(host, candles, admission, episode, fresh)
        assert cycle.replay.replay_pass, cycle.fail_reasons
        assert (
            host.budget.budget_revision_ref_v1() == head
            and host.budget.owner.active_sum_v1() == held > 0
        )
        assert not host.budget.owner.budget_state_v1().admitted
    finally:
        host.budget.owner.close()


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "legacy",
        "retimestamp-config",
        "changed-body",
        "changed-revision",
        "corrupt-receipt",
        "symlink-receipt",
        "old-head",
        "stale-config",
        "future",
    ],
)
def test_rejected_execution_sources_leave_core_and_hold_unchanged(tmp_path, monkeypatch, fault):
    host, candles, admission, episode, _, report, _ = seed_and_bind(tmp_path, monkeypatch)
    try:
        identity = demo.parse_exchange_reconciliation_identity_v1(report["identity"])
        if fault == "stale-config":
            report = host.budget.reconcile_attempt_v1(
                reads=CurrentReads(identity, config_age=4.9),
                reservation_id=identity.portfolio_reservation_id,
                clock=lambda: NOW.timestamp() + 10,
            )
        elif fault not in {"old-head", "future"}:
            report = host.budget.reconcile_attempt_v1(
                reads=CurrentReads(identity),
                reservation_id=identity.portfolio_reservation_id,
                clock=lambda: NOW.timestamp() + 10,
            )
        if fault == "missing":
            report = None
        elif fault == "legacy":
            report.pop("observation_receipt_digest")
        elif fault == "retimestamp-config":
            report["source_observations"][0]["acquired_at"] = (
                NOW + timedelta(seconds=10.1)
            ).isoformat()
        elif fault == "changed-body":
            report["source_observations"][0]["payload"]["data"][0]["uid"] = "999"
        elif fault == "changed-revision":
            report["budget_revision"][0] += 1
        elif fault in {"corrupt-receipt", "symlink-receipt"}:
            path = (
                demo._demo_lane_root(host.budget.root)
                / "execution-observations"
                / f"{report['observation_receipt_digest']}.json"
            )
            if fault == "corrupt-receipt":
                path.write_text("{}")
            else:
                target = tmp_path / "receipt-target.json"
                target.write_bytes(path.read_bytes())
                path.unlink()
                path.symlink_to(target)
        elif fault == "old-head":
            host.budget.reconcile_attempt_v1(
                reads=CurrentReads(identity),
                reservation_id=identity.portfolio_reservation_id,
                clock=lambda: NOW.timestamp() + 10,
            )
        elif fault == "future":
            report = host.budget.reconcile_attempt_v1(
                reads=CurrentReads(identity, seconds=11),
                reservation_id=identity.portfolio_reservation_id,
                clock=lambda: NOW.timestamp() + 11,
            )
        before = core_files(host, episode)
        held = host.budget.owner.active_sum_v1()
        head = host.budget.budget_revision_ref_v1()
        with pytest.raises(ValueError):
            continue_at(host, candles, admission, episode, report)
        assert core_files(host, episode) == before
        assert (
            host.budget.owner.active_sum_v1() == held > 0
            and host.budget.budget_revision_ref_v1() == head
        )
    finally:
        host.budget.owner.close()


@pytest.mark.parametrize("position", [None, "0", "2", "-1"])
def test_pending_or_changed_current_position_blocks_unrelated_occupied_progress(
    tmp_path, monkeypatch, position
):
    host, candles, admission, episode, _, report, _ = seed_and_bind(tmp_path, monkeypatch)
    try:
        identity = demo.parse_exchange_reconciliation_identity_v1(report["identity"])
        report = host.budget.reconcile_attempt_v1(
            reads=CurrentReads(identity, pending=position is None, position=position),
            reservation_id=identity.portfolio_reservation_id,
            clock=lambda: NOW.timestamp() + 10,
        )
        before = core_files(host, episode)
        held = host.budget.owner.active_sum_v1()
        with pytest.raises(ValueError):
            continue_at(host, candles, admission, episode, report)
        assert core_files(host, episode) == before and host.budget.owner.active_sum_v1() == held > 0
    finally:
        host.budget.owner.close()


def test_budget_change_after_source_validation_is_fenced_before_core_write(tmp_path, monkeypatch):
    host, candles, admission, episode, _, report, _ = seed_and_bind(tmp_path, monkeypatch)
    try:
        original = host.budget._require_matched_reconciliation_v1

        def race(*args, **kwargs):
            result = original(*args, **kwargs)
            host.budget.owner.restart_fail_closed_v1()
            return result

        monkeypatch.setattr(host.budget, "_require_matched_reconciliation_v1", race)
        before = core_files(host, episode)
        with pytest.raises(ValueError, match="BUDGET_HEAD_CHANGED"):
            continue_at(host, candles, admission, episode, report, seconds=62)
        assert core_files(host, episode) == before and host.budget.owner.active_sum_v1() > 0
    finally:
        host.budget.owner.close()


@pytest.mark.parametrize("direction", [1, -1])
def test_original_scope_switch_retains_pending_reversal_without_demo_dispatch_or_booking(
    tmp_path, monkeypatch, direction
):
    host, candles, admission, episode, _, report, _ = seed_and_bind(
        tmp_path, monkeypatch, direction
    )
    try:
        native = restore_layered_core_episode_v1(
            host.cursor_root, expected_instrument_id=host.budget.bound.instrument_id
        )
        direction = 1 if native.regime.value == "bull" else -1
        mark = native.running_reference.reference_price_r_t - direction * 1.5 * native.scope.d_t
        held = host.budget.owner.active_sum_v1()
        head = host.budget.budget_revision_ref_v1()
        cycle = continue_at(host, candles, admission, episode, report, seconds=62, price=mark)
        assert cycle.replay.replay_pass, cycle.fail_reasons
        retained = read_occupied_scope_mark_snapshot_v1(host.cursor_root)
        assert retained["mark"]["switch_condition_met"] is True
        assert retained["mark"]["pending_reversal_episode_id"] == episode.identity.episode_id
        before = core_files(host, episode)
        with pytest.raises(ValueError, match="REVERSAL_ALREADY_PLANNED"):
            continue_at(
                host, candles, admission, episode, report, seconds=63, price=mark + direction * 0.1
            )
        assert core_files(host, episode) == before
        assert (
            host.budget.owner.active_sum_v1() == held > 0
            and host.budget.budget_revision_ref_v1() == head
        )
        assert (
            host.budget.owner.read_authenticated_net_reversal_v1(identity_reservation_id(report))
            is None
        )
    finally:
        host.budget.owner.close()


def identity_reservation_id(report):
    return demo.parse_exchange_reconciliation_identity_v1(
        report["identity"]
    ).portfolio_reservation_id


def test_legacy_first_fill_report_remains_readable_without_occupied_upgrade(tmp_path, monkeypatch):
    host, candles, admission, episode, _, report, _ = seed_and_bind(tmp_path, monkeypatch)
    legacy = deepcopy(report)
    legacy.pop("observation_receipt_digest")
    try:
        restored, published = host.budget.bind_confirmed_entry_v1(
            reconciliation=legacy,
            repository_sha=host.repository_sha,
            config_digest=EXIT_CONFIG,
            writer_session_id="legacy-first-fill-readback",
            g17_producer=host.g17,
            cursor_store_root=host.cursor_root,
        )
        assert restored.identity == episode.identity and published["status"] == "ALREADY_PUBLISHED"
        with pytest.raises(ValueError, match="OBSERVATION_RECEIPT_REQUIRED"):
            continue_at(host, candles, admission, episode, legacy, seconds=62)
        assert host.budget.owner.active_sum_v1() > 0
    finally:
        host.budget.owner.close()


def test_original_exchange_snapshot_alone_does_not_bind_config_receipt(tmp_path, monkeypatch):
    host, candles, admission, episode, _, report, _ = seed_and_bind(tmp_path, monkeypatch)
    try:
        identity = demo.parse_exchange_reconciliation_identity_v1(report["identity"])
        captured = demo.BtcDemoObservationsV1(None)
        captured.rows = deepcopy(report["source_observations"])
        first = demo.collect_btc_demo_execution_observation_v1(captured.replay_v1(), identity)[0]
        captured.rows[0]["acquired_at"] = (NOW - timedelta(seconds=1)).isoformat()
        second = demo.collect_btc_demo_execution_observation_v1(captured.replay_v1(), identity)[0]
        assert first.to_dict() == second.to_dict()
        changed = deepcopy(report)
        changed["source_observations"] = captured.rows
        with pytest.raises(ValueError, match="OBSERVATION_RECEIPT_MISMATCH"):
            continue_at(host, candles, admission, episode, changed, seconds=62)
    finally:
        host.budget.owner.close()


def test_original_owner_lock_covers_actual_core_consumer(tmp_path, monkeypatch):
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1 import (
        addressing_join_v1 as join,
    )

    host, candles, admission, episode, _, report, _ = seed_and_bind(tmp_path, monkeypatch)
    original = join.compose_occupied_lane_mv2_dp_durable_cycle_v1
    consumed = []

    def observe(*args, **kwargs):
        acquired = host.budget.owner._lock.acquire(blocking=False)
        if acquired:
            host.budget.owner._lock.release()
        assert acquired is False
        consumed.append(True)
        return original(*args, **kwargs)

    monkeypatch.setattr(join, "compose_occupied_lane_mv2_dp_durable_cycle_v1", observe)
    try:
        assert continue_at(host, candles, admission, episode, report, seconds=62).replay.replay_pass
        assert consumed == [True]
        assert host.budget.owner._lock.acquire(blocking=False)
        host.budget.owner._lock.release()
    finally:
        host.budget.owner.close()


def test_cold_original_budget_requires_new_current_receipt_and_preserves_opening(
    tmp_path, monkeypatch
):
    from src.ops.btc_demo_budget_reconciliation_host_v1 import BtcDemoBudgetReconciliationHostV1
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1,
    )

    host, candles, admission, episode, _, old, _ = seed_and_bind(tmp_path, monkeypatch)
    scope = host.budget.owner.durable_scope_identity_v1()
    root, bound = host.budget.root, host.budget.bound
    opening = demo.read_btc_demo_first_fill_for_research_v1(root, episode.identity.episode_id)
    host.budget.owner.close()
    owner = PortfolioCapitalReservationBudgetOwnerV1(
        durable_root=scope["root"],
        durable_account_identity=scope["account"],
        durable_mode="recover",
        durable_lane_bindings={"LANE_3": bound},
    )
    try:
        host.budget = BtcDemoBudgetReconciliationHostV1(
            owner=owner, bound=bound, account=scope["account"], testnet_root=root
        )
        with pytest.raises(ValueError, match="STALE_OR_FUTURE"):
            continue_at(host, candles, admission, episode, old)
        identity = demo.parse_exchange_reconciliation_identity_v1(old["identity"])
        fresh = host.budget.reconcile_attempt_v1(
            reads=CurrentReads(identity),
            reservation_id=identity.portfolio_reservation_id,
            clock=lambda: NOW.timestamp() + 10,
        )
        assert continue_at(host, candles, admission, episode, fresh).replay.replay_pass
        assert (
            demo.read_btc_demo_first_fill_for_research_v1(root, episode.identity.episode_id)
            == opening
        )
        assert owner.active_sum_v1() > 0 and not owner.budget_state_v1().admitted
    finally:
        owner.close()


def test_receipt_write_failure_retains_budget_commit_and_retry_creates_no_second_revision(
    tmp_path, monkeypatch
):
    from src.ops import btc_demo_budget_reconciliation_host_v1 as module

    host, candles, admission, episode, _, old, _ = seed_and_bind(tmp_path, monkeypatch)
    original = module.immutable_json_v1
    identity = demo.parse_exchange_reconciliation_identity_v1(old["identity"])

    def fail(*args, **kwargs):
        raise OSError("Synthetic receipt storage failure")

    try:
        held = host.budget.owner.active_sum_v1()
        monkeypatch.setattr(module, "immutable_json_v1", fail)
        with pytest.raises(OSError, match="Synthetic receipt"):
            host.budget.reconcile_attempt_v1(
                reads=CurrentReads(identity),
                reservation_id=identity.portfolio_reservation_id,
                clock=lambda: NOW.timestamp() + 10,
            )
        head = host.budget.budget_revision_ref_v1()
        assert host.budget.owner.active_sum_v1() == held > 0
        monkeypatch.setattr(module, "immutable_json_v1", original)
        fresh = host.budget.reconcile_attempt_v1(
            reads=CurrentReads(identity),
            reservation_id=identity.portfolio_reservation_id,
            clock=lambda: NOW.timestamp() + 10,
        )
        assert host.budget.budget_revision_ref_v1() == head
        assert continue_at(host, candles, admission, episode, fresh).replay.replay_pass
        path = (
            demo._demo_lane_root(host.budget.root)
            / "execution-observations"
            / f"{fresh['observation_receipt_digest']}.json"
        )
        assert json.loads(path.read_bytes()) == {
            k: v for k, v in fresh.items() if k != "observation_receipt_digest"
        }
    finally:
        host.budget.owner.close()


@pytest.mark.parametrize("settlement", ["USD", "USDC"])
@pytest.mark.parametrize("rate", ["1", "0.9998", "1.0002"])
def test_index_valuation_private_unit_and_canonical_numeraire_remain_distinct(
    tmp_path, monkeypatch, settlement, rate
):
    host, candles, admission, row = setup_host(tmp_path, monkeypatch)
    try:
        entry, _ = enter(host, candles, admission)
        rows = coverage_source()
        row["settleCcy"] = settlement
        rows[demo._INSTRUMENTS] = [row]
        rows[demo._FX][0]["idxPx"] = rate
        coverage = demo.read_btc_demo_coverage_v2(
            reads=CoverageReads(rows=rows), expected_uid=host.budget.account
        )
        head = host.budget.budget_revision_ref_v1()
        report = host.assess_monetary_entry_v1(entry=entry, coverage=coverage, now=NOW.timestamp())
        assert report["status"] == "BLOCKED" and report["canonical_sizing_operands"] is None
        assert (
            report["native_price_currency"] == "USD"
            and report["canonical_risk_numeraire"] == "USDC"
        )
        assert report["physical_usdc_required_for_numeraire"] is False
        assert report["instrument_monetary_identity"]["settle_currency"] == settlement
        assert report["instrument_monetary_identity"]["instrument_money_unit"] == settlement
        assert report["public_index_valuation"] == dict(
            role="PUBLIC_INDEX_VALUATION_ONLY",
            declared_budget_usdc=coverage["budget_usdc"],
            declared_budget_value_usd=coverage["budget_value_usd"],
        )
        assert (
            report["account_settlement_proven"]
            is report["usd_usdc_conversion_operator_proven"]
            is False
        )
        assert (
            host.budget.budget_revision_ref_v1() == head and host.budget.owner.active_sum_v1() == 0
        )
    finally:
        host.budget.owner.close()


@pytest.mark.parametrize("direction", [1, -1])
def test_demo_mark_stream_returns_on_switch_before_polling_another_mark(
    tmp_path, monkeypatch, direction
):
    host, candles, admission, episode, _, report, _ = seed_and_bind(
        tmp_path, monkeypatch, direction
    )
    try:
        core = restore_layered_core_episode_v1(
            host.cursor_root, expected_instrument_id=host.budget.bound.instrument_id
        )
        sign = 1 if core.regime.value == "bull" else -1
        price = core.running_reference.reference_price_r_t - sign * 1.5 * core.scope.d_t

        def marks():
            yield observation(candles, 62, price, flat=False)
            pytest.fail("a mark was pulled before the pending reversal was settled")

        (cycle,) = host.iter_occupied_marks_v1(
            episode=episode,
            observations=marks(),
            reconciliation=admission,
            execution_reconciliation=lambda: report,
        )
        assert cycle.replay.replay_pass
        assert (
            read_occupied_scope_mark_snapshot_v1(host.cursor_root)["mark"][
                "pending_reversal_episode_id"
            ]
            == episode.identity.episode_id
        )
    finally:
        host.budget.owner.close()
