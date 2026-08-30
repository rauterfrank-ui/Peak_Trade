"""Atomic persistence for Master V2 minimal selector decisions.

OWNER_POLICY_VERSION=V1
HISTORICAL_CLAIM=false

Does not import Cap 2.3 ranking, stickiness, or previous-selection semantics.
Atomic write + manifest pattern only.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from src.ops.master_v2_minimal_selector_v1.constants_v1 import (
    MANIFEST_FILENAME,
    SCHEMA_VERSION,
    SELECTION_FILENAME,
)
from src.ops.master_v2_minimal_selector_v1.models_v1 import (
    MasterV2SelectionDecisionV1,
    canonical_json_dumps,
    sha256_hex,
)


class SelectorPersistenceError(RuntimeError):
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


def persist_selection_decision_atomic_v1(
    *,
    state_root: Path,
    decision: MasterV2SelectionDecisionV1,
) -> Path:
    root = Path(state_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / SELECTION_FILENAME
    _atomic_write_text(path, canonical_json_dumps(decision.to_dict()) + "\n")
    write_manifest(root, (SELECTION_FILENAME,))
    return path


@dataclass(frozen=True)
class LoadSelectionResultV1:
    ok: bool
    decision: Optional[MasterV2SelectionDecisionV1]
    failure_codes: tuple[str, ...]


def load_and_validate_selection_decision_v1(state_root: Path) -> LoadSelectionResultV1:
    root = Path(state_root)
    path = root / SELECTION_FILENAME
    manifest = root / MANIFEST_FILENAME
    if not path.is_file():
        return LoadSelectionResultV1(False, None, ("SELECTION_MISSING",))
    if not manifest.is_file():
        return LoadSelectionResultV1(False, None, ("MANIFEST_MISSING",))
    try:
        payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        decision = MasterV2SelectionDecisionV1.from_dict(payload)
    except Exception:  # noqa: BLE001
        return LoadSelectionResultV1(False, None, ("CORRUPT_SELECTION",))
    if decision.schema_version != SCHEMA_VERSION:
        return LoadSelectionResultV1(False, decision, ("SCHEMA_MISMATCH",))
    recomputed = decision.compute_identity_digest()
    if decision.identity_digest != recomputed:
        return LoadSelectionResultV1(False, decision, ("IDENTITY_DIGEST_MISMATCH",))
    expected = sha256_hex(path.read_bytes())
    found = False
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, _, rel = line.partition("  ")
        if rel == SELECTION_FILENAME:
            found = True
            if digest != expected:
                return LoadSelectionResultV1(False, decision, ("MANIFEST_DIGEST_MISMATCH",))
    if not found:
        return LoadSelectionResultV1(False, decision, ("MANIFEST_ENTRY_MISSING",))
    return LoadSelectionResultV1(True, decision, ())
