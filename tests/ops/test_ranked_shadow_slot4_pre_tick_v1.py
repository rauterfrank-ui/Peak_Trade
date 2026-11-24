"""Cold-read a terminated offline writer. The wallclock session entry point is never called."""

import json
import os
from decimal import Decimal
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from src.ops import ranked_shadow_slot4_successor_v1 as rotation
from src.ops.ranked_shadow_slot4_pre_tick_v1 import CHECKPOINT
from src.ops.ranked_slot_run_source_v1 import read_ranked_run_slot_v1
from tests.ops import test_single_selected_future_runtime_binding_v1 as sample
from tests.ops.test_ranked_shadow_slot4_successor_v1 import _fixed_shadow_sources

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def bound_profile(tmp_path_factory):
    root = tmp_path_factory.mktemp("slot4-generation")
    _, _, _, config = _fixed_shadow_sources(root / "sources")
    profile = root / "profile.json"
    profile.write_text(json.dumps(config("LANE_4")))
    return profile


@pytest.fixture(scope="module")
def budget_receipt(bound_profile):
    # Produce a valid analytical hold with the native sizing owner on a separate offline
    # fixture. The crash subjects consume that binding before receiving any mark.
    from tests.ops.test_ranked_shadow_first_purchase_v1 import exercise_ranked_entry

    config = json.loads(bound_profile.read_bytes())
    slot = read_ranked_run_slot_v1(config)
    inventory = dict(sample._perp("PIEVERSE-USDT-SWAP", base="PIEVERSE"), maxMktSz="100000")
    cycles, _, _ = exercise_ranked_entry(
        bound_profile.parent / "sizing",
        bound_profile,
        slot,
        inventory,
        short=False,
        start=sample.OBSERVED_UNIX,
        price=Decimal("2.00"),
    )
    purchases = [
        c["ranked_shadow_first_purchase"] for c in cycles if c.get("ranked_shadow_first_purchase")
    ]
    purchase = next((p for p in purchases if p["status"] == "FILLED"), None)
    assert purchase is not None, [p["reason_codes"] for p in purchases]
    path = bound_profile.parent / "hold.json"
    path.write_text(json.dumps({k: purchase[k] for k in ("entry", "budget", "sizing")}))
    return path


def _account(profile, root, *, stop_before_manifest=False):
    from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1 import (
        session_runtime_v1 as host,
    )

    config = json.loads(profile.read_bytes())
    slot = read_ranked_run_slot_v1(config)
    session = config["session_id"]
    owner = host.WallclockSessionRuntimeV1(
        evidence_root=root,
        transport=SimpleNamespace(
            opened=False,
            candidate_last=False,
            venue_instrument_id=slot.instrument.venue_native_inst_id,
        ),
        clock_wall=lambda: sample.OBSERVED_UNIX + 8,
    )
    owner.session_id, owner.consumed = session, True
    owner.writer.ensure_append_files()
    owner.writer.write_immutable_json(
        "authorization_consumption.json",
        dict(
            session_id=session,
            authorization_id="offline-test",
            mode="productive_wallclock_v2",
            productive_authorization=True,
            forced_wiring_fixture=False,
            consumed=True,
        ),
    )
    owner.writer.write_immutable_json(
        "authorization_consumption_record.json",
        dict(
            session_id=session,
            authorization_id="offline-test",
            expected_repository_sha=sample.REPO_SHA,
        ),
    )
    owner.writer.write_immutable_text("repo_sha.txt", sample.REPO_SHA)
    owner.lock = host.SessionLockV1(
        lock_path=root / "session.lock", session_id=session, owner=host.CAPABILITY_ID
    )
    owner.lock.acquire()
    owner._initialize_ranked_shadow_account(slot)
    if stop_before_manifest:
        os._exit(73)
    owner.writer.write_immutable_json(
        "session_manifest.json", dict(session_id=session, n5_assignment=slot.reference())
    )
    return owner, slot


