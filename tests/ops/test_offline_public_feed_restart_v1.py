"""R01 through original Safety, S6, S5 and S7 with isolated account and market ports."""

from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
import json
from pathlib import Path

import pytest

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    canonical_json_dumps,
)
from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_governed_continuous_cycle_orchestrator_v1 as s6,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    cursor_last_accepted_c1_venue_event_time_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    bootstrap_s8_lane_via_s7_compose_v1,
    build_s8_occupied_lane_pairs_v1,
    run_offline_persistent_natural_enter_convergence_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
)
from src.ops.gates.risk_gate import kill_switch_should_block_trading
from src.ops.offline_public_feed_recovery_v1 import OfflinePublicFeedRecoveryError
from src.ops.offline_public_feed_restart_v1 import MANDATE_SCHEMA, OfflinePublicFeedRestartV1
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    FUTURES_INVENTORY_REQUEST_COUNT,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from src.risk_layer.kill_switch.state import KillSwitchState
from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
    okx_public_mark_price_payload_v1,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_c1_candles_payload_from_enter_closes_v1,
    strong_uptrend_closes_v1,
)
from tests.ops.test_current_futures_simulated_dispatch_v1 import seeded
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    _lane_g17,
)
from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
    _continuous_auth,
    _occupancy_absent,
)
from tests.ops.test_offline_public_feed_account_reconciliation_v1 import (
    _inventory_venue,
    _mark_feed,
    _open_budget_host,
)

KEY = b"explicit offline R01 test mandate authority only"


def _signed(body):
    return {
        "body": body,
        "signature": hmac.digest(KEY, canonical_json_dumps(body).encode(), "sha256").hex(),
    }


