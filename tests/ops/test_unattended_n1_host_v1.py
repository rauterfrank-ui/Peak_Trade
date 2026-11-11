"""Physical N1 host process death, durable total bounds, fresh governed restart."""

from dataclasses import replace
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

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
        stop = writer.provision_v1(
            scope=FilegateRecoveryScopeV1(
                "synthetic",
                "SHADOW",
                str(tmp_path / "private_store"),
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
    with (tmp_path / "stderr").open("w") as stderr:
        child = subprocess.Popen(
            [*command, "during" if phase == "during" else "before"],
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

    def restart():
        restart_phase = (
            phase if phase in {"kill-during-admission", "reactivated-during-admission"} else "after"
        )
        if phase.startswith("managed-"):
            restart_phase = "after-managed-boot"
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
        assert result["status"] == "RECOVERY_CHECKPOINT_REQUIRED"
        assert result["checkpoint_blocker"] == blocker
        assert result["attempts"] == 1
        assert cursor.read_bytes() == old_cursor
        assert not (tmp_path / "controller/attempts/2").exists()
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
        before = (
            tmp_path / "controller/attempts/1/governed_continuous_cycle_run_ledger_v1.json"
        ).read_bytes()
        repeated = restart()
        assert repeated.returncode == 0, repeated.stderr
        assert json.loads(repeated.stdout.splitlines()[-1])["attempts"] == 2
        assert (
            tmp_path / "controller/attempts/1/governed_continuous_cycle_run_ledger_v1.json"
        ).read_bytes() == before


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
    from dataclasses import asdict
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
