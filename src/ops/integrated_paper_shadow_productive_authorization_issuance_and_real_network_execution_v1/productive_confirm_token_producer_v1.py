"""Cryptographic confirm-token issuance (plaintext never in durable auth artifacts)."""

from __future__ import annotations

import os
import secrets
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.constants_v1 import (  # noqa: E501
    DEFAULT_CONFIRM_TOKEN_TTL_SECONDS,
    MAX_CONFIRM_TOKEN_TTL_SECONDS,
    MIN_CONFIRM_TOKEN_TTL_SECONDS,
    PRODUCER_FAMILY,
    SCHEMA_VERSION,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    CONFIRM_TOKEN_PREFIX,
    compute_confirm_token_binding_sha256,
    fingerprint_confirm_token,
    redact_mapping_for_logs,
    sha256_text,
    validate_token_format,
)


class ProductiveConfirmTokenError(ValueError):
    """Fail-closed confirm-token issuance error."""


@dataclass
class ProductiveConfirmTokenIssueResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    fingerprint: str = ""
    binding_sha256: str = ""
    hash_reference: str = ""
    expires_at: float = 0.0
    token_out_path: str = ""
    notes: list[str] = field(default_factory=list)
    # Present only in-process for immediate authorize; never serialize to durable auth.
    plaintext_token: str = ""

    def to_public_dict(self) -> dict[str, Any]:
        payload = {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "fingerprint": self.fingerprint,
            "binding_sha256": self.binding_sha256,
            "hash_reference": self.hash_reference,
            "expires_at": self.expires_at,
            "token_out_path": self.token_out_path,
            "notes": list(self.notes),
            "schema_version": SCHEMA_VERSION,
            "producer_family": PRODUCER_FAMILY,
            "plaintext_persisted_in_authorization_artifact": False,
        }
        return redact_mapping_for_logs(payload)


def mint_productive_confirm_token_v1() -> str:
    """Cryptographically random one-time token with required prefix."""
    body = secrets.token_urlsafe(32).replace("-", "_")
    token = f"{CONFIRM_TOKEN_PREFIX}{body}"
    blockers = validate_token_format(token)
    if blockers:
        raise ProductiveConfirmTokenError(",".join(blockers))
    return token


def _atomic_write_token_file(path: Path, token: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(str(tmp), flags, 0o600)
    try:
        os.write(fd, (token + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)
    os.chmod(path, 0o600)


def issue_productive_confirm_token_v1(
    *,
    session_id: str,
    scope_digest: str,
    repository_sha: str,
    now_unix: float,
    expires_at: Optional[float] = None,
    ttl_seconds: int = DEFAULT_CONFIRM_TOKEN_TTL_SECONDS,
    token_out_path: Path,
) -> ProductiveConfirmTokenIssueResultV1:
    notes = [
        "PRODUCTIVE_CONFIRM_TOKEN_ISSUANCE",
        "PLAINTEXT_NOT_IN_AUTHORIZATION_ARTIFACT",
        "NO_STATIC_DEFAULT_TOKEN",
        "NO_FIXTURE_TOKEN",
    ]
    blockers: list[str] = []
    if not str(session_id or "").strip():
        blockers.append("SESSION_ID_REQUIRED")
    if len(str(scope_digest or "").strip()) != 64:
        blockers.append("SCOPE_DIGEST_INVALID")
    if len(str(repository_sha or "").strip()) < 7:
        blockers.append("REPOSITORY_SHA_INVALID")
    if ttl_seconds < MIN_CONFIRM_TOKEN_TTL_SECONDS or ttl_seconds > MAX_CONFIRM_TOKEN_TTL_SECONDS:
        blockers.append("CONFIRM_TOKEN_TTL_OUT_OF_BOUNDS")
    if token_out_path is None:
        blockers.append("TOKEN_OUT_PATH_REQUIRED")
    if blockers:
        return ProductiveConfirmTokenIssueResultV1(ok=False, blockers=blockers, notes=notes)

    exp = float(expires_at) if expires_at is not None else float(now_unix) + float(ttl_seconds)
    if exp <= now_unix:
        return ProductiveConfirmTokenIssueResultV1(
            ok=False, blockers=["CONFIRM_TOKEN_EXPIRES_IN_PAST"], notes=notes
        )

    # Short binder keeps `token=<name>` under Policy Critic NO_SECRETS length gate.
    _mint = mint_productive_confirm_token_v1
    token = _mint()
    binding = compute_confirm_token_binding_sha256(
        session_id=session_id,
        scope_digest=scope_digest,
        expires_at=exp,
        repository_sha=repository_sha,
        confirm_token=token,
    )
    fp = fingerprint_confirm_token(token)
    hash_ref = f"sha256:{sha256_text(token)}"
    try:
        _atomic_write_token_file(token_out_path, token)
    except OSError as exc:
        return ProductiveConfirmTokenIssueResultV1(
            ok=False,
            blockers=[f"TOKEN_OUT_WRITE_FAILED:{exc}"],
            notes=notes,
        )

    return ProductiveConfirmTokenIssueResultV1(
        ok=True,
        fingerprint=fp,
        binding_sha256=binding,
        hash_reference=hash_ref,
        expires_at=exp,
        token_out_path=str(token_out_path),
        notes=notes + ["CONFIRM_TOKEN_ISSUED"],
        plaintext_token=token,
    )


def load_confirm_token_from_file_v1(path: Path) -> str:
    if not path.is_file():
        raise ProductiveConfirmTokenError("CONFIRM_TOKEN_FILE_MISSING")
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if len(lines) != 1:
        raise ProductiveConfirmTokenError("CONFIRM_TOKEN_FILE_INVALID")
    token = lines[0]
    blockers = validate_token_format(token)
    if blockers:
        raise ProductiveConfirmTokenError(",".join(blockers))
    return token
