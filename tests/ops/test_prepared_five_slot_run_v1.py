"""Offline joins: signed Demo fixture -> original DDO -> GVEF, and fixed sequencing."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from threading import local

import pytest

from scripts.ops import prepared_five_slot_run_v1 as five
from scripts.ops import run_btc_demo_learning_session_v1 as learning
from src.experiments.canonical_experiment_identity_v1 import CanonicalCodeProvenanceV1
from src.experiments.canonical_research_prepared_execution_v1 import digest_v1, read_v1
from tests.learning.test_offline_ddo_research_cycle_v1 import native_research_fixture
from tests.ops.test_btc_demo_bounded_host_v1 import (
    runtime_case as runtime_case,
    demo_entry as demo_entry,
    no_network as no_network,
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
)


def research_draft(root, config):
    instrument = config["fixed_pin"]["canonical_instrument_id"]
    bars, cfg, request = native_research_fixture(instrument, "c" * 64)
    root.mkdir()
    csv, settings, template = (
        root / name for name in ("bars.csv", "backtest.json", "descriptor.json")
    )
    bars.to_csv(csv)
    settings.write_text(json.dumps(cfg))
    profile = request.model_dump(mode="json", exclude={"learning_evidence_digest", "times"})
    profile.update(
        schema_version="offline_ddo_research_profile.v1",
        observed_surface="TESTNET",
        gap_dimensions=[],
    )
    template.write_text(
        json.dumps(
            dict(
                schema_version="offline_research_input.v1",
                instrument_id=instrument,
                bars_csv_sha256=sha256(csv.read_bytes()).hexdigest(),
                backtest_json_sha256=sha256(settings.read_bytes()).hexdigest(),
                profile=profile,
            )
        )
    )
    return dict(
        state=str(root / "gvef"),
        paper_runs=str(root / "paper"),
        shadow_runs=str(root / "shadow"),
        shadow_follow_ups=str(root / "follow"),
        testnet_root=config["testnet_root"],
        testnet_source="BOUNDED_HOST_ENTRY",
        research_inputs={
            instrument: [dict(template=str(template), bars=str(csv), config=str(settings))]
        },
        jobs_per_tick=1,
        history_jobs=4,
        retry_seconds=1,
        slot=dict(
            lane_id="LANE_3",
            surface="TESTNET",
            session_id=config["session_id"],
            instrument_id=instrument,
            venue_native_id=config["fixed_pin"]["native_instrument_id"],
            starts_at=None,
            ends_at=None,
        ),
    )


@pytest.mark.parametrize("net_switches", [0, 2])
def test_bounded_host_automatically_reaches_original_ddo_and_gvef(
    runtime_case, tmp_path, net_switches
):
    runtime, start, venue = runtime_case
    draft = research_draft(tmp_path / "research", runtime.config)

    def pause(seconds):
        if venue.net_count >= net_switches and venue.post_count and runtime.portfolio is not None:
            venue.clock = venue.start + 3600
        else:
            venue.clock += seconds
            if venue.position is None:
                venue.mark += venue.direction * 600
            elif net_switches:
                from decimal import Decimal
                from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
                    restore_layered_core_episode_v1,
                )

                core = restore_layered_core_episode_v1(
                    runtime.cursor, expected_instrument_id=runtime.bound.instrument_id
                )
                venue.mark = Decimal(str(core.running_reference.reference_price_r_t)) - (
                    1 if Decimal(venue.position["pos"]) > 0 else -1
                ) * Decimal(str(core.scope.d_t)) * Decimal("1.5")

    result = learning.run_session_v1(
        runtime.config,
        draft,
        start,
        runtime=runtime,
        code=CanonicalCodeProvenanceV1(runtime.config["repository_sha"], "CLEAN"),
        clock=lambda: venue.clock,
        pause=pause,
    )
    assert result["host"]["status"] == "CONFIRMED_CLOSED", result
    assert venue.net_count == net_switches
    tail = result["learning"]
    assert tail["status"] == "PROCESSED", tail
    assert tail["original_first_fill_count"] == 1
    assert tail["research"]["jobs"][0]["status"] == "MECHANISM_PASS"
    completed = list((Path(draft["state"]) / "completed").glob("*.json"))
    assert len(completed) == 1
    digest = read_v1(completed[0])["learning_digest"]
    research = read_v1(Path(draft["state"]) / "offline-ddo-research" / digest / "result.json")
    assert research["evaluation"]["economic_status"] == "BLOCKED"
    assert tail["campaign"]["slot"]["starts_at"] == runtime.registration.started_at_utc.replace(
        "+00:00", "Z"
    )
    assert datetime.fromisoformat(tail["campaign"]["slot"]["ends_at"]) - datetime.fromisoformat(
        tail["campaign"]["slot"]["starts_at"]
    ) == timedelta(hours=1)
    lane = runtime.root / "testnet-state/LANE_3"
    before = {
        str(p): p.read_bytes()
        for name in ("ddo", "research-first-fills")
        for p in (lane / name).rglob("*")
        if p.is_file()
    }
    again = learning.finish_btc_learning_v1(
        runtime.config,
        draft,
        runtime.registration,
        code=CanonicalCodeProvenanceV1(runtime.config["repository_sha"], "CLEAN"),
    )
    assert again["status"] == "PROCESSED" and again["research"]["jobs"] == []
    assert all(Path(p).read_bytes() == body for p, body in before.items())
    from scripts.ops.btc_demo_bounded_learning_source_v1 import (
        read_bounded_btc_entry_measurement_v1,
    )

    original = runtime.root / "original-entry-g17-c1.json"
    body = original.read_bytes()
    changed = json.loads(body)
    changed["record_digest"] = "0" * 64
    original.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="ORIGINAL_PACKET_CHANGED"):
        read_bounded_btc_entry_measurement_v1(runtime.root)
    original.write_bytes(body)


def test_btc_campaign_refuses_other_session_root_instrument_and_dated_draft(runtime_case, tmp_path):
    runtime, _, venue = runtime_case
    draft = research_draft(tmp_path / "research", runtime.config)
    for field, value in (
        ("session_id", "foreign"),
        ("venue_native_id", "ETH-USDT-SWAP"),
        ("starts_at", "2026-11-24T00:00:00Z"),
    ):
        other = deepcopy(draft)
        other["slot"][field] = value
        with pytest.raises(ValueError, match="ORIGINAL_SESSION_REQUIRED"):
            learning.campaign_for_host_v1(runtime.config, other, started_at=venue.now())
    with pytest.raises(ValueError, match="ORIGINAL_SESSION_REQUIRED"):
        learning.campaign_for_host_v1(
            runtime.config,
            {**draft, "testnet_root": str(tmp_path / "other")},
            started_at=venue.now(),
        )
    assert not runtime.root.exists() and not venue.calls


def test_default_btc_learning_cli_is_offline(runtime_case, tmp_path, monkeypatch, capsys):
    runtime, _, _ = runtime_case
    draft = research_draft(tmp_path / "research", runtime.config)
    config_path, draft_path = tmp_path / "config.json", tmp_path / "draft.json"
    config_path.write_text(json.dumps(runtime.config))
    draft_path.write_text(json.dumps(draft))
    monkeypatch.setattr(
        learning, "macos_demo_signer_v1", lambda *_: pytest.fail("no signer during prepare")
    )
    monkeypatch.setattr(
        learning, "BtcDemoRuntimeV1", lambda **_: pytest.fail("no runtime during prepare")
    )
    assert learning.main(["--config", str(config_path), "--campaign-draft", str(draft_path)]) == 0
    assert json.loads(capsys.readouterr().out)["session_started"] is False
    assert not runtime.root.exists()


def test_later_five_slot_bundle_dispatches_offsets_without_waiting_for_other_tails(monkeypatch):
    code = CanonicalCodeProvenanceV1("a" * 40, "CLEAN")
    monkeypatch.setattr(five, "inspect_code_provenance_v1", lambda _: code)
    plan = dict(
        repository_sha=code.git_sha,
        input_sha256={},
        slots=[
            dict(
                number=n,
                lane_id=f"LANE_{n}",
                native_id=native,
                surface=surface,
                offset_seconds=offset * 60,
                duration_seconds=minutes * 60,
                producer=dict(module=five.MODULES[surface]),
            )
            for n, native, surface, offset, minutes in five.SLOTS
        ],
    )
    plan["plan_digest"] = digest_v1(plan)
    origin = datetime(2026, 11, 24, tzinfo=timezone.utc)
    bundle = dict(
        action="START_PREPARED_FIVE_SLOT_RUN",
        plan_digest=plan["plan_digest"],
        t0=origin.isoformat(),
        expires_at_utc=(origin + timedelta(minutes=1)).isoformat(),
        admission_wait_until_utc=(origin + timedelta(hours=4)).isoformat(),
    )
    state = local()
    calls = []

    def clock():
        return getattr(state, "now", origin.timestamp())

    def pause(seconds):
        state.now = clock() + seconds

    def run_slot(plan, slot, *, wait_until):
        calls.append((slot["lane_id"], clock() - origin.timestamp()))
        return dict(lane_id=slot["lane_id"], status="OFFLINE_DISPATCH_FIXTURE")

    result = five.run_five_slots_v1(plan, bundle, clock=clock, pause=pause, run_slot=run_slot)
    assert sorted(calls) == [(f"LANE_{n}", offset * 60) for n, _, _, offset, _ in five.SLOTS]
    assert len(result["slots"]) == 5
    with pytest.raises(ValueError, match="EXPLICIT_BOUND_START_REQUIRED"):
        five.run_five_slots_v1(plan, {**bundle, "plan_digest": "0" * 64}, clock=clock)
    with pytest.raises(ValueError, match="FRESH_START_WINDOW_REQUIRED"):
        five.run_five_slots_v1(plan, {**bundle, "t0": "2026-11-23T00:00:00Z"}, clock=clock)


def test_expired_entry_wait_never_invokes_producer(tmp_path):
    slot = dict(entry_input=str(tmp_path / "missing.json"), lane_id="LANE_4")
    result = five.run_slot_v1(
        {},
        slot,
        wait_until=0,
        clock=lambda: 1,
        execute=lambda *_: pytest.fail("no producer before valid original entry"),
    )
    assert result["status"] == "ENTRY_NOT_ADMITTED"


def test_cross_revision_admission_keeps_historical_occupancy_and_replays_policy(
    tmp_path, monkeypatch
):
    from src.ops import ranked_slot_run_source_v1 as source
    from src.ops.current_mf_member_to_pinned_cap23_n1_adapter_v1.adapter_v1 import (
        build_governed_cap23_pin_v1,
    )
    from src.ops.single_selected_future_policy_v1.producer_v1 import (
        run_single_selected_future_policy_v1,
    )
    from src.ops.single_selected_future_policy_v1.persistence_v1 import (
        load_and_validate_selection_v1,
    )
    from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
        load_and_validate_ranking_snapshot_v1,
    )
    from tests.ops import test_single_selected_future_runtime_binding_v1 as chain

    oldroot, newroot = tmp_path / "old", tmp_path / "new"
    oldroot.mkdir()
    newroot.mkdir()
    old = chain._build_chain(oldroot)
    prior = old["selection"]
    monkeypatch.setattr(chain, "REPO_SHA", "b" * 40)
    monkeypatch.setattr(chain, "SOURCE_EVENT", str(int(chain.SOURCE_EVENT) + 60000))
    monkeypatch.setattr(chain, "OBSERVED_UNIX", chain.OBSERVED_UNIX + 60)
    new = chain._build_chain(newroot)
    rank = load_and_validate_ranking_snapshot_v1(new["ranking_root"]).snapshot
    session = "new-session"
    root = newroot / session / "LANE_1"
    pin = build_governed_cap23_pin_v1(
        canonical_instrument_id=prior.instrument_id,
        ranking_snapshot=rank.to_dict(),
        lane_state_root=root,
    )
    result = run_single_selected_future_policy_v1(
        state_root=root,
        ranking_state_root=new["ranking_root"],
        repository_sha=chain.REPO_SHA,
        producer_observed_at_unix=chain.OBSERVED_UNIX,
        session_id=session,
        previous_selection=prior.to_dict(),
        load_previous_from_state=False,
        governed_pin=pin,
    )
    assert result["ok"], result
    selected = load_and_validate_selection_v1(root).selection
    assert selected.previous_selection_id == prior.selection_id
    assert selected.selected_at_event_time == prior.selected_at_event_time
    assert selected.config_digest != prior.config_digest  # revision is part of this digest
    assert rank.event_time > prior.ranking_event_time
    original = source.RankedRunSlotV1("LANE_1", prior, None, "old-universe", "original-transition")
    admission = dict(
        occupancy=original.reference(),
        selection_root=str(root),
        ranking_root=str(new["ranking_root"]),
        universe_root=str(new["universe_root"]),
        selection_digest=selected.integrity_digest,
        repository_sha=chain.REPO_SHA,
        original_repository_sha=prior.repository_sha,
    )
    cfg = dict(surface="SHADOW", session_id=session, shadow_entry_admission=admission)
    current = source.read_shadow_entry_admission_v1(cfg, original)
    assert current.selection.repository_sha != original.selection.repository_sha
    assert current.selection.previous_selection_id == prior.selection_id
    assert current.selection.selected_at_event_time == prior.selected_at_event_time
    for field, value in (
        ("original_repository_sha", "c" * 40),
        ("repository_sha", "d" * 40),
        ("selection_digest", "e" * 64),
    ):
        with pytest.raises(ValueError):
            source.read_shadow_entry_admission_v1(
                {**cfg, "shadow_entry_admission": {**admission, field: value}}, original
            )
    assert original.selection == prior


@pytest.mark.parametrize("number", [1, 2, 4, 5])
def test_common_driver_passes_same_session_originals_and_actual_paper_window(
    tmp_path, monkeypatch, number
):
    from types import SimpleNamespace

    native, surface, minutes = next(
        (native, surface, minutes) for n, native, surface, _, minutes in five.SLOTS if n == number
    )
    session = f"session_lane_{number}"
    state = tmp_path / session
    state.mkdir()
    paper, shadow, follow = (state / k for k in ("paper", "shadow", "follow"))
    archive = paper / session
    original = SimpleNamespace(selection=SimpleNamespace(integrity_digest="a" * 64))
    args = (
        {
            "--run-root": str(archive),
            "--slot-config": str(state / "fresh.json"),
            "--duration-seconds": minutes * 60,
        }
        if surface == "PAPER_EXCHANGE"
        else {
            "--companion-root": str(follow / session),
            "--gvef-campaign": str(state / "campaign.json"),
            "--ranked-slot-config": str(state / "fresh.json"),
        }
    )
    monkeypatch.setattr(five, "admit_entry_v1", lambda *_, **__: (args, original))
    entry = state / "entry.json"
    entry.write_text("{}")
    start = datetime(2026, 11, 24, tzinfo=timezone.utc)
    draft = dict(
        state=str(state / "gvef"),
        paper_runs=str(paper),
        shadow_runs=str(shadow),
        shadow_follow_ups=str(follow),
        jobs_per_tick=1,
        history_jobs=4,
        retry_seconds=1,
        research_inputs={native: []},
        slot=dict(
            lane_id=f"LANE_{number}",
            surface=surface,
            session_id=session,
            instrument_id=native,
            venue_native_id=native,
            starts_at=None,
            ends_at=None,
        ),
    )
    draft_path = state / "draft.json"
    draft_path.write_text(json.dumps(draft))
    slot = dict(
        lane_id=f"LANE_{number}",
        entry_input=str(entry),
        campaign_draft=str(draft_path),
        duration_seconds=minutes * 60,
        surface=surface,
        producer=dict(module=five.MODULES[surface], mode="run"),
    )
    calls = []

    def execute(argv, output):
        assert argv[:4] == [str(five.REPO / "scripts/pt"), "-m", five.MODULES[surface], "run"]
        assert str(state / "fresh.json") in argv
        if surface == "PAPER_EXCHANGE":
            archive.mkdir(parents=True)
            (archive / "window.json").write_text(
                json.dumps(dict(started_at=start.timestamp() + 7, duration_seconds=minutes * 60))
            )
        else:
            campaign = five.read(Path(args["--gvef-campaign"]))
            assert campaign["slot"]["session_id"] == session
            close = follow / session / "gvef"
            close.mkdir(parents=True)
            (close / "closeout.json").write_text('{"jobs":[{"status":"BLOCKED"}]}')
        return 0

    def tick(campaign, **_):
        calls.append(campaign)
        assert campaign.slot.starts_at.timestamp() == start.timestamp() + 7
        assert campaign.slot.session_id == session and campaign.paper_runs / session == archive
        assert campaign.jobs_per_tick == 3
        return dict(jobs=[dict(status="BLOCKED")])

    monkeypatch.setattr(
        five, "closed_paper_episode_ids_v1", lambda p: ["original-a", "original-b", "original-c"]
    )
    monkeypatch.setattr(five, "tick_research_campaign_v1", tick)
    result = five.run_slot_v1(
        {}, slot, wait_until=start.timestamp() + 100, clock=start.timestamp, execute=execute
    )
    assert result["status"] == "FOLLOW_UP_OR_PRODUCER_OPEN"
    assert len(calls) == (1 if surface == "PAPER_EXCHANGE" else 0)


@pytest.mark.parametrize(
    "status,expected",
    [("COMPLETED", 0), ("ENTRY_NOT_ADMITTED", 2), ("FOLLOW_UP_OR_PRODUCER_OPEN", 2)],
)
def test_common_cli_keeps_incomplete_runs_nonzero(tmp_path, monkeypatch, capsys, status, expected):
    plan = tmp_path / "plan.json"
    start = tmp_path / "start.json"
    plan.write_text("{}")
    start.write_text("{}")
    monkeypatch.setattr(five, "run_five_slots_v1", lambda *args: dict(slots=[dict(status=status)]))
    assert five.main(["--plan", str(plan), "--run", "--start-bundle", str(start)]) == expected
    assert json.loads(capsys.readouterr().out)["slots"][0]["status"] == status


def test_changed_prepared_input_blocks_before_any_producer(tmp_path):
    path = tmp_path / "original.json"
    path.write_text("{}")
    plan = dict(input_sha256={str(path): sha256(path.read_bytes()).hexdigest()})
    path.write_text('{"changed":true}')
    with pytest.raises(ValueError, match="FIVE_SLOT_INPUT_CHANGED"):
        five.run_slot_v1(plan, {}, wait_until=0, execute=lambda *_: pytest.fail("no producer"))
