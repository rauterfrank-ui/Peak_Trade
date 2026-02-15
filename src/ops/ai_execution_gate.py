from __future__ import annotations

from pathlib import Path

from src.governance.ai_activation_gate_v1 import AIGateError, AIGateV1


DEFAULT_GATE_PATH = Path("config/governance/ai_activation_gate_v1.json")


def assert_ai_may_execute(mode: str, gate_path: Path = DEFAULT_GATE_PATH) -> None:
    gate = AIGateV1.load(gate_path)
    gate.assert_ai_signals_allowed(mode=mode)
    gate.assert_ai_execution_allowed(mode=mode)
