"""Verifier for HEAD-bound integrated offline replay correctness evidence v1."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    MANIFEST_NAME,
    PROOF_ARTIFACT_NAME,
    SCHEMA_ID,
)
from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.proof_v1 import (
    resolve_repository_head_sha_v1,
)


@dataclass
class HeadBoundCorrectnessVerificationResultV1:
    verified: bool
    schema_id: str
    blockers: list[str] = field(default_factory=list)
    proof: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def verify_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
    *,
    evidence_root: Path,
    repo_root: Path,
    require_current_head: bool = True,
) -> HeadBoundCorrectnessVerificationResultV1:
    blockers: list[str] = []
    root = evidence_root.resolve()
    if not root.is_dir():
        return HeadBoundCorrectnessVerificationResultV1(
            verified=False,
            schema_id=SCHEMA_ID,
            blockers=["EVIDENCE_ROOT_MISSING"],
        )

    manifest_path = root / MANIFEST_NAME
    proof_path = root / PROOF_ARTIFACT_NAME
    if not manifest_path.is_file():
        blockers.append("MANIFEST_MISSING")
    if not proof_path.is_file():
        blockers.append("PROOF_ARTIFACT_MISSING")

    if manifest_path.is_file() and proof_path.is_file():
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                blockers.append("MANIFEST_MALFORMED")
                continue
            digest, name = parts[0], parts[1]
            target = root / name
            if not target.is_file():
                blockers.append(f"MANIFEST_TARGET_MISSING:{name}")
                continue
            actual = hashlib.sha256(target.read_bytes()).hexdigest()
            if actual != digest:
                blockers.append(f"MANIFEST_DIGEST_MISMATCH:{name}")

    proof: dict[str, Any] = {}
    if proof_path.is_file():
        try:
            loaded = json.loads(proof_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            blockers.append("PROOF_JSON_MALFORMED")
            loaded = {}
        if isinstance(loaded, dict):
            proof = loaded
        else:
            blockers.append("PROOF_JSON_NOT_OBJECT")

    if proof.get("authority_effect") != AUTHORITY_EFFECT_NONE:
        blockers.append("AUTHORITY_EFFECT_NOT_NONE")
    if proof.get("EXTERNAL_EFFECT_COUNT", 0) != 0:
        blockers.append("EXTERNAL_EFFECT_COUNT_NONZERO")

    for key in (
        "INTEGRATED_OFFLINE_REPLAY_AND_CORRECTNESS_PASS",
        "CURRENT_HEAD_BOUND",
        "CRS_CONTEXT_BOUND",
        "ENTRY_QUANTITY_SEMANTICS_PASS",
        "EXIT_QUANTITY_SEMANTICS_PASS",
        "POSITION_LIFECYCLE_PASS",
        "FEES_SLIPPAGE_ACCOUNTED",
        "ACCOUNTING_CONSISTENCY_PASS",
    ):
        if proof.get(key) is not True:
            blockers.append(f"{key}_NOT_TRUE")

    evidence_head = str(proof.get("repository_head_sha") or "")
    if require_current_head:
        try:
            current = resolve_repository_head_sha_v1(repo_root=repo_root.resolve())
        except ValueError:
            blockers.append("CURRENT_HEAD_RESOLUTION_FAILED")
            current = ""
        if evidence_head != current:
            blockers.append("EVIDENCE_HEAD_STALE")

    return HeadBoundCorrectnessVerificationResultV1(
        verified=not blockers,
        schema_id=SCHEMA_ID,
        blockers=sorted(set(blockers)),
        proof=proof or None,
    )
