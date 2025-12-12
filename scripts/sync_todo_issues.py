#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


# -------------------------
# shell helpers
# -------------------------
def run(cmd: List[str], check: bool = False) -> Tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise SystemExit(f"❌ Command failed: {' '.join(cmd)}\n{p.stderr}")
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def git_root() -> Path:
    rc, out, _ = run(["git", "rev-parse", "--show-toplevel"], check=True)
    return Path(out)


# -------------------------
# TODO parsing (same semantics as board)
# -------------------------
ID_RE = re.compile(r"\[([A-Za-z0-9_\-]+)\]")
HINT_PATH_RE = re.compile(r"hint_path:\s*\"([^\"]+)\"|hint_path:\s*([^\s]+)")
TAG_RE = re.compile(r"#([A-Za-z0-9_\-]+)")

@dataclass(frozen=True)
class TodoItem:
    id: str
    status: str   # TODO | DOING | DONE
    title: str
    section: str
    hint_path: Optional[str]
    tags: List[str]
    source_line: str


def detect_source_md(root: Path, override: Optional[str]) -> Path:
    if override:
        p = Path(override)
        return p if p.is_absolute() else (root / p)

    preferred = root / "docs" / "Peak_Trade_Research_Strategy_TODO_2025-12-07.md"
    if preferred.exists():
        return preferred

    docs_dir = root / "docs"
    if docs_dir.exists():
        cands = sorted(docs_dir.rglob("*TODO*.md"))
        if cands:
            return cands[0]

    raise SystemExit("❌ Keine TODO-Quelle gefunden. Erwartet z.B. docs/*TODO*.md")


def parse_todos(md_text: str) -> List[TodoItem]:
    items: List[TodoItem] = []
    section = "Allgemein"
    auto_id = 1

    for raw in md_text.splitlines():
        line = raw.rstrip()

        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            section = m.group(2).strip()
            continue

        m = re.match(r"^\s*[-*]\s+\[( |x|X)\]\s+(.*)$", line)
        if not m:
            continue

        checked = m.group(1).lower() == "x"
        rest = m.group(2).strip()

        status = "DONE" if checked else "TODO"
        if not checked and re.search(r"\b(doing|wip|in\s*arbeit)\b", rest, re.IGNORECASE):
            status = "DOING"

        mid = ID_RE.search(rest)
        if mid:
            item_id = mid.group(1)
            rest = ID_RE.sub("", rest).strip()
        else:
            item_id = f"T{auto_id:04d}"
            auto_id += 1

        hp = None
        mhp = HINT_PATH_RE.search(rest)
        if mhp:
            hp = (mhp.group(1) or mhp.group(2) or "").strip().strip('"')

        tags = sorted({t.lower() for t in TAG_RE.findall(rest)})

        items.append(TodoItem(
            id=item_id,
            status=status,
            title=rest,
            section=section,
            hint_path=hp,
            tags=tags,
            source_line=line,
        ))

    return items


# -------------------------
# GitHub issue sync via gh
# -------------------------
def gh_repo_arg(repo: Optional[str]) -> List[str]:
    return ["--repo", repo] if repo else []


def issue_exists(item_id: str, repo: Optional[str]) -> Optional[str]:
    # Search for "[ID]" in open issues first; if not found, search all.
    cmd = ["gh", "issue", "list", "--search", f"[{item_id}]", "--state", "all", "--json", "url,title"] + gh_repo_arg(repo)
    rc, out, err = run(cmd)
    if rc != 0:
        raise SystemExit(f"❌ gh issue list failed:\n{err}")
    if not out:
        return None
    issues = json.loads(out)
    if not issues:
        return None
    return issues[0]["url"]


def ensure_label(label: str, repo: Optional[str], dry_run: bool) -> None:
    # Best-effort: create label if missing. If it fails, continue.
    cmd_list = ["gh", "label", "list", "--search", label, "--json", "name"] + gh_repo_arg(repo)
    rc, out, _ = run(cmd_list)
    if rc == 0 and out:
        existing = json.loads(out)
        if any((x.get("name") or "").lower() == label.lower() for x in existing):
            return

    if dry_run:
        print(f"  🏷️  (dry-run) would create label: {label}")
        return

    cmd_create = ["gh", "label", "create", label, "--description", "Synced from Peak_Trade TODO board"] + gh_repo_arg(repo)
    rc, _, err = run(cmd_create)
    if rc != 0:
        # ignore (often already exists / permission)
        return


def build_title(it: TodoItem) -> str:
    return f"[{it.id}] {it.title}".strip()


