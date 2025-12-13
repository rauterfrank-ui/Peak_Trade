#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import shlex
import subprocess
import sys
import unicodedata
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


# --- ZERO-DIFF WRITE GUARD (AUTO) ---
def _write_text_if_changed(path: Path, content: str, encoding: str = "utf-8") -> bool:
    """Write only if file content differs. Returns True if written."""
    try:
        if path.exists():
            try:
                old = path.read_text(encoding=encoding)
            except Exception:
                old = None  # unreadable -> treat as changed
            if old is not None and old == content:
                return False
    except Exception:
        # If any FS weirdness occurs, fall back to writing (safe default)
        pass

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)
    return True
# --- ZERO-DIFF WRITE GUARD (AUTO) --- END


# -------------------------
# Encoding helpers (robust UTF-16/BOM support)
# -------------------------
def read_text_smart(path: Path) -> str:
    """
    Robustly read text files with automatic encoding detection.

    Handles:
    - UTF-16 BOM (FF FE / FE FF)
    - UTF-16LE/BE detection via NUL byte heuristic
    - UTF-8 with fallback to replace mode
    - Control character cleanup (except \n and \t)

    Args:
        path: Path to the file to read

    Returns:
        Cleaned text content as str
    """
    b = path.read_bytes()
    head = b[:4096] if len(b) >= 4096 else b
    nul_count = head.count(b"\x00")

    enc = "utf-8"

    # Check for BOM
    if b.startswith(b"\xff\xfe"):
        enc = "utf-16le"
    elif b.startswith(b"\xfe\xff"):
        enc = "utf-16be"
    elif b.startswith(b"\xff\xfe\x00\x00"):
        enc = "utf-32le"
    elif b.startswith(b"\x00\x00\xfe\xff"):
        enc = "utf-32be"
    elif nul_count > 0:
        # Heuristic: UTF-16LE often has NUL bytes in odd positions for ASCII text
        if len(head) > 1:
            odd_nul = head[1::2].count(0)
            even_nul = head[0::2].count(0)
            if odd_nul > even_nul:
                enc = "utf-16le"
            elif even_nul > odd_nul:
                enc = "utf-16be"

    # Try decoding
    try:
        txt = b.decode(enc)
    except (UnicodeDecodeError, LookupError):
        # Fallback: UTF-8 with replace
        txt = b.decode("utf-8", errors="replace")

    # Remove BOM if present
    if txt.startswith('\ufeff'):
        txt = txt[1:]

    # Remove control characters except \n (0x0A) and \t (0x09)
    # This prevents issues like DC3 (0x13) appearing in output
    cleaned = "".join(
        ch for ch in txt
        if ch == "\n" or ch == "\t" or unicodedata.category(ch) != "Cc"
    )

    return cleaned


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
    rc, out = _run_git(["symbolic-ref", "-q", "refs/remotes/origin/HEAD"])
    if rc == 0 and out:
        parts = out.split("/")
        if parts:
            return parts[-1]
    return fallback


def get_deterministic_marker(source_file: Path) -> str:
    """
    Get a deterministic marker based on the source file's git history.
    Returns format: "YYYY-MM-DD HH:MM:SS [sha7]"
    Falls back to current timestamp if git info unavailable.
    """
    rc, out = _run_git(["log", "-1", "--format=%ct %h", "--", str(source_file)])
    if rc == 0 and out:
        parts = out.split()
        if len(parts) == 2:
            timestamp_str, sha_short = parts
            try:
                timestamp = int(timestamp_str)
                dt_obj = dt.datetime.fromtimestamp(timestamp)
                return f"{dt_obj.strftime('%Y-%m-%d %H:%M:%S')} [{sha_short}]"
            except (ValueError, OSError):
                pass

    # Fallback to current time (non-deterministic)
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# -------------------------
# TODO parsing
# -------------------------
ID_RE = re.compile(r"\[([A-Za-z0-9_\-]+)\]")
HINT_PATH_RE = re.compile(r"hint_path:\s*\"([^\"]+)\"|hint_path:\s*([^\s]+)")
HINT_REF_RE = re.compile(r"hint_ref:\s*\"([^\"]+)\"|hint_ref:\s*([^\s]+)")
HINT_LINE_RE = re.compile(r"hint_line:\s*(\d+)")
TAG_RE = re.compile(r"#([A-Za-z0-9_\-]+)")


