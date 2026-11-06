#!/usr/bin/env python3
"""CLI for Step-5 final generic auth-consume and network-start binding.

Commands:
  preflight / prove-binding — structural binding proof (no session)
  failure-injection         — offline fail-closed matrix
  materialize-evidence      — write docs/evidence bundle + MANIFEST

Never starts a real network session. Never issues real production auth/tokens.
Confirm-token plaintext argv/env are rejected.
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

from src.ops.phase_9_2_step_5_final_generic_session_authorization_consume_and_network_start_binding_v1.binding_v1 import (  # noqa: E402
    prove_step5_final_generic_consume_start_binding_complete_v1,
)
from src.ops.phase_9_2_step_5_final_generic_session_authorization_consume_and_network_start_binding_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS,
)
from src.ops.phase_9_2_step_5_final_generic_session_authorization_consume_and_network_start_binding_v1.evidence_v1 import (  # noqa: E402
    materialize_step5_final_generic_binding_evidence_v1,
    run_step5_final_generic_failure_injection_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (  # noqa: E402
    load_activation_config_v1,
)


def _repo_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
    ).strip()


def _cfg() -> str:
    return str(
        load_activation_config_v1(
            config_path=_REPO_ROOT
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )


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
            "prove-binding",
            "failure-injection",
            "materialize-evidence",
        ),
    )
    p.add_argument("--evidence-root", type=Path, default=None)
    p.add_argument("--persistence-root", type=Path, default=None)
    p.add_argument("--expected-repository-sha", default=None)
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
    cfg = _cfg()

    if args.command in {"preflight", "prove-binding"}:
        result = prove_step5_final_generic_consume_start_binding_complete_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            repo_root=_REPO_ROOT,
            argv=raw,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("ok") else 1

    if args.command == "failure-injection":
        persistence = args.persistence_root or (
            _REPO_ROOT / "var" / "tmp" / "step5_final_generic_fi_persistence"
        )
        fi = run_step5_final_generic_failure_injection_v1(
            repository_sha=sha,
            config_digest=cfg,
            persistence_root=Path(persistence),
            repo_root=_REPO_ROOT,
        )
        print(json.dumps(fi, indent=2, sort_keys=True))
        return 0 if fi.get("ok") else 1

    if args.command == "materialize-evidence":
        summary = materialize_step5_final_generic_binding_evidence_v1(
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
