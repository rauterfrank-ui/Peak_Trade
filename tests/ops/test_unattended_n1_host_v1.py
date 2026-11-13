"""Physical N1 host process death, durable total bounds, fresh governed restart."""

from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.unattended_v1 import (
    UnattendedHostBoundsV1,
    run_unattended_n1_host_v1,
)
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.state import KillSwitchState

REPO = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("phase", "blocker"),
    [
        ("before", None),
        ("during", "HOST_RESTART_ORIGINAL_WAIT_UNPROVEN"),
        ("other-boot", "HOST_RESTART_PROCESS_OR_BOOT_UNPROVEN"),
        ("managed-other-boot", None),
        ("managed-other-boot-no-anchor", "HOST_RESTART_PROCESS_OR_BOOT_UNPROVEN"),
        ("managed-hold-publish", None),
        ("managed-hold-s5-changed", "HOST_RESTART_ORIGINAL_WAIT_UNPROVEN"),
        ("managed-restore-wait", "HOST_RESTART_ORIGINAL_WAIT_UNPROVEN"),
        ("managed-partial-s5", "HOST_RESTART_ORIGINAL_WAIT_UNPROVEN"),
        ("managed-sealed-partial-s5", None),
        ("managed-sealed-partial-s5-changed", "HOST_RESTART_ORIGINAL_WAIT_UNPROVEN"),
        ("managed-sealed-partial-s5-kill", "HOST_RESTART_FILEGATE_BLOCKED"),
        ("managed-orderly-stop", None),
        ("managed-orderly-stop-unproven", "HOST_RESTART_FILEGATE_BLOCKED"),
        ("managed-joint-rollback", "HOST_RESTART_FILEGATE_BLOCKED"),
        ("pid-present", "HOST_RESTART_PREVIOUS_PID_PRESENT"),
        ("foreign-start", "HOST_RESTART_ORIGINAL_WAIT_UNPROVEN"),
        ("foreign-checkpoint", "HOST_RESTART_CHECKPOINT_SCOPE_CHANGED"),
        ("changed-cursor", "HOST_RESTART_ORIGINAL_WAIT_UNPROVEN"),
        ("missing-attempt", "HOST_RESTART_PREVIOUS_ATTEMPT_UNPROVEN"),
        ("filegate", "HOST_RESTART_FILEGATE_BLOCKED"),
        ("foreign-filegate", "HOST_RESTART_FILEGATE_SCOPE_CHANGED"),
        ("kill-during-admission", None),
        ("reactivated-during-admission", None),
    ],
)
def test_unattended_actual_n1_restart_after_sigkill_obeys_checkpoint_and_total_budget(
    tmp_path, phase, blocker
):
    from tests.ops._host_private_rest_fixture_v1 import initialize_synthetic_host_budget_v1
    from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
        _bound_lane_1,
    )

    # One explicit temporary bootstrap before the first process. Restarted
    # workers must recover this same store; they cannot create their own.
    initialize_synthetic_host_budget_v1(tmp_path / "private_store", _bound_lane_1())
    filegate = StatePersistence(str(tmp_path / "filegate.json"))
    env = {**os.environ, "PEAK_KILL_SWITCH_STATE_PATH": str(filegate.state_file)}
    env.pop("PEAK_KILL_SWITCH", None)
    if phase.startswith("managed-"):
        from nacl.signing import SigningKey

        from src.ops.filegate_recovery_authority_v1 import (
            FilegateRecoveryScopeV1,
            attest_filegate_owner_evidence_v1,
        )
        from src.ops.managed_filegate_v1 import ROOT_ENV, ManagedFilegateV1

        separate = tmp_path.resolve().with_name(tmp_path.name + "-independent")
        separate.mkdir(mode=0o700)
        writer = ManagedFilegateV1(state_path=filegate.state_file, root=separate)
        issuer = SigningKey.generate()
        keys = {role: SigningKey.generate() for role in ("CAUSE", "ACCOUNT", "HOST")}
        orderly = phase.startswith("managed-orderly-stop")
        if orderly:
            (tmp_path / "fixture-keys.json").write_text(
                json.dumps(
                    {role: bytes(key).hex() for role, key in {"issuer": issuer, **keys}.items()}
                )
            )
        stop = writer.provision_v1(
            scope=FilegateRecoveryScopeV1(
                "synthetic",
                "SHADOW",
                str(
                    tmp_path / "private_store" / "portfolio_budget_host_v1"
                    if orderly
                    else tmp_path / "private_store"
                ),
                (_bound_lane_1().venue_native_id,),
                "a" * 64,
            ),
            issuer_public_key=bytes(issuer.verify_key),
            owner_public_keys={role: bytes(key.verify_key) for role, key in keys.items()},
            recoverable_causes={"R03"},
        )
        now = time.time()
        evidence = {
            role: attest_filegate_owner_evidence_v1(
                role=role,
                stop=stop,
                evidence_sha256="b" * 64,
                observed_at=now,
                expires_at=now + 5,
                key=key,
            )
            for role, key in keys.items()
        }
        writer.release_v1(
            release=writer.issue_release_v1(evidence=evidence, issuer_key=issuer),
            evidence=evidence,
        )
        env[ROOT_ENV] = str(separate)
    else:
        filegate.save(KillSwitchState.ACTIVE)
    if env.get("GITHUB_ACTIONS") == "true":
        env.update(PT_RUNTIME_MODE="provisioned", PT_PROVISIONED_PYTHON=sys.executable)
    command = [str(REPO / "scripts/pt"), "-m", "tests.ops._unattended_n1_worker_v1", str(tmp_path)]
    if phase.startswith("managed-orderly-stop"):
        completed = subprocess.run(
            [*command, phase], cwd=REPO, env=env, capture_output=True, text=True, timeout=25
        )
        assert completed.returncode == 0, completed.stderr
        result = json.loads(completed.stdout.splitlines()[-1])
        before = json.loads((tmp_path / "cursor-before-filegate-loss.json").read_bytes())
        cursor = next((tmp_path / "lane_state").rglob(CURSOR_FILENAME))
        after = json.loads(cursor.read_bytes())
        proof = tmp_path / "retired-host-proof.json"
        if blocker is not None:
            assert result["status"] == "STOPPED" and result["checkpoint_blocker"] == blocker
            assert result["attempts"] == 1
            assert not proof.exists() and after == before
            assert writer.inspect_stop_v1()["causes"] == ["R03"]
        else:
            assert result["status"] == "COMPLETED"
            assert result["attempts"] == result["cycles_used"] == 2
            assert result["last_fault_observation"]["status"] == "SAFETY_RELEASE_CONFIRMED"
            assert json.loads(proof.read_bytes())["body"]["stop"]["causes"] == ["R03"]
            assert writer.read_v1()["state"] == "ACTIVE"
            assert after["trading_epoch"] == before["trading_epoch"] + 1
        return
    with (tmp_path / "stderr").open("w") as stderr:
        start_phase = {
            "during": "during",
            "managed-hold-publish": "managed-hold-publish",
            "managed-hold-s5-changed": "managed-hold-publish",
            "managed-restore-wait": "managed-restore-wait",
            "managed-partial-s5": "managed-partial-s5",
            "managed-sealed-partial-s5": "managed-sealed-partial-s5",
            "managed-sealed-partial-s5-changed": "managed-sealed-partial-s5",
            "managed-sealed-partial-s5-kill": "managed-sealed-partial-s5",
            "managed-joint-rollback": "managed-joint-rollback",
        }.get(phase, "before")
        child = subprocess.Popen(
            [*command, start_phase],
            cwd=REPO,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=stderr,
        )
        try:
            deadline = time.monotonic() + 25
            while (
                not (tmp_path / "checkpoint.json").exists()
                and child.poll() is None
                and time.monotonic() < deadline
            ):
                time.sleep(0.05)
            assert (tmp_path / "checkpoint.json").exists(), (tmp_path / "stderr").read_text()
            checkpoint = json.loads((tmp_path / "checkpoint.json").read_text())
            cursor = Path(checkpoint["cursor"])
            old_cursor = cursor.read_bytes()
            child.send_signal(signal.SIGKILL)
            child.wait(timeout=5)
        finally:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=5)
    receipt = tmp_path / "controller" / "host_restart_state_v1.json"
    state = json.loads(receipt.read_bytes())
    prior = state["previous"]
    assert prior["process_identity"]["pid"] == checkpoint["pid"] == child.pid
    assert prior["process_identity"]["process_start_identity"]
    assert prior["boot_identity"]
    if phase == "other-boot":
        prior["boot_identity"] = "00000000-0000-0000-0000-000000000001"
        receipt.write_text(json.dumps(state))
    elif phase == "pid-present":
        prior["process_identity"]["pid"] = os.getpid()
        receipt.write_text(json.dumps(state))
    elif phase == "foreign-start":
        prior["process_identity"]["process_start_identity"] = "foreign start identity"
        receipt.write_text(json.dumps(state))
    elif phase == "foreign-checkpoint":
        prior["evidence_root"] = str(tmp_path / "foreign")
        receipt.write_text(json.dumps(state))
    elif phase == "missing-attempt":
        state["previous"] = None
        receipt.write_text(json.dumps(state))
    elif phase == "changed-cursor":
        cursor.write_bytes(old_cursor + b"\n")
        old_cursor = cursor.read_bytes()
    elif phase == "filegate":
        filegate.save(KillSwitchState.KILLED, trigger_reason="fixture emergency")
    elif phase == "foreign-filegate":
        foreign = StatePersistence(str(tmp_path / "foreign-filegate.json"))
        foreign.save(KillSwitchState.ACTIVE)
        env["PEAK_KILL_SWITCH_STATE_PATH"] = str(foreign.state_file)
    elif phase == "managed-other-boot-no-anchor":
        from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
            LOCK_NAME,
        )

        writer.set_host_checkpoint_v1(
            lock_path=Path(prior["lock_root"]) / LOCK_NAME,
            checkpoint=None,
        )
    elif phase in {"managed-hold-publish", "managed-hold-s5-changed"}:
        evidence = Path(prior["evidence_root"])
        ledger = evidence / "governed_continuous_cycle_run_ledger_v1.json"
        assert json.loads(ledger.read_bytes())["reason_code"] == "S5_CYCLE_STARTING"
        s5 = (
            evidence
            / "cycles"
            / checkpoint["consume_id"]
            / "s5"
            / "governed_cycle_orchestrator_ledger_v1.json"
        )
        assert json.loads(s5.read_bytes())["state"] == "COMPLETED"
        if phase == "managed-hold-s5-changed":
            s5.write_bytes(s5.read_bytes() + b"\n")
    elif phase in {"managed-restore-wait", "managed-joint-rollback"}:
        ledger = Path(prior["evidence_root"]) / "governed_continuous_cycle_run_ledger_v1.json"
        assert json.loads(ledger.read_bytes())["reason_code"] == "S5_CYCLE_STARTING"
        ledger.write_bytes((tmp_path / "earlier-wait.json").read_bytes())
        if phase == "managed-joint-rollback":
            newer_stop = writer.kill_v1(cause="R09", reason="fixture kill after later S5")
            earlier_cursor = (tmp_path / "earlier-cursor.json").read_bytes()
            assert earlier_cursor != old_cursor
            assert (
                json.loads(earlier_cursor)["trading_epoch"]
                < json.loads(old_cursor)["trading_epoch"]
            )
            earlier_filegate = (tmp_path / "earlier-filegate.json").read_bytes()
            assert json.loads(earlier_filegate)["state"] == "ACTIVE"
            filegate.state_file.write_bytes(earlier_filegate)
            cursor.write_bytes(earlier_cursor)
            old_cursor = earlier_cursor
    elif phase == "managed-partial-s5":
        earlier = json.loads((tmp_path / "before-partial-s5-cursor.json").read_bytes())
        assert json.loads(old_cursor)["trading_epoch"] == earlier["trading_epoch"] + 1
        s5_ledger = Path(checkpoint["s5_ledger"])
        partial_s5 = s5_ledger.read_bytes()
        assert json.loads(partial_s5)["state"] == "IN_PROGRESS"
    elif phase.startswith("managed-sealed-partial-s5"):
        from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
            LOCK_NAME,
        )

        s5_ledger = Path(checkpoint["s5_ledger"])
        assert json.loads(s5_ledger.read_bytes())["state"] == "IN_PROGRESS"
        anchor = writer.read_host_checkpoint_v1(lock_path=Path(prior["lock_root"]) / LOCK_NAME)
        assert anchor["s5_terminal_ledger"]["terminal_class"] == "MARKET_STATE_REQUIRED"
        assert anchor["s5_terminal_ledger"]["portfolio_reservation_id"] == ""
        assert anchor["wait_ledger"]["consumed_instance_ids"] == [s5_ledger.parents[1].name]
        if phase.endswith("-changed"):
            s5_ledger.write_bytes(s5_ledger.read_bytes() + b"\n")
        if phase.endswith("-kill"):
            writer.kill_v1(cause="R09", reason="fixture kill after sealed S5 HOLD")
        partial_s5 = s5_ledger.read_bytes()

    def restart():
        restart_phase = (
            phase if phase in {"kill-during-admission", "reactivated-during-admission"} else "after"
        )
        if phase in {"managed-other-boot", "managed-other-boot-no-anchor", "managed-hold-publish"}:
            restart_phase = "after-managed-boot"
        if phase in {"managed-restore-wait", "managed-partial-s5"}:
            restart_phase = "after-managed-monitor"
        if phase == "managed-joint-rollback":
            restart_phase = "after-managed-joint-rollback"
        return subprocess.run(
            [*command, restart_phase],
            cwd=REPO,
            env=env,
            capture_output=True,
            text=True,
            timeout=25,
        )

    completed = restart()
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout.splitlines()[-1])
    if blocker is not None:
        assert result["status"] == (
            "STOPPED"
            if phase in {"managed-restore-wait", "managed-partial-s5", "managed-joint-rollback"}
            else "RECOVERY_CHECKPOINT_REQUIRED"
        )
        assert result["checkpoint_blocker"] == blocker
        assert result["attempts"] == 1
        assert cursor.read_bytes() == old_cursor
        assert not (tmp_path / "controller/attempts/2").exists()
        if phase == "managed-partial-s5" or phase.startswith("managed-sealed-partial-s5"):
            assert s5_ledger.read_bytes() == partial_s5
        if phase == "managed-joint-rollback":
            stop = writer.inspect_stop_v1()
            assert stop["causes"] == ["R03", "R09"]
            assert stop["generation"] > newer_stop["generation"]
            assert writer.read_v1()["state"] == "KILLED"
            assert ledger.read_bytes() == (tmp_path / "earlier-wait.json").read_bytes()
        if phase == "filegate":
            assert filegate.load()["state"] == "KILLED"
            filegate.save(KillSwitchState.ACTIVE)
            completed = restart()
            assert completed.returncode == 0, completed.stderr
            resumed = json.loads(completed.stdout.splitlines()[-1])
            assert resumed["status"] == "COMPLETED"
            assert resumed["attempts"] == resumed["cycles_used"] == 2
    elif phase in {"kill-during-admission", "reactivated-during-admission"}:
        assert result["status"] == "GOVERNED_RUNTIME_STOPPED"
        assert result["attempts"] == 2 and result["cycles_used"] == 1
        assert filegate.load()["state"] == (
            "KILLED" if phase == "kill-during-admission" else "ACTIVE"
        )
        assert cursor.read_bytes() == old_cursor
    else:
        assert result["status"] == "COMPLETED"
        assert result["attempts"] == 2
        assert result["cycles_used"] == 2
        assert (
            json.loads(cursor.read_bytes())["trading_epoch"]
            == json.loads(old_cursor)["trading_epoch"] + 1
        )
        if phase == "managed-sealed-partial-s5":
            assert s5_ledger.read_bytes() == partial_s5
            assert len(list(s5_ledger.parents[2].iterdir())) == 1
        before = (
            tmp_path / "controller/attempts/1/governed_continuous_cycle_run_ledger_v1.json"
        ).read_bytes()
        repeated = restart()
        assert repeated.returncode == 0, repeated.stderr
        assert json.loads(repeated.stdout.splitlines()[-1])["attempts"] == 2
        assert (
            tmp_path / "controller/attempts/1/governed_continuous_cycle_run_ledger_v1.json"
        ).read_bytes() == before


