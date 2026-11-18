from contextlib import closing
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest

from src.ops.full_core_live_path_composition_root_v1 import pretrade_acquisition_v1
from src.ops.full_core_live_path_composition_root_v1.current_productive_s6_live_fresh_c1_continuous_observation_source_v1 import (
    LiveFreshC1ContinuousObservationSourceV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    load_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.offline_first_entry_start_v2 import (
    OfflineFirstEntryMarketInputsV2,
    run_offline_first_entry_start_v2,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from src.ops.portfolio_capital_reservation_budget_v1.slot_loss_budget_v1 import (
    SlotCapitalAllocationV1,
)
from tests.ops.test_bounded_multislot_connected_cycle_v1 import ports
from tests.ops.test_bounded_multislot_entry_budget_v1 import policy
from tests.ops.test_first_entry_mark_clock_v2 import (
    CANDLE_OPEN,
    NATIVE,
    market_kwargs,
    mark_kwargs,
    no_network as no_network,
)
from tests.ops.test_portfolio_budget_host_v1 import _fetch


@pytest.mark.parametrize(
    "fault",
    [None, "prepared", "foreign-cycle", "max-quantity", "occupied", "restarted-after-enter"],
)
def test_brev_existing_poller_to_original_25_usdc_owner(tmp_path, monkeypatch, fault):
    market = market_kwargs(tmp_path, 1)
    bound = market["bound"]
    offset = iter((2, 2, 4, 6, 8, 12, 14, 16, 18))
    candle_root = tmp_path / "entry" / "flat-entry-mark-v2" / "LANE_1"
    clock = CANDLE_OPEN + 61.0
    candle_calls = []
    mark_calls = []
    pretrade_calls = []

    class PublicFixture:
        def get(self, *, endpoint, auth_required, **kwargs):
            nonlocal clock
            assert not auth_required
            assert f"instId={NATIVE}" in endpoint
            if "/candles?" in endpoint:
                candle_calls.append(endpoint)
                return SimpleNamespace(get_performed=True, payload=market["candles_payload"])
            assert "/mark-price?" in endpoint
            seconds = next(offset)
            tick = mark_kwargs(seconds, 0.109 + seconds * 0.0005)
            clock = round(tick["observed_unix"], 3)
            mark_calls.append(seconds)
            return SimpleNamespace(
                get_performed=True,
                payload=tick["mark_price_payload"],
                acquired_at_utc=tick["mark_acquired_at_utc"],
            )

    def now():
        return datetime.fromtimestamp(clock, timezone.utc).isoformat()

    monkeypatch.setattr(pretrade_acquisition_v1, "utc_now_iso_v1", now)
    public = LiveFreshC1ContinuousObservationSourceV1(
        cursor_store_root=candle_root,
        evidence_root=tmp_path / "public-evidence",
        run_id="offline-brev-first-entry",
        native_id=NATIVE,
        transport=PublicFixture(),
    )
    account = "offline-brev-account"

    def pretrade(epoch, cycle_id):
        pretrade_calls.append((epoch, cycle_id))
        if fault == "restarted-after-enter" and len(pretrade_calls) == 1:
            raise InterruptedError("proof process stopped after the committed ENTER")
        data = ports(bound, epoch, cycle_id, denied=fault == "max-quantity", account=account)
        limits = data.venue_quantity_limits
        metadata = data.instruments_payload
        native = next(row for row in metadata["data"] if row["instId"] == NATIVE)
        native.update(ctVal="1", tickSz="0.00001")
        body = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
        private = json.loads(limits.private_source.payload_json)
        if fault == "max-quantity":
            private["data"][0]["maxSell"] = "0"
        private_body = json.dumps(private, sort_keys=True, separators=(",", ":"))
        limits = replace(
            limits,
            public_source=replace(
                limits.public_source,
                acquired_at_utc=epoch,
                payload_json=body,
                response_body_sha256=sha256(body.encode()).hexdigest(),
            ),
            private_source=replace(
                limits.private_source,
                acquired_at_utc=epoch,
                payload_json=private_body,
                response_body_sha256=sha256(private_body.encode()).hexdigest(),
            ),
        )
        return replace(
            data,
            acquisition_decision_id=epoch,
            acquisition_cycle_id="foreign" if fault == "foreign-cycle" else cycle_id,
            pretrade_acquired_at_utc=(epoch,),
            venue_quantity_limits=replace(limits, integrity_digest=limits.digest_v1()),
        )

    positions = [{"instId": NATIVE, "pos": "1", "posSide": "net"}] if fault == "occupied" else ()
    host_settings = dict(
        root=tmp_path / "budget",
        private_rest_fetch=_fetch(uid=account, positions=positions),
        repository_sha="offline-brev-v2",
        session_id="offline-brev",
        expected_account_identity=account,
        clock=lambda: clock,
        execution_environment="INTERNAL_SIMULATED_EXECUTION",
        entry_budget_policy=policy(),
    )
    allocation = SlotCapitalAllocationV1(
        account, "test:initial-allocation", (("LANE_1", Decimal("25")),)
    )
    with closing(
        PortfolioBudgetHostV1(
            **host_settings, durable_mode="create", slot_capital_allocation=allocation
        )
    ) as host:
        args = dict(
            state_root=tmp_path / "entry",
            bound=bound,
            budget_host=host,
            source=public,
            market_inputs=lambda _: OfflineFirstEntryMarketInputsV2(
                **{k: market[k] for k in OfflineFirstEntryMarketInputsV2.__dataclass_fields__}
            ),
            pretrade=pretrade,
            reconciliation=market["reconciliation"],
            max_polls=5,
            clock=lambda: clock,
            prepare_read_only_pretrade=fault == "prepared",
        )
        if fault == "restarted-after-enter":
            with pytest.raises(InterruptedError, match="committed ENTER"):
                run_offline_first_entry_start_v2(**args)
            assert host.owner.stored_reservation_count_v1() == 0
            assert not host.owner.execution_links_v1()
            prior = load_current_productive_sidestate_confirmation_cursor_v1(candle_root)
            parent = json.loads(
                prior["entry_assessment_frame"]["components"]["parent"]["canonical"]
            )
            original_decision = parent["decision_id"]
            original_mark_count = prior["cap61_confirmation_state"]["observation_acceptance_state"][
                "market_observation_epoch"
            ]["value"]
            original_scope = host.owner.durable_scope_identity_v1()
            host.close()
            with closing(
                PortfolioBudgetHostV1(**host_settings, durable_mode="recover")
            ) as reopened:
                assert reopened.owner is None
                result = run_offline_first_entry_start_v2(**(args | {"budget_host": reopened}))
                assert result.disposition == "PRE_EXTERNAL_EFFECT", result
                assert result.decision_id != original_decision
                assert pretrade_calls[0][1] != pretrade_calls[1][1]
                assert (
                    datetime.fromisoformat(pretrade_calls[1][0])
                    - datetime.fromisoformat(pretrade_calls[0][0])
                ).total_seconds() > 5
                assert reopened.owner.durable_scope_identity_v1() == original_scope
                assert reopened.owner.stored_reservation_count_v1() == 1
                assert reopened.owner.slot_capital_basis_v1("LANE_1").net_basis_usdc == Decimal(
                    "25"
                )
                revived = load_current_productive_sidestate_confirmation_cursor_v1(candle_root)
                assert (
                    revived["cap61_confirmation_state"]["observation_acceptance_state"][
                        "market_observation_epoch"
                    ]["value"]
                    > original_mark_count
                )
                assert len(pretrade_calls) == 2
            return

        result = run_offline_first_entry_start_v2(**args)
        if fault == "occupied":
            assert result.reason == "START_ACCOUNT_NOT_FLAT"
            assert not mark_calls and not pretrade_calls
            assert host.owner.stored_reservation_count_v1() == 0
            return

        assert mark_calls == [2, 2, 4, 6] and len(candle_calls) == 4
        assert result.polls == 4 and len(pretrade_calls) == 1
        cursor = load_current_productive_sidestate_confirmation_cursor_v1(candle_root)
        frame = cursor["entry_assessment_frame"]
        assert (
            json.loads(frame["components"]["parent"]["canonical"])["decision_id"]
            == result.decision_id
        )
        assert (
            cursor["cap61_confirmation_state"]["observation_acceptance_state"][
                "market_observation_epoch"
            ]["value"]
            == 3
        )
        if fault and fault != "prepared":
            assert result.disposition == "BLOCKED", result.reason
            assert result.envelope is None and not host.owner.execution_links_v1()
            assert host.owner.active_sum_v1() == 0
            expected = (
                "ENTRY_PRETRADE_BINDING_MISMATCH"
                if fault == "foreign-cycle"
                else "VENUE_QUANTITY_EXCEEDS_MAXBUY"
            )
            assert result.reason == expected
            return

        assert result.disposition == "PRE_EXTERNAL_EFFECT", result
        assert host.owner.slot_capital_basis_v1("LANE_1").net_basis_usdc == Decimal("25")
        assert 0 < host.owner.active_slot_sum_v1("LANE_1") <= 25
        envelope = result.envelope
        assert envelope.instrument_id == NATIVE and envelope.side == "buy"
        link = host.owner.execution_links_v1()[result.reservation_id]
        assert link["phase"] == "PLAN_BOUND" and link["identity"] is None
        assert "external_effect_permit" not in link
        assert link["envelope"] == envelope.to_runtime_json_v1()
        assert len(host.owner.execution_links_v1()) == host.owner.stored_reservation_count_v1() == 1
        root = host_settings["root"] / "owner" / "reservations.sqlite3"
        inode = root.stat().st_ino
        stored_plan = host.owner.execution_plan_context_v1(result.reservation_id, envelope)
        assert stored_plan.order_environment == "INTERNAL_SIMULATED_EXECUTION"

    with closing(PortfolioBudgetHostV1(**host_settings, durable_mode="recover")) as reopened:
        second = run_offline_first_entry_start_v2(**(args | {"budget_host": reopened}))
        assert second.disposition == "ENTRY_ALREADY_DECIDED"
        assert len(pretrade_calls) == 1
        assert root.stat().st_ino == inode
        assert reopened.owner.stored_reservation_count_v1() == 1
        assert reopened.owner.execution_links_v1()[result.reservation_id] == link