@dataclass(frozen=True)
class TodoItem:
    id: str
    status: str   # TODO | DOING | DONE
    title: str
    section: str
    hint_path: Optional[str]
    hint_ref: Optional[str]   # "file.py:120" format
    hint_line: Optional[int]  # standalone line number
    tags: List[str]


def detect_source_md(repo_root: Path) -> Path:
    preferred = repo_root / "docs" / "Peak_Trade_Research_Strategy_TODO_2025-12-07.md"
    if preferred.exists():
        return preferred

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

        # hint_path
        hp = None
        mhp = HINT_PATH_RE.search(rest)
        if mhp:
            hp = (mhp.group(1) or mhp.group(2) or "").strip().strip('"')

        # hint_ref: "file.py:120" format
        hr = None
        mhr = HINT_REF_RE.search(rest)
        if mhr:
            hr = (mhr.group(1) or mhr.group(2) or "").strip().strip('"')

        # hint_line: standalone line number
        hl = None
        mhl = HINT_LINE_RE.search(rest)
        if mhl:
            try:
                hl = int(mhl.group(1))
            except ValueError:
                pass

        tags = sorted({t.lower() for t in TAG_RE.findall(rest)})

        items.append(TodoItem(
            id=item_id,
            status=status,
            title=rest,
            section=section,
            hint_path=hp,
            hint_ref=hr,
            hint_line=hl,
            tags=tags
        ))

    return items


# -------------------------
# Link & command builders
# -------------------------
def github_link(repo_web: Optional[str], branch: str, it: TodoItem) -> Optional[str]:
    """
    GitHub link mit optionaler Zeilen-Unterstützung.
    Priorität: hint_ref > hint_path (+ hint_line)
    """
    if not repo_web:
        return None

    # hint_ref: "path/file.py:120"
    if it.hint_ref:
        ref = it.hint_ref.strip().lstrip("/")
        if ":" in ref:
            fpath, line = ref.split(":", 1)
            return f"{repo_web}/blob/{branch}/{fpath.rstrip('/')}#L{line}"
        else:
            # kein :line → blob/tree heuristic
            is_dir = ref.endswith("/") or (not os.path.splitext(ref)[1])
            mode = "tree" if is_dir else "blob"
            return f"{repo_web}/{mode}/{branch}/{ref.rstrip('/')}"

    # hint_path + optional hint_line
    if it.hint_path:
        p = it.hint_path.strip().lstrip("/")
        if not p:
            return None
        is_dir = p.endswith("/") or (not os.path.splitext(p)[1])
        mode = "tree" if is_dir else "blob"
        base = f"{repo_web}/{mode}/{branch}/{p.rstrip('/')}"
        if it.hint_line and mode == "blob":
            return f"{base}#L{it.hint_line}"
        return base

    return None


def cursor_link(repo_root: Optional[Path], it: TodoItem) -> Optional[str]:
    """
    Cursor link mit Zeilen-Support - PATH INDEPENDENT.
    Priorität: hint_ref > hint_path (+ hint_line) > repo_root
    Format: cursor://file/__REPO_ROOT__/<REL_PATH>:line:col
    The __REPO_ROOT__ placeholder will be replaced by the actual repo root path
    when the HTML is opened (via JavaScript injection or similar mechanism).
    """
    if not repo_root:
        return None

    # Use a placeholder for repo root to maintain path independence
    repo_placeholder = "__REPO_ROOT__"

    # hint_ref: "path/file.py:120"
    if it.hint_ref:
        ref = it.hint_ref.strip().lstrip("/")
        if ":" in ref:
            fpath, line = ref.split(":", 1)
            # Use relative path with placeholder
            return f"cursor://file/{repo_placeholder}/{fpath}:{line}:1"
        else:
            return f"cursor://file/{repo_placeholder}/{ref}:1:1"

    # hint_path + optional hint_line
    if it.hint_path:
        p = it.hint_path.strip().lstrip("/")
        if it.hint_line:
            return f"cursor://file/{repo_placeholder}/{p}:{it.hint_line}:1"
        return f"cursor://file/{repo_placeholder}/{p}:1:1"

    # fallback: repo root
    return f"cursor://file/{repo_placeholder}:1:1"


