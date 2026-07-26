#!/usr/bin/env python3
"""Fail-closed tracked secret-like policy gate (v1).

Scans tracked textual repository content for high-confidence secret-like
patterns. Never prints matched secret values — only path, pattern class, and
line number.

Allowlist: docs/ops/specs/tracked_credential_like_allowlist_v1.json
Canonical redaction owner: scripts/security/secret_hygiene_redaction_v1.py
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST_PATH = REPO_ROOT / "docs" / "ops" / "specs" / "tracked_credential_like_allowlist_v1.json"

# High-confidence patterns only. Matched values are never emitted.
PATTERN_CLASSES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "PEM_PRIVATE_KEY",
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        ),
    ),
    ("AWS_ACCESS_KEY_ID", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("OPENAI_STYLE_KEY", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    (
        "JWT_LIKE",
        re.compile(r"\beyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\b"),
    ),
    (
        "URL_USERINFO_CREDENTIAL",
        re.compile(
            r"(?i)\b(?:https?|postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://"
            r"[^/\s:@]+:[^/\s@]+@"
        ),
    ),
)

TEXT_SUFFIXES = frozenset(
    {
        ".py",
        ".md",
        ".txt",
        ".json",
        ".yml",
        ".yaml",
        ".toml",
        ".ini",
        ".cfg",
        ".env",
        ".sh",
        ".bash",
        ".zsh",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".css",
        ".html",
        ".sql",
        ".csv",
        ".xml",
        ".rst",
        ".ipynb",
    }
)

SKIP_PREFIXES = (
    ".git/",
    "out/",
    "reports/",
    "docs/reports/",
    "node_modules/",
    ".venv/",
    "venv/",
)


@dataclass(frozen=True)
class Finding:
    path: str
    line_no: int
    pattern_class: str


def _git_tracked_files() -> list[str]:
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    raw = proc.stdout.split(b"\0")
    out: list[str] = []
    for item in raw:
        if not item:
            continue
        try:
            out.append(item.decode("utf-8"))
        except UnicodeDecodeError:
            continue
    return out


def _is_candidate(path: str) -> bool:
    if any(path.startswith(prefix) for prefix in SKIP_PREFIXES):
        return False
    p = Path(path)
    if p.suffix.lower() in TEXT_SUFFIXES:
        return True
    # Extensionless tracked policy/text files commonly named exactly.
    name = p.name.lower()
    return name in {"dockerfile", "makefile", "jenkinsfile", "license", "readme"}


def _load_allowlist() -> dict[str, object]:
    if not ALLOWLIST_PATH.is_file():
        raise FileNotFoundError(f"allowlist missing: {ALLOWLIST_PATH}")
    data = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("allowlist root must be object")
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise ValueError("allowlist.entries must be list")
    return data


def _allowlisted(path: str, pattern_class: str, allowlist: dict[str, object]) -> bool:
    entries = allowlist.get("entries", [])
    assert isinstance(entries, list)
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("path") == path and entry.get("pattern_class") == pattern_class:
            reason = str(entry.get("reason") or "")
            if (
                "synthetic" in reason.lower()
                or "placeholder" in reason.lower()
                or "fixture" in reason.lower()
            ):
                return True
            # Fail closed: allowlist reasons must be visibly bounded.
            if entry.get("bounded") is True:
                return True
    return False


def scan_text(path: str, text: str, allowlist: dict[str, object]) -> list[Finding]:
    findings: list[Finding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for pattern_class, rx in PATTERN_CLASSES:
            if not rx.search(line):
                continue
            if _allowlisted(path, pattern_class, allowlist):
                continue
            findings.append(Finding(path=path, line_no=line_no, pattern_class=pattern_class))
    return findings


def scan_repo(paths: Iterable[str] | None = None) -> list[Finding]:
    allowlist = _load_allowlist()
    tracked = list(paths) if paths is not None else _git_tracked_files()
    findings: list[Finding] = []
    for rel in tracked:
        if not _is_candidate(rel):
            continue
        abs_path = REPO_ROOT / rel
        if not abs_path.is_file():
            continue
        try:
            text = abs_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError:
            continue
        findings.extend(scan_text(rel, text, allowlist))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paths-file",
        help="Optional file with repo-relative paths to scan (one per line).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine JSON summary (no secret values).",
    )
    args = parser.parse_args(argv)

    paths: list[str] | None = None
    try:
        if args.paths_file:
            paths = [
                line.strip()
                for line in Path(args.paths_file).read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
        findings = scan_repo(paths)
    except Exception as exc:  # fail closed
        print(f"TRACKED_SECRET_POLICY_GATE=FAIL reason={type(exc).__name__}", file=sys.stderr)
        return 2

    summary = {
        "gate": "tracked_credential_hygiene_policy_v1",
        "findings_count": len(findings),
        "findings": [
            {
                "path": f.path,
                "line_no": f.line_no,
                "pattern_class": f.pattern_class,
                "secret_value_exposed": False,
            }
            for f in findings
        ],
        "secret_value_exposed": False,
        "allowlist_path": str(ALLOWLIST_PATH.relative_to(REPO_ROOT)),
    }

    if args.json:
        print(json.dumps(summary, sort_keys=True, indent=2))
    else:
        if findings:
            print("TRACKED_SECRET_POLICY_GATE=FAIL")
            for f in findings:
                # Never print matched values.
                print(f"SECRET_LIKE_HIT path={f.path} line={f.line_no} class={f.pattern_class}")
        else:
            print("TRACKED_SECRET_POLICY_GATE=PASS")
            print("SECRET_VALUE_EXPOSED=false")

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
