from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


class AiModelPolicyError(RuntimeError):
    pass


@dataclass(frozen=True)
class PolicyStatusV1:
    enabled: bool
    armed: bool
    stage: str
    token_required: bool
    policy_path: str
    audit_path: str


def _default_policy_dir() -> Path:
    # Repo-local, deterministic and git-ignored by convention (out/)
    return Path("out/ops/ai_policy")


def _policy_path() -> Path:
    return _default_policy_dir() / "ai_model_policy_v1.json"


def _audit_path() -> Path:
    return _default_policy_dir() / "ai_model_policy_v1_audit.ndjson"


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json_atomic(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, sort_keys=True, indent=2), encoding="utf-8")
    tmp.replace(path)


def _now_utc() -> int:
    return int(time.time())


def _get_stage() -> str:
    # Prefer explicit env. Fall back to "research".
    return os.environ.get("PEAKTRADE_STAGE", "research").strip().lower()


def read_policy_v1(path: Optional[Path] = None) -> Dict[str, Any]:
    path = path or _policy_path()
    p = _load_json(path)
    # Defaults: deny-by-default
    p.setdefault("version", 1)
    p.setdefault("enabled", False)
    p.setdefault("armed", False)
    p.setdefault(
        "token_required_by_stage",
        {
            "research": False,
            "shadow": False,
            "testnet": True,
            "live": True,
        },
    )
    # Secret for HMAC: must be provided explicitly for token flow
    # (do NOT auto-generate; prevents accidental enabling).
    p.setdefault("hmac_secret_env", "PEAKTRADE_AI_CONFIRM_SECRET")
    # Token TTL
    p.setdefault("token_ttl_sec", 600)
    return p


def write_policy_v1(p: Dict[str, Any], path: Optional[Path] = None) -> None:
    path = path or _policy_path()
    _write_json_atomic(path, p)


def get_status_v1(path: Optional[Path] = None) -> PolicyStatusV1:
    path = path or _policy_path()
    p = read_policy_v1(path)
    stage = _get_stage()
    token_required = bool(p["token_required_by_stage"].get(stage, True))
    return PolicyStatusV1(
        enabled=bool(p["enabled"]),
        armed=bool(p["armed"]),
        stage=stage,
        token_required=token_required,
        policy_path=str(path),
        audit_path=str(_audit_path()),
    )


def _secret_bytes(p: Dict[str, Any]) -> bytes:
    env_name = str(p.get("hmac_secret_env", "PEAKTRADE_AI_CONFIRM_SECRET"))
    secret = os.environ.get(env_name, "").encode("utf-8")
    if not secret:
        raise AiModelPolicyError(
            f"Missing confirm secret env var '{env_name}'. Refusing token operations."
        )
    return secret


def mint_confirm_token_v1(p: Dict[str, Any], reason: str, now_utc: Optional[int] = None) -> str:
    now_utc = _now_utc() if now_utc is None else int(now_utc)
    ttl = int(p.get("token_ttl_sec", 600))
    exp = now_utc + ttl
    payload = {
        "v": 1,
        "exp": exp,
        "stage": _get_stage(),
        "reason": reason,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(_secret_bytes(p), raw, hashlib.sha256).hexdigest()
    token = json.dumps({"p": payload, "sig": sig}, sort_keys=True, separators=(",", ":"))
    return token


def verify_confirm_token_v1(
    p: Dict[str, Any], token: str, now_utc: Optional[int] = None
) -> Dict[str, Any]:
    now_utc = _now_utc() if now_utc is None else int(now_utc)
    try:
        obj = json.loads(token)
        payload = obj["p"]
        sig = obj["sig"]
    except Exception as e:
        raise AiModelPolicyError(f"Invalid token JSON: {e}") from e

    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    expected = hmac.new(_secret_bytes(p), raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise AiModelPolicyError("Invalid token signature.")

    exp = int(payload.get("exp", 0))
    if now_utc > exp:
        raise AiModelPolicyError("Token expired.")

    stage = str(payload.get("stage", "")).strip().lower()
    if stage != _get_stage():
        raise AiModelPolicyError(f"Token stage mismatch: token={stage} current={_get_stage()}")

    return payload


def policy_allows_ai_call_v1(
    *,
    confirm_token: Optional[str],
    path: Optional[Path] = None,
) -> None:
    """
    Raise AiModelPolicyError if the call is not allowed.
    """
    path = path or _policy_path()
    p = read_policy_v1(path)
    st = get_status_v1(path)

    if not st.enabled:
        raise AiModelPolicyError("AI models disabled by policy (enabled=false).")
    if not st.armed:
        raise AiModelPolicyError("AI models not armed (armed=false).")

    if st.token_required:
        if not confirm_token:
            raise AiModelPolicyError("Confirm token required for this stage but not provided.")
        verify_confirm_token_v1(p, confirm_token)
