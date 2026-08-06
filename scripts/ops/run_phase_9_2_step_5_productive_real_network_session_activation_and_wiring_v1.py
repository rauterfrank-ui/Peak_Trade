#!/usr/bin/env python3
"""CLI for Phase 9.2 Step-5 productive real-network session activation and wiring.

Commands:
  preflight / prove-wiring — structural wiring proof (no session)
  failure-injection        — offline gate truth-table negatives
  simulated-fetcher-once   — offline fake fetcher once under simulated full gate
  materialize-evidence     — write docs/evidence bundle + MANIFEST

Never starts a real network session. Never issues or consumes auth/tokens.
Confirm-token plaintext argv/env are rejected.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.evidence_v1 import (  # noqa: E402
    materialize_activation_wiring_evidence_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.failure_injection_v1 import (  # noqa: E402
    run_step5_activation_wiring_failure_injection_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.governed_activation_wiring_v1 import (  # noqa: E402
    prove_step5_activation_wiring_v1,
    run_simulated_full_gate_fetcher_once_v1,
)


def _repo_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
    ).strip()


def _reject_confirm_argv(raw: list[str]) -> list[str]:
    blockers: list[str] = []
    lowered = [a.lower() for a in raw]
    for flag in FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS:
        if flag.lower() in lowered:
            blockers.append(f"CONFIRM_TOKEN_ARGV_FORBIDDEN:{flag}")
    return blockers


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "command",
        choices=(
            "preflight",
            "prove-wiring",
            "failure-injection",
            "simulated-fetcher-once",
            "materialize-evidence",
        ),
    )
    p.add_argument("--evidence-root", type=Path, default=None)
    p.add_argument("--persistence-root", type=Path, default=None)
    p.add_argument("--expected-repository-sha", default=None)
    p.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    argv_blockers = _reject_confirm_argv(raw)
    parser = build_parser()
    args = parser.parse_args(raw)
    if argv_blockers:
        print(
            json.dumps(
                {
                    "ok": False,
                    "blockers": argv_blockers,
                    "capability_id": CAPABILITY_ID,
                    "network_session_started": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    sha = args.expected_repository_sha or _repo_sha()

    if args.command in {"preflight", "prove-wiring"}:
        result = prove_step5_activation_wiring_v1(
            expected_repository_sha=sha,
            repo_root=_REPO_ROOT,
            argv=raw,
        )
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0 if result.ok else 1

    if args.command == "failure-injection":
        fi = run_step5_activation_wiring_failure_injection_v1(
            expected_repository_sha=sha,
            now_unix=time.time(),
            repo_root=_REPO_ROOT,
        )
        print(json.dumps(fi, indent=2, sort_keys=True))
        return 0 if fi.get("ok") else 1

    if args.command == "simulated-fetcher-once":
        persistence = args.persistence_root or (
            _REPO_ROOT / "var" / "tmp" / "step5_activation_wiring_persistence"
        )
        evidence = args.evidence_root or (
            _REPO_ROOT / "var" / "tmp" / "step5_activation_wiring_evidence"
        )
        sim = run_simulated_full_gate_fetcher_once_v1(
            expected_repository_sha=sha,
            persistence_root=Path(persistence),
            evidence_root=Path(evidence),
            now_unix=time.time(),
            repo_root=_REPO_ROOT,
        )
        print(json.dumps(sim.to_dict(), indent=2, sort_keys=True))
        return 0 if sim.ok else 1

    if args.command == "materialize-evidence":
        summary = materialize_activation_wiring_evidence_v1(
            repository_sha=sha,
            evidence_root=args.evidence_root,
            repo_root=_REPO_ROOT,
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0 if summary.get("ok") else 1

    print(json.dumps({"ok": False, "blockers": ["UNKNOWN_COMMAND"]}, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
