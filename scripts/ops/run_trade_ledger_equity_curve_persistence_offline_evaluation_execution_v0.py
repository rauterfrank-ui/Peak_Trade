#!/usr/bin/env python3
"""Run trade ledger equity curve persistence offline evaluation execution v0.

Fail-closed runner contract for bounded offline evaluation with TRADE_LEDGER_V1.jsonl and
EQUITY_CURVE_V1.jsonl persistence. No runtime, order, credentials, arming, or authority
effect. Operator GO: GO_TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_EXECUTION_V0
(requires separate GO after binding materialization merge and green checks).
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (_SRC_ROOT, _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from src.research.trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    EXECUTION_AUTHORIZED,
    FAIL_CLOSED_REASON,
    GO_TOKEN,
    RUNTIME_EFFECT,
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def main() -> None:
    _die(
        f"{FAIL_CLOSED_REASON}: execution_authorized={EXECUTION_AUTHORIZED} "
        f"go_token={GO_TOKEN} authority_effect={AUTHORITY_EFFECT} runtime_effect={RUNTIME_EFFECT}. "
        "Binding materialization defines owner/runner refs only; separate operator GO required "
        "after merge and green checks.",
        code=2,
    )


if __name__ == "__main__":
    main()
