"""FIND_COMPLETELY census pass v2 inventory helpers.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
Repository-internal search only. Not disposition. Not runtime authorization.

Exhaustion claims in persisted YAML must be reproducible by these helpers.
Dedup is exact Git object/tree SHA only. Name similarity is not identity.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from scripts.ops.system_atlas_v1.constants_v1 import (
    RECONCILIATION_RELATIVE_ROOT,
    RECONCILIATION_SCHEMA_VERSION,
)

BOUND_ORIGIN_MAIN = "origin/main"
PEAKTRADEREPO_ADD_COMMIT = "cf2253aa60ffdbfd77356e33e611cd85ea53b849"
PEAKTRADEREPO_TREE_PATH = "archive/PeakTradeRepo"
RELEVANT_PREFIXES = (
    "src/",
    "docs/",
    "tests/",
    "scripts/",
    "evidence/",
    "forensics/",
    "forensic/",
    "archive/",
    "config/",
    "templates/",
    "static/",
    "schemas/",
    "governance/",
)
PYTHON_DEF_RE = re.compile(r"^(?:async\s+)?(?:class|def|protocol)\s+([A-Za-z_][A-Za-z0-9_]*)")
HEADING_RE = re.compile(r"^#{1,3}\s+(.+)$")
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{3,}")


def _git(args: list[str], *, cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True)


def origin_main_tree_sha(*, repo_root: Path) -> str:
    return _git(["rev-parse", f"{BOUND_ORIGIN_MAIN}^{{tree}}"], cwd=repo_root).strip()


def reachable_commit_count(*, repo_root: Path) -> int:
    return len([ln for ln in _git(["rev-list", "--all"], cwd=repo_root).splitlines() if ln.strip()])


def collect_ref_inventory(*, repo_root: Path) -> list[dict[str, str]]:
    """Machine-readable ref inventory: local branches, origin remotes, tags."""
    rows: list[dict[str, str]] = []
    raw = _git(
        [
            "for-each-ref",
            "--format=%(objecttype)\t%(objectname)\t%(*objectname)\t%(refname)",
            "refs/heads",
            "refs/remotes/origin",
            "refs/tags",
        ],
        cwd=repo_root,
    )
    commits: list[tuple[str, str, str]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        otype = parts[0]
        oid = parts[1]
        peeled = parts[2] if len(parts) > 2 else ""
        ref = parts[3] if len(parts) > 3 else ""
        if otype == "commit":
            commit = oid
        elif otype == "tag" and peeled:
            commit = peeled
        else:
            try:
                commit = _git(["rev-parse", f"{oid}^{{commit}}"], cwd=repo_root).strip()
            except subprocess.CalledProcessError:
                continue
        group = (
            "local"
            if ref.startswith("refs/heads/")
            else ("origin" if ref.startswith("refs/remotes/origin/") else "tag")
        )
        commits.append((group, ref, commit))
    if not commits:
        return rows
    payload = "".join(f"{commit}^{{tree}}\n" for _, _, commit in commits)
    proc = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objectname)"],
        cwd=repo_root,
        input=payload,
        text=True,
        check=True,
        capture_output=True,
    )
    trees = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    if len(trees) != len(commits):
        raise RuntimeError(f"TREE_BATCH_MISMATCH:{len(trees)}!={len(commits)}")
    for (group, ref, commit), tree in zip(commits, trees, strict=True):
        rows.append(
            {
                "group": group,
                "ref": ref,
                "commit_sha": commit,
                "tree_sha": tree,
            }
        )
    return rows


def unique_trees_by_group(inventory: list[dict[str, str]]) -> dict[str, dict[str, list[str]]]:
    grouped: dict[str, dict[str, list[str]]] = {
        "local": defaultdict(list),
        "origin": defaultdict(list),
        "tag": defaultdict(list),
    }
    for row in inventory:
        grouped[row["group"]][row["tree_sha"]].append(row["ref"])
    return {k: dict(v) for k, v in grouped.items()}


def union_unique_tree_shas(inventory: list[dict[str, str]]) -> set[str]:
    return {row["tree_sha"] for row in inventory}


def _relevant(path: str) -> bool:
    return any(path == p[:-1] or path.startswith(p) for p in RELEVANT_PREFIXES)


def path_family(path: str, *, depth: int = 3) -> str:
    parts = [p for p in path.split("/") if p]
    return "/".join(parts[:depth]) if parts else path


def list_tree_paths(*, repo_root: Path, tree_sha: str, prefix: str) -> list[str]:
    try:
        raw = _git(
            ["ls-tree", "-r", "--name-only", f"{tree_sha}:{prefix.rstrip('/')}"], cwd=repo_root
        )
    except subprocess.CalledProcessError:
        return []
    return [f"{prefix.rstrip('/')}/{ln}" if prefix else ln for ln in raw.splitlines() if ln.strip()]


def list_tree_children(*, repo_root: Path, treeish: str) -> list[str]:
    try:
        raw = _git(["ls-tree", "--name-only", treeish], cwd=repo_root)
    except subprocess.CalledProcessError:
        return []
    return [ln for ln in raw.splitlines() if ln.strip()]


def origin_main_relevant_paths(*, repo_root: Path) -> list[str]:
    tree = origin_main_tree_sha(repo_root=repo_root)
    found: list[str] = []
    for prefix in RELEVANT_PREFIXES:
        found.extend(list_tree_paths(repo_root=repo_root, tree_sha=tree, prefix=prefix[:-1]))
    return sorted(set(found))


def diff_tree_added_paths(*, repo_root: Path, baseline_tree: str, other_tree: str) -> list[str]:
    if baseline_tree == other_tree:
        return []
    raw = _git(
        ["diff-tree", "-r", "--diff-filter=A", "--name-only", baseline_tree, other_tree],
        cwd=repo_root,
    )
    return [ln for ln in raw.splitlines() if ln.strip() and _relevant(ln)]


def walk_unique_tree_deltas(
    *,
    repo_root: Path,
    unique_trees: set[str],
    baseline_tree: str,
) -> dict[str, Any]:
    """Walk every unique tip tree vs origin/main. Dedup by exact tree SHA."""
    added_by_path: dict[str, list[str]] = defaultdict(list)
    trees_with_relevant_adds = 0
    walked = 0
    for tree in sorted(unique_trees):
        walked += 1
        added = diff_tree_added_paths(
            repo_root=repo_root, baseline_tree=baseline_tree, other_tree=tree
        )
        if added:
            trees_with_relevant_adds += 1
            for path in added:
                if tree not in added_by_path[path]:
                    added_by_path[path].append(tree)
    families: dict[str, int] = defaultdict(int)
    for path in added_by_path:
        families[path_family(path)] += 1
    return {
        "unique_trees_walked": walked,
        "trees_with_relevant_adds_vs_origin_main": trees_with_relevant_adds,
        "unique_added_relevant_path_count": len(added_by_path),
        "added_path_families": dict(sorted(families.items(), key=lambda kv: (-kv[1], kv[0]))),
        "added_paths": sorted(added_by_path),
        "added_path_tree_shas": {k: v for k, v in sorted(added_by_path.items())},
    }


def deleted_paths(*, repo_root: Path, refs: str) -> list[str]:
    raw = _git(
        ["log", refs, "--diff-filter=D", "--name-only", "--pretty=format:"],
        cwd=repo_root,
    )
    return sorted({ln for ln in raw.splitlines() if ln.strip()})


def rename_pairs(*, repo_root: Path) -> list[dict[str, str]]:
    raw = _git(
        ["log", "--all", "--diff-filter=R", "--name-status", "--pretty=format:"],
        cwd=repo_root,
    )
    pairs: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for line in raw.splitlines():
        if not line.startswith("R"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        src, dst = parts[1], parts[2]
        key = (src, dst)
        if key in seen:
            continue
        seen.add(key)
        pairs.append(
            {"from": src, "to": dst, "family_from": path_family(src), "family_to": path_family(dst)}
        )
    return pairs


def reachable_object_paths(*, repo_root: Path) -> list[str]:
    raw = _git(["rev-list", "--objects", "--all"], cwd=repo_root)
    paths: set[str] = set()
    for line in raw.splitlines():
        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue
        path = parts[1].strip()
        if path:
            paths.add(path)
    return sorted(paths)


def peaktraderepo_files(*, repo_root: Path) -> dict[str, Any]:
    treeish = f"{PEAKTRADEREPO_ADD_COMMIT}:{PEAKTRADEREPO_TREE_PATH}"
    files = [
        ln
        for ln in _git(["ls-tree", "-r", "--name-only", treeish], cwd=repo_root).splitlines()
        if ln
    ]
    tree_sha = _git(["rev-parse", treeish], cwd=repo_root).strip()
    return {
        "bound_commit": PEAKTRADEREPO_ADD_COMMIT,
        "tree_path": PEAKTRADEREPO_TREE_PATH,
        "tree_sha": tree_sha,
        "file_count": len(files),
        "files": files,
    }


def corpus_listing(*, repo_root: Path, treeish_prefix: str) -> list[str]:
    return list_tree_children(repo_root=repo_root, treeish=f"{BOUND_ORIGIN_MAIN}:{treeish_prefix}")


def list_matching_paths(*, repo_root: Path, needle: str) -> list[str]:
    raw = _git(["ls-tree", "-r", "--name-only", BOUND_ORIGIN_MAIN], cwd=repo_root)
    needle_l = needle.lower()
    return [ln for ln in raw.splitlines() if needle_l in ln.lower()]


def families_from_paths(paths: list[str], *, prefix: str, depth: int) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for path in paths:
        if path == prefix.rstrip("/") or path.startswith(prefix):
            counts[path_family(path, depth=depth)] += 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def inventories_root(repo_root: Path) -> Path:
    return repo_root / RECONCILIATION_RELATIVE_ROOT / "inventories"


def schema_header() -> dict[str, Any]:
    return {
        "schema_version": RECONCILIATION_SCHEMA_VERSION,
        "bound_against_ref": BOUND_ORIGIN_MAIN,
        "atlas_authority": "NONE",
        "reconciliation_authority": "NONE",
        "census_pass_id": "FIND_COMPLETELY_PASS_V2",
        "dedup_rule": "exact_git_object_or_tree_sha_only",
        "identity_fusion_forbidden": True,
        "disposition_performed": False,
    }


def _git_grep(args: list[str], *, cwd: Path) -> str:
    proc = subprocess.run(["git", "grep", *args], cwd=cwd, text=True, capture_output=True)
    if proc.returncode not in (0, 1):
        raise subprocess.CalledProcessError(
            proc.returncode, ["git", "grep", *args], proc.stdout, proc.stderr
        )
    return proc.stdout


def current_python_symbols(*, repo_root: Path) -> dict[str, Any]:
    raw = _git_grep(
        [
            "-h",
            "-E",
            r"^(async[[:space:]]+)?(class|def)[[:space:]]+",
            BOUND_ORIGIN_MAIN,
            "--",
            "*.py",
        ],
        cwd=repo_root,
    )
    classes: set[str] = set()
    functions: set[str] = set()
    for line in raw.splitlines():
        match = PYTHON_DEF_RE.match(line.strip())
        if not match:
            continue
        name = match.group(1)
        if line.lstrip().startswith("class"):
            classes.add(name)
        else:
            functions.add(name)
    imports_raw = _git_grep(
        ["-h", "-E", r"^(from|import)[[:space:]]+", BOUND_ORIGIN_MAIN, "--", "*.py"],
        cwd=repo_root,
    )
    modules: set[str] = set()
    for line in imports_raw.splitlines():
        stripped = line.strip()
        if stripped.startswith("from "):
            rest = stripped[5:].split(" import", 1)[0].strip()
            if rest and not rest.startswith("."):
                modules.add(rest.split(".", 1)[0])
        elif stripped.startswith("import "):
            rest = stripped[7:].split(",", 1)[0].strip().split(" as ", 1)[0].strip()
            if rest:
                modules.add(rest.split(".", 1)[0])
    return {
        "class_count": len(classes),
        "function_count": len(functions),
        "imported_top_module_count": len(modules),
        "classes": sorted(classes),
        "functions": sorted(functions),
        "imported_top_modules": sorted(modules),
    }


def current_heading_tokens(*, repo_root: Path) -> list[str]:
    raw = _git_grep(
        ["-h", "-E", r"^#{1,3}[[:space:]]+", BOUND_ORIGIN_MAIN, "--", "*.md"],
        cwd=repo_root,
    )
    tokens: set[str] = set()
    for line in raw.splitlines():
        match = HEADING_RE.match(line.strip())
        if not match:
            continue
        heading = match.group(1)
        for tok in TOKEN_RE.findall(heading):
            if tok.isupper() or "_" in tok or tok[:1].isupper():
                tokens.add(tok)
    return sorted(tokens)


def _dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=120)
    path.write_text(
        "# ATLAS_AUTHORITY=NONE\n# RECONCILIATION_AUTHORITY=NONE\n" + text, encoding="utf-8"
    )


def _progress(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def generate_census_pass_v2_inventories(*, repo_root: Path) -> dict[str, Any]:
    """Build reproducible FIND_COMPLETELY pass v2 inventories. No disposition."""
    header = schema_header()
    origin_main_sha = _git(["rev-parse", BOUND_ORIGIN_MAIN], cwd=repo_root).strip()
    header["bound_against_sha"] = origin_main_sha
    out = inventories_root(repo_root)

    _progress("census_v2: ref inventory")
    inventory = collect_ref_inventory(repo_root=repo_root)
    grouped = unique_trees_by_group(inventory)
    union_trees = union_unique_tree_shas(inventory)
    baseline_tree = origin_main_tree_sha(repo_root=repo_root)
    local_refs = [r for r in inventory if r["group"] == "local"]
    origin_refs = [r for r in inventory if r["group"] == "origin"]
    tag_refs = [r for r in inventory if r["group"] == "tag"]

    ref_doc = {
        **header,
        "local_branch_count": len(local_refs),
        "origin_remote_branch_count": len(origin_refs),
        "tag_count": len(tag_refs),
        "unique_local_branch_tree_count": len(grouped["local"]),
        "unique_origin_branch_tree_count": len(grouped["origin"]),
        "unique_tag_tree_count": len(grouped["tag"]),
        "union_unique_tip_tree_count": len(union_trees),
        "origin_main_tree_sha": baseline_tree,
        "refs": inventory,
    }
    _dump(out / "ref_inventory.yaml", ref_doc)

    unique_doc = {
        **header,
        "origin_main_tree_sha": baseline_tree,
        "groups": {
            group: [
                {
                    "tree_sha": tree,
                    "ref_count": len(refs),
                    "is_origin_main_tree": tree == baseline_tree,
                    "refs": sorted(refs),
                }
                for tree, refs in sorted(trees.items(), key=lambda kv: (-len(kv[1]), kv[0]))
            ]
            for group, trees in grouped.items()
        },
    }
    _dump(out / "unique_trees.yaml", unique_doc)

    _progress(f"census_v2: walking {len(union_trees)} unique tip trees vs origin/main")
    deltas = walk_unique_tree_deltas(
        repo_root=repo_root,
        unique_trees=union_trees,
        baseline_tree=baseline_tree,
    )
    src_added = [p for p in deltas["added_paths"] if p.startswith("src/")]
    tree_doc = {
        **header,
        "method": "git diff-tree -r --diff-filter=A vs origin/main tree; exact tree SHA dedup",
        "unique_trees_walked": deltas["unique_trees_walked"],
        "trees_with_relevant_adds_vs_origin_main": deltas[
            "trees_with_relevant_adds_vs_origin_main"
        ],
        "unique_added_relevant_path_count": deltas["unique_added_relevant_path_count"],
        "added_path_family_count": len(deltas["added_path_families"]),
        "added_src_path_count": len(src_added),
        "added_path_families": deltas["added_path_families"],
        "added_src_paths": src_added,
        "added_relevant_paths": deltas["added_paths"],
        "exhaustion_proven_for_tip_tree_relevant_delta": True,
        "remaining_gap": "Tip-tree delta is not blob-level history of non-tip commits.",
    }
    _dump(out / "tree_content_census.yaml", tree_doc)

    _progress("census_v2: historical deleted/rename paths")
    deleted_main = deleted_paths(repo_root=repo_root, refs=BOUND_ORIGIN_MAIN)
    deleted_all = deleted_paths(repo_root=repo_root, refs="--all")
    renames = rename_pairs(repo_root=repo_root)
    hist_doc = {
        **header,
        "method": "git log --diff-filter=D/R --name-only/--name-status",
        "deleted_path_count_origin_main": len(deleted_main),
        "deleted_path_count_all_refs": len(deleted_all),
        "rename_pair_count": len(renames),
        "deleted_src_families": families_from_paths(deleted_all, prefix="src/", depth=3),
        "deleted_docs_families": families_from_paths(deleted_all, prefix="docs/", depth=3),
        "deleted_tests_families": families_from_paths(deleted_all, prefix="tests/", depth=3),
        "deleted_scripts_families": families_from_paths(deleted_all, prefix="scripts/", depth=3),
        "deleted_src_paths": [p for p in deleted_all if p.startswith("src/")],
        "rename_pairs": renames,
        "exhaustion_proven_for_named_deleted_and_renamed_paths": True,
        "remaining_gap": "Merge-only path changes and blob contents are not covered by name-status.",
    }
    _dump(out / "historical_path_families.yaml", hist_doc)

    _progress("census_v2: reachable object paths (not blob contents)")
    object_paths = reachable_object_paths(repo_root=repo_root)
    relevant_objects = [p for p in object_paths if _relevant(p)]
    py_objects = [p for p in object_paths if p.endswith(".py")]
    reachable_doc = {
        **header,
        "method": "git rev-list --objects --all (path inventory; blob contents not read)",
        "reachable_object_path_count": len(object_paths),
        "relevant_object_path_count": len(relevant_objects),
        "python_object_path_count": len(py_objects),
        "src_families": families_from_paths(object_paths, prefix="src/", depth=3),
        "docs_families": families_from_paths(object_paths, prefix="docs/", depth=2),
        "blob_contents_read": False,
        "exhaustion_proven_for_reachable_path_names": True,
        "remaining_gap": "Object path names are not blob-level symbol/terminology contents.",
    }
    _dump(out / "reachable_object_paths.yaml", reachable_doc)

    _progress("census_v2: PeakTradeRepo inner archive")
    inner = {**header, **peaktraderepo_files(repo_root=repo_root)}
    inner["exhaustion_proven_for_inner_archive_file_inventory"] = True
    inner["remaining_gap"] = (
        "File inventory is complete; inner file contents were not semantically understood."
    )
    _dump(out / "inner_archive_peaktraderepo.yaml", inner)

    _progress("census_v2: corpus enumeration")
    evidence_ops = corpus_listing(repo_root=repo_root, treeish_prefix="evidence/ops")
    evidence_ops_file_counts = {}
    for pack in evidence_ops:
        files = list_tree_paths(
            repo_root=repo_root, tree_sha=baseline_tree, prefix=f"evidence/ops/{pack}"
        )
        evidence_ops_file_counts[pack] = len(files)
    manifests = list_matching_paths(repo_root=repo_root, needle="MANIFEST")
    atlas_yaml = [
        p
        for p in _git(
            ["ls-tree", "-r", "--name-only", BOUND_ORIGIN_MAIN, "--", "docs/system_atlas"],
            cwd=repo_root,
        ).splitlines()
        if p.endswith((".yaml", ".yml"))
    ]
    corpus_doc = {
        **header,
        "method": "git ls-tree on origin/main corpus prefixes; evidence/ops packs counted file-by-file",
        "current_src_packages": corpus_listing(repo_root=repo_root, treeish_prefix="src"),
        "current_docs_top": corpus_listing(repo_root=repo_root, treeish_prefix="docs"),
        "current_tests_top": corpus_listing(repo_root=repo_root, treeish_prefix="tests"),
        "current_scripts_top": corpus_listing(repo_root=repo_root, treeish_prefix="scripts"),
        "evidence_top": corpus_listing(repo_root=repo_root, treeish_prefix="evidence"),
        "evidence_ops_pack_count": len(evidence_ops),
        "evidence_ops_packs": evidence_ops,
        "evidence_ops_file_counts": evidence_ops_file_counts,
        "evidence_ops_file_count_total": sum(evidence_ops_file_counts.values()),
        "forensics_top": corpus_listing(repo_root=repo_root, treeish_prefix="forensics"),
        "forensic_top": corpus_listing(repo_root=repo_root, treeish_prefix="forensic"),
        "docs_forensics_top": corpus_listing(repo_root=repo_root, treeish_prefix="docs/forensics"),
        "docs_forensic_top": corpus_listing(repo_root=repo_root, treeish_prefix="docs/forensic"),
        "manifest_path_count": len(manifests),
        "manifest_paths": manifests,
        "atlas_yaml_count": len(atlas_yaml),
        "atlas_yaml_paths": atlas_yaml,
        "file_counts_origin_main": {
            prefix[:-1]: len(
                list_tree_paths(repo_root=repo_root, tree_sha=baseline_tree, prefix=prefix[:-1])
            )
            for prefix in RELEVANT_PREFIXES
        },
    }
    _dump(out / "corpus_enumeration.yaml", corpus_doc)

    _progress("census_v2: import/symbol census (current tree + path-derived history)")
    symbols = current_python_symbols(repo_root=repo_root)
    hist_py_modules = sorted(
        {
            path_family(p, depth=3)
            for p in deleted_all + object_paths
            if p.endswith(".py") and p.startswith("src/")
        }
    )
    symbol_doc = {
        **header,
        "method": "git grep class/def/import on origin/main *.py; historical module names from path inventory",
        "current_class_count": symbols["class_count"],
        "current_function_count": symbols["function_count"],
        "current_imported_top_module_count": symbols["imported_top_module_count"],
        "historical_src_python_family_count": len(hist_py_modules),
        "historical_src_python_families": hist_py_modules,
        "current_classes": symbols["classes"],
        "current_imported_top_modules": symbols["imported_top_modules"],
        "current_functions_omitted": True,
        "current_functions_omitted_reason": "Function-name list is large; counts bound. Names remain searchable via git grep.",
        "blob_level_historical_symbol_scan_performed": False,
        "exhaustion_proven": False,
        "remaining_gap": "Symbols only inside historical non-tip blobs were not parsed.",
    }
    _dump(out / "import_symbol_census.yaml", symbol_doc)

    _progress("census_v2: terminology census")
    headings = current_heading_tokens(repo_root=repo_root)
    path_tokens: set[str] = set()
    for path in object_paths:
        for part in path.split("/"):
            stem = part.rsplit(".", 1)[0]
            for tok in TOKEN_RE.findall(stem):
                if "_" in tok or (tok.isupper() and len(tok) > 3):
                    path_tokens.add(tok)
    term_doc = {
        **header,
        "method": "origin/main markdown H1-H3 tokens plus reachable path-name tokens; Atlas terms are navigation only",
        "current_heading_token_count": len(headings),
        "reachable_path_token_count": len(path_tokens),
        "current_heading_tokens": headings,
        "reachable_path_tokens": sorted(path_tokens),
        "atlas_historical_terminology_cited_as_navigation_only": [
            "docs/system_atlas/census/historical_terminology.yaml"
        ],
        "atlas_complete_flags_ignored_for_exhaustion": True,
        "exhaustion_proven": False,
        "remaining_gap": "Heading/token census of historical blob contents beyond current tree and path names was not performed.",
    }
    _dump(out / "terminology_census.yaml", term_doc)

    summary = {
        **header,
        "local_branch_count": len(local_refs),
        "unique_local_branch_tree_count": len(grouped["local"]),
        "origin_remote_branch_count": len(origin_refs),
        "unique_origin_branch_tree_count": len(grouped["origin"]),
        "tag_count": len(tag_refs),
        "unique_tag_tree_count": len(grouped["tag"]),
        "union_unique_tip_tree_count": len(union_trees),
        "tree_content_census_unique_added_path_count": deltas["unique_added_relevant_path_count"],
        "historical_deleted_path_count_all_refs": len(deleted_all),
        "historical_path_family_count": len(hist_doc["deleted_src_families"])
        + len(hist_doc["deleted_docs_families"]),
        "reachable_object_path_count": len(object_paths),
        "import_symbol_class_count": symbols["class_count"],
        "terminology_heading_token_count": len(headings),
        "inner_archive_file_count": inner["file_count"],
        "blob_level_scan_performed": False,
    }
    _dump(out / "summary.yaml", summary)
    _progress("census_v2: inventories written")
    return summary


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[3]
    generate_census_pass_v2_inventories(repo_root=repo)
