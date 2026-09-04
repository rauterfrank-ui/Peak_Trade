"""Repo-wide exhaustive census of persisted restart-handoff candidates.

Read-only. Does not GET. Does not POST. Does not execute a restart.
Does not invent a missing Live durable_state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_execute_v1 import (
    census_live_restart_handoff_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_INSTID,
    BOUND_ORDID,
    LIVE_EVIDENCE_DIRNAME,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_validators_v1 import (
    classify_artifact_role_v1,
)

_LIVE_WRITER_DEF_PREFIXES: tuple[str, ...] = (
    "def write_campaign_durable_state_v1(",
    "def write_actual_start_durable_state_v1(",
)
_SECTION_1114_PREFIX = "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1"
_LIVE_CANARY_PREFIX = "src/ops/section_11_13_5_live_canary_minimum_exposure_v1"


def _classify_durable_tree(relpath: str) -> str:
    normalized = relpath.replace("\\", "/")
    if "section_11_14_live_order_and_economic_evidence_ladder_v1" in normalized:
        return "SECTION_11_14_LIVE_LADDER"
    if "section_11_12" in normalized or "testnet" in normalized.lower():
        return "TESTNET_OR_DEMO_NOT_THIS_FIELD"
    if "phase_9_2" in normalized or "capability_phase_9_2" in normalized:
        return "PHASE_9_2_MD_OR_FIXTURE_NOT_THIS_FIELD"
    if "/fixtures/" in normalized:
        return "FIXTURE_NOT_THIS_FIELD"
    return "UNRELATED_OR_NON_LIVE"


def _scan_writer_markers(repo_root: Path, rel_prefix: str) -> list[str]:
    root = repo_root / rel_prefix
    if not root.is_dir():
        return []
    hits: list[str] = []
    for path in sorted(root.rglob("*.py")):
        lines = path.read_text(encoding="utf-8").splitlines()
        if any(
            line.lstrip().startswith(prefix)
            for line in lines
            for prefix in _LIVE_WRITER_DEF_PREFIXES
        ):
            hits.append(str(path.relative_to(repo_root)))
    return hits


def census_exhaustive_live_restart_handoff_v1(*, repo_root: Path) -> dict[str, Any]:
    root = Path(repo_root)
    bound_census = census_live_restart_handoff_v1(repo_root=root)
    live_root = root / "evidence" / "ops" / LIVE_EVIDENCE_DIRNAME
    live_packs: list[dict[str, Any]] = []
    if live_root.is_dir():
        for pack in sorted(child for child in live_root.iterdir() if child.is_dir()):
            names = sorted(item.name for item in pack.iterdir())
            durable_dir = pack / "durable_state"
            live_packs.append(
                {
                    "run_id": pack.name,
                    "names": names,
                    "durable_state_dir_exists": durable_dir.is_dir(),
                    "durable_state_files": (
                        sorted(
                            str(path.relative_to(root))
                            for path in durable_dir.rglob("*")
                            if path.is_file()
                        )
                        if durable_dir.is_dir()
                        else []
                    ),
                }
            )
    durable_trees: list[dict[str, Any]] = []
    identity_hits: list[str] = []
    search_roots = [root / "evidence", root / "docs" / "evidence"]
    seen: set[str] = set()
    for search_root in search_roots:
        if not search_root.is_dir():
            continue
        for durable_dir in sorted(search_root.rglob("durable_state")):
            if not durable_dir.is_dir():
                continue
            rel = str(durable_dir.relative_to(root))
            if rel in seen:
                continue
            seen.add(rel)
            files = sorted(
                str(path.relative_to(root)) for path in durable_dir.rglob("*") if path.is_file()
            )
            tree_identity_hits: list[str] = []
            for file_rel in files:
                text = (root / file_rel).read_text(encoding="utf-8", errors="replace")
                if BOUND_ORDID in text or BOUND_CLORDID in text:
                    tree_identity_hits.append(file_rel)
                    identity_hits.append(file_rel)
            durable_trees.append(
                {
                    "path": rel,
                    "classification": _classify_durable_tree(rel),
                    "file_count": len(files),
                    "files": files,
                    "bound_identity_hits": tree_identity_hits,
                    "artifact_roles": [classify_artifact_role_v1(path=item) for item in files],
                }
            )
    section_1114_writers = _scan_writer_markers(root, _SECTION_1114_PREFIX)
    live_canary_writers = _scan_writer_markers(root, _LIVE_CANARY_PREFIX)
    live_durable_present = any(
        item["durable_state_dir_exists"] is True or item["durable_state_files"]
        for item in live_packs
    )
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_RESTART_EXHAUSTIVE_CENSUS_V1",
        "BOUND_ORDID": BOUND_ORDID,
        "BOUND_CLORDID": BOUND_CLORDID,
        "BOUND_INSTID": BOUND_INSTID,
        "KNOWN_PACK_CENSUS": bound_census,
        "LIVE_LADDER_PACK_COUNT": len(live_packs),
        "LIVE_LADDER_PACKS": live_packs,
        "DURABLE_STATE_TREE_COUNT": len(durable_trees),
        "DURABLE_STATE_TREES": durable_trees,
        "BOUND_IDENTITY_HITS_IN_DURABLE_STATE": identity_hits,
        "DURABLE_PRE_RESTART_HANDOFF_PRESENT": False,
        "HANDOFF_DISTINCT_FROM_ACCOUNTING_VENUE_GET_PATH": False,
        "LIVE_LADDER_DURABLE_STATE_PRESENT": live_durable_present,
        "SECTION_11_14_DURABLE_STATE_WRITER_HITS": section_1114_writers,
        "LIVE_CANARY_DURABLE_STATE_WRITER_HITS": live_canary_writers,
        "SECTION_11_14_LIVE_DURABLE_STATE_WRITER_EXISTS": bool(section_1114_writers),
        "LIVE_CANARY_DURABLE_STATE_WRITER_EXISTS": bool(live_canary_writers),
        "TESTNET_OR_FIXTURE_DURABLE_STATE_EXISTS": any(
            tree["classification"]
            in {
                "TESTNET_OR_DEMO_NOT_THIS_FIELD",
                "PHASE_9_2_MD_OR_FIXTURE_NOT_THIS_FIELD",
                "FIXTURE_NOT_THIS_FIELD",
            }
            for tree in durable_trees
        ),
        "ACCOUNTING_CLOSURE_IS_NOT_RESTART": True,
        "TESTNET_RESTART_IS_NOT_THIS_FIELD": True,
        "EARLIEST_MISSING_FACT": "DURABLE_LIVE_PRE_RESTART_HANDOFF",
    }
