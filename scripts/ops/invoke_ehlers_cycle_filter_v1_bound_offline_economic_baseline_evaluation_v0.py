#!/usr/bin/env python3
"""Canonical invocation adapter for ehlers_cycle_filter/v1 bound offline baseline evaluation.

Offline-only adapter. Resolves repo-local ``.venv/bin/python``, reads ``GO_TOKEN`` from
the environment, and forwards ``--confirm-go-token`` to the existing evaluation runner.
No economic evaluation logic is owned here.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.offline_evaluation_runner_invocation_contract_v0 import (  # noqa: E402
    RUNNER_INVOCATION_CONTRACT_PASS,
    emit_invocation_contract_failure_v0,
    invoke_bound_offline_evaluation_runner_v0,
    read_confirm_go_token_from_env_v0,
)

RUNNER_REL_PATH = (
    "scripts/ops/run_ehlers_cycle_filter_v1_bound_offline_economic_baseline_evaluation_v0.py"
)


def main() -> None:
    confirm_go_token, token_reason, token_exit = read_confirm_go_token_from_env_v0()
    if token_reason != RUNNER_INVOCATION_CONTRACT_PASS:
        emit_invocation_contract_failure_v0(token_reason)
        raise SystemExit(token_exit)

    exit_code, reason_code = invoke_bound_offline_evaluation_runner_v0(
        repo_root=_REPO_ROOT,
        runner_rel_path=RUNNER_REL_PATH,
        confirm_go_token=confirm_go_token,
    )
    if reason_code != RUNNER_INVOCATION_CONTRACT_PASS:
        emit_invocation_contract_failure_v0(reason_code)
        raise SystemExit(exit_code)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