def build_body(it: TodoItem, source_md: Path) -> str:
    tags = " ".join(f"#{t}" for t in it.tags) if it.tags else "(keine)"
    hp = it.hint_path or "(kein hint_path)"
    return "\n".join([
        "Automatisch synchronisiert aus dem Peak_Trade TODO Board.",
        "",
        f"- **Status:** {it.status}",
        f"- **Section:** {it.section}",
        f"- **Tags:** {tags}",
        f"- **hint_path:** `{hp}`",
        "",
        f"- **Quelle:** `{source_md}`",
        "",
        "Hinweis: Bitte den TODO-Eintrag (ID + Text) als Source of Truth behandeln.",
    ])


def create_issue(it: TodoItem, source_md: Path, repo: Optional[str], base_labels: List[str], dry_run: bool) -> Optional[str]:
    title = build_title(it)
    body = build_body(it, source_md)

    labels = list(base_labels)
    # status labels
    if it.status == "DOING":
        labels.append("doing")
    elif it.status == "DONE":
        labels.append("done")
    else:
        labels.append("todo")

    # tag labels
    labels.extend([f"tag:{t}" for t in it.tags])

    # ensure labels exist (best-effort)
    for lab in sorted(set(labels)):
        ensure_label(lab, repo, dry_run)

    if dry_run:
        print(f"  ➕ (dry-run) would create: {title}")
        return None

    cmd = ["gh", "issue", "create", "--title", title, "--body", body]
    for lab in sorted(set(labels)):
        cmd += ["--label", lab]
    cmd += gh_repo_arg(repo)

    rc, out, err = run(cmd)
    if rc != 0:
        raise SystemExit(f"❌ gh issue create failed:\n{err}")
    return out.strip() if out else None


def update_issue(issue_url: str, it: TodoItem, source_md: Path, repo: Optional[str], base_labels: List[str], dry_run: bool) -> None:
    title = build_title(it)
    body = build_body(it, source_md)

    labels = list(base_labels)
    if it.status == "DOING":
        labels.append("doing")
    elif it.status == "DONE":
        labels.append("done")
    else:
        labels.append("todo")
    labels.extend([f"tag:{t}" for t in it.tags])

    for lab in sorted(set(labels)):
        ensure_label(lab, repo, dry_run)

    if dry_run:
        print(f"  ✏️  (dry-run) would update: {issue_url} -> {title}")
        return

    # gh issue edit supports --add-label; removing old labels is optional.
    cmd = ["gh", "issue", "edit", issue_url, "--title", title, "--body", body]
    for lab in sorted(set(labels)):
        cmd += ["--add-label", lab]
    cmd += gh_repo_arg(repo)

    rc, _, err = run(cmd)
    if rc != 0:
        raise SystemExit(f"❌ gh issue edit failed:\n{err}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync Peak_Trade TODO items to GitHub Issues (via gh CLI).")
    ap.add_argument("--source-md", default=None, help="TODO markdown path (default: auto-detect in docs/).")
    ap.add_argument("--repo", default=None, help="Override repo (OWNER/REPO). Default: current origin.")
    ap.add_argument("--dry-run", action="store_true", help="Do not create/update issues.")
    ap.add_argument("--include-done", action="store_true", help="Also process DONE items (default: skip DONE).")
    ap.add_argument("--update-existing", action="store_true", help="Update existing issue title/body/labels.")
    ap.add_argument("--label", action="append", default=[], help="Base label(s) to apply, e.g. --label peak_trade")
    args = ap.parse_args()

    root = git_root()
    source = detect_source_md(root, args.source_md)
    md = source.read_text(encoding="utf-8", errors="replace")
    items = parse_todos(md)

    # default: only TODO + DOING
    if not args.include_done:
        items = [it for it in items if it.status in ("TODO", "DOING")]

    if not items:
        print("ℹ️  Keine passenden TODO Items gefunden.")
        return 0

    # Quick gh auth sanity
    rc, _, err = run(["gh", "auth", "status"])
    if rc != 0:
        raise SystemExit(f"❌ gh auth status failed. Bitte 'gh auth login' ausführen.\n{err}")

    print(f"📄 Quelle: {source}")
    print(f"🧩 Items:  {len(items)}")
    print(f"🧷 Repo:   {args.repo or '(origin)'}")
    print(f"🧪 Dry:    {args.dry_run}")
    print(f"🛠️  Update existing: {args.update_existing}")
    print("")

    created = 0
    skipped = 0
    updated = 0

    for it in items:
        print(f"- [{it.status}] {it.id} {it.title}")
        url = issue_exists(it.id, args.repo)
        if url:
            if args.update_existing:
                update_issue(url, it, source, args.repo, args.label, args.dry_run)
                updated += 1
                print(f"  ✅ Updated: {url}")
            else:
                skipped += 1
                print(f"  ⏭️  Skipped (exists): {url}")
            continue

        new_url = create_issue(it, source, args.repo, args.label, args.dry_run)
        created += 1
        if new_url:
            print(f"  ✅ Created: {new_url}")

    print("")
    print(f"📌 Summary: created={created}, updated={updated}, skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
