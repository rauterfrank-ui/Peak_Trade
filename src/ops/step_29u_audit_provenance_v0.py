"""STEP 29U Audit / Provenance Completeness v0.

Offline, fail-closed, non-activating evaluation of whether the canonical
Step-29U evidence chain is complete and internally consistent.

Does not authorize activation. Does not invent a second audit authority for
runtime, UI, or economic thresholds.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.step_29u_canonical_shadow_binding_v0 import (
    CANONICAL_STEP_29U_EVIDENCE_RELPATH,
    verify_canonical_step_29u_binding_evidence_v0,
)
from src.ops.step_29u_offline_capability_v0 import verify_capability_evidence_v0

PACKAGE_MARKER = "STEP_29U_AUDIT_PROVENANCE_V0=true"
PRODUCER_FAMILY = "ops.step_29u_audit_provenance_v0"
SCHEMA_ID = PRODUCER_FAMILY
SCHEMA_VERSION = "v0"
CAPABILITY_ID = "STEP_29U_AUDIT_PROVENANCE_V0"

STATUS_COMPLETE = "COMPLETE"
STATUS_ABSENT = "ABSENT"
STATUS_INVALID = "INVALID"
STATUS_CONTRADICTORY = "CONTRADICTORY"
STATUS_STALE = "STALE"
STATUS_UNVERIFIED = "UNVERIFIED"
VALID_STATUSES = frozenset(
    {
        STATUS_COMPLETE,
        STATUS_ABSENT,
        STATUS_INVALID,
        STATUS_CONTRADICTORY,
        STATUS_STALE,
        STATUS_UNVERIFIED,
    }
)

OFFLINE_CAPABILITY_RELPATH = CANONICAL_STEP_29U_EVIDENCE_RELPATH
BINDING_EVIDENCE_RELPATH = "evidence/ops/step_29u_canonical_shadow_binding/2026-07-26_capability_v0"
SOAK_EVIDENCE_RELPATH = "evidence/ops/step_29u_post_merge_shadow_soak/20260725T222915Z"
INVENTORY_OWNER_RELPATH = "src/ops/step_29u_activation_eligibility_inventory_v0.py"
INVENTORY_RUNBOOK_RELPATH = "docs/ops/runbooks/STEP_29U_ACTIVATION_ELIGIBILITY_INVENTORY_V0.md"
BINDING_RUNBOOK_RELPATH = (
    "docs/ops/runbooks/STEP_29U_CANONICAL_BINDING_AND_IMPLEMENTATION_INVENTORY_V0.md"
)
EXPECTED_SOAK_TESTED_HEAD_SHA = "cd6d465c83c6c65733e5d85238aa223d4bffd548"
# Binding capability evidence is older than the post-merge soak head; both are
# current for their stage. Do not treat the offline SHA as soak-stale.
EXPECTED_OFFLINE_SOURCE_GIT_SHA = "237cfe07850d9a579f73f596bb4df18adddfbe69"

# Superseded soak / capability dirs that must not silently become current.
SUPERSEDED_EVIDENCE_MARKERS: tuple[str, ...] = (
    "evidence/ops/okx_futures_shadow_no_order/2026-07-25_postmerge_600s_soak",
)


class Step29UAuditProvenanceError(ValueError):
    """Fail-closed audit/provenance evaluator error."""


@dataclass(frozen=True)
class AuditLinkRecordV0:
    link_id: str
    path: str
    status: str
    reason_code: str
    digest: Optional[str]
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "link_id": self.link_id,
            "path": self.path,
            "status": self.status,
            "reason_code": self.reason_code,
            "digest": self.digest,
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class AuditProvenanceResultV0:
    schema_id: str
    schema_version: str
    generated_at: str
    evaluated_main_sha: str
    capability_id: str
    status: str
    audit_provenance_complete: bool
    links: tuple[AuditLinkRecordV0, ...]
    blockers: tuple[str, ...]
    traversal_order: tuple[str, ...]
    provenance: Mapping[str, Any]
    safety_facts: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "evaluated_main_sha": self.evaluated_main_sha,
            "capability_id": self.capability_id,
            "status": self.status,
            "audit_provenance_complete": self.audit_provenance_complete,
            "links": [link.to_dict() for link in self.links],
            "blockers": list(self.blockers),
            "traversal_order": list(self.traversal_order),
            "provenance": dict(self.provenance),
            "safety_facts": dict(self.safety_facts),
        }


@dataclass(frozen=True)
class AuditProvenanceOverridesV0:
    offline_dir: Optional[Path] = None
    binding_dir: Optional[Path] = None
    soak_dir: Optional[Path] = None
    evaluated_main_sha: Optional[str] = None
    treat_as_local_only: bool = False
    force_unknown_status: bool = False
    expected_soak_head: Optional[str] = None


def default_repo_root_v0() -> Path:
    return Path(__file__).resolve().parents[2]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_sha(repo_root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return out.strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_manifest(manifest_path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            raise Step29UAuditProvenanceError(f"MANIFEST_LINE_INVALID:{manifest_path}")
        digest, rel = parts
        mapping[rel.strip()] = digest.strip().lower()
    return mapping


def _verify_manifest(dir_path: Path, manifest_path: Path) -> tuple[bool, str, Optional[str]]:
    if not manifest_path.is_file():
        return False, "MANIFEST_MISSING", None
    try:
        expected = _read_manifest(manifest_path)
    except (OSError, UnicodeError, Step29UAuditProvenanceError):
        return False, "MANIFEST_MALFORMED", None
    if not expected:
        return False, "MANIFEST_EMPTY", None
    for rel, digest in sorted(expected.items()):
        target = dir_path / rel
        if not target.is_file():
            return False, f"MANIFEST_FILE_MISSING:{rel}", None
        actual = _sha256_file(target)
        if actual.lower() != digest.lower():
            return False, f"DIGEST_MISMATCH:{rel}", actual
    return True, "MANIFEST_OK", _sha256_file(manifest_path)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Step29UAuditProvenanceError(f"JSON_MALFORMED:{path}:{exc}") from exc
    except OSError as exc:
        raise Step29UAuditProvenanceError(f"JSON_UNREADABLE:{path}:{exc}") from exc


def _parse_ts(value: str) -> Optional[datetime]:
    text = (value or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _path_tracked_under_repo(repo_root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return False
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_root), "ls-files", "--error-unmatch", str(path)],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return bool(out.strip())
    except (OSError, subprocess.CalledProcessError):
        # Untracked paths under repo are local-only for audit purposes.
        return False


def _link(
    *,
    link_id: str,
    path: str,
    status: str,
    reason_code: str,
    digest: Optional[str] = None,
    details: Optional[Mapping[str, Any]] = None,
) -> AuditLinkRecordV0:
    if status not in VALID_STATUSES:
        raise Step29UAuditProvenanceError(f"UNKNOWN_AUDIT_STATUS:{status}")
    return AuditLinkRecordV0(
        link_id=link_id,
        path=path,
        status=status,
        reason_code=reason_code,
        digest=digest,
        details=dict(details or {}),
    )


def evaluate_step_29u_audit_provenance_v0(
    *,
    repo_root: Path | None = None,
    overrides: AuditProvenanceOverridesV0 | None = None,
) -> AuditProvenanceResultV0:
    """Evaluate the Step-29U evidence provenance chain. Always non-activating."""
    root = (repo_root or default_repo_root_v0()).resolve()
    ov = overrides or AuditProvenanceOverridesV0()
    evaluated_at = _utc_now()
    evaluated_sha = ov.evaluated_main_sha or _git_sha(root)
    expected_soak_head = ov.expected_soak_head or EXPECTED_SOAK_TESTED_HEAD_SHA

    if ov.force_unknown_status:
        raise Step29UAuditProvenanceError("UNKNOWN_AUDIT_STATUS:FORCED")

    traversal_order = (
        "binding_runbook",
        "offline_capability_evidence",
        "canonical_binding_evidence",
        "post_merge_soak_evidence",
        "activation_inventory_owner",
        "supersession_guard",
    )
    links: list[AuditLinkRecordV0] = []
    blockers: list[str] = []

    # 1) Binding inventory runbook (tracked SSOT)
    binding_runbook = root / BINDING_RUNBOOK_RELPATH
    if not binding_runbook.is_file():
        links.append(
            _link(
                link_id="binding_runbook",
                path=BINDING_RUNBOOK_RELPATH,
                status=STATUS_ABSENT,
                reason_code="BINDING_RUNBOOK_ABSENT",
            )
        )
        blockers.append("binding_runbook:ABSENT")
    elif ov.treat_as_local_only or not _path_tracked_under_repo(root, binding_runbook):
        links.append(
            _link(
                link_id="binding_runbook",
                path=BINDING_RUNBOOK_RELPATH,
                status=STATUS_INVALID,
                reason_code="LOCAL_ONLY_CLAIMED_AS_TRACKED",
                digest=_sha256_file(binding_runbook),
            )
        )
        blockers.append("binding_runbook:INVALID")
    else:
        links.append(
            _link(
                link_id="binding_runbook",
                path=BINDING_RUNBOOK_RELPATH,
                status=STATUS_COMPLETE,
                reason_code="BINDING_RUNBOOK_TRACKED",
                digest=_sha256_file(binding_runbook),
            )
        )

    # 2) Offline capability evidence
    offline_dir = (
        ov.offline_dir.resolve()
        if ov.offline_dir is not None
        else (root / OFFLINE_CAPABILITY_RELPATH).resolve()
    )
    offline_manifest = offline_dir / "evidence_manifest.sha256"
    offline_result = offline_dir / "capability_result.json"
    if not offline_dir.is_dir():
        links.append(
            _link(
                link_id="offline_capability_evidence",
                path=OFFLINE_CAPABILITY_RELPATH,
                status=STATUS_ABSENT,
                reason_code="OFFLINE_EVIDENCE_DIR_ABSENT",
            )
        )
        blockers.append("offline_capability_evidence:ABSENT")
    elif not offline_manifest.is_file():
        links.append(
            _link(
                link_id="offline_capability_evidence",
                path=OFFLINE_CAPABILITY_RELPATH,
                status=STATUS_ABSENT,
                reason_code="MANIFEST_MISSING",
            )
        )
        blockers.append("offline_capability_evidence:ABSENT")
    else:
        try:
            offline_rel = str(offline_dir.relative_to(root))
        except ValueError:
            offline_rel = str(offline_dir)
        if ov.treat_as_local_only or (
            offline_dir.is_relative_to(root)
            and not _path_tracked_under_repo(root, offline_manifest)
        ):
            links.append(
                _link(
                    link_id="offline_capability_evidence",
                    path=offline_rel,
                    status=STATUS_INVALID,
                    reason_code="LOCAL_ONLY_CLAIMED_AS_TRACKED",
                )
            )
            blockers.append("offline_capability_evidence:INVALID")
        else:
            manifest_ok, manifest_reason, manifest_digest = _verify_manifest(
                offline_dir, offline_manifest
            )
            ok_cap, cap_reasons = verify_capability_evidence_v0(evidence_dir=offline_dir)
            payload: dict[str, Any] = {}
            contradictions: list[str] = []
            stale_reasons: list[str] = []
            capability_pass = False
            if offline_result.is_file():
                loaded = _load_json(offline_result)
                if isinstance(loaded, dict):
                    payload = loaded
                    capability_pass = (
                        payload.get("capability_result") == "STEP_29U_OFFLINE_CAPABILITY_PASS"
                    )
                    if capability_pass and (
                        payload.get("step_29u_activated") is True
                        or payload.get("orders_created") is True
                        or payload.get("orders_submitted") is True
                    ):
                        contradictions.append("PASS_RESULT_ACTIVATION_OR_ORDER_CONTRADICTION")
                    identity = payload.get("identity")
                    if isinstance(identity, dict):
                        src_sha = str(identity.get("source_git_sha") or "").strip()
                        if not src_sha or src_sha.upper() == "UNKNOWN":
                            contradictions.append("PRODUCER_GIT_SHA_MISSING")
                        elif src_sha != EXPECTED_OFFLINE_SOURCE_GIT_SHA:
                            # Unexpected offline identity SHA is stale vs canonical binding.
                            stale_reasons.append("OFFLINE_SOURCE_GIT_SHA_UNEXPECTED")
                    producer = str(payload.get("lifecycle_owner") or "").strip()
                    if not producer:
                        contradictions.append("PRODUCER_SOURCE_IDENTIFIER_MISSING")
            if not manifest_ok:
                links.append(
                    _link(
                        link_id="offline_capability_evidence",
                        path=offline_rel,
                        status=STATUS_INVALID,
                        reason_code=manifest_reason,
                        digest=manifest_digest,
                    )
                )
                blockers.append("offline_capability_evidence:INVALID")
            elif contradictions:
                links.append(
                    _link(
                        link_id="offline_capability_evidence",
                        path=offline_rel,
                        status=STATUS_CONTRADICTORY,
                        reason_code=",".join(contradictions)[:200],
                        digest=manifest_digest,
                        details={"capability_verify_ok": ok_cap, "reasons": list(cap_reasons)},
                    )
                )
                blockers.append("offline_capability_evidence:CONTRADICTORY")
            elif stale_reasons:
                links.append(
                    _link(
                        link_id="offline_capability_evidence",
                        path=offline_rel,
                        status=STATUS_STALE,
                        reason_code=",".join(stale_reasons)[:200],
                        digest=manifest_digest,
                    )
                )
                blockers.append("offline_capability_evidence:STALE")
            elif not ok_cap or not capability_pass:
                links.append(
                    _link(
                        link_id="offline_capability_evidence",
                        path=offline_rel,
                        status=STATUS_UNVERIFIED,
                        reason_code=(
                            ",".join(cap_reasons)[:200]
                            if not ok_cap
                            else "CAPABILITY_RESULT_NOT_PASS"
                        ),
                        digest=manifest_digest,
                    )
                )
                blockers.append("offline_capability_evidence:UNVERIFIED")
            else:
                links.append(
                    _link(
                        link_id="offline_capability_evidence",
                        path=offline_rel,
                        status=STATUS_COMPLETE,
                        reason_code="OFFLINE_EVIDENCE_VERIFIED",
                        digest=manifest_digest,
                        details={
                            "source_git_sha": EXPECTED_OFFLINE_SOURCE_GIT_SHA,
                            "producer": "ops.step_29u_offline_capability_v0",
                        },
                    )
                )

    # 3) Canonical binding evidence (links offline)
    binding_dir = (
        ov.binding_dir.resolve()
        if ov.binding_dir is not None
        else (root / BINDING_EVIDENCE_RELPATH).resolve()
    )
    binding_manifest = binding_dir / "evidence_manifest.sha256"
    binding_prov = binding_dir / "source_provenance.json"
    if not binding_dir.is_dir():
        links.append(
            _link(
                link_id="canonical_binding_evidence",
                path=BINDING_EVIDENCE_RELPATH,
                status=STATUS_ABSENT,
                reason_code="BINDING_EVIDENCE_DIR_ABSENT",
            )
        )
        blockers.append("canonical_binding_evidence:ABSENT")
    elif not binding_manifest.is_file():
        links.append(
            _link(
                link_id="canonical_binding_evidence",
                path=BINDING_EVIDENCE_RELPATH,
                status=STATUS_ABSENT,
                reason_code="MANIFEST_MISSING",
            )
        )
        blockers.append("canonical_binding_evidence:ABSENT")
    else:
        try:
            binding_rel = str(binding_dir.relative_to(root))
        except ValueError:
            binding_rel = str(binding_dir)
        manifest_ok, manifest_reason, manifest_digest = _verify_manifest(
            binding_dir, binding_manifest
        )
        binding_ok, binding_reasons, _payload = verify_canonical_step_29u_binding_evidence_v0(
            repo_root=root,
            evidence_dir=ov.offline_dir if ov.offline_dir is not None else None,
        )
        link_ok = False
        link_reason = "BINDING_SOURCE_PROVENANCE_MISSING"
        if binding_prov.is_file():
            prov = _load_json(binding_prov)
            if isinstance(prov, dict):
                linked = str(prov.get("canonical_step_29u_evidence_relpath") or "").strip()
                producer = str(prov.get("binding_owner") or "").strip()
                if linked != OFFLINE_CAPABILITY_RELPATH:
                    link_reason = "BINDING_OFFLINE_LINK_MISMATCH"
                elif not producer:
                    link_reason = "PRODUCER_SOURCE_IDENTIFIER_MISSING"
                elif prov.get("activation_authorized") is True:
                    link_reason = "BINDING_ACTIVATION_AUTHORIZED_TRUE"
                else:
                    link_ok = True
                    link_reason = "BINDING_LINKS_OFFLINE_EVIDENCE"
        if not manifest_ok:
            links.append(
                _link(
                    link_id="canonical_binding_evidence",
                    path=binding_rel,
                    status=STATUS_INVALID,
                    reason_code=manifest_reason,
                    digest=manifest_digest,
                )
            )
            blockers.append("canonical_binding_evidence:INVALID")
        elif not link_ok:
            status = (
                STATUS_CONTRADICTORY
                if "ACTIVATION" in link_reason or "MISMATCH" in link_reason
                else STATUS_INVALID
            )
            links.append(
                _link(
                    link_id="canonical_binding_evidence",
                    path=binding_rel,
                    status=status,
                    reason_code=link_reason,
                    digest=manifest_digest,
                )
            )
            blockers.append(f"canonical_binding_evidence:{status}")
        elif not binding_ok:
            links.append(
                _link(
                    link_id="canonical_binding_evidence",
                    path=binding_rel,
                    status=STATUS_UNVERIFIED,
                    reason_code=",".join(binding_reasons)[:200] or "BINDING_UNVERIFIED",
                    digest=manifest_digest,
                )
            )
            blockers.append("canonical_binding_evidence:UNVERIFIED")
        else:
            links.append(
                _link(
                    link_id="canonical_binding_evidence",
                    path=binding_rel,
                    status=STATUS_COMPLETE,
                    reason_code=link_reason,
                    digest=manifest_digest,
                    details={"offline_link": OFFLINE_CAPABILITY_RELPATH},
                )
            )

    # 4) Post-merge soak evidence
    soak_dir = (
        ov.soak_dir.resolve()
        if ov.soak_dir is not None
        else (root / SOAK_EVIDENCE_RELPATH).resolve()
    )
    soak_summary = soak_dir / "soak_summary.json"
    soak_manifest = soak_dir / "evidence_manifest.sha256"
    soak_exact = soak_dir / "exact_head.txt"
    if not soak_dir.is_dir():
        links.append(
            _link(
                link_id="post_merge_soak_evidence",
                path=SOAK_EVIDENCE_RELPATH,
                status=STATUS_ABSENT,
                reason_code="SOAK_DIR_ABSENT",
            )
        )
        blockers.append("post_merge_soak_evidence:ABSENT")
    elif not soak_manifest.is_file():
        links.append(
            _link(
                link_id="post_merge_soak_evidence",
                path=SOAK_EVIDENCE_RELPATH,
                status=STATUS_ABSENT,
                reason_code="MANIFEST_MISSING",
            )
        )
        blockers.append("post_merge_soak_evidence:ABSENT")
    elif not soak_summary.is_file():
        links.append(
            _link(
                link_id="post_merge_soak_evidence",
                path=SOAK_EVIDENCE_RELPATH,
                status=STATUS_ABSENT,
                reason_code="SOAK_SUMMARY_ABSENT",
            )
        )
        blockers.append("post_merge_soak_evidence:ABSENT")
    else:
        try:
            soak_rel = str(soak_dir.relative_to(root))
        except ValueError:
            soak_rel = str(soak_dir)
        try:
            manifest_ok, manifest_reason, manifest_digest = _verify_manifest(
                soak_dir, soak_manifest
            )
            payload = _load_json(soak_summary)
            if not isinstance(payload, dict):
                raise Step29UAuditProvenanceError("SOAK_SUMMARY_NOT_OBJECT")
            tested_head = str(payload.get("TESTED_HEAD_SHA") or "").strip()
            exact_head = (
                soak_exact.read_text(encoding="utf-8").strip() if soak_exact.is_file() else ""
            )
            status_field = str(payload.get("STATUS") or "")
            started = _parse_ts(str(payload.get("STARTED_AT_UTC") or ""))
            finished = _parse_ts(str(payload.get("FINISHED_AT_UTC") or ""))
            contradictions: list[str] = []
            if status_field == "PASS" and (
                payload.get("ORDERS_CREATED") is True
                or payload.get("ORDERS_SUBMITTED") is True
                or payload.get("RUNTIME_ACTIVATED") is True
            ):
                contradictions.append("PASS_RESULT_SAFETY_CONTRADICTION")
            if started and finished and finished < started:
                contradictions.append("TIMESTAMP_ORDER_INVALID")
            if not started or not finished:
                contradictions.append("TIMESTAMP_MISSING_OR_INVALID")
            if not manifest_ok:
                links.append(
                    _link(
                        link_id="post_merge_soak_evidence",
                        path=soak_rel,
                        status=STATUS_INVALID,
                        reason_code=manifest_reason,
                        digest=manifest_digest,
                    )
                )
                blockers.append("post_merge_soak_evidence:INVALID")
            elif tested_head != expected_soak_head or (
                exact_head and exact_head != expected_soak_head
            ):
                links.append(
                    _link(
                        link_id="post_merge_soak_evidence",
                        path=soak_rel,
                        status=STATUS_STALE if tested_head else STATUS_INVALID,
                        reason_code="WRONG_GIT_SHA" if tested_head else "GIT_SHA_MISSING",
                        digest=manifest_digest,
                        details={
                            "tested_head": tested_head,
                            "exact_head": exact_head,
                            "expected": expected_soak_head,
                        },
                    )
                )
                blockers.append("post_merge_soak_evidence:STALE")
            elif contradictions:
                links.append(
                    _link(
                        link_id="post_merge_soak_evidence",
                        path=soak_rel,
                        status=STATUS_CONTRADICTORY,
                        reason_code=",".join(contradictions)[:200],
                        digest=manifest_digest,
                    )
                )
                blockers.append("post_merge_soak_evidence:CONTRADICTORY")
            elif status_field != "PASS":
                links.append(
                    _link(
                        link_id="post_merge_soak_evidence",
                        path=soak_rel,
                        status=STATUS_UNVERIFIED,
                        reason_code=f"SOAK_STATUS_{status_field or 'MISSING'}",
                        digest=manifest_digest,
                    )
                )
                blockers.append("post_merge_soak_evidence:UNVERIFIED")
            else:
                links.append(
                    _link(
                        link_id="post_merge_soak_evidence",
                        path=soak_rel,
                        status=STATUS_COMPLETE,
                        reason_code="SOAK_EVIDENCE_VERIFIED",
                        digest=manifest_digest,
                        details={"tested_head": tested_head},
                    )
                )
        except Step29UAuditProvenanceError as exc:
            links.append(
                _link(
                    link_id="post_merge_soak_evidence",
                    path=soak_rel,
                    status=STATUS_INVALID,
                    reason_code=str(exc)[:200],
                )
            )
            blockers.append("post_merge_soak_evidence:INVALID")

    # 5) Activation inventory owner + runbook (tracked composition surface)
    inventory_owner = root / INVENTORY_OWNER_RELPATH
    inventory_runbook = root / INVENTORY_RUNBOOK_RELPATH
    if not inventory_owner.is_file() or not inventory_runbook.is_file():
        links.append(
            _link(
                link_id="activation_inventory_owner",
                path=INVENTORY_OWNER_RELPATH,
                status=STATUS_ABSENT,
                reason_code="INVENTORY_OWNER_OR_RUNBOOK_ABSENT",
            )
        )
        blockers.append("activation_inventory_owner:ABSENT")
    elif not _path_tracked_under_repo(root, inventory_owner) or not _path_tracked_under_repo(
        root, inventory_runbook
    ):
        links.append(
            _link(
                link_id="activation_inventory_owner",
                path=INVENTORY_OWNER_RELPATH,
                status=STATUS_INVALID,
                reason_code="LOCAL_ONLY_CLAIMED_AS_TRACKED",
                digest=_sha256_file(inventory_owner),
            )
        )
        blockers.append("activation_inventory_owner:INVALID")
    else:
        links.append(
            _link(
                link_id="activation_inventory_owner",
                path=INVENTORY_OWNER_RELPATH,
                status=STATUS_COMPLETE,
                reason_code="INVENTORY_OWNER_TRACKED_AND_LINKED",
                digest=_sha256_file(inventory_owner),
                details={"runbook": INVENTORY_RUNBOOK_RELPATH},
            )
        )

    # 6) Supersession guard — historical #5544 soak must not be treated as Step-29U closeout
    superseded_hit = False
    for marker in SUPERSEDED_EVIDENCE_MARKERS:
        marker_path = root / marker
        if marker_path.is_dir() and (soak_dir.resolve() == marker_path.resolve()):
            superseded_hit = True
            break
    if superseded_hit:
        links.append(
            _link(
                link_id="supersession_guard",
                path=SOAK_EVIDENCE_RELPATH,
                status=STATUS_STALE,
                reason_code="SUPERSEDED_EVIDENCE_TREATED_AS_CURRENT",
            )
        )
        blockers.append("supersession_guard:STALE")
    else:
        links.append(
            _link(
                link_id="supersession_guard",
                path="evidence/ops/step_29u_post_merge_shadow_soak/",
                status=STATUS_COMPLETE,
                reason_code="CANONICAL_SOAK_NOT_SUPERSEDED_MARKER",
                details={"superseded_markers_checked": list(SUPERSEDED_EVIDENCE_MARKERS)},
            )
        )

    # Deterministic aggregate
    by_id = {link.link_id: link for link in links}
    missing = [lid for lid in traversal_order if lid not in by_id]
    if missing:
        raise Step29UAuditProvenanceError(f"INCOMPLETE_TRAVERSAL:{','.join(missing)}")
    ordered = tuple(by_id[lid] for lid in traversal_order)

    priority = (
        STATUS_CONTRADICTORY,
        STATUS_INVALID,
        STATUS_STALE,
        STATUS_ABSENT,
        STATUS_UNVERIFIED,
    )
    aggregate = STATUS_COMPLETE
    for candidate in priority:
        if any(link.status == candidate for link in ordered):
            aggregate = candidate
            break

    complete = aggregate == STATUS_COMPLETE and not blockers
    dedup_blockers = tuple(dict.fromkeys(blockers))

    return AuditProvenanceResultV0(
        schema_id=SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        generated_at=evaluated_at,
        evaluated_main_sha=evaluated_sha,
        capability_id=CAPABILITY_ID,
        status=aggregate,
        audit_provenance_complete=complete,
        links=ordered,
        blockers=dedup_blockers,
        traversal_order=traversal_order,
        provenance={
            "package_marker": PACKAGE_MARKER,
            "producer_family": PRODUCER_FAMILY,
            "offline_capability_relpath": OFFLINE_CAPABILITY_RELPATH,
            "binding_evidence_relpath": BINDING_EVIDENCE_RELPATH,
            "soak_evidence_relpath": SOAK_EVIDENCE_RELPATH,
            "expected_soak_tested_head_sha": expected_soak_head,
            "expected_offline_source_git_sha": EXPECTED_OFFLINE_SOURCE_GIT_SHA,
        },
        safety_facts={
            "STEP_29U_ACTIVATED": False,
            "ACTIVATION_ELIGIBLE": False,
            "OPERATOR_GO_INFERRED": False,
            "NETWORK_USED": False,
        },
    )


def serialize_audit_result_json_v0(result: AuditProvenanceResultV0) -> str:
    return json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n"
