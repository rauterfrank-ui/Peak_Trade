from __future__ import annotations

from pathlib import Path

import pytest

from src.governance.ai_activation_gate_v1 import AIGateError, AIGateV1


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "gate.json"
    p.write_text(content, encoding="utf-8")
    return p


def test_default_blocks_live_execution(tmp_path: Path):
    p = _write(
        tmp_path,
        """
        {"version":1,"papertrail_ready":false,"allow_ai_signals_in_shadow_paper":true,"allow_ai_to_execute_live":false,
         "live_unlock":{"enabled":false,"armed":false,"confirm_token_env":"PT_CONFIRM_TOKEN","confirm_token_required":true}}
        """,
    )
    gate = AIGateV1.load(p)
    gate.assert_ai_signals_allowed("paper")
    with pytest.raises(AIGateError):
        gate.assert_ai_execution_allowed("live")


def test_shadow_signals_can_be_disabled(tmp_path: Path):
    p = _write(
        tmp_path,
        """
        {"version":1,"papertrail_ready":false,"allow_ai_signals_in_shadow_paper":false,"allow_ai_to_execute_live":false,
         "live_unlock":{"enabled":false,"armed":false,"confirm_token_env":"PT_CONFIRM_TOKEN","confirm_token_required":true}}
        """,
    )
    gate = AIGateV1.load(p)
    with pytest.raises(AIGateError):
        gate.assert_ai_signals_allowed("shadow")


def test_live_unlock_requires_all_conditions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    p = _write(
        tmp_path,
        """
        {"version":1,"papertrail_ready":true,"allow_ai_signals_in_shadow_paper":true,"allow_ai_to_execute_live":true,
         "live_unlock":{"enabled":true,"armed":true,"confirm_token_env":"PT_CONFIRM_TOKEN","confirm_token_required":true}}
        """,
    )
    monkeypatch.delenv("PT_CONFIRM_TOKEN", raising=False)
    gate = AIGateV1.load(p)
    with pytest.raises(AIGateError):
        gate.assert_ai_execution_allowed("live")

    monkeypatch.setenv("PT_CONFIRM_TOKEN", "YES")
    gate.assert_ai_execution_allowed("live")
