from __future__ import annotations

import os
from dataclasses import dataclass


class AIModelHardGateError(RuntimeError):
    """Raised when AI model execution is blocked by hard gate."""


def _is_yes(v: str | None) -> bool:
    if v is None:
        return False
    return v.strip().upper() in {"1", "TRUE", "YES", "Y", "ON"}


@dataclass(frozen=True)
class AIModelHardGateStatus:
    enabled: bool
    papertrail_ready: bool
    armed: bool

    @property
    def ok(self) -> bool:
        # armed is optional; if set in env, we require it to be YES as well.
        # If PT_AI_MODELS_ARMED is unset, we treat it as True (no 2-step configured).
        return self.enabled and self.papertrail_ready and self.armed


def read_ai_model_hard_gate_status() -> AIModelHardGateStatus:
    enabled = _is_yes(os.environ.get("PT_AI_MODELS_ENABLED"))
    papertrail_ready = _is_yes(os.environ.get("PT_PAPERTRAIL_READY"))

    armed_env = os.environ.get("PT_AI_MODELS_ARMED")
    armed = True if armed_env is None else _is_yes(armed_env)

    return AIModelHardGateStatus(enabled=enabled, papertrail_ready=papertrail_ready, armed=armed)


def require_ai_models_allowed(*, context: str) -> AIModelHardGateStatus:
    """
    Hard gate for AI model usage.
    Deny-by-default unless:
      - PT_AI_MODELS_ENABLED=YES
      - PT_PAPERTRAIL_READY=YES
      - and (if present) PT_AI_MODELS_ARMED=YES
    """
    st = read_ai_model_hard_gate_status()
    if st.ok:
        return st

    # Stable, actionable error message
    msg = (
        f"AI model execution blocked by hard gate (context={context}). "
        "Required env: PT_AI_MODELS_ENABLED=YES and PT_PAPERTRAIL_READY=YES"
    )
    if os.environ.get("PT_AI_MODELS_ARMED") is not None:
        msg += " and PT_AI_MODELS_ARMED=YES"
    msg += "."
    raise AIModelHardGateError(msg)
