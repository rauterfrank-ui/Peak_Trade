"""Execution evidence production and sealing for §11.12.8 dry activation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.constants_v1 import (
    CAPABILITY_ID,
    MANIFEST_FILENAME,
    OWNER,
)


class Section11128EvidenceError(RuntimeError):
    """Fail-closed evidence / seal violation."""


@dataclass(frozen=True)
class EvidenceSealV1:
    sealed: bool
    evidence_dir: str
    manifest_path: str
    entry_count: int
    independently_verifiable: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "sealed": self.sealed,
            "evidence_dir": self.evidence_dir,
            "manifest_path": self.manifest_path,
            "entry_count": self.entry_count,
            "independently_verifiable": self.independently_verifiable,
        }


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_execution_evidence_v1(
    evidence_dir: Path,
    *,
    payload: Mapping[str, Any],
    filename: str = "execution_evidence_v1.json",
) -> Path:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    path = evidence_dir / filename
    body = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "OWNER": OWNER,
        "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": False,
        "NETWORK_EFFECT": "NONE",
        "ORDER_EFFECT": "NONE",
        "LIVE_ORDER_EFFECT": "NONE",
        "SECTION_11_13_STARTED": False,
        "payload": dict(payload),
    }
    path.write_text(
        json.dumps(body, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return path


def seal_evidence_dir_v1(evidence_dir: Path) -> EvidenceSealV1:
    if not evidence_dir.is_dir():
        raise Section11128EvidenceError("EVIDENCE_DIR_MISSING")
    manifest_lines: list[str] = []
    for path in sorted(evidence_dir.rglob("*")):
        if not path.is_file() or path.name == MANIFEST_FILENAME:
            continue
        rel = path.relative_to(evidence_dir).as_posix()
        digest = _sha256_bytes(path.read_bytes())
        manifest_lines.append(f"{digest}  {rel}")
    if not manifest_lines:
        raise Section11128EvidenceError("EVIDENCE_DIR_EMPTY")
    manifest_path = evidence_dir / MANIFEST_FILENAME
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    # Independent verification pass.
    for line in manifest_lines:
        digest, _, rel = line.partition("  ")
        actual = _sha256_bytes((evidence_dir / rel).read_bytes())
        if actual != digest:
            raise Section11128EvidenceError(f"EVIDENCE_SEAL_VERIFY_MISMATCH:{rel}")
    return EvidenceSealV1(
        sealed=True,
        evidence_dir=str(evidence_dir),
        manifest_path=str(manifest_path),
        entry_count=len(manifest_lines),
        independently_verifiable=True,
    )


def verify_evidence_seal_v1(evidence_dir: Path) -> int:
    manifest = evidence_dir / MANIFEST_FILENAME
    if not manifest.is_file():
        return 2
    lines = [ln.strip() for ln in manifest.read_text(encoding="utf-8").splitlines() if ln.strip()]
    for line in lines:
        digest, _, rel = line.partition("  ")
        path = evidence_dir / rel
        if not path.is_file():
            return 2
        if _sha256_bytes(path.read_bytes()) != digest:
            return 2
    return 0
