"""Offline bounds and actual Mac-to-V2 dispatch with zero runtime ports."""

from contextlib import closing
from dataclasses import asdict, replace
import json
import plistlib
from types import SimpleNamespace

import pytest

from src.ops import n1_mac_host_service_v2 as service
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    current_productive_cursor_digest_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1 import (
    StandingSupervisorConfigV1,
    budget_owner_root_for_config_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.unattended_v1 import (
    UnattendedHostBoundsV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import DurableBudgetStoreV1
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1 import (
    _bound,
)


SHA = "a" * 40
DIGEST = "b" * 64
RESERVATION = "c" * 64
EPISODE = "d" * 64
ACCOUNT = "offline-account"


def _forbidden(*_args, **_kwargs):
    pytest.fail("A blocked preflight must not open a port or dispatch the host")


@pytest.fixture
def manifest(tmp_path):
    value = {
        "schema": service.SCHEMA,
        "repository_root": str(service.REPO),
        "state_root": str(tmp_path / "host"),
        "bounds": asdict(UnattendedHostBoundsV1("fixture", SHA, DIGEST, 200, 1, 20, 1)),
        "runtime_request_config": {
            "repository_sha": SHA,
            "roots": {"lane_state_root": str(tmp_path / "lanes")},
            "authorization": {
                "max_cycles_per_run": 1,
                "max_run_duration_seconds": 20,
                "wait_interval_seconds": 1,
            },
        },
        "checkpoint": asdict(service.OccupiedCheckpoint(RESERVATION, EPISODE, 1, DIGEST, DIGEST)),
        "filegate": {"path": str(tmp_path / "filegate.json"), "revision": DIGEST},
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(value))
    return path


def test_prepare_plist_is_parked_and_routes_to_v2(manifest, tmp_path):
    plist = tmp_path / "de.peaktrade.n1-host.v2.plist"
    result = service.mac_host_service_v2(
        action="prepare", manifest_path=manifest, output_path=plist
    )
    assert result["ok"] and result["service_activated"] is False
    args = plistlib.loads(plist.read_bytes())
    assert args["Label"] == service.LABEL
    assert args["ProgramArguments"][1:] == [
        "-m",
        "src.ops.n1_mac_host_service_v2",
        "run",
        "--manifest",
        str(manifest),
    ]
    assert args["RunAtLoad"] is False and args["KeepAlive"] is False
    assert not (tmp_path / "host").exists()


def test_accepted_dispatch_reaches_actual_v2_filegate(manifest, monkeypatch, tmp_path):
    # Drive only the entry dispatch. The real V2 controller observes an
    # unavailable Filegate and never asks the original factory for ports.
    monkeypatch.setattr(service, "preflight_mac_host_v2", lambda *a, **kw: {"ok": True})
    monkeypatch.setattr(service.startup_factory_v1, "prepare_occupied_n1_request_v1", _forbidden)
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(tmp_path / "filegate.json"))
    result = service.mac_host_service_v2(action="run", manifest_path=manifest, clock=lambda: 100)
    assert result["host_state"]["status"] == "FILEGATE_BLOCKED"
    assert result["host_state"]["cycles_used"] == 0
    assert (tmp_path / "host/occupied_host_state_v2.json").is_file()


def test_blocked_preflight_reports_independent_reasons(manifest, monkeypatch, tmp_path):
    monkeypatch.setattr(service, "run_occupied_n1_net_reversal_host_v2", _forbidden)
    monkeypatch.setattr(
        service,
        "validate_bounded_continuous_run_owner_go_decision_v1",
        lambda **kw: (False, ("BASELINE_LINEAGE_IMMUTABLE_SURFACE_DRIFT",)),
    )
    ledgers = SimpleNamespace(
        status="REJECTED",
        blocking_reasons=("RUNTIME_APPLIED_SEAM_UNAVAILABLE",),
        to_dict=lambda: {},
    )
    monkeypatch.setattr(
        service,
        "run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1",
        lambda *_: ledgers,
    )
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(tmp_path / "filegate.json"))
    result = service.mac_host_service_v2(action="run", manifest_path=manifest, clock=lambda: 300)
    assert not result["ok"]
    assert set(result["blockers"]) == {"runtime_window", "owner_go", "filegate", "f1_m9", "request"}
    assert not (tmp_path / "host").exists()


def test_cap24_rejects_fresh_publication_for_foreign_instrument(monkeypatch):
    bound = _bound(lane_id=service.LANE)
    foreign = SimpleNamespace(
        selection=SimpleNamespace(
            venue_native_id="FOREIGN-USDT-SWAP",
            instrument_id=bound.instrument_id,
            selection_id=bound.selection_id,
            integrity_digest=bound.selection_integrity_digest,
        ),
        ranking=SimpleNamespace(
            ranking_snapshot_id=bound.ranking_snapshot_id,
            integrity_digest=bound.ranking_integrity_digest,
        ),
        universe=SimpleNamespace(snapshot_id=bound.universe_snapshot_id),
    )
    monkeypatch.setattr(service, "inspect_selection_v1", lambda **_: foreign)
    with pytest.raises(ValueError, match="N1_MAC_V2_CAP24_BINDING_MISMATCH"):
        service._require_cap24(SimpleNamespace(cap24_productivity_root=None), bound, SHA, now=100)