def build_work_prompt(it: TodoItem) -> str:
    tags = ", ".join([f"#{t}" for t in it.tags]) if it.tags else "(keine)"
    
    # Location info mit Priorität
    loc_parts = []
    if it.hint_ref:
        loc_parts.append(f"hint_ref: {it.hint_ref}")
    elif it.hint_path:
        loc_parts.append(f"hint_path: {it.hint_path}")
        if it.hint_line:
            loc_parts.append(f"line: {it.hint_line}")
    else:
        loc_parts.append("hint_path: .")
    
    loc = " | ".join(loc_parts)
    
    return (
        f"Peak_Trade TODO [{it.id}] ({it.status}) — {it.title} | "
        f"Section: {it.section} | {loc} | Tags: {tags}. "
        "Bitte implementiere/fixe dieses TODO minimal-invasiv, mit Tests wo sinnvoll, "
        "und gib mir einen sauberen Git-Diff + kurze Begründung."
    )


def claude_code_command(repo_root: Optional[Path], it: TodoItem) -> Optional[str]:
    """
    Claude Code startet mit initial prompt - PATH INDEPENDENT:
      cd __REPO_ROOT__ && claude "query"
    The __REPO_ROOT__ placeholder will be replaced by the actual repo root path
    when the command is copied (via JavaScript).
    """
    if not repo_root:
        return None

    prompt = build_work_prompt(it).replace("\n", " ").strip()
    # Use placeholder for repo root to maintain path independence
    return f'cd __REPO_ROOT__ && claude {shlex.quote(prompt)}'


