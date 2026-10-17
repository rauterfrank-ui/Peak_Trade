"""B5/B6 security closure V2: single kill-switch source, live-attempt-bound ledger release.

Offline only: fake states under tmp_path, no venue, no credentials, no owner ledger.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_global_venue_effect_authority_ledger_v1 as ledger_mod,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_global_venue_effect_authority_ledger_v1 import (
    ACCOUNT_SCOPE_K1,
    CLASS_UNKNOWN_OUTCOME,
    ENVIRONMENT_LIVE_EEA,
    RISK_CLASS_NEW_RISK,
    RISK_CLASS_RISK_REDUCING,
    SCHEMA_VERSION,
    STATE_ABORTED_BEFORE_TRANSPORT,
    STATE_CLAIMED,
    STATE_COMPLETED_RESPONSE_RECEIVED,
    STATE_SENT_INITIATED,
    STATE_UNKNOWN_OUTCOME,
    GlobalVenueEffectAuthorityLedgerV1,
    GlobalVenueEffectIdentityV1,
    GlobalVenueEffectLedgerError,
    GlobalVenueEffectReplayDeniedError,
    ledger_filesystem_is_proven_local_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_post_path_kill_switch_gate_v1 import (
    DENY_ACTIVE_NOT_CANONICAL_WRITER,
    DENY_ENV_OVERRIDE_REJECTED,
    PostPathKillSwitchDecisionV1,
    evaluate_post_path_kill_switch_v1,
    read_post_path_kill_switch_evidence_v1,
    resolve_post_path_kill_switch_state_path_v1,
)
from src.ops.gates.risk_gate import (
    canonical_kill_switch_state_path,
    kill_switch_should_block_trading,
)
from src.risk_layer.kill_switch.cli import cmd_recover, cmd_trigger
from src.risk_layer.kill_switch.core import KillSwitch
from src.risk_layer.kill_switch.state import KillSwitchState
from tests.ops._post_path_safety_fixtures_v1 import (
    isolate_kill_switch_state_root_v1,
    write_kill_switch_state_v1,
)
from tests.ops.test_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    _new_risk_envelope,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
KILL_SWITCH_ENV = "PEAK_KILL_SWITCH_STATE_PATH"
TEST_BASELINE_SHA = "1" * 40


def _bind_root(monkeypatch: pytest.MonkeyPatch, root: Path) -> Path:
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    return isolate_kill_switch_state_root_v1(monkeypatch, root)


def _writer() -> KillSwitch:
    return KillSwitch(
        {"persist_state": True, "require_approval_code": False, "recovery_cooldown_seconds": 0}
    )


def _admission(evidence):  # noqa: ANN001, ANN202
    return evaluate_post_path_kill_switch_v1(
        evidence=evidence, envelope=_new_risk_envelope(), risk_reduction_proof=None
    )


def _identity(
    *, client_order_id: str = "pt-v2-cl-1", risk_class: str = RISK_CLASS_NEW_RISK
) -> GlobalVenueEffectIdentityV1:
    return GlobalVenueEffectIdentityV1(
        owner_go_token=f"GO-V2-{client_order_id}",
        account_scope=ACCOUNT_SCOPE_K1,
        environment=ENVIRONMENT_LIVE_EEA,
        permit_id=f"eep-{client_order_id}",
        envelope_id=f"env-{client_order_id}",
        envelope_digest=hashlib.sha256(client_order_id.encode("utf-8")).hexdigest(),
        client_order_id=client_order_id,
        risk_class=risk_class,
        baseline_origin_main_sha=TEST_BASELINE_SHA,
    )


def _ledger(tmp_path: Path) -> GlobalVenueEffectAuthorityLedgerV1:
    return GlobalVenueEffectAuthorityLedgerV1(root=tmp_path / "ledger")


# --------------------------------------------------------------------------- B5


def test_v2_writer_and_all_readers_share_one_source_across_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bind_root(monkeypatch, tmp_path / "ks")
    writer_cwd = tmp_path / "writer_cwd"
    writer_cwd.mkdir()
    monkeypatch.chdir(writer_cwd)
    writer = _writer()
    cmd_trigger(Namespace(reason="v2-single-source", confirm=True), writer)
    other = tmp_path / "other_cwd"
    other.mkdir()
    monkeypatch.chdir(other)
    assert canonical_kill_switch_state_path() == str(path.resolve())
    assert resolve_post_path_kill_switch_state_path_v1() == path.resolve()
    assert json.loads(path.read_text(encoding="utf-8"))["state"] == "KILLED"
    assert kill_switch_should_block_trading(explicit_active=False) is True
    evidence = read_post_path_kill_switch_evidence_v1()
    assert evidence.state_path == str(path.resolve())
    assert evidence.state_name == "KILLED"
    assert _admission(evidence).decision is PostPathKillSwitchDecisionV1.DENY
    assert _writer().state is KillSwitchState.KILLED

    cmd_recover(Namespace(reason="v2-recover", code="any", approved_by="test"), writer)
    assert json.loads(path.read_text(encoding="utf-8"))["state"] == "RECOVERING"
    assert kill_switch_should_block_trading(explicit_active=False) is True
    assert _admission(read_post_path_kill_switch_evidence_v1()).decision is (
        PostPathKillSwitchDecisionV1.DENY
    )
    assert writer.complete_recovery() is True
    assert writer.state is KillSwitchState.ACTIVE
    evidence = read_post_path_kill_switch_evidence_v1()
    assert evidence.writer_schema_state == "ACTIVE"
    assert kill_switch_should_block_trading(explicit_active=False) is False
    assert _admission(evidence).decision is PostPathKillSwitchDecisionV1.ALLOW


_CHILD_KILL_SWITCH_PROBE = (
    "import sys, json; from pathlib import Path; sys.path.insert(0, sys.argv[1]);"
    "ambient = sys.argv[2];"
    "__import__('pytest') if ambient == 'pytest_imported' else None;"
    "from src.ops.gates.risk_gate import ("
    " canonical_kill_switch_state_path, kill_switch_env_override_rejected,"
    " kill_switch_should_block_trading);"
    "from src.ops.full_core_live_path_composition_root_v1."
    "current_productive_post_path_kill_switch_gate_v1 import ("
    " read_post_path_kill_switch_evidence_v1, evaluate_post_path_kill_switch_v1);"
    "ev = read_post_path_kill_switch_evidence_v1();"
    "out = {"
    " 'pytest_loaded': 'pytest' in sys.modules,"
    " 'canonical': canonical_kill_switch_state_path(),"
    " 'rejected': kill_switch_env_override_rejected(),"
    " 'blocked': kill_switch_should_block_trading(explicit_active=False),"
    " 'evidence_rejected': ev.env_override_rejected,"
    " 'evidence_status': ev.evidence_status,"
    " 'evidence_path': ev.state_path};"
    "from tests.ops.test_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1"
    " import _new_risk_envelope;"
    "adm = evaluate_post_path_kill_switch_v1("
    " evidence=ev, envelope=_new_risk_envelope(), risk_reduction_proof=None);"
    "out['decision'] = adm.decision.value; out['reasons'] = list(adm.reason_codes);"
    "print(json.dumps(out))"
)


def _run_child_kill_switch_probe(*, cwd: Path, ambient: str, env_override: Path | None) -> dict:
    env = {
        k: v
        for k, v in os.environ.items()
        if k
        not in {
            "PYTEST_CURRENT_TEST",
            KILL_SWITCH_ENV,
            "PEAKTRADE_KILL_SWITCH_STATE_PATH",
            "PEAK_KILL_SWITCH",
        }
    }
    if ambient == "pytest_current_test_env":
        env["PYTEST_CURRENT_TEST"] = "forged::probe (call)"
    if env_override is not None:
        env[KILL_SWITCH_ENV] = str(env_override)
    proc = subprocess.run(
        [sys.executable, "-c", _CHILD_KILL_SWITCH_PROBE, str(REPO_ROOT), ambient],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout.strip().splitlines()[-1])


@pytest.mark.parametrize("ambient", ["none", "pytest_current_test_env", "pytest_imported"])
def test_v3_env_override_never_redirects_regardless_of_pytest_presence(
    tmp_path: Path, ambient: str
) -> None:
    forged = write_kill_switch_state_v1(tmp_path / "forged" / "state.json", state="ACTIVE")
    other = tmp_path / "other_cwd"
    other.mkdir()
    out = _run_child_kill_switch_probe(cwd=other, ambient=ambient, env_override=forged)
    assert out["pytest_loaded"] is (ambient == "pytest_imported")
    assert out["rejected"] is True
    assert out["canonical"] == canonical_kill_switch_state_path()
    assert out["canonical"] != str(forged.resolve())
    assert out["evidence_path"] == out["canonical"]
    assert out["blocked"] is True
    assert out["evidence_rejected"] is True
    assert out["decision"] == PostPathKillSwitchDecisionV1.DENY.value
    assert DENY_ENV_OVERRIDE_REJECTED in out["reasons"]


def test_v3_in_process_test_injection_is_not_inherited_by_child_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    injected = write_kill_switch_state_v1(_bind_root(monkeypatch, tmp_path / "ks"), state="ACTIVE")
    assert _admission(read_post_path_kill_switch_evidence_v1()).decision is (
        PostPathKillSwitchDecisionV1.ALLOW
    )
    monkeypatch.undo()
    canonical = canonical_kill_switch_state_path()
    assert canonical != str(injected)
    if Path(canonical).is_file():
        pytest.skip("checkout has a real kill-switch state file; MISSING branch not observable")
    out = _run_child_kill_switch_probe(cwd=tmp_path, ambient="pytest_imported", env_override=None)
    assert out["evidence_path"] == canonical
    assert out["evidence_status"] == "MISSING"
    assert out["decision"] == PostPathKillSwitchDecisionV1.DENY.value


def test_v2_post_gate_denies_rejected_override_before_any_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = write_kill_switch_state_v1(_bind_root(monkeypatch, tmp_path), state="ACTIVE")
    evidence = read_post_path_kill_switch_evidence_v1()
    assert _admission(evidence).decision is PostPathKillSwitchDecisionV1.ALLOW
    forged = type(evidence)(**{**evidence.__dict__, "env_override_rejected": True})
    admission = _admission(forged)
    assert admission.decision is PostPathKillSwitchDecisionV1.DENY
    assert admission.reason_codes == (DENY_ENV_OVERRIDE_REJECTED,)
    other = write_kill_switch_state_v1(tmp_path / "other" / "state.json", state="ACTIVE")
    monkeypatch.setenv(KILL_SWITCH_ENV, str(other))
    redirected = read_post_path_kill_switch_evidence_v1()
    assert redirected.state_path == str(path)
    assert redirected.env_override_rejected is True
    assert kill_switch_should_block_trading(explicit_active=False) is True
    assert _admission(redirected).reason_codes == (DENY_ENV_OVERRIDE_REJECTED,)


@pytest.mark.parametrize(
    "payload",
    [
        {"state": "ACTIVE"},
        {"state": "ACTIVE", "saved_at": "2026-10-17T00:00:00"},
        {"state": "ACTIVE", "version": "0.9", "saved_at": "2026-10-17T00:00:00"},
        {"state": "ACTIVE", "version": "1.0", "saved_at": ""},
        {"state": "ACTIVE", "version": "1.0", "saved_at": "yesterday"},
    ],
    ids=["no_schema", "no_version", "wrong_version", "empty_saved_at", "bad_saved_at"],
)
def test_v2_historical_active_file_never_counts_as_active(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, payload: dict
) -> None:
    path = _bind_root(monkeypatch, tmp_path)
    write_kill_switch_state_v1(path, raw=json.dumps(payload))
    evidence = read_post_path_kill_switch_evidence_v1()
    admission = _admission(evidence)
    assert admission.decision is PostPathKillSwitchDecisionV1.DENY
    assert DENY_ACTIVE_NOT_CANONICAL_WRITER in admission.reason_codes


def test_v2_legacy_cwd_stop_signal_blocks_legacy_reader_and_post_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_kill_switch_state_v1(_bind_root(monkeypatch, tmp_path / "primary"), state="ACTIVE")
    legacy_root = tmp_path / "legacy_cwd"
    write_kill_switch_state_v1(legacy_root / "data" / "kill_switch" / "state.json", state="KILLED")
    assert kill_switch_should_block_trading(explicit_active=False) is False
    monkeypatch.chdir(legacy_root)
    assert kill_switch_should_block_trading(explicit_active=False) is True
    assert _admission(read_post_path_kill_switch_evidence_v1()).decision is (
        PostPathKillSwitchDecisionV1.DENY
    )


def test_v2_legacy_cwd_active_never_admits_when_canonical_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _bind_root(monkeypatch, tmp_path / "absent")
    legacy_root = tmp_path / "legacy_cwd"
    legacy_root.mkdir()
    monkeypatch.chdir(legacy_root)
    without_legacy = kill_switch_should_block_trading(explicit_active=False)
    write_kill_switch_state_v1(legacy_root / "data" / "kill_switch" / "state.json", state="ACTIVE")
    assert kill_switch_should_block_trading(explicit_active=False) is without_legacy
    evidence = read_post_path_kill_switch_evidence_v1()
    assert evidence.evidence_status == "MISSING"
    assert _admission(evidence).decision is PostPathKillSwitchDecisionV1.DENY


def test_v2_writer_persists_atomically_with_canonical_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bind_root(monkeypatch, tmp_path / "ks")
    writer = _writer()
    cmd_trigger(Namespace(reason="v2-schema", confirm=True), writer)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["version"] == "1.0"
    assert payload["state"] == "KILLED"
    assert payload["saved_at"]
    assert not list(path.parent.glob("*.tmp"))


# --------------------------------------------------------------------------- B6


def test_v2_restarted_instance_cannot_release_sent_initiated(tmp_path: Path) -> None:
    live = _ledger(tmp_path)
    claim = live.claim_v1(_identity())
    live.mark_sent_initiated_v1(
        claim.claim_id,
        permit_id=claim.identity.permit_id,
        envelope_digest=claim.identity.envelope_digest,
    )
    restarted = _ledger(tmp_path)
    for releasing in (STATE_COMPLETED_RESPONSE_RECEIVED, STATE_ABORTED_BEFORE_TRANSPORT):
        with pytest.raises(GlobalVenueEffectLedgerError, match="REQUIRES_LIVE_ATTEMPT"):
            restarted.mark_outcome_v1(claim.claim_id, outcome_state=releasing)
    assert restarted.load_claim_v1(claim.claim_id)["state"] == STATE_SENT_INITIATED
    restarted.mark_outcome_v1(claim.claim_id, outcome_state=STATE_UNKNOWN_OUTCOME)
    [view] = restarted.classify_unresolved_claims_v1()
    assert view["classification"] == CLASS_UNKNOWN_OUTCOME
    assert view["safe_to_retry"] is False
    with pytest.raises(GlobalVenueEffectLedgerError, match="INVALID_TRANSITION"):
        live.mark_outcome_v1(claim.claim_id, outcome_state=STATE_COMPLETED_RESPONSE_RECEIVED)
    with pytest.raises(GlobalVenueEffectLedgerError, match="BLOCKS_NEW_RISK"):
        restarted.claim_v1(_identity(client_order_id="pt-v2-next"))


def test_v2_live_attempt_releases_and_new_risk_unblocks(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path)
    claim = ledger.claim_v1(_identity())
    [view] = ledger.classify_unresolved_claims_v1()
    assert view["held_by_this_live_attempt"] is True
    ledger.abandon_unsent_claim_v1(claim.claim_id, reason="live attempt never sent")
    assert ledger.unresolved_claims_v1() == []
    with pytest.raises(GlobalVenueEffectReplayDeniedError):
        ledger.claim_v1(_identity())
    second = ledger.claim_v1(_identity(client_order_id="pt-v2-second"))
    ledger.mark_sent_initiated_v1(
        second.claim_id,
        permit_id=second.identity.permit_id,
        envelope_digest=second.identity.envelope_digest,
    )
    ledger.mark_outcome_v1(second.claim_id, outcome_state=STATE_COMPLETED_RESPONSE_RECEIVED)
    record = ledger.load_claim_v1(second.claim_id)
    assert record["retry_allowed"] is False
    assert record["authorization_reusable"] is False


def test_v2_abandon_forbidden_when_history_shows_send_even_if_state_forged(
    tmp_path: Path,
) -> None:
    ledger = _ledger(tmp_path)
    claim = ledger.claim_v1(_identity())
    ledger.mark_sent_initiated_v1(
        claim.claim_id,
        permit_id=claim.identity.permit_id,
        envelope_digest=claim.identity.envelope_digest,
    )
    path = ledger.namespace / "claims" / f"{claim.claim_id}.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["state"] = STATE_CLAIMED
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(GlobalVenueEffectLedgerError, match="ABANDON_AFTER_SEND_FORBIDDEN"):
        ledger.abandon_unsent_claim_v1(claim.claim_id, reason="forged")


def test_v2_claim_record_without_markers_still_replay_denied(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path)
    claim = ledger.claim_v1(_identity())
    ledger.abandon_unsent_claim_v1(claim.claim_id, reason="unsent")
    for marker in ledger.namespace.glob("*/*.json"):
        if marker.parent.name != "claims":
            marker.unlink()
    with pytest.raises(GlobalVenueEffectReplayDeniedError, match="CLAIM_RECORD"):
        ledger.claim_v1(_identity())


def test_v2_host_binding_mismatch_fails_closed(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path)
    claim = ledger.claim_v1(_identity(risk_class=RISK_CLASS_RISK_REDUCING))
    binding = ledger.namespace / "host_binding.json"
    assert json.loads(binding.read_text(encoding="utf-8"))["host_identity_sha256"]
    binding.write_text(
        json.dumps({"schema_version": SCHEMA_VERSION, "host_identity_sha256": "f" * 64}),
        encoding="utf-8",
    )
    with pytest.raises(GlobalVenueEffectLedgerError, match="HOST_BINDING_MISMATCH"):
        ledger.claim_v1(_identity(client_order_id="pt-v2-other-host"))
    with pytest.raises(GlobalVenueEffectLedgerError, match="HOST_BINDING_MISMATCH"):
        ledger.mark_sent_initiated_v1(
            claim.claim_id,
            permit_id=claim.identity.permit_id,
            envelope_digest=claim.identity.envelope_digest,
        )
    binding.unlink()
    with pytest.raises(GlobalVenueEffectLedgerError, match="HOST_BINDING_MISSING"):
        ledger.abandon_unsent_claim_v1(claim.claim_id, reason="binding removed")


def test_v2_unproven_local_filesystem_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert ledger_filesystem_is_proven_local_v1(tmp_path) is True
    monkeypatch.setattr(ledger_mod, "ledger_filesystem_is_proven_local_v1", lambda _p: False)
    with pytest.raises(GlobalVenueEffectLedgerError, match="FILESYSTEM_NOT_PROVEN_LOCAL"):
        _ledger(tmp_path)


# --------------------------------------------------------------------------- protected pins


def test_v2_protected_pins_detect_every_unpinned_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.ops import _protected_surface_content_pins_v1 as pins

    repo = tmp_path / "repo"
    (repo / "prot").mkdir(parents=True)
    git_env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=repo, env=git_env, check=True, capture_output=True, text=True
        ).stdout.strip()

    git("init", "-q")
    (repo / "prot" / "a.py").write_text("A = 1\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-qm", "base")
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    monkeypatch.setattr(pins, "REPO_ROOT", repo)
    monkeypatch.setattr(pins, "AUTHORIZED_PROTECTED_SURFACE_CHANGES_V1", {})
    assert pins.unauthorized_protected_changes_v1(["prot/"]) == []

    (repo / "prot" / "a.py").write_text("A = 2\n", encoding="utf-8")
    (repo / "prot" / "new.py").write_text("N = 1\n", encoding="utf-8")
    assert pins.unauthorized_protected_changes_v1(["prot/"]) == [
        "prot/a.py:NOT_PINNED",
        "prot/new.py:NOT_PINNED",
    ]

    base_blob = git("rev-parse", "origin/main:prot/a.py")
    sha = hashlib.sha256(b"A = 2\n").hexdigest()
    new_sha = hashlib.sha256(b"N = 1\n").hexdigest()
    monkeypatch.setattr(
        pins,
        "AUTHORIZED_PROTECTED_SURFACE_CHANGES_V1",
        {"prot/a.py": ("GO", base_blob, sha), "prot/new.py": ("GO", None, new_sha)},
    )
    assert pins.unauthorized_protected_changes_v1(["prot/"]) == []

    (repo / "prot" / "a.py").write_text("A = 3\n", encoding="utf-8")
    (repo / "prot" / "other.py").write_text("O = 1\n", encoding="utf-8")
    assert pins.unauthorized_protected_changes_v1(["prot/"]) == [
        "prot/a.py:CONTENT_NOT_PINNED",
        "prot/other.py:NOT_PINNED",
    ]
    (repo / "prot" / "other.py").unlink()
    (repo / "prot" / "a.py").write_text("A = 2\n", encoding="utf-8")
    (repo / "prot" / "new.py").unlink()
    assert pins.unauthorized_protected_changes_v1(["prot/"]) == []

    (repo / "prot" / "a.py").write_text("A = 9\n", encoding="utf-8")
    git("commit", "-qam", "main moved")
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    (repo / "prot" / "a.py").write_text("A = 2\n", encoding="utf-8")
    assert pins.unauthorized_protected_changes_v1(["prot/"]) == ["prot/a.py:ORIGIN_MAIN_BASE_MOVED"]
    (repo / "prot" / "a.py").unlink()
    assert pins.unauthorized_protected_changes_v1(["prot/"]) == ["prot/a.py:ORIGIN_MAIN_BASE_MOVED"]


@pytest.mark.skipif(sys.platform != "darwin", reason="darwin mount classification")
def test_v2_non_allowlisted_filesystem_type_is_not_local() -> None:
    assert ledger_filesystem_is_proven_local_v1("/dev") is False


# --------------------------------------------------------------------------- V5 linux allowlist

_FS_MAGIC_EXT4 = 0xEF53
_FS_MAGIC_XFS = 0x58465342
_FS_MAGIC_BTRFS = 0x9123683E
_FS_MAGIC_TMPFS = 0x01021994
_FS_MAGIC_OVERLAYFS = 0x794C7630
_FS_MAGIC_NFS = 0x6969


def _fake_linux_statfs(monkeypatch: pytest.MonkeyPatch, *, magic: int, rc: int = 0) -> list[bytes]:
    calls: list[bytes] = []

    class _FakeLibc:
        def statfs(self, path: bytes, ref) -> int:  # noqa: ANN001
            calls.append(path)
            ref._obj[0] = magic
            return rc

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(ledger_mod.ctypes, "CDLL", lambda *_a, **_k: _FakeLibc())
    return calls


def test_v5_linux_allowlist_is_exactly_reboot_persistent_filesystems() -> None:
    assert ledger_mod._LINUX_LOCAL_FS_MAGIC == frozenset(
        {_FS_MAGIC_EXT4, _FS_MAGIC_XFS, _FS_MAGIC_BTRFS}
    )
    assert ledger_mod._DARWIN_LOCAL_FSTYPES == frozenset({"apfs", "hfs"})


@pytest.mark.parametrize("magic", [_FS_MAGIC_TMPFS, _FS_MAGIC_OVERLAYFS, _FS_MAGIC_NFS, 0], ids=str)
def test_v5_linux_non_persistent_or_unknown_filesystem_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, magic: int
) -> None:
    calls = _fake_linux_statfs(monkeypatch, magic=magic)
    assert ledger_filesystem_is_proven_local_v1(tmp_path) is False
    assert calls == [os.fsencode(str(tmp_path))]


@pytest.mark.parametrize("magic", [_FS_MAGIC_EXT4, _FS_MAGIC_XFS, _FS_MAGIC_BTRFS], ids=str)
def test_v5_linux_persistent_filesystem_still_allowed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, magic: int
) -> None:
    _fake_linux_statfs(monkeypatch, magic=magic)
    assert ledger_filesystem_is_proven_local_v1(tmp_path) is True


def test_v5_linux_statfs_failure_and_unknown_platform_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _fake_linux_statfs(monkeypatch, magic=_FS_MAGIC_EXT4, rc=-1)
    assert ledger_filesystem_is_proven_local_v1(tmp_path) is False
    monkeypatch.setattr(sys, "platform", "win32")
    assert ledger_filesystem_is_proven_local_v1(tmp_path) is False


@pytest.mark.parametrize("magic", [_FS_MAGIC_TMPFS, _FS_MAGIC_OVERLAYFS], ids=str)
def test_v5_alternative_store_root_cannot_bypass_linux_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, magic: int
) -> None:
    calls = _fake_linux_statfs(monkeypatch, magic=magic)
    for root in (tmp_path / "alt", tmp_path / "missing" / "nested" / "root", tmp_path):
        with pytest.raises(GlobalVenueEffectLedgerError, match="FILESYSTEM_NOT_PROVEN_LOCAL"):
            GlobalVenueEffectAuthorityLedgerV1(root=root)
    assert len(calls) == 3
    with pytest.raises(GlobalVenueEffectLedgerError, match="CANONICAL_ROOT_FORBIDDEN_UNDER_TEST"):
        GlobalVenueEffectAuthorityLedgerV1()
    assert sorted(p.name for p in tmp_path.iterdir()) == []


@pytest.mark.skipif(sys.platform != "darwin", reason="darwin mount classification")
def test_v5_darwin_classification_unchanged_and_ignores_linux_allowlist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ledger_mod, "_LINUX_LOCAL_FS_MAGIC", frozenset())
    assert ledger_filesystem_is_proven_local_v1(tmp_path) is True
    assert ledger_filesystem_is_proven_local_v1("/dev") is False


# --------------------------------------------------------------------------- V3 orphan recovery

_CHILD_CLAIMER = r"""
import hashlib, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from src.ops.full_core_live_path_composition_root_v1.current_productive_global_venue_effect_authority_ledger_v1 import (
    ACCOUNT_SCOPE_K1, ENVIRONMENT_LIVE_EEA, RISK_CLASS_NEW_RISK,
    GlobalVenueEffectAuthorityLedgerV1, GlobalVenueEffectIdentityV1,
)
root, cl_ord_id, mode = Path(sys.argv[2]), sys.argv[3], sys.argv[4]
identity = GlobalVenueEffectIdentityV1(
    owner_go_token="GO-V2-" + cl_ord_id,
    account_scope=ACCOUNT_SCOPE_K1,
    environment=ENVIRONMENT_LIVE_EEA,
    permit_id="eep-" + cl_ord_id,
    envelope_id="env-" + cl_ord_id,
    envelope_digest=hashlib.sha256(cl_ord_id.encode("utf-8")).hexdigest(),
    client_order_id=cl_ord_id,
    risk_class=RISK_CLASS_NEW_RISK,
    baseline_origin_main_sha="1" * 40,
)
ledger = GlobalVenueEffectAuthorityLedgerV1(root=root)
claim = ledger.claim_v1(identity)
if mode == "sent":
    ledger.mark_sent_initiated_v1(
        claim.claim_id, permit_id=identity.permit_id, envelope_digest=identity.envelope_digest
    )