def _crash_writer(profile, root, hold, cut):
    from src.ops.instrument_card_stream_v1 import bind_shadow_slot_entry_budget_v1
    from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import (
        ReservationSizingBindingV1,
    )

    owner, slot = _account(
        Path(profile), Path(root), stop_before_manifest=cut == "before_session_manifest"
    )
    checkpoint = owner.bridge_state.slot4_pre_tick_checkpoint
    if hold:
        fixture = json.loads(Path(hold).read_bytes())
        entry = fixture["entry"]
        if cut == "during_bind":
            checkpoint.finish = lambda event: os._exit(73)
        bound = SimpleNamespace(
            **{
                k: entry[k] for k in ("instrument_id", "selection_id", "selection_integrity_digest")
            },
            venue_native_id=entry["venue_native_id"],
        )
        bind_shadow_slot_entry_budget_v1(
            state=owner.bridge_state,
            bound=bound,
            budget=fixture["budget"],
            entry=entry,
            sizing=ReservationSizingBindingV1.from_dict_v1(fixture["sizing"]),
        )
    assert owner.sequence == owner.accepted_ticks == owner.bridge_state.cycle_index == 0
    if cut == "account":
        os._exit(73)
    if cut == "first_mark":
        checkpoint.first_mark()
        os._exit(73)
    owner._abort("INVARIANT_VIOLATION", "offline test")
    assert owner.killstate.active and (Path(root) / "killstate_events.jsonl").stat().st_size
    if cut == "kill":
        os._exit(73)
    if cut == "before_seal":

        def crash(**kwargs):
            assert (Path(root) / "slot4_shadow_closeout_v1.json").is_file()
            os._exit(73)

        owner.writer.finalize = crash
    result = owner._finalize_result(session_id=owner.session_id, incomplete=True, ranked_slot=slot)
    assert cut == "sealed" and result.terminal_verdict == "ABORT" and not result.network_opened


def _write_in_subprocess(profile, root, hold, cut):
    cmd = [
        str(REPO / "scripts/pt"),
        "-c",
        "import sys; from tests.ops.test_ranked_shadow_slot4_pre_tick_v1 import _crash_writer; _crash_writer(*sys.argv[1:])",
        str(profile),
        str(root),
        str(hold) if hold else "",
        cut,
    ]
    result = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=60)
    assert result.returncode == (0 if cut == "sealed" else 73), result.stderr


@pytest.mark.parametrize("hold", [False, True], ids=["empty", "open-hold"])
@pytest.mark.parametrize("cut", ["account", "kill", "before_seal", "sealed"])
def test_rotation_cold_read(tmp_path, bound_profile, budget_receipt, cut, hold):
    _write_in_subprocess(bound_profile, tmp_path, budget_receipt if hold else None, cut)
    with pytest.raises(rotation.Slot4ShadowRecoveryRequired) as denied:
        rotation.prepare_slot4_shadow_rotation_v1(
            bound_profile, tmp_path, clock=lambda: sample.OBSERVED_UNIX + 8
        )
    evidence = denied.value.evidence
    record = evidence["pre_tick_checkpoint"]
    assert (
        record["assignment"]
        == read_ranked_run_slot_v1(json.loads(bound_profile.read_bytes())).reference()
    )
    assert record["session_id"] == json.loads(bound_profile.read_bytes())["session_id"]
    assert record["phase"] == "OBSERVED"
    observed = record["last_observation"]
    assert observed["positions_native_contracts"] == []
    assert observed["pending_external_custody"] is False
    assert observed["pending_pre_external_custody"] is hold
    assert observed["confirmed_entry_budget"] == (
        json.loads(budget_receipt.read_bytes())["entry"] if hold else None
    )
    assert observed["killstate"]["active"] is (cut != "account")
    assert not (tmp_path / "market_data_sequence.jsonl").read_bytes()
    assert (tmp_path / "evidence_manifest.sha256").exists() is (cut == "sealed")
    if cut != "sealed":
        assert evidence["unproven_rotation_inputs"] == list(rotation.ROTATION_INPUTS)
    else:
        assert (
            evidence["abort_owner_observation"]["current_inputs"]["lane_health_allows_replacement"]
            is False
        )


@pytest.mark.parametrize(
    "cut,phase", [("during_bind", "CHANGE_PENDING"), ("first_mark", "FIRST_MARK")]
)
def test_prior_flat_is_only_historical(tmp_path, bound_profile, budget_receipt, cut, phase):
    _write_in_subprocess(bound_profile, tmp_path, budget_receipt, cut)
    with pytest.raises(rotation.Slot4ShadowRecoveryRequired) as denied:
        rotation.prepare_slot4_shadow_rotation_v1(bound_profile, tmp_path)
    record = denied.value.evidence["pre_tick_checkpoint"]
    assert record["phase"] == phase
    assert record["last_observation"]["pending_pre_external_custody"] is (cut == "first_mark")
    assert record["proposed_budget_binding"] == (
        json.loads(budget_receipt.read_bytes())["entry"] if cut == "during_bind" else None
    )
    assert denied.value.evidence["unproven_rotation_inputs"] == list(rotation.ROTATION_INPUTS)


