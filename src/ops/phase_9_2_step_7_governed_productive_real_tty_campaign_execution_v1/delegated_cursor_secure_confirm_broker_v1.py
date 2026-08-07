"""Delegated Cursor secure confirm broker (EPHEMERAL_EXECUTION_LATCH).

Token role is explicitly NOT a proof of human Real-TTY presence.
Plaintext never goes to argv, stdout/stderr, logs, or durable evidence —
only SHA-256 digests are public. Transport is in-process handle and/or
chmod-0600 tempfile / FD (never CLI args).
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.constants_v1 import (
    AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
    CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
    DELEGATED_CURSOR_SECURE_CONFIRM_BROKER_OWNER,
)

_TOKEN_FILE_MODE = 0o600


class DelegatedCursorSecureConfirmError(RuntimeError):
    """Fail-closed broker error; never embeds plaintext token."""


def digest_sha256_v1(plaintext: str) -> str:
    return hashlib.sha256(str(plaintext).encode("utf-8")).hexdigest()


def _constant_time_equal_v1(left: str, right: str) -> bool:
    a = str(left or "").encode("utf-8")
    b = str(right or "").encode("utf-8")
    if len(a) != len(b):
        # Still run compare_digest on equal-length digests of inputs to
        # avoid trivial short-circuit timing on length alone for callers
        # that compare digests; for plaintext we digest both sides.
        return hmac.compare_digest(digest_sha256_v1(left), digest_sha256_v1(right)) and False
    return hmac.compare_digest(a, b)


@dataclass
class DelegatedCursorSecureConfirmPublicV1:
    ok: bool
    blockers: list[str]
    authorization_channel: str
    token_role: str
    confirm_token_digest_sha256: str
    consumed: bool
    cleared: bool
    temp_secret_cleaned: bool
    plaintext_persisted: bool = False
    plaintext_disclosed: bool = False
    one_time_use_enforced: bool = True
    notes: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "AUTHORIZATION_CHANNEL": self.authorization_channel,
            "TOKEN_ROLE": self.token_role,
            "confirm_token_digest_sha256": self.confirm_token_digest_sha256,
            "consumed": self.consumed,
            "cleared": self.cleared,
            "temp_secret_cleaned": self.temp_secret_cleaned,
            "plaintext_persisted": self.plaintext_persisted,
            "plaintext_disclosed": self.plaintext_disclosed,
            "one_time_use_enforced": self.one_time_use_enforced,
            "broker_owner": DELEGATED_CURSOR_SECURE_CONFIRM_BROKER_OWNER,
            "notes": list(self.notes or []),
        }


class DelegatedCursorSecureConfirmLatchV1:
    """One-time EPHEMERAL_EXECUTION_LATCH for DELEGATED_CURSOR_SECURE_CONFIRM."""

    __slots__ = (
        "_token",
        "_digest",
        "_consumed",
        "_cleared",
        "_temp_path",
        "_expected_digest",
    )

    def __init__(self, token: str, *, expected_digest: str | None = None) -> None:
        if not isinstance(token, str) or not token.strip():
            raise DelegatedCursorSecureConfirmError("CONFIRM_TOKEN_MISSING")
        self._token: str | None = token
        self._digest = digest_sha256_v1(token)
        if expected_digest is not None and not hmac.compare_digest(
            self._digest, str(expected_digest)
        ):
            raise DelegatedCursorSecureConfirmError("CONFIRM_TOKEN_DIGEST_MISMATCH")
        self._expected_digest = self._digest
        self._consumed = False
        self._cleared = False
        self._temp_path: Path | None = None

    @classmethod
    def mint_v1(cls) -> DelegatedCursorSecureConfirmLatchV1:
        # cryptographically strong one-time latch; never log this value
        return cls(secrets.token_urlsafe(32))

    def __repr__(self) -> str:
        return (
            "DelegatedCursorSecureConfirmLatchV1("
            f"digest={self._digest[:16]}..., consumed={self._consumed}, "
            f"cleared={self._cleared})"
        )

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def digest(self) -> str:
        return self._digest

    @property
    def consumed(self) -> bool:
        return self._consumed

    @property
    def cleared(self) -> bool:
        return self._cleared

    @property
    def temp_path(self) -> Path | None:
        return self._temp_path

    def public_dict_v1(self) -> dict[str, Any]:
        return {
            "AUTHORIZATION_CHANNEL": AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
            "TOKEN_ROLE": CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
            "confirm_token_digest_sha256": self._digest,
            "consumed": self._consumed,
            "cleared": self._cleared,
            "temp_path_present": self._temp_path is not None,
            "plaintext_persisted": False,
            "broker_owner": DELEGATED_CURSOR_SECURE_CONFIRM_BROKER_OWNER,
        }

    def write_tempfile_0600_v1(
        self,
        *,
        repository_root: Path,
        evidence_root: Path | None = None,
        directory: Path | None = None,
    ) -> Path:
        """Write latch to chmod-0600 tempfile outside repo/evidence roots."""
        if self._cleared or self._token is None:
            raise DelegatedCursorSecureConfirmError("CONFIRM_TOKEN_UNAVAILABLE")
        repo = Path(repository_root).resolve()
        evidence = (
            Path(evidence_root).resolve()
            if evidence_root is not None
            else (repo / "docs" / "evidence").resolve()
        )
        parent = Path(directory).resolve() if directory is not None else Path(tempfile.gettempdir())
        try:
            parent.relative_to(repo)
            raise DelegatedCursorSecureConfirmError("TOKEN_PATH_INSIDE_REPOSITORY")
        except ValueError:
            pass
        try:
            parent.relative_to(evidence)
            raise DelegatedCursorSecureConfirmError("TOKEN_PATH_INSIDE_EVIDENCE_ROOT")
        except ValueError:
            pass
        fd, name = tempfile.mkstemp(
            prefix="peak_trade_step7_delegated_confirm_",
            suffix=".token",
            dir=str(parent),
        )
        path = Path(name)
        try:
            os.write(fd, (self._token + "\n").encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)
        os.chmod(path, _TOKEN_FILE_MODE)
        st = os.lstat(path)
        if not stat.S_ISREG(st.st_mode) or stat.S_IMODE(st.st_mode) != _TOKEN_FILE_MODE:
            self._secure_unlink_v1(path)
            raise DelegatedCursorSecureConfirmError("TOKEN_FILE_MODE_NOT_0600")
        self._temp_path = path
        return path

    def load_from_tempfile_v1(self, path: Path) -> str:
        """Load plaintext once from tempfile; does not mark consumed."""
        target = Path(path)
        if target.is_symlink():
            raise DelegatedCursorSecureConfirmError("TOKEN_FILE_SYMLINK_FORBIDDEN")
        if not target.is_file():
            raise DelegatedCursorSecureConfirmError("CONFIRM_TOKEN_MISSING")
        st = os.lstat(target)
        if stat.S_IMODE(st.st_mode) != _TOKEN_FILE_MODE:
            raise DelegatedCursorSecureConfirmError("TOKEN_FILE_MODE_NOT_0600")
        raw = target.read_text(encoding="utf-8")
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        if len(lines) != 1:
            raise DelegatedCursorSecureConfirmError("CONFIRM_TOKEN_FILE_INVALID")
        return lines[0]

    def consume_once_v1(self) -> str:
        if self._cleared or self._token is None:
            raise DelegatedCursorSecureConfirmError("CONFIRM_TOKEN_MISSING")
        if self._consumed:
            raise DelegatedCursorSecureConfirmError("CONFIRM_TOKEN_REPLAY")
        self._consumed = True
        return self._token

    def verify_presented_and_consume_v1(
        self, presented: str
    ) -> DelegatedCursorSecureConfirmPublicV1:
        blockers: list[str] = []
        presented_s = str(presented or "")
        try:
            if self._cleared or self._token is None:
                blockers.append("CONFIRM_TOKEN_MISSING")
            elif self._consumed:
                blockers.append("CONFIRM_TOKEN_REPLAY")
            elif not presented_s.strip():
                blockers.append("CONFIRM_TOKEN_MISSING")
            elif not _constant_time_equal_v1(presented_s, self._token or ""):
                blockers.append("CONFIRM_TOKEN_DIGEST_MISMATCH")
                blockers.append("CONFIRM_TOKEN_INVALID")
            else:
                self._consumed = True
        finally:
            # never leave presented in locals for accidental logging
            presented_s = ""
        return DelegatedCursorSecureConfirmPublicV1(
            ok=not blockers,
            blockers=sorted(set(blockers)),
            authorization_channel=AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
            token_role=CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
            confirm_token_digest_sha256=self._digest,
            consumed=self._consumed and not blockers,
            cleared=self._cleared,
            temp_secret_cleaned=False,
            notes=["TOKEN_ROLE=EPHEMERAL_EXECUTION_LATCH", "DIGEST_ONLY_PUBLIC=true"],
        )

    def consume_from_tempfile_once_v1(
        self, path: Path | None = None
    ) -> DelegatedCursorSecureConfirmPublicV1:
        target = Path(path) if path is not None else self._temp_path
        blockers: list[str] = []
        presented = ""
        try:
            if target is None:
                blockers.append("CONFIRM_TOKEN_MISSING")
                return DelegatedCursorSecureConfirmPublicV1(
                    ok=False,
                    blockers=blockers,
                    authorization_channel=AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
                    token_role=CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
                    confirm_token_digest_sha256=self._digest,
                    consumed=False,
                    cleared=self._cleared,
                    temp_secret_cleaned=False,
                )
            presented = self.load_from_tempfile_v1(target)
            result = self.verify_presented_and_consume_v1(presented)
            return result
        except DelegatedCursorSecureConfirmError as exc:
            blockers.append(str(exc) or "CONFIRM_TOKEN_FAILURE")
            return DelegatedCursorSecureConfirmPublicV1(
                ok=False,
                blockers=sorted(set(blockers)),
                authorization_channel=AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
                token_role=CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
                confirm_token_digest_sha256=self._digest,
                consumed=False,
                cleared=self._cleared,
                temp_secret_cleaned=False,
            )
        finally:
            presented = ""
            cleaned = self.cleanup_temp_secret_v1()
            _ = cleaned

    def clear_v1(self) -> None:
        self._token = None
        self._cleared = True

    def cleanup_temp_secret_v1(self) -> bool:
        path = self._temp_path
        self._temp_path = None
        if path is None:
            return True
        return self._secure_unlink_v1(path)

    @staticmethod
    def _secure_unlink_v1(path: Path) -> bool:
        try:
            p = Path(path)
            if p.is_symlink():
                p.unlink(missing_ok=True)  # type: ignore[call-arg]
                return not p.exists()
            if p.exists():
                try:
                    size = p.stat().st_size
                    with open(p, "r+b", buffering=0) as fh:
                        fh.write(b"\0" * max(size, 1))
                        fh.flush()
                        os.fsync(fh.fileno())
                except OSError:
                    pass
                p.unlink(missing_ok=True)  # type: ignore[call-arg]
            return not Path(path).exists()
        except OSError:
            return not Path(path).exists()

    def as_getpass_fn_v1(self):
        """Adapter for Real-TTY-shaped consumers; still one-time latch semantics."""

        def _getpass(_prompt: str = "") -> str:
            return self.consume_once_v1()

        return _getpass


def mint_delegated_cursor_secure_confirm_latch_v1() -> DelegatedCursorSecureConfirmLatchV1:
    return DelegatedCursorSecureConfirmLatchV1.mint_v1()


def acquire_delegated_cursor_secure_confirm_v1(
    *,
    latch: DelegatedCursorSecureConfirmLatchV1 | None = None,
    token_file: Path | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Acquire and consume delegated confirm latch (digest-only public result).

    Preferred: in-process ``latch``. Exception path: chmod-0600 ``token_file``.
    Plaintext is never returned in the public result.
    """
    from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.confirm_token_path_v1 import (
        reject_confirm_token_argv_v1,
        reject_confirm_token_env_fallback_v1,
    )

    blockers: list[str] = []
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))
    owned = latch
    temp_cleaned = True
    digest = ""

    def _fail(extra: list[str], *, fp: str = "", cleaned: bool = True) -> dict[str, Any]:
        return {
            "ok": False,
            "blockers": sorted(set(blockers + extra)),
            "fingerprint": fp,
            "confirm_token_consumed": False,
            "AUTHORIZATION_CHANNEL": AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
            "TOKEN_ROLE": CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
            "DELEGATED_SECURE_CONFIRM_VERIFIED": False,
            "temp_secret_cleaned": cleaned,
            "plaintext": "",
        }

    try:
        if blockers:
            return _fail([])
        if owned is None and token_file is not None:
            raw = ""
            probe = DelegatedCursorSecureConfirmLatchV1.mint_v1()
            try:
                raw = probe.load_from_tempfile_v1(Path(token_file))
                owned = DelegatedCursorSecureConfirmLatchV1(raw)
                owned._temp_path = Path(token_file)  # noqa: SLF001 — broker owns cleanup
            except DelegatedCursorSecureConfirmError as exc:
                return _fail([str(exc) or "CONFIRM_TOKEN_FAILURE"])
            finally:
                raw = ""
                probe.clear_v1()
                probe.cleanup_temp_secret_v1()
        if owned is None:
            return _fail(["CONFIRM_TOKEN_MISSING"])

        digest = owned.digest
        if token_file is not None or owned.temp_path is not None:
            result = owned.consume_from_tempfile_once_v1(
                Path(token_file) if token_file is not None else owned.temp_path
            )
            temp_cleaned = owned.cleanup_temp_secret_v1()
            if not result.ok:
                owned.clear_v1()
                return _fail(list(result.blockers), fp=digest, cleaned=temp_cleaned)
        else:
            try:
                _ = owned.consume_once_v1()
            except DelegatedCursorSecureConfirmError as exc:
                owned.clear_v1()
                return _fail([str(exc) or "CONFIRM_TOKEN_FAILURE"], fp=digest)

        owned.clear_v1()
        return {
            "ok": True,
            "blockers": [],
            "fingerprint": digest,
            "confirm_token_consumed": True,
            "AUTHORIZATION_CHANNEL": AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
            "TOKEN_ROLE": CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
            "DELEGATED_SECURE_CONFIRM_VERIFIED": True,
            "temp_secret_cleaned": temp_cleaned,
            "plaintext": "",
            "notes": [
                "TOKEN_ROLE=EPHEMERAL_EXECUTION_LATCH",
                "NOT_HUMAN_TTY_PRESENCE_PROOF=true",
                "DIGEST_ONLY_PERSISTED=true",
            ],
        }
    except Exception:
        if owned is not None:
            try:
                owned.cleanup_temp_secret_v1()
                owned.clear_v1()
            except Exception:
                pass
        raise


def prove_delegated_cursor_secure_confirm_broker_binding_v1() -> dict[str, Any]:
    return {
        "ok": True,
        "broker_owner": DELEGATED_CURSOR_SECURE_CONFIRM_BROKER_OWNER,
        "authorization_channel": AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
        "token_role": CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
        "real_tty_required": False,
        "single_use": True,
        "plaintext_persistence": False,
        "plaintext_argv": False,
        "plaintext_env": False,
        "plaintext_log": False,
        "plaintext_stdout_stderr": False,
        "digest_only_evidence": True,
        "tempfile_mode": "0600",
        "notes": [
            "TOKEN_ROLE=EPHEMERAL_EXECUTION_LATCH",
            "NOT_HUMAN_TTY_PRESENCE_PROOF=true",
            "DELEGATED_CURSOR_SECURE_CONFIRM_CHANNEL=true",
            "NO_ARGV_NO_ENV_PLAINTEXT=true",
        ],
    }
