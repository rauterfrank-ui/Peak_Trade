#!/usr/bin/env python3
"""Fail-closed verifier / materializer for evidence/market_dashboard_deletion.

Canonical definitions:

1) Changed-file inventory
   Source: ``git diff --name-status -M <BASE> <HEAD_TREEISH>``
   TOTAL_CHANGED_FILES = number of name-status lines
   A/M/D/R counted by status prefix (R* = one rename entry)

2) final_intended_files.txt
   One destination path per name-status entry (rename → new path only)
   INTENDED_ENTRY_COUNT == TOTAL_CHANGED_FILES

3) final_diff_sha256.txt
   SHA-256 of:
   LC_ALL=C git -c core.quotepath=false diff --binary --full-index --no-ext-diff \\
     <BASE> <HEAD_TREEISH> -- . ':(exclude)evidence/market_dashboard_deletion/**'
   Evidence under that pathspec is excluded (no self-referential digest).
   Commit/tree identity is recorded separately in final_head_sha.txt.

4) manifest.sha256
   sha256sum listing of all files under evidence/market_dashboard_deletion/
   except ``manifest.sha256`` and ``manifest_file.sha256`` (no circular self-entry).

5) manifest_file.sha256
   Single-line digest of ``manifest.sha256`` bytes only.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

EVIDENCE_DIR = Path("evidence/market_dashboard_deletion")
DEFAULT_BASE = "987e020378d1767fbd6fb1f0914d475f9a485f51"
DIFF_PATHSPEC = (".", ":(exclude)evidence/market_dashboard_deletion/**")
MANIFEST_EXCLUDES = frozenset(
    {
        "manifest.sha256",
        "manifest_file.sha256",
        "final_head_sha.txt",  # commit identity; excluded to avoid closeout hash loops
    }
)
COUNTER_KEYS = (
    "TOTAL_CHANGED_FILES",
    "ADDED_FILES",
    "MODIFIED_FILES",
    "DELETED_FILES",
    "RENAMED_FILES",
    "INTENDED_ENTRY_COUNT",
    "FINAL_DIFF_SHA256",
    "FINAL_BASE_SHA",
)


class EvidenceVerifyError(RuntimeError):
    pass


def _run(cmd: list[str], *, env: dict[str, str] | None = None) -> bytes:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    proc = subprocess.run(cmd, check=False, capture_output=True, env=merged)
    if proc.returncode != 0:
        raise EvidenceVerifyError(
            f"command_failed rc={proc.returncode} cmd={cmd!r} stderr={proc.stderr.decode()[:800]}"
        )
    return proc.stdout


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_counters(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        out[key.strip()] = val.strip()
    return out


def _rev_parse(ref: str) -> str:
    return _run(["git", "rev-parse", ref]).decode().strip()


def _tree_of(ref: str) -> str:
    # Commits resolve via ^{tree}; bare tree ids return themselves.
    try:
        return _run(["git", "rev-parse", f"{ref}^{{tree}}"]).decode().strip()
    except EvidenceVerifyError:
        return _rev_parse(ref)


def _name_status(base: str, head: str) -> list[tuple[str, list[str]]]:
    raw = _run(
        ["git", "diff", "--name-status", "-M", base, head],
        env={"LC_ALL": "C"},
    ).decode()
    rows: list[tuple[str, list[str]]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        rows.append((parts[0], parts[1:]))
    return rows


def _counts(rows: list[tuple[str, list[str]]]) -> dict[str, int]:
    added = modified = deleted = renamed = 0
    for status, _paths in rows:
        if status.startswith("A"):
            added += 1
        elif status.startswith("M"):
            modified += 1
        elif status.startswith("D"):
            deleted += 1
        elif status.startswith("R"):
            renamed += 1
        else:
            raise EvidenceVerifyError(f"unsupported_status={status!r}")
    return {
        "TOTAL_CHANGED_FILES": len(rows),
        "ADDED_FILES": added,
        "MODIFIED_FILES": modified,
        "DELETED_FILES": deleted,
        "RENAMED_FILES": renamed,
    }


def _intended_paths(rows: list[tuple[str, list[str]]]) -> list[str]:
    out: list[str] = []
    for status, paths in rows:
        if status.startswith("R"):
            if len(paths) != 2:
                raise EvidenceVerifyError(f"rename_path_arity status={status} paths={paths}")
            out.append(paths[1])
        else:
            if len(paths) != 1:
                raise EvidenceVerifyError(f"path_arity status={status} paths={paths}")
            out.append(paths[0])
    return out


def _scoped_diff_digest(base: str, head: str) -> str:
    data = _run(
        [
            "git",
            "-c",
            "core.quotepath=false",
            "diff",
            "--binary",
            "--full-index",
            "--no-ext-diff",
            base,
            head,
            "--",
            *DIFF_PATHSPEC,
        ],
        env={"LC_ALL": "C"},
    )
    return _sha256_bytes(data)


def _expected_manifest_lines(evidence_root: Path) -> list[str]:
    files = sorted(
        p for p in evidence_root.rglob("*") if p.is_file() and p.name not in MANIFEST_EXCLUDES
    )
    lines: list[str] = []
    for path in files:
        rel = path.relative_to(evidence_root).as_posix()
        lines.append(f"{_sha256_file(path)}  ./{rel}")
    return lines


def verify(*, base: str, head: str, evidence_root: Path) -> None:
    if not evidence_root.is_dir():
        raise EvidenceVerifyError(f"missing_evidence_dir={evidence_root}")

    required = [
        "final_audit_counters.txt",
        "final_intended_files.txt",
        "final_diff_sha256.txt",
        "manifest.sha256",
        "manifest_file.sha256",
        "diff_hash_scope.txt",
        "final_base_sha.txt",
        "name_status_inventory.txt",
        "rename_inventory.txt",
    ]
    for name in required:
        if not (evidence_root / name).is_file():
            raise EvidenceVerifyError(f"missing_required_file={evidence_root / name}")

    base_full = _rev_parse(base)
    head_full = _rev_parse(head)
    recorded_base = (evidence_root / "final_base_sha.txt").read_text(encoding="utf-8").strip()
    if recorded_base != base_full:
        raise EvidenceVerifyError(f"base_mismatch recorded={recorded_base} expected={base_full}")

    # Optional documentary head stamp (excluded from manifest; never fail-closed).
    head_stamp = evidence_root / "final_head_sha.txt"
    if head_stamp.is_file():
        recorded_head = head_stamp.read_text(encoding="utf-8").strip()
        print(f"FINAL_HEAD_STAMP={recorded_head}")
        print(f"VERIFY_HEAD={head_full}")

    rows = _name_status(base_full, head_full)
    counts = _counts(rows)
    intended = _intended_paths(rows)
    scoped = _scoped_diff_digest(base_full, head_full)

    ns_text = _run(
        ["git", "diff", "--name-status", "-M", base_full, head_full],
        env={"LC_ALL": "C"},
    ).decode()
    if (evidence_root / "name_status_inventory.txt").read_text(encoding="utf-8") != ns_text:
        raise EvidenceVerifyError("name_status_inventory_mismatch")

    intended_recorded = [
        ln
        for ln in (evidence_root / "final_intended_files.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if ln.strip()
    ]
    if intended_recorded != intended:
        raise EvidenceVerifyError(
            f"final_intended_files_mismatch recorded={len(intended_recorded)} actual={len(intended)}"
        )

    recorded_diff = (evidence_root / "final_diff_sha256.txt").read_text(encoding="utf-8").strip()
    if recorded_diff != scoped:
        raise EvidenceVerifyError(
            f"final_diff_sha256_mismatch recorded={recorded_diff} actual={scoped}"
        )

    counters = _parse_counters(
        (evidence_root / "final_audit_counters.txt").read_text(encoding="utf-8")
    )
    for key in COUNTER_KEYS:
        if key not in counters:
            raise EvidenceVerifyError(f"missing_counter={key}")
    for key, val in counts.items():
        if counters[key] != str(val):
            raise EvidenceVerifyError(
                f"counter_mismatch {key} recorded={counters[key]} actual={val}"
            )
    if counters["INTENDED_ENTRY_COUNT"] != str(len(intended)):
        raise EvidenceVerifyError("intended_entry_count_mismatch")
    if counters["FINAL_DIFF_SHA256"] != scoped:
        raise EvidenceVerifyError("counter_final_diff_sha256_mismatch")
    if counters["FINAL_BASE_SHA"] != base_full:
        raise EvidenceVerifyError("counter_base_mismatch")
    # FINAL_HEAD_SHA may be absent from counters (identity lives in final_head_sha.txt)

    expected_manifest = _expected_manifest_lines(evidence_root)
    recorded_manifest = [
        ln
        for ln in (evidence_root / "manifest.sha256").read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    if any(line.endswith(" ./manifest.sha256") for line in recorded_manifest):
        raise EvidenceVerifyError("manifest_self_reference")
    if any(line.endswith(" ./manifest_file.sha256") for line in recorded_manifest):
        raise EvidenceVerifyError("manifest_file_listed_in_manifest")
    if recorded_manifest != expected_manifest:
        rec_set = {ln.split("  ", 1)[1] for ln in recorded_manifest if "  " in ln}
        exp_set = {ln.split("  ", 1)[1] for ln in expected_manifest if "  " in ln}
        raise EvidenceVerifyError(
            "manifest_content_mismatch "
            f"extra={sorted(rec_set - exp_set)[:8]} missing={sorted(exp_set - rec_set)[:8]}"
        )

    manifest_path = evidence_root / "manifest.sha256"
    manifest_digest = _sha256_file(manifest_path)
    mf_line = (evidence_root / "manifest_file.sha256").read_text(encoding="utf-8").strip()
    expected_mf = f"{manifest_digest}  ./manifest.sha256"
    if mf_line != expected_mf:
        raise EvidenceVerifyError(
            f"manifest_file_sha_mismatch recorded={mf_line!r} expected={expected_mf!r}"
        )

    scope_text = (evidence_root / "diff_hash_scope.txt").read_text(encoding="utf-8")
    if ":(exclude)evidence/market_dashboard_deletion/**" not in scope_text:
        raise EvidenceVerifyError("diff_hash_scope_missing_exclude")
    if "--binary" not in scope_text or "--full-index" not in scope_text:
        raise EvidenceVerifyError("diff_hash_scope_missing_flags")

    print("EVIDENCE_VERIFY_PASS=true")
    print(f"TOTAL_CHANGED_FILES={counts['TOTAL_CHANGED_FILES']}")
    print(f"FINAL_DIFF_SHA256={scoped}")
    print(f"MANIFEST_FILE_SHA256={manifest_digest}")
    print(f"FINAL_HEAD_SHA={head_full}")
    print("MANIFEST_SELF_REFERENCE=false")


def materialize(
    *,
    base: str,
    head: str,
    evidence_root: Path,
    record_head: str | None = None,
) -> None:
    """Materialize evidence.

    ``head`` is the tree-ish used for name-status / scoped diff.
    ``record_head`` is the identity written into evidence (commit SHA).
    When preparing an index fixed-point before commit, pass
    ``record_head='PENDING_COMMIT'`` so embedded identity bytes stay stable.
    """
    evidence_root.mkdir(parents=True, exist_ok=True)
    forensic = evidence_root / "forensic_audit_pr_5290"
    forensic.mkdir(parents=True, exist_ok=True)

    base_full = _rev_parse(base)
    head_tree = _rev_parse(head)
    head_record = record_head if record_head is not None else head_tree
    if head_record != "PENDING_COMMIT":
        head_record = _rev_parse(head_record)

    rows = _name_status(base_full, head_tree)
    counts = _counts(rows)
    intended = _intended_paths(rows)
    scoped = _scoped_diff_digest(base_full, head_tree)
    ns_text = _run(
        ["git", "diff", "--name-status", "-M", base_full, head_tree],
        env={"LC_ALL": "C"},
    ).decode()

    (evidence_root / "final_base_sha.txt").write_text(base_full + "\n", encoding="utf-8")
    (evidence_root / "final_head_sha.txt").write_text(head_record + "\n", encoding="utf-8")
    (evidence_root / "final_diff_sha256.txt").write_text(scoped + "\n", encoding="utf-8")
    (evidence_root / "final_intended_files.txt").write_text(
        "\n".join(intended) + ("\n" if intended else ""), encoding="utf-8"
    )
    (evidence_root / "name_status_inventory.txt").write_text(ns_text, encoding="utf-8")

    rename_lines = [
        f"{status}\t{paths[0]}\t{paths[1]}" for status, paths in rows if status.startswith("R")
    ]
    (evidence_root / "rename_inventory.txt").write_text(
        "\n".join(rename_lines) + ("\n" if rename_lines else ""), encoding="utf-8"
    )

    scope_head_token = head_record if head_record == "PENDING_COMMIT" else head_record
    (evidence_root / "diff_hash_scope.txt").write_text(
        "\n".join(
            [
                "FINAL_DIFF_HASH_ALGORITHM=sha256",
                (
                    "FINAL_DIFF_HASH_SCOPE=LC_ALL=C git -c core.quotepath=false diff "
                    f"--binary --full-index --no-ext-diff {base_full} HEAD "
                    "-- . ':(exclude)evidence/market_dashboard_deletion/**'"
                ),
                "FINAL_DIFF_HASH_HEAD_RESOLVED=see_final_head_sha_txt",
                (
                    "RENAME_COUNTING_MODEL=git diff --name-status -M; one R* line = one "
                    "changed entry; TOTAL_CHANGED_FILES=name-status lines; "
                    "final_intended_files uses destination path only"
                ),
                (
                    "SELF_REFERENCE_AVOIDANCE=evidence/market_dashboard_deletion/** excluded "
                    "from FINAL_DIFF_SHA256; tree/commit identity in FINAL_HEAD_SHA; "
                    "manifest.sha256 excludes itself and manifest_file.sha256; "
                    "manifest_file.sha256 hashes manifest.sha256 bytes only"
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )

    counters = "\n".join(
        [
            f"TOTAL_CHANGED_FILES={counts['TOTAL_CHANGED_FILES']}",
            f"ADDED_FILES={counts['ADDED_FILES']}",
            f"MODIFIED_FILES={counts['MODIFIED_FILES']}",
            f"DELETED_FILES={counts['DELETED_FILES']}",
            f"RENAMED_FILES={counts['RENAMED_FILES']}",
            f"INTENDED_ENTRY_COUNT={len(intended)}",
            f"FINAL_DIFF_SHA256={scoped}",
            f"FINAL_BASE_SHA={base_full}",
            "MANIFEST_SELF_REFERENCE=false",
            "RENAME_COUNTING_MODEL=name_status_entry_equals_one_changed_file",
            "DIFF_HASH_EXCLUDES=evidence/market_dashboard_deletion/**",
            "MANIFEST_FILE_SHA256_PATH=evidence/market_dashboard_deletion/manifest_file.sha256",
            "FINAL_HEAD_SHA_PATH=evidence/market_dashboard_deletion/final_head_sha.txt",
        ]
    )
    (evidence_root / "final_audit_counters.txt").write_text(counters + "\n", encoding="utf-8")

    (forensic / "REPRODUCTION.md").write_text(
        f"""# Market Dashboard deletion — forensic reproduction (PR #5290)

