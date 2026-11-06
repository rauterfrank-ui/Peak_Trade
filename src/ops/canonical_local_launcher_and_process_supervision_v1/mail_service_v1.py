"""Canonical operator control for the auxiliary macOS recovery mail service."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import plistlib
import re
import subprocess
import sys

from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.runtime_recovery_email_v1 import (
    default_recovery_email_config_path_v1,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.evidence_v1 import write_json

LABEL = "de.peaktrade.runtime-recovery-mail.v1"


def mail_service_v1(repository_root: Path, action: str) -> dict:
    if sys.platform != "darwin":
        raise ValueError("MAIL_SERVICE_REQUIRES_MACOS")
    repo = Path(repository_root).resolve()
    state = Path.home() / ".local/state/peak_trade/mail_worker_v1"
    config = Path.home() / ".config/peak_trade/runtime_mail_worker_v1.json"
    plist = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"
    domain = f"gui/{os.getuid()}"
    target = f"{domain}/{LABEL}"

    def launchctl(*args):
        return subprocess.run(["/bin/launchctl", *args], capture_output=True, timeout=20)

    if action == "install":
        if plist.exists() or config.exists():
            raise ValueError("MAIL_SERVICE_ALREADY_CONFIGURED_USE_STATUS")
        mail_config = default_recovery_email_config_path_v1()
        if not mail_config.is_file() or not (repo / "scripts/pt").is_file():
            raise ValueError("MAIL_SERVICE_REQUIRED_PATH_MISSING")
        state.mkdir(parents=True, mode=0o700, exist_ok=True)
        config.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        write_json(
            config,
            {
                "mail_config_path": str(mail_config),
                "state_root": str(state),
                "source_roots": [
                    str(repo / ".runtime/canonical_local_launcher_v1"),
                    str(repo / "runtime/current_productive"),
                ],
                "installed_at_utc": datetime.now(timezone.utc).isoformat(),
            },
        )
        config.chmod(0o600)
        plist.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "Label": LABEL,
            "ProgramArguments": [
                str(repo / "scripts/pt"),
                "-m",
                "src.ops.runtime_health_recovery_and_failure_injection_closure_v1.runtime_mail_worker_v1",
                "--worker-config",
                str(config),
            ],
            "WorkingDirectory": str(repo),
            "RunAtLoad": True,
            "KeepAlive": True,
            "ThrottleInterval": 60,
            "ProcessType": "Background",
            "Umask": 0o077,
            "StandardOutPath": str(state / "stdout.log"),
            "StandardErrorPath": str(state / "stderr.log"),
        }
        with plist.open("xb") as stream:
            plistlib.dump(payload, stream)
        plist.chmod(0o600)
        result = launchctl("bootstrap", domain, str(plist))
        if result.returncode:
            return {
                "ok": False,
                "status": "INSTALL_PRESENT_BOOTSTRAP_FAILED",
                "exit_code": result.returncode,
            }
    elif action == "stop":
        result = launchctl("bootout", target)
        return {
            "ok": result.returncode == 0,
            "status": "STOP_REQUESTED",
            "autostart_plist_preserved": True,
        }
    elif action == "start":
        if not plist.is_file():
            raise ValueError("MAIL_SERVICE_NOT_INSTALLED")
        if launchctl("print", target).returncode:
            launchctl("bootstrap", domain, str(plist))
        launchctl("kickstart", target)
    elif action != "status":
        raise ValueError("MAIL_SERVICE_ACTION_INVALID")
    job = launchctl("print", target)
    loaded = job.returncode == 0
    pid_match = re.search(rb"^\s*pid = ([0-9]+)\s*$", job.stdout, re.MULTILINE)
    job_pid = int(pid_match.group(1)) if pid_match else None
    heartbeat = state / "status.json"
    status = json.loads(heartbeat.read_text()) if heartbeat.exists() else None
    fresh = (
        bool(status)
        and 0
        <= (
            datetime.now(timezone.utc) - datetime.fromisoformat(status["observed_at_utc"])
        ).total_seconds()
        < 180
    )
    identity_bound = bool(status) and job_pid is not None and job_pid == status.get("pid")
    return {
        "ok": loaded and fresh and identity_bound and status.get("status") == "READY",
        "loaded": loaded,
        "process_identity_bound": identity_bound,
        "heartbeat_fresh": fresh,
        "worker": status,
        "plist": str(plist),
    }