print(claim.claim_id, flush=True)
if mode == "hold":
    sys.stdin.read()
"""


def _spawn_child_claimer(root: Path, cl_ord_id: str, mode: str) -> tuple[subprocess.Popen, str]:
    proc = subprocess.Popen(
        [sys.executable, "-c", _CHILD_CLAIMER, str(REPO_ROOT), str(root), cl_ord_id, mode],
        cwd=str(root.parent),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    claim_id = proc.stdout.readline().strip()
    assert claim_id, proc.stderr.read() if proc.poll() is not None else "no claim id"
    return proc, claim_id


def _finished_child_claim(root: Path, cl_ord_id: str, mode: str = "exit") -> str:
    proc, claim_id = _spawn_child_claimer(root, cl_ord_id, mode)
    _, err = proc.communicate(input="", timeout=60)
    assert proc.returncode == 0, err
    return claim_id


def _rewrite_claim(ledger: GlobalVenueEffectAuthorityLedgerV1, claim_id: str, **changes) -> None:
    path = ledger._claim_path(claim_id)
    record = json.loads(path.read_text(encoding="utf-8"))
    for key, value in changes.items():
        if value is None:
            record.pop(key, None)
        else:
            record[key] = value
    path.write_text(json.dumps(record), encoding="utf-8")


def test_v3_dead_owner_same_boot_unsent_claim_settles_and_stays_single_use(
    tmp_path: Path,
) -> None:
    root = tmp_path / "ledger"
    orphan_id = _finished_child_claim(root, "pt-v3-orphan")
    ledger = GlobalVenueEffectAuthorityLedgerV1(root=root)
    [view] = ledger.classify_unresolved_claims_v1()
    assert view["proven_not_sent"] is True
    assert view["safe_to_retry"] is False
    assert view["authorization_reusable"] is False

    risk_reducing = ledger.claim_v1(
        _identity(client_order_id="pt-v3-reduce", risk_class=RISK_CLASS_RISK_REDUCING)
    )
    assert ledger.load_claim_v1(orphan_id)["state"] == STATE_CLAIMED
    ledger.abandon_unsent_claim_v1(risk_reducing.claim_id, reason="TEST_RELEASE")

    fresh = ledger.claim_v1(_identity(client_order_id="pt-v3-next"))
    settled = ledger.load_claim_v1(orphan_id)
    assert settled["state"] == STATE_ABORTED_BEFORE_TRANSPORT
    assert settled["history"][-1]["detail"] == ledger_mod.DETAIL_PROVEN_NOT_SENT
    with pytest.raises(GlobalVenueEffectReplayDeniedError):
        ledger.claim_v1(_identity(client_order_id="pt-v3-orphan"))
    assert [c["claim_id"] for c in ledger.unresolved_claims_v1()] == [fresh.claim_id]


@pytest.mark.parametrize(
    "case",
    [
        "other_boot_session",
        "unknown_boot_session",
        "record_without_boot_session",
        "record_foreign_host",
        "record_non_int_pid",
        "sent_initiated",
        "forged_claimed_after_sent_initiated",
    ],
)
def test_v3_orphan_not_proven_unsent_keeps_blocking_new_risk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    root = tmp_path / "ledger"
    mode = "sent" if "sent_initiated" in case else "exit"
    orphan_id = _finished_child_claim(root, "pt-v3-orphan", mode)
    ledger = GlobalVenueEffectAuthorityLedgerV1(root=root)
    if case == "other_boot_session":
        monkeypatch.setattr(ledger_mod, "_boot_session_identity_v1", lambda: "f" * 64)
    elif case == "unknown_boot_session":
        monkeypatch.setattr(ledger_mod, "_boot_session_identity_v1", lambda: "")
    elif case == "record_without_boot_session":
        _rewrite_claim(ledger, orphan_id, boot_session_sha256=None)
    elif case == "record_foreign_host":
        _rewrite_claim(ledger, orphan_id, host_identity_sha256="0" * 64)
    elif case == "record_non_int_pid":
        _rewrite_claim(ledger, orphan_id, process_id="999999")
    elif case == "forged_claimed_after_sent_initiated":
        _rewrite_claim(ledger, orphan_id, state=STATE_CLAIMED)
    before = ledger.load_claim_v1(orphan_id)
    [view] = ledger.classify_unresolved_claims_v1()
    assert view["proven_not_sent"] is False
    with pytest.raises(GlobalVenueEffectLedgerError, match="BLOCKS_NEW_RISK"):
        ledger.claim_v1(_identity(client_order_id="pt-v3-next"))
    assert ledger.load_claim_v1(orphan_id) == before


def test_v3_orphan_with_live_owner_process_is_not_settled_until_it_exits(tmp_path: Path) -> None:
    root = tmp_path / "ledger"
    proc, orphan_id = _spawn_child_claimer(root, "pt-v3-held", "hold")
    try:
        ledger = GlobalVenueEffectAuthorityLedgerV1(root=root)
        with pytest.raises(GlobalVenueEffectLedgerError, match="BLOCKS_NEW_RISK"):
            ledger.claim_v1(_identity(client_order_id="pt-v3-next"))
        assert ledger.load_claim_v1(orphan_id)["state"] == STATE_CLAIMED
    finally:
        proc.communicate(input="", timeout=60)
    assert proc.returncode == 0
    ledger.claim_v1(_identity(client_order_id="pt-v3-next"))
    assert ledger.load_claim_v1(orphan_id)["state"] == STATE_ABORTED_BEFORE_TRANSPORT


def test_v3_same_process_unsent_claim_is_never_self_settled(tmp_path: Path) -> None:
    first = _ledger(tmp_path)
    claim = first.claim_v1(_identity())
    restarted_instance = _ledger(tmp_path)
    with pytest.raises(GlobalVenueEffectLedgerError, match="BLOCKS_NEW_RISK"):
        restarted_instance.claim_v1(_identity(client_order_id="pt-v3-next"))
    assert first.load_claim_v1(claim.claim_id)["state"] == STATE_CLAIMED


def test_v3_settled_claim_can_never_reach_transport_even_if_owner_survived(
    tmp_path: Path,
) -> None:
    owner = _ledger(tmp_path)
    claim = owner.claim_v1(_identity())
    dead_pid_holder = _finished_child_claim(tmp_path / "pid_source", "pt-v3-pid")
    dead_pid = GlobalVenueEffectAuthorityLedgerV1(root=tmp_path / "pid_source").load_claim_v1(
        dead_pid_holder
    )["process_id"]
    other = _ledger(tmp_path)
    _rewrite_claim(other, claim.claim_id, process_id=dead_pid)
    other.claim_v1(_identity(client_order_id="pt-v3-next"))
    assert other.load_claim_v1(claim.claim_id)["state"] == STATE_ABORTED_BEFORE_TRANSPORT
    with pytest.raises(GlobalVenueEffectLedgerError, match="INVALID_TRANSITION"):
        owner.mark_sent_initiated_v1(
            claim.claim_id,
            permit_id=claim.identity.permit_id,
            envelope_digest=claim.identity.envelope_digest,
        )
    with pytest.raises(GlobalVenueEffectLedgerError):
        owner.assert_sent_initiated_for_transport_v1(
            claim.claim_id,
            permit_id=claim.identity.permit_id,
            envelope_digest=claim.identity.envelope_digest,
        )


@pytest.mark.parametrize("error", [PermissionError, OSError])
def test_v3_unprovable_owner_liveness_counts_as_alive(
    monkeypatch: pytest.MonkeyPatch, error: type[OSError]
) -> None:
    def _kill(pid: int, sig: int) -> None:
        raise error("probe")

    monkeypatch.setattr(ledger_mod.os, "kill", _kill)
    assert ledger_mod._process_gone_v1(424242) is False
    for pid in (None, "1", True, 0, -1):
        assert ledger_mod._process_gone_v1(pid) is False