def test_unattended_host_does_not_complete_on_flat_with_pending_booking(tmp_path, monkeypatch):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_l10_close_reconciliation_v1 import (
        AuthenticatedL10CloseReadbackV1,
    )
    from src.ops.n1_standing_pre_external_runtime_supervisor_v1 import (
        StandingSupervisorRunResultV1,
        unattended_v1,
    )
    from src.ops.n1_standing_pre_external_runtime_supervisor_v1.trace_v1 import (
        StandingSupervisorTraceV1,
    )
    from tests.ops._n1_standing_supervisor_offline_inject_harness_v1 import (
        OWNER_GO_BASELINE_SHA,
        supervisor_config_from_roots,
    )
    from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
        _bound_lane_1,
        _continuous_auth,
    )

    bound = _bound_lane_1()

    def request_factory(_, evidence):
        return dict(
            config=supervisor_config_from_roots(
                public_store=tmp_path / "public",
                private_store=tmp_path / "private",
                lane_state=tmp_path / "lane",
                evidence_root=evidence,
                lock_root=tmp_path / "lock",
            ),
            origin_main_sha=OWNER_GO_BASELINE_SHA,
            bound=bound,
            authorization=_continuous_auth(native_id=bound.venue_native_id),
        )

    readback = AuthenticatedL10CloseReadbackV1(
        "CLOSE_FLAT_CONFIRMED", "a" * 64, ("L10_CLOSE_NET_BOOKING_PENDING",)
    )
    result = StandingSupervisorRunResultV1(
        ok=True,
        run_id="close-readback",
        trace=StandingSupervisorTraceV1("close-readback", terminal_disposition=readback.status),
        recovery=None,
        policy_result=None,
        owner_go_consumed=False,
        authority_invariants_ok=True,
        close_readback=readback,
    )
    monkeypatch.setattr(unattended_v1, "_filegate_revision", lambda path: "fixture-active")
    monkeypatch.setattr(
        unattended_v1, "run_n1_standing_pre_external_supervisor_v1", lambda **kwargs: result
    )
    bounds = UnattendedHostBoundsV1(
        "flat-close",
        OWNER_GO_BASELINE_SHA,
        unattended_v1.unattended_request_digest_v1(request_factory(1, tmp_path / "unused")),
        120,
        1,
        30,
        1,
    )
    controller = tmp_path / "controller"
    stopped = run_unattended_n1_host_v1(
        bounds=bounds, state_root=controller, request_factory=request_factory, clock=lambda: 100
    )
    assert stopped["status"] == "GOVERNED_RUNTIME_STOPPED"
    assert stopped["close_readback_status"] == "CLOSE_FLAT_CONFIRMED"
    assert stopped["close_booking_pending"] is True
    assert stopped["cycles_used"] == 0
    assert json.loads((controller / "host_restart_state_v1.json").read_bytes()) == stopped


