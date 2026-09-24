"""Static backflow guard for research stratification v2."""

from __future__ import annotations

from pathlib import Path

FORBIDDEN_BACKFLOW_TOKENS: tuple[str, ...] = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1",
    "double_play_sole_authority",
    "bull_bear_state_switch",
    "src.execution",
    "place_order",
    "submit_order",
)


def assert_no_trading_backflow_v2(*, package_root: Path | None = None) -> dict[str, str]:
    root = package_root or Path(__file__).resolve().parent
    violations: list[str] = []
    for path in sorted(root.glob("*.py")):
        if path.name == "backflow_check_v2.py":
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not (stripped.startswith("import ") or stripped.startswith("from ")):
                continue
            for token in FORBIDDEN_BACKFLOW_TOKENS:
                if token in stripped:
                    violations.append(f"{path.name}:{token}")
    if violations:
        raise RuntimeError("RESEARCH_STRATIFICATION_V2_TRADING_BACKFLOW:" + "|".join(violations))
    return {
        "trading_decision": "NONE",
        "bull_bear_state_switch": "NONE",
        "selection": "NONE",
        "risk_sizing": "NONE",
        "execution": "NONE",
        "live_boundary": "NONE",
        "optimization_promotion": "NONE",
    }
