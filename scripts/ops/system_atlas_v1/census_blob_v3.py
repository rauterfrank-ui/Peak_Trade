"""FIND_COMPLETELY pass v3 historical blob/commit-message census.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
Dedup is exact Git blob SHA only. Name similarity is not identity.
Not disposition. Not runtime authorization.
"""

from __future__ import annotations

import ast
import hashlib
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

from scripts.ops.system_atlas_v1.constants_v1 import (
    RECONCILIATION_RELATIVE_ROOT,
    RECONCILIATION_SCHEMA_VERSION,
)

BOUND_ORIGIN_MAIN = "origin/main"
BOUND_REV_LIST_ARGS = ("--branches", "--tags", "--remotes=origin")
BOUND_REF_PREFIXES = ("refs/heads", "refs/remotes/origin", "refs/tags")
MAX_TEXT_BLOB_BYTES = 1_500_000

RELEVANT_EXTENSIONS = frozenset(
    {
        ".py",
        ".pyi",
        ".yaml",
        ".yml",
        ".toml",
        ".json",
        ".jsonl",
        ".md",
        ".rst",
        ".txt",
        ".sh",
        ".bash",
        ".zsh",
        ".cfg",
        ".ini",
        ".conf",
        ".csv",
        ".tsv",
        ".html",
        ".xml",
        ".svg",
        ".sql",
        ".mako",
        ".j2",
        ".jinja",
        ".in",
        ".service",
        ".plist",
    }
)
RELEVANT_FILENAMES = frozenset(
    {
        "makefile",
        "dockerfile",
        "containerfile",
        "manifest",
        "manifest.in",
        "license",
        "licence",
        "notice",
        "authors",
        "contributors",
        "changelog",
        "pipfile",
        "gemfile",
        ".gitignore",
        ".gitattributes",
        ".editorconfig",
        ".dockerignore",
        "pyproject.toml",
        "requirements.txt",
        "setup.py",
        "setup.cfg",
        "tox.ini",
        "pytest.ini",
        "ruff.toml",
    }
)
BINARY_EXTENSIONS = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".ico",
        ".bmp",
        ".tif",
        ".tiff",
        ".pdf",
        ".zip",
        ".gz",
        ".bz2",
        ".xz",
        ".7z",
        ".whl",
        ".egg",
        ".pyc",
        ".pyo",
        ".so",
        ".dylib",
        ".dll",
        ".a",
        ".o",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".otf",
        ".mp4",
        ".mov",
        ".avi",
        ".wav",
        ".mp3",
        ".flac",
        ".parquet",
        ".pqt",
        ".feather",
        ".bin",
        ".exe",
        ".pkl",
        ".pickle",
        ".npy",
        ".npz",
        ".h5",
        ".hdf5",
        ".db",
        ".sqlite",
        ".sqlite3",
        ".pyd",
        ".class",
        ".jar",
        ".wasm",
    }
)
VENDOR_PATH_SEGMENTS = frozenset(
    {
        "node_modules",
        ".venv",
        "vendor",
        "third_party",
        "__pycache__",
        ".tox",
        "site-packages",
    }
)
GENERATED_PATH_PREFIXES = ("docs/system_atlas/generated/",)

PYTHON_DEF_RE = re.compile(
    r"^(?:async\s+)?(?:class|def|protocol)\s+([A-Za-z_][A-Za-z0-9_]*)",
    re.MULTILINE,
)
HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
YAML_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_\-]*)\s*:", re.MULTILINE)
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{3,}")
COMPONENTISH_RE = re.compile(
    r"(?:Engine|Runtime|Runbook|Dashboard|Selector|Orchestrator|Registry|"
    r"KillSwitch|Gate|Adapter|Readmodel|ReadModel|_v[0-9]+)$"
)
COMMIT_DISCOVERY_RE = re.compile(
    r"\b(delet(?:e|ed|ion)|remov(?:e|ed)|renam(?:e|ed)|mov(?:e|ed)|"
    r"restor(?:e|ed)|replac(?:e|ed)|revert(?:ed)?|vanish(?:ed)?|"
    r"introduc(?:e|ed)|add(?:ed)?)\b",
    re.IGNORECASE,
)
NOISE_TOKENS = frozenset(
    {
        "this",
        "that",
        "with",
        "from",
        "true",
        "false",
        "none",
        "null",
        "self",
        "test",
        "tests",
        "return",
        "import",
        "class",
        "def",
        "async",
        "await",
        "pass",
        "else",
        "elif",
        "true",
        "false",
        "when",
        "then",
        "into",
        "over",
        "under",
        "after",
        "before",
        "using",
        "used",
        "also",
        "only",
        "have",
        "been",
        "will",
        "should",
        "would",
        "could",
        "must",
        "note",
        "todo",
        "fixme",
        "http",
        "https",
        "www",
        "json",
        "yaml",
        "utf8",
        "utf_8",
        "ascii",
        "linux",
        "darwin",
        "windows",
    }
)


