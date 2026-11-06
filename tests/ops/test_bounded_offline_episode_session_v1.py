"""Explicit session identity, restart bounds and actual occupied N1 composition."""

from dataclasses import replace
import json
from pathlib import Path

import pytest

from src.ops.bounded_peaktrade_system_composition_v1.manifest_v1 import (
    OfflineEpisodeLaneV1,
    OfflineEpisodeSessionManifestV1,
    load_offline_episode_session_manifest_v1,
    repository_source_digest_v1,
)
from src.ops.bounded_peaktrade_system_composition_v1 import session_v1 as sessions
from src.ops.hard_facts_system_closure_v1.instrument_sensitive_identity_v1 import (
    BoundInstrumentLaneIdentityV1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneSlotV1,
    lane_state_root_for,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    persist_current_productive_sidestate_confirmation_cursor_v1,
)
from tests.ops.test_simulated_accounting_entry_source_v1 import _history, _args
from tests.ops.test_position_episode_exit_continuity_v1 import _natural_entry, _bound
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    create_position_episode_from_simulated_accounting_v1,
)


def _manifest(context, source, cursor_root, bound, max_attempts=2):
    lane_identity = BoundInstrumentLaneIdentityV1.from_bound_instrument(
        lane_id="LANE_1", bound=bound
    )
    return OfflineEpisodeSessionManifestV1(
        session_id="offline-session-test",
        repository_sha=context.binding.repository_sha,
        origin_main_sha="b" * 40,
        implementation_source_digest=repository_source_digest_v1(),
        exit_policy_config_digest=context.binding.config_digest,
        account_scope=context.identity.account_scope,
        replay_start_unix=1700000000.0,
        replay_stop_unix=2100000000.0,
        max_attempts=max_attempts,
        lanes=(
            OfflineEpisodeLaneV1(
                identity=context.identity,
                bound_instrument_identity=lane_identity.bound_instrument_identity,
                instrument_epoch=lane_identity.instrument_epoch,
                source_path=str(source.resolve()),
                source_content_digest=json.loads(source.read_text())["content_digest"],
                exit_state_root=str(Path(context.binding.state_root).resolve()),
                cursor_state_root=str(cursor_root.resolve()),
            ),
        ),
    )


def _setup(tmp_path):
    tmp_path = tmp_path.resolve()
    bound = _bound()
    cursor_root = Path(
        lane_state_root_for(topology_state_root_base=tmp_path / "lanes", lane_id="LANE_1")
    )
    cursor = _natural_entry(cursor_root, 1)
    persist_current_productive_sidestate_confirmation_cursor_v1(cursor, store_root=cursor_root)
    identity, session, fills = _history()
    args = _args(tmp_path, identity)
    args["repository_sha"] = "a" * 40
    context = create_position_episode_from_simulated_accounting_v1(
        **args, session=session, fills=fills
    )
    source = next((tmp_path / "sources").glob("*.json"))
    manifest = _manifest(context, source, cursor_root, bound)
    slot = IsolatedLaneSlotV1(
        lane_id="LANE_1",
        occupancy="OCCUPIED",
        canonical_instrument_id=bound.instrument_id,
        lane_state_root=str(cursor_root),
        universe_snapshot_id=bound.universe_snapshot_id,
        ranking_snapshot_id=bound.ranking_snapshot_id,
        ranking_integrity_digest=bound.ranking_integrity_digest,
    )
    return manifest, {"LANE_1": (slot, bound)}


def _session(manifest, root, mode="create"):
    return sessions.BoundedOfflineEpisodeSessionV1(
        manifest=manifest, state_root=root.resolve(), mode=mode
    )


