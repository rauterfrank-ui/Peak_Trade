"""Verify the bounded inventory against the pinned tree. AUTHORITY=NONE."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from scripts.ops.execution_parent_instruments_v1.inventory_v1 import (
    CALL_EDGES,
    OBSERVED_SUBJECTS,
    UNKNOWN_EDGES,
    UNKNOWN_SUBJECT,
)
from scripts.ops.pin_scope_binding_v1.constants_v1 import (
    CENSUS_EMBEDDED_PIN_KEY,
    CENSUS_RELATIVE_PATH,
    CURRENCY_ABSENT,
    CURRENCY_HISTORICAL,
    GRAPH_ABSENT_PIN,
    LANDSCAPE_EMBEDDED_COMMIT_KEY,
    LANDSCAPE_EMBEDDED_TREE_KEY,
    LANDSCAPE_RELATIVE_PATH,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]


def execution_provenance_v1(
    *,
    commit_sha: str,
    tree_sha: str,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Label embedded census and landscape pins as historical."""
    root = _REPO_ROOT if repo_root is None else repo_root
    census = json.loads((root / CENSUS_RELATIVE_PATH).read_text(encoding="utf-8"))
    landscape = json.loads((root / LANDSCAPE_RELATIVE_PATH).read_text(encoding="utf-8"))
    return {
        "census": {
            "pin": str(census[CENSUS_EMBEDDED_PIN_KEY]),
            "currency": CURRENCY_HISTORICAL,
        },
        "landscape": {
            "commit_pin": str(landscape[LANDSCAPE_EMBEDDED_COMMIT_KEY]),
            "tree_pin": str(landscape[LANDSCAPE_EMBEDDED_TREE_KEY]),
            "currency": CURRENCY_HISTORICAL,
        },
        "graph": {"pin": GRAPH_ABSENT_PIN, "currency": CURRENCY_ABSENT},
        "domain_evidence": {
            "commit_pin": commit_sha,
            "tree_pin": tree_sha,
        },
    }


def load_verified_inventory_v1(
    repo_root: Path | None = None,
    *,
    commit_sha: str,
    tree_sha: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Return admission subjects and evidenced edges, or one failure reason."""
    root = _REPO_ROOT if repo_root is None else repo_root
    blobs: dict[str, list[str]] = {}
    subjects: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    for record in OBSERVED_SUBJECTS:
        path = str(record["path"])
        if path not in blobs:
            blob = _git_show(root, f"{tree_sha}:{path}")
            if blob is None:
                return None, "inventory_blob_unreadable"
            blobs[path] = blob.splitlines()
        reason = _subject_reason(blobs[path], record)
        if reason is not None:
            return None, reason
        admitted = {
            "subject_id": record["subject_id"],
            "classification": "OBSERVED",
            "path": path,
            "symbol": record["symbol"],
            "start_line": record["start_line"],
            "end_line": record["end_line"],
        }
        subjects.append(admitted)
        by_id[str(record["subject_id"])] = record
    subjects.append(
        {
            "subject_id": UNKNOWN_SUBJECT["subject_id"],
            "classification": "UNKNOWN",
            "unknown_reason": UNKNOWN_SUBJECT["unknown_reason"],
        }
    )
    edges: list[dict[str, Any]] = []
    for edge in CALL_EDGES:
        source = by_id.get(str(edge["source_subject_id"]))
        target = by_id.get(str(edge["target_subject_id"]))
        if source is None or target is None:
            return None, f"edge_subject_missing:{edge['edge_id']}"
        line_no = int(edge["evidence_line"])
        if not source["start_line"] <= line_no <= source["end_line"]:
            return None, f"edge_line_outside_source:{edge['edge_id']}"
        source_lines = blobs[str(source["path"])]
        if (
            re.search(rf"\b{re.escape(str(edge['callee_symbol']))}\b", source_lines[line_no - 1])
            is None
        ):
            return None, f"edge_call_absent:{edge['edge_id']}"
        edges.append(_call_edge(edge))
    return {
        "pin": commit_sha,
        "tree": tree_sha,
        "disclosure_subjects": subjects,
        "call_edges": edges,
        "unknown_edges": [dict(edge) for edge in UNKNOWN_EDGES],
        "productive_runtime_evidence": False,
        "functional_membership": False,
    }, None


def _subject_reason(lines: list[str], record: dict[str, Any]) -> str | None:
    start = int(record["start_line"])
    end = int(record["end_line"])
    if start < 1 or end > len(lines) or start > end:
        return f"subject_lines:{record['subject_id']}"
    window_lines = lines[start - 1 : end]
    window = "\n".join(window_lines)
    digest = hashlib.sha256(window.encode()).hexdigest()
    if digest != record["source_sha256"]:
        return f"subject_hash_mismatch:{record['subject_id']}"
    if re.search(rf"\b{re.escape(str(record['symbol']))}\b", window) is None:
        return f"subject_symbol_absent:{record['subject_id']}"
    return None


def _call_edge(edge: dict[str, Any]) -> dict[str, Any]:
    return {
        "edge_id": edge["edge_id"],
        "source_native_id": edge["source_subject_id"],
        "target_native_id": edge["target_subject_id"],
        "evidence_plane": "DOMAIN_CODE_REFERENCE",
        "causal_traversal_eligible": True,
        "evidence_line": edge["evidence_line"],
        "typed_edge": {
            "edge_type": "CALLS",
            "trading_authority_implied": False,
        },
        "boundary_reference": bool(edge.get("boundary_reference")),
    }


def _git_show(repo_root: Path, spec: str) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "show", spec],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout
