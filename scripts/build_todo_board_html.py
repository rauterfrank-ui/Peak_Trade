#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


# -------------------------
# Git helpers (robust)
# -------------------------
def _run_git(args: List[str]) -> Tuple[int, str]:
    try:
        p = subprocess.run(["git", *args], capture_output=True, text=True)
        out = (p.stdout or "").strip()
        return p.returncode, out
    except Exception:
        return 1, ""


def detect_repo_root() -> Optional[Path]:
    rc, out = _run_git(["rev-parse", "--show-toplevel"])
    if rc == 0 and out:
        return Path(out)
    return None


def detect_origin_url() -> Optional[str]:
    rc, out = _run_git(["remote", "get-url", "origin"])
    if rc == 0 and out:
        return out
    return None


def origin_to_repo_web(origin: str) -> Optional[str]:
    """
    Converts origin formats to web base, e.g.
      - https://github.com/OWNER/REPO.git -> https://github.com/OWNER/REPO
      - git@github.com:OWNER/REPO.git    -> https://github.com/OWNER/REPO
      - ssh://git@github.com/OWNER/REPO.git -> https://github.com/OWNER/REPO
    Also works for GitHub Enterprise domains.
    """
    origin = origin.strip()

    # HTTPS
    m = re.match(r"^(https?://[^/]+/[^/]+/[^/]+?)(\.git)?$", origin)
    if m:
        return m.group(1)

    # SCP-like SSH: git@host:owner/repo(.git)
    m = re.match(r"^git@([^:]+):(.+?)(\.git)?$", origin)
    if m:
        host = m.group(1)
        path = m.group(2)
        return f"https://{host}/{path}"

    # ssh://git@host/owner/repo(.git)
    m = re.match(r"^ssh://git@([^/]+)/(.+?)(\.git)?$", origin)
    if m:
        host = m.group(1)
        path = m.group(2)
        return f"https://{host}/{path}"

    return None


def detect_default_branch(fallback: str = "main") -> str:
    # Best: refs/remotes/origin/HEAD -> origin/main
    rc, out = _run_git(["symbolic-ref", "-q", "refs/remotes/origin/HEAD"])
    if rc == 0 and out:
        # out: refs/remotes/origin/main
        parts = out.split("/")
        if parts:
            return parts[-1]
    return fallback


# -------------------------
# TODO parsing
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


def detect_source_md(repo_root: Path) -> Path:
    preferred = repo_root / "docs" / "Peak_Trade_Research_Strategy_TODO_2025-12-07.md"
    if preferred.exists():
        return preferred

    # fallback: find first TODO-ish markdown in docs
    docs_dir = repo_root / "docs"
    if docs_dir.exists():
        candidates = sorted(docs_dir.rglob("*TODO*.md"))
        if candidates:
            return candidates[0]

    raise SystemExit("❌ Keine TODO-Quelle gefunden. Erwartet z.B. docs/*TODO*.md")


def parse_todos(md_text: str) -> List[TodoItem]:
    items: List[TodoItem] = []
    section = "Allgemein"
    auto_id = 1

    for raw in md_text.splitlines():
        line = raw.rstrip()

        # headings as sections
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            section = m.group(2).strip()
            continue

        # checkbox tasks
        m = re.match(r"^\s*[-*]\s+\[( |x|X)\]\s+(.*)$", line)
        if not m:
            continue

        checked = m.group(1).lower() == "x"
        rest = m.group(2).strip()

        # status override keywords
        # (simple + practical)
        status = "DONE" if checked else "TODO"
        if not checked:
            if re.search(r"\b(doing|in\s*arbeit|wip)\b", rest, re.IGNORECASE):
                status = "DOING"

        # stable ID if present like [PT-123]
        mid = ID_RE.search(rest)
        if mid:
            item_id = mid.group(1)
            # remove id token from title text
            rest = ID_RE.sub("", rest).strip()
        else:
            item_id = f"T{auto_id:04d}"
            auto_id += 1

        # hint_path if present
        hp = None
        mhp = HINT_PATH_RE.search(rest)
        if mhp:
            hp = (mhp.group(1) or mhp.group(2) or "").strip().strip('"')
        # tags: #ops #docs
        tags = sorted({t.lower() for t in TAG_RE.findall(rest)})

        title = rest
        items.append(TodoItem(
            id=item_id,
            status=status,
            title=title,
            section=section,
            hint_path=hp,
            tags=tags
        ))

    return items