def test_wrong_generation_and_corruption(tmp_path, bound_profile):
    from src.ops.ranked_shadow_slot4_pre_tick_v1 import read_slot4_pre_tick_checkpoint_v1
    from dataclasses import replace

    owner, slot = _account(bound_profile, tmp_path)
    for session, expected in [
        (owner.session_id, replace(slot, transition_id="foreign")),
        ("other", slot),
    ]:
        with pytest.raises(ValueError):
            read_slot4_pre_tick_checkpoint_v1(tmp_path, expected, session)
    path = tmp_path / CHECKPOINT
    data = json.loads(path.read_bytes())
    data["record"]["last_observation"]["killstate"]["active"] = True
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="CHECKPOINT_INTEGRITY"):
        rotation.prepare_slot4_shadow_rotation_v1(bound_profile, tmp_path)
    owner.lock.release()


def test_account_before_session_manifest(tmp_path, bound_profile):
    _write_in_subprocess(bound_profile, tmp_path, None, "before_session_manifest")
    assert not (tmp_path / "session_manifest.json").exists()
    with pytest.raises(rotation.Slot4ShadowRecoveryRequired) as recovery:
        rotation.prepare_slot4_shadow_rotation_v1(bound_profile, tmp_path)
    assert recovery.value.evidence["pre_tick_checkpoint"]["event"] == "ACCOUNT_INITIALIZED"


@pytest.mark.parametrize("name,cut", [("OL", "account"), ("CSOPSKHYNIX2L", "sealed")])
def test_other_slot4_generation(tmp_path, bound_profile, name, cut):
    _, _, _, config = _fixed_shadow_sources(tmp_path / "sources", slot4=name)
    profile = tmp_path / "profile.json"
    profile.write_text(json.dumps(config("LANE_4")))
    root = tmp_path / "evidence"
    root.mkdir()
    _write_in_subprocess(profile, root, None, cut)
    with pytest.raises(rotation.Slot4ShadowRecoveryRequired) as recovery:
        rotation.prepare_slot4_shadow_rotation_v1(profile, root)
    record = recovery.value.evidence["pre_tick_checkpoint"]
    assert record["assignment"]["venue_native_id"] == name + "-USDT-SWAP"
    assert record["last_observation"]["killstate"]["active"] is (cut == "sealed")
    # Same slot and session, different actual N5 generation.
    with pytest.raises(ValueError, match="MISMATCH"):
        rotation.prepare_slot4_shadow_rotation_v1(bound_profile, root)


def test_write_failure_preserves_original_kill_and_last_observation(
    tmp_path, bound_profile, monkeypatch
):
    from src.ops import ranked_shadow_slot4_pre_tick_v1 as checkpoint_module
    from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.wallclock_evidence_v1 import (
        WallclockEvidenceError,
    )

    owner, slot = _account(bound_profile, tmp_path)
    checkpoint = owner.bridge_state.slot4_pre_tick_checkpoint
    original = (tmp_path / CHECKPOINT).read_bytes()

    def fail_write(*args):
        raise OSError("offline injected disk error")

    monkeypatch.setattr(checkpoint_module, "durable_bytes_v1", fail_write)
    with pytest.raises(WallclockEvidenceError, match="WRITE_FAILED"):
        checkpoint.first_mark()
    assert owner.bridge_state.slot4_pre_tick_checkpoint is checkpoint and owner.sequence == 0
    owner._abort("EVIDENCE_SINK_FAILURE")
    assert owner.killstate.active and owner.killstate.last_trigger == "EVIDENCE_SINK_FAILURE"
    assert (tmp_path / "killstate_events.jsonl").stat().st_size
    assert (tmp_path / CHECKPOINT).read_bytes() == original
    with pytest.raises(rotation.Slot4ShadowRecoveryRequired) as recovery:
        rotation.prepare_slot4_shadow_rotation_v1(bound_profile, tmp_path)
    assert recovery.value.evidence["unproven_rotation_inputs"] == list(rotation.ROTATION_INPUTS)
    owner.lock.release()
