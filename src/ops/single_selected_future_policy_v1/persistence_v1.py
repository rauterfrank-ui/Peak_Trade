"""Atomic persistence + load/validate for single selected future selections."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.single_selected_future_policy_v1.constants_v1 import (
    CAPABILITY_ID,
    EVIDENCE_FILENAME,
    MANIFEST_FILENAME,
    MAX_POSITIONS_EFFECTIVE,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    SELECTED_FUTURE_COUNT,
    SELECTION_FILENAME,
    SELECTION_STATES,
    STAGING_DIRNAME_PREFIX,
    STATE_NO_SELECTION,
)
from src.ops.single_selected_future_policy_v1.models_v1 import (
    SingleSelectedFutureSelectionV1,
    canonical_json_dumps,
    sha256_hex,
)
from src.ops.single_selected_future_policy_v1.reason_codes_v1 import SelectionFailureCodeV1
from src.ops.single_selected_future_policy_v1.single_writer_v1 import (
    DuplicateSelectionWriterError,
    SingleSelectedFutureSingleWriterV1,
)


class SelectionPersistenceError(RuntimeError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


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
        raise SelectionPersistenceError(
            SelectionFailureCodeV1.CORRUPT_PERSISTED_SELECTION.value, "MANIFEST_MISSING"
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
        raise SelectionPersistenceError(
            SelectionFailureCodeV1.CORRUPT_PERSISTED_SELECTION.value,
            ";".join(errors),
        )
    return {"ok": True, "manifest_path": str(manifest)}


@dataclass(frozen=True)
class SelectionLoadResultV1:
    ok: bool
    selection: Optional[SingleSelectedFutureSelectionV1]
    failure_codes: tuple[str, ...]
    detail: str = ""
    alpha_blocked: bool = True


def validate_selection_bindings_v1(
    selection: SingleSelectedFutureSelectionV1,
    *,
    expected_repository_sha: str | None = None,
    expected_config_digest: str | None = None,
    expected_schema_version: str = SCHEMA_VERSION,
) -> SelectionLoadResultV1:
    failures: list[str] = []
    if selection.schema_version != expected_schema_version:
        failures.append(SelectionFailureCodeV1.SCHEMA_MISMATCH.value)
    if selection.capability_id != CAPABILITY_ID:
        failures.append(SelectionFailureCodeV1.SCHEMA_MISMATCH.value)
    if selection.producer_version != PRODUCER_VERSION:
        failures.append(SelectionFailureCodeV1.SCHEMA_MISMATCH.value)
    if selection.state not in SELECTION_STATES:
        failures.append(SelectionFailureCodeV1.CORRUPT_PERSISTED_SELECTION.value)
    recomputed = selection.compute_integrity_digest()
    if not selection.integrity_digest or selection.integrity_digest != recomputed:
        failures.append(SelectionFailureCodeV1.INTEGRITY_FAILURE.value)
        failures.append(SelectionFailureCodeV1.CORRUPT_PERSISTED_SELECTION.value)
    if expected_repository_sha is not None and selection.repository_sha != expected_repository_sha:
        failures.append(SelectionFailureCodeV1.REPOSITORY_SHA_MISMATCH.value)
    if expected_config_digest is not None and selection.config_digest != expected_config_digest:
        failures.append(SelectionFailureCodeV1.CONFIG_DIGEST_MISMATCH.value)
    if selection.dashboard_input_used:
        failures.append(SelectionFailureCodeV1.DASHBOARD_INPUT_FORBIDDEN.value)
    if selection.allowlist_input_used:
        failures.append(SelectionFailureCodeV1.ALLOWLIST_INPUT_FORBIDDEN.value)
    if selection.manual_override_used:
        failures.append(SelectionFailureCodeV1.MANUAL_OVERRIDE_FORBIDDEN.value)
    if int(selection.selected_future_count) != SELECTED_FUTURE_COUNT:
        failures.append(SelectionFailureCodeV1.MAX_POSITIONS_VIOLATION.value)
    if int(selection.max_positions_effective) != MAX_POSITIONS_EFFECTIVE:
        failures.append(SelectionFailureCodeV1.MAX_POSITIONS_VIOLATION.value)
    if selection.multi_future_runtime_authorized:
        failures.append(SelectionFailureCodeV1.MULTI_FUTURE_UNAUTHORIZED.value)
    if selection.alpha_authority_for_replacement:
        failures.append(SelectionFailureCodeV1.ALPHA_BLOCKED.value)
    if failures:
        return SelectionLoadResultV1(
            False,
            selection,
            tuple(sorted(set(failures))),
            "VALIDATE_FAIL",
            alpha_blocked=True,
        )
    alpha_blocked = selection.state == STATE_NO_SELECTION or not selection.alpha_allowed
    return SelectionLoadResultV1(True, selection, (), "VALIDATE_OK", alpha_blocked=alpha_blocked)


def load_and_validate_selection_v1(
    state_root: Path,
    *,
    expected_repository_sha: str | None = None,
    expected_config_digest: str | None = None,
    require_manifest: bool = True,
) -> SelectionLoadResultV1:
    root = Path(state_root)
    path = root / SELECTION_FILENAME
    if not path.is_file():
        return SelectionLoadResultV1(
            False,
            None,
            (SelectionFailureCodeV1.CORRUPT_PERSISTED_SELECTION.value,),
            "SELECTION_MISSING",
            alpha_blocked=True,
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return SelectionLoadResultV1(
            False,
            None,
            (SelectionFailureCodeV1.CORRUPT_PERSISTED_SELECTION.value,),
            f"UNREADABLE:{exc}",
            alpha_blocked=True,
        )
    if not isinstance(payload, Mapping):
        return SelectionLoadResultV1(
            False,
            None,
            (SelectionFailureCodeV1.RANKING_SNAPSHOT_INVALID.value,),
            "SELECTION_NOT_OBJECT",
            alpha_blocked=True,
        )
    try:
        selection = SingleSelectedFutureSelectionV1.from_dict(payload)
    except Exception as exc:  # noqa: BLE001
        return SelectionLoadResultV1(
            False,
            None,
            (SelectionFailureCodeV1.CORRUPT_PERSISTED_SELECTION.value,),
            f"PARSE:{exc}",
            alpha_blocked=True,
        )
    if require_manifest:
        try:
            verify_manifest(root)
        except SelectionPersistenceError as exc:
            return SelectionLoadResultV1(
                False, selection, (exc.failure_code,), str(exc), alpha_blocked=True
            )
    return validate_selection_bindings_v1(
        selection,
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
    )


def _existing_selection_conflict_v1(
    root: Path,
    selection: SingleSelectedFutureSelectionV1,
) -> Optional[str]:
    path = root / SELECTION_FILENAME
    if not path.is_file():
        return None
    try:
        existing = SingleSelectedFutureSelectionV1.from_dict(
            json.loads(path.read_text(encoding="utf-8"))
        )
    except Exception:  # noqa: BLE001
        return SelectionFailureCodeV1.CORRUPT_PERSISTED_SELECTION.value
    if existing.selection_id != selection.selection_id:
        return None
    if existing.integrity_digest == selection.integrity_digest:
        return None
    return SelectionFailureCodeV1.SELECTION_ID_CONTENT_CONFLICT.value


def persist_selection_bundle_atomic_v1(
    *,
    state_root: Path,
    writer: SingleSelectedFutureSingleWriterV1,
    selection: SingleSelectedFutureSelectionV1,
    evidence: Mapping[str, Any],
    simulate_partial_write: bool = False,
    simulate_write_failure: bool = False,
    simulate_crash_after_persist_before_confirm: bool = False,
) -> dict[str, Any]:
    """Atomically stage→publish selection + evidence + manifest, then verify."""
    try:
        writer.assert_held()
    except DuplicateSelectionWriterError as exc:
        raise SelectionPersistenceError(exc.failure_code, str(exc)) from exc

    if simulate_write_failure:
        raise SelectionPersistenceError(
            SelectionFailureCodeV1.PERSISTENCE_WRITE_FAILURE.value,
            "SIMULATED",
        )

    root = Path(state_root)
    root.mkdir(parents=True, exist_ok=True)

    conflict = _existing_selection_conflict_v1(root, selection)
    if conflict == SelectionFailureCodeV1.SELECTION_ID_CONTENT_CONFLICT.value:
        raise SelectionPersistenceError(conflict, selection.selection_id)
    if conflict == SelectionFailureCodeV1.CORRUPT_PERSISTED_SELECTION.value:
        raise SelectionPersistenceError(conflict, "EXISTING_UNREADABLE")

    staging = root / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"
    staging.mkdir(parents=True, exist_ok=False)
    try:
        selection_text = json.dumps(selection.to_dict(), sort_keys=True, indent=2) + "\n"
        evidence_text = json.dumps(dict(evidence), sort_keys=True, indent=2) + "\n"
        (staging / SELECTION_FILENAME).write_text(selection_text, encoding="utf-8")
        (staging / EVIDENCE_FILENAME).write_text(evidence_text, encoding="utf-8")
        write_manifest(staging, (SELECTION_FILENAME, EVIDENCE_FILENAME))

        if simulate_partial_write:
            _atomic_write_text(root / SELECTION_FILENAME, selection_text)
            raise SelectionPersistenceError(
                SelectionFailureCodeV1.PARTIAL_WRITE.value,
                "SIMULATED_PARTIAL",
            )

        for name in (SELECTION_FILENAME, EVIDENCE_FILENAME, MANIFEST_FILENAME):
            src = staging / name
            _atomic_write_text(root / name, src.read_text(encoding="utf-8"))

        if simulate_crash_after_persist_before_confirm:
            raise SelectionPersistenceError(
                SelectionFailureCodeV1.PERSISTENCE_WRITE_FAILURE.value,
                "SIMULATED_CRASH_AFTER_PERSIST_BEFORE_CONFIRM",
            )

        verification = verify_manifest(root)
        loaded = load_and_validate_selection_v1(
            root,
            expected_repository_sha=selection.repository_sha,
            expected_config_digest=selection.config_digest,
        )
        if not loaded.ok or loaded.selection is None:
            raise SelectionPersistenceError(
                SelectionFailureCodeV1.CORRUPT_PERSISTED_SELECTION.value,
                f"POST_LOAD:{loaded.failure_codes}:{loaded.detail}",
            )
        if loaded.selection.integrity_digest != selection.integrity_digest:
            raise SelectionPersistenceError(
                SelectionFailureCodeV1.INTEGRITY_FAILURE.value,
                "POST_DIGEST_MISMATCH",
            )
        return {
            "ok": True,
            "verification": verification,
            "selection_id": selection.selection_id,
            "integrity_digest": selection.integrity_digest,
            "persistence_path": str(root / SELECTION_FILENAME),
            "reloaded_digest": loaded.selection.integrity_digest,
            "idempotent_identical": True,
        }
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def evidence_digest_v1(evidence: Mapping[str, Any]) -> str:
    return sha256_hex(canonical_json_dumps(dict(evidence)))
