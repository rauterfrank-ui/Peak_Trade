from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(
    "config/research/"
    "cross_sectional_realized_volatility_rank_rotation_v0_versioned_bindings_and_eval_scope.json"
)

REQUIRED_FALSE_FLAGS = (
    "evaluation_execution_authorized",
    "runtime_authority_touched",
    "promotion_granted",
)

FORBIDDEN_RUNTIME_AUTHORITIES = {
    "RUNTIME_REWIRE",
    "SHADOW",
    "PAPER",
    "TESTNET",
    "SCHEDULER",
    "ADAPTER_SUBMISSION",
    "ORDERS",
    "CREDENTIALS",
    "ARMING",
    "CANARY",
    "LIVE",
}


def load_binding(path: Path = CONFIG_PATH) -> dict[str, Any]:
    return json.loads(path.read_text())


def validate_binding(binding: dict[str, Any]) -> None:
    if binding["strategy_id"] != "cross_sectional_realized_volatility_rank_rotation":
        raise ValueError("unexpected strategy_id")
    if binding["strategy_version"] != "v0":
        raise ValueError("unexpected strategy_version")

    for flag in REQUIRED_FALSE_FLAGS:
        if binding.get(flag) is not False:
            raise ValueError(f"{flag} must be false")

    forbidden = set(binding.get("forbidden", []))
    missing = FORBIDDEN_RUNTIME_AUTHORITIES - forbidden
    if missing:
        raise ValueError(f"missing forbidden runtime authorities: {sorted(missing)}")

    if binding["parameter_binding"]["unchanged_retry_or_threshold_rescue_allowed"] is not False:
        raise ValueError("unchanged retry or threshold rescue must remain forbidden")

    if binding["cost_execution_bindings"]["no_implicit_zero_cost_backtest"] is not True:
        raise ValueError("no implicit zero-cost backtest binding required")


def main() -> int:
    validate_binding(load_binding())
    print("BINDING_VALIDATION_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
