"""Auxiliary mail worker. No trading process or trading authorization effects."""

import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

from src.ops.canonical_local_launcher_and_process_supervision_v1.single_writer_v1 import (
    LauncherSingleWriterV1,
)
from .evidence_v1 import write_json
from .runtime_notice_v1 import EVENTS_FILENAME
from .runtime_recovery_email_v1 import (
    build_recovery_email_channel_v1,
    process_runtime_recovery_emails_v1,
)


def discover_notice_roots_v1(source_roots):
    """Only configured trees; never follow symlinks into unrelated sources."""
    found = set()
    for source in source_roots:
        source = Path(source)
        if not source.is_absolute() or source.is_symlink():
            raise ValueError("MAIL_SOURCE_ROOT_INVALID")
        if not source.exists():
            continue
        for directory, dirs, files in os.walk(source, followlinks=False):
            dirs[:] = [d for d in dirs if not (Path(directory) / d).is_symlink()]
            notice = Path(directory) / EVENTS_FILENAME
            if EVENTS_FILENAME in files and not notice.is_symlink():
                found.add(Path(directory))
    return sorted(found)


async def process_mail_worker_batch_v1(
    settings, *, channel_factory=build_recovery_email_channel_v1
):
    channel = channel_factory(Path(settings["mail_config_path"]))
    summary = {
        "configured": channel.is_enabled(),
        "queues": 0,
        "pending": 0,
        "exhausted": 0,
        "transport_accepted": 0,
        "queue_errors": 0,
    }
    for root in discover_notice_roots_v1(settings["source_roots"]):
        summary["queues"] += 1
        try:
            result = await process_runtime_recovery_emails_v1(
                evidence_root=root,
                channel=channel,
                deliver=True,
                retry_cooldown_seconds=600,
            )
            for key in ("pending", "exhausted", "transport_accepted"):
                summary[key] += len(result[key])
        except Exception:
            # Preserve the broken queue. Other source queues still get drained.
            summary["queue_errors"] += 1
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker-config", required=True, type=Path)
    args = parser.parse_args()
    settings = json.loads(args.worker_config.read_text())
    state_root = Path(settings["state_root"])
    with LauncherSingleWriterV1(
        state_root / "worker_lock", writer_identity="peak_trade.o6_mail_worker_v1"
    ):
        while True:
            status = {"pid": os.getpid(), "observed_at_utc": datetime.now(timezone.utc).isoformat()}
            try:
                status.update(asyncio.run(process_mail_worker_batch_v1(settings)))
                status["status"] = (
                    "READY"
                    if status["configured"]
                    and not any(status[key] for key in ("pending", "exhausted", "queue_errors"))
                    else "DELIVERY_PENDING"
                )
            except Exception as exc:
                # Do not log SMTP responses, configuration contents or secrets.
                status.update(status="BLOCKED", error_type=type(exc).__name__)
            write_json(state_root / "status.json", status)
            time.sleep(60)


if __name__ == "__main__":
    main()
