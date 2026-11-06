"""Atomic dynamic-scope persistence and restart load."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any, Optional

from src.ops.dynamic_scope_persistence_binding_v1.constants_v1 import (
    COMMIT_MARKER_FILENAME,
    MANIFEST_FILENAME,
    SCOPE_STATE_FILENAME,
    STAGING_DIRNAME_PREFIX,
    STATE_VERSION,
)
from src.ops.dynamic_scope_persistence_binding_v1.models_v1 import (
    CanonicalDynamicScopeStateV1,
    sha256_hex,
)
from src.ops.dynamic_scope_persistence_binding_v1.reason_codes_v1 import (
    DynamicScopeBindingFailureCodeV1,
)
from src.ops.dynamic_scope_persistence_binding_v1.single_writer_v1 import (
    DynamicScopeStateSingleWriterV1,
)


class DynamicScopePersistenceError(RuntimeError):
    def __init__(self, code: DynamicScopeBindingFailureCodeV1, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code.value}:{detail}" if detail else code.value)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def write_manifest(root: Path, relative_files: tuple[str, ...]) -> str:
    lines: list[str] = []
    for rel in sorted(relative_files):
        digest = sha256_hex((root / rel).read_bytes())
        lines.append(f"{digest}  {rel}")
    body = "\n".join(lines) + "\n"
    _atomic_write_text(root / MANIFEST_FILENAME, body)
    return sha256_hex(body)


def verify_manifest(root: Path) -> dict[str, Any]:
    manifest = Path(root) / MANIFEST_FILENAME
    if not manifest.is_file():
        raise DynamicScopePersistenceError(
            DynamicScopeBindingFailureCodeV1.MANIFEST_VERIFY_FAILED,
            "MANIFEST_MISSING",
        )
    errors: list[str] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, rel = line.split(None, 1)
        path = Path(root) / rel
        if not path.is_file():
            errors.append(f"MISSING:{rel}")
            continue
        actual = sha256_hex(path.read_bytes())
        if actual != digest:
            errors.append(f"DIGEST_MISMATCH:{rel}")
    if errors:
        raise DynamicScopePersistenceError(
            DynamicScopeBindingFailureCodeV1.MANIFEST_VERIFY_FAILED,
            ";".join(errors),
        )
    return {"ok": True, "manifest_path": str(manifest)}


def scope_state_path(state_root: Path) -> Path:
    return Path(state_root) / SCOPE_STATE_FILENAME


def commit_marker_path(state_root: Path) -> Path:
    return Path(state_root) / COMMIT_MARKER_FILENAME


def prior_commit_exists(state_root: Path) -> bool:
    root = Path(state_root)
    return commit_marker_path(root).is_file() or scope_state_path(root).is_file()


def load_dynamic_scope_state_v1(
    state_root: Path,
    *,
    require_present: bool = False,
    expected_repository_sha: str | None = None,
    expected_config_digest: str | None = None,
    expected_instrument_id: str | None = None,
    allow_missing_before_first_state: bool = True,
) -> Optional[CanonicalDynamicScopeStateV1]:
    root = Path(state_root)
    path = scope_state_path(root)
    marker = commit_marker_path(root)
    if not path.is_file():
        if require_present or (marker.is_file() and not allow_missing_before_first_state):
            code = (
                DynamicScopeBindingFailureCodeV1.CHECKPOINT_MISSING_AFTER_PRIOR_COMMIT
                if marker.is_file()
                else DynamicScopeBindingFailureCodeV1.CHECKPOINT_MISSING_BEFORE_FIRST_STATE
            )
            raise DynamicScopePersistenceError(code, str(path))
        if marker.is_file():
            raise DynamicScopePersistenceError(
                DynamicScopeBindingFailureCodeV1.CHECKPOINT_MISSING_AFTER_PRIOR_COMMIT,
                str(path),
            )
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        state = CanonicalDynamicScopeStateV1.from_dict(payload)
    except Exception as exc:  # noqa: BLE001
        raise DynamicScopePersistenceError(
            DynamicScopeBindingFailureCodeV1.CORRUPTED_CHECKPOINT,
            str(exc),
        ) from exc
    if state.state_version != STATE_VERSION:
        raise DynamicScopePersistenceError(
            DynamicScopeBindingFailureCodeV1.STATE_VERSION_MISMATCH,
            state.state_version,
        )
    if expected_repository_sha is not None and state.repository_sha != expected_repository_sha:
        raise DynamicScopePersistenceError(
            DynamicScopeBindingFailureCodeV1.REPOSITORY_SHA_MISMATCH,
            f"{state.repository_sha}!={expected_repository_sha}",
        )
    if expected_config_digest is not None and state.config_digest != expected_config_digest:
        raise DynamicScopePersistenceError(
            DynamicScopeBindingFailureCodeV1.CONFIG_DIGEST_MISMATCH,
            f"{state.config_digest}!={expected_config_digest}",
        )
    if expected_instrument_id is not None and state.instrument_id != expected_instrument_id:
        raise DynamicScopePersistenceError(
            DynamicScopeBindingFailureCodeV1.INSTRUMENT_ISOLATION_VIOLATION,
            f"{state.instrument_id}!={expected_instrument_id}",
        )
    return state


def persist_dynamic_scope_state_atomic_v1(
    *,
    state_root: Path,
    state: CanonicalDynamicScopeStateV1,
    writer: DynamicScopeStateSingleWriterV1,
    interrupt_after_state_before_marker: bool = False,
    interrupt_before_state_write: bool = False,
    interrupt_during_state_write: bool = False,
) -> dict[str, Any]:
    """Atomically persist scope state + commit marker. Serialization has no authority."""
    writer.assert_held()
    root = Path(state_root)
    root.mkdir(parents=True, exist_ok=True)
    if interrupt_before_state_write:
        raise DynamicScopePersistenceError(
            DynamicScopeBindingFailureCodeV1.PERSISTENCE_INTERRUPTION,
            "INJECTED_INTERRUPT_BEFORE_STATE_WRITE",
        )
    staging = root / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"
    staging.mkdir(parents=True, exist_ok=False)
    try:
        if not state.commit_identity:
            commit_sequence = int(state.commit_sequence) + 1
            commit_identity = sha256_hex(
                f"{state.scope_session_id}:{commit_sequence}:{state.state_digest()}"
            )
            state = state.with_commit(
                commit_identity=commit_identity,
                commit_sequence=commit_sequence,
            )
        durable = state.to_dict()
        marker = {
            "commit_identity": state.commit_identity,
            "commit_sequence": state.commit_sequence,
            "scope_session_id": state.scope_session_id,
            "instrument_id": state.instrument_id,
            "state_digest": state.state_digest(),
            "repository_sha": state.repository_sha,
            "config_digest": state.config_digest,
            "state_version": state.state_version,
            "previous_state_digest": state.previous_state_digest,
        }
        if interrupt_during_state_write:
            raise DynamicScopePersistenceError(
                DynamicScopeBindingFailureCodeV1.PERSISTENCE_INTERRUPTION,
                "INJECTED_INTERRUPT_DURING_STATE_WRITE",
            )
        (staging / SCOPE_STATE_FILENAME).write_text(
            json.dumps(durable, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        if interrupt_after_state_before_marker:
            raise DynamicScopePersistenceError(
                DynamicScopeBindingFailureCodeV1.PERSISTENCE_INTERRUPTION,
                "INJECTED_INTERRUPT_AFTER_STATE_BEFORE_MARKER",
            )
        (staging / COMMIT_MARKER_FILENAME).write_text(
            json.dumps(marker, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        for name in (SCOPE_STATE_FILENAME, COMMIT_MARKER_FILENAME):
            src = staging / name
            dst = root / name
            os.replace(src, dst)
        write_manifest(root, (SCOPE_STATE_FILENAME, COMMIT_MARKER_FILENAME))
        verify_manifest(root)
        return {
            "ok": True,
            "commit_identity": state.commit_identity,
            "commit_sequence": state.commit_sequence,
            "state_digest": state.state_digest(),
            "state": state,
        }
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def assert_no_silent_reinitialization_v1(
    *,
    state_root: Path,
    loaded: Optional[CanonicalDynamicScopeStateV1],
    initializing_fresh: bool,
) -> None:
    """After any prior durable commit, fresh init without load is forbidden."""
    if initializing_fresh and prior_commit_exists(state_root) and loaded is None:
        raise DynamicScopePersistenceError(
            DynamicScopeBindingFailureCodeV1.SILENT_REINITIALIZATION_BLOCKED,
            str(state_root),
        )