def test_expired_stopped_or_lost_receipt_never_calls_runtime_factory(tmp_path):
    bounds = UnattendedHostBoundsV1("test", "revision", "config", 90, 2, 30, 1)

    def forbidden(*_):
        raise AssertionError("No source, credentials or runtime may be opened")

    result = run_unattended_n1_host_v1(
        bounds=bounds, state_root=tmp_path / "expired", request_factory=forbidden, clock=lambda: 100
    )
    assert result["status"] == "BOUNDS_EXHAUSTED"
    with pytest.raises(ValueError, match="REGISTERED_STATE_MISSING"):
        run_unattended_n1_host_v1(
            bounds=bounds, state_root=tmp_path, request_factory=forbidden, clock=lambda: 100
        )
    with pytest.raises(ValueError, match="RECEIPT_UNPROVEN"):
        run_unattended_n1_host_v1(
            bounds=replace(bounds, runtime_config_digest="changed"),
            state_root=tmp_path / "expired",
            request_factory=forbidden,
            clock=lambda: 100,
        )


def test_launch_agent_preparation_has_no_activation_and_rejects_test_source_factory(tmp_path):
    import plistlib
    from src.ops.n1_standing_pre_external_runtime_supervisor_v1.unattended_v1 import host_service_v1

    bounds = UnattendedHostBoundsV1("test", "revision", "config", time.time() + 60, 1, 30, 1)
    manifest = {
        "schema": "n1_unattended_host_service.v1",
        "bounds": asdict(bounds),
        "state_root": str(tmp_path / "controller"),
        "repository_root": str(REPO),
        "runtime_factory": "src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1:run_n1_standing_pre_external_supervisor_v1",
        "runtime_request_config": {},
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    result = host_service_v1(manifest_path=path, action="validate")
    assert result["runtime_ports_validated"] is False
    output = tmp_path / "host.plist"
    assert (
        host_service_v1(manifest_path=path, action="prepare", output_path=output)[
            "service_activated"
        ]
        is False
    )
    plist = plistlib.loads(output.read_bytes())
    assert plist["KeepAlive"] == {"SuccessfulExit": False}
    assert plist["RunAtLoad"] is True and plist["ThrottleInterval"] == 60
    assert "host-service" in plist["ProgramArguments"]
    assert not (tmp_path / "controller").exists()
    with pytest.raises(FileExistsError):
        host_service_v1(manifest_path=path, action="prepare", output_path=output)
    manifest["fault_recovery"] = {
        "factory": "src.ops.managed_fault_recovery_v1:build_standing_managed_fault_recovery_v1",
        "filegate_state_path": str(tmp_path / "filegate.json"),
        "authority_root": str(tmp_path / "authority"),
        "config": {},
    }
    path.write_text(json.dumps(manifest))
    managed_output = tmp_path / "managed-host.plist"
    prepared = host_service_v1(manifest_path=path, action="prepare", output_path=managed_output)
    assert prepared["service_activated"] is False
    managed_plist = plistlib.loads(managed_output.read_bytes())
    assert managed_plist["EnvironmentVariables"] == {
        "PEAK_KILL_SWITCH_STATE_PATH": str(tmp_path / "filegate.json"),
        "PEAK_FILEGATE_AUTHORITY_ROOT": str(tmp_path / "authority"),
    }
    manifest["runtime_factory"] = "tests.ops._unattended_n1_worker_v1:main"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="SOURCE_FACTORY_REQUIRED"):
        host_service_v1(manifest_path=path, action="validate")