# -------------------------
# HTML rendering
# -------------------------
def render_html(items: List[TodoItem], source_md: Path, repo_root: Optional[Path], repo_web: Optional[str], branch: str) -> str:
    marker = get_deterministic_marker(source_md)
    # Make source path relative to repo root for path independence
    try:
        src_rel = str(source_md.relative_to(repo_root)).replace("\\", "/")
    except (ValueError, AttributeError):
        src_rel = str(source_md).replace("\\", "/")

    cards = []
    for it in items:
        cards.append({
            "id": it.id,
            "status": it.status,
            "title": it.title,
            "section": it.section,
            "hint_path": it.hint_path,
            "hint_ref": it.hint_ref,
            "hint_line": it.hint_line,
            "tags": it.tags,
            "github": github_link(repo_web, branch, it),
            "cursor": cursor_link(repo_root, it),
            "prompt": build_work_prompt(it),
            "claude_cmd": claude_code_command(repo_root, it),
        })

    cards_json = json.dumps(cards, ensure_ascii=False, indent=None)

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
      --toast: rgba(0,0,0,0.75);
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
    .search {{ display: flex; gap: 8px; align-items: center; }}
    input {{
      width: 420px; max-width: 80vw;
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
      flex-wrap: wrap;
    }}
    .id {{
      font-size: 11px; color: var(--muted);
      border: 1px solid var(--border); border-radius: 999px; padding: 2px 8px;
      flex: 0 0 auto;
    }}
    .left {{
      flex: 1 1 460px;
      min-width: 260px;
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
      margin-top: 2px;
      user-select: none;
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
      line-height: 1.6;
    }}
    .toast {{
      position: fixed;
      left: 50%;
      bottom: 24px;
      transform: translateX(-50%);
      background: var(--toast);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 10px 12px;
      border-radius: 12px;
      box-shadow: var(--shadow);
      opacity: 0;
      transition: opacity 120ms ease;
      pointer-events: none;
      font-size: 12px;
      max-width: min(820px, 92vw);
      text-align: center;
    }}
    .toast.show {{ opacity: 1; }}
    code {{ color: var(--text); }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="top">
      <div>
        <div class="title">Peak_Trade – TODO Board</div>
        <div class="meta">
          Quelle: {esc(src_rel)}<br/>
          Generiert: {esc(marker)}<br/>
          {repo_line}
        </div>
      </div>
      <div class="search">
        <input id="q" placeholder="Suche (Text, ID, Tag, Section, Pfad) …" />
      </div>
    </div>

    <div class="grid" id="grid"></div>

    <div class="foot">
      🌐 GitHub ist aktiv bei <code>hint_path</code> oder <code>hint_ref</code> (springt zu Zeile bei <code>#L...</code>).<br/>
      🧠 Cursor: öffnet Pfad + springt zu Zeile (bei <code>hint_ref: "file:120"</code> oder <code>hint_line</code>) + kopiert Prompt.<br/>
      🤖 Claude Code: kopiert <code>cd … && claude "…"</code> Kommando (ins Terminal pasten & Enter).<br/>
      <em>Syntax</em>: <code>hint_path: "src/"</code>, <code>hint_ref: "file.py:120"</code>, <code>hint_line: 42</code>
    </div>
  </div>

  <div id="toast" class="toast"></div>

<script>
// Replace __REPO_ROOT__ placeholder with actual repo root at runtime
(function() {{
  // Get the actual repo root from the HTML file's location
  let actualRepoRoot = "";

  if (window.location.protocol === "file:") {{
    let pathname = decodeURIComponent(window.location.pathname);

    // Windows file:// URLs may have leading slash before drive letter (e.g., /C:/...)
    if (pathname.match(/^\/[A-Z]:\//)) {{
      pathname = pathname.substring(1);
    }}

    // Strip marker: file is under docs/00_overview/<filename>
    const marker = "/docs/00_overview/";
    const markerIdx = pathname.indexOf(marker);

    if (markerIdx !== -1) {{
      // Extract repo root: everything before the marker
      actualRepoRoot = pathname.substring(0, markerIdx);
    }} else {{
      // Fallback: assume file is 3 levels deep from repo root
      const parts = pathname.split("/");
      actualRepoRoot = parts.slice(0, -3).join("/");
    }}
  }}

  // Replace __REPO_ROOT__ in all CARDS cursor and claude_cmd fields
  window.__ACTUAL_REPO_ROOT__ = actualRepoRoot;
}})();

const CARDS = {cards_json};

const COLS = [
  {{ key: "TODO",  title: "Offen" }},
  {{ key: "DOING", title: "In Arbeit" }},
  {{ key: "DONE",  title: "Erledigt" }},
];

function norm(s) {{
  return (s || "").toString().toLowerCase();
}}

function showToast(msg) {{
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  window.clearTimeout(window.__toastTimer);
  window.__toastTimer = window.setTimeout(() => t.classList.remove("show"), 1600);
}}

async function copyToClipboard(text) {{
  try {{
    await navigator.clipboard.writeText(text);
    return true;
  }} catch(e) {{
    try {{
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      return true;
    }} catch(_) {{
      return false;
    }}
  }}
}}

function matches(card, q) {{
  if (!q) return true;
  const hay = [
    card.id, card.title, card.section,
    (card.hint_path || ""),
    (card.hint_ref || ""),
    (card.tags || []).join(" "),
    (card.github || "")
  ].map(norm).join(" | ");
  return hay.includes(q);
}}

function buildLocationLabel(c) {{
  if (c.hint_ref) return `Ref: ${{c.hint_ref}}`;
  if (c.hint_path && c.hint_line) return `Pfad: ${{c.hint_path}}:${{c.hint_line}}`;
  if (c.hint_path) return `Pfad: ${{c.hint_path}}`;
  return null;
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

      const id = document.createElement("div");
      id.className = "id";
      id.textContent = c.id;

      const left = document.createElement("div");
      left.className = "left";

      const title = document.createElement("div");
      title.className = "txt";
      title.textContent = c.title;

      const sub = document.createElement("div");
      sub.className = "sub";

      const sec = document.createElement("span");
      sec.textContent = `Section: ${{c.section}}`;
      sub.appendChild(sec);

      const locLabel = buildLocationLabel(c);
      if (locLabel) {{
        const loc = document.createElement("span");
        loc.textContent = locLabel;
        sub.appendChild(loc);
      }}

      (c.tags || []).forEach(t => {{
        const tag = document.createElement("span");
        tag.className = "tag";
        tag.textContent = `#${{t}}`;
        sub.appendChild(tag);
      }});

      left.appendChild(title);
      left.appendChild(sub);

      // 🌐 GitHub
      const btnGH = document.createElement("a");
      btnGH.className = "btn";
      btnGH.textContent = "🌐 GitHub";
      if (c.github) {{
        btnGH.href = c.github;
        btnGH.target = "_blank";
        btnGH.rel = "noopener noreferrer";
        const hasLine = c.github.includes("#L");
        btnGH.title = hasLine ? "Öffnet Datei auf GitHub an Zeile" : "Öffnet Datei/Verzeichnis auf GitHub";
      }} else {{
        btnGH.setAttribute("aria-disabled", "true");
        btnGH.href = "#";
        btnGH.title = "Kein hint_path/hint_ref oder Repo nicht erkannt";
      }}

      // 🧠 Cursor: copy prompt + open
      const btnCU = document.createElement("a");
      btnCU.className = "btn";
      btnCU.textContent = "🧠 Cursor";
      if (c.cursor) {{
        // Replace __REPO_ROOT__ placeholder with actual path at runtime
        const cursorUrl = c.cursor.replace(/__REPO_ROOT__/g, window.__ACTUAL_REPO_ROOT__ || "");
        btnCU.href = cursorUrl;
        btnCU.onclick = async (ev) => {{
          const ok = await copyToClipboard(c.prompt || "");
          const hasLine = c.hint_ref && c.hint_ref.includes(":") || c.hint_line;
          const msg = ok
            ? (hasLine ? "Cursor-Prompt kopiert — Cursor springt zu Zeile…" : "Cursor-Prompt kopiert — Cursor öffnet…")
            : "Konnte Prompt nicht kopieren (Clipboard)";
          showToast(msg);
        }};
        const hasLine = c.hint_ref && c.hint_ref.includes(":") || c.hint_line;
        btnCU.title = hasLine ? "Öffnet in Cursor + springt zu Zeile + kopiert Prompt" : "Öffnet in Cursor + kopiert Prompt";
      }} else {{
        btnCU.setAttribute("aria-disabled", "true");
        btnCU.href = "#";
      }}

      // 🤖 Claude Code: copy terminal command
      const btnCC = document.createElement("a");
      btnCC.className = "btn";
      btnCC.textContent = "🤖 Claude Code";
      if (c.claude_cmd) {{
        btnCC.href = "#";
        btnCC.onclick = async (ev) => {{
          ev.preventDefault();
          // Replace __REPO_ROOT__ placeholder with actual path at runtime
          const claudeCmd = c.claude_cmd.replace(/__REPO_ROOT__/g, window.__ACTUAL_REPO_ROOT__ || "");
          const ok = await copyToClipboard(claudeCmd);
          showToast(ok ? "Claude Code Kommando kopiert — im Terminal einfügen & Enter" : "Konnte Kommando nicht kopieren (Clipboard)");
        }};
        btnCC.title = "Kopiert: cd … && claude \"…\" (ins Terminal pasten)";
      }} else {{
        btnCC.setAttribute("aria-disabled", "true");
        btnCC.href = "#";
      }}

      row.appendChild(id);
      row.appendChild(left);
      row.appendChild(btnGH);
      row.appendChild(btnCU);
      row.appendChild(btnCC);

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

    md = read_text_smart(source)
    items = parse_todos(md)

    origin = detect_origin_url()
    repo_web = args.repo_web or (origin_to_repo_web(origin) if origin else None)
    branch = args.branch or detect_default_branch("main")

    out_html = repo_root / args.out_html
    html_doc = render_html(items, source, repo_root, repo_web, branch)
    _write_text_if_changed(out_html, html_doc, encoding="utf-8")

    # Generate deterministic marker for README
    marker = get_deterministic_marker(source)

    out_readme = repo_root / args.out_readme
    readme_content = f"""# Peak_Trade – TODO Board

Dieses TODO Board wird automatisch aus einer Markdown-TODO-Datei generiert.

## Generieren

```bash
python3 scripts/build_todo_board_html.py
```

Öffne dann `docs/00_overview/PEAK_TRADE_TODO_BOARD.html` in deinem Browser.

### Operator Quick Commands

```bash
make todo-board                # Generiere TODO Board
make todo-board-check          # Validierung (Idempotenz + Tests)
./scripts/check_todo_board_ci.sh  # CI Guard direkt
```

## Features

- 3-spaltige Kanban-Ansicht (TODO, DOING, DONE)
- Echtzeit-Suche über Text, IDs, Tags, Sections, Pfade
- Deep-Links zu GitHub (tree/blob) mit Zeilen-Support
- Cursor URL-Scheme Links mit Zeilen-Sprung + Prompt-Copy
- Claude Code Terminal-Kommando Generator
- Dark Theme UI

## Syntax in der Source-TODO-Datei

```markdown
## Meine Section

- [ ] [PT-123] Aufgabe mit ID hint_path: "docs/ops/" #ops #urgent
- [ ] Task mit Zeilen-Ref hint_ref: "scripts/foo.py:120" #feature
- [ ] Task mit separatem Line hint_path: "src/core.py" hint_line: 42 #bug
- [ ] Task ohne ID (wird T0001) #feature
- [x] Erledigte Aufgabe
- [ ] DOING: Läuft gerade (Status-Override)
```

## Location Hints (Priorität)

1. **`hint_ref: "file.py:120"`** - Kombiniert Pfad + Zeile (bevorzugt)
   - Cursor springt direkt zu Zeile 120
   - GitHub öffnet Datei bei `#L120`

2. **`hint_path: "file.py"` + `hint_line: 42`** - Getrennte Angaben
   - Cursor springt zu Zeile 42
   - GitHub öffnet Datei bei `#L42`

3. **`hint_path: "src/dir/"`** - Nur Pfad
   - Cursor/GitHub öffnen Datei/Verzeichnis ohne Zeilen-Sprung

## Button-Funktionen

- **🌐 GitHub**: Öffnet Datei/Verzeichnis auf GitHub (mit `#L...` bei Zeilen-Angabe)
- **🧠 Cursor**: Kopiert Task-Prompt + öffnet Pfad (springt zu Zeile bei Angabe)
- **🤖 Claude Code**: Kopiert `cd ... && claude "..."` Kommando für Terminal

## Quell-Datei

Standard: `docs/Peak_Trade_Research_Strategy_TODO_2025-12-07.md`
Fallback: Erste `*TODO*.md` in `docs/`.

Override mit `--source-md`.

---

**Generated:** {marker}
**Output:** `{out_html.relative_to(repo_root)}`
"""
    _write_text_if_changed(out_readme, readme_content, encoding="utf-8")

    print(f"✅ TODO Board erstellt:")
    print(f"   HTML:   {out_html.relative_to(repo_root)}")
    print(f"   README: {out_readme.relative_to(repo_root)}")
    print(f"\n📂 Öffne {out_html.name} in deinem Browser.")

    # Auto-inject Claude Code auth shortcuts (idempotent)
    try:
        inject_script = repo_root / "scripts" / "inject_todo_board_shortcuts.py"
        if inject_script.exists():
            import subprocess
            result = subprocess.run([sys.executable, str(inject_script), str(out_html)],
                                   capture_output=True, text=True, cwd=str(repo_root))
            if result.returncode == 0:
                print(f"   {result.stdout.strip()}")
            else:
                print(f"   ⚠️  Shortcut injection failed: {result.stderr.strip()}")
    except Exception as e:
        print(f"   ⚠️  Shortcut injection error: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