@pytest.mark.parametrize("direction", [1, -1])
def test_actual_n1_close_is_bound_to_session_and_restart_does_not_renew_attempts(
    tmp_path, monkeypatch, direction
):
    from tests.ops import test_simulated_accounting_entry_source_v1 as scenario
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
        invoke_join_v1 as consumer,
    )

    original_args = scenario._args

    def pinned_args(*args):
        value = original_args(*args)
        value["repository_sha"] = "a" * 40
        return value

    monkeypatch.setattr(scenario, "_args", pinned_args)

    def in_session(pairs, **kwargs):
        context = kwargs.pop("position_episode_bindings")["LANE_1"]
        kwargs.pop("position_episode_scope")
        kwargs["origin_main_sha"] = "b" * 40
        source = Path(context.entry_source_ref.split(":", 2)[2])
        manifest = _manifest(
            context, source, Path(pairs["LANE_1"][0].lane_state_root), pairs["LANE_1"][1], 1
        )
        root = tmp_path / "session"
        with _session(manifest, root) as opened:
            result = opened.run_occupied_cycle_v1(pairs, **kwargs)
            assert opened.state["attempts_used"] == 1 and opened.state["status"] == "READY"
        with _session(manifest, root, "recover") as reopened:
            assert reopened.state["attempts_used"] == 1
            with pytest.raises(ValueError, match="ATTEMPTS_EXHAUSTED"):
                reopened.run_occupied_cycle_v1(pairs, **{**kwargs, "cycle_id_prefix": "new-prefix"})
        with pytest.raises(ValueError, match="NOT_OPEN"):
            reopened.run_occupied_cycle_v1(pairs, **kwargs)
        return result

    monkeypatch.setattr(consumer, "invoke_occupied_lane_governed_cycle_n1_consumer_v1", in_session)
    scenario.test_accounting_source_reaches_actual_n1_remaining_position_close(
        tmp_path, monkeypatch, direction
    )


@pytest.mark.parametrize(
    "change", ["mode", "maxpos", "counter_bool", "root_alias", "scope", "digest"]
)
def test_invalid_manifest_rejects_before_session_store_creation(tmp_path, change):
    manifest, pairs = _setup(tmp_path)
    if change == "mode":
        manifest = replace(
            manifest, account_scope=replace(manifest.account_scope, execution_environment="LIVE")
        )
    elif change == "maxpos":
        manifest = replace(manifest, lanes=manifest.lanes * 2)
    elif change == "counter_bool":
        manifest = replace(manifest, max_attempts=True)
    elif change == "root_alias":
        manifest = replace(
            manifest,
            lanes=(
                replace(manifest.lanes[0], exit_state_root=manifest.lanes[0].cursor_state_root),
            ),
        )
    elif change == "scope":
        manifest = replace(
            manifest, account_scope=replace(manifest.account_scope, account_identity="another")
        )
    else:
        manifest = replace(manifest, implementation_source_digest="invalid")
    with pytest.raises(ValueError):
        with _session(manifest, tmp_path / "session"):
            pytest.fail("opened invalid manifest")
    assert not (tmp_path / "session").exists()


def test_overlapping_session_roots_cannot_hold_same_owner_lease(tmp_path):
    manifest, pairs = _setup(tmp_path)
    with _session(manifest, tmp_path / "first"):
        with pytest.raises(ValueError, match="LEASE_CONFLICT"):
            with _session(replace(manifest, session_id="second"), tmp_path / "second"):
                pytest.fail("acquired aliased owners")
    # Release is explicit and idempotent; the original receipt still recovers.
    with _session(manifest, tmp_path / "first", "recover") as opened:
        assert opened.state["attempts_used"] == 0


@pytest.mark.parametrize("same_session_id", [True, False])
def test_new_session_root_cannot_renew_budget_against_already_registered_owner_roots(
    tmp_path, same_session_id
):
    manifest, pairs = _setup(tmp_path)
    with _session(manifest, tmp_path / "first"):
        pass
    other = manifest if same_session_id else replace(manifest, session_id="another-session")
    with pytest.raises(ValueError, match="RESOURCE_ALREADY_REGISTERED"):
        with _session(other, tmp_path / "second"):
            pytest.fail("silently rebound registered owners")
    with _session(manifest, tmp_path / "first", "recover"):
        pass