def test_canonical_host_service_observes_after_expiry_and_process_death(tmp_path):
    from nacl.signing import SigningKey

    from src.ops.filegate_recovery_authority_v1 import FilegateRecoveryScopeV1
    from src.ops.managed_filegate_v1 import ROOT_ENV, ManagedFilegateV1

    authority = tmp_path.resolve().with_name(tmp_path.name + "-authority")
    authority.mkdir(mode=0o700)
    proof_root = tmp_path / "proofs"
    proof_root.mkdir(mode=0o700)
    filegate = tmp_path / "filegate.json"
    issuer = SigningKey.generate()
    seed_path = proof_root / "issuer.seed"
    seed_path.write_bytes(bytes(issuer))
    seed_path.chmod(0o600)
    cause_key = SigningKey.generate()
    cause_seed = proof_root / "cause.seed"
    cause_seed.write_bytes(bytes(cause_key))
    cause_seed.chmod(0o600)
    writer = ManagedFilegateV1(state_path=filegate, root=authority)
    integrity_stop = writer.provision_v1(
        scope=FilegateRecoveryScopeV1(
            "fixture-account", "SHADOW", "fixture-host", ("FUTURES",), "a" * 64
        ),
        issuer_public_key=bytes(issuer.verify_key),
        owner_public_keys={
            "CAUSE": bytes(cause_key.verify_key),
            **{role: bytes(SigningKey.generate().verify_key) for role in ("ACCOUNT", "HOST")},
        },
        recoverable_causes={"R03"},
    )
    bounds = UnattendedHostBoundsV1("fixture-host", "revision", "config", time.time() - 1, 1, 30, 1)
    state_root = tmp_path / "controller"
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": "n1_unattended_host_service.v1",
                "bounds": asdict(bounds),
                "state_root": str(state_root),
                "repository_root": str(REPO),
                # This symbol cannot supply the factory arguments. Expiry must
                # stop the service before it tries to open any runtime ports.
                "runtime_factory": "src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1:run_n1_standing_pre_external_supervisor_v1",
                "runtime_request_config": {},
                "fault_recovery": {
                    "factory": "src.ops.managed_fault_recovery_v1:build_standing_managed_fault_recovery_v1",
                    "filegate_state_path": str(filegate),
                    "authority_root": str(authority),
                    "config": {
                        "proof_root": str(proof_root),
                        "issuer_seed_path": str(seed_path),
                        "interval_seconds": 1,
                    },
                },
            }
        )
    )
    env = {**os.environ}
    for key in (ROOT_ENV, "PEAK_KILL_SWITCH_STATE_PATH", "PEAK_KILL_SWITCH"):
        env.pop(key, None)
    if env.get("GITHUB_ACTIONS") == "true":
        env.update(PT_RUNTIME_MODE="provisioned", PT_PROVISIONED_PYTHON=sys.executable)
    command = [
        str(REPO / "scripts/pt"),
        str(REPO / "scripts/ops/peak_trade_runtime.py"),
        "--repository-root",
        str(REPO),
        "host-service",
        "run",
        "--manifest",
        str(manifest),
    ]

    def owner_poll(owner_seed):
        owner_command = command.copy()
        owner_command[owner_command.index("run")] = "owner-poll"
        result = subprocess.run(
            [*owner_command, "--owner-role", "R03", "--owner-seed-path", str(owner_seed)],
            cwd=REPO,
            env=env,
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
        return json.loads(result.stdout[result.stdout.index("{") :])

    result = owner_poll(cause_seed)
    assert result["result"] == {
        "status": "OWNER_PROOF_PUBLISHED",
        "generation": integrity_stop["generation"],
    }
    assert result["external_effect_authorized"] is False
    proof_path = proof_root / (
        f"{integrity_stop['generation']}-{integrity_stop['stop_id']}-CAUSE-R03.json"
    )
    proof = proof_path.read_bytes()
    assert json.loads(proof)["body"]["stop"] == integrity_stop
    assert owner_poll(seed_path)["result"] == {
        "status": "OWNER_OBSERVATION_BLOCKED",
        "reason": "FILEGATE_SIGNATURE_UNPROVEN",
    }
    assert proof_path.read_bytes() == proof
    assert writer.inspect_stop_v1() == integrity_stop
    stop = writer.kill_v1(cause="R09", reason="fixture persistent emergency")
    observation = state_root / "stopped_fault_observation_v1.json"
    previous_write = None
    for restart in (False, True):
        with subprocess.Popen(
            command, cwd=REPO, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ) as child:
            try:
                deadline = time.monotonic() + 20
                while child.poll() is None and time.monotonic() < deadline:
                    if observation.exists() and observation.stat().st_mtime_ns != previous_write:
                        break
                    time.sleep(0.05)
                assert child.poll() is None, child.communicate()
                assert observation.exists() and observation.stat().st_mtime_ns != previous_write
                previous_write = observation.stat().st_mtime_ns
                observed = json.loads(observation.read_bytes())
                assert observed["status"] == "BLOCKED_OBSERVING"
                assert observed["stop"] == stop
                if restart:
                    (state_root / "STOP").touch()
                    stdout, stderr = child.communicate(timeout=10)
                    assert child.returncode == 0, (stdout, stderr)
                else:
                    child.send_signal(signal.SIGKILL)
                    assert child.wait(timeout=5) == -signal.SIGKILL
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait(timeout=5)
    assert writer.inspect_stop_v1() == stop
    assert not (state_root / "attempts").exists()