@pytest.fixture
def scenario(seeded, monkeypatch, request):
    old_host, bound, _, send = seeded
    old_host.close()
    native = bound.venue_native_id
    lane_base = old_host.root.parent / "lanes"
    pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane_base, bound=bound)
    producers = _lane_g17(pairs)
    cursor_path = Path(pairs["LANE_1"][0].lane_state_root) / CURSOR_FILENAME
    closes = strong_uptrend_closes_v1(count=128)
    now = datetime.now(timezone.utc)
    event = (int(now.timestamp()) // 60 - 1) * 60
    before = event - 60
    mark = okx_public_mark_price_payload_v1(native_id=native, mark_px=closes[103])
    mark["data"][0]["ts"] = str(int(now.timestamp() * 1000))
    bootstrap_s8_lane_via_s7_compose_v1(
        composed_pairs=pairs,
        origin_main_sha=old_host.repository_sha,
        g17_producers=producers,
        candles_payload=governed_c1_candles_payload_from_enter_closes_v1(
            enter_closes=closes[:102], last_event_ts_unix=before - 60
        ),
        mark_price_payload=mark,
        venue_native_id=native,
        mark_acquired_at_utc=now.isoformat(),
    )
    first_floor = cursor_last_accepted_c1_venue_event_time_v1(json.loads(cursor_path.read_bytes()))
    original_run = run_offline_persistent_natural_enter_convergence_v1(
        authorization=replace(
            _continuous_auth(native_id=native, max_cycles=1),
            expected_cursor_floor=first_floor,
        ),
        origin_main_sha=old_host.repository_sha,
        lane_state_root=lane_base,
        bound=bound,
        g17_producers=producers,
        observation_source=s6.ScriptedContinuousObservationSourceV1(
            [
                s6.InjectedContinuousObservationV1(
                    candles_payload=governed_c1_candles_payload_from_enter_closes_v1(
                        enter_closes=closes[:104],
                        last_event_ts_unix=before,
                    ),
                    occupancy_payloads=_occupancy_absent(),
                    mark_price_payload=mark,
                    mark_acquired_at_utc=now.isoformat(),
                )
            ]
        ),
        evidence_root=old_host.root.parent / "original-preincident-run",
    )
    assert original_run.disposition == s6.DISPOSITION_MAX_CYCLES, original_run.reason_code
    initial_cursor = cursor_path.read_bytes()
    before = cursor_last_accepted_c1_venue_event_time_v1(json.loads(initial_cursor))
    event = before + 60
    feed, receipt = _mark_feed(
        old_host,
        bound,
        monkeypatch,
        started_at=now - timedelta(seconds=31.5),
        mark_px=str(closes[105] + 1),
        index_px=str((closes[105] + 1) * 0.995),
        repair=getattr(request, "param", True),
    )
    venue = _inventory_venue(old_host.account)
    occupancy = {
        key: venue.fetch(path, {})
        for key, path in (
            ("CONFIG", "/api/v5/account/config"),
            ("POSITIONS", "/api/v5/account/positions"),
            ("PENDING", "/api/v5/trade/orders-pending"),
        )
    }
    candles = governed_c1_candles_payload_from_enter_closes_v1(
        enter_closes=closes[:106], last_event_ts_unix=event
    )
    observation = s6.InjectedContinuousObservationV1(
        candles_payload={**candles, "instId": native},
        occupancy_payloads=occupancy,
        mark_price_payload={"code": "0", "data": feed.frames[0]["data"]},
        mark_acquired_at_utc=receipt["mark"]["captured_at"] if receipt else "",
    )
    authorization = replace(
        _continuous_auth(native_id=native, max_cycles=1), expected_cursor_floor=before
    )
    mandate = _signed(
        {
            "schema": MANDATE_SCHEMA,
            "incident": feed.incident.binding(),
            "environment": old_host.execution_environment,
            "host_root": str(old_host.root),
            "account": old_host.account,
            "repository_sha": old_host.repository_sha,
            "selected_instrument": bound.to_dict(),
            "authorization": asdict(authorization),
            "cursor_path": str(cursor_path),
            "cursor_sha256": sha256(initial_cursor).hexdigest(),
            "expires_at": (feed.now + timedelta(seconds=4)).isoformat(),
        }
    )
    with _open_budget_host(
        old_host, feed, venue, monkeypatch, reads=FUTURES_INVENTORY_REQUEST_COUNT
    ) as host:
        yield dict(
            feed=feed,
            safety=OfflinePublicFeedRestartV1(feed.repair, authority_key=KEY),
            venue=venue,
            common=dict(host=host, bound=bound, authorization=authorization, mandate=mandate),
            observation=observation,
            producers=producers,
            cursor_path=cursor_path,
            initial_cursor=initial_cursor,
            send=send,
        )


def _resume(scenario, *, safety=None):
    return (safety or scenario["safety"]).resume_v1(
        **scenario["common"],
        observation=scenario["observation"],
        g17_producers=scenario["producers"],
    )


def test_r01_releases_and_restarts_actual_host_once_with_original_cursor(scenario):
    safety, common = scenario["safety"], scenario["common"]
    assert kill_switch_should_block_trading(explicit_active=False)
    release = safety.activate_v1(**common)
    assert release["account_evidence"]["account"] == common["host"].account
    assert not kill_switch_should_block_trading(explicit_active=False)
    assert scenario["cursor_path"].read_bytes() == scenario["initial_cursor"]
    assert safety.activate_v1(**common) == release

    result = _resume(scenario)
    assert result["cursor_after"] == result["cursor_before"] + 60
    before = json.loads(scenario["initial_cursor"])
    after = json.loads(scenario["cursor_path"].read_bytes())
    assert after["trading_epoch"] > before["trading_epoch"]
    assert scenario["send"]["simulated_transport"].post_count == 0
    assert len(scenario["venue"].requests) == FUTURES_INVENTORY_REQUEST_COUNT

    # Fresh owner instance reads the existing completion without invoking S6 twice.
    cold = OfflinePublicFeedRestartV1(scenario["feed"].cold_reader(), authority_key=KEY)
    assert _resume(scenario, safety=cold) == result


@pytest.mark.parametrize("scenario", [False], indirect=True)
def test_one_automatic_entry_runs_from_killed_feed_to_original_cursor(scenario):
    feed = scenario["feed"]
    assert feed.transport.state.reconnect_count == 0
    result = scenario["safety"].recover_and_resume_v1(
        **scenario["common"],
        runtime=feed.runtime,
        observation=scenario["observation"],
        g17_producers=scenario["producers"],
    )
    assert result["cursor_after"] == result["cursor_before"] + 60
    assert feed.transport.state.reconnect_count == 1
    assert not kill_switch_should_block_trading(explicit_active=False)
    assert scenario["send"]["simulated_transport"].post_count == 0


def test_foreign_c1_after_release_fences_safety_before_host_cycle(scenario):
    scenario["safety"].activate_v1(**scenario["common"])
    original = scenario["observation"]
    scenario["observation"] = replace(
        original, candles_payload={**original.candles_payload, "instId": "FOREIGN"}
    )
    with pytest.raises(OfflinePublicFeedRecoveryError, match="ORIGINAL_OBSERVATION_MISMATCH"):
        _resume(scenario)
    assert kill_switch_should_block_trading(explicit_active=False)
    assert scenario["cursor_path"].read_bytes() == scenario["initial_cursor"]


@pytest.mark.parametrize("fault", ["signature", "expired", "foreign-scope"])
def test_unproven_authority_stays_killed_without_account_access(scenario, fault):
    common = scenario["common"].copy()
    body = common["mandate"]["body"]
    if fault == "signature":
        common["mandate"] = {**common["mandate"], "signature": "0" * 64}
    elif fault == "expired":
        common["mandate"] = _signed(
            {**body, "expires_at": (scenario["feed"].now - timedelta(seconds=1)).isoformat()}
        )
    else:
        common["mandate"] = _signed({**body, "account": "foreign-account"})
    with pytest.raises(OfflinePublicFeedRecoveryError):
        scenario["safety"].activate_v1(**common)
    assert scenario["venue"].requests == []
    assert scenario["cursor_path"].read_bytes() == scenario["initial_cursor"]
    assert kill_switch_should_block_trading(explicit_active=False)


def test_new_kill_before_release_invalidates_old_revision(scenario, monkeypatch):
    from src.ops import offline_public_feed_restart_v1 as module

    capture = module.capture_offline_feed_account_reconciliation_v1

    def capture_then_kill(*args, **kwargs):
        evidence = capture(*args, **kwargs)
        scenario["safety"].record_kill_v1(reason="NEW_EMERGENCY")
        return evidence

    monkeypatch.setattr(module, "capture_offline_feed_account_reconciliation_v1", capture_then_kill)
    with pytest.raises(OfflinePublicFeedRecoveryError, match="STOP_CHANGED_OR_UNPROVEN"):
        scenario["safety"].activate_v1(**scenario["common"])
    assert scenario["feed"].store.load()["trigger_reason"] == "NEW_EMERGENCY"
    assert kill_switch_should_block_trading(explicit_active=False)


def test_new_kill_after_release_blocks_the_actual_host(scenario):
    safety = scenario["safety"]
    safety.activate_v1(**scenario["common"])
    safety.record_kill_v1(reason="NEW_EMERGENCY")
    with pytest.raises(OfflinePublicFeedRecoveryError, match="ACTIVE_UNPROVEN"):
        _resume(scenario)
    assert scenario["cursor_path"].read_bytes() == scenario["initial_cursor"]
    assert kill_switch_should_block_trading(explicit_active=False)


def test_cold_host_reads_release_and_continues_without_reopening_budget_writer(scenario):
    safety, common = scenario["safety"], scenario["common"]
    safety.activate_v1(**common)
    prior = common["host"]
    prior.close()
    host = PortfolioBudgetHostV1(
        root=prior.root,
        private_rest_fetch=None,
        repository_sha=prior.repository_sha,
        session_id=prior.session_id,
        expected_account_identity=prior.expected_account_identity,
        clock=prior.clock,
        execution_environment=prior.execution_environment,
    )
    try:
        cold = OfflinePublicFeedRestartV1(scenario["feed"].cold_reader(), authority_key=KEY)
        result = cold.resume_v1(
            **{**common, "host": host},
            observation=scenario["observation"],
            g17_producers=scenario["producers"],
        )
        assert result["cursor_after"] == result["cursor_before"] + 60
        assert host.owner is None
    finally:
        host.close()


def test_unscoped_active_file_cannot_admit_the_original_host(scenario):
    safety, common = scenario["safety"], scenario["common"]
    store = scenario["feed"].store
    store.save(KillSwitchState.ACTIVE)
    with pytest.raises(OfflinePublicFeedRecoveryError, match="AUTHORITY_INVALID"):
        _resume(scenario)
    assert scenario["cursor_path"].read_bytes() == scenario["initial_cursor"]


def test_crash_before_atomic_release_keeps_original_stop(scenario, monkeypatch):
    from src.ops import offline_public_feed_restart_v1 as module

    write = module.atomic_write_json

    def interrupted(*, path, payload):
        if payload.get("state") == "ACTIVE":
            raise OSError("interrupted before atomic publication")
        write(path=path, payload=payload)

    monkeypatch.setattr(module, "atomic_write_json", interrupted)
    with pytest.raises(OSError, match="interrupted before atomic publication"):
        scenario["safety"].activate_v1(**scenario["common"])
    assert scenario["feed"].incident.state_path.read_bytes() == scenario["feed"].initial_state
    assert kill_switch_should_block_trading(explicit_active=False)