def test_interrupted_attempt_stays_charged_and_cannot_automatically_resume(tmp_path, monkeypatch):
    manifest, pairs = _setup(tmp_path)

    def interrupt(*args, **kwargs):
        raise OSError("injected after durable attempt charge")

    monkeypatch.setattr(sessions, "invoke_occupied_lane_governed_cycle_n1_consumer_v1", interrupt)
    root = tmp_path / "session"
    with _session(manifest, root) as opened:
        with pytest.raises(OSError, match="injected"):
            opened.run_occupied_cycle_v1(
                pairs,
                origin_main_sha="b" * 40,
                cycle_id_prefix="interrupted",
                observed_unix=1700000300.0,
                last_finalized_event_ts_unix=1700000240.0,
            )
        assert opened.state["attempts_used"] == 1
        assert opened.state["status"] == "RECOVERY_REQUIRED"
        with pytest.raises(ValueError, match="REQUIRES_REVIEW"):
            opened.run_occupied_cycle_v1(pairs)
    before = (root / sessions.RECEIPT).read_bytes()
    with pytest.raises(ValueError, match="REQUIRES_REVIEW"):
        with _session(manifest, root, "recover"):
            pytest.fail("resumed unproven attempt")
    assert (root / sessions.RECEIPT).read_bytes() == before


def test_manifest_loader_rejects_unknown_capability_and_duplicate_keys(tmp_path):
    manifest, pairs = _setup(tmp_path)
    path = tmp_path / "input.json"
    path.write_text(json.dumps(manifest.to_dict()))
    assert load_offline_episode_session_manifest_v1(path).digest() == manifest.digest()
    path.write_text(json.dumps({**manifest.to_dict(), "signing_port": "forbidden"}))
    with pytest.raises(ValueError, match="SCHEMA_MISMATCH"):
        load_offline_episode_session_manifest_v1(path)
    path.write_text('{"session_id":"one","session_id":"two"}')
    with pytest.raises(ValueError, match="DUPLICATE_JSON_KEY"):
        load_offline_episode_session_manifest_v1(path)


@pytest.mark.parametrize(
    "change", ["source", "code", "scope", "origin", "bounds", "lane", "receipt", "manifest"]
)
def test_changed_binding_rejects_before_attempt_charge(tmp_path, monkeypatch, change):
    manifest, pairs = _setup(tmp_path)
    root = tmp_path / "session"

    def forbidden(*args, **kwargs):
        pytest.fail("invalid binding reached the governed owner")

    # Let each negative reach its named preflight, not a missing-argument error.
    monkeypatch.setattr(sessions, "invoke_occupied_lane_governed_cycle_n1_consumer_v1", forbidden)
    with _session(manifest, root) as opened:
        kwargs = dict(
            origin_main_sha="b" * 40,
            cycle_id_prefix="attempt",
            observed_unix=1700000300.0,
            last_finalized_event_ts_unix=1700000240.0,
        )
        if change == "source":
            Path(manifest.lanes[0].source_path).write_text('{"content_digest":"changed"}')
        elif change == "code":
            monkeypatch.setattr(sessions, "repository_source_digest_v1", lambda: "c" * 64)
        elif change == "scope":
            kwargs["position_episode_scope"] = manifest.account_scope
        elif change == "origin":
            kwargs["origin_main_sha"] = "c" * 40
        elif change == "bounds":
            kwargs["observed_unix"] = manifest.replay_stop_unix + 1
        elif change == "lane":
            slot, bound = pairs["LANE_1"]
            pairs = {"LANE_1": (slot, replace(bound, selection_id="another-generation"))}
        elif change == "receipt":
            (root / sessions.RECEIPT).write_text("{}")
        else:
            (root / sessions.MANIFEST).write_text("{}")
        reason = {
            "source": "SOURCE_BINDING_MISMATCH",
            "code": "IMPLEMENTATION_CHANGED",
            "scope": "OWNER_OVERRIDE_FORBIDDEN",
            "origin": "ORIGIN_BINDING_CHANGED",
            "bounds": "REPLAY_BOUNDS_OR_PREFIX_INVALID",
            "lane": "BOUND_LANE_CHANGED",
            "receipt": "RECEIPT_CHANGED",
            "manifest": "MANIFEST_SCHEMA_MISMATCH",
        }[change]
        with pytest.raises(ValueError, match=reason):
            opened.run_occupied_cycle_v1(pairs, **kwargs)
        assert opened.state["attempts_used"] == 0