# -------------------------
# HTML rendering
# -------------------------
def github_link(repo_web: Optional[str], branch: str, hint_path: Optional[str]) -> Optional[str]:
    if not repo_web:
        return None
    # ✅ Fallback: ohne hint_path auf Repo-Root (tree)
    if not hint_path:
        return f"{repo_web}/tree/{branch}"

    p = hint_path.strip().lstrip("/")
    if not p:
        return f"{repo_web}/tree/{branch}"

    # heuristic: dir -> tree, file -> blob
    is_dir = p.endswith("/") or (not os.path.splitext(p)[1])
    mode = "tree" if is_dir else "blob"
    return f"{repo_web}/{mode}/{branch}/{p.rstrip('/')}"


def render_html(items: List[TodoItem], source_md: Path, repo_web: Optional[str], branch: str) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    src_rel = str(source_md).replace("\\", "/")

    # group by status
    cols = [("TODO", "Offen"), ("DOING", "In Arbeit"), ("DONE", "Erledigt")]

    # precompute cards
    cards = []
    for it in items:
        gh = github_link(repo_web, branch, it.hint_path)
        cards.append({
            "id": it.id,
            "status": it.status,
            "title": it.title,
            "section": it.section,
            "hint_path": it.hint_path,
            "tags": it.tags,
            "github": gh,
        })

    cards_json = json.dumps(cards, ensure_ascii=False)

    def esc(s: str) -> str:
        return html.escape(s, quote=True)

    repo_line = f"Repo: {esc(repo_web)} (Branch: {esc(branch)})" if repo_web else "Repo: (nicht erkannt – GitHub Buttons deaktiviert)"

    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Peak_Trade – TODO Board</title>
  <style>
    :root {{
      --bg: #0b0f14;
      --card: #111827;
      --muted: #9ca3af;
      --text: #e5e7eb;
      --border: rgba(255,255,255,0.08);
      --shadow: 0 10px 30px rgba(0,0,0,0.35);
      --radius: 14px;
    }}
    body {{
      margin: 0; padding: 0;
      background: var(--bg);
      color: var(--text);
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
    }}
    .wrap {{ max-width: 1280px; margin: 0 auto; padding: 18px; }}
    .top {{
      display: flex; flex-wrap: wrap; gap: 12px; align-items: center; justify-content: space-between;
      border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px;
      background: rgba(255,255,255,0.03);
      box-shadow: var(--shadow);
    }}
    .title {{ font-size: 18px; font-weight: 700; letter-spacing: 0.2px; }}
    .meta {{ font-size: 12px; color: var(--muted); line-height: 1.45; }}
    .search {{
      display: flex; gap: 8px; align-items: center;
    }}
    input {{
      width: 340px; max-width: 70vw;
      padding: 10px 12px; border-radius: 12px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.04);
      color: var(--text);
      outline: none;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
      margin-top: 14px;
    }}
    @media (max-width: 980px) {{
      .grid {{ grid-template-columns: 1fr; }}
      input {{ width: 100%; }}
    }}
    .col {{
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: rgba(255,255,255,0.02);
      box-shadow: var(--shadow);
      overflow: hidden;
      min-height: 240px;
    }}
    .colhead {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--border);
      display: flex; align-items: baseline; justify-content: space-between;
      gap: 10px;
    }}
    .colname {{ font-weight: 700; }}
    .count {{ font-size: 12px; color: var(--muted); }}
    .list {{ padding: 10px; display: flex; flex-direction: column; gap: 10px; }}
    .card {{
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 10px 10px 10px 12px;
      background: rgba(255,255,255,0.03);
    }}
    .row {{
      display: flex; align-items: flex-start; justify-content: space-between; gap: 10px;
    }}
    .id {{
      font-size: 11px; color: var(--muted);
      border: 1px solid var(--border); border-radius: 999px; padding: 2px 8px;
      flex: 0 0 auto;
    }}
    .txt {{
      font-size: 13px; line-height: 1.35;
      margin: 6px 0 4px 0;
      white-space: pre-wrap;
      word-break: break-word;
    }}
    .sub {{
      font-size: 11px; color: var(--muted);
      display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
    }}
    .tag {{
      font-size: 11px; padding: 2px 8px; border-radius: 999px;
      border: 1px solid var(--border); color: var(--muted);
    }}
    .btn {{
      display: inline-flex; gap: 6px; align-items: center;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 6px 10px;
      text-decoration: none;
      color: var(--text);
      background: rgba(255,255,255,0.04);
      font-size: 12px;
      flex: 0 0 auto;
    }}
    .btn[aria-disabled="true"] {{
      opacity: .45;
      pointer-events: none;
    }}
    .foot {{
      margin-top: 14px;
      font-size: 12px;
      color: var(--muted);
      padding: 12px 4px 0 4px;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="top">
      <div>
        <div class="title">Peak_Trade – TODO Board</div>
        <div class="meta">
          Quelle: {esc(src_rel)}<br/>
          Generiert: {esc(now)}<br/>
          {repo_line}
        </div>
      </div>
      <div class="search">
        <input id="q" placeholder="Suche (Text, ID, Tag, Section, Pfad) …" />
      </div>
    </div>

    <div class="grid" id="grid"></div>

    <div class="foot">
      Hinweis: GitHub-Buttons verlinken auf <code>hint_path</code> (falls angegeben) oder auf das Repo-Root.
      Beispiel: <code>hint_path: "docs/ops/"</code> → tree/main/docs/ops/ | ohne hint_path → tree/main/
    </div>
  </div>

<script>
const CARDS = {cards_json};

const COLS = [
  {{ key: "TODO",  title: "Offen" }},
  {{ key: "DOING", title: "In Arbeit" }},
  {{ key: "DONE",  title: "Erledigt" }},
];

function norm(s) {{
  return (s || "").toString().toLowerCase();
}}

function matches(card, q) {{
  if (!q) return true;
  const hay = [
    card.id, card.title, card.section,
    (card.hint_path || ""),
    (card.tags || []).join(" "),
    (card.github || "")
  ].map(norm).join(" | ");
  return hay.includes(q);
}}

function render(q) {{
  const grid = document.getElementById("grid");
  grid.innerHTML = "";

  COLS.forEach(col => {{
    const colEl = document.createElement("div");
    colEl.className = "col";

    const head = document.createElement("div");
    head.className = "colhead";
    const name = document.createElement("div");
    name.className = "colname";
    name.textContent = col.title;

    const list = document.createElement("div");
    list.className = "list";

    const filtered = CARDS.filter(c => c.status === col.key && matches(c, q));
    const cnt = document.createElement("div");
    cnt.className = "count";
    cnt.textContent = `${{filtered.length}} Items`;

    head.appendChild(name);
    head.appendChild(cnt);

    filtered.forEach(c => {{
      const card = document.createElement("div");
      card.className = "card";

      const row = document.createElement("div");
      row.className = "row";

      const left = document.createElement("div");
      left.style.flex = "1 1 auto";

      const id = document.createElement("div");
      id.className = "id";
      id.textContent = c.id;

      const title = document.createElement("div");
      title.className = "txt";
      title.textContent = c.title;

      const sub = document.createElement("div");
      sub.className = "sub";

      const sec = document.createElement("span");
      sec.textContent = `Section: ${{c.section}}`;
      sub.appendChild(sec);

      if (c.hint_path) {{
        const hp = document.createElement("span");
        hp.textContent = `Pfad: ${{c.hint_path}}`;
        sub.appendChild(hp);
      }}

      (c.tags || []).forEach(t => {{
        const tag = document.createElement("span");
        tag.className = "tag";
        tag.textContent = `#${{t}}`;
        sub.appendChild(tag);
      }});

      left.appendChild(title);
      left.appendChild(sub);

      const btn = document.createElement("a");
      btn.className = "btn";
      btn.textContent = "🌐 GitHub";
      if (c.github) {{
        btn.href = c.github;
        btn.target = "_blank";
        btn.rel = "noopener noreferrer";
      }} else {{
        btn.setAttribute("aria-disabled", "true");
        btn.href = "#";
        btn.title = "Kein hint_path oder Repo nicht erkannt";
      }}

      row.appendChild(id);
      row.appendChild(left);
      row.appendChild(btn);

      card.appendChild(row);
      list.appendChild(card);
    }});

    colEl.appendChild(head);
    colEl.appendChild(list);
    grid.appendChild(colEl);
  }});
}}

const qEl = document.getElementById("q");
qEl.addEventListener("input", () => render(norm(qEl.value)));

render("");
</script>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate Peak_Trade TODO Board HTML (DE).")
    ap.add_argument("--source-md", default=None, help="Source TODO markdown file.")
    ap.add_argument("--out-html", default="docs/00_overview/PEAK_TRADE_TODO_BOARD.html", help="Output HTML path.")
    ap.add_argument("--out-readme", default="docs/00_overview/README_TODO_BOARD.md", help="Output README path.")
    ap.add_argument("--repo-web", default=None, help="Override repo web URL (https://.../OWNER/REPO).")
    ap.add_argument("--branch", default=None, help="Override branch name for links (default: origin/HEAD).")
    args = ap.parse_args()

    repo_root = detect_repo_root()
    if not repo_root:
        print("⚠️  Kein Git Repo erkannt. GitHub Buttons werden deaktiviert.")
        repo_root = Path.cwd()

    source = Path(args.source_md) if args.source_md else detect_source_md(repo_root)
    if not source.exists():
        raise SystemExit(f"❌ Source not found: {source}")

    md = source.read_text(encoding="utf-8", errors="replace")
    items = parse_todos(md)

    origin = detect_origin_url() if repo_root else None
    repo_web = args.repo_web or (origin_to_repo_web(origin) if origin else None)
    branch = args.branch or detect_default_branch("main")

    out_html = repo_root / args.out_html if repo_root else Path(args.out_html)
    out_html.parent.mkdir(parents=True, exist_ok=True)

    html_doc = render_html(items, source, repo_web, branch)
    out_html.write_text(html_doc, encoding="utf-8")

    out_readme = repo_root / args.out_readme if repo_root else Path(args.out_readme)
    out_readme.parent.mkdir(parents=True, exist_ok=True)
    out_readme.write_text(f"""# Peak_Trade – TODO Board

Dieses TODO Board wird automatisch aus einer Markdown-TODO-Datei generiert.

## Generieren

```bash
python3 scripts/build_todo_board_html.py
```

## Öffnen

```bash
open docs/00_overview/PEAK_TRADE_TODO_BOARD.html
```

## Features

- **3-Spalten Kanban**: TODO / DOING / DONE
- **Auto-IDs**: Wenn keine explizite `[ID]` in der Zeile → automatische T0001, T0002, …
- **GitHub-Links**: Bei `hint_path: "..."` wird ein Button zu GitHub generiert
- **Tags**: `#ops`, `#docs`, etc. werden erkannt und angezeigt
- **Suche**: Echtzeit-Filter über Text, ID, Tags, Sections, Pfade
- **Dark Theme**: Modern und responsive

## Syntax-Beispiele

```markdown
## Phase 1: Strategie-Forschung

- [ ] Armstrong-Strategie finalisieren [PT-001] hint_path: "src/strategies/armstrong/" #research #prio
- [ ] Backtesting durchführen (doing) hint_path: "tests/backtest/" #testing
- [x] Initial Prototype hint_path: "docs/prototypes/"
```

Status-Keywords:
- `(doing)`, `(wip)`, `(in arbeit)` → Status DOING
- `[x]` → Status DONE
- Sonst → Status TODO

Generiert: {dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
""", encoding="utf-8")

    print(f"✅ Generated: {out_html}")
    print(f"✅ README:    {out_readme}")
    print(f"ℹ️  Items:     {len(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
