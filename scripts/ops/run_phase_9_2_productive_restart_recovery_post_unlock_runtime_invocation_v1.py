#!/usr/bin/env python3
"""CLI for Phase 9.2 post-unlock canonical runtime invocation capability.

Commands:
  preflight            — authority/runner readiness (no side effects)
  materialize-evidence — deterministic offline evidence fixtures
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.constants_v1 import (  # noqa: E402
    CANONICAL_RUNTIME_RUNNER,
    CAPABILITY_ID,
    CONFIG_RELATIVE_PATH,
    PRODUCTIVE_ENTRYPOINT_PATH,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.evidence_v1 import (  # noqa: E402
    materialize_capability_evidence_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.parity_v1 import (  # noqa: E402
    prove_phase92_post_unlock_invocation_parity_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (  # noqa: E402
    redact_mapping_for_logs,
)


def _repo_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
    ).strip()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("preflight", "materialize-evidence"))
    p.add_argument("--evidence-root", type=Path, default=None)
    p.add_argument("--expected-repository-sha", default=None)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sha = args.expected_repository_sha or _repo_sha()

    if args.command == "preflight":
        parity = prove_phase92_post_unlock_invocation_parity_v1()
        cfg = _REPO_ROOT / CONFIG_RELATIVE_PATH
        entry = _REPO_ROOT / PRODUCTIVE_ENTRYPOINT_PATH
        payload = {
            "ok": bool(parity.get("ok") and cfg.is_file() and entry.is_file()),
            "capability_id": CAPABILITY_ID,
            "session_id": TARGET_SESSION_ID,
            "canonical_runtime_runner": CANONICAL_RUNTIME_RUNNER,
            "productive_entrypoint_path": PRODUCTIVE_ENTRYPOINT_PATH,
            "config_present": cfg.is_file(),
            "entrypoint_present": entry.is_file(),
            "parity": parity,
            "network_session_started": False,
            "authorization_consumed": False,
            "notes": [
                "POST_UNLOCK_INVOCATION_SURFACE_READY",
                "CANONICAL_RUNNER_PREEXISTED",
                "NO_REAL_NETWORK",
                "NO_SESSION_STARTED",
            ],
        }
        print(json.dumps(redact_mapping_for_logs(payload), sort_keys=True, indent=2))
        return 0 if payload["ok"] else 1

    summary = materialize_capability_evidence_v1(
        repository_sha=sha,
        evidence_root=args.evidence_root,
        repo_root=_REPO_ROOT,
    )
    print(json.dumps(redact_mapping_for_logs(summary), sort_keys=True, indent=2))
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
