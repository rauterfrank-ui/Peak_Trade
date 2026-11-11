"""Bound R01/P01 repair under the original FILEGATE, with no wire connector."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from src.ops.gates.risk_gate import kill_switch_should_block_trading
from src.ops.offline_public_feed_recovery_v1 import (
    OfflinePublicFeedIncidentV1,
    OfflinePublicFeedRecoveryError,
    OfflinePublicFeedRecoveryV1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
    default_store_paths_v1,
    load_all_facts_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import InstrumentRefV1, fact_digest
from src.ops.peak_trade_public_market_data_runtime_v1.runtime_orchestrator_v1 import (
    PublicMarketDataRuntimeV1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.ws_channel_normalizers_v1 import (
    PublicWsNormalizeError,
)
from src.ops.peak_trade_public_market_data_runtime_v1.ws_transport_v1 import PublicWsTransportV1
from src.risk_layer.kill_switch.core import KillSwitch
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.state import KillSwitchState
from tests.ops.test_current_scope_public_mark_source_v1 import INSTRUMENT, push


class RecordingConnector:
    def __init__(self):
        self.calls = []

    def connect(self, url):
        self.calls.append(("connect", url))

    def subscribe(self, args):
        self.calls.append(("subscribe", args))

    def disconnect(self):
        self.calls.append(("disconnect", None))


class FeedFixture:
    def __init__(
        self, root, monkeypatch, *, instrument=None, session_id="p01-feed", started_at=None
    ):
        self.now = started_at or datetime(2026, 11, 11, 12, tzinfo=timezone.utc)
        instrument = instrument or InstrumentRefV1(**INSTRUMENT)
        incident = OfflinePublicFeedIncidentV1(root, session_id, instrument, "")
        self.frames = [
            push(native=instrument.venue_native_id, timestamp=self.event_ms(-35), markPx="100")
        ]
        self.delays = []
        self.connector = RecordingConnector()
        self.transport = PublicWsTransportV1.from_ratified_binding(
            connector=self.connector,
            message_source=self.receive,
            venue_native_id=instrument.venue_native_id,
        )
        self.transport.sleep = self.backoff
        self.transport.connect_and_subscribe()
        self.runtime = PublicMarketDataRuntimeV1(
            store_root=incident.fact_root,
            venue_native_id=instrument.venue_native_id,
            canonical_instrument_id=instrument.canonical_instrument_id,
            instrument_ref=instrument,
            ws_transport=self.transport,
        )
        self.runtime.run_observation_cycle(
            captured_at=self.now.isoformat(), session_id=incident.session_id
        )
        self.advance(30)
        monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(incident.state_path))
        monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
        self.store = StatePersistence(str(incident.state_path))
        self.switch = KillSwitch({}, persistence=self.store)
        assert self.switch.trigger(incident.reason)
        self.initial_state = incident.state_path.read_bytes()
        self.incident = replace(
            incident, filegate_sha256=hashlib.sha256(self.initial_state).hexdigest()
        )
        self.repair = self.cold_reader()

    def event_ms(self, seconds=0):
        return int((self.now + timedelta(seconds=seconds)).timestamp() * 1000)

    def advance(self, seconds):
        self.now += timedelta(seconds=seconds)

    def backoff(self, seconds):
        self.delays.append(seconds)
        self.advance(seconds)

    def receive(self):
        self.advance(0.25)
        return iter(self.frames)

    def cold_reader(self):
        return OfflinePublicFeedRecoveryV1(self.incident, clock=lambda: self.now)

    def run(self):
        return self.repair.repair_and_observe_v1(self.runtime)


@pytest.fixture
def feed(tmp_path, monkeypatch):
    root = tmp_path.resolve() / "profile"
    root.mkdir(mode=0o700)
    return FeedFixture(root, monkeypatch)


def test_repair_reads_fresh_native_snapshot_after_reconnect_and_cold_read(feed):
    initial_calls = list(feed.connector.calls)
    feed.frames = [push(timestamp=feed.event_ms(1), markPx="101.125", last="99999")]
    result = feed.run()
    assert result["stage"] == "MARK_VERIFIED"
    assert result["mark"]["mark_px"] == "101.125"
    assert result["mark"]["captured_at"] == feed.now.isoformat()
    assert feed.connector.calls == [*initial_calls, ("disconnect", None), *initial_calls]
    assert feed.transport.state.reconnect_count == len(feed.delays) == 1
    assert feed.delays[0] > 0
    assert result["previous_mark_ms"] < result["mark"]["event_ms"]
    assert (result["mark"]["event_ms"] - result["previous_mark_ms"]) > 60_000
    # A fresh mark snapshot is not a reconstruction of skipped trading cycles or PT1M bars.
    facts = load_all_facts_v1(default_store_paths_v1(feed.incident.fact_root))
    assert [fact["fact_kind"] for fact in facts] == ["MarkPriceFactV1", "MarkPriceFactV1"]
    assert result["mark"]["fact_sha256"] == fact_digest(facts[-1])
    assert feed.cold_reader().read_verified_repair_v1() == result
    assert feed.run() == result
    assert feed.transport.state.reconnect_count == 1
    assert feed.incident.state_path.read_bytes() == feed.initial_state
    assert kill_switch_should_block_trading(explicit_active=False)


def test_cold_read_in_fresh_process_needs_no_connector(feed):
    feed.frames = [push(timestamp=feed.event_ms(1), markPx="101")]
    result = feed.run()
    repo = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    if env.get("GITHUB_ACTIONS") == "true":
        # The CI matrix provisions its interpreter without a checkout-local venv.
        env.update(PT_RUNTIME_MODE="provisioned", PT_PROVISIONED_PYTHON=sys.executable)
    restarted = subprocess.run(
        [
            str(repo / "scripts/pt"),
            "-c",
            """