@pytest.mark.parametrize("change", ["budget", "partial", "running", "boolean_count"])
def test_recover_never_recreates_or_renews_unproven_session_state(tmp_path, change):
    manifest, pairs = _setup(tmp_path)
    root = tmp_path / "session"
    with _session(manifest, root):
        pass
    receipt = root / sessions.RECEIPT
    raw = json.loads(receipt.read_text())
    if change == "budget":
        manifest = replace(manifest, max_attempts=manifest.max_attempts + 1)
    elif change == "partial":
        receipt.unlink()
    else:
        raw.update(attempts_used=1, prefixes=["interrupted"], last_observed_unix=1700000300.0)
        if change == "running":
            raw["status"] = "RUNNING"
        else:
            raw["attempts_used"] = True
        receipt.write_text(json.dumps(raw))
    before = receipt.read_bytes() if receipt.exists() else None
    with pytest.raises(ValueError):
        with _session(manifest, root, "recover"):
            pytest.fail("recreated or renewed uncertain state")
    assert (receipt.read_bytes() if receipt.exists() else None) == before


def test_physical_process_death_releases_leases_but_does_not_renew_or_replay_attempt(tmp_path):
    import fcntl
    import signal
    import subprocess
    import time

    manifest, pairs = _setup(tmp_path)
    root = tmp_path / "session"
    with _session(manifest, root):
        pass
    before = {
        p: p.read_bytes()
        for value in (manifest.lanes[0].exit_state_root, manifest.lanes[0].cursor_state_root)
        for p in Path(value).rglob("*.json")
    }
    manifest_path = tmp_path / "worker-input.json"
    manifest_path.write_text(json.dumps(manifest.to_dict()))
    checkpoint = tmp_path / "checkpoint"
    repo = Path(__file__).resolve().parents[2]
    with (tmp_path / "worker-output").open("w") as output:
        child = subprocess.Popen(
            [
                str(repo / "scripts/pt"),
                "-m",
                "tests.ops._bounded_offline_episode_session_worker_v1",
                str(manifest_path),
                str(root),
                str(checkpoint),
            ],
            cwd=repo,
            stdout=output,
            stderr=output,
        )
        try:
            deadline = time.monotonic() + 20
            while not checkpoint.exists() and child.poll() is None and time.monotonic() < deadline:
                time.sleep(0.05)
            assert checkpoint.exists(), (tmp_path / "worker-output").read_text()
            child.send_signal(signal.SIGKILL)
            child.wait(timeout=5)
        finally:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=5)
    receipt = json.loads((root / sessions.RECEIPT).read_text())
    assert receipt["status"] == "RUNNING" and receipt["attempts_used"] == 1
    assert receipt["prefixes"] == ["physical-death-checkpoint"]
    for resource in (
        str(root),
        manifest.lanes[0].exit_state_root,
        manifest.lanes[0].cursor_state_root,
    ):
        with (Path(resource) / sessions.LEASE).open("a") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    with pytest.raises(ValueError, match="INTERRUPTED_ATTEMPT_REQUIRES_REVIEW"):
        with _session(manifest, root, "recover"):
            pytest.fail("replayed an interrupted attempt")
    assert json.loads((root / sessions.RECEIPT).read_text()) == receipt
    assert {p: p.read_bytes() for p in before} == before
