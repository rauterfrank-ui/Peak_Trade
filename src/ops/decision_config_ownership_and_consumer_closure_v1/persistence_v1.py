"""Atomic Cap 6.3 config-binding persistence and restart load."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Optional

from src.ops.decision_config_ownership_and_consumer_closure_v1.constants_v1 import (
    COMMIT_MARKER_FILENAME,
    CONFIG_STATE_FILENAME,
    MANIFEST_FILENAME,
    STAGING_DIRNAME_PREFIX,
    STATE_VERSION,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.models_v1 import (
    DecisionConfigBindingStateV1,
    sha256_hex,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.reason_codes_v1 import (
    DecisionConfigFailureCodeV1,
)


class DecisionConfigPersistenceError(RuntimeError):
    def __init__(self, code: DecisionConfigFailureCodeV1, detail: str = "") -> None:
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
        raise DecisionConfigPersistenceError(
            DecisionConfigFailureCodeV1.MANIFEST_VERIFY_FAILED,
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
        raise DecisionConfigPersistenceError(
            DecisionConfigFailureCodeV1.MANIFEST_VERIFY_FAILED,
            ",".join(errors),
        )
    return {"ok": True, "manifest": str(manifest)}


def prior_commit_exists(root: Path) -> bool:
    return (Path(root) / COMMIT_MARKER_FILENAME).is_file()


def persist_decision_config_state_atomic_v1(
    state: DecisionConfigBindingStateV1,
    *,
    state_root: Path,
) -> DecisionConfigBindingStateV1:
    root = Path(state_root)
    root.mkdir(parents=True, exist_ok=True)
    staging = root / f"{STAGING_DIRNAME_PREFIX}{os.getpid()}"
    if staging.exists():
        for child in staging.iterdir():
            child.unlink()
        staging.rmdir()
    staging.mkdir(parents=True, exist_ok=True)
    try:
        payload = state.to_dict()
        state_path = staging / CONFIG_STATE_FILENAME
        marker_path = staging / COMMIT_MARKER_FILENAME
        _atomic_write_text(state_path, json.dumps(payload, sort_keys=True, indent=2) + "\n")
        marker = {
            "state_version": STATE_VERSION,
            "config_digest": state.config_digest,
            "config_version": state.config_version,
            "commit_sequence": int(state.commit_sequence),
            "state_digest": state.state_digest(),
        }
        _atomic_write_text(marker_path, json.dumps(marker, sort_keys=True, indent=2) + "\n")
        write_manifest(staging, (CONFIG_STATE_FILENAME, COMMIT_MARKER_FILENAME))
        # Commit staging into root.
        for name in (CONFIG_STATE_FILENAME, COMMIT_MARKER_FILENAME, MANIFEST_FILENAME):
            os.replace(staging / name, root / name)
    finally:
        if staging.exists():
            for child in list(staging.iterdir()):
                child.unlink(missing_ok=True)
            staging.rmdir()
    return state


def load_decision_config_state_v1(
    state_root: Path,
    *,
    expected_config_digest: Optional[str] = None,
    expected_config_version: Optional[str] = None,
) -> DecisionConfigBindingStateV1:
    root = Path(state_root)
    state_path = root / CONFIG_STATE_FILENAME
    if not state_path.is_file():
        raise DecisionConfigPersistenceError(
            DecisionConfigFailureCodeV1.CONFIG_PATH_MISSING,
            str(state_path),
        )
    verify_manifest(root)
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
        state = DecisionConfigBindingStateV1.from_dict(payload)
    except Exception as exc:  # noqa: BLE001
        raise DecisionConfigPersistenceError(
            DecisionConfigFailureCodeV1.STATE_CORRUPT,
            str(exc),
        ) from exc
    if state.state_version != STATE_VERSION:
        raise DecisionConfigPersistenceError(
            DecisionConfigFailureCodeV1.CONFIG_VERSION_INCOMPATIBLE,
            f"state_version={state.state_version}",
        )
    if expected_config_version is not None and state.config_version != expected_config_version:
        raise DecisionConfigPersistenceError(
            DecisionConfigFailureCodeV1.CONFIG_VERSION_INCOMPATIBLE,
            f"persisted={state.config_version}:expected={expected_config_version}",
        )
    if expected_config_digest is not None and state.config_digest != expected_config_digest:
        raise DecisionConfigPersistenceError(
            DecisionConfigFailureCodeV1.CONFIG_DIGEST_MISMATCH,
            f"persisted={state.config_digest}:expected={expected_config_digest}",
        )
    return state
