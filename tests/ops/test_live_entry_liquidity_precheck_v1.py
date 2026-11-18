"""Offline evidence for the original-plan, pre-permit liquidity boundary."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
import socket
from urllib.parse import parse_qs, urlsplit

import pytest

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
    invoke_occupied_lane_governed_cycle_n1_consumer_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import LANE_IDS
from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    inspect_original_portfolio_execution_context_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FreshPretradeGetTransportResultV1,
)
from src.ops.live_entry_liquidity_precheck_v1 import (
    LiveEntryLiquidityBlockedV1,
    forward_live_entry_after_liquidity_check_v1,
    precheck_live_entry_liquidity_v1,
)
from tests.ops.test_bounded_multislot_connected_cycle_v1 import connected


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def deny(*args, **kwargs):
        pytest.fail("Live-entry liquidity proof uses offline source responses")

    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket.socket, "connect_ex", deny)


def _profiles(path):
    lines = ['schema = "live_entry_liquidity_profiles.v1"', "[slot_profiles]"]
    lines.extend(f'{lane} = "fixture-{i}"' for i, lane in enumerate(LANE_IDS, 1))
    for i in range(1, 6):
        lines.extend(
            (
                f"[profiles.fixture-{i}]",
                f'spread_limit_bps = "{5 if i == 2 else 30 + i}"',
                f'slippage_limit_bps = "{40 + i}"',
                'adv_participation_limit = "0.10"',
                f"adv_days = {i + 2}",
            )
        )
    path.write_text("\n".join(lines) + "\n")
    return path


class _PublicLiquidityFixture:
    def __init__(self, *, owner, reservation_id, now, fault=None, on_capture=None):
        state = owner.risk_snapshot_v1()["state"]
        (reservation,) = (
            row for row in state["reservations"] if row["reservation_id"] == reservation_id
        )
        self.instrument = reservation["binding"]["bound"]
        self.sizing = state["sizing_bindings"][reservation_id]["applied_input"]["instrument"]
        self.side = state["execution_links"][reservation_id]["envelope"]["side"]
        self.now = now
        self.fault = fault
        self.on_capture = on_capture
        self.requests = []

    def get(self, *, endpoint, auth_required, pretrade_decision_id, **kwargs):
        url = urlsplit(endpoint)
        query = parse_qs(url.query)
        native = self.instrument["venue_native_id"]
        assert auth_required is False and query["instId"] == [native]
        self.requests.append(endpoint)
        path = url.path
        event = int(self.now * 1000) - 100
        when = datetime.fromtimestamp(self.now, timezone.utc).isoformat()
        tick = Decimal(self.sizing["tick_size"])
        lot = Decimal(self.sizing["lot_size"])
        size = Decimal(self.sizing["contract_multiplier"])
        mark = Decimal(100)
        offset = tick * max(1, Decimal(".10") // tick)
        kind = "SWAP" if native.endswith("-SWAP") else "FUTURES"
        _, _, base, _, settle, _ = self.instrument["instrument_id"].split(":")
        if self.fault == "metadata":
            size *= 2
        if path == "/api/v5/public/instruments":
            assert query["instType"] == [kind]
            data = [
                {
                    "instId": native,
                    "instType": kind,
                    "ctType": "linear",
                    "ctValCcy": base,
                    "settleCcy": settle,
                    "state": "live",
                    "tickSz": str(tick),
                    "lotSz": str(lot),
                    "minSz": self.sizing["minimum_quantity"],
                    "maxMktSz": str(lot * 100000),
                    "ctVal": str(size),
                    "ctMult": "1",
                }
            ]
        elif path == "/api/v5/market/books":
            clock = event - 60000 if self.fault == "stale" else event
            depth = lot if self.fault == "thin" else lot * 100000
            mid = mark
            if self.fault == "slippage":
                step = tick * max(1, Decimal(1) // tick)
                mid += step if self.side == "buy" else -step
            data = [
                {
                    "ts": str(clock),
                    "instId": native if self.fault != "foreign" else "OTHER",
                    "bids": [[str(mid - offset), str(depth)]],
                    "asks": [[str(mid + offset), str(depth)]],
                }
            ]
        elif path == "/api/v5/market/candles":
            days = int(query["limit"][0]) - 1
            midnight = int(self.now) // 86400 * 86400000
            contracts = lot if self.fault == "adv" else Decimal("10000000")
            data = [
                [
                    str(midnight - d * 86400000),
                    "100",
                    "100",
                    "100",
                    "100",
                    str(contracts),
                    str(contracts * size),
                    str(contracts * size * mark),
                    "1",
                ]
                for d in range(1, days + 1)
            ]
        else:
            assert path == "/api/v5/public/mark-price" and query["instType"] == [kind]
            data = [{"instId": native, "ts": str(event), "markPx": str(mark)}]
            if self.on_capture is not None:
                self.on_capture()
        payload = {"code": "0", "data": data}
        body = json.dumps(payload).encode()
        result = FreshPretradeGetTransportResultV1(
            get_performed=True,
            method="GET",
            endpoint=endpoint,
            http_status=200,
            payload=payload,
            auth_header_sent=False,
            transport_class="OFFLINE_FIXTURE",
            venue_live_contact=True,
            historical_reuse=False,
            error_class="",
            body_sha256=sha256(body).hexdigest(),
            pretrade_decision_id=pretrade_decision_id,
            acquired_at_utc=when,
        )
        self.raw_response_sink_v1(result=result, body=body)
        return result


def _evaluate(
    owner,
    rid,
    envelope,
    *,
    now,
    profile_path=None,
    fault=None,
    on_capture=None,
    clock=None,
):
    transport = _PublicLiquidityFixture(
        owner=owner, reservation_id=rid, now=now, fault=fault, on_capture=on_capture
    )
    result = precheck_live_entry_liquidity_v1(
        owner=owner,
        reservation_id=rid,
        envelope=envelope,
        execution_plan_context=owner.execution_plan_context_v1(rid, envelope),
        transport_factory=lambda: transport,
        clock=clock if clock is not None else lambda: now,
        **({"profile_path": profile_path} if profile_path is not None else {}),
    )
    return result, transport.requests


@pytest.mark.parametrize("lane", LANE_IDS)
def test_each_slot_reads_its_own_profile_without_changing_owner_state(tmp_path, lane):
    profiles = _profiles(tmp_path / "profiles.toml")
    pairs, _, kwargs, host = connected(tmp_path, 1, canonical_ids=True, lane_ids=(lane,))
    try:
        plans = invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kwargs)
        owner = host.owner
        original = owner.risk_snapshot_v1()
        now = kwargs["observed_unix"]
        i = LANE_IDS.index(lane) + 1
        cycle = plans[lane].governed_cycle_result
        assert cycle.disposition == "PRE_EXTERNAL_EFFECT", cycle.first_real_blocker
        rid = cycle.extra["PORTFOLIO_RESERVATION_ID"]
        envelope = cycle.final_order_envelope
        assert cycle.post_count == 0 and not cycle.permit_created
        missing, requests = _evaluate(owner, rid, envelope, now=now)
        assert missing.reason_codes == (f"LIVE_ENTRY_LIQUIDITY_PROFILE_UNASSIGNED:{lane}",)
        assert not requests
        assessment, requests = _evaluate(owner, rid, envelope, profile_path=profiles, now=now)
        assert assessment.status == ("BLOCKED" if i == 2 else "PASS"), assessment
        if i == 2:
            assert assessment.reason_codes == ("LIVE_ENTRY_LIQUIDITY_SPREAD_LIMIT",)
        assert assessment.authority_effect == "NONE"
        proof = assessment.evidence
        assert proof["lane_id"] == lane and proof["profile_id"] == f"fixture-{i}"
        assert proof["bound"] == pairs[lane][1].to_dict()
        assert proof["envelope_digest"] == envelope.envelope_digest
        assert proof["liquidity"]["quantity_contracts"] == envelope.quantity
        assert proof["liquidity"]["adv_days"] == i + 2
        assert len(requests) == 4
        assert owner.risk_snapshot_v1() == original
    finally:
        host.close()


def test_live_aggregate_budget_veto_precedes_liquidity_on_five_plans(tmp_path):
    profiles = _profiles(tmp_path / "profiles.toml")
    pairs, _, kwargs, host = connected(tmp_path, 5, canonical_ids=True)
    try:
        plans = invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kwargs)
        before = host.owner.risk_snapshot_v1()
        cycle = plans["LANE_1"].governed_cycle_result
        result, requests = _evaluate(
            host.owner,
            cycle.extra["PORTFOLIO_RESERVATION_ID"],
            cycle.final_order_envelope,
            now=kwargs["observed_unix"],
            profile_path=profiles,
        )
        assert result.reason_codes == ("CURRENT_ENTRY_BUDGET_AGGREGATE_LIMIT_EXCEEDED",)
        assert not requests
        assert host.owner.risk_snapshot_v1() == before
    finally:
        host.close()


def test_owner_fence_during_public_capture_invalidates_the_precheck(tmp_path):
    profiles = _profiles(tmp_path / "profiles.toml")
    pairs, _, kwargs, host = connected(tmp_path, 1, canonical_ids=True)
    try:
        plans = invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kwargs)
        cycle = plans["LANE_1"].governed_cycle_result
        rid = cycle.extra["PORTFOLIO_RESERVATION_ID"]
        result, requests = _evaluate(
            host.owner,
            rid,
            cycle.final_order_envelope,
            now=kwargs["observed_unix"],
            profile_path=profiles,
            on_capture=host.owner.restart_fail_closed_v1,
        )
        assert result.status == "BLOCKED"
        assert result.reason_codes == ("EXECUTION_SUBMIT_OWNER_FENCED",)
        assert len(requests) == 4
        assert host.owner.execution_links_v1()[rid]["phase"] == "PLAN_BOUND"
    finally:
        host.close()


@pytest.mark.parametrize("lane", ("LANE_1", "LANE_2"))
def test_prepermit_handoff_checks_fresh_data_and_forwards_only_the_original_plan(tmp_path, lane):
    profile_path = _profiles(tmp_path / "profiles.toml")
    pairs, _, kwargs, host = connected(tmp_path, 1, canonical_ids=True, lane_ids=(lane,))
    try:
        plans = invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kwargs)
        cycle = plans[lane].governed_cycle_result
        assert cycle.disposition == "PRE_EXTERNAL_EFFECT", cycle.first_real_blocker
        assert cycle.post_count == 0 and not cycle.permit_created
        owner = host.owner
        rid, envelope = cycle.extra["PORTFOLIO_RESERVATION_ID"], cycle.final_order_envelope
        context = owner.execution_plan_context_v1(rid, envelope)
        before = owner.risk_snapshot_v1()
        now = kwargs["observed_unix"]
        forwarded = []
        captures = []

        def capture(fault=None):
            port = _PublicLiquidityFixture(owner=owner, reservation_id=rid, now=now, fault=fault)
            captures.append(port)
            return port

        def handoff(**actual):
            assert actual["envelope"] is envelope
            assert actual["portfolio_budget_owner"] is owner
            assert actual["portfolio_reservation_id"] == rid
            assert actual["execution_plan_context"] is context
            assert len(captures[-1].requests) == 4
            proof = inspect_original_portfolio_execution_context_v1(
                **actual, required_execution_environment="LIVE"
            )
            forwarded.append(proof)
            return proof

        common = dict(
            owner=owner,
            reservation_id=rid,
            envelope=envelope,
            execution_plan_context=context,
            prepermit_handoff=handoff,
            clock=lambda: now,
        )
        with pytest.raises(LiveEntryLiquidityBlockedV1, match="PROFILE_UNASSIGNED"):
            forward_live_entry_after_liquidity_check_v1(**common, transport_factory=capture)
        assert not captures and not forwarded

        if lane == "LANE_1":
            proof = forward_live_entry_after_liquidity_check_v1(
                **common, transport_factory=capture, profile_path=profile_path
            )
            assert proof["envelope_digest"] == envelope.envelope_digest
        else:
            with pytest.raises(LiveEntryLiquidityBlockedV1, match="SPREAD_LIMIT"):
                forward_live_entry_after_liquidity_check_v1(
                    **common, transport_factory=capture, profile_path=profile_path
                )

        with pytest.raises(LiveEntryLiquidityBlockedV1, match="SOURCE_STALE") as denied:
            forward_live_entry_after_liquidity_check_v1(
                **common, transport_factory=lambda: capture("stale"), profile_path=profile_path
            )
        assert denied.value.assessment.status == "BLOCKED"
        assert len(captures) == 2
        assert len(forwarded) == (1 if lane == "LANE_1" else 0)
        assert owner.risk_snapshot_v1() == before
    finally:
        host.close()


@pytest.mark.parametrize("short", [False, True])
def test_original_live_entry_plan_can_be_checked_before_any_permit(tmp_path, short):
    profiles = _profiles(tmp_path / "profiles.toml")
    pairs, _, kwargs, host = connected(tmp_path, 1, canonical_ids=True, short=short)
    try:
        plans = invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kwargs)
        cycle = plans["LANE_1"].governed_cycle_result
        assert cycle.disposition == "PRE_EXTERNAL_EFFECT", cycle.first_real_blocker
        assert cycle.post_count == 0 and not cycle.permit_created
        owner = host.owner
        rid, envelope = cycle.extra["PORTFOLIO_RESERVATION_ID"], cycle.final_order_envelope
        before = owner.risk_snapshot_v1()
        now = datetime.fromisoformat(envelope.creation_epoch).timestamp()
        proof, requests = _evaluate(owner, rid, envelope, now=now, profile_path=profiles)
        assert proof.status == "PASS", proof
        assert proof.evidence["order_environment"] == "LIVE"
        assert proof.evidence["liquidity"]["side"] == ("SELL" if short else "BUY")
        assert len(requests) == 4
        denials = (
            ("stale", "SOURCE_STALE"),
            ("foreign", "BOOK_INSTRUMENT_MISMATCH"),
            ("metadata", "CONTRACT_METADATA_CHANGED"),
            ("slippage", "SLIPPAGE_LIMIT"),
            ("adv", "ADV_PARTICIPATION_LIMIT"),
        )
        if short:
            denials += (("thin", "DEPTH_INSUFFICIENT"),)
        for fault, reason in denials:
            denied, _ = _evaluate(owner, rid, envelope, now=now, profile_path=profiles, fault=fault)
            assert denied.status == "BLOCKED", (fault, denied)
            assert reason in denied.reason_codes[0]
        expired, _ = _evaluate(
            owner,
            rid,
            envelope,
            now=now,
            profile_path=profiles,
            clock=iter((now, now + 6)).__next__,
        )
        assert expired.reason_codes == ("LIVE_ENTRY_LIQUIDITY_MARKET_EXPIRED",)
        profile_changed, _ = _evaluate(
            owner,
            rid,
            envelope,
            now=now,
            profile_path=profiles,
            on_capture=lambda: profiles.write_text(
                profiles.read_text().replace('spread_limit_bps = "31"', 'spread_limit_bps = "32"')
            ),
        )
        assert profile_changed.reason_codes == (
            "LIVE_ENTRY_LIQUIDITY_BINDING_CHANGED_DURING_CAPTURE",
        )
        wrong_quantity = str(Decimal(envelope.quantity) + 1)
        for foreign in (
            replace(envelope, reduce_only=True),
            replace(envelope, quantity=wrong_quantity),
        ):
            denied = precheck_live_entry_liquidity_v1(
                owner=owner,
                reservation_id=rid,
                envelope=foreign,
                execution_plan_context=owner.execution_plan_context_v1(rid, envelope),
                transport_factory=lambda: pytest.fail(
                    "foreign envelope must fail before public GETs"
                ),
                profile_path=profiles,
                clock=lambda: now,
            )
            assert denied.status == "BLOCKED"
        assert owner.risk_snapshot_v1() == before
    finally:
        host.close()