@pytest.mark.parametrize(
    "fault,reason",
    [
        ("store", "DURABLE_BUDGET_REVISION_UNPROVEN"),
        ("account", "DURABLE_BUDGET_IDENTITY_MISMATCH"),
        ("hold", "N1_MAC_V2_STORE_HOLD_BINDING_MISMATCH"),
        ("instrument", "N1_MAC_V2_STORE_HOLD_BINDING_MISMATCH"),
        ("offline_v2", "N1_MAC_V2_ORIGINAL_LIVE_STORE_REQUIRED"),
        ("cursor", "N1_MAC_V2_CURSOR_DIGEST_MISMATCH"),
    ],
)
def test_checkpoint_refuses_foreign_or_offline_state(tmp_path, monkeypatch, fault, reason):
    bound = _bound(lane_id=service.LANE)
    config = StandingSupervisorConfigV1(
        public_store_root=tmp_path / "public",
        private_store_root=tmp_path / "private",
        lane_state_root=tmp_path / "lanes",
        evidence_root=tmp_path / "run",
        expected_account_identity=ACCOUNT,
    )
    owner_root = budget_owner_root_for_config_v1(config) / "owner"
    stored = {
        "schema": "portfolio_reservation_state.v1",
        "account_identity": ACCOUNT,
        "slot_capital_allocation": {"schema": "live_slot_capital_allocation.v1"},
        "reservations": [
            {
                "reservation_id": RESERVATION,
                "slot_id": service.LANE,
                "state": "RELEASED" if fault == "hold" else "COMMITTED",
                "binding": {"bound": bound.to_dict()},
            }
        ],
        "lane_bindings": {
            service.LANE: {
                "bound": (
                    replace(bound, venue_native_id="FOREIGN-USDT-SWAP")
                    if fault == "instrument"
                    else bound
                ).to_dict()
            }
        },
    }
    if fault == "offline_v2":
        stored["offline_v2_opening_fills"] = {"receipt": "simulated"}
    with closing(
        DurableBudgetStoreV1(owner_root, account_identity=ACCOUNT, mode="create")
    ) as owner:
        owner.save(stored)
        head = owner.head
    checkpoint = service.OccupiedCheckpoint(
        RESERVATION,
        EPISODE,
        1,
        DIGEST if fault == "store" else head,
        current_productive_cursor_digest_v1({"foreign": "cursor"}),
    )
    if fault == "account":
        config = replace(config, expected_account_identity="foreign-account")
    monkeypatch.setattr(service, "find_authenticated_entry_sources_v1", _forbidden)
    with pytest.raises(ValueError, match=reason):
        service._require_checkpoint(config, bound, tmp_path / "proof", checkpoint)


@pytest.mark.parametrize("matches_retained_order", [True, False])
def test_checkpoint_recovers_booking_before_successor_cursor(
    tmp_path, monkeypatch, matches_retained_order
):
    bound = _bound(lane_id=service.LANE)
    config = StandingSupervisorConfigV1(
        public_store_root=tmp_path / "public",
        private_store_root=tmp_path / "private",
        lane_state_root=tmp_path / "lanes",
        evidence_root=tmp_path / "run",
        expected_account_identity=ACCOUNT,
    )
    booking = {
        "reservation_id": RESERVATION,
        "account": ACCOUNT,
        "slot_id": service.LANE,
        "instrument_id": bound.instrument_id,
        "native_id": bound.venue_native_id,
        "selection_digest": bound.selection_integrity_digest,
        "previous_episode_id": EPISODE,
        "envelope_digest": "f" * 64,
    }
    state = {
        "slot_capital_allocation": {"schema": "live_slot_capital_allocation.v1"},
        "reservations": [
            {
                "reservation_id": RESERVATION,
                "slot_id": service.LANE,
                "state": "COMMITTED",
                "binding": {"bound": bound.to_dict()},
            }
        ],
        "lane_bindings": {service.LANE: {"bound": bound.to_dict()}},
        "live_net_reversal_bookings": {RESERVATION: [booking]},
    }
    monkeypatch.setattr(
        service, "read_budget_revision_read_only_v1", lambda *a, **kw: {"state": state}
    )
    monkeypatch.setattr(service, "require_budget_head_read_only_v1", lambda *a, **kw: DIGEST)
    raw = {"cursor": "original"}
    monkeypatch.setattr(
        service, "load_current_productive_sidestate_confirmation_cursor_v1", lambda _: raw
    )
    monkeypatch.setattr(
        service,
        "parse_current_productive_sidestate_confirmation_cursor_v1",
        lambda _: SimpleNamespace(
            instrument_id=bound.instrument_id,
            venue_native_id=bound.venue_native_id,
            trading_epoch=503,
        ),
    )
    monkeypatch.setattr(
        service,
        "read_occupied_scope_mark_snapshot_v1",
        lambda _: {
            "mark": {"position_episode_id": EPISODE, "pending_reversal_episode_id": EPISODE}
        },
    )
    monkeypatch.setattr(
        service,
        "_read_retained_net_reversal_v1",
        lambda *_: (
            SimpleNamespace(old_reservation_id=RESERVATION),
            SimpleNamespace(
                envelope_digest=booking["envelope_digest"] if matches_retained_order else DIGEST
            ),
        ),
    )
    verified = []
    monkeypatch.setattr(
        service,
        "require_booked_net_reversal_readback_v1",
        lambda **kw: verified.append(kw["booking"]),
    )
    checkpoint = service.OccupiedCheckpoint(
        RESERVATION,
        EPISODE,
        1,
        DIGEST,
        current_productive_cursor_digest_v1(raw),
    )
    if matches_retained_order:
        assert service._require_checkpoint(config, bound, tmp_path / "proof", checkpoint) == 503
        assert verified == [booking]
    else:
        with pytest.raises(ValueError, match="N1_MAC_V2_BOOKED_EPISODE_MISMATCH"):
            service._require_checkpoint(config, bound, tmp_path / "proof", checkpoint)
        assert not verified
