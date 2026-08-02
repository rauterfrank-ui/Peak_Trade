"""Evidence persistence for Cap 4.1 pre-activation closure."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any, Mapping

from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.constants_v1 import (
    EVIDENCE_FILENAME,
    GATE_FILENAME,
    MANIFEST_FILENAME,
    RESULT_FILENAME,
    STAGING_DIRNAME_PREFIX,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.models_v1 import (
    sha256_hex,
)


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
        raise RuntimeError("MANIFEST_MISSING")
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
        raise RuntimeError(";".join(errors))
    return {"ok": True, "manifest_path": str(manifest)}


def persist_pre_activation_evidence_atomic_v1(
    *,
    evidence_root: Path,
    evidence: Mapping[str, Any],
    result: Mapping[str, Any],
    gate: Mapping[str, Any],
) -> dict[str, Any]:
    root = Path(evidence_root)
    root.mkdir(parents=True, exist_ok=True)
    staging = root / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"
    staging.mkdir(parents=True, exist_ok=False)
    try:
        (staging / EVIDENCE_FILENAME).write_text(
            json.dumps(dict(evidence), sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        (staging / RESULT_FILENAME).write_text(
            json.dumps(dict(result), sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        (staging / GATE_FILENAME).write_text(
            json.dumps(dict(gate), sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        write_manifest(staging, (EVIDENCE_FILENAME, RESULT_FILENAME, GATE_FILENAME))
        for name in (EVIDENCE_FILENAME, RESULT_FILENAME, GATE_FILENAME, MANIFEST_FILENAME):
            src = staging / name
            _atomic_write_text(root / name, src.read_text(encoding="utf-8"))
        verification = verify_manifest(root)
        return {"ok": True, "verification": verification, "evidence_root": str(root)}
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
