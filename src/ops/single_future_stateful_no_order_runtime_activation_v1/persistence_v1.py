"""Atomic persistence for Cap 7.2 activation state."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.single_future_stateful_no_order_runtime_activation_v1.constants_v1 import (
    ACTIVATION_STATE_FILENAME,
    COMMIT_MARKER_FILENAME,
    MANIFEST_FILENAME,
    OWNER,
    STAGING_DIRNAME_PREFIX,
    STATE_VERSION,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.models_v1 import (
    CanonicalActivationStateV1,
    sha256_hex,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.reason_codes_v1 import (
    ActivationFailureCodeV1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.single_writer_v1 import (
    ActivationSingleWriterV1,
)


class ActivationPersistenceError(RuntimeError):
    def __init__(self, code: ActivationFailureCodeV1, detail: str = "") -> None:
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
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


def write_manifest(root: Path, relative_files: tuple[str, ...]) -> str:
    lines: list[str] = []
    for rel in sorted(relative_files):
        digest = sha256_hex((root / rel).read_bytes())
        lines.append(f"{digest}  {rel}")
    body = "\n".join(lines) + "\n"
    _atomic_write_text(root / MANIFEST_FILENAME, body)
    return sha256_hex(body.encode("utf-8"))


def verify_manifest(root: Path) -> int:
    manifest = Path(root) / MANIFEST_FILENAME
    if not manifest.is_file():
        return 2
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        path = Path(root) / rel
        if not path.is_file():
            return 1
        if sha256_hex(path.read_bytes()) != digest:
            return 1
    return 0


def prior_commit_exists(state_root: Path) -> bool:
    return (Path(state_root) / COMMIT_MARKER_FILENAME).is_file()


def load_activation_state_v1(
    state_root: Path, *, require_present: bool = False
) -> Optional[CanonicalActivationStateV1]:
    path = Path(state_root) / ACTIVATION_STATE_FILENAME
    if not path.is_file():
        if require_present:
            raise ActivationPersistenceError(
                ActivationFailureCodeV1.MISSING_ACTIVATION_STATE, str(path)
            )
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ActivationPersistenceError(
                ActivationFailureCodeV1.CORRUPT_CHECKPOINT, "not_object"
            )
        state = CanonicalActivationStateV1.from_dict(payload)
        if state.state_version != STATE_VERSION:
            raise ActivationPersistenceError(
                ActivationFailureCodeV1.CORRUPT_CHECKPOINT,
                f"state_version:{state.state_version}",
            )
        return state
    except ActivationPersistenceError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ActivationPersistenceError(
            ActivationFailureCodeV1.CORRUPT_CHECKPOINT, str(exc)
        ) from exc


def persist_activation_state_atomic_v1(
    state_root: Path,
    state: CanonicalActivationStateV1,
    *,
    writer_session_id: str,
    simulate_crash_after_staging: bool = False,
) -> dict[str, Any]:
    root = Path(state_root)
    root.mkdir(parents=True, exist_ok=True)
    staging = root / f"{STAGING_DIRNAME_PREFIX}{os.getpid()}"
    staging.mkdir(parents=True, exist_ok=True)
    payload = state.to_dict()
    payload["owner"] = OWNER
    body = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    marker = {
        "owner": OWNER,
        "commit_sequence": int(state.commit_sequence),
        "repository_sha": state.repository_sha,
        "config_digest": state.config_digest,
        "status": state.status.value,
        "writer_session_id": writer_session_id,
    }
    marker_body = json.dumps(marker, sort_keys=True, indent=2) + "\n"
    (staging / ACTIVATION_STATE_FILENAME).write_text(body, encoding="utf-8")
    (staging / COMMIT_MARKER_FILENAME).write_text(marker_body, encoding="utf-8")
    write_manifest(staging, (ACTIVATION_STATE_FILENAME, COMMIT_MARKER_FILENAME))
    if simulate_crash_after_staging:
        raise ActivationPersistenceError(
            ActivationFailureCodeV1.ACTIVATION_COMMIT_CRASH, "simulated_crash"
        )
    with ActivationSingleWriterV1(root, writer_session_id=writer_session_id):
        for name in (ACTIVATION_STATE_FILENAME, COMMIT_MARKER_FILENAME, MANIFEST_FILENAME):
            os.replace(staging / name, root / name)
    try:
        staging.rmdir()
    except OSError:
        pass
    if verify_manifest(root) != 0:
        raise ActivationPersistenceError(
            ActivationFailureCodeV1.CORRUPT_CHECKPOINT, "post_commit_manifest"
        )
    return {"ok": True, "commit_sequence": int(state.commit_sequence), "path": str(root)}
