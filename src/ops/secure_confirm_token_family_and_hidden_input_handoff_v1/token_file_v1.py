"""Hardened ephemeral confirm-token file create/load/cleanup (O3 exception path)."""

from __future__ import annotations

import atexit
import os
import signal
import stat
from pathlib import Path
from typing import Callable, Optional

from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.constants_v1 import (
    TOKEN_DIRECTORY_MODE,
    TOKEN_FILE_MODE,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.errors_v1 import (
    TokenFileSecurityError,
)

_CLEANUP_REGISTRY: dict[str, Path] = {}
_SIGNAL_HANDLERS_INSTALLED = False
_PREVIOUS_SIGNAL_HANDLERS: dict[int, object] = {}


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def assert_token_path_location_v1(
    path: Path,
    *,
    repository_root: Path,
    evidence_root: Path,
) -> Path:
    resolved = path if path.is_absolute() else path.absolute()
    # Reject before create: must not resolve through symlinks for parent chain identity.
    if resolved.exists() or resolved.is_symlink():
        # Existence is handled by exclusive-create callers; location still checked.
        pass
    if _is_under(resolved, repository_root):
        raise TokenFileSecurityError("TOKEN_PATH_INSIDE_REPOSITORY")
    if _is_under(resolved, evidence_root):
        raise TokenFileSecurityError("TOKEN_PATH_INSIDE_EVIDENCE_ROOT")
    return resolved


def _ensure_parent_dir_secure_v1(parent: Path) -> None:
    if parent.exists():
        if parent.is_symlink():
            raise TokenFileSecurityError("TOKEN_DIRECTORY_SYMLINK_FORBIDDEN")
        if not parent.is_dir():
            raise TokenFileSecurityError("TOKEN_DIRECTORY_NOT_DIRECTORY")
        st = parent.stat()
        if stat.S_IMODE(st.st_mode) != TOKEN_DIRECTORY_MODE:
            os.chmod(parent, TOKEN_DIRECTORY_MODE)
        if st.st_uid != os.getuid():
            raise TokenFileSecurityError("TOKEN_DIRECTORY_OWNER_UID_MISMATCH")
    else:
        parent.mkdir(mode=TOKEN_DIRECTORY_MODE, parents=True, exist_ok=False)
        os.chmod(parent, TOKEN_DIRECTORY_MODE)


def _verify_regular_owned_file_v1(path: Path) -> None:
    if path.is_symlink():
        raise TokenFileSecurityError("TOKEN_FILE_SYMLINK_FOLLOW_FORBIDDEN")
    if not path.is_file():
        raise TokenFileSecurityError("TOKEN_FILE_NOT_REGULAR")
    st = os.lstat(path)
    if not stat.S_ISREG(st.st_mode):
        raise TokenFileSecurityError("TOKEN_FILE_NOT_REGULAR")
    if stat.S_IMODE(st.st_mode) != TOKEN_FILE_MODE:
        raise TokenFileSecurityError("TOKEN_FILE_MODE_NOT_0600")
    if st.st_uid != os.getuid():
        raise TokenFileSecurityError("TOKEN_FILE_OWNER_UID_MISMATCH")


def create_confirm_token_file_exclusive_v1(
    *,
    path: Path,
    token: str,
    repository_root: Path,
    evidence_root: Path,
    register_cleanup: bool = True,
) -> Path:
    """Create token file with O_EXCL, mode 0600, parent 0700, location + owner checks."""
    if not isinstance(token, str) or not token:
        raise TokenFileSecurityError("confirm_token_empty")
    if "\n" in token or "\r" in token:
        raise TokenFileSecurityError("confirm_token_multiline_forbidden")
    target = assert_token_path_location_v1(
        path, repository_root=repository_root, evidence_root=evidence_root
    )
    if target.exists() or target.is_symlink():
        raise TokenFileSecurityError("TOKEN_FILE_EXISTING_TARGET_REJECTED")
    _ensure_parent_dir_secure_v1(target.parent)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        fd = os.open(str(target), flags, TOKEN_FILE_MODE)
    except FileExistsError as exc:
        raise TokenFileSecurityError("TOKEN_FILE_EXISTING_TARGET_REJECTED") from exc
    try:
        os.write(fd, (token + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    os.chmod(target, TOKEN_FILE_MODE)
    _verify_regular_owned_file_v1(target)
    if register_cleanup:
        register_token_file_cleanup_v1(target)
    return target


def load_confirm_token_file_secure_v1(
    *,
    path: Path,
    repository_root: Path,
    evidence_root: Path,
) -> str:
    target = assert_token_path_location_v1(
        path, repository_root=repository_root, evidence_root=evidence_root
    )
    if target.is_symlink():
        raise TokenFileSecurityError("TOKEN_FILE_SYMLINK_FOLLOW_FORBIDDEN")
    if not target.exists():
        raise TokenFileSecurityError("CONFIRM_TOKEN_FILE_MISSING")
    _verify_regular_owned_file_v1(target)
    raw = target.read_text(encoding="utf-8")
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    if len(lines) != 1:
        raise TokenFileSecurityError("CONFIRM_TOKEN_FILE_INVALID")
    return lines[0]


def delete_confirm_token_file_v1(path: Path) -> bool:
    """Best-effort secure delete; returns True if file absent after call."""
    try:
        p = Path(path)
        key = str(p)
        _CLEANUP_REGISTRY.pop(key, None)
        if p.is_symlink():
            p.unlink(missing_ok=True)  # type: ignore[call-arg]
            return not p.exists()
        if p.exists():
            # Overwrite then unlink (best-effort; not a secure wipe guarantee).
            try:
                size = p.stat().st_size
                with open(p, "r+b", buffering=0) as fh:
                    fh.write(b"\0" * max(size, 1))
                    fh.flush()
                    os.fsync(fh.fileno())
            except OSError:
                pass
            p.unlink()
        return not Path(path).exists()
    except OSError:
        return not Path(path).exists()


def register_token_file_cleanup_v1(path: Path) -> None:
    global _SIGNAL_HANDLERS_INSTALLED
    _CLEANUP_REGISTRY[str(path)] = Path(path)
    atexit.register(cleanup_all_registered_token_files_v1)
    if not _SIGNAL_HANDLERS_INSTALLED:
        for sig in (signal.SIGTERM, signal.SIGINT):
            previous = signal.getsignal(sig)
            _PREVIOUS_SIGNAL_HANDLERS[int(sig)] = previous

            def _handler(
                signum: int,
                frame: object,
                _prev: object = previous,
                _sig: signal.Signals = sig,
            ) -> None:
                cleanup_all_registered_token_files_v1()
                if callable(_prev):
                    _prev(signum, frame)  # type: ignore[misc]
                elif _prev == signal.SIG_DFL:
                    signal.signal(_sig, signal.SIG_DFL)
                    os.kill(os.getpid(), int(_sig))

            try:
                signal.signal(sig, _handler)
            except (ValueError, OSError):
                # Not in main thread — atexit still covers normal exits.
                pass
        _SIGNAL_HANDLERS_INSTALLED = True


def cleanup_all_registered_token_files_v1() -> dict[str, bool]:
    results: dict[str, bool] = {}
    for key, path in list(_CLEANUP_REGISTRY.items()):
        results[key] = delete_confirm_token_file_v1(path)
    return results


def unregister_token_file_cleanup_v1(path: Path) -> None:
    _CLEANUP_REGISTRY.pop(str(path), None)


class ConfirmTokenFileLeaseV1:
    """Context manager that creates, yields path, and always cleans up."""

    def __init__(
        self,
        *,
        path: Path,
        token: str,
        repository_root: Path,
        evidence_root: Path,
    ) -> None:
        self.path = path
        self._token = token
        self.repository_root = repository_root
        self.evidence_root = evidence_root
        self.created: Optional[Path] = None

    def __enter__(self) -> Path:
        self.created = create_confirm_token_file_exclusive_v1(
            path=self.path,
            token=self._token,
            repository_root=self.repository_root,
            evidence_root=self.evidence_root,
            register_cleanup=True,
        )
        # Drop local plaintext reference ASAP.
        self._token = ""
        return self.created

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self.created is not None:
            delete_confirm_token_file_v1(self.created)
            unregister_token_file_cleanup_v1(self.created)
        return None
