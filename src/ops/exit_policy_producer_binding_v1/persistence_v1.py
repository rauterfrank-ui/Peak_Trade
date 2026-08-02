"""Atomic persistence for Cap 6.5 exit-policy state."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
    COMMIT_MARKER_FILENAME,
    EXIT_STATE_FILENAME,
    MANIFEST_FILENAME,
    OWNER,
    STAGING_DIRNAME_PREFIX,
    STATE_VERSION,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import (
    CanonicalExitPolicyStateV1,
    sha256_hex,
)
from src.ops.exit_policy_producer_binding_v1.reason_codes_v1 import (
    ExitPolicyBindingFailureCodeV1,
)
from src.ops.exit_policy_producer_binding_v1.single_writer_v1 import (
    ExitPolicySingleWriterV1,
)


class ExitPolicyPersistenceError(RuntimeError):
    def __init__(self, code: ExitPolicyBindingFailureCodeV1, detail: str = "") -> None:
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


def load_exit_policy_state_v1(
    state_root: Path,
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
) -> CanonicalExitPolicyStateV1:
    root = Path(state_root)
    path = root / EXIT_STATE_FILENAME
    if not path.is_file():
        raise ExitPolicyPersistenceError(ExitPolicyBindingFailureCodeV1.EXIT_STATE_MISSING)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        state = CanonicalExitPolicyStateV1.from_dict(payload)
    except Exception as exc:  # noqa: BLE001
        raise ExitPolicyPersistenceError(
            ExitPolicyBindingFailureCodeV1.EXIT_STATE_CORRUPT, str(exc)
        ) from exc
    if state.state_version != STATE_VERSION:
        raise ExitPolicyPersistenceError(
            ExitPolicyBindingFailureCodeV1.EXIT_STATE_CORRUPT, "state_version"
        )
    if state.owner != OWNER:
        raise ExitPolicyPersistenceError(ExitPolicyBindingFailureCodeV1.EXIT_STATE_CORRUPT, "owner")
    if expected_repository_sha and state.repository_sha != expected_repository_sha:
        raise ExitPolicyPersistenceError(ExitPolicyBindingFailureCodeV1.REPOSITORY_SHA_MISMATCH)
    if expected_config_digest and state.config_digest != expected_config_digest:
        raise ExitPolicyPersistenceError(ExitPolicyBindingFailureCodeV1.CONFIG_DIGEST_MISMATCH)
    if verify_manifest(root) != 0:
        raise ExitPolicyPersistenceError(
            ExitPolicyBindingFailureCodeV1.EXIT_STATE_CORRUPT, "manifest"
        )
    return state


def persist_exit_policy_state_atomic_v1(
    *,
    state_root: Path,
    state: CanonicalExitPolicyStateV1,
    writer_session_id: str,
) -> Mapping[str, Any]:
    root = Path(state_root)
    root.mkdir(parents=True, exist_ok=True)
    with ExitPolicySingleWriterV1(root, writer_session_id=writer_session_id):
        staging = root / f"{STAGING_DIRNAME_PREFIX}{os.getpid()}"
        if staging.exists():
            import shutil

            shutil.rmtree(staging)
        staging.mkdir(parents=True, exist_ok=True)
        body = json.dumps(state.to_dict(), sort_keys=True, indent=2) + "\n"
        _atomic_write_text(staging / EXIT_STATE_FILENAME, body)
        marker = {
            "commit_sequence": int(state.commit_sequence),
            "state_digest": state.digest(),
            "instrument_id": state.instrument_id,
            "owner": OWNER,
        }
        _atomic_write_text(
            staging / COMMIT_MARKER_FILENAME,
            json.dumps(marker, sort_keys=True, indent=2) + "\n",
        )
        write_manifest(staging, (EXIT_STATE_FILENAME, COMMIT_MARKER_FILENAME))
        import shutil

        for name in (EXIT_STATE_FILENAME, COMMIT_MARKER_FILENAME, MANIFEST_FILENAME):
            os.replace(staging / name, root / name)
        shutil.rmtree(staging, ignore_errors=True)
        return {
            "ok": True,
            "commit_sequence": int(state.commit_sequence),
            "state_digest": state.digest(),
            "manifest_verify_rc": verify_manifest(root),
        }
