from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import hmac
import hashlib


@dataclass(frozen=True)
class ArmedState:
    enabled: bool
    armed: bool
    armed_since_epoch: Optional[int]
    token_issued_epoch: Optional[int]


class ArmedGate:
    """
    Two-stage execution gate:
      - enabled: feature toggle (config-controlled)
      - armed: runtime state requiring short-lived confirm token
    Deterministic: token verification uses only provided inputs + HMAC.
    """

    def __init__(self, secret: bytes, token_ttl_seconds: int = 120) -> None:
        if not secret:
            raise ValueError("secret must be non-empty")
        if token_ttl_seconds <= 0:
            raise ValueError("token_ttl_seconds must be > 0")
        self._secret = secret
        self._ttl = int(token_ttl_seconds)

    def issue_token(self, now_epoch: int) -> str:
        """
        Token = hex(HMAC_SHA256(secret, f"{now_epoch}"))
        Caller is responsible for persistence/transport.
        """
        msg = str(int(now_epoch)).encode("utf-8")
        mac = hmac.new(self._secret, msg, hashlib.sha256).hexdigest()
        return f"{int(now_epoch)}.{mac}"

    def verify_token(self, token: str, now_epoch: int) -> bool:
        try:
            ts_s, mac = token.split(".", 1)
            ts = int(ts_s)
        except Exception:
            return False

        # TTL check
        if now_epoch < ts:
            return False
        if (now_epoch - ts) > self._ttl:
            return False

        expected = hmac.new(
            self._secret, str(ts).encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, mac)

    def arm(self, state: ArmedState, token: str, now_epoch: int) -> ArmedState:
        if not state.enabled:
            # cannot arm if disabled
            return state
        if not self.verify_token(token, now_epoch):
            return state
        return ArmedState(
            enabled=True,
            armed=True,
            armed_since_epoch=int(now_epoch),
            token_issued_epoch=None,
        )

    def disarm(self, state: ArmedState) -> ArmedState:
        return ArmedState(
            enabled=bool(state.enabled),
            armed=False,
            armed_since_epoch=None,
            token_issued_epoch=state.token_issued_epoch,
        )

    @staticmethod
    def require_armed(state: ArmedState) -> None:
        if not (state.enabled and state.armed):
            raise RuntimeError("Execution blocked: gate not armed")
