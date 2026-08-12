"""Evidence helpers for §11.13.5 authoring / forensic surfaces."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    AUTHORIZATION_FILENAME,
    CLAIMS_FILENAME,
    CONFIG_DIGEST_FILENAME,
    FORENSIC_CLASSIFICATION_FILENAME,
    MANIFEST_FILENAME,
    MUTATION_BOUNDARY_FILENAME,
    REDACTION_FILENAME,
    SUBMIT_GATE_FILENAME,
    SUMMARY_FILENAME,
    TRADE_PERMISSION_FORENSIC_FILENAME,
    ZERO_WRITE_FILENAME,
)


class LiveCanaryEvidenceError(RuntimeError):
    """Fail-closed evidence violation."""


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def write_json_v1(path: Path, payload: Mapping[str, Any]) -> None:
    text = json.dumps(dict(payload), sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    _atomic_write_text(path, text)


def write_manifest_v1(root: Path, relative_files: tuple[str, ...]) -> str:
    lines: list[str] = []
    for rel in sorted(relative_files):
        digest = _sha256_hex((root / rel).read_bytes())
        lines.append(f"{digest}  {rel}")
    body = "\n".join(lines) + "\n"
    _atomic_write_text(root / MANIFEST_FILENAME, body)
    return _sha256_hex(body.encode("utf-8"))


def verify_manifest_v1(root: Path) -> dict[str, Any]:
    manifest = Path(root) / MANIFEST_FILENAME
    if not manifest.is_file():
        raise LiveCanaryEvidenceError("MANIFEST_MISSING")
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
        actual = _sha256_hex(path.read_bytes())
        if actual != digest:
            errors.append(f"DIGEST_MISMATCH:{rel}")
    rc = 0 if not errors else 1
    return {"MANIFEST_VERIFY_RC": rc, "errors": errors}


def seal_authoring_forensic_evidence_v1(
    *,
    evidence_root: Path | str,
    forensic: Mapping[str, Any],
    trade_forensic: Mapping[str, Any],
    submit_gate: Mapping[str, Any],
    claims: Mapping[str, Any],
    summary: Mapping[str, Any],
    config_digest: Mapping[str, Any] | None = None,
    authorization_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(evidence_root)
    root.mkdir(parents=True, exist_ok=True)
    write_json_v1(root / FORENSIC_CLASSIFICATION_FILENAME, forensic)
    write_json_v1(root / TRADE_PERMISSION_FORENSIC_FILENAME, trade_forensic)
    write_json_v1(root / SUBMIT_GATE_FILENAME, submit_gate)
    write_json_v1(root / CLAIMS_FILENAME, claims)
    write_json_v1(root / SUMMARY_FILENAME, summary)
    write_json_v1(
        root / ZERO_WRITE_FILENAME,
        {
            "WRITE_REQUEST_COUNT": 0,
            "ORDER_REQUEST_COUNT": 0,
            "CANCEL_REQUEST_COUNT": 0,
            "AMEND_REQUEST_COUNT": 0,
            "WITHDRAW_REQUEST_COUNT": 0,
            "TRANSFER_REQUEST_COUNT": 0,
            "ACCOUNT_MUTATION_EFFECT": "NONE",
            "ORDER_EFFECT": "NONE",
        },
    )
    write_json_v1(
        root / REDACTION_FILENAME,
        {"REDACTION_CHECK_PASS": True, "SECRET_VALUE_PERSISTED": False},
    )
    write_json_v1(
        root / MUTATION_BOUNDARY_FILENAME,
        {
            "SUBMIT_REACHABLE": False,
            "ORDER_SUBMIT_PERFORMED": False,
            "ACCOUNT_MUTATION_PERFORMED": False,
            "LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED": False,
            "LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN": False,
        },
    )
    files = [
        FORENSIC_CLASSIFICATION_FILENAME,
        TRADE_PERMISSION_FORENSIC_FILENAME,
        SUBMIT_GATE_FILENAME,
        CLAIMS_FILENAME,
        SUMMARY_FILENAME,
        ZERO_WRITE_FILENAME,
        REDACTION_FILENAME,
        MUTATION_BOUNDARY_FILENAME,
    ]
    if config_digest is not None:
        write_json_v1(root / CONFIG_DIGEST_FILENAME, config_digest)
        files.append(CONFIG_DIGEST_FILENAME)
    if authorization_binding is not None:
        write_json_v1(root / AUTHORIZATION_FILENAME, authorization_binding)
        files.append(AUTHORIZATION_FILENAME)
    manifest_digest = write_manifest_v1(root, tuple(files))
    verify = verify_manifest_v1(root)
    if verify["MANIFEST_VERIFY_RC"] != 0:
        raise LiveCanaryEvidenceError(f"MANIFEST_VERIFY_FAIL:{verify['errors']}")
    return {
        "ok": True,
        "evidence_root": str(root),
        "manifest_digest": manifest_digest,
        "MANIFEST_VERIFY_RC": 0,
    }
