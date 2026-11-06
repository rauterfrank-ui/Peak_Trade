"""Provenance-by-reference binding for productive wallclock observation evidence v1.

Read-only toward referenced evidence. authority_effect=NONE.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.bundle_verifier_v1 import (
    RESULT_PASS,
    VERIFIER_ID as WALLCLOCK_BUNDLE_VERIFIER_ID,
    verify_wallclock_evidence_bundle_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    CAPABILITY_ID as WALLCLOCK_CAPABILITY_ID,
    EVIDENCE_SCHEMA_ID as WALLCLOCK_EVIDENCE_SCHEMA_ID,
    EXECUTION_CLASS_ANALYTICAL,
)

REFERENCE_SCHEMA_ID = "ops.productive_wallclock_observation_reference.v1"
REFERENCE_SCHEMA_VERSION = "v1"
REFERENCE_ARTIFACT = "productive_wallclock_observation_reference_v1.json"
BINDING_MODE = "PRODUCTIVE_WALLCLOCK_REFERENCE"

_RELPATH_FORBIDDEN = re.compile(r"(^|[\\/])\.\.([\\/]|$)")


@dataclass
class ProductiveWallclockObservationReferenceVerificationResultV1:
    verified: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    authority_effect: str = AUTHORITY_EFFECT_NONE

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sha256_file(path: Path) -> str:
    return __import__("hashlib").sha256(path.read_bytes()).hexdigest()


def _safe_resolve_evidence_root(*, repo_root: Path, evidence_relpath: str) -> Path | None:
    rel = evidence_relpath.strip().replace("\\", "/")
    if not rel or rel.startswith("/") or _RELPATH_FORBIDDEN.search(rel):
        return None
    root = repo_root.resolve()
    target = (root / rel).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None
    return target


def _heartbeat_count_v1(evidence_root: Path) -> int:
    path = evidence_root / "heartbeat.jsonl"
    if not path.is_file():
        return 0
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            count += 1
    return count


def build_productive_wallclock_observation_reference_document_v1(
    *,
    repo_root: Path,
    evidence_relpath: str,
) -> dict[str, Any]:
    """Build reference document from live evidence files (read-only). Does not write evidence."""
    root = repo_root.resolve()
    evidence_root = _safe_resolve_evidence_root(repo_root=root, evidence_relpath=evidence_relpath)
    if evidence_root is None or not evidence_root.is_dir():
        raise ValueError("productive_wallclock_evidence_relpath_invalid")

    repo_sha_path = evidence_root / "repo_sha.txt"
    if not repo_sha_path.is_file():
        raise ValueError("repo_sha_missing")
    repository_sha = repo_sha_path.read_text(encoding="utf-8").strip()

    manifest_path = evidence_root / "evidence_manifest.sha256"
    integrity_path = evidence_root / "integrity_manifest.json"
    terminal_path = evidence_root / "terminal_verdict.json"
    counters_path = evidence_root / "observation_cycle_counters.json"
    for req in (manifest_path, integrity_path, terminal_path, counters_path):
        if not req.is_file():
            raise ValueError(f"missing_required_artifact:{req.name}")

    terminal = json.loads(terminal_path.read_text(encoding="utf-8"))
    counters = json.loads(counters_path.read_text(encoding="utf-8"))
    cycle_count = int(counters.get("cycle_count") or 0)
    heartbeat_count = _heartbeat_count_v1(evidence_root)

    return {
        "schema_id": REFERENCE_SCHEMA_ID,
        "schema_version": REFERENCE_SCHEMA_VERSION,
        "authority_effect": AUTHORITY_EFFECT_NONE,
        "binding_mode": BINDING_MODE,
        "evidence_relpath": evidence_relpath.strip().replace("\\", "/"),
        "repository_sha": repository_sha,
        "evidence_manifest_sha256": _sha256_file(manifest_path),
        "integrity_manifest_sha256": _sha256_file(integrity_path),
        "terminal_verdict_sha256": _sha256_file(terminal_path),
        "wallclock_verifier_id": WALLCLOCK_BUNDLE_VERIFIER_ID,
        "wallclock_evidence_schema_id": WALLCLOCK_EVIDENCE_SCHEMA_ID,
        "capability_id": WALLCLOCK_CAPABILITY_ID,
        "execution_class": str(terminal.get("execution_class") or EXECUTION_CLASS_ANALYTICAL),
        "observation_cycle_count": cycle_count,
        "heartbeat_count": heartbeat_count,
        "orders_submitted": int(terminal.get("orders_submitted") is True),
        "paper_execution": bool(terminal.get("paper_execution") is True),
        "economic_validity_pass": bool(terminal.get("economic_validity_pass") is True),
    }


def verify_productive_wallclock_observation_reference_v1(
    *,
    repo_root: Path,
    reference: Mapping[str, Any] | None = None,
    reference_path: Path | None = None,
) -> ProductiveWallclockObservationReferenceVerificationResultV1:
    """Fail-closed verification; re-invokes authoritative wallclock bundle verifier."""
    notes = [
        "VERIFY_READ_ONLY_REFERENCED_EVIDENCE",
        f"REFERENCE_SCHEMA_ID={REFERENCE_SCHEMA_ID}",
    ]
    blockers: list[str] = []

    doc: dict[str, Any] = {}
    if reference is not None:
        doc = dict(reference)
    elif reference_path is not None and reference_path.is_file():
        try:
            loaded = json.loads(reference_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            blockers.append("REFERENCE_JSON_MALFORMED")
            loaded = {}
        if isinstance(loaded, dict):
            doc = loaded
        else:
            blockers.append("REFERENCE_JSON_NOT_OBJECT")
    else:
        blockers.append("REFERENCE_MISSING")

    if doc:
        if doc.get("schema_id") != REFERENCE_SCHEMA_ID:
            blockers.append("REFERENCE_SCHEMA_ID_MISMATCH")
        if doc.get("schema_version") != REFERENCE_SCHEMA_VERSION:
            blockers.append("REFERENCE_SCHEMA_VERSION_MISMATCH")
        if doc.get("authority_effect") != AUTHORITY_EFFECT_NONE:
            blockers.append("REFERENCE_AUTHORITY_EFFECT_NOT_NONE")
        if doc.get("binding_mode") != BINDING_MODE:
            blockers.append("REFERENCE_BINDING_MODE_MISMATCH")
        if doc.get("wallclock_verifier_id") != WALLCLOCK_BUNDLE_VERIFIER_ID:
            blockers.append("REFERENCE_WALLCLOCK_VERIFIER_ID_MISMATCH")
        if doc.get("wallclock_evidence_schema_id") != WALLCLOCK_EVIDENCE_SCHEMA_ID:
            blockers.append("REFERENCE_WALLCLOCK_EVIDENCE_SCHEMA_MISMATCH")
        if doc.get("capability_id") != WALLCLOCK_CAPABILITY_ID:
            blockers.append("REFERENCE_CAPABILITY_ID_MISMATCH")

    rel = str(doc.get("evidence_relpath") or "")
    evidence_root = _safe_resolve_evidence_root(repo_root=repo_root.resolve(), evidence_relpath=rel)
    if evidence_root is None:
        blockers.append("EVIDENCE_RELPATH_UNSAFE_OR_INVALID")
    elif not evidence_root.is_dir():
        blockers.append("EVIDENCE_ROOT_MISSING")

    if evidence_root is not None and evidence_root.is_dir() and doc and not blockers:
        repo_sha_path = evidence_root / "repo_sha.txt"
        if not repo_sha_path.is_file():
            blockers.append("REPO_SHA_FILE_MISSING")
        else:
            actual_sha = repo_sha_path.read_text(encoding="utf-8").strip()
            declared_sha = str(doc.get("repository_sha") or "").strip()
            if not declared_sha:
                blockers.append("REFERENCE_REPOSITORY_SHA_MISSING")
            elif actual_sha != declared_sha:
                blockers.append("REPOSITORY_SHA_MISMATCH")

        digest_checks = (
            ("evidence_manifest.sha256", "evidence_manifest_sha256"),
            ("integrity_manifest.json", "integrity_manifest_sha256"),
            ("terminal_verdict.json", "terminal_verdict_sha256"),
        )
        for filename, field_name in digest_checks:
            path = evidence_root / filename
            if not path.is_file():
                blockers.append(f"EVIDENCE_ARTIFACT_MISSING:{filename}")
                continue
            actual_digest = _sha256_file(path)
            declared = str(doc.get(field_name) or "")
            if not declared:
                blockers.append(f"REFERENCE_{field_name.upper()}_MISSING")
            elif actual_digest != declared:
                blockers.append(f"{field_name.upper()}_MISMATCH")

        terminal_path = evidence_root / "terminal_verdict.json"
        counters_path = evidence_root / "observation_cycle_counters.json"
        if terminal_path.is_file():
            terminal = json.loads(terminal_path.read_text(encoding="utf-8"))
            if terminal.get("incomplete") is True:
                blockers.append("TERMINAL_INCOMPLETE")
            if str(terminal.get("verdict") or "") != "PASS":
                blockers.append("TERMINAL_VERDICT_NOT_PASS")
            exec_class = str(terminal.get("execution_class") or "")
            if exec_class != EXECUTION_CLASS_ANALYTICAL:
                blockers.append("EXECUTION_CLASS_MISMATCH")
            if doc.get("execution_class") != EXECUTION_CLASS_ANALYTICAL:
                blockers.append("REFERENCE_EXECUTION_CLASS_MISMATCH")
            if terminal.get("paper_execution") is True:
                blockers.append("PAPER_EXECUTION_FORBIDDEN")
            if doc.get("paper_execution") is True:
                blockers.append("REFERENCE_PAPER_EXECUTION_CLAIM")
            orders = terminal.get("orders_submitted")
            if orders is True or (isinstance(orders, int) and orders > 0):
                blockers.append("ORDERS_SUBMITTED_FORBIDDEN")
            ref_orders = doc.get("orders_submitted")
            if ref_orders not in (0, False):
                blockers.append("REFERENCE_ORDERS_SUBMITTED_NONZERO")
            if terminal.get("economic_validity_pass") is True:
                blockers.append("ECONOMIC_VALIDITY_SIDE_EFFECT_FORBIDDEN")
            if doc.get("economic_validity_pass") is True:
                blockers.append("REFERENCE_ECONOMIC_VALIDITY_CLAIM")

        if counters_path.is_file():
            counters = json.loads(counters_path.read_text(encoding="utf-8"))
            actual_cycles = int(counters.get("cycle_count") or 0)
            declared_cycles = int(doc.get("observation_cycle_count") or -1)
            if declared_cycles != actual_cycles:
                blockers.append("OBSERVATION_CYCLE_COUNT_MISMATCH")
            actual_hb = _heartbeat_count_v1(evidence_root)
            declared_hb = int(doc.get("heartbeat_count") or -1)
            if declared_hb != actual_hb:
                blockers.append("HEARTBEAT_COUNT_MISMATCH")

        if not blockers:
            wallclock = verify_wallclock_evidence_bundle_v1(evidence_root=evidence_root)
            if not wallclock.verified:
                blockers.extend(f"WALLCLOCK:{b}" for b in wallclock.blockers)
            elif wallclock.result != RESULT_PASS:
                blockers.append(f"WALLCLOCK_RESULT_NOT_PASS:{wallclock.result}")

    unique = sorted(set(blockers))
    return ProductiveWallclockObservationReferenceVerificationResultV1(
        verified=not unique,
        blockers=unique,
        notes=notes,
    )
