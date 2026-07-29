"""Offline verifier for wallclock observation evidence bundles."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    CAPABILITY_ID,
    EVIDENCE_SCHEMA_ID,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.killstate_runtime_v1 import (
    TerminalVerdict,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.wallclock_evidence_v1 import (
    APPEND_ONLY,
    REQUIRED_IMMUTABLE,
)

VERIFIER_ID = "ops.paper_shadow_wallclock_evidence_verifier_v1"
RESULT_PASS = "WALLCLOCK_OBSERVATION_EVIDENCE_VERIFIED"
RESULT_FAIL = "WALLCLOCK_OBSERVATION_EVIDENCE_INVALID"
RESULT_ABORT_VERIFIED = "WALLCLOCK_OBSERVATION_ABORT_VERIFIED"


@dataclass
class WallclockEvidenceVerificationResultV1:
    result: str
    verified: bool
    verdict: str = ""
    incomplete: bool = False
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    authority_effect: str = AUTHORITY_EFFECT_NONE
    economic_validity_pass: bool = False
    promotion_pass: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def verify_wallclock_evidence_bundle_v1(
    *,
    evidence_root: Path,
) -> WallclockEvidenceVerificationResultV1:
    notes = [
        f"VERIFIER_ID={VERIFIER_ID}",
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "VERIFIER_NO_NETWORK",
        "VERIFIER_NO_MUTATION",
    ]
    blockers: list[str] = []
    root = evidence_root
    if not root.is_dir():
        return WallclockEvidenceVerificationResultV1(
            result=RESULT_FAIL,
            verified=False,
            blockers=["EVIDENCE_ROOT_MISSING"],
            notes=notes,
        )

    manifest_path = root / "evidence_manifest.sha256"
    if not manifest_path.is_file():
        blockers.append("EVIDENCE_MANIFEST_MISSING")
    else:
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                digest, name = line.split("  ", 1)
            except ValueError:
                blockers.append("EVIDENCE_MANIFEST_MALFORMED")
                continue
            path = root / name
            if not path.is_file():
                blockers.append(f"MANIFEST_FILE_MISSING:{name}")
                continue
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != digest:
                blockers.append(f"EVIDENCE_TAMPER:{name}")

    for name in REQUIRED_IMMUTABLE:
        if not (root / name).is_file():
            # terminal/integrity required always; others may be incomplete abort
            if name in {
                "terminal_verdict.json",
                "integrity_manifest.json",
                "evidence_manifest.sha256",
            }:
                blockers.append(f"REQUIRED_MISSING:{name}")

    verdict = ""
    incomplete = False
    terminal_path = root / "terminal_verdict.json"
    if terminal_path.is_file():
        import json

        terminal = json.loads(terminal_path.read_text(encoding="utf-8"))
        verdict = str(terminal.get("verdict") or "")
        incomplete = bool(terminal.get("incomplete"))
        if terminal.get("economic_validity_pass") is True:
            blockers.append("ECONOMIC_VALIDITY_SIDE_EFFECT_FORBIDDEN")
        if terminal.get("promotion_pass") is True:
            blockers.append("PROMOTION_SIDE_EFFECT_FORBIDDEN")
        if terminal.get("paper_execution") is True:
            blockers.append("PAPER_EXECUTION_CLAIM_FORBIDDEN")
        if terminal.get("orders_submitted") is True:
            blockers.append("ORDERS_SUBMITTED_CLAIM_FORBIDDEN")
        if terminal.get("schema_id") != EVIDENCE_SCHEMA_ID:
            blockers.append("EVIDENCE_SCHEMA_MISMATCH")
        # Safety ABORT must never be remapped to FAIL
        if verdict == TerminalVerdict.FAIL.value and incomplete:
            blockers.append("FAIL_WITH_INCOMPLETE_FORBIDDEN")
        kill_path = root / "killstate_events.jsonl"
        if kill_path.is_file() and kill_path.read_text(encoding="utf-8").strip():
            if verdict == TerminalVerdict.FAIL.value:
                blockers.append("SAFETY_ABORT_REMAPPED_TO_FAIL")
            if verdict == TerminalVerdict.PASS.value:
                blockers.append("SAFETY_EVENTS_WITH_PASS")

    unique = sorted(set(blockers))
    if unique:
        return WallclockEvidenceVerificationResultV1(
            result=RESULT_FAIL,
            verified=False,
            verdict=verdict,
            incomplete=incomplete,
            blockers=unique,
            notes=notes,
        )

    if verdict == TerminalVerdict.ABORT.value:
        result = RESULT_ABORT_VERIFIED
    else:
        result = RESULT_PASS
    return WallclockEvidenceVerificationResultV1(
        result=result,
        verified=True,
        verdict=verdict,
        incomplete=incomplete,
        notes=notes + [f"APPEND_ONLY={list(APPEND_ONLY)}"],
    )
