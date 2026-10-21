"""Bounded batch execution for ten discovery worklists. AUTHORITY=NONE."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from scripts.ops.current_full_stack_semantic_explorer_v1.budget_v1 import BudgetV1
from scripts.ops.current_full_stack_semantic_explorer_v1.run_v1 import run_explorer_v1

SLICES = ("S1", "S2", "S3", "S4", "S5")
STANDARD_BUDGET = BudgetV1()


class BatchStop(RuntimeError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class WorkFile:
    path: str
    blob_sha: str


def _git_blob(repo: Path, commit: str, path: str) -> str | None:
    proc = subprocess.run(
        ["git", "rev-parse", f"{commit}:{path}"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0"},
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _within_standard(budget: BudgetV1) -> None:
    if (
        budget.max_files > STANDARD_BUDGET.max_files
        or budget.max_nodes > STANDARD_BUDGET.max_nodes
        or budget.max_edges > STANDARD_BUDGET.max_edges
        or budget.max_seconds > STANDARD_BUDGET.max_seconds
        or budget.max_depth > STANDARD_BUDGET.max_depth
    ):
        raise BatchStop("BUDGET_RAISE_REFUSED")


def validate_workfiles(
    repo: Path,
    commit: str,
    tree: str,
    files: Sequence[WorkFile],
    *,
    observed_commit: str,
    observed_tree: str,
) -> None:
    if observed_commit != commit or observed_tree != tree:
        raise BatchStop("WORKLIST_BINDING_MISMATCH")
    seen: set[str] = set()
    for item in files:
        if item.path in seen:
            raise BatchStop("DUPLICATE_WORKLIST_ENTRY")
        seen.add(item.path)
        blob = _git_blob(repo, commit, item.path)
        if blob is None:
            raise BatchStop("MISSING_WORKLIST_ENTRY")
        if blob != item.blob_sha:
            raise BatchStop("BLOB_BINDING_MISMATCH")


def plan_batches(files: Sequence[WorkFile], max_files: int) -> list[list[WorkFile]]:
    ordered = sorted(files, key=lambda item: item.path)
    width = max(1, min(max_files, STANDARD_BUDGET.max_files))
    return [ordered[index : index + width] for index in range(0, len(ordered), width)]


def _checkpoint_path(root: Path, item: WorkFile) -> Path:
    digest = hashlib.sha256(f"{item.path}\0{item.blob_sha}".encode("utf-8")).hexdigest()
    return root / "files" / f"{digest}.json"


def _refuse_false_complete(document: dict[str, Any]) -> None:
    if document["status"] != "COMPLETE":
        return
    if any(document["slice_coverage"][name] != "PASS" for name in SLICES):
        raise BatchStop("INCOMPLETE_MARKED_COMPLETE")


def _write_checkpoint(
    root: Path,
    *,
    commit: str,
    tree: str,
    agent_id: str,
    worklist_sha256: str,
    item: WorkFile,
    outcome: dict[str, Any],
    raw_ref: str,
) -> dict[str, Any]:
    document = {
        "schema": "discovery_batch_checkpoint.v1",
        "commit_sha": commit,
        "tree_sha": tree,
        "agent_id": agent_id,
        "worklist_sha256": worklist_sha256,
        "path": item.path,
        "blob_sha": item.blob_sha,
        "status": outcome["status"],
        "slice_coverage": outcome["slice_coverage"],
        "stop_reasons": list(outcome["stop_reasons"]),
        "raw_ref": raw_ref,
    }
    _refuse_false_complete(document)
    destination = _checkpoint_path(root, item)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(document, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return document


def _load_checkpoints(root: Path) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    folder = root / "files"
    if not folder.is_dir():
        return found
    for path in sorted(folder.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        found[str(document["path"])] = document
    return found


def _outcome_for(run: dict[str, Any], item: WorkFile) -> dict[str, Any]:
    for row in run["file_outcomes"]:
        if row["path"] == item.path:
            if row["blob_sha"] != item.blob_sha:
                raise BatchStop("BLOB_BINDING_MISMATCH")
            return row
    raise BatchStop("MISSING_WORKLIST_ENTRY")


def execute_worklist(
    repo: Path | str,
    commit: str,
    tree: str,
    agent_id: str,
    worklist_sha256: str,
    files: Sequence[WorkFile],
    checkpoint_dir: Path | str,
    *,
    budget: BudgetV1 | None = None,
    clock: Callable[[], float] | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    root = Path(repo)
    active = budget or BudgetV1()
    _within_standard(active)
    head = subprocess.run(
        ["git", "rev-parse", f"{commit}^{{commit}}"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0"},
    )
    tree_now = subprocess.run(
        ["git", "rev-parse", f"{commit}^{{tree}}"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0"},
    )
    if head.returncode != 0 or tree_now.returncode != 0:
        raise BatchStop("COMMIT_UNREADABLE")
    if head.stdout.strip() != commit or tree_now.stdout.strip() != tree:
        raise BatchStop("WORKLIST_BINDING_MISMATCH")
    validate_workfiles(
        root,
        commit,
        tree,
        files,
        observed_commit=commit,
        observed_tree=tree,
    )
    store = Path(checkpoint_dir)
    existing = _load_checkpoints(store)
    if resume:
        for item in files:
            saved = existing.get(item.path)
            if saved is None:
                continue
            if (
                saved["commit_sha"] != commit
                or saved["tree_sha"] != tree
                or saved["blob_sha"] != item.blob_sha
                or saved["agent_id"] != agent_id
            ):
                raise BatchStop("CHECKPOINT_BINDING_MISMATCH")
            _refuse_false_complete(saved)
    pending = [
        item
        for item in sorted(files, key=lambda row: row.path)
        if not (resume and existing.get(item.path, {}).get("status") == "COMPLETE")
    ]
    attempts: dict[str, int] = defaultdict(int)
    width = min(active.max_files, STANDARD_BUDGET.max_files)
    steps = 0
    max_steps = len(pending) * 3 + 4
    raw_dir = store / "raw"
    while pending and steps < max_steps:
        steps += 1
        batch = pending[:width]
        for item in batch:
            attempts[item.path] += 1
        run = run_explorer_v1(
            root,
            commit,
            budget=active,
            path_prefixes=tuple(item.path for item in batch),
            clock=clock,
        )
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_path = raw_dir / f"step-{steps:04d}.json"
        raw_path.write_text(json.dumps(run, sort_keys=True) + "\n", encoding="utf-8")
        raw_ref = str(raw_path)
        outcomes = [_outcome_for(run, item) for item in batch]
        if outcomes and all(row["status"] == "NOT_STARTED" for row in outcomes):
            for item, outcome in zip(batch, outcomes, strict=True):
                forced = dict(outcome)
                forced["status"] = "INCOMPLETE"
                if not forced["stop_reasons"]:
                    forced["stop_reasons"] = ["TIME_BUDGET"]
                _write_checkpoint(
                    store,
                    commit=commit,
                    tree=tree,
                    agent_id=agent_id,
                    worklist_sha256=worklist_sha256,
                    item=item,
                    outcome=forced,
                    raw_ref=raw_ref,
                )
            pending = [item for item in pending if item not in batch]
            continue
        completed = [
            item
            for item, outcome in zip(batch, outcomes, strict=True)
            if outcome["status"] == "COMPLETE"
        ]
        for item, outcome in zip(batch, outcomes, strict=True):
            if outcome["status"] != "COMPLETE":
                continue
            _write_checkpoint(
                store,
                commit=commit,
                tree=tree,
                agent_id=agent_id,
                worklist_sha256=worklist_sha256,
                item=item,
                outcome=outcome,
                raw_ref=raw_ref,
            )
        pending = [item for item in pending if item not in completed]
        incomplete = [
            item
            for item, outcome in zip(batch, outcomes, strict=True)
            if outcome["status"] == "INCOMPLETE"
        ]
        if not incomplete:
            width = min(active.max_files, STANDARD_BUDGET.max_files)
            continue
        if len(batch) == 1 or attempts[incomplete[0].path] >= 2:
            for item in incomplete:
                outcome = _outcome_for(run, item)
                if outcome["status"] == "COMPLETE":
                    continue
                forced = dict(outcome)
                forced["status"] = "INCOMPLETE"
                _write_checkpoint(
                    store,
                    commit=commit,
                    tree=tree,
                    agent_id=agent_id,
                    worklist_sha256=worklist_sha256,
                    item=item,
                    outcome=forced,
                    raw_ref=raw_ref,
                )
            pending = [item for item in pending if item not in incomplete]
            width = min(active.max_files, STANDARD_BUDGET.max_files)
            continue
        width = 1 if completed else max(1, len(batch) // 2)
    if pending and steps >= max_steps:
        raise BatchStop("LOOP_GUARD")
    saved = _load_checkpoints(store)
    return {
        "agent_id": agent_id,
        "commit_sha": commit,
        "tree_sha": tree,
        "files": [
            saved[item.path]
            for item in sorted(files, key=lambda row: row.path)
            if item.path in saved
        ],
    }


def merge_agent_results(parts: Sequence[dict[str, Any]]) -> dict[str, Any]:
    claims: dict[str, dict[str, Any]] = {}
    provenance: dict[str, list[str]] = defaultdict(list)
    duplicates: list[str] = []
    files: list[dict[str, Any]] = []
    for part in sorted(parts, key=lambda item: str(item["agent_id"])):
        agent_id = str(part["agent_id"])
        for item in part.get("files", []):
            files.append({"agent_id": agent_id, **item})
        for claim in part.get("claims", []):
            claim_id = str(claim["claim_id"])
            if claim_id in claims:
                duplicates.append(claim_id)
            else:
                claims[claim_id] = claim
            if agent_id not in provenance[claim_id]:
                provenance[claim_id].append(agent_id)
    merged_claims = []
    for claim_id in sorted(claims):
        body = dict(claims[claim_id])
        body["agent_ids"] = sorted(provenance[claim_id])
        merged_claims.append(body)
    coverage = {
        "physical": sum(1 for item in files if item.get("slice_coverage", {}).get("S1") == "PASS"),
        "semantic": sum(1 for item in files if item.get("slice_coverage", {}).get("S2") == "PASS"),
        "causal": sum(1 for item in files if item.get("slice_coverage", {}).get("S3") == "PASS"),
        "runtime_proven": sum(
            1
            for claim in merged_claims
            if claim.get("predicate") == "RUNTIME_OBSERVES" and claim.get("status") == "PROVEN"
        ),
        "runtime_unproven": sum(
            1
            for claim in merged_claims
            if claim.get("evidence_class") == "RUNTIME_OBSERVED"
            and claim.get("status") == "UNPROVEN"
        ),
    }
    open_relations = [claim for claim in merged_claims if claim.get("status") == "UNPROVEN"]
    return {
        "schema": "discovery_agent_merge.v1",
        "authority": "NONE",
        "claims": merged_claims,
        "duplicate_claim_ids": sorted(set(duplicates)),
        "files": sorted(files, key=lambda item: (item["agent_id"], item["path"])),
        "coverage": coverage,
        "open_relations": open_relations,
    }