## Identity

- BASE=`{base_full}`
- HEAD=`git rev-parse HEAD` (see also `../final_head_sha.txt`, excluded from manifest)

## Counts

```bash
LC_ALL=C git diff --name-status -M {base_full} HEAD | wc -l
LC_ALL=C git diff --name-status -M {base_full} HEAD | cut -f1 | sort | uniq -c
```

## Final diff digest (excludes evidence/market_dashboard_deletion/**)

```bash
LC_ALL=C git -c core.quotepath=false diff --binary --full-index --no-ext-diff \\
  {base_full} HEAD -- . ':(exclude)evidence/market_dashboard_deletion/**' \\
  | shasum -a 256
```

## Manifest digest

```bash
shasum -a 256 evidence/market_dashboard_deletion/manifest.sha256
# must match evidence/market_dashboard_deletion/manifest_file.sha256
```

## Verify

```bash
uv run python scripts/ops/verify_market_dashboard_deletion_evidence_v1.py \\
  --base {base_full} --head HEAD
```
""",
        encoding="utf-8",
    )

    # Drop old digest files then rebuild listing → digest
    for name in ("manifest.sha256", "manifest_file.sha256"):
        path = evidence_root / name
        if path.exists():
            path.unlink()

    manifest_lines = _expected_manifest_lines(evidence_root)
    manifest_path = evidence_root / "manifest.sha256"
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    digest = _sha256_file(manifest_path)
    (evidence_root / "manifest_file.sha256").write_text(
        f"{digest}  ./manifest.sha256\n", encoding="utf-8"
    )

    print("EVIDENCE_MATERIALIZE_DONE=true")
    print(f"FINAL_HEAD_SHA={head_record}")
    print(f"DIFF_AGAINST_TREEISH={head_tree}")
    print(f"FINAL_DIFF_SHA256={scoped}")
    print(f"TOTAL_CHANGED_FILES={counts['TOTAL_CHANGED_FILES']}")
    print(f"MANIFEST_FILE_SHA256={digest}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--head", default="HEAD", help="Tree-ish for diff/name-status")
    parser.add_argument(
        "--record-head",
        default=None,
        help="Identity written into evidence (use PENDING_COMMIT for pre-commit fixed point)",
    )
    parser.add_argument("--evidence-dir", default=str(EVIDENCE_DIR))
    parser.add_argument("--materialize", action="store_true")
    args = parser.parse_args()
    evidence_root = Path(args.evidence_dir)
    try:
        if args.materialize:
            materialize(
                base=args.base,
                head=args.head,
                evidence_root=evidence_root,
                record_head=args.record_head,
            )
        else:
            verify(base=args.base, head=args.head, evidence_root=evidence_root)
    except EvidenceVerifyError as exc:
        print("EVIDENCE_VERIFY_PASS=false", file=sys.stderr)
        print(f"ERROR={exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
