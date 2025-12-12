#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys

MARKER_START = "<!-- PT_AUTH_SHORTCUT v1 START -->"
MARKER_END   = "<!-- PT_AUTH_SHORTCUT v1 END -->"

INJECT_BLOCK = f"""
{MARKER_START}

<style>
  /* Peak_Trade: Claude Auth Shortcut */
  #pt-auth-shortcut {{
    position: fixed;
    right: 16px;
    bottom: 16px;
    z-index: 99999;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    align-items: center;
    font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji","Segoe UI Emoji";
  }}
  #pt-auth-shortcut a {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.16);
    background: rgba(20,20,20,0.72);
    backdrop-filter: blur(8px);
    color: #fff;
    text-decoration: none;
    font-size: 13px;
    line-height: 1;
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
    transition: transform 120ms ease, background 120ms ease;
  }}
  #pt-auth-shortcut a:hover {{
    transform: translateY(-1px);
    background: rgba(20,20,20,0.85);
  }}
  #pt-auth-shortcut .dot {{
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: #34d399; /* grün */
  }}
  #pt-auth-shortcut .warn {{
    background: #fbbf24; /* gelb */
  }}
</style>

<div id="pt-auth-shortcut" aria-label="Peak_Trade Shortcuts">
  <a href="../ops/CLAUDE_CODE_AUTH_RUNBOOK.md" target="_blank" rel="noopener">
    <span class="dot warn"></span>
    Claude Auth Runbook
  </a>
  <a href="../DEV_WORKFLOW_SHORTCUTS.md" target="_blank" rel="noopener">
    <span class="dot"></span>
    Workflow Shortcuts
  </a>
  <a href="../../scripts/claude_code_auth_reset.sh" target="_blank" rel="noopener" title="Script öffnen (read-only)">
    <span class="dot"></span>
    auth_reset.sh
  </a>
</div>
{MARKER_END}
""".lstrip("\n")

def inject_into_html(path: Path) -> bool:
    html = path.read_text(encoding="utf-8", errors="replace")

    # idempotent
    if MARKER_START in html and MARKER_END in html:
        return False

    if "</body>" not in html:
        raise RuntimeError(f"Kein </body> Tag gefunden in {path}")

    html = html.replace("</body>", INJECT_BLOCK + "\n</body>")
    path.write_text(html, encoding="utf-8")
    return True

def main() -> int:
    html_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/00_overview/PEAK_TRADE_TODO_BOARD.html")
    if not html_path.exists():
        print(f"❌ HTML nicht gefunden: {html_path}")
        return 2

    changed = inject_into_html(html_path)
    print("✅ Shortcut injiziert." if changed else "ℹ️ Shortcut war bereits vorhanden (idempotent).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
