"""Load CURRENT evidence from a pinned git tree. Never from the worktree."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.ops.mv2_outer_boundary_projector_v1.constants_v1 import (
    CAUSAL_INTEGRATION_PATH,
    CENSUS_PATH,
    CENSUS_TOPOLOGY_ID,
    CYCLE_OWNER_CITATION,
    CYCLE_PATH,
    DECISION_SPEC_PATH,
    DOUBLE_PLAY_ROLE_CITATION,
    GHOSV_EXECUTION_PATH,
    GHV_CROSSWALK_DIR,
    GHV_PURE_FILES,
    HARDENING_PATH,
    LANDSCAPE_PATH,
    MV2_PLANES,
    NON_TRANSFER_MARKERS,
    REPLAY_PATH,
    REPLAY_SYMBOL,
    REQUIRED_DECISION_LINES,
)
from scripts.ops.mv2_outer_boundary_projector_v1.input_contract_v1 import (
    ProjectorFailClosedV1,
)


def git_bytes(repo_root: Path, args: list[str]) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ProjectorFailClosedV1("GIT_READ_FAILED", detail or " ".join(args))
    return completed.stdout


def git_text(repo_root: Path, args: list[str]) -> str:
    return git_bytes(repo_root, args).decode("utf-8")


def git_ok(repo_root: Path, args: list[str]) -> bool:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    return completed.returncode == 0


def validate_pin_v1(repo_root: Path, commit: str, tree: str) -> None:
    if not git_ok(repo_root, ["cat-file", "-e", f"{commit}^{{commit}}"]):
        raise ProjectorFailClosedV1("COMMIT_ABSENT", commit)
    actual = git_text(repo_root, ["rev-parse", f"{commit}^{{tree}}"]).strip()
    if actual != tree:
        raise ProjectorFailClosedV1("TREE_MISMATCH", f"actual={actual} declared={tree}")


def show_text(repo_root: Path, commit: str, path: str) -> str:
    if not git_ok(repo_root, ["cat-file", "-e", f"{commit}:{path}"]):
        raise ProjectorFailClosedV1("PINNED_PATH_ABSENT", path)
    return git_text(repo_root, ["show", f"{commit}:{path}"])


def blob_id(repo_root: Path, commit: str, path: str) -> str:
    return git_text(repo_root, ["rev-parse", f"{commit}:{path}"]).strip()


def is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    if completed.returncode == 0:
        return True
    if completed.returncode == 1:
        return False
    detail = completed.stderr.decode("utf-8", errors="replace").strip()
    raise ProjectorFailClosedV1("GIT_READ_FAILED", detail or "merge-base")


def _plane_is_mv2(plane: object) -> bool:
    return str(plane or "").strip().lower() in MV2_PLANES


def _require_decision_text(text: str) -> str:
    missing = [line for line in REQUIRED_DECISION_LINES if line not in text]
    if missing:
        raise ProjectorFailClosedV1("DECISION_SOURCE_INCOMPLETE", ",".join(missing))
    if REPLAY_SYMBOL not in text:
        raise ProjectorFailClosedV1("DECISION_SOURCE_INCOMPLETE", REPLAY_SYMBOL)
    marker = "CURRENT_REFERENCE_BASELINE="
    start = text.find(marker)
    if start < 0:
        raise ProjectorFailClosedV1("DECISION_SOURCE_INCOMPLETE", marker)
    baseline = text[start + len(marker) : start + len(marker) + 40]
    if len(baseline) != 40 or any(char not in "0123456789abcdef" for char in baseline):
        raise ProjectorFailClosedV1("DECISION_REFERENCE_BASELINE", baseline)
    for _name, needle in NON_TRANSFER_MARKERS:
        if needle not in text:
            raise ProjectorFailClosedV1("DECISION_SOURCE_INCOMPLETE", needle)
    return baseline


@dataclass
class PinnedGhvHelpersV1:
    census_flow_to_typed_edge: Any
    traverse_forensic_graph_v1: Any
    build_cfi_v1: Any
    provenance_record_v1: Any
    blob_ids: dict[str, str]
    loaded_from: str = "PINNED_COMMIT_BLOBS"


@dataclass
class PinnedSourcesV1:
    reference_baseline: str
    reference_is_ancestor: bool
    code_diff_empty: bool
    replay_defined: bool
    cycle_owner_cites_replay: bool
    double_play_role_confirmed: bool
    census_candidates: list[dict[str, Any]]
    census_outer_edges: list[dict[str, Any]]
    census_pin: str
    census_pin_is_ancestor: bool
    landscape_authority: dict[str, Any]
    historical_graphs: list[dict[str, Any]]
    causal_graph_status: str
    causal_graph_verified: bool
    causal_integration_blob: str
    ghosv_execution_blob: str
    current_graph_ghosv_paths: list[str]
    non_transfer_components: list[dict[str, Any]]
    ghv: PinnedGhvHelpersV1
    worktree_ghv_drift: dict[str, str] = field(default_factory=dict)
    decision_blob: str = ""
    census_blob: str = ""


def load_pinned_ghv_helpers_v1(repo_root: Path, commit: str) -> PinnedGhvHelpersV1:
    """Import pure GHV helpers from pinned blobs, not from a drifted worktree."""

    blob_ids: dict[str, str] = {}
    sources: dict[str, str] = {}
    for name in GHV_PURE_FILES:
        path = f"{GHV_CROSSWALK_DIR}/{name}"
        blob_ids[path] = blob_id(repo_root, commit, path)
        sources[name] = show_text(repo_root, commit, path)
    prefix = f"mv2_obp_pinned_ghv_{commit[:12]}"
    constants_mod = f"{prefix}_constants_v1"
    identity_mod = f"{prefix}_identity_v1"
    edges_mod = f"{prefix}_edges_v1"
    traversal_mod = f"{prefix}_traversal_v1"
    rewritten = {
        "constants_v1.py": sources["constants_v1.py"],
        "identity_v1.py": sources["identity_v1.py"].replace(
            "scripts.ops.ghv_forensic_whole_system_crosswalk_v1.constants_v1",
            constants_mod,
        ),
        "edges_v1.py": sources["edges_v1.py"].replace(
            "scripts.ops.ghv_forensic_whole_system_crosswalk_v1.constants_v1",
            constants_mod,
        ),
        "traversal_v1.py": sources["traversal_v1.py"],
    }
    for name, text in rewritten.items():
        if name == "constants_v1.py":
            continue
        if "scripts.ops.ghv_forensic_whole_system_crosswalk_v1" in text:
            raise ProjectorFailClosedV1("GHV_PIN_IMPORT_REWRITE", name)
    module_names = {
        "constants_v1.py": constants_mod,
        "identity_v1.py": identity_mod,
        "edges_v1.py": edges_mod,
        "traversal_v1.py": traversal_mod,
    }
    loaded: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="mv2_obp_ghv_") as tmp:
        root = Path(tmp)
        for name, text in rewritten.items():
            file_path = root / name
            file_path.write_text(text, encoding="utf-8")
            module_name = module_names[name]
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                raise ProjectorFailClosedV1("GHV_PIN_LOAD_FAILED", name)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            loaded[name] = module
    return PinnedGhvHelpersV1(
        census_flow_to_typed_edge=loaded["edges_v1.py"].census_flow_to_typed_edge,
        traverse_forensic_graph_v1=loaded["traversal_v1.py"].traverse_forensic_graph_v1,
        build_cfi_v1=loaded["identity_v1.py"].build_cfi_v1,
        provenance_record_v1=loaded["identity_v1.py"].ProvenanceRecordV1,
        blob_ids=blob_ids,
    )


def _worktree_drift(repo_root: Path, commit: str) -> dict[str, str]:
    drift: dict[str, str] = {}
    for name in GHV_PURE_FILES:
        relative = f"{GHV_CROSSWALK_DIR}/{name}"
        pinned = blob_id(repo_root, commit, relative)
        worktree_file = repo_root / relative
        if not worktree_file.is_file():
            drift[relative] = f"WORKTREE_ABSENT pinned={pinned}"
            continue
        completed = subprocess.run(
            ["git", "hash-object", str(worktree_file)],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            drift[relative] = "WORKTREE_HASH_FAILED"
            continue
        actual = completed.stdout.strip()
        if actual != pinned:
            drift[relative] = f"DRIFT worktree={actual} pinned={pinned}"
    return drift


def _census_views(
    census: dict[str, Any],
    *,
    commit: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    member_ids: set[str] = set()
    for topology in census.get("topology_domains") or []:
        if topology.get("topology_id") != CENSUS_TOPOLOGY_ID:
            continue
        for object_id in topology.get("positive_member_object_ids") or []:
            member_ids.add(str(object_id))
    objects = {str(item.get("object_id")): item for item in (census.get("census_objects") or [])}
    candidates: list[dict[str, Any]] = []
    for object_id in sorted(member_ids):
        obj = objects.get(object_id) or {}
        candidates.append(
            {
                "component_id": f"census:{object_id}",
                "census_object_id": object_id,
                "name": obj.get("name"),
                "paths": list(obj.get("paths") or []),
                "census_primary_class": obj.get("primary_class"),
                "basis": "CENSUS_TAXONOMY",
                "classification": "POSSIBLE_MV2_MEMBER_UNCLASSIFIED",
                "membership_granted": False,
                "universe_ratification": False,
                "proof_status": "NOT_PROVEN",
                "uncertainty": "CENSUS_AUTHORITY_NONE_PACKAGE_OR_TAXONOMY_LABEL",
                "baseline": commit,
            }
        )
    edges: list[dict[str, Any]] = []
    for edge in census.get("semantic_edges") or []:
        source_object = str(edge.get("source_object") or "")
        target_object = str(edge.get("target_object") or "")
        source_mv2 = _plane_is_mv2(edge.get("source_universe_or_plane")) or (
            source_object in member_ids
        )
        target_mv2 = _plane_is_mv2(edge.get("target_universe_or_plane")) or (
            target_object in member_ids
        )
        if source_mv2 == target_mv2:
            continue
        if target_mv2 and not source_mv2:
            direction = "INBOUND"
        elif source_mv2 and not target_mv2:
            direction = "OUTBOUND"
        else:
            direction = "UNKNOWN"
        edges.append(
            {
                "edge_id": str(edge.get("edge_id") or ""),
                "source_id": source_object,
                "target_id": target_object,
                "original_flow_type": edge.get("flow_type"),
                "endpoint_resolution": "PACKAGE",
                "source_kind": "CENSUS_NAVIGATION",
                "baseline": commit,
                "artifact": CENSUS_PATH,
                "authority": "NONE",
                "corroboration": None,
                "observed_direction": direction,
                "contract_or_payload": edge.get("contract_or_payload"),
                "current_proof": False,
            }
        )
    census_pin = str(census.get("source_baseline_head") or "")
    return candidates, edges, census_pin


def _historical_graphs(repo_root: Path, commit: str, paths: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        if not path.endswith("composed_forensic_graph.v1.json"):
            continue
        document = json.loads(show_text(repo_root, commit, path))
        code_snapshot = document.get("code_snapshot") or {}
        git_head = str(code_snapshot.get("git_head") or "")
        records.append(
            {
                "path": path,
                "snapshot_id": document.get("snapshot_id"),
                "git_head": git_head,
                "graph_claims_current_verified": document.get("CURRENT_GRAPH_VERIFIED"),
                "current_proof": False,
                "reason": "HISTORICAL_GRAPH_BASELINE_DIFFERS"
                if git_head != commit
                else "STORED_GRAPH_NOT_ADMITTED_WITHOUT_FRESH_DRIFT_PROOF",
                "edges_used_as_current_boundary_proof": False,
            }
        )
    records.sort(key=lambda item: str(item["path"]))
    return records


def _causal_status(paths: list[str]) -> tuple[str, bool]:
    integrated = [path for path in paths if path.endswith("integrated_causal_graph.v1.json")]
    if not integrated:
        return "NOT_MATERIALIZED", False
    return "PRESENT_UNVERIFIED_FOR_THIS_PROJECTOR", False


def load_pinned_sources_v1(repo_root: Path, commit: str) -> PinnedSourcesV1:
    decision = show_text(repo_root, commit, DECISION_SPEC_PATH)
    reference = _require_decision_text(decision)
    reference_ancestor = is_ancestor(repo_root, reference, commit)
    replay_text = show_text(repo_root, commit, REPLAY_PATH)
    cycle_text = show_text(repo_root, commit, CYCLE_PATH)
    hardening_text = show_text(repo_root, commit, HARDENING_PATH)
    diff_names = git_text(
        repo_root,
        [
            "diff",
            "--name-only",
            reference,
            commit,
            "--",
            REPLAY_PATH,
            CYCLE_PATH,
            HARDENING_PATH,
        ],
    ).strip()
    census = json.loads(show_text(repo_root, commit, CENSUS_PATH))
    candidates, outer_edges, census_pin = _census_views(census, commit=commit)
    census_ancestor = False
    if len(census_pin) == 40:
        census_ancestor = is_ancestor(repo_root, census_pin, commit)
    landscape = json.loads(show_text(repo_root, commit, LANDSCAPE_PATH))
    tree_paths = [
        line
        for line in git_text(repo_root, ["ls-tree", "-r", "--name-only", commit]).splitlines()
        if line
    ]
    ghosv_paths = [path for path in tree_paths if "current_causal_graph_ghosv" in path.lower()]
    return PinnedSourcesV1(
        reference_baseline=reference,
        reference_is_ancestor=reference_ancestor,
        code_diff_empty=diff_names == "" and reference_ancestor,
        replay_defined=f"def {REPLAY_SYMBOL}(" in replay_text,
        cycle_owner_cites_replay=CYCLE_OWNER_CITATION in cycle_text,
        double_play_role_confirmed=DOUBLE_PLAY_ROLE_CITATION in hardening_text,
        census_candidates=candidates,
        census_outer_edges=outer_edges,
        census_pin=census_pin,
        census_pin_is_ancestor=census_ancestor,
        landscape_authority={
            "path": LANDSCAPE_PATH,
            "authority_effect": landscape.get("authority_effect"),
            "not_a_universe_ratification": landscape.get("not_a_universe_ratification"),
            "labels_used_as_membership": False,
        },
        historical_graphs=_historical_graphs(repo_root, commit, tree_paths),
        causal_graph_status=_causal_status(tree_paths)[0],
        causal_graph_verified=_causal_status(tree_paths)[1],
        causal_integration_blob=blob_id(repo_root, commit, CAUSAL_INTEGRATION_PATH),
        ghosv_execution_blob=blob_id(repo_root, commit, GHOSV_EXECUTION_PATH),
        current_graph_ghosv_paths=sorted(ghosv_paths),
        non_transfer_components=[
            {
                "component_id": f"owner-named:{name}",
                "classification": "UNRESOLVED_COMPONENT",
                "marker": needle,
                "outside_named_by_owner": True,
                "direct_component_edge": False,
                "proof_status": "NOT_PROVEN",
                "uncertainty": "AUTHORITY_NON_TRANSFER_IS_NOT_A_DIRECT_EDGE",
                "baseline": commit,
            }
            for name, needle in NON_TRANSFER_MARKERS
        ],
        ghv=load_pinned_ghv_helpers_v1(repo_root, commit),
        worktree_ghv_drift=_worktree_drift(repo_root, commit),
        decision_blob=blob_id(repo_root, commit, DECISION_SPEC_PATH),
        census_blob=blob_id(repo_root, commit, CENSUS_PATH),
    )
