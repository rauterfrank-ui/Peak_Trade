"""Test-only OS-process child for control-state WAL process-boundary proofs.

Not a host-crash harness. Not a productive consumer. SIGKILL of this
process is process-crash/process-restart evidence only.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from src.learning.mutation_critical_control_state_storage_v1.records_v1 import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STATE_CLASS_B_SUPERVISOR_CONTROL_STATE,
)
from src.learning.mutation_critical_control_state_storage_v1.wal_adapter_v1 import (
    MutationCriticalControlStateWalAdapterV1,
)

MODE_COMMIT_THEN_WAIT = "commit_then_wait"
MODE_PREPARE_THEN_WAIT = "prepare_then_wait"
MODE_BEFORE_PREPARE_WAIT = "before_prepare_wait"
READY_FILENAME = "PROCESS_CHILD_READY"


def _record(record_id: str) -> dict[str, str | dict[str, str] | None]:
    return {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "record_id": record_id,
        "state_class": STATE_CLASS_B_SUPERVISOR_CONTROL_STATE,
        "payload": {"state": "armed_false", "reason": "process_boundary_child"},
        "correlation_id": "process-boundary-corr",
        "depends_on_record_id": None,
    }


def _mark_ready(root: Path, mode: str) -> None:
    (root / READY_FILENAME).write_text(mode, encoding="utf-8")


def _wait_forever() -> None:
    while True:
        time.sleep(60.0)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument(
        "--mode",
        required=True,
        choices=(MODE_COMMIT_THEN_WAIT, MODE_PREPARE_THEN_WAIT, MODE_BEFORE_PREPARE_WAIT),
    )
    parser.add_argument("--record-id", required=True)
    args = parser.parse_args(argv)
    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    record = _record(args.record_id)
    if args.mode == MODE_BEFORE_PREPARE_WAIT:
        _mark_ready(root, args.mode)
        _wait_forever()
    wal = MutationCriticalControlStateWalAdapterV1(root)
    wal.open()
    try:
        if args.mode == MODE_COMMIT_THEN_WAIT:
            result = wal.commit_record(record)
            if result.status != "COMMITTED":
                raise SystemExit(f"unexpected_commit_status:{result.status}")
            _mark_ready(root, args.mode)
            _wait_forever()
        if args.mode == MODE_PREPARE_THEN_WAIT:
            prepared = wal.prepare(record)
            if prepared.status != "PREPARED":
                raise SystemExit(f"unexpected_prepare_status:{prepared.status}")
            _mark_ready(root, args.mode)
            _wait_forever()
    finally:
        wal.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
