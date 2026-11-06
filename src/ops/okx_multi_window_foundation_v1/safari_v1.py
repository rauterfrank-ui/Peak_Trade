"""Read/write Safari window state via AppleScript (local macOS only)."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

NEUTRAL_SLOT_URLS = frozenset({"favorites://", "about:blank", "about:home"})


@dataclass(frozen=True)
class SafariWindow:
    window_id: int
    tab_count: int
    name: str
    primary_tab_url: str

    def slot_fingerprint(self) -> str:
        return f"{self.name}|{self.tab_count}|{self.primary_tab_url}"

    def is_neutral_slot_window(self) -> bool:
        return (
            self.tab_count == 1
            and self.primary_tab_url in NEUTRAL_SLOT_URLS
            and self.name.startswith("Startseite")
        )


class SafariProbeError(RuntimeError):
    pass


_LIST_WINDOWS_SCRIPT = """
tell application "Safari"
  set outText to ""
  repeat with w in windows
    set tabUrl to URL of current tab of w
    set outText to outText & (id of w as text) & "\\t" & (count of tabs of w as text) & "\\t" & (name of w as text) & "\\t" & tabUrl & linefeed
  end repeat
  return outText
end tell
"""

_CREATE_WINDOW_SCRIPT = """
tell application "Safari"
  make new document
  delay 0.3
  return id of front window
end tell
"""

_SET_TAB_URL_TEMPLATE = """
tell application "Safari"
  repeat with w in windows
    if id of w is {window_id} then
      set URL of current tab of w to {url_json}
      return "ok"
    end if
  end repeat
  return "missing"
end tell
"""


def _run_osascript(script: str) -> str:
    proc = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SafariProbeError(proc.stderr.strip() or proc.stdout.strip() or "osascript failed")
    return proc.stdout.strip()


def list_safari_windows() -> list[SafariWindow]:
    raw = _run_osascript(_LIST_WINDOWS_SCRIPT)
    windows: list[SafariWindow] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t", 3)
        if len(parts) != 4:
            raise SafariProbeError(f"unexpected_window_line:{line!r}")
        windows.append(
            SafariWindow(
                window_id=int(parts[0]),
                tab_count=int(parts[1]),
                name=parts[2],
                primary_tab_url=parts[3],
            )
        )
    return windows


def create_safari_window() -> int:
    raw = _run_osascript(_CREATE_WINDOW_SCRIPT)
    return int(raw)


def set_window_tab_url(window_id: int, url: str) -> None:
    script = _SET_TAB_URL_TEMPLATE.format(
        window_id=window_id,
        url_json=json.dumps(url),
    )
    result = _run_osascript(script)
    if result != "ok":
        raise SafariProbeError(f"window_not_found:{window_id}")
