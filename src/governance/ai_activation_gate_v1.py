from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class AIGateError(RuntimeError):
    pass


@dataclass(frozen=True)
class LiveUnlock:
    enabled: bool
    armed: bool
    confirm_token_env: str
    confirm_token_required: bool

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "LiveUnlock":
        return LiveUnlock(
            enabled=bool(d.get("enabled", False)),
            armed=bool(d.get("armed", False)),
            confirm_token_env=str(d.get("confirm_token_env", "PT_CONFIRM_TOKEN")),
            confirm_token_required=bool(d.get("confirm_token_required", True)),
        )


@dataclass(frozen=True)
class AIGateV1:
    version: int
    papertrail_ready: bool
    allow_ai_signals_in_shadow_paper: bool
    allow_ai_to_execute_live: bool
    live_unlock: LiveUnlock

    @staticmethod
    def load(path: str | Path) -> "AIGateV1":
        p = Path(path)
        data = json.loads(p.read_text(encoding="utf-8"))
        if int(data.get("version", 0)) != 1:
            raise ValueError(f"Unsupported AIGate version: {data.get('version')}")
        return AIGateV1(
            version=1,
            papertrail_ready=bool(data.get("papertrail_ready", False)),
            allow_ai_signals_in_shadow_paper=bool(
                data.get("allow_ai_signals_in_shadow_paper", True)
            ),
            allow_ai_to_execute_live=bool(data.get("allow_ai_to_execute_live", False)),
            live_unlock=LiveUnlock.from_dict(dict(data.get("live_unlock", {}))),
        )

    def _confirm_token_ok(self) -> bool:
        if not self.live_unlock.confirm_token_required:
            return True
        token = os.environ.get(self.live_unlock.confirm_token_env, "")
        return bool(token.strip())

    def assert_ai_signals_allowed(self, mode: str) -> None:
        """
        mode: "shadow" | "paper" | "testnet" | "live"
        Signals are allowed in shadow/paper/testnet if configured. Live signals are allowed but irrelevant
        unless they can execute (execution is separately gated below).
        """
        m = mode.lower().strip()
        if m in {"shadow", "paper", "testnet"}:
            if not self.allow_ai_signals_in_shadow_paper:
                raise AIGateError(f"AI signals disabled for mode={m}")
            return
        if m == "live":
            # Signals can exist, but do not imply execution.
            return
        raise ValueError(f"Unknown mode: {mode}")

    def assert_ai_execution_allowed(self, mode: str) -> None:
        """
        HARD RULE:
        - Live execution is ALWAYS blocked unless:
          papertrail_ready=true AND allow_ai_to_execute_live=true AND enabled+armed AND confirm_token present (if required).
        - Non-live execution should still be handled by existing safety gates; this function focuses on AI->LIVE.
        """
        m = mode.lower().strip()
        if m != "live":
            return

        if not self.papertrail_ready:
            raise AIGateError("Live execution blocked: papertrail_ready=false")
        if not self.allow_ai_to_execute_live:
            raise AIGateError("Live execution blocked: allow_ai_to_execute_live=false")
        if not (self.live_unlock.enabled and self.live_unlock.armed):
            raise AIGateError("Live execution blocked: live_unlock.enabled/armed not both true")
        if not self._confirm_token_ok():
            raise AIGateError(
                f"Live execution blocked: missing confirm token env={self.live_unlock.confirm_token_env}"
            )
