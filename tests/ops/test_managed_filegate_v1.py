"""The original risk readers and writer share the managed Safety generation."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from types import SimpleNamespace

import pytest
from nacl.signing import SigningKey

from src.ops.filegate_recovery_authority_v1 import (
    FilegateAuthorityError,
    FilegateRecoveryScopeV1,
    attest_filegate_owner_evidence_v1,
    sign_filegate_revocation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_post_safety_veto_v1 import (
    CurrentPostSafetyContextV1,
    CurrentPostSafetyVetoError,
)
from src.ops.full_core_live_path_composition_root_v1.durable_filegate_join_v1 import (
    read_durable_filegate_join_evidence_v1,
)
from src.ops.gates.risk_gate import kill_switch_should_block_trading
from src.ops.managed_filegate_v1 import ROOT_ENV, ManagedFilegateV1
from src.risk_layer.kill_switch.core import KillSwitch
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.state import KillSwitchState
from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    _envelope,
)


@pytest.fixture
def safety(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    separate = tmp_path / "separate"
    separate.mkdir(mode=0o700)
    path = runtime / "state.json"
    clock = [1000.0]
    writer = ManagedFilegateV1(state_path=path, root=separate, clock=lambda: clock[0])
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(path))
    monkeypatch.setenv(ROOT_ENV, str(separate))
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    owner_keys = {role: SigningKey.generate() for role in ("CAUSE", "ACCOUNT", "HOST")}
    issuer_key = SigningKey.generate()
    scope = FilegateRecoveryScopeV1("account", "SHADOW", "host", ("BTC-FUTURES",), "a" * 64)
    writer.provision_v1(
        scope=scope,
        issuer_public_key=bytes(issuer_key.verify_key),
        owner_public_keys={role: bytes(key.verify_key) for role, key in owner_keys.items()},
        recoverable_causes={"R01", "R03", "R04", "R06"},
    )
    return SimpleNamespace(
        writer=writer, path=path, clock=clock, issuer_key=issuer_key, owner_keys=owner_keys
    )


def _approved(safety):
    writer = safety.writer
    stop = writer.inspect_stop_v1()
    evidence = {
        role: attest_filegate_owner_evidence_v1(
            role=role,
            stop=stop,
            evidence_sha256="c" * 64,
            observed_at=safety.clock[0],
            expires_at=safety.clock[0] + 10,
            key=key,
        )
        for role, key in safety.owner_keys.items()
    }
    return dict(
        release=writer.issue_release_v1(evidence=evidence, issuer_key=safety.issuer_key),
        evidence=evidence,
    )


def test_provision_repair_release_original_readback_and_no_replay(safety):
    assert kill_switch_should_block_trading()
    original_switch = KillSwitch({}, persistence=StatePersistence(str(safety.path)))
    assert original_switch.is_killed
    assert not original_switch.request_recovery("legacy")
    assert not original_switch.complete_recovery()
    approval = _approved(safety)
    released = safety.writer.release_v1(**approval)
    assert released["state"] == "ACTIVE"
    assert original_switch.is_active
    evidence = read_durable_filegate_join_evidence_v1()
    assert evidence.state_name == "ACTIVE" and evidence.blocked is False
    with pytest.raises(FilegateAuthorityError, match="STOP_UNPROVEN"):
        safety.writer.release_v1(**approval)
    assert original_switch.trigger("emergency from the original entry point")
    assert original_switch.is_killed
    assert original_switch.get_status()["state"] == "KILLED"
    assert safety.writer.inspect_stop_v1()["causes"] == ["R09"]
    with pytest.raises(FilegateAuthorityError, match="CAUSE_REQUIRES_SEPARATE_AUTHORITY"):
        _approved(safety)


def test_new_authenticated_kill_invalidates_old_release_and_duplicate_is_idempotent(safety):
    approval = _approved(safety)
    args = dict(
        cause="R04",
        reason="confirmed fill incident",
        incident_id="b" * 64,
        incident_scope=dict(
            account="account", environment="SHADOW", host="host", instrument="BTC-FUTURES"
        ),
    )
    newer = safety.writer.kill_v1(**args)
    assert newer["causes"] == ["R03", "R04"]
    assert newer["generation"] > approval["release"]["body"]["stop"]["generation"]
    assert safety.writer.kill_v1(**args) == newer
    with pytest.raises(FilegateAuthorityError, match="BINDING_CHANGED"):
        safety.writer.release_v1(**approval)
    with pytest.raises(FilegateAuthorityError, match="CAUSE_EVIDENCE_COVERAGE_UNPROVEN"):
        _approved(safety)
    assert kill_switch_should_block_trading()


@pytest.mark.parametrize("fault", ["absent", "invalid", "rollback", "foreign-active"])
def test_rollback_or_damaged_projection_is_fenced_until_repaired(safety, fault):
    safety.writer.release_v1(**_approved(safety))
    older = safety.path.read_bytes()
    safety.writer.kill_v1(cause="R01", reason="feed loss")
    if fault == "absent":
        safety.path.unlink()
    else:
        safety.path.write_bytes(
            {"invalid": b"{", "rollback": older, "foreign-active": b'{"state":"ACTIVE"}'}[fault]
        )
    assert kill_switch_should_block_trading()
    assert KillSwitch({}, persistence=StatePersistence(str(safety.path))).is_killed
    restored = safety.writer.repair_projection_v1()
    assert restored["causes"] == ["R01", "R03"]
    assert read_durable_filegate_join_evidence_v1().state_name == "KILLED"


@pytest.mark.parametrize("fault", ["expired", "forged", "revoked", "foreign-proof", "overlay"])
def test_release_denies_invalid_authority_and_preserves_original_stop(safety, monkeypatch, fault):
    approval = _approved(safety)
    before = safety.path.read_bytes()
    if fault == "expired":
        safety.clock[0] += 10
    elif fault == "forged":
        approval["release"]["signature"] = "0" * 64
    elif fault == "revoked":
        safety.writer.revoke_release_v1(
            revocation=sign_filegate_revocation_v1(
                release=approval["release"], issuer_key=safety.issuer_key
            )
        )
    elif fault == "foreign-proof":
        approval["evidence"]["HOST"] = approval["evidence"]["ACCOUNT"]
    else:
        monkeypatch.setenv("PEAK_KILL_SWITCH", "1")
    with pytest.raises(FilegateAuthorityError):
        safety.writer.release_v1(**approval)
    assert safety.path.read_bytes() == before
    assert kill_switch_should_block_trading()


def test_new_pending_kill_preempts_release_even_during_publication(safety, monkeypatch):
    approval = _approved(safety)
    publish = safety.writer._publish
    publish_json = safety.writer._publish_json
    publishing, attempted_kill, resume = Event(), Event(), Event()
    blocked_during_publication = []

    def pause_release(projection):
        if projection["state"] == "ACTIVE":
            publishing.set()
            assert resume.wait(timeout=5)
        publish(projection)
        if projection["state"] == "ACTIVE":
            blocked_during_publication.append(kill_switch_should_block_trading())

    def track_pending(path, payload):
        publish_json(path, payload)
        if path.name.startswith("kill-intent-"):
            attempted_kill.set()

    def kill():
        return safety.writer.kill_v1(cause="R01", reason="new incident")

    monkeypatch.setattr(safety.writer, "_publish", pause_release)
    monkeypatch.setattr(safety.writer, "_publish_json", track_pending)
    with ThreadPoolExecutor(max_workers=2) as pool:
        release = pool.submit(safety.writer.release_v1, **approval)
        try:
            assert publishing.wait(timeout=5)
            pending_kill = pool.submit(kill)
            assert attempted_kill.wait(timeout=5)
            assert not pending_kill.done()
            assert kill_switch_should_block_trading()
        finally:
            resume.set()
        assert pending_kill.result(timeout=5)["causes"] == ["R01"]
        with pytest.raises(FilegateAuthorityError, match="STOP_CHANGED_BEFORE_RELEASE"):
            release.result(timeout=5)
    assert blocked_during_publication == [True]
    assert kill_switch_should_block_trading()


def test_crash_between_committed_release_and_projection_remains_blocked(safety, monkeypatch):
    approval = _approved(safety)
    with monkeypatch.context() as patch:

        def fail(_projection):
            raise OSError("fault injection before publication")

        patch.setattr(safety.writer, "_publish", fail)
        with pytest.raises(OSError, match="fault injection"):
            safety.writer.release_v1(**approval)
    cold = ManagedFilegateV1(
        state_path=safety.path, root=safety.writer.root, clock=lambda: safety.clock[0]
    )
    assert kill_switch_should_block_trading()
    assert cold.repair_projection_v1()["causes"] == ["R03"]
    with pytest.raises(FilegateAuthorityError):
        cold.release_v1(**approval)


def test_emergency_with_separate_head_temporarily_unavailable_is_preserved(safety):
    safety.writer.release_v1(**_approved(safety))
    (database,) = safety.writer.root.glob("*.sqlite3")
    moved = database.with_suffix(".unavailable")
    database.rename(moved)
    assert kill_switch_should_block_trading()
    switch = KillSwitch({}, persistence=StatePersistence(str(safety.path)))
    assert switch.trigger("emergency while head unavailable")
    moved.rename(database)
    assert kill_switch_should_block_trading()
    assert safety.writer.repair_projection_v1()["causes"] == ["R03", "R09"]


def test_legacy_write_and_backup_restore_cannot_replace_managed_projection(safety, monkeypatch):
    persistence = StatePersistence(str(safety.path))
    safety.writer.release_v1(**_approved(safety))
    for mutation in (
        persistence.clear,
        persistence.restore_from_backup,
        lambda: persistence.save(KillSwitchState.ACTIVE),
    ):
        with pytest.raises(ValueError, match="FILEGATE_MANAGED"):
            mutation()
    monkeypatch.delenv(ROOT_ENV)
    assert kill_switch_should_block_trading()
    with pytest.raises(ValueError, match="FILEGATE_MANAGED"):
        persistence.save(KillSwitchState.ACTIVE)
    assert KillSwitch({}, persistence=persistence).is_killed


def test_revoked_published_release_reblocks_original_reader(safety):
    approval = _approved(safety)
    safety.writer.release_v1(**approval)
    assert not kill_switch_should_block_trading()
    revocation = sign_filegate_revocation_v1(
        release=approval["release"], issuer_key=safety.issuer_key
    )
    safety.writer.revoke_release_v1(revocation=revocation)
    first = safety.writer.inspect_stop_v1()
    safety.writer.revoke_release_v1(revocation=revocation)
    assert first == safety.writer.inspect_stop_v1()
    assert first["causes"] == ["R06"]
    assert kill_switch_should_block_trading()


def test_old_order_safety_context_cannot_cross_a_kill_followed_by_fresh_release(safety):
    safety.writer.release_v1(**_approved(safety))
    envelope = _envelope()
    old = CurrentPostSafetyContextV1(envelope, str(safety.path))
    assert not old.inspect_v1(stage="PRE_PERMIT").blocked
    safety.writer.kill_v1(cause="R01", reason="feed failure")
    safety.writer.release_v1(**_approved(safety))
    with pytest.raises(CurrentPostSafetyVetoError, match="FILEGATE_REVISION_CHANGED"):
        old.inspect_v1(stage="PRE_SOCKET")
    new = CurrentPostSafetyContextV1(envelope, str(safety.path))
    assert not new.inspect_v1(stage="PRE_PERMIT").blocked
