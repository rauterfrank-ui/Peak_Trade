#!/usr/bin/env python3
"""Build a generic offline evidence run registry from a runtime evidence archive.

Non-authorizing: indexes run metadata only. Does not start runtime, read secrets,
grant Live/Testnet/Go, or imply scheduler/canary/live authority.

Lane semantics: docs/ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md
(§6a remote runtime host metadata; §6a.1 Notion post-closeout sync projection; §6a.2 Market Dashboard read-only run projection; §6a.3 S3 finalized evidence export gate; §6b combined OUTROOT composition-index).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Notion post-closeout sync projection v0 (taxonomy §6a.1): Registry v1 JSON is the sole Notion feed.
NOTION_POST_CLOSEOUT_SYNC_PROJECTION_SPEC_V0 = True
REGISTRY_V1_IS_SOLE_NOTION_PROJECTION_FEED = True

# Market Dashboard read-only run projection v0 (taxonomy §6a.2): Registry v1 JSON is the sole Dashboard feed.
MARKET_DASHBOARD_READONLY_RUN_PROJECTION_SPEC_V0 = True
REGISTRY_V1_IS_SOLE_DASHBOARD_PROJECTION_FEED = True

# S3 finalized evidence export gate v0 (taxonomy §6a.3): transport metadata only; no S3 authority.
S3_FINALIZED_EVIDENCE_EXPORT_GATE_V0 = True
EVIDENCE_TRANSPORT_DEFAULT = "local_only"

SCHEMA = "peak_trade.generic_evidence_run_registry.v1"

# Remote Runtime Host Metadata v0 (taxonomy §6a): run-row metadata; non-authorizing defaults.
# Machine marker: REGISTRY_V1_SECTION_6A_FIELDS_POPULATED=true
REGISTRY_V1_SECTION_6A_FIELDS_POPULATED = True
REMOTE_RUNTIME_HOST_METADATA_CONTRACT_V0 = True

REMOTE_RUNTIME_HOST_METADATA_V0_FIELD_ALLOWED: dict[str, tuple[str, ...]] = {
    "runtime_host": ("local", "remote"),
    "runtime_backend": ("laptop", "ec2", "vps", "data_node", "gha_runner"),
    "runtime_mode": ("paper_only", "paper_then_shadow"),
    "evidence_root_type": ("local_durable", "remote_durable"),
    "evidence_transport": ("local_only", "s3_export_after_finalize"),
    "notion_projection": ("disabled", "post_closeout_sync", "verified_evidence_index"),
    "market_dashboard_projection": (
        "disabled",
        "read_only_run_status",
        "read_only_evidence_status",
    ),
}

REMOTE_RUNTIME_HOST_METADATA_V0_DEFAULTS: dict[str, str | bool] = {
    "runtime_host": "local",
    "runtime_backend": "laptop",
    "runtime_mode": "paper_only",
    "evidence_root_type": "local_durable",
    "evidence_transport": "local_only",
    "notion_projection": "disabled",
    "market_dashboard_projection": "disabled",
    "live_authority": False,
    "testnet_authority": False,
}

SECTION_6A_METADATA_FIELD_NAMES: tuple[str, ...] = tuple(
    REMOTE_RUNTIME_HOST_METADATA_V0_DEFAULTS.keys()
)

TAXONOMY_SPEC_REL = Path("docs/ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md")

VERDICT_PASS_BLOCKED_SAFE = "GENERIC_EVIDENCE_RUN_REGISTRY_PASS_BLOCKED_SAFE"
VERDICT_REVIEW_REQUIRED = "GENERIC_EVIDENCE_RUN_REGISTRY_REVIEW_REQUIRED"
VERDICT_FAIL_CLOSED = "GENERIC_EVIDENCE_RUN_REGISTRY_FAIL_CLOSED"

BLOCKER_HOLD = "HOLD_NO_PAPER_RUN_NOT_CLEARED"
BLOCKER_GLB_014 = "GLB_014_NOT_CLEARED"
BLOCKER_GLB_015 = "GLB_015_NOT_CLEARED"
BLOCKER_PREFLIGHT = "PREFLIGHT_BLOCKED"
BLOCKER_LIVE = "LIVE_NOT_AUTHORIZED"
BLOCKER_BROKER = "BROKER_EXCHANGE_NOT_AUTHORIZED"

PRIMARY_EVIDENCE_LANES = ("paper", "shadow", "testnet")
NON_RUN_LANES = frozenset({"dashboard", "ai_orchestrator", "notion", "docs"})

# Combined OUTROOT composition-index v0 (taxonomy §6b): directory names under runs/ that are
# composition wrappers, not lane_id catalog entries. Does not introduce lane_id=daemon_paper_24h.
COMBINED_OUTROOT_COMPOSITION_INDEX_V0 = True
COMPOSITION_INDEX_DIRECTORIES = frozenset({"daemon_paper_24h"})
COMPOSITION_INDEX_FORBIDDEN_LANE_IDS = frozenset({"daemon_paper_24h", "remote_runtime"})
COMPOSITION_INDEX_DEFAULT_RUNTIME_MODE = "paper_then_shadow"
COMPOSITION_ROLLUP_MANIFEST_REL = Path("manifests") / "MANIFEST.sha256"

UNSAFE_TRUE_KEYS: frozenset[str] = frozenset(
    {
        "SECRET_VALUES_INCLUDED",
        "LIVE_ALLOWED",
        "BROKER_EXCHANGE_ALLOWED",
        "GO_DECISION_GRANTED",
        "CAN_AUTHORIZE_LIVE",
        "CAN_TOUCH_BROKER_EXCHANGE",
        "HOLD_NO_PAPER_RUN_CLEARED",
        "GLB_014_CLEARED",
        "GLB_015_CLEARED",
    }
)

UNSAFE_KEY_TO_CODE: dict[str, str] = {
    "SECRET_VALUES_INCLUDED": "UNSAFE_SECRET_VALUES_INCLUDED",
    "LIVE_ALLOWED": "UNSAFE_LIVE_AUTHORITY",
    "BROKER_EXCHANGE_ALLOWED": "UNSAFE_BROKER_EXCHANGE_AUTHORITY",
    "GO_DECISION_GRANTED": "UNSAFE_GO_DECISION_GRANTED",
    "CAN_AUTHORIZE_LIVE": "UNSAFE_LIVE_AUTHORITY",
    "CAN_TOUCH_BROKER_EXCHANGE": "UNSAFE_BROKER_EXCHANGE_AUTHORITY",
}

MACHINE_LINE_RE = re.compile(r"^([A-Z0-9_]+)=(true|false)\s*$")

GOVERNANCE_KEYS = (
    "go_decision_granted",
    "hold_no_paper_run_cleared",
    "glb_014_cleared",
    "glb_015_cleared",
    "preflight_ready",
    "live_allowed",
    "broker_exchange_allowed",
    "secret_values_included",
)

LANE_DEFAULTS: dict[str, dict[str, Any]] = {
    "paper": {
        "lane_kind": "bounded_runtime_candidate",
        "authority_level": "evidence_only",
        "runtime_allowed_by_default": False,
        "requires_approval_record": True,
        "review_required": False,
        "manifest_required": True,
        "durable_retention_required": True,
        "notion_link_allowed": "index_only",
        "indexing_mode": "runs_directory",
    },
    "shadow": {
        "lane_kind": "bounded_runtime_candidate",
        "authority_level": "evidence_only",
        "runtime_allowed_by_default": False,
        "requires_approval_record": True,
        "review_required": True,
        "manifest_required": True,
        "durable_retention_required": True,
        "notion_link_allowed": "index_only",
        "indexing_mode": "runs_directory",
    },
    "testnet": {
        "lane_kind": "bounded_runtime_candidate",
        "authority_level": "evidence_only",
        "runtime_allowed_by_default": False,
        "requires_approval_record": True,
        "review_required": True,
        "manifest_required": True,
        "durable_retention_required": True,
        "notion_link_allowed": "index_only",
        "indexing_mode": "runs_directory",
    },
    "scheduler": {
        "lane_kind": "infrastructure",
        "authority_level": "planning_only",
        "runtime_allowed_by_default": False,
        "requires_approval_record": False,
        "review_required": False,
        "manifest_required": False,
        "durable_retention_required": False,
        "notion_link_allowed": "false",
        "indexing_mode": "planning_only",
    },
    "canary": {
        "lane_kind": "governance_docs",
        "authority_level": "planning_only",
        "runtime_allowed_by_default": False,
        "requires_approval_record": False,
        "review_required": False,
        "manifest_required": False,
        "durable_retention_required": False,
        "notion_link_allowed": "false",
        "indexing_mode": "absent",
    },
    "live_canary": {
        "lane_kind": "governance_docs",
        "authority_level": "live_authority_requires_separate_record",
        "runtime_allowed_by_default": False,
        "requires_approval_record": True,
        "review_required": True,
        "manifest_required": False,
        "durable_retention_required": False,
        "notion_link_allowed": "false",
        "indexing_mode": "external_record_required",
    },
    "live_production": {
        "lane_kind": "execution",
        "authority_level": "live_authority_requires_separate_record",
        "runtime_allowed_by_default": False,
        "requires_approval_record": True,
        "review_required": True,
        "manifest_required": False,
        "durable_retention_required": False,
        "notion_link_allowed": "false",
        "indexing_mode": "external_record_required",
    },
}


@dataclass
class Issue:
    code: str
    message: str
    path: str | None = None

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.path is not None:
            out["path"] = self.path
        return out


@dataclass
class BuildContext:
    archive_root: Path
    repo_root: Path
    fixed_generated_at_utc: str | None = None
    issues: list[Issue] = field(default_factory=list)

    def add_issue(self, code: str, message: str, path: Path | None = None) -> None:
        rel = None
        if path is not None:
            try:
                rel = str(path.relative_to(self.archive_root))
            except ValueError:
                rel = str(path)
        self.issues.append(Issue(code=code, message=message, path=rel))


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_machine_lines(text: str) -> list[tuple[str, bool]]:
    out: list[tuple[str, bool]] = []
    for raw in text.splitlines():
        match = MACHINE_LINE_RE.match(raw.strip())
        if match:
            out.append((match.group(1), match.group(2) == "true"))
    return out


def _scan_texts(root: Path) -> str:
    if not root.is_dir():
        return ""
    chunks: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".json", ".log", ".txt"}:
            continue
        if path.name in {"MANIFEST.sha256", "MANIFEST_VERIFY.log"}:
            continue
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return "\n".join(chunks)


def _parse_machine_line(text: str, key: str) -> bool | None:
    machine_key = key.upper()
    values = [value for name, value in _iter_machine_lines(text) if name == machine_key]
    if not values:
        return None
    return values[-1]


def _section_6a_runtime_mode_for_lane(lane_id: str) -> str:
    """Return safe §6a runtime_mode default for a lane row (non-authorizing)."""
    if lane_id == "paper":
        return "paper_only"
    return str(REMOTE_RUNTIME_HOST_METADATA_V0_DEFAULTS["runtime_mode"])


def _section_6a_metadata(*, runtime_mode: str | None = None) -> dict[str, str | bool]:
    """Build taxonomy §6a metadata defaults without inferring remote/S3/Notion/Dashboard."""
    out = dict(REMOTE_RUNTIME_HOST_METADATA_V0_DEFAULTS)
    if runtime_mode is not None:
        allowed = REMOTE_RUNTIME_HOST_METADATA_V0_FIELD_ALLOWED["runtime_mode"]
        if runtime_mode not in allowed:
            raise ValueError(f"runtime_mode {runtime_mode!r} not in allowed values {allowed!r}")
        out["runtime_mode"] = runtime_mode
    return out


def _apply_section_6a_metadata(record: dict[str, Any], *, runtime_mode: str | None = None) -> None:
    """Merge §6a fields into an existing runs[] or compositions[] record (additive only)."""
    record.update(_section_6a_metadata(runtime_mode=runtime_mode))


def scan_unsafe_text(text: str, ctx: BuildContext, path: Path) -> None:
    for key, value in _iter_machine_lines(text):
        if not value:
            continue
        if key in UNSAFE_TRUE_KEYS:
            code = UNSAFE_KEY_TO_CODE.get(key, "UNSAFE_PLANNING_MARKER")
            ctx.add_issue(code, f"unsafe machine line {key}=true", path)
        if key == "RUNTIME_ALLOWED_BY_DEFAULT" and value:
            ctx.add_issue(
                "UNSAFE_SCHEDULER_RUNTIME_DEFAULT",
                "scheduler/runtime lane must not claim runtime_allowed_by_default=true",
                path,
            )


def verify_manifest_directory(root: Path, ctx: BuildContext, label: str) -> bool:
    manifest_path = root / "MANIFEST.sha256"
    return _verify_manifest_at_path(root, manifest_path, ctx, label)


def verify_composition_rollup_manifest(
    composition_root: Path, ctx: BuildContext, label: str
) -> bool:
    """Verify manifests/MANIFEST.sha256 rollup on a combined OUTROOT (taxonomy §6b).

    Rollup manifest paths are relative to the composition root. This does not replace
    per-lane MANIFEST.sha256 at runs/{paper,shadow,testnet}/{run_id}/.
    """
    manifest_path = composition_root / COMPOSITION_ROLLUP_MANIFEST_REL
    if not composition_root.is_dir():
        ctx.add_issue("MISSING_RUN_DIR", f"{label} composition directory missing", composition_root)
        return False
    if not manifest_path.is_file():
        ctx.add_issue(
            "MISSING_COMPOSITION_ROLLUP_MANIFEST",
            f"{label} composition rollup manifest missing at manifests/MANIFEST.sha256",
            manifest_path,
        )
        return False
    return _verify_manifest_at_path(composition_root, manifest_path, ctx, label)


def _verify_manifest_at_path(
    root: Path, manifest_path: Path, ctx: BuildContext, label: str
) -> bool:
    if not root.is_dir():
        ctx.add_issue("MISSING_RUN_DIR", f"{label} run directory missing", root)
        return False
    if not manifest_path.is_file():
        ctx.add_issue("MISSING_MANIFEST", f"{label} MANIFEST.sha256 missing", manifest_path)
        return False

    ok = True
    for line_no, raw in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            ctx.add_issue(
                "MANIFEST_ENTRY_MISSING",
                f"{label} MANIFEST line {line_no} invalid",
                manifest_path,
            )
            ok = False
            continue
        expected_hash, rel_path = parts
        target = root / rel_path
        if not target.is_file():
            ctx.add_issue(
                "MANIFEST_ENTRY_MISSING",
                f"{label} manifest entry missing file: {rel_path}",
                target,
            )
            ok = False
            continue
        if _sha256_file(target) != expected_hash:
            ctx.add_issue(
                "MANIFEST_HASH_MISMATCH",
                f"{label} hash mismatch for {rel_path}",
                target,
            )
            ok = False
    return ok


def _load_review_verdict(review_path: Path) -> tuple[str | None, str | None]:
    if not review_path.is_file():
        return None, "missing"
    try:
        payload = json.loads(review_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"invalid JSON: {exc}"
    verdict = payload.get("verdict")
    if not isinstance(verdict, str):
        return None, "verdict missing or not string"
    return verdict, None


def _discover_lane_runs(archive_root: Path) -> list[tuple[str, Path]]:
    runs_root = archive_root / "runs"
    if not runs_root.is_dir():
        return []
    out: list[tuple[str, Path]] = []
    for lane_dir in sorted(runs_root.iterdir()):
        if not lane_dir.is_dir():
            continue
        lane_id = lane_dir.name
        if lane_id in COMPOSITION_INDEX_DIRECTORIES:
            continue
        for run_dir in sorted(lane_dir.iterdir()):
            if run_dir.is_dir():
                out.append((lane_id, run_dir))
    return out


def _discover_composition_runs(archive_root: Path) -> list[tuple[str, Path]]:
    runs_root = archive_root / "runs"
    if not runs_root.is_dir():
        return []
    out: list[tuple[str, Path]] = []
    for composition_id in sorted(COMPOSITION_INDEX_DIRECTORIES):
        composition_lane = runs_root / composition_id
        if not composition_lane.is_dir():
            continue
        for run_dir in sorted(composition_lane.iterdir()):
            if run_dir.is_dir():
                out.append((composition_id, run_dir))
    return out


def _discover_all_runs(archive_root: Path) -> list[tuple[str, Path]]:
    """Backward-compatible alias: lane runs only (excludes composition-index directories)."""
    return _discover_lane_runs(archive_root)


def _infer_child_lane_refs(
    archive_root: Path, run_id: str, *, expected_lanes: tuple[str, ...] = ("paper", "shadow")
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for lane_id in expected_lanes:
        child_dir = archive_root / "runs" / lane_id / run_id
        present = child_dir.is_dir()
        ref: dict[str, Any] = {
            "lane_id": lane_id,
            "present": present,
        }
        if present:
            ref["archive_path"] = str(child_dir.relative_to(archive_root).as_posix())
            ref["manifest_present"] = (child_dir / "MANIFEST.sha256").is_file()
        else:
            ref["archive_path"] = None
            ref["manifest_present"] = False
        refs.append(ref)
    return refs


def _build_composition_record(
    composition_root: Path,
    composition_id: str,
    ctx: BuildContext,
    lane_run_index: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    run_id = composition_root.name
    scan_unsafe_text(_scan_texts(composition_root), ctx, composition_root)

    child_lane_refs = _infer_child_lane_refs(ctx.archive_root, run_id)
    child_present_count = sum(1 for ref in child_lane_refs if ref["present"])
    child_manifest_count = sum(1 for ref in child_lane_refs if ref.get("manifest_present"))

    rollup_path = composition_root / COMPOSITION_ROLLUP_MANIFEST_REL
    rollup_present = rollup_path.is_file()
    if rollup_present:
        rollup_verified = verify_composition_rollup_manifest(composition_root, ctx, composition_id)
    else:
        ctx.add_issue(
            "MISSING_COMPOSITION_ROLLUP_MANIFEST",
            (
                f"composition {composition_id!r} rollup manifest missing at "
                "manifests/MANIFEST.sha256"
            ),
            rollup_path,
        )
        rollup_verified = False

    root_manifest_present = (composition_root / "MANIFEST.sha256").is_file()
    if root_manifest_present:
        ctx.add_issue(
            "COMPOSITION_ROOT_MANIFEST_NOT_PRIMARY",
            (
                f"composition {composition_id!r} must not use root MANIFEST.sha256; "
                "per-lane primary evidence remains at runs/{lane}/{run_id}/MANIFEST.sha256; "
                "composition rollup belongs at manifests/MANIFEST.sha256 only"
            ),
            composition_root / "MANIFEST.sha256",
        )

    child_lane_status: list[dict[str, Any]] = []
    for ref in child_lane_refs:
        lane_id = ref["lane_id"]
        lane_row = lane_run_index.get((lane_id, run_id))
        status = {
            "lane_id": lane_id,
            "present": ref["present"],
            "manifest_present": ref.get("manifest_present", False),
        }
        if lane_row is not None:
            status["evidence_status"] = lane_row.get("evidence_status")
            status["manifest_verified"] = lane_row.get("manifest_verified")
        elif ref["present"]:
            status["evidence_status"] = "unknown"
            status["manifest_verified"] = ref.get("manifest_present", False)
        else:
            status["evidence_status"] = "missing"
            status["manifest_verified"] = False
        child_lane_status.append(status)

    if not rollup_present:
        composition_evidence_status = "incomplete"
    elif not rollup_verified:
        composition_evidence_status = "incomplete"
    elif child_present_count < len(child_lane_refs):
        composition_evidence_status = "partial"
    else:
        child_statuses = [s.get("evidence_status") for s in child_lane_status if s["present"]]
        if any(s not in ("verified", None) for s in child_statuses):
            composition_evidence_status = "partial"
        else:
            composition_evidence_status = "indexed"

    rel_archive = str(composition_root.relative_to(ctx.archive_root).as_posix())

    record: dict[str, Any] = {
        "record_kind": "composition_index",
        "composition_id": composition_id,
        "run_id": run_id,
        "runtime_mode": COMPOSITION_INDEX_DEFAULT_RUNTIME_MODE,
        "archive_path": rel_archive,
        "rollup_manifest_present": rollup_present,
        "rollup_manifest_path": COMPOSITION_ROLLUP_MANIFEST_REL.as_posix(),
        "rollup_manifest_verified": rollup_verified,
        "root_manifest_present": root_manifest_present,
        "child_lane_refs": child_lane_refs,
        "child_lane_status": child_lane_status,
        "child_lanes_present": child_present_count,
        "child_lanes_with_manifest": child_manifest_count,
        "composition_index_authority": False,
        "live_authority": False,
        "testnet_authority": False,
        "s3_authority": False,
        "notion_authority": False,
        "market_dashboard_authority": False,
        "can_clear_hold": False,
        "can_clear_glb": False,
        "can_authorize_live": False,
        "can_touch_broker_exchange": False,
        "protected_master_v2_boundary": True,
        "evidence_status": composition_evidence_status,
        "issues": [],
    }
    _apply_section_6a_metadata(record, runtime_mode=COMPOSITION_INDEX_DEFAULT_RUNTIME_MODE)
    return record


def _build_run_record(
    run_dir: Path,
    lane_id: str,
    ctx: BuildContext,
) -> dict[str, Any]:
    run_issues: list[dict[str, Any]] = []

    if lane_id in NON_RUN_LANES:
        ctx.add_issue(
            "UNSAFE_NON_RUN_SURFACE_AUTHORITY",
            f"non-run lane {lane_id!r} must not appear as executable run evidence",
            run_dir,
        )
        defaults = {
            "lane_kind": "display",
            "authority_level": "review_input_only",
            "runtime_allowed_by_default": False,
            "requires_approval_record": False,
            "review_required": False,
            "manifest_required": False,
            "durable_retention_required": False,
            "notion_link_allowed": "false",
        }
    elif lane_id not in LANE_DEFAULTS:
        ctx.add_issue("UNKNOWN_LANE", f"unknown lane {lane_id!r}", run_dir)
        defaults = LANE_DEFAULTS["paper"].copy()
    else:
        defaults = LANE_DEFAULTS[lane_id]

    scan_unsafe_text(_scan_texts(run_dir), ctx, run_dir)

    manifest_present = (run_dir / "MANIFEST.sha256").is_file()
    if defaults.get("manifest_required") and not manifest_present:
        ctx.add_issue(
            "MISSING_MANIFEST",
            f"{lane_id} MANIFEST.sha256 missing",
            run_dir / "MANIFEST.sha256",
        )
    manifest_verified = (
        verify_manifest_directory(run_dir, ctx, lane_id) if manifest_present else False
    )

    review_path = run_dir / "review" / "REVIEW_RESULT.json"
    review_present = review_path.is_file()
    review_verdict: str | None = None
    if defaults["review_required"]:
        verdict, err = _load_review_verdict(review_path)
        if err == "missing":
            ctx.add_issue(
                "MISSING_REVIEW_JSON",
                f"{lane_id} review/REVIEW_RESULT.json missing",
                review_path,
            )
        elif err is not None:
            ctx.add_issue(
                "MISSING_REVIEW_JSON",
                f"{lane_id} review invalid: {err}",
                review_path,
            )
        else:
            review_verdict = verdict
            if verdict != "PASS":
                ctx.add_issue(
                    "REVIEW_VERDICT_NOT_PASS",
                    f"{lane_id} review verdict must be PASS, got {verdict!r}",
                    review_path,
                )
    elif review_present:
        review_verdict, _ = _load_review_verdict(review_path)

    if lane_id == "scheduler" and defaults["runtime_allowed_by_default"]:
        ctx.add_issue(
            "UNSAFE_SCHEDULER_RUNTIME_DEFAULT",
            "scheduler lane runtime_allowed_by_default must be false",
            run_dir,
        )

    if lane_id in {"live_canary", "live_production"}:
        ctx.add_issue(
            "MISSING_EXTERNAL_LIVE_RECORD",
            f"{lane_id} run present without separate external live authority record",
            run_dir,
        )

    evidence_status = "verified"
    if not manifest_verified:
        evidence_status = "incomplete"
    elif defaults["review_required"] and review_verdict != "PASS":
        evidence_status = "failed_review"

    rel_archive = str(run_dir.relative_to(ctx.archive_root).as_posix())

    record: dict[str, Any] = {
        "run_id": run_dir.name,
        "lane_id": lane_id,
        "lane_kind": defaults["lane_kind"],
        "archive_path": rel_archive,
        "manifest_present": manifest_present,
        "manifest_verified": manifest_verified,
        "review_required": defaults["review_required"],
        "review_present": review_present,
        "review_verdict": review_verdict,
        "durable_retention_required": defaults["durable_retention_required"],
        "durable_retention_verified": manifest_verified and not str(run_dir).startswith("/tmp"),
        "notion_link_allowed": defaults["notion_link_allowed"],
        "notion_link_present": "notion" in _scan_texts(run_dir).lower(),
        "authority_level": defaults["authority_level"],
        "runtime_allowed_by_default": defaults["runtime_allowed_by_default"],
        "requires_approval_record": defaults["requires_approval_record"],
        "can_clear_hold": False,
        "can_clear_glb": False,
        "can_authorize_live": False,
        "can_touch_broker_exchange": False,
        "protected_master_v2_boundary": True,
        "evidence_status": evidence_status,
        "issues": run_issues,
    }
    _apply_section_6a_metadata(record, runtime_mode=_section_6a_runtime_mode_for_lane(lane_id))
    return record


def _lane_catalog_entry(lane_id: str, discovered: int) -> dict[str, Any]:
    defaults = LANE_DEFAULTS[lane_id]
    mode = defaults["indexing_mode"]
    if discovered == 0 and lane_id in PRIMARY_EVIDENCE_LANES:
        mode = "runs_directory"
    elif discovered == 0:
        mode = defaults["indexing_mode"]
    return {
        "lane_id": lane_id,
        "lane_kind": defaults["lane_kind"],
        "discovered_run_count": discovered,
        "default_authority_level": defaults["authority_level"],
        "runtime_allowed_by_default": defaults["runtime_allowed_by_default"],
        "indexing_mode": mode,
    }


def derive_governance(planning_root: Path) -> dict[str, bool]:
    blob = _scan_texts(planning_root)
    governance: dict[str, bool] = {}
    for key in GOVERNANCE_KEYS:
        parsed = _parse_machine_line(blob, key.upper())
        governance[key] = parsed if parsed is not None else False
    governance["governance_blocked"] = (
        not governance.get("go_decision_granted", False)
        and not governance.get("live_allowed", False)
        and not governance.get("broker_exchange_allowed", False)
        and (
            not governance.get("hold_no_paper_run_cleared", False)
            or not governance.get("glb_014_cleared", False)
            or not governance.get("glb_015_cleared", False)
            or not governance.get("preflight_ready", False)
        )
    )
    governance["evidence_does_not_authorize_runtime"] = True
    return governance


def derive_blockers(governance: dict[str, bool]) -> list[str]:
    blockers: list[str] = []
    if not governance.get("hold_no_paper_run_cleared", False):
        blockers.append(BLOCKER_HOLD)
    if not governance.get("glb_014_cleared", False):
        blockers.append(BLOCKER_GLB_014)
    if not governance.get("glb_015_cleared", False):
        blockers.append(BLOCKER_GLB_015)
    if not governance.get("preflight_ready", False):
        blockers.append(BLOCKER_PREFLIGHT)
    if not governance.get("live_allowed", False):
        blockers.append(BLOCKER_LIVE)
    if not governance.get("broker_exchange_allowed", False):
        blockers.append(BLOCKER_BROKER)
    return sorted(set(blockers))


def derive_verdict(ctx: BuildContext) -> str:
    codes = {issue.code for issue in ctx.issues}
    fail_codes = {
        "UNSAFE_LIVE_AUTHORITY",
        "UNSAFE_BROKER_EXCHANGE_AUTHORITY",
        "UNSAFE_SECRET_VALUES_INCLUDED",
        "UNSAFE_GO_DECISION_GRANTED",
        "UNSAFE_SCHEDULER_RUNTIME_DEFAULT",
        "UNSAFE_NON_RUN_SURFACE_AUTHORITY",
        "UNSAFE_TESTNET_TO_LIVE_PROMOTION",
        "MANIFEST_HASH_MISMATCH",
        "REVIEW_VERDICT_NOT_PASS",
        "MASTER_V2_DOUBLE_PLAY_BOUNDARY_NOT_PROTECTED",
    }
    if codes & fail_codes or any(c.startswith("UNSAFE_") for c in codes):
        return VERDICT_FAIL_CLOSED
    review_codes = {
        "MISSING_ARCHIVE_ROOT",
        "MISSING_TAXONOMY_SPEC",
        "MISSING_RUN_DIR",
        "MISSING_MANIFEST",
        "MANIFEST_ENTRY_MISSING",
        "MISSING_REVIEW_JSON",
        "MISSING_EXTERNAL_LIVE_RECORD",
        "MISSING_COMPOSITION_ROLLUP_MANIFEST",
        "COMPOSITION_ROOT_MANIFEST_NOT_PRIMARY",
    }
    if codes & review_codes:
        return VERDICT_REVIEW_REQUIRED
    return VERDICT_PASS_BLOCKED_SAFE


def build_registry(ctx: BuildContext) -> dict[str, Any]:
    archive_root = ctx.archive_root
    if not archive_root.is_dir():
        ctx.add_issue("MISSING_ARCHIVE_ROOT", "archive root does not exist", archive_root)

    taxonomy_path = ctx.repo_root / TAXONOMY_SPEC_REL
    if not taxonomy_path.is_file():
        ctx.add_issue("MISSING_TAXONOMY_SPEC", "taxonomy spec missing on main", taxonomy_path)

    planning_root = archive_root / "planning"
    scan_unsafe_text(_scan_texts(planning_root), ctx, planning_root)

    runs: list[dict[str, Any]] = []
    compositions: list[dict[str, Any]] = []
    runs_by_lane: dict[str, int] = {lid: 0 for lid in LANE_DEFAULTS}

    for lane_id, run_dir in _discover_lane_runs(archive_root):
        runs_by_lane[lane_id] = runs_by_lane.get(lane_id, 0) + 1
        runs.append(_build_run_record(run_dir, lane_id, ctx))

    lane_run_index = {(r["lane_id"], r["run_id"]): r for r in runs}

    for composition_id, composition_root in _discover_composition_runs(archive_root):
        compositions.append(
            _build_composition_record(composition_root, composition_id, ctx, lane_run_index)
        )

    # Testnet PASS must not imply live — check planning/run text for promotion markers
    blob = _scan_texts(archive_root)
    if _parse_machine_line(blob, "TESTNET_AUTHORIZED") is True:
        ctx.add_issue(
            "UNSAFE_TESTNET_TO_LIVE_PROMOTION",
            "TESTNET_AUTHORIZED=true must not appear in archive evidence",
            archive_root,
        )

    governance = derive_governance(planning_root)
    if governance.get("live_allowed"):
        ctx.add_issue("UNSAFE_LIVE_AUTHORITY", "live_allowed=true in planning", planning_root)
    if governance.get("broker_exchange_allowed"):
        ctx.add_issue(
            "UNSAFE_BROKER_EXCHANGE_AUTHORITY",
            "broker_exchange_allowed=true in planning",
            planning_root,
        )
    if governance.get("secret_values_included"):
        ctx.add_issue(
            "UNSAFE_SECRET_VALUES_INCLUDED",
            "secret_values_included=true in planning",
            planning_root,
        )
    if governance.get("go_decision_granted"):
        ctx.add_issue(
            "UNSAFE_GO_DECISION_GRANTED",
            "go_decision_granted=true in planning",
            planning_root,
        )

    for run in runs:
        if not run.get("protected_master_v2_boundary", True):
            ctx.add_issue(
                "MASTER_V2_DOUBLE_PLAY_BOUNDARY_NOT_PROTECTED",
                "run record must protect Master V2 / Double Play boundary",
                archive_root / run["archive_path"],
            )

    verified = sum(1 for r in runs if r["evidence_status"] == "verified")
    review_required_runs = sum(1 for r in runs if r["review_required"])
    fail_closed_runs = sum(1 for r in runs if r["evidence_status"] == "failed_review")

    lanes = [_lane_catalog_entry(lid, runs_by_lane.get(lid, 0)) for lid in LANE_DEFAULTS]

    generated_at = ctx.fixed_generated_at_utc or os.environ.get("PEAK_TRADE_FIXED_GENERATED_AT_UTC")
    if not generated_at:
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    blockers = derive_blockers(governance)
    verdict = derive_verdict(ctx)

    summaries = {
        "total_runs": len(runs),
        "total_compositions": len(compositions),
        "runs_by_lane": {k: runs_by_lane.get(k, 0) for k in PRIMARY_EVIDENCE_LANES},
        "verified_runs": verified,
        "review_required_runs": review_required_runs,
        "fail_closed_runs": fail_closed_runs,
        "primary_evidence_lanes_present": all(
            runs_by_lane.get(l, 0) > 0 for l in PRIMARY_EVIDENCE_LANES
        ),
        "scheduler_boundary_gap_acknowledged": True,
        "live_authority_present": governance.get("live_allowed", False),
        "broker_exchange_authority_present": governance.get("broker_exchange_allowed", False),
    }

    authority = {
        **governance,
        "scheduler_boundary_gap_acknowledged": True,
        "master_v2_double_play_boundary_preserved": True,
    }

    return {
        "schema": SCHEMA,
        "generated_at_utc": generated_at,
        "archive_root": str(archive_root.resolve()),
        "lanes": lanes,
        "runs": runs,
        "compositions": compositions,
        "summaries": summaries,
        "authority": authority,
        "blockers": blockers,
        "verdict": verdict,
        "issues": [issue.as_dict() for issue in ctx.issues],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=_repo_root())
    parser.add_argument("--fixed-generated-at-utc")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ctx = BuildContext(
        archive_root=args.archive_root.expanduser().resolve(),
        repo_root=args.repo_root.expanduser().resolve(),
        fixed_generated_at_utc=args.fixed_generated_at_utc,
    )
    registry = build_registry(ctx)
    if args.json:
        print(json.dumps(registry, indent=2, sort_keys=False))
    else:
        print(f"verdict={registry['verdict']}")
        print(f"total_runs={registry['summaries']['total_runs']}")
        print(f"issues={len(registry['issues'])}")
    if registry["verdict"] == VERDICT_FAIL_CLOSED:
        return 2
    if registry["verdict"] == VERDICT_REVIEW_REQUIRED:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
