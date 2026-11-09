"""Atomic persistence for Cap 6.5 exit-policy state."""

from __future__ import annotations

import json
import math
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
    canonical_digest_v1,
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
    expected = {EXIT_STATE_FILENAME, COMMIT_MARKER_FILENAME}
    seen: set[str] = set()
    try:
        for line in manifest.read_text(encoding="utf-8").splitlines():
            digest, rel = line.split("  ", 1)
            if rel not in expected or rel in seen:
                return 1
            seen.add(rel)
            path = Path(root) / rel
            if not path.is_file() or sha256_hex(path.read_bytes()) != digest:
                return 1
    except (ValueError, OSError):
        return 1
    if seen != expected:
        return 1
    return 0


def prior_commit_exists(state_root: Path) -> bool:
    return (Path(state_root) / COMMIT_MARKER_FILENAME).is_file()


def load_exit_policy_state_v1(
    state_root: Path,
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    expected_instrument_id: str | None = None,
) -> CanonicalExitPolicyStateV1:
    root = Path(state_root)
    path = root / EXIT_STATE_FILENAME
    if not path.is_file():
        raise ExitPolicyPersistenceError(ExitPolicyBindingFailureCodeV1.EXIT_STATE_MISSING)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        fields = set(CanonicalExitPolicyStateV1.__dataclass_fields__)
        optional = {
            "current_cursor_publication",
            "simulated_accounting_progress",
            "simulated_accounting_close",
            "pending_rotation_close",
        }
        if not isinstance(payload, dict) or not fields - optional <= set(payload) <= fields:
            raise ValueError("exit state field contract")
        for name in optional:
            if name in payload and not isinstance(payload[name], dict):
                raise ValueError("optional exit composition object required")
        if type(payload["has_open_position"]) is not bool:
            raise ValueError("exit position boolean")
        if type(payload["commit_sequence"]) is not int:
            raise ValueError("exit state commit sequence")
        for field in ("commit_sequence", "entry_trading_epoch"):
            value = payload[field]
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError("exit state integer")
        for field in (
            "entry_price",
            "entry_event_time",
            "time_exit_max_hold_seconds",
            "last_evaluated_event_time",
        ):
            value = payload[field]
            if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
                raise ValueError("exit state finite numeric")
        state = CanonicalExitPolicyStateV1.from_dict(payload)
        if state.pending_rotation_close is not None:
            from src.ops.full_core_live_path_composition_root_v1.current_productive_rotation_close_v1 import (
                verify_pending_rotation_close_v1,
            )

            verify_pending_rotation_close_v1(state.pending_rotation_close)
            if (
                state.has_open_position
                and state.pending_exit_class != "time_exit"
                or not state.has_open_position
                and (state.pending_exit_class or state.simulated_accounting_close is None)
            ):
                raise ValueError("rotation close without original pending exit")
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
    if expected_instrument_id is not None and state.instrument_id != expected_instrument_id:
        raise ExitPolicyPersistenceError(ExitPolicyBindingFailureCodeV1.INSTRUMENT_MISMATCH)
    if expected_repository_sha and state.repository_sha != expected_repository_sha:
        raise ExitPolicyPersistenceError(ExitPolicyBindingFailureCodeV1.REPOSITORY_SHA_MISMATCH)
    if expected_config_digest and state.config_digest != expected_config_digest:
        raise ExitPolicyPersistenceError(ExitPolicyBindingFailureCodeV1.CONFIG_DIGEST_MISMATCH)
    if verify_manifest(root) != 0:
        raise ExitPolicyPersistenceError(
            ExitPolicyBindingFailureCodeV1.EXIT_STATE_CORRUPT, "manifest"
        )
    try:
        marker = json.loads((root / COMMIT_MARKER_FILENAME).read_text(encoding="utf-8"))
        if not isinstance(marker, dict) or type(marker.get("commit_sequence")) is not int:
            raise ValueError("commit marker sequence")
        expected_marker = {
            "commit_sequence": state.commit_sequence,
            "state_digest": canonical_digest_v1(payload),
            "instrument_id": state.instrument_id,
            "owner": OWNER,
        }
        if marker != expected_marker:
            raise ValueError("commit marker differs from canonical state")
    except (ValueError, OSError) as exc:
        raise ExitPolicyPersistenceError(
            ExitPolicyBindingFailureCodeV1.EXIT_STATE_CORRUPT, "commit_marker"
        ) from exc
    return state


def persist_exit_policy_state_atomic_v1(
    *,
    state_root: Path,
    state: CanonicalExitPolicyStateV1,
    writer_session_id: str,
    expected_prior_sequence: int | None = None,
) -> Mapping[str, Any]:
    root = Path(state_root)
    root.mkdir(parents=True, exist_ok=True)
    with ExitPolicySingleWriterV1(root, writer_session_id=writer_session_id):
        if expected_prior_sequence is not None:
            present = any(
                (root / name).exists()
                for name in (EXIT_STATE_FILENAME, COMMIT_MARKER_FILENAME, MANIFEST_FILENAME)
            )
            if expected_prior_sequence == -1:
                if present or state.commit_sequence != 1:
                    raise ExitPolicyPersistenceError(
                        ExitPolicyBindingFailureCodeV1.WRITER_CONFLICT, "state_already_present"
                    )
            elif expected_prior_sequence >= 0:
                prior = load_exit_policy_state_v1(
                    root,
                    expected_repository_sha=state.repository_sha,
                    expected_config_digest=state.config_digest,
                    expected_instrument_id=state.instrument_id,
                )
                if (
                    prior.commit_sequence != expected_prior_sequence
                    or state.commit_sequence != expected_prior_sequence + 1
                ):
                    raise ExitPolicyPersistenceError(
                        ExitPolicyBindingFailureCodeV1.WRITER_CONFLICT, "commit_sequence_conflict"
                    )
            else:
                raise ValueError("invalid expected exit-policy commit sequence")
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
        if verify_manifest(root) != 0:
            raise ExitPolicyPersistenceError(
                ExitPolicyBindingFailureCodeV1.EXIT_STATE_CORRUPT, "publication_readback"
            )
        return {
            "ok": True,
            "commit_sequence": int(state.commit_sequence),
            "state_digest": state.digest(),
            "manifest_verify_rc": verify_manifest(root),
        }