def _git(args: list[str], *, cwd: Path, input_text: str | None = None) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True, input=input_text)


def _progress(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def schema_header() -> dict[str, Any]:
    return {
        "schema_version": RECONCILIATION_SCHEMA_VERSION,
        "bound_against_ref": BOUND_ORIGIN_MAIN,
        "atlas_authority": "NONE",
        "reconciliation_authority": "NONE",
        "census_pass_id": "FIND_COMPLETELY_PASS_V3",
        "dedup_rule": "exact_git_blob_sha_only",
        "identity_fusion_forbidden": True,
        "disposition_performed": False,
    }


def inventories_root(repo_root: Path) -> Path:
    return repo_root / RECONCILIATION_RELATIVE_ROOT / "inventories"


def bound_ref_names(*, repo_root: Path) -> list[str]:
    raw = _git(
        ["for-each-ref", "--format=%(refname)", *BOUND_REF_PREFIXES],
        cwd=repo_root,
    )
    return [ln for ln in raw.splitlines() if ln.strip()]


def extra_ref_names(*, repo_root: Path) -> list[str]:
    raw = _git(["for-each-ref", "--format=%(refname)"], cwd=repo_root)
    bound = set(bound_ref_names(repo_root=repo_root))
    return [ln for ln in raw.splitlines() if ln.strip() and ln not in bound]


def commit_shas(*, repo_root: Path, args: list[str]) -> list[str]:
    raw = _git(["rev-list", *args], cwd=repo_root)
    return [ln for ln in raw.splitlines() if ln.strip()]


def _parse_objects(text: str) -> dict[str, set[str]]:
    paths: dict[str, set[str]] = defaultdict(set)
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split(" ", 1)
        sha = parts[0]
        path = parts[1] if len(parts) > 1 else ""
        if path:
            paths[sha].add(path)
        else:
            paths.setdefault(sha, set())
    return paths


def unique_blob_index(*, repo_root: Path, rev_list_args: list[str]) -> dict[str, dict[str, Any]]:
    """Map blob SHA -> observed paths and size. Dedup by exact blob SHA."""
    raw = _git(["rev-list", "--objects", *rev_list_args], cwd=repo_root)
    obj_paths = _parse_objects(raw)
    shas = list(obj_paths)
    if not shas:
        return {}
    payload = "".join(f"{sha}\n" for sha in shas)
    checked = _git(
        ["cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
        cwd=repo_root,
        input_text=payload,
    )
    blobs: dict[str, dict[str, Any]] = {}
    for line in checked.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        sha, otype, size_s = parts[0], parts[1], parts[2]
        if otype != "blob":
            continue
        blobs[sha] = {
            "sha": sha,
            "size": int(size_s),
            "paths": sorted(obj_paths.get(sha) or []),
        }
    return blobs


def classify_path(path: str, size: int) -> str:
    lowered = path.replace("\\", "/").lower()
    parts = [p for p in lowered.split("/") if p]
    name = parts[-1] if parts else ""
    if any(seg in VENDOR_PATH_SEGMENTS for seg in parts):
        return "excluded_generated_or_vendor"
    if any(lowered.startswith(prefix) for prefix in GENERATED_PATH_PREFIXES):
        return "excluded_generated_or_vendor"
    ext = ""
    if "." in name:
        ext = "." + name.rsplit(".", 1)[-1]
    if ext in BINARY_EXTENSIONS:
        return "excluded_binary"
    if size > MAX_TEXT_BLOB_BYTES:
        return "other_excluded_oversize"
    if ext in RELEVANT_EXTENSIONS or name in RELEVANT_FILENAMES:
        return "relevant_text"
    if name.startswith("makefile") or name.startswith("dockerfile"):
        return "relevant_text"
    if "manifest" in name and ext in {"", ".sha256", ".txt", ".json", ".yaml", ".yml"}:
        return "relevant_text"
    if ext in {"", ".lock"} and size < 200_000:
        return "relevant_text_unknown_ext"
    if ext:
        return "other_excluded_unlisted_extension"
    return "relevant_text_unknown_ext"


def classify_blob(paths: list[str], size: int) -> str:
    """Classify a unique blob using all observed paths. Not name-based dedup."""
    if size > MAX_TEXT_BLOB_BYTES:
        return "other_excluded_oversize"
    if not paths:
        return "relevant_text_unknown_ext"
    classes = [classify_path(path, size) for path in paths]
    if all(klass == "excluded_generated_or_vendor" for klass in classes):
        return "excluded_generated_or_vendor"
    if all(klass == "excluded_binary" for klass in classes):
        return "excluded_binary"
    if any(klass == "relevant_text" for klass in classes):
        return "relevant_text"
    if any(klass == "relevant_text_unknown_ext" for klass in classes):
        return "relevant_text_unknown_ext"
    if any(klass == "excluded_binary" for klass in classes):
        return "excluded_binary"
    return "other_excluded_unlisted_extension"


def _looks_binary(data: bytes) -> bool:
    if not data:
        return False
    if b"\x00" in data[:8192]:
        return True
    return False


def decode_blob(data: bytes) -> tuple[str, str]:
    if _looks_binary(data):
        return "", "binary_nul"
    try:
        return data.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="replace"), "utf-8-replace"


def scan_python(content: str) -> dict[str, list[str]]:
    classes: list[str] = []
    functions: list[str] = []
    protocols: list[str] = []
    imports: list[str] = []
    try:
        tree = ast.parse(content)
        ast_ok = True
    except SyntaxError:
        ast_ok = False
        tree = None
    if ast_ok and tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(base.attr)
                if "Protocol" in bases:
                    protocols.append(node.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split(".", 1)[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module.split(".", 1)[0])
    else:
        for match in PYTHON_DEF_RE.finditer(content):
            line = content[match.start() : content.find("\n", match.start())]
            name = match.group(1)
            if "class" in line[:12]:
                classes.append(name)
            else:
                functions.append(name)
    return {
        "classes": sorted(set(classes)),
        "functions": sorted(set(functions)),
        "protocols": sorted(set(protocols)),
        "imports": sorted(set(imports)),
        "parse": "ast" if ast_ok else "regex_fallback",
    }


def scan_structured_text(content: str) -> dict[str, list[str]]:
    headings = [m.group(2).strip() for m in HEADING_RE.finditer(content)]
    keys = [m.group(1) for m in YAML_KEY_RE.finditer(content)]
    tokens = []
    for tok in TOKEN_RE.findall(content):
        if tok.lower() in NOISE_TOKENS:
            continue
        if tok.isupper() or "_" in tok or (tok[:1].isupper() and len(tok) > 4):
            tokens.append(tok)
    return {
        "headings": headings[:400],
        "keys": sorted(set(keys))[:400],
        "tokens": sorted(set(tokens)),
    }


def sha256_sorted(values: Iterable[str]) -> str:
    joined = "\n".join(sorted(values)) + "\n"
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _cat_blobs(repo_root: Path, shas: list[str]) -> dict[str, bytes]:
    if not shas:
        return {}
    payload = "".join(f"{sha}\n" for sha in shas)
    proc = subprocess.run(
        ["git", "cat-file", "--batch"],
        cwd=repo_root,
        input=payload.encode("utf-8"),
        stdout=subprocess.PIPE,
        check=True,
    )
    out = proc.stdout
    result: dict[str, bytes] = {}
    i = 0
    n = len(out)
    while i < n:
        nl = out.find(b"\n", i)
        if nl < 0:
            break
        header = out[i:nl].decode("ascii", errors="replace")
        i = nl + 1
        parts = header.split()
        if len(parts) < 3 or parts[1] == "missing":
            continue
        sha, _otype, size_s = parts[0], parts[1], parts[2]
        size = int(size_s)
        data = out[i : i + size]
        i += size
        if i < n and out[i : i + 1] == b"\n":
            i += 1
        result[sha] = data
    return result


def persist_pass_v3_baseline(*, repo_root: Path) -> dict[str, Any]:
    """Pre-run git baseline. Timestamp is navigation, not authority."""
    header = schema_header()
    origin_main_sha = _git(["rev-parse", BOUND_ORIGIN_MAIN], cwd=repo_root).strip()
    head_sha = _git(["rev-parse", "HEAD"], cwd=repo_root).strip()
    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root).strip()
    shallow = _git(["rev-parse", "--is-shallow-repository"], cwd=repo_root).strip()
    try:
        partial = _git(["rev-parse", "--is-partial-clone"], cwd=repo_root).strip()
    except subprocess.CalledProcessError:
        partial = "false"
    dirty = _git(["status", "--porcelain"], cwd=repo_root)
    extra_refs = extra_ref_names(repo_root=repo_root)
    payload = {
        **header,
        "bound_against_sha": origin_main_sha,
        "expected_origin_main_sha": "1b52df25b99a36b99eed91943c2a203ce84f1cad",
        "expected_branch": "feat/reconsolidation-census-v1",
        "expected_local_head_sha": "ff02a54a546d4ee0a1532306ed921ac71c42f823",
        "observed_origin_main_sha": origin_main_sha,
        "observed_branch": branch,
        "observed_local_head_sha": head_sha,
        "git_is_shallow": shallow == "true",
        "git_is_partial_clone": partial == "true",
        "working_tree_dirty": bool(dirty.strip()),
        "dirty_porcelain": dirty.splitlines() if dirty.strip() else [],
        "extra_local_ref_count": len(extra_refs),
        "extra_local_refs": extra_refs,
        "baseline_timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "census_timestamp_role": "NAVIGATION_NOT_AUTHORITY",
        "origin_main_sha_match": origin_main_sha == "1b52df25b99a36b99eed91943c2a203ce84f1cad",
        "branch_match": branch == "feat/reconsolidation-census-v1",
        "local_head_match": head_sha == "ff02a54a546d4ee0a1532306ed921ac71c42f823",
        "not_shallow": shallow != "true",
        "not_partial_clone": partial != "true",
        "baseline_match": (
            origin_main_sha == "1b52df25b99a36b99eed91943c2a203ce84f1cad"
            and branch == "feat/reconsolidation-census-v1"
            and head_sha == "ff02a54a546d4ee0a1532306ed921ac71c42f823"
            and shallow != "true"
            and partial != "true"
        ),
        "dirty_note": (
            "Pre-run working tree may include this pass's enumerator files. "
            "Dirty is recorded, not auto-cleaned. Unexplained SHA/branch/shallow drift is fail-closed."
        ),
    }
    out = inventories_root(repo_root)
    out.mkdir(parents=True, exist_ok=True)
    _dump(out / "pass_v3_baseline.yaml", payload)
    return payload


def src_path_prefix(path: str) -> str:
    parts = path.replace("\\", "/").split("/")
    if len(parts) >= 3 and parts[0] == "src":
        return "/".join(parts[:3])
    if len(parts) >= 2 and parts[0] == "src":
        return "/".join(parts[:2])
    return ""


def generate_pass_v3_blob_census(*, repo_root: Path) -> dict[str, Any]:
    """Enumerate unique blobs, scan relevant contents, scan commit messages."""
    baseline = persist_pass_v3_baseline(repo_root=repo_root)
    if not baseline.get("baseline_match"):
        raise SystemExit(
            "BASELINE_VALIDATION=FAIL_CLOSED "
            f"origin={baseline.get('observed_origin_main_sha')} "
            f"branch={baseline.get('observed_branch')} "
            f"head={baseline.get('observed_local_head_sha')} "
            f"dirty={baseline.get('working_tree_dirty')} "
            f"shallow={baseline.get('git_is_shallow')}"
        )
    header = schema_header()
    origin_main_sha = str(baseline["observed_origin_main_sha"])
    header["bound_against_sha"] = origin_main_sha
    out = inventories_root(repo_root)
    out.mkdir(parents=True, exist_ok=True)

    _progress("census_v3: bind git universes")
    extra_refs = extra_ref_names(repo_root=repo_root)
    commits_main = commit_shas(repo_root=repo_root, args=[BOUND_ORIGIN_MAIN])
    commits_bound = commit_shas(repo_root=repo_root, args=list(BOUND_REV_LIST_ARGS))
    commits_all = commit_shas(repo_root=repo_root, args=["--all"])
    main_set = set(commits_main)
    bound_set = set(commits_bound)
    all_set = set(commits_all)
    extra_only = sorted(all_set - bound_set)
    non_main_bound = sorted(bound_set - main_set)
    roots_main = _git(["rev-list", "--max-parents=0", BOUND_ORIGIN_MAIN], cwd=repo_root).split()
    roots_bound = _git(
        ["rev-list", "--max-parents=0", *BOUND_REV_LIST_ARGS],
        cwd=repo_root,
    ).split()

    universe = {
        **header,
        "git_is_shallow": bool(baseline.get("git_is_shallow")),
        "git_is_partial_clone": bool(baseline.get("git_is_partial_clone")),
        "universes": {
            "A_origin_main": {
                "root_refs": [BOUND_ORIGIN_MAIN],
                "rev_list_command": f"git rev-list {BOUND_ORIGIN_MAIN}",
                "reachable_commit_count": len(commits_main),
                "unique_commit_sha_count": len(main_set),
                "root_commits": roots_main,
            },
            "B_bound_search_universe": {
                "root_ref_prefixes": list(BOUND_REF_PREFIXES),
                "rev_list_command": "git rev-list --branches --tags --remotes=origin",
                "reachable_commit_count": len(commits_bound),
                "unique_commit_sha_count": len(bound_set),
                "root_commits": roots_bound,
                "note": "Explicitly NOT git rev-list --all. Extra local refs are out of this universe.",
            },
        },
        "overlap_commit_count": len(main_set & bound_set),
        "non_origin_main_reachable_commit_count": len(non_main_bound),
        "extra_local_refs_not_in_bound_universe": extra_refs,
        "extra_local_ref_count": len(extra_refs),
        "commits_only_on_extra_local_refs_count": len(extra_only),
        "commits_only_on_extra_local_refs": extra_only,
        "all_refs_commit_count_for_contrast_only": len(commits_all),
        "object_enumeration_method": "git rev-list --objects then git cat-file --batch-check type=blob; dedup exact blob SHA",
        "census_timestamp_role": "NAVIGATION_NOT_AUTHORITY",
    }
    _dump(out / "git_universe_v3.yaml", universe)

    _progress("census_v3: unique blob index origin/main")
    blobs_main = unique_blob_index(repo_root=repo_root, rev_list_args=[BOUND_ORIGIN_MAIN])
    _progress("census_v3: unique blob index bound universe")
    blobs_bound = unique_blob_index(repo_root=repo_root, rev_list_args=list(BOUND_REV_LIST_ARGS))
    main_blob_shas = set(blobs_main)
    bound_blob_shas = set(blobs_bound)
    non_main_blobs = bound_blob_shas - main_blob_shas

    class_counts: dict[str, int] = defaultdict(int)
    relevant_shas: list[str] = []
    path_relations = 0
    non_main_src_prefixes: set[str] = set()
    for sha, meta in blobs_bound.items():
        paths = list(meta["paths"] or [])
        path_relations += max(1, len(paths))
        klass = classify_blob(paths, int(meta["size"]))
        meta["class"] = klass
        meta["in_origin_main"] = sha in main_blob_shas
        class_counts[klass] += 1
        if klass.startswith("relevant_text"):
            relevant_shas.append(sha)
        if sha in non_main_blobs:
            for path in paths:
                prefix = src_path_prefix(path)
                if prefix:
                    non_main_src_prefixes.add(prefix)

    blob_digest_main = sha256_sorted(main_blob_shas)
    blob_digest_bound = sha256_sorted(bound_blob_shas)
    blob_digest_relevant = sha256_sorted(relevant_shas)

    scope = {
        **header,
        "unique_blob_count_origin_main": len(blobs_main),
        "unique_blob_count_all_bound": len(blobs_bound),
        "unique_non_main_blob_count": len(non_main_blobs),
        "blob_path_relation_count": path_relations,
        "unique_blob_count_total": len(blobs_bound),
        "unique_relevant_text_blob_count": class_counts["relevant_text"]
        + class_counts["relevant_text_unknown_ext"],
        "excluded_binary_blob_count": class_counts["excluded_binary"],
        "excluded_generated_or_vendor_blob_count": class_counts["excluded_generated_or_vendor"],
        "other_excluded_blob_count": class_counts["other_excluded_oversize"]
        + class_counts["other_excluded_unlisted_extension"],
        "class_counts": dict(class_counts),
        "exclusion_taxonomy": {
            "excluded_binary": "Extension in BINARY_EXTENSIONS (images/archives/binaries).",
            "excluded_generated_or_vendor": "Path contains vendor/generated markers.",
            "other_excluded_oversize": f"Size > {MAX_TEXT_BLOB_BYTES} bytes.",
            "other_excluded_unlisted_extension": "Non-empty unlisted extension, not relevant/binary.",
            "relevant_text": "Documented source/config/docs/test/script/manifest extensions.",
            "relevant_text_unknown_ext": "No/lock extension, UTF-8 text candidate under size cap.",
        },
        "max_text_blob_bytes": MAX_TEXT_BLOB_BYTES,
        "blob_sha_digest_origin_main": blob_digest_main,
        "blob_sha_digest_bound": blob_digest_bound,
        "blob_sha_digest_relevant": blob_digest_relevant,
        "non_main_blob_sample": [
            {
                "sha": sha,
                "paths": (blobs_bound[sha]["paths"] or [])[:3],
                "class": blobs_bound[sha].get("class"),
            }
            for sha in sorted(non_main_blobs)[:25]
        ],
        "name_based_dedup_forbidden": True,
        "first_last_observation": "NOT_COMPUTED_FOR_FULL_SET",
        "first_last_observation_reason": (
            "Per-blob first/last commit would require a full tree walk of every bound commit. "
            "Pass v3 binds blob SHA + observed path family from rev-list --objects. "
            "A 25-blob non-main sample records find-object provenance only."
        ),
        "non_main_src_path_prefix_count": len(non_main_src_prefixes),
        "non_main_src_path_prefixes": sorted(non_main_src_prefixes),
    }
    _progress("census_v3: sample find-object provenance for 25 non-main blobs")
    for row in scope["non_main_blob_sample"]:
        found = _git(
            [
                "log",
                *BOUND_REV_LIST_ARGS,
                f"--find-object={row['sha']}",
                "--format=%H",
                "-n",
                "3",
            ],
            cwd=repo_root,
        )
        row["sample_commit_shas"] = [ln for ln in found.splitlines() if ln][:3]
    _dump(out / "blob_scope_v3.yaml", scope)

    _progress(f"census_v3: scanning {len(relevant_shas)} unique relevant blobs")
    classes: dict[str, dict[str, str]] = {}
    functions_count = 0
    protocols: dict[str, dict[str, str]] = {}
    imports: set[str] = set()
    headings: dict[str, dict[str, str]] = {}
    keys: dict[str, dict[str, str]] = {}
    tokens: dict[str, dict[str, str]] = {}
    parse_fallback = 0
    binary_reclass = 0
    scanned = 0
    batch_size = 200
    for offset in range(0, len(relevant_shas), batch_size):
        batch = relevant_shas[offset : offset + batch_size]
        contents = _cat_blobs(repo_root, batch)
        for sha in batch:
            meta = blobs_bound[sha]
            data = contents.get(sha, b"")
            scanned += 1
            if _looks_binary(data):
                binary_reclass += 1
                continue
            text, _enc = decode_blob(data)
            if not text:
                continue
            path = (meta["paths"] or [""])[0]
            py_paths = [p for p in (meta["paths"] or []) if p.endswith(".py") or p.endswith(".pyi")]
            if py_paths:
                path = py_paths[0]
                py = scan_python(text)
                if py["parse"] != "ast":
                    parse_fallback += 1
                functions_count += len(py["functions"])
                for name in py["classes"]:
                    classes.setdefault(name, {"blob_sha": sha, "path": path})
                for name in py["protocols"]:
                    protocols.setdefault(name, {"blob_sha": sha, "path": path})
                imports.update(py["imports"])
            structured = scan_structured_text(text)
            for heading in structured["headings"]:
                headings.setdefault(heading, {"blob_sha": sha, "path": path})
            for key in structured["keys"]:
                keys.setdefault(key, {"blob_sha": sha, "path": path})
            for tok in structured["tokens"]:
                tokens.setdefault(tok, {"blob_sha": sha, "path": path})
        if offset and offset % 2000 == 0:
            _progress(f"census_v3: scanned {scanned}/{len(relevant_shas)} blobs")

    componentish = sorted(name for name in classes if COMPONENTISH_RE.search(name))
    symbol_doc = {
        **header,
        "method": "unique relevant blob SHA cat-file --batch; Python AST-first with regex fallback",
        "unique_relevant_blobs_scanned": scanned,
        "python_ast_fallback_count": parse_fallback,
        "reclassified_binary_after_nul_check": binary_reclass,
        "historical_class_count": len(classes),
        "historical_function_name_occurrences_sum": functions_count,
        "historical_protocol_count": len(protocols),
        "historical_import_top_module_count": len(imports),
        "historical_class_name_digest": sha256_sorted(classes),
        "componentish_class_count": len(componentish),
        "componentish_classes": [{"name": name, **classes[name]} for name in componentish[:500]],
        "historical_protocols": [
            {"name": name, **meta} for name, meta in sorted(protocols.items())
        ],
        "blob_contents_read": True,
        "raw_inventory_not_authority": True,
        "exhaustion_proven_for_unique_relevant_bound_blobs": True,
    }
    _dump(out / "historical_symbol_census_v3.yaml", symbol_doc)

    architecture_headings = [
        {"text": text, **meta}
        for text, meta in sorted(headings.items())
        if COMPONENTISH_RE.search(text.replace(" ", ""))
        or re.search(r"(Landscape|Master V2|Double Play|Peak_Trade|Runbook|Registry)", text)
    ]
    term_doc = {
        **header,
        "method": "headings/keys/tokens from unique relevant historical blobs; noise token denylist",
        "noise_filter": sorted(NOISE_TOKENS),
        "historical_heading_count": len(headings),
        "historical_key_count": len(keys),
        "historical_token_count": len(tokens),
        "historical_heading_digest": sha256_sorted(headings),
        "historical_token_digest": sha256_sorted(tokens),
        "architecture_like_headings": architecture_headings[:800],
        "componentish_tokens": [
            {"name": tok, **tokens[tok]} for tok in sorted(tokens) if COMPONENTISH_RE.search(tok)
        ][:800],
        "functional_core_literal_found": "FUNCTIONAL_CORE" in tokens
        or "FUNCTIONAL_CORE" in classes,
        "ssot_child_literal_found": "SSOT_CHILD" in tokens or "SSOT_CHILD" in classes,
        "atlas_complete_flags_ignored_for_exhaustion": True,
        "known_seeds_are_not_census_boundaries": ["Landscape", "Master V2", "Double Play"],
        "raw_inventory_not_authority": True,
        "exhaustion_proven_for_unique_relevant_bound_blob_text": True,
    }
    _dump(out / "historical_terminology_census_v3.yaml", term_doc)

    _progress("census_v3: commit messages subject+body over bound commit set")
    payload = "".join(f"{sha}\n" for sha in commits_bound)
    msg_raw = _git(
        ["log", "--no-walk", "--stdin", "--format=%H%x00%s%x00%b%x1e"],
        cwd=repo_root,
        input_text=payload,
    )
    messages = [chunk for chunk in msg_raw.split("\x1e") if chunk.strip()]
    with_body = 0
    hits: list[dict[str, Any]] = []
    named_hits: list[dict[str, Any]] = []
    named_path_re = re.compile(r"\b(?:src|docs|archive|scripts|tests)/[A-Za-z0-9_./\-]+")
    named_label_re = re.compile(r"\bPeak_Trade[_A-Za-z0-9.\-]*|\b[A-Z][A-Za-z0-9]+(?:V2|_v\d+)")
    for chunk in messages:
        parts = chunk.strip("\n").split("\x00")
        if len(parts) < 2:
            continue
        sha = parts[0].strip()
        subject = parts[1]
        body = parts[2] if len(parts) > 2 else ""
        if body.strip():
            with_body += 1
        blob_text = f"{subject}\n{body}"
        discovery = bool(COMMIT_DISCOVERY_RE.search(blob_text) or COMPONENTISH_RE.search(blob_text))
        if discovery:
            hits.append(sha)
        paths = named_path_re.findall(blob_text)
        labels = named_label_re.findall(blob_text)
        if discovery and (paths or labels or COMPONENTISH_RE.search(blob_text)):
            named_hits.append(
                {
                    "commit_sha": sha,
                    "subject": subject[:240],
                    "has_body": bool(body.strip()),
                    "observed_paths": sorted(set(paths))[:20],
                    "observed_labels": sorted(set(labels))[:20],
                    "epistemic_status": "FORENSIC_RAW_FACT",
                    "not_proof_of_component_existence": True,
                }
            )
    message_count_matches_commits = len(messages) == len(commits_bound)
    msg_digest = sha256_sorted(chunk.strip() for chunk in messages if chunk.strip())
    msg_doc = {
        **header,
        "method": (
            "git rev-list --branches --tags --remotes=origin then "
            "git log --no-walk --stdin --format=SHA,subject,body"
        ),
        "bound_commit_count": len(commits_bound),
        "commit_message_count": len(messages),
        "commit_message_count_matches_bound_commits": message_count_matches_commits,
        "commit_message_with_body_count": with_body,
        "commit_message_discovery_hit_count": len(hits),
        "named_architecture_or_path_hit_count": len(named_hits),
        "commit_message_set_digest": msg_digest,
        "discovery_hit_sha_digest": sha256_sorted(hits),
        "hits_are_navigational_not_existence_proof": True,
        "named_hits": named_hits,
        "exhaustion_proven_for_bound_commit_messages": message_count_matches_commits,
        "remaining_gap": (
            ""
            if message_count_matches_commits
            else "git log --no-walk message count != bound rev-list commit count"
        ),
    }
    _dump(out / "commit_messages_v3.yaml", msg_doc)

    summary = {
        **header,
        "reachable_commit_count_origin_main": len(commits_main),
        "reachable_commit_count_all_bound": len(commits_bound),
        "non_origin_main_reachable_commit_count": len(non_main_bound),
        "unique_blob_count_origin_main": len(blobs_main),
        "unique_blob_count_all": len(blobs_bound),
        "unique_non_main_blob_count": len(non_main_blobs),
        "blob_path_relation_count": path_relations,
        "unique_relevant_text_blob_count": scope["unique_relevant_text_blob_count"],
        "excluded_binary_blob_count": scope["excluded_binary_blob_count"],
        "excluded_generated_or_vendor_blob_count": scope["excluded_generated_or_vendor_blob_count"],
        "other_excluded_blob_count": scope["other_excluded_blob_count"],
        "historical_symbol_count": len(classes),
        "historical_terminology_token_count": len(tokens),
        "commit_message_count": len(messages),
        "commit_message_with_body_count": with_body,
        "commit_message_discovery_hit_count": len(hits),
        "new_candidates_from_commit_messages_deferred_to_persist": True,
        "blob_level_scan_performed": True,
        "blob_level_scan_scope": "unique_relevant_text_blobs_in_bound_search_universe",
        "functional_core_literal_found": "FUNCTIONAL_CORE" in tokens
        or "FUNCTIONAL_CORE" in classes,
        "ssot_child_literal_found": "SSOT_CHILD" in tokens or "SSOT_CHILD" in classes,
    }
    _dump(out / "pass_v3_summary.yaml", summary)
    _progress("census_v3: inventories written")
    return summary


def _dump(path: Path, payload: dict[str, Any]) -> None:
    rendered = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=120)
    path.write_text(
        "# ATLAS_AUTHORITY=NONE\n# RECONCILIATION_AUTHORITY=NONE\n" + rendered,
        encoding="utf-8",
    )


if __name__ == "__main__":
    generate_pass_v3_blob_census(repo_root=Path(__file__).resolve().parents[3])