from datetime import datetime
from pathlib import Path
import json
import sys
from src.ops.offline_public_feed_recovery_v1 import (
    OfflinePublicFeedIncidentV1, OfflinePublicFeedRecoveryV1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import InstrumentRefV1

root, binding_json, evaluation_clock = sys.argv[1:]
binding = json.loads(binding_json)
incident = OfflinePublicFeedIncidentV1(
    Path(root), binding['session_id'], InstrumentRefV1(**binding['instrument']),
    binding['filegate_sha256'],
)
recovery = OfflinePublicFeedRecoveryV1(incident, clock=lambda: datetime.fromisoformat(evaluation_clock))
print(json.dumps(recovery.read_verified_repair_v1()))
""",
            str(feed.incident.root),
            json.dumps(feed.incident.binding()),
            feed.now.isoformat(),
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    assert json.loads(restarted.stdout.splitlines()[-1]) == result
    assert feed.incident.state_path.read_bytes() == feed.initial_state


def test_receipt_cannot_substitute_for_missing_original_facts(feed):
    feed.frames = [push(timestamp=feed.event_ms(1), markPx="101")]
    feed.run()
    default_store_paths_v1(feed.incident.fact_root).finalized_facts.unlink()
    with pytest.raises(OfflinePublicFeedRecoveryError, match="FRESH_BOUND_MARK_UNPROVEN"):
        feed.cold_reader().read_verified_repair_v1()


@pytest.mark.parametrize(
    "mode", ["heartbeat", "duplicate", "correction", "before_reconnect", "future"]
)
def test_nonadvancing_or_invalid_mark_leaves_repair_open(feed, mode):
    original = feed.frames[0]
    initial_event = original["data"][0]["ts"]
    feed.frames = {
        "heartbeat": [{"event": "subscribe", "arg": {"channel": "mark-price"}}],
        "duplicate": [original],
        "correction": [push(timestamp=initial_event, markPx="101")],
        "before_reconnect": [push(timestamp=feed.event_ms(-1), markPx="101")],
        "future": [push(timestamp=feed.event_ms(10), markPx="101")],
    }[mode]
    with pytest.raises(OfflinePublicFeedRecoveryError, match="FRESH_BOUND_MARK_UNPROVEN"):
        feed.run()
    with pytest.raises(OfflinePublicFeedRecoveryError, match="MARK_RECEIPT_MISSING"):
        feed.cold_reader().read_verified_repair_v1()
    with pytest.raises(OfflinePublicFeedRecoveryError, match="ATTEMPT_NOT_REPLAYABLE"):
        feed.cold_reader().repair_and_observe_v1(feed.runtime)
    feed.frames = [push(timestamp=feed.event_ms(), markPx="103")]
    if mode == "future":
        # The original sequence owner has advanced. Wait for an actual newer venue snapshot.
        feed.advance(11)
        feed.frames = [push(timestamp=feed.event_ms(), markPx="103")]
    assert feed.run()["mark"]["mark_px"] == "103"
    assert feed.transport.state.reconnect_count == 1
    assert kill_switch_should_block_trading(explicit_active=False)


def test_original_normalizer_rejects_wrong_instrument(feed):
    feed.frames = [push(native="SOL-USDT-SWAP", timestamp=feed.event_ms(1), markPx="101")]
    with pytest.raises(PublicWsNormalizeError, match="WS_INSTRUMENT_MISMATCH"):
        feed.run()
    with pytest.raises(OfflinePublicFeedRecoveryError, match="MARK_RECEIPT_MISSING"):
        feed.cold_reader().read_verified_repair_v1()


def test_freshness_checked_again_at_cold_read(feed):
    feed.frames = [push(timestamp=feed.event_ms(1), markPx="101")]
    feed.run()
    feed.advance(6)
    with pytest.raises(OfflinePublicFeedRecoveryError, match="FRESH_BOUND_MARK_UNPROVEN"):
        feed.cold_reader().read_verified_repair_v1()


def test_running_owner_refreshes_stale_mark_on_same_transport(feed):
    feed.frames = [push(timestamp=feed.event_ms(1), markPx="101")]
    first = feed.run()
    feed.advance(120)
    feed.frames = [
        push(
            native=feed.incident.instrument.venue_native_id, timestamp=feed.event_ms(), markPx="102"
        )
    ]
    second = feed.run()
    assert second["mark"]["event_ms"] > first["mark"]["event_ms"]
    assert second["mark"]["mark_px"] == "102"
    assert feed.cold_reader().read_verified_repair_v1() == second
    assert feed.transport.state.reconnect_count == 1
    assert kill_switch_should_block_trading(explicit_active=False)


def test_new_kill_during_final_receipt_write_invalidates_old_observation(feed, monkeypatch):
    from src.ops import offline_public_feed_recovery_v1 as module

    write = module.atomic_write_json

    def write_with_new_kill(*, path, payload):
        if payload["body"]["stage"] == "MARK_VERIFIED":
            feed.store.save(
                KillSwitchState.KILLED,
                killed_at=feed.now.replace(tzinfo=None),
                trigger_reason="NEW_SAFETY_INCIDENT",
            )
        write(path=path, payload=payload)

    monkeypatch.setattr(module, "atomic_write_json", write_with_new_kill)
    feed.frames = [push(timestamp=feed.event_ms(1), markPx="101")]
    with pytest.raises(OfflinePublicFeedRecoveryError, match="STOP_CHANGED_OR_UNPROVEN"):
        feed.run()
    with pytest.raises(OfflinePublicFeedRecoveryError, match="STOP_CHANGED_OR_UNPROVEN"):
        feed.cold_reader().read_verified_repair_v1()
    assert feed.store.load()["trigger_reason"] == "NEW_SAFETY_INCIDENT"
    assert kill_switch_should_block_trading(explicit_active=False)


def test_emergency_overlay_never_licenses_repair(feed, monkeypatch):
    monkeypatch.setenv("PEAK_KILL_SWITCH", "1")
    with pytest.raises(OfflinePublicFeedRecoveryError, match="STOP_CHANGED_OR_UNPROVEN"):
        feed.run()
    assert feed.transport.state.reconnect_count == 0


def test_foreign_feed_store_rejected_before_reconnect(feed):
    feed.runtime.store_root = feed.incident.root
    with pytest.raises(OfflinePublicFeedRecoveryError, match="ORIGINAL_SESSION_MISMATCH"):
        feed.run()
    assert feed.transport.state.reconnect_count == 0


def test_reserved_attempt_is_not_reissued_after_failed_reconnect(feed):
    feed.transport.max_reconnect = 0
    with pytest.raises(RuntimeError, match="RECONNECT_BUDGET_EXCEEDED"):
        feed.run()
    with pytest.raises(OfflinePublicFeedRecoveryError, match="ATTEMPT_NOT_REPLAYABLE"):
        feed.cold_reader().repair_and_observe_v1(feed.runtime)
    assert feed.transport.state.reconnect_count == 0
    assert kill_switch_should_block_trading(explicit_active=False)
