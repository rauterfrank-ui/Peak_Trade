"""Emergency flatten / close-all — mock-only, NO-LIVE, no network (LB-EMG-001 slice).

This script does not send orders or open sockets. It exercises a testable emergency-close
shell with dry_run default True. Real exchange closeout and production paths require
separate governance (e.g. LB-APR-001) and are out of scope for this module.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import List, Protocol, runtime_checkable


@runtime_checkable
class EmergencyBroker(Protocol):
    """Injectable broker boundary; live implementations are out of scope for v1."""

    def close_all_positions(self, *, dry_run: bool) -> List[str]: ...


@dataclass(frozen=True)
class EmergencyCloseResultV1:
    dry_run: bool
    messages: tuple[str, ...]
    exit_code: int


class MockEmergencyBrokerV1:
    """Deterministic test double — no network, no credentials."""

    def close_all_positions(self, *, dry_run: bool) -> List[str]:
        if dry_run:
            return [
                "LB_EMG_001_MOCK dry_run=True — no orders sent; would schedule flatten (mock).",
            ]
        return [
            "LB_EMG_001_MOCK dry_run=False — mock path only; NO-LIVE; no exchange closeout.",
        ]


def run_emergency_close_all_v1(*, dry_run: bool, broker: EmergencyBroker) -> EmergencyCloseResultV1:
    """Run the emergency close flow; broker must be mock-only in this repo slice."""
    if not isinstance(broker, EmergencyBroker):
        raise TypeError("broker must implement EmergencyBroker (LB-EMG-001 mock boundary)")
    msgs = broker.close_all_positions(dry_run=dry_run)
    return EmergencyCloseResultV1(
        dry_run=dry_run,
        messages=tuple(msgs),
        exit_code=0,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "NO-LIVE — Emergency flatten helper (mock broker only). "
            "No production unlock; no substitute for external Canary approval."
        ),
        epilog=(
            "Default: dry_run (no --execute). No network I/O. "
            "See docs/ops/runbooks/CANARY_LIVE_ENTRY_CRITERIA.md for governance."
        ),
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Exercise non-dry_run branch; still mock-only (no network).",
    )
    ns = parser.parse_args(argv)
    dry_run = not ns.execute
    result = run_emergency_close_all_v1(dry_run=dry_run, broker=MockEmergencyBrokerV1())
    for line in result.messages:
        print(line)
    return result.exit_code


__all__ = [
    "EmergencyBroker",
    "EmergencyCloseResultV1",
    "MockEmergencyBrokerV1",
    "run_emergency_close_all_v1",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
