#!/usr/bin/env python3
"""Fail-closed tracked secret-like policy gate (v1) + governance scanner entrypoint.

Capability overlay: SECRET_SCANNING_AND_PUSH_PROTECTION_GOVERNANCE_V1
Canonical scanner owner (reuse): this module — do not create a parallel scanner.

Scans tracked textual repository content for high-confidence secret-like
patterns. Never prints matched secret values — only path, pattern class, and
line number. Display-safe strings are routed through the canonical redaction
owner when any residual credential-shaped text could appear in output.

Allowlist: docs/ops/specs/tracked_credential_like_allowlist_v1.json
Canonical redaction owner: scripts/security/secret_hygiene_redaction_v1.py

History model: TRACKED_TREE enforced here; full-history scanning is
MANUAL_BOUNDED via --manual-history (not CI-enforced; not claimed as complete
repository-history protection).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ALLOWLIST_PATH = REPO_ROOT / "docs" / "ops" / "specs" / "tracked_credential_like_allowlist_v1.json"
ALLOWLIST_SCHEMA_VERSION = "tracked_credential_like_allowlist_v1"
GATE_ID = "tracked_credential_hygiene_policy_v1"
CAPABILITY_ID = "SECRET_SCANNING_AND_PUSH_PROTECTION_GOVERNANCE_V1"
HISTORY_SCAN_STATUS = "MANUAL_BOUNDED"

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
    (
        "AUTHORIZATION_HEADER_OR_ASSIGNMENT",
        re.compile(
            r"(?i)\b(?:authorization|proxy[_-]?authorization)\s*[:=]\s*"
            r"(?:bearer|basic)\s+[A-Za-z0-9_\-\.\/=+]{12,}"
        ),
    ),
)

# Sensitive assignment keys for bounded high-entropy heuristic (not a global rule disable).
# Quoted assignments only — avoids false positives on unpacking / call sites
# like `api_key, api_secret = load_credentials()`.
_SENSITIVE_ASSIGN_RX = re.compile(
    r"(?i)\b("
    r"api[_-]?key|api[_-]?secret|access[_-]?token|refresh[_-]?token|"
    r"client[_-]?secret|password|passwd|passphrase|private[_-]?key|"
    r"secret[_-]?key|auth[_-]?token|webhook[_-]?secret"
    r")\s*[=:]\s*[\"']([A-Za-z0-9_\-+/=.]{20,})[\"']"
)
_PLACEHOLDER_VALUE_RX = re.compile(
    r"(?i)(?:synthetic|placeholder|fixture|example|fake|dummy|not[_-]?real|"
    r"redacted|your[_-]|xxx+|changeme|todo|sample|test[_-]?only|null|none)"
)
_HIGH_ENTROPY_CLASS = "HIGH_ENTROPY_CREDENTIAL_ASSIGNMENT"
_MIN_ENTROPY = 3.5
_MIN_VALUE_LEN = 20

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

# Documented exclusions (reported in every summary — never silent).
SKIP_PREFIXES = (
    ".git/",
    "out/",
    "reports/",
    "docs/reports/",
    "node_modules/",
    ".venv/",
    "venv/",
)

REQUIRED_ENTRY_KEYS = frozenset({"path", "pattern_class", "bounded", "reason", "owner"})


@dataclass(frozen=True)
class Finding:
    path: str
    line_no: int
    pattern_class: str

    @property
    def secret_value_exposed(self) -> bool:
        return False


def _safe_display(text: str) -> str:
    """Route potential credential-shaped text through canonical redaction."""
    from scripts.security import secret_hygiene_redaction_v1 as redaction

    return str(redaction.redact_for_diagnostics(text))


def _shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = Counter(value)
    length = len(value)
    return -sum((n / length) * math.log2(n / length) for n in counts.values())


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


def _parse_optional_date(raw: object, field: str, path: str) -> date | None:
    if raw is None or raw == "":
        return None
    if not isinstance(raw, str):
        raise ValueError(f"allowlist entry {path}: {field} must be YYYY-MM-DD string")
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"allowlist entry {path}: invalid {field}={raw!r}") from exc


def _validate_allowlist(data: dict[str, object]) -> dict[str, object]:
    schema = data.get("schema_version")
    if schema != ALLOWLIST_SCHEMA_VERSION:
        raise ValueError(f"allowlist schema_version must be {ALLOWLIST_SCHEMA_VERSION}")
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise ValueError("allowlist.entries must be list")
    today = date.today()
    known_classes = {name for name, _ in PATTERN_CLASSES} | {_HIGH_ENTROPY_CLASS}
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"allowlist.entries[{idx}] must be object")
        missing = REQUIRED_ENTRY_KEYS - set(entry.keys())
        if missing:
            raise ValueError(f"allowlist.entries[{idx}] missing keys: {sorted(missing)}")
        path = entry.get("path")
        pattern_class = entry.get("pattern_class")
        if not isinstance(path, str) or not path or any(ch in path for ch in "*?[]"):
            raise ValueError(
                f"allowlist.entries[{idx}]: path must be exact repo-relative path "
                "(no directory wildcards)"
            )
        if path.endswith("/"):
            raise ValueError(
                f"allowlist.entries[{idx}]: directory wildcard/prefix suppressions forbidden"
            )
        if not isinstance(pattern_class, str) or pattern_class not in known_classes:
            raise ValueError(
                f"allowlist.entries[{idx}]: pattern_class must be a known rule id "
                f"(got {pattern_class!r})"
            )
        if entry.get("bounded") is not True:
            raise ValueError(f"allowlist.entries[{idx}]: bounded must be true")
        if entry.get("disable_rule") is True or entry.get("global_disable") is True:
            raise ValueError(f"allowlist.entries[{idx}]: global rule disable forbidden")
        owner = entry.get("owner")
        if not isinstance(owner, str) or not owner.strip():
            raise ValueError(f"allowlist.entries[{idx}]: owner required")
        reason = str(entry.get("reason") or "")
        reason_l = reason.lower()
        if not (
            "synthetic" in reason_l
            or "placeholder" in reason_l
            or "fixture" in reason_l
            or "documentation" in reason_l
            or "pattern definition" in reason_l
        ):
            raise ValueError(
                f"allowlist.entries[{idx}]: reason must state synthetic/placeholder/"
                "fixture/documentation/pattern definition"
            )
        expires = _parse_optional_date(entry.get("expires_on"), "expires_on", path)
        review_by = _parse_optional_date(entry.get("review_by"), "review_by", path)
        if expires is None and review_by is None:
            raise ValueError(
                f"allowlist.entries[{idx}]: expires_on or review_by required (YYYY-MM-DD)"
            )
        if expires is not None and expires < today:
            raise ValueError(f"allowlist.entries[{idx}]: expires_on {expires} is expired")
        if review_by is not None and review_by < today:
            raise ValueError(f"allowlist.entries[{idx}]: review_by {review_by} is overdue")
    return data


def _load_allowlist() -> dict[str, object]:
    if not ALLOWLIST_PATH.is_file():
        raise FileNotFoundError(f"allowlist missing: {ALLOWLIST_PATH}")
    data = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("allowlist root must be object")
    return _validate_allowlist(data)


def _allowlisted(path: str, pattern_class: str, allowlist: dict[str, object]) -> bool:
    entries = allowlist.get("entries", [])
    assert isinstance(entries, list)
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("path") == path and entry.get("pattern_class") == pattern_class:
            # Schema already enforced bounded + reason + expiry; honor exact match only.
            return True
    return False


def _high_entropy_hits(line: str) -> bool:
    for match in _SENSITIVE_ASSIGN_RX.finditer(line):
        value = match.group(2)
        if len(value) < _MIN_VALUE_LEN:
            continue
        if _PLACEHOLDER_VALUE_RX.search(value):
            continue
        # Reject low-diversity / repeated-char noise.
        if len(set(value)) < 8:
            continue
        if _shannon_entropy(value) >= _MIN_ENTROPY:
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
        if _high_entropy_hits(line):
            if not _allowlisted(path, _HIGH_ENTROPY_CLASS, allowlist):
                findings.append(
                    Finding(path=path, line_no=line_no, pattern_class=_HIGH_ENTROPY_CLASS)
                )
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


def _manual_history_scan(*, max_commits: int) -> list[Finding]:
    """Bounded manual history audit — not CI-enforced; not full-history protection.

    Inspects recent commit message subjects and names of files touched in the
    last N commits for high-confidence pattern classes. Does not dump patch
    bodies (avoids printing secret values into CI/operator logs).
    """
    if max_commits < 1 or max_commits > 500:
        raise ValueError("max_commits must be in 1..500")
    proc = subprocess.run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "log",
            f"-n{max_commits}",
            "--pretty=format:%H%x00%s",
            "--name-only",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    allowlist = _load_allowlist()
    findings: list[Finding] = []
    current_commit = "UNKNOWN"
    for raw_line in proc.stdout.splitlines():
        line = raw_line.strip("\n")
        if not line:
            continue
        if "\0" in line:
            current_commit, subject = line.split("\0", 1)
            # Scan subject only (never print subject if it matches — report class only).
            for pattern_class, rx in PATTERN_CLASSES:
                if rx.search(subject) and not _allowlisted(
                    f"git:commit_subject:{current_commit}", pattern_class, allowlist
                ):
                    findings.append(
                        Finding(
                            path=f"git:commit_subject:{current_commit[:12]}",
                            line_no=0,
                            pattern_class=pattern_class,
                        )
                    )
            continue
        # File path touched — if the path string itself embeds a secret-like token.
        for pattern_class, rx in PATTERN_CLASSES:
            if rx.search(line) and not _allowlisted(line, pattern_class, allowlist):
                findings.append(
                    Finding(
                        path=f"git:path:{current_commit[:12]}",
                        line_no=0,
                        pattern_class=pattern_class,
                    )
                )
    return findings


def _build_summary(findings: list[Finding], *, mode: str) -> dict[str, object]:
    return {
        "gate": GATE_ID,
        "capability_id": CAPABILITY_ID,
        "mode": mode,
        "history_scan_status": HISTORY_SCAN_STATUS,
        "tracked_tree_scan_enforced": mode == "tracked_tree",
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
        "documented_skip_prefixes": list(SKIP_PREFIXES),
        "network_required": False,
        "fail_closed": True,
    }


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
    parser.add_argument(
        "--manual-history",
        action="store_true",
        help=(
            "Run MANUAL_BOUNDED history audit (recent commits subjects/paths only). "
            "Not claimed as complete Git-history protection; not CI-enforced."
        ),
    )
    parser.add_argument(
        "--history-max-commits",
        type=int,
        default=100,
        help="Commit window for --manual-history (1..500, default 100).",
    )
    args = parser.parse_args(argv)

    paths: list[str] | None = None
    try:
        if args.manual_history:
            findings = _manual_history_scan(max_commits=args.history_max_commits)
            mode = "manual_history_bounded"
        else:
            if args.paths_file:
                paths = [
                    line.strip()
                    for line in Path(args.paths_file).read_text(encoding="utf-8").splitlines()
                    if line.strip() and not line.strip().startswith("#")
                ]
            findings = scan_repo(paths)
            mode = "tracked_tree"
        summary = _build_summary(findings, mode=mode)
    except Exception as exc:  # fail closed
        safe_reason = _safe_display(f"{type(exc).__name__}: {exc}")
        print(
            f"TRACKED_SECRET_POLICY_GATE=FAIL reason={safe_reason}",
            file=sys.stderr,
        )
        return 2

    if args.json:
        from scripts.security import secret_hygiene_redaction_v1 as redaction

        # Structured redaction on the summary object (no secret values present).
        safe_summary = redaction.redact_for_diagnostics(summary)
        print(json.dumps(safe_summary, sort_keys=True, indent=2))
    else:
        if findings:
            print("TRACKED_SECRET_POLICY_GATE=FAIL")
            print(f"HISTORY_SCAN_STATUS={HISTORY_SCAN_STATUS}")
            print(f"DOCUMENTED_SKIP_PREFIXES={','.join(SKIP_PREFIXES)}")
            for f in findings:
                # Never print matched values.
                print(f"SECRET_LIKE_HIT path={f.path} line={f.line_no} class={f.pattern_class}")
        else:
            print("TRACKED_SECRET_POLICY_GATE=PASS")
            print("SECRET_VALUE_EXPOSED=false")
            print(f"HISTORY_SCAN_STATUS={HISTORY_SCAN_STATUS}")
            print(f"DOCUMENTED_SKIP_PREFIXES={','.join(SKIP_PREFIXES)}")

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
