#!/usr/bin/env python3
"""STEP29M single-instrument offline evaluation adapter runner for bouchaud OHLCV proxy v1.

Implementation slice only: validates contracts and materializes adapter evidence.
Blocks economic evaluation unless separate evaluation GO is provided (also blocked here).
No runtime, credentials, orders, or authority effect.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research.bouchaud_microstructure_ohlcv_proxy_v1_step29m_single_instrument_offline_evaluation_adapter_v0 import (  # noqa: E402
    EVALUATION_GO_TOKEN,
    IMPLEMENTATION_GO_TOKEN,
    classify_go_token_v0,
    run_adapter_implementation_v0,
)

RUNNER_OWNER = (
    "scripts.ops.run_bouchaud_microstructure_ohlcv_proxy_v1_step29m_single_instrument_"
    "offline_evaluation_adapter_v0"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-go-token", required=True)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--durable-evidence-root",
        type=Path,
        default=Path(
            "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
        ),
    )
    args = parser.parse_args()

    operator_go = args.confirm_go_token
    go_result = classify_go_token_v0(operator_go)
    if go_result.classification.value == "REJECTED":
        raise SystemExit(f"ERR: {go_result.blocking_reasons[0]}")

    if operator_go == EVALUATION_GO_TOKEN:
        raise SystemExit("ERR: evaluation_go_blocked_in_implementation_slice")

    if operator_go != IMPLEMENTATION_GO_TOKEN:
        raise SystemExit(f"ERR: invalid_go_token:{operator_go}")

    result = run_adapter_implementation_v0(
        repo_root=args.repo_root,
        confirm_operator_go=operator_go,
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
